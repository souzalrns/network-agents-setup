# Vertical editorial

Redação digital para uma publicação jornalística: banco de pautas, produção de artigos com revisão e aprovação,
verificação de afirmações, radar de fontes, quatro agentes que propõem (nunca decidem), distribuição para redes
e o site público. A marca é configuração: o mesmo código serve qualquer publicação.

O estado e as decisões por tomar estão no `PENDENCIAS.md` (item **E-005**, decisões **P-91 a P-94**).

## O que está feito

| Parte | Onde | Testado |
|---|---|---|
| Base de dados com isolamento por publicação | `db/migrations/0001_init.sql`, `0002_security.sql` | `tests/isolation.test.ts` |
| Fluxo de 11 estados com regras na base de dados | `src/lib/workflow.ts`, `stories.ts`, trigger `stories_guard` | `tests/workflow.test.ts` |
| Aprovação presa ao conteúdo aprovado, afirmações revalidadas, distribuição protegida, quatro olhos na verificação | `db/migrations/0003_integrity.sql` | `tests/integrity.test.ts` (R1–R8 da revisão técnica) |
| Rascunhos no servidor, autosave, conflitos, versões com comparação e restauro | `0004_drafts.sql`, `src/lib/drafts.ts`, `src/app/redacao/rascunho/`, `pecas/[id]/article-editor.tsx`, `pecas/[id]/versoes/` | `tests/drafts.test.ts`, `tests/e2e/editor.mjs` |
| Editor com barra de formatação, figuras com legenda e crédito, vídeo, pré-visualização ao lado e fiel ao site | `article-editor.tsx`, `src/lib/markdown.ts`, `src/components/article-view.tsx`, `/redacao/pre-visualizar/` | `tests/markdown.test.ts`, `tests/e2e/editor.mjs` |
| Quadro de pautas com movimentação segura (arrastar só para destinos permitidos; «Mover para…») | `pautas/board.tsx` | `tests/e2e/board.mjs` |
| Atividade, filtros e paginação | `/redacao/atividade`, `pautas/page.tsx`, `listActivity`, `countStoriesTx` | `tests/queries.test.ts` |
| Telemóvel: menu em `<dialog>`, sem transbordo, equipa numa linha por pessoa | `src/components/nav.tsx`, `globals.css`, `equipa/[id]` | `tests/e2e/mobile.mjs` |
| Validação da configuração inicial | `db/validate-seed.mjs` (`npm run db:validate`) | `tests/seed.test.ts` |
| Recuperar a palavra-passe sem email (link de uso único, 24 h, gerado pela direção) | `0007`, `src/lib/accounts.ts`, `/redacao/recuperar/[token]` | `tests/operations.test.ts`, `tests/e2e/operations.mjs` |
| Biblioteca de média na própria base (redução no browser, tipo confirmado pelos bytes, legenda e crédito) | `0007`, `src/lib/media.ts`, `/redacao/media`, `/media/[id]` | idem |
| Newsletter: inscrição com consentimento registado (RGPD), anulação por link, exportação CSV | `0007`, `src/lib/newsletter.ts`, `/newsletter`, `/redacao/newsletter` | idem |
| Cópia de segurança da publicação (JSON, sem segredos) | `src/lib/backup.ts`, Configuração → Descarregar cópia | idem |
| Redação (painel, pautas, ficha da peça, calendário, radar, fontes, equipa, distribuição, configuração) | `src/app/redacao/` | `tests/e2e/run.mjs` |
| Site público (início, editorias, artigo, autor, pesquisa, páginas, sitemap, robots, RSS) | `src/app/(site)/`, `src/app/sitemap.ts`, `robots.ts`, `feed.xml/` | `tests/e2e/run.mjs` |
| Radar de fontes (RSS/Atom, allowlist, SSRF, deduplicação, relevância) | `src/lib/radar/` | `tests/radar.test.ts` |
| Agentes `editorial.radar`, `.research`, `.factcheck`, `.editor` | `src/lib/agents/` | `tests/agents.test.ts` |
| Envio para o Postiz (rascunhos, só aprovados, sem reenvios) | `src/lib/postiz.ts` | `tests/postiz.test.ts` (transporte simulado), `tests/e2e/run.mjs` (sem credenciais) |
| Publicação agendada e radar automáticos | `src/app/api/cron/` | `tests/workflow.test.ts` (`publishDue`) |

