"""Capabilities por domínio (Capability First) + inventário agente ↔ skill.

`config/<domínio>-capabilities.yaml` (hoje: `security` e `marketing`, F4)
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
- `deferred`/`planned`: podem ficar a null; se preenchidos, têm de existir;
- maturidade (F4): `implemented` exige evidência de uso, ou seja, pelo menos 1 plano do
  runner (`docs/orchestration/**/*.plan.yaml`) com um passo dessa `action`. Sem plano,
  a capability é `partial` (há executor, mas ainda nenhum fluxo a usa).
  Escala: planned < deferred < partial < implemented.

Maturidade (F4-MAT-1, P-38 = B): **medida, não declarada.** Nenhum campo novo nos
YAML de capabilities; o `status` continua a ser o âmbito declarado. A escala é a do
EXECUTION-PLAN §15.7 e cada nível exige o anterior:

- DRAFT: sem `action`;
- DECLARED: `action`, mas falta o agente ou a skill (ou não existem);
- WIRED: `action` + agente + skill existentes (o executor está ligado);
- EXECUTABLE: e pelo menos 1 plano do runner usa a `action`;
- VALIDATED: e um teste de `runner/tests/` corre esse plano com o Gemini falso
  (o ficheiro de teste cita o path do plano e troca o transport do worker);
- PROVEN: e um run real desse plano está registado em `config/capability-runs.yaml`,
  com o documento de evidência a citar o plano, o run e o `anchor` (verificado no E7).

Uma capability que não está `implemented` fica no máximo em EXECUTABLE: várias
partilham a mesma `action` e o mesmo agente (ex.: `secrets_hygiene` usa o
`security_audit`), e um run do auditor não prova a parte que o `status: partial` diz
que falta. `python -m plan_runner.areas --maturity` mostra a tabela.

O inventário (`python -m plan_runner.areas --inventory`) lista, sem falhar o CI:
agentes sem skill, skills sem agente (fora do pack `skills/claude/`), agentes
do runner que carregam skills do pack Claude (prompts longos, lição B1-bis) e
skills partilhadas cujo `action:` difere do agente.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from .skills import _frontmatter, resolve_skill_path

LEVELS = ("read", "prepare", "act", "lab")
STATUSES = ("implemented", "partial", "deferred", "planned")
ACTIVE = ("implemented", "partial")
FORBIDDEN_ONLY = ("offensive", "act_in_production")
CLAUDE_PACK = "skills/claude/"
PLAN_GLOB = "docs/orchestration/**/*.plan.yaml"
MATURITY = ("DRAFT", "DECLARED", "WIRED", "EXECUTABLE", "VALIDATED", "PROVEN")
RUNS_FILE = "config/capability-runs.yaml"
TESTS_GLOB = "runner/tests/test_*.py"
# Um teste "com o Gemini falso" troca o transport HTTP do worker (external_worker.httpx_transport).
FAKE_GEMINI_MARKER = "httpx_transport"
_PLAN_PATH = re.compile(r"docs/orchestration/[\w./-]+?\.plan\.yaml")


def capability_files(repo_root: Path) -> list[Path]:
    return sorted((repo_root / "config").glob("*-capabilities.yaml"))


def plan_actions(repo_root: Path) -> dict[str, list[str]]:
    """`action` → planos do runner que a usam (evidência de maturidade, F4)."""
    found: dict[str, list[str]] = {}
    for rel, actions in actions_by_plan(repo_root).items():
        for action in actions:
            found.setdefault(action, []).append(rel)
    return found


def actions_by_plan(repo_root: Path) -> dict[str, list[str]]:
    """Plano do runner (path relativo) → `action`s que usa, por ordem de aparição."""
    out: dict[str, list[str]] = {}

    def walk(node: Any, acc: list[str]) -> None:
        if isinstance(node, dict):
            action = node.get("action")
            if isinstance(action, str) and action and action not in acc:
                acc.append(action)
            for value in node.values():
                walk(value, acc)
        elif isinstance(node, list):
            for value in node:
                walk(value, acc)

    for path in sorted(repo_root.glob(PLAN_GLOB)):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            continue  # o plan_schema (W-006) já reporta planos ilegíveis
        acc: list[str] = []
        walk(data, acc)
        out[path.relative_to(repo_root).as_posix()] = acc
    return out


def validated_plans(repo_root: Path) -> dict[str, list[str]]:
    """Plano → testes que o correm com o Gemini falso (VALIDATED, §15.7)."""
    out: dict[str, list[str]] = {}
    for test in sorted(repo_root.glob(TESTS_GLOB)):
        text = test.read_text(encoding="utf-8")
        if FAKE_GEMINI_MARKER not in text:
            continue
        rel = test.relative_to(repo_root).as_posix()
        for plan in sorted(set(_PLAN_PATH.findall(text))):
            if (repo_root / plan).is_file():
                out.setdefault(plan, []).append(rel)
    return out


def load_runs(repo_root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Runs reais registados (PROVEN). Devolve (runs válidos e `passed`, erros). Sem ficheiro: ([], [])."""
    path = repo_root / RUNS_FILE
    if not path.is_file():
        return [], []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        return [], [f"{RUNS_FILE}: não é YAML legível ({e})"]
    runs = data.get("runs") if isinstance(data, dict) else None
    if not isinstance(runs, list):
        return [], [f"{RUNS_FILE}: falta a lista `runs`"]
    errors: list[str] = []
    ok: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, run in enumerate(runs):
        rid = run.get("id") if isinstance(run, dict) else None
        where = f"{RUNS_FILE}: runs[{i}]" + (f" `{rid}`" if rid else "")
        if not isinstance(run, dict) or not isinstance(rid, str) or not rid or rid in seen:
            errors.append(f"{where}: `id` em falta ou repetido")
            continue
        seen.add(rid)
        before = len(errors)
        if not isinstance(run.get("date"), date):
            errors.append(f"{where}: `date` tem de ser uma data (AAAA-MM-DD)")
        plan = run.get("plan")
        if not isinstance(plan, str) or not (repo_root / plan).is_file() or not plan.endswith(".plan.yaml"):
            errors.append(f"{where}: `plan` tem de ser um plano do runner que existe")
        if run.get("worker") != "gemini":
            errors.append(f"{where}: `worker` tem de ser `gemini` (um run real com o provider; stub não conta)")
        if run.get("verdict") not in ("passed", "failed"):
            errors.append(f"{where}: `verdict` tem de ser passed ou failed")
        evidence = _rel_file(repo_root, run.get("evidence"))
        anchor = run.get("anchor")
        if evidence is None:
            errors.append(f"{where}: `evidence` tem de ser um ficheiro do repo")
        elif not isinstance(anchor, str) or not anchor.strip():
            errors.append(f"{where}: falta `anchor` (texto que o documento de evidência tem de conter)")
        else:
            doc = evidence.read_text(encoding="utf-8")
            for label, needle in (("anchor", anchor), ("plano", Path(str(plan)).name), ("run_id", run.get("run_id"))):
                if needle and str(needle) not in doc:
                    errors.append(f"{where}: o documento {run['evidence']} não contém o {label} {needle!r}")
        if len(errors) == before and run["verdict"] == "passed":
            ok.append(run)
    return ok, errors


