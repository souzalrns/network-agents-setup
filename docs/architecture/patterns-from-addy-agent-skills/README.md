# Padrões — addyosmani/agent-skills

**Fonte:** [github.com/addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT)  
**O quê:** skills de engenharia para coding agents + slash commands + personas.  
**Não é:** vertical marketing; é **lifecycle de software** (Define→Ship).

---

## 1. Modelo mental (6 fases)

```text
DEFINE → PLAN → BUILD → VERIFY → REVIEW → SHIP
 /spec    /plan   /build  /test    /review  /ship
```

| Fase | Comando | Princípio |
|------|---------|-----------|
| Define | `/spec` | Spec before code |
| Plan | `/plan` | Tarefas pequenas e atómicas |
| Build | `/build` | Uma fatia de cada vez |
| Verify | `/test` | Testes = prova |
| Constraints | `/constraints` | Barra de qualidade fixa |
| Review | `/review` | Saúde do código |
| Perf web | `/webperf` | Medir antes de optimizar |
| Simplify | `/code-simplify` | Clareza > esperteza |
| Ship | `/ship` | Fan-out + go/no-go |

Alinha com **Spec Kit** (`constitution → specify → plan → tasks → implement`) e com o nosso **plan-execute** (steps + `done_when` + HITL).

---

## 2. Três camadas (regra de ouro)

| Camada | Papel | Nosso equivalente |
|--------|-------|-------------------|
| **Skill** | *Como* — passos + exit criteria | `skills/**/SKILL.md` |
| **Persona / Agent** | *Quem* — perspectiva + formato de saída | `agents/**/*.agent.md` |
| **Command / entry** | *Quando* — compõe skills/personas | `plan.yaml` template ou slash no IDE |

**Composição:** o utilizador (ou o command/plan) **orquestra**. Personas **não** invocam outras personas em mesh.

Isto é exactamente a nossa regra do marketing orchestrator + registry de actions.

---

## 3. `/ship` — fan-out paralelo (padrão a roubar)

```text
/ship
  ├── (paralelo) code-reviewer
  ├── (paralelo) security-auditor
  └── (paralelo) test-engineer
            ↓
     merge (agente principal)
            ↓
     GO | NO-GO + rollback plan
```

Regras do upstream:

- Sub-tarefas **independentes** (sem estado mutável partilhado) → paralelo seguro  
- Caso contrário → sequência (`/spec` → `/plan` → …)  
- Skip fan-out só se: ≤2 ficheiros, &lt;50 linhas, e **não** toca auth/payments/data/config  

### Mapeamento ao nosso runner

Hoje o `plan_runner` é **sequencial** (`depends_on`). Fan-out = extensão futura:

```yaml
# Conceito — ainda não implementado no runner lab
- id: ship_gate
  parallel:
    - action: code_review
    - action: security_scan
    - action: test_engineer
  merge_action: ship_decision  # GO|NO-GO
  human_gate: { kind: confirmation, allow: [approve, reject] }
```

Até existir `parallel` no engine: plan sequencial `code_review → security → tests → ship_decision` ou três steps sem deps mútuas documentados como “logicamente paralelos”.

---

## 4. O que adoptar

| Padrão | Acção no setup |
|--------|----------------|
| Skill + agent + command/plan | Já temos; reforçar linguagem |
| Fases Define→Ship para **engenharia** | Templates `plan` de software (além de marketing) |
| `/ship` fan-out + GO/NO-GO | Doc + action `ship_decision`; parallel no runner = fase 2 |
| Five-axis code review | Skill `code_review` (correctness, readability, architecture, security, performance) |
| TDD enforced no build | Skill `test_driven` + `done_when` = testes |
| Plan clobber guard (não sobrescrever plan incompleto) | Runner: não apagar `out` resumível (já parcial) |
| Personas não orquestram personas | L0 policy |
| Eval/rank de skill descriptions | Opcional portfolio qualidade |

## 5. O que **não** adoptar por inteiro

| Item | Motivo |
|------|--------|
| Plugin Claude/Cursor como runtime único | Setup é multi-IDE + plan_runner lab |
| 25 skills de engenharia de uma vez | Ingestão selectiva |
| Substituir vertical marketing | Domínios diferentes |
| Mesh livre de agentes | Upstream também rejeita |

---

## 6. Analogia marketing (já validada)

| Engenharia (Addy) | Marketing (nosso) |
|-------------------|-------------------|
| /spec | objective + research |
| /plan | plan.yaml template |
| /build | copy / social / story |
| /test | critic / creative_review |
| /review | critic_item13 |
| /ship | HITL publish (+ futuro fan-out legal/brand/risk) |

---

## 7. Providências

| ID | Providência | Estado |
|----|-------------|--------|
| AO-01 | Documentar 3 camadas skill/agent/command | este doc |
| AO-02 | Action `ship_decision` (GO/NO-GO + rollback notes) | registry |
| AO-03 | Skill `code_review` five-axis (engenharia) | a criar sob demanda |
| AO-04 | Template plan `software-ship` sequencial | a criar sob demanda |
| AO-05 | Runner `parallel` steps | futuro |
| AO-06 | MIT: pode copiar padrões; não vendor-lock ao plugin | — |

---

## 8. Licença

MIT — padrões e ideias reutilizáveis; ao copiar texto de skills, manter atribuição quando for excerpt substantivo.
