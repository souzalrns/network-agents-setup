# Skills Claude (cópia de produção)

**Fonte:** `agent-network-mcp/.claude/skills/` (repo público)  
**Destino:** este setup — `network-agents-setup`  
**Produção:** intocada

## Como obter a cópia completa (recomendado)

Na raiz deste repo:

```bash
bash scripts/sync-skills-from-prod.sh
```

Isto faz clone shallow de `agent-network-mcp`, copia as ~30 skills para `skills/claude/` e adiciona cabeçalho de proveniência. **Não altera** o repo de produção.

## Porquê um script

As skills somam ~500KB de markdown. O sync a partir do repo público é a forma fiável de ter o conteúdo **byte-a-byte** no setup para testes reais mais à frente, sem risco na rede operacional.

## Inventário (após sync)

- api-and-interface-design
- browser-testing-with-devtools
- ci-cd-and-automation
- code-review-and-quality
- code-simplification
- context-engineering
- debugging-and-error-recovery
- deprecation-and-migration
- documentation-and-adrs
- doubt-driven-development
- find-skills
- frontend-ui-engineering
- git-workflow-and-versioning
- idea-refine (SKILL + examples + frameworks + criteria + script)
- incremental-implementation
- interview-me
- observability-and-instrumentation
- performance-optimization
- planning-and-task-breakdown
- ponytail
- security-and-hardening
- shipping-and-launch
- source-driven-development
- spec-driven-development
- test-driven-development
- using-agent-skills

## Já no git (parcial)

Alguns ficheiros/stubs podem já existir nesta pasta a partir de commits anteriores; o script **substitui** a pasta `skills/claude` pelo espelho completo da produção.
