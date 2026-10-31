"""Kill-switch do operador (secção 3 — runtime hardening).

Termina um run de forma auditável sem apagar ledger nem artefactos.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .engine import load_status, save_status
from .events import EventLog
from .graph import PlanError

__all__ = ["abort_run"]


def abort_run(out_dir: Path, *, reason: str = "operator") -> dict[str, Any]:
    """Define state=aborted_operator e emite plan_aborted.

    Estados já terminais não mudam. Não retoma a partir daqui.
    """
    out_dir = Path(out_dir)
    status = load_status(out_dir)
    if not status:
        raise PlanError("no status.json")
    state = status.get("state")
    terminal = frozenset(
        {"done", "failed", "rejected", "aborted_budget", "aborted_operator"}
    )
    if state in terminal:
        raise PlanError(f"cannot abort from terminal state {state!r}")
    run_id = status.get("run_id") or "unknown"
    log = EventLog(out_dir / "events.jsonl")
    log.append(
        "plan_aborted",
        run_id,
        {
            "reason": reason,
            "by": "operator",
            "previous_state": state,
            "paused_at_step": status.get("paused_at_step"),
            "current_step": status.get("current_step"),
        },
    )
    status["state"] = "aborted_operator"
    status["abort_reason"] = reason
    status["current_step"] = None
    save_status(out_dir, status)
    lines = [
        "# Abort",
        "",
        f"Run `{run_id}` aborted by operator.",
        "",
        f"- previous_state: `{state}`",
        f"- reason: {reason}",
        "- artefactos e token_usage.jsonl preservados.",
        "",
    ]
    (out_dir / "ABORT.md").write_text("\n".join(lines), encoding="utf-8")
    return status
