# Loop plan→improve e gates

## Loop ECC

| Fase | Significado | Nosso |
|------|-------------|--------|
| plan | Artefacto editável **antes** de implementar | step `plan` / Spec Kit / plan.yaml |
| test | RED antes de código (TDD) | step testes ou done_when |
| implement | Worker isolado | action implement_task |
| review | **Fresh context** — outro agent/step | code_review / critic |
| verify | Checks determinísticos + evidência | verify_plan, CI, hooks |
| remember | Distilar sessão → memória/skill | L2 summary → L4/L3 candidate |
| improve | Promover padrões que funcionaram | skill promote gate |

## Template de plan (engenharia genérico)

```yaml
steps:
  - id: plan
    action: tech_plan
  - id: test_red
    action: write_failing_tests
    depends_on: [plan]
  - id: implement
    action: implement_task
    depends_on: [test_red]
  - id: review
    action: code_review
    depends_on: [implement]
    # ideal: modelo/contexto diferente do implement
  - id: verify
    action: run_tests_and_lint
    depends_on: [review]
  - id: remember
    action: distill_session
    depends_on: [verify]
    human_gate: { kind: output_review, allow: [approve, reject] }
```

## Gates fora do modelo (hooks)

ECC: PreToolUse / PostToolUse / Stop — enforcement **não** depende de o LLM “lembrar”.

Nosso equivalente:

- runner: budget, tools_allowed, schema check  
- CI: lint/test  
- futuro: hook antes de `execute_verified_action`  

Profiles: `minimal` | `standard` | `strict` (desligar hooks perigosos em lab).
