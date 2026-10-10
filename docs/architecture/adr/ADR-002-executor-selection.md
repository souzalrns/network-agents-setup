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

## 4. O que fica adiado — e porquê (honesto)

**Budget-aware *por estimativa*** (escolher um modelo mais barato porque a
*próxima* chamada não caberia no que resta do tecto) fica **deliberadamente
adiado**. Razão concreta, não esquecimento: exige uma **estimativa de tokens
pré-chamada fiável**, e a única que existe no repo —
`runner/plan_runner/token_projection.py` — está marcada no próprio ficheiro como
*"NÃO VERIFICADA. NÃO USAR PARA DECISÕES"*. Construir uma degradação de orçamento
sobre um número não verificado violaria o padrão de evidência do projecto.

**Pré-requisito para desbloquear:** um estimador de tokens verificado — o
endpoint `countTokens` da API Gemini, ou `usageMetadata` real calibrado — a
seguir ao qual a regra "se o custo projectado da chamada exceder o que resta do
`max_cost_usd`, degrada para o tier/modelo mais barato" passa a assentar em algo
sólido e testável. Até lá, o cost cap fail-closed (§3) é a protecção honesta.

## 5. Consequências

- Critério 5 passa a **proven (signal + availability-aware)**; a parte
  budget-por-estimativa fica **documentada como adiada com pré-requisito**, não
  como lacuna silenciosa.
- Fronteira mantida: a complexidade escolhe o *modelo*, nunca o *papel*
  (`model_tier`); a disponibilidade só filtra o modelo de sinal; nada disto é
  política de runtime imposta à planwright.
