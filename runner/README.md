# Plan-Execute Runner (lab)

Runner **mínimo** do setup: lê um `plan.yaml`, respeita `depends_on`, budget, `human_gate`, grava **L2** `events.jsonl` + `status.json`.

**Não** é o MCP de produção. **Não** chama LLMs por omissão (executor `stub`).

## Setup

```bash
cd runner
pip install -r requirements.txt
```

## Uso

```bash
# Dry-run: só mostra ordem dos steps
python -m plan_runner run ../docs/orchestration/marketing/templates/seo-article.plan.yaml --mode dry-run

# Stub: cria artefactos placeholder + events
python -m plan_runner run ../docs/orchestration/marketing/templates/seo-article.plan.yaml --mode stub --out ../pilots/run-seo-stub

# Retomar após HITL (ficheiro de decisão)
python -m plan_runner resume ../pilots/run-seo-stub --decision approve
```

## Modes

| Mode | Comportamento |
|------|----------------|
| `dry-run` | Valida plan, imprime ordem topológica, não escreve |
| `stub` | Executa steps na ordem; escreve placeholders nos `output_artifact`; para em `human_gate` |
| `external` | Emite pedido de execução em `pending_steps/`; espera ficheiro `result.json` (integração manual/outra IA) |

## Ligação à memória

| Camada | Runner |
|--------|--------|
| L0 | Não carrega (humano/processo à parte) |
| L1 | Estado do step em memória do processo |
| L2 | `events.jsonl` + `status.json` no `--out` |
| L3–L5 | Stub não carrega skills/RAG; `external` pode |

## Produção

Proibido apontar este runner a secrets ou write paths de `agent-network-mcp` sem decisão explícita.
