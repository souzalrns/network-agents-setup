"""AU-22 / P-10 = A: verificacao do `done_when` no fim do run.

O runner reconhece 2 formas (as unicas que os planos usam e que se verificam
sem interpretar texto livre):

- `<caminho> exists`: o ficheiro existe dentro do directorio do run
  (ex.: `artifacts/04-critic.json exists`);
- `human_gate_resolved on <passo>`: ha um evento `human_gate_resolved` desse
  passo no `events.jsonl` do run.

Se alguma falhar, o run termina em `failed` com `detail = "done_when"` e a
lista em `status["done_when_failed"]`. Uma condicao noutra forma nao e
interpretavel: gera o evento `done_when_unverifiable` e NAO falha o run
(decisao do maestro, 2026-10-03; reescrever essas condicoes e o AU-22b).
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from doneproof import evaluate as _evaluate

from .events import EventLog

# O motor de classificacao (passed/failed/unverifiable por evidencia) vem do pacote
# publicado `doneproof` (PyPI, extraido de oss/doneproof). Este modulo mantem o nome
# `done_when` (o campo `done_when:` do plano), liga o seam `gate_resolved` ao
# events.jsonl do run e traduz as `reason` para PT, que fazem parte do contrato de
# eventos do runner (asseridas nos testes). Devolvido em 2026-10-13 (flywheel,
# docs/initiatives/REPO-EVAL-PLAYBOOK.md).
GateResolved = Callable[[str], bool]

_REASON_PT = {
    "path outside the run directory": "caminho fora do directorio do run",
    "file missing": "ficheiro em falta",
    "gate not resolved": "gate nao resolvido",
}


def evaluate(out: Path, conditions: list[str], log: EventLog, run_id: str) -> dict[str, list[Any]]:
    """Classifica cada condicao em passed, failed ou unverifiable.

    passed: [{kind, target}] (kind = file_exists | gate_resolved); failed: o mesmo
    mais {condition, reason}; unverifiable: o texto original. As que passam vao
    estruturadas, sem o texto original, para nao se confundirem com o evento
    `human_gate_resolved` em quem procura no events.jsonl por texto. Liga o seam
    `gate_resolved` do `doneproof.evaluate` ao events.jsonl deste run.
    """
    r = _evaluate(
        out,
        conditions,
        lambda step: log.has_event("human_gate_resolved", run_id, step_id=step),
    )
    for item in r["failed"]:
        item["reason"] = _REASON_PT.get(item["reason"], item["reason"])
    return r


def check(out: Path, done_when: list[str], log: EventLog, run_id: str, status: dict[str, Any]) -> bool:
    """Verifica o done_when antes de o run passar a `done`.

    Devolve True se o run pode terminar em `done`. Com alguma condicao falhada,
    poe o status em `failed` (detail `done_when`) e devolve False; quem chama
    grava o status e nao emite `plan_done`.
    """
    if not done_when:
        return True
    r = evaluate(out, done_when, log, run_id)
    for cond in r["unverifiable"]:
        log.append("done_when_unverifiable", run_id, {"condition": cond, "item": "AU-22b"})
    log.append("done_when_checked", run_id, r)
    if not r["failed"]:
        return True
    log.append("done_when_failed", run_id, {"failed": r["failed"]})
    status["state"] = "failed"
    status["detail"] = "done_when"
    status["done_when_failed"] = r["failed"]
    status["current_step"] = None
    return False
