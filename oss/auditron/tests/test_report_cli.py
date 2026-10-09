"""Relatórios (JSON/SARIF/texto) e CLI — sem engines reais (scanners trocados por falsos)."""

from __future__ import annotations

import json

import pytest

from auditron import cli, core, report
from auditron.model import Finding, ScanResult, ToolRun


def _sample() -> ScanResult:
    return ScanResult(
        "repo",
        [
            ToolRun(
                "pip-audit",
                "pip-audit 2.10.1",
                blocking=True,
                findings=[Finding("pip-audit", "PYSEC-1", "error", "requests 2.19.0", "requirements.txt")],
            ),
            ToolRun(
                "bandit",
                "bandit 1.9.4",
                blocking=False,
                findings=[Finding("bandit", "B602", "error", "shell=True", "pkg/bad.py", 3)],
            ),
            ToolRun("zizmor", "zizmor 1.30.1", blocking=False, error="não deu SARIF"),
        ],
    )


def test_json_roundtrip():
    d = json.loads(report.to_json(_sample()))
    assert d["auditron"]["blocked"] is True
    assert d["auditron"]["counts"] == {"note": 0, "warning": 0, "error": 2}
    assert [r["tool"] for r in d["runs"]] == ["pip-audit", "bandit", "zizmor"]
    assert d["runs"][2]["error"] == "não deu SARIF"


def test_sarif_estrutura():
    d = json.loads(report.to_sarif(_sample()))
    assert d["version"] == "2.1.0" and d["$schema"].endswith("sarif-schema-2.1.0.json")
    assert len(d["runs"]) == 3
    pa = d["runs"][0]
    assert pa["tool"]["driver"]["name"] == "pip-audit" and pa["tool"]["driver"]["version"] == "pip-audit 2.10.1"
    res = pa["results"][0]
    assert res["ruleId"] == "PYSEC-1" and res["level"] == "error"
    assert res["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "requirements.txt"
    # a regra do achado está declarada no driver
    assert {r["id"] for r in pa["tool"]["driver"]["rules"]} == {"PYSEC-1"}
    # o achado com linha leva region.startLine
    b = d["runs"][1]["results"][0]
    assert b["locations"][0]["physicalLocation"]["region"]["startLine"] == 3


def test_texto_tem_veredicto_e_tags():
    t = report.to_text(_sample())
    assert "BLOQUEIA" in t and "informa" in t and "veredicto: BLOQUEADO" in t


def _fake(result: ScanResult):
    def _scan(target, policy, only=None):
        return result

    return _scan


def test_cli_exit0_quando_so_informativo(monkeypatch, clean_repo, capsys):
    only_info = ScanResult(
        str(clean_repo), [ToolRun("bandit", blocking=False, findings=[Finding("bandit", "B1", "error", "m")])]
    )
    monkeypatch.setattr(core, "scan", _fake(only_info))
    assert cli.main(["scan", str(clean_repo)]) == 0
    assert "veredicto: ok" in capsys.readouterr().out


def test_cli_exit1_quando_bloqueia(monkeypatch, clean_repo, tmp_path):
    monkeypatch.setattr(core, "scan", _fake(_sample()))
    sarif = tmp_path / "out.sarif"
    assert cli.main(["scan", str(clean_repo), "--sarif", str(sarif), "--quiet"]) == 1
    assert json.loads(sarif.read_text())["version"] == "2.1.0"  # o SARIF foi gravado


def test_cli_path_inexistente_sai_2(tmp_path):
    assert cli.main(["scan", str(tmp_path / "nao-ha")]) == 2


def test_cli_config_invalida_sai_2(clean_repo):
    (clean_repo / "auditron.toml").write_text('[auditron]\nblocking=["x"]\n', encoding="utf-8")
    assert cli.main(["scan", str(clean_repo)]) == 2


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as e:
        cli.main(["--version"])
    assert e.value.code == 0
    assert "auditron" in capsys.readouterr().out
