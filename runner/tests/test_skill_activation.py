"""activate_for_task + SEC-1.3 (plan_runner/skill_activation.py). Sem rede: o provider e injectado."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from plan_runner import external_worker as ew
from plan_runner import skill_activation as sa
from plan_runner import skill_scan
from plan_runner.executor import execute_external_request
from plan_runner.models import Step

REPO_ROOT = Path(__file__).resolve().parents[2]
_REAL_HTTP_GET = sa._http_get  # a fixture _no_network substitui o do modulo


def _w(path: Path, text: str = "x", mode: int | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if mode is not None:
        path.chmod(mode)
    return path


def _skill(repo: Path, vertical: str = "marketing", action: str = "review", body: str = "---\nname: review\n---\n# review") -> Path:
    return _w(repo / "skills" / vertical / action / "SKILL.md", body)


def _cfg(repo: Path, text: str) -> None:
    _w(repo / "config" / "skills.yaml", text)


def _step(action: str = "review", **raw) -> Step:
    return Step(id="s1", action=action, raw={"id": "s1", "action": action, **raw})


def _boom(query, limit):  # provider que nao pode ser chamado
    raise AssertionError("pesquisa externa nao devia correr")


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Rede proibida em todos os testes deste ficheiro (o provider real nunca corre)."""
    def deny(*a, **k):
        raise AssertionError("rede proibida nos testes")
    monkeypatch.setattr(sa, "_http_get", deny)
    monkeypatch.setattr(sa.httpx, "stream", deny)
    monkeypatch.setattr(skill_scan, "github_fetch", lambda *a, **k: pytest.fail("clone real proibido nos testes"))
    monkeypatch.delenv(sa.OFFLINE_ENV, raising=False)
    monkeypatch.delenv(sa.SKILLS_API_ENV, raising=False)


# --------------------------------------------------------------------------- resolucao + integridade


def test_resolve_skill_e_agente_com_sha256(tmp_path):
    skill = _skill(tmp_path)
    agent = _w(tmp_path / "agents" / "marketing" / "review.agent.md", "---\nid: rev\n---\n# agente")
    act = sa.activate_for_task(tmp_path, _step(), search=_boom)
    assert act.skill_rel == "skills/marketing/review/SKILL.md"
    assert act.agent_rel == "agents/marketing/review.agent.md"
    assert len(act.skill_sha256) == 64 and act.skill_sha256 != act.agent_sha256
    assert act.skill_name == "review"
    assert act.scripts_found == [] and act.prompt_block() == ""
    assert act.external["status"] == "not_requested"
    assert skill.is_file() and agent.is_file()


def test_vertical_do_passo_e_respeitado_s34(tmp_path):
    _skill(tmp_path, "design", "ux_flow")
    act = sa.activate_for_task(tmp_path, _step("ux_flow", vertical="design"), search=_boom)
    assert act.skill_rel == "skills/design/ux_flow/SKILL.md"
    assert sa.activate_for_task(tmp_path, _step("ux_flow"), search=_boom).skill_rel is None


def test_sem_skill_nem_agente_nao_rebenta(tmp_path):
    act = sa.activate_for_task(tmp_path, _step("nao_existe"), search=_boom)
    assert act.skill_path is None and act.agent_path is None and act.skill_sha256 is None
    assert act.to_request_fields()["allowed_scripts"] == []


# --------------------------------------------------------------------------- SEC-1.3


def test_scripts_bloqueados_por_omissao_sem_config(tmp_path):
    _skill(tmp_path)
    _w(tmp_path / "skills/marketing/review/scripts/check.sh", "#!/bin/sh\necho ok")
    _w(tmp_path / "skills/marketing/review/tool.py", "print(1)")
    _w(tmp_path / "skills/marketing/review/references/guia.md", "# doc")
    _w(tmp_path / "skills/marketing/review/scripts/README.md", "# doc dos scripts")
    act = sa.activate_for_task(tmp_path, _step(), search=_boom)
    assert act.scripts_found == ["scripts/check.sh", "tool.py"]
    assert act.allowed_scripts == [] and act.blocked_scripts == ["scripts/check.sh", "tool.py"]
    assert not sa.is_script_allowed(act, "scripts/check.sh")
    block = act.prompt_block()
    assert "autorizados: nenhum" in block and "bloqueado: scripts/check.sh" in block


