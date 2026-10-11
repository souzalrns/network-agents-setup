from __future__ import annotations

import json
import urllib.parse
from decimal import Decimal

import pytest

from economia_trader import RiskLimits


class FakeTransport:
    """Records every request; answers from a {path: (status, json)} table."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, method, url, headers, body):
        parsed = urllib.parse.urlsplit(url)
        self.calls.append(
            {
                "method": method,
                "url": url,
                "path": parsed.path,
                "query": dict(urllib.parse.parse_qsl(parsed.query)),
                "headers": dict(headers),
                "body": json.loads(body) if body else None,
                "raw_body": body,
            }
        )
        if parsed.path not in self.routes:
            return 404, {"retCode": 404, "retMsg": "no route", "code": 404, "msg": "no route"}
        return self.routes[parsed.path]


def bybit_ok(result):
    return 200, {"retCode": 0, "retMsg": "OK", "result": result}


@pytest.fixture
def limits():
    return RiskLimits.from_mapping(
        {
            "max_order_notional": "100",
            "max_loss_per_trade": "5",
            "max_daily_loss": "10",
            "allowed_symbols": ["BTCUSDT", "ETHUSDT"],
            "max_open_positions": 1,
        }
    )


D = Decimal
