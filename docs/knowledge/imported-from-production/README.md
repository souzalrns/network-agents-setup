# Importado de produção (`agent-network-mcp`)

**Data da cópia:** 2026-09-02  
**Fonte:** `souzalrns/agent-network-mcp` @ `main` (commit de referência no momento da cópia)  
**Destino:** `network-agents-setup` (setup / portfolio / laboratório)

## Regras

- Esta pasta é **cópia de trabalho**. Editar aqui à vontade.
- **Não** alterar `agent-network-mcp` por causa destas edições.
- Não contém secrets, bridge VM, dashboard auth nem plugins de negócio (`viannalegal`, `mesaflow`, etc.).
- Origem: ficheiros `ingestion/*`, `PADROES_ERROS_IA.md`, `docs/ADDENDUM_PADROES_ORQUESTRADORES.md`.

## Inventário

| Ficheiro | Origem produção | Uso no setup |
|----------|-----------------|--------------|
| `marketing-base.md` | `ingestion/marketing-base.md` | Pool marketing / copy / campanhas |
| `produto-tech-a11y-seo.md` | `ingestion/produto-tech-transversal-a11y-seo.md` | SEO + a11y + Item 13 |
| `comunicacoes-atendimento-base.md` | `ingestion/comunicacoes-atendimento-base.md` | Atendimento / triagem |
| `guia-tdd-testes.md` | `ingestion/guia-tdd-testes.md` | TDD / PR tests / E2E |
| `revisor-codigo-security-database.md` | `ingestion/revisor-codigo-security-database.md` | Security + DB review |
| `radar-ferramentas-opensource.md` | `ingestion/radar-ferramentas-opensource.md` | Fork / sanitize / package open-source |
| `MANIFEST.md` | `ingestion/MANIFEST.md` | Modelo de manifesto de ingestão |
| `PADROES_ERROS_IA.md` | raiz produção | Checklist de revisão de outputs de IA |
| `ADDENDUM_PADROES_ORQUESTRADORES.md` | `docs/` produção | Padrões multi-agente (sem código de terceiros) |

## Próximo (opcional)

1. Fundir trechos de `marketing-base` nos packs finos (`copywriter`, `content-strategist`, etc.).
2. Copiar `.claude/skills/*` da produção para `skills/` neste repo (lote seguinte).
3. Extrair só blocos `marketing` / `design` / `produto-tech-transversal` de `lib/agents.js` (sanitizado).

*Produção permanece operacional e intocada.*
