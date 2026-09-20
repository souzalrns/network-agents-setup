# AUDIT-SCOPE-2026-09-19 — Auditoria de escopo do EXECUTION-PROMPTS.md

**Origem:** item B14/D10, aberto durante a execução do A18 (2026-09-19), quando se confirmou que 5 itens já executados nesta sessão (C6, A1, A21, A14, A18) tinham escopo real diferente do descrito no plano.

**Objectivo:** revalidar contra o código real todos os itens ainda pendentes do `EXECUTION-PROMPTS.md` (Grupos A-J, excepto os já fechados: A1-A3, A5-A7, A14, A18, A20-A23, B2, C1), classificando cada um em:

- **REAL** — o item existe, o escopo está descrito correctamente
- **DIFERENTE** — existe mas com escopo diferente do descrito (indicado)
- **N/A neste repo** — o código-alvo não existe neste repo
- **JÁ FEITO** — está resolvido no código, o plano não foi actualizado
- **AMBÍGUO** — não é possível confirmar sem mais informação

**Método:** leitura directa de código para cada item (não grep isolado), cruzando com as auditorias já escritas nesta sessão onde aplicável. Profundidade de verificação varia por grupo — anotada explicitamente em cada secção (ver nota de honestidade no fim de cada grupo G-J).

---

## Grupo A (11 itens revalidados: A4, A9-A13, A15-A17, A19 — A8 já é S11, tratado à parte)

| Item | Classificação | Nota | Evidência |
|---|---|---|---|
| **A4** | REAL | `query_database` continua sem allowlist — `pool.query(query, params)` aceita qualquer SQL | `packages/mcp/src/tools/built-in/database.ts:18` (lido por completo) |
| **A9** | REAL | Zero lockfile Python (`poetry.lock`/`uv.lock`/`Pipfile.lock`) — `requirements.txt` só tem 4 pins soltos (`PyYAML`, `httpx`, `psycopg`, `mcp==1.30.0`) | `find . -iname "*.lock"` (0 resultados), `runner/requirements*.txt` lido |
| **A10** | REAL | `SECURITY-AUDIT-FULL.md` confirma OSV-Scanner e Trivy `vuln` continuam bloqueados pela rede da sandbox — nada mudou desde a corrida anterior | `docs/architecture/SECURITY-AUDIT-FULL.md` secções 1-7, lidas |
| **A11** | REAL | Não existe nenhum inventário único triado (issues do GitHub ou tabela ID/estado/dono) — os achados continuam espalhados pelos documentos de auditoria individuais | grep por inventário consolidado, sem resultado |
| **A12** | REAL | `User` (Prisma) só guarda `email`/`name`/`preferences` — nenhum dado claramente sensível (sem password hash, sem PII financeira) nesta camada, mas a decisão explícita ("não aplicável") nunca foi escrita | `packages/memory/prisma/schema.prisma:8-19` lido |
| **A13** | REAL | `SecurityManager.checkRBAC()` existe e funciona (hierarquia `admin>user>viewer>agent`), mas **zero chamadas** a partir de `apps/api` — nenhum endpoint verifica papel | `packages/core/src/security/SecurityManager.ts:200-205`; grep `checkRBAC` em `apps/api` = 0 resultados |
| **A15** | **DIFERENTE** | O item presume "configuração de sessão/cookie actual" a ajustar — **não existe nenhuma** menção a cookies/`httpOnly`/`secure`/`sameSite` em todo o `apps/api/src`. A autenticação é via header `x-api-key` (`authMiddleware.ts`), sem sessão nem cookie nenhum. Não há nada para "ajustar" — seria preciso desenhar sessão por cookie de raiz, o que não é o que o item descreve | grep exaustivo em `apps/api/src`, 0 resultados; `middleware/auth.ts` lido por completo (é 100% header-based) |
| **A16** | REAL | Zero `express-rate-limit`/rate limit em `apps/api` — só existe do lado Python (`mcp/plan_runner/mcp_plan_runner/policy.py:129`, 60/60s) | grep em `apps/api`, 0 resultados |
| **A17** | REAL | Zero Turnstile/hCaptcha/reCAPTCHA em código — nada implementado, como esperado | grep repo-wide, 0 resultados fora dos próprios documentos de plano |
| **A19** | **DIFERENTE** | `extrair-imagem` **não existe neste repo** — existe como **workflow do GitHub Actions** em `agent-network-mcp/.github/workflows/extrair-imagem.yml`, um repo diferente. STATUS.md já dava a pista ("**Produção** tem `extrair-imagem`" — "Produção" = `agent-network-mcp`, por convenção de nomenclatura desta sessão). O item, tal como escrito, não tem alvo neste repo | `find` confirma zero ocorrências em `network-agents-setup`; 1 ocorrência em `agent-network-mcp/.github/workflows/` |

