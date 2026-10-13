"""Alerts: tell a human when the trader stops itself or keeps failing (decision of 2026-10-13).

The watcher reads the journal from where it stopped last time (an offset file next to it), so it works
for any state dir (the stock loop, the grid) without touching the trading code, and a crash of the
trader cannot stop an alert that is already in the journal. Three rules:

- ``auto_kill``: the loop engaged the kill switch (drawdown or repeated failures). **critical**
- ``grid_refused``: a grid that does not fit the risk limits refused to trade. **warning**
- ``errors_in_row``: ``errors_after`` errors (``run_error``/``error``) with no successful tick (``run``)
  in between. **warning**, sent once per streak.

Channels come from the environment only (never from files in the repo), all optional and free:
Telegram (``ECONOMIA_TRADER_ALERT_TELEGRAM_TOKEN`` + ``..._CHAT_ID``), a generic webhook
(``ECONOMIA_TRADER_ALERT_WEBHOOK``: Slack, Discord, ntfy...), e-mail by SMTP (``ECONOMIA_TRADER_ALERT_SMTP_*``).
Every alert is also appended to ``alerts.jsonl``. A failing channel is recorded there and never raises:
the trader keeps running, and the alert stays in the file.
"""

from __future__ import annotations

import json
import smtplib
import ssl
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from .contracts import now_iso

ENV = "ECONOMIA_TRADER_ALERT_"
ERROR_KINDS = ("run_error", "error")

Send = Callable[["Alert"], None]


@dataclass(frozen=True)
class Alert:
    level: str  # critical | warning
    rule: str
    title: str
    detail: str
    at: str
    state_dir: str

    def text(self) -> str:
        icon = "🛑" if self.level == "critical" else "⚠️"
        return f"{icon} economia-trader [{self.rule}] {self.title}\n{self.detail}\n{self.state_dir} · {self.at}"


def _post_json(url: str, body: dict[str, Any], timeout: float = 10) -> None:
    if not url.startswith("https://"):
        raise ValueError("alert endpoints must be https")
    req = urllib.request.Request(  # noqa: S310 (https only, checked above)
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosemgrep  # noqa: S310
        resp.read()


Post = Callable[[str, dict[str, Any]], None]


def telegram_sender(token: str, chat_id: str, post: Post | None = None) -> Send:
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    def send(alert: Alert) -> None:
        (post or _post_json)(url, {"chat_id": chat_id, "text": alert.text(), "disable_web_page_preview": True})

    send.channel = "telegram"  # type: ignore[attr-defined]
    return send


def webhook_sender(url: str, post: Post | None = None) -> Send:
    def send(alert: Alert) -> None:
        # "text" for Slack-style hooks, "content" for Discord; the rest is for anything that reads JSON
        (post or _post_json)(url, {"text": alert.text(), "content": alert.text(), "alert": asdict(alert)})

    send.channel = "webhook"  # type: ignore[attr-defined]
    return send


def email_sender(
    host: str, port: int, user: str, password: str, to: str, smtp: Callable[..., Any] = smtplib.SMTP_SSL
) -> Send:
    def send(alert: Alert) -> None:
        msg = EmailMessage()
        msg["Subject"] = f"[economia-trader] {alert.level.upper()}: {alert.title}"
        msg["From"], msg["To"] = user, to
        msg.set_content(alert.text())
        with smtp(host, port, context=ssl.create_default_context(), timeout=15) as s:
            s.login(user, password)
            s.send_message(msg)

    send.channel = "email"  # type: ignore[attr-defined]
    return send


def senders_from_env(env: Mapping[str, str]) -> list[Send]:
    out: list[Send] = []
    if env.get(ENV + "TELEGRAM_TOKEN") and env.get(ENV + "TELEGRAM_CHAT_ID"):
        out.append(telegram_sender(env[ENV + "TELEGRAM_TOKEN"], env[ENV + "TELEGRAM_CHAT_ID"]))
    if env.get(ENV + "WEBHOOK"):
        out.append(webhook_sender(env[ENV + "WEBHOOK"]))
    if all(env.get(ENV + k) for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "EMAIL_TO")):
        out.append(
            email_sender(
                env[ENV + "SMTP_HOST"],
                int(env.get(ENV + "SMTP_PORT", "465")),
                env[ENV + "SMTP_USER"],
                env[ENV + "SMTP_PASSWORD"],
                env[ENV + "EMAIL_TO"],
            )
        )
    return out


