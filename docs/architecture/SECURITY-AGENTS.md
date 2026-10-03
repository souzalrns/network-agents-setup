# Security agents — pipeline defensivo + Capability First

## Pipeline (área `security`)

```text
security.triage → meta.security-auditor → security.reporter → HITL
```

| Agente | id | Função |
|--------|-----|--------|
| Triage | `security.triage` | Severidade, surfaces, `needs_full_audit` |
| Auditor | `meta.security-auditor` | Audit defensivo (OWASP LLM 2026, etc.) |
| Reporter | `security.reporter` | Relatório consolidado |

Registo: `config/areas.yaml` → área `security` (`hitl: required`, `max_tokens: 40000`).  
Cyber ≡ security (sem área separada).

## Capability First (não 8 agentes)

As capabilities de cyber security vivem em `config/security-capabilities.yaml`.  
**Não** se cria um agente permanente por capability. O `plan_runner` executa steps com `action` genérica; skills e profiles materializam o comportamento.

| Capability | Executor v1 | Nível max |
|------------|-------------|-----------|
| triage | `security.triage` | READ |
| defensive_audit | `meta.security-auditor` | READ (+ orienta PREPARE) |
| security_report | `security.reporter` | READ / PREPARE (texto) |
| secrets_hygiene | auditor + CI (gitleaks) | READ |
| supply_chain | auditor + OSV/Trivy guidance | READ |
| mcp_surface | auditor (skill security-audit) | READ |
| hardening_recommend | auditor / reporter → engenharia | PREPARE only |
| agent_redteam_lab | CI/lab (PyRIT/DeepTeam) — **fora do runner prod** | lab only |

## READ / PREPARE / ACT

| Nível | Agentes security |
|-------|------------------|
| READ | Sim |
| PREPARE | Sim (relatório, checklist, plano de patch) |
| ACT (write prod, exploit, rotate live) | **Não** — só engenharia/ops após HITL |

## O que não fazer

- Ataque activo / pentest ofensivo no runner de produção
- Escrever em produção a partir destes agentes
- Aceitar risco CRITICAL/HIGH sem HITL
- Tratar `security_auditor` como meta-agente de deliberação (é C3 domínio)
- Criar 8 agentes permanentes para as 8 capabilities

## Conselho (deliberação)

`config/councils.yaml` → painel `security`: chairman `meta.chairman`, member required `meta.security-auditor`.  
Para decisões estruturais (threat model, política de segredos), não para cada triage diário.

## Planos

Exemplo: `docs/orchestration/security/templates/examples/security-audit-demo.plan.yaml`.
