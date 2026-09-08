from __future__ import annotations

from pathlib import Path


def repo_root_from_out(out_root: Path) -> Path:
    """Best-effort: out is often <repo>/pilots/<run>."""
    # out_root = .../pilots/run-x -> parents[1] = repo
    if out_root.parent.name == "pilots":
        return out_root.parent.parent
    return out_root.parent


def resolve_skill_path(repo_root: Path, action: str, vertical: str = "marketing") -> Path | None:
    p = repo_root / "skills" / vertical / action / "SKILL.md"
    return p if p.is_file() else None


def resolve_agent_path(repo_root: Path, action: str, vertical: str = "marketing") -> Path | None:
    p = repo_root / "agents" / vertical / f"{action}.agent.md"
    return p if p.is_file() else None


def read_text_if_exists(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    return path.read_text(encoding="utf-8")
