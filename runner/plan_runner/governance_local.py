"""GOV-LOCAL-1 (P-93 = B): contrato local mínimo de governança, sem dependências nem rede.

Três peças, todas em ficheiros append-only dentro do run (ou da pasta que o chamador escolher):

- **Política** (`config/governance.yaml`): quem pode fazer o quê. `deny` ganha a `approve`, que ganha a `allow`.
  Sem regra aplicável, decide `default` (por omissão `deny`: fail-closed).
- **Grafo de delegação** (`delegations.jsonl`): quem delegou que capacidades a quem, até quando e com que
  profundidade. Só se delega o que se tem (o âmbito só encolhe), sem ciclos, com raiz humana, revogável.
- **Recibos de ação** (`receipts.jsonl`): um por ação governada, com hash encadeado ao anterior e, se existir a
  chave `GOVERNANCE_HMAC_KEY`, assinatura HMAC-SHA256. `verify` apanha edição, remoção no meio, reordenação e
  (com o `receipts.head`) corte do fim.

Limite honesto: sem uma âncora fora do ficheiro (assinatura com chave que o atacante não tem, ou o hash final
guardado noutro sítio) quem puder escrever na pasta pode refazer a cadeia inteira. O HMAC e o `receipts.head`
levantam a fasquia; não substituem um registo externo. O Microsoft AGT, o Cedar e o AgentMesh entram depois,
como adaptadores opcionais, sem reescrever este contrato.

O motor usa isto em `engine.py` (`governance_gate`, `governance_receipt`). Em `mode: record` (omissão) só regista;
em `mode: enforce` recusa o passo que a política não autorize.
"""
from __future__ import annotations

import argparse
import contextlib
import fnmatch
import hashlib
import hmac
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = REPO_ROOT / "config" / "governance.yaml"
DELEGATIONS = "delegations.jsonl"
RECEIPTS = "receipts.jsonl"
HEAD = "receipts.head"
EFFECTS = ("allow", "approve", "deny")
MODES = ("record", "enforce")
HMAC_ENV = "GOVERNANCE_HMAC_KEY"
MAX_DEPTH_DEFAULT = 3
GENESIS = "0" * 64


class GovernanceError(RuntimeError):
    """Pedido inválido ou ficheiro de governança corrompido."""


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat()


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError as e:
        raise GovernanceError(f"data inválida: {ts!r}") from e
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_inputs(inputs: Any) -> str:
    """Hash estável dos inputs relevantes (o recibo guarda o hash, nunca o conteúdo)."""
    return sha256_text(canonical(inputs))


@contextlib.contextmanager
def _lock(path: Path, timeout: float = 5.0):
    """Lock portável (Windows incluído): ficheiro criado em exclusivo; lock com mais de 30 s é considerado órfão."""
    lock = path.with_suffix(path.suffix + ".lock")
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > 30:
                    lock.unlink()
                    continue
            except OSError:
                pass
            if time.monotonic() > deadline:
                raise GovernanceError(f"não consegui o lock de {path.name} (outro processo a escrever?)") from None
            time.sleep(0.02)
    try:
        yield
    finally:
        with contextlib.suppress(OSError):
            lock.unlink()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            raise GovernanceError(f"{path.name}:{n} não é JSON válido ({e.msg})") from e
        if not isinstance(row, dict):
            raise GovernanceError(f"{path.name}:{n} não é um objecto")
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Política
# ---------------------------------------------------------------------------

@dataclass
class Decision:
    effect: str                      # allow | approve | deny
    reason: str
    chain: list[str] = field(default_factory=list)   # ids das delegações usadas (raiz primeiro)

    @property
    def allowed(self) -> bool:
        return self.effect == "allow"


@dataclass
class Policy:
    mode: str
    default: str
    rules: list[dict[str, str]]
    max_depth: int = MAX_DEPTH_DEFAULT

    def match(self, agent: str, capability: str) -> str | None:
        """deny > approve > allow entre todas as regras que se aplicam; None se nenhuma se aplica."""
        hit = {r["effect"] for r in self.rules if fnmatch.fnmatchcase(agent, r["agent"]) and fnmatch.fnmatchcase(capability, r["capability"])}
        for effect in EFFECTS[::-1]:
            if effect in hit:
                return effect
        return None


