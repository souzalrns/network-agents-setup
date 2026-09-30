# Auditoria de Memória Persistente + Aprendizagem Autónoma — 2026-09-20

**Objectivo:** mapear repositórios relevantes para resolver o gap **L7** (auto-extracção de memória) e reforçar **L4** (memória semântica) do setup do utilizador, com evidência de código real — não de README.

**Método:** 5 subagentes de investigação em paralelo (um por categoria), cada um com acesso a WebSearch/WebFetch/clone raso de repositórios, consulta directa à API do GitHub, OSV.dev e GitHub Security Advisories. ~50 repositórios + 4 papers avaliados no total. Cada afirmação abaixo tem `ficheiro:linha` ou URL de commit citado pelo subagente responsável; onde não foi possível verificar, está marcado **NÃO VERIFICADO** (preservado tal como reportado — não removido nem suavizado).

**Contexto de partida (não reinvestigado aqui):** L4 só existe como JSON Schema (`docs/architecture/memory/contracts.md`), zero código. L5 (RAG) funciona via Supabase+pgvector+Gemini mas estava desligado da execução real (parcialmente ligado nesta sessão). L7 não existe. `working_memory.py` (read-only) e `session_search.py` (FTS5) foram ligados ao motor hoje (S30/S31).

---

## Sumário executivo

### Top 10 (cruzando as 5 categorias)

| # | Repo | Categoria | Classificação | Papel recomendado |
|---|---|---|---|---|
| 1 | **topoteretes/cognee** | 1+4 | ADOPTAR/ADAPTAR | Servidor MCP de memória principal — extracção real + grafo/vector/SQL embutidos, MCP nativo confirmado por código |
| 2 | **mem0ai/mem0** | 1+3 | ADOPTAR/ADAPTAR | Motor de extracção L4 — pipeline ADD/UPDATE/DELETE/NOOP verificado em código, backend `pgvector`/Supabase nativo |
| 3 | **getzep/graphiti** | 1+4+5 | ADOPTAR/ADAPTAR | Alternativa/complemento a Cognee para grafo temporal com supersessão (fecha janela de validade em vez de apagar) |
| 4 | **langchain-ai/langmem** | 2 | ADOPTAR | Biblioteca de memória standalone mais limpa — extracção real, MIT, caminho Postgres/pgvector via `langgraph-checkpoint-postgres` |
| 5 | **vectorize-io/hindsight** | 1 | ADAPTAR | MCP nativo por-banco, Postgres/pgvector directo, zero CVEs — 2ª opção para L4/L7 combinados |
| 6 | **doobidoo/mcp-memory-service** | 1+4 | ADAPTAR (com mitigação obrigatória) | Pipeline harvest→consolidation→decay mais completo — mas 4 CVEs incl. 1 CRITICAL, nunca expor publicamente sem auth |
| 7 | **A-MEM** (agiresearch/A-mem) | 5 | REFERÊNCIA/EXTRAIR | Padrão de notas Zettelkasten auto-evolutivas por-evento (complementa extracção em lote) |
| 8 | **Generative Agents** (joonspk-research) | 5 | REFERÊNCIA/EXTRAIR | Padrão de reflexão periódica (síntese L2→memória de nível superior, disparada por limiar) |
| 9 | **crewAI** `analyze.py`/`encoding_flow.py` | 2 | EXTRAIR | Padrão de dedup por embeddings + consolidação automática (não adoptar o framework) |
| 10 | **CaviraOSS/LongMemory** | 1 | ADAPTAR/EXTRAIR | TypeScript (encaixa em `packages/core`), MCP nativo, zero CVEs, "session porter" para importar logs de outros harnesses — mas extracção é regex, não LLM |

**Para cada função:**
- **L4 (semântica):** mem0 (extracção) ou hindsight (se preferir tudo-em-MCP-nativo)
- **L7 (auto-extracção):** Cognee (pipeline `cognify`, já o mecanismo interno) — reforçado com o padrão de reflexão do Generative Agents para sínteses periódicas de nível superior
- **Vector search:** manter Supabase+pgvector — nenhum vector DB analisado (Qdrant/Chroma/Weaviate/Milvus) justifica substituição. Acção concreta: confirmar versão ≥ 0.8.2 (CVE-2026-3172) e activar `halfvec`/quantização binária, subaproveitadas
- **Grafo (se necessário):** Graphiti com Kuzu embutido (local, sem serviço externo) — só quando/se L6 (consultas relacionais) se tornar necessário; Cognee já inclui um grafo embutido (Kuzu) para quem quiser um único componente
- **Combinação recomendada:** **Cognee como servidor MCP principal** (satisfaz "MCP é o padrão da casa", extracção real, tudo embutido) + padrões de mem0 (ciclo ADD/UPDATE/DELETE) e Generative Agents (reflexão periódica) para enriquecer/informar a extracção, escrevendo no Supabase/pgvector já existente em vez de armazenamento embutido novo

---

## Arquitectura recomendada

