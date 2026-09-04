# Policy pipeline (tools com policy)

Inspirado no pipeline `tools/pre-execute` → execute → `post-execute` do Harness e em waterfall de política Cordis.

## Pipeline conceptual (qualquer runtime)

```text
pedido de tool
  → 1. Tool na allowlist do passo/agente?     senão DENY
  → 2. Args validam schema?                 senão DENY
  → 3. Path/target fora de zona proibida?   senão DENY
  → 4. High-impact → human_gate?            senão WAIT
  → 5. EXECUTE
  → 6. Log (tool_call + tool_result)        P03
  → 7. Post-check opcional (tamanho, secret scan)
```

## Zonas proibidas (setup)

- Escrever em `agent-network-mcp` a partir do lab sem decisão explícita  
- Secrets em git  
- DNS / produção `.com.br` a partir de pilots de método  

## Mapeamento actual

| Etapa | Hoje no setup |
|-------|----------------|
| 1 Allowlist | `tools_allowed` no step |
| 2 Schema | JSON Schema dos outputs; args ainda informais |
| 3 Paths | constraints no `context` |
| 4 HITL | `human_gate`, `on_fail: human` |
| 5 Execute | manual / agente externo |
| 6 Log | ficheiros em `pilots/` |

## Fase runtime

Implementar 1–6 como função única `execute_verified_action(...)` no lab — alinhado à discussão C (registo) sem forçar B (tudo pelo motor) em produção até haver disciplina.
