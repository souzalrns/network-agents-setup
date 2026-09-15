"""Working memory (MEMORY.md) por cliente -- leitura, sem escrita.

Design note do projeto: docs/architecture/memory-integration.md descreve
LightRAG (o que sabemos) e Cognee (o que fizemos). Ambos sao opcionais e
dependem de LLM. Isto NAO e isso. Isto e a working memory descrita no
STATUS.md (S7): um ficheiro MEMORY.md curado por cliente, ~1300 tokens,
que o agente le antes de correr. Curadoria e humana; este modulo so le.

Convencao (espelha runner/plan_runner/skills.py):
    skills/<vertical>/<action>/SKILL.md  -> resolve_skill_path()
    memory/<client_id>/MEMORY.md         -> resolve_memory_path()

Um cliente pode ter varias verticais (marketing, design, ...). Por isso
a chave e o client_id, sem vertical no path.

API (funcoes module-level, mesmo estilo do skills.py / events.py / hitl.py):
    resolve_memory_path(repo_root, client_id) -> Path | None
    read_memory(client_id, *, repo_root=None, out_dir=None) -> str | None
    memory_status(client_id, *, repo_root=None, out_dir=None) -> dict

Sem escrita, sem LLM, sem dependencias novas.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

# Limite suave. O STATUS.md diz "~1300 tokens"; nao bloqueia, so reporta.
TOKEN_LIMIT_SOFT = 1300

# Aproximacao de tokens sem tokenizer: ~4 caracteres por token (en/pt).
_CHARS_PER_TOKEN = 4


def _resolve_repo_root(
    *,
    repo_root: Path | None,
    out_dir: Path | None,
) -> Path:
    """Resolve o repo root a partir de repo_root OU out_dir.

    Exactamente um dos dois tem de ser dado. Se for out_dir, reutiliza a
    mesma logica do skills.py (out costuma ser <repo>/pilots/<run>).
    """
    if repo_root is not None and out_dir is not None:
        raise ValueError("give repo_root OR out_dir, not both")
    if repo_root is None and out_dir is None:
        raise ValueError("give repo_root or out_dir")
    if repo_root is not None:
        return repo_root
    # out_dir: .../pilots/run-x -> parents[1] = repo
    assert out_dir is not None
    if out_dir.parent.name == "pilots":
        return out_dir.parent.parent
    return out_dir.parent


def resolve_memory_path(repo_root: Path, client_id: str) -> Path | None:
    """Path do MEMORY.md do cliente, ou None se nao existir.

    Nao valida client_id (o caller decide a politica). Se client_id for
    vazio, devolve None (nao ha memoria sem cliente).
    """
    if not client_id:
        return None
    p = repo_root / "memory" / client_id / "MEMORY.md"
    return p if p.is_file() else None


def read_memory(
    client_id: str,
    *,
    repo_root: Path | None = None,
    out_dir: Path | None = None,
) -> str | None:
    """Le o MEMORY.md do cliente. None se nao existir.

    Devolve o conteudo em bruto (utf-8). Nao trunca, nao resume, nao
    interpreta. O caller decide o que fazer com o texto.
    """
    root = _resolve_repo_root(repo_root=repo_root, out_dir=out_dir)
    path = resolve_memory_path(root, client_id)
    if path is None:
        return None
    return path.read_text(encoding="utf-8")


def memory_status(
    client_id: str,
    *,
    repo_root: Path | None = None,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    """Estado da memoria de um cliente, sem ler o conteudo em bruto.

    Devolve:
        {
            "client_id": str,
            "exists": bool,
            "path": str | None,        # path absoluto se existir
            "chars": int,              # 0 se nao existir
            "approx_tokens": int,      # chars // 4
            "over_limit": bool,        # approx_tokens > TOKEN_LIMIT_SOFT
            "limit": int,              # TOKEN_LIMIT_SOFT
        }

    Util para o engine (S7b) decidir se injecta contexto, e para um
    eventual endpoint de diagnostico. Nao bloqueia nada.
    """
    root = _resolve_repo_root(repo_root=repo_root, out_dir=out_dir)
    path = resolve_memory_path(root, client_id)

    if path is None:
        return {
            "client_id": client_id,
            "exists": False,
            "path": None,
            "chars": 0,
            "approx_tokens": 0,
            "over_limit": False,
            "limit": TOKEN_LIMIT_SOFT,
        }

    text = path.read_text(encoding="utf-8")
    chars = len(text)
    approx = chars // _CHARS_PER_TOKEN
    return {
        "client_id": client_id,
        "exists": True,
        "path": str(path),
        "chars": chars,
        "approx_tokens": approx,
        "over_limit": approx > TOKEN_LIMIT_SOFT,
        "limit": TOKEN_LIMIT_SOFT,
    }