```
┌─────────────────────────────────────────────────────────────────┐
│  VM Oracle (ARM, 2 OCPU/12GB) — 130.61.213.226                  │
│                                                                   │
│  ┌──────────────────┐        ┌────────────────────────────┐    │
│  │  Cognee MCP       │◄──────┤  agent-network-mcp /        │    │
│  │  server           │  MCP  │  mcp_plan_runner            │    │
│  │  (cognee-mcp/)    │       │  (clientes MCP já existentes)│    │
│  │                   │       └────────────────────────────┘    │
│  │  remember/recall/ │                                          │
│  │  forget/cognify   │       ┌────────────────────────────┐    │
│  └────────┬──────────┘       │  runner/plan_runner          │    │
│           │                  │  events.jsonl (L2, já existe)│    │
│           │ storage backend  │  session_search.py (S31)     │    │
│           │ = pgvector       │       │                      │    │
│           ▼                  │       ▼ (job periódico novo) │    │
│  ┌──────────────────┐        │  Reflexão estilo Generative  │    │
│  │  Supabase         │◄───────┤  Agents: lê eventos via      │    │
│  │  (Postgres +      │        │  session_search, sintetiza   │    │
│  │  pgvector ≥0.8.2, │        │  memórias L4, chama          │    │
│  │  halfvec activado)│        │  Cognee.remember()           │    │
│  └──────────────────┘        └────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘

Working memory (MEMORY.md, S30) continua read-only e curada por humano,
já ligada ao arranque do run — não substituída, complementar ao L4 automático.
```

**Porquê Cognee como front-door em vez de mem0 directo:** mem0 não tem servidor MCP first-party confirmado (só integrações comunitárias) — como MCP é o padrão da casa, expor a memória via um servidor MCP nativo e real (Cognee, código lido e confirmado) é mais alinhado do que embrulhar mem0 manualmente. O storage do Cognee é plugável — configurar para escrever no Postgres/pgvector do Supabase já existente evita montar LanceDB/Kuzu como armazenamento adicional (mantém "zero infra nova").

---

## Plano de implementação (fases)

1. **Fase 0 — Higiene do que já existe (sem tocar em nada novo):**
   - Confirmar versão do pgvector no Supabase ≥ 0.8.2 (CVE-2026-3172, buffer overflow em HNSW paralelo)
   - Avaliar activar `halfvec`/quantização binária no schema `knowledge_chunks_t6` existente

2. **Fase 1 — Piloto isolado do Cognee (lab, sem produção):**
   - Instalar `cognee` + `cognee-mcp` num ambiente de teste (pode ser o próprio portátil, componentes embutidos são leves)
   - Configurar storage backend para apontar ao Supabase (Postgres/pgvector) em vez de LanceDB/Kuzu locais
   - Confirmar que `remember()`/`recall()`/`forget()` funcionam contra dados de teste, sem tocar em `knowledge_chunks_t6` (tabela exclusiva, não partilhar)
   - Mitigar CVE-2026-58473 (config LLM sobrescrita por não-superuser) — confirmar isolamento single-tenant antes de sequer considerar exposição de rede

3. **Fase 2 — Deploy na VM Oracle:**
   - Subir o servidor MCP do Cognee na VM (12GB é confortável para os componentes embutidos)
   - **Nunca expor a porta MCP publicamente sem uma camada de auth própria em frente** — lição directa dos CVEs críticos do mcp-memory-service (leitura sem autenticação) e do Cognee (config overwrite)
   - Ligar o `mcp_plan_runner`/`agent-network-mcp` como clientes deste novo servidor MCP

4. **Fase 3 — L7 automático real:**
   - Implementar o job de reflexão periódica (padrão Generative Agents): lê eventos recentes via `session_search.py` (já exposto por CLI, S31), sintetiza via LLM, escreve no Cognee via `remember()`
   - Informar o design do prompt de extracção com o ciclo ADD/UPDATE/DELETE/NOOP do mem0 (`configs/prompts.py`) e/ou o padrão per-evento do A-MEM, conforme o volume real de eventos justificar lote vs. streaming

5. **Fase 4 — Validação:**
   - Testar recall real: um agente numa sessão nova consegue recuperar um facto guardado numa sessão anterior?
   - Medir latência/custo de tokens do pipeline de extracção antes de generalizar a todos os planos

---

## O que NÃO usar e porquê

