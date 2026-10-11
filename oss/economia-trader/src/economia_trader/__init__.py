"""economia-trader: an auditable trading core for AI agents — agents propose, a deterministic
risk engine and an execution gate decide, and every step lands in a hash-chained journal.

    from economia_trader import RiskLimits, TradeProposal, Trader, PaperBroker, Journal, Mode
    from economia_trader.exchanges import make_exchange

    limits = RiskLimits.from_mapping({"max_order_notional": "50", "max_loss_per_trade": "2",
                                      "max_daily_loss": "5", "allowed_symbols": ["BTCUSDT"]})
    trader = Trader(make_exchange("bybit", Mode.PAPER), mode=Mode.PAPER, limits=limits,
                    journal=Journal(".economia-trader/journal.jsonl"), broker=PaperBroker("1000"))
    trader.submit(TradeProposal("BTCUSDT", "buy", "0.0005", stop_loss="60000", proposer="my-agent"))

Paper by default. Bybit testnet and MEXC order validation need explicit environment locks;
real orders need a further acknowledgement, a key without withdraw permission and a human
approval per order (``safety``). Zero runtime dependencies.
"""

from __future__ import annotations

from .contracts import (
    SCHEMA_VERSION,
    EconomicEvent,
    Fill,
    OrderIntent,
    RiskAssessment,
    SimulationRun,
    TradeProposal,
)
from .journal import Journal, verify
from .paper import PaperBroker, PaperRejected
from .risk import PortfolioState, Position, RiskLimits, assess
from .safety import ExecutionBlocked, HitlApprover, KillSwitch, Mode, authorize
from .trader import Outcome, Trader

__version__ = "0.1.0"

__all__ = [
    "SCHEMA_VERSION",
    "EconomicEvent",
    "ExecutionBlocked",
    "Fill",
    "HitlApprover",
    "Journal",
    "KillSwitch",
    "Mode",
    "OrderIntent",
    "Outcome",
    "PaperBroker",
    "PaperRejected",
    "PortfolioState",
    "Position",
    "RiskAssessment",
    "RiskLimits",
    "SimulationRun",
    "TradeProposal",
    "Trader",
    "__version__",
    "assess",
    "authorize",
    "verify",
]
