# PLANO DE ACÇÃO — porta de entrada da auditoria

> **Branch:** `claude/audit-completo` · **Base auditada:** commit `3dc3b25` · **Data:** 2026-09-29.
> **Natureza:** documento de navegação e consolidação. **Não implementa nada, não corrige nada e não altera nenhum dos 12 documentos da auditoria.**

---

## 0. REGRA NOVA E PERMANENTE — decisões humanas em A/B/C (acrescentado em 2026-09-30)

**Nenhuma decisão humana pode chegar em aberto.** Toda a bifurcação chega ao Dev como escolha concreta:

```
Opção A — <descrição> | Custo: <x> | Consequência: <y>
Opção B — <descrição> | Custo: <x> | Consequência: <y>
Opção C — <descrição> | Custo: <x> | Consequência: <y>
RECOMENDADA: <letra> porque <razão>
Se o Dev não responder em N dias, executa-se a RECOMENDADA.
```

Acabou o "o que queres fazer?". A regra aplica-se a todas as decisões, incluindo as antigas da secção 8. O estado actual de cada uma está na **secção 13**: tomada, ou em aberto com uma opção recomendada por omissão.

Secções acrescentadas em 2026-09-30:
- **13** — Decisões tomadas vs. em aberto;
- **14** — EXTRAIR (não adoptar);
- **15** — Protocolo meta-agentes (Fase 2).

---

## 1. Cabeçalho

### O que é este documento

É a **porta de entrada única** da auditoria. Junta num só sítio o estado real do projecto, as decisões pendentes, o plano de acção e as pendências, sempre com **link para a origem**.

### Para que serve

- Saber, em minutos, **o que está partido**, **o que decidir** e **o que se pode fazer já**.
- Encontrar o detalhe de qualquer item sem ter de ler os 12 documentos por ordem.

### Como se lê

1. Secções 2–3: o estado e as decisões.
2. Secções 4–6: o que fazer e por que ordem.
3. Secção 7: o que muda consoante a decisão tomada.
4. Secção 8: as perguntas que precisam de resposta tua.
5. Secções 9–12: índice, contagens e links.

Cada secção indica no topo a **origem** (ficheiro + secção).

> **Nota:** este é o ponto de entrada. **O detalhe está nos 12 ficheiros ligados em baixo. Nada foi suprimido.** Quando um item não aparece aqui por extenso, é porque vive no ficheiro de origem, com link, e não porque foi cortado. As marcas **NÃO VERIFICADO / NÃO VERIFICÁVEL** e **[ACRESCENTADO PELO AUDITOR]** das fontes foram mantidas.

### Índice dos 13 documentos

| # | Documento | Uma linha |
|---|---|---|
| 0 | **PLANO-DE-ACAO.md** (este) | Porta de entrada: estado, decisões, plano e pendências, com links |
| 1 | [AUDIT-1-estrutura.md](./AUDIT-1-estrutura.md) | Repos, pacotes, REAL/MORTO/AMBÍGUO, build verificado, retificações R1–R13 |
| 2 | [AUDIT-2-cadeia.md](./AUDIT-2-cadeia.md) | Cadeia `/chat` executada por sonda (Q1–Q7), motor Python corrido, RAG verificado ao vivo |
| 3 | [AUDIT-3-agentes.md](./AUDIT-3-agentes.md) | 24 agentes na config, 35 `.md`, 27 de marketing desenhados, delegação e nichos |
| 4 | [AUDIT-4-modulos.md](./AUDIT-4-modulos.md) | MOCK/INCOMPLETO/órfãos, contradições no `CORE-MAPPING`, varrimento do core |
| 5 | [AUDIT-5-itens.md](./AUDIT-5-itens.md) | Inventário de ~175 itens com estado verificado; 50 achados AU |
| 6 | [AUDIT-6-lacunas.md](./AUDIT-6-lacunas.md) | Lacunas L1–L10, retificações, inclusões, ligações por área, ferramentas pendentes |
| 7 | [AUDIT-COMPLETO.md](./AUDIT-COMPLETO.md) | Consolidação da Fase 1: resumo, atribuição, índice-mestre, top 10 |
| 8 | [DECISAO-1-runtimes.md](./DECISAO-1-runtimes.md) | Python vs TS vs ambos vs maestro no MCP (vias A/B/C/D) |
| 9 | [DECISAO-2-maestro.md](./DECISAO-2-maestro.md) | O maestro hoje, o que devia ser, opções de desenho, perguntas ADR |
| 10 | [DECISAO-3-memoria.md](./DECISAO-3-memoria.md) | L4 própria vs mem0 vs adiar, com leitura do código do mem0 2.2.0 |
| 11 | [DECISAO-4-ordem.md](./DECISAO-4-ordem.md) | Primeiro passo por via; bloqueado vs independente; 11 frentes |
| 12 | [DECISOES-COMPLETO.md](./DECISOES-COMPLETO.md) | Consolidação da Fase 2 |

---

## 2. Resumo executivo

> **Origem:** [AUDIT-COMPLETO.md](./AUDIT-COMPLETO.md) → "Resumo executivo".

### O que o projecto é hoje

Um monorepo com **dois runtimes que não se falam**:

| Runtime | O que é | Estado |
|---|---|---|
| **Motor Python** (`runner/plan_runner`, ~3.2k LOC) | Executa planos YAML com gates humanos, auditoria e retoma | **Funciona e está testado** (195/195), mas não executa trabalho nenhum sozinho: entrega cada passo a um "worker externo" que não existe no repo |
| **Plataforma TypeScript** (`apps/api` + 8 pacotes, ~19.5k LOC, 12.7k só no `core`) | Router → Planner (LLM) → Executor | **Não chega ao LLM**: todos os pedidos são bloqueados na deliberação por um erro de escala. Atrás desse bloqueio há mais três quebras |

Além disso: **226 documentos de desenho e auditoria**, **67 skills** e **35 agentes em markdown**.

Há ainda um **terceiro runtime** fora deste repo, o `agent-network-mcp` (JavaScript, produção Vercel), que tem o **único router LLM em produção** (origem: [DECISAO-1](./DECISAO-1-runtimes.md) §1.1, [ACRESCENTADO PELO AUDITOR]).

### O que está ligado, morto ou só no papel

