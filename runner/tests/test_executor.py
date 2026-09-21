"""Testes de executor.py: ramos de erro do external + stub artifacts."""
from __future__ import annotations

import json

from plan_runner.executor import execute_external_request, execute_stub
from plan_runner.models import HumanGate, Step


def test_execute_stub_with_human_gate(tmp_path):
    step = Step(id="hitl", action="approve", human_gate=HumanGate())
    result = execute_stub(tmp_path, step)
    assert result.ok is True
    assert result.detail == "awaiting_human_gate"
    assert result.artifact is None


def test_execute_stub_writes_json_artifact(tmp_path):
    step = Step(id="a", action="do", output_artifact="artifacts/a.json")
    result = execute_stub(tmp_path, step)
    assert result.ok is True
    assert result.detail == "stub_ok"
    # Normalizar separadores (Windows devolve \, POSIX devolve /)
    assert result.artifact.replace("\\", "/") == "artifacts/a.json"
    body = json.loads((tmp_path / "artifacts/a.json").read_text(encoding="utf-8"))
    assert body["_stub"] is True
    assert body["step_id"] == "a"


def test_execute_stub_writes_md_artifact(tmp_path):
    step = Step(id="a", action="do", output_artifact="artifacts/note.md")
    result = execute_stub(tmp_path, step)
    assert result.ok is True
    text = (tmp_path / "artifacts/note.md").read_text(encoding="utf-8")
    assert "Stub: a" in text


def test_execute_stub_no_artifact(tmp_path):
    step = Step(id="a", action="do")
    result = execute_stub(tmp_path, step)
    assert result.ok is True
    assert result.artifact is None


def test_external_waits_when_no_result_json(tmp_path):
    step = Step(id="prep", action="prep")
    result = execute_external_request(tmp_path, step)
    assert result.ok is False
    assert result.detail == "waiting_external"
    req = tmp_path / "pending_steps" / "prep" / "request.json"
    assert req.exists()


def test_external_ok_with_artifact_content_dict(tmp_path):
    step = Step(id="prep", action="prep", output_artifact="artifacts/prep.json")
    pending = tmp_path / "pending_steps" / "prep"
    pending.mkdir(parents=True)
    (pending / "result.json").write_text(
        json.dumps({"ok": True, "artifact_content": {"k": "v"}}),
        encoding="utf-8",
    )
    result = execute_external_request(tmp_path, step)
    assert result.ok is True
    assert result.detail == "external_ok"
    assert result.artifact == "artifacts/prep.json"
    body = json.loads((tmp_path / "artifacts/prep.json").read_text(encoding="utf-8"))
    assert body == {"k": "v"}


def test_external_ok_with_artifact_content_str(tmp_path):
    step = Step(id="prep", action="prep", output_artifact="artifacts/prep.md")
    pending = tmp_path / "pending_steps" / "prep"
    pending.mkdir(parents=True)
    (pending / "result.json").write_text(
        json.dumps({"ok": True, "artifact_content": "# hello"}),
        encoding="utf-8",
    )
    result = execute_external_request(tmp_path, step)
    assert result.ok is True
    assert (tmp_path / "artifacts/prep.md").read_text(encoding="utf-8") == "# hello"


def test_external_fails_when_ok_false(tmp_path):
    step = Step(id="prep", action="prep")
    pending = tmp_path / "pending_steps" / "prep"
    pending.mkdir(parents=True)
    (pending / "result.json").write_text(
        json.dumps({"ok": False, "detail": "boom"}),
        encoding="utf-8",
    )
    result = execute_external_request(tmp_path, step)
    assert result.ok is False
    assert result.detail == "boom"


def test_external_ok_no_artifact(tmp_path):
    step = Step(id="prep", action="prep")
    pending = tmp_path / "pending_steps" / "prep"
    pending.mkdir(parents=True)
    (pending / "result.json").write_text(
        json.dumps({"ok": True}),
        encoding="utf-8",
    )
    result = execute_external_request(tmp_path, step)
    assert result.ok is True
    assert result.detail == "external_ok_no_artifact"


def test_external_resolves_skill_by_vertical_from_step_raw(tmp_path):
    """S34 -- regressao do bug real: executor.py chamava resolve_skill_path()
    sempre com vertical="marketing" (omissao), partindo design-flow-demo.plan.yaml
    (acoes so existentes em skills/design/). Corrigido lendo step.raw["vertical"].

    repo_root_from_out(out_root) devolve out_root.parent.parent quando
    out_root.parent.name == "pilots" -- por isso o out_root aqui simula
    <repo>/pilots/<run>, para o repo_root resolvido ser tmp_path (que
    controlamos), tal como acontece no repo real.
    """
    repo_root = tmp_path
    out_root = repo_root / "pilots" / "run-x"
    out_root.mkdir(parents=True)

    skill = repo_root / "skills" / "design" / "ux_flow" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# ux_flow (design)", encoding="utf-8")
    # Confirma que NAO existe em marketing -- prova que o bug reproduziria
    # skill_path=None se o vertical nao fosse propagado.
    assert not (repo_root / "skills" / "marketing" / "ux_flow").exists()

    step = Step(id="ux", action="ux_flow", raw={"id": "ux", "action": "ux_flow", "vertical": "design"})
    result = execute_external_request(out_root, step)

    assert result.ok is False  # waiting_external, sem result.json ainda
    req = json.loads((out_root / "pending_steps" / "ux" / "request.json").read_text(encoding="utf-8"))
    assert req["skill_path"] == "skills/design/ux_flow/SKILL.md"
    assert (out_root / "pending_steps" / "ux" / "SKILL.md").read_text(encoding="utf-8") == "# ux_flow (design)"


def test_external_falls_back_to_marketing_when_no_vertical_in_raw(tmp_path):
    """Nao-regressao: planos existentes sem `vertical:` continuam a resolver
    contra marketing, exactamente como antes do fix do S34."""
    repo_root = tmp_path
    out_root = repo_root / "pilots" / "run-y"
    out_root.mkdir(parents=True)

    skill = repo_root / "skills" / "marketing" / "prep" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# prep (marketing)", encoding="utf-8")

    step = Step(id="prep", action="prep", raw={"id": "prep", "action": "prep"})
    execute_external_request(out_root, step)

    req = json.loads((out_root / "pending_steps" / "prep" / "request.json").read_text(encoding="utf-8"))
    assert req["skill_path"] == "skills/marketing/prep/SKILL.md"
