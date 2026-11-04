"""M-006: pacote do publicador -> Postiz (plan_runner/postiz.py, docs/ops/POSTIZ.md).

Um run real do template Social (worker Gemini falso), com o pacote e a compliance escritos antes da
aprovação humana. O Postiz é um transporte falso: nenhum teste toca na rede.
"""
from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
import yaml

from plan_runner import external_worker as ew
from plan_runner import postiz
from plan_runner.engine import resume_run, run_plan
from tests.test_external_worker import FakeGemini

REPO_ROOT = Path(__file__).resolve().parents[2]
SOCIAL = REPO_ROOT / "docs/orchestration/marketing/templates/areas/social.plan.yaml"
KEY = "chave-postiz-secreta-de-teste"
FUTURE = (datetime.now(UTC) + timedelta(days=7)).replace(microsecond=0)
INTEGRATIONS = [
    {"id": "ig-1", "identifier": "instagram", "name": "loja", "disabled": False},
    {"id": "fb-1", "identifier": "facebook", "name": "loja", "disabled": False},
    {"id": "li-1", "identifier": "linkedin", "name": "a", "disabled": False},
    {"id": "li-2", "identifier": "linkedin-page", "name": "b", "disabled": False},
]


def _post(**kw):
    base = {"rede": "instagram", "quando": FUTURE.strftime("%Y-%m-%dT%H:%M:%S"), "fuso": "Europe/Lisbon",
            "legenda": "Revisão de inverno da tua bicicleta, esta semana na loja.", "ficheiros": [],
            "alt": [], "hashtags": ["#bicicleta"], "identificacoes": ["Imagem gerada com IA"], "aprovado": False}
    return {**base, **kw}


class FakePostiz:
    def __init__(self, fail_on_create: int | None = None):
        self.calls: list[tuple[str, str, dict]] = []
        self.creates = 0
        self.fail_on_create = fail_on_create

    def __call__(self, method, url, *, headers, json_body=None, file=None, timeout=30.0):
        assert headers == {"Authorization": KEY}
        self.calls.append((method, url, {"json": json_body, "file": file[0] if file else None}))
        if url.endswith("/integrations"):
            return 200, INTEGRATIONS
        if url.endswith("/upload"):
            return 200, {"id": f"m{len(self.calls)}", "path": f"https://postiz.local/uploads/{file[0]}"}
        self.creates += 1
        if self.fail_on_create == self.creates:
            return 500, {"message": "erro interno"}
        return 200, [{"postId": f"p{self.creates}", "integration": json_body["posts"][0]["integration"]["id"]}]


def _client(fake):
    return postiz.Client("https://postiz.local/api/public/v1", KEY, send=fake)


def _plan(run):
    return {s["action"]: s for s in yaml.safe_load((run / "plan.yaml").read_text(encoding="utf-8"))["steps"]}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    monkeypatch.setenv("PLAN_RUNNER_SKILLS_OFFLINE", "1")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL", "POSTIZ_API_URL", "POSTIZ_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(ew, "httpx_transport", FakeGemini())


