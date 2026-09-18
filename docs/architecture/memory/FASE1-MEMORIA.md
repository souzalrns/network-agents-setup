# Fase 1 — Auditoria de memória: estado actual + dsh-long-memory + Graphiti + Cognee

Primeira fase da auditoria de memória/conhecimento/federação pedida. Tudo abaixo foi verificado por leitura directa de código (ficheiros deste repo + `pyproject.toml`/`package.json`/schemas dos 3 projectos externos), não por confiança em descrição de README. Onde não foi possível confirmar, está marcado **NÃO VERIFICADO**.

## 1. Achado prévio, decisivo para tudo o resto

Este repo **já tem uma arquitectura de memória em 7 camadas desenhada** (`docs/architecture/memory/ARCHITECTURE.md`), com contratos JSON Schema próprios (`contracts.md`). Isto não estava reflectido em nenhum documento produzido hoje até agora — nem no `ECOSYSTEM.md`, nem no `ADR-001`, nem no `STATUS.md`. Resolve também a confusão "L5 vs C8/T6" de conversas anteriores: **é a mesma coisa** — L5 é o nome da camada no desenho arquitectural; C8/T6 foi o identificador da iniciativa que a implementou hoje.

```
L0  IDENTITY / POLICY     git, humano                      -- CLAUDE.md/AGENTS.md (precisam de reconciliação, já identificado)
L1  WORKING               RAM/run state, efémero           -- status.json + estado em memória do runner
L2  EPISODIC              append-only log                  -- events.jsonl (EventLog) -- IMPLEMENTADO
L3  PROCEDURAL            skills/ em git                    -- skills/**/SKILL.md -- IMPLEMENTADO
L4  SEMANTIC              factos estáveis (remember/recall/forget) -- SÓ CONTRATO, sem implementação de escrita/API
L5  DOMAIN KNOWLEDGE       corpus RAG multi-KB               -- IMPLEMENTADO (C8/T6) MAS NÃO LIGADO à execução real
L6  RELATIONAL             grafo de entidades (opcional)     -- VAZIO, nada implementado
```

## 2. Matriz de capacidades

| Capacidade | Implementação actual | Limitação | Importância |
|---|---|---|---|
| Memória episódica | `events.jsonl` (`EventLog`, append-only JSONL) | Sem índice, sem query estruturada — só grep/parse linear | Alta — já em uso real |
| Memória semântica | Contrato `remember`/`recall`/`forget` (L4) definido em JSON Schema | **Sem implementação** — nenhum código escreve/lê L4 hoje | Alta — é o gap mais imediato |
| Memória procedural | `skills/**/SKILL.md` em git | Nenhuma — funciona bem | Já resolvido |
| Preferências | `working_memory.py` (`MEMORY.md` por cliente) | Curadoria **humana**, só leitura, sem auto-extracção | Média |
| Memória de sessão | `status.json` (L1, efémero) | Não sobrevive ao fim do run — por desenho | Já resolvido para o caso de uso actual |
| Memória persistente | `events.jsonl` + `knowledge_chunks_t6` (Supabase) | Persistente mas sem consolidação entre runs | Média |
| Temporalidade | **Ausente** — nem `events.jsonl` nem `knowledge_chunks_t6` têm `valid_at`/`invalid_at` | Um facto que muda não invalida o antigo, só acrescenta | Depende do caso de uso — não crítico hoje |
| Versionamento | Parcial — `content_hash` em `knowledge_chunks_t6` deteta mudança de ficheiro-fonte | Sem histórico de versões anteriores, só substitui | Baixa-média |
| Actualização de factos | **Ausente** no L4 (não implementado); no L5, `replace_chunks` substitui por completo | Sem mecanismo de "actualizar 1 facto" | Média |
| Invalidação de factos | **Ausente** | — | Baixa-média |
| Consolidação | **Ausente** | Nada resume/funde memórias antigas | Baixa hoje, sobe se o volume crescer |
| Deduplicação | **Ausente** explicitamente (existe supersessão básica no dsh-long-memory externo, não aqui) | — | Média |
| Conflitos | **Ausente** | — | Baixa hoje |
| Relações entre entidades | **Ausente** (L6 vazio) | — | Depende de precisar de multi-hop |
| Busca lexical | **Ausente** no `knowledge.py` actual (só vector via Gemini embeddings) | Sem FTS/BM25 | Média |
| Busca vetorial | **Implementada** — `embedder.py` + `supabase_writer.py` (pgvector) | Falha por quota Gemini (já documentado em `RATE-LIMITS.md`) | Alta, já crítica |
| Busca híbrida | **Ausente** | Só vetorial | Média |
| Knowledge graph | **Ausente** (L6 vazio) | — | Depende do caso de uso |
| Multi-hop retrieval | **Ausente** | — | Depende do caso de uso |
| Provenance | Parcial — `citation.source` no formato de hit do L5 | Sem `locator` real (já documentado no `MCP-MAPPING.md`) | Média |
| Auditoria | **Forte** — `events.jsonl`, `audit.jsonl` do MCP local, `Action Receipt` desenhado no `ADR-001` | Ainda não federada entre agentes | Alta, já bem coberta |
| Rollback | Parcial — HITL permite `reject`; sem rollback de estado de memória em si | — | Baixa hoje |
| Federation | **Ausente** — é o gap identificado no `ROADMAP-GOVERNANCE.md`/`ADR-001` | — | Alta a médio prazo, não hoje |
| Sincronização | **Ausente** | — | Idem |
| CRDT | **Ausente** | — | Só relevante se federação avançar |
| MCP | **Implementado** — `retrieve_knowledge` tool, `mcp/plan_runner` server | **Confirmado hoje: `retrieve_knowledge`/`McpKnowledge` nunca são chamados por `engine.py`/`langgraph_engine.py`/`cli.py`** — RAG existe mas está desligado da execução real (S9, já no backlog) | **Crítica** |
| Consentimento | Contrato L4 tem `status: candidate\|active` (gate humano) | Sem implementação | Média |
| Isolamento por utilizador/agente/projeto | `scope.kind: user\|project\|agent\|org` no contrato L4; `client_id` no L1/preferências | Só no papel para L4 | Média-alta |
| Custo | Gemini free tier (RAG), zero custo por desenho | Já esgotou quota hoje | Alta, já crítico |
| Offline/local | `working_memory.py`, `events.jsonl`, `skills/` — tudo local, zero infra | L5 depende de Supabase+Gemini (não é offline) | Média |