def validate_config(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict) or data.get("version") != 1:
        return ["config/governance.yaml sem `version: 1`"]
    if data.get("mode") not in MODES:
        errors.append(f"`mode` tem de ser um de {MODES}")
    if data.get("default") not in EFFECTS:
        errors.append(f"`default` tem de ser um de {EFFECTS}")
    md = data.get("max_delegation_depth", MAX_DEPTH_DEFAULT)
    if isinstance(md, bool) or not isinstance(md, int) or not 1 <= md <= 10:
        errors.append("`max_delegation_depth` tem de ser um inteiro de 1 a 10")
    rules = data.get("rules")
    if not isinstance(rules, list):
        errors.append("`rules` tem de ser uma lista")
        return errors
    for i, r in enumerate(rules, 1):
        if not isinstance(r, dict) or set(r) != {"agent", "capability", "effect"}:
            errors.append(f"regra {i}: precisa exactamente de agent, capability e effect")
        elif r["effect"] not in EFFECTS or not all(isinstance(r[k], str) and r[k] for k in ("agent", "capability")):
            errors.append(f"regra {i}: effect fora de {EFFECTS} ou agent/capability vazios")
    return errors


def load_policy(path: Path | None = None) -> Policy:
    """Fail-closed: ficheiro em falta ou inválido recusa (GovernanceError), nunca devolve uma política permissiva."""
    p = Path(path) if path else CONFIG_FILE
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        raise GovernanceError(f"não foi possível ler {p.name}: {e}") from e
    errors = validate_config(data)
    if errors:
        raise GovernanceError(f"{p.name} inválido:\n- " + "\n- ".join(errors))
    return Policy(mode=data["mode"], default=data["default"], rules=list(data["rules"]),
                  max_depth=int(data.get("max_delegation_depth", MAX_DEPTH_DEFAULT)))


# ---------------------------------------------------------------------------
# Grafo de delegação
# ---------------------------------------------------------------------------

def _covers(scope: list[str], capability: str) -> bool:
    return any(fnmatch.fnmatchcase(capability, pattern) for pattern in scope)


def _is_root(actor: str) -> bool:
    return actor.startswith("human:")


