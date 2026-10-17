"""The TradingAgents example configs: Gemini on the free plan by default (P-56, revised 2026-10-17).
Grok is only an opt-in deep tier: paid on xAI, or a free variant on OpenRouter while one exists.
They carry model choices, never keys."""

import json
import re
from pathlib import Path

import pytest

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
SECRETISH = re.compile(r"key|secret|token|password", re.I)


def _load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def _provider(cfg: dict, tier: str) -> str:
    return cfg.get(f"{tier}_think_provider") or cfg["llm_provider"]


def test_default_runs_both_tiers_on_gemini_with_one_key():
    cfg = _load("tradingagents.example.json")
    assert {_provider(cfg, t) for t in ("quick", "deep")} == {"google"}
    assert cfg["quick_think_llm"] == "gemini-3.5-flash-lite"  # most calls: the larger free daily quota
    assert cfg["deep_think_llm"] == "gemini-3.8-flash"  # two calls per run: the managers


def test_grok_is_only_the_deep_tier_and_the_rest_stays_free():
    cfg = _load("tradingagents.grok.example.json")
    assert _provider(cfg, "quick") == "google"
    assert _provider(cfg, "deep") == "xai" and cfg["deep_think_llm"].startswith("grok-")


def test_free_grok_goes_through_openrouter_free_variant_only():
    cfg = _load("tradingagents.grok-free.example.json")
    assert _provider(cfg, "quick") == "google"
    assert _provider(cfg, "deep") == "openrouter"
    assert cfg["deep_think_llm"].startswith("x-ai/grok-") and cfg["deep_think_llm"].endswith(":free")


@pytest.mark.parametrize(
    "name",
    ["tradingagents.example.json", "tradingagents.grok.example.json", "tradingagents.grok-free.example.json"],
)
def test_examples_hold_no_credentials_and_keep_the_debate_short(name):
    cfg = _load(name)
    assert not [k for k in cfg if SECRETISH.search(k)]  # keys come from the environment only
    assert "backend_url" not in cfg  # each provider uses its own official endpoint
    assert cfg["max_debate_rounds"] == 1 and cfg["max_risk_discuss_rounds"] == 1
