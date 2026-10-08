"""Waivers: a human accepts ONE finding, for ONE exact content, for a limited time.

Static scanners have false positives (a documented `rm -rf` example, a test fixture). Other
tools answer with a global switch (`--exclude RULE`, `--unsafe-install`) that silently applies
to every future version. Here a waiver is:

- bound to the content hash: `(content_sha256, engine/rule, path)`. When the skill changes, the
  waiver no longer matches and the finding counts again. Nothing to forget to clean up;
- justified and dated: a reason (≥ 10 characters) and an expiry (default 90 days, max 365);
- approved by a human, under the same rules as an install (no AI agent, typed hash prefix or
  `--approve-sha256`);
- recorded in the lock file (reviewable in a pull request) and in the audit chain (`verify`
  rejects a waiver with no `waiver_added` record, i.e. one added to the lock by hand).

Never waivable: `critical` findings (private keys, credential theft: remove them instead),
files that cannot be pinned (symlinks, special files) and engine failures (no finding to waive).
A waived finding still shows in every report, marked with its waiver; SARIF marks it as an
accepted suppression.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
from dataclasses import dataclass, replace

from .engines import Finding
from .errors import UsageError

DEFAULT_DAYS = 90
MAX_DAYS = 365
MIN_REASON = 10
NEVER_WAIVABLE_SEVERITY = ("critical",)
NEVER_WAIVABLE_RULES = ("skill-scout/unpinnable-entry", "asm/blocked")


def today() -> _dt.date:
    return _dt.datetime.now(_dt.timezone.utc).date()


def waiver_id(content_sha256: str, rule_id: str, path: str) -> str:
    return hashlib.sha256(f"{content_sha256}\0{rule_id}\0{path}".encode()).hexdigest()[:16]


@dataclass(frozen=True)
class Waiver:
    id: str
    content_sha256: str
    rule: str  # engine/rule
    path: str
    reason: str
    expires: str  # YYYY-MM-DD (inclusive)
    source: str = ""
    actor: str = ""
    created: str = ""

    def active(self, on: _dt.date | None = None) -> bool:
        try:
            return _dt.date.fromisoformat(self.expires) >= (on or today())
        except ValueError:
            return False

    def matches(self, f: Finding, content_sha256: str) -> bool:
        return self.content_sha256 == content_sha256 and self.rule == f.rule_id and self.path == f.path

    @classmethod
    def from_json(cls, d: dict) -> Waiver:
        return cls(**{k: str(d.get(k, "")) for k in cls.__dataclass_fields__})

    def to_json(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


def check_waivable(f: Finding) -> None:
    if f.severity in NEVER_WAIVABLE_SEVERITY:
        raise UsageError(f"{f.rule_id} is {f.severity}: critical findings cannot be waived (remove the cause)")
    if f.rule_id in NEVER_WAIVABLE_RULES:
        raise UsageError(f"{f.rule_id} cannot be waived")


def parse_expiry(value: str | None, on: _dt.date | None = None) -> str:
    on = on or today()
    if not value:
        return (on + _dt.timedelta(days=DEFAULT_DAYS)).isoformat()
    try:
        day = _dt.date.fromisoformat(value)
    except ValueError:
        raise UsageError(f"--expires must be YYYY-MM-DD, got {value!r}") from None
    if day <= on:
        raise UsageError("--expires must be in the future")
    if day > on + _dt.timedelta(days=MAX_DAYS):
        raise UsageError(f"--expires is at most {MAX_DAYS} days ahead")
    return day.isoformat()


def check_reason(reason: str | None) -> str:
    reason = (reason or "").strip()
    if len(reason) < MIN_REASON:
        raise UsageError(f"--reason is required (at least {MIN_REASON} characters): why is this a false positive?")
    return reason[:500]


def load(lock_data: dict) -> list[Waiver]:
    return [Waiver.from_json(w) for w in lock_data.get("waivers") or [] if isinstance(w, dict)]


def trusted(lock_data: dict, audit_path) -> list[Waiver]:
    """The lock's waivers that have a matching `waiver_added` record in an intact audit chain.

    A waiver written into the lock by hand (or by an agent) has no such record and is ignored
    here, so it can never turn a blocking finding into "waived"; `verify` reports it.
    """
    from pathlib import Path

    from . import audit

    path = Path(audit_path)
    try:
        if audit.verify(path):
            return []
        records = {r.get("seq"): r for r in audit.read(path)}
    except Exception:  # an unreadable log trusts nothing
        return []
    out = []
    for raw in lock_data.get("waivers") or []:
        if not isinstance(raw, dict):
            continue
        w = Waiver.from_json(raw)
        ref = raw.get("audit") if isinstance(raw.get("audit"), dict) else {}
        rec = records.get(ref.get("seq"))
        data = (rec or {}).get("data") or {}
        if (
            rec is not None
            and rec.get("event") == "waiver_added"
            and rec.get("hash") == ref.get("hash")
            and all(data.get(k) == getattr(w, k) for k in ("id", "content_sha256", "rule", "path", "expires"))
        ):
            out.append(w)
    return out


def apply(findings: list[Finding], content_sha256: str, waivers: list[Waiver]) -> list[Finding]:
    """Mark the findings an active waiver for this exact content accepts."""
    live = [w for w in waivers if w.active()]
    out = []
    for f in findings:
        w = next((w for w in live if w.matches(f, content_sha256)), None)
        if w and f.severity not in NEVER_WAIVABLE_SEVERITY and f.rule_id not in NEVER_WAIVABLE_RULES:
            f = replace(f, waiver=w.id, waiver_reason=w.reason)
        out.append(f)
    return out
