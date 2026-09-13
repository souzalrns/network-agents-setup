# Patterns from codebase-memory-mcp

**Fonte:** DeusData/codebase-memory-mcp (MIT) — high-performance code intelligence MCP server. Indexa codebases num knowledge graph persistente, expoe 15 MCP tools, single static binary.

**Nota importante:** isto NAO e codigo deste repo. E uma ferramenta externa que corre localmente (`~/.cache/codebase-memory-mcp/`, binario em `%LOCALAPPDATA%\Programs\codebase-memory-mcp\`). O que roubamos sao *padroes*, nao a ferramenta.

**Diferenca para `patterns-from-mcp/`:** aquele documenta o NOSSO MCP server governado (`mcp/plan_runner/`). Este documenta uma ferramenta externa que usamos para navegar o codigo. Ver tambem `patterns-from-mcp/README.md`.

---

## O que e

- **Knowledge graph:** nao e "grep rapido" nem RAG. Extrai *factos* de codigo (funcoes, classes, call chains, HTTP routes) e guarda num SQLite persistente.
- **158 linguagens** via tree-sitter vendored + Hybrid LSP pass (type-aware, refinado).
- **15 MCP tools:** `index_repository`, `index_status`, `list_projects`, `delete_project`, `search_graph`, `search_code`, `trace_path`, `detect_changes`, `query_graph`, `get_graph_schema`, `get_code_snippet`, `get_architecture`, `check_index_coverage`, `manage_adr`, `ingest_traces`.
- **Cypher query support** via `query_graph` (MATCH, RETURN, LIMIT).
- **UI grafica** em `localhost:9749` (3D graph view).

**Porque interessa:** 5 queries estruturais consomem ~3,400 tokens via graph vs ~412,000 tokens via file-by-file exploration — ~99% reducao [citation:1][citation:3].

---

## O que implementamos / adoptamos neste repo

**Estado actual:** ferramenta externa instalada localmente, indexa este repo (`C-Users-souza-Downloads-network-agents-setup.db`, 5306 nodes, 9006 edges).

**Adoptado:**
- Navegacao estrutural durante sessoes de desenvolvimento (substitui grep em exploracao de codigo).
- Cypher queries para analise de dependencias e impacto.
- Evidence tiers (Scout/Verify/Auditor) como modelo de confianca aplicavel ao nosso setup (ver `evidence-tiers.md`).

**NAO adoptado:**
- Substituir `mcp/plan_runner/` por este MCP. Sao coisas diferentes: um governa execucao de planos, o outro navega codigo.
- Auto-index sem revisao. O grafo pode ficar stale — ver gotchas abaixo.

---

## Ficheiros deste pacote

| Ficheiro | Conteudo |
|----------|----------|
| `README.md` | Este indice: fonte, o que e, o que adoptamos |
| `tools-catalog.md` | As 15 tools: purpose, params principais, quando usar |
| `evidence-tiers.md` | Scout / Verify / Auditor — modelo de confianca |

---

## Gotchas (do SKILL.md oficial)

1. `search_graph(relationship="HTTP_CALLS")` filtra nodes por degree — usar `query_graph` com Cypher para ver edges reais.
2. `query_graph` tem ceiling de 100k rows — adicionar `LIMIT`.
3. `trace_path` precisa de nomes exactos — usar `search_graph(name_pattern=...)` primeiro.
4. `direction="outbound"` perde callers cross-service — usar `direction="both"`.
5. `search_graph` default 50/page — verificar `has_more` e usar `offset`.

---

## Referencias

- Repo: `github.com/DeusData/codebase-memory-mcp` [citation:4]
- Doc: `model-context-protocol.com/servers/codebase-memory-mcp` [citation:7]
- SKILL.md local: `~/.claude/skills/codebase-memory/SKILL.md`