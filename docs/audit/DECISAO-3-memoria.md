# DECISÃO 3 — Memória L4: própria, mem0, ou adiar

> **Base:** commit `3dc3b25` + AUDIT-4 §4.3 + AUDIT-6 L6. **Data:** 2026-09-29.
> **Evidência nova:**
> - definição L4 em `docs/architecture/memory/layers.md:40-45`, `contracts.md:7-68`, `scopes.md:1-28`;
> - decisão anterior em `memory/FASE4-SINTESE.md`;
> - **código-fonte do `mem0ai` 2.2.0 instalado** (`/usr/local/lib/python3.11/dist-packages/mem0/`), lido directamente em vez da documentação.

## Resumo

A L4 **está definida** no repo (campos, contrato `remember`/`recall`/`forget`, âmbitos `user|project|agent|org`, `status: candidate` até gate humano), mas tem **zero código**. A decisão registada (`FASE4-SINTESE.md:18`) é **construí-la internamente** e não adoptar ferramentas externas agora. O teste de mem0 que pediste contradiz isso.

A leitura do código do mem0 2.2.0 mostra três coisas:

- **Encaixa parcialmente:** âmbitos `user`/`agent`/`run`; project/org só por metadata.
- **Custa tokens a cada escrita:** 1 chamada LLM por `add()`, com `infer=True` por omissão.
- **Traz dependências e telemetria:** `vecs` em falta para o Supabase; telemetria para a PostHog ligada por omissão.

**Recomendação provisória: VIA A**, L4 própria e pequena, sobre o Supabase já existente, **com o mem0 como spike comparativo de 1–2 dias** e não como adopção. A escolha final depende de 3 perguntas (§3.4).

---

## 3.1 Estado real da memória hoje `[PEDIDO]`

Camadas segundo `layers.md` e o que existe em código:

| Camada | Definição (repo) | Existe em código? | Estado | Evidência |
|---|---|---|---|---|
| L0 identidade/política | `layers.md:3-7` | Parcial | `CLAUDE.md`, `AGENTS.md`, `agents/_shared/grounding.directive.md` (docs) | — |
| L1 contexto de trabalho | `layers.md:9-13` | Sim | Entrada do step + `pending_steps/<id>/` | `executor.py:61-134` |
| L2 episódica | `layers.md:15-32` | **Sim** | `events.jsonl` append-only por run; `status.json` | Runs da Fase 2 |
| L2 pesquisa | — | Sim (por run) | `session_search` FTS5; `plan_runner search` | S31; `cli.py:38` |
| L3 procedural | `layers.md:34-38` | Sim | 67 `SKILL.md`; ciclo candidate→active **não implementado** (só docs) | `docs/generated/SKILLS.md` |
| **L4 semântica** | `layers.md:40-45`; `contracts.md:7-68` | **NÃO** | **Zero código** (grep `remember\|recall\|forget` vazio) | S29 |
| "Memória de cliente" (substituto manual da L4) | `STATUS.md:59` (S30) | Sim, só leitura | `memory/<client_id>/MEMORY.md` → `CLIENT_MEMORY.md` por step; **nenhuma função escreve** | `working_memory.py` (`def`s: `resolve_memory_path`, `read_memory`, `memory_status`) |
| L5 RAG | `layers.md:47-53` | Sim, **partido** | Ingere t6, lê `knowledge_chunks` | AU-19 |
| L6 relacional | `layers.md:55-59` | Não | Opcional por desenho | `FASE4-SINTESE.md:130` |
| HITL (estado de decisões) | — | Python sim; TS em RAM | — | AUDIT-4 §4.3 |
| Estado por projecto (produção) | — | Sim (outro repo) | `project_state` (`last_interaction`) no MCP | `agentRuntime.js:98,169-174` |

**O que falha hoje:** nada lembra factos entre sessões de forma automática. O que atravessa sessões é o `MEMORY.md` (curado à mão), o `project_state` do MCP (só a última interacção) e os `events.jsonl` (por run, sem índice global).

---

## 3.2 O que a L4 exige (definido no repo) `[PEDIDO]`