| Repo | Porquê rejeitar |
|---|---|
| **basicmachines-co/basic-memory** | Arquitectura mais próxima do `MEMORY.md` actual (sync Markdown bidireccional), mas **AGPL-3.0** — copyleft, viola a regra de licença permissiva sem excepção. Extrair o padrão, não o código. |
| **getzep/zep** (self-hosted) | Confirmado por leitura directa do README: edição community **descontinuada**, só resta Zep Cloud pago — viola "zero custo recorrente". Usar Graphiti directamente em vez disto. |
| **google/adk-python** (módulo memory) | A única extracção real vive no Vertex AI Memory Bank, serviço GCP **pago**. Sem isso, é só indexação de texto bruto. |
| **microsoft/semantic-kernel** (módulo memory) | Oficialmente marcado `@deprecated` no próprio código-fonte. |
| **mem0ai/mem0-mcp** | Repo **arquivado**; sucessor OpenMemory está a ser descontinuado; 4 CVEs reais de falta de autenticação nos endpoints de gestão de memória. |
| **letta-ai/letta** (Python) | O branch `main` só tem ficheiros meta — o código real foi movido para o branch `archive`, **descontinuado pelos próprios mantenedores**. Sucessor (`letta-code`) é um produto CLI/cloud em TypeScript, não uma lib de memória. Vale só como referência de design (sleeptime agent). |
| **kingjulio8238/memary** | Último commit out/2024 — **abandonado** (regra de 12 meses). |
| **wwskills/dsh-long-memory** | 1 star / 0 forks — risco de manutenção inaceitável como dependência de produção, apesar do padrão de ciclo de vida de regras ser genuinamente relevante. |
| **chroma-core/chroma** | CVE pré-autenticação real (leitura/escrita/eliminação cross-tenant); sem elasticidade de RAM (HNSW tem de estar todo em RAM). Sem vantagem sobre pgvector já em uso. |
| **weaviate/weaviate** | Licenciamento misto (módulo `wl/` proprietário gated por chave); 8 advisories, mais que qdrant. |
| **milvus-io/milvus** | Requer mínimo 8GB RAM só para o standalone — incompatível com os 12GB partilhados da VM. |
| **Aider-AI/aider**, **continuedev/continue** | Confirmado por código/issue oficial: **zero aprendizagem autónoma real** — só ficheiros de convenção manuais (aider) ou RAG de código (continue); o pedido de "memory bank" do Continue foi fechado oficialmente como "not planned". |
| **CaviraOSS/LongMemory** (como L7) | O README sugere extracção "cognitiva" mas o código real (`claim_extractor.ts:24-62`) é **regex puro, sem LLM** — não é auto-extracção no sentido pedido. Útil só como camada complementar barata. |
| **okooo5km/memory-mcp-server, Puliczek/mcp-memory, AojdevStudio/simple-memory-mcp** | Sem licença declarada — REJEITAR sem excepção. |
| **coleam00/mcp-mem0** | >12 meses sem commits — abandonado. |
| **mnemoverse/mcp-memory-server** | Serviço hospedado pago ("one API key") — viola zero-custo/local-first. |
| **MemoriLabs/memori-mcp** | Produto SaaS com quotas (`memori_signup`, `memori_quota`) — não local-first. |

---

## Detalhe completo por categoria (evidência de código, ficheiro:linha)

### Categoria 1 — Memória persistente para agentes (16 repos)

**Método do subagente:** dados de licença/commits verificados via `raw.githubusercontent.com` e páginas `/commits/main`; CVEs via API real do osv.dev; top repos lidos via `raw.githubusercontent.com` (código real, não README).

#### 1. mem0ai/mem0
| Campo | Valor |
|---|---|
| Stars / Licença / Última actualização | ~65.7k / Apache-2.0 / 18 set 2026 |
| Auto-extracção? | **TEM.** `mem0/memory/main.py:879` (`_add_to_vector_store`), fase "LLM extraction" em `:940-991`, chamando `generate_additive_extraction_prompt` (`:948`). Prompts reais: `mem0/configs/prompts.py:15` (`FACT_RETRIEVAL_PROMPT`), `:468` (`ADDITIVE_EXTRACTION_PROMPT`), `:176` (`DEFAULT_UPDATE_MEMORY_PROMPT`, ciclo ADD/UPDATE/DELETE/NOOP) |
| Local-first? | Parcial — lib Python/TS local, mas extractor depende de LLM externo e vector store |
| Python/MCP? | Python (+SDK TS). MCP: sem servidor first-party confirmado no core |
| Peso (RAM) | Baixo como lib; backend `pgvector` real em `mem0/vector_stores/pgvector.py` (psycopg) |
| CVEs conhecidos | 4 CVEs (osv.dev), todos no servidor REST **opcional**: CVE-2026-31240 (HIGH, falta auth), CVE-2026-31245/31241 (MODERATE), CVE-2026-7597 (LOW) |
| Classificação | **ADAPTAR** |
| Justificação | Auto-extracção real e madura, backend pgvector já pronto; CVEs isolados ao servidor REST opcional (não usar) |

#### 2. getzep/graphiti
| Campo | Valor |
|---|---|
| Stars / Licença / Última actualização | ~31k / Apache-2.0 / 21 set 2026 |
| Auto-extracção? | NÃO VERIFICADO a fundo nesta categoria (ver categoria 4 para confirmação por código) |
| Local-first? | Parcial — Kuzu embutido disponível; produção tipicamente usa Neo4j/FalkorDB/Neptune |
| Python/MCP? | Python. MCP: pasta `mcp_server/` dedicada confirmada |
| Classificação | **REFERÊNCIA** (nesta categoria) → revisto para **ADOPTAR/ADAPTAR** após confirmação na categoria 4 |
| Justificação | Motor sólido e activo, mas exige grafo dedicado para uso sério |