Os agentes estão também no catálogo da plataforma: `agents/editorial/*.agent.md`, `skills/editorial/*/SKILL.md`,
área `editorial` em `config/areas.yaml` (com `hitl: required`) e departamento Redação em `config/office.yaml`.

## Regras que a base de dados impõe

A aplicação liga-se com o papel `editorial_app`, sem privilégios de dono. Todas as tabelas têm RLS forçado e cada
transacção declara a publicação e quem actua (`withCtx`, em `src/lib/db.ts`). Sem esse contexto não se vê nenhuma linha.

- Uma publicação nunca vê nem altera dados de outra.
- Só edição, direção ou administração aprovam pautas e artigos, agendam e publicam.
- Quem escreveu uma peça não a aprova (a direção pode desligar a regra para uma redação de uma pessoa).
- Não se aprova com informação não confirmada no artigo ou com factos por verificar; agendar e publicar voltam a
  verificar (uma afirmação acrescentada depois da aprovação também bloqueia).
- Uma afirmação só fica verificada com evidência e por uma pessoa, que fica registada. Com os quatro olhos, quem
  escreveu a peça ou registou a afirmação não a verifica. Mudar o texto, o tipo, a atribuição ou a evidência volta a
  pô-la «por verificar».
- A aprovação fica presa ao conteúdo: uma impressão digital (sha256) de título, textos, endereço, editoria,
  autoria, imagem, legenda, crédito, etiquetas, SEO e tipo. Agendar e publicar exigem o conteúdo exactamente aprovado.
  Mexer numa peça aprovada ou agendada devolve-a a revisão; mudar conteúdo e estado na mesma operação é recusado;
  os campos da aprovação só mudam pelo fluxo; uma peça arquivada não se reescreve.
- Editar uma peça publicada: só a edição, com nota obrigatória; conta como nova aprovação e fica no histórico.
- Imagem principal e figuras do texto precisam de crédito para aprovar.
- O sistema só publica o que uma pessoa agendou, à hora marcada, sem tocar no texto; cada peça é tentada à parte.
- Agentes só criam ideias, propostas, afirmações pendentes e notas. Não lêem fontes, contactos nem comentários.
- Distribuição: só segue para o agendador o conteúdo exactamente aprovado por uma pessoa da edição; o que seguiu já
  não se altera.
- Rascunhos: só quem pode alterar a peça tem rascunho dela; guardar uma versão sobre uma versão que mudou entretanto
  é recusado (a última gravação não ganha em silêncio) e o texto fica no rascunho.
- Cada mudança de estado, cada versão do texto e cada execução de agente ficam registadas.

## Correr localmente

Precisa de Node 20+ e Postgres 16.

```bash
npm install
# base de dados (ligação do DONO do esquema)
export EDITORIAL_MIGRATION_URL=postgres://postgres:postgres@127.0.0.1:5432/editorial
npm run db:migrate
psql "$EDITORIAL_MIGRATION_URL" -c "alter role editorial_app login password 'escolhe-uma'"
# publicação (ficheiro de configuração da marca) e primeira conta de administração
EDITORIAL_SEED_FILE=config/seed.example.json \
EDITORIAL_ADMIN_EMAIL=tu@exemplo.pt EDITORIAL_ADMIN_PASSWORD='pelo-menos-10-caracteres' \
npm run db:seed
# aplicação (ligação do papel editorial_app)
export EDITORIAL_DATABASE_URL=postgres://editorial_app:escolhe-uma@127.0.0.1:5432/editorial
export EDITORIAL_DEFAULT_PUBLICATION=gazeta-exemplo
npm run build && npm start   # http://localhost:3000 (site) e /redacao (redação)
```

