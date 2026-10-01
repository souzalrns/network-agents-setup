"""Fixtures partilhadas para os testes do runner.

Cada teste corre num diretorio temporario isolado.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest

# Ativa coverage em subprocessos.
# O runner corre via subprocess.run(["python", "-m", "plan_runner", ...])
# num processo filho. Sem COVERAGE_PROCESS_START, o coverage do pytest
# nao ve nada do processo filho e reporta 0%.
_coveragerc = Path(__file__).resolve().parent.parent / ".coveragerc"
if _coveragerc.exists():
    os.environ.setdefault("COVERAGE_PROCESS_START", str(_coveragerc))


# Paths base
RUNNER_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = RUNNER_DIR.parent
PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "orchestration"
    / "marketing"
    / "templates"
    / "examples"
    / "ship-parallel.plan.yaml"
)


@pytest.fixture
def runner_dir() -> Path:
    """Path do diretorio runner/."""
    return RUNNER_DIR


@pytest.fixture
def plan_path() -> Path:
    """Path do plano ship-parallel."""
    if not PLAN_PATH.exists():
        pytest.skip(f"Plan nao encontrado: {PLAN_PATH}")
    return PLAN_PATH


@pytest.fixture
def tmp_run_dir() -> Path:
    """Diretorio temporario para um run isolado, dentro de pilots/.

    O plan_runner exige que --out esteja sob <repo>/pilots/ (guard
    _validate_out_dir em engine.py e langgraph_engine.py). Testes antigos
    usavam tmp_path/run (fora do repo), o que quebrava o modo external.

    Cleanup automatico no teardown.
    """
    root = REPO_ROOT / "pilots" / f"_pytest_{uuid4().hex[:8]}"
    root.mkdir(parents=True, exist_ok=True)
    yield root
    shutil.rmtree(root, ignore_errors=True)


def _run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Executa 'python -m plan_runner ...' e devolve o resultado."""
    return subprocess.run(
        [sys.executable, "-m", "plan_runner", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )

def _load_status_safe(out_dir: Path) -> dict:
    """Le status.json tolerando ficheiro ausente ou corrompido.

    Fixtures de teste nao podem explodir com JSONDecodeError quando o
    proprio teste corrompe o status.json de proposito. Nesses casos,
    devolvemos {} e deixamos o teste validar o comportamento do motor.
    """
    status_file = out_dir / "status.json"
    if not status_file.exists():
        return {}
    try:
        return json.loads(status_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


@pytest.fixture
def run_cli():
    """Devolve uma funcao que corre o CLI do runner."""
    def _runner(args: list[str]) -> subprocess.CompletedProcess:
        return _run_cli(args, cwd=RUNNER_DIR)
    return _runner


@pytest.fixture
def run_plan(run_cli, plan_path: Path):
    """Corre 'run' com o plano ship-parallel e devolve (proc, status)."""
    def _run(
        out_dir: Path,
        *,
        mode: str = "stub",
        engine: str = "langgraph",
    ) -> tuple[subprocess.CompletedProcess, dict]:
        proc = run_cli([
            "run",
            str(plan_path),
            "--engine", engine,
            "--mode", mode,
            "--out", str(out_dir),
        ])
        status = _load_status_safe(out_dir)
        return proc, status
    return _run


@pytest.fixture
def resume_plan(run_cli):
    """Corre 'resume' com o out_dir e decisao dados."""
    def _resume(out_dir: Path, decision: str) -> tuple[subprocess.CompletedProcess, dict]:
        proc = run_cli([
            "resume",
            str(out_dir),
            "--decision", decision,
        ])
        status = _load_status_safe(out_dir)
        return proc, status
    return _resume


@pytest.fixture
def write_result_json():
    """Escreve um result.json para um step pending (mode external)."""
    def _write(out_dir: Path, step_id: str, ok: bool = True, detail: str = "done") -> Path:
        step_dir = out_dir / "pending_steps" / step_id
        step_dir.mkdir(parents=True, exist_ok=True)
        result_file = step_dir / "result.json"
        result_file.write_text(
            json.dumps({"ok": ok, "detail": detail}),
            encoding="utf-8",
        )
        return result_file
    return _write


# --------------------------------------------------------------------------
# L4 (D3): schema descartavel com o SQL versionado (tests/test_memory_l4*.py).
# So corre com RAG_TEST_DATABASE_URL (Postgres + pgvector descartavel, nunca o
# Supabase de producao); os modulos de teste fazem skip/erro sem ele.
# --------------------------------------------------------------------------

L4_SQL_FILES = [REPO_ROOT / "scripts/create_memory_l4_table.sql", REPO_ROOT / "scripts/create_recall_l4_rpc.sql"]


@pytest.fixture
def l4_opts():
    """Schema proprio com o SQL versionado aplicado 2x (idempotencia). Devolve as `options` de ligacao."""
    schema = f"l4_test_{uuid4().hex[:8]}"
    with _psycopg().connect(os.environ["RAG_TEST_DATABASE_URL"], autocommit=True) as admin:
        admin.execute("CREATE EXTENSION IF NOT EXISTS vector")
        admin.execute(f"CREATE SCHEMA {schema}")
    opts = f"-c search_path={schema},public"
    sql = [f.read_text(encoding="utf-8").replace("public.", f"{schema}.") for f in L4_SQL_FILES]
    try:
        with _psycopg().connect(os.environ["RAG_TEST_DATABASE_URL"], autocommit=True, options=opts) as c:
            for _ in range(2):  # idempotencia
                for text in sql:
                    c.execute(text)
        yield opts
    finally:
        with _psycopg().connect(os.environ["RAG_TEST_DATABASE_URL"], autocommit=True) as admin:
            admin.execute(f"DROP SCHEMA {schema} CASCADE")


@pytest.fixture
def db(l4_opts):
    conn = _psycopg().connect(os.environ["RAG_TEST_DATABASE_URL"], autocommit=False, row_factory=_psycopg().rows.dict_row, options=l4_opts)
    try:
        yield conn
    finally:
        conn.close()




def _psycopg():
    import psycopg
    import psycopg.rows  # noqa: F401 -- carrega o submodulo para _psycopg().rows

    return psycopg