#### 3. topoteretes/cognee
| Campo | Valor |
|---|---|
| Stars / Licença / Última actualização | ~30.9k / Apache-2.0 / 18 set 2026 (v1.6.0) |
| Auto-extracção? | **TEM.** Servidor MCP real em `cognee-mcp/src/server.py` (FastMCP). Pipeline `cognify()` em `cognee/tasks/graph/` + `cognee/tasks/entity_completion/` (extractores plugáveis LLM/regex) |
| Local-first? | Parcial-a-total — pode operar 100% com modelos locais; storage plugável incl. Postgres+pgvector |
| Python/MCP? | Python. MCP nativo confirmado por código real |
| CVEs conhecidos | CVE-2026-58473 (GHSA-49f7-whx5-4256), **CRITICAL** — não-superuser sobrescreve config global de LLM. Mitigável em single-tenant |
| Classificação | **ADAPTAR** |
| Justificação | MCP nativo real + extracção real + compatível com Postgres/pgvector; CVE crítico mitigável, não bloqueante em single-tenant |

#### 4. HKUDS/LightRAG
| Campo | Valor |
|---|---|
| Stars / Licença / Última actualização | ~39.8k / MIT / 20 set 2026 |
| Auto-extracção? | NÃO TEM (no sentido L7) — extrai de documentos ingeridos em lote, não deriva de conversas de agentes |
| Classificação | **REJEITAR** (para esta categoria) |
| Justificação | Excelente para RAG documental, não é memória de agente |

#### 5. vectorize-io/hindsight
| Campo | Valor |
|---|---|
| Stars / Licença / Última actualização | ~24.1k / MIT / 20 set 2026 |
| Auto-extracção? | Evidência textual directa do README: *"Behind the scenes, retain uses an LLM to extract key facts, temporal data, entities, and relationships"* — chamada `client.retain(bank_id=..., content=...)` sem pré-estruturação manual. **PROVÁVEL, evidência parcial** (não ficheiro:linha completo, pacote &gt;50MB impediu leitura exaustiva) |
| Local-first? | Sim — Postgres+pgvector ou Oracle AI Database 23ai, self-hosted Docker |
| Python/MCP? | Python (API)+SDKs. **MCP confirmado explicitamente**: endpoint nativo por-bank em `/mcp/{bank_id}/` |
| CVEs conhecidos | 0 no osv.dev; página de advisories confirma "não há nenhum publicado" |
| Classificação | **ADAPTAR** |
| Justificação | Melhor encaixe estrutural na infra existente (Postgres/Supabase, MCP nativo por design), sem CVEs — mas verificação de código do extractor ficou incompleta |

#### 6-11 (triagem, menos aprofundados)
| Repo | Licença/Actividade | Achado principal | Classificação |
|---|---|---|---|
| MemoriLabs/Memori | Apache-2.0 / 18 set 2026 | Extracção reivindicada (87% accuracy), NÃO VERIFICADO a código | REFERÊNCIA |
| memodb-io/memobase | Apache-2.0 / jan 2026 (a arrefecer) | "Buffer zones" reivindicadas, NÃO VERIFICADO; bom modelo de dados (perfil+timeline) | EXTRAIR |
| basicmachines-co/basic-memory | **AGPL-3.0** / 16 set 2026 | Sync Markdown bidireccional real, MCP-nativo, mas licença copyleft | **REJEITAR** (extrair só o padrão) |
| MemTensor/MemOS | Apache-2.0 / 16 set 2026 | MemScheduler reivindicado, NÃO VERIFICADO; MCP não confirmado | REFERÊNCIA |
| letta-ai/letta | Apache-2.0 / 10 set 2026 | Conceitos fortes mas NÃO VERIFICADO a código nesta categoria (ver cat. 2 para achado do branch archive) | REFERÊNCIA |
| wwskills/dsh-long-memory | MIT / 10 set 2026, **1 star/0 forks** | Ciclo de vida de regras (proposed→archived) + Jaccard, conceptualmente próximo do L7, mas risco de manutenção inaceitável | REJEITAR (extrair padrão) |

#### 12. doobidoo/mcp-memory-service
| Campo | Valor |
|---|---|
| Stars / Licença / Última actualização | ~2k / Apache-2.0 / 20 set 2026 (73 PRs numa release) |
| Auto-extracção? | **TEM, confirmado por estrutura real**: pastas `consolidation/`, `harvest/`, `extraction/` existem de facto; tags `harvest:method:llm`/`harvest:method:heuristic` com proveniência |
| Local-first? | Muito forte — SQLite-vec + ONNX local (all-MiniLM-L6-v2, ~90MB), "5ms sem cloud lock-in" |
| CVEs conhecidos | **4 CVEs**: CVE-2026-50027 **CRITICAL** (leitura não-autenticada), CVE-2026-49291 HIGH (escrita/eliminação via OAuth read-only), CVE-2026-33010 HIGH (CORS wildcard), CVE-2026-29787 MODERATE |
| Classificação | **ADAPTAR (mitigação obrigatória)** |
| Justificação | Mais leve + único com harvest E consolidação confirmados por código, mas 4 CVEs sérios — nunca expor na VM (IP público) sem confirmar patch + restringir rede |

