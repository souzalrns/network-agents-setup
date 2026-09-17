# Governança — visão geral da camada

Governança é o novo foco do projecto. Este documento consolida o que já existe (`packages/core/`), o que uma ferramenta externa cobre (AGT), e o que fica como trabalho próprio — sem repetir o detalhe linha-a-linha, que fica nos dois documentos-fonte citados ao longo do texto.

**Fontes:** [`CORE-MAPPING.md`](./CORE-MAPPING.md) (mapeamento dos 39 ficheiros de `packages/core/src/`) e [`governance/ROADMAP-GOVERNANCE.md`](./governance/ROADMAP-GOVERNANCE.md) (cronograma, verificação externa do AGT e das dependências). Tudo aqui vem de lá — este documento não introduz factos novos, só reorganiza para dar uma entrada única ao tema.

## 1. O que é a camada de governança

Neste contexto, "governança" cobre 5 preocupações:

- **Policy** — decidir se uma acção é permitida, e a que nível de escrutínio (`DeliberationEngine`, e futuramente o Agent OS do AGT).
- **Identity** — saber quem (que agente, com que credenciais) está a pedir a acção (`SecurityManager` hoje, AgentMesh do AGT no futuro).
- **Delegation** — quando um agente delega trabalho a outro, saber com que âmbito e até onde vai a confiança transmitida (gap actual — ver secção 4).
- **Receipts** — prova imutável de que uma decisão foi tomada e por quem (gap actual — ver secção 4).
- **Compliance** — conformidade com normas externas e gestão de dados (`ComplianceManager`, `DataGovernance` hoje; Agent Compliance do AGT no futuro).

**Onde vive:** `packages/core/` (o que já está escrito, ver secção 2) + AGT (ferramenta externa a adoptar, ver secção 3) + a "cola" ainda por construir (ver secção 4).

**O que NÃO é:**
- Não é o motor (`plan_runner`) — o motor executa planos; a governança decide se uma acção dentro de um plano é permitida.
- Não é o RAG — o RAG dá conhecimento; a governança dá controlo.
- Não é o HITL sozinho — o `HitlManager` é **um** dos 7 módulos de governança (aprovação humana), não a camada inteira.

## 2. O que já existe no setup

7 módulos de `packages/core/src/` tocam directamente em governança (fonte: `CORE-MAPPING.md`):

| Módulo | O que faz | Estado | O que falta |
|---|---|---|---|
| `governance/DeliberationEngine.ts` | Scoring ponderado (impacto/incerteza/risco/reversibilidade/custo/dependências) que decide o nível de aprovação necessário — operational/tactical/strategic/constitutional | **REAL** | Nada — funciona como está |
| `governance/TrustManager.ts` | Certificação de competências por 6 níveis de confiança (LEVEL_0 a LEVEL_5), com limites de autonomia (`AutonomyBoundary`) por competência | INCOMPLETO | Persistência — todo o estado (`Map`) perde-se num restart |
| `governance/ArchitectureCouncil.ts` | Fluxo de propostas arquiteturais → revisão/auto-aprovação → registo de decisões (ADRs) | INCOMPLETO | Persistência das propostas/decisões |
| `security/SecurityManager.ts` | Autenticação, sessões, RBAC, MFA, detectores heurísticos (prompt injection, jailbreak) | **MOCK** | Tudo — `verifyPassword()` devolve sempre `true`, hash sem salt, `verifyMFA()` aceita código fixo `'123456'`. Não é base reaproveitável |
| `compliance/ComplianceManager.ts` | Consentimento LGPD/GDPR, pedidos de titular de dados, logs de auditoria | **MOCK** | Lógica real — `processDataRequest` devolve strings fixas sem apagar nada; `getStats()` tem `complianceScore: 80` hardcoded |
| `data/DataGovernance.ts` | Classificação de activos de dados, linhagem, score de qualidade | **MOCK** | `observeData()` é simulação explícita — a parte de classificação/linhagem tem mais substância que os outros MOCK, mas a ingestão é vazia |
| `hitl/HitlManager.ts` | Pedidos de aprovação humana (pending/approved/rejected/expired) + checkpoints | INCOMPLETO | Persistência — 5 `Map`s, todo o estado de aprovação é volátil |

**Resumo do estado:** 1 REAL, 3 INCOMPLETO, 3 MOCK. Nenhum dos 3 MOCK (Security, Compliance, Data) vale a pena "consertar" incrementalmente — ver secção 3.

## 3. O que o AGT cobre

**Microsoft Agent Governance Toolkit** (`microsoft/agent-governance-toolkit`, licença MIT, "Microsoft-signed public preview", cobre 10/10 do OWASP Agentic Top 10 2026) — dados confirmados por pesquisa directa na documentação/repositório do projecto (não inferência):

