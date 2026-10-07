"""F0.7a: golden set do L5 de security (config/l5-golden-security.yaml) e métricas, sem rede.

- o golden set é válido e cada âncora cai em exactamente 1 chunk do pack (chunking real);
- as métricas (hit@1/@3/@k de chunk, hit de fonte, MRR, proveniência) contam o que dizem;
- o bloco `knowledge:` do plano demo de security (F0.5) cumpre o sub-schema `knowledge`
  do Plan.schema.json (o resto desse schema é de outro formato de plano).
A medição real (F0.7b) é `python -m plan_runner.l5_eval run`, com MCP_URL + MCP_API_KEY.
"""
from __future__ import annotations

import json

import jsonschema
import pytest
import yaml

from plan_runner import l5_eval as ev

GOLDEN = ev.REPO_ROOT / ev.GOLDEN_DEFAULT


@pytest.fixture(scope="module")
def golden():
    return ev.load_golden(GOLDEN)


@pytest.fixture(scope="module")
def chunks(golden):
    return ev._local_chunks(golden)


def test_golden_set_tem_10_a_20_casos_unicos_do_pack_security(golden):
    assert golden["kb"] == "security" and golden["source"] == "docs/knowledge/security-agents-stack.md"
    assert 10 <= len(golden["cases"]) <= 20
    assert len({c["id"] for c in golden["cases"]}) == len(golden["cases"])
    assert golden["k"] == 4  # = match_count por omissão do match_knowledge


def test_cada_ancora_cai_em_exactamente_um_chunk_do_pack(golden, chunks):
    assert ev.anchor_errors(golden, chunks) == []


def test_as_perguntas_nao_copiam_a_ancora(golden):
    """Mede procura semântica: a pergunta não pode conter a âncora literal."""
    for case in golden["cases"]:
        assert ev._norm(case["anchor"]) not in ev._norm(case["question"]), case["id"]


def test_validate_cli_passa_offline(capsys):
    assert ev.main(["validate"]) == 0
    assert "0 erros" in capsys.readouterr().out


def test_ancora_ambigua_ou_inexistente_e_erro(golden, chunks):
    bad = dict(golden, cases=[{"id": "x", "question": "q", "anchor": "security"},
                              {"id": "y", "question": "q", "anchor": "texto que nao existe no pack"}])
    errs = ev.anchor_errors(bad, chunks)
    assert len(errs) == 2 and "x:" in errs[0] and "(esperado 1)" in errs[1]


