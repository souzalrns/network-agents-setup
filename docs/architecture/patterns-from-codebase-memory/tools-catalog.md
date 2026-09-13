# Tools catalog — codebase-memory-mcp

**Fonte:** `DeusData/codebase-memory-mcp` (MIT) — 15 MCP tools, JSON-RPC 2.0, stdio transport.

As 15 tools expostas pelo servidor. Agrupadas por funcao para facilitar consulta.

---

## Gestao de indice

### `index_repository`
**Purpose:** indexar (ou re-indexar) um repositorio no knowledge graph.
**Params:** `repo_path` (absolute path).
**Quando usar:** primeira vez num repo, ou apos mudancas grandes. Auto-index existe mas pode ser desligado.

### `index_status`
**Purpose:** ver estado do indice (fresh/stale, node/edge counts, generation).
**Quando usar:** antes de confiar em resultados — especialmente para claims de "dead code" ou "impacto completo".

### `list_projects`
**Purpose:** listar todos os projetos indexados.
**Quando usar:** inicio de sessao, ou quando nao sabes o nome exacto do projeto.

### `delete_project`
**Purpose:** remover um projeto do indice.
**Quando usar:** cleanup de repos que ja nao usas.

---

## Discovery

### `search_graph`
**Purpose:** procurar nodes no grafo por label + name pattern (regex).
**Params principais:** `label`, `name_pattern`, `max_degree`, `min_degree`, `relationship`, `direction`.
**Exemplos:**
- `search_graph(label="Function", name_pattern=".*Handler.*")`
- `search_graph(max_degree=0, exclude_entry_points=true)` — dead code
- `search_graph(min_degree=10, relationship="CALLS", direction="outbound")` — high fan-out

**Gotcha:** default 50 results/page; verificar `has_more`, usar `offset`.

### `search_code`
**Purpose:** text search (como grep, mas dentro do grafo).
**Quando usar:** quando precisas de conteudo literal, nao estrutura.

---

## Tracing / Impacto

### `trace_path`
**Purpose:** seguir call chains (inbound, outbound, ou both).
**Params principais:** `function_name`, `direction`, `depth`, `risk_labels`.
**Gotcha:** precisa de nomes exactos. Usar `search_graph(name_pattern=".*Partial.*")` primeiro.

### `detect_changes`
**Purpose:** mapear `git diff` para simbolos afectados.
**Quando usar:** antes de commit, para ver impacto real das mudancas.

---

## Analise estrutural

### `query_graph`
**Purpose:** Cypher queries directas sobre o grafo.
**Exemplo:**
```
MATCH (a)-[r:HTTP_CALLS]->(b) RETURN a.name, b.name, r.url_path LIMIT 20
```
**Gotcha:** ceiling de 100k rows — adicionar `LIMIT`.

### `get_graph_schema`
**Purpose:** node/edge types + propriedades disponiveis.
**Quando usar:** antes de escrever Cypher custom.

### `get_code_snippet`
**Purpose:** ler source de um simbolo por `qualified_name`.
**Quando usar:** depois de `search_graph` encontrar o simbolo.

### `get_architecture`
**Purpose:** overview da codebase (layers, entry points, modulos centrais).
**Quando usar:** onboarding num repo desconhecido.

### `check_index_coverage`
**Purpose:** verificar se o indice cobriu todos os paths relevantes.
**Quando usar:** obrigatorio para claims negativas ou exaustivas (ver `evidence-tiers.md`).

---

## Meta / ADR

### `manage_adr`
**Purpose:** gerir Architecture Decision Records dentro do MCP server.
**Quando usar:** documentar decisoes enquanto navegas o codigo.

### `ingest_traces`
**Purpose:** ingerir runtime traces para validar edges `HTTP_CALLS`.
**Quando usar:** quando queres confirmar que uma rota HTTP e realmente chamada em runtime.

---

## Resumo por caso de uso

| Pergunta | Tool |
|----------|------|
| Quem chama X? | `trace_path(direction="inbound")` |
| O que X chama? | `trace_path(direction="outbound")` |
| Call context completo | `trace_path(direction="both")` |
| Encontrar por nome | `search_graph(name_pattern="...")` |
| Dead code | `search_graph(max_degree=0, exclude_entry_points=true)` |
| Cross-service edges | `query_graph` com Cypher |
| Impacto de mudancas | `detect_changes()` |
| Trace com risk labels | `trace_path(risk_labels=true)` |

---

Refs: `README.md`, `evidence-tiers.md`, `~/.claude/skills/codebase-memory/SKILL.md`.