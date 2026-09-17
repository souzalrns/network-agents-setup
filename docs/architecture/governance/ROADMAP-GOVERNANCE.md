# Roadmap — Camada de Governança

Cronograma ajustado para a camada de governança, cruzando o que o setup já tem (`CORE-MAPPING.md`), o que uma ferramenta open source de terceiros (Microsoft Agent Governance Toolkit — AGT) já cobre, e o que fica como trabalho próprio ("a cola").

**Nota de verificação:** os dados sobre o AGT e as dependências externas (secções 2 e 5) foram confirmados por pesquisa directa na documentação/repositório de cada projecto nesta tarefa — não são inferência. Onde a fonte tinha ambiguidade ou números que variam por versão, isso está assinalado explicitamente, em vez de arredondado para o número que o pedido original sugeria.

## 1. O que o setup já tem (governança)

Módulos de `packages/core/src/` que tocam em governança, com o estado confirmado em `CORE-MAPPING.md`:

| Módulo | O que faz | Estado | O que falta |
|---|---|---|---|
| `governance/DeliberationEngine.ts` | Scoring ponderado (impacto/incerteza/risco/reversibilidade/custo/dependências) que decide o nível de aprovação necessário — operational/tactical/strategic/constitutional | **REAL** | Nada — funciona como está |
| `governance/TrustManager.ts` | Certificação de competências por 6 níveis de confiança (LEVEL_0 a LEVEL_5), com limites de autonomia (`AutonomyBoundary`) por competência | INCOMPLETO | Persistência — todo o estado (`Map`) perde-se num restart |
| `governance/ArchitectureCouncil.ts` | Fluxo de propostas arquiteturais → revisão/auto-aprovação → registo de decisões (ADRs) | INCOMPLETO | Persistência das propostas/decisões |
| `security/SecurityManager.ts` | Autenticação, sessões, RBAC, MFA, detectores heurísticos (prompt injection, jailbreak) | **MOCK** | Tudo — `verifyPassword()` devolve sempre `true`, hash sem salt, `verifyMFA()` aceita código fixo `'123456'`. Não é uma base reaproveitável, é preciso construir de novo |
| `compliance/ComplianceManager.ts` | Consentimento LGPD/GDPR, pedidos de titular de dados, logs de auditoria | **MOCK** | Lógica real — `processDataRequest` devolve strings fixas sem apagar nada; `getStats()` tem `complianceScore: 80` hardcoded |
| `data/DataGovernance.ts` | Classificação de activos de dados, linhagem, score de qualidade | **MOCK** | `observeData()` é simulação explícita ("Em produção conectaria a sensores/APIs") — a parte de classificação/linhagem em si tem mais substância que os outros MOCK, mas a ingestão é vazia |
| `hitl/HitlManager.ts` | Pedidos de aprovação humana (pending/approved/rejected/expired) + checkpoints | INCOMPLETO | Persistência — 5 `Map`s, todo o estado de aprovação é volátil |

## 2. O que o AGT cobre

Componentes do **Microsoft Agent Governance Toolkit** (`microsoft/agent-governance-toolkit`, licença MIT, "Microsoft-signed public preview", cobre 10/10 do OWASP Agentic Top 10 2026) e o que substituiriam no setup:

