"""Incorpora coreyhaines31/marketingskills (MIT) sem parceiros pagos e sem chamadas a APIs.

Uso (a partir da raiz do repo; o checkout tem de estar no commit indicado):

    git clone https://github.com/coreyhaines31/marketingskills /tmp/marketingskills
    git -C /tmp/marketingskills checkout <commit>
    python scripts/vendor_marketingskills.py --src /tmp/marketingskills --commit <commit>

Gera (e reescreve; não editar à mão):

- ``vendor/marketingskills/``: as 50 skills limpas (SKILL.md + references/, sem evals/), LICENSE e
  PROVENANCE.md. É daqui que o ``skill-scout`` instala no Claude Code (agent-network-mcp/.claude/skills).
- ``skills/marketing/<action>/SKILL.md`` + ``agents/marketing/<action>.agent.md`` para as skills que o
  runner ainda não tinha (``NEW``), e o bloco gerado em ``config/marketing-capabilities.yaml``.
- ``vendor/marketingskills/tools-registry.md``: o catálogo de ferramentas, sem parceiros nem guias de API.

Limpeza (decisão do maestro, 2026-10-12): fica de fora tudo o que chama APIs (``tools/clis``,
``tools/integrations``, ``tools/composio``, ``tools/SETUP.md``) e os parceiros pagos (Converly, Ploy e
as marcas ◆). Cada remoção dirigida tem de encontrar o texto esperado; se o upstream mudar, o script
falha em vez de deixar passar um parceiro novo. No fim, nada do que sai pode conter os marcadores.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess  # nosec B404 - só `git rev-parse` no checkout dado
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "coreyhaines31/marketingskills"
VENDOR = ROOT / "vendor" / "marketingskills"
BEGIN = "  # BEGIN marketingskills (gerado por scripts/vendor_marketingskills.py; não editar à mão)"
END = "  # END marketingskills"

# As 11 que o runner já cobre em parte (skills/marketing/): vão só para o Claude Code.
OVERLAP = {
    "ad-creative": "ad_creative",
    "ads": "media_plan",
    "ai-seo": "seo_brief",
    "seo-audit": "skills/meta/seo-tech-checklist",
    "copywriting": "copy_answer_first",
    "copy-editing": "critic / creative_review",
    "customer-research": "research",
    "social": "copy_social / trend_hunter",
    "video": "video_edit_plan",
    "influencer-marketing": "influencer_brief / ugc_brief",
    "content-strategy": "internal_brief / seo_brief",
}

# As que o runner não tinha: action -> (capability id, níveis, descrição PT).
NEW: dict[str, tuple[str, str, str]] = {
    "ab-testing": ("ab_testing", "prepare", "Desenha testes A/B e programas de experimentação: hipótese, métrica, tamanho de amostra e leitura do resultado."),
    "analytics": ("analytics_tracking", "prepare", "Plano de medição e tracking (eventos, UTMs, GA4/GTM, dashboards); prepara a especificação, não mexe nas contas."),
    "aso": ("app_store_optimization", "prepare", "Auditoria e optimização de fichas na App Store e Google Play (título, keywords, screenshots, reviews)."),
    "attribution": ("performance_analysis", "read", "Lê resultados de campanha e atribuição (modelos, incrementalidade, MMM leve) para decidir o próximo ciclo."),
    "churn-prevention": ("churn_prevention", "prepare", "Reduz churn: fluxos de cancelamento, ofertas de retenção, recuperação de pagamentos falhados."),
    "co-marketing": ("co_marketing", "prepare", "Encontra parceiros de co-marketing e planeia campanhas conjuntas."),
    "cold-email": ("cold_outbound", "prepare", "Rascunhos de outbound B2B (emails frios e follow-ups) dentro do RGPD/LGPD; nunca envia."),
    "community-marketing": ("community_marketing", "prepare", "Estratégia de comunidade (fóruns, Discord, grupos) para crescimento e lealdade."),
    "competitor-profiling": ("competitor_profiling", "read", "Perfis de concorrentes a partir dos sites deles: posicionamento, preços, mensagens, lacunas."),
    "competitors": ("comparison_pages", "prepare", "Páginas de comparação e de alternativas (vs/alternativas) para SEO e para quem compra."),
    "cro": ("conversion_optimization", "prepare", "Optimização de conversão de páginas e formulários: diagnóstico, hipóteses e alterações priorizadas."),
    "directory-submissions": ("directory_submissions", "prepare", "Lista e textos para submeter o produto em directórios e sites de reviews; o envio é humano."),
    "emails": ("email_sequences", "prepare", "Sequências de email (boas-vindas, nurture, lifecycle, reactivação) com copy e calendário."),
    "events": ("events_marketing", "prepare", "Planeia webinars, conferências e eventos (organizar, patrocinar, falar) com metas de pipeline."),
    "free-tools": ("free_tools", "prepare", "Planeia e avalia ferramentas grátis de marketing (calculadoras, geradores) para leads e SEO."),
    "image": ("marketing_images", "prepare", "Briefs e prompts de imagens de marketing (heróis de blog, gráficos sociais, OG) e a sua optimização."),
    "launch": ("launch_plan", "prepare", "Plano de lançamento de produto ou funcionalidade: fases, canais, mensagens e checklist."),
    "lead-magnets": ("lead_magnets", "prepare", "Cria e optimiza lead magnets (guias, templates, checklists) para captar emails."),
    "marketing-council": ("marketing_council", "prepare", "Painel simulado de especialistas que discute uma questão de marketing e converge numa recomendação."),
    "marketing-ideas": ("marketing_ideas", "prepare", "Ideias e estratégias de marketing filtradas pelo estágio, canal e orçamento do negócio."),
    "marketing-loops": ("marketing_loops", "prepare", "Desenha loops recorrentes de marketing que um agente prepara; publicar ou enviar continua humano."),
    "marketing-plan": ("marketing_plan", "prepare", "Plano de marketing completo (objectivos, públicos, canais, orçamento, calendário, métricas)."),
    "marketing-psychology": ("marketing_psychology", "prepare", "Aplica princípios de psicologia e economia comportamental à mensagem, oferta e página, sem manipulação."),
    "offers": ("offer_design", "prepare", "Desenha ou melhora a oferta (o que se vende): valor, bónus, garantias, escassez honesta."),
    "onboarding": ("onboarding_activation", "prepare", "Onboarding e activação pós-registo: primeiro uso, tempo até ao valor, emails e checklists."),
    "paywalls": ("paywalls_upgrades", "prepare", "Paywalls, ecrãs de upgrade e feature gates dentro do produto."),
    "popups": ("popups_overlays", "prepare", "Popups, modais e banners de conversão: gatilhos, oferta, copy e regras de frequência."),
    "pricing": ("pricing_strategy", "prepare", "Decisões de preço, planos e monetização, com hipóteses a validar."),
    "product-marketing": ("product_marketing_context", "prepare", "Documento de contexto de product marketing (produto, público, posicionamento) que as outras skills leem primeiro."),
    "programmatic-seo": ("programmatic_seo", "prepare", "Páginas SEO em escala a partir de templates e dados, com controlo de qualidade e de canibalização."),
    "prospecting": ("prospecting_lists", "prepare", "Define e qualifica listas de prospects B2B (empresas e cargos) dentro do RGPD/LGPD; sem identificação de pessoas."),
    "public-relations": ("public_relations", "prepare", "Relações públicas: ângulos, comunicados, pitch a jornalistas e comunicação de crise."),
    "referrals": ("referral_programs", "prepare", "Programas de referência e afiliados: incentivo, mecânica, regras e medição."),
    "revops": ("revenue_operations", "prepare", "RevOps: ciclo de vida do lead, scoring, routing e passagem marketing → vendas."),
    "sales-enablement": ("sales_enablement", "prepare", "Material de vendas: one-pagers, decks, objecções e guiões de demo."),
    "schema": ("schema_markup", "prepare", "Schema markup e dados estruturados (JSON-LD) para páginas e rich results."),
    "signup": ("signup_flow", "prepare", "Optimiza registo, criação de conta e activação do trial."),
    "site-architecture": ("site_architecture", "prepare", "Arquitectura do site: hierarquia de páginas, navegação, URLs e linkagem interna."),
    "sms": ("sms_whatsapp", "prepare", "Marketing por SMS e WhatsApp com opt-in explícito (RGPD/LGPD): fluxos, copy e frequência."),
}

# Notas obrigatórias por skill (política do domínio: offensive forbidden, GOV-IMPACT-1, P-65).
COMPLIANCE = {
    "cold-email": "Conformidade: RGPD + ePrivacy (PT: Lei 41/2004) e LGPD (BR). Só contactos profissionais com interesse legítimo documentado, opt-out em cada mensagem, nada de listas compradas de pessoas. O runner prepara rascunhos; enviar é sempre humano.",
    "prospecting": "Conformidade: RGPD/LGPD. Listas de empresas e cargos, não de pessoas enriquecidas; sem identificação de visitantes a nível de pessoa nem ferramentas de busca de pessoas (GOV-IMPACT-1, P-65). Fontes citadas.",
    "sms": "Conformidade: só para contactos com opt-in explícito e registado (RGPD/LGPD, ePrivacy); horários e frequência limitados; STOP em cada mensagem. O envio é humano.",
    "emails": "Conformidade: só para quem deu consentimento (ou cliente com interesse legítimo); opt-out em cada email.",
    "marketing-loops": "O loop prepara peças e relatórios; publicar, enviar ou gastar media continua a exigir aprovação humana (`plan_approve`).",
    "referrals": "Conformidade: incentivos a reviews têm regras próprias por plataforma e por lei (UE: Directiva Omnibus); confirmar antes de executar.",
}

# Remoções dirigidas: (ficheiro relativo a skills/, texto exacto, substituto).
PATCHES: list[tuple[str, str, str]] = [
    ("launch/references/site-launch-qa.md",
     "; Ploy ◆ promotes a previous deploy from its Deploys screen (its CLI always publishes to production, with no "
     + "staging target, so preview before publishing).",
     "."),
    ("prospecting/references/saas-prospecting.md",
     "via `node tools/clis/github-prospects.js stargazers <owner/repo> --enrich --with-company --format csv`",
     "from each repo's public stargazers/forks list"),
    ("prospecting/references/data-sources.md", "RB2B, Warmly, Vector, Ploy ◆ (sites hosted on Ploy)", "RB2B, Warmly, Vector"),
    ("site-architecture/references/platforms-and-migration.md", "(Ploy ◆, Flint, and similar)", "(Flint and similar)"),
    ("site-architecture/references/platforms-and-migration.md",
     "Some hosted platforms provide the router themselves. Ploy ◆, for example, routes by path prefix in front of your domain (up to 20 rules), so its pages can serve on a subpath while everything else proxies to your existing origin.",
     "Some hosted platforms provide the router themselves, routing by path prefix in front of your domain, so their pages can serve on a subpath while everything else proxies to your existing origin."),
    ("programmatic-seo/references/implementation-platforms.md", "(Ploy ◆ PloyDB, and similar)", "(database-backed builders)"),
    ("ai-seo/references/agent-readiness.md",
     " Ploy ◆, for example, has a Ploybook that inspects the site, defines tool contracts, implements them against "
     + "existing form logic, and validates them. It's a guided workflow, not a hosted MCP server. ◆ marks a "
     + "[Verified Partner](https://github.com/coreyhaines31/marketingskills/blob/main/tools/REGISTRY.md#verified-partners) "
     + "of this repository (disclosure, not endorsement); name an alternative alongside it when you mention it.",
     ""),
]
# Linhas/parágrafos inteiros a remover quando contêm estes marcadores (parceiros pagos).
DROP_LINE = re.compile(
    r"\bPloy\w*|◆|Verified Partner|\bConverly\b|tools/clis/|tools/integrations/[\w-]+\.md|tools/SETUP\.md|\bcomposio\b", re.I
)
# Secções inteiras (do título até ao próximo título do mesmo nível ou a um ---).
DROP_SECTIONS = [
    ("prospecting/references/data-sources.md", "## Built into a site platform (Ploy ◆)"),
    ("ad-creative/SKILL.md", "## Tool Integrations"),  # puxar dados e gerir campanhas pelos CLIs de API
]
# Ligações para tools/ do upstream (guias de API, CLIs, registo): ficam só com o texto.
TOOLS_LINK = re.compile(r"\[([^\]]*)\]\((?:https://github\.com/coreyhaines31/marketingskills/blob/main/|(?:\.\./)+)tools/[^)]*\)")
# Ponteiros que só apontavam para um guia de API e ficaram vazios ("**Integration**: see", "live in .").
DANGLING = re.compile(r"^\s*\*\*Integrations?\*\*:\s*(?:see)?[\s,and]*$|(?:live in|see|consult)\s*[,.]?\s*$")


def _tools_link(m: re.Match[str]) -> str:
    """Uma ligação para tools/ fica só com o texto; um ponteiro para o guia de API (``x.md``) desaparece."""
    text = m.group(1)
    return "" if text.endswith(".md") or text.lower() in ("integration guide", "guide", "setup guide") else text


def _tidy(line: str) -> str:
    line = re.sub(r"\s*\(\s*\)", "", line)  # "(integration guide)" vazio
    line = re.sub(r"(?:,\s*)+(?=[,.]|$)", "", line)  # vírgulas órfãs
    line = re.sub(r"\s+(?:and|,)\s*(?=[.]?$)", "", line)
    if line.lstrip().startswith("|"):
        while re.search(r"\|\s*\|", line):
            line = re.sub(r"\|\s*\|", "| — |", line, count=1)
    return line


FORBIDDEN = re.compile(
    r"\bPloy\w*|◆|Verified Partner|\bConverly\b|tools/clis/|tools/integrations/[\w-]+\.md|tools/SETUP\.md|\bcomposio\b"
    r"|ref=marketingskills",
    re.I,
)


def _git_head(src: Path) -> str:
    out = subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)  # nosec B603 B607
    return out.stdout.strip()


def _drop_section(text: str, title: str) -> str:
    start = text.index(title)
    level = title.split(" ")[0]
    rest = text[start + len(title):]
    m = re.search(rf"\n(?:{re.escape(level)} |---\n\n?)", rest)
    if m is None:
        return text[:start]
    # um `---` que fechava a secção sai com ela (senão ficam duas réguas seguidas)
    end = start + len(title) + (m.end() if m.group(0).startswith("\n---") else m.start() + 1)
    return text[:start] + text[end:]


def clean(rel: str, text: str) -> str:
    for title in [t for f, t in DROP_SECTIONS if f == rel]:
        text = _drop_section(text, title)
    for f, old, new in PATCHES:
        if f == rel:
            if old not in text:
                raise SystemExit(f"upstream mudou: não encontrei o texto a limpar em {rel!r}: {old[:60]!r}")
            text = text.replace(old, new)
    if rel.endswith(".md"):
        out = []
        for line in text.split("\n"):
            if TOOLS_LINK.search(line):  # só as linhas com ligação para tools/ são arrumadas
                line = _tidy(TOOLS_LINK.sub(_tools_link, line))
                if DANGLING.search(line):
                    continue
            if DROP_LINE.search(line):
                continue
            out.append(line)
        text = "\n".join(out)
    if FORBIDDEN.search(text):
        hit = FORBIDDEN.search(text)
        raise SystemExit(f"sobrou um parceiro ou chamada a API em {rel}: {text[max(0, hit.start() - 60):hit.end() + 60]!r}")
    return text


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    end = text.index("\n---\n", 4)
    return text[4:end], text[end + 5:]


def vendor_skills(src: Path) -> dict[str, str]:
    """Copia e limpa as 50 skills; devolve {nome: sha256 do SKILL.md limpo}."""
    if VENDOR.exists():
        shutil.rmtree(VENDOR)
    (VENDOR / "skills").mkdir(parents=True)
    digests: dict[str, str] = {}
    for skill in sorted(p for p in (src / "skills").iterdir() if p.is_dir()):
        for f in sorted(skill.rglob("*")):
            rel = f.relative_to(src / "skills").as_posix()
            if f.is_dir() or "/evals/" in f"/{rel}" or f.is_symlink():
                continue
            out = VENDOR / "skills" / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            if f.suffix not in (".md", ".html", ".csv"):  # texto revisto: templates HTML/CSV sem rede
                raise SystemExit(f"ficheiro inesperado numa skill (só .md/.html/.csv): {rel}")
            out.write_text(clean(rel, f.read_text(encoding="utf-8")), encoding="utf-8")
        digests[skill.name] = hashlib.sha256((VENDOR / "skills" / skill.name / "SKILL.md").read_bytes()).hexdigest()
    shutil.copy(src / "LICENSE", VENDOR / "LICENSE")
    return digests


def registry(src: Path) -> None:
    text = (src / "tools" / "REGISTRY.md").read_text(encoding="utf-8")
    # parceiros, CLIs e o "comece por ler o guia de API": fora
    for title in ("## Verified Partners", "## CLI Tools", "## Quick Start by Use Case"):
        text = _drop_section(text, title)
    text = re.sub(r"\[([^\]]*)\]\((?:integrations/|clis/|SETUP\.md|PARTNERS\.md|\.\./)[^)]*\)", r"\1", text)
    text = re.sub(r"\| [\w.-]+\.md \|", "| — |", text)  # coluna Guide (guias de API)
    skip = ("<!--", "integrations/", "guided setup")
    text = "\n".join(
        line for line in text.split("\n") if not DROP_LINE.search(line) and not any(k in line for k in skip)
    )
    if FORBIDDEN.search(text):
        raise SystemExit("o registo ainda refere parceiros ou guias de API")
    head = (
        "# Registo de ferramentas de marketing\n\n"
        f"> Catálogo de `{UPSTREAM}` (`tools/REGISTRY.md`, MIT), sem parceiros pagos, sem a lista de CLIs e sem\n"
        "> ligações aos guias de API (decisão do maestro, 2026-10-12). Serve para conhecer as opções; ligar uma\n"
        "> ferramenta com chaves é uma decisão à parte. Gerado por `scripts/vendor_marketingskills.py`.\n\n"
    )
    body = text.split("\n", 1)[1] if text.startswith("# ") else text
    out = VENDOR / "tools-registry.md"
    out.write_text(head + body.lstrip(), encoding="utf-8")


def relink(body: str, name: str) -> str:
    """Os links `references/x.md` do upstream passam a apontar para a cópia única em vendor/.

    SKILL-REF-1 (H-01, 2026-10-25, B): a skill do runner fica em skills/marketing/<action>/ e as
    referências só existem em vendor/marketingskills/skills/<name>/references/ (uma cópia, sem duplicar).
    """
    return re.sub(r"\]\((references/[^)\s]+)\)", lambda m: f"](../../../vendor/marketingskills/skills/{name}/{m.group(1)})", body)


def runner_files(commit: str) -> None:
    for name, (cap, _levels, desc) in NEW.items():
        action = name.replace("-", "_")
        src_md = (VENDOR / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        _fm, body = split_frontmatter(src_md)
        body = relink(body, name)
        notes = [
            "Prepara; não publica, não envia e não gasta media (`act_in_production: forbidden`; gate `plan_approve`).",
            "Nunca inventar dados do negócio (preços, clientes, métricas): usar o que vem no plano ou pedir.",
            "O conhecimento abaixo está em inglês; a peça sai na língua do pedido (PT-PT ou PT-BR, conforme o negócio).",
            "Onde o texto manda ler `.agents/product-marketing-context.md`, usar o contexto do plano (e o "
            + "`product_marketing_context`, se existir). As referências citadas estão em "
            + f"`vendor/marketingskills/skills/{name}/references/`.",
        ]
        if name in COMPLIANCE:
            notes.append(COMPLIANCE[name])
        skill_dir = ROOT / "skills" / "marketing" / action
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            f"name: {action}\n"
            f'description: "{desc}"\n'
            f"action: {action}\n"
            "version: 1\n"
            "vertical: marketing\n"
            "priority: P2\n"
            "item_13: false\n"
            f'source: "{UPSTREAM}@{commit[:7]} skills/{name} (MIT)"\n'
            "---\n\n"
            f"# Skill — {action}\n\n"
            f"> Incorporada de [{UPSTREAM}](https://github.com/{UPSTREAM}/tree/{commit}/skills/{name}) (MIT),\n"
            "> sem parceiros pagos nem chamadas a APIs. Gerada por `scripts/vendor_marketingskills.py`: não editar à mão.\n\n"
            "## Contrato do runner (obrigatório)\n\n" + "".join(f"- {n}\n" for n in notes) + "\n"
            "## Conhecimento (upstream)\n\n" + body.lstrip(),
            encoding="utf-8",
        )
        (ROOT / "agents" / "marketing" / f"{action}.agent.md").write_text(
            "---\n"
            f"id: marketing.{action}\n"
            "kind: internal\n"
            f"role: {action}\n"
            f"action: {action}\n"
            f'description: "{desc}"\n'
            f"skill: skills/marketing/{action}/SKILL.md\n"
            "vertical: marketing\n"
            "priority: P2\n"
            "item_13: false\n"
            "version: 1\n"
            "---\n\n"
            f"# Agent — {action} (marketing)\n\n"
            "## Identidade\n\n"
            f"{desc}\n\n"
            "## Skill obrigatória\n\n"
            f"`skills/marketing/{action}/SKILL.md`\n\n"
            "## System (compacto)\n\n"
            f"Tu és `marketing.{action}`. Segue a skill e o contrato do runner que ela abre.\n"
            "Preparas a peça; um humano aprova e publica. Tools: só `tools_allowed`.\n"
            "Sem dados de negócio inventados: o que faltar, pede.\n",
            encoding="utf-8",
        )


def capabilities_block(existing: set[str]) -> str:
    """Bloco gerado; ids que já existem fora dele (ex.: `performance_analysis`) são ligados à mão lá."""
    lines = [BEGIN]
    for name, (cap, levels, desc) in NEW.items():
        if cap in existing:
            continue
        action = name.replace("-", "_")
        lines += [
            f"  - id: {cap}",
            f"    description: {json.dumps(desc, ensure_ascii=False)}",
            f"    levels: [{levels}]",
            f"    action: {action}",
            f"    agent: marketing.{action}",
            f"    skill: skills/marketing/{action}/SKILL.md",
            "    status: partial  # ligada (agente + skill); `implemented` só com um plano que a use",
            "",
        ]
    return "\n".join(lines + [END])


def write_capabilities() -> None:
    path = ROOT / "config" / "marketing-capabilities.yaml"
    text = path.read_text(encoding="utf-8")
    outside = text[: text.index(BEGIN)] + text[text.index(END) + len(END):] if BEGIN in text else text
    block = capabilities_block(set(re.findall(r"^  - id: (\S+)", outside, re.M)))
    if BEGIN in text:
        text = text[: text.index(BEGIN)] + block + text[text.index(END) + len(END):]
    else:
        text = text.rstrip("\n") + "\n\n" + block + "\n"
    path.write_text(text, encoding="utf-8")


def provenance(commit: str, digests: dict[str, str]) -> None:
    rows = "\n".join(
        f"| `{n}` | {'runner: `' + n.replace('-', '_') + '`' if n in NEW else 'já coberta no runner por ' + OVERLAP[n]} | `{d[:12]}` |"
        for n, d in sorted(digests.items())
    )
    (VENDOR / "PROVENANCE.md").write_text(
        "# Proveniência de `vendor/marketingskills/`\n\n"
        "> Gerado por `scripts/vendor_marketingskills.py`. Não editar à mão: correr o script outra vez.\n\n"
        f"- **Origem:** [{UPSTREAM}](https://github.com/{UPSTREAM}) (MIT, ver `LICENSE`)\n"
        f"- **Commit:** `{commit}`\n"
        f"- **Skills:** {len(digests)} (SKILL.md + references/; `evals/` fora)\n"
        "- **Fora (decisão do maestro, 2026-10-12):** tudo o que chama APIs (`tools/clis`, `tools/integrations`,\n"
        "  `tools/composio`, `tools/SETUP.md`) e os parceiros pagos (Converly, Ploy, marcas ◆). As ligações para\n"
        "  `tools/` ficam só com o texto; o catálogo limpo está em `vendor/marketingskills/tools-registry.md`.\n"
        "- **Scan:** `skill-scout scan` no commit acima: as 50 skills `safe`, 0 achados dentro de `skills/`.\n\n"
        "| Skill | No runner | sha256 do SKILL.md limpo (12) |\n|---|---|---|\n" + rows + "\n",
        encoding="utf-8",
    )


def install_script(commit: str) -> None:
    """O comando que o maestro corre (o skill-scout recusa aprovações de agentes de IA).

    Os hashes vêm do próprio skill-scout (``oss/skill-scout``), sobre o conteúdo limpo: se o vendor mudar e
    o script não for regenerado, o hash não bate e nada é instalado (fail-closed).
    """
    sys.path.insert(0, str(ROOT / "oss" / "skill-scout" / "src"))
    from skill_scout.treehash import tree_hash

    lines = [
        "#!/bin/sh",
        "# Instala as 50 skills de marketing (vendor/marketingskills, limpas) no Claude Code do agent-network-mcp.",
        "# Gerado por scripts/vendor_marketingskills.py; não editar à mão.",
        f"# Origem: {UPSTREAM}@{commit} (MIT), sem parceiros pagos nem chamadas a APIs.",
        "#",
        "# Corre TU, no teu terminal: o skill-scout recusa aprovações vindas de um agente de IA.",
        "# Ao correr isto aprovas o conteúdo pelos hashes abaixo (scan `safe` nas 50: ver PROVENANCE.md).",
        "#   pip install -e oss/skill-scout            # uma vez",
        "#   sh scripts/install-marketing-skills.sh ../agent-network-mcp",
        "# Depois, no agent-network-mcp: commit de .claude/skills/, skill-scout.lock.json e skill-scout.audit.jsonl.",
        "set -eu",
        'NAS="$(cd "$(dirname "$0")/.." && pwd)"',
        'ANM="${1:?uso: sh scripts/install-marketing-skills.sh <caminho do agent-network-mcp>}"',
        'cd "$ANM"',
        'one() { skill-scout install "$NAS/vendor/marketingskills/skills/$1" --dest .claude/skills --approve-sha256 "$2"; }',
    ]
    for skill in sorted(p for p in (VENDOR / "skills").iterdir() if p.is_dir()):
        lines.append(f"one {skill.name} {tree_hash(skill).digest}")
    lines += ["skill-scout verify", 'echo "ok: 50 skills de marketing instaladas em $ANM/.claude/skills"', ""]
    out = ROOT / "scripts" / "install-marketing-skills.sh"
    out.write_text("\n".join(lines), encoding="utf-8")
    out.chmod(0o755)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", required=True, type=Path, help="checkout de coreyhaines31/marketingskills")
    ap.add_argument("--commit", required=True, help="commit esperado do checkout (o auditado)")
    args = ap.parse_args(argv)
    head = _git_head(args.src)
    if not head.startswith(args.commit):
        raise SystemExit(f"o checkout está em {head}, não em {args.commit}")
    names = {p.name for p in (args.src / "skills").iterdir() if p.is_dir()}
    if names != set(NEW) | set(OVERLAP):
        raise SystemExit(f"skills novas ou removidas no upstream: {sorted(names ^ (set(NEW) | set(OVERLAP)))}")
    digests = vendor_skills(args.src)
    registry(args.src)
    runner_files(head)
    write_capabilities()
    provenance(head, digests)
    install_script(head)
    print(f"ok: {len(digests)} skills em vendor/, {len(NEW)} actions novas no runner, commit {head[:7]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
