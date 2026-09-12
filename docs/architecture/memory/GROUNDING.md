# Grounding — anti-alucinação (lab + produção)

**Origem:** diagnóstico 2026-09-12 em `agent-network-mcp` (ingestão grava, agente não lê a fonte certa + completa de memória).

**Âmbito neste repo:** regras para **todos** os agents/skills do setup. Runtime de produção aplica o mesmo espírito em `lib/agentRuntime.js`.

---

## Regra de produto (obrigatória)

> Se o contexto recuperado (L4/L5, banco operacional, artefactos do plan) **não contiver** o dado pedido, o agente diz que **não tem** — **nunca** completa de memória de treino nem inventa valores plausíveis.

Aplicar a: licenças, versões, status, números, datas, papéis de arquitectura, claims de mercado.

---

## Regras de evidência (colar no system / agent)

1. Factos concretos só a partir do **contexto injectado** nesta execução (L1 inputs, L4 recall, L5 retrieve, L2 artefactos, bancos operacionais).
2. Se o contexto não tiver o dado → **admitir a falta** explicitamente.
3. Quando usares um facto, **citar a fonte** (`[Fonte: …]`, `source`, tabela, artefacto).
4. Diferenciar sempre:
   - **(a)** está no contexto
   - **(b)** não está no contexto
   - **(c)** hipótese (marcada como hipótese)

Ficheiro canónico para agents: `agents/_shared/grounding.directive.md`.

---

## Duas fontes de verdade (não confundir)

| Tipo de facto | Onde vive | O que **não** faz |
|---------------|-----------|-------------------|
| Status operacional / avaliação de ferramenta | Banco operacional (ex. `tool_evaluations` em produção) | Ingerir só em RAG **não** actualiza este banco |
| Docs, skills, normas, texto longo | **L5** `knowledge_chunks` / corpus | Não é fonte de status “integrado/rejeitado” |
| Preferências estáveis | **L4** semantic | Não indexar PDFs inteiros aqui |
| Como fazer | **L3** skills | Não guardar PII |

**Ingerir ≠ o agente ler a tabela certa.** Pipeline de ingest e pipeline de retrieve devem apontar para a mesma classe de verdade que o prompt declara.

---

## L5 retrieval (padrão a adoptar)

Ver [rag-l5.md](./rag-l5.md).

Mínimo:

- `topK` generoso (ex. 12) + fetch ampliado antes de filtrar
- **merge** agent-scoped + `global` (não só fallback se vazio)
- `minSimilarity` configurável (default lab ~0.22)
- bloco explícito quando **0 hits**: “contexto vazio — não inventar”

---

## Plan-execute / external mode

No `plan_runner` external:

- O artefacto do step anterior é **evidência** para o step seguinte.
- Skills com `done_when` devem falhar ou pedir human se faltarem factos obrigatórios — não “preencher de memória”.
- HITL antes de publish/spend continua obrigatório (`AGENTS.md`).

---

## Checklist rápido (agent/skill nova)

- [ ] Referência a `agents/_shared/grounding.directive.md` ou texto equivalente
- [ ] Secção “Não inventar” / anti-padrões com exemplos de domínio
- [ ] Se usa L5: documentar **qual** KB / agent_id / source
- [ ] Se usa banco operacional: **não** depender só de `ingest_knowledge`