class DelegationGraph:
    """Concessões e revogações em `delegations.jsonl` (append-only). O estado é sempre recalculado do ficheiro."""

    def __init__(self, directory: Path, *, max_depth: int = MAX_DEPTH_DEFAULT):
        self.path = Path(directory) / DELEGATIONS
        self.max_depth = max_depth

    # -- leitura --------------------------------------------------------------
    def _state(self) -> tuple[dict[str, dict[str, Any]], set[str]]:
        edges: dict[str, dict[str, Any]] = {}
        revoked: set[str] = set()
        for row in _read_jsonl(self.path):
            if row.get("op") == "grant":
                edges[row["id"]] = row
            elif row.get("op") == "revoke":
                revoked.add(row["edge"])
        return edges, revoked

    def _valid(self, edge: dict[str, Any], edges: dict[str, dict[str, Any]], revoked: set[str], now: datetime) -> bool:
        seen: set[str] = set()
        cur: dict[str, Any] | None = edge
        while cur is not None:
            if cur["id"] in seen or cur["id"] in revoked:
                return False
            seen.add(cur["id"])
            exp = _parse(cur.get("expires_at"))
            if exp is not None and exp <= now:
                return False
            parent = cur.get("parent")
            if parent is None:
                return _is_root(cur["from"])
            cur = edges.get(parent)
        return False

    def chain_for(self, agent: str, capability: str, *, now: datetime | None = None) -> list[str] | None:
        """Cadeia de ids (raiz primeiro) que dá `capability` a `agent`, ou None."""
        now = now or _now()
        edges, revoked = self._state()
        for edge in edges.values():
            if edge["to"] != agent or not _covers(edge["scope"], capability) or not self._valid(edge, edges, revoked, now):
                continue
            chain = [edge["id"]]
            cur = edge
            while cur.get("parent"):
                cur = edges[cur["parent"]]
                chain.append(cur["id"])
            return chain[::-1]
        return None

    # -- escrita --------------------------------------------------------------
    def grant(self, *, from_: str, to: str, scope: list[str], granted_by: str, expires_at: str | None = None,
              parent: str | None = None, now: datetime | None = None) -> dict[str, Any]:
        now = now or _now()
        if not scope or not all(isinstance(s, str) and s for s in scope):
            raise GovernanceError("o âmbito (scope) não pode ser vazio")
        if from_ == to:
            raise GovernanceError("ninguém delega a si próprio")
        if not _is_root(granted_by):
            raise GovernanceError("a concessão tem de ser autorizada por um humano (`human:<nome>`)")
        exp = _parse(expires_at)
        if exp is not None and exp <= now:
            raise GovernanceError("a delegação já nasce expirada")
        with _lock(self.path):
            edges, revoked = self._state()
            depth = 0
            if parent is None:
                if not _is_root(from_):
                    raise GovernanceError("sem delegação-mãe, quem delega tem de ser humano (`human:<nome>`)")
            else:
                par = edges.get(parent)
                if par is None or par["to"] != from_ or not self._valid(par, edges, revoked, now):
                    raise GovernanceError(f"delegação-mãe {parent!r} inexistente, de outro agente, revogada ou expirada")
                if not all(_covers(par["scope"], s) for s in scope):
                    raise GovernanceError("só se delega o que se tem: o âmbito novo sai do âmbito da delegação-mãe")
                par_exp = _parse(par.get("expires_at"))
                if par_exp is not None and (exp is None or exp > par_exp):
                    raise GovernanceError("a delegação não pode durar mais do que a delegação-mãe")
                depth = int(par["depth"]) + 1
                cur, members = par, {par["from"], par["to"]}
                while cur.get("parent"):
                    cur = edges[cur["parent"]]
                    members |= {cur["from"], cur["to"]}
                if to in members:
                    raise GovernanceError(f"ciclo: {to!r} já está na cadeia de delegação")
            if depth >= self.max_depth:
                raise GovernanceError(f"profundidade máxima de delegação ({self.max_depth}) atingida")
            edge = {"op": "grant", "id": f"del_{uuid.uuid4().hex[:10]}", "from": from_, "to": to, "scope": sorted(set(scope)),
                    "granted_by": granted_by, "parent": parent, "depth": depth, "created_at": _iso(now),
                    "expires_at": _iso(exp) if exp else None}
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(edge, ensure_ascii=False) + "\n")
        return edge

    def revoke(self, edge_id: str, *, by: str, now: datetime | None = None) -> dict[str, Any]:
        if not _is_root(by):
            raise GovernanceError("só um humano revoga (`human:<nome>`)")
        with _lock(self.path):
            edges, _ = self._state()
            if edge_id not in edges:
                raise GovernanceError(f"delegação {edge_id!r} inexistente")
            row = {"op": "revoke", "edge": edge_id, "by": by, "at": _iso(now or _now())}
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row


# ---------------------------------------------------------------------------
# Autorização = política + delegações
# ---------------------------------------------------------------------------

def authorize(policy: Policy, graph: DelegationGraph | None, agent: str, capability: str, *, now: datetime | None = None) -> Decision:
    """deny da política ganha sempre. Depois, uma delegação válida dá `allow`; senão decide a política (ou o `default`)."""
    matched = policy.match(agent, capability)
    if matched == "deny":
        return Decision("deny", f"política nega {capability!r} a {agent!r}")
    chain = graph.chain_for(agent, capability, now=now) if graph else None
    if chain:
        return Decision("allow", f"delegação válida de {capability!r} a {agent!r}", chain)
    if matched is not None:
        return Decision(matched, f"política: {matched} {capability!r} para {agent!r}")
    return Decision(policy.default, f"sem regra nem delegação para {capability!r} de {agent!r}: default {policy.default}")


# ---------------------------------------------------------------------------
# Recibos de ação
# ---------------------------------------------------------------------------

def _sign(hash_hex: str) -> str | None:
    key = os.environ.get(HMAC_ENV)
    if not key:
        return None
    return hmac.new(key.encode("utf-8"), hash_hex.encode("ascii"), hashlib.sha256).hexdigest()


