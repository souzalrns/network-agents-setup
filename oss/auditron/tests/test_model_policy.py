"""Modelo, política e código de saída — sem rede nem engines."""

from __future__ import annotations

import pytest

from auditron.config import DEFAULT, ENGINES, load
from auditron.model import Finding, ScanResult, ToolRun, level_rank


def test_level_rank_ordena_e_trata_desconhecido():
    assert level_rank("note") < level_rank("warning") < level_rank("error")
    assert level_rank("inventado") >= level_rank("error")  # desconhecido = o mais grave


def test_toolrun_ok_e_contagens():
    r = ToolRun(tool="bandit")
    assert r.ok  # correu, sem achados, sem erro
    r.findings.append(Finding("bandit", "B602", "error", "x", "a.py", 3))
    r.findings.append(Finding("bandit", "B101", "note", "y", "b.py", 9))
    assert not r.ok
    assert r.counts() == {"note": 1, "warning": 0, "error": 1}


def test_scanresult_bloqueia_so_por_engine_bloqueante():
    err = ToolRun(tool="pip-audit", blocking=True, findings=[Finding("pip-audit", "V", "error", "m")])
    info = ToolRun(tool="bandit", blocking=False, findings=[Finding("bandit", "B1", "error", "m")])
    assert ScanResult("t", [info]).blocked() is False  # achado informativo não bloqueia
    assert ScanResult("t", [err]).blocked() is True
    assert ScanResult("t", [err, info]).counts() == {"note": 0, "warning": 0, "error": 2}


def test_engine_que_rebenta_bloqueia_se_for_bloqueante():
    # ausência de prova não é prova de ausência: um engine bloqueante que falha bloqueia
    broke = ToolRun(tool="pip-audit", blocking=True, error="não deu JSON")
    assert ScanResult("t", [broke]).blocked() is True
    broke_info = ToolRun(tool="zizmor", blocking=False, error="não deu SARIF")
    assert ScanResult("t", [broke_info]).blocked() is False


def test_policy_default():
    assert DEFAULT.enabled() == list(ENGINES)
    assert DEFAULT.is_blocking("pip-audit") and not DEFAULT.is_blocking("bandit")


def test_policy_load_sem_ficheiro(tmp_path):
    assert load(None) is DEFAULT
    assert load(tmp_path / "nao-existe.toml") is DEFAULT


def test_policy_load_toml(tmp_path):
    p = tmp_path / "auditron.toml"
    p.write_text('[auditron]\nblocking = ["pip-audit", "bandit"]\ndisabled = ["zizmor"]\n', encoding="utf-8")
    pol = load(p)
    assert pol.is_blocking("bandit") and "zizmor" not in pol.enabled()
    assert pol.enabled() == ["pip-audit", "bandit"]


@pytest.mark.parametrize(
    "body, msg",
    [
        ('[auditron]\nblocking = ["inventado"]\n', "desconhecidos"),
        ('[auditron]\nblocking = ["bandit"]\ndisabled = ["bandit"]\n', "ao mesmo tempo"),
        ("[auditron]\nblocking = [1, 2]\n", "listas de nomes"),
    ],
)
def test_policy_load_recusa_invalido(tmp_path, body, msg):
    p = tmp_path / "auditron.toml"
    p.write_text(body, encoding="utf-8")
    with pytest.raises(ValueError, match=msg):
        load(p)
