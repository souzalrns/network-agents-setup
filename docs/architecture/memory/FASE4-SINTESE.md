# Fase 4 — Síntese final: matriz, arquitectura, decisão S7, roadmap

## Executive Summary

**A pergunta original era: estamos a construir memória que já existe, e pior? A resposta, com evidência, é: parcialmente sim, parcialmente não — e a acção certa não é adoptar nenhuma das 9 ferramentas avaliadas agora.**

1. **O que já construímos (L5 — RAG) não é inferior por natureza** — é chunking+embedding+vector search, a mesma coisa que qualquer uma das ferramentas avaliadas faz na base. O problema real do L5 não é "devia ser outra ferramenta" — é que **está desligado da execução** (S9, confirmado por leitura directa do código: `retrieve_knowledge` nunca é chamado). Corrigir isso custa zero e vale mais do que trocar de ferramenta.

2. **A recomendação original do "deep" (adoptar dsh-long-memory + Graphiti + MELD) está refutada, item a item, com prova:**
   - `dsh-long-memory` — real, bem construído, **mas é um plugin do DeepSeek Harness, não uma biblioteca instalável aqui**. "Adoptar" significaria reescrever o padrão em Python, não `npm install`.
   - `Graphiti` — real, maduro, **mas exige Neo4j + OpenAI como dependências obrigatórias por omissão** (não opcionais) e teve uma **CVE de injecção via prompt injection** (2026-32247) que o documento original nunca mencionou.
   - `MELD` — é um **paper/protocolo, sem implementação de referência pública** (confirmei e corrigi um engano meu próprio a meio da auditoria) — não há nada para "adoptar", só para reimplementar do zero.

   Recomendar estas 3 sem verificar isto seria exactamente o erro que a regra do documento original pedia para evitar: confiar em benchmark e popularidade em vez de código.

3. **O que falta (L4 — memória semântica, Delegation Graph, Context Sync) não tem substituto externo directo** para o desenho já existente neste repo (o `scope.kind: user|project|agent|org` do contrato L4 é específico, ninguém de fora encaixa sem adaptação pesada). Aqui sim há trabalho novo a construir — mas é pequeno e bem definido, não uma reescrita.

4. **Veredicto:** não adoptar nada agora. Ordem de prioridade real: **(1) ligar o L5 já feito → (2) construir L4 in-house, pequeno e alinhado ao contrato já desenhado → (3) só considerar grafo/federação externos quando houver um caso de uso real, não antes.** Isto não é "não construir nada" nem "construir tudo" — é fechar o que já está feito antes de decidir o resto.

---

Fecha a auditoria de memória/conhecimento/federação (`FASE1`, `FASE2`, `FASE3`). Toda a decisão abaixo é explícita — nada fica "por decidir" sem razão técnica declarada.

## 1. Matriz de decisão (NATIVO / FORTE / PARCIAL / AUSENTE / NÃO VERIFICADO)