class ReceiptLog:
    def __init__(self, directory: Path):
        self.dir = Path(directory)
        self.path = self.dir / RECEIPTS
        self.head = self.dir / HEAD

    def append(self, *, run_id: str, step_id: str | None, agent: str, capability: str, decision: Decision | str,
               inputs: Any = None, approver: str | None = None, cost_usd: float | None = None, tokens: int | None = None,
               artifacts: list[dict[str, str]] | None = None, detail: str | None = None) -> dict[str, Any]:
        dec = decision if isinstance(decision, Decision) else Decision(decision, "")
        if dec.effect not in EFFECTS:
            raise GovernanceError(f"decisão {dec.effect!r} fora de {EFFECTS}")
        if approver is not None and not _is_root(approver):
            raise GovernanceError("o aprovador de um recibo é um humano (`human:<nome>`)")
        self.dir.mkdir(parents=True, exist_ok=True)
        with _lock(self.path):
            rows = _read_jsonl(self.path)
            prev = rows[-1]["hash"] if rows else GENESIS
            body = {"seq": len(rows) + 1, "ts": _iso(_now()), "run_id": run_id, "step_id": step_id, "agent": agent,
                    "capability": capability, "inputs_hash": hash_inputs(inputs) if inputs is not None else None,
                    "decision": dec.effect, "reason": dec.reason, "delegation_chain": dec.chain, "approver": approver,
                    "cost_usd": cost_usd, "tokens": tokens, "artifacts": artifacts or [], "detail": detail, "prev": prev}
            digest = sha256_text(prev + canonical(body))
            rec = {**body, "hash": digest, "sig": _sign(digest)}
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            self.head.write_text(f"{rec['seq']} {rec['hash']}\n", encoding="utf-8")
        return rec

    def verify(self) -> list[str]:
        """Lista de problemas (vazia = cadeia íntegra). Nunca lança por conteúdo adulterado."""
        problems: list[str] = []
        try:
            rows = _read_jsonl(self.path)
        except GovernanceError as e:
            return [str(e)]
        prev = GENESIS
        key_missing_noted = False
        for i, rec in enumerate(rows, 1):
            if rec.get("seq") != i:
                problems.append(f"recibo {i}: seq {rec.get('seq')!r} (falta ou foi reordenado um recibo)")
            if rec.get("prev") != prev:
                problems.append(f"recibo {i}: `prev` não bate com o recibo anterior (cadeia quebrada)")
            body = {k: v for k, v in rec.items() if k not in ("hash", "sig")}
            if sha256_text(str(rec.get("prev")) + canonical(body)) != rec.get("hash"):
                problems.append(f"recibo {i}: o conteúdo não bate com o hash (adulterado)")
            sig = rec.get("sig")
            if sig:
                expected = _sign(str(rec.get("hash")))
                if expected is None:
                    if not key_missing_noted:
                        problems.append(f"recibos assinados mas {HMAC_ENV} não está definida: assinaturas por verificar")
                        key_missing_noted = True
                elif not hmac.compare_digest(sig, expected):
                    problems.append(f"recibo {i}: assinatura inválida")
            elif os.environ.get(HMAC_ENV):
                problems.append(f"recibo {i}: sem assinatura, mas {HMAC_ENV} está definida")
            prev = str(rec.get("hash"))
        if self.head.exists():
            try:
                seq, last = self.head.read_text(encoding="utf-8").split()
                if int(seq) != len(rows) or (rows and last != rows[-1].get("hash")):
                    problems.append(f"{HEAD} diz {seq} recibos com fim {last[:12]}…, o ficheiro tem {len(rows)} (cortado ou refeito)")
            except ValueError:
                problems.append(f"{HEAD} ilegível")
        elif rows:
            problems.append(f"falta {HEAD} (não dá para detetar corte no fim)")
        return problems

    def records(self) -> list[dict[str, Any]]:
        return _read_jsonl(self.path)


# ---------------------------------------------------------------------------
# Ligação ao motor (engine.py)
# ---------------------------------------------------------------------------

STEP_CAPABILITY = "step:run"


def step_capabilities(step: Any) -> list[str]:
    return [STEP_CAPABILITY, *[f"tool:{t}" for t in getattr(step, "tools_allowed", []) or []]]


