# Plan-Execute — Schema do plano

**Repo:** network-agents-setup (setup only)  
**Produção:** não aplicar automaticamente

## Objectivo

Contrato máquina-legível (e legível por humanos) entre **Planner** e **Executor**.

## Validação formal

| Artefacto | JSON Schema |
|-----------|-------------|
| Plano completo | [`schemas/Plan.schema.json`](./schemas/Plan.schema.json) |
| SeoBrief | [`schemas/SeoBrief.schema.json`](./schemas/SeoBrief.schema.json) |
| CopyAnswerFirst | [`schemas/CopyAnswerFirst.schema.json`](./schemas/CopyAnswerFirst.schema.json) |
| CriticReport | [`schemas/CriticReport.schema.json`](./schemas/CriticReport.schema.json) |

## Schema (campos)

```yaml
plan_id: string          # ex: piloto-seo-copy-002
created_at: iso8601
goal: string             # objectivo em uma frase
context:
  brand: string
  audience: string
  constraints: [string]  # Item 13, disclaimer, sem cutover, etc.
  knowledge_refs: [string]  # paths no repo

steps:
  - id: string           # "1", "2", ...
    name: string
    action: string       # seo_brief | copy_answer_first | critic_item13
    inputs: [string]     # refs a goal, steps anteriores, knowledge
    depends_on: [string] # IDs de steps que devem estar done antes (ex: ["1"])
    tools_allowed: [string]
    output_artifact: string  # path relativo esperado
    output_schema: string    # SeoBrief | CopyAnswerFirst | CriticReport
    done_when: [string]      # critérios testáveis
    on_fail: replan | abort | human
    model_tier: planner | executor | verifier

verify:
  checks: [string]
  human_gate: boolean
  human_gate_when: string

budget:
  max_replans: number
  max_steps: number

status: draft | approved | running | done | aborted
```

### `depends_on`

- Lista de `steps[].id` que têm de estar concluídos antes deste passo.
- Passo inicial: `depends_on: []`.
- Runtime: não iniciar o passo enquanto dependências ≠ done.
- Complementa `inputs` (inputs = dados; depends_on = ordem/gate).

## Regras

1. O **Planner** não escreve em produção nem chama tools destrutivas.
2. O **Executor** só usa `tools_allowed` do passo actual.
3. Sem `done_when`, o passo é inválido.
4. `human_gate: true` bloqueia publicação / git push / DNS.
5. Replan só com evidência do passo falhado; respeitar `max_replans`.
6. Todo passo (exceto o primeiro) deve declarar `depends_on` explícito.

## Output schemas de referência (marketing + Item 13)

Ver JSON Schema em `schemas/`. Resumo:

### SeoBrief
- intent_primary, queries, unique_promise
- title, meta_description, h1
- h2_outline[]
- faq[] (question + answer_draft)
- cannibalization_risks[]
- item13_notes[]
- cta_primary

### CopyAnswerFirst
- hero (h1, answer_paragraph, cta)
- sections[]
- faq_final[]
- disclaimer
- meta_title, meta_description

### CriticReport
- pass: boolean
- gaps[] (severity, message, field?)
- item13_score: 1-5
- publish_ready: boolean  # nunca true sem human_gate se jurídico
