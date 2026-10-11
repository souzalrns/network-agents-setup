from decimal import Decimal as D

import pytest

from economia_trader import ExecutionBlocked, HitlApprover, KillSwitch, Mode, OrderIntent, RiskAssessment, authorize
from economia_trader.safety import ENV_ALLOW_TESTNET, ENV_KILL, ENV_LIVE, LIVE_ACK, gate_report


def _pair(approved=True):
    intent = OrderIntent("BTCUSDT", "buy", D("0.001"), proposal_id="p1")
    a = RiskAssessment("p1", approved, () if approved else ("x",), D(50000), D(50), D(1))
    return intent, a


@pytest.fixture
def ks(tmp_path):
    return KillSwitch(tmp_path / "KILL", env={})


def _code(fn):
    with pytest.raises(ExecutionBlocked) as e:
        fn()
    return e.value.code


def test_paper_passes(ks):
    authorize(Mode.PAPER, *_pair(), kill_switch=ks, env={})


def test_kill_switch_file_and_env(tmp_path, ks):
    ks.engage("test")
    assert _code(lambda: authorize(Mode.PAPER, *_pair(), kill_switch=ks, env={})) == "kill_switch"
    ks.release()
    env_ks = KillSwitch(tmp_path / "none", env={ENV_KILL: "1"})
    assert _code(lambda: authorize(Mode.PAPER, *_pair(), kill_switch=env_ks, env={})) == "kill_switch"


def test_unapproved_or_mismatched_risk(ks):
    assert _code(lambda: authorize(Mode.PAPER, *_pair(False), kill_switch=ks, env={})) == "risk"
    _, a = _pair()
    other = OrderIntent("BTCUSDT", "buy", D("0.001"), proposal_id="p2")
    assert _code(lambda: authorize(Mode.PAPER, other, a, kill_switch=ks, env={})) == "risk"


def test_testnet_needs_env(ks):
    assert _code(lambda: authorize(Mode.TESTNET, *_pair(), kill_switch=ks, env={})) == "testnet_disabled"
    authorize(Mode.TESTNET, *_pair(), kill_switch=ks, env={ENV_ALLOW_TESTNET: "1"})


def test_live_has_three_locks(ks):
    env = {ENV_LIVE: LIVE_ACK}
    assert _code(lambda: authorize(Mode.LIVE, *_pair(), kill_switch=ks, env={ENV_LIVE: "yes"})) == "live_disabled"
    assert _code(lambda: authorize(Mode.LIVE, *_pair(), kill_switch=ks, env=env)) == "key_unchecked"
    assert (
        _code(lambda: authorize(Mode.LIVE, *_pair(), kill_switch=ks, env=env, key_checked=True)) == "awaiting_approval"
    )
    authorize(Mode.LIVE, *_pair(), kill_switch=ks, env=env, key_checked=True, approver=lambda i, a: True)


def test_hitl_approver_roundtrip(tmp_path):
    from hitlwright import latest_request, write_decision

    approver = HitlApprover(tmp_path)
    intent, a = _pair()
    assert approver(intent, a) is False  # writes the request, pending
    req = latest_request(tmp_path / intent.client_order_id)
    assert req["priority"] == "critical" and req["source"] == "economia-trader"
    assert approver(intent, a) is False  # still pending, no duplicate request needed
    write_decision(tmp_path / intent.client_order_id, req["id"], response="approve", responder_id="user:maestro")
    assert approver(intent, a) is True


def test_hitl_approver_reject(tmp_path):
    from hitlwright import latest_request, write_decision

    approver = HitlApprover(tmp_path)
    intent, a = _pair()
    approver(intent, a)
    req = latest_request(tmp_path / intent.client_order_id)
    write_decision(tmp_path / intent.client_order_id, req["id"], response="reject")
    assert approver(intent, a) is False


def test_gate_report(ks):
    rep = gate_report(Mode.LIVE, kill_switch=ks, env={ENV_ALLOW_TESTNET: "1"})
    assert rep == {"mode": "live", "kill_switch": False, "testnet_enabled": True, "live_acknowledged": False}
