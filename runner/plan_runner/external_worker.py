"""Worker do modo `external` (AU-23, PLANO-DE-ACAO #6): executa um passo com o Gemini.

Fecha o buraco que deixava o runner parado em `waiting_external`. Para cada
passo pendente:

1. le `pending_steps/<id>/request.json` (escrito por executor.py);
2. le `AGENT.md` e `SKILL.md` (copiados para o mesmo directorio pelo executor),
   a directiva de grounding (agents/_shared) e o contexto opcional
   (`knowledge_context.md`, `CLIENT_MEMORY.md`, artefactos de input);
3. chama o Gemini (`generateContent`, gemini-flash-lite-latest por omissao);
4. escreve `result.json` no formato que executor.py ja le
   (`{ok, detail, artifact_content}`);
5. regista os tokens no ledger J6 (`token_usage`): sempre em
   `<run>/token_usage.jsonl`; no Supabase so se SUPABASE_URL e
   SUPABASE_SERVICE_ROLE_KEY estiverem definidas (mesmo contrato e mesma
   regra do servidor MCP: gravar nunca faz falhar o passo);
6. respeita o HITL: nunca executa um passo com `human_gate` nem avanca um
   run em `paused_human_gate` -- a decisao e humana (hitl-*.jsonl, resume).

Falha do Gemini (rede, HTTP, resposta vazia, JSON invalido) NAO escreve
`result.json`: deixa `worker_error.json` com o motivo e o passo continua em
`waiting_external`, por isso basta `resume` para tentar outra vez.

Sem dependencias novas: httpx (ja usado por embedder.py), PyYAML.

CLI (para runs ja parados em waiting_external, de qualquer engine):
    python -m plan_runner.external_worker <run_dir> [--resume]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import yaml

from .skills import _frontmatter, repo_root_from_out

DEFAULT_MODEL = "gemini-flash-lite-latest"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MAX_OUTPUT_TOKENS = 4096
INPUT_MAX_CHARS = 20000  # por ficheiro de input/contexto
LEDGER_FILE = "token_usage.jsonl"
ERROR_FILE = "worker_error.json"
TOKEN_TABLE = "token_usage"

# run_id do runner ("run_ab12cd34ef") -> uuid estavel para a coluna uuid do
# token_usage. Mesmo run => mesmo uuid, por isso os passos agrupam por run.
_RUN_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "network-agents-setup/plan_runner")

# Gemini: (url, headers, body, timeout) -> (status_code, json). Injectavel nos testes.
Transport = Callable[[str, dict[str, str], dict[str, Any], float], tuple[int, dict[str, Any]]]
# Ledger remoto: (row) -> None. Injectavel nos testes; None = desligado.
RemoteSink = Callable[[dict[str, Any]], None]


class WorkerError(RuntimeError):
    """O passo nao foi executado (Gemini falhou ou a resposta nao serve)."""


class HumanGateBlocked(WorkerError):
    """O passo ou o run esperam uma decisao humana; o worker nao avanca."""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _clip(text: str, limit: int = INPUT_MAX_CHARS) -> str:
    return text if len(text) <= limit else text[:limit] + f"\n\n[... cortado: {len(text) - limit} caracteres]"


def ledger_run_uuid(run_id: str | None) -> str | None:
    return str(uuid.uuid5(_RUN_NAMESPACE, run_id)) if run_id else None


def build_usage_row(
    *, run_id: str | None, agent_id: str | None, model: str, response: dict | None, call_kind: str = "agent"
) -> dict[str, Any]:
    """Linha de token_usage -- espelho de buildUsageRow (agent-network-mcp lib/tokenLedger.js).

    So colunas da tabela (memory/token_usage.sql no agent-network-mcp); o
    PostgREST recusa colunas desconhecidas.
    """
    usage = (response or {}).get("usageMetadata")
    has_usage = isinstance(usage, dict)

    def _int(key: str) -> int | None:
        v = usage.get(key) if has_usage else None
        return v if isinstance(v, int) and not isinstance(v, bool) else None

    return {
        "run_id": ledger_run_uuid(run_id),
        "agent_id": agent_id,
        "call_kind": call_kind,  # agent | router | embed_query (check da tabela)
        "model": model,
        "model_version": (response or {}).get("modelVersion"),
        "tokens_in": _int("promptTokenCount"),
        "tokens_out": _int("candidatesTokenCount"),
        "tokens_total": _int("totalTokenCount"),
        "status": "ok" if has_usage else "missing_usage",
        "raw_usage": usage if has_usage else None,
        "service_tier": usage.get("serviceTier") if has_usage else None,
        "response_id": (response or {}).get("responseId"),
    }


def supabase_sink_from_env(timeout: float = 10.0) -> RemoteSink | None:
    """POST no PostgREST com o service_role, como o MCP. None se faltar config."""
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not key:
        return None

    def sink(row: dict[str, Any]) -> None:
        r = httpx.post(
            f"{url}/rest/v1/{TOKEN_TABLE}",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json=row,
            timeout=timeout,
        )
        if r.status_code >= 300:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")

    return sink


def record_token_usage(
    out_root: Path,
    row: dict[str, Any],
    *,
    step_id: str,
    run_id: str | None,
    remote: RemoteSink | None,
) -> dict[str, Any]:
    """Grava a linha no jsonl local e (se houver) no Supabase. Nunca lanca.

    O jsonl leva tambem o run_id original do runner e o step_id, que a tabela
    nao tem; o `remote` diz o que aconteceu do lado do Supabase.
    """
    entry = {**row, "recorded_at": _now(), "runner_run_id": run_id, "step_id": step_id}
    if remote is None:
        entry["remote"] = "skipped"
    else:
        try:
            remote(row)
            entry["remote"] = "ok"
        except Exception as e:  # noqa: BLE001 -- o ledger nunca parte o passo
            entry["remote"] = f"error: {str(e)[:200]}"
            print(f"[token_usage] falha ao gravar: {str(e)[:200]}", file=sys.stderr)
    try:
        with (out_root / LEDGER_FILE).open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"[token_usage] falha no jsonl local: {e}", file=sys.stderr)
    return entry


def gemini_api_key(explicit: str | None = None) -> str:
    key = (explicit or os.environ.get("GEMINI_API_KEY", "")).strip()
    if not key:
        raise WorkerError("GEMINI_API_KEY em falta no ambiente (chave gratuita: aistudio.google.com/apikey)")
    return key


def gemini_generate(
    system: str,
    user: str,
    *,
    model: str,
    api_key: str | None = None,
    wants_json: bool = False,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    timeout: float = 60.0,
    transport: Transport | None = None,
) -> dict[str, Any]:
    """Uma chamada generateContent. Devolve o JSON da resposta; lanca WorkerError.

    Partilhada pelo worker e pelo router (plan_runner/router.py).
    """
    generation: dict[str, Any] = {"maxOutputTokens": max_output_tokens}
    if wants_json:
        generation["responseMimeType"] = "application/json"
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": generation,
    }
    send = transport or httpx_transport
    try:
        # Chave no header (nao na query): nunca aparece em URLs de erro nem em logs.
        code, response = send(GEMINI_URL.format(model=model), {"x-goog-api-key": gemini_api_key(api_key)}, body, timeout)
    except httpx.HTTPError as e:
        raise WorkerError(f"gemini: erro de rede: {type(e).__name__}") from e
    if code != 200:
        msg = ((response.get("error") or {}).get("message") or "")[:300]
        raise WorkerError(f"gemini HTTP {code}: {msg}")
    return response


def httpx_transport(url: str, headers: dict[str, str], body: dict[str, Any], timeout: float) -> tuple[int, dict[str, Any]]:
    r = httpx.post(url, headers=headers, json=body, timeout=timeout)
    try:
        data = r.json()
    except ValueError:
        data = {"error": {"message": r.text[:300]}}
    return r.status_code, data if isinstance(data, dict) else {"data": data}


def _load_plan_raw(out_root: Path) -> dict[str, Any]:
    p = out_root / "plan.yaml"
    if not p.is_file():
        return {}
    data = yaml.safe_load(p.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def _plan_step(plan_raw: dict[str, Any], step_id: str) -> dict[str, Any] | None:
    for s in plan_raw.get("steps") or []:
        if isinstance(s, dict) and str(s.get("id")) == step_id:
            return s
    return None


def check_hitl(out_root: Path, step_id: str) -> None:
    """Lanca HumanGateBlocked se o passo tem gate ou o run espera decisao humana."""
    status_path = out_root / "status.json"
    if status_path.is_file():
        try:
            status = _read_json(status_path)
        except (json.JSONDecodeError, UnicodeDecodeError):
            status = {}
        if status.get("state") == "paused_human_gate":
            raise HumanGateBlocked(
                f"run em paused_human_gate no passo {status.get('paused_at_step')!r}: "
                "decide primeiro (hitl-decisions.jsonl ou `plan_runner resume --decision ...`)"
            )
    step = _plan_step(_load_plan_raw(out_root), step_id)
    if step is not None and step.get("human_gate"):
        raise HumanGateBlocked(f"passo {step_id!r} tem human_gate: a decisao e humana, o worker nao o executa")


def _section(title: str, body: str) -> str:
    return f"## {title}\n\n{body.strip()}\n"


def build_prompt(out_root: Path, pending: Path, request: dict[str, Any]) -> tuple[str, str, bool]:
    """(system, user, quer_json). Tudo o que o modelo ve vem de ficheiros do run/repo."""
    repo_root = repo_root_from_out(out_root)
    system_parts: list[str] = []
    for name, title in (("AGENT.md", "Agente"), ("SKILL.md", "Skill")):
        p = pending / name
        if p.is_file():
            system_parts.append(_section(title, p.read_text(encoding="utf-8")))
    grounding = repo_root / "agents" / "_shared" / "grounding.directive.md"
    if grounding.is_file():
        system_parts.append(_section("Grounding (obrigatorio)", grounding.read_text(encoding="utf-8")))

    artifact = request.get("output_artifact") or ""
    wants_json = artifact.lower().endswith(".json")
    schema = request.get("output_schema")
    fmt = (
        "JSON valido (um unico objecto), sem texto antes nem depois"
        + (f", com a estrutura de `{schema}` descrita na skill" if schema else "")
        if wants_json
        else "Markdown"
    )
    system_parts.append(
        _section(
            "Saida",
            f"Devolve SO o conteudo do artefacto `{artifact or '(sem ficheiro)'}`, em {fmt}. "
            "Sem preambulos nem comentarios sobre a tarefa. Nao tens tools neste passo: "
            "usa apenas o contexto desta mensagem e marca o que falta como lacuna.",
        )
    )

    plan_raw = _load_plan_raw(out_root)
    user_parts = [
        _section(
            "Passo",
            f"- plano: {plan_raw.get('id', '?')}\n- passo: {request.get('step_id')}\n"
            f"- action: {request.get('action')}\n- artefacto: {artifact or '(nenhum)'}",
        )
    ]
    for key, title in (("objective", "Objectivo do plano"), ("audience", "Audiencia")):
        if plan_raw.get(key):
            user_parts.append(_section(title, str(plan_raw[key])))
    # `task:` opcional no passo (o router escreve-a em cada passo de um plano gerado).
    task = (_plan_step(plan_raw, str(request.get("step_id"))) or {}).get("task")
    if task:
        user_parts.append(_section("Tarefa deste passo", str(task)))

    # Inputs declarados; sem eles, os artefactos dos passos de que este depende.
    inputs = list(request.get("inputs") or [])
    if not inputs:
        step = _plan_step(plan_raw, str(request.get("step_id"))) or {}
        for dep in step.get("depends_on") or []:
            dep_step = _plan_step(plan_raw, str(dep)) or {}
            if dep_step.get("output_artifact"):
                inputs.append(str(dep_step["output_artifact"]))
    for rel in inputs:
        p = (out_root / rel).resolve()
        if p.is_relative_to(out_root.resolve()) and p.is_file():
            user_parts.append(_section(f"Input: {rel}", _clip(p.read_text(encoding="utf-8"))))
        else:
            user_parts.append(_section(f"Input: {rel}", "(ficheiro em falta -- trata como lacuna)"))

    for name, title in (("knowledge_context.md", "Conhecimento recuperado (L5)"), ("CLIENT_MEMORY.md", "Memoria do cliente")):
        p = pending / name
        if p.is_file():
            user_parts.append(_section(title, _clip(p.read_text(encoding="utf-8"))))

    return "\n".join(system_parts), "\n".join(user_parts), wants_json


def _response_text(response: dict[str, Any]) -> tuple[str, str | None]:
    candidates = response.get("candidates") or []
    if not candidates:
        return "", None
    first = candidates[0] if isinstance(candidates[0], dict) else {}
    parts = (first.get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    return text, first.get("finishReason")


def _parse_json_output(text: str) -> Any:
    t = text.strip()
    if t.startswith("```"):  # alguns modelos embrulham em ```json mesmo com responseMimeType
        t = t.split("\n", 1)[1] if "\n" in t else ""
        t = t.rsplit("```", 1)[0]
    return json.loads(t)


class GeminiWorker:
    """Executa um passo pendente com o Gemini e escreve result.json."""

    name = "gemini"

    def __init__(
        self,
        *,
        model: str | None = None,
        api_key: str | None = None,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
        timeout: float = 60.0,
        transport: Transport | None = None,
        remote_ledger: RemoteSink | None | bool = True,
    ):
        self.model = model or os.environ.get("AGENT_MODEL") or DEFAULT_MODEL
        self._api_key = api_key
        self.max_output_tokens = max_output_tokens
        self.timeout = timeout
        self.transport = transport or httpx_transport
        # True = Supabase se o ambiente o tiver; None/False = so jsonl local.
        self.remote_ledger = supabase_sink_from_env() if remote_ledger is True else (remote_ledger or None)

    def process(self, out_root: Path, step_id: str, *, run_id: str | None = None) -> dict[str, Any]:
        """Executa o passo. Devolve o result.json escrito; lanca WorkerError/HumanGateBlocked."""
        pending = out_root / "pending_steps" / step_id
        result_path = pending / "result.json"
        if result_path.exists():
            return _read_json(result_path)  # idempotente: o passo ja tem resultado
        check_hitl(out_root, step_id)
        request_path = pending / "request.json"
        if not request_path.is_file():
            raise WorkerError(f"sem request.json em {pending}")
        request = _read_json(request_path)
        if run_id is None:
            status_path = out_root / "status.json"
            run_id = _read_json(status_path).get("run_id") if status_path.is_file() else None

        try:
            return self._run(out_root, pending, request, step_id, run_id)
        except WorkerError as e:
            (pending / ERROR_FILE).write_text(
                json.dumps({"at": _now(), "model": self.model, "error": str(e)}, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            raise

    def _run(self, out_root: Path, pending: Path, request: dict, step_id: str, run_id: str | None) -> dict[str, Any]:
        system, user, wants_json = build_prompt(out_root, pending, request)
        response = gemini_generate(
            system,
            user,
            model=self.model,
            api_key=self._api_key,
            wants_json=wants_json,
            max_output_tokens=self.max_output_tokens,
            timeout=self.timeout,
            transport=self.transport,
        )

        agent_id = _frontmatter(pending / "AGENT.md").get("id") or request.get("action")
        row = build_usage_row(run_id=run_id, agent_id=agent_id, model=self.model, response=response)
        ledger = record_token_usage(out_root, row, step_id=step_id, run_id=run_id, remote=self.remote_ledger)

        text, finish = _response_text(response)
        if not text.strip():
            raise WorkerError(f"gemini: resposta vazia (finishReason={finish})")
        content: Any = text
        if wants_json:
            try:
                content = _parse_json_output(text)
            except json.JSONDecodeError as e:
                raise WorkerError(f"gemini: JSON invalido para {request.get('output_artifact')}: {e.msg}") from e

        result = {
            "ok": True,
            "detail": f"gemini:{row['model_version'] or self.model}",
            "artifact_content": content,
            "meta": {
                "worker": self.name,
                "model": self.model,
                "model_version": row["model_version"],
                "finish_reason": finish,
                "tokens_in": row["tokens_in"],
                "tokens_out": row["tokens_out"],
                "tokens_total": row["tokens_total"],
                "response_id": row["response_id"],
                "ledger_remote": ledger["remote"],
            },
        }
        (pending / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (pending / ERROR_FILE).unlink(missing_ok=True)
        return result


WORKERS = ("gemini",)


def make_worker(name: str | None) -> GeminiWorker | None:
    if name in (None, "", "none"):
        return None
    if name == "gemini":
        return GeminiWorker()
    raise ValueError(f"worker desconhecido {name!r} (opcoes: none, {', '.join(WORKERS)})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="plan_runner.external_worker",
        description="Executa com o Gemini o passo em waiting_external de um run (qualquer engine).",
    )
    parser.add_argument("out", type=Path, help="Directorio do run (com status.json)")
    parser.add_argument("--resume", action="store_true", help="Depois do passo, retoma o run com o worker inline (engine native)")
    args = parser.parse_args(argv)

    out = args.out.resolve()
    status_path = out / "status.json"
    if not status_path.is_file():
        print(f"error: sem status.json em {out}", file=sys.stderr)
        return 1
    status = _read_json(status_path)
    worker = GeminiWorker()
    try:
        if status.get("state") == "paused_human_gate":
            check_hitl(out, str(status.get("paused_at_step")))
        if status.get("state") != "waiting_external":
            print(f"error: run em {status.get('state')!r}, nao em waiting_external", file=sys.stderr)
            return 1
        step_id = str(status.get("paused_at_step"))
        result = worker.process(out, step_id, run_id=status.get("run_id"))
    except HumanGateBlocked as e:
        print(f"hitl: {e}", file=sys.stderr)
        return 2
    except WorkerError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    summary: dict[str, Any] = {"step_id": step_id, "detail": result.get("detail"), "meta": result.get("meta")}
    if args.resume:
        if str(status.get("engine", "")).startswith("langgraph"):
            summary["resume"] = "engine langgraph: corre `python -m plan_runner resume <run>` para continuar"
        else:
            from .engine import resume_run

            summary["status"] = resume_run(out, decision="approve", worker="gemini")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
