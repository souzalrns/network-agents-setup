"""Tool implementations — call into plan_runner engine."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .policy import audit, authorize, rate_limit, repo_root, sanitize_repo_path


def _ensure_runner_on_path() -> Path:
    root = repo_root()
    runner = root / "runner"
    if str(runner) not in sys.path:
        sys.path.insert(0, str(runner))
    return root


def list_templates() -> dict:
    auth = authorize("list_templates")
    rate_limit(auth.caller)
    if not auth.authorized:
        audit({"tool": "list_templates", "ok": False, "reason": auth.reason})
        return {"ok": False, "error": auth.reason}
    root = repo_root()
    base = root / "docs" / "orchestration"
    found: list[str] = []
    if base.is_dir():
        for p in sorted(base.rglob("*.plan.yaml")):
            found.append(str(p.relative_to(root)).replace("\\", "/"))
    audit({"tool": "list_templates", "ok": True, "count": len(found), "caller": auth.caller})
    return {"ok": True, "templates": found, "repo_root": str(root)}


def get_status(out_dir: str) -> dict:
    auth = authorize("get_status")
    rate_limit(auth.caller)
    if not auth.authorized:
        return {"ok": False, "error": auth.reason}
    try:
        path = sanitize_repo_path(out_dir, must_exist=True)
        if path.is_file() and path.name == "status.json":
            status_file = path
        elif path.is_dir():
            status_file = path / "status.json"
        else:
            status_file = path
        if not status_file.exists():
            raise FileNotFoundError(str(status_file))
        data = json.loads(status_file.read_text(encoding="utf-8-sig"))
        audit({"tool": "get_status", "ok": True, "out": str(path), "caller": auth.caller})
        return {"ok": True, "status": data}
    except Exception as e:
        audit({"tool": "get_status", "ok": False, "error": str(e)})
        return {"ok": False, "error": str(e)}


def run_plan(plan: str, mode: str = "stub", out: str | None = None) -> dict:
    auth = authorize("run_plan")
    rate_limit(auth.caller)
    if not auth.authorized:
        audit({"tool": "run_plan", "ok": False, "reason": auth.reason})
        return {"ok": False, "error": auth.reason}
    if mode not in {"dry-run", "stub", "external"}:
        return {"ok": False, "error": "mode must be dry-run|stub|external"}
    try:
        _ensure_runner_on_path()
        from plan_runner.engine import run_plan as engine_run

        plan_path = sanitize_repo_path(plan, must_exist=True)
        out_dir = None
        if out:
            out_dir = sanitize_repo_path(out, must_exist=False)
            out_dir.mkdir(parents=True, exist_ok=True)
        result = engine_run(plan_path, mode=mode, out_dir=out_dir)
        audit(
            {
                "tool": "run_plan",
                "ok": True,
                "plan": str(plan_path),
                "mode": mode,
                "caller": auth.caller,
                "profile": auth.profile,
                "auth_reason": auth.reason,
            }
        )
        return {"ok": True, "result": result}
    except Exception as e:
        audit({"tool": "run_plan", "ok": False, "error": str(e)})
        return {"ok": False, "error": str(e)}


def resume_plan(out_dir: str, decision: str = "approve") -> dict:
    auth = authorize("resume_plan")
    rate_limit(auth.caller)
    if not auth.authorized:
        audit({"tool": "resume_plan", "ok": False, "reason": auth.reason})
        return {"ok": False, "error": auth.reason}
    try:
        _ensure_runner_on_path()
        from plan_runner.engine import resume_run

        path = sanitize_repo_path(out_dir, must_exist=True)
        result = resume_run(path, decision=decision)
        audit(
            {
                "tool": "resume_plan",
                "ok": True,
                "out": str(path),
                "decision": decision,
                "caller": auth.caller,
            }
        )
        return {"ok": True, "result": result}
    except Exception as e:
        audit({"tool": "resume_plan", "ok": False, "error": str(e)})
        return {"ok": False, "error": str(e)}
