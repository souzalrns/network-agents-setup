# Meta-agentes, Fase 2: Execution Broker (contrato arquitectural)

| Campo | Valor |
|---|---|
| **Estado** | **Registo. NÃO implementar.** Contrato arquitectural para a evolução dos meta-agentes depois do `CouncilSession` (Fase 1) |
| **Data** | 2026-10-03 |
| **Origem** | Análise do GPT, entregue pelo maestro e transcrita sem alterações na secção "Análise original" |
| **Relacionados** | [ADR-META-AGENTS](./adr/ADR-META-AGENTS.md) (Fase 1 implementada; §2.2 Fase 2 = deliberação multi-IA), [COUNCIL.md](../ops/COUNCIL.md) (`CouncilSession`), [BUDGET.md](../ops/BUDGET.md) (tecto de tokens), `docs/initiatives/OPEN-ITEMS.md` (itens da Fase 2) |

## Resumo do contrato

Vários agentes ou IAs **raciocinam** sobre um problema; a plataforma decide dinamicamente **um só** provider para **executar**, dentro das políticas e do orçamento. São quatro responsabilidades separadas:

| Componente | Pergunta | Estado hoje |
|---|---|---|
| **Council** | "O que devemos fazer? Como? Que riscos? Que restrições?" | **Existe** (Fase 1): `CouncilSession` |
| **Executor Selector / Execution Broker** | "Quem pode fazer isto agora, dentro das restrições?" (capability, ferramentas, acesso, custo estimado em tokens, política, quota, disponibilidade, fallback) | Não existe |
| **Execution Manager / Lease** | "Só este executor executa": claim → lease → execute → observe → validate → release | Não existe |
| **Plan Runner** | "Controlo o workflow": estados persistentes, retoma | **Existe** (`plan_runner`) |

**Decisões do broker** (as "5 decisões" da análise):

| Decisão | Quando |
|---|---|
| **EXECUTE** | Há capability, autorização e orçamento |
| **REDIRECT** | O executor escolhido não pode agora, mas outro elegível pode |
| **WAIT** | Nenhum alternativo é adequado, mas há recuperação esperada (ex.: reset da quota) |
| **DEFER** | Adiado de forma consciente: não vale gastar agora (`budget_optimization`) |
| **BLOCK** | Nenhum executor válido, e passa a HITL se for preciso |

Regras-chave:
- **Sem downgrade silencioso.** Um fallback exige um `minimum_capability_match` e uma qualidade mínima; se não chegar lá, a decisão é WAIT.
- **O token budget é uma restrição operacional**, como a autorização e a capability, e não só uma métrica. Há orçamentos de sessão, plano, tarefa, custo e quota por provider.
- **Execution Package:** ao redireccionar, o novo executor recebe a decisão, o contexto, os artefactos e os critérios de aceitação, e não começa do zero.
- **Learning:** a plataforma compara o *estimado* com o *real* por tipo de tarefa e provider, e regista no ledger.
- **O executor é um *Execution Provider*,** não necessariamente um agente: pode ser um agent, uma skill, uma tool, um workflow, um modelo, um serviço externo ou um humano.

## Ligação à Fase 1 (`CouncilSession`)

A sequência da análise começa onde a Fase 1 acaba:

```text
CouncilSession (Fase 1, existe)  ──►  Decision  ──►  Executor Selection  ──►  Execution Lease  ──►  Single Executor
                                                   └──────────────── Fase 2 (este documento, não implementado) ────────────────┘
```

O que já existe e serve de base, com evidência:

