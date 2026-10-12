"""Forecast confirmation on **Kronos** (shiyu-coder/Kronos, code MIT; weights NeoQuasar/* on Hugging Face),
a foundation model for candlesticks. Decided P-68: it **confirms or vetoes** an idea, never generates one
(P-69), and is proven in the backtest against the same version without it before it gates paper.

The forecast is probabilistic (sampled paths). We fix the seed, draw ``samples`` paths, and confirm only if
both hold over the next ``horizon`` bars:

- the mean predicted close is at least ``min_expected_return`` above the last close, and
- at least ``min_up_share`` of the paths end above the last close.

Kronos is not pip-installable (no setup.py; its code lives in a top-level ``model/`` folder). The loader
imports it from a pinned checkout (``KRONOS_COMMIT``) and refuses to shadow another ``model`` package.
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from statistics import fmean
from typing import Any

from .exchanges.base import Kline

KRONOS_COMMIT = "67b630e"
# (klines oldest->newest, horizon, samples, seed) -> list of paths, each a list of predicted closes
Forecaster = Callable[[list[Kline], int, int, int], list[list[float]]]


@dataclass
class ForecastOpinion:
    ticker: str
    confirms: bool
    rating: str
    expected_return: float | None
    up_share: float | None
    detail: str = ""


class ForecastConfirmer:
    name = "kronos"

    def __init__(
        self,
        forecaster: Forecaster,
        *,
        horizon: int = 5,
        samples: int = 10,
        seed: int = 42,
        min_expected_return: float = 0.01,
        min_up_share: float = 0.6,
        min_bars: int = 64,
        max_runs_per_day: int = 20,
    ) -> None:
        self.forecaster = forecaster
        self.horizon, self.samples, self.seed = horizon, samples, seed
        self.min_expected_return, self.min_up_share, self.min_bars = min_expected_return, min_up_share, min_bars
        self.max_runs_per_day = max_runs_per_day
        self._runs: dict[str, int] = {}

    def opinion(self, ticker: str, bars: list[Kline], day: str = "") -> ForecastOpinion:
        if len(bars) < self.min_bars:
            return ForecastOpinion(ticker, False, "NO_DATA", None, None, f"{len(bars)} bars < {self.min_bars}")
        if day and self._runs.get(day, 0) >= self.max_runs_per_day:
            return ForecastOpinion(ticker, False, "BUDGET", None, None, "daily forecast cap reached")
        if day:
            self._runs[day] = self._runs.get(day, 0) + 1
        last = float(bars[-1].close)
        paths = [p for p in self.forecaster(bars, self.horizon, self.samples, self.seed) if p]
        if not paths or last <= 0:
            return ForecastOpinion(ticker, False, "NO_FORECAST", None, None, "forecaster returned nothing")
        ends = [p[-1] for p in paths]
        expected = fmean(ends) / last - 1
        up_share = sum(1 for e in ends if e > last) / len(ends)
        ok = expected >= self.min_expected_return and up_share >= self.min_up_share
        return ForecastOpinion(
            ticker,
            ok,
            "UP" if ok else "NOT_UP",
            round(expected, 5),
            round(up_share, 3),
            f"{len(paths)} paths, {self.horizon} bars: E[r]={expected:.2%}, up={up_share:.0%}",
        )


def confirmer_for(forecaster: Forecaster, config: Any, **kw: Any) -> ForecastConfirmer:
    """A confirmer whose horizon and thresholds come from a versioned ``RunConfig``."""
    return ForecastConfirmer(
        forecaster,
        horizon=config.forecast_horizon,
        min_expected_return=float(config.forecast_min_expected_return),
        min_up_share=float(config.forecast_min_up_share),
        **kw,
    )


# ---- the Kronos plug ----


def load_kronos_package(repo_path: str | Path) -> Any:
    """Import ``<repo>/model`` from a pinned checkout.

    Kronos imports itself as ``model`` (``from model.module import *``), so the top-level name ``model`` is
    taken. We put the checkout on ``sys.path`` only for the import, and refuse if another ``model`` package
    is already loaded rather than shadow it.
    """
    root = Path(repo_path).resolve()
    init = root / "model" / "__init__.py"
    if not init.exists():
        raise RuntimeError(f"Kronos checkout not found at {repo_path} (git clone shiyu-coder/Kronos @ {KRONOS_COMMIT})")
    loaded = sys.modules.get("model")
    if loaded is not None:
        if Path(getattr(loaded, "__file__", "") or "").resolve() == init:
            return loaded
        raise RuntimeError("another top-level 'model' package is already imported; Kronos needs that name")
    sys.path.insert(0, str(root))
    try:
        return importlib.import_module("model")
    finally:
        sys.path.remove(str(root))


def kronos_forecaster(
    repo_path: str | Path,
    *,
    model: str = "NeoQuasar/Kronos-small",
    tokenizer: str = "NeoQuasar/Kronos-Tokenizer-base",
    max_context: int = 512,
    device: str = "cpu",
) -> Forecaster:
    """Kronos-small on CPU by default. Needs torch, pandas, einops, huggingface_hub, safetensors."""
    import pandas as pd
    import torch

    pkg = load_kronos_package(repo_path)
    predictor = pkg.KronosPredictor(
        pkg.Kronos.from_pretrained(model),
        pkg.KronosTokenizer.from_pretrained(tokenizer),
        device=device,
        max_context=max_context,
    )

    def forecast(bars: list[Kline], horizon: int, samples: int, seed: int) -> list[list[float]]:
        bars = bars[-max_context:]
        df = pd.DataFrame(
            {
                "open": [float(b.open) for b in bars],
                "high": [float(b.high) for b in bars],
                "low": [float(b.low) for b in bars],
                "close": [float(b.close) for b in bars],
                "volume": [float(b.volume) for b in bars],
            }
        )
        ts = pd.to_datetime([b.open_time_ms for b in bars], unit="ms")
        step = ts[-1] - ts[-2] if len(ts) > 1 else pd.Timedelta(days=1)
        future = pd.Series([ts[-1] + step * (i + 1) for i in range(horizon)])
        paths = []
        for i in range(samples):
            torch.manual_seed(seed + i)
            pred = predictor.predict(
                df=df,
                x_timestamp=pd.Series(ts),
                y_timestamp=future,
                pred_len=horizon,
                T=1.0,
                top_p=0.9,
                sample_count=1,
                verbose=False,
            )
            paths.append([float(x) for x in pred["close"].tolist()])
        return paths

    return forecast


# ---- backtest A/B: the same strategy with and without the confirmation ----


def with_forecast_confirm(strategy: Any, confirmer: ForecastConfirmer) -> Any:
    """Wrap a backtest strategy: buys pass only if the forecast (from bars so far) confirms."""

    def wrapped(bars: list[Kline], state: Any, limits: Any, symbol: str) -> Any:
        proposal = strategy(bars, state, limits, symbol)
        if proposal is None or proposal.side != "buy":
            return proposal
        return proposal if confirmer.opinion(symbol, bars).confirms else None

    wrapped.__name__ = f"{getattr(strategy, '__name__', 'strategy')}+kronos"
    return wrapped


def compare_summaries(base: dict[str, Any], test: dict[str, Any]) -> dict[str, Any]:
    keys = ("trades_closed", "win_rate", "return_pct", "max_drawdown_pct", "fees")
    out = {k: {"sem": base.get(k), "com": test.get(k)} for k in keys}
    out["melhora_retorno"] = Decimal(str(test.get("return_pct", 0))) > Decimal(str(base.get("return_pct", 0)))
    return out
