from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Step
from .skills import (
    activate_for_task,
    materialize_activation,
    read_text_if_exists,
    repo_root_from_out,
)


class StepResult:
    def __init__(
        self,
        ok: bool,
        detail: str = "",
        artifact: str | None = None,
        worker_error: str | None = None,
        budget: dict[str, Any] | None = None,
    ):
        self.ok = ok
        self.detail = detail
        self.artifact = artifact
        # So com worker inline: porque e que o passo continua em waiting_external.
        self.worker_error = worker_error
        # detail == "budget_exceeded": {"spent": N, "cap": M} (docs/ops/BUDGET.md)
        self.budget = budget


def _read_json(path: Path) -> Any:
    """PowerShell Set-Content -Encoding utf8 often writes BOM; accept utf-8-sig."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_stub_artifact(out_root: Path, step: Step) -> str | None:
    if not step.output_artifact:
        return None
    path = out_root / step.output_artifact
    path.parent.mkdir(parents=True, exist_ok=True)
    body: dict[str, Any] = {
        "_stub": True,
        "step_id": step.id,
        "action": step.action,
        "tools_allowed": step.tools_allowed,
        "message": "Placeholder artifact from plan_runner stub mode. Replace with real worker output.",
    }
    if step.output_schema:
        body["output_schema"] = step.output_schema
    if path.suffix.lower() in {".md", ".txt"}:
        path.write_text(
            f"# Stub: {step.id} ({step.action})\n\n"
            f"tools_allowed: {step.tools_allowed}\n\n"
            f"Replace with real worker output.\n",
            encoding="utf-8",
        )
    else:
        path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return str(path.relative_to(out_root))


def execute_stub(out_root: Path, step: Step) -> StepResult:
    if step.human_gate:
        return StepResult(ok=True, detail="awaiting_human_gate", artifact=None)
    art = _write_stub_artifact(out_root, step)
    return StepResult(ok=True, detail="stub_ok", artifact=art)


def execute_external_request(out_root: Path, step: Step, worker: Any = None) -> StepResult:
    """Write a pending request including agent+skill paths; wait for result.json.

    `worker` (AU-23, external_worker.GeminiWorker): se vier, executa o passo
    logo a seguir a escrever o pedido, em vez de deixar o run em
    waiting_external. Sem worker (omissao), o contrato e o de sempre.
    """
    pending = out_root / "pending_steps" / step.id
    pending.mkdir(parents=True, exist_ok=True)

    repo_root = repo_root_from_out(out_root)
    # Worker chama activate_for_task antes de executar: resolve skill/agent,
    # aplica SEC-1.3 (allow-list de scripts) e, se should_search_external,
    # consulta npx skills find / SkillsCat. Resultado entra no request.json
    # e no prompt (skill_activation.json + SKILL.md/AGENT.md).
    activation = activate_for_task(repo_root, step)
    skill_path = activation.skill_path
    agent_path = activation.agent_path

    req: dict[str, Any] = {
        "step_id": step.id,
        "action": step.action,
        "tools_allowed": step.tools_allowed,
        "inputs": step.inputs,
        "output_artifact": step.output_artifact,
        "output_schema": step.output_schema,
        "agent_path": activation.agent_rel,
        "skill_path": activation.skill_rel,
        "instruction": (
            "Load agent_path + skill_path from the repo. "
            "Execute the skill. Respect allowed_scripts (SEC-1.3); do not run blocked_scripts. "
            "Write result.json: "
            "{ok: bool, detail?: str, artifact_content?: str|object}. "
            "Or write the output_artifact file and result.json {ok: true}."
        ),
    }
    req.update(activation.to_request_fields())

    # S30: working memory do cliente (out/client_memory.md, escrito uma vez
    # no arranque do run por engine.py::_load_client_memory) -- aditivo,
    # so aparece se o plan.yaml tiver `client_id` e o MEMORY.md existir.
    client_memory_path = out_root / "client_memory.md"
    if client_memory_path.is_file():
        req["client_memory_path"] = "client_memory.md"

    (pending / "request.json").write_text(
        json.dumps(req, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    materialize_activation(pending, activation)
    if client_memory_path.is_file():
        (pending / "CLIENT_MEMORY.md").write_text(
            client_memory_path.read_text(encoding="utf-8"), encoding="utf-8"
        )

    result_path = pending / "result.json"
    if not result_path.exists() and worker is not None:
        from .external_worker import BudgetExceeded, WorkerError

        try:
            worker.process(out_root, step.id)
        except BudgetExceeded as e:
            # Tecto de tokens (ou de custo, D6) atingido: o passo nao correu; o motor pausa o run (paused_budget).
            budget = {"spent": e.spent, "cap": e.cap}
            if e.unit == "usd":
                budget["unit"] = "usd"
            return StepResult(ok=False, detail="budget_exceeded", worker_error=str(e), budget=budget)
        except WorkerError as e:
            # Sem result.json: o passo fica em waiting_external e o resume tenta outra vez.
            return StepResult(ok=False, detail="waiting_external", worker_error=str(e))
    if not result_path.exists():
        return StepResult(ok=False, detail="waiting_external")
    data = _read_json(result_path)
    if not data.get("ok"):
        return StepResult(ok=False, detail=str(data.get("detail") or "external_failed"))
    if step.output_artifact and isinstance(data.get("artifact_summary"), str) and data["artifact_summary"].strip():
        # B1-bis: resumo estruturado para os passos seguintes (context_policy.summary_path)
        from .context_policy import summary_path

        sp = summary_path(out_root, step.output_artifact)
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_text(data["artifact_summary"], encoding="utf-8")
    if step.output_artifact and data.get("artifact_content") is not None:
        path = out_root / step.output_artifact
        path.parent.mkdir(parents=True, exist_ok=True)
        content = data["artifact_content"]
        if isinstance(content, (dict, list)):
            path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        else:
            path.write_text(str(content), encoding="utf-8")
        return StepResult(ok=True, detail="external_ok", artifact=step.output_artifact)
    if step.output_artifact and (out_root / step.output_artifact).exists():
        return StepResult(ok=True, detail="external_ok", artifact=step.output_artifact)
    return StepResult(ok=True, detail="external_ok_no_artifact")
