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

A second analyst, **ai-hedge-fund** (virattt, MIT), runs in its own virtualenv: see ``AiHedgeFundAnalyst``.
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


def langfuse_handler(env: Any = None) -> Any:
    """Optional tracing of every agent step (prompts, tool calls, tokens, latency) in **Langfuse**
    (MIT core, self-hostable). On only when LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set
    (LANGFUSE_HOST for self-hosting) and ``pip install 'economia-trader[tracing]'``."""
    import os

    env = os.environ if env is None else env
    if not (env.get("LANGFUSE_PUBLIC_KEY") and env.get("LANGFUSE_SECRET_KEY")):
        return None
    try:
        from langfuse.langchain import CallbackHandler
    except ImportError:
        return None
    return CallbackHandler()


# (ticker, trade_date) -> (final_state, rating)
Propagate = Callable[[str, str], tuple[dict[str, Any], str]]


class TradingAgentsAnalyst:
    name = "tradingagents"

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
        callbacks = [self.usage.as_handler()]
        tracer = langfuse_handler()
        if tracer is not None:
            callbacks.append(tracer)
        graph = TradingAgentsGraph(config={**DEFAULT_CONFIG, **overrides}, callbacks=callbacks)
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


# ---- ai-hedge-fund (virattt, MIT): investor personas as a second opinion (P-59) ----

AIHF_VERSION = "2.5.0"
AIHF_PERSONAS = ("buffett", "munger", "graham", "lynch", "druckenmiller")
# Env passed to ai-hedge-fund's process: its data + LLM keys only, never exchange keys.
_AIHF_ENV = (
    "PATH",
    "HOME",
    "LANG",
    "HTTPS_PROXY",
    "HTTP_PROXY",
    "NO_PROXY",
    "SSL_CERT_FILE",
    "REQUESTS_CA_BUNDLE",
    "FINANCIAL_DATASETS_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "DEEPSEEK_API_KEY",
    "XAI_API_KEY",
    "KIMI_API_KEY",
)
# (request) -> reply, both JSON-shaped; the default runs aihf_bridge.py in ai-hedge-fund's own venv.
Bridge = Callable[[dict[str, Any]], dict[str, Any]]


def subprocess_bridge(python: str | Path, *, timeout_s: float = 600, env: Any = None) -> Bridge:
    """Run ``aihf_bridge.py`` with the interpreter of ai-hedge-fund's virtualenv (``pipx install aihf``)."""
    import os
    import subprocess  # nosec B404 - fixed argv, no shell

    script = Path(__file__).with_name("aihf_bridge.py")
    source = os.environ if env is None else env
    child_env = {k: source[k] for k in _AIHF_ENV if k in source}

    def run(request: dict[str, Any]) -> dict[str, Any]:
        # argv is fixed: [the venv's python, -I, our own bridge script]; the request goes on stdin, never argv.
        argv = [str(python), "-I", str(script)]
        proc = subprocess.run(  # noqa: S603  # nosec B603  # nosemgrep
            argv,
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=child_env,
            check=False,
        )
        if proc.returncode != 0:
            tail = (proc.stderr or "").strip().splitlines()[-1:] or ["no stderr"]
            raise RuntimeError(f"ai-hedge-fund exited {proc.returncode}: {tail[0][:300]}")
        return json.loads(proc.stdout)

    return run


class AiHedgeFundAnalyst:
    """Investor personas (Buffett, Munger, Graham, Lynch, Druckenmiller) from **ai-hedge-fund** reason over a
    point-in-time fundamentals snapshot. Confirms only when, among the personas that formed a view, the mean
    conviction is at least ``min_conviction`` and at least ``min_bullish_share`` are bullish. Every failure
    (process, data, no view, budget) vetoes. It never orders."""

    name = "ai-hedge-fund"

    def __init__(
        self,
        *,
        bridge: Bridge,
        personas: tuple[str, ...] | list[str] = ("buffett", "lynch", "druckenmiller"),
        model: str = "gemini-3.8-flash",
        min_conviction: float = 0.2,
        min_bullish_share: float = 0.5,
        evidence_dir: str | Path = ".economia-trader/evidence",
        max_runs_per_day: int = 5,
    ) -> None:
        unknown = sorted(set(personas) - set(AIHF_PERSONAS))
        if unknown or not personas:
            raise ValueError(f"unknown ai-hedge-fund personas {unknown}; choose from {AIHF_PERSONAS}")
        if model.startswith("jev"):
            raise ValueError("TypeSafe (jev-*) models are not allowed: they send data to a third-party service")
        self.bridge, self.personas, self.model = bridge, tuple(personas), model
        self.min_conviction, self.min_bullish_share = min_conviction, min_bullish_share
        self.evidence_dir = Path(evidence_dir)
        self.max_runs_per_day = max_runs_per_day
        self._runs: dict[str, int] = {}
        self.calls: dict[str, dict[str, int]] = {}

    def opinion(self, ticker: str, trade_date: str) -> Opinion:
        if self._runs.get(trade_date, 0) >= self.max_runs_per_day:
            return Opinion(ticker, trade_date, "BUDGET", confirms=False)
        self._runs[trade_date] = self._runs.get(trade_date, 0) + 1
        request = {"ticker": ticker, "date": trade_date, "personas": list(self.personas), "model": self.model}
        try:
            reply = self.bridge(request)
            signals = [s for s in reply.get("signals", []) if isinstance(s, dict)]
        except Exception as exc:  # a broken process or data source vetoes, never crashes the tick
            return Opinion(ticker, trade_date, f"ERROR ({type(exc).__name__})", confirms=False)
        views = [s for s in signals if not s.get("abstained")]
        row = self.calls.setdefault(self.model, {"calls": 0, "cached": 0})
        row["calls"] += sum(1 for s in views if not s.get("cached"))
        row["cached"] += sum(1 for s in views if s.get("cached"))
        if views:
            mean = sum(float(s["value"]) for s in views) / len(views)
            ups = sum(1 for s in views if float(s["value"]) > 0)
            ok = mean >= self.min_conviction and ups / len(views) >= self.min_bullish_share
            rating = f"{'BULLISH' if ok else 'NOT_BULLISH'} {mean:+.2f} ({ups}/{len(views)})"
        else:
            ok, rating = False, "NO_VIEW"
        path = self.evidence_dir / f"{trade_date}_{ticker}_aihf.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "ticker": ticker,
                    "trade_date": trade_date,
                    "rating": rating,
                    "observed_at": now_iso(),
                    "aihf": AIHF_VERSION,
                    "model": self.model,
                    "signals": signals,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return Opinion(ticker, trade_date, rating, ok, str(path), usage=json.loads(json.dumps(self.calls)))
