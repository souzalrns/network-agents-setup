from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Step


class StepResult:
    def __init__(self, ok: bool, detail: str = "", artifact: str | None = None):
        self.ok = ok
        self.detail = detail
        self.artifact = artifact


def _write_stub_artifact(out_root: Path, step: Step) -> str | None:
    if not step.output_artifact:
        return None
    path = out_root / step.output_artifact
    path.parent.mkdir(parents=True, exist_ok=True)
    body: dict[str, Any] = {
        "_stub": True,
        "step_id": step.id,
        "action": step.action,
        "tools_allowed": step.tools_allowed,
        "message": "Placeholder artifact from plan_runner stub mode. Replace with real worker output.",
    }
    if step.output_schema:
        body["output_schema"] = step.output_schema
    if path.suffix.lower() in {".md", ".txt"}:
        path.write_text(
            f"# Stub: {step.id} ({step.action})\n\n"
            f"tools_allowed: {step.tools_allowed}\n\n"
            f"Replace with real worker output.\n",
            encoding="utf-8",
        )
    else:
        path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return str(path.relative_to(out_root))


def execute_stub(out_root: Path, step: Step) -> StepResult:
    if step.human_gate:
        return StepResult(ok=True, detail="awaiting_human_gate", artifact=None)
    art = _write_stub_artifact(out_root, step)
    return StepResult(ok=True, detail="stub_ok", artifact=art)


def execute_external_request(out_root: Path, step: Step) -> StepResult:
    """Write a pending request; complete when pending_steps/<id>/result.json exists."""
    pending = out_root / "pending_steps" / step.id
    pending.mkdir(parents=True, exist_ok=True)
    req = {
        "step_id": step.id,
        "action": step.action,
        "tools_allowed": step.tools_allowed,
        "inputs": step.inputs,
        "output_artifact": step.output_artifact,
        "output_schema": step.output_schema,
        "instruction": "Run worker for this action; write result.json with {ok, detail?, artifact_content?}.",
    }
    (pending / "request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
    result_path = pending / "result.json"
    if not result_path.exists():
        return StepResult(ok=False, detail="waiting_external")
    data = json.loads(result_path.read_text(encoding="utf-8"))
    if not data.get("ok"):
        return StepResult(ok=False, detail=str(data.get("detail") or "external_failed"))
    if step.output_artifact and data.get("artifact_content") is not None:
        path = out_root / step.output_artifact
        path.parent.mkdir(parents=True, exist_ok=True)
        content = data["artifact_content"]
        if isinstance(content, (dict, list)):
            path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        else:
            path.write_text(str(content), encoding="utf-8")
        return StepResult(ok=True, detail="external_ok", artifact=step.output_artifact)
    if step.output_artifact and (out_root / step.output_artifact).exists():
        return StepResult(ok=True, detail="external_ok", artifact=step.output_artifact)
    return StepResult(ok=True, detail="external_ok_no_artifact")
