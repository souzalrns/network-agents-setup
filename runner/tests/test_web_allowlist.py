"""F2-ALLOW-1 (P-25 = A): allowlist do `fetch` por área (config/web-allowlist.yaml).

- o ficheiro real existe, cobre as áreas do config/areas.yaml, passa no E7 e tem a v1 dos
  domínios do maestro (2026-10-08) tal como dada: `software` vazia, as exclusões de propósito;
- o validador recusa domínios que não são nomes DNS simples, áreas que não existem e repetidos;
- `resolve_allowlist`: a área dá a política; um `--allow` só a pode estreitar; área vazia ou
  desconhecida não busca nada; sem área, recusa (a área é obrigatória desde a v1);
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


# A v1 do maestro (2026-10-08), por área, corrigida pela P-46 = A (2026-10-08). Mudar um domínio =
# decisão + linha no PENDENCIAS §10; este teste apanha uma edição silenciosa do ficheiro.
V1 = {
    "software": [],
    "marketing": ["instagram.com", "tiktok.com", "facebook.com", "linkedin.com", "youtube.com", "x.com",
                  "pinterest.com", "threads.net", "threads.com", "meta.com", "developers.facebook.com", "ads.google.com",
                  "developers.google.com"],
    "legal": ["planalto.gov.br", "in.gov.br", "stf.jus.br", "stj.jus.br", "tst.jus.br", "tse.jus.br",
              "cnj.jus.br", "senado.leg.br", "camara.leg.br", "jusbrasil.com.br", "conjur.com.br", "dre.pt",
              "diariodarepublica.pt", "pgdlisboa.pt", "oa.pt", "justica.gov.pt", "tribunalconstitucional.pt",
              "stj.pt", "eur-lex.europa.eu", "curia.europa.eu"],
    "ops": ["github.com", "docs.github.com", "gitlab.com", "kubernetes.io", "docker.com", "docs.docker.com",
            "helm.sh", "prometheus.io", "grafana.com", "terraform.io", "developer.hashicorp.com", "cloud.google.com", "docs.aws.amazon.com",
            "learn.microsoft.com", "oracle.com", "sentry.io"],
    "research": ["wikipedia.org", "wikidata.org", "arxiv.org", "scholar.google.com", "pubmed.ncbi.nlm.nih.gov",
                 "doi.org", "semanticscholar.org", "ssrn.com", "openalex.org", "crossref.org"],
    "finance": ["bcb.gov.br", "cvm.gov.br", "b3.com.br", "fazenda.gov.br", "ibge.gov.br", "bportugal.pt",
                "cmvm.pt", "ecb.europa.eu", "esma.europa.eu", "sec.gov", "federalreserve.gov", "imf.org",
                "worldbank.org", "oecd.org", "bis.org"],
    "gamedev": ["unity.com", "docs.unity3d.com", "unrealengine.com", "docs.unrealengine.com", "godotengine.org",
                "docs.godotengine.org", "khronos.org", "blender.org", "docs.blender.org", "itch.io",
                "partner.steamgames.com", "gamedeveloper.com"],
    "security": ["owasp.org", "nvd.nist.gov", "cve.mitre.org", "cve.org", "cwe.mitre.org", "attack.mitre.org", "cert.org",
                 "sei.cmu.edu",
                 "first.org", "cisecurity.org", "cisa.gov", "enisa.europa.eu", "osv.dev", "snyk.io"],
    "docs": ["docs.python.org", "python.org", "nodejs.org", "developer.mozilla.org", "typescriptlang.org",
             "pydantic.dev", "fastapi.tiangolo.com", "react.dev", "nextjs.org", "supabase.com", "vercel.com",
             "ai.google.dev", "cloud.google.com", "platform.openai.com", "docs.anthropic.com", "platform.claude.com", "pytest.org",
             "ruff.rs", "docs.astral.sh", "pnpm.io"],
    "horizontal": ["ietf.org", "datatracker.ietf.org", "rfc-editor.org", "w3.org", "schema.org", "openapis.org",
                   "json-schema.org", "github.com"],
}


def test_ficheiro_real_tem_a_v1_do_maestro():
    areas = wa.load(REPO_ROOT / wa.ALLOWLIST_FILE)["areas"]
    assert {a: list(d or []) for a, d in areas.items()} == V1
    assert sum(len(d) for d in V1.values()) == 128  # 122 da v1 + 9 da P-46 - 3 nomes trocados


# P-46 = A: os endereços actuais das mesmas fontes (evidência: a sonda do CI, run 37807283070).
P46_ADDED = {"security": ["cve.org", "sei.cmu.edu"], "ops": ["developer.hashicorp.com"],
             "docs": ["platform.claude.com", "docs.astral.sh"], "marketing": ["threads.com"],
             "legal": ["justica.gov.pt"], "gamedev": ["partner.steamgames.com"], "horizontal": ["openapis.org"]}
P46_REMOVED = {"openapi.org", "justice.gov.pt", "steamworks.steampowered.com"}


def test_p46_aplicada_na_area_da_fonte():
    for area, domains in P46_ADDED.items():
        for d in domains:
            assert wa.resolve_allowlist(REPO_ROOT, area, [d]) == ([d], [])
    assert sum(len(d) for d in P46_ADDED.values()) == 9
    every = {d for ds in V1.values() for d in ds}
    assert not P46_REMOVED & every
    # os 6 que redireccionam ficam (uma página interna pode responder directamente)
    assert {"cve.mitre.org", "cert.org", "terraform.io", "docs.anthropic.com", "ruff.rs", "threads.net"} <= every
    with pytest.raises(wa.AllowlistError, match="fora da allowlist"):
        wa.resolve_allowlist(REPO_ROOT, "marketing", ["business.google.com"])  # ficou de fora da P-46


def test_v1_deny_by_default_e_exclusoes_de_proposito():
    real = REPO_ROOT
    with pytest.raises(wa.AllowlistError, match="não tem domínios"):  # lista vazia = nada
        wa.resolve_allowlist(real, "software", None)
    every = {d for ds in V1.values() for d in ds}
    # as raízes gov.br e jus.br ficam de fora: só os órgãos listados
    assert not {"gov.br", "jus.br", "www.gov.br"} & every
    with pytest.raises(wa.AllowlistError, match="fora da allowlist"):
        wa.resolve_allowlist(real, "finance", ["www.gov.br"])  # fazenda/cvm não abrem o gov.br
    # notícias de finanças fora da v1; reddit e medium, se entrarem, só em marketing
    assert not {"reuters.com", "ft.com", "bloomberg.com"} & every
    assert not {"reddit.com", "medium.com"} & {d for a, ds in V1.items() if a != "marketing" for d in ds}


def test_v1_area_estreita_e_subdominios(tmp_path):
    real = REPO_ROOT
    domains, warnings = wa.resolve_allowlist(real, "research", None)
    assert domains == V1["research"] and warnings == []
    assert wa.resolve_allowlist(real, "research", ["export.arxiv.org"]) == (["export.arxiv.org"], [])
    assert wa.resolve_allowlist(real, "legal", ["www.planalto.gov.br"]) == (["www.planalto.gov.br"], [])
    with pytest.raises(wa.AllowlistError, match="fora da allowlist da área `research`"):
        wa.resolve_allowlist(real, "research", ["github.com"])  # github.com é de ops e horizontal
    with pytest.raises(wa.AllowlistError, match="fora da allowlist"):
        wa.resolve_allowlist(real, "legal", ["stf.jus.br.mau.org"])  # sufixo, não prefixo


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


@pytest.mark.parametrize("area", [None, ""])
def test_sem_area_recusa_mesmo_com_allow(tmp_path, area):
    repo = _repo(tmp_path, {"research": ["exemplo.org"]})
    with pytest.raises(wa.AllowlistError, match="`--area` é obrigatória"):
        wa.resolve_allowlist(repo, area, ["exemplo.org"])
    with pytest.raises(wa.AllowlistError, match="`--area` é obrigatória"):
        wa.resolve_allowlist(repo, area, None)


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
    assert wf.main(["https://exemplo.org/", "--area", "software"]) == 1  # na v1, `software` está vazia
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


def test_cli_so_allow_sai_com_2_sem_rede(wf, capsys):
    assert wf.main(["https://exemplo.org/", "--allow", "exemplo.org"]) == 2
    assert "--area" in capsys.readouterr().err and wf.calls == []


def test_cli_area_real_da_v1(wf, capsys):
    assert wf.main(["https://arxiv.org/abs/2401.00001", "--area", "research"]) == 0
    assert wf.calls == [V1["research"]]
    assert wf.main(["https://arxiv.org/abs/2401.00001", "--area", "research", "--allow", "arxiv.org"]) == 0
    assert wf.calls[-1] == ["arxiv.org"]
