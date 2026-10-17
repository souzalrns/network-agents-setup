import json
from decimal import Decimal as D
from pathlib import Path

import pytest

from economia_trader import RiskLimits
from economia_trader.alerts import (
    Alert,
    AlertWatcher,
    email_sender,
    senders_from_env,
    telegram_sender,
    webhook_sender,
)
from economia_trader.cli import main
from economia_trader.exchanges.base import ExchangeError, Ticker
from economia_trader.grid import GridBot, GridConfig
from economia_trader.journal import Journal
from economia_trader.safety import Mode

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
LIMITS = RiskLimits.from_mapping(json.loads((EXAMPLES / "limits.example.json").read_text()))


class Inbox:
    def __init__(self, fail=False):
        self.got, self.fail = [], fail

    def __call__(self, alert):
        if self.fail:
            raise ConnectionError("channel down")
        self.got.append(alert)


def watcher(tmp, *senders, **kw):
    return AlertWatcher(tmp, list(senders), **kw)


# ---- rules ----


def test_auto_kill_and_grid_refused_alert_once(tmp_path):
    j = Journal(tmp_path / "journal.jsonl")
    j.append("run", {})
    j.append("auto_kill", {"reason": "drawdown 16.0% from peak 120.00"})
    j.append("grid_refused", {"problems": ["a full stop-out loses 9.00 > max_daily_loss 5"]})
    inbox = Inbox()
    w = watcher(tmp_path, inbox)
    sent = w.check()
    assert [a.rule for a in inbox.got] == ["auto_kill", "grid_refused"]
    assert inbox.got[0].level == "critical" and "drawdown 16.0%" in inbox.got[0].detail
    assert sent[0]["channels"] == {"custom": "ok"}
    assert w.check() == [] and len(inbox.got) == 2  # the offset: nothing is sent twice
    j.append("auto_kill", {"reason": "3 ticks in a row without the exchange"})
    w.check()
    assert len(inbox.got) == 3


def test_errors_in_row_alert_once_per_streak_and_reset_by_a_good_tick(tmp_path):
    j = Journal(tmp_path / "journal.jsonl")
    inbox = Inbox()
    w = watcher(tmp_path, inbox, errors_after=3)
    for _ in range(2):
        j.append("run_error", {"error": "timeout"})
    w.check()
    assert inbox.got == []  # 2 < 3
    j.append("error", {"error": "order rejected by exchange"})
    j.append("run_error", {"error": "timeout"})
    w.check()  # the streak survives across scans
    assert [a.title for a in inbox.got] == ["3 erros seguidos"]
    j.append("run", {})
    for _ in range(3):
        j.append("run_error", {"error": "502"})
    w.check()
    assert len(inbox.got) == 2 and inbox.got[1].detail == "502"


def test_a_failing_channel_is_recorded_and_never_raises(tmp_path):
    Journal(tmp_path / "journal.jsonl").append("auto_kill", {"reason": "x"})
    good, bad = Inbox(), Inbox(fail=True)
    bad.channel = "telegram"
    sent = watcher(tmp_path, bad, good).check()
    assert sent[0]["channels"]["telegram"].startswith("failed: ConnectionError") and good.got
    log = [json.loads(x) for x in (tmp_path / "alerts.jsonl").read_text().splitlines()]
    assert log[0]["rule"] == "auto_kill"


def test_rotated_journal_starts_over(tmp_path):
    j = Journal(tmp_path / "journal.jsonl")
    for _ in range(3):
        j.append("run", {})
    inbox = Inbox()
    w = watcher(tmp_path, inbox)
    w.check()
    (tmp_path / "journal.jsonl").unlink()
    Journal(tmp_path / "journal.jsonl").append("auto_kill", {"reason": "new"})
    w.check()
    assert [a.detail for a in inbox.got] == ["new"]


# ---- channels (no network: the transport is a fake) ----


def alert():
    return Alert("critical", "auto_kill", "Kill switch acionado sozinho", "drawdown", "2026-10-13T10:00:00+00:00", "/s")


def test_telegram_and_webhook_payloads():
    calls = []
    telegram_sender("123:ABC", "42", post=lambda url, body: calls.append((url, body)))(alert())
    webhook_sender("https://hooks.example/x", post=lambda url, body: calls.append((url, body)))(alert())
    (t_url, t_body), (w_url, w_body) = calls
    assert t_url == "https://api.telegram.org/bot123:ABC/sendMessage" and t_body["chat_id"] == "42"
    assert "🛑" in t_body["text"] and "[auto_kill]" in t_body["text"]
    assert (
        w_url == "https://hooks.example/x"
        and w_body["text"] == w_body["content"]
        and w_body["alert"]["level"] == "critical"
    )


