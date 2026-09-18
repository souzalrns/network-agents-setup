# Fase 2 — Auditoria de memória: LightRAG, Mem0, Hindsight, outras memórias

Continuação de `FASE1-MEMORIA.md`. Mesma disciplina: verificado em código/API real, não em README.

## 1. LightRAG (`HKUDS/LightRAG`)

```
- Stars: 39.748 (real, via API) — mais que Graphiti e Cognee
- Licença: MIT
- Dependências base: `nano-vectordb` (vector embutido) + `networkx`
  (grafo embutido) — LOCAL-FIRST por omissão, tal como o Cognee, ao
  contrário do Graphiti
- Também depende de `google-genai` directamente na base (não é extra)
- Grafo dual-level: entidade + tema, confirmado na descrição oficial
- API REST real, confirmada em código: `lightrag/api/lightrag_server.py`
  com routers `document_routes.py`, `graph_routes.py`, `query_routes.py`,
  `ollama_api.py` (suporte nativo a Ollama = caminho 100% local possível)
- MCP: NÃO encontrado — só 2 resultados incidentais numa busca de código
  no repo, nada que indique servidor MCP nativo
- Incremental update: confirmado pela própria natureza do dual-level
  graph (não é o foco desta verificação aprofundar o mecanismo exacto)
- Maturidade: Beta declarado no próprio `pyproject.toml`
  ("Development Status :: 4 - Beta"), 245 issues abertas — sinal de uso
  real, não abandonado
```

**Comparação directa com Graphiti/Cognee:** dos 3, é o único com API REST própria já pronta e com suporte nativo a Ollama (LLM 100% local). Não tem MCP nativo (Graphiti e Mem0 têm). Arquitectura de infra: tão local-first quanto o Cognee, mais popular que os dois.

## 2. Mem0 (`mem0ai/mem0`)

```
- Stars: 65.575 (real) — o mais popular de todos os avaliados até agora
- Licença: Apache-2.0
- Dependências base: `qdrant-client` (Qdrant é EXTERNO — precisa de
  servidor, self-hosted ou cloud) + `openai` OBRIGATÓRIO
- Extras de vector store: chromadb, weaviate, pinecone, cassandra,
  vecs (Supabase) — muitas opções, mas todas externas
- MCP: confirmado, e extensamente — `integrations/claude-code-plugin`,
  `integrations/codex-plugin`, `integrations/antigravity-plugin`,
  `agent-plugin-core` genérico. É o mais integrado com ferramentas de
  IDE/agentes de todos os avaliados
- Scopes user/session/agent: confirmado pela documentação oficial
- Self-editing: não verificado ao nível de código nesta passagem —
  **NÃO VERIFICADO**
```

**Nota de infra:** ao contrário do LightRAG/Cognee, o Mem0 não tem um caminho "zero infra" na configuração base — precisa sempre de um vector store externo (Qdrant por omissão). Isto é uma desvantagem directa face ao princípio "capaz de funcionar sem infraestrutura externa obrigatória" do pedido original.

## 3. Hindsight (`vectorize-io/hindsight`)

```
- Stars: 23.883 (real, repo canónico confirmado — há muitos forks sob
  contas de terceiros com o mesmo README, não são projectos distintos)
- Licença: MIT
- Empresa por trás: Vectorize (real, tem outros repos activos:
  vectorize-mcp-server com 110 stars, hindsight-cookbook, hindsight-skills)
- Actividade: push mais recente há horas — mantido activamente
- Estrutura de memória: World facts / Experiences / Observations /
  Mental models, "memory banks" — confirmado pela documentação oficial
- Métodos: Retain / Reflect (+ um terceiro não detalhado nesta pesquisa)
- Benchmark LongMemEval: a alegação de "state-of-the-art" é
  PARCIALMENTE independente — o próprio texto do projecto diz que foi
  "independently reproduced by research collaborators at Virginia Tech
  Sanghani Center... and The Washington Post", o que é mais forte que
  benchmark autorreportado puro, mas "Fortune 500 em produção" continua
  a ser afirmação do próprio vendor, não verificável externamente
- Infra necessária: NÃO VERIFICADO em detalhe nesta passagem (o
  pyproject.toml raiz é só o wrapper do monorepo, não lista as
  dependências reais dos pacotes internos)
- MCP: NÃO VERIFICADO directamente, mas a Vectorize já mantém um
  `vectorize-mcp-server` (110 stars) — sugere que existe caminho MCP,
  não confirmei se é o mesmo produto
```

## 4. Comparação directa: LightRAG vs Mem0 vs Hindsight vs Graphiti vs Cognee

