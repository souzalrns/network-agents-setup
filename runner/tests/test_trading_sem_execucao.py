"""G1.5: o PCU nunca envia ordens nem toca em chaves de corretora. A execução vive no economia-trader, com o seu portão."""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from plan_runner import governance_local as g

ROOT = Path(__file__).resolve().parents[2]
ACCOES_PROIBIDAS = [
    "place_order", "place_market_order", "create_order", "submit_order", "send_order", "cancel_order", "modify_order",
    "amend_order", "execute_order", "execute_trade", "close_position", "set_leverage", "withdraw", "withdraw_funds",
    "transfer_funds", "transfer_to_exchange", "set_api_key", "rotate_api_key", "update_api_secret",
]
LEITURAS_PERMITIDAS = ["fetch_url", "read_repo_file", "get_order_book", "fetch_ticker", "get_positions", "list_orders", "market_analysis"]


@pytest.mark.parametrize("tool", ACCOES_PROIBIDAS)
def test_politica_do_repo_nega_accoes_de_ordens_e_chaves(tool):
    pol = g.load_policy()
    assert pol.match("market_analysis", f"tool:{tool}") == "deny"
    assert pol.match("*", f"tool:{tool}") == "deny"


@pytest.mark.parametrize("tool", LEITURAS_PERMITIDAS)
def test_leituras_de_mercado_continuam_permitidas(tool):
    assert g.load_policy().match("market_analysis", f"tool:{tool}") != "deny"


def test_modo_da_politica_e_enforce():
    # em `record` os deny só registavam: a garantia exige enforce
    assert g.load_policy().mode == "enforce"


def test_capabilities_de_trading_nao_tem_nivel_act():
    cfg = yaml.safe_load((ROOT / "config" / "trading-capabilities.yaml").read_text(encoding="utf-8"))
    assert cfg["policy"]["act_in_production"] == "forbidden" and cfg["policy"]["default_level"] == "read"
    for cap in cfg["capabilities"]:
        assert set(cap["levels"]) <= {"read", "prepare"}, cap["id"]


def test_planos_de_trading_nao_pedem_ferramentas_de_acao():
    ferramentas = set()
    for plan in (ROOT / "docs" / "orchestration" / "trading").rglob("*.plan.yaml"):
        for step in yaml.safe_load(plan.read_text(encoding="utf-8")).get("steps", []):
            ferramentas |= set(step.get("tools_allowed") or [])
    pol = g.load_policy()
    assert ferramentas, "esperava-se pelo menos uma ferramenta nos planos de exemplo"
    assert all(pol.match("market_analysis", f"tool:{t}") != "deny" for t in ferramentas), ferramentas


SEGREDOS = re.compile(r"(ECONOMIA_TRADER_LIVE|I_ACCEPT_REAL_LOSSES|BYBIT_API|BINANCE_API|ALPACA_(API|SECRET)|MEXC_API|EXCHANGE_API_(KEY|SECRET))", re.I)


def test_runner_e_skills_nao_tocam_em_credenciais_de_corretora():
    ficheiros = [*(ROOT / "runner" / "plan_runner").rglob("*.py"), *(ROOT / "skills" / "trading").rglob("*"),
                 *(ROOT / "config").glob("*.yaml")]
    achados = [str(f.relative_to(ROOT)) for f in ficheiros if f.is_file() and SEGREDOS.search(f.read_text(encoding="utf-8", errors="ignore"))]
    assert achados == [], f"credenciais de corretora fora do economia-trader: {achados}"


def test_plano_com_ferramenta_de_ordem_nem_chega_a_correr(tmp_path, tmp_run_dir):
    """1.ª barreira: o motor só aceita ferramentas que conhece (R1); `place_order` não existe. A governança é a 2.ª."""
    from plan_runner.engine import run_plan
    from plan_runner.policy import PolicyError

    exemplo = ROOT / "docs" / "orchestration" / "trading" / "templates" / "examples" / "market-analysis-demo.plan.yaml"
    raw = yaml.safe_load(exemplo.read_text(encoding="utf-8"))
    raw["steps"][0]["tools_allowed"] = ["place_order"]
    plan = tmp_path / "plan.yaml"
    plan.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    with pytest.raises(PolicyError, match="place_order"):
        run_plan(plan, mode="stub", out_dir=tmp_run_dir)
    assert not (tmp_run_dir / "artifacts").exists() or not any((tmp_run_dir / "artifacts").iterdir())