A configuração d'O Bode (marca, 8 editorias, páginas e 35 pautas) está em
`agent-network-mcp/publications/o-bode/seed.json`, no repositório de produção: os dados de negócio não vivem neste
repositório público.

## Testes

```bash
# Postgres de teste em 127.0.0.1:55432 (postgres/postgres); cada corrida cria a sua base
docker run -d --name editorial-pg -e POSTGRES_PASSWORD=postgres -p 127.0.0.1:55432:5432 postgres:16-alpine
npm test                 # 108 testes: isolamento, fluxo, integridade (R1–R8), rascunhos, radar, agentes, Postiz…
npm run typecheck
# no browser, numa base PRÓPRIA e descartável (editorial_e2e): migra, semeia o exemplo, arranca next start
npm run build && npm run test:e2e   # fluxo 30, telemóvel 12, editor com duas pessoas 19, quadro 9
npm run db:validate      # valida a configuração inicial antes de semear
```

## Variáveis de ambiente

| Variável | Para quê |
|---|---|
| `EDITORIAL_DATABASE_URL` | Ligação da aplicação (papel `editorial_app`) |
| `EDITORIAL_MIGRATION_URL` | Só para migrações e seed (dono do esquema). Nunca na aplicação |
| `EDITORIAL_DEFAULT_PUBLICATION` | Slug servido quando o domínio do pedido não corresponde a nenhuma publicação |
| `EDITORIAL_SITE_URL` | Endereço público canónico (sitemap, partilhas, Postiz) |
| `CRON_SECRET` | Segredo (24+ caracteres) das tarefas `/api/cron/publicar` e `/api/cron/radar` |
| `GEMINI_API_KEY` | Opcional: liga o passo com modelo dos agentes. Sem ela, só a parte determinística |
| `EDITORIAL_LLM_MODEL`, `EDITORIAL_AGENT_MAX_USD`, `EDITORIAL_AGENT_MAX_CALLS`, `EDITORIAL_AGENT_MAX_OUTPUT_TOKENS` | Modelo e limites por execução (omissão: `gemini-2.5-flash-lite`, 0,05 USD, 3 chamadas, 1024 tokens) |
| `POSTIZ_API_URL`, `POSTIZ_API_KEY` | Opcional: o Postiz da redação. Sem elas, o envio simula |

## Deployment: Vercel (Hobby) + Neon (Free), a custo zero

**Porquê Neon** (decisão P-94, com a evidência de 2026-11-17/18): a organização Supabase já tem os 2 projectos
gratuitos ocupados (`agent-network-memory` e `vianna-gestao`) e o limite é por pessoa, não por organização; um
terceiro obriga ao plano pago ou a misturar a redacção com a memória dos agentes ou com um cliente. O Neon gratuito
tem 100 projectos, 1 GB por projecto, desliga-se sozinho sem uso (não há nada para «esquecer ligado») e não cobra
excessos: sem cartão, o pior caso é a base parar até ao mês seguinte. A integração Neon do Vercel cria as ligações
no projecto sem passos manuais. Contrapartida: 100 CU-horas por mês por projecto; com tráfego real contínuo, medir e
decidir entre o plano pago do Neon e o Supabase Pro (as duas funcionam com o mesmo código).

Passos (testado no projecto `editorial-teste`):

1. Projecto Vercel com raiz `verticals/editorial` ligado ao repositório. O `vercel.json` fixa a região `fra1`
   (perto da base em Frankfurt) e as tarefas diárias.
2. Separador **Storage → Create → Neon → Free**, região Frankfurt, ligado a Production e Preview. A integração cria
   `DATABASE_URL` (pooler) e `DATABASE_URL_UNPOOLED` (dono).