| Componente AGT | O que faz | Substitui ou complementa |
|---|---|---|
| **Agent OS** (Policy Engine) | Motor de políticas declarativas (YAML, OPA Rego, ou Cedar); intercepta a acção antes de chegar ao modelo — classifica como `DESTRUCTIVE_DATA`/`DATA_EXFILTRATION`/`PRIVILEGE_ESCALATION` e bloqueia/reduz confiança. Benchmark real medido pelo próprio projecto: ~0,07ms p50 / ~0,42ms p99 para o stack completo (policy + trust + ring + auditoria Merkle) — não é uma latência universal de "<0,1ms", é a mediana; o p99 sobe a 0,42ms | **Substitui** o `DeliberationEngine` como motor de decisão de facto — mas o `DeliberationEngine` (REAL, já escrito) pode continuar a alimentar o *score* que decide o nível, com o Agent OS a aplicar a política final |
| **AgentMesh** (Identity) | Identidade zero-trust por DID (`did:mesh:...`), assinatura Ed25519, pontuação de confiança que decai com o tempo sem sinal positivo, patrocínio humano por agente | **Substitui** por completo o `security/SecurityManager.ts` (que é MOCK) — não vale a pena consertar o `SecurityManager` actual, é mais barato adoptar isto |
| **Agent Hypervisor** | Anéis de privilégio inspirados em CPU (Ring 0 a Ring 3), com limites de recursos por anel; agentes novos entram no Ring 3 e sobem por mérito (trust score). Logs em cadeia Merkle (hash chain) com verificação de integridade | **Complementa** — o `TrustManager` (INCOMPLETO, mas com lógica de 6 níveis já escrita) mapeia conceptualmente para isto; a ideia de "subir de nível por mérito" já existe no `TrustManager`, o Hypervisor dá a componente de isolamento/execução que o setup não tem nenhuma |
| **Agent SRE** | SLOs, orçamento de erro, kill switch, disjuntores para falhas em cascata | **Complementa** — nada equivalente existe hoje no setup |
| **Agent Compliance** | Mapeamento formal a normas (EU AI Act, SOC 2, HIPAA, OWASP Agentic Top 10) | **Substitui** o `ComplianceManager.ts` (MOCK) — o `ComplianceManager` actual não tem mapeamento nenhum, só simula fluxo LGPD/GDPR |
| **MCP Security Gateway** | Intercepta chamadas de ferramenta MCP; `MCPSecurityScanner` deteta *tool poisoning*, *rug pulls*, esquemas com instruções escondidas; `MCPGateway` faz *rate limiting*, sanitização e aprovação humana opcional por chamada | **Complementa** — nada equivalente existe hoje no setup; é directamente relevante para o `agent-network-mcp` |

**Nota sobre o número de pacotes:** o pedido original assumia "8 packages". A documentação actual do projecto fala em "nove pacotes" numa fonte (blog de terceiros, Abril 2026) e, mais recentemente, o próprio README do AGT diz que 5 pacotes antigos (`agent-os-kernel`, `agentmesh-primitives`, `agentmesh-runtime`, `agent-hypervisor`, `agentmesh-platform`) foram consolidados num único `agent-governance-toolkit-core`, com os nomes antigos a continuar instaláveis como *stubs* de redirecionamento. O número exacto de pacotes independentes depende da versão consultada — não fixar "8" como facto sem verificar a versão a instalar no momento da Sessão 1.

## 3. O que falta construir (a "cola")

O AGT cobre identidade, política e execução — não cobre a ligação entre múltiplos agentes a delegarem trabalho uns aos outros dentro desta rede, nem a sincronização de contexto entre eles. Isto é trabalho próprio, não coberto por nenhuma dependência externa verificada nesta tarefa:

| Componente | O que é | Esforço | Dependências |
|---|---|---|---|
| **Delegation Graph** | Schema + implementação que regista quem delegou o quê a quem, com que âmbito e até quando — para que uma cadeia de delegação tenha um tecto de confiança rastreável (um agente delegado não pode exceder as permissões de quem delegou). **Continua trabalho próprio** — confirmado por leitura directa da spec `AGENTMESH-TRUST-COORDINATION-1.0` (2026-09-17): não existe secção de "Delegation" nela, e a §17.1 (Transitive Trust) diz explicitamente *"If Agent A trusts Agent B and Agent B trusts Agent C, Agent A MUST NOT automatically trust Agent C"* — a confiança multi-salto é rejeitada por desenho, não é algo que falte implementar, é uma decisão de arquitectura do AgentMesh. **Reaproveitar, sim:** o `CapabilityGrant` da spec (§8.3) já dá o schema de concessão de um único salto (`granted_to`, `granted_by`, `capability`, `expires_at`, revogação individual/em massa) — usar isso como primitivo de base em vez de desenhar o grant do zero; a travessia da cadeia + tecto de confiança continuam por construir | Médio — o schema de um salto reduz-se ao adoptar `CapabilityGrant`; a validação da cadeia continua a ser o grosso do trabalho | AgentMesh `CapabilityGrant` (§8.3, primitivo de grant), TrustManager (níveis de confiança de cada nó) |
| **Action Receipts** | Recibo assinado e encadeado por hash para cada acção governada — prova imutável de que uma decisão foi tomada e por quem. O AGT já tem cadeia Merkle de auditoria (`AuditLog`/`MerkleAuditChain` no `agent-mesh`) — o trabalho aqui é adaptar esse mecanismo ao formato de recibo que este setup precisa, não construir hash-chaining do zero | Baixo-médio — a primitiva (Merkle) já existe no AGT, é adaptação, não invenção | AGT (`agent-mesh` audit chain) |
| **Context Sync** | Sincronização de contexto partilhado entre agentes de forma federada — para que dois agentes a colaborar na mesma tarefa vejam o mesmo estado sem depender de um único processo central | Alto — é o item com menos cobertura externa das três; nenhuma das dependências verificadas na secção 5 resolve isto directamente | Delegation Graph (para saber quem tem direito a que parte do contexto) |

