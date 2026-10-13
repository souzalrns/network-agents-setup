"""US stocks/ETFs through Alpaca's official SDK, **alpaca-py** (Apache-2.0).

Alpaca's paper account (free, broker-side simulation, same API) is this adapter's "testnet"
rung. Market data needs a key even for the free IEX feed. The Trading API exposes no
withdrawal endpoint, so ``can_withdraw`` is False by API design.

``pip install economia-trader[stocks]``. ``trading=`` / ``data=`` inject clients (tests).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Literal

from ..contracts import OrderIntent, dec
from .base import Credentials, ExchangeError, KeyCheck, Kline, OrderStatus, Ticker, check_interval

_STATUS = {
    "filled": "filled",
    "partially_filled": "partially_filled",
    "canceled": "canceled",
    "expired": "canceled",
    "rejected": "rejected",
    "done_for_day": "canceled",
}
_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AlpacaPy:
    name = "alpaca"
    supports_testnet = True  # the paper account

    def __init__(
        self,
        network: Literal["paper", "live"] = "paper",
        *,
        credentials: Credentials | None = None,
        trading: Any = None,
        data: Any = None,
        allow_live_orders: bool = False,
        feed: str = "iex",
        clock: Any = None,
    ) -> None:
        if network not in ("paper", "live"):
            raise ValueError(f"network must be paper|live, got {network!r}")
        self.network = network
        self.allow_live_orders = allow_live_orders
        self.feed = feed
        self._clock = clock or _now
        if trading is None or data is None:
            if credentials is None:
                raise ExchangeError("alpaca: needs ALPACA_API_KEY / ALPACA_SECRET_KEY (paper keys are free)")
            try:
                from alpaca.data.historical import StockHistoricalDataClient
                from alpaca.trading.client import TradingClient
            except ImportError as exc:
                raise ExchangeError("alpaca-py is not installed: pip install 'economia-trader[stocks]'") from exc
            trading = trading or TradingClient(credentials.key_id, credentials.signing_key, paper=network == "paper")
            data = data or StockHistoricalDataClient(credentials.key_id, credentials.signing_key)
        self.trading, self.data = trading, data

    def _call(self, what: str, fn: Any, *args: Any) -> Any:
        try:
            from alpaca.common.exceptions import APIError
        except ImportError:  # pragma: no cover
            APIError = RuntimeError
        try:
            return fn(*args)
        except APIError as exc:
            raise ExchangeError(f"alpaca {what}: {exc}") from exc

    # ---- market data ----

    def ticker(self, symbol: str) -> Ticker:
        from alpaca.data.requests import StockLatestQuoteRequest, StockLatestTradeRequest

        sym = symbol.upper()
        trade = self._call(
            "latest trade",
            self.data.get_stock_latest_trade,
            StockLatestTradeRequest(symbol_or_symbols=sym, feed=self.feed),
        ).get(sym)
        quote = self._call(
            "latest quote",
            self.data.get_stock_latest_quote,
            StockLatestQuoteRequest(symbol_or_symbols=sym, feed=self.feed),
        ).get(sym)
        if trade is None or not trade.price:
            raise ExchangeError(f"alpaca: no trades for {symbol}")
        return Ticker(
            symbol=sym,
            last=dec(trade.price),
            bid=dec(quote.bid_price) if quote is not None and quote.bid_price else None,
            ask=dec(quote.ask_price) if quote is not None and quote.ask_price else None,
        )

    def klines(self, symbol: str, interval: str, limit: int = 200) -> list[Kline]:
        check_interval(interval)
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

        amount, unit = {
            "1m": (1, TimeFrameUnit.Minute),
            "5m": (5, TimeFrameUnit.Minute),
            "15m": (15, TimeFrameUnit.Minute),
            "1h": (1, TimeFrameUnit.Hour),
            "4h": (4, TimeFrameUnit.Hour),
            "1d": (1, TimeFrameUnit.Day),
        }[interval]
        sym = symbol.upper()
        req = StockBarsRequest(
            symbol_or_symbols=sym,
            timeframe=TimeFrame(amount, unit),
            start=self._clock() - timedelta(minutes=_MINUTES[interval] * limit * 5),  # bars only in market hours
            limit=limit,
            feed=self.feed,
        )
        bars = self._call("bars", self.data.get_stock_bars, req).data.get(sym, [])
        out = [
            Kline(
                int(b.timestamp.timestamp() * 1000), dec(b.open), dec(b.high), dec(b.low), dec(b.close), dec(b.volume)
            )
            for b in bars
        ]
        return sorted(out, key=lambda k: k.open_time_ms)[-limit:]

    # ---- account ----

    def check_key(self) -> KeyCheck:
        acc = self._call("account", self.trading.get_account)
        status = getattr(acc.status, "value", acc.status)
        can_trade = str(status) == "ACTIVE" and not acc.trading_blocked and not acc.account_blocked
        return KeyCheck(
            can_trade=bool(can_trade),
            can_withdraw=False,  # the Trading API exposes no withdrawal endpoint
            read_only=not can_trade,
            detail={
                "status": str(status),
                "trading_blocked": acc.trading_blocked,
                "account_blocked": acc.account_blocked,
                "pattern_day_trader": acc.pattern_day_trader,
                "network": self.network,
            },
        )

    # ---- orders ----

    def place_order(self, intent: OrderIntent) -> dict[str, Any]:
        if self.network == "live" and not self.allow_live_orders:
            raise ExchangeError("alpaca: live orders are disabled in this adapter instance")
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

        common = {
            "symbol": intent.symbol.upper(),
            "qty": float(intent.qty),
            "side": OrderSide.BUY if intent.side == "buy" else OrderSide.SELL,
            "time_in_force": TimeInForce.DAY,  # fractional orders must be DAY
            "client_order_id": intent.client_order_id,
        }
        if intent.order_type == "limit":
            req = LimitOrderRequest(**common, limit_price=float(intent.price))  # type: ignore[arg-type]
        else:
            req = MarketOrderRequest(**common)
        order = self._call("submit_order", self.trading.submit_order, req)
        return {
            "exchange": "alpaca",
            "network": self.network,
            "order_id": str(getattr(order, "id", "")),
            "symbol": common["symbol"],
            "side": intent.side,
            "type": intent.order_type,
            "qty": format(intent.qty.normalize(), "f"),
            "client_order_id": intent.client_order_id,
        }

    # ---- reconciliation (paper account / live) ----

    def order_status(self, symbol: str, order_id: str) -> OrderStatus:
        o = self._call("get_order", self.trading.get_order_by_id, order_id)
        raw = str(getattr(o.status, "value", o.status)).lower()
        filled = dec(o.filled_qty or 0)
        status = _STATUS.get(raw, "open")
        if status == "canceled" and filled > 0:
            status = "filled"
        avg = o.filled_avg_price
        return OrderStatus(str(o.id), status, filled, dec(avg) if avg else None)

    def place_stop(self, symbol: str, qty: Decimal, stop_price: Decimal, client_order_id: str) -> dict[str, Any]:
        if self.network == "live" and not self.allow_live_orders:
            raise ExchangeError("alpaca: live orders are disabled in this adapter instance")
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import StopOrderRequest

        whole = qty == qty.to_integral_value()
        req = StopOrderRequest(
            symbol=symbol.upper(),
            qty=float(qty),
            side=OrderSide.SELL,
            # fractional orders must be DAY: the trader re-places the stop when the exchange drops it
            time_in_force=TimeInForce.GTC if whole else TimeInForce.DAY,
            stop_price=float(stop_price),
            client_order_id=client_order_id,
        )
        o = self._call("submit_stop", self.trading.submit_order, req)
        return {
            "order_id": str(getattr(o, "id", "")),
            "symbol": symbol.upper(),
            "qty": str(qty),
            "stop": str(stop_price),
            "client_order_id": client_order_id,
            "tif": "gtc" if whole else "day",
        }

    def cancel_order(self, symbol: str, order_id: str) -> None:
        self._call("cancel_order", self.trading.cancel_order_by_id, order_id)

    def position_qty(self, symbol: str) -> Decimal:
        try:
            from alpaca.common.exceptions import APIError
        except ImportError:  # pragma: no cover
            APIError = RuntimeError
        try:
            pos = self.trading.get_open_position(symbol.upper())
        except APIError as exc:
            if "position does not exist" in str(exc).lower() or getattr(exc, "status_code", None) == 404:
                return Decimal(0)
            raise ExchangeError(f"alpaca position: {exc}") from exc
        return dec(pos.qty)

    def account_equity(self, marks: dict[str, Decimal]) -> Decimal:
        return dec(self._call("account", self.trading.get_account).equity)
