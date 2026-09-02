# Importado de produção (`agent-network-mcp`)

**Data da cópia:** 2026-09-02  
**Fonte:** `souzalrns/agent-network-mcp` @ `main`  
**Destino:** `network-agents-setup` (setup / portfolio / laboratório)

## Regras

- Esta pasta e `skills/claude/` são **cópia de trabalho**. Editar aqui à vontade.
- **Não** alterar `agent-network-mcp` por causa destas edições.
- Não contém secrets, bridge VM, dashboard auth nem plugins de negócio.

## Lote 1 — knowledge (`docs/knowledge/imported-from-production/`)

| Ficheiro | Origem produção |
|----------|-----------------|
| `marketing-base.md` | `ingestion/marketing-base.md` |
| `produto-tech-a11y-seo.md` | `ingestion/produto-tech-transversal-a11y-seo.md` |
| `comunicacoes-atendimento-base.md` | `ingestion/comunicacoes-atendimento-base.md` |
| `guia-tdd-testes.md` | `ingestion/guia-tdd-testes.md` |
| `revisor-codigo-security-database.md` | `ingestion/revisor-codigo-security-database.md` |
| `radar-ferramentas-opensource.md` | `ingestion/radar-ferramentas-opensource.md` |
| `MANIFEST.md` | `ingestion/MANIFEST.md` |
| `PADROES_ERROS_IA.md` | raiz produção |
| `ADDENDUM_PADROES_ORQUESTRADORES.md` | `docs/` produção |

## Lote 2 — skills Claude

Espelho de `.claude/skills/` → `skills/claude/`.

```bash
bash scripts/sync-skills-from-prod.sh
```

Repo de produção é **público**; o script só faz clone de leitura + cópia local. Depois podes fazer commit no setup quando quiseres versionar o espelho completo.

## Próximo

1. Correr o sync e commit das skills no setup.
2. Fundir `marketing-base` nos packs finos se ainda não estiver.
3. Piloto de teste real (mais à frente).

*Produção permanece operacional e intocada.*
