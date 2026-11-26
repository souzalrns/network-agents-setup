"""M-008 (fase 1): regras do plano verificadas pelo motor antes de arrancar.

As regras vivem em `config/plan-policy.yaml` (o cabeçalho desse ficheiro explica cada uma).
`engine.load_plan` chama `check_plan` depois da validação estrutural (`graph.validate_plan`),
por isso valem para todos os caminhos que correm um plano: run, resume, dry-run, LangGraph e
router. Um plano que falhe não arranca (`PolicyError`, com a lista de regras falhadas).

Fail-closed: ficheiro de regras em falta ou inválido, acção sem agente ou valor desconhecido
recusam o plano. Não há campo no plano nem variável de ambiente para desligar a verificação;
`policy_path` só existe para os testes apontarem para uma cópia das regras.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .graph import PlanError
from .models import Plan, Step
from .skills import _frontmatter
from .tool_executor import REGISTRY

REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_FILE = REPO_ROOT / "config" / "plan-policy.yaml"


class PolicyError(PlanError):
    """O plano não cumpre as regras de config/plan-policy.yaml (não arranca)."""

    def __init__(self, plan_id: str, violations: list[str]):
        self.plan_id = plan_id
        self.violations = violations
        super().__init__(f"plano `{plan_id}` recusado pelas regras do motor:\n- " + "\n- ".join(violations))


def load_policy(path: Path | None = None) -> dict[str, Any]:
    p = Path(path) if path else POLICY_FILE
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        raise PolicyError("?", [f"R9: não foi possível ler as regras do motor ({p.name}): {e}"]) from e
    errors: list[str] = []
    if not isinstance(data, dict) or data.get("version") != 1:
        errors.append("R9: regras do motor sem `version: 1`")
        data = data if isinstance(data, dict) else {}
    g = data.get("global")
    if not isinstance(g, dict):
        errors.append("R9: regras do motor sem bloco `global`")
    else:
        cap = g.get("max_steps_cap")
        if not isinstance(cap, int) or isinstance(cap, bool) or cap < 1:
            errors.append("R9: `global.max_steps_cap` tem de ser um inteiro >= 1")
        for k in ("gate_actions", "delivery_values"):
            if not isinstance(g.get(k), list) or not g.get(k):
                errors.append(f"R9: `global.{k}` tem de ser uma lista não vazia")
    if not isinstance(data.get("verticals"), dict):
        errors.append("R9: regras do motor sem bloco `verticals`")
    else:
        for vert, prof in data["verticals"].items():
            errors += _profile_errors(str(vert), prof)
    if errors:
        raise PolicyError("?", errors)
    return data


def _strs(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(x, str) and x for x in value)


def _profile_errors(vert: str, prof: Any) -> list[str]:
    """Tipos de um perfil de vertical: um valor estranho recusa tudo (R9), não fica a meio."""
    tag = f"R9: `verticals.{vert}`"
    if not isinstance(prof, dict):
        return [f"{tag} tem de ser um mapa"]
    errs = []
    for k in ("require_delivery", "require_explicit_max_steps"):
        if k in prof and not isinstance(prof[k], bool):
            errs.append(f"{tag}.{k} tem de ser true ou false")
    for k in ("review_before_gate", "indexable_deliverables", "external_actions"):
        if k in prof and not _strs(prof[k]):
            errs.append(f"{tag}.{k} tem de ser uma lista de nomes")
    for k in ("citability_action", "leader_prefix", "area_deliverable_prefix"):
        if k in prof and not (isinstance(prof[k], str) and prof[k]):
            errs.append(f"{tag}.{k} tem de ser um nome")
    if "knowledge" in prof:
        kn = prof["knowledge"]
        mq = kn.get("min_query_chars", 1) if isinstance(kn, dict) else None
        if not isinstance(kn, dict) or not _strs(kn.get("allowed_kbs")) or not kn.get("allowed_kbs") \
                or not isinstance(mq, int) or isinstance(mq, bool) or mq < 1:
            errs.append(f"{tag}.knowledge tem de ter allowed_kbs (lista não vazia) e min_query_chars (inteiro >= 1)")
    return errs


def policy_kb(vertical: str, path: Path | None = None) -> str | None:
    """1.º kb permitido se a vertical exigir conhecimento em cada passo (R6); None se não exigir."""
    prof = load_policy(path)["verticals"].get(vertical)
    kn = prof.get("knowledge") if isinstance(prof, dict) else None
    kbs = kn.get("allowed_kbs") if isinstance(kn, dict) else None
    return str(kbs[0]) if kbs else None


def requires_knowledge(step: Step, *, policy_path: Path | None = None, repo_root: Path | None = None) -> bool:
    """O passo tem de receber contexto da base de conhecimento (R6 da vertical dele)?"""
    policy = load_policy(policy_path)
    if _is_gate(step, {str(a) for a in policy["global"]["gate_actions"]}):
        return False
    vert = _step_vertical(step, _agent_index(str((repo_root or REPO_ROOT).resolve())))
    prof = policy["verticals"].get(vert) if vert else None
    return isinstance(prof, dict) and isinstance(prof.get("knowledge"), dict)


@lru_cache(maxsize=4)
def _agent_index(repo_root: str) -> dict[str, list[str]]:
    """action -> verticais dos agentes com essa action (frontmatter de agents/**/*.agent.md)."""
    index: dict[str, list[str]] = {}
    for p in sorted(Path(repo_root, "agents").glob("**/*.agent.md")):
        fm = _frontmatter(p)
        action = fm.get("action")
        if action:
            index.setdefault(str(action), []).append(str(fm.get("vertical") or p.parent.name))
    return index


def _step_vertical(step: Step, index: dict[str, list[str]]) -> str | None:
    """Vertical do agente que o passo resolve (a mesma preferência de skills._find_agent_by_action)."""
    verticals = index.get(step.action)
    if not verticals:
        return None
    wanted = str(step.raw.get("vertical") or "marketing") if isinstance(step.raw, dict) else "marketing"
    return wanted if wanted in verticals else verticals[0]


def _ancestors(by_id: dict[str, Step], sid: str) -> set[str]:
    seen: set[str] = set()
    stack = list(by_id[sid].depends_on)
    while stack:
        d = stack.pop()
        if d not in seen:
            seen.add(d)
            stack.extend(by_id[d].depends_on)
    return seen


def _is_gate(step: Step, gate_actions: set[str]) -> bool:
    return step.human_gate is not None or step.action in gate_actions


def _done_when_gates(plan: Plan) -> list[str]:
    out = []
    for line in plan.done_when:
        parts = str(line).split()
        if len(parts) == 3 and parts[0] == "human_gate_resolved" and parts[1] == "on":
            out.append(parts[2])
    return out


def check_plan(plan: Plan, *, policy_path: Path | None = None, repo_root: Path | None = None) -> None:
    """Levanta PolicyError se o plano falhar alguma regra; não devolve nada se cumprir todas."""
    policy = load_policy(policy_path)
    g = policy["global"]
    gate_actions = {str(a) for a in g["gate_actions"]}
    index = _agent_index(str((repo_root or REPO_ROOT).resolve()))
    by_id = {s.id: s for s in plan.steps}
    raw = plan.raw if isinstance(plan.raw, dict) else {}
    v: list[str] = []

    # R9 acções e verticais em uso
    if not plan.steps:
        v.append("R9: o plano não tem passos")
    in_vertical: dict[str, list[Step]] = {}
    for s in plan.steps:
        if _is_gate(s, gate_actions):
            if s.human_gate is None:
                v.append(f"R9: o passo `{s.id}` (`{s.action}`) é uma aprovação mas não tem `human_gate`")
            continue
        vert = _step_vertical(s, index)
        if vert is None:
            v.append(f"R9: o passo `{s.id}` usa a acção `{s.action}`, que nenhum agente tem (agents/**/*.agent.md)")
            continue
        in_vertical.setdefault(vert, []).append(s)

    # R1 ferramentas
    for s in plan.steps:
        unknown = [str(t) for t in s.tools_allowed if str(t) not in REGISTRY]
        if unknown:
            v.append(f"R1: o passo `{s.id}` declara ferramentas que o motor não tem: {', '.join(unknown)}")

    # R3 teto
    budget = raw.get("budget") if isinstance(raw.get("budget"), dict) else {}
    declared = budget.get("max_steps")
    if declared is not None and (not isinstance(declared, int) or isinstance(declared, bool)
                                 or not 1 <= declared <= g["max_steps_cap"]):
        v.append(f"R3: `budget.max_steps` tem de ser um inteiro entre 1 e {g['max_steps_cap']} (veio {declared!r})")

    # R2 entrega
    delivery = raw.get("delivery")
    if delivery is not None and delivery not in g["delivery_values"]:
        v.append(f"R2: `delivery` tem de ser {' ou '.join(g['delivery_values'])} (veio {delivery!r})")
    # um passo que prepara uma publicação faz do plano uma entrega externa, diga o plano o que disser
    publishing = [s for vert, ss in in_vertical.items() for s in ss
                  if s.action in ((policy["verticals"].get(vert) or {}).get("external_actions") or [])]
    if publishing and delivery != "external":
        v.append(f"R2: o passo `{publishing[0].id}` (`{publishing[0].action}`) prepara uma publicação: "
                 "o plano tem de declarar `delivery: external`")
        delivery = "external"
    final_gates = [gid for gid in _done_when_gates(plan) if gid in by_id and by_id[gid].human_gate is not None]
    if delivery == "external":
        if not final_gates:
            v.append("R2: entrega externa sem aprovação humana em `done_when` (`human_gate_resolved on <id do passo>`)")
        else:
            # nada fica fora da aprovação final: nem ao lado dela, nem depois dela
            covered = set().union(*(_ancestors(by_id, gid) for gid in final_gates)) | set(final_gates)
            loose = [s.id for s in plan.steps if s.id not in covered and s.human_gate is None]
            if loose:
                v.append(f"R2: entrega externa com passos fora da aprovação humana final: {', '.join(loose)}")

    # Perfis por vertical
    for vert, steps in sorted(in_vertical.items()):
        prof = policy["verticals"].get(vert)
        if not isinstance(prof, dict):
            continue
        tag = f"[{vert}]"
        if prof.get("require_explicit_max_steps") and declared is None:
            v.append(f"R3 {tag}: o plano tem de declarar `budget.max_steps`")
        if prof.get("require_delivery") and delivery is None:
            v.append(f"R2 {tag}: o plano tem de declarar `delivery: internal` ou `delivery: external`")
        if delivery == "external":
            needed = [str(a) for a in prof.get("review_before_gate") or []]
            dtype = str(raw.get("deliverable_type") or "")
            if dtype in (prof.get("indexable_deliverables") or []) and prof.get("citability_action"):
                needed.append(str(prof["citability_action"]))
            reviewers = set(needed) | {str(a) for a in prof.get("review_before_gate") or []}
            for gid in final_gates:
                direct = {by_id[d].action for d in by_id[gid].depends_on}
                missing = [a for a in needed if a not in direct]
                if missing:
                    rule = "R5" if missing == [prof.get("citability_action")] else "R4"
                    v.append(f"{rule} {tag}: a aprovação `{gid}` tem de depender directamente de: {', '.join(missing)}")
                # cada revisor tem de ver o trabalho todo que a aprovação cobre (não basta existir)
                work = {a for a in _ancestors(by_id, gid)
                        if by_id[a].human_gate is None and by_id[a].action not in reviewers}
                for d in by_id[gid].depends_on:
                    if by_id[d].action in needed:
                        unseen = sorted(work - _ancestors(by_id, d))
                        if unseen:
                            v.append(f"R4 {tag}: o revisor `{d}` (`{by_id[d].action}`) não recebe o trabalho de: {', '.join(unseen)}")
        kn = prof.get("knowledge")
        if isinstance(kn, dict):
            kbs = [str(k) for k in kn.get("allowed_kbs") or []]
            min_q = int(kn.get("min_query_chars", 1))
            for s in steps:
                spec = s.raw.get("knowledge") if isinstance(s.raw, dict) else None
                if not isinstance(spec, dict):
                    v.append(f"R6 {tag}: o passo `{s.id}` (`{s.action}`) não consulta a base de conhecimento (falta `knowledge:`)")
                    continue
                if spec.get("kb") not in kbs:
                    v.append(f"R6 {tag}: o passo `{s.id}` usa `knowledge.kb: {spec.get('kb')!r}`; permitido: {', '.join(kbs)}")
                q = spec.get("query")
                if not isinstance(q, str) or len(q.strip()) < min_q:
                    v.append(f"R6 {tag}: o passo `{s.id}` tem `knowledge.query` vazia ou com menos de {min_q} caracteres")
        prefix = prof.get("leader_prefix")
        if prefix:
            leaders = [s for s in steps if s.action.startswith(str(prefix))]
            area_prefix = prof.get("area_deliverable_prefix")
            if area_prefix and str(raw.get("deliverable_type") or "").startswith(str(area_prefix)) and not leaders:
                v.append(f"R7 {tag}: um plano de área (`{raw.get('deliverable_type')}`) tem de ter o passo do líder (`{prefix}*`)")
            if len(leaders) > 1:
                v.append(f"R7 {tag}: só pode haver um líder no plano (há {', '.join(s.id for s in leaders)})")
            elif leaders:
                lid = leaders[0].id
                behind = [s.id for s in plan.steps if s.id != lid and lid not in _ancestors(by_id, s.id)]
                if behind:
                    v.append(f"R7 {tag}: estes passos não dependem do líder `{lid}`: {', '.join(behind)}")

    if v:
        raise PolicyError(plan.id, v)