#### 13. CaviraOSS/LongMemory
| Campo | Valor |
|---|---|
| Stars / Licença / Última actualização | ~4.5k / Apache-2.0 / 20 set 2026 |
| Auto-extracção? | **TEM, mas por REGEX, não LLM** — `src/core/engine/claim_extractor.ts:24-27,62` e `facet_extractor.ts` confirmados sem nenhuma chamada LLM. Refuta a impressão do README |
| Python/MCP? | **TypeScript** (encaixa em `packages/core`). MCP nativo — pasta `src/mcp/`, "Streamable HTTP MCP" |
| CVEs conhecidos | 0 no osv.dev, advisories confirmam nenhum publicado |
| Classificação | **ADAPTAR** (estrutura/L4) + **EXTRAIR** (session porter) — não confiar como L7 real |
| Justificação | Melhor encaixe de linguagem, MCP nativo, zero CVEs — mas extracção heurística, não substitui uma camada LLM real |

#### 14-16
| Repo | Achado | Classificação |
|---|---|---|
| langchain-ai/langmem | Extracção reivindicada, NÃO VERIFICADO nesta categoria (ver categoria 2, confirmado lá) | EXTRAIR (revisto para ADOPTAR na cat. 2) |
| getzep/zep | README confirma: community edition descontinuada, foco é Zep Cloud pago | **REJEITAR** |
| kingjulio8238/memary | Último commit out/2024 | **REJEITAR (abandonado)** |

---

### Categoria 2 — Frameworks com memória integrada

**Método do subagente:** clonagem rasa + `grep`/`git show` para código real, API do GitHub para metadados, OSV.dev para CVEs.

#### 1. agno-agi/agno
| Campo | Valor |
|---|---|
| Stars / Licença / Última actualização | 42.273 / Apache-2.0 / 2026-09-20 |
| Auto-extracção? | **TEM.** `libs/agno/agno/agent/_managers.py:28` `make_memories()` → `create_user_memories()` (`memory/manager.py:377`), condicionado a `update_memory_on_run` (default `False`, `agent.py:132`) |
| Local-first? | Sim — `db/postgres/` e `db/sqlite/` nativos |
| CVEs conhecidos | 6 no OSV: GHSA-77rh-m34w-rv36 (eval injection, corrigido 2.3.24), **GHSA-82m5-3pcp-hccq (SQL injection, sem "fixed" registado)**, GHSA-vw84-hprm-cxmm (overwrite entre utilizadores, corrigido 2.2.2) |
| Classificação | **ADAPTAR** |
| Justificação | Único com Postgres nativo + extracção activa hoje, mas SQL injection sem correcção confirmada — auditar antes de usar |

#### 2. crewAIInc/crewAI
| Campo | Valor |
|---|---|
| Stars / Licença / Última actualização | 58.829 / MIT / 2026-09-21 |
| Auto-extracção? | **TEM, o mais sofisticado.** `lite_agent.py:696` `_save_to_memory()` automático (não manual). Pipeline: `memory/analyze.py` (`extract_memories_from_content()` :155, `analyze_for_save()` :275, `analyze_for_consolidation()` :333), `memory/encoding_flow.py` (`EncodingFlow` :75, `intra_batch_dedup` :143 por cosine similarity) |
| Local-first? | Parcial — LanceDB/Qdrant-edge nativos; sem backend Postgres/pgvector nativo (extensível via `StorageBackend` Protocol) |
| CVEs conhecidos | 0 no OSV para `crewai` |
| Classificação | **EXTRAIR** |
| Justificação | Não adoptar o framework (orquestração é overkill), mas o trio analyze+encoding_flow+storage é o design mais reaproveitável |

#### 3. langchain-ai/langmem
| Campo | Valor |
|---|---|
| Stars / Licença / Última actualização | 1.674 / MIT / 2026-09-09 |
| Auto-extracção? | **TEM, é o propósito central.** `src/langmem/knowledge/extraction.py:1666` `create_memory_store_manager()`; `MemoryManager` (:217), `MemoryStoreManager` (:832) — procura→extracção→update→delete como `Runnable` agendável em background |
| Local-first? | `InMemoryStore` (dev) + `AsyncPostgresStore` (via `langgraph-checkpoint-postgres`, índice vectorial compatível pgvector/Supabase) |
| CVEs conhecidos | 0 para `langmem`; dependência `langgraph` tem GHSA-g48c-2wqr-h844 (deserialização msgpack insegura) |
| Classificação | **ADOPTAR** |
| Justificação | Único desenhado desde o início como módulo de memória desacoplado, extracção genuína, MIT, caminho Postgres/pgvector real. Custo: adopta `langgraph` como dependência |

