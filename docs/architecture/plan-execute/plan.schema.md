# Plan-Execute — Schema do plano

**Repo:** network-agents-setup (setup only)  
**Produção:** não aplicar automaticamente

## Objectivo

Contrato máquina-legível (e legível por humanos) entre **Planner** e **Executor**.

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
    action: string       # identificador estável: seo_brief | copy_answer_first | critic_item13
    inputs: [string]     # refs a goal, steps anteriores, knowledge
    tools_allowed: [string]
    output_artifact: string  # path relativo esperado
    output_schema: string    # nome do contrato de saída
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

## Regras

1. O **Planner** não escreve em produção nem chama tools destrutivas.
2. O **Executor** só usa `tools_allowed` do passo actual.
3. Sem `done_when`, o passo é inválido.
4. `human_gate: true` bloqueia publicação / git push / DNS.
5. Replan só com evidência do passo falhado; respeitar `max_replans`.

## Output schemas de referência (marketing + Item 13)

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
- gaps[]
- item13_score: 1-5
- publish_ready: boolean  # nunca true sem human_gate se jurídico