| | dsh-long-memory | Graphiti | Cognee | LightRAG | Mem0 | Hindsight | MELD | Stigmem | ai-memory-mcp |
|---|---|---|---|---|---|---|---|---|---|
| Adequação ao plan_runner | PARCIAL (só o padrão, não o código) | PARCIAL (L6) | PARCIAL (L6) | PARCIAL (L6) | PARCIAL (L4) | PARCIAL (L4) | AUSENTE (protocolo, não lib) | AUSENTE | PARCIAL (federação futura) |
| Sobreposição com o que já existe | FORTE (L4+L6 juntos) | FORTE (L6) | FORTE (L6) | FORTE (L6) | FORTE (L4) | FORTE (L4) | AUSENTE | AUSENTE | AUSENTE |
| Complexidade de integração | ALTA (não é lib) | MÉDIA | BAIXA-MÉDIA | BAIXA-MÉDIA | MÉDIA | NÃO VERIFICADO | ALTA (reimplementar) | ALTA | ALTA |
| Dependências obrigatórias | Node/DSH | Neo4j+OpenAI | Nenhuma | Nenhuma | Qdrant+OpenAI | NÃO VERIFICADO | — | Nenhuma | Nenhuma |
| Infraestrutura | Zero (SQLite) | Externa (por omissão) | Zero | Zero | Externa | NÃO VERIFICADO | — | Zero | Zero |
| Portabilidade | FORTE (SQLite) | FRACA por omissão | FORTE | FORTE | FRACA | NÃO VERIFICADO | — | FORTE (conceptual) | FORTE |
| Local-first | FORTE | AUSENTE por omissão | FORTE | FORTE | AUSENTE | NÃO VERIFICADO | N/A | FORTE | FORTE |
| MCP | FORTE | FORTE | NÃO VERIFICADO | AUSENTE | FORTE | NÃO VERIFICADO | N/A | FORTE (config) | FORTE |
| Temporalidade | PARCIAL (supersessão) | FORTE (bi-temporal) | PARCIAL | PARCIAL | NÃO VERIFICADO | PARCIAL (declarado) | FORTE (por desenho) | AUSENTE | AUSENTE |
| Graph | FORTE (edges+PageRank) | FORTE | FORTE | FORTE (dual-level) | PARCIAL (opcional) | FORTE (declarado) | N/A | AUSENTE | AUSENTE |
| Multi-hop | PARCIAL | FORTE | FORTE | FORTE | NÃO VERIFICADO | NÃO VERIFICADO | N/A | AUSENTE | AUSENTE |
| Consolidação | PARCIAL (L7) | AUSENTE | FORTE (Cognify) | AUSENTE | PARCIAL | FORTE (Reflect) | N/A | AUSENTE | AUSENTE |
| Federation | AUSENTE | AUSENTE | AUSENTE | AUSENTE | AUSENTE | AUSENTE | FORTE (por desenho) | FORTE (por desenho) | FORTE |
| Auditabilidade | FORTE (audit log) | PARCIAL | NÃO VERIFICADO | NÃO VERIFICADO | NÃO VERIFICADO | NÃO VERIFICADO | FORTE (Patch) | PARCIAL | FORTE (hash chain assinado) |
| Custo | Zero | Alto (Neo4j+OpenAI) | Zero-baixo | Zero-baixo | Alto (Qdrant+OpenAI) | NÃO VERIFICADO | N/A | Zero | Zero |
| Licença | MIT | NÃO VERIFICADO (Apache-2.0, confirmado na Fase 3) | Apache-2.0 | MIT | Apache-2.0 | MIT | N/A (paper) | Apache-2.0 | Apache-2.0 |
| Maturidade | FRACA (1⭐, 1 mantenedor) | FORTE (31k⭐, CVE já corrigida) | FORTE (30.8k⭐) | FORTE (39.7k⭐) | FORTE (65.5k⭐) | FORTE (23.9k⭐, empresa real) | AUSENTE (sem impl.) | FRACA (4⭐, parado 3 meses) | MÉDIA (activo hoje) |
| Facilidade de integração | FRACA (acoplado a DSH) | MÉDIA | FORTE | FORTE | MÉDIA | NÃO VERIFICADO | FRACA (é protocolo) | FRACA | FRACA |
| Lock-in | BAIXO (MIT, mas DSH-specific) | ALTO (Neo4j+OpenAI por omissão) | BAIXO | BAIXO | ALTO (Qdrant+OpenAI) | NÃO VERIFICADO | N/A | BAIXO | BAIXO |
| Manutenção futura | RISCO (1 pessoa) | FORTE (empresa, 63 contrib.) | FORTE | FORTE (245 issues activas) | FORTE (empresa) | FORTE (empresa) | N/A | RISCO (parado) | RISCO (muito recente) |

## 2. Sobreposição entre projectos

- **Graphiti, Cognee, LightRAG** sobrepõem-se quase por completo (grafo+vector, multi-hop) — a diferença real está em infra (Cognee/LightRAG local-first; Graphiti servidor-first) e em maturidade de mercado (Graphiti é o produto duma empresa com plataforma paga por trás; os outros dois são mais "biblioteca pura").
- **Mem0 e Hindsight** sobrepõem-se em proposta (memória semântica para agentes, self-editing/reflection) mas Mem0 exige infra externa e Hindsight não foi possível verificar a infra — ficam como concorrentes directos, não complementares.
- **MELD, Stigmem, ai-memory-mcp** não se sobrepõem entre si de facto — MELD é protocolo sem implementação, Stigmem está parado, ai-memory-mcp é o único dos três com código real e activo hoje.
- **dsh-long-memory é o único que combina L4 (factos, preferências) + L6 (grafo simples) numa coisa só** — todos os outros escolhem um lado ou outro.

