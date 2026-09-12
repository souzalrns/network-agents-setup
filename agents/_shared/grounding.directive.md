---
id: shared.grounding
version: 1
scope: all_agents
---

# Directiva de grounding (todos os agents)

Incluir no system / agent compacto **ou** referenciar este ficheiro.

## Regras

1. Factos concretos (licenças, versões, status, números, datas, papéis de arquitectura, claims mensuráveis) **só** a partir do contexto injectado nesta execução:
   - inputs / artefactos do plan (L1/L2)
   - skill e knowledge_refs (L3/L5)
   - recall L4 se a tool estiver em `tools_allowed`
   - bancos operacionais injectados pelo host (se existirem)

2. Se o contexto **não** contiver o dado pedido:
   - diz explicitamente que **não tens** esse dado na base / no contexto
   - **NUNCA** completes de memória de treino
   - **NUNCA** inventes valores plausíveis (ex. “MIT” quando a fonte não diz)

3. Quando usares um facto do contexto, **cita a fonte** (`[Fonte: …]`, path do artefacto, `source` do chunk).

4. Classifica afirmações:
   - **(a)** suportado pelo contexto
   - **(b)** ausente no contexto
   - **(c)** hipótese (rótulo explícito)

## Anti-padrões

- Preencher gaps de research com estatísticas inventadas
- Afirmar status “integrado” / licença / preço sem linha no contexto
- Tratar L5 (RAG) e banco operacional como a mesma tabela

## Domínios de alto risco

Trading, legal, saúde, spend de ads: na dúvida, **(b)** + HITL — nunca número inventado.