@pytest.fixture
def paused(tmp_path, tmp_run_dir):
    """Run do template Social parado no hitl."""
    plan = yaml.safe_load(SOCIAL.read_text(encoding="utf-8"))
    plan["objective"] = "Uma loja de bicicletas fictícia quer mais clientes no inverno."
    path = tmp_path / "plan.yaml"
    path.write_text(yaml.safe_dump(plan, allow_unicode=True), encoding="utf-8")
    status = run_plan(path, mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "paused_human_gate"
    return tmp_run_dir


def _write(run, posts, verdict="aprovado"):
    steps = _plan(run)
    (run / steps["publish_package"]["output_artifact"]).write_text(json.dumps({"posts": posts, "fora": []}), encoding="utf-8")
    (run / steps["compliance_check"]["output_artifact"]).write_text(
        json.dumps({"veredicto": verdict, "verificacoes": [], "rever_por_profissional": False}), encoding="utf-8")


@pytest.fixture
def approved(paused):
    def make(posts, verdict="aprovado", decision="approve"):
        _write(paused, posts, verdict)
        resume_run(paused, decision=decision)
        return paused
    return make


# --------------------------------------------------------------------------- prova exigida


def test_sem_aprovacao_humana_recusa(paused):
    _write(paused, [_post()])
    with pytest.raises(postiz.PostizError, match="não está concluído|sem aprovação"):
        postiz.dispatch(paused)


def test_rejeitado_recusa(approved):
    run = approved([_post()], decision="reject")
    with pytest.raises(postiz.PostizError):
        postiz.dispatch(run)


def test_compliance_bloqueada_recusa(approved):
    run = approved([_post()], verdict="bloqueado")
    with pytest.raises(postiz.PostizError, match="veredicto: aprovado"):
        postiz.dispatch(run)


def test_pacote_alterado_depois_da_aprovacao_recusa(approved):
    run = approved([_post()])
    pkg = run / _plan(run)["publish_package"]["output_artifact"]
    later = datetime.now(UTC).timestamp() + 60
    os.utime(pkg, (later, later))
    with pytest.raises(postiz.PostizError, match="alterado depois da aprovação"):
        postiz.dispatch(run)


def test_pacote_invalido_recusa(approved):
    run = approved([{"rede": "instagram"}])
    with pytest.raises(postiz.PostizError, match="pacote inválido"):
        postiz.dispatch(run)


# --------------------------------------------------------------------------- simulação (omissão)


def test_simula_por_omissao_sem_rede(approved):
    run = approved([_post()])
    report = postiz.dispatch(run)  # sem client: se tentasse a rede, falhava
    assert report["modo"] == "simulacao" and report["contagens"] == {"simulado": 1}
    payload = report["items"][0]["payload"]
    assert payload["type"] == "draft"
    local = FUTURE.replace(tzinfo=ZoneInfo("Europe/Lisbon"))  # `quando` sem offset + `fuso`
    assert payload["date"] == local.astimezone(UTC).isoformat().replace("+00:00", "Z")
    content = payload["posts"][0]["value"][0]["content"]
    assert "#bicicleta" in content and "Imagem gerada com IA" in content  # identificação de IA no texto
    assert json.loads((run / postiz.REPORT).read_text(encoding="utf-8"))["modo"] == "simulacao"
    events = [json.loads(line) for line in (run / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert events[-1]["type"] == "postiz_dispatch" and events[-1]["payload"]["modo"] == "simulacao"


@pytest.mark.parametrize(("post", "motivo"), [
    (_post(quando="2020-01-01T10:00:00Z"), "data no passado"),
    (_post(legenda="Promoção de [[A DEFINIR]]"), "A DEFINIR"),
    (_post(ficheiros=["../../etc/passwd"], alt=["x"]), "fora do run"),
    (_post(ficheiros=["artifacts/00-brief-social.md"], alt=[]), "texto alternativo"),
    (_post(rede="myspace"), "rede não suportada"),
    (_post(quando="2030-01-01T10:00:00", fuso=""), "sem fuso"),
])
def test_post_com_problema_fica_recusado_com_motivo(approved, post, motivo):
    run = approved([post, _post()])
    report = postiz.dispatch(run)
    assert report["items"][0]["estado"] == "recusado" and motivo in report["items"][0]["motivo"]
    assert report["items"][1]["estado"] == "simulado"  # o resto do pacote segue
    assert postiz.main([str(run)]) == 2  # a CLI assinala a recusa


# --------------------------------------------------------------------------- envio


def test_envia_rascunhos_com_ficheiros_e_integracao_certa(approved):
    run = approved([_post(ficheiros=["artifacts/00-brief-social.md"], alt=["Bicicleta na oficina"]),
                    _post(rede="Facebook")])
    fake = FakePostiz()
    report = postiz.dispatch(run, send=True, client=_client(fake))
    assert report["modo"] == "rascunho" and report["contagens"] == {"enviado": 2}
    creates = [c for c in fake.calls if c[1].endswith("/posts")]
    assert [c[2]["json"]["type"] for c in creates] == ["draft", "draft"]
    first = creates[0][2]["json"]["posts"][0]
    assert first["integration"] == {"id": "ig-1"} and first["settings"]["__type"] == "instagram"
    assert first["value"][0]["image"][0]["path"].startswith("https://postiz.local/uploads/")
    assert creates[1][2]["json"]["posts"][0]["integration"] == {"id": "fb-1"}


def test_agenda_so_com_schedule_e_nunca_publica_ja(approved):
    run = approved([_post()])
    fake = FakePostiz()
    postiz.dispatch(run, send=True, schedule=True, client=_client(fake))
    types = {c[2]["json"]["type"] for c in fake.calls if c[1].endswith("/posts")}
    assert types == {"schedule"}
    assert '"now"' not in Path(postiz.__file__).read_text(encoding="utf-8")  # publicar já não existe no código


def test_integracao_ambigua_recusa_e_override_resolve(approved):
    run = approved([_post(rede="linkedin")])
    report = postiz.dispatch(run, send=True, client=_client(FakePostiz()))
    assert report["items"][0]["estado"] == "recusado" and "--integration linkedin=" in report["items"][0]["motivo"]
    report = postiz.dispatch(run, send=True, overrides={"linkedin": "li-2"}, client=_client(FakePostiz()))
    assert report["items"][0]["estado"] == "enviado" and report["items"][0]["integracao"] == "li-2"


def test_idempotente_nao_reenvia(approved):
    run = approved([_post(), _post(rede="facebook")])
    postiz.dispatch(run, send=True, client=_client(FakePostiz()))
    again = FakePostiz()
    report = postiz.dispatch(run, send=True, client=_client(again))
    assert report["contagens"] == {"ja_enviado": 2} and again.creates == 0


def test_erro_a_meio_guarda_o_que_saiu_e_retoma_so_o_resto(approved):
    run = approved([_post(), _post(rede="facebook"), _post(legenda="Terceiro post da semana.")])
    report = postiz.dispatch(run, send=True, client=_client(FakePostiz(fail_on_create=2)))
    assert [i["estado"] for i in report["items"]] == ["enviado", "erro", "nao_enviado"]
    retry = FakePostiz()
    report = postiz.dispatch(run, send=True, client=_client(retry))
    assert [i["estado"] for i in report["items"]] == ["ja_enviado", "enviado", "enviado"] and retry.creates == 2


def test_send_sem_credenciais_recusa_e_chave_nunca_fica_escrita(approved, monkeypatch):
    run = approved([_post()])
    with pytest.raises(postiz.PostizError, match="POSTIZ_API_URL e POSTIZ_API_KEY"):
        postiz.dispatch(run, send=True)
    postiz.dispatch(run, send=True, client=_client(FakePostiz()))
    for f in run.rglob("*"):
        if f.is_file():
            assert KEY not in f.read_text(encoding="utf-8", errors="ignore"), f


def test_cli_schedule_exige_send(approved, capsys):
    run = approved([_post()])
    with pytest.raises(SystemExit):
        postiz.main([str(run), "--schedule"])
    assert postiz.main([str(run)]) == 0
    assert "simulado" in capsys.readouterr().out


# --------------------------------------------------------------------------- contrato do Postiz (CreatePostDto)


def test_conteudo_em_html_com_quebras_e_escape(approved):
    run = approved([_post(legenda="Linha 1 <b>\nLinha 2 & mais", hashtags=[], identificacoes=[])])
    content = postiz.dispatch(run)["items"][0]["payload"]["posts"][0]["value"][0]["content"]
    assert content == "<p>Linha 1 &lt;b&gt;</p><p>Linha 2 &amp; mais</p>"


def test_settings_por_rede(approved):
    run = approved([
        _post(),  # instagram: post_type por omissão
        _post(rede="youtube"),  # youtube sem title/type: recusado
        _post(rede="tiktok", settings={"privacy_level": "PUBLIC_TO_EVERYONE", "title": "Revisão"}),
    ])
    items = postiz.dispatch(run)["items"]
    assert items[0]["payload"]["posts"][0]["settings"] == {"post_type": "post", "__type": "instagram"}
    assert items[1]["estado"] == "recusado" and "title, type" in items[1]["motivo"]
    tk = items[2]["payload"]["posts"][0]["settings"]
    assert tk["content_posting_method"] == "DIRECT_POST" and tk["video_made_with_ai"] is True  # rótulo de IA do pacote
    assert tk["__type"] == "tiktok"


def test_alt_segue_cada_ficheiro_para_o_postiz(approved):
    run = approved([_post(ficheiros=["artifacts/00-brief-social.md"], alt={"00-brief-social.md": "Bicicleta na oficina"})])
    fake = FakePostiz()
    postiz.dispatch(run, send=True, client=_client(fake))
    image = next(c for c in fake.calls if c[1].endswith("/posts"))[2]["json"]["posts"][0]["value"][0]["image"][0]
    assert image["alt"] == "Bicicleta na oficina" and image["id"] and image["path"]
