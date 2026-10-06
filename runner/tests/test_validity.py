"""F3b, validade (P-27 = C, P-28 = C, P-29 = A): política, classes, TTL e relatório. Sem BD."""

from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from plan_runner.provenance import ProvenanceError
from plan_runner.validity import (
    EVERGREEN,
    apply_validity,
    classify,
    load_policy,
    validity_state,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = REPO_ROOT / "config/knowledge-validity.yaml"
AT = datetime(2026, 10, 6, 12, tzinfo=UTC)


@pytest.fixture(scope="module")
def policy():
    return load_policy(POLICY_PATH)


def _web(**extra):
    return {
        "uri": "https://exemplo.pt/pagina",
        "title": "Página",
        "document_type": "html",
        "retrieved_at": datetime(2026, 9, 1, tzinfo=UTC),
        "status": "active",
        **extra,
    }


# --- política -------------------------------------------------------------------------------


def test_politica_do_repo_tem_as_3_classes_decididas(policy):
    assert [c.id for c in policy.classes] == ["legal", "market_data", "web"]
    assert policy.by_id("legal").require == ("effective_from",)
    assert policy.by_id("market_data").require == ("effective_until",)
    assert policy.by_id("web").ttl_days == 90 and not policy.by_id("web").require
    assert policy.expiring_within_days == 30


@pytest.mark.parametrize(
    ("yaml_text", "erro"),
    [
        ("version: 2\nclasses: []\n", "version"),
        ("version: 1\nclasses:\n  - id: a\n    paths: [x]\n    require: [retrieved_at]\n", "require"),
        ("version: 1\nclasses:\n  - id: a\n    paths: [x]\n    ttl_days: 0\n", "ttl_days"),
        ("version: 1\nclasses:\n  - id: a\n    paths: [x]\n    ttl_days: true\n", "ttl_days"),
        ("version: 1\nclasses:\n  - id: a\n    require: [effective_from]\n", "paths ou uri_schemes"),
        ("version: 1\nclasses:\n  - id: a\n    paths: [x]\n", "require ou ttl_days"),
        ("version: 1\nclasses:\n  - id: evergreen\n    paths: [x]\n    ttl_days: 1\n", "reservado"),
        (
            "version: 1\nclasses:\n  - {id: a, paths: [x], ttl_days: 1}\n  - {id: a, paths: [y], ttl_days: 1}\n",
            "repetidos",
        ),
    ],
)
def test_politica_mal_formada_da_erro_claro(tmp_path, yaml_text, erro):
    path = tmp_path / "v.yaml"
    path.write_text(yaml_text, encoding="utf-8")
    with pytest.raises(ValueError, match=erro):
        load_policy(path)


# --- classes --------------------------------------------------------------------------------


def test_classe_por_path_por_esquema_e_por_override(policy):
    assert classify(policy, "docs/knowledge/legal/direito-br-pt.md", None).id == "legal"
    assert classify(policy, "docs/knowledge/imobiliario/fipezap.md", None).id == "market_data"
    assert classify(policy, "docs/knowledge/ingested/pagina.md", _web()).id == "web"
    assert classify(policy, "docs/knowledge/copywriter.md", None) is None  # playbook: evergreen
    lei = {"uri": "external:lei.pdf", "validity_class": "legal"}
    assert classify(policy, "docs/knowledge/ingested/lei.md", lei).id == "legal"
    assert classify(policy, "docs/knowledge/legal/x.md", {"validity_class": EVERGREEN}) is None


def test_override_desconhecido_e_recusado(policy):
    with pytest.raises(ProvenanceError, match="desconhecida"):
        classify(policy, "docs/knowledge/x.md", {"validity_class": "lei"})


# --- aplicar a validade ---------------------------------------------------------------------


def test_playbook_sem_data_nao_muda_nada(policy):
    assert apply_validity(policy, "docs/knowledge/copywriter.md", None) == (None, [])
    meta = {"uri": "external:a.pdf", "status": "active"}
    assert apply_validity(policy, "docs/knowledge/ingested/a.md", meta) == (meta, [])


def test_classe_datada_sem_sidecar_so_avisa(policy):
    meta, warnings = apply_validity(policy, "docs/knowledge/legal/direito-br-pt.md", None)
    assert meta is None
    assert len(warnings) == 1 and warnings[0].startswith("VALIDITY_MISSING") and "legal" in warnings[0]


def test_classe_datada_com_sidecar_sem_data_e_recusada(policy):
    with pytest.raises(ProvenanceError, match="effective_from"):
        apply_validity(policy, "docs/knowledge/legal/lei.md", {"uri": "external:lei.pdf"})
    with pytest.raises(ProvenanceError, match="effective_until"):
        apply_validity(policy, "docs/knowledge/imobiliario/indice.md", {"uri": "external:i.pdf"})


def test_classe_datada_com_a_data_passa(policy):
    meta = {"uri": "external:lei.pdf", "effective_from": date(2024, 1, 1)}
    assert apply_validity(policy, "docs/knowledge/legal/lei.md", meta) == (meta, [])


def test_web_ganha_ttl_de_90_dias_desde_o_retrieved_at(policy):
    meta, warnings = apply_validity(policy, "docs/knowledge/ingested/p.md", _web())
    assert warnings == []
    assert meta["effective_until"] == datetime(2026, 9, 1, tzinfo=UTC) + timedelta(days=90)
    assert meta["effective_until_source"] == "ttl:90d"


def test_web_com_data_do_autor_mantem_a_do_autor(policy):
    fim = datetime(2027, 1, 1, tzinfo=UTC)
    meta, _ = apply_validity(policy, "docs/knowledge/ingested/p.md", _web(effective_until=fim))
    assert meta["effective_until"] == fim and "effective_until_source" not in meta


def test_ttl_e_estavel_entre_corridas(policy):
    """O mesmo sidecar dá sempre a mesma data: o ingest não faz META_UPDATED à toa."""
    a, _ = apply_validity(policy, "docs/knowledge/ingested/p.md", _web())
    b, _ = apply_validity(policy, "docs/knowledge/ingested/p.md", _web())
    assert a == b


# --- estado (relatório) ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("rel", "meta", "estado"),
    [
        ("docs/knowledge/copywriter.md", None, "sem_data"),
        ("docs/knowledge/legal/x.md", None, "falta_data"),
        ("docs/knowledge/legal/x.md", {"uri": "e:x"}, "sidecar_invalido"),
        ("docs/knowledge/legal/x.md", {"uri": "e:x", "effective_from": date(2027, 1, 1)}, "ainda_nao_vigora"),
        ("docs/knowledge/legal/x.md", {"uri": "e:x", "effective_from": date(2020, 1, 1)}, "valido"),
        ("docs/knowledge/imobiliario/x.md", {"uri": "e:x", "effective_until": date(2026, 10, 1)}, "expirado"),
        ("docs/knowledge/imobiliario/x.md", {"uri": "e:x", "effective_until": date(2026, 10, 20)}, "a_expirar"),
        ("docs/knowledge/imobiliario/x.md", {"uri": "e:x", "effective_until": date(2027, 6, 1)}, "valido"),
        ("docs/knowledge/legal/x.md", {"uri": "e:x", "effective_from": date(2020, 1, 1), "status": "revoked"}, "revoked"),
    ],
)
def test_estado_num_instante(policy, rel, meta, estado):
    assert validity_state(policy, rel, meta, at=AT)["state"] == estado