def test_shebang_e_bit_de_execucao_contam_como_script(tmp_path):
    _skill(tmp_path)
    _w(tmp_path / "skills/marketing/review/run", "#!/usr/bin/env python3\n")
    _w(tmp_path / "skills/marketing/review/bin/tool", "binario", mode=0o755)
    _w(tmp_path / "skills/marketing/review/dados.csv", "a,b")
    act = sa.activate_for_task(tmp_path, _step(), search=_boom)
    assert act.scripts_found == ["bin/tool", "run"]


def test_allow_list_por_vertical_action(tmp_path):
    _skill(tmp_path)
    _w(tmp_path / "skills/marketing/review/scripts/check.sh", "#!/bin/sh")
    _w(tmp_path / "skills/marketing/review/scripts/rm.sh", "#!/bin/sh")
    _cfg(tmp_path, "allow_scripts:\n  marketing/review:\n    - scripts/check.sh\n")
    act = sa.activate_for_task(tmp_path, _step(), search=_boom)
    assert act.policy_key == "marketing/review"
    assert act.allowed_scripts == ["scripts/check.sh"] and act.blocked_scripts == ["scripts/rm.sh"]
    assert sa.is_script_allowed(act, "scripts/check.sh")
    assert sa.is_script_allowed(act, "./scripts/check.sh")
    assert not sa.is_script_allowed(act, "scripts/rm.sh")
    assert not sa.is_script_allowed(act, "../review/scripts/check.sh")


def test_chave_por_path_da_skill_tem_prioridade(tmp_path):
    _skill(tmp_path)
    _w(tmp_path / "skills/marketing/review/scripts/a.sh", "#!/bin/sh")
    _w(tmp_path / "skills/marketing/review/scripts/b.sh", "#!/bin/sh")
    _cfg(tmp_path, "allow_scripts:\n  marketing/review: [scripts/a.sh]\n  skills/marketing/review/SKILL.md: [scripts/b.sh]\n")
    act = sa.activate_for_task(tmp_path, _step(), search=_boom)
    assert act.policy_key == "skills/marketing/review/SKILL.md" and act.allowed_scripts == ["scripts/b.sh"]


@pytest.mark.parametrize("entry", ["/etc/passwd", "../outra/scripts/x.sh", "C:\\\\x.bat", 42])
def test_entradas_invalidas_na_allow_list_sao_ignoradas_com_aviso(tmp_path, entry):
    _skill(tmp_path)
    _w(tmp_path / "skills/marketing/review/scripts/a.sh", "#!/bin/sh")
    _cfg(tmp_path, f"allow_scripts:\n  marketing/review:\n    - {json.dumps(entry)}\n")
    act = sa.activate_for_task(tmp_path, _step(), search=_boom)
    assert act.allowed_scripts == [] and any(w.startswith("allow_list_invalid") for w in act.warnings)


def test_entrada_que_nao_existe_gera_aviso_de_config_obsoleta(tmp_path):
    _skill(tmp_path)
    _w(tmp_path / "skills/marketing/review/scripts/a.sh", "#!/bin/sh")
    _cfg(tmp_path, "allow_scripts:\n  marketing/review: [scripts/sumiu.sh]\n")
    act = sa.activate_for_task(tmp_path, _step(), search=_boom)
    assert act.allowed_scripts == [] and any("allow_list_missing: scripts/sumiu.sh" in w for w in act.warnings)


def test_true_por_skill_e_global_autorizam_com_aviso(tmp_path):
    _skill(tmp_path)
    _w(tmp_path / "skills/marketing/review/scripts/a.sh", "#!/bin/sh")
    _cfg(tmp_path, "allow_scripts:\n  marketing/review: true\n")
    act = sa.activate_for_task(tmp_path, _step(), search=_boom)
    assert act.allowed_scripts == ["scripts/a.sh"] and any(w.startswith("allow_all") for w in act.warnings)
    _cfg(tmp_path, "allow_scripts: true\n")
    act = sa.activate_for_task(tmp_path, _step(), search=_boom)
    assert act.policy_key == "*" and act.allowed_scripts == ["scripts/a.sh"]
    assert any("global" in w for w in act.warnings)


@pytest.mark.parametrize("text", ["allow_scripts: [", "- lista\n- na raiz\n", "allow_scripts: 7\n", "allow_scripts:\n  marketing/review: sim\n"])
def test_config_invalida_falha_fechado(tmp_path, text):
    _skill(tmp_path)
    _w(tmp_path / "skills/marketing/review/scripts/a.sh", "#!/bin/sh")
    _cfg(tmp_path, text)
    act = sa.activate_for_task(tmp_path, _step(), search=_boom)
    assert act.allowed_scripts == [] and act.blocked_scripts == ["scripts/a.sh"]
    assert any("invalid" in w for w in act.warnings)


