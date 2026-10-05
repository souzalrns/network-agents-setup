from __future__ import annotations

from pathlib import Path

import yaml


def repo_root_from_out(out_root: Path) -> Path:
    """Best-effort: out is often <repo>/pilots/<run>."""
    # out_root = .../pilots/run-x -> parents[1] = repo
    if out_root.parent.name == "pilots":
        return out_root.parent.parent
    return out_root.parent


def _frontmatter(path: Path) -> dict:
    """Frontmatter YAML de um .agent.md; {} se faltar ou for invalido."""
    try:
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return {}
        data = yaml.safe_load(text.split("---", 2)[1])
    except (OSError, IndexError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _find_agent_by_action(repo_root: Path, action: str, vertical: str) -> Path | None:
    """A8/D8: procura o agente pelo `action:` do frontmatter, nao pelo nome do
    ficheiro (23/35 agentes tinham action != nome, ex. security_auditor ->
    security_audit, ui -> ui_spec). Com action repetida, prefere o vertical pedido."""
    matches = [
        p for p in sorted((repo_root / "agents").glob("**/*.agent.md"))
        if _frontmatter(p).get("action") == action
    ]
    for p in matches:
        if (_frontmatter(p).get("vertical") or p.parent.name) == vertical:
            return p
    return matches[0] if matches else None


def resolve_skill_path(repo_root: Path, action: str, vertical: str = "marketing") -> Path | None:
    # A8: o `skill:` do frontmatter do agente tem prioridade (ex. security_auditor
    # -> skills/meta/security-audit, com hifen); sem ele, a convencao de sempre.
    agent = resolve_agent_path(repo_root, action, vertical)
    declared = _frontmatter(agent).get("skill") if agent else None
    if isinstance(declared, str) and declared:
        p = repo_root / declared
        if p.is_file() and p.resolve().is_relative_to(repo_root.resolve()):
            return p
    p = repo_root / "skills" / vertical / action / "SKILL.md"
    return p if p.is_file() else None


def resolve_agent_path(repo_root: Path, action: str, vertical: str = "marketing") -> Path | None:
    p = repo_root / "agents" / vertical / f"{action}.agent.md"
    if p.is_file():
        return p
    return _find_agent_by_action(repo_root, action, vertical)


def read_text_if_exists(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def skill_ref(out_root: Path, step) -> str | None:
    """Skill que o passo carrega, relativa ao repo (para o evento step_started).

    Mede o uso real das skills: so os planos e o router as carregam, e sem isto
    nao havia forma de saber quais correm. None se o passo nao resolver skill
    (ex.: gates humanos).
    """
    vertical = str(step.raw.get("vertical") or "marketing") if isinstance(step.raw, dict) else "marketing"
    repo = repo_root_from_out(Path(out_root))
    path = resolve_skill_path(repo, step.action, vertical)
    if path is None:
        return None
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return None