3. Variáveis: `EDITORIAL_PROVISION=1`, `EDITORIAL_DEFAULT_PUBLICATION`, `EDITORIAL_SEED_URL` (ou
   `EDITORIAL_SEED_JSON`), `EDITORIAL_ADMIN_EMAIL`, `EDITORIAL_ADMIN_PASSWORD` (sensível), `EDITORIAL_ADMIN_SLUG`
   (opcional) e `CRON_SECRET` (sensível, 24+ caracteres).
4. Deploy. O script `vercel-build` corre `db/provision.mjs` antes do `next build`: migrações em falta, papel
   `editorial_app` com palavra-passe derivada da do dono (`db/app-url.mjs`, sem segredo novo) e sementeira **só se a
   publicação ainda não existir** (depois quem manda é a redacção; `EDITORIAL_SEED_FORCE=1` obriga, por exemplo para
   acrescentar uma conta de direcção ou pautas novas do ficheiro, que nunca substituem as existentes).
5. Domínio: preencher `domain` na configuração da publicação.
6. Lançamento: com o registo na ERC feito, ligar «Site lançado». Até lá o site mostra um aviso, o `robots.txt`
   bloqueia tudo e as páginas pedem para não ser indexadas.

Detalhes que só aparecem num Postgres gerido (e estão resolvidos):

- O dono não é superutilizador: `0005_owner_policies.sql` dá-lhe uma política própria para as funções SECURITY
  DEFINER (entrar, sessões, domínio); a aplicação (`editorial_app`) não ganha nenhum acesso.
- O Neon e os poolers ignoram o `search_path` enviado ao ligar: cada transacção define-o (`withCtx`).
- Publicação agendada: no Hobby as tarefas correm uma vez por dia, por isso cada visita ao site ou à redacção
  publica as peças cuja hora chegou (no máximo uma vez por minuto por instância, como «sistema», que só publica o
  que uma pessoa agendou). A tarefa diária fica como rede de segurança.
- Protecção do Vercel: o projecto de teste está sem a autenticação do Vercel para a direcção poder entrar (a
  redacção tem login próprio e o site está em pré-lançamento). Em produção, com domínio próprio, a autenticação do
  Vercel não se aplica ao domínio; quem guarda a redacção é o login da aplicação.

Outro Postgres: também funciona com `EDITORIAL_MIGRATION_URL` (dono) e `EDITORIAL_DATABASE_URL` (aplicação,
pooler em modo transacção; o driver usa `prepare: false`), com `db/migrate.mjs` e `db/seed.mjs` à mão.

## Decisões técnicas tomadas (reversíveis)

- **Uma peça, 11 estados.** Pauta e artigo são a mesma linha (`stories`): a ideia vira pauta, a pauta vira artigo,
  e o histórico fica inteiro. Um artigo sem pauta é uma pauta que avança directamente.
- **Regras na base de dados, não só na interface.** O que um agente, o sistema ou um papel podem fazer está em RLS e
  triggers; a aplicação repete a regra só para dar uma mensagem clara.
- **Next.js com Server Actions e formulários HTML.** Funciona sem JavaScript no browser; cada acção verifica a
  sessão e devolve a página com a mensagem.
- **Sessões próprias** (cookie httpOnly, token aleatório guardado como sha256, scrypt nas palavras-passe), em vez de
  um fornecedor externo: menos dependências e funciona em qualquer Postgres.