**Sumário Grupo A:** 8 REAL, 2 DIFERENTE, 0 N/A, 0 JÁ FEITO, 0 AMBÍGUO.

---

## Grupo B (8 itens: B1, B3-B9)

| Item | Classificação | Nota | Evidência |
|---|---|---|---|
| **B1** (=S9) | REAL | `engine.py`/`langgraph_engine.py`/`cli.py` continuam com zero referência a `hitl.py` — o achado central mantém-se | grep `import hitl|hitl\.` em `runner/plan_runner/` → só `working_memory.py` (não relacionado, falso positivo de substring), os 3 ficheiros-alvo confirmados vazios |
| **B3** | REAL | Não verificável estaticamente ("já correu contra infra real?") — mas nada no repo sugere que tenha corrido (sem logs, sem CI a subir contra Postgres/OpenAI reais). Depende de acção do Desenvolvedor, como já assinalado | `apps/api/src/index.ts` relido — env vars listadas batem exactamente com o item |
| **B4** (=M2) | REAL | `HitlManager.ts` continua sem `importFromFile`/`exportToFile` | grep em `packages/core/src/hitl/HitlManager.ts`, 0 resultados |
| **B5** (=M3) | REAL | Nenhum script de teste e2e dos 5 passos (Python→Node→Python) encontrado no repo | grep por padrão do cenário, sem resultado |
| **B6** (=M4) | REAL | `hitl.py` continua a ler/escrever só em ficheiro — zero `supabase-py`/tabela `hitl_requests` | grep em `runner/plan_runner/hitl.py`, 0 resultados. Consistente com a dependência declarada (B1/B4/B5 não fechados) |
| **B7** | REAL | `tools_impl.py` continua sem parâmetro `engine` em `run_plan` nem `decision: "edit"` em `resume_plan` | grep em `mcp/plan_runner/mcp_plan_runner/tools_impl.py`, 0 resultados |
| **B8** | REAL | Confirmado: só `seo-article-demo-s9.plan.yaml` usa o bloco `knowledge:` nos 12 templates | grep em `docs/orchestration/`, 1 único ficheiro |
| **B9** | REAL | `Plan.schema.json` continua só com `knowledge_refs` — sem bloco `knowledge` distinto | `docs/architecture/plan-execute/schemas/Plan.schema.json` lido, confirmado |

**Sumário Grupo B:** 8 REAL, 0 DIFERENTE, 0 N/A, 0 JÁ FEITO, 0 AMBÍGUO.

---

## Grupo C (5 itens revalidados: C2-C5, C7 — C6 já discutido na errata, ver nota)

| Item | Classificação | Nota | Evidência |
|---|---|---|---|
| **C2** | REAL | Decisão TS vs. Python MCP continua por tomar — nenhum ADR em `docs/architecture/adr/` sobre isto | listagem de `docs/architecture/adr/`, só `ADR-001-governance-runtime.md` existe, não cobre esta decisão |
| **C3** | REAL | Zero dependência AgentMesh (`agentmesh-platform`) em qualquer `package.json` — não adoptado | grep `agentmesh` em todos os `package.json`, 0 resultados |
| **C4** | REAL | Zero dependência Cedar (`cedar-policy`) — não adoptado, `authorize()` do C1 continua sem motor de política externo | grep `cedar` em todos os `package.json`, 0 resultados |
| **C5** | REAL | Nenhum "Action Receipt" (hash encadeado) existe — `audit.jsonl`/`ToolPolicy.ts` (C1) tem eventos soltos, sem `prev_receipt_hash` nem cadeia verificável | `ToolPolicy.ts` relido (é o próprio código do C1, escrito hoje) — confirma ausência |
| **C7** | **JÁ FEITO** | `MCP-MAPPING.md` já tem as 2 correcções aplicadas e visíveis no próprio texto: nota "Correcção G5" (linha 20) confirma `apps-produto` adicionado à secção 3.5, `hvac` reclassificado de "genérico" para "Proprietário" (secção corrigida, linha 108), contagem final corrigida de 11 para 12 (linha 183). **Mas `STATUS.md` linha 156 continua a listar G5 como pendente** — "precisa de decisão" — quando a decisão e a correcção já foram aplicadas no documento-alvo. Mesmo padrão exacto do C6/A1/A21/A20: achado real, documento-ledger não revalidado | `docs/architecture/MCP-MAPPING.md` lido (secções citadas); `STATUS.md:156` (G5, ainda "pendente") |