def test_email_sender_uses_ssl_and_logs_in():
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, context, timeout):
            sent["host"] = (host, port)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def login(self, user, password):
            sent["login"] = user

        def send_message(self, msg):
            sent["subject"] = msg["Subject"]

    email_sender("smtp.gmail.com", 465, "me@x.pt", "app-pass", "me@x.pt", smtp=FakeSMTP)(alert())
    assert sent == {
        "host": ("smtp.gmail.com", 465),
        "login": "me@x.pt",
        "subject": "[economia-trader] CRITICAL: Kill switch acionado sozinho",
    }


def test_senders_from_env_and_secret_redaction(tmp_path):
    env = {
        "ECONOMIA_TRADER_ALERT_TELEGRAM_TOKEN": "123:SECRET",
        "ECONOMIA_TRADER_ALERT_TELEGRAM_CHAT_ID": "42",
        "ECONOMIA_TRADER_ALERT_WEBHOOK": "https://hooks.example/abc",
    }
    assert [s.channel for s in senders_from_env(env)] == ["telegram", "webhook"]
    assert senders_from_env({}) == []

    def leaky(a):
        raise RuntimeError("POST https://api.telegram.org/bot123:SECRET/sendMessage failed")

    leaky.channel = "telegram"
    Journal(tmp_path / "journal.jsonl").append("auto_kill", {"reason": "x"})
    sent = AlertWatcher(tmp_path, [leaky], env=env).check()
    assert "SECRET" not in json.dumps(sent) and "***" in sent[0]["channels"]["telegram"]
    assert "SECRET" not in (tmp_path / "alerts.jsonl").read_text()


def test_only_https_endpoints():
    from economia_trader.alerts import _post_json

    with pytest.raises(ValueError, match="https"):
        _post_json("http://hooks.example/x", {})


# ---- end to end: the grid refuses, the CLI alerts ----


class Ex:
    name = "fake"
    supports_testnet = False

    def __init__(self, fail=False):
        self.fail = fail

    def ticker(self, s):
        if self.fail:
            raise ExchangeError("exchange unreachable")
        return Ticker(s, D("100000"), None, None)


def test_grid_refusal_and_exchange_errors_reach_the_inbox(tmp_path):
    big = GridConfig.from_mapping(
        {"symbol": "BTCUSDT", "lower": "94000", "upper": "106000", "levels": 6, "order_notional": "45", "max_lots": 6}
    )
    GridBot(Ex(), mode=Mode.PAPER, limits=LIMITS, config=big, state_dir=tmp_path, env={}).run_once()
    bot = GridBot(Ex(fail=True), mode=Mode.PAPER, limits=LIMITS, config=big, state_dir=tmp_path, env={})
    for _ in range(3):
        bot.run_once()
    inbox = Inbox()
    watcher(tmp_path, inbox).check()
    assert [a.rule for a in inbox.got] == ["grid_refused", "errors_in_row"]


def test_cli_alerts_once_and_test(tmp_path, monkeypatch, capsys):
    import economia_trader.alerts as al

    calls = []
    monkeypatch.setattr(al, "_post_json", lambda url, body, timeout=10: calls.append(url))
    monkeypatch.setenv("ECONOMIA_TRADER_ALERT_WEBHOOK", "https://hooks.example/abc")
    Journal(tmp_path / "journal.jsonl").append("auto_kill", {"reason": "x"})
    assert main(["alerts", "--state-dir", str(tmp_path), "--once"]) == 0
    assert json.loads(capsys.readouterr().out)["sent"][0]["channels"] == {"webhook": "ok"}
    assert main(["alerts", "--state-dir", str(tmp_path), "--test"]) == 0
    assert json.loads(capsys.readouterr().out)["rule"] == "test" and len(calls) == 2


def test_test_alert_on_a_fresh_state_dir(tmp_path):
    """`alerts --test` before the trader ever ran: the state dir does not exist yet."""
    w = AlertWatcher(tmp_path / "nova" / "state", [], env={})
    rec = w.test()
    assert rec["rule"] == "test"
    assert (tmp_path / "nova" / "state" / "alerts.jsonl").is_file()
