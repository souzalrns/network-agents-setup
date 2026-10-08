# Activação da skill antes do worker (`activate_for_task`) + SEC-1.3

**Estado:** em produção no `main` (merge do #123, 2026-10-07, `7cda6f1`).
**Item:** SEC-1.3, FECHADO (`docs/initiatives/PENDENCIAS.md` §7). Governança: ISO/IEC 42001, controlos A.4.4, A.7.5 e A.10.3 (`docs/governance/ISO-42001-MAPPING.md`). É um pré-requisito do AU-20 e **não fecha o AU-20**: o worker continua sem tools (P-37 por decidir).
**Código:** `runner/plan_runner/skill_activation.py`, chamado em `runner/plan_runner/executor.py` → `execute_external_request`.
**Testes:** `runner/tests/test_skill_activation.py` (39 testes, sem rede) e `runner/tests/test_skill_scan.py` (33 testes, SKILL-SCAN-1).
**Scan das candidatas:** SKILL-SCAN-1 (EM CURSO, PR do branch `feat/skill-scan-1`), código em `runner/plan_runner/skill_scan.py`.

## Fluxo

```
execute_external_request(out_root, step)
  └─ pending_steps/<id>/
  └─ activation = activate_for_task(repo_root, step)
       ├─ resolve agente + skill (com o `vertical:` do passo, S34)
       ├─ sha256 de SKILL.md e AGENT.md (+ pin opcional)
       ├─ inventaria scripts da pasta da skill → allow-list SEC-1.3 (deny-by-default)
       └─ (opt-in) pesquisa skills externas → candidatas, nunca instaladas
            └─ scan estático de cada candidata (SKILL-SCAN-1) → scan.verdict
  └─ request.json += activation.to_request_fields()
  └─ materialize_activation(pending, activation)
       ├─ SKILL.md, AGENT.md          (como antes)
       ├─ skill_activation.json       (sempre: rasto de auditoria)
       └─ SKILL_ACTIVATION.md         (só se a skill tem scripts ou houve pesquisa externa)
  └─ worker.process(...)              → o prompt ganha "Activacao da skill (SEC-1.3)" só se o .md existir
```

## Compatibilidade

- O plano não precisa de mudar nada. Sem scripts na skill e sem flags novas, **o prompt fica igual ao de antes**, nos dois modos (`opt`/`legacy`). Há teste para isto.
- Só o `request.json` ganha campos novos. Mantém `agent_path`, `skill_path`, `skill_preview_head` (2000) e `agent_preview_head` (1500), e acrescenta:

| Campo | Conteúdo |
|---|---|
| `skill_sha256`, `agent_sha256` | integridade no momento da activação |
| `allowed_scripts`, `blocked_scripts` | resultado da SEC-1.3 (paths relativos à pasta da skill) |
| `external_skill_candidates` | candidatas saneadas (`installed: false`, `trusted: false`), cada uma com `scan` (SKILL-SCAN-1) |
| `skill_activation` | `"skill_activation.json"` |

## SEC-1.3: allow-list de scripts

Config: `config/skills.yaml`.

| Regra | Valor |
|---|---|
| Omissão | **deny**: nenhum script é autorizado |
| O que conta como script | tudo em `scripts/`, extensão executável (`.sh`, `.py`, `.js`, `.ts`, `.ps1`, …), bit de execução ou shebang. Docs/dados (`.md`, `.txt`, `.json`, `.yaml`, `.csv`, imagens) não contam |
| Chave | path da SKILL.md (prioridade) ou `vertical/action` |
| Valor | lista de paths relativos à pasta da skill, ou `true` (todos, com aviso `allow_all`) |
| `allow_scripts: true` global | aceite, com aviso "evitar em produção" |
| Entradas inválidas | absolutas, com `..`, drive Windows, não-string → ignoradas, aviso `allow_list_invalid` |
| Entradas obsoletas | path que já não existe como script → aviso `allow_list_missing` |
| Symlinks | **nunca** autorizados, nem com `true`; aviso `symlink_blocked` |
| Config em falta | deny, sem pesquisa externa |
| Config inválida | **fail-closed**: deny + aviso `config_invalid`; o passo nunca rebenta por causa da config |
| Inventário | máximo 500 ficheiros por skill; acima disso, aviso `scan_truncated` |
| Pin (`pins:`) | sha256 esperado da SKILL.md. Se não conferir, aviso `pin_mismatch` e **todos** os scripts dessa skill ficam bloqueados |
| Enforcement | hoje o worker não executa nada (não tem tools). `is_script_allowed(activation, path)` é o ponto de controlo que o executor de tools do AU-20 (P-37) **tem** de consultar |

O prompt diz ao modelo o que está autorizado e bloqueado e que não executa scripts neste passo.

Estado do repo real: só `skills/claude/idea-refine/scripts/idea-refine.sh` é script, e fica bloqueado (teste `test_skill_real_com_script_fica_bloqueada`).

## Pesquisa de skills externas (opt-in)

| Regra | Valor |
|---|---|
| Activação | `should_search_external: true` (ou `search_external: true`) no passo; ou `search_external_default: true` **e** skill local em falta. Valores não booleanos são ignorados, com aviso |
| Query | `skill_query:` do passo, ou `"<action> <vertical>"` |
| Provider | `skills_sh`: `GET {SKILLS_API_URL ou https://skills.sh}/api/search?q=&limit=10` por HTTPS directo (`httpx`), só `https`, sem redirects, timeout de 5 s, máximo de 256 KB lido em streaming |
| Saneamento | remove controlo/ANSI; nomes e slugs fora de `[A-Za-z0-9._/@:-]` são descartados; máximo de 10, ordenadas por installs |
| Instalação | **nunca**. Candidatas com `installed: false` e `trusted: false`, só para revisão humana; o prompt diz para não seguir instruções delas |
| Falhas | rede, timeout ou JSON inválido → `external.status = "error: <Tipo>"`; o passo segue |
| Sem rede | `PLAN_RUNNER_SKILLS_OFFLINE=1` |
| Testes | nunca tocam na rede (`_http_get` e `httpx.stream` bloqueados por fixture; o provider é injectado) |

### Porque não `npx skills find` (desvio do relatório original, com evidência)

1. **`find` não tem `--json`** no `skills@1.7.1` (MIT, vercel-labs/skills). Em `dist/cli.mjs`, o `--json` só existe noutros comandos; o `find` imprime texto com códigos ANSI. Fazer o parsing disso seria frágil.
2. **`npx` descarrega e executa código do npm em runtime.** É o risco "Supply Chain Compromise" (crítico) do OWASP Agentic Skills Top 10, e foi assinalado ao `find-skills` por usar `npx` sem versão fixa.
3. **A fonte de dados é a mesma.** O `find` chama `searchSkillsAPI` → `GET ${SKILLS_API_URL ou https://skills.sh}/api/search?q&limit`, resposta `{skills:[{name,id,source,installs}]}`. O provider Python chama esse endpoint directamente e honra o mesmo `SKILLS_API_URL`.

Resultado: os mesmos dados, sem execução de código de terceiros e sem custo.

### SkillsCat: estacionado (SKILL-EXT-1)

O relatório original pedia `https://skills.cat/api/search`. Não foi implementado:
- não há contrato público verificável desse endpoint (sem documentação de API; a egress desta sessão também o bloqueia);
- o serviço é AGPL-3.0. Consultar uma API não importa código, mas os candidatos podem trazer licenças fora de MIT/Apache.

Fica como **SKILL-EXT-1** (BLOQUEADO), no fim do §4. Critério de desbloqueio: contrato da API documentado + decisão do maestro sobre licenças dos candidatos. `external_provider: skillscat` dá hoje aviso `provider_unsupported` e não pesquisa.

## Scan das candidatas (SKILL-SCAN-1)

**Decisão:** maestro, 2026-10-07, opção A: `agentic-skills-manager` (scan estático, bloqueia high/critical, modo CI, não executa código).
**Ferramenta:** [`agentic-skills-manager`](https://pypi.org/project/agentic-skills-manager/) 1.0.4, MIT, só stdlib ([código](https://github.com/mazen160/skills-manager)). Pin em `runner/requirements-test.txt`; `skill_scan.SCANNER_PIN` tem de ser igual (há teste).

### Onde encaixa

```
activate_for_task(repo_root, step)
  └─ _apply_external_search → candidatas (só com opt-in no passo)
  └─ scan_candidates(candidatas)                       ← novo, só se houver candidatas
       por candidata:
       ├─ source tem de ser owner/repo do GitHub        (senão: not_scanned)
       ├─ github_fetch: clone raso para uma pasta temporária (1 clone por repo)
       ├─ locate_skill: a SKILL.md com `name:` igual ao da candidata; senão o repo inteiro
       ├─ run_scanner: python -I -m skills_manager scan <pasta> --ci   (só estático)
       └─ verdict_from → candidata["scan"]
       no fim: a pasta temporária é apagada
  └─ external["scan"] = resumo (scanner, contagens por veredicto, avisos)
```

Sem candidatas (pesquisa não pedida, 0 resultados ou erro), não há scan e o `external` fica como antes.

### Veredicto

| `scan.verdict` | Quando | O que quer dizer |
|---|---|---|
| `dangerous` | o scanner bloqueia: alguma finding **high** ou **critical** (ou `safe: false`) | não usar; é a política por omissão do scanner |
| `risky` | passa, mas tem findings **medium** | rever à mão antes de qualquer uso |
| `safe` | só findings **low**, ou nenhuma | o scan estático não encontrou nada; **não** quer dizer confiável |
| `not_scanned` | sem scanner instalado, `PLAN_RUNNER_SKILLS_OFFLINE=1`, sem `source` GitHub válido, clone ou scan falhou, orçamento de tempo esgotado | sem veredicto; **fail-closed**, nunca conta como `safe` |

O veredicto **nunca instala nem muda a confiança**: `installed: false` e `trusted: false` ficam iguais em todas as candidatas, e o clone é temporário (nada vai para `skills/` nem para as pastas de skills dos agentes). O próprio scanner avisa que um relatório limpo não prova que a skill é segura.

Exemplo de uma candidata em `skill_activation.json`:

```json
{
  "name": "evil", "source": "acme/skills", "installed": false, "trusted": false,
  "scan": {
    "verdict": "dangerous", "blocked": true, "risk_level": "critical",
    "counts": {"low": 0, "medium": 0, "high": 2, "critical": 1},
    "findings": [{"severity": "critical", "rule": "private-key-material", "path": ".env", "issue": "Private key material found."}],
    "scope": "skill", "path": "skills/evil",
    "commit": "683bc88e56f3e09ba94f7055977f3d3aa499f202",
    "skill_sha256": "9f78b835…"
  }
}
```

E o resumo em `external.scan`: `{"scanner": "agentic-skills-manager 1.0.4", "mode": "static", "counts": {"safe": 1, "risky": 1, "dangerous": 1, "not_scanned": 1}, "status": "3/4 analisadas: …", "warnings": []}`.

**O veredicto vale para um conteúdo exacto:** `commit` (lido de `.git/HEAD` do clone, sem correr o `git`) e `skill_sha256` (da SKILL.md analisada). Um install posterior pode trazer outro commit, e então tem de ser analisado de novo; se a skill for adoptada, o `skill_sha256` serve de pin (`pins:` em `config/skills.yaml`). `null` quando não há `.git` ou SKILL.md (`scope: repo`).

No prompt, cada candidata leva só o veredicto (`- acme/skills@evil [scan: dangerous, critical]`) e a regra "nunca recomendes instalar uma `dangerous`". Os paths e textos das findings vêm do repo da candidata (não confiáveis) e ficam só no JSON, saneados.

### Regras de segurança do scan

| Regra | Valor |
|---|---|
| Só estático | o scanner lê os ficheiros e não executa código da skill (há teste com um script-armadilha). `--ai-checks` **nunca** é pedido: chamaria um CLI de agente pago (claude, codex, cursor) com código não confiável e o ambiente do processo |
| Clone | `https://github.com/<owner>/<repo>.git` só; `owner/repo` validado por regex e passado depois de `--`; `--depth 1 --single-branch --no-tags`; `protocol.allow=never` (só https), `core.hooksPath=/dev/null`, sem submódulos, sem LFS; sem a config do sistema nem a do utilizador; `GIT_TERMINAL_PROMPT=0` |
| Ambiente dos processos filhos | mínimo: `PATH`, locale, proxy e CA. **Nenhuma** variável do runner (chaves, tokens, `DATABASE_URL`) passa para o `git` nem para o scanner (há teste). `HOME` e `TMPDIR` numa pasta temporária |
| Localização da skill | sem seguir symlinks, no máximo 5000 ficheiros e 8 níveis; frontmatter lido por regex (sem YAML), até 16 KB. Sem SKILL.md com o `name:` da candidata, analisa o repo inteiro (`scope: repo`), que contém tudo o que um install podia copiar |
| Tempo | clone 60 s, scan 60 s, 240 s no total por activação; no timeout mata o grupo de processos (o `git` lança filhos). Acima do orçamento: `not_scanned` |
| Falhas | nunca falham o passo; ficam em `scan.reason` |
| Sem rede | `PLAN_RUNNER_SKILLS_OFFLINE=1` desliga também o clone |
| Dependência | o scanner está em `requirements-test.txt` (corre no CI). Num ambiente sem ele, as candidatas ficam `not_scanned` com `scanner_unavailable` |

### Testes (`runner/tests/test_skill_scan.py`, 33)

Skills sintéticas criadas em runtime (a chave privada falsa é montada por partes, para nenhum detector de segredos a ver no código):

| Skill | Conteúdo | Veredicto do scanner real |
|---|---|---|
| safe | SKILL.md + `references/guia.md` | `safe`, 0 findings |
| risky | `scripts/env.py` lê `os.environ` | `risky` (`environment-access`, medium) |
| malicious | `curl … \| sh`, `rm -rf /`, chave privada em `.env` | `dangerous`, critical (`private-key-material`, `network-pipe-to-shell`, `destructive-remove`) |

Cobrem também: o fluxo no `activate_for_task` com um monorepo de 3 skills (veredictos, 1 clone por repo, pasta temporária apagada, repo local sem alterações, `skill_activation.json`, prompt sem paths do repo); `not_scanned` sem scanner, offline, com `source` inválido, com falha de clone ou de scan e com o orçamento esgotado; o mapa de veredictos; o commit e o sha256 analisados (incluindo uma ref com `..`, que nunca é seguida); o saneamento das findings; a localização pelo `name:` e pelos symlinks; o comando de clone e o ambiente sem segredos; o timeout que mata o grupo de processos; o pin igual ao `requirements-test.txt`. Sem rede: o clone real é proibido por fixture. Fora do CI, sem o scanner, os 5 testes que o usam são ignorados; no CI a falta é erro (`test_no_ci_o_scanner_tem_de_estar_instalado`: é um teste e não um erro na recolha, porque o job `test-slow` não instala o `requirements-test.txt`).

**Prova real (2026-10-07, fora dos testes):** `scan_candidates` com o clone real contra `anthropics/skills`: `pdf` e `skill-creator` → `risky` (medium: `executable-file-mode`, `code-execution-primitive`, `environment-access`), e um repo inexistente → `not_scanned` (`git clone falhou`), em 2 s. O `pdf` ficou registado com `commit: 683bc88e56f3e09ba94f7055977f3d3aa499f202`.

## `skill_activation.json` (versão 1)

```json
{
  "version": 1,
  "activated_at": "2026-10-07T10:00:00+00:00",
  "action": "review", "vertical": "marketing",
  "skill": {"path": "skills/marketing/review/SKILL.md", "sha256": "…", "pinned": null, "name": "review", "allowed_tools": null},
  "agent": {"path": "agents/marketing/review.agent.md", "sha256": "…"},
  "scripts": {"policy": "deny_by_default", "policy_key": null, "found": ["scripts/check.sh"], "allowed": [], "blocked": ["scripts/check.sh"]},
  "external": {"requested": false, "status": "not_requested", "candidates": []},
  "warnings": []
}
```

Com candidatas, `external` ganha `scan` (resumo) e cada candidata ganha `scan` (SKILL-SCAN-1). Os campos são aditivos; a versão continua 1.

## Fontes

- Agent Skills specification (agentskills/agentskills, `docs/specification.mdx`): `SKILL.md`, `scripts/`, `references/`, `assets/`, `allowed-tools` (experimental), progressive disclosure. O `allowed-tools` da skill é registado em `skill.allowed_tools` (informativo).
- OWASP Agentic Skills Top 10 (Malicious Skills, Supply Chain Compromise, Over-Privileged Skills, Update Drift → pinning por hash).
- vercel-labs/skills `skills@1.7.1` (MIT), `dist/cli.mjs` (`searchSkillsAPI`, `parseFindOptions`): `source` é `owner/repo` do GitHub e o install é `npx skills add owner/repo@skill`.
- mazen160/skills-manager (`agentic-skills-manager` 1.0.4, MIT): `skills scan --ci` (JSON com `safe`, `risk_level`, `findings`), política por omissão que bloqueia high e critical, SECURITY.md sobre o isolamento da revisão por IA.