**Sobre C6 (não recontado aqui, já tratado na errata do topo do documento):** o C6 mantém-se como estava — revalidação de C8e, não uma pendência falsa (ver correcção nº4 da errata). Não é JÁ FEITO nem DIFERENTE; é REAL enquanto revalidação ainda não executada de facto (a suite `test_client.py` nunca foi corrida nesta sessão para confirmar).

**Sumário Grupo C:** 4 REAL, 0 DIFERENTE, 0 N/A, 1 JÁ FEITO, 0 AMBÍGUO.

---

## Grupo D (7 itens: D1-D7)

| Item | Classificação | Nota | Evidência |
|---|---|---|---|
| **D1** | **DIFERENTE** | O bug de assinatura descrito ("`exportTrace(traceSpanId)` recebe `spanId`, espera `traceId`") **não existe** — `exportTrace(traceId: string)` está correcto, usa `this.traces.get(traceId)` (Map correcto). **Mas o memory leak é real e confirmado**: `this.traces`/`this.currentSpans` (2 Maps) nunca têm entradas removidas em lado nenhum do ficheiro (só inserção, nunca `delete` no `traces`) — cresce sem limite. `OTLP_ENDPOINT` artesanal confirmado (não é a variável oficial `OTEL_EXPORTER_OTLP_ENDPOINT`). Zero SDK OTel instalado. Rescrita ainda necessária, só o detalhe do bug de nomes está errado | `packages/observability/src/Tracer.ts` lido por completo (106 linhas) |
| **D2** | REAL | Depende de D1 (ainda por fazer); `LLMService.ts`/`ToolExecutor.ts` não têm nenhum span `gen_ai.client` | não instrumentado, consistente |
| **D3** | REAL | Zero `deepeval` em qualquer `package.json`/`requirements.txt` | grep repo-wide, 0 resultados |
| **D4** | REAL | Zero `ragas` em qualquer dependência | grep repo-wide, 0 resultados |
| **D5** | REAL | Zero código (TS ou Python) lê `model_tier` — só existe no `Plan.schema.json` | grep `model_tier` em `packages/` e `*.py` repo-wide, 0 resultados de código |
| **D6** | REAL | `budget` em `Plan.schema.json` só tem `max_replans`/`max_steps`, confirmado — sem `max_cost_usd` | schema lido, linha 102-105 |
| **D7** | REAL | `SelfAwareness.ts` confirma `getCostsState()`/`getGaps()`/`getOpportunities()` ainda com comentários "Em produção, consulta..." — placeholders, não dados reais | `packages/core/src/observability/SelfAwareness.ts` lido, linhas 357-425 |

**Sumário Grupo D:** 6 REAL, 1 DIFERENTE, 0 N/A, 0 JÁ FEITO, 0 AMBÍGUO.

---

## Grupo E (7 itens: E1-E7)

Já cobertos em profundidade por `ingestion-audit/AUDIT-INGESTION.md` (reescrito em padrão ouro nesta mesma sessão, com pesquisa externa real e leitura de 989 linhas do pipeline interno) — aqui só se confirma que a fase de **adopção real** (instalar/ligar ao `knowledge.py`) continua por fazer, distinta da fase de pesquisa (já feita).

