"""scripts/setup_close_runs.py: o script único de evidência do fecho do setup, sem rede.

O run real precisa das credenciais do maestro (docs/ops/SETUP-CLOSE-SESSION.md); aqui prova-se
o que se pode provar sem elas:
- sem GEMINI_API_KEY/MCP_URL/MCP_API_KEY falha logo (código 2) e só mostra os nomes;
- os valores das chaves nunca chegam aos logs nem ao relatório;
- o F2 só passa com fontes web da fetch_url; o F3-ART-1 lê o meta.sources dos result.json;
- o ensaio em stub corre os planos até ao gate humano e não escreve na evidência versionada.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = REPO_ROOT / "pilots" / "evidence"


@pytest.fixture(scope="module")
def sc():
    spec = importlib.util.spec_from_file_location("setup_close_runs", REPO_ROOT / "scripts" / "setup_close_runs.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["setup_close_runs"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def out_dir():
    d = REPO_ROOT / "pilots" / f"_pytest_setup_{uuid.uuid4().hex[:8]}"
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _fake_run(run_dir: Path, *, state: str, completed: list[str], sources: dict[str, list[dict]]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "status.json").write_text(json.dumps({"state": state, "completed": completed,
                                                    "paused_at_step": "hitl"}), encoding="utf-8")
    for step, srcs in sources.items():
        p = run_dir / "pending_steps" / step / "result.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"meta": {"sources": srcs}}), encoding="utf-8")


def test_sem_credenciais_falha_logo_e_so_mostra_os_nomes(sc, monkeypatch, capsys) -> None:
    for name in sc.REQUIRED_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("MCP_API_KEY", "")  # vazia conta como em falta
    assert sc.main(["--check"]) == 2
    err = capsys.readouterr().err
    assert "GEMINI_API_KEY" in err and "MCP_URL" in err and "MCP_API_KEY" in err


def test_valores_das_chaves_nunca_saem(sc) -> None:
    # Valores gerados em execução: nenhum valor parecido com uma chave fica no código (gitleaks).
    gemini, mcp = "g" + uuid.uuid4().hex, "m" + uuid.uuid4().hex
    env = {"GEMINI_API_KEY": gemini, "MCP_API_KEY": mcp}
    text = f"url https://x/api/mcp/k/{mcp} e a outra {gemini}"
    clean = sc.redact(text, env)
    assert gemini not in clean and mcp not in clean
    assert "<MCP_API_KEY>" in clean and "<GEMINI_API_KEY>" in clean


def test_item_desconhecido_e_recusado(sc) -> None:
    assert sc.main(["--only", "F9", "--stub"]) == 2


def test_f2_so_passa_com_fontes_web_da_fetch_url(sc, monkeypatch, tmp_path) -> None:
    def fake_cmd(srcs):
        def run_cmd(args, *, log, env, timeout):
            run_dir = Path(args[args.index("--out") + 1])
            _fake_run(run_dir, state="paused_human_gate", completed=["research"], sources={"research": srcs})
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text("ok", encoding="utf-8")
            return 0, ""
        return run_cmd

    web = {"kind": "web", "final_url": "https://example.org/a", "title": "A", "tool": "fetch_url"}
    monkeypatch.setattr(sc, "run_cmd", fake_cmd([web]))
    ok = sc.Result("F2", "F2", "t")
    sc.do_plan(ok, tmp_path, {}, stub=False)
    assert ok.status == "PASS" and "1 fonte(s) web" in ok.detail

    monkeypatch.setattr(sc, "run_cmd", fake_cmd([{"kind": "l5", "source": "x.md"}]))
    sem_web = sc.Result("F2", "F2", "t")
    sc.do_plan(sem_web, tmp_path / "b", {}, stub=False)
    assert sem_web.status == "FAIL" and "não trouxe nenhuma fonte web" in sem_web.detail


def test_f3_art_1_le_o_meta_sources_dos_runs(sc, tmp_path) -> None:
    run = tmp_path / "run"
    web = {"kind": "web", "final_url": "https://example.org/a"}
    _fake_run(run, state="paused_human_gate", completed=["research"], sources={"research": [web]})
    assert sc.sources_of(run) == [{"step": "research", **web}]
    f2 = sc.Result("F2", "F2", "t", status="PASS", sources=sc.sources_of(run))
    art = sc.Result("F3-ART-1", "F3-ART-1", "t")
    sc.do_artifacts(art, {"F2": f2}, stub=False)
    assert art.status == "PASS" and art.sources[0]["run"] == "F2"
    falhou = sc.Result("F3-ART-1", "F3-ART-1", "t")
    sc.do_artifacts(falhou, {"F2": sc.Result("F2", "F2", "t", status="PASS")}, stub=False)
    assert falhou.status == "FAIL"


def test_estado_falhado_e_fail(sc, tmp_path) -> None:
    run = tmp_path / "run"
    _fake_run(run, state="failed", completed=[], sources={})
    res = sc.Result("F6-REVIEW", "F6", "t")
    sc.judge_run(res, run, 1)
    assert res.status == "FAIL" and "failed" in res.detail


def test_ensaio_stub_ate_ao_gate_sem_tocar_na_evidencia(sc, out_dir) -> None:
    before = set(EVIDENCE.glob("setup-close-*")) if EVIDENCE.exists() else set()
    assert sc.main(["--stub", "--only", "F6-REVIEW,F3-ART-1", "--out", str(out_dir)]) == 0
    report = (out_dir / "REPORT.md").read_text(encoding="utf-8")
    assert "ENSAIO EM STUB" in report and "| F6-REVIEW | F6 | **PASS** |" in report
    assert "| F3-ART-1 | F3-ART-1 | **SKIP** |" in report and "P-81" in report
    data = json.loads((out_dir / "report.json").read_text(encoding="utf-8"))
    assert [r["key"] for r in data][:2] == ["MCP-V3", "F2"]
    after = set(EVIDENCE.glob("setup-close-*")) if EVIDENCE.exists() else set()
    assert after == before  # um ensaio nunca vai para a evidência versionada


def test_com1_em_stub_vai_ate_ao_gate_e_diz_o_que_conferir(sc, out_dir) -> None:
    assert sc.main(["--stub", "--only", "COM-1", "--out", str(out_dir)]) == 0
    report = (out_dir / "REPORT.md").read_text(encoding="utf-8")
    assert "| COM-1 | COM-1 | **PASS** |" in report
    assert "cliente C (pediu para parar) fora dos rascunhos" in report
