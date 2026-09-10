from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class EventLog:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def append(self, type_: str, run_id: str, payload: dict[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
        evt = {
            "id": f"evt_{uuid4().hex[:12]}",
            "type": type_,
            "run_id": run_id,
            "at": _now(),
            "payload": payload or {},
            **extra,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")
        return evt

    def has_event(self, type_: str, run_id: str, **match: Any) -> bool:
        """Verifica se ja existe um evento com type + run_id + payload match.

        Usado para evitar duplicados quando o LangGraph reexecuta um no
        (ex: no resume de HITL, o no "hitl" e reexecutado do inicio).
        """
        if not self.path.exists():
            return False
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if evt.get("type") != type_ or evt.get("run_id") != run_id:
                    continue
                payload = evt.get("payload", {})
                if all(payload.get(k) == v for k, v in match.items()):
                    return True
        return False
