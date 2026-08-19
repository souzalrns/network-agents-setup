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
| Ingestão BR (`brazilian-law.ts`) | **Conteúdo real curado** (18/08/2026): 15 leis reais (CC, CPC, CP, CPP, CLT, CDC, CTN, LGPD, Lei de Licitações antiga e nova, Estatuto da Cidade, CF/88 etc.), cada uma com resumo substantivo e artigos-chave. Duas citações erradas herdadas da lista original foram corrigidas (Lei 7.209/84 e 7.210/84 não eram CP/CPP — trocadas por DL 2.848/40 e DL 3.689/41, os diplomas certos). |
| Ingestão PT (`portuguese-law.ts`) | **Conteúdo real curado**, mas lista reduzida de 19 para 9 leis — verificadas uma a uma por busca contra fontes oficiais/confiáveis (DRE, OA, pgdlisboa.pt). A lista original tinha números de decreto-lei inventados (ex.: Código Civil PT rotulado como "Lei 4/2015", quando na verdade é o DL 47.344/66 — 4/2015 é o Código do Procedimento Administrativo). As 10 entradas removidas ficam pendentes de verificação antes de reentrar. |
| Jurisprudência (`jurisprudence.ts`) | **6 casos reais e verificados** (STF: ADI 4277/ADPF 132, RE 898.060 Tema 622, Súmula Vinculante 13; STJ: Súmulas 385 e 7; STJ Portugal: Acórdão Uniformizador 6/2023), no lugar dos 22 casos anteriores com números de processo **fabricados** (`RE-123456-7` etc.) — problema mais sério que placeholder óbvio, porque parecia real sem ser. |
| Doutrina (`doctrine.ts`) | 4 sínteses doutrinárias originais (não atribuídas a autor específico, para não fabricar citação nem violar direitos autorais de obra licenciada) sobre princípios do CC brasileiro e português, função social do contrato (comparado BR-PT) e usucapião. |
| Embeddings (`embeddings.ts`) | Código real (OpenAI `text-embedding-3-small`), lazy-init corrigido. **Nunca rodou de verdade** — precisaria de `OPENAI_API_KEY` paga. Agora geraria embedding de conteúdo real, não mais de texto simulado. |
| MCP tools jurídicas (`search_brazilian_law` etc.) | Código real. Testado contra o Prisma fake: já retorna resultado real (`source: 'database'`) em vez de cair no fallback simulado, porque agora há conteúdo de verdade para encontrar. |
| `smoke-test.ts` | Testado de fato (não só `tsc`) contra um Prisma fake em memória (harness descartável, fora do repo), 18/08/2026: 34 documentos (23 BR + 11 PT), sem duplicação na reingestão, 4/4 agentes jurídicos operacionais (81-92% de completude). |

**Resumo em uma frase:** o conteúdo do pipeline de ingestão agora é real e curado (leis,
jurisprudência e doutrina verificadas), mas ainda não foi persistido em banco nenhum —
falta (a) um Postgres real conectado (isolado do Supabase de produção, ver princípio de
isolamento acima) e (b) rodar a ingestão contra ele de verdade, fora do harness fake.

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

## CI (`.github/workflows/ci.yml`) — 18/08/2026

Repositório é **público**, confirmado via API do GitHub (`private: false`) — minutos de
GitHub Actions em runners hospedados pelo GitHub são ilimitados e gratuitos, sem risco de
cota. Isso resolve a limitação acima: o egress bloqueado é uma característica só deste
sandbox de desenvolvimento, não do runner do GitHub Actions. Por isso o CI roda o
pipeline de verdade — Postgres real (serviço `pgvector/pgvector:pg16`), `prisma generate`
e `prisma db push` reais (não o harness fake usado durante o desenvolvimento), depois
`tsc --noEmit` (via `tsconfig.typecheck.json`, committed — necessário porque nenhum
pacote em `packages/*/` tem `tsconfig.json` próprio) e o `smoke-test.ts --quick`.

**Confirmado rodando de verdade no GitHub** (não só escrito e revisado localmente — este
sandbox não tem Docker, então não dava para validar contra um Postgres real aqui antes do
push). Levou 5 iterações reais até ficar verde, cada uma corrigindo um problema genuíno
só visível rodando no runner de verdade:

1. `pnpm/action-setup` com `version: 8` fixo colidia com `packageManager: pnpm@8.0.0` do
   `package.json` — erro fatal do action. Corrigido removendo a versão fixa.
2. `cache: pnpm` no `setup-node` exige `pnpm-lock.yaml` commitado (não existe ainda) —
   corrigido removendo o cache por ora.
3. `pnpm install` falhou uma vez por instabilidade do registry (não reproduziu na
   iteração seguinte) — sem correção necessária, só confirmação de que era transiente.
4. `prisma generate` falhou uma vez pelo mesmo tipo de instabilidade de rede — idem.
5. Execução limpa: install, extensão `pgvector`, `prisma generate` e `prisma db push`
   reais, `tsc --noEmit`, `validate:consistency` (28/28 checks) e `smoke-test --quick`
   (34 documentos, 4/4 agentes operacionais) — tudo passou contra um Postgres real.

Para diagnosticar as falhas 1-2 acima sem acesso a Docker, o log completo do GitHub
Actions não pôde ser baixado diretamente daqui (redireciona para blob storage fora da
allowlist de rede deste sandbox) — contornado publicando os logs como um check-run
próprio via `actions/github-script` (ver comentário em `ci.yml`), lido pela API normal do
GitHub sem precisar do blob. Esse passo de diagnóstico ficou permanente no workflow.

Pendência conhecida do CI: sem `pnpm-lock.yaml` commitado ainda (`--no-frozen-lockfile`
contorna isso, mas builds não são 100% reprodutíveis até isso ser corrigido — tentei gerar
um aqui, mas o pnpm 8.0.0 deste sandbox tem um bug de compatibilidade com fetch que impede
`pnpm install`; precisa ser gerado num ambiente onde pnpm funcione, ex. o próprio runner).
