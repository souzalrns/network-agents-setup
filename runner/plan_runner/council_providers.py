"""IAs externas do conselho `structural` (M-011; decisões P-91 = A e P-92 = B).

O conselho interno (council_session.py) corre numa só IA (Gemini). Aqui um utilizador pode registar as IAs
que já tem (config/council-providers.yaml, opcional e vazio por omissão) e cada uma entrega a sua posição
por MCP, com a subscrição que já paga: custo zero, nenhuma chave no repo.

Este módulo tem duas partes:

1. Cadastro: carregar e validar `config/council-providers.yaml` e decidir o MODO do painel pelo número de IAs
   (0 = recusa, 1 = simples, ímpar >= 3 = completo, par = sem desempate).
2. Troca de ficheiros entre o motor e as IAs (as 3 ferramentas do MCP chamam estas funções):
   - `get_request`: a IA lê o pedido (sistema + utilizador) da sua posição;
   - `submit_position`: a IA entrega a posição (validada com as mesmas regras do conselho interno);
   - `session_status`: quem falta.
   As posições vão para `<sessão>/inbox/r<ronda>-<ia>.json`, um ficheiro por IA e por ronda, escrito uma só
   vez e de forma atómica. O motor (`CouncilSession.independent`) é quem as lê e as aplica ao estado, por isso
   as IAs nunca escrevem no `council.json`.
"""
from __future__ import annotations

import hmac
import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PROVIDERS_FILE = Path("config") / "council-providers.yaml"
INBOX = "inbox"
ID_RE = re.compile(r"^[a-z][a-z0-9_-]{1,30}$")
KEY_ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
MAX_PROVIDERS = 5
KINDS = ("mcp",)  # `api` (chave paga) fica para uma fase seguinte e só com aprovação (regra: nada pago)
MODES = ("none", "simple", "full", "even")
MEMBER_PREFIX = "ext:"


class ProviderError(RuntimeError):
    """Cadastro, pedido ou entrega inválidos."""


def _now() -> str:
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Cadastro
# ---------------------------------------------------------------------------

def load_providers(repo_root: Path = REPO_ROOT) -> list[dict[str, Any]]:
    """Lista de IAs registadas ([] se o ficheiro não existir ou estiver vazio). ValueError se ilegível."""
    path = repo_root / PROVIDERS_FILE
    if not path.is_file():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        raise ValueError(f"{PROVIDERS_FILE}: não é YAML legível ({e})") from e
    if data is None:
        return []
    if not isinstance(data, dict) or not isinstance(data.get("providers", []), list):
        raise ValueError(f"{PROVIDERS_FILE}: falta a lista `providers:` no topo")
    return list(data.get("providers") or [])


def validate_providers(repo_root: Path = REPO_ROOT) -> list[str]:
    """Erros do cadastro. [] = válido (ou vazio, que é o estado normal)."""
    try:
        providers = load_providers(repo_root)
    except ValueError as e:
        return [str(e)]
    errors: list[str] = []
    seen: set[str] = set()
    for i, p in enumerate(providers):
        where = f"providers[{i}]"
        if not isinstance(p, dict):
            errors.append(f"{where}: tem de ser um objecto")
            continue
        pid = p.get("id")
        if not isinstance(pid, str) or not ID_RE.match(pid):
            errors.append(f"{where}: `id` tem de ser minúsculas/números/-/_, 2 a 31 caracteres")
        elif pid in seen:
            errors.append(f"{where}: id `{pid}` repetido")
        else:
            seen.add(pid)
        kind = p.get("kind", "mcp")
        if kind not in KINDS:
            errors.append(f"{where}: kind `{kind}` não suportado (só {', '.join(KINDS)}; `api` é pago e fica para outra fase)")
        key_env = p.get("key_env")
        if key_env is not None and (not isinstance(key_env, str) or not KEY_ENV_RE.match(key_env)):
            errors.append(f"{where}: key_env tem de ser o NOME de uma variável de ambiente (ex.: COUNCIL_KEY_CLAUDE), nunca a chave")
        extra = set(p) - {"id", "kind", "key_env"}
        if extra:
            errors.append(f"{where}: campos desconhecidos {sorted(extra)} (a chave nunca vai neste ficheiro)")
    if len(providers) > MAX_PROVIDERS:
        errors.append(f"{PROVIDERS_FILE}: no máximo {MAX_PROVIDERS} IAs")
    return errors


def panel_mode(n: int) -> str:
    """none (0) | simple (1) | full (ímpar >= 3) | even (par >= 2: sem desempate)."""
    if n <= 0:
        return "none"
    if n == 1:
        return "simple"
    return "full" if n % 2 == 1 else "even"


def member_id(provider_id: str) -> str:
    return f"{MEMBER_PREFIX}{provider_id}"


def member_for(provider_id: str) -> dict[str, Any]:
    return {"id": member_id(provider_id), "role": "member", "provider": provider_id}


