"""countTokens: o estimador verificado + a guarda de orçamento PROJECTIVA (ADR-002).

O Gemini é falso (transport injectado): o mesmo fake responde a `:countTokens`
(estimativa) e a `:generateContent` (geração). Nenhum teste sai para a rede.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from plan_runner import cost
from plan_runner import external_worker as ew
from plan_runner.engine import run_plan

USAGE = {"promptTokenCount": 812, "candidatesTokenCount": 143, "totalTokenCount": 955}


class FakeTransport:
    """Responde a countTokens com `prompt_tokens`; a generateContent como o real."""

    def __init__(self, *, prompt_tokens: int = 800):
        self.prompt_tokens = prompt_tokens
        self.gen_calls: list[dict] = []
        self.count_calls: list[dict] = []

    def __call__(self, url, headers, body, timeout):
        if url.endswith(":countTokens"):
            self.count_calls.append({"url": url, "body": body})
            return 200, {"totalTokens": self.prompt_tokens}
        self.gen_calls.append({"url": url, "body": body})
        return 200, {
            "candidates": [{"content": {"role": "model", "parts": [{"text": "# ok\n\ntexto"}]}, "finishReason": "STOP"}],
            "modelVersion": "m",
            "responseId": f"r{len(self.gen_calls)}",
            "usageMetadata": USAGE,
        }


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL", "PLAN_RUNNER_BUDGET_PROJECT"):
        monkeypatch.delenv(var, raising=False)


# --------------------------------------------------------------------------
# count_tokens: o estimador verificado (vem da API, não de heurística local)
# --------------------------------------------------------------------------

def test_count_tokens_returns_total():
    fake = FakeTransport(prompt_tokens=1234)
    n = ew.count_tokens("sys", "user", model="m", transport=fake)
    assert n == 1234
    assert fake.count_calls[0]["url"].endswith(":countTokens")


def test_count_tokens_errors():
    def http500(url, headers, body, timeout):
        return 500, {"error": {"message": "boom"}}
    with pytest.raises(ew.WorkerError, match="countTokens HTTP 500"):
        ew.count_tokens("s", "u", model="m", transport=http500)

    def no_total(url, headers, body, timeout):
        return 200, {"nope": 1}
    with pytest.raises(ew.WorkerError, match="totalTokens"):
        ew.count_tokens("s", "u", model="m", transport=no_total)


# --------------------------------------------------------------------------
# check_budget_projected: pára ANTES, por tokens e por custo
# --------------------------------------------------------------------------

def _status(out: Path, **kw):
    (out / "status.json").write_text(json.dumps({"run_id": "r", **kw}), encoding="utf-8")


def test_projected_token_cap(tmp_run_dir):
    _status(tmp_run_dir, max_tokens=1000)
    # spent 0; projecção 200+900=1100 > 1000 -> bloqueia
    with pytest.raises(ew.BudgetExceeded):
        ew.check_budget_projected(tmp_run_dir, "m", 200, 900)
    # projecção 100+800=900 <= 1000 -> ok
    ew.check_budget_projected(tmp_run_dir, "m", 100, 800)


def test_projected_token_cap_counts_what_is_spent(tmp_run_dir):
    _status(tmp_run_dir, max_tokens=2000)
    (tmp_run_dir / ew.LEDGER_FILE).write_text(json.dumps({"tokens_total": 1500}) + "\n", encoding="utf-8")
    # gasto 1500 + projecção 100+300=400 -> 1900 <= 2000 ok
    ew.check_budget_projected(tmp_run_dir, "m", 100, 300)
    # gasto 1500 + projecção 100+500=600 -> 2100 > 2000 bloqueia
    with pytest.raises(ew.BudgetExceeded):
        ew.check_budget_projected(tmp_run_dir, "m", 100, 500)


def test_projected_cost_cap(tmp_run_dir, tmp_path, monkeypatch):
    prices = tmp_path / "prices.yaml"
    prices.write_text(json.dumps({"models": {"m": {"usd_per_1m_input": 1.0, "usd_per_1m_output": 10.0}}}), encoding="utf-8")
    monkeypatch.setattr(cost, "PRICES_PATH", prices)
    _status(tmp_run_dir, max_cost_usd=0.01)
    # 1000 in * 1/1M + 1000 out * 10/1M = 0.011 > 0.01 -> bloqueia
    with pytest.raises(ew.CostBudgetExceeded):
        ew.check_budget_projected(tmp_run_dir, "m", 1000, 1000)
    # 100 in + 100 out = 0.0011 <= 0.01 ok
    ew.check_budget_projected(tmp_run_dir, "m", 100, 100)


def test_projected_cost_unknown_price_fails_closed(tmp_run_dir, tmp_path, monkeypatch):
    prices = tmp_path / "prices.yaml"
    prices.write_text(json.dumps({"models": {}}), encoding="utf-8")
    monkeypatch.setattr(cost, "PRICES_PATH", prices)
    _status(tmp_run_dir, max_cost_usd=1.0)
    with pytest.raises(ew.WorkerError, match="preco confirmado"):
        ew.check_budget_projected(tmp_run_dir, "m", 10, 10)


def test_no_cap_is_noop(tmp_run_dir):
    _status(tmp_run_dir)  # sem tecto nenhum
    ew.check_budget_projected(tmp_run_dir, "m", 10_000, 10_000)  # não lança


# --------------------------------------------------------------------------
# End-to-end: a projecção pára ANTES de uma chamada que o reactivo deixaria passar
# --------------------------------------------------------------------------

def _plan(tmp_path: Path) -> Path:
    p = tmp_path / "plan.yaml"
    p.write_text(
        "id: proj\nobjective: x\nbudget:\n  max_tokens: 5000\nsteps:\n"
        "  - {id: s1, action: research, output_artifact: artifacts/1.md}\n"
        "  - {id: s2, action: research, depends_on: [s1], output_artifact: artifacts/2.md}\n"
        "  - {id: s3, action: research, depends_on: [s2], output_artifact: artifacts/3.md}\n",
        encoding="utf-8",
    )
    return p


def test_projection_off_runs_all(tmp_path, tmp_run_dir, monkeypatch):
    fake = FakeTransport()
    monkeypatch.setattr(ew, "httpx_transport", fake)
    # sem a flag: o reactivo deixa correr (955 < 5000 a cada passo)
    status = run_plan(_plan(tmp_path), mode="external", out_dir=tmp_run_dir, worker="gemini")
    assert status["state"] == "done"
    assert len(fake.gen_calls) == 3 and fake.count_calls == []  # sem countTokens


def test_projection_on_pauses_before_the_call(tmp_path, tmp_run_dir, monkeypatch):
    monkeypatch.setenv("PLAN_RUNNER_BUDGET_PROJECT", "1")
    fake = FakeTransport(prompt_tokens=800)  # projecção = 800 + 4096 (max_output) = 4896
    monkeypatch.setattr(ew, "httpx_transport", fake)
    status = run_plan(_plan(tmp_path), mode="external", out_dir=tmp_run_dir, worker="gemini")
    # s1: 0 + 4896 <= 5000 corre (955). s2: 955 + 4896 = 5851 > 5000 -> PÁRA antes de gerar.
    assert status["state"] == "paused_budget"
    assert status["paused_at_step"] == "s2"
    assert len(fake.gen_calls) == 1  # só o s1 gerou; o s2 nunca chamou generateContent
    # pausa de orçamento não é erro: sem worker_error.json no s2
    assert not (tmp_run_dir / "pending_steps" / "s2" / ew.ERROR_FILE).exists()
