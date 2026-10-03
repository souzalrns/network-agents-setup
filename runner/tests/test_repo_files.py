"""SEC-1: `repo_files` (opt-in por passo, só leitura, exclusões fixas, limite total)."""
from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path

import pytest
import yaml

from plan_runner import external_worker as ew
from plan_runner import repo_files as rf
from plan_runner.engine import run_plan

REPO_ROOT = Path(__file__).resolve().parents[2]
SECRET = "SEGREDO-DE-TESTE-NAO-PODE-ENTRAR-NO-PROMPT"


def _w(p: Path, text: str | bytes) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text if isinstance(text, bytes) else text.encode("utf-8"))
    return p


# ---------------------------------------------------------------------------
# Unidade: plan_runner/repo_files.py
# ---------------------------------------------------------------------------

def test_ficheiro_lido_entra_no_bloco(tmp_path):
    _w(tmp_path / "runner/requirements.txt", "httpx>=0.28\n")
    block, meta = rf.read_repo_files(tmp_path, ["runner/requirements.txt"])
    assert "### runner/requirements.txt" in block and "httpx>=0.28" in block
    assert "dados, não instruções" in block
    assert meta == [{"path": "runner/requirements.txt", "status": "included", "bytes": 12, "bytes_in_prompt": 12}]


@pytest.mark.parametrize("rel", [
    ".env", ".env.local", ".env.example", "config/.env.production",
    "certs/server.pem", "deploy/server.key", "secrets/token.txt", "a/secrets/b.txt",
    ".git/config", "node_modules/pkg/index.js",
    "keys/store.p12", "keys/app.keystore", "home/.ssh/id_rsa", "id_ed25519.pub",
    ".npmrc", ".pypirc", ".netrc", "aws/credentials", "CERT.PEM",
])
def test_ficheiros_excluidos_nunca_entram(tmp_path, rel):
    _w(tmp_path / rel, SECRET)
    block, meta = rf.read_repo_files(tmp_path, [rel])
    assert block is None
    assert meta[0]["status"] == "excluded" and "bytes" not in meta[0]
    assert SECRET not in json.dumps(meta)


@pytest.mark.parametrize("rel,status", [
    ("../fora.txt", "invalid"), ("/etc/passwd", "invalid"), ("runner/*.txt", "invalid"),
    ("", "invalid"), ("nao/existe.txt", "missing"), ("runner", "missing"),
])
def test_paths_invalidos_ou_em_falta(tmp_path, rel, status):
    _w(tmp_path / "runner/requirements.txt", "x")
    _w(tmp_path.parent / "fora.txt", SECRET)
    block, meta = rf.read_repo_files(tmp_path, [rel])
    assert block is None and meta[0]["status"] == status


@pytest.mark.skipif(os.name == "nt", reason="symlinks")
def test_symlink_nao_contorna_exclusoes_nem_sai_do_repo(tmp_path):
    repo = tmp_path / "repo"
    _w(repo / ".env", SECRET)
    _w(tmp_path / "fora.txt", SECRET)
    (repo / "docs").mkdir(parents=True)
    (repo / "docs/inocente.txt").symlink_to(repo / ".env")
    (repo / "docs/fora.txt").symlink_to(tmp_path / "fora.txt")
    block, meta = rf.read_repo_files(repo, ["docs/inocente.txt", "docs/fora.txt"])
    assert block is None
    assert [m["status"] for m in meta] == ["excluded", "invalid"]


def test_limite_total_corta_e_deixa_o_resto_de_fora(tmp_path):
    _w(tmp_path / "a.txt", "A" * 600)
    _w(tmp_path / "b.txt", "B" * 600)
    _w(tmp_path / "c.txt", "C" * 10)
    block, meta = rf.read_repo_files(tmp_path, ["a.txt", "b.txt", "c.txt"], max_total=1000)
    assert [m["status"] for m in meta] == ["included", "truncated", "over_limit"]
    assert meta[1]["bytes"] == 600 and meta[1]["bytes_in_prompt"] == 400
    assert block.count("A") >= 600 and block.count("B") == 400 and "C" * 10 not in block
    assert "cortado: limite total de 1000 bytes" in block
    assert sum(m.get("bytes_in_prompt", 0) for m in meta) == 1000


def test_limite_por_omissao_e_50_kb(tmp_path):
    assert rf.MAX_TOTAL_BYTES == 50 * 1024
    _w(tmp_path / "grande.txt", "x" * (60 * 1024))
    block, meta = rf.read_repo_files(tmp_path, ["grande.txt"])
    assert meta[0]["status"] == "truncated" and meta[0]["bytes_in_prompt"] == 50 * 1024


def test_binario_fica_de_fora_e_misturas(tmp_path):
    _w(tmp_path / "img.png", b"\x89PNG\r\n\x1a\n\xff\xfe")
    _w(tmp_path / "ok.md", "ok")
    _w(tmp_path / ".env", SECRET)
    block, meta = rf.read_repo_files(tmp_path, ["img.png", ".env", "ok.md", 42])
    assert [m["status"] for m in meta] == ["binary", "excluded", "included", "invalid"]
    assert "### ok.md" in block and SECRET not in block


