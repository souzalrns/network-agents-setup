# PRs da cadeia F1 → F6

NAS = `souzalrns/network-agents-setup`; MCP = `souzalrns/agent-network-mcp`. O merge é sempre do maestro.

| Fase | PR | Estado | O que fez |
|---|---|---|---|
| F0.7b | [NAS #102](https://github.com/souzalrns/network-agents-setup/pull/102) | merged 2026-10-05 | O cliente MCP recusa o pacote `mcp` 2.x com uma mensagem clara |
| F0.7b | [NAS #103](https://github.com/souzalrns/network-agents-setup/pull/103) | merged 2026-10-05 | Cabeçalho opcional de bypass da protecção da Vercel |
| F0.7b | [NAS #104](https://github.com/souzalrns/network-agents-setup/pull/104) | merged 2026-10-05 | Evidência do golden set contra produção (PASSOU) e gate M1 |
| F1 | [NAS #105](https://github.com/souzalrns/network-agents-setup/pull/105) | merged 2026-10-05 | `ingest_document` com o adapter MarkItDown (T6a) |
| F1 | [NAS #106](https://github.com/souzalrns/network-agents-setup/pull/106) | merged 2026-10-05 | Fixture PDF sintética reprodutível + regressão |
| F1 | [NAS #107](https://github.com/souzalrns/network-agents-setup/pull/107) | merged 2026-10-05 | Fixtures DOCX e XLSX + regressão |
| F1 | [NAS #108](https://github.com/souzalrns/network-agents-setup/pull/108) | merged 2026-10-05 | Conversão num processo filho com timeout e limite de memória |
| F1 | [NAS #109](https://github.com/souzalrns/network-agents-setup/pull/109) | merged 2026-10-05 | Documentos convertidos entram no T6 com proveniência |
| F1 | [NAS #110](https://github.com/souzalrns/network-agents-setup/pull/110) | merged 2026-10-05 | Fecho do F1: benchmark S5, P-21 a P-23 |
| F2 | [NAS #111](https://github.com/souzalrns/network-agents-setup/pull/111) | merged 2026-10-05 | `fetch` com allowlist, robots, SSRF e proveniência |
| F3 | [NAS #112](https://github.com/souzalrns/network-agents-setup/pull/112) | merged 2026-10-05 | ADR da proveniência no retrieve (P-26) |
| F3a | [NAS #113](https://github.com/souzalrns/network-agents-setup/pull/113) | merged 2026-10-06 | Migração aditiva, `match_knowledge_v2`, writer com proveniência |
| F3a | [MCP #19](https://github.com/souzalrns/agent-network-mcp/pull/19) | merged 2026-10-05 | `retrieve_knowledge` na v2 atrás da flag `KNOWLEDGE_RPC_V2` |
| F4 | [NAS #114](https://github.com/souzalrns/network-agents-setup/pull/114) | merged 2026-10-06 | Mapa de capabilities de marketing com maturidade medida |
| F5 | [NAS #115](https://github.com/souzalrns/network-agents-setup/pull/115) | merged 2026-10-06 | Runbook e recolhedor de evidência do run real |
| F5 | [NAS #116](https://github.com/souzalrns/network-agents-setup/pull/116) | merged 2026-10-06 | Run real PASSOU; F5 e F4 fechados |
| F3a | [NAS #117](https://github.com/souzalrns/network-agents-setup/pull/117) | merged 2026-10-06 | F3a fechado com a prova da v2 em produção |
| Segurança | [NAS #118](https://github.com/souzalrns/network-agents-setup/pull/118) | merged 2026-10-06 | 2 alertas do Dependabot (`proxy-addr` 2.0.8, `source-map-js` 1.2.2) |
| F3c | [NAS #119](https://github.com/souzalrns/network-agents-setup/pull/119) | **aberto** (CI verde) | Todo o `.md` de `docs/knowledge/` no MANIFEST ou no `EXCLUDED`, com teste |
| F3b | [NAS #120](https://github.com/souzalrns/network-agents-setup/pull/120) | **aberto** | Classes de validade no ingest (P-27 a P-29) |
| F6 | PR do branch `docs/f6-hardening-portfolio` | **aberto** | Este pacote, hardening e resumo de portfolio |

**Antes da cadeia, já com merge, que a sustentam:** MCP #15 (o `ingestDocument` só apaga linhas do MCP), MCP #16 (CHECK do `token_usage`), MCP #17 (`next` com a correcção crítica), MCP #18 (higiene e actions pinadas).