# ---------------------------------------------------------------------------
# Ficheiros da caixa de entrada
# ---------------------------------------------------------------------------

def submission_path(out_dir: Path, round_no: int, provider_id: str) -> Path:
    return Path(out_dir) / INBOX / f"r{int(round_no)}-{provider_id}.json"


def read_submission(out_dir: Path, round_no: int, provider_id: str) -> dict[str, Any] | None:
    """O JSON da posição entregue, ou None (não entregue ou ilegível: o motor trata como em falta)."""
    path = submission_path(out_dir, round_no, provider_id)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data.get("data") if isinstance(data, dict) and isinstance(data.get("data"), dict) else None


def _load_state(out_dir: Path) -> dict[str, Any]:
    path = Path(out_dir) / "council.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ProviderError(f"sem sessão de conselho em {out_dir} ({type(e).__name__})") from e


def _authenticate(repo_root: Path, provider_id: str, key: str | None) -> dict[str, Any]:
    """Verifica que a IA está registada e, se tem `key_env`, que a chave enviada é a dela (falha fechada)."""
    providers = {p.get("id"): p for p in load_providers(repo_root) if isinstance(p, dict)}
    prov = providers.get(provider_id)
    if prov is None:
        raise ProviderError(f"IA `{provider_id}` não está registada em {PROVIDERS_FILE}")
    key_env = prov.get("key_env")
    if key_env:
        expected = os.environ.get(key_env, "")
        if not expected:
            raise ProviderError(f"IA `{provider_id}` exige chave (`{key_env}`), mas a variável não está definida no servidor")
        if not key or not hmac.compare_digest(str(key).encode(), expected.encode()):
            raise ProviderError(f"chave inválida para a IA `{provider_id}`")
    return prov


def _member(state: dict[str, Any], provider_id: str) -> dict[str, Any]:
    for m in state["council"]["members"]:
        if m.get("provider") == provider_id:
            return m
    raise ProviderError(f"a IA `{provider_id}` não faz parte desta sessão")


def waiting_for(state: dict[str, Any], out_dir: Path) -> list[str]:
    """Ids das IAs desta ronda que ainda não entregaram."""
    rnd = state["round"]
    return [m["provider"] for m in state["council"]["members"]
            if m.get("provider") and not submission_path(out_dir, rnd, m["provider"]).is_file()]


# ---------------------------------------------------------------------------
# As 3 operações que o MCP expõe
# ---------------------------------------------------------------------------

def get_request(out_dir: Path, provider_id: str, *, key: str | None = None, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """O pedido para a posição desta IA na ronda actual (sem ver as posições das outras)."""
    from . import council_session as cs

    _authenticate(repo_root, provider_id, key)
    state = _load_state(out_dir)
    member = _member(state, provider_id)
    if state.get("status") != "awaiting_external":
        raise ProviderError(f"a sessão está em `{state.get('status')}`, não a espera de posições")
    if submission_path(out_dir, state["round"], provider_id).is_file():
        raise ProviderError(f"a IA `{provider_id}` já entregou a posição da ronda {state['round']}")
    system, user = cs.external_member_prompt(state, member)
    return {"session_id": state["session_id"], "round": state["round"], "stage": "independent",
            "instructions": system, "request": user, "answer_format": cs.POSITION_FORMAT}


def submit_position(out_dir: Path, provider_id: str, data: Any, *, key: str | None = None,
                    repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Entrega a posição. Validada com as regras do conselho interno; escrita uma só vez, de forma atómica."""
    from . import council_session as cs

    _authenticate(repo_root, provider_id, key)
    state = _load_state(out_dir)
    _member(state, provider_id)
    if state.get("status") != "awaiting_external":
        raise ProviderError(f"a sessão está em `{state.get('status')}`, não a espera de posições")
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            raise ProviderError(f"a posição não é JSON válido ({e.msg})") from e
    try:
        cs.normalize_position(data)
    except ValueError as e:
        raise ProviderError(f"posição inválida: {e}") from e
    path = submission_path(out_dir, state["round"], provider_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"provider": provider_id, "round": state["round"], "submitted_at": _now(), "data": data},
                         ensure_ascii=False, indent=2)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
        try:
            os.link(tmp, path)  # falha se já existir: uma entrega por IA e por ronda, sem corrida
        except FileExistsError as e:
            raise ProviderError(f"a IA `{provider_id}` já entregou a posição da ronda {state['round']}") from e
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    return {"ok": True, "round": state["round"], "waiting_for": waiting_for(state, out_dir)}


def session_status(out_dir: Path) -> dict[str, Any]:
    """Estado público da sessão (sem tema, contexto nem posições)."""
    state = _load_state(out_dir)
    return {"session_id": state["session_id"], "council": state["council_type"], "status": state["status"],
            "stage": state["stage"], "round": state["round"], "mode": (state.get("panel") or {}).get("mode"),
            "waiting_for": waiting_for(state, out_dir) if state["status"] == "awaiting_external" else []}
