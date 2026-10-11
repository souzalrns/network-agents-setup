"""The execution gate: which orders may leave the process, and to where.

    PAPER    always allowed (simulated fills against real public prices).
    TESTNET  needs ECONOMIA_TRADER_ALLOW_TESTNET=1 (exchange test funds; MEXC has no testnet).
    LIVE     needs ALL of: ECONOMIA_TRADER_LIVE=I_ACCEPT_REAL_LOSSES, an approver that says yes
             to *this* order (default: deny), and a key verified without withdraw permission.

Every mode is stopped by the kill switch (a file, or ECONOMIA_TRADER_KILL=1) and by a risk
assessment that did not approve. Real orders are therefore off by default and need a human.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from enum import Enum
from pathlib import Path
from typing import Any

from .contracts import OrderIntent, RiskAssessment, to_dict

ENV_ALLOW_TESTNET = "ECONOMIA_TRADER_ALLOW_TESTNET"
ENV_LIVE = "ECONOMIA_TRADER_LIVE"
LIVE_ACK = "I_ACCEPT_REAL_LOSSES"
ENV_KILL = "ECONOMIA_TRADER_KILL"
DEFAULT_KILL_FILE = Path(".economia-trader") / "KILL"


class Mode(str, Enum):
    PAPER = "paper"
    TESTNET = "testnet"
    LIVE = "live"


class ExecutionBlocked(RuntimeError):
    """An order was stopped by the gate. ``code`` says which lock held."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code


class KillSwitch:
    """Engaged if the file exists or ``ECONOMIA_TRADER_KILL=1``. Engaging is one ``touch``."""

    def __init__(self, path: str | Path = DEFAULT_KILL_FILE, env: Mapping[str, str] | None = None) -> None:
        self.path = Path(path)
        self._env = os.environ if env is None else env

    def engaged(self) -> bool:
        return self.path.exists() or self._env.get(ENV_KILL) == "1"

    def engage(self, reason: str = "") -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(reason or "engaged\n", encoding="utf-8")

    def release(self) -> None:
        self.path.unlink(missing_ok=True)


# An approver is asked once per LIVE order and must return True to let it through.
Approver = Callable[[OrderIntent, RiskAssessment], bool]


def deny_all(intent: OrderIntent, assessment: RiskAssessment) -> bool:
    return False


class HitlApprover:
    """Per-order human approval over the hitlwright contract (``pip install hitlwright``).

    First call for an order writes a request under ``<run_dir>/<client_order_id>/`` and returns
    False (pending). A human answers with ``hitlwright decide <dir> <id> --response approve``;
    the next call sees the decision. Anything but ``approve`` keeps the order blocked.
    """

    def __init__(self, run_dir: str | Path) -> None:
        try:
            import hitlwright  # noqa: F401
        except ImportError as exc:  # pragma: no cover - exercised only without the extra
            raise RuntimeError("HitlApprover needs `pip install economia-trader[hitl]`") from exc
        self.run_dir = Path(run_dir)

    def __call__(self, intent: OrderIntent, assessment: RiskAssessment) -> bool:
        from hitlwright import latest_request, read_decision, write_request

        order_dir = self.run_dir / intent.client_order_id
        request = latest_request(order_dir)
        if request is None:
            write_request(
                order_dir,
                step_id="live-order",
                action="place_order",
                title=f"LIVE {intent.side} {intent.qty} {intent.symbol}",
                description=f"notional {assessment.notional}, loss at stop {assessment.loss_at_stop}",
                priority="critical",
                source="economia-trader",
                category="trading",
                context={"intent": to_dict(intent), "assessment": to_dict(assessment)},
            )
            return False
        decision = read_decision(order_dir)
        return bool(decision and decision.get("id") == request["id"] and decision.get("response") == "approve")


def authorize(
    mode: Mode,
    intent: OrderIntent,
    assessment: RiskAssessment,
    *,
    kill_switch: KillSwitch,
    approver: Approver = deny_all,
    key_checked: bool = False,
    env: Mapping[str, str] | None = None,
) -> None:
    """Raise ``ExecutionBlocked`` unless every lock for ``mode`` is open."""
    env = os.environ if env is None else env
    if kill_switch.engaged():
        raise ExecutionBlocked("kill_switch", f"kill switch engaged ({kill_switch.path} or {ENV_KILL}=1)")
    if not assessment.approved or assessment.proposal_id != intent.proposal_id:
        raise ExecutionBlocked("risk", "no matching approved risk assessment")
    if mode is Mode.PAPER:
        return
    if mode is Mode.TESTNET:
        if env.get(ENV_ALLOW_TESTNET) != "1":
            raise ExecutionBlocked("testnet_disabled", f"set {ENV_ALLOW_TESTNET}=1 to send testnet orders")
        return
    if env.get(ENV_LIVE) != LIVE_ACK:
        raise ExecutionBlocked("live_disabled", f"real orders are off; {ENV_LIVE}={LIVE_ACK} is required")
    if not key_checked:
        raise ExecutionBlocked("key_unchecked", "the API key was not verified (read+trade only, no withdraw)")
    if not approver(intent, assessment):
        raise ExecutionBlocked("awaiting_approval", "this order has no human approval yet")


def gate_report(mode: Mode, *, kill_switch: KillSwitch, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    """What would block an order right now (for the CLI and for a dashboard)."""
    env = os.environ if env is None else env
    return {
        "mode": mode.value,
        "kill_switch": kill_switch.engaged(),
        "testnet_enabled": env.get(ENV_ALLOW_TESTNET) == "1",
        "live_acknowledged": env.get(ENV_LIVE) == LIVE_ACK,
    }
