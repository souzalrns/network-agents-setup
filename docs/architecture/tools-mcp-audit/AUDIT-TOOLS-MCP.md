# AUDIT-TOOLS-MCP.md — Auditoria técnica profunda: Tool Use / Ecossistema MCP

**Estado deste documento:** reescrita completa, padrão ouro (mesmo rigor das auditorias de Governança/Memória/Agentes/Ingestão). A versão anterior citava só o achado já conhecido (`ToolExecutor.ts` sem autorização) e resumia pesquisa feita noutra fase. Esta versão lê **todos** os ficheiros de `packages/mcp/src/` linha a linha (não só os dois já citados) e cruza os achados com CVEs reais de servidores MCP publicados em 2025-2026 — não com opinião genérica de "isto parece inseguro".

## 0. Estado interno completo, verificado por leitura de todos os ficheiros de `packages/mcp/src/`

| Ficheiro | Linhas | O que faz | Achado |
|---|---|---|---|
| `tools/ToolRegistry.ts` | 44 | `Map<string, MCPTool>` em memória | Sem persistência, versão, ou proveniência (já conhecido) |
| `tools/ToolExecutor.ts` | 25 | Valida só presença de campos obrigatórios, executa directo | Zero verificação de capacidade/scope (já conhecido, `GOV-FASE1.md`) |
| `server/MCPServer.ts` | 47 | Handler HTTP `executeTool`/`getTools` | Zero autenticação (já conhecido) |
| `client/MCPClient.ts` | 53 | Cliente HTTP simples | **Novo, confirmado agora:** nunca envia nenhum header de autenticação — simétrico à ausência do lado servidor |
| `tools/built-in/database.ts` | 56 | Tool `query_database` | **NOVO E CRÍTICO:** `pool.query(query, params)` executa **qualquer string SQL** recebida do agente, sem allowlist, sem modo read-only, sem restrição de tabela |
| `tools/built-in/web.ts` | 63 | Tools `http_request`, `scrape_webpage` | **NOVO E CRÍTICO:** `fetch(url, ...)` sobre URL vinda do agente, **zero protecção SSRF**; `scrape_webpage` interpola `selector` (também do agente) numa `RegExp` construída em runtime |
| `tools/built-in/filesystem.ts` | 86 | Tools `read_file`/`write_file`/`list_directory` | **NOVO:** guarda de path traversal com bug de bypass clássico — `resolved.startsWith(basePath)` sem separador |
| `tools/legal/{brazilian,portuguese}-law.ts`, `db.ts` | 284 | Conteúdo jurídico curado + Prisma client | Sem achados de segurança relevantes nesta passagem |

**Contraste que fecha o argumento, confirmado por leitura directa de ambos os lados:** `mcp/plan_runner/mcp_plan_runner/policy.py:sanitize_repo_path()` (Python) já implementa a correção certa — `cand.relative_to(root)` (usa `pathlib`, rejeita corretamente qualquer path fora da raiz, incluindo o caso "directório irmão com prefixo igual") — exatamente o bug que `filesystem.ts` (TypeScript) tem. **A correção já existe neste repo, só não foi replicada para o outro lado.** E `tools_impl.py` (Python) aplica `authorize()`+`rate_limit()`+`sanitize_repo_path()`+`audit()` de forma consistente em **todas** as 4 tools (`list_templates`, `get_status`, `run_plan`, `resume_plan`), confirmado por leitura completa do ficheiro — não é uma alegação de resumo, é o padrão real em código.

## 1. `query_database` — SQL arbitrário sem restrição

**Isto não é uma preocupação teórica — é a categoria de falha mais documentada em servidores MCP de base de dados em 2025-2026:**

