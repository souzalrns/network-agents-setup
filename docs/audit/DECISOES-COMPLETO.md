# DECISÕES — Consolidação (Fase 2 da auditoria)

> **Base:** commit `3dc3b25` + Fase 1 (`AUDIT-*.md`). **Branch:** `claude/audit-completo`. **Data:** 2026-09-29.
> **Natureza:** análise para decisão. **Nada foi implementado nem corrigido.** Só foram criados ficheiros em `docs/audit/`.
> **Documentos:** [DECISAO-1-runtimes](./DECISAO-1-runtimes.md) · [DECISAO-2-maestro](./DECISAO-2-maestro.md) · [DECISAO-3-memoria](./DECISAO-3-memoria.md) · [DECISAO-4-ordem](./DECISAO-4-ordem.md)

---

## Resumo das 4 decisões

| # | O que está em jogo | Recomendação (provisória) | Pergunta decisiva ao humano |
|---|---|---|---|
| **1 — Runtimes** | Dois runtimes sem ponte, mais um terceiro em produção (MCP). O Python ganha em 6 dos 9 critérios da visão (custo zero, memória, ingestão, tokens, HITL, testes); o TS em 3 (tools, API e, marginalmente, maestro). As vantagens do TS cabem em ~1,2k LOC portáveis; as do Python custariam ~4,3k LOC + 195 testes a reescrever | **VIA A** — consolidar em Python, portando ~1,2k LOC do TS e **arquivando** o resto (≈17k LOC) | **Quem chama o sistema** (IDE via MCP? o MCP de produção? HTTP externo?) e **onde corre** o motor (VM? local?) |
| **2 — Maestro** | Três maestros parciais: TS bloqueado e com 8 agentes inalcançáveis; Python sem planeador; MCP com router LLM real mas plano, ~1,5k tokens por pedido a crescer ~44 tokens por agente | **Router hierárquico híbrido** (área por palavras-chave/embeddings → agente por LLM só dentro da área) sobre um **registo de áreas versionado e validado em CI**; horizontais sempre candidatos; clarificação/HITL com baixa confiança | **Um agente por pedido ou plano multi-passo?** Qual é a **lista inicial de áreas**? |
| **3 — Memória L4** | L4 definida (contrato completo) e com zero código. O mem0 2.2.0 encaixa parcialmente, gasta 1 chamada LLM por escrita, precisa de `vecs` para o Supabase e envia telemetria por omissão | **VIA A** — L4 própria em `runner/plan_runner`, sobre o Supabase existente, **depois** de consertar o RAG, **com um spike mem0** de 1–2 dias para comparar | **Extracção automática de factos ou escrita explícita?** E o teste de mem0 era **avaliação ou adopção**? |
| **4 — Ordem** | 5 dos 10 itens prioritários estão bloqueados por inteiro pelas decisões e 2 em parte; há 11 frentes independentes | Começar pelas 11 frentes independentes; tomar as decisões 1→2→3 **por esta ordem** | — |

### Tabela de decisão

| Decisão | Opções | Recomendação | Pergunta ao humano |
|---|---|---|---|
| D1 Runtime | A Python · B TS · C ambos · D maestro no MCP + motor Python *(acrescentada)* | A (provisória) | Q1 quem chama o sistema? · Q2 onde corre? · Q3 o MCP continua a ser a porta de entrada? · Q4 a governança TS é roadmap activo? |
| D2 Maestro | Mapeamento M1–M4 · Alcançabilidade G1–G4 · Routing C1–C5 · Local das áreas: código/config/Supabase/frontmatter | M3 + G1/G2/G3 + C4, em config versionada | ADR-M1…M8 (runtime, 1 agente vs plano, lista de áreas, local do registo, política de baixa confiança, orçamento/HITL por área, verticais do MCP no registo, nomenclatura) |
| D3 Memória L4 | A própria · B mem0 · C adiar | A + spike mem0 | M-Q1 extracção automática? · M-Q2 Supabase ou SQLite? · M-Q3 avaliação ou adopção do mem0? |
| D4 Ordem | Por via (A/B/C/D) | 11 frentes já; depois D1→D2→D3 | — |

---

## PODE COMEÇAR AGORA (não depende de decisão nenhuma)

