# AUDIT-EVALUATION.md — Auditoria de Evaluation (estendida)

Consolida `agents-audit/FASE4-AGENTES.md` (avaliação de comportamento de agente: Ragas, DeepEval, Promptfoo etc. — não repetido aqui) com uma extensão nova: **seleção/routing de modelo por custo**, ligada diretamente ao gap de segurança LLM06 (Unbounded Consumption).

## 1. Achado prévio: `model_tier` é só schema, zero implementação

`patterns-from-hermes/README.md` (padrão H04) já descrevia o conceito "multi-model/provider routing": um sítio mapeia `(papel|action|tier) → provider/modelo`, com `model_tier: planner|executor|verifier`. **Verificado agora por busca em todo o repo:** `model_tier` aparece em 5 lugares — todos em `Plan.schema.json`, `plan.schema.md`, e um exemplo de plano. **Nenhum ficheiro de código (`.ts`/`.js`/`.py`) lê `model_tier` e resolve um provider/modelo real.** É um campo obrigatório do schema sem nenhum resolver por trás — mesma classe de achado que `budget_max_replans` (Fase 1 da auditoria de Agentes): desenhado, nunca ligado.

Achado adicional: `budget:` no `Plan.schema.json` só tem `max_replans`/`max_steps` (contadores) — **nenhum campo de custo** ($/tokens).

## 2. LLM Routing / Cost Management — resumo (pesquisa nova)

| Ferramenta | Estrelas/Licença/Atividade | O que faz de facto | Classificação |
|---|---|---|---|
| **LiteLLM** (`BerriAI/litellm`) | 59.112★, MIT (core), atividade diária | `Router` com `cost-based-routing`/`usage-based-routing-v2`/`latency-based-routing`; Budget Manager real: `max_budget`+`budget_duration` hierárquico (global/team/user/key), **reserva de custo pré-chamada** + reconciliação pós-resposta, requer Postgres | **ADOPT** |
| **RouteLLM** (`lm-sys/RouteLLM`) | 5.501★, Apache-2.0, **último commit 2024-08-10** (>2 anos parado) | Classificador de dificuldade da query → modelo forte vs. fraco (académico, LMSYS) | **DEFER/REFERENCE** — padrão sim, dependência não (projeto parado) |
| **Helicone** | 6.164★, Apache-2.0, self-host real | Proxy de observabilidade+custo, forte em UX de dashboard; **adquirida pela Mintlify em março/2026, em modo manutenção** desde então | **REFERENCE** — não ADOPT dado o estado de manutenção |
| Not Diamond / Martian | Comerciais, core fechado | Sem SDK open-source de produção equivalente | **REJECT** como dependência |

**Nota de ceticismo confirmada:** uma busca web sugeriu uma "v0.3 Themis Kubernetes-native" do RouteLLM — verificado diretamente via GitHub API (commits/releases) e **é falso ou confusão com outro projeto**. Descartado.

## 3. Distinção importante — dois eixos diferentes, não confundir

- `model_tier` deste repo é **role-based** (decidido estaticamente no plano, por quem escreve o step: planner/executor/verifier).
- O padrão RouteLLM é **difficulty-based** (decidido dinamicamente, por classificador, a partir do conteúdo da query).

São complementares, não substitutos. Se este repo quiser o padrão RouteLLM no futuro, é um eixo adicional dentro de cada `model_tier`, não substituto dele.

## 4. Recomendação mínima (fecha o gap LLM06)

1. Colocar as chamadas do `LLMService` atrás de `litellm.Router` (não precisa do proxy HTTP completo — o Router embutido basta para um MVP), com um model-group por `model_tier`.
2. Atribuir `max_budget`+`budget_duration` por tier, usando `tags`/`metadata` do LiteLLM com `plan_id`+`step_id` (já existem no schema) para correlacionar custo por execução — fecha "tracking por run, não só por chamada".
3. Adicionar campo de custo ao `budget:` do Plan schema (ex. `max_cost_usd`) + gate no runtime que leia o spend acumulado antes de iniciar cada step.
4. Helicone/Langfuse ficam bem como camada opcional de dashboard por cima — não são o mecanismo de corte (enforcement); só o LiteLLM oferece isso de forma madura entre as ferramentas avaliadas.

## 5. Classificação consolidada (Evaluation, completa)

Ver `agents-audit/FASE4-AGENTES.md` secção 5 para avaliação de comportamento de agente (DeepEval ADOPT, Ragas ADAPT, etc.). Adicional desta extensão:

| Item | Classificação |
|---|---|
| LiteLLM Router + Budget Manager | **ADOPT** |
| RouteLLM (padrão difficulty-based) | REFERENCE (não o pacote) |
| Helicone | REFERENCE |
| `model_tier` → implementar resolver real | **BUILD** |
| `budget.max_cost_usd` no Plan schema | **BUILD** |

## 6. O que NÃO fazer

- Não adotar RouteLLM como dependência — parado há mais de 2 anos, confirmado via API, não por alegação de terceiros.
- Não confiar em alegações de "nova versão"/"atividade recente" de projetos deste tipo sem verificação direta no repositório — uma alegação assim revelou-se falsa nesta própria pesquisa.
- Não adotar Helicone como aposta de infraestrutura agora — em modo manutenção desde a aquisição.
- Não tratar `cost-based-routing` do LiteLLM como "escolha automática de modelo forte vs. fraco por dificuldade" — é balanceamento dentro de um pool já equivalente, não substitui um classificador de dificuldade.
- Não montar billing multi-tenant com Redis para o caso de uso atual (lab, não produção multi-tenant).