def test_web_expira_pelo_ttl(policy):
    velha = _web(retrieved_at=datetime(2026, 6, 1, tzinfo=UTC))
    assert validity_state(policy, "docs/knowledge/ingested/p.md", velha, at=AT)["state"] == "expirado"
    recente = _web(retrieved_at=datetime(2026, 9, 30, tzinfo=UTC))
    assert validity_state(policy, "docs/knowledge/ingested/p.md", recente, at=AT)["state"] == "valido"


# --- scripts/validity_report.py -------------------------------------------------------------


def _report_module():
    spec = importlib.util.spec_from_file_location("validity_report", REPO_ROOT / "scripts/validity_report.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["validity_report"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_relatorio_do_repo_cobre_o_manifest_inteiro():
    rep = _report_module()
    out = rep.collect(REPO_ROOT, AT)
    from scripts.ingest_delta import MANIFEST

    assert [r["source"] for r in out["rows"]] == [p for p, _, _ in MANIFEST]
    assert sum(out["counts"].values()) == len(MANIFEST)
    # as fontes de classe datada estão sempre assinaladas: com data, ou sem ela (falta_data)
    datadas = {r["source"]: r["state"] for r in out["rows"] if r["class"] in ("legal", "market_data")}
    assert set(datadas) == {"docs/knowledge/legal/direito-br-pt.md", "docs/knowledge/imobiliario/fipezap.md"}


def test_relatorio_markdown_e_strict(capsys):
    rep = _report_module()
    md = rep.to_markdown(
        {
            "at": "2026-10-06T12:00:00+00:00",
            "expiring_within_days": 30,
            "counts": {"expirado": 1},
            "rows": [{"source": "docs/a.md", "class": "web", "state": "expirado", "detail": "x | y"}],
        }
    )
    assert "| `docs/a.md` | web | **expirado** |" in md and "x / y" in md
    assert rep.main(["--at", "2026-10-06T12:00:00+00:00"]) == 0
    capsys.readouterr()