- **CVE-2025-66336 (Apache Doris MCP Server, CVSS 8.1)** — nome de base de dados controlado pelo utilizador interpolado directamente numa query SQL, executada sem passar o contexto de autorização do chamador. O investigador (Tomer Peled) encontrou a mesma classe de falha em **três** servidores MCP de base de dados populares.
- **O próprio servidor de referência oficial da Anthropic** (`@modelcontextprotocol/server-postgres`) tentava impor read-only envolvendo a query em `BEGIN TRANSACTION READ ONLY; <query>; ROLLBACK;` — bypass documentado pela Datadog Security Labs: o cliente `pg` aceita múltiplos statements separados por `;`, logo um atacante submetia `COMMIT; DROP SCHEMA public CASCADE;` — o `COMMIT` terminava a transação read-only prematuramente. **Este servidor de referência foi descontinuado e arquivado em julho de 2025 precisamente por esta falha.**
- Catalogado formalmente no **OWASP MCP Top 10** como **MCP05 — Command Injection & Execution**.

**Conclusão directa: `query_database` deste repo não tem sequer a tentativa (falhada) de read-only que o servidor oficial da Anthropic tinha — está estritamente pior que um caso já reconhecido como motivo de descontinuação oficial.**

**Correção mínima, em camadas (nenhuma sozinha basta — a lição do incidente Anthropic é que confiar só na aplicação falha):**
1. **Utilizador de Postgres com `GRANT SELECT` apenas** (sem INSERT/UPDATE/DELETE/DDL) — a defesa primária real, ao nível do motor, não da aplicação.
2. Allowlist sintáctica (só `SELECT`/`WITH`, rejeitar `;` adicional, rejeitar keywords de escrita) como rede de segurança adicional.
3. `SET statement_timeout` + `client.release(true)` (descartar a ligação, não reutilizar do pool) após cada query.

**Classificação: BUILD (correção obrigatória, prioridade 1 — a mais urgente das três desta auditoria).**

## 2. `http_request`/`scrape_webpage` — SSRF sem mitigação + parsing frágil

**Também não é hipotético.** Múltiplos CVEs reais e independentes em 2025-2026, todos com o mesmo padrão de raiz — uma guarda de SSRF escrita à mão, com um buraco:

| CVE/GHSA | Falha exacta |
|---|---|
| CVE-2025-65513 (`fetch-mcp`, CVSS 6.3) | Validação insuficiente permite contornar bloqueio de IP privado |
| CVE-2026-80347 (`mcp-fetch`) | Guarda `isSafeUrl` falha para IPv6 **entre colchetes** — `net.isIP` devolve 0, salta o bloqueio |
| CVE-2026-49857 (`auth-fetch-mcp`, CVSS 7.4) | Falha a detetar loopback IPv4-mapeado-em-IPv6 (`::ffff:127.0.0.1`) — o parser URL normaliza antes da checagem |
| GHSA-vv7q-7jx5-f767 (FastMCP `OpenAPIProvider`) | SSRF + path traversal combinados: parâmetro de path sem URL-encoding, `urljoin()` interpreta `../` |

**O padrão que se repete em todos: verificações manuais de IP privado têm sempre um buraco subtil — reforça que a correção certa não é escrever a guarda à mão, é usar uma biblioteca mantida** (`ssrf-req-filter`/`request-filtering-agent`) que valida o **IP de ligação real, pós-resolução DNS**, ao nível do `http.Agent` — não a string do hostname antes de resolver.

Para `scrape_webpage`: interpolar `selector` (vindo do agente) numa `RegExp` construída em runtime é uma instância de **CWE-1333 (Regex DoS)** — não encontrei um CVE nomeado exatamente nesta forma em MCP (**NOT VERIFIED** como incidente documentado), mas a correção (trocar regex por parser DOM real, `cheerio`, `selector` passado como argumento de query CSS nunca interpolado em padrão) é de baixo risco e alto retorno.

> **RESOLVIDO em 2026-09-19 (apenas a parte de `scrape_webpage`/regex — o SSRF de `http_request` continua pendente, ver A4/A5) — `web.ts` passa a usar `cheerio.load(html)` + `$(selector).text()`/`$('title').text()`, `selector` nunca mais interpolado em `RegExp`. Testado com selector contendo meta-caracteres de regex (`"(a|a)*"`, tratado como query CSS, não quebra) e selector válido (`"p"`, extrai conteúdo real). Suite completa: 94/94 testes que correm passam, 0 regressões. Ver `EXECUTION-PROMPTS.md` A6.**