| Peça do contrato | O que já existe | Evidência |
|---|---|---|
| **Council → Decision** | O `CouncilSession` produz um veredicto estruturado: decisão, condições, kill criteria e `next_actions` | `runner/plan_runner/council_session.py:369` (`next_actions`), classe em `:589` |
| **Separação deliberar ≠ executar** | Já está assim: um `approve` no HITL só promove o veredicto na L4 e fecha a sessão; **não executa nada** | `council_session.py:853-858` |
| **Ponto de entrada (escalada)** | O router escala pedidos estruturais para conselho | `runner/plan_runner/router.py:345` (`escalate`), `:442` (`execute`) |
| **Registo de providers (discovery)** | Agentes com `kind` (`internal` / `external_ai` / `meta`); `external_ai` está reservado para a Fase 2. Áreas e conselhos em YAML, validados no CI (E7) | `agents/README.md:19-20`; `config/areas.yaml`; `config/councils.yaml` |
| **Token budget como restrição** | Tecto de tokens por run, plano ou área, verificado **antes** de cada chamada; ao tecto, `BudgetExceeded` → `paused_budget` | `runner/plan_runner/external_worker.py:78`, `:256`, `:272`, `:286`; `runner/plan_runner/engine.py:123-127` |
| **Estados persistentes / retoma** (WAITING, BLOCKED) | `waiting_external`, `paused_human_gate` e `paused_budget` são retomáveis; o plano não morre | `engine.py:72` (`_RESUMABLE`) |
| **BLOCK → HITL** | HITL durável, contrato `hitl-request-v1` | `docs/architecture/hitl/hitl-request-v1.json`; `runner/plan_runner/hitl.py` |
| **Ledger (actual)** | Uma linha `token_usage` por chamada, com o `usageMetadata` real | `external_worker.py:103` (`build_usage_row`) |
| **Estimated** | `countTokens` + floor/ceiling por conselho | `council_session.py:1001` (`count_tokens`), `:1017` (`estimate_cost`) |
| **1.º dado de "estimated vs actual"** | C-1: estimado 5 860–22 756 contra real 11 760 (1 ronda do `architecture`) | `docs/ops/COUNCIL.md`, "Custo medido (C-1)" |

O que **não existe** (são os itens da Fase 2 em OPEN-ITEMS):
- **Execution Broker:** registo de providers com capabilities, ferramentas, quotas, custo e disponibilidade; selecção (Execution Selection Score, sem ranking fixo de modelos); as 5 decisões; fallback configurável sem downgrade silencioso; Execution Package.
- **Execution Lease:** um só executor por tarefa (claim/lease/expiry/release), com os restantes em modo observador. Hoje nada impede dois executores com escrita de actuarem sobre a mesma intenção.
- **Learning (estimated vs actual):** guardar a estimativa e o real por tarefa e provider no ledger, e aprender com isso.

## Teste de validação: o caso Grok + Claude em paralelo

O caso real relatado pelo maestro é o **teste de aceitação** desta camada. Grok e Claude analisaram **e executaram** em paralelo sobre o mesmo problema, no mesmo projecto. A análise lê-o como prova empírica: sem arbitragem, vários agentes com acesso de escrita executam a mesma intenção ao mesmo tempo.

Critérios de aceitação (a detalhar quando houver ordem de implementação):
1. A mesma intenção chega a dois providers com escrita.
2. O broker emite **uma** lease: um provider fica em EXECUTE e o outro em observador.
3. Uma segunda tentativa de execução sem lease é recusada e registada.
4. Se o executor com lease ficar sem quota, a decisão é REDIRECT (com Execution Package) ou WAIT; nunca há execução dupla.
5. O ledger regista a selecção: `selected_executor`, `selection_reason`, `estimated_cost`, `selection_confidence` e `alternatives`. Regista também o real, para o Learning.

## Notas de leitura (registo, sem alterar a análise)

- **"4 estados" contra "5 decisões".** A análise anuncia 4 estados (READY → EXECUTABLE → BLOCKED → WAITING) e a seguir descreve EXECUTE, REDIRECT, WAIT, BLOCKED e uma 5.ª, DEFERRED. O resumo do fluxo final usa as 5: EXECUTE / REDIRECT / WAIT / DEFER / BLOCK. O contrato acima segue essas 5. Os estados do diagrama de 4 parecem ser do ciclo da tarefa, não decisões do broker; fica por fixar quando houver desenho detalhado.
- **Duas "Fase 2".** O ADR-META-AGENTS §2.2 chama Fase 2 à *deliberação* multi-IA (participantes `external_ai`). Esta análise acrescenta a *execução* (broker e lease) depois do conselho. Ficam registadas as duas sob "Fase 2", sem ordem decidida entre elas.
- **Pré-requisito do ADR que se mantém:** o ledger de tokens é obrigatório antes da Fase 2 (ADR-META-AGENTS §4). O ledger existe (J6); falta a migração do `call_kind` dos conselhos no Supabase (C-2).

