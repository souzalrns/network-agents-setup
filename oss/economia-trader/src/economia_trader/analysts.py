"""LLM analysts on **TradingAgents** (Apache-2.0, TauricResearch): market, social/sentiment, news
and fundamentals analysts, a bull/bear debate, a trader and a risk discussion. We reuse the
whole graph and keep one rule of ours: **an analyst only confirms or vetoes; it never orders.**

How it is used: the deterministic whale screen picks 0-3 names; TradingAgents gives each a
second opinion; only ``Buy``/``Overweight`` lets the entry through to the risk engine and the
gate. ``Hold``/``Underweight``/``Sell``/``REVIEW`` veto it. That bounds the LLM cost to a few
runs a day (``max_runs_per_day``) and keeps the expensive, non-deterministic part out of sizing,
stops and execution.

Install (not on PyPI; pin the audited commit):
``pip install 'git+https://github.com/TauricResearch/TradingAgents@1394a3f'``. The provider and
models are TradingAgents' own config (``llm_provider``, ``quick_think_llm``, ``deep_think_llm``).
Keep ``TYPESAFE_API_KEY`` unset unless you want social posts sent to that service.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .contracts import now_iso

CONFIRM = frozenset({"buy", "overweight"})
REPORT_KEYS = (
    "market_report",
    "sentiment_report",
    "news_report",
    "fundamentals_report",
    "investment_plan",
    "final_trade_decision",
)


@dataclass
class Opinion:
    ticker: str
    trade_date: str
    rating: str
    confirms: bool
    evidence_path: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)


class TokenUsage:
    """A LangChain callback that adds up tokens per model (passed to TradingAgents' ``callbacks``)."""

    def __init__(self) -> None:
        self.by_model: dict[str, dict[str, int]] = {}

    def as_handler(self) -> Any:
        from langchain_core.callbacks import BaseCallbackHandler

        usage = self

        class _Handler(BaseCallbackHandler):
            def on_llm_end(self, response: Any, **kwargs: Any) -> None:
                for gens in response.generations or []:
                    for g in gens:
                        meta = getattr(getattr(g, "message", None), "usage_metadata", None) or {}
                        model = (getattr(getattr(g, "message", None), "response_metadata", None) or {}).get(
                            "model_name"
                        ) or (getattr(getattr(g, "message", None), "response_metadata", None) or {}).get("model", "?")
                        usage.add(model, int(meta.get("input_tokens", 0)), int(meta.get("output_tokens", 0)))

        return _Handler()

    def add(self, model: str, tokens_in: int, tokens_out: int) -> None:
        row = self.by_model.setdefault(model, {"in": 0, "out": 0, "calls": 0})
        row["in"] += tokens_in
        row["out"] += tokens_out
        row["calls"] += 1


# (ticker, trade_date) -> (final_state, rating)
Propagate = Callable[[str, str], tuple[dict[str, Any], str]]


class TradingAgentsAnalyst:
    def __init__(
        self,
        *,
        config: dict[str, Any] | None = None,
        evidence_dir: str | Path = ".economia-trader/evidence",
        max_runs_per_day: int = 3,
        propagate: Propagate | None = None,
    ) -> None:
        self.evidence_dir = Path(evidence_dir)
        self.max_runs_per_day = max_runs_per_day
        self.usage = TokenUsage()
        self._runs: dict[str, int] = {}
        if propagate is None:
            propagate = self._build(config or {})
        self._propagate = propagate

    def _build(self, overrides: dict[str, Any]) -> Propagate:
        try:
            from tradingagents.default_config import DEFAULT_CONFIG
            from tradingagents.graph.trading_graph import TradingAgentsGraph
        except ImportError as exc:
            raise RuntimeError(
                "TradingAgents is not installed: pip install 'git+https://github.com/TauricResearch/TradingAgents@1394a3f'"
            ) from exc
        graph = TradingAgentsGraph(config={**DEFAULT_CONFIG, **overrides}, callbacks=[self.usage.as_handler()])
        return lambda ticker, day: graph.propagate(ticker, day)

    def opinion(self, ticker: str, trade_date: str) -> Opinion:
        """Run the graph once. Over the daily budget it vetoes without calling any LLM."""
        if self._runs.get(trade_date, 0) >= self.max_runs_per_day:
            return Opinion(ticker, trade_date, "BUDGET", confirms=False)
        self._runs[trade_date] = self._runs.get(trade_date, 0) + 1
        state, rating = self._propagate(ticker, trade_date)
        rating = str(rating or "REVIEW")
        path = self.evidence_dir / f"{trade_date}_{ticker}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "ticker": ticker,
                    "trade_date": trade_date,
                    "rating": rating,
                    "observed_at": now_iso(),
                    "reports": {k: str(state.get(k, ""))[:20000] for k in REPORT_KEYS},
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return Opinion(
            ticker,
            trade_date,
            rating,
            rating.lower() in CONFIRM,
            str(path),
            usage=json.loads(json.dumps(self.usage.by_model)),
        )