| Requisito | Fonte |
|---|---|
| Registo: `id`, `scope`, `subject`, `statement`, `confidence`, `source_run`, `created_at`, `ttl?` | `layers.md:43` |
| Conflitos: **novo facto + invalidação opcional do anterior; não editar em silêncio** | `layers.md:44` |
| `forget` para correcção/compliance (soft-delete/tombstone) | `layers.md:45`; `contracts.md:54-68` |
| `remember`: `scope.kind ∈ {user, project, agent, org}` obrigatório; `statement` ≤ 2000; `status` **`candidate` por omissão até gate humano** | `contracts.md:7-34` |
| `recall`: por `scope` + `query` + `limit` (≤ 50) + `tags` | `contracts.md:36-52` |
| Âmbitos: hierarquia `global ⊂ org ⊂ project ⊂ (user\|agent_role) ⊂ run`; o agente não eleva o âmbito; `remember` sem âmbito é recusado | `scopes.md:5-27` |
| Storage | **Não decidido**: SQLite local vs. Supabase (`FASE4-SINTESE.md:163`) |

---

## 3.3 As opções `[PEDIDO]`

### VIA A — Construir L4 internamente

| | Conteúdo |
|---|---|
| **O que implica** | Módulo novo em `runner/plan_runner/` (onde a síntese o coloca, `FASE4-SINTESE.md:143`) com `remember`/`recall`/`forget` no contrato; tabela `memory_l4` (Supabase, reutilizando `DATABASE_URL` e `supabase_writer`) ou SQLite; embeddings Gemini (já usados, `embedder.py`); `status: candidate` + promoção por HITL (o Python já tem HITL durável); ligação ao `executor` para injectar `recall` no `request.json` (mesmo padrão do `CLIENT_MEMORY.md`, S30) |
| **Custo (estimativa do auditor, NÃO VERIFICADA)** | Pequeno a médio: um módulo, uma tabela, um ponto de injecção, testes (o repo já tem padrões para cada peça) |
| **Ganhos** | Encaixe exacto no contrato (âmbitos, `candidate`, tombstone); **zero LLM na escrita** (a escrita é explícita; se se quiser extracção automática, é decisão separada); custo zero; sem telemetria de terceiros; um só storage com a L5 |
| **Riscos** | Código novo a manter; extracção automática de factos fica por fazer (é o que o mem0 dá "de graça", a troco de tokens) |

### VIA B — Adoptar o mem0 (ou similar)

Factos do código-fonte do `mem0ai` 2.2.0:

| Aspecto | Facto | Evidência |
|---|---|---|
| Escrita | `add(…, infer=True)` por omissão → **1 chamada LLM** para extrair factos (`self.llm.generate_response`) + embedding de cada facto extraído | `mem0/memory/main.py:770,956,991-1001` |
| Escrita sem LLM | `infer=False` salta a extracção (fica um vector store com metadados) | `main.py:880` |
| Edição automática | **Não** no `add()` 2.2.0: só emite eventos `ADD`; o prompt de UPDATE/DELETE (`get_update_memory_messages`) está definido mas **não é chamado** por `main.py`; alterações e remoções só por `update()`/`delete()` explícitos | `main.py:909,1070,1196,1869`; `configs/prompts.py:406` (sem chamadores) |
| Âmbitos | `user_id`, `agent_id`, `run_id` (pelo menos um obrigatório) + `metadata` | `main.py:764-787` |
| Storage Supabase | Exige a biblioteca **`vecs`, que não vem nas dependências do pacote** | `mem0/vector_stores/supabase.py:8-10`; `pip show mem0ai` (Requires: httpx, openai, posthog, protobuf, pydantic, pytz, qdrant-client, sqlalchemy) |
| Alternativa | Existe `vector_stores/pgvector.py` (Postgres directo) | `ls mem0/vector_stores/` |
| Dependências arrastadas | `openai`, `qdrant-client`, `posthog`, `sqlalchemy`, … mesmo usando Gemini | `pip show` |
| **Telemetria** | **Ligada por omissão** (`MEM0_TELEMETRY="True"`), enviada para `https://us.i.posthog.com` | `mem0/memory/telemetry.py:14-16` |

| Encaixe no contrato L4 | Resultado |
|---|---|
| `scope.kind` `user`/`agent` | ✅ nativo |
| `scope.kind` `project`/`org` | ⚠️ só via `metadata` + filtros |
| `status: candidate` até gate humano | ❌ não nativo (via `metadata` + lógica própria) |
| `confidence`, `source_run`, `ttl` | ⚠️ via `metadata` |
| Não editar em silêncio | ✅ na 2.2.0 (add só aditivo) |
| `forget` com tombstone | ⚠️ `delete()` apaga; tombstone exige lógica própria |

