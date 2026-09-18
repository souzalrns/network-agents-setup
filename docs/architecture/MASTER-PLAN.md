# Master Plan — Estrutura completa do sistema (2026-09-18)

Mapa consolidado de tudo o que foi feito, o que precisa alterar, e o que precisa criar — juntando o trabalho de mapeamento (`CORE-MAPPING.md`, `MCP-MAPPING.md`), governança (`GOVERNANCE.md`, `ADR-001`), segurança (`SECURITY.md`, `SECURITY-AUDIT*.md`) e a análise de bootstrap de sessão feita nesta conversa.

## Diagrama da arquitectura completa

```
                                    UTILIZADOR
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │   BOOTSTRAP DA SESSÃO           │
                        │   CLAUDE.md + AGENTS.md          [ALTERAR]
                        │   (aponta para ficheiro errado)  │
                        └───────────────┬───────────────┘
                                        │
                                        ▼
        ┌───────────────────────────────────────────────────────────┐
        │              NETWORK-AGENTS-SETUP  (núcleo do produto)      │
        │                                                              │
        │  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐ │
        │  │   MOTOR      │  │  GOVERNANÇA   │  │   HORIZONTAIS       │ │
        │  │ plan_runner  │  │ packages/core │  │ skills/ + agents/    │ │
        │  │  [FEITO]     │  │  [FEITO]      │  │  [FEITO]             │ │
        │  │ 167 testes   │  │ mapeado:      │  │ G2: +16 skills       │ │
        │  │              │  │ 5 REAL        │  │ G4: +13 agentes      │ │
        │  │              │  │ 19 INCOMPLETO │  │ B2: +security_auditor│ │
        │  │              │  │ 14 MOCK       │  │                      │ │
        │  └──────┬───────┘  └──────┬───────┘  └──────────┬──────────┘ │
        │         │                  │                      │             │
        │         │          ┌───────▼────────┐             │             │
        │         │          │ GOVERNANCE      │             │             │
        │         │          │ RUNTIME         │             │             │
        │         │          │  [CRIAR]        │             │             │
        │         │          │ ADR-001 já      │             │             │
        │         │          │ desenhou o      │             │             │
        │         │          │ contrato, falta │             │             │
        │         │          │ implementar:    │             │             │
        │         │          │ - Delegation    │             │             │
        │         │          │   Graph         │             │             │
        │         │          │ - Action        │             │             │
        │         │          │   Receipts      │             │             │
        │         │          │ - Context Sync  │             │             │
        │         │          └────────┬────────┘             │             │
        │         ▼                   │                      ▼             │
        │  ┌─────────────┐            │             ┌────────────────────┐│
        │  │     RAG      │            │             │  MCP LOCAL           ││
        │  │ knowledge.py │            │             │ mcp/plan_runner      ││
        │  │  [FEITO]     │            │             │  [FEITO], mas        ││
        │  │ 110 chunks   │            │             │  policy.py:73        ││
        │  │ McpKnowledge │            │             │  [ALTERAR]           ││
        │  │ retry+budget │            │             │  (execução sem chave,││
        │  │  [FEITO]     │            │             │  aviso ≠ fechado)    ││
        │  │  MAS falha   │            │             └────────────────────┘│
        │  │  por quota   │                                                 │
        │  │  diária      │                                                 │
        │  │  [ALTERAR]   │                                                 │
        │  └─────────────┘                                                 │
        └───────────────────────────────┬────────────────────────────────┘
                                          │ plug-in
                                          ▼
                        ┌───────────────────────────────┐
                        │       AGENT-NETWORK-MCP          │
                        │   (verticais — 20 agentes,        │
                        │    proprietários, ficam aqui)      │
                        │        [FEITO — intocado]          │
                        └───────────────────────────────┘
```

## O que já foi feito

| Camada | Item | Evidência |
|---|---|---|
| Mapeamento | `CORE-MAPPING.md`, `MCP-MAPPING.md`, `ROADMAP-GOVERNANCE.md` | Leitura directa, não inferência |
| Horizontais | G2 (16 skills), G3 (5 knowledge packs), G4 (13 agentes) | Migrados de `agent-network-mcp`, termos privados limpos |
| Segurança | `security_auditor` + skill + `SECURITY.md` + 2 auditorias reais | 8 ferramentas correram de verdade |
| Correcções | CodeQL #5 (bcrypt), #6 (escaping), Dependabot majors, 4 workflows com `permissions:` | Testado, não só escrito |
| RAG | pipeline completo + retry/budget para 429 | Falha continua (quota diária) |
| Governança (desenho) | `ADR-001` — pipeline de 10 passos, 5 contratos, modelo de delegação, identidade, State×Memory | Ainda não implementado |
| Ecossistema | `ECOSYSTEM.md`, `README.md` corrigidos (núcleo vs plugin) | |

## O que precisa alterar