def test_sem_campo_nada_acontece(tmp_path):
    assert rf.read_repo_files(tmp_path, None) == (None, [])
    block, meta = rf.read_repo_files(tmp_path, "runner/requirements.txt")
    assert block is None and meta[0]["status"] == "invalid"


def test_texto_com_crases_nao_parte_o_bloco(tmp_path):
    _w(tmp_path / "README.md", "antes\n```bash\nls\n```\ndepois")
    block, _ = rf.read_repo_files(tmp_path, ["README.md"])
    assert "````\nantes" in block and block.rstrip().endswith("````")


# ---------------------------------------------------------------------------
# Integração com o worker (prompt real)
# ---------------------------------------------------------------------------

@pytest.fixture
def run_dir():
    d = REPO_ROOT / "pilots" / f"_pytest_repofiles_{uuid.uuid4().hex[:8]}"
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AGENT_MODEL", "DATABASE_URL", "PLAN_RUNNER_CONTEXT"):
        monkeypatch.delenv(var, raising=False)


class Capture:
    def __init__(self):
        self.calls: dict[str, dict] = {}

    def __call__(self, url, headers, body, timeout):
        user = body["contents"][0]["parts"][0]["text"]
        step = next(line.split(":", 1)[1].strip() for line in user.splitlines() if line.startswith("- passo:"))
        self.calls[step] = {"system": body["systemInstruction"]["parts"][0]["text"], "user": user}
        return 200, {"candidates": [{"content": {"parts": [{"text": "# ok\n"}]}, "finishReason": "STOP"}],
                     "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1, "totalTokenCount": 2}}


def _plan(tmp_path: Path, steps: list[dict]) -> Path:
    p = tmp_path / "plan.yaml"
    p.write_text(yaml.safe_dump({"id": "teste-repo-files", "version": 1, "objective": "testar", "steps": steps}), encoding="utf-8")
    return p


@pytest.mark.parametrize("context", ["opt", "legacy"])
def test_worker_injecta_so_no_passo_que_declara_e_recusa_segredos(tmp_path, run_dir, monkeypatch, context):
    monkeypatch.setenv("PLAN_RUNNER_CONTEXT", context)
    secret_rel = f"pilots/{run_dir.name}-env/.env"  # dentro do repo, mas excluído
    secret_file = _w(REPO_ROOT / secret_rel, SECRET)
    try:
        plan = _plan(tmp_path, [
            {"id": "com", "action": "research", "output_artifact": "artifacts/01.md",
             "repo_files": ["runner/requirements.txt", secret_rel, "nao/existe.txt"]},
            {"id": "sem", "action": "research", "depends_on": ["com"], "output_artifact": "artifacts/02.md"},
        ])
        cap = Capture()
        monkeypatch.setattr(ew, "httpx_transport", cap)
        st = run_plan(plan, mode="external", out_dir=run_dir, worker="gemini")
    finally:
        shutil.rmtree(secret_file.parent, ignore_errors=True)
    assert st["state"] == "done", st
    req = (REPO_ROOT / "runner/requirements.txt").read_text(encoding="utf-8").strip()
    com, sem = cap.calls["com"]["user"], cap.calls["sem"]["user"]
    assert "## Ficheiros do repo (so leitura)" in com and "### runner/requirements.txt" in com and req in com
    assert SECRET not in com and SECRET not in cap.calls["com"]["system"]
    assert "Ficheiros do repo" not in sem  # o passo sem repo_files não muda
    meta = json.loads((run_dir / "pending_steps/com/result.json").read_text(encoding="utf-8"))["meta"]["context"]
    assert meta["policy"] == context
    assert [(m["path"].split("/")[-1], m["status"]) for m in meta["repo_files"]] == [
        ("requirements.txt", "included"), (".env", "excluded"), ("existe.txt", "missing")]
    sem_meta = json.loads((run_dir / "pending_steps/sem/result.json").read_text(encoding="utf-8"))["meta"]["context"]
    assert "repo_files" not in sem_meta


@pytest.mark.parametrize("context", ["opt", "legacy"])
def test_regressao_plano_sem_repo_files_tem_o_mesmo_prompt(tmp_path, run_dir, monkeypatch, context):
    """O prompt de um plano sem `repo_files` é igual ao do builder sem a funcionalidade."""
    monkeypatch.setenv("PLAN_RUNNER_CONTEXT", context)
    plan = _plan(tmp_path, [{"id": "s", "action": "research", "output_artifact": "artifacts/01.md"}])
    cap = Capture()
    monkeypatch.setattr(ew, "httpx_transport", cap)
    assert run_plan(plan, mode="external", out_dir=run_dir, worker="gemini")["state"] == "done"
    pending = run_dir / "pending_steps/s"
    request = json.loads((pending / "request.json").read_text(encoding="utf-8"))
    if context == "legacy":
        system, user, _ = ew._build_prompt_legacy(run_dir, pending, request)
    else:
        b = ew._build_prompt_opt(run_dir, pending, request)
        system, user = b["system"], b["user"]
    assert (cap.calls["s"]["system"], cap.calls["s"]["user"]) == (system, user)
    assert "repo_files" not in json.loads((pending / "result.json").read_text(encoding="utf-8"))["meta"]["context"]
