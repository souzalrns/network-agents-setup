"""M-006: medição de visibilidade em IA (plan_runner/ai_visibility.py, docs/ops/AI-VISIBILITY.md).

Sem rede: o Gemini é um transporte falso que devolve groundingMetadata como a API real.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from plan_runner import ai_visibility as av

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = REPO_ROOT / "docs/orchestration/marketing/ai-visibility/painel-exemplo.yaml"


def _gemini(answers: dict[str, tuple[str, list[str]]], fail: dict[str, int] | None = None):
    """answers: texto da pergunta (prefixo) -> (resposta, domínios das fontes)."""
    calls = []

    def send(url, headers, body, timeout):
        calls.append({"url": url, "headers": headers, "body": body})
        q = body["contents"][0]["parts"][0]["text"]
        key = next(k for k in answers if q.startswith(k))
        if fail and key in fail:
            return fail[key], {"error": {"code": fail[key]}}
        text, domains = answers[key]
        return 200, {"candidates": [{
            "content": {"parts": [{"text": text}]},
            "groundingMetadata": {
                "webSearchQueries": [q[:30]],
                "groundingChunks": [{"web": {"uri": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/x",
                                             "title": d, "domain": d}} for d in domains],
            },
        }]}

    send.calls = calls
    return send


@pytest.fixture
def panel():
    return av.load_panel(EXAMPLE)


ANSWERS = {
    "Onde posso fazer a revisão": ("A Bicicletas do Rio, em Braga, faz revisões. A Oficina Pedal Norte também.",
                                   ["bicicletas-do-rio.example", "pedal-norte.example"]),
    "Qual é a melhor oficina": ("A Oficina Pedal Norte é a mais referida.", ["pedal-norte.example"]),
    "Quanto custa": ("Entre 40 e 80 euros, segundo várias oficinas.", ["loja.bicicletas-do-rio.example"]),
    "Como preparar": ("Limpa a corrente e verifica os travões.", []),
    "Onde comprar": ("Na roda livre bikes há usadas revistas.", ["outra.example"]),
}


# --------------------------------------------------------------------------- painel e pontuação


def test_painel_de_exemplo_e_valido_e_ficticio(panel):
    assert 1 <= len(panel["perguntas"]) <= av.MAX_QUESTIONS
    for e in [panel["marca"], *panel["concorrentes"]]:
        assert all(d.endswith(".example") for d in e["dominios"])  # domínios reservados, nunca reais


@pytest.mark.parametrize("bad", [
    {"marca": {"nome": "X"}, "perguntas": []},
    {"marca": {"nome": "Loja"}, "perguntas": [{"id": "a", "texto": "pergunta um"}] * 2},
    {"marca": {"nome": "Loja", "dominios": ["https://loja.pt"]}, "perguntas": [{"id": "a", "texto": "pergunta"}]},
    {"marca": {"nome": "Loja"}, "perguntas": [{"id": f"q{i}", "texto": "pergunta"} for i in range(26)]},
])
def test_painel_invalido_recusa(tmp_path, bad):
    path = tmp_path / "p.yaml"
    path.write_text(yaml.safe_dump(bad, allow_unicode=True), encoding="utf-8")
    with pytest.raises(av.VisibilityError):
        av.load_panel(path)


def test_mencao_sem_acentos_nem_maiusculas_e_palavra_inteira():
    e = {"nome": "Roda Livre", "aliases": ["Roda Livre Bikes"]}
    assert av.mentioned(e, "na RODA LIVRE há usadas")
    assert not av.mentioned(e, "a rodalivre.example não conta como nome")
    assert av.mentioned({"nome": "Pedal Ébano"}, "a pedal ebano abriu")


def test_citacao_pelo_dominio_ou_subdominio():
    e = {"nome": "Loja", "dominios": ["loja.example"]}
    assert av.cited(e, ["https://www.loja.example/revisao"]) and av.cited(e, ["blog.loja.example"])
    assert not av.cited(e, ["outraloja.example", "loja.example.falso.pt"])


# --------------------------------------------------------------------------- medir (Gemini)


def test_medir_simula_por_omissao_sem_rede(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    send = _gemini(ANSWERS)
    assert av.main(["medir", str(EXAMPLE), "--out", str(tmp_path)], send=send) == 0
    assert send.calls == [] and not list(tmp_path.iterdir())
    assert "Nada foi enviado" in capsys.readouterr().out


def test_medir_sem_chave_recusa(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert av.main(["medir", str(EXAMPLE), "--out", str(tmp_path), "--run"], send=_gemini(ANSWERS)) == 1


def test_medir_com_grounding_pontua_e_regista(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    send = _gemini(ANSWERS)
    assert av.main(["medir", str(EXAMPLE), "--out", str(tmp_path), "--run", "--model", "gemini-teste"], send=send) == 0
    assert len(send.calls) == 5
    body = send.calls[0]["body"]
    assert body["tools"] == [{"google_search": {}}] and "português de Portugal" in body["contents"][0]["parts"][0]["text"]
    assert "gemini-teste:generateContent" in send.calls[0]["url"]
    med = json.loads(next(tmp_path.glob("medicao-gemini-*.json")).read_text(encoding="utf-8"))
    s = med["resumo"]
    assert (s["medidas"], s["marca"]["mencionada"], s["marca"]["citada"]) == (5, 1, 2)
    assert s["concorrentes"]["Oficina Pedal Norte"] == {"mencionada": 2, "citada": 2, "mencionada_pct": 40.0, "citada_pct": 40.0}
    assert s["concorrentes"]["Roda Livre"]["mencionada"] == 1  # pelo nome alternativo, sem maiúsculas
    assert med["linhas"][0]["pesquisas"]  # as pesquisas que o Gemini fez ficam registadas
    resumo = (tmp_path / "resumo.md").read_text(encoding="utf-8")
    assert "primeira medição" in resumo and "Amostra pequena (5 perguntas)" in resumo
    assert "chave-de-teste" not in "".join(f.read_text(encoding="utf-8") for f in tmp_path.iterdir())


def test_quota_para_e_guarda_o_que_mediu(tmp_path, panel):
    send = _gemini(ANSWERS, fail={"Quanto custa": 429})
    rows = av.score(panel, av.ask_gemini(panel, api_key="k", model="m", send=send))
    assert len(send.calls) == 3  # parou na 3.ª: não insiste nem continua
    assert [r["estado"] for r in rows] == ["medida", "medida", "nao_medida", "nao_medida", "nao_medida"]
    assert "quota" in rows[2]["erro"]
    s = av.summary(panel, rows)
    assert s["medidas"] == 2 and s["marca"]["mencionada_pct"] == 50.0  # percentagem só sobre o medido


# --------------------------------------------------------------------------- importar (qualquer motor, sem API)


def test_importar_respostas_coladas_e_variacao_face_a_anterior(tmp_path, panel, capsys):
    ans = tmp_path / "chatgpt.yaml"
    ans.write_text(yaml.safe_dump([
        {"pergunta": "revisao-braga", "resposta": "Recomendo a Bicicletas do Rio.", "fontes": ["https://bicicletas-do-rio.example/"]},
        {"pergunta": "eletrica-minho", "resposta": "A Pedal Norte.", "fontes": []},
    ], allow_unicode=True), encoding="utf-8")
    out = tmp_path / "medicoes"
    t0 = datetime(2026, 10, 1, tzinfo=UTC)
    first = av.record(panel, av.score(panel, av._load_answers(ans)), engine="chatgpt", out=out, when=t0)
    assert first["resumo"]["medidas"] == 2 and first["resumo"]["perguntas"] == 5
    assert av.main(["importar", str(EXAMPLE), str(ans), "--motor", "chatgpt", "--out", str(out)]) == 2  # 3 por medir
    resumo = (out / "resumo.md").read_text(encoding="utf-8")
    assert "50.0% (+0.0)" in resumo and "primeira medição" not in resumo
    assert len((out / "historico.jsonl").read_text(encoding="utf-8").splitlines()) == 2


def test_importar_motor_invalido_e_respostas_invalidas(tmp_path):
    bad = tmp_path / "r.yaml"
    bad.write_text(yaml.safe_dump([{"pergunta": "x"}]), encoding="utf-8")
    assert av.main(["importar", str(EXAMPLE), str(bad), "--motor", "chatgpt", "--out", str(tmp_path / "o")]) == 1
    assert av.main(["importar", str(EXAMPLE), str(bad), "--motor", "../x", "--out", str(tmp_path / "o")]) == 1


def test_painel_diferente_nao_se_compara(tmp_path, panel):
    out = tmp_path / "m"
    av.record(panel, av.score(panel, {}), engine="claude", out=out)
    other = {**panel, "perguntas": panel["perguntas"][:2]}
    av.record(other, av.score(other, {}), engine="claude", out=out)
    assert "primeira medição deste painel" in (out / "resumo.md").read_text(encoding="utf-8")