#### 4. google/adk-python
| Campo | Valor |
|---|---|
| Stars / Licença / Última actualização | 21.580 / Apache-2.0 / 2026-09-20 |
| Auto-extracção? | **NÃO TEM no código OSS.** `add_session_to_memory()` é chamada manual (`agents/context.py:719,739`). Única extracção real é `memory/vertex_ai_memory_bank_service.py:236` — corre no **serviço pago GCP** |
| Local-first? | Não para memória persistente real — só `InMemoryMemoryService` (não persiste) é não-cloud |
| CVEs conhecidos | GHSA-rg7c-g689-fr3x (Code Injection + Missing Authentication) |
| Classificação | **REJEITAR** |
| Justificação | Viola "zero custo recorrente"/"local-first" directamente |

#### 5. letta-ai/letta (+ letta-code)
| Campo | Valor |
|---|---|
| Stars / Licença | 24.811 / Apache-2.0 |
| Achado crítico | **Branch `main` só tem 12 ficheiros meta** (README, LICENSE, TERMS...) — código Python real está no branch `archive` (último commit real 2026-08-13), declarado "retired" pelos próprios mantenedores. Sucessor real é `letta-ai/letta-code` (Node/TS, "Letta Cloud" pago) |
| Auto-extracção? (branch archive) | **TEM, o padrão mais avançado encontrado**: `letta/groups/sleeptime_multi_agent_v4.py:132` `run_sleeptime_agents()` — agente em background a cada N turnos que reflecte e edita memória sozinho. Tools auto-invocadas pelo LLM: `core_memory_append`/`memory_replace`/`memory_rethink` (`functions/function_sets/base.py:246,311,488`), `archival_memory_insert/search` (:164,194) |
| Local-first? (branch archive) | Sim — `settings.py:273-278` Postgres/SQLite; `orm/passage.py` + `sqlalchemy_base.py:379` usa pgvector |
| CVEs conhecidos | GHSA-7p2g-2vxc-5g55 (controlo de acesso incorrecto, `last_affected: 0.3.17`) |
| Classificação | **REFERÊNCIA** |
| Justificação | Arquitectura mais alinhada ao objectivo (sleeptime agent + memory blocks), mas **abandonada por decisão dos mantenedores**, não por inactividade — risco de manutenção alto demais para adoptar |

#### Outros (triagem, tabela comparativa do subagente)
| Framework | Auto-extracção? | Classificação |
|---|---|---|
| run-llama/llama_index | **TEM** — `FactExtractionMemoryBlock._aput()` (`memory_blocks/fact.py:67,119`), extrai via LLM a cada mensagem | EXTRAIR |
| microsoft/agent-framework | NÃO TEM no core — só hooks `ContextProvider`/`HistoryProvider` | REFERÊNCIA |
| microsoft/autogen | NÃO TEM hoje — "Teachability" só existia na API legada 0.2, descontinuada | REJEITAR |
| langchain-ai/langgraph | Sem extracção embutida (junta-se com langmem para isso) | REFERÊNCIA |
| griptape-ai/griptape | NÃO VERIFICADO suficientemente | NÃO VERIFICADO |
| microsoft/semantic-kernel | **Módulo oficialmente `@deprecated`** no código-fonte | **REJEITAR** |
| stanfordnlp/dspy | Não aplicável — 0 ficheiros de memória, é framework de optimização de prompts | REJEITAR |

---

### Categoria 3 — Sistemas de auto-aprendizagem + Vector DBs

**Método do subagente:** clone raso de aider/mem0 (letta abortou por espaço em disco), leitura de ficheiros crus, osv.dev, GitHub Security Advisories, WebFetch de documentação de deployment real (não marketing).

#### Grupo A — ferramentas "aprender/lembrar"

| Repo | Auto-extracção? | Classificação | Nota |
|---|---|---|---|
| Aider-AI/aider | **NÃO TEM** — só `CONVENTIONS.md` manual (`aider/website/docs/usage/conventions.md`) + cache RAM do repo-map (`aider/repomap.py:210`, é cache não aprendizagem) | REJEITAR (L7) / REFERÊNCIA (conventions file) | 2 CVEs: GHSA-7w7m-v5vp-w699 (code injection), GHSA-hchg-qm84-cj9p (SSRF) |
| continuedev/continue | **NÃO TEM** — issue oficial #4615 "Memory Bank" fechada como "not planned"; `.continue/rules` é markdown estático; `@codebase` é RAG, não memória aprendida | REFERÊNCIA | Indexação local via LanceDB+SQLite (bom padrão de referência) |
| mem0ai/mem0 (reconfirmado) | Ver categoria 1 — pipeline completo em `main.py:879-1120`, com **entity linking automático** (Phase 7, :1080-1110) confirmado nesta leitura mais profunda | **ADOPTAR/ADAPTAR** | **Achado novo desta categoria:** suporte nativo directo a Supabase via `mem0/vector_stores/supabase.py:1-40` (biblioteca `vecs`), além do `pgvector.py:146,271` (HNSW) |
| letta-ai/letta (reconfirmado) | Ver categoria 2 | REFERÊNCIA | Confirma achado do branch `archive` |
| getzep/zep (reconfirmado) | Não self-hosted | **REJEITAR** | README confirma "Zep Community Edition is no longer supported" |