def _redact(text: str, env: Mapping[str, str]) -> str:
    for k, v in env.items():
        if k.startswith(ENV) and ("TOKEN" in k or "PASSWORD" in k or "WEBHOOK" in k) and v:
            text = text.replace(v, "***")
    return text


class AlertWatcher:
    """Scan new journal entries, turn the ones that matter into alerts, send them on every channel."""

    def __init__(
        self,
        state_dir: str | Path,
        senders: list[Send],
        *,
        errors_after: int = 3,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.journal = self.state_dir / "journal.jsonl"
        self.offset_path = self.state_dir / "alerts.offset.json"
        self.log = self.state_dir / "alerts.jsonl"
        self.senders, self.errors_after = senders, errors_after
        self.env = env or {}

    def _load(self) -> dict[str, Any]:
        if self.offset_path.exists():
            return json.loads(self.offset_path.read_text(encoding="utf-8"))
        return {"line": 0, "streak": 0, "streak_alerted": False}

    def _save(self, st: dict[str, Any]) -> None:
        tmp = self.offset_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(st), encoding="utf-8")
        tmp.replace(self.offset_path)

    def scan(self) -> list[Alert]:
        """New alerts since the last scan (the offset is saved by ``check``)."""
        st = self._load()
        lines = self.journal.read_text(encoding="utf-8").splitlines() if self.journal.exists() else []
        if st["line"] > len(lines):  # the journal was rotated/replaced: start over
            st = {"line": 0, "streak": 0, "streak_alerted": False}
        alerts = []
        for line in lines[st["line"] :]:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            kind, p, at = e.get("kind"), e.get("payload") or {}, e.get("ts", now_iso())
            if kind == "auto_kill":
                alerts.append(
                    self._alert("critical", "auto_kill", "Kill switch acionado sozinho", str(p.get("reason")), at)
                )
            elif kind == "grid_refused":
                alerts.append(
                    self._alert(
                        "warning", "grid_refused", "Grid recusado pelos limites", "; ".join(p.get("problems", [])), at
                    )
                )
            elif kind in ERROR_KINDS:
                st["streak"] += 1
                if st["streak"] >= self.errors_after and not st["streak_alerted"]:
                    st["streak_alerted"] = True
                    alerts.append(
                        self._alert(
                            "warning",
                            "errors_in_row",
                            f"{st['streak']} erros seguidos",
                            str(p.get("error", ""))[:300],
                            at,
                        )
                    )
            elif kind == "run":
                st["streak"], st["streak_alerted"] = 0, False
        st["line"] = len(lines)
        self._pending_state = st
        return alerts

    def _alert(self, level: str, rule: str, title: str, detail: str, at: str) -> Alert:
        return Alert(level, rule, title, detail, at, str(self.state_dir))

    def send(self, alert: Alert) -> dict[str, Any]:
        record: dict[str, Any] = {"sent_at": now_iso(), **asdict(alert), "channels": {}}
        for s in self.senders:
            name = getattr(s, "channel", "custom")
            try:
                s(alert)
                record["channels"][name] = "ok"
            except Exception as exc:  # a channel down must never stop the trader or the other channels
                record["channels"][name] = _redact(f"failed: {type(exc).__name__}: {exc}", self.env)[:300]
        with self.log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def check(self) -> list[dict[str, Any]]:
        """Scan, send, and remember where we stopped. Returns what was sent."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        alerts = self.scan()
        sent = [self.send(a) for a in alerts]
        self._save(self._pending_state)
        return sent

    def test(self) -> dict[str, Any]:
        """Send one harmless alert to every configured channel (to check the setup)."""
        return self.send(
            self._alert("warning", "test", "Alerta de teste", "Se estás a ler isto, o canal funciona.", now_iso())
        )