| Categoria | Itens |
|---|---|
| **Ligado** | **Motor Python:** `stub`, `external`, HITL por ficheiros, retoma, LangGraph com checkpoints, memória de cliente (só leitura), pesquisa de eventos. **Superfície MCP do motor:** stdio. **Ingestão RAG:** 110 chunks no Supabase em cada push. **Autenticação HTTP:** fail-closed. **CI:** TS e Python verdes; `pnpm audit` = 0, **mas o GitHub ainda reporta 1 alerta crítico do Dependabot (#11)**, provavelmente do manifest órfão `tests/package.json` (AU-05; **NÃO VERIFICADO directamente**, a API devolve 403) |
| **Morto** | `apps/web`, `packages/langgraph`, `tests/package.json` |
| **Só no papel** | Build de produção TS (`pnpm build`/`Dockerfile` falham); `k8s/` (deploy que nunca existiu); workflow `keep-alive` (falhou nos 5 runs); 18 dos 31 módulos que o orquestrador instancia são órfãos (6 039 LOC); 45 ferramentas externas referidas nos docs, **0** em código |

### As 7 lacunas críticas

| # | Lacuna | Achado |
|---|---|---|
| 1 | Não há maestro: dois orquestradores sem ponte, e o único router real vive noutro repo | AU-07 |
| 2 | O RAG ingere para `knowledge_chunks_t6` e o retrieve lê `knowledge_chunks` | AU-19 |
| 3 | Os tokens nunca são contados, por isso o objectivo n.º 1 da visão não tem instrumento | AU-16/L8 |
| 4 | A memória L4 tem zero código | S29 |
| 5 | O HITL TS é volátil e não tem retoma | AU-18 |
| 6 | Nenhum agente corre sozinho | L9 |
| 7 | Financeiro, jogos e segurança não existem como áreas; "jogo" é encaminhado para um domínio com 0 agentes | AU-35/AU-30 |

### O que falta para ter "pernas"

Ver a secção 10 deste documento: **3 decisões + 4 construções pequenas**.

---

## 3. As 4 decisões pendentes

> **Origem:** [DECISOES-COMPLETO.md](./DECISOES-COMPLETO.md) → "Resumo das 4 decisões"; detalhe em [DECISAO-1](./DECISAO-1-runtimes.md), [DECISAO-2](./DECISAO-2-maestro.md), [DECISAO-3](./DECISAO-3-memoria.md), [DECISAO-4](./DECISAO-4-ordem.md).
> Todas as recomendações são **provisórias** até o humano responder às perguntas da secção 8.

| Decisão | O que está em jogo | Recomendação da auditoria | Pergunta decisiva ao humano | Itens que desbloqueia |
|---|---|---|---|---|
| **D1 — Runtimes** ([DECISAO-1](./DECISAO-1-runtimes.md)) | Dois runtimes sem ponte, mais um terceiro em produção (MCP). O Python ganha em 6 dos 9 critérios da visão (custo zero, memória, ingestão, tokens, HITL, testes); o TS em 3 (tools, API e, marginalmente, maestro). As vantagens do TS cabem em ~1,2k LOC portáveis; as do Python custariam ~4,3k LOC + 195 testes a reescrever | **VIA A** — consolidar em Python, portando ~1,2k LOC do TS e **arquivando** (não apagando) o resto (≈17k LOC). Alternativas: **B** (TS), **C** (ambos), **D** (maestro no MCP + motor Python, [ACRESCENTADO PELO AUDITOR]) | **Quem chama o sistema?** e **onde corre o motor?** (Q1–Q4, secção 8) | Worker (A/C/D) **ou** quebras do `/chat` (B/C); provider Gemini; HITL TS; build/Docker; órfãos TS; `MCPServer` TS; `query_database`; CORS; CI lento/lockfile Py (se ≠ B) |
| **D2 — Maestro** ([DECISAO-2](./DECISAO-2-maestro.md)) | Três maestros parciais: TS bloqueado e com 8 agentes inalcançáveis; Python sem planeador; MCP com router LLM real mas plano, ~1,5k tokens/pedido a crescer ~44 tokens por agente (heurística chars/4, **NÃO medido com tokenizer**) | **Router hierárquico híbrido** (área por palavras-chave/embeddings → agente por LLM só dentro da área) sobre um **registo de áreas versionado e validado em CI**; horizontais sempre candidatos; clarificação/HITL com baixa confiança | **Um agente por pedido ou plano multi-passo?** Qual a **lista inicial de áreas?** (ADR-M1…M8) | Código do router/planner; fallback; alcançabilidade no runtime; implementação dos nichos |
| **D3 — Memória L4** ([DECISAO-3](./DECISAO-3-memoria.md)) | L4 definida (contrato completo) e com zero código. O mem0 2.2.0 encaixa parcialmente, gasta 1 chamada LLM por escrita, precisa de `vecs` para o Supabase e envia telemetria por omissão | **VIA A** — L4 própria em `runner/plan_runner`, sobre o Supabase existente, **depois** de consertar o RAG, **com um spike mem0** de 1–2 dias para comparar | **Extracção automática de factos ou escrita explícita?** O teste de mem0 era **avaliação ou adopção**? (M-Q1…Q3) | Módulo L4; ponte HITL↔memória; `MEMORY.md` passa a fallback |
| **D4 — Ordem** ([DECISAO-4](./DECISAO-4-ordem.md)) | Do top 10, 5 itens estão bloqueados por inteiro pelas decisões e 2 em parte | **Já resolvida:** começar pelas **11 frentes independentes** (secção 4) e tomar as decisões **D1 → D2 → D3** por esta ordem | — | — |

---

## 4. Plano de acção — PODE COMEÇAR JÁ

> **Origem:** [DECISAO-4-ordem.md](./DECISAO-4-ordem.md) §4.3 (detalhe e justificação de independência) e §4.4 (ordem).
> **Critério:** o valor mantém-se em **todas** as vias da D1 e não precisa de nenhuma das decisões 1–3.

| Ordem | Item | O que é | Quem | Evidência |
|---|---|---|---|---|
| 1 | **J1 — Keep-alive** (AU-47) | Definir as secrets `SUPABASE_URL`/`SUPABASE_ANON_KEY` neste repo e criar a tabela `keepalive`; confirmar um run verde. Protege o Supabase que todas as vias usam. **FEITO 2026-09-30** (run #6 verde) | DEV (secrets) → CLAUDE (SQL + verificação) | [AUDIT-5](./AUDIT-5-itens.md) AU-47: 5/5 runs ❌ → run #6 ✅ |
| 2 | **J7 — Apagar `tests/package.json`** (AU-05) | Manifest órfão fora do workspace, causa provável do Dependabot #11 crítico. **FEITO 2026-09-30** (PR #30 merged) | CLAUDE | [AUDIT-5](./AUDIT-5-itens.md) AU-05 |
| 3 | **J3 — RAG** (AU-19) | Micro-decisão "tabela canónica" (`knowledge_chunks_t6` vs `knowledge_chunks`, ou RPC por tabela) + retrieve que lê o que se ingere. **FEITO 2026-09-30** (PR #31 merged + migração corrida; falta apagar a t6) | AMBOS | [AUDIT-2](./AUDIT-2-cadeia.md) §2.4; `docs/ops/RAG-CANONICAL.md` |
| 4 | **J6 — Ledger de tokens no MCP de produção** | Guardar o `usageMetadata` do Gemini por agente/pedido; hoje é ignorado. Linha de base do objectivo n.º 1. ~~**NÃO VERIFICADO** se o `usageMetadata` vem na resposta usada~~ — **verificado** por chamada real (vem no `generateContent`; o `embedContent` não o tem). **FEITO 2026-09-30**: tabela `token_usage` em produção (PR #8 do `agent-network-mcp`) | AMBOS (outro repo) | `agent-network-mcp/lib/tokenLedger.js`; `agent-network-mcp/docs/ops/TOKEN-LEDGER.md` |
| 5 | **J4 — `description:` nos 35 agentes `.md`** | 0/35 têm descrição; qualquer router precisa dela; validar `vertical:` nos 5 que faltam | CLAUDE redige → DEV revê | [DECISAO-2](./DECISAO-2-maestro.md) §2.1 |
| 6 | **J5 — Registo de áreas como dados** | `areas.yaml` (id, descrição, agentes, horizontais), **sem código de router** | DEV decide a lista → CLAUDE escreve | [DECISAO-2](./DECISAO-2-maestro.md) §2.5 |
| 7 | **J8 — Higiene de docs** | AU-45 (colisões de IDs), AU-46 (regenerar OPEN-ITEMS), AU-37 (errata CORE-MAPPING), AU-12 (partir o STATUS de 95 KB), AU-08 (`.env.example`) | CLAUDE | [AUDIT-5](./AUDIT-5-itens.md) §5.1 |
| 8 | **J2 — VM Oracle** (S20) | Chave antiga no `pm2`; o bridge-worker está parado. **NÃO VERIFICÁVEL daqui** | DEV | `STATUS.md:41` |
| 9 | **J11 — Spike mem0 vs L4** | 1–2 dias, medindo tokens por `add()`; **informa** a D3 | AMBOS | [DECISAO-3](./DECISAO-3-memoria.md) §3.4 |
| 10 | **J9 — Pesquisas de nicho** | G1.1 (trading/simulação) e G2.1 (gamedev), só pesquisa; informam a D2 | CLAUDE | `EXECUTION-PROMPTS.md:1618,1896` |
| 11 | **J10 — Gate de segurança em CI** | gitleaks/semgrep (já listados no B2b) | AMBOS | `STATUS.md:28` |

**Correcção ao que parecia independente** (origem: [DECISAO-4](./DECISAO-4-ordem.md) → Resumo): "corrigir as 4 quebras do `/chat`" **não** está nesta lista, porque só tem valor nas vias B ou C da D1. "Medir tokens" está, mas **no MCP de produção**, não no TS do setup.

---

## 5. Plano de acção — BLOQUEADO POR DECISÃO

> **Origem:** [DECISAO-4-ordem.md](./DECISAO-4-ordem.md) §4.2 (por item) e §4.4 (por decisão).

### Por item

| Item | Bloqueado por | Porquê / o que desbloqueia |
|---|---|---|
| AU-13/14/15/17 (quebras do `/chat` + teste) | **D1** | Só valem em B ou C |
| AU-18 / M4 / M3 (HITL TS durável e retoma) | **D1** | Na A e na D usa-se o HITL Python, que já é durável |
| AU-23 (worker `external`) | **D1** | Central na A, C e D; desnecessário na B |
| M6 (provider Gemini) | **D1** | A forma muda: cliente Python (A) vs `GeminiProvider` TS (B) |
| AU-01/AU-02 (build TS, Docker, k8s) | **D1** | Só relevantes se o TS ficar |
| AU-38 / M5 (mover 18 órfãos) | **D1** | Na A arquiva-se o TS inteiro, tornando o M5 desnecessário |
| AU-41 / EX-C2 (montar ou descontinuar `MCPServer` TS) | **D1** | Idem |
| AU-48 (`query_database` read-only), S13 (CORS) | **D1** | Só TS |
| AU-20 (fonte de `toolsAllowed`) | **D1 + D2** | A fonte depende do runtime e do contrato de handoff |
| AU-26/AU-30/AU-34 (código do router/planner) | **D2** | O mecanismo de routing é o ADR do maestro |
| AU-35, B3, B4, G1.x/G2.x de implementação (nichos) | **D2** (+ escopo) | Os nichos entram como áreas no registo |
| S29 / AU-39 / L4 | **D3** (+ D1) | Storage e modelo de escrita por decidir |
| AU-22 (campos de plano mortos no Python) | **D1** | Só vale se o Python ficar (A/C/D) |
| AU-09, AU-31, AU-32, A9 (CI lento, resolução skill↔agente, template design, lockfile Py) | **D1** (fraco) | Valem em A/C/D; perdem-se na B |

### Por decisão

| Decisão | O que desbloqueia |
|---|---|
| **D1 (runtime)** | Worker (A/C/D) **ou** quebras do `/chat` (B/C); provider Gemini; HITL TS; build/Docker; órfãos TS; `MCPServer` TS; `query_database`; CORS; CI lento/lockfile Py (se ≠ B) |
| **D2 (maestro)** | Código do router/planner; fallback; alcançabilidade no runtime; implementação dos nichos |
| **D3 (L4)** | Módulo L4; ponte HITL↔memória; `MEMORY.md` passa a fallback |
| **D1 + D2** | Fonte de `toolsAllowed`; contrato de handoff; orçamento por área |

---

## 6. Top-10 prioridades

> **Origem:** [AUDIT-COMPLETO.md](./AUDIT-COMPLETO.md) §7.3. Ordenadas pelo que desbloqueia mais da visão com menos esforço; as decisões vêm antes da construção.
> **Estado actual de cada uma face às decisões:** ver a coluna final, que vem de [DECISAO-4](./DECISAO-4-ordem.md) → Resumo.

| # | O quê | Porquê | Itens | Quem | Bloqueio (DECISAO-4) |
|---|---|---|---|---|---|
| 1 | **Decidir o maestro** (ADR: Python + worker, TS desbloqueado, ou router do MCP) | Tudo o resto (delegação, nichos, HITL, tools) depende desta escolha | AU-07, EX-C2, AU-41 | **DEV** (Claude redige o ADR com as opções e os custos) | É a própria decisão (D1/D2) |
| 2 | **Consertar o RAG**: tabela canónica + retrieve que a lê + teste ingest→retrieve | O conhecimento ingerido é inacessível; é a base do grounding (menos tokens) | AU-19, AU-11, AU-06, B11 | **AMBOS** | Pode começar já (J3) |
| 3 | **Keep-alive**: secrets + tabela | Risco operacional imediato (pausa do Supabase), e é barato | AU-47, S15b | **DEV** → CLAUDE | Pode começar já (J1) |
| 4 | **Medir tokens**: somar por passo, persistir num ledger, aplicar orçamento | Sem medição, o objectivo n.º 1 é inverificável | AU-16, AU-49, D6, D5 | **CLAUDE** | **Em parte**: já no MCP (J6); no setup depende da D1 |
| 5 | **Provider de custo zero** (Gemini) | Premissa "custo zero"; hoje só OpenAI; reconciliar com o P6 arquivado | M6, P6 | **AMBOS** | Bloqueado (D1) |
| 6 | **Worker do modo `external`** (lê `request.json`, chama o LLM barato, escreve `result.json`, respeita HITL e orçamento) | Sem ele nenhum agente Python corre sozinho | AU-23 | **AMBOS** | Bloqueado (D1) |
| 7 | **Registo único de áreas** + router com confiança e fallback | Pré-requisito da delegação por área e dos 3 nichos | AU-33, AU-34, AU-26, AU-30 | **DEV** desenha → **CLAUDE** implementa | **Em parte**: os dados já (J5); o código depende da D2 |
| 8 | **Se o TS ficar:** corrigir Q1–Q4 e o teste falso-verde, depois correr o EX-B3 | 5 correcções pequenas que tornam o `/chat` testável | AU-13, AU-14, AU-15, AU-17, EX-B3 | **CLAUDE** (AU-13: AMBOS) | Bloqueado (D1) |
| 9 | **Decidir a memória L4** (própria pelo contrato vs mem0) | "Memória persistente" é pilar; decisão bloqueada desde 09-20 | S29, L6 | **DEV** | Bloqueado (D3) |
| 10 | **Teste e2e no CI** (TS `/chat` + testes lentos Python + ingest→retrieve) | Impede que as quebras voltem sem ninguém notar | L1, AU-09, AU-17 | **CLAUDE** | Bloqueado (D1) |

**Fora do top 10, mas urgente operacionalmente** (mesma origem): S20 (chave antiga na VM Oracle; o bridge-worker falha com 401) e S27 (limites do Oracle Free Tier), ambos DEV e fora do código. **Barato, com retorno imediato em tokens de bootstrap:** AU-45, AU-46, AU-37 e AU-12 (CLAUDE, cerca de 1–2 h). **Barato e fecha um alerta crítico:** AU-05 (CLAUDE, 5 min).

---

## 7. Ligação decisão → itens ("se… então…") — [ACRESCENTADO PELO AUDITOR]

> **Origem:** reorganização de [DECISAO-1](./DECISAO-1-runtimes.md) §1.2 e §1.4, [DECISAO-2](./DECISAO-2-maestro.md) §2.3 e §2.5, [DECISAO-3](./DECISAO-3-memoria.md) §3.3 e §3.4, e [DECISAO-4](./DECISAO-4-ordem.md) §4.1 e §4.2.
> **Não acrescenta factos novos:** só torna explícito o que já estava disperso. As 11 frentes da secção 4 mantêm-se **em qualquer cenário**.

### D1 — Runtimes

| Se a D1 for… | 1.º passo | Fica desbloqueado | Arquiva-se / deixa de ser preciso | Muda no top 10 |
|---|---|---|---|---|
| **VIA A — Python** | Worker mínimo do modo `external` com Gemini, **já com registo de tokens por passo** | Worker (AU-23); cliente Gemini em Python (M6 na forma Python); L4 em `runner/` (D3); AU-22, AU-09, AU-31, AU-32, A9; portar ~1,2k LOC do TS (LLM com tools, Planner, Router, `web`+`SsrfGuard`, `ToolPolicy`/`ToolExecutor`/`ToolRegistry`, `ActionReceipt`, opcional `DeliberationEngine`) | `apps/api`, `apps/web`, `packages/*` (≈17k LOC), CI TS, `Dockerfile`/`k8s`; deixam de ser precisos AU-13/14/15/17, AU-18/M4/M3 (versão TS), AU-01/02, M5/AU-38, AU-41, AU-48, S13 | **#6 worker sobe para #2**; #8 (`/chat`) desaparece; #2 RAG simplifica (o Python já tem `DATABASE_URL`/psycopg e pode ler o t6 directamente) |
| **VIA B — TypeScript** | Q1 → Q2 → Q3 → Q4 + teste que prove um `/chat` real (EX-B3) | AU-13/14/15/17; `GeminiProvider` TS (M6); HITL durável TS (M4) e retoma (AU-18); build (AU-01); M5/AU-38; AU-48; S13 | Runner Python, MCP stdio, scripts de ingest Python, CI Python; migrar ≈4,3k LOC + 195 testes; LangGraph Python → LangGraph.js | **#6 worker desaparece** (o Executor TS chama o LLM directamente); **#8 torna-se obrigatório e prioritário**; #2 RAG precisa de retrieve TS novo + escolha de pipeline |
| **VIA C — Os dois** | ADR de interface TS↔Python (quem chama quem, contrato, transporte) | Tudo o que A e B fazem nas partes que mantêm, mais a ponte | Nada se arquiva | #1 passa a incluir o contrato da ponte; #2 RAG corrigido nos dois lados; #6 necessário na metade Python; #8 obrigatório; a duplicação medida agrava-se |
| **VIA D — Maestro no MCP** *(ACRESCENTADO PELO AUDITOR em DECISAO-1)* | Registo de tokens no `runAgent`/`routeRequest` de produção + desenho do despacho MCP → `plan_runner` com worker Gemini | Reuso do router Gemini de produção; despacho por fila (padrão `code_tasks`) | O TS do setup (como na A); o `claude -p` pago e parado dá lugar a um worker Gemini | #1 fica quase resolvido (router existe); #2 exige uma RPC no Supabase que leia o t6; #4 faz-se no MCP; #6 ganha versão Gemini. **Contradiz** `ECOSYSTEM.md:9-10` (setup = núcleo) e **NÃO VERIFICADO** se o Vercel pode chamar um serviço externo |

### D2 — Maestro

| Se a D2 escolher… | O que muda | Itens afectados |
|---|---|---|
| **Um agente por pedido** (como o MCP) | O router basta; não é preciso planeador multi-passo | AU-26/AU-34 simplificam; o `Planner` deixa de ser necessário |
| **Plano multi-passo por área** (como o `Planner.ts`/`plan_runner`) | É preciso planeador + contrato de handoff + orçamento por passo | AU-20 (`toolsAllowed`), contrato de handoff, orçamento por área (D1+D2) |
| **Mapeamento M1** (campo `domain` na config) | Mantém-se o modelo actual; os horizontais continuam fora | AU-26 persiste |
| **Mapeamento M2** (`vertical:` no frontmatter) | Usa o que já existe em 30/35 | J4 obrigatório (descrições + 5 sem `vertical`) |
| **Mapeamento M3** (registo `areas.yaml`, recomendado) | Uma só fonte, validável em CI | J5 + validador (G1) |
| **Mapeamento M4** (Supabase) | Dinâmico e partilhável com o MCP | A tabela `projects` do MCP **NÃO foi relida** |
| **Routing C1 / C3** (palavras-chave / embeddings) | ~0 tokens por pedido | AU-34 (`routeWithConfidence` já existe) |
| **Routing C2** (LLM sobre a lista plana) | ~1,5k tokens por pedido, crescendo linearmente | Contra o objectivo n.º 1 quando os agentes crescerem |
| **Routing C4** (hierárquico híbrido, recomendado) | Área barata + LLM só com a lista da área | J4 + J5 como base |
| **Routing C5** (Planner escolhe área e passos) | O mais caro por pedido, mas com plano completo | — |

### D3 — Memória L4

| Se a D3 for… | O que muda | Itens afectados |
|---|---|---|
| **VIA A — L4 própria** (recomendada) | Módulo em `runner/plan_runner`; tabela no Supabase (ou SQLite, M-Q2); escrita explícita sem LLM; `status: candidate` + HITL | S29, AU-39; exige a D1 = A/C/D; fazer **depois** do J3 (RAG) |
| **VIA B — mem0** | Revogar em ADR a decisão de `FASE4-SINTESE.md:18`; usar `pgvector` (evita o `vecs`); `MEM0_TELEMETRY=false`; camada própria para `candidate`/`project`/`org`/tombstone; 1 LLM por `add()` salvo `infer=False` | J11 (spike) passa a critério de adopção |
| **VIA C — Adiar** | Continua o `MEMORY.md` manual + `project_state` (MCP) + L2 por run | "Memória persistente" fica por cumprir; o nicho trader e o maestro sem base de histórico |

---

## 8. Perguntas ao humano (reunidas num só sítio)

> **Origem:** [DECISAO-1](./DECISAO-1-runtimes.md) §1.3; [DECISAO-2](./DECISAO-2-maestro.md) §2.4; [DECISAO-3](./DECISAO-3-memoria.md) §3.4; [AUDIT-6](./AUDIT-6-lacunas.md) §6.5.

| # | Pergunta | Decisão | O que desbloqueia |
|---|---|---|---|
| **Q1** | **Quem vai chamar o sistema?** (IDE via MCP stdio, o `agent-network-mcp` em produção, uma app/frontend, clientes externos por HTTP) | D1 | Se a VIA A precisa de camada HTTP; peso da C/D |
| **Q2** | **Onde corre o motor em regime de serviço?** (VM Oracle, PC local, serverless) | D1 | Viabilidade da A/D; o `plan_runner` escreve em disco. VM: **NÃO VERIFICÁVEL daqui** (S27) |
| **Q3** | **O `agent-network-mcp` continua a ser a porta de entrada de produção?** | D1 | VIA D vs maestro neste repo |
| **Q4** | **A governança TS (18 módulos órfãos) tem valor de roadmap para ti?** | D1 | Arquivar (A) vs manter (C) |
| **ADR-M1** | Em que runtime vive o maestro? | D2 (depende da D1) | Código do router/planner |
| **ADR-M2** | Um agente por pedido, plano multi-passo por área, ou ambos por tipo de pedido? | D2 | Planeador, handoff, orçamento por passo |
| **ADR-M3** | Qual a lista de áreas de partida? (as 10 da AUDIT-3 §3.3 + 3 nichos, ou um corte menor) | D2 | J5 (registo) e nichos |
| **ADR-M4** | Onde vive o registo de áreas? (config versionada, Supabase ou frontmatter) | D2 | J5 |
| **ADR-M5** | O que acontece com baixa confiança? (clarificação, HITL, horizontal genérico, recusar) | D2 | Fallback (AU-30/AU-34) |
| **ADR-M6** | Orçamento e HITL são por área? (ex.: trader com limite por ordem e aprovação obrigatória) | D2 | Nicho financeiro (G1.5) |
| **ADR-M7** | Os 33 agentes de produção entram no registo como verticais plug-in ou ficam só no MCP? | D2 | Registo de áreas |
| **ADR-M8** | Qual a nomenclatura canónica dos agentes? (resolve as 3 de marketing, AU-36) | D2 | Migração de nomes |
| **M-Q1** | Extracção automática de factos (como o mem0) ou escrita explícita (`remember` por passo/HITL)? | D3 | A vs B na L4 |
| **M-Q2** | Storage da L4: Supabase (recomendado) ou SQLite local? (`FASE4-SINTESE.md:163`) | D3 | Módulo L4 |
| **M-Q3** | O teste de mem0 era para avaliar ou para adoptar? Se era adopção, é preciso revogar a FASE4 num ADR | D3 | J11 / VIA B |
| **Micro-decisão RAG** | Qual a tabela canónica: `knowledge_chunks_t6` ou `knowledge_chunks` (ou RPC por tabela)? | — (J3) | Correcção do RAG (AU-19) |
| **"Deep Hardness Obsidian"** | Não existe com esse nome no repo. Qual era a pretendida: **Obsidian/Logseq** (F10 = G4.1 = I8) ou **deepseek-harness / `dsh-long-memory`** (INIT-094 = EX-F8; opção do S29)? **NÃO VERIFICADO** | — | Inventário de ferramentas pendentes (AUDIT-6 §6.5) |

---

## 9. Índice-mestre resumido

> **Origem:** [AUDIT-COMPLETO.md](./AUDIT-COMPLETO.md) §7.2.
> **Nota explícita:** a linha completa, com "o que falta fazer", o bloqueio e a evidência, está na [AUDIT-5](./AUDIT-5-itens.md) §5.1 (AU) e §5.2/§5.4 (STATUS/EX). **Esta é uma visão de conjunto.**

### Achados novos (AU)

| ID | Título | Estado | Tipo | Sev. | Quem |
|---|---|---|---|---|---|
| AU-01 | Build TS de produção não funciona | NÃO INICIADO | FALTA-CONSTRUIR | Alta | AMBOS |
| AU-02 | Dockerfile quebrado; k8s só no papel | NÃO INICIADO | BUG | Média | DEV |
| AU-03 | `apps/web` morto | MORTO | FALTA-DECIDIR | Baixa | AMBOS |
| AU-04 | `packages/langgraph` morto | MORTO | FALTA-DECIDIR | Baixa | AMBOS |
| AU-05 | `tests/package.json` órfão; causa provável do Dependabot #11 | MORTO | BUG | Média | CLAUDE |
| AU-06 | Duas pipelines de ingestão | EM CURSO | FALTA-DECIDIR | Alta | DEV |
| AU-07 | Dois orquestradores sem ponte; maestro por escolher | NÃO INICIADO | FALTA-DECIDIR | **Crítica** | DEV |
| AU-08 | `.env.example` incompleto | NÃO INICIADO | DOC-ERRADO | Média | CLAUDE |
| AU-09 | CI Python ignora os testes lentos | NÃO INICIADO | FALTA-TESTE | Média | CLAUDE |
| AU-10 | `skills/claude` sem proveniência | NÃO INICIADO | DOC-ERRADO | Baixa | CLAUDE |
| AU-11 | Schema RAG em dois sítios | NÃO INICIADO | FALTA-DECIDIR | Média | DEV |
| AU-12 | STATUS de 95 KB / docs pesados | NÃO INICIADO | FALTA-DECIDIR | Média | AMBOS |
| AU-13 | Deliberação bloqueia 100% dos pedidos | NÃO INICIADO | BUG | **Crítica** | AMBOS |
| AU-14 | `update` sem `create` (P2025) | NÃO INICIADO | BUG | **Crítica** | CLAUDE |
| AU-15 | `finalOutput` vazio | NÃO INICIADO | BUG | Alta | CLAUDE |
| AU-16 | Tokens nunca somados | NÃO INICIADO | BUG | Alta | CLAUDE |
| AU-17 | Teste de integração falso-verde | NÃO INICIADO | FALTA-TESTE | Alta | CLAUDE |
| AU-18 | Sem retoma pós-HITL; polling em RAM | NÃO INICIADO | FALTA-CONSTRUIR | Alta | AMBOS |
| AU-19 | RAG: ingere t6, lê knowledge_chunks | NÃO INICIADO | BUG | **Crítica** | AMBOS |
| AU-20 | `toolsAllowed` sem fonte | NÃO INICIADO | FALTA-DECIDIR | Alta | AMBOS |
| AU-21 | Streaming só no papel | NÃO INICIADO | FALTA-CONSTRUIR | Baixa | CLAUDE |
| AU-22 | Campos de plano mortos | NÃO INICIADO | BUG | Média | CLAUDE |
| AU-23 | Sem worker para `external` | EM PR (2026-10-01, `feat/external-worker`; ver `docs/ops/WORKER-EXTERNAL.md`) | FALTA-CONSTRUIR → em revisão | Alta | AMBOS |
| AU-24 | Regex anti-injecção com falsos positivos | NÃO INICIADO | BUG | Baixa | CLAUDE |
| AU-25 | MCP `moderate` sem chave | EM CURSO | FALTA-DECIDIR | Baixa | DEV |
| AU-26 | 8 agentes sem domínio inalcançáveis | NÃO INICIADO | BUG | Alta | AMBOS |
| AU-27 | 22/24 sem `systemPrompt` | NÃO INICIADO | FALTA-CONSTRUIR | Média | AMBOS |
| AU-28 | F1 profiles não ligado | NÃO INICIADO | BUG | Média | CLAUDE |
| AU-29 | `PUBLIC_MODE` só serve `legal` | NÃO INICIADO | BUG | Média | DEV |
| AU-30 | `software`/jogos sem agentes → erro | NÃO INICIADO | BUG | Alta | CLAUDE |
| AU-31 | Resolução agente↔skill por nome | NÃO INICIADO | BUG | Média | CLAUDE |
| AU-32 | `design-flow.plan.yaml` sem `vertical` | NÃO INICIADO | BUG | Baixa | CLAUDE |
| AU-33 | 4 taxonomias de áreas | NÃO INICIADO | FALTA-DECIDIR | Alta | DEV |
| AU-34 | Router por primeiro match | NÃO INICIADO | BUG | Média | CLAUDE |
| AU-35 | Nichos sem área nem agentes | NÃO INICIADO | FALTA-CONSTRUIR | Alta | DEV |
| AU-36 | 3 nomenclaturas de marketing | NÃO INICIADO | FALTA-DECIDIR | Média | AMBOS |
| AU-37 | `CORE-MAPPING` desactualizado | NÃO INICIADO | DOC-ERRADO | Média | CLAUDE |
| AU-38 | 18 módulos órfãos + 3 timers | NÃO INICIADO | FALTA-DECIDIR | Média | DEV |
| AU-39 | Import/export HITL sem chamadores | NÃO INICIADO | FALTA-LIGAR | Média | CLAUDE |
| AU-40 | Repos de memória órfãos + Redis | NÃO INICIADO | FALTA-DECIDIR | Baixa | AMBOS |
| AU-41 | `MCPServer` TS não montado | NÃO INICIADO | FALTA-DECIDIR | Média | DEV |
| AU-42 | MFA fixo em código morto | NÃO INICIADO | BUG | Baixa | CLAUDE |
| AU-43 | `getHitlStats` MOCK | NÃO INICIADO | BUG | Baixa | CLAUDE |
| AU-44 | Análise de reels sem template nem ponte | NÃO INICIADO | FALTA-LIGAR | Média | AMBOS |
| AU-45 | Colisões de IDs | NÃO INICIADO | DOC-ERRADO | Média | CLAUDE |
| AU-46 | `OPEN-ITEMS.md` desactualizado | NÃO INICIADO | DOC-ERRADO | Média | CLAUDE |
| AU-47 | keep-alive 5/5 falhados | NÃO INICIADO | BUG | Alta | DEV |
| AU-48 | `query_database` SQL arbitrário (= A4) | EM CURSO | BUG | Média | CLAUDE |
| AU-49 | Orçamento de tokens não aplicado | NÃO INICIADO | FALTA-CONSTRUIR | Alta | CLAUDE |
| AU-50 | `agent_id` composto no t6 | NÃO INICIADO | BUG | Baixa | CLAUDE |

### Itens existentes em aberto (STATUS + EX)

| ID | Título | Estado | Tipo | Sev. | Quem |
|---|---|---|---|---|---|
| S29 | Memória L4 | NÃO INICIADO | FALTA-DECIDIR | Alta | DEV |
| M6 (=EX-B13) | GeminiProvider + Planner | NÃO INICIADO | FALTA-CONSTRUIR | Alta | AMBOS |
| M4 (=EX-B6) | HITL durável Postgres | NÃO INICIADO | FALTA-CONSTRUIR | Alta | AMBOS |
| M3 (=EX-B5) | e2e HITL Py→Node→Py | NÃO INICIADO | FALTA-CONSTRUIR | Alta | AMBOS |
| EX-B3 | `apps/api` contra infra real | NÃO INICIADO | FALTA-TESTE | Alta | AMBOS |
| EX-C2 | TS vs Python MCP | NÃO INICIADO | FALTA-DECIDIR | Alta | DEV |
| S20 | Chave antiga na VM Oracle | NÃO INICIADO (não verificável) | BUG | Alta | DEV |
| B3 / B4 | Trading / gamedev | NÃO INICIADO | FALTA-CONSTRUIR | Alta | DEV |
| D6 | `max_cost_usd` | NÃO INICIADO | FALTA-CONSTRUIR | Alta | CLAUDE |
| D5 / D7 | `model_tier`; dashboards reais | NÃO INICIADO | FALTA-CONSTRUIR/LIGAR | Média | CLAUDE |
| EX-B7 | Expor langgraph/edit no MCP | NÃO INICIADO | FALTA-LIGAR | Média | CLAUDE |
| E1–E7 | Conectores de ingestão | NÃO INICIADO | FALTA-DECIDIR | Média | AMBOS |
| A9 | Lockfile Python | NÃO INICIADO | FALTA-CONSTRUIR | Média | AMBOS |
| A13 | RBAC | NÃO INICIADO | FALTA-DECIDIR | Média | DEV |
| B2b / B2c | Ferramentas de segurança / triagem | EM CURSO | FALTA-TESTE / FALTA-DECIDIR | Média | AMBOS |
| S24 | Cobertura TS restante | EM CURSO | FALTA-TESTE | Média | CLAUDE |
| M5 (=EX-B12) | Mover órfãos (lista = AU-38) | NÃO INICIADO | FALTA-DECIDIR | Média | DEV |
| M7 | Piloto real de marketing | NÃO INICIADO | FALTA-DECIDIR | Média | DEV |
| S13 (=A23) | CORS | NÃO INICIADO | FALTA-DECIDIR | Média | DEV |
| S19 / S27 | Oracle (uso / limites) | NÃO INICIADO | FALTA-DECIDIR | Média | DEV |
| S32 / F7 | Descoberta entre agentes / PMO | NÃO INICIADO | FALTA-DECIDIR | Média | DEV |
| D3 / D4 | DeepEval / Ragas | NÃO INICIADO | FALTA-TESTE | Média | DEV / AMBOS |
| EX-C3 / EX-C4 / B16=G7 | AgentMesh / Cedar / receipts ADR-001 | NÃO INICIADO | FALTA-DECIDIR | Média/Baixa | DEV |
| INIT-093 / INIT-094 | google/skills / harnesses | NÃO INICIADO | FALTA-DECIDIR | Média/Baixa | AMBOS/CLAUDE |
| P6 | Multi-provider arquivado (contradiz M6) | OBSOLETO | DOC-ERRADO | Média | DEV |
| B11 / B12 | Script `knowledge_sources` / `knowledge_log` | NÃO INICIADO / EM CURSO | FALTA-CONSTRUIR / DOC-ERRADO | Média/Baixa | CLAUDE |
| S5 | Consistência no CI (já feito, não fechado) | FECHADO-VERIFICADO | DOC-ERRADO | Baixa | CLAUDE |
| S14, S17, S21, S28, B1, B5, B6, G6, A1b, A12, A15, A19 | (ver AUDIT-5 §5.2, §5.4) | NÃO INICIADO / OBSOLETO | vários | Baixa | DEV/CLAUDE |
| G1.1–G1.14, G2.1–G2.4, G3.x, G4.x, H1–H4, I1–I11, J1–J7 | Backlog de nichos e ferramentas (título a título em AUDIT-5 §5.4) | NÃO INICIADO / OBSOLETO (J) | FALTA-DECIDIR | Baixa–Alta | DEV |

### "Done" reverificados

| Grupo | IDs | Estado |
|---|---|---|
| **Só no papel** | **C8, keep-alive, S33, S15b** | **FECHADO-SÓ-NO-PAPEL** |
| Verificados | S1, S2a, S2b-1..3, S3, S4, S4b, S6a, S7, S8, S9, S10\*, S11\*, S12, S15a, S18, S22, S23, S30, S31, S34\*, S35, S36\*, M1, M2\*, M8\*, B2\*, B7, B8, B9, B10, B13\*, B14, B15, B17\*, B18, C1, C2, C5, C8a-1, C8a-2, C8b, C8c, C8d, C8e\*, G2, G3, G4, G5, G-skill-1..5\* | FECHADO-VERIFICADO (\* = com ressalva registada na AUDIT-5 §5.3) |
| Não verificáveis daqui | S16, C3, C6, C7 | FECHADO — NÃO VERIFICÁVEL |

A checklist de segurança de 20 itens reverificada está na [AUDIT-5](./AUDIT-5-itens.md) §5.5.

---

## 10. As lacunas críticas e os passos que faltam para ter "pernas"

> **Origem:** [AUDIT-COMPLETO.md](./AUDIT-COMPLETO.md) → "O que falta para ter 'pernas'"; lacunas estruturais completas (L1–L10) em [AUDIT-6](./AUDIT-6-lacunas.md) §6.1.

### As 4 junções partidas (origem: [AUDIT-6](./AUDIT-6-lacunas.md) → Resumo)

| # | Junção partida | Achado |
|---|---|---|
| 1 | O pedido nunca chega ao LLM | AU-13 |
| 2 | O RAG escreve numa tabela e lê de outra | AU-19 |
| 3 | Há dois maestros sem ponte | AU-07 |
| 4 | Os tokens nunca são contados | AU-16 |

### As 3 decisões

| # | Decisão | Onde se decide |
|---|---|---|
| 1 | Qual é o maestro | [DECISAO-1](./DECISAO-1-runtimes.md) + [DECISAO-2](./DECISAO-2-maestro.md) |
| 2 | Qual é a tabela canónica do RAG | Micro-decisão (secção 8); [AUDIT-2](./AUDIT-2-cadeia.md) §2.4 |
| 3 | Como se implementa a memória L4 | [DECISAO-3](./DECISAO-3-memoria.md) |

### As 4 construções pequenas

| # | Construção | Itens |
|---|---|---|
| 1 | Worker de custo zero para o modo `external` | AU-23 (depende da D1) |
| 2 | Ledger de tokens com orçamento aplicado | AU-16, AU-49, D6 (começa já no MCP, J6) |
| 3 | Registo único de áreas | AU-33 (os dados começam já, J5) |
| 4 | Teste end-to-end no CI | L1, AU-09, AU-17 |

Com isto, os nichos (trader, jogos, segurança) passam a ser **conteúdo** (agentes, skills e tools por área) e deixam de ser infraestrutura por construir.

### As 10 lacunas estruturais (lista completa em [AUDIT-6](./AUDIT-6-lacunas.md) §6.1)

| # | Lacuna | Impacto |
|---|---|---|
| L1 | Não há teste end-to-end | Crítico |
| L2 | "Auth é `return true`": refutado no caminho real; a lacuna é de identidade/autorização | Médio |
| L3 | HITL não durável no caminho TS | Crítico |
| L4 | `toolsAllowed` nunca gerado | Alto |
| L5 | Ingestão de conhecimento fragmentada | Crítico |
| L6 | Memória persistente não unificada | Alto |
| L7 | Não existe um maestro [ACRESCENTADO] | Crítico |
| L8 | Tokens não medidos [ACRESCENTADO] | Crítico |
| L9 | Nenhum agente corre sozinho [ACRESCENTADO] | Crítico |
| L10 | Infra de persistência frágil [ACRESCENTADO] | Alto |

---

## 11. Contagens e estado

> **Origem:** [AUDIT-5-itens.md](./AUDIT-5-itens.md) → Resumo e "Contagens"; atribuição em [AUDIT-COMPLETO](./AUDIT-COMPLETO.md) §7.1.

**~175 itens inventariados:**
- 96 IDs do `STATUS.md`;
- os itens do `OPEN-ITEMS.md` e dos grupos G–J do `EXECUTION-PROMPTS.md`;
- 20 da checklist de segurança;
- **50 achados novos (AU-01…AU-50)**.

| Estado | N.º aprox. |
|---|---|
| FECHADO-VERIFICADO | ~55 |
| FECHADO-SÓ-NO-PAPEL | **4** (C8, keep-alive, S33, S15b) |
| FECHADO — NÃO VERIFICÁVEL daqui | ~6 |
| EM CURSO | ~9 |
| NÃO INICIADO | ~85 (incluindo 44 dos 50 AU) |
| MORTO | 3 (AU-03, AU-04, AU-05) |
| OBSOLETO | ~17 (P1–P6, J1–J7, A15, A19, S25 e N/A da checklist) |

*(Contagens aproximadas porque há itens duplicados entre séries, marcados `=X`; cada item conta uma vez.)*

### Os 4 "Done" que caíram para "só no papel"

| Item | Porquê | Origem |
|---|---|---|
| **C8** | "Pipeline completo markdown→…→retrieve": o retrieve não lê o que é ingerido; só 1 das 33 fontes coincide | [AUDIT-2](./AUDIT-2-cadeia.md) §2.4 |
| **keep-alive** | Nunca funcionou: 5/5 runs falhados, secrets vazias, tabela inexistente | [AUDIT-5](./AUDIT-5-itens.md) AU-47 |
| **S33** | "Tools chegam a um LLM real": `toolsAllowed` sem fonte e o Executor nunca é alcançado | [AUDIT-2](./AUDIT-2-cadeia.md) §2.2 |
| **S15b** | Afirma que o keep-alive funciona, o que é falso | [AUDIT-5](./AUDIT-5-itens.md) §5.3 |

### Atribuição dos achados AU

CLAUDE **25** · DEV **11** · AMBOS **14** (contagem exacta). Itens abertos do STATUS/EX sem G–J ≈ CLAUDE 11 · DEV 34 · AMBOS 12 (contagem manual). Grupos G–J (~45 linhas): todos DEV.

---

## 12. Links para todos os documentos

| Documento | Uma linha | Commit |
|---|---|---|
| [AUDIT-1-estrutura.md](./AUDIT-1-estrutura.md) | Estrutura, pacotes, build verificado, R1–R13 | `fb1ba73` |
| [AUDIT-2-cadeia.md](./AUDIT-2-cadeia.md) | Cadeia de execução com sondas, motor Python, RAG ao vivo | `96aa9ec` |
| [AUDIT-3-agentes.md](./AUDIT-3-agentes.md) | Agentes instanciados vs desenhados, delegação | `dcca4d0` |
| [AUDIT-4-modulos.md](./AUDIT-4-modulos.md) | MOCK/INCOMPLETO/órfãos, contradições | `ec3b637` |
| [AUDIT-5-itens.md](./AUDIT-5-itens.md) | Inventário completo, AU-01…50, checklist de segurança | `e3cc0ee` (+ `8991c27` correcção Dependabot #11) |
| [AUDIT-6-lacunas.md](./AUDIT-6-lacunas.md) | Lacunas, retificações, inclusões, ferramentas | `b2ae5e9` |
| [AUDIT-COMPLETO.md](./AUDIT-COMPLETO.md) | Consolidação da Fase 1 | `edd55b5` (+ `8991c27`) |
| [DECISAO-1-runtimes.md](./DECISAO-1-runtimes.md) | Vias A/B/C/D | `5820be8` |
| [DECISAO-2-maestro.md](./DECISAO-2-maestro.md) | Maestro e perguntas ADR | `d298fe3` |
| [DECISAO-3-memoria.md](./DECISAO-3-memoria.md) | Memória L4 vs mem0 | `aa6747a` |
| [DECISAO-4-ordem.md](./DECISAO-4-ordem.md) | Ordem de ataque | `706a0fa` |
| [DECISOES-COMPLETO.md](./DECISOES-COMPLETO.md) | Consolidação da Fase 2 | `e061f87` |

---

## 13. Decisões tomadas vs. em aberto (acrescentado em 2026-09-30)

### 13.1 TOMADAS (não reabrir)

| Decisão | Conteúdo | Registo |
|---|---|---|
| **D1 — Runtime** | Núcleo = Python (`runner/plan_runner`). TS **arquivado, não apagado**. O `agent-network-mcp` continua a ser a porta de entrada de produção. Responde Q1, Q3, Q4 e ADR-M1 (runtime) | Grok, 2026-09-30 |
| **D2 — Maestro** | Router hierárquico híbrido sobre `config/areas.yaml` versionado e validado em CI. Responde ADR-M3 (as 10 áreas) e ADR-M4 (config versionada) | Grok; `config/areas.yaml` |
| **D3 — Memória L4** | L4 própria no `plan_runner` sobre Supabase. Responde M-Q2 (Supabase). Spike mem0 = **avaliação, não adopção** (M-Q3). **Escrita explícita** (`remember`) por omissão (M-Q1) | Grok |
| **RAG canónico** | Tabela canónica = **`knowledge_chunks`**; `knowledge_chunks_t6` **abandonada** (fecha a micro-decisão do J3) | Grok |
| **`areas.yaml` v1** | 10 áreas: software, marketing, legal, ops, research, finance, gamedev, security, docs, horizontal. Os 35 agentes `.agent.md` ficam cada um em exactamente uma área | `config/areas.yaml` |
| **HITL por área** (parte do ADR-M6) | `hitl: required` em legal, finance e security; `budget: null` até existir o ledger J6 | `config/areas.yaml` |
| **Keep-alive** | Precisa de **duas condições**: secrets `SUPABASE_URL`/`SUPABASE_ANON_KEY` **+** tabela `keepalive` | J1 / AU-47 |
| **AU-13** (escala da deliberação) | Corrige-se **quando se for ligar a deliberação**, não antes | Grok; [ADR-META-AGENTS](../architecture/adr/ADR-META-AGENTS.md) §6 |
| **DB Plano B** | Ficar no Supabase agora. Plano B managed = **Neon**; plano B local-first = **Postgres+pgvector na Oracle**. 4 gatilhos de saída definidos | [ADR-DB-PLAN-B](../architecture/adr/ADR-DB-PLAN-B.md) |
| **Meta-agentes: modo / forma / participantes** | O Dev não respondeu; executaram-se as recomendadas A/A/A: modo assistido, conselhos por tipo de decisão, participantes mistos | [ADR-META-AGENTS](../architecture/adr/ADR-META-AGENTS.md) §2–3 |
| **Campo `kind` no agente** | `internal \| external_ai \| meta`, por omissão `internal`. Está no agente, não na área | `agents/README.md`; `packages/shared/src/types/agent.ts` |

### 13.2 EM ABERTO — cada uma com opção recomendada por omissão (N = 7 dias)

| # | Decisão | Opção A | Opção B | Opção C | RECOMENDADA |
|---|---|---|---|---|---|
| E1 | **Q2 — Onde corre o motor em serviço** | VM Oracle. Custo US$ 0. Serviço 24/7, mas exige S20 (chave antiga) + S27 (acesso) | PC local. Custo US$ 0. Zero operação; só corre com o PC ligado | Serverless (Vercel). Custo US$ 0–20. Incompatível: o `plan_runner` escreve em disco | **B** até o worker mínimo correr; depois A, quando S20 e S27 fecharem. O motor ainda não tem worker, e a VM tem pendências de segurança |
| E2 | **ADR-M1 — Onde vive o router (área → agente)** | No MCP (JS) a ler `areas.yaml`. Custo baixo. Duas fontes de verdade (JS + YAML de outro repo) | No `plan_runner` (Python); o MCP delega. Custo médio. Uma fonte, testável com a suíte do runner | Área no MCP, agente no Python. Custo alto. Duas metades para manter | **B**: segue a D1 (núcleo Python) e o `areas.yaml` vive neste repo |
| E3 | **ADR-M2 — Um agente por pedido ou plano** | Sempre 1 agente. Simples; perde pedidos multi-passo | Sempre plano. Custo em tokens por pedido simples | 1 agente por omissão; plano quando o `meta.planejador` classificar o pedido como multi-passo | **C**: é o padrão do MCP (1 agente) e do `plan_runner` (plano) sem obrigar a escolher |
| E4 | **ADR-M5 — Baixa confiança no routing** | Pedir clarificação ao utilizador. Custo: 1 volta | HITL. Custo: tempo do Dev | Encaminhar para um horizontal genérico (`meta.planejador`). Custo: resposta menos especializada | **A**, e **B** nas áreas com `hitl: required`. Não se inventa especialista |
| E5 | **ADR-M7 — Os 33 agentes do MCP de produção no registo** | Entram na v2, depois de existir o validador (E7) | Entram já na v1 | Nunca; o MCP mantém o seu catálogo | **A**: sem validador, 33 IDs de outro repo apodreciam sem aviso |
| E6 | **ADR-M8 — Nomenclatura canónica** | `vertical.nome` do frontmatter `.agent.md` (ex.: `marketing.critic`) | IDs do MCP (`lib/agents.js`) | Esquema novo | **A**: já é o usado em `areas.yaml` e no runtime Python (D1) |
| E7 | **Validação do `areas.yaml` em CI** (exigida pela D2) | Script Python pequeno + passo no `runner-tests.yml`. Custo ~1h. Verifica IDs e cobertura | Script TS em `packages/scripts`. Contradiz a D1 (TS arquivado) | Só um hook local de pre-commit. Não protege PRs | **A — EXECUTADA**: `runner/plan_runner/areas.py` (+ `runner/tests/test_areas.py`), passo no `runner-tests.yml`, que passa a correr também quando mudam `agents/**` ou `config/areas.yaml`. Antes, a validação tinha sido feita à mão em 2026-09-30: 10 áreas, 35/35 agentes, 0 IDs desconhecidos, 0 duplicados |
| E8 | **Trader** (não é uma das 10 áreas) | Trading como parte de `finance`: G1/B3 como agentes de `finance`, `hitl: required`, *paper trading* por omissão | Área própria `trading` na v2 | Fora de escopo | **A**: evita uma área vazia; o gate de risco (G1.5) usa o `hitl` da área |
| E9 | **Cyber** vs **security** | `cyber` = `security` (o `security_auditor` já se declara "agente de cibersegurança defensivo") | Área `cyber` separada | Sub-área de `security` | **A**: não há código nem desenho distinto para "cyber" (T1.1) |
| E10 | **"Deep Hardness Obsidian"** | Obsidian/Logseq como vista humana da memória (F10 = G4.1 = I8), fase posterior | deepseek-harness / `dsh-long-memory` como memória longa | Descartar | **A**: a função de B (memória longa) já é coberta pela L4 própria (D3); Obsidian não compete com ela |
| E11 | **Estrutura existente de security/finance (T1.1)** | Integrar já no `areas.yaml` | Manter como referência | Avaliar em item próprio | **A** para `meta.security-auditor` e `gestao.contabilidade` (prompt real; **já integrados**). **B** para `financial-analyst` do TS (casca: só `description`, `config/agents.config.ts:69-73`) |
| J5-b | **`councils.yaml` v0** (config dos painéis de conselho). *Acrescentado 2026-09-30* | Criar agora, no Bloco A. Custo: ~30 min. Consequência: config sem consumidor, que apodrece até existir runtime | Criar no início da Fase 1 (depois de AU-13 + motor mínimo). Custo: 0 esperar. Consequência: nasce junto do código que a lê | Criar só na Fase 2 (multi-IA). Custo: 0. Consequência: atrasa o conselho interno da Fase 1, que precisa de painéis | **B**: o desenho está pronto (ADR-META-AGENTS §13), mas o runtime ainda não existe; criar agora seria config sem consumidor. Custo zero de esperar. **Prazo: 7 dias** |
| J5-c | **Implementar o `CouncilSession` (LangGraph)**. *Acrescentado 2026-09-30* | Implementar agora, antes do Bloco A. Custo: dias. Consequência: vai contra a ordem (DECISAO-4 §4.4) e fica sem motor nem ledger por baixo | Implementar no **Bloco C**, depois de AU-13 + motor mínimo. Critério de done: 1 conselho interno end-to-end + HITL + ledger + veredicto `candidate` persistido em L4. Custo: dias, no momento certo. Consequência: fecha a Fase 1 | Guardar como desenho, sem agendar. Custo: 0. Consequência: adiamento indefinido da visão | **B**: é o passo natural da Fase 1 e tem critério de done claro. A vai contra a ordem; C é adiar indefinidamente. **Prazo: 7 dias** |
| E12 | **Onde vive o `councils.yaml`**. *Acrescentado 2026-09-30* | `config/councils.yaml`, na mesma pasta do `areas.yaml`. Custo: 0. Consequência: lido pelo mesmo validador de CI (E7) | `docs/architecture/councils.yaml`. Custo: 0. Consequência: config de runtime misturada com documentação | Dentro do `areas.yaml` (secção `councils:`). Custo: 0. Consequência: acopla painéis (transversais) a áreas | **A**: é config de runtime, não documentação; fica ao lado do `areas.yaml` e é lido pelo mesmo validador (E7). **Prazo: 7 dias** |
| E13 | **Colisão de nomes: camadas de controlo L0–L3** (ADR-META-AGENTS §9) vs **camadas de memória L0–L6** (`docs/architecture/memory/layers.md:1`). *Acrescentado pelo auditor* | Renomear as de controlo para **C0–C3**. Custo: ~10 min (só o ADR). Consequência: "L4" passa a significar só memória | Manter L0–L3 com a nota de desambiguação. Custo: 0. Consequência: ambiguidade permanente em docs e prompts | Renomear as de memória. Custo: alto (várias docs). Consequência: parte referências existentes | **A**: é a mudança mais barata que elimina a ambiguidade, e o ADR é o único sítio que usa L0–L3 de controlo. **Prazo: 7 dias** ✅ **Executada 2026-09-30:** camadas de controlo → C0–C3. |
| E14 | **Nome do estado consolidado da L4**: o brief diz `committed`; o contrato diz `active` (`docs/architecture/memory/contracts.md:29`). *Acrescentado pelo auditor* | Usar `active` (o do contrato). Custo: 0. Consequência: o ADR e o contrato ficam iguais | Mudar o contrato para `committed`. Custo: pequeno. Consequência: altera um contrato já referido noutras docs | Aceitar os dois como sinónimos. Custo: 0. Consequência: dois nomes para o mesmo estado | **A**: o contrato é a fonte (DECISAO-3); o ADR já diz "committed = `active`". **Prazo: 7 dias** ✅ **Executada 2026-09-30:** o ADR usa só `active`; contrato intacto. |
| E15 | **Proveniência do esboço `CouncilSession` e do `councils.yaml` v0**: o "esboço já produzido" não existe em ficheiro; foi reconstituído do brief. *Acrescentado pelo auditor* | Manter a reconstituição (ADR §12–13). Custo: 0. Consequência: pode divergir em detalhe do original | O Dev cola o original e substitui-se. Custo: ~5 min do Dev. Consequência: fidelidade total | Retirar os esboços do ADR. Custo: 0. Consequência: perde-se o desenho | **A**, e B quando o Dev tiver o original à mão. A reconstituição segue a especificação do brief; os IDs foram validados contra o `areas.yaml`. **Prazo: 7 dias** |

---

## 14. EXTRAIR (não adoptar) — análise de repos em 4 níveis (acrescentado em 2026-09-30)

> **Crédito:** transcrição da análise do **Grok**, "Análise profunda do plano de acção × repos padrão ouro". A classificação é dele. As notas `[ACRESCENTADO PELO AUDITOR]` são verificações locais.

### 14.1 ADOPTAR (dependência de produção, já alinhada)

| Repo / ferramenta | Papel | Nota `[ACRESCENTADO PELO AUDITOR]` |
|---|---|---|
| **LangGraph** + **langgraph-checkpoint-postgres** (MIT) | Infra de fluxo e HITL durável. **Já usado** no `plan_runner`: aprofundar, não adoptar de novo | `langgraph>=0.6.11` em `runner/requirements-langgraph.txt:3`. O checkpointer hoje é **SQLite** (`:4`; `langgraph_engine.py:12,224`); o Postgres é **dependência nova** |
| **modelcontextprotocol/python-sdk** | Base do `mcp_plan_runner` | Verificado: `mcp==1.30.0` em `runner/requirements.txt:4` |
| **pgvector** (extensão + imagem `pgvector/pgvector`) | Vectores no Postgres | Verificado: imagem no CI (`.github/workflows/ci.yml:30`); extensão `vector 0.8.2` no Supabase (SQL, 2026-09-30) |
| **gitleaks/gitleaks** + **semgrep/semgrep** | Segurança de CI (J10) | **Não** estão no CI hoje; só são corridos à mão pelo `security_auditor` (`agents/meta/security_auditor.agent.md`) |
| **trufflehog** (opcional) | Referência adicional para segredos | — |

### 14.2 EXTRAIR (ler padrões, NÃO adoptar como dependência)

| Repo | O que se extrai | Nota |
|---|---|---|
| **mem0** | Padrões ADD/UPDATE/DELETE de memória; spike J11. **Não** é dependência | D3; [DECISAO-3](./DECISAO-3-memoria.md) §3.3 |
| **karpathy/llm-council** | Protocolo em 3 estágios: parallel → blind peer → chairman. Extrair, não adoptar o stack | [ADR-META-AGENTS](../architecture/adr/ADR-META-AGENTS.md) §5 |
| **HKUDS/LightRAG** | GraphRAG leve; só na Fase 2; versão ≥ 1.5.5 (CVEs) | Versão/CVEs **NÃO VERIFICADOS** nesta sessão |

### 14.3 REFERÊNCIA (ideias, não código)

| Repo | Ideia |
|---|---|
| **Microsoft Conductor** (workflows YAML) | Formato para o `areas.yaml` |
| **aurelio-labs/semantic-router** | Routing barato por embeddings (área antes de LLM). Actividade do repo **NÃO VERIFICADA** |
| **Cognee / Graphiti / Microsoft GraphRAG** | Padrões de memória e recuperação *multi-hop* |

### 14.4 REJEITAR como núcleo

| Repo | Porquê |
|---|---|
| **CrewAI / AutoGen** | Outro modelo (crew/chat). O AutoGen está em manutenção. Não substituem o `plan_runner` |
| **Supabase self-host completo na Oracle (12 GB)** | Pesado para o que se usa |

### 14.5 PLANO B DB (contingência, não "extrair")

| Opção | Nota |
|---|---|
| **Neon** (managed, sem a pausa de 7 dias) | Recomendada quando um gatilho disparar, [ADR-DB-PLAN-B](../architecture/adr/ADR-DB-PLAN-B.md) §3 |
| **Postgres+pgvector em Docker na Oracle** (local-first) | Checklist de capacidade em [ADR-DB-PLAN-B](../architecture/adr/ADR-DB-PLAN-B.md) §4 |

---

## 15. Protocolo meta-agentes (Fase 2) — resumo do ADR (acrescentado em 2026-09-30)

> Fonte: [ADR-META-AGENTS](../architecture/adr/ADR-META-AGENTS.md). **Visão registada, nada implementado.**

- **Objectivo:** deliberação entre agentes e, na Fase 2, entre várias IAs (Claude, Grok, outras), cada uma representada por um agente-maestro, sem o Dev a fazer de pombo-correio.
- **Fase 1:** deliberação interna, reimplementada em Python no `plan_runner` a partir das ideias do `DeliberationEngine`/`ArchitectureCouncil`. **Não é drop-in do TS**, que está arquivado (D1).
- **Fase 2:** mesmos protocolos, com participantes `kind: external_ai`.
- **Protocolo (extraído do llm-council):**
  1. **parallel** — cada participante responde sozinho;
  2. **blind peer** — crítica anonimizada;
  3. **chairman** — síntese com dissent + próximo passo.
- **Modo, forma e participantes:** assistido (o Dev aprova o commit final) · conselhos por tipo de decisão (architecture, security, product) · participantes mistos.
- **Pré-requisitos, por ordem:** motor mínimo a correr → AU-13 corrigido ao ligar a deliberação → conselho interno a funcionar → **ledger de tokens (J6)** → Fase 2.
- **Não-objectivos:** não substitui o maestro; não é um orquestrador paralelo.
