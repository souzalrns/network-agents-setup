"""Agents as characters in a pixel office: a bridge from our journal to **Star-Office-UI**
(ringhyacinth/Star-Office-UI; code MIT, art assets non-commercial: fine for personal use, replace
the art for anything commercial).

We do not draw anything. Star-Office-UI already renders agents moving between office areas by
state (idle, writing, researching, executing, syncing, error); we only *tell* it what each of our
agents is doing, by tailing the journal:

    monitor   (news/macro)   researching when events arrive
    screen    (whale screen) executing on a proposal
    analyst   (TradingAgents / Kronos) writing an opinion or forecast; error on a veto
    risk      (risk + gate)  executing on approval; error on reject/block/auto-kill; syncing on macro block
    executor  (orders)       executing on intent/fill/order

Protocol (backend/app.py): ``POST /join-agent {name, state, detail, joinKey}`` once per agent
(auto-approved with a valid key) -> ``agentId``; then ``POST /agent-push {agentId, joinKey, state,
detail}``. The bridge is a separate process (``economia-trader office``): the trader never waits on,
or breaks because of, the visual layer.
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

AGENTS = {
    "monitor": "Monitor (notícias/macro)",
    "screen": "Triagem (baleias)",
    "analyst": "Analista LLM",
    "risk": "Risco e travas",
    "executor": "Executor",
}

# (method, url, json_body) -> parsed json
Post = Callable[[str, dict[str, Any]], dict[str, Any]]


def http_post(url: str, body: dict[str, Any]) -> dict[str, Any]:
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"refusing URL scheme: {url}")
    req = urllib.request.Request(  # noqa: S310 (scheme checked above)
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as resp:  # nosemgrep  # noqa: S310
        return json.loads(resp.read().decode() or "{}")


def map_entry(entry: dict[str, Any]) -> tuple[str, str, str] | None:
    """Journal entry -> (agent, state, detail). None = nothing to show."""
    kind, p = entry.get("kind"), entry.get("payload") or {}
    if kind == "proposal":
        return "screen", "executing", f"{p.get('side')} {p.get('symbol')} ({p.get('proposer')})"
    if kind in ("opinion", "forecast"):
        state = "writing" if p.get("confirms") else "error"
        suffix = " (kronos)" if kind == "forecast" else ""
        return "analyst", state, f"{p.get('ticker')}: {p.get('rating')}{suffix}"
    if kind == "assessment":
        if p.get("approved"):
            return "risk", "executing", f"aprovado {p.get('proposal_id')}"
        return "risk", "error", "; ".join(p.get("reasons", []))[:120]
    if kind == "blocked":
        return "risk", "error", f"bloqueado: {p.get('code')}"
    if kind == "odds_block":
        return "risk", "syncing", "pausa por probabilidades: " + "; ".join(p.get("reasons", []))[:100]
    if kind == "macro_block":
        return "risk", "syncing", "pausa macro: " + ", ".join(p.get("releases", []))[:100]
    if kind == "auto_kill":
        return "risk", "error", f"KILL: {p.get('reason')}"[:120]
    if kind in ("intent", "order", "fill"):
        return "executor", "executing", f"{kind} {p.get('side', '')} {p.get('symbol', '')}".strip()
    if kind == "run":
        return "monitor", "idle", f"tick {p.get('as_of', '')[:16]} v{p.get('version', '')}"
    if kind in ("run_error", "error"):
        return "executor", "error", str(p.get("error", ""))[:120]
    return None


class OfficeBridge:
    def __init__(self, url: str, join_key: str, state_path: str | Path, post: Post = http_post) -> None:
        self.url = url.rstrip("/")
        self.join_key = join_key
        self.state_path = Path(state_path)
        self.post = post
        st = json.loads(self.state_path.read_text()) if self.state_path.exists() else {}
        self.agent_ids: dict[str, str] = st.get("agent_ids", {})
        self.offset: int = int(st.get("offset", 0))
        self.events_offset: int = int(st.get("events_offset", 0))

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(
            json.dumps({"agent_ids": self.agent_ids, "offset": self.offset, "events_offset": self.events_offset})
        )

    def _agent_id(self, agent: str) -> str:
        if agent not in self.agent_ids:
            res = self.post(
                f"{self.url}/join-agent",
                {"name": AGENTS[agent], "state": "idle", "detail": "", "joinKey": self.join_key},
            )
            if not res.get("ok") or not res.get("agentId"):
                raise RuntimeError(f"office join failed for {agent}: {res.get('msg')}")
            self.agent_ids[agent] = res["agentId"]
        return self.agent_ids[agent]

    def push(self, agent: str, state: str, detail: str) -> dict[str, Any]:
        body = {"agentId": self._agent_id(agent), "joinKey": self.join_key, "state": state, "detail": detail}
        return self.post(f"{self.url}/agent-push", body)

    def sync(self, journal: str | Path, events: str | Path | None = None) -> int:
        """Push what happened since the last sync. Returns how many updates were sent."""
        sent = 0
        lines = Path(journal).read_text(encoding="utf-8").splitlines() if Path(journal).exists() else []
        for line in lines[self.offset :]:
            mapped = map_entry(json.loads(line)) if line.strip() else None
            if mapped:
                self.push(*mapped)
                sent += 1
        self.offset = len(lines)
        if events and Path(events).exists():
            ev_lines = Path(events).read_text(encoding="utf-8").splitlines()
            new = ev_lines[self.events_offset :]
            if new:
                kinds = [json.loads(x).get("kind") for x in new if x.strip()]
                self.push(
                    "monitor", "researching", f"{kinds.count('news')} notícias, {kinds.count('macro_release')} releases"
                )
                sent += 1
            self.events_offset = len(ev_lines)
        self._save()
        return sent
