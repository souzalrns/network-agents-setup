"""Runs **inside ai-hedge-fund's own virtualenv** (``pipx install aihf==2.5.0``), never imported here.

economia-trader starts it with that venv's interpreter (``python -I aihf_bridge.py``), sends one JSON
request on stdin and reads the personas' signals as JSON on stdout. ai-hedge-fund pins LangChain 0.3
(``langchain-anthropic==0.3.5``), which cannot share an environment with TradingAgents (LangChain >= 1.6),
so the two never load in the same process.

Request: ``{"ticker": "ACME", "date": "2026-10-13", "personas": ["buffett", ...], "model": "gemini-3.8-flash"}``
Reply:   ``{"signals": [{"persona", "value", "abstained", "signal", "confidence", "reasoning", "cached"}]}``
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    req = json.load(sys.stdin)
    from hedge_fund.data.cached import CachedDataClient
    from hedge_fund.data.client import FDClient
    from hedge_fund.llm import make_llm
    from hedge_fund.signals import ALPHA_MODEL_REGISTRY

    llm = make_llm(req["model"])
    out = []
    with FDClient() as raw:
        data = CachedDataClient(raw)
        for persona in req["personas"]:
            sig = ALPHA_MODEL_REGISTRY[persona](llm=llm).predict(req["ticker"], req["date"], data)
            meta = sig.metadata or {}
            out.append(
                {
                    "persona": persona,
                    "value": float(sig.value),
                    "abstained": bool(meta.get("abstained")),
                    "signal": meta.get("signal"),
                    "confidence": meta.get("confidence"),
                    "reasoning": (sig.reasoning or "")[:4000],
                    "cached": bool(meta.get("cached")),
                }
            )
    json.dump({"signals": out, "model": llm.model}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
