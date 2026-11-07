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
5. Disciplina de veredicto (secção seguinte) — nenhum achado é "finding" sem ela.

## Disciplina de veredicto (incorporado 2026-11-07, origem: auditoria Cloudflare security-audit ao mesaflow-api)

Todo achado recebe um de três veredictos; só `confirmed` leva severidade:

- **`confirmed`** — path de código verificado por um segundo agente/execução independente da
  que o encontrou; resultado concreto demonstrado (não hipotético).
- **`needs_validation`** — hipótese bem fundamentada no código mas que depende de facto fora
  do código-fonte (config de deployment, dados de produção, teste em execução). Registar o
  facto exacto em falta e um plano seguro para o validar. **Nunca** atribuir severidade a um
  `needs_validation`.
- **`candidate`** — ainda não passou por verificação independente. Entra na tabela de Findings
  só identificado como candidato, nunca como achado final; não conta para `highest_severity`
  nem para `verdict` até ser promovido a `confirmed` ou `needs_validation`.

### Âncoras de severidade (só para `confirmed`)

- **critical** — actor não-autenticado ganha execução de código, acesso total à base de dados,
  ou controlo de qualquer conta.
- **high** — um controlo de segurança explícito é totalmente derrotado com consequência real:
  bypass de autenticação, leitura/escrita cross-tenant, execução de script persistente
  afectando outros utilizadores, execução de código autenticada, ou paragem remota não
  autenticada de um serviço partilhado.
- **medium** — violação real de fronteira com impacto limitado, pré-condições pouco comuns, ou
  consequência confinada a um conjunto estreito de recursos.
- **low** — divulgação de internals não secretos, ou efeito que exige esforço sustentado para
  ganho mínimo.
- **informational** — observação confirmada mas de impacto mínimo, útil como pré-requisito
  dentro de um achado maior.

Discriminador high/medium: o resultado demonstrado derrota totalmente um controlo explícito
numa acção com consequência real, ou só o enfraquece? Se não conseguires dizer o dano concreto,
a severidade é mais baixa do que parece.

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

| ID | Verdict | Severity | Title | OWASP (LLM/API) | ATLAS (if any) | Evidence | Recommendation |
|----|---------|----------|-------|-------------------|-----------------|----------|-----------------|
| F1 | confirmed\|needs_validation\|candidate | (só se confirmed) | | | | | |

## Needs validation / candidates (sem severidade)
- Listar aqui todo item `needs_validation` ou `candidate`, com o facto exacto em falta ou a
  verificação independente pendente.

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

## JSON opcional (só em rodapé)

O passo escreve **um** artefacto (`output_artifact`); não há ficheiro irmão. Se quiseres o resumo máquina-legível, põe-no no fim do markdown, num bloco ```json.

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
- [ ] Todo item da tabela tem veredicto (confirmed/needs_validation/candidate)
- [ ] Nenhum `needs_validation` ou `candidate` com severidade atribuída
- [ ] `highest_severity` e `verdict` calculados só a partir de itens `confirmed`
- [ ] next_steps concretos
- [ ] Nenhuma invocação de scanner ou ataque