---

## Análise original (GPT), transcrita sem alterações

> Transcrição integral do material entregue pelo maestro (2026-10-03). Só se acrescentou a separação "Parte 1 / Parte 2" entre as duas respostas, que vinham seguidas.

### Parte 1

Sim — e olhando para a ideia que você acabou de esclarecer, eu mudaria uma parte importante da conclusão anterior.
A ideia não é tornar a execução “exclusiva” de um agente ou de uma capability. O objetivo é evitar execução redundante e usar os meta-agentes como camada de deliberação/seleção.
A arquitetura fica muito mais interessante assim:

```text
                 META-AGENTS
        ┌────────────┼────────────┐
        │            │            │
       GPT         Claude        Grok
        │            │            │
        └────────────┼────────────┘
                     ↓
              DELIBERAÇÃO
                     ↓
          ┌─────────────────────┐
          │ Executor Selection  │
          │ capability          │
          │ custo/token         │
          │ ferramentas        │
          │ contexto            │
          │ risco               │
          └──────────┬──────────┘
                     ↓
              1 EXECUTOR
                     ↓
              EXECUÇÃO REAL
                     ↓
        resultado / evidências / audit
```

E acho que há uma evolução ainda melhor
Eu não usaria somente "quem tem a capability?" + "quem custa menos?".
Criaria um Execution Selection Score, mas sem transformar isso em ranking fixo de modelos.
O selector recebe algo como:

```yaml
execution_request:
  required_capabilities:
    - application_security
    - vulnerability_management

  constraints:
    production_write: false
    repository_write: true

  estimated_complexity: high

  budget:
    max_tokens: 50000

  risk:
    level: medium
```

E os meta-agentes fornecem suas avaliações:

```yaml
candidate:
  provider: claude
  capabilities:
    match: 0.94
  estimated_tokens: 18000
  tool_fit: 0.91
  context_fit: 0.96
  risk_fit: 0.93
```

Outro:

```yaml
candidate:
  provider: grok
  capabilities:
    match: 0.89
  estimated_tokens: 12000
  tool_fit: 0.88
  context_fit: 0.87
  risk_fit: 0.91
```

Outro:

```yaml
candidate:
  provider: gpt
  capabilities:
    match: 0.96
  estimated_tokens: 24000
  tool_fit: 0.97
  context_fit: 0.95
  risk_fit: 0.96
```

O resultado não deveria ser simplesmente "GPT ganhou".
O sistema deveria produzir:

```text
selected_executor
selection_reason
estimated_cost
selection_confidence
alternatives
```

E registrar isso no ledger.
E aqui está a parte que considero mais importante
Você falou:
"essa execução podemos adotar para além de capacidade o consumo de tokens para executar"
Sim.
Eu transformaria isso em uma Capability + Execution Economics Layer.
Porque no futuro não teremos apenas:

```text
GPT
Claude
Grok
```

Poderemos ter:

```text
GPT
Claude
Grok
Gemini
local model
specialized model
security model
coding model
cheap model
```

E cada um pode ter:

* capacidades diferentes;
* custo diferente;
* latência diferente;
* ferramentas diferentes;
* contexto diferente;
* confiabilidade diferente;
* limites diferentes.

Então o meta-agente não deveria decidir:
"Claude é melhor."
Deveria decidir:
"Para esta tarefa, neste contexto, sob estas políticas e orçamento, este provider é elegível para executar."
Isso é muito mais universal.
E muda a interpretação do que aconteceu com Grok + Claude
Eu não classificaria simplesmente como "anti-padrão".
Na verdade, o experimento revelou exatamente a necessidade da camada que vocês estão construindo.
Vocês colocaram:

```text
GPT → análise
Grok → análise + execução
Claude → análise + execução
```

e observaram:

```text
        MESMO PROBLEMA
              ↓
      ┌───────┴───────┐
      ↓               ↓
    GROK            CLAUDE
      ↓               ↓
    EXECUTA         EXECUTA
```

Isso demonstra empiricamente:
Sem um mecanismo de arbitration/executor selection, múltiplos agentes com acesso de escrita podem executar a mesma intenção simultaneamente.
Essa é uma descoberta arquitetural válida.
Eu faria uma correção no conceito de CouncilSession
Não acho que o CouncilSession deva virar diretamente:

