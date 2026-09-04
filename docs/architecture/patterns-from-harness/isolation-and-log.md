# Isolamento de sub-fluxos + model-visible log

## Isolamento

| Princípio | Prática |
|-----------|--------|
| Contexto mínimo | Passo recebe só `inputs` declarados |
| Artefacto como fronteira | Output em path fixo; não “memória mental” partilhada |
| Fresh por omissão | Novo passo ≠ dump completo do pai |
| Fork explícito | Só se o plan disser `inputs` com histórico alargado |

Anti-padrão: um único context window com todos os agentes a falar peer-to-peer.

## Model-visible → log

| Princípio | Prática |
|-----------|--------|
| Se o modelo viu ou produziu e isso importa | Tem de existir no disco ou no event log |
| Replay | Dado plan + artefactos, reconstituir a história |
| Done | `done_when` + existência de artefactos + verify |

### Eventos mínimos (fase 3)

```text
plan_created | plan_approved
step_started {id, action}
tool_called {step, tool, args_digest}
tool_finished {step, tool, ok}
step_finished {id, artifact}
verify_finished {pass}
human_gate {reason, status}
plan_aborted | plan_done
```

Até haver runtime: a pasta `pilots/<id>/` *é* o log.
