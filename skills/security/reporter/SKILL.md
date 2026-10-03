---
name: security-report
action: security_report
version: 1
role: security_technique
priority: P1
description: >
  Consolida triage + audit defensivo num relatório estruturado (summary,
  findings mapeados, next_steps). Sem re-scan e sem patches.
requires: []
---

# Skill — security-report

## Trigger

- Após `security_audit` (e triage, se existir) no mesmo plan.

## Regras curtas

1. Só factos presentes nos inputs.
2. Não suavizar CRITICAL/HIGH.
3. Zero findings = relatório limpo válido.
4. Saída principal: markdown no `output_artifact`; opcional bloco JSON final.

## Template markdown

```markdown
# Security report

## Executive summary
- Verdict: pass | pass_with_findings | fail
- Highest severity: …
- Needs human decision: yes | no

## Scope
- From triage: surfaces, severity, out_of_scope
- Audit coverage notes: …

## Findings

| ID | Severity | Title | OWASP LLM | ATLAS (if any) | Evidence | Recommendation |
|----|----------|-------|-----------|-----------------|----------|-----------------|
| F1 | | | | | | |

## Mapped controls
- OWASP LLM 2026: (cobertos / N/A justificados)
- NIST AI RMF: Govern | Map | Measure | Manage (notas curtas)
- MAESTRO layers touched: …

## Next steps
1. … (agente ou humano)
2. …

## Explicit non-actions
- No active attack performed
- No production changes by security agents
```

## JSON opcional (rodapé ou ficheiro irmão)

```json
{
  "verdict": "pass|pass_with_findings|fail",
  "highest_severity": "critical|high|medium|low|info|none",
  "findings_count": 0,
  "needs_human_decision": true,
  "finding_ids": []
}
```

## Done when

- [ ] Summary + tabela (mesmo que vazia)
- [ ] next_steps concretos
- [ ] Nenhuma invocação de scanner ou ataque
