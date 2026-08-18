# STATUS — network-agents-setup (PCU)

> Última atualização: 18/08/2026. Este arquivo existe para responder uma pergunta em
> segundos, sem reabrir o histórico de conversas: **o que deste repo está real e
> funcionando, o que está só desenhado, e o que já existe em outro lugar e não deveria
> ser duplicado aqui.**
>
> Regra para qualquer sessão futura (Claude ou humano): antes de retomar trabalho neste
> repo, consultar `system_inventory` e `pendencias_negocio` (área `agent-network` e
> `pcu-nucleo-generico`) no Supabase `agent-network-memory` — esse é o índice geral da
> LRNSdigital, não este arquivo. Este arquivo é o índice *deste repo específico*.

## O que é este repo

Implementação de referência da arquitetura PCU (Plataforma Cognitiva Universal) descrita
em `docs/estrutura-geral-agentes.md` — 5 camadas (Orquestração Central, Domínios,
Especialistas, Transversais/Skills, Segurança/HITL), Router→Planner→Executor→Orchestrator,
Prisma+Redis, MCP tools, observabilidade própria.

## ⚠️ Existe sobreposição não resolvida com `agent-network-mcp`

O repo `github.com/souzalrns/agent-network-mcp` já é uma rede de agentes **em produção**
(Vercel, dashboard, GitHub Actions, bridge chat↔Claude Code), com 34 agentes configurados
em `lib/agents.js`, incluindo `direito-br-pt` — que já tem RAG real funcionando
(`knowledge_chunks` no Supabase, embeddings Gemini, 46 chunks ingeridos em 06/08/2026,
incluindo conteúdo real de usucapião/regimes de bens).

Este repo (`network-agents-setup`) foi construído em paralelo, do zero, **sem checar
primeiro** se esse trabalho já existia — esse é o erro a não repetir. Decisão pendente
(registrada em `pendencias_negocio`, área `agent-network-setup-vs-mcp`): manter os dois
propositalmente separados (este = arquitetura de referência/estudo, `agent-network-mcp` =
produção), fundir um no outro, ou descontinuar este.

## O que está implementado aqui e seu estado real

| Peça | Estado |
|---|---|
| Scaffolding PCU (Router/Planner/Executor/Orchestrator, packages/core etc.) | Implementado, `tsc --noEmit` limpo. **Nunca rodou contra um Postgres real.** |
| Prisma schema `LegalDocument` (`packages/memory/prisma/schema.prisma`) | Definido. `prisma generate`/`migrate` **não rodam neste sandbox** (egress bloqueado para `binaries.prisma.sh`, 403). Nunca aplicado a um banco real. |
| Ingestão BR (`packages/scripts/src/ingest/brazilian-law.ts`) | Código real, mas **conteúdo 100% simulado** (`"Conteúdo ... (simulado para teste)"`) — scraping do Planalto bloqueado deste sandbox (egress falha). |
| Ingestão PT (`portuguese-law.ts`) | Mesmo caso — DRE também bloqueado, conteúdo simulado. |
| Jurisprudência (STF/STJ/TJSP/tribunais PT) | Código real (`ingestCourt`/`fetchXCase`), mas resultado é texto simulado (`probeReachable` só confirma alcance HTTP, não extrai conteúdo real — portais são SPAs). |
| Doutrina | 2 entradas seed, simuladas. |
| Embeddings (`embeddings.ts`) | Código real (OpenAI `text-embedding-3-small`), lazy-init corrigido. **Nunca rodou de verdade** — precisaria de `OPENAI_API_KEY` paga, e ainda assim geraria embedding de texto simulado. |
| MCP tools jurídicas (`search_brazilian_law` etc.) | Código real, com fallback simulado quando a base está vazia — que é sempre o caso hoje, já que nada real foi persistido. |
| `smoke-test.ts` | Real, testado de fato (não só `tsc`) contra um Prisma fake em memória (harness descartável, fora do repo). Confirmou que o pipeline roda ponta a ponta *estruturalmente* — mas nunca contra um banco real, e sempre com dados simulados. |

**Resumo em uma frase:** o código do pipeline de ingestão está correto e testado
estruturalmente, mas nenhuma linha de conteúdo jurídico real foi persistida em lugar
nenhum a partir deste repo — porque (a) não há Postgres real conectado e (b) o scraping
das fontes oficiais está bloqueado neste ambiente.

## Alternativa já funcionando (fora deste repo)

`ask_agent_network` / `run_specific_agent(agent: 'direito-br-pt')` via o MCP
"Rede de Agentes LRNSdigital" — já responde perguntas jurídicas BR/PT reais, citando
artigos corretos, usando conteúdo real ingerido no Supabase `agent-network-memory`
(tabela `knowledge_chunks`). É a via recomendada para uso imediato enquanto a decisão
acima não é tomada.

## Limitações confirmadas deste sandbox (não deste repo)

- Sem Docker daemon, sem Postgres local.
- `prisma generate`/`migrate`: 403 em `binaries.prisma.sh` mesmo com
  `PRISMA_ENGINES_CHECKSUM_IGNORE_MISSING=1`.
- Egress bloqueado para `legislacao.presidencia.gov.br` e `diariodarepublica.pt`.
- `new PrismaClient()` lança na hora de importar o módulo (client stub não gerado) —
  qualquer script que importe `packages/scripts/src/db.ts` sem workaround quebra.