## 4. Cronograma ajustado (8–12 sessões)

| Sessão | Entregável | Dependências |
|---|---|---|
| 1–2 | Schemas de `delegation-graph` e `action-receipt` definidos e revistos | Nenhuma — trabalho de desenho |
| 3–4 | Delegation Graph implementado (validação de cadeia, tecto de confiança) | Sessões 1–2; AgentMesh instalado (para identidade dos nós) |
| 5 | Action Receipts — adaptação da cadeia Merkle do AGT ao formato de recibo do setup | Sessão 1 (schema); AGT `agent-mesh` instalado |
| 6 | Context Sync — primeira versão | Sessão 3–4 (Delegation Graph, para escopo de acesso) |
| 7–8 | Integração do AGT no `agent-network-mcp` e no `plan_runner` | Sessões 3–6; decisão tomada sobre qual motor de política adoptar (Agent OS vs. `DeliberationEngine` próprio, ver secção 2) |
| 9–10 | Testes de conformidade — correr `agt verify` (comando de conformidade OWASP ASI 2026 do próprio AGT) e testes próprios do Delegation Graph/Action Receipts | Sessões 7–8 |
| 11–12 | Endurecimento + documentação | Sessões 9–10 |

## 5. Dependências externas (verificadas)

| Dependência | Licença | O que faz |
|---|---|---|
| **SPIFFE/SPIRE** | Apache-2.0 | Identidade de *workload* (não é específico de agentes de IA) — projecto CNCF graduado, base madura para identidade criptográfica de processos/serviços |
| **OpenA2A AIM** (`opena2a-org/agent-identity-management`) | Apache-2.0 | Camada de IAM para agentes de IA — identidade criptográfica, autorização por capacidade, trilhas de auditoria, *trust score* de 9 factores |
| **agentgateway** (`agentgateway.dev`, solo.io) | Apache-2.0 | *Data plane* — gateway único para tráfego MCP, A2A e LLM; conceitos-chave confirmados: `Bind` (porta), `Listener`, `Route`, `Backend` |
| **ContextForge** | — ver nota | Descoberta/discovery — **atenção: existem 2 projectos distintos com este nome**, ver nota abaixo |
| **Cedar / OPA** | Apache-2.0 | Motores de política declarativa usados pelo próprio AGT (Agent OS aceita política em Cedar ou Rego/OPA, além de YAML) |
| **Microsoft AGT** (`microsoft/agent-governance-toolkit`) | MIT | Ver secção 2 — número exacto de pacotes independentes varia por versão, não é um "8" fixo |

**Nota importante sobre "ContextForge":** a pesquisa desta tarefa encontrou **dois projectos open source distintos** com o mesmo nome:
1. `mcp-context-forge` (também espelhado como IBM/mcp-context-forge e outros forks) — gateway/registo/proxy MCP que federa ferramentas, agentes e APIs num único endpoint com *discovery* e *guardrails* centralizados. Este é o que melhor corresponde a "discovery" no pedido original.
2. `waterflane/ContextForge` — ferramenta completamente diferente, para construir pacotes de contexto delimitado para agentes de código (licença Apache-2.0, pré-alpha).
Antes de adoptar qualquer um, confirmar qual dos dois é o pretendido — não assumir que é o mesmo projecto só porque o nome bate.

## 6. O que NÃO fazer no MVP

- Memória federada completa
- Context Graph completo
- Multi-vendor real (Claude ↔ Gemini)
- Kill-switch federado global
- Compliance frameworks completos (EU AI Act, SOC 2, HIPAA, ISO 42001 — o AGT tem mapeamento para estes, mas adoptar o mapeamento inteiro de uma vez não é MVP)

## 7. Próximo passo imediato

**Semana 1:** clonar `microsoft/agent-governance-toolkit`, ler `ARCHITECTURE.md`, focar no Agent OS Engine + AgentMesh. Confirmar nesta leitura, antes de instalar, qual é a distribuição actual recomendada (`agent-governance-toolkit-core` consolidado, ou os pacotes antigos ainda suportados) — a estrutura de pacotes mudou de versão para versão.

**Semana 2:** clonar `agentgateway/agentgateway`, entender `Bind`/`Listener`/`Route`/`Backend`. Em paralelo, resolver a ambiguidade do "ContextForge" (secção 5) antes de decidir se entra no MVP.