def capability_maturity(repo_root: Path, known: dict[str, Path]) -> list[dict[str, Any]]:
    """Maturidade medida de cada capability (§15.7, P-38 = B), com a evidência que a sustenta."""
    by_plan = actions_by_plan(repo_root)
    tested = validated_plans(repo_root)
    runs, _ = load_runs(repo_root)
    out: list[dict[str, Any]] = []
    for path in capability_files(repo_root):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue  # o E7 já reporta
        for cap in data.get("capabilities") or []:
            if not isinstance(cap, dict) or not cap.get("id"):
                continue
            action, agent, skill, status = cap.get("action"), cap.get("agent"), cap.get("skill"), cap.get("status")
            plans = [p for p, acts in by_plan.items() if action and action in acts]
            tests = sorted({t for p in plans for t in tested.get(p, [])})
            proven = [r["id"] for r in runs if r["plan"] in plans]
            checks = [
                bool(action),
                agent in known and _rel_file(repo_root, skill) is not None,
                bool(plans),
                bool(tests),
                bool(proven),
            ]
            level = 0
            for passed in checks:
                if not passed:
                    break
                level += 1
            note = None
            ceiling = MATURITY.index("EXECUTABLE")
            if status != "implemented" and level > ceiling:
                note = f"limitado a EXECUTABLE pelo status `{status}` (a evidência é da action partilhada)"
                level = ceiling
            out.append({
                "domain": data.get("domain"), "id": cap["id"], "status": status, "maturity": MATURITY[level],
                "action": action, "plans": plans, "tests": tests, "runs": proven, "note": note,
            })
    return out


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
    used_actions = plan_actions(repo_root)
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
            if status == "implemented" and isinstance(action, str) and action not in used_actions:
                errors.append(
                    f"{where}: `implemented` exige pelo menos 1 plano em {PLAN_GLOB} com a action "
                    f"`{action}` (maturidade, F4); sem plano, use `partial`"
                )
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
