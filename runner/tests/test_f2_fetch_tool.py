"""F2 + F3-ART-1: a tool `fetch_url` no runner e as fontes no result.json de cada passo.

Sem rede: o fetcher é injectado (o `scripts/web_fetch.py` real tem os seus 42 testes com
servidor local em test_web_fetch.py). O que se prova aqui é a política (a área vem do plano,
nunca do modelo) e o caminho da proveniência até ao artefacto.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from plan_runner import artifact_sources as asrc
from plan_runner import tool_executor as te
from plan_runner.knowledge import grounding_block
from plan_runner.plan_schema import plan_errors

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO = REPO_ROOT / "docs/orchestration/marketing/templates/examples/web-research-demo.plan.yaml"


def _page(url, *, allowlist):
    _page.calls.append((url, list(allowlist)))
    return {
        "content": "# Answer-first\n\nResponder primeiro, detalhar depois.",
        "source_meta": {
            "uri": url, "final_url": url + "?v=1", "title": "Guia", "retrieved_at": "2026-10-23T18:00:00+00:00",
            "content_hash": "ab" * 32, "status": "active", "http_status": 200, "content_type": "text/html",
        },
        "warnings": ["redirected"],
    }


def _ctx(tmp_path, area="marketing", fetcher=_page):
    _page.calls = []
    return te.ToolContext(repo_root=REPO_ROOT, out_root=tmp_path, step_id="s", web_area=area, web_fetcher=fetcher)


def _call(url="https://developers.google.com/search/docs"):
    return {"name": "fetch_url", "args": {"url": url}}


def test_fetch_url_com_area_devolve_texto_com_a_fonte_e_regista_a_proveniencia(tmp_path):
    plan = te.plan_tools(["fetch_url"])
    response, record = te.execute_call(_call(), plan, _ctx(tmp_path))
    assert response["ok"] and response["content"].startswith("[Fonte: https://developers.google.com/search/docs?v=1 | Guia")
    assert "provenance" not in response and "sources" not in response  # ficam no registo, não gastam tokens
    (prov,) = record["provenance"]
    assert prov["kind"] == "web" and prov["area"] == "marketing" and prov["content_hash"] == "ab" * 32
    assert record["sources"] == ["https://developers.google.com/search/docs?v=1"]
    (_url, allowlist), = _page.calls
    assert allowlist and all("." in d for d in allowlist)  # a allowlist da área, não uma escolha do modelo


def test_sem_web_area_no_passo_nao_ha_pedido(tmp_path):
    response, _ = te.execute_call(_call(), te.plan_tools(["fetch_url"]), _ctx(tmp_path, area=None))
    assert response["error"] == "no_web_area" and _page.calls == []


def test_area_sem_dominios_recusa_sem_rede(tmp_path):
    response, _ = te.execute_call(_call(), te.plan_tools(["fetch_url"]), _ctx(tmp_path, area="software"))
    assert response["error"] == "blocked_by_allowlist" and _page.calls == []


def test_erro_do_fetch_volta_ao_modelo_com_o_codigo(tmp_path):
    class Recusado(Exception):
        code, detail = "robots_disallowed", "robots.txt proíbe"

    def recusa(url, *, allowlist):
        raise Recusado()

    response, record = te.execute_call(_call(), te.plan_tools(["fetch_url"]), _ctx(tmp_path, fetcher=recusa))
    assert response["error"] == "robots_disallowed" and not record["ok"]


def test_url_que_nao_e_http_e_recusado_na_validacao(tmp_path):
    response, _ = te.execute_call(_call("file:///etc/passwd"), te.plan_tools(["fetch_url"]), _ctx(tmp_path))
    assert response["ok"] is False and _page.calls == []


def test_fontes_do_artefacto_juntam_l5_e_tools_sem_repetir(tmp_path):
    hits = [
        {"content": "x", "citation": {"source": "docs/knowledge/marketing/geo.md", "uri": "repo://geo", "locator": "§2"},
         "metadata": {"status": "active", "document_type": "md", "effective_until": "2027-01-01T00:00:00+00:00"}},
        {"content": "y", "citation": {"source": "docs/knowledge/marketing/geo.md", "uri": "repo://geo", "locator": "§2"}},
    ]
    (tmp_path / asrc.KNOWLEDGE_SOURCES_FILE).write_text(json.dumps(asrc.knowledge_sources(hits, "marketing")))
    _, rec_fetch = te.execute_call(_call(), te.plan_tools(["fetch_url"]), _ctx(tmp_path))
    tools_meta = {"calls": [rec_fetch, {"tool": "read_repo_file", "ok": True, "sources": ["README.md"]},
                            {"tool": "fetch_url", "ok": False, "error": "timeout"}]}
    sources = asrc.collect(tmp_path, tools_meta)
    assert [s["kind"] for s in sources] == ["l5", "web", "tool"]  # o hit repetido do L5 conta uma vez
    assert sources[0]["effective_until"].startswith("2027-01-01") and sources[0]["locator"] == "§2"
    assert sources[1]["final_url"].endswith("?v=1") and sources[1]["tool"] == "fetch_url"
    assert sources[2] == {"kind": "tool", "tool": "read_repo_file", "source": "README.md"}


def test_passo_sem_fontes_diz_lista_vazia(tmp_path):
    assert asrc.collect(tmp_path, None) == []


def test_bloco_do_l5_mostra_uri_estado_e_validade():
    block = grounding_block([{"content": "a", "citation": {"source": "s.md", "locator": "§1", "uri": "repo://s"},
                              "metadata": {"status": "superseded", "effective_until": "2026-12-31T00:00:00+00:00"}}])
    assert "[Fonte: s.md @ §1 | uri: repo://s; estado: superseded; válido até 2026-12-31]" in block


def test_plano_de_demonstracao_e_valido_e_usa_a_tool_com_area():
    raw = yaml.safe_load(DEMO.read_text(encoding="utf-8"))
    assert plan_errors(raw) == []
    step = raw["steps"][0]
    assert step["tools_allowed"] == ["fetch_url"] and step["web_area"] == "marketing" and step["action"] == "research"


def test_repo_root_from_out_sessao_aninhada(tmp_path):
    """O setup_close_runs usa --out pilots/<sessão>/run-x: a raiz tem de ser o repo, não pilots/<sessão>."""
    from plan_runner.skills import repo_root_from_out

    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "web-allowlist.yaml").write_text("version: 1\nareas: {}\n", encoding="utf-8")
    out = tmp_path / "pilots" / "setup-close-x" / "run-f2"
    out.mkdir(parents=True)
    assert repo_root_from_out(out) == tmp_path.resolve()
