"""Walk-forward tuning: pick strategy parameters on the past, keep them only if they also win on data they
never saw. Nothing here trades; every run goes through the same risk engine and paper broker as
``backtest`` (``run_backtest``).

The bars are cut into ``folds + 1`` consecutive segments. For fold ``i`` every candidate is scored on
segment ``i`` (train); the best one is then run on segment ``i + 1`` (test), which it never saw, next to
the current config (the baseline). That is the out-of-sample (OOS) evidence: it measures the re-tuning
procedure, fold by fold, never a final pick on data that helped choose it.

- the config to deploy is the pick of the last fold (the most recent window); ``picked_in_folds`` says how
  stable that choice was;
- it is **accepted** only if, out of sample, the picks beat the baseline's mean score by more than
  ``min_edge`` points (a hair's difference is noise, not a reason to change), the worst drawdown stays
  under ``max_drawdown_pct`` and they closed at least ``min_trades`` trades (no trades is not a skill).

A grid candidate that does not fit the risk limits at its worst (``GridConfig.problems``) is never scored:
tuning cannot propose a config the live loop would refuse. Each segment is replayed on its own, so a
relative grid anchors on the segment's first bar, as the live loop anchors on the first price it sees.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from .backtest import run_backtest, sma_cross
from .exchanges.base import Kline
from .grid import GridConfig, grid_strategy
from .risk import RiskLimits

STRATEGIES = ("grid", "sma")
SMA_KEYS = ("fast", "slow", "stop_pct")
MAX_CANDIDATES = 500


def bars_hash(bars: Sequence[Kline]) -> str:
    """Fingerprint of the data, so a tuning result can be reproduced on the same bars."""
    blob = json.dumps([[b.open_time_ms, str(b.open), str(b.high), str(b.low), str(b.close)] for b in bars])
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def candidates(base: Mapping[str, Any], search: Mapping[str, Sequence[Any]]) -> list[dict[str, Any]]:
    """Every combination of the ``search`` values over ``base`` (base first, as-is)."""
    keys = sorted(search)
    out = [dict(base)]
    for combo in itertools.product(*(list(search[k]) for k in keys)):
        c = {**base, **dict(zip(keys, combo, strict=True))}
        if c not in out:
            out.append(c)
    if len(out) > MAX_CANDIDATES:
        raise ValueError(f"{len(out)} candidates > {MAX_CANDIDATES}: narrow the search")
    return out


def segments(bars: Sequence[Kline], folds: int) -> list[list[Kline]]:
    if folds < 1:
        raise ValueError("folds must be >= 1")
    n = len(bars) // (folds + 1)
    if n < 20:
        raise ValueError(f"{len(bars)} bars are too few for {folds} folds (need >= 20 per segment)")
    return [list(bars[i * n : (i + 1) * n]) for i in range(folds + 1)]


def score(summary: Mapping[str, Any], dd_weight: Decimal) -> Decimal:
    """Return minus a drawdown penalty, both in percent."""
    return Decimal(summary["return_pct"]) - dd_weight * Decimal(summary["max_drawdown_pct"])


def _strategy(kind: str, params: Mapping[str, Any], bars: Sequence[Kline], limits: RiskLimits):
    """(strategy, refusal reasons). A refused candidate is never run."""
    if kind == "grid":
        cfg = GridConfig.from_mapping(params).anchor(bars[0].close)
        problems = cfg.problems(limits)
        return (None, problems) if problems else (grid_strategy(cfg, limits), [])
    unknown = set(params) - set(SMA_KEYS)
    if unknown:
        raise ValueError(f"unknown sma keys: {sorted(unknown)}")
    fast, slow = int(params.get("fast", 10)), int(params.get("slow", 30))
    if not 1 <= fast < slow:
        return None, [f"need 1 <= fast < slow (got {fast}, {slow})"]
    return sma_cross(fast, slow, Decimal(str(params.get("stop_pct", "0.03")))), []


def _run(kind, params, bars, limits, cash, symbol, exchange) -> dict[str, Any] | None:
    strat, _ = _strategy(kind, params, bars, limits)
    if strat is None:
        return None
    return run_backtest(list(bars), strat, symbol=symbol, limits=limits, cash=cash, exchange_name=exchange).summary()


def walk_forward(
    bars: Sequence[Kline],
    *,
    kind: str,
    base: Mapping[str, Any],
    search: Mapping[str, Sequence[Any]],
    limits: RiskLimits,
    symbol: str,
    cash: Decimal | str = "1000",
    folds: int = 4,
    dd_weight: Decimal | str = "0.5",
    min_trades: int = 3,
    min_edge: Decimal | str = "0.1",
    max_drawdown_pct: Decimal | str | None = None,
    exchange: str = "bybit",
) -> dict[str, Any]:
    if kind not in STRATEGIES:
        raise ValueError(f"strategy must be one of {STRATEGIES}")
    dd_w, edge = Decimal(str(dd_weight)), Decimal(str(min_edge))
    if max_drawdown_pct is None:
        max_drawdown_pct = Decimal(str(base.get("max_drawdown_pct", "0.15"))) * 100 if kind == "grid" else 15
    max_dd = Decimal(str(max_drawdown_pct))
    cands = candidates(base, search)
    segs = segments(bars, folds)
    run = lambda p, seg: _run(kind, p, seg, limits, cash, symbol, exchange)  # noqa: E731

    fold_rows, picks = [], []
    refused: dict[int, list[str]] = {}
    train_scores: dict[int, list[Decimal]] = {}
    for i in range(folds):
        train, test = segs[i], segs[i + 1]
        scored = []
        for ci, c in enumerate(cands):
            s = run(c, train)
            if s is None:
                refused.setdefault(ci, _strategy(kind, c, train, limits)[1])
                continue
            sc = score(s, dd_w)
            train_scores.setdefault(ci, []).append(sc)
            scored.append((sc, ci, s))
        if not scored:
            fold_rows.append({"fold": i + 1, "pick": None, "note": "every candidate refused by the risk limits"})
            continue
        best_sc, best_ci, best_train = max(scored, key=lambda t: (t[0], -t[1]))
        picks.append(best_ci)
        oos, baseline = run(cands[best_ci], test), run(cands[0], test)
        fold_rows.append(
            {
                "fold": i + 1,
                "train_range_ms": [train[0].open_time_ms, train[-1].open_time_ms],
                "test_range_ms": [test[0].open_time_ms, test[-1].open_time_ms],
                "pick": best_ci,
                "train_score": str(best_sc),
                "train": best_train,
                "oos": oos,
                "baseline_oos": baseline,
            }
        )

    if not picks:
        return _result(bars, kind, cands, folds, fold_rows, refused, None, None, ["no candidate fits the limits"])
    # Out-of-sample evidence = each fold's pick on the NEXT segment, which it never saw. (Running one final pick
    # on every test segment would reuse segments that trained later folds: selection bias.)
    scored_rows = [r for r in fold_rows if r.get("pick") is not None]
    oos = _aggregate([r["oos"] for r in scored_rows if r["oos"]], dd_w)
    base_oos = _aggregate([r["baseline_oos"] for r in scored_rows if r["baseline_oos"]], dd_w)
    # what to deploy: the pick of the most recent fold (trained on the latest window before the last test)
    chosen = scored_rows[-1]["pick"]
    count = Counter(picks)
    mean_train = {ci: sum(train_scores[ci], Decimal(0)) / len(train_scores[ci]) for ci in count}

    reasons: list[str] = []
    notes: list[str] = []
    if not oos["runs"]:
        reasons.append("every pick was refused on its test segment")
    else:
        gain = Decimal(oos["mean_score"]) - Decimal(base_oos["mean_score"]) if base_oos["runs"] else None
        if not base_oos["runs"]:
            notes.append(
                f"the current config does not fit the limits ({'; '.join(refused.get(0, []))}): nothing to compare with"
            )
        if gain is not None and gain <= edge:
            reasons.append(
                f"out of sample it does not beat the current config by more than {edge} "
                f"({oos['mean_score']} vs {base_oos['mean_score']})"
            )
        if Decimal(oos["worst_drawdown_pct"]) > max_dd:
            reasons.append(f"out-of-sample drawdown {oos['worst_drawdown_pct']}% > {max_dd}%")
        if oos["trades_closed"] < min_trades:
            reasons.append(f"only {oos['trades_closed']} trades closed out of sample (< {min_trades})")
    verdict = {
        "chosen": chosen,
        "params": cands[chosen],
        "picked_in_folds": count[chosen],
        "picks_per_fold": picks,
        "mean_train_score": str(mean_train[chosen]),
        "oos": oos,
        "baseline_oos": base_oos,
        "overfit_gap": str(mean_train[chosen] - Decimal(oos["mean_score"])) if oos["runs"] else None,
        "notes": notes,
    }
    return _result(bars, kind, cands, folds, fold_rows, refused, verdict, chosen, reasons)


def _aggregate(runs: list[dict[str, Any]], dd_w: Decimal) -> dict[str, Any]:
    if not runs:
        return {"runs": 0, "mean_score": "0", "mean_return_pct": "0", "worst_drawdown_pct": "0", "trades_closed": 0}
    n = len(runs)
    return {
        "runs": n,
        "mean_score": str((sum((score(r, dd_w) for r in runs), Decimal(0)) / n).quantize(Decimal("0.01"))),
        "mean_return_pct": str(
            (sum((Decimal(r["return_pct"]) for r in runs), Decimal(0)) / n).quantize(Decimal("0.01"))
        ),
        "worst_drawdown_pct": str(max(Decimal(r["max_drawdown_pct"]) for r in runs)),
        "trades_closed": sum(int(r["trades_closed"]) for r in runs),
        "rejected_by_risk": sum(int(r["rejected_by_risk"]) for r in runs),
    }


def _result(bars, kind, cands, folds, fold_rows, refused, verdict, chosen, reasons) -> dict[str, Any]:
    accepted = chosen is not None and not reasons
    out: dict[str, Any] = {
        "strategy": kind,
        "bars": len(bars),
        "bars_hash": bars_hash(bars),
        "from_ms": bars[0].open_time_ms if bars else None,
        "to_ms": bars[-1].open_time_ms if bars else None,
        "folds": folds,
        "candidates": len(cands),
        "refused_by_limits": {str(k): v for k, v in sorted(refused.items())},
        "per_fold": fold_rows,
        "verdict": verdict,
        "accepted": accepted,
        "reasons": reasons or (["accepted: beats the current config out of sample"] if accepted else []),
    }
    if accepted and kind == "grid":
        out["config_hash"] = GridConfig.from_mapping(
            cands[chosen]
        ).version  # of the file; a paper run logs the anchored one
    return out