#### Grupo B — Vector DBs (avaliação fria vs. pgvector já em uso)

| Repo | Peso RAM | CVEs | Classificação |
|---|---|---|---|
| **pgvector/pgvector** (já em uso) | Depende do índice (HNSW &gt; IVFFlat; `halfvec` reduz ~50%) | **CVE-2026-3172** — buffer overflow em builds paralelos HNSW, v0.6.0–0.8.1, corrigido em **0.8.2** | **ADOPTAR (já adoptado) — optimizar, não substituir** |
| qdrant/qdrant | Mais elástico — modo "cold"/mmap, cache só do subconjunto activo | GHSA-f632-vm87-2m2f (escrita arbitrária), GHSA-xcr2-h8hv-6227 (path traversal) | REFERÊNCIA |
| chroma-core/chroma | **Rígido** — HNSW "must reside in RAM", min. ~2GB | 4 GHSAs, incl. **acesso cross-tenant sem auth** e code injection pré-auth | **REJEITAR** |
| weaviate/weaviate | ~2× tamanho bruto dos vectores | 8 advisories (path traversal ×2, autorização imprópria, DoS); **licenciamento misto** (módulo `wl/` proprietário) | **REJEITAR** |
| lancedb/lancedb | **O mais leve** — mmap, RSS pequeno mesmo com índices grandes (usado pelo próprio Continue.dev) | NÃO VERIFICADO | REFERÊNCIA |
| asg017/sqlite-vec | Muito leve (extensão SQLite) | NÃO VERIFICADO | REFERÊNCIA |
| milvus-io/milvus | **Requer mín. 8GB só para standalone** (+ etcd+MinIO) | NÃO VERIFICADO | **REJEITAR** (RAM incompatível) |

---

### Categoria 4 — MCP servers de memória (24 servidores)

**Método do subagente:** GitHub API, leitura de código real via CDN/raw, osv.dev + GitHub Security Advisories.

#### Top candidatos

| Repo | Stars/Licença/Actividade | Auto-extracção (evidência) | CVEs | Classificação |
|---|---|---|---|---|
| **Cognee MCP** | 30.900 / Apache-2.0 / 2026-09-18 | `remember()`→`cognee_client.remember()`→pipeline "add+cognify"; `improve()` corre 9 estágios incl. `triplet_enrichment` (`cognee-mcp/src/server.py`) | GHSA-49f7-whx5-4256 (baixa) | **ADOPTAR** |
| **Graphiti MCP** | 31.032 / Apache-2.0 / 2026-09-21 | `add_memory()`→`queue_service.add_episode()`→`LLMClientFactory` extrai entidades/factos (`mcp_server/src/graphiti_mcp_server.py`) | GHSA-gg5m-55jj-8m5g (Cypher injection, moderada) | **ADOPTAR/ADAPTAR** |
| **mcp-memory-service** | 1.952 / Apache-2.0 / 2026-09-20 | `AutoCaptureService.capture()` (`harvest/auto_capture.py`), `SessionHarvester._harvest_file()` (`harvest/harvester.py`), dedup Jaccard &gt;0.35, refino via `HarvestRewriter.rewrite_batch_sync()`, módulo `consolidation/` com decay/forgetting/compression/contradictions/belief | **8 advisories** (Critical ×3 — auth bypass, SSE sem auth, API sem auth; High ×2; Moderate ×3) | **ADAPTAR** (mitigação obrigatória) |
| Official Memory Server (modelcontextprotocol) | 90.506 (monorepo) / MIT-Apache-2.0 / 2026-09-03 | **NÃO TEM** — 9 tools manuais, busca por substring | Nenhum | **REFERÊNCIA** (baseline de schema) |
| basic-memory | 4.010 / **AGPL-3.0** / 2026-09-16 | Colaborativo (humano edita, LLM lê/escreve), não autónomo | 0 | **REJEITAR** (licença) |
| mem0-mcp + OpenMemory | 663 / Apache-2.0 / **archived** | Sim ao nível mem0 core, mas repo MCP arquivado, sucessor a ser descontinuado | 4 GHSAs (falta de auth) | **REJEITAR** |
| memento-mcp | 424 / MIT / **2025-10-27** (~11 meses, no limiar de abandono) | NÃO TEM — manual, mas **decay scoring com half-life configurável + reinforcement** é um padrão valioso | NÃO VERIFICADO (Neo4j 5.13+ obrigatório, pesado) | **EXTRAIR o padrão** |
| mcp-local-memory | 56 / MIT / 2026-09-14 | **TEM, configurável** — `ARCHIVIST_STRATEGY`: passive/NLP(default)/LLM/hybrid, 100% local sem rede | NÃO VERIFICADO (projecto pequeno, baixo escrutínio) | **ADAPTAR** (único genuinamente leve p/ portátil 1GB) |
| mcp-memory-keeper | 135 / MIT / 2026-09-03 | NÃO TEM (é gestão de contexto/checkpoints, não aprendizagem) | NÃO VERIFICADO | **EXTRAIR** (padrão de perfis de tools + checkpoints/sessões) |