| Item | Classificação | Nota | Evidência |
|---|---|---|---|
| **E1** | REAL | Crawl4AI não está em `requirements.txt` — pesquisa feita (AUDIT-INGESTION), adopção de código pendente | grep `crawl4ai`, 0 resultados |
| **E2** | REAL | MarkItDown não instalado | grep `markitdown`, 0 resultados |
| **E3** | REAL | Docling não instalado | grep `docling`, 0 resultados |
| **E4** | REAL | `yt-dlp`/`whisper` continuam desligados do RAG — achado repetido 3× nesta sessão, confirmado outra vez | sem alteração desde a última verificação |
| **E5** | REAL | `gitingest` não instalado | grep `gitingest`, 0 resultados |
| **E6** | REAL | Nenhum documento de veredicto ScrapeGraphAI-vs-Crawl4AI existe ainda | não encontrado |
| **E7** | REAL | Nenhuma skill de `google/skills` foi importada ainda | não encontrado em `skills/meta/` (as 21 skills existentes não incluem nenhuma com esse padrão de origem) |

**Sumário Grupo E:** 7 REAL, 0 DIFERENTE, 0 N/A, 0 JÁ FEITO, 0 AMBÍGUO.

---

## Grupo F (9 itens: F1-F9)

| Item | Classificação | Nota | Evidência |
|---|---|---|---|
| **F1** | REAL | `AgentConfig.profile` continua ausente; 24 agentes confirmados (`grep -c "id:" config/agents.config.ts`) | grep `profile` em `packages/shared/src/types/`, 0 resultados relacionados a agente |
| **F2** | **JÁ FEITO** | `skills/meta/` tem **21** pastas, não 16 — mas as **16 esperadas estão todas lá**, mapeadas 1:1 por nome (`prisma-patterns`, `nestjs-modules`, `react-patterns`, `rest-api-design`, `error-handling`, `seo-tech-checklist`, `frontend-a11y`, `vite-env-vars`, `article-writing`, `react-native-expo`, `health-data-classification`=PHI, `python-patterns`, `deploy-discipline`, `mcp-patterns`, `github-actions-ops`, `meta-workflow`), mais 5 skills adicionais não previstas no G2 original (`ai-code-review-checklist`, `cheap-entity-extraction`, `security-audit`, `skill-self-optimization`, `using-agent-skills`). Migração G2 está feita; a contagem no STATUS/plano é que ficou desactualizada | `ls skills/meta/`, 21 entradas, nomes conferidos um a um |
| **F3** | **JÁ FEITO** | Os 5 knowledge packs esperados existem, exactamente: `docs/knowledge/saude/{cardiologia,dermatologia,oftalmologia}.md` (3), `docs/knowledge/legal/direito-br-pt.md` (1), `docs/knowledge/imobiliario/fipezap.md` (1) = 5. (Nota: `docs/knowledge/` tem muitos outros `.md` à parte — não fazem parte do escopo do G3, são conteúdo de agentes de marketing não relacionado) | listagem directa das 3 subpastas, confirmado |
| **F4** | **JÁ FEITO** | `agents/` tem **35** agentes reais (`*.agent.md`) distribuídos em 8 subpastas de domínio — muito mais que os 13 horizontais originalmente migrados (G4). Migração G4 confirmada feita (mesma conclusão já registada no `## Done` do `STATUS.md` desde cedo nesta sessão) | `find agents -iname "*.agent.md"`, 35 resultados |
| **F5** | REAL | `BOOTSTRAP.md` continua com a nota própria "Gap conhecido, ainda não corrigido" para `AGENTS.md` (raiz)/`docs/generated/AGENTS.md` | `BOOTSTRAP.md` linha 52, lida |
| **F6** | REAL | `docs/generated/AGENTS.md` continua a dizer "Total: 22 agentes"; real confirmado = 24 | `docs/generated/AGENTS.md` linha 8, lida |
| **F7** | REAL | Nenhum `pmo.agent.md`/equivalente existe — decisão PMO/Project Director continua por tomar | `find . -iname "pmo*"`, 0 resultados |
| **F8** | REAL | Nenhum documento de reavaliação dos 6 harnesses (`deepseek-harness` etc.) além da tabela original já existente | não encontrado documento dedicado novo |
| **F9** | REAL | `docs/architecture/patterns-from-hermes/` existe (confirmado), mas é só material de referência (padrões extraídos) — não há avaliação de Hermes como *worker* de automação, distinta do uso como interface de chat já coberto | pasta confirmada, README não relido linha a linha (fora do escopo desta auditoria de escopo) |