```text
CouncilSession
   └── executor_escolhido
```

Eu separaria as responsabilidades.
Council
Delibera.

```text
What should be done?
How should it be done?
What are the risks?
What constraints exist?
```

Executor Selector
Decide quem é elegível para executar.

```text
Who can do it?
Who has the required capabilities?
Who has the tools?
Who has access?
What is the estimated token/cost?
Who satisfies policy?
```

Execution Manager
Entrega a execução a um único executor.

```text
claim
lease
execute
observe
validate
release
```

Isso é uma separação muito mais limpa.
E aparece um conceito novo muito interessante: Execution Lease
Eu adicionaria isso ao desenho.
Depois da deliberação:

```text
Council
   ↓
Decision
   ↓
Executor Selection
   ↓
Execution Lease
```

Exemplo:

```yaml
execution_lease:
  task_id: task_7842

  executor:
    provider: claude
    agent: security_specialist

  capabilities:
    - application_security
    - vulnerability_management

  budget:
    max_tokens: 30000
    max_cost: 0.80

  permissions:
    repository_read: true
    repository_write: true
    production_write: false

  expires_at: ...

  approval:
    status: approved
```

Enquanto a lease estiver ativa:

```text
Claude → EXECUTA
Grok   → OBSERVA
GPT    → OBSERVA
```

E isso resolve uma coisa que eu considero ainda mais importante que o custo:
concorrência.
Tokens também deveriam entrar como orçamento, não apenas como métrica
Eu faria:

```text
Task
 │
 ├── token_budget
 ├── cost_budget
 ├── time_budget
 └── tool_budget
```

Por exemplo:

```yaml
budget:
  input_tokens: 30000
  output_tokens: 10000
  total_tokens: 40000
  max_cost: 1.50
  max_execution_time: 15m
```

Isso permite uma evolução futura:

```text
Task
 ↓
Estimate
 ↓
Select
 ↓
Execute
 ↓
Actual usage
 ↓
Compare estimated vs actual
 ↓
Ledger
 ↓
Learning
```

E aí a plataforma começa a aprender:
"Para tarefas deste tipo, provider X normalmente usa 40% menos tokens."
Isso é muito mais interessante do que simplesmente escolher "o modelo mais barato".
E existe uma consequência importante
O executor não precisa ser um agente.
Pode ser:

```text
Agent
Skill
Tool
Workflow
Model
External service
Human
```

Então o verdadeiro conceito deveria ser:
Execution Provider
e não necessariamente "Execution Agent".
Isso encaixa perfeitamente na visão universal.

```text
                    TASK
                      ↓
               CAPABILITY NEED
                      ↓
               PROVIDER DISCOVERY
                      ↓
             ┌────────┴─────────┐
             ↓                  ↓
        GPT Provider       Claude Provider
             ↓                  ↓
        Grok Provider      Local Provider
             └────────┬─────────┘
                      ↓
              POLICY + BUDGET
                      ↓
              EXECUTION LEASE
                      ↓
                ONE EXECUTOR
```

Portanto, minha avaliação da ideia
A ideia é mais forte do que a interpretação inicial que eu tinha feito.
Porque vocês não estão tentando criar:
"um sistema onde apenas um agente pode executar."
Estão tentando criar:
um sistema onde vários agentes podem raciocinar sobre o problema, mas a plataforma decide dinamicamente qual provider deve assumir a execução daquela tarefa.
E essa decisão pode considerar:

```text
Capability
+ Tool availability
+ Context
+ Authorization
+ Risk
+ Token budget
+ Cost
+ Latency
+ Historical performance
+ Availability
```

Isso começa a parecer uma verdadeira camada de scheduling/arbitration cognitivo da PCU.
E eu não implementaria isso ainda.
Eu colocaria como próximo contrato arquitetural, primeiro auditando o que vocês já têm no `CouncilSession`, `plan_runner`, registry e ledger.
A sequência correta seria:

```text
CouncilSession
       ↓
DELIVERABLE: Decision
       ↓
Executor Selection
       ↓
Execution Lease
       ↓
Single Executor
       ↓
Execution
       ↓
Validation
       ↓
Ledger
       ↓
Learning
```

