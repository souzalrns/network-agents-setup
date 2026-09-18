# Fase 3 — Auditoria de memória: Federação (MELD, Stigmem, ai-memory-mcp) + Sandbox + Observabilidade

Continuação de `FASE1-MEMORIA.md`/`FASE2-MEMORIA.md`.

## 1. MELD — correcção a uma afirmação minha anterior

Antes da Fase 1, mencionei ter encontrado uma org `memory-meld` no GitHub como possível implementação de referência. **Verifiquei agora e estava errado** — essa org não tem descrição, não tem blog, e os seus 13 repos são todos sobre kernel Linux, hypervisors, e benchmarks de memória de sistema operativo (`cloud-hypervisor`, `linux`, `go-ycsb`, `DeathStarBench`) — zero relação com o paper "MELD: A Protocol for Merging Knowledge Across Distributed Agentic Memories" (arXiv 2608.16357).

**Conclusão corrigida:** não encontrei nenhuma implementação de referência pública do protocolo MELD. Continua a ser **(C) referência conceptual** — o próprio paper, e a síntese já feita no `ADR-001` §5 e §10, são o que há para aproveitar. Não há biblioteca para instalar nem para "adaptar parcialmente" — só o modelo (5 outcomes, CRDT por claim, Patch) para reimplementar do zero, se se decidir por isso.

## 2. Stigmem (`eidetic-labs/stigmem`)

```
- Stars: 4 (real, via API)
- Licença: Apache-2.0
- Último push: 2026-06-18 -- mais de 3 meses parado à data de hoje
  (2026-09-18), apesar do estado "alpha" sugerir desenvolvimento activo
- 6 issues abertas
```

**Avaliação honesta:** o número de estrelas e o hiato de 3 meses sem push contradizem a impressão de "alpha activo" que a descrição sugere. Não é um projecto abandonado com certeza (pode estar em pausa por outras razões), mas não há evidência de tracção real. Tratar como **referência conceptual**, não como candidato a adopção nesta fase.

## 3. ai-memory-mcp — nome ambíguo, mas o correcto foi encontrado e confirmado

**Nome partilhado por pelo menos 5 repos distintos** (`alphaonedev/ai-memory-mcp`, `moorej2400/ai-memory-mcp`, `synapseradio/ai-memory-mcp`, `scanadi/mcp-ai-memory`, `supercorp-ai/memory-mcp`) — mesmo padrão de ambiguidade já visto com ContextForge/mcpguard/AIP. Identifiquei o correcto por correspondência de características, não por adivinhação:

```
Repo confirmado: alphaonedev/ai-memory-mcp
- Linguagem: Rust
- Licença: Apache-2.0
- Push mais recente: hoje (2026-09-18) -- activamente mantido
- Quorum writes W-of-N: CONFIRMADO no código/docs ("W-of-N writes,
  default majority")
- Hash chain assinado: CONFIRMADO ("tamper-evident coordination.<op>
  row... V-4 hash chain")
- CRDT: CONFIRMADO ("vector-clock CRDT-lite merge")
- mTLS entre peers: CONFIRMADO
- Chaos tests (partition/kill/timeout): NÃO VERIFICADO directamente
  nesta passagem -- os issues #1722/#1718 sugerem trabalho activo nessa
  área, mas não confirmei os testes em si
- Nota importante do próprio projecto: "not an agent runtime and not
  'autonomous AI' on its own" -- é claro sobre os seus próprios limites,
  sinal de maturidade de comunicação, não de marketing inflado
```

**Resposta à pergunta original ("infraestrutura útil para o futuro ou complexidade prematura?"):** dado que federação (Delegation Graph/Context Sync) já está no roadmap próprio (`ADR-001`), isto é **infraestrutura relevante para o futuro, não para agora** — o `ADR-001` já resolve a mesma classe de problema com peças mais alinhadas ao que já existe (AGT, capability grants). Vale como referência de padrão (W-of-N, hash chain assinado), não como adopção imediata.

## 4. Sandbox / execução

| Ferramenta | Stars reais | Licença | Nota |
|---|---|---|---|
| **OpenHands** (`OpenHands/OpenHands`) | **88.401** | MIT | De longe o mais popular de tudo o que foi avaliado nas 3 fases — inclusive mais que Mem0 |
| **E2B** (`e2b-dev/E2B`) | 13.868 | Apache-2.0 | Sandbox cloud, confirmado |
| **microsandbox** (`superradcompany/microsandbox`) | 8.287 | Apache-2.0 | Nota: o nome de utilizador do maintainer (`superradcompany`) não corresponde ao nome do projecto — confirmar que é mesmo o oficial antes de adoptar |
| SandboxAI | Não encontrado um repo canónico claro na busca | — | **NÃO VERIFICADO** — vários candidatos pequenos (0 estrelas), nenhum claramente "o" projecto |

**Relevância directa:** nenhum sandbox foi avaliado ao nível de integração com `plan_runner` nesta fase — a Parte 12 do pedido original só pedia identificar candidatos, não integrar. OpenHands, com 88k estrelas e MIT, é claramente o mais estabelecido se este tema avançar para uma fase de decisão.

## 5. Observabilidade

| Ferramenta | Stars reais | Licença | Nota |
|---|---|---|---|
| OpenTelemetry | NÃO VERIFICADO nesta passagem (padrão da indústria, conhecimento estável, não pesquisado de novo) | — | — |
| **Langfuse** | 34.774 | API devolveu `NOASSERTION` (**não confirma MIT/Apache como memória geral sugere — verificar manualmente antes de assumir**) | Popular, real |
| RAGAS | **NÃO VERIFICADO** — a busca pelo repo esperado (`explodinggradients/ragas`) não devolveu dados; nome/org pode estar errado | — | Precisa de nova busca antes de qualquer decisão |
| Attestix | Só 10 resultados genéricos numa busca — **não encontrei um projecto proeminente e específico com este nome** | — | Tratar como não confirmado, possivelmente nome incorrecto ou projecto muito pequeno |
| "Agent Passport" | **Fragmentado** — pelo menos 3 projectos pequenos e não relacionados (`aeoess/agent-passport-system` 45⭐, `Zerobase-labs/agent-passport` 15⭐, `aeoess/agent-passport-mcp` 4⭐) | — | Não há um "Agent Passport" dominante — é uma categoria de ideia (passaporte de identidade de agente), não um produto único maduro |

**Achado desta secção:** ao contrário das memórias (Parte 1-8), onde a maioria dos nomes correspondiam a projectos únicos e identificáveis, a secção de observabilidade tem **mais nomes vagos/fragmentados do que esperado** (Attestix, Agent Passport). Isto não significa que os conceitos (provenance, attestation) não sejam válidos — significa que ainda não há um produto dominante a adoptar, ao contrário de Langfuse/OpenTelemetry.

## 6. O que fica para a Fase 4

Síntese final: matriz de decisão completa (20 critérios), sobreposição entre projectos, arquitectura recomendada, decisão sobre S7, o que não construir, roadmap, riscos, questões em aberto — juntando as 3 fases já feitas.