| Componente AGT | O que faz | Substitui ou complementa |
|---|---|---|
| **Agent OS** (Policy Engine) | Motor de políticas declarativas (YAML, OPA Rego, ou Cedar); classifica acções como `DESTRUCTIVE_DATA`/`DATA_EXFILTRATION`/`PRIVILEGE_ESCALATION` e bloqueia/reduz confiança | **Substitui** o `DeliberationEngine` como motor de decisão de facto — mas o `DeliberationEngine` (REAL) pode continuar a alimentar o *score*, com o Agent OS a aplicar a política final |
| **AgentMesh** (Identity) | Identidade zero-trust por DID (`did:mesh:...`), Ed25519, confiança que decai sem sinal positivo, patrocínio humano por agente | **Substitui** por completo o `SecurityManager` (MOCK) — mais barato adoptar do que consertar |
| **Agent Hypervisor** | Anéis de privilégio tipo CPU (Ring 0–3); agentes novos entram no Ring 3 e sobem por mérito (trust score); logs em cadeia Merkle | **Complementa** — mapeia conceptualmente para o `TrustManager` (já tem a ideia de "subir de nível"), mas dá a componente de isolamento/execução que não existe hoje |
| **Agent SRE** | SLOs, orçamento de erro, kill switch, disjuntores para falhas em cascata | **Complementa** — nada equivalente existe hoje |
| **Agent Compliance** | Mapeamento formal a normas (EU AI Act, SOC 2, HIPAA, OWASP Agentic Top 10) | **Substitui** o `ComplianceManager` (MOCK, sem mapeamento nenhum) |
| **MCP Security Gateway** | Intercepta chamadas de ferramenta MCP; deteta *tool poisoning*, *rug pulls*; faz *rate limiting* e aprovação humana opcional | **Complementa** — nada equivalente hoje; directamente relevante para o `agent-network-mcp` |

**Nota sobre números verificados:** a latência do stack completo (policy + trust + ring + auditoria Merkle) medida pelo próprio projecto é **~0,07ms p50 / ~0,42ms p99** — não uma latência universal "<0,1ms" fixa. O número de pacotes independentes do AGT também **varia por versão** (fontes falam em "nove", mas versões recentes consolidam 5 pacotes antigos num só `agent-governance-toolkit-core`) — não fixar um número sem confirmar a versão instalada.

## 4. O que falta construir (a "cola")

O AGT cobre identidade, política e execução — não cobre a delegação entre agentes desta rede nem a sincronização de contexto entre eles:

| Componente | O que é | Esforço | Dependências |
|---|---|---|---|
| **Delegation Graph** | Schema + implementação que regista quem delegou o quê a quem, com que âmbito e até quando — tecto de confiança rastreável numa cadeia de delegação | Médio — schema rápido, validação da cadeia é o grosso | AgentMesh (identidade dos nós), `TrustManager` (níveis de confiança) |
| **Action Receipts** | Recibo assinado e encadeado por hash por acção governada. O AGT já tem cadeia Merkle de auditoria — o trabalho é adaptar o formato, não construir hash-chaining do zero | Baixo-médio — primitiva já existe, é adaptação | AGT (`agent-mesh` audit chain) |
| **Context Sync** | Sincronização de contexto partilhado entre agentes de forma federada, sem depender de um processo central | Alto — o item com menos cobertura externa | Delegation Graph (escopo de acesso) |
| **Integração AGT no MCP + `plan_runner`** | Ligar o Agent OS/AgentMesh de facto ao `agent-network-mcp` e ao motor | Depende do resto | Delegation Graph, Action Receipts, Context Sync já decididos |

## 5. Cronograma (resumo)

8–12 sessões — detalhe completo em [`governance/ROADMAP-GOVERNANCE.md`](./governance/ROADMAP-GOVERNANCE.md) secção 4:

| Sessão | Entregável |
|---|---|
| 1–2 | Schemas de `delegation-graph` e `action-receipt` |
| 3–4 | Delegation Graph implementado |
| 5 | Action Receipts (adaptação da cadeia Merkle do AGT) |
| 6 | Context Sync — primeira versão |
| 7–8 | Integração do AGT no `agent-network-mcp` e no `plan_runner` |
| 9–10 | Testes de conformidade (`agt verify` + testes próprios) |
| 11–12 | Endurecimento + documentação |

## 6. Dependências externas

| Dependência | Licença | O que faz |
|---|---|---|
| **SPIFFE/SPIRE** | Apache-2.0 | Identidade de *workload* (genérica, não específica de IA) — projecto CNCF graduado |
| **OpenA2A AIM** | Apache-2.0 | IAM para agentes de IA — identidade criptográfica, autorização por capacidade, *trust score* de 9 factores |
| **agentgateway** (solo.io) | Apache-2.0 | *Data plane* para tráfego MCP, A2A e LLM |
| **ContextForge** | — ver nota | Discovery — **ambíguo**, ver abaixo |
| **Cedar / OPA** | Apache-2.0 | Motores de política declarativa (usados pelo próprio Agent OS do AGT) |
| **Microsoft AGT** | MIT | Ver secção 3 — nº de pacotes varia por versão |

**Nota sobre "ContextForge":** existem **dois projectos distintos** com este nome — `mcp-context-forge` (gateway/registo/proxy MCP com discovery, o candidato mais provável) e `waterflane/ContextForge` (ferramenta não relacionada, para contexto de agentes de código). Confirmar qual antes de adoptar qualquer um.

## 7. O que NÃO fazer no MVP

- Memória federada completa
- Context Graph completo
- Multi-vendor real (Claude ↔ Gemini)
- Kill-switch federado global
- Compliance frameworks completos (o AGT tem mapeamento para EU AI Act/SOC 2/HIPAA/ISO 42001, mas adoptar tudo de uma vez não é MVP)

## 8. Referências

- [`CORE-MAPPING.md`](./CORE-MAPPING.md) — os 39 ficheiros de `packages/core/`
- [`governance/ROADMAP-GOVERNANCE.md`](./governance/ROADMAP-GOVERNANCE.md) — cronograma completo, verificação externa
- [`ECOSYSTEM.md`](./ECOSYSTEM.md) — visão geral do ecossistema (setup ↔ MCP)
- [`plug-in-agents.md`](./plug-in-agents.md) — visão original das 3 camadas