Essa, para mim, é a evolução correta da arquitetura dos meta-agentes.
E o fato de Grok e Claude terem efetivamente executado em paralelo no mesmo projeto é justamente um ótimo caso real para usar como teste de validação dessa nova camada — não apenas como algo a evitar.

---

### Parte 2

Sim — e essa questão é fundamental. Eu não faria simplesmente “se não há tokens → escolher outra IA”. Isso pode quebrar continuidade, contexto e até autorização.
Eu trataria orçamento/quotas como parte da elegibilidade do executor, mas com uma política explícita de fallback.
O problema real
Imagine:

```text
Tarefa
  ↓
Council
  ↓
Executor selecionado = Claude
  ↓
Claude disponível?
  ├── SIM → executa
  └── NÃO
        ↓
   por quê?
```

Pode ser:

1. Sem tokens disponíveis nesta sessão
2. Limite mensal/plano atingido
3. Rate limit temporário
4. Modelo gratuito disponível, mas com menor capacidade
5. Provider indisponível
6. Tarefa exige contexto que outro provider não possui
7. Não há nenhum executor elegível

Essas situações não são iguais.
Eu criaria 4 estados

```text
READY
  ↓
EXECUTABLE
  ↓
BLOCKED
  ↓
WAITING
```

Mas com motivo estruturado.
1. EXECUTE
Há capacidade + autorização + orçamento.

```text
Claude
✓ capability
✓ tools
✓ authorization
✓ tokens
✓ budget
```

→ executa.
2. REDIRECT
O executor escolhido não pode executar agora, mas outro executor elegível pode.
Exemplo:

```text
Claude
tokens disponíveis: 0
        ↓
Grok
tokens disponíveis: 25k
        ↓
Capability compatível
        ↓
Policy compatível
        ↓
REDIRECT
```

Isso é muito útil quando algumas IAs são gratuitas.
3. WAIT
Nenhum outro executor é adequado agora, mas existe expectativa razoável de recuperação.
Exemplo:

```text
Claude
quota reset: 14:00

Grok
não possui capability necessária

GPT
quota esgotada
```

Resultado:

```yaml
status: waiting
reason: quota_exhausted
resume_at: 14:00
```

O sistema não fica consumindo tokens tentando alternativas.
4. BLOCKED
Não existe executor válido.
Exemplo:

```text
Tarefa exige:
application_security
+
GitHub write
+
produção

Providers:

Claude → sem quota
Grok → sem GitHub write
GPT → sem quota
Local → não possui capability
```

Resultado:

```yaml
status: blocked
reason: no_eligible_executor
```

E aqui entra HITL se necessário.
E existe uma quinta situação muito interessante
`DEFERRED`
A tarefa pode ser adiada conscientemente porque não vale gastar dinheiro/tokens agora.
Exemplo:

```text
Tarefa:
"Faça uma análise profunda de 300 arquivos."

Custo estimado:
$8

Orçamento restante:
$2

Não é urgente.
```

O sistema deveria poder dizer:

```text
DEFERRED
reason: budget_optimization
```

e não simplesmente falhar.
Isso muda o conceito de orçamento
Eu separaria pelo menos:

```text
SESSION BUDGET
PLAN BUDGET
PROVIDER QUOTA
TASK BUDGET
COST BUDGET
```

Por exemplo:

```yaml
budget:
  session:
    tokens_remaining: 12000

  plan:
    tokens_remaining: 30000

  task:
    max_tokens: 10000

providers:
  claude:
    available_tokens: 0

  grok:
    available_tokens: 8000

  gpt:
    available_tokens: 15000

  free_model:
    available_tokens: 5000
```

Então a decisão não é simplesmente:
"Claude acabou."
É:
"Qual executor elegível consegue cumprir esta tarefa dentro das restrições atuais?"
E eu colocaria uma hierarquia de fallback
Não necessariamente fixa para sempre, mas configurável.

```text
1. Executor deliberado
        ↓
2. Mesmo provider / outra sessão
        ↓
3. Provider equivalente
        ↓
4. Provider gratuito compatível
        ↓
5. Modelo mais barato compatível
        ↓
6. WAIT
        ↓
7. HITL
        ↓
8. BLOCKED
```