@pytest.mark.parametrize("patch,msg", [
    ({"kb": ""}, "`kb`"), ({"k": 0}, "`k`"), ({"cases": []}, "`cases`"),
    ({"cases": [{"id": "a", "question": "q", "anchor": "x"}, {"id": "a", "question": "q", "anchor": "x"}]}, "repetido"),
    ({"cases": [{"id": "a", "question": "", "anchor": "x"}]}, "`question`"),
])
def test_golden_invalido_e_recusado(tmp_path, golden, patch, msg):
    p = tmp_path / "g.yaml"
    p.write_text(yaml.safe_dump({**golden, **patch}, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ValueError, match=msg):
        ev.load_golden(p)


def _hit(source, content):
    return {"content": content, "citation": {"source": source, "locator": None}}


def test_metricas_contam_rank_de_chunk_fonte_mrr_e_proveniencia(golden):
    g = {**golden, "k": 4, "cases": [
        {"id": "a", "question": "qa", "anchor": "alfa"},
        {"id": "b", "question": "qb", "anchor": "beta"},
        {"id": "c", "question": "qc", "anchor": "gama"},
        {"id": "d", "question": "qd", "anchor": "delta"},
    ]}
    src = g["source"]
    answers = {
        "qa": [_hit(src, "... Alfa  ...")],                                        # chunk rank 1
        "qb": [_hit("outra.md", "beta"), _hit(src, "x"), _hit(src, "o BETA")],    # fonte rank 2, chunk rank 3
        "qc": [_hit(src, "nada"), _hit("", "gama")],                               # fonte sim, chunk não; sem fonte num hit
        "qd": [],                                                                   # sem hits
    }
    asked = []

    def retrieve(kb, q, k):
        asked.append((kb, k))
        return answers[q] + [_hit(src, "extra")] * 5  # o avaliador corta em k

    rep = ev.evaluate(g, retrieve)
    by = {r["id"]: r for r in rep["cases"]}
    assert set(asked) == {("security", 4)}
    assert (by["a"]["chunk_rank"], by["b"]["chunk_rank"], by["c"]["chunk_rank"], by["d"]["chunk_rank"]) == (1, 3, None, None)
    assert (by["b"]["source_rank"], by["c"]["source_rank"]) == (2, 1)
    assert by["c"]["provenance_ok"] is False and by["a"]["provenance_ok"] is True
    assert by["d"]["hits"] == 4  # só a cauda "extra": corta em k
    s = rep["summary"]
    assert s["chunk_hit@1"] == 0.25 and s["chunk_hit@3"] == 0.5 and s["chunk_hit@4"] == 0.5
    assert s["source_hit@4"] == 1.0  # a cauda "extra" é da fonte esperada
    assert s["mrr_chunk"] == round((1 + 1 / 3) / 4, 3)
    assert s["no_hits"] == 0 and s["provenance_ok"] == 0.75


def test_antes_do_f04_sem_pack_ingerido_tudo_falha_e_e_mensuravel(golden):
    """Estado esperado hoje: o pack não está no knowledge_chunks (ingest_delta.py)."""
    rep = ev.evaluate(golden, lambda kb, q, k: [])
    assert rep["summary"]["chunk_hit@4"] == 0.0 and rep["summary"]["no_hits"] == len(golden["cases"])
    assert rep["summary"]["provenance_ok"] is None


def test_run_sem_credenciais_do_mcp_falha_sem_medir(monkeypatch):
    from plan_runner.mcp_knowledge import McpKnowledgeError

    for var in ("MCP_API_KEY", "MCP_URL"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(McpKnowledgeError, match="MCP_API_KEY"):
        ev.main(["run"])


def test_bloco_knowledge_do_plano_security_cumpre_o_sub_schema():
    schema = json.loads((ev.REPO_ROOT / "docs/architecture/plan-execute/schemas/Plan.schema.json")
                        .read_text(encoding="utf-8-sig"))
    sub = schema["properties"]["steps"]["items"]["properties"]["knowledge"]
    plan = yaml.safe_load((ev.REPO_ROOT / "docs/orchestration/security/templates/examples/"
                           "security-audit-demo.plan.yaml").read_text(encoding="utf-8"))
    blocks = {s["id"]: s["knowledge"] for s in plan["steps"] if "knowledge" in s}
    assert list(blocks) == ["audit"] and blocks["audit"]["kb"] == "security"
    jsonschema.validate(instance=blocks["audit"], schema=sub)


# --- R-006: o eval distingue a v1 da v2 (F3a) -------------------------------------------------


def _golden_r006():
    return {"kb": "security", "k": 2, "source": "docs/a.md",
            "cases": [{"id": "x", "question": "q", "anchor": "texto"}]}


@pytest.mark.parametrize(
    ("hit", "v2"),
    [
        ({"content": "texto", "citation": {"source": "docs/a.md", "locator": None}, "metadata": None}, 0.0),
        ({"content": "texto", "citation": {"source": "docs/a.md", "uri": "docs/a.md"},
          "metadata": {"status": "active", "document_type": "md"}}, 1.0),
        ({"content": "texto", "citation": {"source": "docs/a.md"}, "metadata": {"status": "active"}}, 0.0),
    ],
    ids=["v1", "v2", "v2-sem-uri"],
)
def test_provenance_v2_ok_distingue_v1_de_v2(hit, v2):
    rep = ev.evaluate(_golden_r006(), lambda kb, q, k: [hit])
    assert rep["summary"]["provenance_ok"] == 1.0  # o source está sempre lá
    assert rep["summary"]["provenance_v2_ok"] == v2

