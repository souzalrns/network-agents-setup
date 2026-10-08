"""Human approval of an install. Never automatic; bound to the exact content that was scanned.

Order of checks (`approve`):
1. verdict `dangerous` or `not_scanned` → blocked before any approval is asked;
2. an AI coding agent is detected in the environment → refused: an agent must not approve
   its own install, even with `--approve-sha256`. Run the command in your own terminal;
3. `--approve-sha256 <hash>` → must be the full content hash of THIS fetch (the human copies
   it from a `skill-scout scan` report); a different hash means the content changed since
   the human looked at it (time-of-check/time-of-use) and the install stops;
4. otherwise, an interactive terminal → the human types the first 12 characters of the content
   hash after reading the verdict and the findings;
5. otherwise → refused: "approval required". There is no `--yes`.

Agent detection is a port of the environment checks in `@vercel/detect-agent` 1.2.5
(Apache-2.0, https://github.com/vercel/vercel/tree/main/packages/detect-agent), the module the
`skills` CLI uses. It stops accidental self-approval by an agent; it is not a defence against
a hostile process that edits its own environment. The strong control is the review of the
lock file in a pull request (see README, "Threat model").
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from .audit import actor
from .errors import ApprovalError, BlockedError
from .report import ScanReport, now, render_text

PREFIX_LEN = 12
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def detect_agent(env: Mapping[str, str]) -> str | None:
    """Name of the AI agent running this process, or None (port of @vercel/detect-agent)."""

    def has(name: str) -> bool:
        return bool((env.get(name) or "").strip())

    if has("AI_AGENT"):
        return env["AI_AGENT"].strip()[:80]
    if has("CURSOR_TRACE_ID") or has("CURSOR_AGENT") or env.get("CURSOR_EXTENSION_HOST_ROLE") == "agent-exec":
        return "cursor"
    if has("GEMINI_CLI"):
        return "gemini"
    if has("CODEX_SANDBOX") or has("CODEX_CI") or has("CODEX_THREAD_ID"):
        return "codex"
    if has("ANTIGRAVITY_AGENT"):
        return "antigravity"
    if has("AUGMENT_AGENT"):
        return "augment-cli"
    if has("OPENCODE_CLIENT"):
        return "opencode"
    if has("CLAUDECODE") or has("CLAUDE_CODE"):
        return "cowork" if has("CLAUDE_CODE_IS_COWORK") else "claude"
    if has("REPL_ID"):
        return "replit"
    if has("COPILOT_MODEL") or has("COPILOT_ALLOW_ALL") or has("COPILOT_GITHUB_TOKEN"):
        return "github-copilot"
    return None


@dataclass(frozen=True)
class Approval:
    mode: str  # "tty" | "flag"
    actor: str
    at: str

    def to_json(self) -> dict:
        return {"mode": self.mode, "actor": self.actor, "at": self.at}


def confirm(
    digest: str,
    *,
    what: str,
    summary: str,
    approve_sha256: str | None,
    env: Mapping[str, str],
    interactive: bool,
    ask: Callable[[str], str] = input,
    out: Callable[[str], None] = lambda s: print(s, file=sys.stderr),
) -> Approval:
    """A human confirms `what` for content `digest` (rules 2-5 of the module docstring)."""
    agent = detect_agent(env)
    if agent:
        raise ApprovalError(
            f"refused: an AI agent ({agent}) cannot approve {what}. Run the command yourself, in your own terminal."
        )
    if approve_sha256 is not None:
        given = approve_sha256.strip().lower()
        if not _SHA256.match(given):
            raise ApprovalError("--approve-sha256 must be the full 64-character content hash from the scan report")
        if given != digest:
            raise ApprovalError(
                f"content changed since it was approved: approved {given[:12]}…, "
                f"fetched {digest[:12]}…. Scan it again before approving."
            )
        return Approval("flag", actor(), now())
    if not interactive:
        raise ApprovalError(
            "approval required: run in an interactive terminal, or pass "
            "--approve-sha256 <content hash from `skill-scout scan`>"
        )
    out(summary)
    answer = ask(
        f"Type the first {PREFIX_LEN} characters of the content hash to approve {what} (anything else cancels): "
    )
    if (answer or "").strip().lower() != digest[:PREFIX_LEN]:
        raise ApprovalError("not approved")
    return Approval("tty", actor(), now())


def approve(
    report: ScanReport,
    *,
    approve_sha256: str | None,
    env: Mapping[str, str],
    interactive: bool,
    ask: Callable[[str], str] = input,
    out: Callable[[str], None] = lambda s: print(s, file=sys.stderr),
    extra: str = "",
) -> Approval:
    """Approve installing `report`: blocked verdicts first, then a human confirmation."""
    if report.verdict in ("dangerous", "not_scanned"):
        raise BlockedError(f"blocked: verdict {report.verdict} (never installable; see the findings)")
    return confirm(
        report.tree.digest,
        what=f"installing this {report.verdict.upper()} skill",
        summary=render_text(report) + extra,
        approve_sha256=approve_sha256,
        env=env,
        interactive=interactive,
        ask=ask,
        out=out,
    )
