"""tokenwright: token-cost ledger + projective budget cap (fail-closed)."""

from __future__ import annotations

import json

import pytest

from tokenwright import (
    BudgetExceeded,
    CostUnknown,
    estimate_cost_usd,
    guard_next_call,
    ledger_cost_usd,
    prices_from_mapping,
    row_cost_usd,
    would_exceed,
)

PRICES = prices_from_mapping(
    {
        "m1": {"usd_per_1m_input": 1.0, "usd_per_1m_output": 2.0},
        "free": {"usd_per_1m_input": 0.0, "usd_per_1m_output": 0.0},
        "unpriced": {"usd_per_1m_input": None, "usd_per_1m_output": 2.0},  # dropped
    }
)


# ---- prices ----


def test_prices_keeps_only_confirmed():
    assert "m1" in PRICES and "free" in PRICES
    assert "unpriced" not in PRICES  # a null price is left out (fail-closed later)


# ---- estimate ----


def test_estimate_cost():
    # 1_000_000 in * 1.0 + 1_000_000 out * 2.0 = 3.0 USD
    assert estimate_cost_usd(1_000_000, 1_000_000, "m1", PRICES) == pytest.approx(3.0)


def test_estimate_zero_tokens_is_free_even_if_unpriced():
    assert estimate_cost_usd(0, 0, "whatever", PRICES) == 0.0


def test_estimate_unknown_model_fails_closed():
    with pytest.raises(CostUnknown):
        estimate_cost_usd(10, 10, "unpriced", PRICES)
    with pytest.raises(CostUnknown):
        estimate_cost_usd(10, 10, "missing", PRICES)


# ---- row cost: reasoning tokens via tokens_total ----


def test_row_cost_uses_total_minus_in_for_output():
    # tokens_total present: out = 1_000_000 - 200_000 = 800_000
    row = {"model": "m1", "tokens_in": 200_000, "tokens_total": 1_000_000}
    # 200k*1 + 800k*2 = 0.2 + 1.6 = 1.8 (per 1e6)
    assert row_cost_usd(row, PRICES) == pytest.approx(0.2e-6 * 1_000_000 + 1.6)


def test_row_cost_falls_back_to_tokens_out():
    row = {"model": "m1", "tokens_in": 1_000_000, "tokens_out": 1_000_000}
    assert row_cost_usd(row, PRICES) == pytest.approx(3.0)


def test_row_no_tokens_is_zero():
    assert row_cost_usd({"model": "missing"}, PRICES) == 0.0  # no tokens -> 0, no CostUnknown


# ---- ledger ----


def test_ledger_from_rows():
    rows = [
        {"model": "m1", "tokens_in": 1_000_000, "tokens_out": 0},  # 1.0
        {"model": "m1", "tokens_in": 0, "tokens_out": 1_000_000},  # 2.0
        {"note": "no tokens"},  # 0
    ]
    assert ledger_cost_usd(rows, PRICES) == pytest.approx(3.0)


def test_ledger_from_file_skips_bad_lines(tmp_path):
    p = tmp_path / "ledger.jsonl"
    p.write_text(
        json.dumps({"model": "m1", "tokens_in": 1_000_000, "tokens_out": 0})
        + "\n"
        + "{bad json\n\n"
        + json.dumps({"model": "m1", "tokens_in": 0, "tokens_out": 500_000})
        + "\n",
        encoding="utf-8",
    )
    assert ledger_cost_usd(p, PRICES) == pytest.approx(1.0 + 1.0)


def test_ledger_missing_file_is_zero(tmp_path):
    assert ledger_cost_usd(tmp_path / "nope.jsonl", PRICES) == 0.0


def test_ledger_unknown_model_fails_closed():
    with pytest.raises(CostUnknown):
        ledger_cost_usd([{"model": "missing", "tokens_in": 10}], PRICES)


# ---- budget cap (projective guard) ----


def test_would_exceed():
    assert would_exceed(0.04, 0.02, 0.05) is True
    assert would_exceed(0.01, 0.02, 0.05) is False


def test_guard_allows_under_cap():
    # next call: 1e6 in * 1.0 = 1.0 USD; spent 0, cap 2.0 -> ok
    assert guard_next_call(
        0.0, projected_in=1_000_000, projected_out=0, model="m1", prices=PRICES, cap_usd=2.0
    ) == pytest.approx(1.0)


def test_guard_blocks_over_cap():
    with pytest.raises(BudgetExceeded) as e:
        guard_next_call(1.5, projected_in=1_000_000, projected_out=0, model="m1", prices=PRICES, cap_usd=2.0)
    assert e.value.cap == 2.0 and e.value.spent == 1.5


def test_guard_fails_closed_on_unknown_price():
    with pytest.raises(CostUnknown):
        guard_next_call(0.0, projected_in=10, projected_out=10, model="missing", prices=PRICES, cap_usd=99.0)


# ---- CLI ----


def _prices_file(tmp_path):
    p = tmp_path / "prices.json"
    p.write_text(json.dumps({"m1": {"usd_per_1m_input": 1.0, "usd_per_1m_output": 2.0}}), encoding="utf-8")
    return str(p)


def test_cli_cost(tmp_path, capsys):
    from tokenwright.cli import main

    ledger = tmp_path / "l.jsonl"
    ledger.write_text(json.dumps({"model": "m1", "tokens_in": 1_000_000, "tokens_out": 0}) + "\n", encoding="utf-8")
    assert main(["cost", str(ledger), "--prices", _prices_file(tmp_path)]) == 0
    assert capsys.readouterr().out.strip() == "1.000000"


def test_cli_cost_over_cap(tmp_path):
    from tokenwright.cli import main

    ledger = tmp_path / "l.jsonl"
    ledger.write_text(json.dumps({"model": "m1", "tokens_in": 1_000_000, "tokens_out": 0}) + "\n", encoding="utf-8")
    assert main(["cost", str(ledger), "--prices", _prices_file(tmp_path), "--cap", "0.5"]) == 1


def test_cli_check_ok_and_exceed(tmp_path):
    from tokenwright.cli import main

    pf = _prices_file(tmp_path)
    assert (
        main(["check", "--spent", "0", "--in", "1000000", "--out", "0", "--model", "m1", "--prices", pf, "--cap", "2"])
        == 0
    )
    assert (
        main(
            ["check", "--spent", "1.5", "--in", "1000000", "--out", "0", "--model", "m1", "--prices", pf, "--cap", "2"]
        )
        == 1
    )
    assert (
        main(["check", "--spent", "0", "--in", "10", "--out", "10", "--model", "x", "--prices", pf, "--cap", "2"]) == 2
    )


def test_cli_version(capsys):
    from tokenwright.cli import main

    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0
    assert "tokenwright" in capsys.readouterr().out
