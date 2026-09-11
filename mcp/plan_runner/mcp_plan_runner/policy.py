"""Scopes, profiles, path sanitize, rate limit, audit — patterns from MCP governance research."""

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
    prof = profile()
    caller = os.environ.get("PLAN_RUNNER_MCP_CALLER", "mcp-client")
    key = expected_key()
    provided = (provided_key or os.environ.get("PLAN_RUNNER_MCP_KEY_PRESENT", "") or "").strip()
    # For stdio, key is typically only in env; treat env key as credential presence
    has_cred = bool(key) and (provided == key or provided_key is None and key)

    if tool not in SCOPES:
        return AuthContext(prof, caller, False, "unknown_tool")

    if prof == "permissive":
        return AuthContext(prof, caller, True, "permissive")

    if tool in MUTATING:
        if not key:
            if prof == "strict":
                return AuthContext(prof, caller, False, "missing_PLAN_RUNNER_MCP_KEY")
            # moderate: allow mutate only if key configured OR explicit allow
            if os.environ.get("PLAN_RUNNER_MCP_ALLOW_MUTATE", "").lower() in {"1", "true", "yes"}:
                return AuthContext(prof, caller, True, "allow_mutate_env")
            return AuthContext(prof, caller, False, "configure_PLAN_RUNNER_MCP_KEY_or_ALLOW_MUTATE")
        return AuthContext(prof, caller, True, "key_configured")

    return AuthContext(prof, caller, True, "read_ok")


def repo_root() -> Path:
    env = os.environ.get("PLAN_RUNNER_REPO_ROOT")
    if env:
        return Path(env).resolve()
    # mcp/plan_runner/mcp_plan_runner -> repo root
    return Path(__file__).resolve().parents[3]


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
    if ".." in Path(user_path).parts:
        # still ok if resolved under root; double-check
        cand.relative_to(root)
    if must_exist and not cand.exists():
        raise FileNotFoundError(str(cand))
    return cand


_rate_lock = Lock()
_rate_bucket: dict[str, list[float]] = {}


def rate_limit(caller: str, limit: int = 30, window: float = 60.0) -> None:
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