## 3. dsh-long-memory (`@wwskills/dsh-long-memory`, v0.2.0)

```
dsh-long-memory
├── capacidades: 8 tools MCP (mem_search, mem_record, ...), tipos fixos
│   (USER/PREFERENCE/PROJECT/FACT/SKILL/EVENT/TASK), scopes
│   (user/project/domain/episodic), supersessão por chave, arquivo/activo,
│   FTS5 + vector opcional + híbrido (`SCORE_PATHS` confirma os 5 modos:
│   exact/generalized/hybrid/fts5-only/vector-only), grafo simples com
│   arestas tipadas (BELONGS_TO/KNOWS/SUPERSEDED_BY) + PageRank real para
│   ranking personalizado -- confirmado no código (`lib/kg.js`)
├── arquitectura: SQLite (better-sqlite3 provável, não confirmado o driver
│   exacto), 4 migrations reais (`0001_initial`, `0002_l7_buffer`,
│   `0003_embedding_cache_key`, `0004_corrections_rules`), módulo L7
│   (`lib/l7.js`) de auto-extracção confirmado como código real, não só
│   promessa
├── interfaces: MCP (é um plugin DSH — Session/Tool/Agent Loop/Prompt
│   Assembly/Credentials seams do Cordis/DSH)
├── dependências: TypeScript, Node, acoplado ao ciclo de vida de plugins
│   do DeepSeek Harness (`cordis.patch.yml` confirma isto)
├── pontos fortes: zero infra obrigatória (SQLite), grafo+FTS+vector já
│   integrados numa coisa só, licença MIT, testes reais no CI
│   (`vitest run` + testes de migração + e2e)
├── limitações: **1 estrela no GitHub, projecto de um autor, muito
│   recente** (push mais recente 2026-09-10) -- não é "produção" no
│   sentido de adopção real, é um projecto individual bem construído
├── riscos: manutenção de um só mantenedor; está acoplado ao DSH, não é
│   standalone
└── integração possível com plan_runner: NÃO DIRECTA. É plugin DSH, não
    biblioteca Python nem servidor MCP standalone chamável por HTTP. A
    única integração real seria **portar o padrão** (schema SQLite +
    FTS5 + grafo de arestas simples + PageRank) para uma implementação
    Python própria -- não "instalar" nada.
```

**Correcção a uma afirmação da "deep":** o documento anterior classificou isto como "Produção (MIT)". Com 1 estrela e um só mantenedor, "produção" não é o termo correcto — é um projecto individual, MIT, bem escrito e testado, mas sem adopção externa verificável.

## 4. Graphiti (`getzep/graphiti`)