def governance_gate(out: Path, step: Any, *, policy: Policy | None = None) -> tuple[bool, Decision]:
    """Antes de um passo. Em `record` nunca bloqueia; em `enforce` bloqueia o que a política não autoriza.
    `approve` só vale com gate humano no passo (o HITL é a aprovação). Devolve (pode_correr, decisão mais restritiva)."""
    pol = policy or load_policy()
    graph = DelegationGraph(out, max_depth=pol.max_depth)
    worst = Decision("allow", "")
    for cap in step_capabilities(step):
        d = authorize(pol, graph, step.action, cap)
        if d.effect == "approve" and getattr(step, "human_gate", None):
            d = Decision("allow", f"{d.reason}; coberto pelo gate humano do passo")
        if EFFECTS.index(d.effect) > EFFECTS.index(worst.effect):
            worst = Decision(d.effect, f"{cap}: {d.reason}", d.chain)
        elif worst.effect == "allow" and not worst.reason:
            worst = Decision("allow", d.reason, d.chain)
    if pol.mode == "record":
        return True, worst
    return worst.effect == "allow", worst


def governance_receipt(out: Path, run_id: str, step: Any, decision: Decision, *, detail: str | None = None,
                       artifact: str | None = None, approver: str | None = None) -> dict[str, Any]:
    """Recibo de um passo concluído. O artefacto entra com o sha256 do ficheiro, se existir."""
    arts: list[dict[str, str]] = []
    if artifact:
        p = Path(out) / artifact
        arts.append({"path": artifact, "sha256": hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "ausente"})
    return ReceiptLog(out).append(
        run_id=run_id, step_id=step.id, agent=step.action, capability=STEP_CAPABILITY, decision=decision,
        inputs={"inputs": list(getattr(step, "inputs", []) or []), "tools_allowed": list(step.tools_allowed or [])},
        approver=approver, artifacts=arts, detail=detail)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="plan_runner.governance_local", description="Governança local: delegações e recibos (GOV-LOCAL-1)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verify", help="Verifica a cadeia de recibos de uma pasta de run")
    v.add_argument("dir", type=Path)
    c = sub.add_parser("check", help="Autoriza (agente, capacidade) com a política e as delegações da pasta")
    c.add_argument("dir", type=Path)
    c.add_argument("agent")
    c.add_argument("capability")
    g = sub.add_parser("delegate", help="Um humano delega capacidades a um agente (ou um agente sub-delega)")
    g.add_argument("dir", type=Path)
    g.add_argument("--from", dest="from_", required=True)
    g.add_argument("--to", required=True)
    g.add_argument("--scope", required=True, help="capacidades separadas por vírgula (aceita * e ?)")
    g.add_argument("--by", required=True, help="human:<nome> que autoriza")
    g.add_argument("--expires", default=None, help="data ISO 8601")
    g.add_argument("--parent", default=None)
    r = sub.add_parser("revoke", help="Um humano revoga uma delegação (e as que dela derivam)")
    r.add_argument("dir", type=Path)
    r.add_argument("edge")
    r.add_argument("--by", required=True)
    args = ap.parse_args(argv)
    try:
        if args.cmd == "verify":
            problems = ReceiptLog(args.dir).verify()
            n = len(ReceiptLog(args.dir).records()) if not problems or ReceiptLog(args.dir).path.exists() else 0
            print(json.dumps({"ok": not problems, "receipts": n, "problems": problems}, ensure_ascii=False, indent=2))
            return 0 if not problems else 1
        pol = load_policy()
        graph = DelegationGraph(args.dir, max_depth=pol.max_depth)
        if args.cmd == "check":
            d = authorize(pol, graph, args.agent, args.capability)
            print(json.dumps({"effect": d.effect, "reason": d.reason, "chain": d.chain}, ensure_ascii=False))
            return 0 if d.allowed else 2
        if args.cmd == "delegate":
            e = graph.grant(from_=args.from_, to=args.to, scope=[s for s in args.scope.split(",") if s], granted_by=args.by,
                            expires_at=args.expires, parent=args.parent)
            print(json.dumps(e, ensure_ascii=False))
            return 0
        print(json.dumps(graph.revoke(args.edge, by=args.by), ensure_ascii=False))
        return 0
    except GovernanceError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
