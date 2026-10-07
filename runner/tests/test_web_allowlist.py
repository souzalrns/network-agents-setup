"""F2-ALLOW-1 (P-25 = A): allowlist do `fetch` por área (config/web-allowlist.yaml).

- o ficheiro real existe, cobre as áreas do config/areas.yaml e passa no E7;
- o validador recusa domínios que não são nomes DNS simples, áreas que não existem e repetidos;
- `resolve_allowlist`: a área dá a política; um `--allow` só a pode estreitar; área vazia ou
  desconhecida não busca nada; sem área, mantém o F2a com o aviso `no_area_allowlist`;
- a CLI do `scripts/web_fetch.py` recusa antes de qualquer pedido de rede.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

from plan_runner import web_allowlist as wa
from plan_runner.areas import load_areas, validate_areas

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_web_fetch():
    spec = importlib.util.spec_from_file_location("web_fetch_allow", REPO_ROOT / "scripts" / "web_fetch.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["web_fetch_allow"] = mod
    spec.loader.exec_module(mod)
    return mod


def _repo(tmp_path: Path, areas: dict) -> Path:
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    (tmp_path / wa.ALLOWLIST_FILE).write_text(yaml.safe_dump({"version": 1, "areas": areas}), encoding="utf-8")
    return tmp_path


# --------------------------------------------------------------------------- o ficheiro real


def test_ficheiro_real_existe_cobre_as_areas_e_passa_no_e7():
    assert (REPO_ROOT / wa.ALLOWLIST_FILE).is_file()
    data = wa.load(REPO_ROOT / wa.ALLOWLIST_FILE)
    assert set(data["areas"]) == {a["id"] for a in load_areas(REPO_ROOT)}
    assert wa.validate(REPO_ROOT, {a["id"] for a in load_areas(REPO_ROOT)}) == []
    assert validate_areas(REPO_ROOT) == []


# --------------------------------------------------------------------------- validação


@pytest.mark.parametrize("domain", ["exemplo.org", "www.exemplo.org", "a-b.co.uk", "xn--bcher-kva.example"])
def test_dominios_validos(domain):
    assert wa.domain_error(domain) is None


@pytest.mark.parametrize("domain, why", [
    ("https://exemplo.org", "esquema"),
    ("exemplo.org/x", "esquema"),
    ("exemplo.org:8080", "porta"),
    ("127.0.0.1", "IP"),
    ("::1", "IP"),
    ("*.exemplo.org", "*"),
    ("Exemplo.org", "minúsculas"),
    (" exemplo.org", "minúsculas"),
    ("localhost", "DNS"),
    ("-mau.org", "DNS"),
    ("", "texto"),
    (7, "texto"),
])
def test_dominios_recusados(domain, why):
    assert why in wa.domain_error(domain)


def test_validador_recusa_area_inexistente_repetidos_e_formas_erradas(tmp_path):
    repo = _repo(tmp_path, {"research": ["exemplo.org", "exemplo.org", "https://x.org"],
                            "inventada": [], "legal": "exemplo.org", "docs": None})
    errors = wa.validate(repo, {"research", "legal", "docs"})
    assert any("`inventada`: não existe" in e for e in errors)
    assert any("`exemplo.org` repetido" in e for e in errors)
    rel = wa.ALLOWLIST_FILE.as_posix()
    assert f"{rel}: área `research`: domínio 'https://x.org' inválido (sem esquema nem caminho (só o domínio))" in errors
    assert any("`legal`: os domínios têm de ser uma lista" in e for e in errors)
    assert not any("`docs`" in e for e in errors)  # `docs:` sem valor = lista vazia
    assert len(errors) == 4


def test_validador_exige_version_e_mapa(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / wa.ALLOWLIST_FILE).write_text(yaml.safe_dump({"areas": ["research"]}), encoding="utf-8")
    errors = wa.validate(tmp_path, {"research"})
    assert any("`version`" in e for e in errors) and any("`areas` tem de ser um mapa" in e for e in errors)
    assert wa.validate(tmp_path / "sem-ficheiro", {"research"}) == []  # mini-repos dos testes


# --------------------------------------------------------------------------- resolve_allowlist


def test_area_da_a_politica_e_allow_so_estreita(tmp_path):
    repo = _repo(tmp_path, {"research": ["exemplo.org", "outro.net"], "legal": []})
    assert wa.resolve_allowlist(repo, "research", None) == (["exemplo.org", "outro.net"], [])
    assert wa.resolve_allowlist(repo, "research", ["www.exemplo.org"]) == (["www.exemplo.org"], [])
    with pytest.raises(wa.AllowlistError, match="mau.org fora da allowlist da área `research`"):
        wa.resolve_allowlist(repo, "research", ["exemplo.org", "mau.org"])
    with pytest.raises(wa.AllowlistError, match="fora da allowlist"):
        wa.resolve_allowlist(repo, "research", ["maliciosoexemplo.org"])  # não é subdomínio
    with pytest.raises(wa.AllowlistError, match="não tem domínios"):
        wa.resolve_allowlist(repo, "legal", ["exemplo.org"])
    with pytest.raises(wa.AllowlistError, match="não está em"):
        wa.resolve_allowlist(repo, "inventada", None)


def test_sem_area_mantem_o_f2a_com_aviso(tmp_path):
    repo = _repo(tmp_path, {"research": []})
    assert wa.resolve_allowlist(repo, None, ["Exemplo.org "]) == (["exemplo.org"], [wa.NO_AREA_WARNING])
    with pytest.raises(wa.AllowlistError, match="nada pode ser buscado"):
        wa.resolve_allowlist(repo, None, [])


# --------------------------------------------------------------------------- CLI do fetch


@pytest.fixture
def wf(monkeypatch):
    mod = _load_web_fetch()
    calls: list = []

    def fake_fetch(url, allowlist, timeout_s, max_bytes):
        calls.append(list(allowlist))
        return {"content": "# ok\n", "source_meta": {"final_url": url}, "warnings": []}

    monkeypatch.setattr(mod, "fetch", fake_fetch)
    mod.calls = calls
    return mod


def test_cli_sem_area_nem_allow_sai_com_2(wf):
    assert wf.main(["https://exemplo.org/"]) == 2 and wf.calls == []


def test_cli_area_vazia_recusa_sem_rede(wf, capsys):
    assert wf.main(["https://exemplo.org/", "--area", "marketing"]) == 1  # no repo real as listas estão vazias
    out = json.loads(capsys.readouterr().out)
    assert out["error"] == "blocked_by_allowlist" and "não tem domínios" in out["message"]
    assert wf.calls == []


def test_cli_area_com_dominios(wf, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(wf, "REPO_ROOT", _repo(tmp_path, {"research": ["exemplo.org"]}))
    assert wf.main(["https://www.exemplo.org/x", "--area", "research"]) == 0
    assert wf.calls == [["exemplo.org"]]
    assert json.loads(capsys.readouterr().out)["warnings"] == []
    assert wf.main(["https://mau.org/", "--area", "research", "--allow", "mau.org"]) == 1
    assert wf.calls == [["exemplo.org"]]  # o 2.º nunca chegou à rede


def test_cli_so_allow_leva_o_aviso(wf, capsys):
    assert wf.main(["https://exemplo.org/", "--allow", "exemplo.org"]) == 0
    assert json.loads(capsys.readouterr().out)["warnings"] == [wa.NO_AREA_WARNING]