- **Sistema próprio em vez de um CMS existente.** Comparação (2026-11-21), pelo que O Bode precisa:

  | | Este sistema | Ghost | WordPress | Superdesk | We.Publish / Byline |
  |---|---|---|---|---|---|
  | Regras de redacção impostas pela base (quatro olhos, aprovação presa ao conteúdo, afirmações verificadas antes de publicar) | **sim**, provadas contra contornos directos (R1–R8) | não | só com plugins, na interface | parcial (fluxo, sem afirmações) | não |
  | Fontes protegidas fora do alcance de agentes e do público | **sim** (RLS) | não | não | não | não |
  | Agentes de IA que só propõem, ligados à plataforma LRNSdigital | **sim** | não | por plugins, sem limites na base | não | não |
  | Várias publicações com a marca só em configuração | **sim** | uma por instalação | multisite | sim | sim |
  | Newsletter | inscrição, consentimento e exportação (envio num serviço à escolha) | **completa, com assinaturas pagas** | por plugins | não | parcial |
  | Editor | Markdown com barra, figuras e vídeo | **rico** | **rico** | rico | rico |
  | Maturidade, comunidade, actualizações | nova; mantida por nós | **grande** | **enorme** | média | pequena |
  | Licença e custo | nossa; custo zero (Vercel Hobby + Neon Free) | MIT; alojamento próprio ou pago | GPL | AGPL; pesado para 4 pessoas | MIT / MPL |

  Decisivo: as regras de integridade e a protecção das fontes não existem nos outros e teriam de ser reconstruídas
  por cima de um modelo de dados alheio. Onde os outros ganham (editor rico, assinaturas pagas, maturidade), a
  resposta está nas secções de limites: o Ghost continua a ser o complemento natural se a newsletter paga for
  central no modelo de negócio (híbrido: esta redacção produz e verifica, o Ghost serve leitores pagantes).
- **Postiz pela API pública, mesmo contrato do `runner/plan_runner/postiz.py`:** só rascunhos, idempotente, sem
  publicação imediata. PostSider e OpenPost não foram instalados (duplicariam o Postiz).
- **Markdown com dialecto próprio (D2)** em vez de um editor rico: figura `![Legenda](https://… "Crédito")` e
  vídeo (endereço do YouTube ou Vimeo sozinho numa linha). O mesmo `renderMarkdown` serve a pré-visualização e o site.
- **Autosave no servidor (D4)**: o browser só guarda uma cópia enquanto o servidor não confirma; as versões nascem
  em «Guardar versão»; restaurar cria uma versão nova.
- **Menu móvel em `<dialog>` nativo (D1)** e arrastar e largar nativo (D3): sem bibliotecas.
- **Agentes determinísticos primeiro.** Cada agente produz trabalho útil sem modelo e testado; o modelo, quando há
  chave, acrescenta sugestões validadas contra o contrato e com tecto de custo.
- **Radar só com metadados.** Título, excerto até 300 caracteres e ligação; nunca o artigo de outro meio.

## Limites conhecidos

- Nenhum feed do radar foi verificado nesta sessão: o proxy do ambiente recusou todos os domínios (P-93).
- O radar verifica o DNS antes de cada pedido, mas o `fetch` volta a resolver o nome ao ligar (janela de
  DNS rebinding); fechá-la exige um conector próprio.
- Imagens: biblioteca na própria base (máx. 3 MB cada, reduzidas no browser); com a base gratuita de 1 GB cabem
  milhares de fotografias, mas vídeo e áudio continuam por endereço. Para muito volume, mover para um armazenamento
  de objectos (a rota `/media/[id]` isola essa troca).
- O aviso de quem está a editar é informativo (2 minutos depois da última gravação), não um bloqueio.
- Os agentes correm dentro da vertical (D7): a integração com o motor universal está registada como dívida (E-006).
- Sem envio de email (notificações e newsletter): falta escolher um serviço. A recuperação da palavra-passe
  funciona sem email (link gerado pela direção); a newsletter recolhe e exporta, o envio faz-se nesse serviço.
- Cópias de segurança: a direção descarrega quando quiser; ainda não há cópia automática para um sítio privado.
- Podcast e vídeo: há rascunhos de guião e descrição pelo agente de edição; transcrição e cortes ficaram de fora
  (o Podguy foi avaliado: MIT, criado em maio de 2026, sem versões publicadas).
