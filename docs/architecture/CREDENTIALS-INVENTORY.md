# Inventário de Credenciais — 2026-09-20

Produzido durante a auditoria de cobertura desta sessão (item S22), na sequência da rotação de credenciais de 2026-09-19 (`SUPABASE_SERVICE_ROLE_KEY`, password da BD, `GEMINI_API_KEY`). Cobre os 6 repos locais confirmados em `REPOSITORY-MAP.md`: `agent-network-mcp` (×2 clones), `network-agents-setup` (×2 clones), `repo-vianna`/`viannalegal-site` (mesmo remote).

**Método:** leitura directa de todos os `.env.example` encontrados + grep de `secrets\.` em todos os `.github/workflows/*.yml` + confirmação de ausência/presença de ficheiros `.env` reais (nunca o conteúdo/valor). Nenhum valor de credencial foi exposto neste documento.

---

## Tabela consolidada

| Credencial | Onde vive | Última actualização | Notas de consistência |
|---|---|---|---|
| `SUPABASE_SERVICE_ROLE_KEY` | Vercel (`agent-network-mcp`, não verificável localmente); GitHub Actions secret de `agent-network-mcp` (7 workflows: `audit-tools.yml`, `diagnostico-playwright-portal.yml`, `extrair-imagem.yml`, `scrape.yml`, `testar-portal-justica.yml`, `transcribe.yml`, `visual-review.yml`); VM Oracle (`bridge-worker.js`, S20 — provavelmente ainda antiga) | Rotacionada 2026-09-19; GitHub Actions actualizada 2026-09-20 (S15a); VM Oracle **não confirmada** (S20) | **Inconsistência de nome encontrada:** o `.env` da cópia `Downloads` (apagado, S16) usava `SUPABASE_SERVICE_KEY` (sem "ROLE") — nome errado. O nome correcto, usado em `agent-network-mcp/.env.example` e em todos os workflows, é `SUPABASE_SERVICE_ROLE_KEY` |
| `SUPABASE_ANON_KEY` | GitHub Actions secret de `network-agents-setup` (`keep-alive.yml`, único uso confirmado) | **Não rotacionada** (decisão consciente, S15b — é pública por design) | Sem inconsistência de nome encontrada |
| `SUPABASE_URL` | Acompanha as 2 chaves acima em todos os mesmos sítios (não é secreta em si, mas tratada como secret nos workflows) | N/A (URL de projecto, não muda com rotação de chaves) | Consistente em todos os sítios |
| `DATABASE_URL` | `.env.example` (raiz, placeholder `postgresql://network:CHANGE_ME@localhost:5432/...`); GitHub Actions secret de `network-agents-setup` (`ingest-knowledge.yml`) | Password rotacionada 2026-09-19; GitHub Actions actualizada 2026-09-20 (confirmado pelo utilizador antes desta auditoria) | Sem inconsistência de nome. Prefixo antigo da password (`RJAMGRSak0tdFZs9...`) **não encontrado** em nenhum ficheiro local (varredura 2b) |
| `GEMINI_API_KEY` | `agent-network-mcp/.env.example` (Vercel); GitHub Actions secret de `network-agents-setup` (`ingest-knowledge.yml`) | Rotacionada 2026-09-19; GitHub Actions actualizada 2026-09-20 (confirmado pelo utilizador) | Sem inconsistência de nome. Prefixo antigo (`AQ.Ab8RN6L2...`) **não encontrado** em nenhum ficheiro local |
| `MCP_API_KEY` | `agent-network-mcp/.env.example` (lado servidor, `app/api/mcp/route.js`); consumida pelo lado cliente em `network-agents-setup/runner/plan_runner/mcp_knowledge.py:63` | Não é uma das 3 credenciais rotacionadas — **fora do escopo desta rotação**, presume-se válida | **Segredo partilhado por desenho** entre os 2 repos — os dois lados têm de ter o mesmo valor. Não encontrado em nenhum `.env` local (nem antes nem depois da rotação) — só existe em Vercel |
| `CODECOV_TOKEN` | GitHub Actions secret de `network-agents-setup` (`runner-tests.yml`) | Não relacionada com a rotação de 2026-09-19 | Sem inconsistência |
| `INSTAGRAM_COOKIES` | GitHub Actions secret de `agent-network-mcp` (`extrair-imagem.yml`, único uso) | Não relacionada com a rotação de 2026-09-19; cookies de sessão expiram por si (fora do escopo desta rotação, mas nota geral: vale a pena confirmar validade periodicamente) | Sem inconsistência |
| `GH_PAT_ALL_REPOS` | GitHub Actions secret de `agent-network-mcp` (`audit-tools.yml`, único uso) | Não relacionada com a rotação de 2026-09-19 | PAT com acesso amplo a repos — sensível por natureza, não por esta rotação |
| `CROSS_DISPATCH_PAT` | GitHub Actions secret de `viannalegal-site`/`repo-vianna` (`trigger-visual-review.yml`) — dispara `visual-review.yml` no `agent-network-mcp` via API | Não relacionada com a rotação de 2026-09-19 | Achado durante 2d (não estava na lista original do utilizador) |
| `INGEST_URL` / `INGEST_SECRET` | GitHub Actions secrets de `agent-network-mcp` (`ingest.yml`, `heartbeat.yml` usam `INGEST_URL`; `ingest.yml` usa também `INGEST_SECRET`); `INGEST_SECRET` também em `.env.example` (Vercel) | Não relacionadas directamente com a rotação de 2026-09-19, mas protegem um endpoint que escreve no Supabase indirectamente | Sem inconsistência de nome |
| `API_KEY` | `.env.example` (raiz de `network-agents-setup`) — autenticação da própria API (`apps/api`, `x-api-key` header) | N/A | **Não confundir com `MCP_API_KEY`** — são credenciais distintas para sistemas distintos, nomes parecidos |
| `OPENAI_API_KEY` | `.env.example` (raiz); GitHub Actions secret de `network-agents-setup` (`ci.yml`) | Não relacionada com a rotação de 2026-09-19 | Sem inconsistência |
| `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` | `.env.example` (raiz) — só template, nenhum uso real encontrado em workflows | N/A | Presentes no template mas sem consumidor activo confirmado nesta auditoria |
| Token GitHub (`~/.git-credentials`) | VM Oracle/GCP (per `CONFIGURACAO_VM_BRIDGE_WORKER.md`) | Não verificável sem SSH | Fora do âmbito desta rotação |

