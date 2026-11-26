"""Pegada do setup: tetos estáticos (tamanho do repo e das dependências) e o golden do trading."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from plan_runner import l5_eval

ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location("setup_footprint", ROOT / "scripts" / "setup_footprint.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_tetos_estaticos_da_baseline():
    fp = _load()
    ceilings = json.loads(fp.BASELINE.read_text(encoding="utf-8"))["ceilings"]
    m = {**fp.repo_size(), **fp.deps_size()}
    assert m["repo_tracked_mb"] <= ceilings["repo_tracked_mb"], "o repo engordou: ver docs/ops/FOOTPRINT-BASELINE.json"
    assert m["runner_deps_mb"] <= ceilings["runner_deps_mb"], "as dependências do runner engordaram"


def test_check_aponta_o_que_passa_do_teto(tmp_path, monkeypatch):
    fp = _load()
    b = tmp_path / "b.json"
    b.write_text(json.dumps({"ceilings": {"repo_tracked_mb": 1.0, "cli_peak_mb": 100.0}}), encoding="utf-8")
    monkeypatch.setattr(fp, "BASELINE", b)
    assert fp.check({"repo_tracked_mb": 2.0, "cli_peak_mb": 50.0}) == ["repo_tracked_mb: 2.0 > teto 1.0"]
    monkeypatch.setattr(fp, "BASELINE", tmp_path / "nao-existe.json")
    assert fp.check({}) and "falta" in fp.check({})[0]


def test_golden_do_trading_valido_contra_o_chunking_real():
    golden = l5_eval.load_golden(ROOT / "config" / "l5-golden-trading.yaml")
    assert golden["kb"] == "trading" and len(golden["cases"]) >= 12
    assert l5_eval.anchor_errors(golden, l5_eval._local_chunks(golden)) == []
