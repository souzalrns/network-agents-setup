"""Capabilities por domínio (Capability First) + inventário agente ↔ skill.

`config/<domínio>-capabilities.yaml` (hoje: `security-capabilities.yaml`)
descreve o que um domínio sabe fazer, sem criar um agente por capability. O
ficheiro não tem consumidor em runtime: por isso é validado no E7
(`python -m plan_runner.areas`), para não apodrecer em silêncio (a lição do
J5-b no PLANO). Regras:

- `domain` é uma área do areas.yaml e bate com o nome do ficheiro;
- política: `offensive: forbidden` e `act_in_production: forbidden` são as únicas
  opções aceites; `hitl` tem de ser `required` se a área o exigir;
- níveis: read | prepare | act | lab. `act` é recusado enquanto
  `act_in_production` for `forbidden`; `lab` só em capabilities `deferred`
  (fora do runner de produção);
- `implemented`/`partial`: `action`, `agent` e `skill` existem e batem uns com os
  outros (o `action:` do agente e o da skill são o da capability; o agente está
  em agents[] da área do domínio; o `skill:` declarado pelo agente é o mesmo);
- `deferred`/`planned`: podem ficar a null; se preenchidos, têm de existir.

O inventário (`python -m plan_runner.areas --inventory`) lista, sem falhar o CI:
agentes sem skill, skills sem agente (fora do pack `skills/claude/`), agentes
do runner que carregam skills do pack Claude (prompts longos, lição B1-bis) e
skills partilhadas cujo `action:` difere do agente.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .skills import _frontmatter, resolve_skill_path

LEVELS = ("read", "prepare", "act", "lab")
STATUSES = ("implemented", "partial", "deferred", "planned")
ACTIVE = ("implemented", "partial")
FORBIDDEN_ONLY = ("offensive", "act_in_production")
CLAUDE_PACK = "skills/claude/"


def capability_files(repo_root: Path) -> list[Path]:
    return sorted((repo_root / "config").glob("*-capabilities.yaml"))


def _rel_file(repo_root: Path, rel: Any) -> Path | None:
    """Ficheiro do repo a partir de um path relativo; None se não existir ou sair do repo."""
    if not isinstance(rel, str) or not rel:
        return None
    p = (repo_root / rel).resolve()
    if not p.is_relative_to(repo_root.resolve()) or not p.is_file():
        return None
    return p


def validate_capabilities(repo_root: Path, known: dict[str, Path], areas: list[dict]) -> list[str]:
    errors: list[str] = []
    by_area = {a.get("id"): a for a in areas if isinstance(a, dict)}
    for path in capability_files(repo_root):
        rel = path.relative_to(repo_root)
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as e:
            errors.append(f"{rel}: não é YAML legível ({e})")
            continue
        if not isinstance(data, dict):
            errors.append(f"{rel}: tem de ser um objecto")
            continue
        if not isinstance(data.get("version"), int) or isinstance(data.get("version"), bool):
            errors.append(f"{rel}: `version` tem de ser inteiro")
        domain = data.get("domain")
        area = by_area.get(domain)
        if area is None:
            errors.append(f"{rel}: domain `{domain}` não é uma área do areas.yaml")
        elif path.name != f"{domain}-capabilities.yaml":
            errors.append(f"{rel}: o ficheiro de domain `{domain}` chama-se `{domain}-capabilities.yaml`")
        area_agents = set((area or {}).get("agents") or [])

        policy = data.get("policy")
        if not isinstance(policy, dict):
            errors.append(f"{rel}: falta `policy`")
            policy = {}
        for key in FORBIDDEN_ONLY:
            if policy.get(key) != "forbidden":
                errors.append(f"{rel}: policy.{key} tem de ser `forbidden` (got {policy.get(key)!r})")
        if area is not None and area.get("hitl") == "required" and policy.get("hitl") != "required":
            errors.append(f"{rel}: a área `{domain}` tem `hitl: required`, por isso policy.hitl tem de ser `required`")
        if policy.get("default_level") not in LEVELS:
            errors.append(f"{rel}: policy.default_level tem de ser um de {', '.join(LEVELS)}")

        caps = data.get("capabilities")
        if not isinstance(caps, list) or not caps:
            errors.append(f"{rel}: falta a lista `capabilities` (não vazia)")
            continue
        seen: set[str] = set()
        for i, cap in enumerate(caps):
            if not isinstance(cap, dict) or not isinstance(cap.get("id"), str) or not cap["id"]:
                errors.append(f"{rel}: capabilities[{i}] sem `id`")
                continue
            where = f"{rel}: capability `{cap['id']}`"
            if cap["id"] in seen:
                errors.append(f"{where}: id repetido")
            seen.add(cap["id"])
            if not str(cap.get("description") or "").strip():
                errors.append(f"{where}: falta `description`")
            status = cap.get("status")
            if status not in STATUSES:
                errors.append(f"{where}: status tem de ser um de {', '.join(STATUSES)}")
            levels = cap.get("levels")
            if not isinstance(levels, list) or not levels or any(lv not in LEVELS for lv in levels):
                errors.append(f"{where}: levels tem de ser uma lista não vazia de {', '.join(LEVELS)}")
                levels = []
            if "act" in levels and policy.get("act_in_production") == "forbidden":
                errors.append(f"{where}: nível `act` proibido (policy.act_in_production: forbidden)")
            if "lab" in levels and status != "deferred":
                errors.append(f"{where}: nível `lab` só em capabilities `deferred` (fora do runner de produção)")
            tg = cap.get("tools_guidance")
            if tg is not None and (not isinstance(tg, list) or not all(isinstance(x, str) and x for x in tg)):
                errors.append(f"{where}: tools_guidance tem de ser uma lista de nomes")

            action, agent, skill = cap.get("action"), cap.get("agent"), cap.get("skill")
            if status in ACTIVE:
                for key, val in (("action", action), ("agent", agent), ("skill", skill)):
                    if not isinstance(val, str) or not val:
                        errors.append(f"{where}: `{key}` obrigatório em status `{status}`")
            if agent is not None:
                if agent not in known:
                    errors.append(f"{where}: agente `{agent}` não existe em agents/**/*.agent.md")
                else:
                    afm = _frontmatter(known[agent])
                    if status in ACTIVE and agent not in area_agents:
                        errors.append(f"{where}: agente `{agent}` não está em agents[] da área `{domain}`")
                    if action and afm.get("action") != action:
                        errors.append(f"{where}: o agente `{agent}` tem action `{afm.get('action')}`, não `{action}`")
                    if skill and afm.get("skill") and afm.get("skill") != skill:
                        errors.append(f"{where}: o agente `{agent}` declara a skill `{afm.get('skill')}`, não `{skill}`")
            if skill is not None:
                sp = _rel_file(repo_root, skill)
                if sp is None:
                    errors.append(f"{where}: skill `{skill}` não existe no repo")
                elif action and _frontmatter(sp).get("action") != action:
                    errors.append(f"{where}: a skill `{skill}` tem action `{_frontmatter(sp).get('action')}`, não `{action}`")
    return errors


def declared_skill_errors(repo_root: Path, known: dict[str, Path]) -> list[str]:
    """Um `skill:` declarado no frontmatter de um agente tem de existir (senão o worker cai na convenção em silêncio)."""
    errors = []
    for aid, path in sorted(known.items()):
        decl = _frontmatter(path).get("skill")
        if decl is not None and _rel_file(repo_root, decl) is None:
            errors.append(f"agente `{aid}` ({path.relative_to(repo_root)}): skill `{decl}` não existe no repo")
    return errors


def inventory(repo_root: Path, known: dict[str, Path]) -> dict[str, list[str]]:
    """Agente ↔ skill, só informativo (não falha o CI)."""
    used: set[Path] = set()
    out: dict[str, list[str]] = {"agents_without_skill": [], "skills_without_agent": [],
                                 "agents_using_claude_pack": [], "shared_skill_action_differs": []}
    for aid, path in sorted(known.items()):
        fm = _frontmatter(path)
        res = resolve_skill_path(repo_root, str(fm.get("action") or ""), str(fm.get("vertical") or path.parent.name))
        if res is None:
            out["agents_without_skill"].append(aid)
            continue
        used.add(res.resolve())
        rel = res.resolve().relative_to(repo_root.resolve()).as_posix()
        if rel.startswith(CLAUDE_PACK):
            out["agents_using_claude_pack"].append(f"{aid} -> {rel}")
        sk_action = _frontmatter(res).get("action")
        if sk_action and sk_action != fm.get("action"):
            out["shared_skill_action_differs"].append(f"{aid} ({fm.get('action')}) -> {rel} ({sk_action})")
    for s in sorted((repo_root / "skills").glob("**/SKILL.md")):
        rel = s.relative_to(repo_root).as_posix()
        if not rel.startswith(CLAUDE_PACK) and s.resolve() not in used:
            out["skills_without_agent"].append(rel)
    return out
