"""Scopes, profiles, path sanitize, rate limit, audit."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

SCOPES = {
    "list_templates": "runner:template:list",
    "get_status": "runner:plan:read",
    "run_plan": "runner:plan:execute",
    "resume_plan": "runner:plan:resume",
}

MUTATING = {"run_plan", "resume_plan"}


@dataclass
class AuthContext:
    profile: str
    caller: str
    authorized: bool
    reason: str = ""


def profile() -> str:
    p = os.environ.get("PLAN_RUNNER_MCP_PROFILE", "moderate").strip().lower()
    return p if p in {"permissive", "moderate", "strict"} else "moderate"


def expected_key() -> str | None:
    k = os.environ.get("PLAN_RUNNER_MCP_KEY", "").strip()
    return k or None


def authorize(tool: str, provided_key: str | None = None) -> AuthContext:
    """stdio: credential = PLAN_RUNNER_MCP_KEY set in the server process env.

    - permissive: all tools
    - moderate: reads always; mutate if key set OR PLAN_RUNNER_MCP_ALLOW_MUTATE=1
    - strict: mutate only if key set (non-empty)
    """
    prof = profile()
    caller = os.environ.get("PLAN_RUNNER_MCP_CALLER", "mcp-client")
    key = expected_key()

    if tool not in SCOPES:
        return AuthContext(prof, caller, False, "unknown_tool")

    if provided_key is not None and key and provided_key != key:
        return AuthContext(prof, caller, False, "invalid_key")

    if prof == "permissive":
        return AuthContext(prof, caller, True, "permissive")

    if tool not in MUTATING:
        return AuthContext(prof, caller, True, "read_ok")

    # mutating
    if key:
        return AuthContext(prof, caller, True, "key_configured")

    allow = os.environ.get("PLAN_RUNNER_MCP_ALLOW_MUTATE", "").lower() in {"1", "true", "yes"}
    if allow:
        return AuthContext(prof, caller, True, "allow_mutate_env")

    if prof == "moderate":
        # Lab default: allow mutate without key but record reason (audit still runs)
        return AuthContext(prof, caller, True, "moderate_lab_open")

    return AuthContext(prof, caller, False, "strict_requires_PLAN_RUNNER_MCP_KEY")


def repo_root() -> Path:
    env = os.environ.get("PLAN_RUNNER_REPO_ROOT")
    if env:
        return Path(env).resolve()

    here = Path(__file__).resolve()
    for parent in [here.parents[i] for i in range(1, min(6, len(here.parents)))]:
        if (parent / "runner" / "plan_runner").is_dir() and (parent / "docs").is_dir():
            return parent
    # fallback: mcp/plan_runner/mcp_plan_runner -> parents[3]
    return here.parents[3]


def sanitize_repo_path(user_path: str, *, must_exist: bool = False) -> Path:
    root = repo_root()
    raw = Path(user_path)
    if not raw.is_absolute():
        cand = (root / raw).resolve()
    else:
        cand = raw.resolve()
    try:
        cand.relative_to(root)
    except ValueError as e:
        raise PermissionError(f"path outside repo root: {user_path}") from e
    if must_exist and not cand.exists():
        raise FileNotFoundError(str(cand))
    return cand


_rate_lock = Lock()
_rate_bucket: dict[str, list[float]] = {}


def rate_limit(caller: str, limit: int = 60, window: float = 60.0) -> None:
    now = time.time()
    with _rate_lock:
        q = _rate_bucket.setdefault(caller, [])
        q[:] = [t for t in q if now - t < window]
        if len(q) >= limit:
            raise RuntimeError(f"rate_limit exceeded for {caller}")
        q.append(now)


def audit_path() -> Path:
    p = Path(__file__).resolve().parents[1] / "audit"
    p.mkdir(parents=True, exist_ok=True)
    return p / "audit.jsonl"


def audit(event: dict) -> None:
    event = {**event, "ts": time.time()}
    line = json.dumps(event, ensure_ascii=False)
    with audit_path().open("a", encoding="utf-8") as f:
        f.write(line + "\n")