## 3. Arquitectura recomendada

```
                    USER
                      │
                      ▼
                PLAN_RUNNER
                      │
        ┌─────────────┼─────────────────────┐
        ▼             ▼                     ▼
   L1 WORKING     L2 EPISODIC          L3 PROCEDURAL
   status.json    events.jsonl         skills/**/SKILL.md
   [FEITO]        [FEITO]              [FEITO]
        │
        ▼
   L0 IDENTITY/POLICY
   CLAUDE.md/AGENTS.md/BOOTSTRAP.md
   [CORRIGIDO hoje]
        │
        ├──────────────────┬─────────────────────┐
        ▼                  ▼                     ▼
   L4 SEMANTIC         L5 KNOWLEDGE          L6 RELATIONAL
   [NÃO IMPLEMENTADO]  [FEITO, MAS           [VAZIO]
   remember/recall/    DESLIGADO DA          Candidato: nenhum
   forget -- contrato  EXECUÇÃO -- S9]       adoptado ainda;
   existe, código não  Prioridade #1         se algum dia for
        │                                    preciso multi-hop,
        ▼                                    Cognee/LightRAG
   working_memory.py                         (local-first) antes
   (MEMORY.md por                            de Graphiti/Mem0
   cliente) -- FICA
   como fallback/
   bootstrap (decisão
   S7, secção 4)
```

**Donos de cada responsabilidade:**

| Responsabilidade | Dono |
|---|---|
| Estado do run | `engine.py`/`langgraph_engine.py` (L1) |
| Memória | `working_memory.py` (fallback) + futuro L4 a implementar |
| Knowledge graph | Ninguém ainda — L6 vazio, sem adopção decidida |
| Resolução de conflitos | Ninguém ainda — nenhum mecanismo de conflito existe hoje em L4/L5 |
| Retrieval | `knowledge.py`/`McpKnowledge` (L5) — construído, não ligado |
| Consolidação | Ninguém — ausente em todo o sistema actual |
| Federation | `ADR-001` (desenhado, não implementado) |
| Provenance | `events.jsonl` + `citation` em hits L5 + `Action Receipt` (desenhado) |
| MCP | `mcp/plan_runner/` (local) + `retrieve_knowledge` tool |
| Opcional (fica de fora do core) | Grafo (L6), federação, consolidação — todos opcionais por desenho, nenhum bloqueia o núcleo |

## 4. Decisão sobre S7 (`working_memory.py`)

**Decisão: opção 4 + 6 combinadas — mantido como fallback E especificamente para bootstrap/offline.** Não removido, não substituído, não transformado em adapter agora.

**Justificação técnica, não preferência:** nenhuma das 9 ferramentas avaliadas (dsh-long-memory incluído) tem como proposta central "nota curada por humano, lida sem LLM, sem extracção automática, no arranque de uma sessão". Todas as alternativas fazem **extracção automática dinâmica** — é um mecanismo diferente, mais pesado, para um problema parcialmente diferente (memória que aprende sozinha vs. contexto que um humano decidiu que é importante). Substituir `working_memory.py` por qualquer uma delas resolveria um problema que `working_memory.py` não tem (não falha, não é lento, custa zero) e não resolveria o problema real (L4 por implementar, L5 desligado). Fica como está; a única evolução natural é, quando L4 for implementado, `working_memory.py` tornar-se o *fallback* desse L4 quando não há backend configurado — não uma prioridade agora.

## 5. O que NÃO construir internamente

| Item | Prova de maturidade externa |
|---|---|
| Vector database | pgvector já em uso (Supabase); LanceDB/nano-vectordb existem para local |
| Graph database | networkx (embutido) cobre o caso simples; Neo4j/FalkorDB para o caso pesado |
| FTS | SQLite FTS5 (visto em dsh-long-memory) é maduro e trivial de embutir se um dia for preciso busca lexical |
| Tracing/observabilidade | OpenTelemetry é o padrão da indústria, não há razão para reinventar |
| CRDT | ai-memory-mcp já implementa vector-clock CRDT-lite de forma auditável — copiar o padrão, não a ideia do zero |