**Classificação: BUILD (prioridade 2 — potencialmente tão grave quanto o SQL num ambiente cloud, onde SSRF pode expor endpoints de metadata/credenciais IAM, mas tipicamente exige um passo adicional de exploração).**

**Regra adicional confirmada pela pesquisa:** nunca seguir redirects HTTP automaticamente numa tool de fetch exposta a agente — um alvo aprovado pode responder `302` para um alvo interno, contornando qualquer validação feita só sobre a URL original.

## 3. `filesystem.ts` — path traversal (CWE-22 clássico)

Já descrito na secção 0. Confirmado como **o exemplo canónico** usado em guias de correção OWASP/Snyk — `resolved.startsWith(basePath)` sem separador deixa passar qualquer directório irmão que partilhe o prefixo de string. A advisory GHSA-vv7q-7jx5-f767 do FastMCP (já citada) combina exatamente este erro conceptual com SSRF no mesmo ponto de código, confirmando que não é um erro isolado deste repo — é um padrão recorrente no ecossistema MCP.

**Correção padrão e comprovada** (`path.relative`, já implementada correctamente no lado Python deste mesmo repo via `pathlib`):

```ts
export function resolveSafePath(basePath: string, filePath: string): string {
  const base = path.resolve(basePath);
  const resolved = path.resolve(base, filePath);
  const rel = path.relative(base, resolved);
  if (rel === '..' || rel.startsWith('..' + path.sep) || path.isAbsolute(rel)) {
    throw new Error(`Path traversal blocked: "${filePath}" resolves outside "${base}"`);
  }
  return resolved;
}
```

Ressalva não verificada: se o servidor permitir criação de symlinks dentro de `basePath`, a comparação de string (mesmo corrigida) não protege — precisaria de `fs.realpath()` adicional. **NOT VERIFIED se este repo permite isso.**

**Classificação: BUILD (prioridade 3 — genuinamente sério, mas correção trivial e sem risco de regressão).**

> **RESOLVIDO em 2026-09-19 (item A3 de `EXECUTION-PROMPTS.md`):** guarda substituída por `path.relative` nas 3 tools de `packages/mcp/src/tools/built-in/filesystem.ts`, exactamente como acima. Teste novo (`tests/unit/filesystem.test.ts`) escrito ANTES da correção — confirmado que falhava (provando o bypass real do directório irmão) — e confirmado a passar depois. Suite completa: 91 testes, 0 falhas. Ressalva de symlinks acima **continua NOT VERIFIED**, não foi tratada por este item.

## 4. Autorização/autenticação (achado já conhecido, reconfirmado)

`ToolExecutor.ts` sem verificação de capacidade/scope; `MCPServer.ts` sem autenticação HTTP; `MCPClient.ts` nunca envia auth. Correção já detalhada: portar o pipeline `sanitize → auth → rate limit → scope check → execute → audit` já testado em `mcp/plan_runner/mcp_plan_runner/policy.py` (Python) — confirmado por leitura completa de `tools_impl.py` nesta auditoria, não é resumo de segunda mão.

**Confirmado por pesquisa externa (não repetida em detalhe aqui, ver histórico desta sessão):** nem FastMCP nem `mcp-agent` (a implementação mais citada dos padrões "Building Effective Agents" da Anthropic) resolvem isto por nós — `Agent.call_tool()` do `mcp-agent` também não verifica scope antes de invocar.

## 5. Prioridade de correção consolidada

1. **`query_database`** — impacto: controlo total da base de dados subjacente; precedente directo (servidor oficial da Anthropic descontinuado por isto).
2. **`http_request` SSRF** — impacto potencialmente igual ou maior em cloud (exfiltração de credenciais IAM via metadata endpoint), levemente atrás por exigir um passo adicional de exploração.
3. **Autorização em `ToolExecutor`/`MCPServer`** — sem isto, mesmo corrigindo 1-2-3, qualquer chamador não autenticado continua a poder invocar as tools corrigidas.
4. **Path traversal em `filesystem.ts`** — sério, mas correção trivial e já escrita (no lado Python).