| # | Item | Quem | Evidência |
|---|---|---|---|
| 1 | **Keep-alive**: secrets `SUPABASE_URL`/`SUPABASE_ANON_KEY` + tabela `keepalive` (5/5 runs falhados) | DEV → CLAUDE | AUDIT-5 AU-47 |
| 2 | **Apagar `tests/package.json`** (causa provável do Dependabot #11 crítico) | CLAUDE | AUDIT-5 AU-05 |
| 3 | **RAG**: escolher a tabela canónica e pôr o retrieve a ler o que se ingere (micro-decisão, não bloqueada por D1–D3) | AMBOS | AUDIT-2 §2.4 |
| 4 | **Ledger de tokens no MCP de produção** (`usageMetadata`, hoje ignorado): a linha de base do objectivo n.º 1 | AMBOS | `agentRuntime.js:56-59` |
| 5 | **`description:` nos 35 agentes `.md`** (0/35 hoje) | CLAUDE → DEV revê | DECISAO-2 §2.1 |
| 6 | **Registo de áreas como dados** (sem código de router) | DEV (lista) → CLAUDE | DECISAO-2 §2.5 |
| 7 | **Higiene de docs** (colisões de IDs, OPEN-ITEMS, errata CORE-MAPPING, partir o STATUS, `.env.example`) | CLAUDE | AUDIT-5 AU-08/12/37/45/46 |
| 8 | **VM Oracle** (chave antiga no `pm2`) | DEV | `STATUS.md:41` |
| 9 | **Spike mem0 vs L4** (informa a D3) | AMBOS | DECISAO-3 §3.4 |
| 10 | **Pesquisas de nicho** G1.1 (trading) e G2.1 (gamedev), só pesquisa | CLAUDE | `EXECUTION-PROMPTS.md:1618,1896` |
| 11 | **Gate de segurança em CI** (gitleaks/semgrep) | AMBOS | `STATUS.md:28` |

**Não está nesta lista, ao contrário do que o brief sugeria:** "corrigir as 4 quebras do `/chat`". Só tem valor nas vias B ou C. Na A e na D o código TS é arquivado, e o esforço perde-se.

---

## ACRESCENTADO PELO AUDITOR

| O quê | Onde | Porquê |
|---|---|---|
| **Terceiro runtime (produção MCP) na comparação** + **VIA D** | DECISAO-1 §1.1, §1.2 | O único router LLM em produção está fora deste repo; ignorá-lo enviesava a comparação A/B/C |
| **Estado real do worker de fila** (`code_tasks`: 28 feitas por US$ 7,01, 20 erros, 2 presas, parado desde 09-09) | DECISAO-1 §1.1 | Mostra que o padrão "worker externo" já foi usado e quanto custou; o "worker que não existe" existe noutro repo, mas é pago e está parado |
| **Pontuação por critério da visão** (9 critérios, com evidência) | DECISAO-1 §1.3 | Transformar "recomendação" em comparação verificável |
| **Medição do custo em tokens do router de produção** (~1,5k por pedido, +~44 por agente) | DECISAO-2 §2.1 | Base quantitativa para escolher o routing hierárquico (objectivo n.º 1) |
| **Frontmatter dos agentes: 0/35 com `description:`** | DECISAO-2 §2.1 | Nenhum router semântico funciona sem isto; é um trabalho independente e barato |
| **O validador de consistência verifica o STATUS histórico e só 4 agentes** | DECISAO-2 §2.1 | O mecanismo natural de "nenhum agente inalcançável" existe, mas está apontado ao sítio errado |
| **Leitura do código-fonte do mem0 2.2.0** (1 LLM por `add()`; `vecs` em falta; telemetria ligada por omissão; `add()` só aditivo) | DECISAO-3 §3.3 | Decidir sobre código, não sobre documentação; corrige a suposição de que o mem0 reescreve memórias em silêncio |
| **O teu teste de mem0 falharia** (`ImportError: vecs`; nome de variável fora da convenção do repo) | DECISAO-3 §3.3 | Evita perder tempo a depurar `.env` quando a causa é outra |
| **Correcção ao brief** sobre o que é independente (as quebras do `/chat` não são; os tokens são, se medidos no MCP) | DECISAO-4 resumo e §4.3 | Honestidade sobre o que se perde em cada via |
| **Nota de segurança no MCP**: a chave Gemini vai na query string (`agentRuntime.js:39`), problema já corrigido no setup (A7) | DECISAO-1 §1.1 | Achado lateral, fora deste repo |

---

## Secções marcadas NÃO VERIFICADO / NÃO VERIFICÁVEL

| Ponto | Estado | Requer |
|---|---|---|
| Esforços em dias das vias A/B/C/D | Estimativas do auditor; **só os LOC e os testes foram medidos** | — |
| A VM Oracle aguenta o motor como serviço (VIA A/D) | NÃO VERIFICÁVEL daqui | Consola/SSH (S27) |
| O MCP (Vercel) consegue chamar um serviço externo (VIA D) | NÃO VERIFICADO | Config do Vercel |
| Tokens do router medidos por heurística (chars/4) | NÃO medido com o tokenizer | Chamada real ao Gemini |
| Tabela `projects` do MCP como opção de registo | NÃO relida | Leitura do schema |
| mem0 executado contra o Supabase | NÃO executado (sem `.env`, sem `vecs`) | `.env` + `vecs` ou `pgvector` |
| Modelo `gemini-3.1-flash-lite` do teu teste | NÃO VERIFICADO que exista | Chamada à API |
| `usageMetadata` disponível na resposta usada pelo MCP | NÃO VERIFICADO | Chamada real com chave |

---

## Commits desta fase

`5820be8` (decisão 1), `d298fe3` (decisão 2), `aa6747a` (decisão 3), `706a0fa` (decisão 4) e o commit deste ficheiro ("audit: decisões consolidado").
