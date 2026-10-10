# ADR-002 — Selecção de executor: sinal, disponibilidade e o que fica adiado

**Estado:** aceite e implementado (parcial, por decisão — ver §4).
**Data:** 2026-10-10
**Contexto:** critério 5 da `CAPABILITY-MATRIX-PLANWRIGHT.md` ("Executor selection").
**Código:** `runner/plan_runner/model_tiers.py`, `config/model-tiers.yaml` ·
`runner/tests/test_model_tier.py`.

## 1. Contexto

A selecção de modelo do runner tinha duas peças por fechar no critério 5:
**budget-aware** (escolher mais barato quando o orçamento aperta) e
**availability-aware** (não escolher um modelo que a chave não serve). A base
("signal-aware") ficou fechada no #166: o sinal `complexity` da planwright,
lido de `router.signals`, escolhe o modelo quando o passo não declara
`model_tier` (papel). Este ADR decide o resto — e, com honestidade, o que **não**
se faz já e porquê.

## 2. Decisão — disponibilidade (feito)

Nova lista `available` em `config/model-tiers.yaml` (**vazia por omissão = sem
restrição**). Quando não está vazia e um modelo escolhido **pelo sinal**
`complexity` não está nela, a selecção **degrada para o modelo default**. Regras:

- O sinal **informa, nunca força**: um modelo indisponível não parte o run,
  degrada graciosamente para o default.
- **Não filtra o `model_tier` explícito** — esse é a escolha deliberada do DEV
  (autoridade do papel), não um palpite de sinal.
- Vazia = comportamento de antes; a config do repo vai vazia (ship-safe).

Prova: `test_sinal_indisponivel_degrada_para_default`,
`test_disponibilidade_nao_filtra_o_model_tier_explicito`, e o end-to-end
`test_run_degrada_modelo_de_sinal_indisponivel`.

## 3. O que já existe (não reimplementar)

- **Cost cap fail-closed:** com `budget.max_cost_usd`, um modelo sem preço
  confirmado em `config/model-prices.yaml` **falha fechado antes de gastar**
  (`external_worker.check_budget` + `cost.py`; `test_custo_sem_preco_confirmado`).
  Isto já é uma forma de budget-awareness: o runner recusa gastar às cegas.

## 4. Budget-aware *por estimativa* — DESBLOQUEADO (2026-10-10)

O pré-requisito ficou resolvido: o estimador de tokens é agora **verificado** —
`external_worker.count_tokens()` chama o endpoint `:countTokens` da API Gemini, por
isso o número vem da própria API, não da heurística local (o
`token_projection.py`, ainda marcado "não usar para decisões", não é usado aqui).

Com isso, a **guarda projectiva** `check_budget_projected(out, model, prompt_tokens,
max_output_tokens)` estima a próxima chamada (`prompt + max_output`) e pára **antes**
dela se `gasto + projecção > tecto` (tokens ou custo) — ao contrário do `check_budget`
reactivo, que só pára depois de gastar. É **opt-in** (`PLAN_RUNNER_BUDGET_PROJECT=1`;
por omissão desligada, comportamento inalterado), aplica-se ao caminho sem tools, e
falha fechada num modelo sem preço confirmado (como o cost cap). Prova:
`runner/tests/test_counttokens.py` (unidade + end-to-end com transporte falso).

**Nota de escopo:** a versão implementada **pára** o run (pausa `paused_budget`,
retomável com um tecto maior) em vez de **degradar** automaticamente para um modelo
mais barato. A degradação automática fica como passo seguinte (combina esta guarda
com a selecção por `complexity`/`available` da §2) — mas a base agora assenta num
estimador verificado, não num número duvidoso.

## 5. Consequências

- Critério 5 passa a **proven (signal + availability-aware + budget-por-estimativa
  opt-in)**; falta só a *degradação automática* de modelo (passo seguinte), não a
  medição.
- Fronteira mantida: a complexidade escolhe o *modelo*, nunca o *papel*
  (`model_tier`); a disponibilidade só filtra o modelo de sinal; nada disto é
  política de runtime imposta à planwright.
