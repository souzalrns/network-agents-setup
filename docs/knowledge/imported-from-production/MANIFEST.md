<!-- COPIA de agent-network-mcp/ingestion/MANIFEST.md — 2026-09-02 — modelo de ingestão; não aponta ao Supabase de produção -->
# Manifesto de ingestão (modelo)

Cada linha = mapeamento ficheiro → agente destino → source.
No **setup**, usar isto como template para T6 / RAG local — **não** chamar `ingest_knowledge` da rede de produção a partir daqui.

| Arquivo | agent (destino) | source (nome curto) |
|---|---|---|
| `revisor-codigo-security-database.md` | `revisor-codigo` | ECC security-reviewer + database-reviewer |
| `arquitetura-agentes-planejamento-rede-docs.md` | `arquitetura-agentes` | ECC planner+architect (se copiado) |
| `guia-tdd-testes.md` | `guia-tdd` | ECC tdd-guide+pr-test-analyzer+e2e-runner |
| `radar-ferramentas-opensource.md` | `radar-ferramentas` | ECC opensource-forker+packager+sanitizer |
| `marketing-base.md` | `marketing` | ECC marketing-agent |
| `comunicacoes-atendimento-base.md` | `comunicacoes-atendimento` | ECC chief-of-staff |
| `produto-tech-a11y-seo.md` | `produto-tech-transversal` | ECC a11y-architect+seo-specialist |

Critério de pool horizontal: *"isto ainda seria útil se amanhã surgisse um 11º negócio totalmente diferente?"*