```
- Modelo de dados: temporal, `valid_at`/`invalid_at` confirmados na
  documentação oficial ("Facts have validity windows... old facts are
  invalidated — not deleted")
- Entidades/episódios/comunidades: confirmado (Episodes & Provenance,
  Prescribed & Learned Ontology)
- Retrieval: híbrido (semantic + keyword + graph traversal), confirmado
- Persistência: **exige backend de grafo** -- `neo4j>=5.26.0` é
  dependência OBRIGATÓRIA no pyproject.toml, não opcional. Extras
  disponíveis: `falkordb`, `falkordblite` (embutido, sem servidor --
  única via verdadeiramente local), `kuzu` (upstream **não
  mantido**, aviso do próprio Graphiti), `neptune` (AWS)
- LLM: `openai>=1.91.0` também é dependência OBRIGATÓRIA -- por omissão
  assume OpenAI para inferência E embeddings. Extras para
  anthropic/groq/google-genai existem, mas não são o caminho por defeito
- MCP server: confirmado, "1.0" lançado, "hundreds of thousands of
  weekly users" (fonte: blog oficial Zep, não é uma métrica verificável
  independentemente)
- Custo/complexidade operacional: alta por omissão (precisa de Neo4j
  gerido) -- baixa só se se usar `falkordblite`
- Maturidade: real -- ~31k estrelas (confirmado via API, não a fonte
  original), 63 contribuidores
- Licença: NÃO VERIFICADO nesta passagem (não confirmei o ficheiro
  LICENSE directamente)
- Segurança: **CVE-2026-32247** -- injecção de Cypher via `entitytypes`,
  explorável por prompt injection contra o cliente LLM, corrigida em
  0.28.2. Confirmado via OSV.dev, não mencionado pela "deep"
- Integração com knowledge.py: exigiria um novo `KnowledgeBackend` (ou
  um novo backend para L6, não L5 -- Graphiti é grafo, a camada certa
  para ele no desenho já existente é L6, não L5)
```

**Resposta à questão central (A/B/C/D):** com a evidência disponível, Graphiti encaixa como **(C) backend opcional para L6** — não como memória principal (exigiria substituir a persistência actual toda por Neo4j, desproporcional ao problema actual) nem como "só inspiração" (é código real, integrável). É overkill se o problema imediato é "a sessão não sabe o que já foi decidido" — esse problema resolve-se com L4 (ainda por implementar) e disciplina de bootstrap, não com um grafo bi-temporal.

## 5. Cognee (`topoteretes/cognee`)

```
- Arquitectura: pipeline Extract → Cognify → Load, confirmado
- Vector: `lancedb` (embutido, sem servidor) é dependência base
- Grafo: `networkx` (puro Python, em memória) é dependência base;
  `neo4j` é EXTRA opcional, não obrigatório -- oposto do Graphiti
- Licença: Apache-2.0 (confirmado via API), mais permissiva que a
  maioria dos MIT/proprietário vistos hoje
- Estrelas: 30.799 (confirmado via API)
- Local: SIM, por omissão -- LanceDB+NetworkX não precisam de infra
  externa. Isto é uma diferença arquitectural real e favorável face ao
  Graphiti, não um detalhe menor
- Sobreposição com Graphiti: parcial -- ambos fazem grafo+vector, mas
  Cognee é local-first por omissão e Graphiti é servidor-first por
  omissão. Não são a mesma escolha de trade-off
- Sobreposição com dsh-long-memory: baixa -- dsh-long-memory é um
  plugin DSH leve (SQLite), Cognee é uma plataforma de pipeline de
  ingestão mais pesada (ainda que local)
```

**Resposta à pergunta ("substituiria ou duplicaria?"):** substituiria parcialmente o papel de L5 (RAG) SE se quisesse grafo além de vector — mas o L5 actual (Gemini+Supabase) já funciona para busca vectorial pura; a duplicação real só existiria se se adoptasse Cognee E se mantivesse o pipeline actual sem decidir qual dos dois é a fonte de verdade para L5.

## 6. O que fica para a Fase 2

LightRAG, Mem0, Hindsight, e a lista de "outras memórias" (EverMemOS, ENGRAM, A-Mem, Memobase, Memary, Memori, MemOS, LangMem) — nenhum verificado ainda ao nível de código nesta fase.

## 7. Achado que muda a prioridade de tudo

O achado mais importante desta fase não é sobre nenhuma ferramenta externa — é que **o L5 já construído hoje nunca é chamado durante a execução real de um plano** (confirmado: zero ocorrências de `retrieve_knowledge`/`McpKnowledge` em `engine.py`, `langgraph_engine.py`, `cli.py`, `executor.py`). Antes de decidir se se adopta Graphiti para L6, ou se se implementa L4, vale mais fechar o fio que já existe e está desligado — isso é S9, já no `STATUS.md`, e é mais barato e mais imediato do que qualquer adopção nova.