#### Rejeitados na triagem (sem análise profunda)
memobase (sem MCP oficial claro — REFERÊNCIA), mnemoverse (serviço hospedado pago — REJEITAR), memori-mcp (SaaS com quotas — REJEITAR), MemoryMesh (manual-only, fora de âmbito), coleam00/mcp-mem0 (**abandonado**, >12 meses), okooo5km/Puliczek/AojdevStudio (**sem licença** — REJEITAR sem excepção), shaneholloman/mcp-knowledge-graph (fork idêntico ao oficial), mem-port (conceito interessante, não aprofundado), membase-mcp (blockchain-based, desalinhado), hpkv-io/blueman82/CanopyHQ (404 — **NÃO VERIFICADO**, possivelmente removidos).

---

### Categoria 5 — Papers/protocolos

Ver secção "Sumário executivo" acima para a síntese. Detalhe completo:

| Paper | Padrão central | Implementação real | Aplicável ao L7? |
|---|---|---|---|
| **MELD** (arXiv:2608.16357, ago 2026) | Protocolo de fusão entre memórias de agentes distribuídos/soberanos (5 saídas: insert/merge/relate/conflict/reject, "Patch" auditável) | NÃO ENCONTRADA | Não agora — só se federar múltiplas instâncias |
| **CoALA** (arXiv:2309.02427) | Taxonomia modular (working/episódica/semântica/procedural) + espaço de acções — é a origem académica da taxonomia L0-L6 já em uso | NÃO ENCONTRADA (é conceptual) | Parcial — valida a arquitectura, não o mecanismo |
| **Generative Agents** (arXiv:2304.03442) | Memory stream + **reflection tree**: limiar de importância → LLM sintetiza L2→memórias de nível superior com pointers às fontes | `joonspk-research/generative_agents` (20k★, **congelado desde ago/2023**) | **Sim, directamente** |
| **MemGPT** (arXiv:2310.08560) | Paginação de contexto estilo SO + gravação oportunista via tool-call durante a conversa | `letta-ai/letta` (~24-25k★, activo) — mapeamento função-a-função fortemente corroborado mas não lido em 1ª mão nesta categoria | Parcial — resolve L1→L2, não um pipeline dedicado |
| **A-MEM** (arXiv:2502.12110, NeurIPS 2025, adicionado) | Notas Zettelkasten auto-organizáveis; nova memória pode refactorar notas vizinhas ("evolução contínua") sem intervenção humana | `agiresearch/A-mem` (~1.2k★, código real) | **Sim, directamente** |
| **Mem0 paper** (arXiv:2504.19413, adicionado) | Extracção single-pass ADD-only + 2º estágio de dedup/merge multi-sinal | `mem0ai/mem0` (65.7k★) | **Sim, directamente** — mais barato (91% menos latência p95, &gt;90% menos custo de tokens, reportado pelos autores) |
| **Zep/Graphiti paper** (arXiv:2501.13956, adicionado) | Grafo de conhecimento temporal; contradição **fecha janela de validade em vez de apagar** | `getzep/graphiti` (31k★, activo, Kuzu embarcado) | **Sim** — cobre L7+L4 (supersessão temporal) simultaneamente |
| "Missing Knowledge Layer" (arXiv:2604.11364, abr 2026, adicionado) | 4 políticas de persistência distintas por tipo de dado (Knowledge/Memory/Wisdom/Intelligence) | NÃO VERIFICADO (repo não confirmado publicamente) | Parcial — grade conceptual para decidir TTL/regra de update por tipo de facto extraído |

---

## Auto-crítica (consolidada dos 5 subagentes)

**O que NÃO foi verificado:**
- Peso real de RAM em produção (não simulação) para a maioria dos repos — só estimativas/documentação oficial, não medição directa
- `letta-code` (sucessor do letta) não foi investigado em profundidade — fora do orçamento desta investigação
- CVEs de repos fora do "top 5" de cada categoria — só triagem superficial (licença/actividade), não verificação exaustiva de segurança
- Contagens exactas de stars/forks em alguns casos vieram de leitura de página HTML, não da API REST (rate-limited a meio de uma investigação sem token) — ordem de grandeza fiável, número exacto não
- griptape-ai/griptape não foi aprofundado (falta de tempo/orçamento do subagente da categoria 2)

**Onde os subagentes podem estar errados:**
- A classificação de "hindsight" como ADAPTAR assenta em evidência textual do README + 1 chamada de exemplo, não em leitura completa do extractor (pacote grande demais para o método usado)
- A recomendação de Cognee como servidor MCP principal não foi testada em runtime nesta investigação — é uma inferência a partir de código lido, não um piloto validado
- O estado de "abandono" do letta (Python) é uma interpretação da declaração dos mantenedores no README, não uma auditoria do que efectivamente acontece ao código no branch `archive` daqui para a frente
