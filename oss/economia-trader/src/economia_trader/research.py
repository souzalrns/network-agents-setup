"""Research exports (decision of 2026-10-12: FinRL for research only, in its own environment).

FinRL (AI4Finance, MIT) trains reinforcement-learning agents on a long DataFrame with the columns
``date, open, high, low, close, volume, tic``, sorted by date and ticker. It pins old libraries
(``ccxt ^3``, ``alpaca-trade-api``, ray, selenium...), so it never shares an environment with the trader:
we only hand it our own klines as CSV. Nothing it trains is wired into the loop; see RESEARCH-FINRL.md.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .exchanges.base import Kline

FINRL_COLUMNS = ("date", "open", "high", "low", "close", "volume", "tic")


def finrl_rows(series: Mapping[str, Iterable[Kline]]) -> list[dict[str, Any]]:
    rows = []
    for tic, bars in series.items():
        for b in bars:
            dt = datetime.fromtimestamp(b.open_time_ms / 1000, tz=timezone.utc)
            date = dt.strftime("%Y-%m-%d") if (dt.hour, dt.minute) == (0, 0) else dt.strftime("%Y-%m-%d %H:%M:%S")
            rows.append(
                {
                    "date": date,
                    "open": str(b.open),
                    "high": str(b.high),
                    "low": str(b.low),
                    "close": str(b.close),
                    "volume": str(b.volume),
                    "tic": tic,
                }
            )
    return sorted(rows, key=lambda r: (r["date"], r["tic"]))


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> int:
    with Path(path).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FINRL_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    return len(rows)
