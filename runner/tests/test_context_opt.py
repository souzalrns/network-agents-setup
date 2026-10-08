"""B1-bis: politica de contexto do worker (plan_runner/context_policy.py).

Gemini falso (sem rede). A reducao de tokens e medida com
plan_runner/token_projection.py, calibrado no B1 real.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from plan_runner import context_policy as cp
from plan_runner import external_worker as ew
from plan_runner import token_projection as tp
from plan_runner.engine import resume_run, run_plan

SEO_DEMO = tp.SEO_DEMO


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL", cp.CONTEXT_ENV):
        monkeypatch.delenv(var, raising=False)


class SummaryGemini:
    """Responde como o modelo: artefacto (+ resumo no formato pedido, se `obey`)."""

    def __init__(self, obey: bool = True):
        self.obey = obey
        self.calls: list[dict] = []

    def __call__(self, url, headers, body, timeout):
        system = body["systemInstruction"]["parts"][0]["text"]
        user = body["contents"][0]["parts"][0]["text"]
        step = user.split("- passo: ", 1)[1].split("\n", 1)[0]
        wants_json = body["generationConfig"].get("responseMimeType") == "application/json"
        wants_summary = self.obey and ("`resumo`" in system or cp.SUMMARY_MARKER in system)
        self.calls.append({"step": step, "system": system, "user": user})
        resumo = {"factos": [f"facto de {step} [Fonte: x]"], "keywords": [f"kw-{step}"], "estrutura": ["H2 a", "H2 b"],
                  "tom": ["directo"], "restricoes": ["sem stats inventadas"], "decisoes": [f"decisao de {step}"]}
        if wants_json:
            art = {"step": step, "outline": ["intro", "faq"], "keywords": ["ai findability", "geo"]}
            text = json.dumps({"artifact": art, "resumo": resumo} if wants_summary else art)
        else:
            text = f"# {step}\n\nCorpo completo do {step}, com secções.\n"
            if wants_summary:
                text += f"{cp.SUMMARY_MARKER}\n" + cp.render_summary(resumo)
        return 200, {"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}],
                     "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "totalTokenCount": 15},
                     "modelVersion": "gemini-3.5-flash-lite"}

    def by_step(self, step: str) -> dict:
        return next(c for c in self.calls if c["step"] == step)


@pytest.fixture
def fake(monkeypatch):
    f = SummaryGemini()
    monkeypatch.setattr(ew, "httpx_transport", f)
    return f


def _result(out: Path, step: str) -> dict:
    return json.loads((out / "pending_steps" / step / "result.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# O resumo e gerado (so quando alguem o consome) e escrito ao lado do artefacto
# --------------------------------------------------------------------------

def test_resumo_gerado_na_mesma_chamada_so_onde_e_consumido(tmp_run_dir, fake):
    status = run_plan(SEO_DEMO, mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "paused_human_gate"  # mesmo gate de sempre (HITL intacto)
    assert len(fake.calls) == 4  # nenhuma chamada extra para resumir

    # seo_brief: o critic consome-o como resumo -> pedido na mesma chamada
    assert "`resumo`" in fake.by_step("seo_brief")["system"]
    brief = json.loads((tmp_run_dir / "artifacts/02-seo-brief.json").read_text(encoding="utf-8"))
    assert "resumo" not in brief and brief["step"] == "seo_brief"  # o artefacto fica limpo
    summary = (tmp_run_dir / "artifacts/02-seo-brief.summary.md").read_text(encoding="utf-8")
    assert [line for line in summary.splitlines() if line.startswith("### ")] == [f"### {t}" for _, t in cp.SUMMARY_KEYS]
    assert _result(tmp_run_dir, "seo_brief")["meta"]["context"]["summary"] == "written"

    # research (consumido completo pelo seo_brief) e copy (pin do critic): sem resumo
    for step in ("research", "copy", "critic"):
        assert "`resumo`" not in fake.by_step(step)["system"] and cp.SUMMARY_MARKER not in fake.by_step(step)["system"]
        assert _result(tmp_run_dir, step)["meta"]["context"]["summary"] == "not_needed"
    assert not list((tmp_run_dir / "artifacts").glob("0[13]-*.summary.md"))


def test_resumo_em_markdown_tambem_e_separado_do_artefacto(tmp_path, tmp_run_dir, fake):
    plan = tmp_path / "p.yaml"
    plan.write_text(
        "id: md\nobjective: x\nsteps:\n"
        "  - {id: research, action: research, output_artifact: artifacts/01.md}\n"
        "  - {id: brief, action: internal_brief, depends_on: [research], output_artifact: artifacts/02.md}\n"
        "  - {id: copy, action: copy_social, depends_on: [brief], inputs: [artifacts/01.md, artifacts/02.md],"
        " output_artifact: artifacts/03.md}\n", encoding="utf-8")
    run_plan(plan, mode="external", out_dir=tmp_run_dir, worker="gemini")
    art = (tmp_run_dir / "artifacts/01.md").read_text(encoding="utf-8")
    assert cp.SUMMARY_MARKER not in art and art.startswith("# research")
    assert "### Keywords" in (tmp_run_dir / "artifacts/01.summary.md").read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# A politica escolhe o resumo certo (pin no ultimo input) e nunca resume em cascata
# --------------------------------------------------------------------------

def test_policy_critic_recebe_resumo_do_brief_e_copy_completo(tmp_run_dir, fake):
    run_plan(SEO_DEMO, mode="external", out_dir=tmp_run_dir, worker="gemini")
    critic = fake.by_step("critic")["user"]
    summary = (tmp_run_dir / "artifacts/02-seo-brief.summary.md").read_text(encoding="utf-8")
    assert "## Input (resumo): artifacts/02-seo-brief.json" in critic
    assert summary.strip() in critic  # exactamente o resumo do produtor: nunca resumo de resumo
    assert (tmp_run_dir / "artifacts/03-copy.md").read_text(encoding="utf-8").strip() in critic  # copy completo
    assert '"outline"' not in critic  # o brief completo nao entra
    inputs = _result(tmp_run_dir, "critic")["meta"]["context"]["inputs"]
    assert [(i["path"], i["mode"]) for i in inputs] == [
        ("artifacts/02-seo-brief.json", "summary"), ("artifacts/03-copy.md", "full")]


def test_policy_copy_recebe_brief_completo_em_json_compacto(tmp_run_dir, fake):
    run_plan(SEO_DEMO, mode="external", out_dir=tmp_run_dir, worker="gemini")
    copy = fake.by_step("copy")["user"]
    brief = json.loads((tmp_run_dir / "artifacts/02-seo-brief.json").read_text(encoding="utf-8"))
    assert json.dumps(brief, ensure_ascii=False, separators=(",", ":")) in copy  # tudo, sem indentacao
    assert '\n  "' not in copy


def test_policy_override_no_plano_e_sem_resumo_cai_no_completo(tmp_run_dir, monkeypatch):
    raw = {"steps": [
        {"id": "a", "output_artifact": "a.md"},
        {"id": "b", "inputs": ["a.md", "x.md"], "context": {"full": ["a.md"]}},
        {"id": "c", "inputs": ["a.md", "x.md"]},
    ]}
    assert cp.input_modes(raw, "b", ["a.md", "x.md"]) == {"a.md": "full", "x.md": "full"}
    assert cp.input_modes(raw, "c", ["a.md", "x.md"]) == {"a.md": "summary", "x.md": "full"}
    assert cp.needs_summary(raw, "a", "a.md") is True  # por causa do c
    raw["steps"][2]["context"] = {"full": ["a.md"]}
    assert cp.needs_summary(raw, "a", "a.md") is False

    # o modelo ignora o pedido de resumo -> o consumidor recebe o completo e o meta diz porque
    fake = SummaryGemini(obey=False)
    monkeypatch.setattr(ew, "httpx_transport", fake)
    run_plan(SEO_DEMO, mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert _result(tmp_run_dir, "seo_brief")["meta"]["context"]["summary"] == "missing"
    modes = {i["path"]: i["mode"] for i in _result(tmp_run_dir, "critic")["meta"]["context"]["inputs"]}
    assert modes["artifacts/02-seo-brief.json"] == "full (sem resumo)"


# --------------------------------------------------------------------------
# Prompt-base: grounding por area, frontmatter e seccoes de documentacao
# --------------------------------------------------------------------------

def _prompt_for(tmp_run_dir: Path, action: str, vertical: str, context: str = "opt") -> str:
    plan = tmp_run_dir.parent / f"_{tmp_run_dir.name}_{action}.yaml"
    plan.write_text(f"id: g\nobjective: x\nsteps:\n  - {{id: s, action: {action}, vertical: {vertical}, "
                    f"output_artifact: artifacts/s.md}}\n", encoding="utf-8")
    try:
        run_plan(plan, mode="external", out_dir=tmp_run_dir)  # sem worker: so escreve o pedido
    finally:
        plan.unlink()
    pend = tmp_run_dir / "pending_steps" / "s"
    built = ew.build_prompt_ctx(tmp_run_dir, pend, json.loads((pend / "request.json").read_text()), context=context)
    return built["system"]


def test_grounding_slim_so_em_marketing_docs_research(tmp_run_dir):
    assert "Grounding (versão curta" in _prompt_for(tmp_run_dir, "research", "marketing")


@pytest.mark.parametrize("action, vertical", [("contabilidade", "gestao"), ("security_audit", "meta")])
def test_areas_de_risco_mantem_o_grounding_completo(tmp_run_dir, action, vertical):
    system = _prompt_for(tmp_run_dir, action, vertical)
    assert "Directiva de grounding" in system and "versão curta" not in system


def test_validador_recusa_grounding_slim_em_area_de_risco(tmp_path):
    from plan_runner.areas import validate_areas
    from tests.test_areas import AGENTS, VALID
    from tests.test_areas import _repo as areas_repo

    y = VALID.replace("    agents: [eng.dev]\n", "    agents: [eng.dev]\n    hitl: required\n    grounding: slim\n")
    errors = validate_areas(areas_repo(tmp_path, y, AGENTS))
    assert any("`grounding: slim` não é permitido" in e for e in errors), errors


def test_sem_frontmatter_nem_seccoes_de_documentacao_mas_com_as_de_comportamento(tmp_run_dir):
    system = _prompt_for(tmp_run_dir, "research", "marketing")
    assert "id: marketing.research" not in system and "Papel: Prepara research" in system
    for gone in ("## Memória", "## Handoff", "## Skill obrigatória"):
        assert gone not in system
    assert "## Identidade" in system and "## System (compacto)" in system

    sec_dir = tmp_run_dir.parent / f"{tmp_run_dir.name}_sec"
    try:
        security = _prompt_for(sec_dir, "security_audit", "meta")
    finally:
        import shutil

        shutil.rmtree(sec_dir, ignore_errors=True)
    assert "## Enforcement Note" in security  # proibe accoes ofensivas: nunca sai
    assert "## Trigger" not in security


def test_modo_legacy_repoe_o_prompt_anterior(tmp_run_dir, monkeypatch):
    legacy = _prompt_for(tmp_run_dir, "research", "marketing", context="legacy")
    assert "id: marketing.research" in legacy and "Directiva de grounding" in legacy and "## Memória" in legacy
    monkeypatch.setenv(cp.CONTEXT_ENV, "talvez")
    with pytest.raises(ValueError, match="legacy"):
        cp.context_mode()


def test_drop_doc_sections_nao_corta_seccoes_desconhecidas():
    body = "# T\n\n## Identidade\nfica\n\n## Handoff\nsai\n\n## Regras Novas\nfica tambem\n"
    out, gone = cp.drop_doc_sections(body, "agent")
    assert gone == ["Handoff"] and "fica tambem" in out and "sai" not in out


# --------------------------------------------------------------------------
# Tokens: o critic baixa 30-50% e o total baixa (projeccao calibrada no B1)
# --------------------------------------------------------------------------

# O B1 correu antes do P-45 (as skills de marketing nao tinham `description`): a calibracao e as
# comparacoes legacy vs opt usam essas entradas. O custo do P-45 e medido a parte, abaixo.
B1_INPUTS = ("description",)


@pytest.fixture(scope="module")
def projection():
    return {ctx: {r["step"]: r for r in tp.project(context=ctx, drop_skill_keys=B1_INPUTS)}
            for ctx in ("legacy", "opt")}


@pytest.fixture(scope="module")
def projection_now():
    """Com as skills como estao hoje (com a `description` do P-45)."""
    return {ctx: {r["step"]: r for r in tp.project(context=ctx)} for ctx in ("legacy", "opt")}


def test_legacy_reproduz_o_b1_real(projection):
    total = sum(r["total"] for r in projection["legacy"].values())
    assert abs(total - 13130) / 13130 < 0.02  # calibracao: +-2% do B1 real
    for step, (t_in, _) in tp.B1_REAL.items():
        assert abs(projection["legacy"][step]["tokens_in"] - t_in) / t_in < 0.03


def test_p45_description_nao_custa_tokens_no_modo_opt(projection, projection_now):
    """O modo opt (o de omissao) tira o frontmatter da skill: a `description` nunca chega ao prompt."""
    for step, row in projection["opt"].items():
        assert projection_now["opt"][step]["tokens_in"] == row["tokens_in"], step


def test_p45_custo_no_modo_legacy_e_pequeno_e_conhecido(projection, projection_now):
    """No legacy (prompt antigo byte a byte, so para A/B e rollback) a `description` entra: < 3%."""
    before = sum(r["total"] for r in projection["legacy"].values())
    after = sum(r["total"] for r in projection_now["legacy"].values())
    assert 0 < after - before < before * 0.03, (before, after)


def test_drop_frontmatter_keys_so_mexe_no_frontmatter():
    text = '---\nname: x\ndescription: "a: b"\naction: x\n---\n# x\ndescription: fica no corpo\n'
    assert tp._drop_frontmatter_keys(text, ("description",)) == "---\nname: x\naction: x\n---\n# x\ndescription: fica no corpo\n"
    assert tp._drop_frontmatter_keys("# sem frontmatter\n", ("description",)) == "# sem frontmatter\n"


def test_tokens_in_do_critic_cai_30_a_50_por_cento(projection):
    before, after = projection["legacy"]["critic"]["tokens_in"], projection["opt"]["critic"]["tokens_in"]
    assert 0.30 <= (before - after) / before <= 0.50, (before, after)


def test_total_baixa_e_nenhum_passo_sobe_mais_de_5_por_cento(projection):
    tb = sum(r["total"] for r in projection["legacy"].values())
    ta = sum(r["total"] for r in projection["opt"].values())
    assert ta < tb * 0.88  # >= 12% abaixo
    for step in tp.B1_REAL:  # o seo_brief paga o resumo (+300 out), compensado no critic
        assert projection["opt"][step]["total"] <= projection["legacy"][step]["total"] * 1.05


# --------------------------------------------------------------------------
# Qualidade: o critic e o copy continuam a receber o que precisam; HITL igual
# --------------------------------------------------------------------------

def test_qualidade_critic_tem_checklist_copy_completo_e_resumo_estruturado(tmp_run_dir, fake):
    run_plan(SEO_DEMO, mode="external", out_dir=tmp_run_dir, worker="gemini")
    critic = fake.by_step("critic")
    skill_body = cp.strip_frontmatter((tmp_run_dir / "pending_steps/critic/SKILL.md").read_text(encoding="utf-8"))[1]
    kept, _ = cp.drop_doc_sections(skill_body, "skill")
    assert kept.strip()[:300] in critic["system"]  # a checklist do critic (skill) entra inteira
    for title in ("Keywords", "Estrutura", "Restricoes", "Decisoes"):
        assert f"### {title}" in critic["user"]  # o brief chega em bullets estruturados
    copy = fake.by_step("copy")
    assert "## Input: artifacts/02-seo-brief.json" in copy["user"]  # o copy ve o brief inteiro


def test_hitl_para_nos_mesmos_gates_nos_dois_modos(tmp_run_dir, fake, monkeypatch):
    status = run_plan(SEO_DEMO, mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert (status["state"], status["paused_at_step"]) == ("paused_human_gate", "hitl_publish_decision")
    assert resume_run(tmp_run_dir, decision="approve")["state"] == "done"

    other = tmp_run_dir.parent / f"{tmp_run_dir.name}_legacy"
    monkeypatch.setenv(cp.CONTEXT_ENV, "legacy")
    try:
        legacy = run_plan(SEO_DEMO, mode="external", out_dir=other, worker="gemini")
        assert (legacy["state"], legacy["paused_at_step"]) == ("paused_human_gate", "hitl_publish_decision")
    finally:
        import shutil

        shutil.rmtree(other, ignore_errors=True)


def test_cli_da_projeccao(capsys):
    assert tp.main([]) == 0
    out = capsys.readouterr().out
    assert "| **TOTAL** |" in out and "critic: artifacts/02-seo-brief.json (resumo)" in out