Mas há uma regra crítica:
Não fazer downgrade silencioso.
Imagine que o Council deliberou:
Claude Sonnet é necessário para análise complexa.
O sistema não deve automaticamente mandar para um modelo gratuito muito inferior simplesmente porque tem tokens.
Deve avaliar:

```yaml
fallback:
  allowed: true
  minimum_capability_match: 0.85
  minimum_quality: medium
```

Se não atingir o mínimo:

```text
WAIT
```

E as IAs gratuitas são extremamente interessantes
Porque elas podem funcionar como capacity pool, não como “IA inferior”.
Imagine:

```text
                    EXECUTION POOL
                          │
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
      PAID              FREE             LOCAL
        │                 │                 │
    Claude/GPT          Model X          Model Y
```

A plataforma pode saber:

```text
Provider       Custo      Quota       Capability
------------------------------------------------
Claude          €€€        0          Alta
GPT             €€         12k        Alta
Grok            €          20k        Alta
Free-X          €0         8k         Média
Local           €0         ∞          Baixa
```

E então:

```text
TASK
 ↓
requirements
 ↓
eligible providers
 ↓
budget filter
 ↓
capability filter
 ↓
policy filter
 ↓
quality threshold
 ↓
select
```

Mas tem uma questão ainda mais importante: contexto
Suponha:

```text
Claude fez a deliberação.
Claude foi escolhido executor.
Claude ficou sem tokens.
```

Mandar a tarefa para Grok não significa começar do zero.
O sistema deveria entregar um Execution Package:

```yaml
execution_package:
  task:
  objective:
  decision:
  constraints:
  relevant_context:
  artifacts:
  prior_findings:
  required_capabilities:
  policies:
  acceptance_criteria:
  budget:
```

Então:

```text
Claude
  ↓
Deliberation Artifact
  ↓
Execution Package
  ↓
Grok
```

Isso é muito importante para a tua ideia de memória + contexto sincronizado.
E isso conversa diretamente com o Plan Runner
O estado poderia ficar:

```text
PLAN
 │
 ├── Task A → DONE
 │
 ├── Task B → WAITING
 │              └── reason: quota
 │
 ├── Task C → EXECUTING
 │
 └── Task D → BLOCKED
```

Não precisamos matar o plano porque um provider ficou sem tokens.
O plano fica persistente.
Quando houver capacidade:

```text
WAITING
   ↓
RESUME
   ↓
SELECT PROVIDER NOVAMENTE
   ↓
EXECUTE
```

Isso é muito melhor do que:

```text
erro → reiniciar tudo
```

Eu colocaria isso como um componente próprio
Não dentro do Council.
Algo como:
`Execution Broker`
ou, talvez mais precisamente:
`Execution Scheduler`
Responsável por:

```text
Provider Discovery
Quota
Budget
Capability
Authorization
Availability
Cost
Fallback
Queue
Lease
Retry
Resume
```

Enquanto:
Council

```text
"O que devemos fazer?"
```

Execution Broker

```text
"Quem pode fazer agora, dentro das restrições?"
```

Executor

```text
"Vou executar."
```

Plan Runner

```text
"Vou controlar o workflow."
```

Essa separação está ficando muito limpa.
O fluxo completo ficaria

```text
                 META-AGENTS
              GPT / Claude / Grok
                       │
                       ▼
                  COUNCIL
                       │
                 DELIBERATION
                       │
                       ▼
                EXECUTION PLAN
                       │
                       ▼
              EXECUTION BROKER
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
    Capability       Budget         Policy
    matching         /quota         /auth
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                 PROVIDER SELECT
                       │
              ┌────────┴────────┐
              ▼                 ▼
           EXECUTE            WAIT
              │                 │
              ▼                 ▼
          VALIDATE           RESUME
              │
              ▼
            AUDIT
```

E a decisão pode ser:

```text
EXECUTE
REDIRECT
WAIT
DEFER
BLOCK
```

Isso resolve tanto IAs pagas quanto gratuitas, e também permite futuramente modelos locais, APIs de terceiros e até humanos como executores.
Para mim, essa questão que você levantou revela que “token budget” não é apenas uma métrica de custo. É uma restrição operacional do sistema, assim como autorização, capability e disponibilidade. Deve fazer parte do contrato de execução desde o início.