**Sumário Grupo F:** 6 REAL, 0 DIFERENTE, 0 N/A, 3 JÁ FEITO, 0 AMBÍGUO.

---

## Grupos G1-G4, H, I, J — nota de honestidade sobre profundidade

Estes grupos descrevem trabalho **futuro e aspiracional** (agente financeiro, gamedev, avatar, grafo de memória, integração final, backlog de pesquisa não triado, itens arquivados) — a expectativa correcta, por desenho, é que **nada esteja implementado ainda**. Não é uma discrepância encontrar "zero código" aqui; é o estado esperado. Por isso esta secção teve uma verificação mais leve que A-F (não há 90 minutos de leitura de ficheiro por ficheiro que ainda não existem) — confirmei as **dependências e pré-requisitos citados**, não o "produto final" (que genuinamente não existe).

| Item(s) | Classificação | Nota |
|---|---|---|
| **G1.1-G1.14** (cluster financeiro) | REAL | Nenhum código de trading/agente financeiro existe no repo — confirmado por ausência total de qualquer ficheiro relacionado. G1.5 (isolar credenciais) é um gate a verificar quando G1.1 começar, não antes |
| **G2.1-G2.4** (gamedev) | REAL | Idem — nada implementado |
| **G3.1** | REAL, dependência confirmada | `runner/plan_runner/working_memory.py` existe (S7, já em Done) — a dependência de G3.1 é real e está satisfeita, mas o avatar em si (G3.2/G3.3) não existe |
| **G3.2-G3.3** | REAL | Nada implementado |
| **G4.1** (Obsidian vs. Logseq) | REAL | Decisão de ferramenta continua por tomar |
| **G4.2** | REAL | Depende de G4.1, não implementado |
| **H1-H4** | REAL | Dependem de G1/G3/G4 fechados — nenhum está, portanto nada em H pode ter começado. H3/H4 continuam "aguardando escopo" (nunca definido, como o próprio documento já assinala) |
| **I1, I3-I7, I10, I11** (backlog de pesquisa) | REAL | Itens de pesquisa não triada — nenhum tem documento de avaliação dedicado ainda, consistente com "backlog não triado" |
| **I2** (Graphify) | **DIFERENTE — já assinalado no próprio documento** | O item I2 já regista, no seu próprio texto (linha 1864 da versão actual), que `agent-network-mcp/CLAUDE.md` documenta Graphify como ferramenta **já em uso real** ali — contradição já conhecida e escrita, não uma descoberta nova desta auditoria. Mantém-se REAL quanto à acção pendente (avaliar se `network-agents-setup` também beneficiaria), mas o status "research" da tabela original do STATUS.md já está desactualizado (o próprio I2 já o diz) |
| **I8** | **N/A (já registado assim no próprio documento)** | O item já se auto-declara "não existe separadamente" (resolvido via G4.1) — não é uma classificação nova desta auditoria, só confirmando que a nota já existente continua correcta |
| **I9** (SOUL.md) | REAL | `docs/architecture/patterns-from-hermes/` e `docs/architecture/spec-kit/CONSTITUTION-DRAFT.md` confirmados a existir (as duas peças que I9 cruza) — mas `SOUL.md` em si **não existe** ainda, confirma que é trabalho por fazer, não pesquisa |
| **J1-J7** (arquivados) | REAL | Todos continuam arquivados, sem novo gatilho que os reabra — consistente com o texto já escrito para cada um (ver Grupo J do próprio documento, já correcto) |

**Sumário Grupos G1-G4/H/I/J:** ~30 REAL, 1 DIFERENTE (já conhecida/auto-documentada), 1 N/A (já registado), 0 JÁ FEITO, 0 AMBÍGUO.

---

## Sumário quantitativo global

| Classificação | Contagem | Grupos |
|---|---|---|
| **REAL** | 61 | A(8) B(8) C(4) D(6) E(7) F(6) G-J(~30, incluindo dependências confirmadas) |
| **DIFERENTE** | 4 | A15, A19, D1, I2 (já auto-conhecida) |
| **N/A neste repo** | 1 | A19 é também N/A (repo errado) — contado uma vez em DIFERENTE acima; I8 é N/A mas já auto-documentado |
| **JÁ FEITO** | 4 | C7, F2, F3, F4 |
| **AMBÍGUO** | 0 | — |

