"""F3b: autoridade das fontes (P-31 = D, P-32 = B, P-33 = B). Sem BD nem rede.

Os testes contra Postgres + pgvector (match_knowledge_v3) estão em test_f3b_authority_db.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from plan_runner import authority as au
from plan_runner.knowledge import CONFLICT_RULE, grounding_block
from plan_runner.provenance import ProvenanceError, default_meta, to_source_columns

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "config" / "knowledge-authority.yaml"
MIGRATION = REPO_ROOT / "scripts" / "migrations" / "f3b_authority_v3.sql"
DIRECTIVE = REPO_ROOT / "agents" / "_shared" / "grounding.directive.md"
SLIM = REPO_ROOT / "agents" / "_shared" / "grounding.slim.md"


def _policy(tmp_path: Path, **overrides) -> au.AuthorityPolicy:
    data = {"version": 1, "levels": list(au.LEVELS), "default": "curado", "rules": [], **overrides}
    path = tmp_path / "authority.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return au.load_policy(path)


# --- config ---------------------------------------------------------------------------------


def test_config_do_repo_e_valido_e_deixa_tudo_curado() -> None:
    policy = au.load_policy(CONFIG)
    assert policy.default == "curado" and policy.rules == ()  # P-32 = B: as 39 fontes de hoje


def test_config_e_sql_tem_os_mesmos_niveis_e_o_mesmo_default() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "COALESCE(s.meta->>'authority', 'curado')" in sql
    assert "IN ('oficial', 'curado', 'experimental')" in sql
    assert "WHEN 'oficial' THEN 3 WHEN 'curado' THEN 2 WHEN 'experimental' THEN 1" in sql
    assert au.LEVELS == ("oficial", "curado", "experimental") and au.SQL_DEFAULT == "curado"


@pytest.mark.parametrize(
    ("overrides", "erro"),
    [
        ({"version": 2}, "version"),
        ({"levels": ["oficial", "curado"]}, "levels"),
        ({"default": "oficial"}, "default"),
        ({"rules": [{"authority": "maxima", "paths": ["x/**"]}]}, "maxima"),
        ({"rules": [{"authority": "oficial"}]}, "paths ou uri_schemes"),
    ],
)
def test_config_mal_formado_da_erro_claro(tmp_path, overrides, erro) -> None:
    with pytest.raises(ValueError, match=erro):
        _policy(tmp_path, **overrides)


# --- autoridade de uma fonte ----------------------------------------------------------------------


def test_regra_por_path_e_por_esquema_do_uri(tmp_path) -> None:
    policy = _policy(
        tmp_path,
        rules=[
            {"authority": "oficial", "paths": ["docs/knowledge/legal/**"]},
            {"authority": "experimental", "uri_schemes": ["https"]},
        ],
    )
    assert au.authority_for(policy, "docs/knowledge/legal/lei.md", None) == "oficial"
    web = {"uri": "https://exemplo.pt/x"}
    assert au.authority_for(policy, "docs/knowledge/ingested/x.md", web) == "experimental"
    assert au.authority_for(policy, "docs/knowledge/marketing/geo.md", None) == "curado"


def test_sidecar_ganha_a_regra(tmp_path) -> None:
    policy = _policy(tmp_path, rules=[{"authority": "experimental", "uri_schemes": ["https"]}])
    meta = {"uri": "https://dre.pt/lei", "authority": "oficial"}
    assert au.authority_for(policy, "docs/knowledge/ingested/lei.md", meta) == "oficial"


def test_autoridade_desconhecida_no_sidecar_e_invalid_meta(tmp_path) -> None:
    with pytest.raises(ProvenanceError, match="authority 'maxima'"):
        au.apply_authority(_policy(tmp_path), "a.md", {"status": "active", "authority": "maxima"})


def test_default_nao_se_grava_e_o_resto_vai_para_o_meta_jsonb(tmp_path) -> None:
    policy = _policy(tmp_path, rules=[{"authority": "oficial", "paths": ["legal/**"]}])
    curado = au.apply_authority(policy, "x.md", {**default_meta("x.md"), "authority": "curado"})
    assert "authority" not in curado  # sem escrita: as fontes de hoje não mudam (P-32 = B)
    assert to_source_columns(curado)["meta"] == {}
    oficial = to_source_columns(au.apply_authority(policy, "legal/l.md", default_meta("legal/l.md")))
    assert oficial["meta"] == {"authority": "oficial"}


def test_superseded_by_exige_status_superseded(tmp_path) -> None:
    policy = _policy(tmp_path)
    ok = au.apply_authority(
        policy, "v1.md", {"status": "superseded", "superseded_by": " docs/knowledge/v2.md "}
    )
    assert ok["superseded_by"] == "docs/knowledge/v2.md"
    assert to_source_columns(ok)["meta"] == {"superseded_by": "docs/knowledge/v2.md"}
    with pytest.raises(ProvenanceError, match="exige status: superseded"):
        au.apply_authority(policy, "v1.md", {"status": "active", "superseded_by": "v2.md"})
    for mau in ("", 3, "x" * 501):
        with pytest.raises(ProvenanceError, match="superseded_by"):
            au.apply_authority(policy, "v1.md", {"status": "superseded", "superseded_by": mau})


# --- ingest_apply ---------------------------------------------------------------------------------


def test_ingest_aplica_a_autoridade_antes_de_gravar(tmp_path, monkeypatch) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "ingest_apply_f3b_auth", REPO_ROOT / "scripts" / "ingest_apply.py"
    )
    ia = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ia)
    monkeypatch.setattr(ia, "ROOT", tmp_path)
    md = tmp_path / "docs" / "knowledge" / "x.md"
    md.parent.mkdir(parents=True)
    md.write_text("# X\n\nTexto.\n", encoding="utf-8")
    md.with_suffix(".meta.yaml").write_text(
        yaml.safe_dump(
            {
                "uri": "external:x.pdf",
                "title": "X",
                "document_type": "pdf",
                "retrieved_at": "2026-10-05T10:00:00+00:00",
                "content_hash": ia.sha256_file(md)[0],
                "status": "active",
                "superseded_by": "docs/knowledge/y.md",
            }
        ),
        encoding="utf-8",
    )
    out = ia.apply_one("docs/knowledge/x.md", "security", "P1", dry_run=True, budget=ia.ChunkBudget(9))
    assert out["action"] == "INVALID_META" and "superseded_by" in out["note"]


# --- bloco do L5 e regra no prompt do worker -------------------------------------------------------


def test_bloco_do_l5_mostra_autoridade_data_e_supersessao() -> None:
    block = grounding_block(
        [
            {
                "content": "Prazo de 30 dias.",
                "citation": {"source": "v1.md", "locator": "l.1-4", "uri": "repo://v1"},
                "metadata": {
                    "authority": "oficial",
                    "retrieved_at": "2026-10-05T10:00:00+00:00",
                    "status": "superseded",
                    "superseded_by": "docs/knowledge/v2.md",
                    "effective_from": "2025-01-01T00:00:00+00:00",
                    "effective_until": "2027-01-01T00:00:00+00:00",
                },
            }
        ]
    )
    assert (
        "[Fonte: v1.md @ l.1-4 | uri: repo://v1; autoridade: oficial; data: 2026-10-05; "
        "estado: superseded; substituída por docs/knowledge/v2.md; em vigor desde 2025-01-01; "
        "válido até 2027-01-01]"
    ) in block


def test_bloco_do_l5_da_v2_continua_igual() -> None:
    hit = {"content": "a", "citation": {"source": "s.md", "locator": "§1", "uri": "repo://s"},
           "metadata": {"status": "active", "authority": None}}
    assert "[Fonte: s.md @ §1 | uri: repo://s]" in grounding_block([hit])


def test_regra_de_conflitos_so_entra_com_2_ou_mais_fontes() -> None:
    um = {"content": "a", "citation": {"source": "a.md"}}
    dois = {"content": "b", "citation": {"source": "b.md"}}
    assert CONFLICT_RULE not in grounding_block([um])  # sem custo quando não pode haver conflito
    block = grounding_block([um, dois])
    assert block.index(CONFLICT_RULE) > block.index("b.md") and block.endswith("[/L5 CONTEXT]")
    for termo in ("substituída por", "oficial > curado > experimental", "mais recente", "HITL"):
        assert termo in CONFLICT_RULE


def test_directivas_de_grounding_nao_mudam() -> None:
    """A regra não vai para a directiva: custaria tokens em todos os agentes, com ou sem L5."""
    for path in (DIRECTIVE, SLIM):
        assert "autoridade" not in path.read_text(encoding="utf-8")