@pytest.mark.skipif(os.name == "nt", reason="symlinks")
def test_symlink_nunca_e_autorizado(tmp_path):
    _skill(tmp_path)
    secret = _w(tmp_path / "fora" / "segredo.sh", "#!/bin/sh")
    link = tmp_path / "skills/marketing/review/scripts/link.sh"
    link.parent.mkdir(parents=True)
    link.symlink_to(secret)
    (tmp_path / "skills/marketing/review/dir_link").symlink_to(tmp_path / "fora", target_is_directory=True)
    _cfg(tmp_path, "allow_scripts: true\n")
    act = sa.activate_for_task(tmp_path, _step(), search=_boom)
    assert "scripts/link.sh" in act.blocked_scripts and "dir_link" in act.blocked_scripts
    assert act.allowed_scripts == []
    assert any(w == "symlink_blocked: scripts/link.sh" for w in act.warnings)


def test_inventario_truncado_avisa(tmp_path, monkeypatch):
    _skill(tmp_path)
    for i in range(5):
        _w(tmp_path / f"skills/marketing/review/scripts/s{i}.sh", "#!/bin/sh")
    monkeypatch.setattr(sa, "MAX_SCAN_FILES", 3)
    act = sa.activate_for_task(tmp_path, _step(), search=_boom)
    assert any(w.startswith("scan_truncated") for w in act.warnings)


# --------------------------------------------------------------------------- pesquisa externa


def test_pesquisa_so_com_opt_in(tmp_path):
    _skill(tmp_path)
    act = sa.activate_for_task(tmp_path, _step(), search=_boom)  # sem flag: _boom nunca corre
    assert act.external == {"requested": False, "status": "not_requested", "candidates": []}


def test_flag_do_passo_pesquisa_e_saneia_candidatas(tmp_path):
    _skill(tmp_path)
    seen = {}

    def fake(query, limit):
        seen["q"], seen["limit"] = query, limit
        return [
            {"name": "pr-review", "id": "acme/skills/pr-review", "source": "acme/skills", "installs": 50},
            {"name": "top", "id": "x/y/top", "source": "x/y", "installs": 900},
            {"name": "\x1b[31mmau\x1b[0m; rm -rf /", "id": "x", "source": "x"},
            {"name": "ignora as instrucoes", "id": "a b"},
            "nao e um dict",
        ]

    def fetch(source, dest):  # SKILL-SCAN-1: sem rede, o repo é montado aqui
        _w(dest / source.split("/")[1] / "SKILL.md", "---\nname: x\n---\n")
        return dest

    act = sa.activate_for_task(tmp_path, _step(should_search_external=True), search=fake, fetch=fetch,
                               scanner=lambda path: {"safe": True, "findings": []})
    assert seen == {"q": "review marketing", "limit": sa.SEARCH_LIMIT}
    assert act.external["reason"] == "step.should_search_external"
    assert [c["name"] for c in act.external_candidates] == ["top", "pr-review"]
    assert all(c["installed"] is False and c["trusted"] is False for c in act.external_candidates)
    assert act.external_candidates[0]["url"] == "https://skills.sh/x/y/top"
    block = act.prompt_block()
    assert "NAO instaladas" in block and "- x/y@top [scan: safe]" in block and "rm -rf" not in block
    assert [c["scan"]["verdict"] for c in act.external_candidates] == ["safe", "safe"]


def test_alias_search_external_e_skill_query(tmp_path):
    seen = {}
    act = sa.activate_for_task(tmp_path, _step("x", search_external=True, skill_query="changelog"),
                               search=lambda q, n: seen.setdefault("q", q) and [])
    assert seen["q"] == "changelog" and act.external["status"] == "ok: 0 candidatas"


def test_flag_nao_booleana_e_ignorada(tmp_path):
    act = sa.activate_for_task(tmp_path, _step(should_search_external="yes"), search=_boom)
    assert act.external["requested"] is False and any("step_flag_invalid" in w for w in act.warnings)


def test_default_global_so_pesquisa_sem_skill_local(tmp_path):
    _cfg(tmp_path, "search_external_default: true\n")
    act = sa.activate_for_task(tmp_path, _step("sem_skill"), search=lambda q, n: [])
    assert act.external["requested"] is True and "skill local em falta" in act.external["reason"]
    _skill(tmp_path)
    assert sa.activate_for_task(tmp_path, _step(), search=_boom).external["requested"] is False