| | Stars reais | Licença | Infra obrigatória | MCP nativo | Local-first por omissão |
|---|---|---|---|---|---|
| Mem0 | 65.575 | Apache-2.0 | Qdrant (externo) | ✅ Extenso | ❌ |
| LightRAG | 39.748 | MIT | Nenhuma | ❌ | ✅ |
| Cognee | 30.799 | Apache-2.0 | Nenhuma | NÃO VERIFICADO | ✅ |
| Graphiti | 30.978 | NÃO VERIFICADO | Neo4j+OpenAI | ✅ | ❌ (`falkordblite` é excepção) |
| Hindsight | 23.883 | MIT | NÃO VERIFICADO | NÃO VERIFICADO | NÃO VERIFICADO |

**Achado transversal:** popularidade (estrelas) e "local-first por omissão" são **inversamente correlacionados** nesta amostra — os 2 mais populares (Mem0, e Graphiti perto) exigem infra externa por omissão; os "local-first" (LightRAG, Cognee) são populares mas não os líderes. Isto não é coincidência acidental — ferramentas pensadas para produção enterprise tendem a assumir infra gerida; ferramentas pensadas para adopção individual tendem a embutir tudo. Vale ter isto em mente ao decidir: o objectivo é "o mais adoptado" ou "o mais alinhado com zero-infra"?

## 5. Outras memórias (Parte 8) — tabela

| Nome | Inovação principal | Stars reais | Licença | Local | MCP | Temporal | Graph | Adequação ao plan_runner |
|---|---|---|---|---|---|---|---|---|
| A-Mem | Zettelkasten (notas ligadas) | 1.180 | MIT | NÃO VERIFICADO | NÃO VERIFICADO | NÃO VERIFICADO | Sim (notas ligadas) | Baixa prioridade — nicho académico |
| Memobase | User-profile, time-aware | 2.905 | Apache-2.0 | NÃO VERIFICADO | NÃO VERIFICADO | Parcial (declarado) | NÃO VERIFICADO | Média — foco em perfil de utilizador pode servir L4 |
| Memary | Reasoning trails, KG | 2.648 | MIT | NÃO VERIFICADO | NÃO VERIFICADO | NÃO VERIFICADO | Sim | Linguagem principal é Jupyter Notebook — sinal de projecto mais experimental que produto |
| Memori | LLM-agnostic, enterprise/on-prem | **16.795** (muito mais popular do que o "deep" sugeria) | NOASSERTION (sem licença clara — **risco legal real**, verificar antes de qualquer uso) | NÃO VERIFICADO | NÃO VERIFICADO | NÃO VERIFICADO | NÃO VERIFICADO | Popularidade alta merece segunda olhada, mas licença por confirmar é bloqueio real |
| MemOS | OS-style scheduler, MemCubes | 11.448 | Apache-2.0 | NÃO VERIFICADO | NÃO VERIFICADO | NÃO VERIFICADO | NÃO VERIFICADO | Linguagem TypeScript (não Python) — integração com `plan_runner` (Python) exigiria ponte |
| LangMem | Primitivas de memória LangChain | 1.671 | MIT | Depende do backend LangGraph escolhido | Não aplicável (é lib, não servidor) | NÃO VERIFICADO | NÃO VERIFICADO | **Relevante** — `plan_runner` já usa LangGraph (`SqliteSaver`); esta é a única desta lista com sobreposição arquitectural directa e comprovada com o motor já em uso |
| EverMemOS | Lifecycle MemCells→MemScenes | — | — | — | — | — | — | **Confirmado: sem repositório público encontrado** — é paper, como o "deep" já dizia |
| ENGRAM | Typed memory, dense-only | — | — | — | — | — | — | **Confirmado: sem repositório correspondente encontrado** — buscas devolvem projectos homónimos não relacionados (framework JS, etc.) |

**Achado que muda uma prioridade:** `Memori` tem **16.795 estrelas reais** — muito mais popular do que a tabela do "deep" sugeria (não lhe atribuiu número). Mas tem `license: NOASSERTION` — GitHub não conseguiu determinar uma licença clara no repo. Isto é um risco real de adopção, não um detalhe menor, e não estava sinalizado antes.

**Achado mais relevante ao `plan_runner` especificamente:** `LangMem` é a única desta lista de 8 com sobreposição arquitectural directa comprovada — o motor já usa `langgraph.checkpoint.sqlite.SqliteSaver`. Se algo desta lista vale a pena avaliar com profundidade extra na Fase 4, é este, não os mais populares.

## 6. O que fica para a Fase 3

MELD, Stigmem, ai-memory-mcp (federação) + Sandbox/Observabilidade — nenhum verificado ainda nesta ronda, à excepção do MELD (já confirmado real na conversa antes da Fase 1).