---

## Credenciais futuras (ainda não em uso)

Introduzidas em 2026-09-20 (A8/S11) em `packages/mcp/src/server/McpAuth.ts` e `packages/mcp/src/client/MCPClient.ts`, mas **deliberadamente não adicionadas ao `.env.example`** — o `MCPServer.createHttpHandler()` que as consome não está ligado a nenhum servidor real hoje (achado do próprio S11); um template no `.env.example` sem consumidor real seria um template morto, o mesmo padrão de anomalia já assinalado no achado 3 abaixo.

| Credencial | Onde vive (código) | Estado | Quando activar |
|---|---|---|---|
| `MCP_SERVER_KEYS` | `packages/mcp/src/server/McpAuth.ts` (lista separada por vírgulas — cada key é um caller distinto) | Não em uso — `createHttpHandler()` nunca é montado num servidor real | Adicionar ao `.env.example` quando `MCPServer` for ligado a um endpoint HTTP real |
| `MCP_CLIENT_KEY` | `packages/mcp/src/client/MCPClient.ts` (construtor, `apiKey` opcional) | Não em uso pelo mesmo motivo | Idem — par da chave acima, o cliente real usaria uma das `MCP_SERVER_KEYS` |
| `MCP_ALLOW_UNAUTHENTICATED` | `packages/mcp/src/server/McpAuth.ts` (bypass de dev local, ignorado em produção) | Não em uso | Idem |

---

## Problemas encontrados

1. **Inconsistência de nome:** `SUPABASE_SERVICE_KEY` (encontrado no `.env` apagado da cópia `Downloads`, S16) vs. `SUPABASE_SERVICE_ROLE_KEY` (nome correcto, usado em todo o resto). Já resolvido pela remoção do ficheiro errado (S16), mas o nome errado pode reaparecer se alguém recriar o `.env` a partir de memória em vez do `.env.example` real.
2. **Duplicação por desenho, não por acidente:** `MCP_API_KEY` existe propositadamente nos 2 repos (servidor + cliente) — não é uma duplicação a corrigir, é um contrato partilhado.
3. **Credencial morta ainda potencialmente em uso activo:** `SUPABASE_SERVICE_ROLE_KEY` na VM Oracle (S20) — mesma família de problema que o S15a, ainda por confirmar/corrigir.
4. **`ANTHROPIC_API_KEY`/`GOOGLE_API_KEY`** no `.env.example` sem nenhum consumidor activo encontrado — possível resíduo de um template mais genérico, ou preparação para uso futuro; não investigado a fundo (fora do âmbito desta tarefa).

## Sítios que requerem intervenção humana (não verificável nesta sessão)

- **Vercel** (`agent-network-mcp`, `viannalegal-site`, `viannalegal-site-ht7m`) — sem acesso à consola, não é possível confirmar directamente que valor está configurado em cada variável de ambiente.
- **VM Oracle** (`130.61.213.226`) — sem SSH, não é possível confirmar o valor real de `SUPABASE_SERVICE_ROLE_KEY` no ambiente do processo `pm2` (S20).
- **`~/.git-credentials` na VM** — idem, sem SSH.

## Cross-referência com S15a/S20

Confirma-se que **S15a** (GitHub Actions de `agent-network-mcp`) e **S20** (VM Oracle) são os 2 únicos sítios, para além do já resolvido `.env` local (S16), onde a `SUPABASE_SERVICE_ROLE_KEY` antiga pode ainda estar em uso — consistente com a nota de agrupamento já registada em `STATUS.md`.

---

*Gerado durante a auditoria de cobertura de 2026-09-20 (Tarefa 2, S22). Não editar credenciais reais a partir deste documento — é só inventário, não gestão de segredos.*