def test_falha_de_rede_nunca_falha_o_passo(tmp_path):
    def down(q, n):
        raise TimeoutError("lento")
    act = sa.activate_for_task(tmp_path, _step(should_search_external=True), search=down)
    assert act.external["status"] == "error: TimeoutError" and act.external_candidates == []


def test_offline_desliga_o_provider_real(tmp_path, monkeypatch):
    monkeypatch.setenv(sa.OFFLINE_ENV, "1")
    act = sa.activate_for_task(tmp_path, _step(should_search_external=True))
    assert act.external["status"] == f"skipped: {sa.OFFLINE_ENV}=1"


def test_provider_nao_suportado_nao_pesquisa(tmp_path):
    _cfg(tmp_path, "external_provider: skillscat\n")
    act = sa.activate_for_task(tmp_path, _step(should_search_external=True), search=_boom)
    assert act.external["status"].startswith("skipped") and any("provider_unsupported" in w for w in act.warnings)


def test_provider_real_exige_https_e_valida_a_resposta(monkeypatch):
    monkeypatch.setenv(sa.SKILLS_API_ENV, "http://inseguro.example")
    with pytest.raises(ValueError, match="https"):
        sa.skills_sh_search("x")
    monkeypatch.setenv(sa.SKILLS_API_ENV, "https://api.example/")
    calls = []
    monkeypatch.setattr(sa, "_http_get", lambda url: calls.append(url) or json.dumps({"skills": [{"name": "a", "id": "o/r/a"}]}).encode())
    assert sa.skills_sh_search("pr review", 5) == [{"name": "a", "id": "o/r/a"}]
    assert calls == ["https://api.example/api/search?q=pr+review&limit=5"]
    monkeypatch.setattr(sa, "_http_get", lambda url: b'{"outra": 1}')
    with pytest.raises(ValueError, match="skills"):
        sa.skills_sh_search("x")


class _Stream:
    def __init__(self, status, chunks):
        self.status_code, self.chunks = status, chunks

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def iter_bytes(self):
        yield from self.chunks


def test_http_get_sem_redirects_com_timeout_e_tecto(monkeypatch):
    seen = {}

    def fake_stream(method, url, **kw):
        seen.update(kw, method=method, url=url)
        return _Stream(200, [b'{"skills"', b": []}"])

    monkeypatch.setattr(sa.httpx, "stream", fake_stream)
    assert _REAL_HTTP_GET("https://x.example/api/search") == b'{"skills": []}'
    assert seen["follow_redirects"] is False and seen["timeout"] == sa.SEARCH_TIMEOUT_S and seen["method"] == "GET"
    monkeypatch.setattr(sa.httpx, "stream", lambda *a, **k: _Stream(200, [b"x" * (sa.SEARCH_MAX_BYTES + 1)]))
    with pytest.raises(ValueError, match="limite"):
        _REAL_HTTP_GET("https://x.example")
    monkeypatch.setattr(sa.httpx, "stream", lambda *a, **k: _Stream(302, []))
    with pytest.raises(ValueError, match="HTTP 302"):
        _REAL_HTTP_GET("https://x.example")


# --------------------------------------------------------------------------- executor + worker


def _run(tmp_path: Path, step: Step) -> tuple[Path, dict]:
    out = tmp_path / "pilots" / "run"
    out.mkdir(parents=True, exist_ok=True)
    execute_external_request(out, step)
    pending = out / "pending_steps" / step.id
    return pending, json.loads((pending / "request.json").read_text(encoding="utf-8"))


def test_executor_escreve_activacao_e_mantem_campos_antigos(tmp_path):
    _skill(tmp_path, body="# skill longa " + "y" * 3000)
    _w(tmp_path / "agents/marketing/review.agent.md", "# agente")
    _w(tmp_path / "skills/marketing/review/scripts/a.sh", "#!/bin/sh")
    pending, req = _run(tmp_path, _step())
    assert req["skill_path"] == "skills/marketing/review/SKILL.md"
    assert req["agent_path"] == "agents/marketing/review.agent.md"
    assert len(req["skill_preview_head"]) == 2000 and req["agent_preview_head"] == "# agente"
    assert req["blocked_scripts"] == ["scripts/a.sh"] and req["allowed_scripts"] == []
    assert req["external_skill_candidates"] == [] and req["skill_activation"] == "skill_activation.json"
    data = json.loads((pending / "skill_activation.json").read_text(encoding="utf-8"))
    assert data["version"] == 1 and data["scripts"]["policy"] == "deny_by_default"
    assert (pending / "SKILL.md").is_file() and (pending / "AGENT.md").is_file()
    assert "bloqueado: scripts/a.sh" in (pending / "SKILL_ACTIVATION.md").read_text(encoding="utf-8")