| Item | Problema | Decisão pendente |
|---|---|---|
| `CLAUDE.md` | Bootstrap aponta para `docs/STATUS.md` (18/08, desactualizado), não menciona nenhum dos 11 docs de hoje | — |
| `AGENTS.md` | "lab/método" (desactualizado); "não misturar sem decisão explícita" (já superado pelo G2/G4) | — |
| `docs/STATUS.md` vs `docs/initiatives/STATUS.md` | Dois sistemas paralelos, um deles ligado a rollup de 9 repos | **Do utilizador, ainda pendente** |
| Terminologia RAG | `AGENTS.md` fala em "L5"/`rag-l5.md`; trabalho de hoje fala em "C8"/T6 | Não esclarecido — mesma coisa ou duas iniciativas? |
| `mcp/plan_runner/policy.py:73` | Execução sem chave no perfil `moderate` — só avisado, não fechado | Exige mudar um teste existente que fixa o comportamento inseguro como esperado |
| OSV-Scanner, Trivy `vuln` | Bloqueados pela rede da sandbox de trabalho | Precisa de outro ambiente para correr |

## O que precisa criar

1. **Delegation Graph** — implementação real do contrato já desenhado no `ADR-001` (reaproveitando `CapabilityGrant` do AGT).
2. **Action Receipts** — adaptar a cadeia Merkle do AGT ao formato do `ADR-001`.
3. **Context Sync** — o "Federated State Model" do `ADR-001` é proposta original, ainda por construir.
4. **Reconciliação `CLAUDE.md`/`AGENTS.md`** com o estado de hoje.
5. **Parte 1 da auditoria de memória** — mapear `working_memory.py`/`events.jsonl`/`knowledge.py` célula a célula (proposto, nunca feito a sério).
6. **Fecho real do `policy.py:73`** — exige a decisão humana já identificada.

## Repos externos — ACOPLAR (instalar, o código deles corre)

| Repo | Porquê | Estado da decisão |
|---|---|---|
| `microsoft/agent-governance-toolkit` (AGT) | Agent OS (Cedar/OPA), AgentMesh (identidade Ed25519+DID), Agent Hypervisor (Merkle) | Decidido no `ADR-001` — ainda não instalado |
| `agentgateway` (solo.io) | Data plane MCP/A2A/HTTP | Decidido no `ADR-001` — ainda não instalado |
| `tayler-id/mcphound` | Reputação + `mcp-policy.yaml` em CI | Decidido — ainda não instalado |
| `bcryptjs` | Hash de password | **Já instalado** (correcção CodeQL #5) |
| `offsec-ai` | Auditoria (só modos passivos) | Já usado como ferramenta de auditoria, não produção |
| `OpenA2A AIM`, `Cedar`/`OPA` | Identidade/política complementar | Decidido, não instalado |

## Repos externos — EXTRAIR (copiar a ideia, não o código)

| Repo/fonte | O que se extrai | Porquê não se instala |
|---|---|---|
| ECC (Everything Claude Code) | **Já extraído** — as 16 skills do G2 vieram daqui | Eram skills/técnicas, não uma lib para instalar |
| `obra/superpowers` | **Já extraído** — `meta-workflow` | Idem |
| `wwskills/dsh-long-memory` | A ideia (SQLite+FTS5+embedding opcional+L7+audit log) | É plugin específico do DeepSeek Harness — não corre fora dele |
| MELD (paper) | O modelo (5 outcomes, CRDT por claim, Patch) — já reflectido no `ADR-001` §10 | É um protocolo/paper, não uma biblioteca |
| `draft-prakash-aip` / `draft-singla-aip` | Atenuação de âmbito por salto — já no `ADR-001` §5 | Especificações IETF, não código |
| `aws-samples/sample-agentic-delegation` | Padrão de encadeamento pai→filho por hash — já no `ADR-001` §5 | Blueprint de referência, "não pronto para produção" |
| Graphiti, Mem0, Cognee, LightRAG | **Nada extraído ainda** — avaliados, não decidido | Precisam da Parte 1 (mapear o que já temos) antes de qualquer decisão |

## Referências

- [`ECOSYSTEM.md`](./ECOSYSTEM.md) — visão geral setup ↔ MCP
- [`GOVERNANCE.md`](./GOVERNANCE.md) — camada de governança
- [`adr/ADR-001-governance-runtime.md`](./adr/ADR-001-governance-runtime.md) — contratos e pipeline
- [`CORE-MAPPING.md`](./CORE-MAPPING.md) — 39 ficheiros de `packages/core/`
- [`MCP-MAPPING.md`](./MCP-MAPPING.md) — 33 agentes do `agent-network-mcp`
- [`SECURITY.md`](./SECURITY.md) / [`SECURITY-AUDIT.md`](./SECURITY-AUDIT.md) / [`SECURITY-AUDIT-FULL.md`](./SECURITY-AUDIT-FULL.md)
- [`RATE-LIMITS.md`](./RATE-LIMITS.md)
- [`../initiatives/STATUS.md`](../initiatives/STATUS.md) — pendências detalhadas
