# STATUS — network-agents-setup (PCU)

> Última atualização: 18/08/2026. Este arquivo existe para responder uma pergunta em
> segundos, sem reabrir o histórico de conversas: **o que deste repo está real e
> funcionando, o que está só desenhado, e qual camada (pública/genérica aqui vs.
> privada/produção em `agent-network-mcp`) cada peça deveria ocupar.**
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

## Princípio de arquitetura: uma arquitetura, duas camadas de deployment

Não são dois projetos separados que coincidem — é **uma única arquitetura de agentes
com duas camadas de instância**, com um princípio de design que decide onde cada coisa
mora:

1. **Camada pública/genérica — este repo (`network-agents-setup` / PCU).** Motor
   transversal, pluggable e reutilizável: um agente por domínio/projeto (o "plug") +
   toda a infraestrutura compartilhada (orquestração, memória, tools, pipeline de
   ingestão etc.). Destinado a portfólio e a qualquer desenvolvedor.
2. **Camada privada/produção — `agent-network-mcp`.** Instância específica da
   LRNSdigital com os agentes dos negócios reais (mesaflow, viannalegal, direito-br-pt
   etc.) — os agentes de projeto são os plugins privados que se encaixam na estrutura
   transversal. Aqui ficam dados sensíveis, configurações de negócio e fluxos que não
   devem ser públicos.

**Regra que decide onde cada coisa vive:**

- Conhecimento de domínio (leis, regras, bases de dados públicas) → camada genérica
  (este repo) e é reutilizável, mesmo que tenha sido usado primeiro numa pesquisa
  específica — ele atende a qualquer pessoa por natureza.
- Agente de negócio / lógica privada → é o plugin, isolado em `agent-network-mcp`.
- O diferencial competitivo real não está no código dos agentes no Git (que qualquer um
  pode clonar vazio) — está na **ingestão de conhecimento real e curado**. Por isso este
  repo precisa demonstrar essa capacidade de forma crível (conteúdo substantivo, não
  placeholder), enquanto o isolamento de banco garante que dados privados de produção
  nunca vazem para o repositório público.

Sempre que fizer sentido, melhorias somam de um lado para o outro — não é para duplicar
sem necessidade. Quando este repo for de fato publicado como portfólio, a versão
publicada é uma cópia do estado atual com qualquer resquício de plugin privado removido.

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

## Referência real já funcionando (camada privada, fora deste repo)

`ask_agent_network` / `run_specific_agent(agent: 'direito-br-pt')` via o MCP
"Rede de Agentes LRNSdigital" já responde perguntas jurídicas BR/PT reais, citando
artigos corretos, usando conteúdo real ingerido no Supabase `agent-network-memory`
(tabela `knowledge_chunks`). Isso prova que o conceito funciona — o próximo passo aqui é
levar essa mesma qualidade de conteúdo (curado, real) para a camada genérica/pública
deste repo, sem apontar para o banco privado de produção (ver princípio de isolamento
acima).

## Limitações confirmadas deste sandbox (não deste repo)

- Sem Docker daemon, sem Postgres local.
- `prisma generate`/`migrate`: 403 em `binaries.prisma.sh` mesmo com
  `PRISMA_ENGINES_CHECKSUM_IGNORE_MISSING=1`.
- Egress bloqueado para `legislacao.presidencia.gov.br` e `diariodarepublica.pt`.
- `new PrismaClient()` lança na hora de importar o módulo (client stub não gerado) —
  qualquer script que importe `packages/scripts/src/db.ts` sem workaround quebra.