## 6. Classificação consolidada

| Item | Classificação |
|---|---|
| `query_database` — role read-only + allowlist + timeout | **BUILD**, prioridade 1 |
| `http_request` — `ssrf-req-filter`/`request-filtering-agent`, sem seguir redirects automaticamente | **BUILD**, prioridade 2 |
| `scrape_webpage` — trocar regex por `cheerio` | **BUILD**, baixo risco/alto retorno |
| `filesystem.ts` — `path.relative`, replicar o padrão já correcto do Python | **BUILD**, prioridade 3 |
| `ToolExecutor.ts`/`MCPServer.ts` — pipeline de autorização | **BUILD**, prioridade 3 (já registado) |
| FastMCP/mcp-agent como solução externa para qualquer um destes 5 pontos | **REJECT** — nenhum resolve por nós, confirmado por pesquisa e por eles próprios já terem tido a mesma classe de CVE |

## 7. O que NÃO fazer

- Não corrigir `query_database` só com allowlist regex sem também restringir a permissão do utilizador de BD ao nível do Postgres — o incidente da Anthropic prova que a camada aplicacional sozinha falha.
- Não escrever a guarda de SSRF à mão verificando hostname contra uma lista de ranges privados em string — os 3 CVEs citados são exactamente isto, cada um com um buraco diferente.
- Não seguir redirects HTTP automaticamente numa tool de fetch exposta a agente.
- Não interpolar input do agente num padrão de `RegExp` construído em runtime para parsing de HTML.
- Não assumir que corrigir a comparação de string do path resolve tudo se o servidor permitir symlinks dentro da base (não verificado se se aplica aqui).
- Não esperar que adoptar FastMCP ou mcp-agent resolva algum destes 5 pontos — nenhum dos dois tem estas defesas por omissão, e pelo menos um (FastMCP) já teve a mesma classe exacta de CVE (SSRF+path traversal combinados).

## Referências primárias

- [CVE-2025-66336 — Apache Doris MCP Server SQL Injection](https://hol.org/guard/security/cves/CVE-2025-66336-apache-doris-mcp-server-sql-injection-leading-the)
- [MCP vulnerability case study: SQL injection in the Postgres MCP server — Datadog Security Labs](https://securitylabs.datadoghq.com/articles/mcp-vulnerability-case-study-SQL-injection-in-the-postgresql-mcp-server/)
- [modelcontextprotocol/servers-archived — postgres](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/postgres)
- [CVE-2025-65513 — fetch-mcp SSRF](https://github.com/advisories/GHSA-8fxj-2g9q-8fjw)
- [CVE-2026-80347 — mcp-fetch SSRF](https://www.sentinelone.com/vulnerability-database/cve-2026-80347/)
- [CVE-2026-49857 — auth-fetch-mcp SSRF](https://www.strix.ai/cve/CVE-2026-49857)
- [GHSA-vv7q-7jx5-f767 — FastMCP OpenAPIProvider SSRF + path traversal](https://github.com/PrefectHQ/fastmcp/security/advisories/GHSA-vv7q-7jx5-f767)
- [OWASP MCP Top 10](https://owasp.org/www-project-mcp-top-10/) · [The Vulnerable MCP Project](https://vulnerablemcp.info/)
- [ssrf-req-filter](https://www.npmjs.com/package/ssrf-req-filter) · [request-filtering-agent](https://github.com/azu/request-filtering-agent)
- [OWASP — SSRF Prevention in Node.js](https://owasp.org/www-community/pages/controls/SSRF_Prevention_in_Nodejs)
- Ficheiros deste repo lidos na íntegra: `packages/mcp/src/tools/{ToolRegistry,ToolExecutor}.ts`, `packages/mcp/src/server/MCPServer.ts`, `packages/mcp/src/client/MCPClient.ts`, `packages/mcp/src/tools/built-in/{database,web,filesystem}.ts`, `packages/mcp/src/tools/legal/db.ts`, `mcp/plan_runner/mcp_plan_runner/tools_impl.py`, `mcp/plan_runner/mcp_plan_runner/policy.py` (função `sanitize_repo_path`)