| | Conteúdo |
|---|---|
| **Ganhos** | Extracção automática de factos a partir de conversas; ecossistema e integrações MCP/IDE (`FASE2-MEMORIA.md:38-41`) |
| **Perdas/custos** | Tokens de LLM **em cada escrita** (contra o objectivo n.º 1); dependências pesadas; telemetria por omissão (desligável por env); o contrato L4 continua a precisar de uma camada própria por cima (candidate, project/org, tombstone) |
| **Conflito com as decisões registadas** | Contraria o "não adoptar agora" (`FASE4-SINTESE.md:18`) e o princípio "funcionar sem infra externa obrigatória" citado na avaliação (`FASE2-MEMORIA.md:44`). **Não** contraria o "custo zero" por si só: com Gemini gratuito e `pgvector` no Supabase existente o custo monetário pode ser zero, mas não é zero em tokens |
| **O teu teste local** | `test_mem0_connection.py` (fora do repo) usava `vector_store: supabase` → **falharia com `ImportError: vecs`** mesmo com `.env` correcto; e usava `SUPABASE_DB_CONNECTION_STRING`, nome que o repo não usa (o canónico é `DATABASE_URL`, AUDIT-1 E7). O modelo `gemini-3.1-flash-lite` indicado no teste **NÃO VERIFICADO** (não confirmado que exista com esse nome) |

### VIA C — Não fazer L4 agora

| | Conteúdo |
|---|---|
| **O que implica** | Continuar com `MEMORY.md` manual + `project_state` (MCP) + L2 por run |
| **O que bloqueia** | "Memória persistente" (pilar da visão) fica por cumprir; os agentes não aprendem preferências nem decisões entre sessões; o nicho trader (histórico de decisões e limites) e o maestro (preferências de delegação) ficam sem base |
| **Quando faz sentido** | Se a Decisão 1 ou 2 ainda estiver aberta, a L4 depende do runtime escolhido (Python na VIA A) |

---

## 3.4 Recomendação fundamentada `[PEDIDO]`

**VIA A (L4 própria)**, com três condições:

1. **Storage = Supabase (`pgvector`) já existente**, e não SQLite. Porquê: a L5 já lá está (`knowledge_chunks_t6`), o `DATABASE_URL` e o `supabase_writer` já existem, e fica partilhável com o MCP. **Pendente:** é a questão aberta de `FASE4-SINTESE.md:163`, que o humano tem de fechar.
2. **Spike comparativo com o mem0 (1–2 dias)**, como pede `FASE4-SINTESE.md` §8 ("antes de qualquer adopção, um spike real é obrigatório"), com `vector_store: pgvector` (evita o `vecs`), `MEM0_TELEMETRY=false` e **medição de tokens por `add()`**. Critério de decisão: se a extracção automática poupar mais tokens a jusante do que custa por escrita, reconsidera-se.
3. **Só depois do AU-19 (RAG)**: não construir L4 sobre um L5 cuja junção está partida.

| Critério da visão | VIA A | VIA B (mem0) | VIA C |
|---|---|---|---|
| Redução de tokens | ✅ escrita sem LLM | ❌ 1 LLM por `add()` (salvo `infer=False`) | — |
| Memória persistente | ✅ | ✅ | ❌ |
| Custo zero | ✅ | ⚠️ zero em €, não em tokens; telemetria | ✅ |
| Encaixe no contrato L4 | ✅ exacto | ⚠️ parcial (camada própria por cima) | — |
| Esforço | Médio (código novo) | Baixo para arrancar, médio para cumprir o contrato | Nenhum |

### Perguntas ao humano

| # | Pergunta |
|---|---|
| M-Q1 | **Queres extracção automática de factos** (o agente decide o que lembrar, como o mem0 faz), ou **escrita explícita** (`remember` chamado por passo/HITL)? É a diferença que decide A vs. B |
| M-Q2 | **Storage da L4:** Supabase (recomendado) ou SQLite local? (`FASE4-SINTESE.md:163`) |
| M-Q3 | **O teu teste de mem0 era para avaliar ou para adoptar?** Se era para adoptar, é preciso revogar formalmente a decisão da FASE4 num ADR |

---

## Limites desta secção

- O mem0 foi lido em código, **não executado** contra o Supabase: o `.env` não está disponível nesta sessão, e o `vecs` não está instalado.
- A contagem de tokens por `add()` é estrutural (1 chamada LLM + embeddings). **NÃO foi medida** em tokens reais.
- Hindsight, Graphiti e os outros ficam como avaliados em `FASE2`/`FASE4`; não foram relidos em código nesta secção.