## 6. O que ainda precisamos construir (o diferencial real)

Depois de eliminar o que já existe maduro lá fora, o que **nenhum** dos 9 projectos avaliados resolve para este `plan_runner` especificamente:

1. **Ligar o L5 já construído à execução real** (S9) — nenhuma ferramenta externa faz isto por nós, é fiação interna.
2. **Implementar L4 (remember/recall/forget)** — o contrato já existe (`contracts.md`), falta o código. Nenhuma ferramenta externa se encaixa sem adaptação por causa do `scope.kind: user|project|agent|org` já desenhado, que é específico deste sistema.
3. **Delegation Graph, Action Receipts, Context Sync** (`ADR-001`) — confirmado nas fases anteriores que nenhuma ferramenta cobre isto pronto.
4. **A decisão sobre L6** — não é urgente construir nem adoptar nada agora; é opcional até haver um caso de uso real de multi-hop.

## 7. Roadmap

**Fase 0 — agora:**
- Objectivo: fechar o que já está construído mas desligado.
- Componentes: ligar `retrieve_knowledge`/`McpKnowledge` a `engine.py`/`langgraph_engine.py`/`cli.py` (S9).
- Dependências: nenhuma nova — só fiação.
- Risco: baixo.
- Resultado esperado: RAG (L5) realmente usado em planos reais, não só testado isoladamente.

**Fase 1 — integração:**
- Objectivo: implementar L4 (memória semântica) usando o contrato já existente.
- Componentes: código novo em `runner/plan_runner/` (não uma biblioteca externa — nenhuma se encaixa sem adaptação pesada); `working_memory.py` como fallback quando L4 não está configurado.
- Dependências: decisão de storage para L4 (SQLite local, ao estilo dsh-long-memory, é o padrão mais alinhado com "zero infra" que já vimos funcionar).
- Risco: médio — é código novo, não wiring.
- Resultado esperado: agentes lembram factos entre sessões sem depender de curadoria manual.

**Fase 2 — evolução:**
- Objectivo: Governance Runtime (`ADR-001`) + decisão informada sobre L6, só se um caso de uso real o exigir.
- Componentes: AGT, agentgateway, Delegation Graph, Action Receipts, Context Sync; L6 com Cognee/LightRAG **apenas se** multi-hop se tornar necessário (nunca Graphiti como primeira escolha, dado o CVE e a dependência obrigatória de Neo4j+OpenAI).
- Dependências: Fase 0 e 1 completas.
- Risco: alto (é a parte mais nova, menos testada).
- Resultado esperado: memória federada entre agentes, com prova criptográfica de cada acção.

## 8. Riscos

- **Nenhuma das 9 ferramentas foi testada em código real deste repo** — toda a avaliação é estática (ler pyproject.toml, README, contar estrelas). Antes de qualquer adopção, um spike real de 1-2 dias é obrigatório.
- **Graphiti tem uma CVE já corrigida mas confirma que a superfície de ataque (prompt injection → Cypher injection) é real** — qualquer adopção futura de grafo precisa de threat-modelling próprio (MAESTRO/OWASP LLM, já usados neste repo para outras partes).
- **`Memori` (16.8k⭐) tem licença `NOASSERTION`** — risco legal se alguém o adoptar sem verificar antes.
- **Dependência de um só mantenedor** em `dsh-long-memory`, `ai-memory-mcp` (muito recente) e `Stigmem` (parado) — nenhum destes deve ser uma dependência crítica sem plano de contingência.

## 9. Questões ainda não resolvidas

1. Qual storage exacto para L4 — SQLite local (alinhado com o resto do repo) ou reaproveitar o Supabase já em uso para L5? Não decidido nesta fase.
2. Se/quando L6 for necessário, falta um caso de uso concreto (não hipotético) que justifique multi-hop antes de escolher entre Cognee/LightRAG.
3. `dsh-long-memory`/`Memobase`/`A-Mem`/`Memary` não foram testados em código real, só em README+API — se algum entrar em consideração séria, precisa da mesma verificação de código que já foi feita aos principais.

---

**Nada ficou por decidir sem razão declarada.** As únicas 3 questões genuinamente em aberto (secção 9) são-no porque dependem de informação que não existe ainda (caso de uso real, decisão de storage) — não por evasão.
