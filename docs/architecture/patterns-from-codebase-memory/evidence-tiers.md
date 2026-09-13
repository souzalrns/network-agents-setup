# Evidence tiers (Scout / Verify / Auditor)

**Fonte:** `~/.claude/skills/codebase-memory/SKILL.md` + `github/awesome-copilot` skill `codebase-memory-mcp` [citation:8].

Este e o padrao mais valioso para nos: um modelo explicito de *confianca* na resposta, em funcao do tipo de claim. Aplica-se ao codebase-memory-mcp, mas o conceito e portavel para qualquer ferramenta de analise.

---

## Os 3 tiers

### Scout (Tier 1)
**Quando:** descoberta rapida, orientacao positiva.
**O que permite:** lookups positivos rapidos, com poucas graph calls.
**O que PROIBE:** claims de ausencia, exaustividade, dead-code, ou impacto completo. Resultados sao provisorios.

### Verify (Tier 2 — default)
**Quando:** trabalho task-directed normal.
**O que exige:**
- Verificar freshness quando material
- Snippets exactos do source para claims materiais
- Traces nas direccoes relevantes
- Path coverage
- Todas as paginas de resultados necessarias para o claim

### Auditor (Tier 3)
**Quando:** claims negativas, exaustivas, security, dead-code, architecture-boundary, impacto completo.
**O que exige:**
- Index generation actual
- Bounded scope explicito
- Result streams completos
- `check_index_coverage` com todos os paths
- Source checks para gaps reportados

---

## Regra transversal

**Depois de conhecer os candidate paths, chamar `check_index_coverage` UMA VEZ com todos os evidence paths.** Para claims negativas ou exaustivas, incluir tambem os scopes relevantes.

**Um resultado limpo significa "sem gap registado", NAO prova de completude.** Para coverage partial/skipped/excluded/stale/pending/unknown, ler ou grep os ranges reportados antes de confiar no grafo.

---

## Aplicacao ao nosso setup

**Onde isto interessa:**
- Sessoes de navegacao de codigo (humano ou agente) — escolher o tier antes de agir.
- Documentacao de padroes — declarar que tier foi usado para cada claim.
- Futuras tools do `plan_runner` — o conceito de "evidence tier" podia informar o HITL: um step que so produz Scout evidence nao devia fechar um plano sem revisao humana.

**Limitacao:** o codebase-memory-mcp tem auto-index, o que significa que a freshness do grafo pode ser menor que a do working tree. Para Verify/Auditor, verificar `index_status` primeiro.

---

## Gotchas especificos de confianca

1. **"Sem resultado" nao e "nao existe".** So e conclusivo em Auditor com `check_index_coverage` limpo e bounded scope.
2. **`trace_path(direction="outbound")` perde callers cross-service.** Para impacto real, `direction="both"`.
3. **Dead code por `max_degree=0` e heuristico.** Excluir entry points, mas validar com source antes de apagar.
4. **Freshness:** o grafo pode estar stale se o working tree mudou. `index_status` antes de claims materiais.

---

Refs: `README.md`, `tools-catalog.md`, `~/.claude/skills/codebase-memory/SKILL.md`.