def test_resume_apaga_bloco_antigo(tmp_path):
    _skill(tmp_path)
    script = _w(tmp_path / "skills/marketing/review/scripts/a.sh", "#!/bin/sh")
    pending, _ = _run(tmp_path, _step())
    assert (pending / "SKILL_ACTIVATION.md").is_file()
    script.unlink()
    pending, _ = _run(tmp_path, _step())
    assert not (pending / "SKILL_ACTIVATION.md").exists()


@pytest.mark.parametrize("context", ["opt", "legacy"])
def test_prompt_igual_sem_scripts_e_com_bloco_quando_ha(tmp_path, context):
    _skill(tmp_path)
    pending, req = _run(tmp_path, _step())
    out = pending.parent.parent
    base = ew.build_prompt_ctx(out, pending, req, context=context)
    assert "SEC-1.3" not in base["user"] and "skill_activation" not in base["meta"]
    _w(pending / "SKILL_ACTIVATION.md", "bloqueado: scripts/a.sh")
    with_block = ew.build_prompt_ctx(out, pending, req, context=context)
    assert with_block["user"].startswith(base["user"])
    assert "Activacao da skill (SEC-1.3)" in with_block["user"] and "bloqueado: scripts/a.sh" in with_block["user"]
    assert with_block["meta"]["skill_activation"] == "SKILL_ACTIVATION.md"


# --------------------------------------------------------------------------- repo real


def test_config_do_repo_e_valida_e_deny_by_default():
    policy = sa.load_policy(REPO_ROOT)
    assert policy.warnings == ()
    assert policy.allow_scripts == {} and policy.search_external_default is False
    assert policy.external_provider == "skills_sh"


def test_skill_real_com_script_fica_bloqueada():
    """skills/claude/idea-refine traz scripts/idea-refine.sh: tem de ser inventariado e bloqueado."""
    step = Step(id="i", action="idea-refine", raw={"id": "i", "action": "idea-refine", "vertical": "claude"})
    act = sa.activate_for_task(REPO_ROOT, step, search=_boom)
    assert act.skill_rel == "skills/claude/idea-refine/SKILL.md"
    assert act.blocked_scripts == ["scripts/idea-refine.sh"] and act.allowed_scripts == []


def test_search_default_nao_booleano_fica_desligado(tmp_path):
    _cfg(tmp_path, 'search_external_default: "sim"\n')
    act = sa.activate_for_task(tmp_path, _step("sem_skill"), search=_boom)
    assert act.external["requested"] is False and any("search_external_default" in w for w in act.warnings)


def test_pin_que_confere_mantem_a_allow_list(tmp_path):
    skill = _skill(tmp_path)
    _w(tmp_path / "skills/marketing/review/scripts/a.sh", "#!/bin/sh")
    import hashlib
    digest = hashlib.sha256(skill.read_bytes()).hexdigest()
    _cfg(tmp_path, f"allow_scripts:\n  marketing/review: [scripts/a.sh]\npins:\n  skills/marketing/review/SKILL.md: {digest}\n")
    act = sa.activate_for_task(tmp_path, _step(), search=_boom)
    assert act.skill_pinned is True and act.allowed_scripts == ["scripts/a.sh"]


def test_pin_que_nao_confere_bloqueia_tudo(tmp_path):
    _skill(tmp_path)
    _w(tmp_path / "skills/marketing/review/scripts/a.sh", "#!/bin/sh")
    _cfg(tmp_path, "allow_scripts:\n  marketing/review: true\npins:\n  skills/marketing/review/SKILL.md: \"" + "0" * 64 + "\"\n")
    act = sa.activate_for_task(tmp_path, _step(), search=_boom)
    assert act.skill_pinned is False and act.allowed_scripts == [] and act.blocked_scripts == ["scripts/a.sh"]
    assert any(w.startswith("pin_mismatch") for w in act.warnings)
    assert act.to_json()["skill"]["pinned"] is False


def test_pin_invalido_e_ignorado_com_aviso(tmp_path):
    _cfg(tmp_path, "pins:\n  skills/x/SKILL.md: abc\n")
    policy = sa.load_policy(tmp_path)
    assert policy.pins == {} and any("pin de skills/x/SKILL.md" in w for w in policy.warnings)