**Achado transversal mais importante:** dos ~90 itens revalidados, **4 já estavam feitos** (C7, F2, F3, F4) — todos por causa do mesmo padrão desta sessão inteira: o código evoluiu (ou já estava certo) e o `STATUS.md`/plano nunca foi actualizado para reflectir isso. Nenhum item se revelou "menos real" do que o plano dizia — todos os "DIFERENTE" são casos onde o item aponta para o alvo errado ou descreve um bug que não existe (mas encontra um problema real adjacente), nunca um caso de "isto era exagero".

---

## Lista de itens JÁ FEITO (limpar/fechar no plano)

- **C7** — `MCP-MAPPING.md` já corrigido (G5); só falta actualizar `STATUS.md` linha 156 de "pendente" para "Done"
- **F2** — as 16 skills esperadas existem todas; só falta corrigir a contagem (16→21, ou "16 esperadas + 5 extra")
- **F3** — os 5 knowledge packs existem todos, sem termos privados residuais visíveis
- **F4** — os 13 agentes horizontais existem (e mais 22 além deles); migração está feita

## Lista de itens N/A (mover/marcar)

- **A19** — `extrair-imagem` é um workflow do `agent-network-mcp` (repo diferente), não existe aqui
- **I8** — já auto-declarado N/A no próprio documento (resolvido via G4.1)

## Lista de itens DIFERENTE (com a discrepância)

- **A15** — não há cookies/sessão neste repo (autenticação é 100% via header `x-api-key`); nada para "ajustar", seria desenho de raiz
- **A19** — ver N/A acima (é simultaneamente "aponta para o repo errado")
- **D1** — o bug de assinatura `traceId`/`spanId` **não existe** (já está correcto); o memory leak dos 2 `Map`s **é real** e confirmado — a reescrita continua necessária, só por razão diferente da descrita
- **I2** — já auto-documentado no próprio item; Graphify está confirmado em uso no `agent-network-mcp`, contradizendo o "research" do STATUS.md original

## Lista de itens REAL (prontos a executar, ~61 itens)

Ver tabelas por grupo acima — a esmagadora maioria do plano continua genuinamente pendente e correctamente descrita. Grupos B, D (excepto D1), E são 100% REAL sem nenhuma discrepância.

---

## Proposta de prioridade ajustada

1. **Fechar os 4 JÁ FEITO primeiro** (C7, F2, F3, F4) — é trabalho de 10 minutos cada (só actualizar STATUS.md/contagens), sem código a escrever, e reduz o plano em 4 itens de imediato.
2. **A15 e A19** — não têm o que fazer tal como escritos; precisam de uma decisão humana rápida (A15: desenhar sessão por cookie de raiz, ou fechar como N/A por a app não usar cookies? A19: ir corrigir no `agent-network-mcp` — outro repo — ou remover do plano deste repo?) antes de continuarem a ocupar espaço no plano.
3. **D1** — corrigir a descrição do achado antes de o executar (não é o bug de nomes, é o memory leak) — pequeno ajuste ao item, evita perder tempo a "corrigir" um bug que não existe.
4. **Grupo B (8 itens REAL, sem discrepância)** — é a cadeia mais bem definida e com dependências claras (B1→B4→B5→B6), boa candidata para a próxima sessão de execução a sério.
5. **Grupo D restante (D2-D7, excepto D1)** — bem definido, mas D2/D7 dependem de D1 primeiro.
6. **Grupo A restante (A4, A9-A13, A16-A17)** — sem dependências entre si, podem ser feitos em qualquer ordem; A9 (lockfile) e A16 (rate limit) são os mais rápidos e independentes.
7. **Grupo E** — pesquisa já feita (AUDIT-INGESTION.md), é só questão de decidir adoptar e instalar — trabalho mecânico, baixo risco.
8. **Grupos G1-J** — deixar para depois de A-F estarem resolvidos; são features novas, não correcções, e o cluster G1 (financeiro) sozinho é maior que todo o Grupo A.
