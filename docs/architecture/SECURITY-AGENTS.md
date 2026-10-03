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

## Validação automática (E7)

`python -m plan_runner.areas` (no CI, job `test`) valida o `config/security-capabilities.yaml` contra os agentes, as skills e a área (`runner/plan_runner/capabilities.py`):
- `policy.offensive` e `policy.act_in_production` só aceitam `forbidden`; `policy.hitl` tem de ser `required`, porque a área tem `hitl: required`;
- o nível `act` é recusado; `lab` só em capabilities `deferred` (fora do runner de produção);
- `implemented`/`partial`: o agente existe, está em agents[] da área `security`, tem o mesmo `action:` da capability, e a skill existe com o mesmo `action:`;
- qualquer `skill:` declarado por um agente tem de existir.

`python -m plan_runner.areas --inventory` lista, sem falhar o CI: agentes sem skill, skills sem agente, agentes que carregam o pack Claude e skills partilhadas.

## Routing (router D2)

- As keywords da área (`threat model`, `superficie de ataque`, `security triage`, `hardening`, `pentest`…) mandam o pedido para a área `security`; o LLM do router escolhe entre os 3 agentes.
- **`threat model` / `modelo de ameacas` também são keywords de escalada do conselho `security`** (`config/councils.yaml`). Um pedido com elas vai para o **conselho**, não para o pipeline. Regra de uso: **1 conselho ≈ 1 SEO** (`docs/ops/COUNCIL.md`), por isso só para decisões estruturais.
- Um pedido ofensivo ("pentest", "atacar") cai na área: a triagem regista `out_of_scope: ataque activo proibido` e não sugere exploits.

## Quando usar cada skill de segurança

| Skill | Tamanho | Onde | Quando |
|---|---:|---|---|
| `skills/security/triage` | ~1,5 KB | runner (step `security_triage`) | Classificar o pedido: superfícies, severidade, se precisa de audit completo |
| `skills/meta/security-audit` | ~5,5 KB | runner (step `security_audit`, `meta.security-auditor`) | Auditoria defensiva OWASP LLM 2026 / NIST / ATLAS / MAESTRO |
| `skills/security/reporter` | ~1,7 KB | runner (step `security_report`) | Consolidar triagem + audit num relatório com próximos passos |
| `skills/claude/security-and-hardening` | ~24 KB | **pack Claude** (sessões de engenharia / harness) | Hardening ao **escrever** código (input não confiável, auth, dados pessoais). **Não** entra nos steps do runner: nenhum agente a declara, e o tamanho (24 KB) custaria ~6–7k tokens de entrada por passo, pelos 3,3–3,5 caracteres por token medidos no B1 (lição B1-bis) |

Não se fundem sem decisão explícita: uma audita (READ), a outra guia a implementação (ACT, fora desta área).

## Limites (verificados a 2026-10-03)

- **Em `--mode external` o auditor não vê o repositório.** O worker não tem tools: `tools_allowed: [read_repo_file]` é declarativo, e o prompt diz "Nao tens tools neste passo" (`runner/plan_runner/external_worker.py`). O `knowledge_refs` do plano não é lido pelo runner (AU-22; AUDIT-2 Y9).
  - **Consequência:** em external, o resultado é um audit de âmbito e lacunas (a skill e o grounding obrigam a marcar lacunas), **não** uma auditoria do código.
  - O teste `tests/test_security_pipeline.py` fixa este limite, para que uma mudança nele seja deliberada.
  - **Decisão pendente (SEC-1):** como dar ficheiros ao auditor.
    - **A (recomendada):** campo opt-in por passo (ex.: `repo_files: [...]`), só para os passos que o declarem. Paths dentro do repo, só leitura, cortados por tamanho, com uma denylist fixa (`.env*`, `*.pem`, `*.key`, `secrets/`…). Planos existentes ficam iguais; é uma parte do AU-22.
    - **B:** implementar o `knowledge_refs` para todos os planos (o AU-22 tal como está escrito). Muda os prompts de todos os planos com `knowledge_refs`, incluindo o `seo-article-demo`, e invalida a base medida no B1-bis-R2.
    - **C:** manter. Em external, o audit fica de âmbito e lacunas; a auditoria real faz-se com `gitleaks`/`semgrep` (J10) e revisão humana.
- **Segredos nunca entram num prompt.** Qualquer solução futura que injecte ficheiros tem de excluir `.env*`, chaves e credenciais. A `secrets_hygiene` faz-se com `gitleaks` **local** ou no CI (J10), nunca mandando ficheiros a um LLM externo.
- **Os conselhos usam só o AGENT.md, não a skill.** O `engenharia.revisor-codigo` (crítico nos conselhos `security`/`architecture`) aponta para uma skill do pack Claude (`code-review-and-quality`), que só é carregada quando corre como passo de plano.

## Verificação

```text
cd runner
python -m plan_runner.areas                 # E7 (+ --inventory)
python -m pytest tests/test_capabilities.py tests/test_security_pipeline.py -q
python -m plan_runner run ../docs/orchestration/security/templates/examples/security-audit-demo.plan.yaml --mode stub --out ../pilots/run-security-demo
```

**Resultado (2026-10-03, ambiente com todas as dependências, incluindo `mcp`):**
- E7 verde: 10 áreas, 37 agentes, 3 conselhos, 1 ficheiro de capabilities;
- testes: **34 novos** (`test_capabilities.py` 28, `test_security_pipeline.py` 6); suite rápida 363 passed (41 skipped precisam de Postgres e correm no CI, job `test-rag`); suite lenta 34 passed;
- plano demo:
  - em stub, chega a `paused_human_gate` com os 3 artefactos;
  - em external (Gemini falso), cada passo recebe o AGENT.md e a SKILL.md certos, com grounding `full` e política `opt`;
  - o ledger regista os 3 agentes, e a triagem já não é pedida em resumo (`context.full` no report).

## O que não fazer

- Ataque activo / pentest ofensivo no runner de produção
- Escrever em produção a partir destes agentes
- Aceitar risco CRITICAL/HIGH sem HITL
- Tratar `security_auditor` como meta-agente de deliberação (é C3 domínio)
- Criar 8 agentes permanentes para as 8 capabilities
- Omitir `vertical:` em planos security (S34)
