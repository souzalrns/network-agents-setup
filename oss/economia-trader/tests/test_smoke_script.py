"""The testnet smoke script (examples/smoke_testnet.py) runs end to end against a real ccxt client with
every network call recorded offline, so the commands in SMOKE-TESTNET.md cannot drift from the API."""

import importlib.util
from pathlib import Path

import pytest
from conftest import offline_ccxt

from economia_trader.safety import ENV_ALLOW_TESTNET

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _script():
    spec = importlib.util.spec_from_file_location("smoke_testnet", EXAMPLES / "smoke_testnet.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("venue", ["bybit", "bybiteu"])  # bybiteu: Bybit EU, for PT (#201)
def test_smoke_cycle_offline(tmp_path, venue):
    env = {ENV_ALLOW_TESTNET: "1", "BYBIT_API_KEY": "k-offline", "BYBIT_API_SECRET": "s-offline"}
    client = offline_ccxt(venue)
    ok = _script().smoke(venue, "BTCUSDT", "0.0002", EXAMPLES / "limits.example.json", tmp_path, client=client, env=env)
    assert ok
    sells = [c for c in client.calls if c[0] == "create_order" and c[1][2] == "sell"]
    assert len(sells) == 2  # the resting stop (placed after the buy) + the one exit; the stop was cancelled first
    assert [c[0] for c in client.calls].count("cancel_order") == 1


def test_smoke_refuses_without_the_testnet_lock(tmp_path):
    env = {"BYBIT_API_KEY": "k-offline", "BYBIT_API_SECRET": "s-offline"}  # no ECONOMIA_TRADER_ALLOW_TESTNET
    client = offline_ccxt("bybit")
    ok = _script().smoke(
        "bybit", "BTCUSDT", "0.0002", EXAMPLES / "limits.example.json", tmp_path, client=client, env=env
    )
    assert not ok
    assert not [c for c in client.calls if c[0] == "create_order"]
