from decimal import Decimal as D

import pytest

from economia_trader import PortfolioState, Position, RiskLimits, TradeProposal, assess


def _buy(qty="0.001", stop="49000", **kw):
    return TradeProposal("BTCUSDT", "buy", qty, stop_loss=stop, **kw)


def test_approves_within_limits(limits):
    a = assess(_buy(), mark_price=D("50000"), limits=limits, state=PortfolioState())
    assert a.approved, a.reasons
    assert a.notional == D("50.000")
    # 0.001 * 1000 + 50 * 0.001 * 2 = 1.1
    assert a.loss_at_stop == D("1.1000")


def test_buy_without_stop_rejected(limits):
    a = assess(_buy(stop=None), mark_price=D("50000"), limits=limits, state=PortfolioState())
    assert not a.approved and "buy without stop_loss" in a.reasons


def test_stop_above_entry_rejected(limits):
    a = assess(_buy(stop="51000"), mark_price=D("50000"), limits=limits, state=PortfolioState())
    assert any("below the entry" in r for r in a.reasons)


def test_notional_cap(limits):
    a = assess(_buy(qty="0.01", stop="49900"), mark_price=D("50000"), limits=limits, state=PortfolioState())
    assert any("max_order_notional" in r for r in a.reasons)


def test_loss_at_stop_cap(limits):
    a = assess(_buy(qty="0.0019", stop="45000"), mark_price=D("50000"), limits=limits, state=PortfolioState())
    assert any("max_loss_per_trade" in r for r in a.reasons)


def test_symbol_not_allowed(limits):
    p = TradeProposal("DOGEUSDT", "buy", "10", stop_loss="0.09")
    a = assess(p, mark_price=D("0.1"), limits=limits, state=PortfolioState())
    assert any("allowed_symbols" in r for r in a.reasons)


def test_daily_cap_blocks_buys_but_allows_exits(limits):
    state = PortfolioState(positions={"BTCUSDT": Position(D("0.001"), D("50000"))}, realized_today=D("-10"))
    assert not assess(_buy(), mark_price=D("50000"), limits=limits, state=state).approved
    sell = TradeProposal("BTCUSDT", "sell", "0.001")
    assert assess(sell, mark_price=D("50000"), limits=limits, state=state).approved


def test_remaining_daily_budget(limits):
    state = PortfolioState(realized_today=D("-9.5"))
    a = assess(_buy(), mark_price=D("50000"), limits=limits, state=state)
    assert any("remaining daily loss budget" in r for r in a.reasons)


def test_sell_without_position_rejected(limits):
    a = assess(TradeProposal("BTCUSDT", "sell", "0.001"), mark_price=D("50000"), limits=limits, state=PortfolioState())
    assert any("no shorting" in r for r in a.reasons)


def test_sell_more_than_held(limits):
    state = PortfolioState(positions={"BTCUSDT": Position(D("0.001"), D("50000"))})
    a = assess(TradeProposal("BTCUSDT", "sell", "0.002"), mark_price=D("50000"), limits=limits, state=state)
    assert any("> held" in r for r in a.reasons)


def test_max_open_positions(limits):
    state = PortfolioState(positions={"ETHUSDT": Position(D("0.01"), D("3000"))})
    a = assess(_buy(), mark_price=D("50000"), limits=limits, state=state)
    assert any("max_open_positions" in r for r in a.reasons)


def test_limit_price_far_from_mark(limits):
    a = assess(_buy(entry_price="45000", stop="44000"), mark_price=D("50000"), limits=limits, state=PortfolioState())
    assert any("away from mark" in r for r in a.reasons)


def test_limits_must_be_explicit():
    with pytest.raises(ValueError, match="missing: max_daily_loss"):
        RiskLimits.from_mapping({"max_order_notional": "1", "max_loss_per_trade": "1", "allowed_symbols": ["X"]})
    with pytest.raises(ValueError, match="cannot exceed"):
        RiskLimits.from_mapping(
            {"max_order_notional": "1", "max_loss_per_trade": "5", "max_daily_loss": "1", "allowed_symbols": ["X"]}
        )
    with pytest.raises(ValueError, match="non-empty"):
        RiskLimits.from_mapping(
            {"max_order_notional": "1", "max_loss_per_trade": "1", "max_daily_loss": "1", "allowed_symbols": []}
        )
