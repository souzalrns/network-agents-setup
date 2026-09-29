# DECISÃO 4 — Ordem de ataque

> **Base:** AUDIT-COMPLETO (top 10), DECISAO-1/2/3. **Data:** 2026-09-29.
> **Critério usado:** um item "pode começar agora" se **(a)** o seu valor se mantém em **todas** as vias da Decisão 1 (A/B/C/D) e **(b)** não precisa de nenhuma das decisões 1–3. Se só precisa de uma micro-decisão local (ex.: que tabela é canónica), fica marcado "agora, com micro-decisão".

## Resumo

Do top 10 da Fase 1, as decisões 1–3 bloqueiam **5 itens por inteiro** (#5 provider, #6 worker, #8 `/chat`, #9 L4, #10 e2e) e **2 em parte** (#4 tokens, #7 áreas); o #1 é a própria decisão. Há, mesmo assim, **11 frentes que podem começar hoje** sem desperdício em nenhum cenário. As mais valiosas:

- keep-alive (risco operacional);
- RAG, depois de escolher a tabela;
- descrições + registo de áreas como **dados** (servem qualquer router);
- ledger de tokens **no MCP de produção**;
- higiene de docs e o alerta Dependabot.

**Correcção ao brief:** "corrigir as 4 quebras do `/chat`" **não** é independente. Só tem valor nas vias B ou C; nas vias A e D o código TS é arquivado (DECISAO-1 §1.4). "Medir tokens" é independente **se for feito no MCP de produção** (existe em qualquer via), não no TS do setup.

---

## 4.1 Primeira coisa a fazer em cada cenário `[PEDIDO]`

| Via (Decisão 1) | 1.º passo | Porquê este primeiro | Evidência |
|---|---|---|---|
| **A — Python** | **Worker mínimo do modo `external` com Gemini** (lê `request.json` + `SKILL.md`/`AGENT.md`, escreve `result.json`), **já com registo de tokens por passo** | Sem worker nenhum passo Python executa; medir desde o 1.º dia evita fazer retrofit | `executor.py:117-119`; AU-23; AU-16 |
| **B — TypeScript** | **Q1 → Q2 → Q3 → Q4** (escala da deliberação, `create` da execução, `finalOutput`, tokens) **+ teste que prove um `/chat` real** (EX-B3) | Hoje nenhum pedido chega ao LLM | AUDIT-2 Q1–Q4 |
| **C — os dois** | **ADR de interface TS↔Python** (quem chama quem, contrato, transporte) antes de mexer em código | Sem contrato, qualquer correcção num lado diverge do outro (já aconteceu com o HITL, M2) | `STATUS.md:74` (tradução `approved↔approve`) |
| **D — maestro no MCP** | **Registo de tokens no `runAgent`/`routeRequest` de produção** + desenho do despacho MCP → `plan_runner` com worker Gemini (substituir o `claude -p` pago e parado) | Reaproveita o único router real; o worker actual custa US$ e está parado desde 09-09 | `agentRuntime.js:56-59,62-84`; SELECT `code_tasks` |

Seja qual for a via, **as decisões 2 (maestro) e 3 (L4) só se executam depois da 1**. A L4 é recomendada em Python (DECISAO-3), o que a torna natural nas vias A, C e D.

---

## 4.2 Itens bloqueados enquanto as decisões 1–3 não forem tomadas `[PEDIDO]`

| Item | Bloqueado por | Porquê | Evidência |
|---|---|---|---|
| AU-13/14/15/17 (quebras do `/chat` + teste) | **D1** | Só valem em B ou C | DECISAO-1 §1.4 |
| AU-18 / M4 / M3 (HITL TS durável e retoma) | **D1** | Na A e na D usa-se o HITL Python, que já é durável | AUDIT-2 Y5 |
| AU-23 (worker `external`) | **D1** | É central na A, C e D; desnecessário na B | DECISAO-1 §1.4 |
| M6 (provider Gemini) | **D1** | A forma muda: cliente Python (A) vs `GeminiProvider` TS (B) | `LLMService.ts:98` |
| AU-01/AU-02 (build TS, Docker, k8s) | **D1** | Só relevantes se o TS ficar | AUDIT-1 §1.4 |
| AU-38 / M5 (mover 18 órfãos) | **D1** | Na A arquiva-se o TS inteiro, tornando o M5 desnecessário | AUDIT-4 §4.4 |
| AU-41 / EX-C2 (montar ou descontinuar `MCPServer` TS) | **D1** | Idem | — |
| AU-48 (`query_database` read-only), S13 (CORS) | **D1** | Só TS | — |
| AU-20 (fonte de `toolsAllowed`) | **D1 + D2** | A fonte depende do runtime e do contrato de handoff | AUDIT-2 §2.2 |
| AU-26/AU-30/AU-34 (código do router/planner) | **D2** | O mecanismo de routing é o ADR do maestro | DECISAO-2 |
| AU-35, B3, B4, G1.x/G2.x de implementação (nichos) | **D2** (+ escopo) | Os nichos entram como áreas no registo | DECISAO-2 R8 |
| S29 / AU-39 / L4 | **D3** (+ D1) | Storage e modelo de escrita por decidir | DECISAO-3 M-Q1..Q3 |
| AU-22 (campos de plano mortos no Python) | **D1** | Só vale se o Python ficar (A/C/D) | AUDIT-2 Y7–Y9 |
| AU-09, AU-31, AU-32, A9 (CI lento, resolução skill↔agente, template design, lockfile Py) | **D1** (fraco) | Valem em A/C/D; perdem-se na B | — |

---

## 4.3 Itens que podem avançar JÁ, independentemente das decisões `[PEDIDO]`

| # | Item | Porquê é independente | Quem | Evidência |
|---|---|---|---|---|
| J1 | **AU-47 keep-alive** (secrets `SUPABASE_URL`/`SUPABASE_ANON_KEY` + tabela `keepalive`) | Protege o Supabase que **todas** as vias usam | DEV (secrets) → CLAUDE (SQL + verificar run verde) | 5/5 runs ❌ |
| J2 | **S20 chave antiga na VM Oracle** | Operacional; o bridge-worker está parado | DEV | `STATUS.md:41` |
| J3 | **AU-19 RAG**, com micro-decisão "tabela canónica" (`knowledge_chunks_t6` vs `knowledge_chunks`, ou RPC por tabela) | Todas as vias precisam de o retrieve ler o que se ingere; a correcção pode ficar na RPC do Supabase, que é independente do runtime | AMBOS | AUDIT-2 §2.4 |
| J4 | **`description:` nos 35 `agents/*.agent.md`** + validação de `vertical:` nos 5 que faltam | Qualquer router (TS, Python, MCP, embeddings ou LLM) precisa de descrições; hoje 0/35 as têm | CLAUDE redige, DEV revê | DECISAO-2 §2.1 |
| J5 | **Registo de áreas como dados** (`areas.yaml`: id, descrição, agentes, horizontais) **sem código de router** | Dados reutilizáveis por qualquer mecanismo; precisa só da lista de áreas (ADR-M3, que é decisão de escopo e não de runtime) | DEV decide a lista, CLAUDE escreve | DECISAO-2 §2.5 |
| J6 | **Ledger de tokens no MCP de produção** (`usageMetadata` do Gemini em `callGemini`; guardar por agente/pedido) | O MCP de produção existe em todas as vias; hoje ignora o uso (`agentRuntime.js:56-59`). Dá a **linha de base** do objectivo n.º 1 | AMBOS (outro repo) | `agentRuntime.js:32-60` |
| J7 | **AU-05** apagar o `tests/package.json` órfão (causa provável do Dependabot #11 crítico) | Morto em qualquer via | CLAUDE | AUDIT-5 AU-05 |
| J8 | **Higiene de docs:** AU-45 (colisões de IDs), AU-46 (regenerar OPEN-ITEMS), AU-37 (errata CORE-MAPPING), AU-12 (partir o STATUS de 95 KB), AU-08 (`.env.example`) | Independente; reduz tokens em cada bootstrap | CLAUDE | AUDIT-5 |
| J9 | **Pesquisas de nicho** G1.1 (trading/simulação) e G2.1 (gamedev), só pesquisa | Informam D2 (áreas) sem depender dela | CLAUDE | `EXECUTION-PROMPTS.md:1618,1896` |
| J10 | **Gate de segurança em CI** (gitleaks/semgrep, já listados no B2b) | Protege qualquer código que fique | AMBOS | `STATUS.md:28` |
| J11 | **Spike mem0 vs L4** (1–2 dias, medir tokens por `add()`) | **Informa** a D3 em vez de depender dela | AMBOS | DECISAO-3 §3.4 |

---

## 4.4 Lista final `[PEDIDO]`

### PODE COMEÇAR AGORA

| Ordem sugerida | Item | Quem |
|---|---|---|
| 1 | J1 keep-alive | DEV → CLAUDE |
| 2 | J7 apagar o `tests/package.json` (Dependabot #11) | CLAUDE |
| 3 | J3 RAG (depois da micro-decisão da tabela) | AMBOS |
| 4 | J6 ledger de tokens no MCP de produção | AMBOS |
| 5 | J4 descrições dos 35 agentes | CLAUDE → DEV revê |
| 6 | J5 registo de áreas (dados) | DEV → CLAUDE |
| 7 | J8 higiene de docs | CLAUDE |
| 8 | J2 VM Oracle | DEV |
| 9 | J11 spike mem0 | AMBOS |
| 10 | J9 pesquisas de nicho | CLAUDE |
| 11 | J10 gate de segurança em CI | AMBOS |

### BLOQUEADO POR DECISÃO

| Decisão | O que desbloqueia |
|---|---|
| **D1 (runtime)** | Worker (A/C/D) **ou** quebras do `/chat` (B/C); provider Gemini; HITL TS; build/Docker; órfãos TS; `MCPServer` TS; `query_database`; CORS; CI lento/lockfile Py (se ≠ B) |
| **D2 (maestro)** | Código do router/planner; fallback; alcançabilidade no runtime; implementação dos nichos |
| **D3 (L4)** | Módulo L4; ponte HITL↔memória; `MEMORY.md` passa a fallback |
| **D1 + D2** | Fonte de `toolsAllowed`; contrato de handoff; orçamento por área |

---

## Limites desta secção

- "Independente" foi avaliado contra as 4 vias da DECISAO-1. Se o humano escolher uma via não listada, a classificação tem de ser revista.
- J6 é trabalho no repo `agent-network-mcp`. Não foi verificado se o `usageMetadata` vem na resposta do endpoint usado (`generateContent`): **NÃO VERIFICADO**, precisa de uma chamada real com chave.
