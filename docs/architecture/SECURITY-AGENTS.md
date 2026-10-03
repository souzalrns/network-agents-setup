# Security agents — pipeline defensivo + Capability First

## Pipeline (área `security`)

```text
security.triage → meta.security-auditor → security.reporter → HITL
```

| Agente | id | action | Ficheiro |
|--------|-----|--------|----------|
| Triage | `security.triage` | `security_triage` | `agents/security/security_triage.agent.md` |
| Auditor | `meta.security-auditor` | `security_audit` | `agents/meta/security_auditor.agent.md` |
| Reporter | `security.reporter` | `security_report` | `agents/security/security_report.agent.md` |

Registo: `config/areas.yaml` → área `security` (`hitl: required`, `max_tokens: 40000`).  
Cyber ≡ security (sem área separada).

## S34 — `vertical` nos planos

O executor resolve agentes com `vertical` do step (omissão = `marketing`).  
Planos security **devem** declarar:

- `vertical: security` em triage e report
- `vertical: meta` no audit (`meta.security-auditor`)

Ver `docs/orchestration/security/templates/examples/security-audit-demo.plan.yaml`.

## Capability First (não 8 agentes)

As capabilities vivem em `config/security-capabilities.yaml`.  
**Não** se cria um agente permanente por capability.

| Capability | Executor v1 | Nível max | status |
|------------|-------------|-----------|--------|
| triage | `security.triage` | READ | implemented |
| defensive_audit | `meta.security-auditor` | READ | implemented |
| security_report | `security.reporter` | READ / PREPARE | implemented |
| secrets_hygiene | auditor + CI (gitleaks) | READ | partial |
| supply_chain | auditor + OSV/Trivy guidance | READ | partial |
| mcp_surface | auditor (skill security-audit) | READ | partial |
| hardening_recommend | reporter → engenharia | PREPARE only | partial |
| agent_redteam_lab | CI/lab isolado | lab only | deferred |

## READ / PREPARE / ACT

| Nível | Agentes security |
|-------|------------------|
| READ | Sim |
| PREPARE | Sim (relatório, checklist, plano de patch) |
| ACT (write prod, exploit, rotate live) | **Não** — só engenharia/ops após HITL |

## Conselho (deliberação)

`config/councils.yaml` → painel `security`: chairman `meta.chairman`, member **required** `meta.security-auditor`.  
Para decisões estruturais (threat model, política de segredos), não para cada triage diário.

## Verificação

```text
cd runner
python -m plan_runner.areas
python -m plan_runner run ../docs/orchestration/security/templates/examples/security-audit-demo.plan.yaml --mode stub --out ../pilots/run-security-demo
```

## O que não fazer

- Ataque activo / pentest ofensivo no runner de produção
- Escrever em produção a partir destes agentes
- Aceitar risco CRITICAL/HIGH sem HITL
- Tratar `security_auditor` como meta-agente de deliberação (é C3 domínio)
- Criar 8 agentes permanentes para as 8 capabilities
- Omitir `vertical:` em planos security (S34)
