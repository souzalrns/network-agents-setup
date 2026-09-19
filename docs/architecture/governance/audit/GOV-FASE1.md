# Auditoria de Governança — Fase 1: ADR-001 como hipótese + estado real do núcleo

Primeira fase da auditoria arquitectural de governança, com a mesma disciplina da auditoria de memória: `ADR-001` tratado como **hipótese a validar**, não como arquitectura aprovada. Toda a evidência abaixo vem de leitura directa de código — incluindo ficheiros que **nunca tinham sido cobertos** pelo `CORE-MAPPING.md` (esse só olhou para `packages/core/`; esta auditoria também cobre `packages/mcp/` e `packages/shared/`, onde apareceram 2 achados que mudam conclusões anteriores).

## 1. Auditoria do `ADR-001` (secção 3 do pedido)

| Decisão do ADR | Premissa | Evidência actual | Validada? | Risco |
|---|---|---|---|---|
| Governance Runtime como camada intermédia entre pedido e execução | Não existe hoje nenhuma camada assim — nem em `packages/core/`, nem em `packages/mcp/` | Confirmado: `ToolExecutor.executeTool()` (`packages/mcp/`) executa a tool directamente após validar só os parâmetros obrigatórios — zero verificação de capacidade/scope antes de executar | **NÃO VALIDADA como já existente** — é lacuna real, não descrição do que já há | Baixo — é honesto que falta, o ADR nunca disse que já existia |
| Pipeline de 10 passos (Identify→...→Context Sync) | Cada passo mapeia a um componente externo ou a construir | Nenhum dos 10 passos existe implementado hoje, nem parcialmente, em `packages/mcp/` | NÃO VALIDADA (nunca foi pedido para estar implementado nesta fase — é desenho) | Médio — o pipeline nomeia projectos externos (AGT, agentgateway) como se fossem peças decididas; a Fase 2/3 vai re-testar se são as certas |
| `Scope Contract` inspirado no `CapabilityGrant` do AGT §8.3 | AGT tem um primitivo de grant de 1 salto reutilizável | **Reconfirmado nesta fase**: já tinha sido verificado directamente na spec `AGENTMESH-TRUST-COORDINATION-1.0` antes do ADR-001 ser escrito | **VALIDADA** — é uma das poucas premissas do ADR já confirmada em spec real, não em README | Baixo |
| Modelo de Identity = Ed25519+DID do AgentMesh; SPIFFE seria dependência separada | AgentMesh não é SPIFFE-compliant | **Reconfirmado** — já verificado por leitura directa da spec | **VALIDADA** | Baixo |
| Delegation Graph = trabalho próprio, AGT não resolve por desenho (não-transitividade §17.1) | AGT rejeita confiança transitiva automática | **Reconfirmado** | **VALIDADA** | Baixo |
| `packages/core/` tem 7 módulos de governança relevantes (1 REAL, 3 INCOMPLETO, 3 MOCK) | Vem do `CORE-MAPPING.md` | Confirmado outra vez nesta fase (ver secção 2) | VALIDADA | — |
| **Pressuposto implícito, nunca declarado no ADR: que o `packages/core/` é o ÚNICO lugar onde procurar "o que já existe"** | — | **REFUTADA nesta fase** — existe uma segunda implementação de MCP inteira em `packages/mcp/` (`ToolRegistry`, `ToolExecutor`, `MCPServer`), nunca mencionada no ADR nem no `CORE-MAPPING.md` | **NÃO VALIDADA** | **Alto** — decisões do ADR sobre "Dispatch"/"MCP" foram tomadas sem conhecer esta peça |
| **Pressuposto implícito: os 7 componentes nomeados (AGT, agentgateway, ContextForge, Cedar/OPA, OpenA2A AIM) são as peças certas para as camadas do pipeline** | Vem de nomes de projecto, não de responsabilidades | Ainda **não avaliada nesta fase** (Fases 2-3) — mas o próprio facto de o ADR ter sido montado assim é o erro metodológico identificado por ti/pelo "deep" antes de começar | **NÃO VALIDADA, é o objecto central das próximas fases** | Alto |

## 2. O que já existe — capacidade → implementação → localização → limitação → importância

### 2a. `packages/core/` (já conhecido do `CORE-MAPPING.md`, reconfirmado aqui com a lente de governança)

| Capacidade | Implementação | Localização | Limitação | Importância |
|---|---|---|---|---|
| Policy engine / escalonamento | Scoring ponderado real, sem dependências | `governance/DeliberationEngine.ts` (REAL) | Nenhuma conhecida — é o único módulo limpo desta lista | Alta |
| Trust / certificação de competências | 6 níveis, `AutonomyBoundary`, `checkAutonomy()` | `governance/TrustManager.ts` (INCOMPLETO) | Estado em `Map`, some com restart | Alta |
| Delegation | **Ausente enquanto conceito de cadeia** — `TrustManager` certifica competência, não regista "quem delegou a quem" | — | — | Alta (é o gap central do ADR) |
| Authorization (decisão formal allow/deny) | `ArchitectureCouncil.ts` decide sobre propostas de arquitectura, não sobre acções de agente em runtime | `governance/ArchitectureCouncil.ts` (INCOMPLETO) | Não é o mesmo tipo de "autorização" que uma tool-call precisa | Média |
| Identity / autenticação | `SecurityManager.ts`: registo, login, sessões | `security/SecurityManager.ts` (**MOCK**) | `verifyPassword()` sempre `true`; hash sem salt (já corrigido no CodeQL #5, mas a lógica de sessão/login continua não-funcional para o resto) | Alta |
| RBAC | Sim — hierarquia `admin > user > viewer > agent` | `security/SecurityManager.ts` | É RBAC simples, não ABAC — sem atributos contextuais (projecto, ambiente) | Média |
| ABAC | **Ausente** | — | — | Baixa hoje |
| Compliance / consentimento | `ComplianceManager.ts` — LGPD/GDPR, consent record | `compliance/ComplianceManager.ts` (**MOCK**) | `processDataRequest` devolve string fixa, não apaga nada | Média |
| Data governance / provenance de dados | Classificação, linhagem, qualidade | `data/DataGovernance.ts` (**MOCK** na ingestão, mais substância na classificação) | `observeData()` é simulação admitida no próprio código | Média |
| HITL | Pending/approved/rejected/expired + checkpoints | `hitl/HitlManager.ts` (INCOMPLETO) | Estado em `Map` | Alta — é usado de facto (ver `mcp/plan_runner/hitl.py`, Python, que É funcional) |
| Kill switch / circuit breaker | **Ausente**, confirmado por busca no código inteiro | — | — | Média (mencionado no `ROADMAP-GOVERNANCE.md` como capacidade do "Agent SRE" do AGT, nunca construído aqui) |
| Rate limiting | **Ausente em `packages/core/`** — existe sim em Python, no `mcp/plan_runner/mcp_plan_runner/policy.py` (60 req/60s) | `mcp/plan_runner/` (Python, fora do escopo TS) | Duplicação de responsabilidade entre stacks, não entre ferramentas externas | Média |
| Rollback / replay | **Ausente** | — | — | Baixa hoje |
| SLO | **Ausente** | — | — | Baixa hoje |
| Audit log / provenance | `events.jsonl` (Python), `audit.jsonl` do MCP local (Python) | `runner/plan_runner/events.py`, `mcp/plan_runner/` | Nenhum equivalente em TypeScript — `packages/mcp/` não regista nada | Alta |
| Action/Decision receipt | **Ausente enquanto formato estruturado** — o `ADR-001` desenha isto, nada o implementa | — | — | Alta |
| Revocation | Mencionado como estado (`status: 'revoked'`) em `Competence`, mas **sem mecanismo activo** de revogar em runtime | `governance/TrustManager.ts` | É um campo de estado, não uma acção implementada | Média |
| Federation / trust entre agentes | **Ausente** | — | — | Média (roadmap, não agora) |
| Workload identity / identidade criptográfica | **Ausente** | — | — | Alta se AGT/AgentMesh entrar |

### 2b. `packages/mcp/` — achado novo desta fase, nunca auditado antes

| Capacidade | Implementação | Localização | Limitação | Importância |
|---|---|---|---|---|
| Tool registry | `Map<string, MCPTool>`, registo/remoção/listagem | `tools/ToolRegistry.ts` | Sem persistência, sem versão, sem proveniência de quem registou a tool | Média |
| Tool execution / dispatch | `ToolExecutor.executeTool()` | `tools/ToolExecutor.ts` | Só valida presença de parâmetros obrigatórios — **zero verificação de capacidade, scope, ou identidade do chamador antes de executar** | **Alta — é uma lacuna de segurança real, não só arquitectural** |
| MCP server (HTTP) | `MCPServer.createHttpHandler()`, Express | `server/MCPServer.ts` | **Sem autenticação nenhuma no handler HTTP** — qualquer pedido `getTools`/`executeTool` é aceite | **Alta** |
| Tool governance / authorization | **Ausente por completo** nesta implementação | — | Contrasta com `mcp/plan_runner/policy.py` (Python), que TEM auth, rate limit e audit — duas implementações MCP no mesmo repo, maturidades muito diferentes | **Alta — precisa de decisão: qual das duas é a real, ou fundir?** |

> **RESOLVIDO em 2026-09-19 — `ToolExecutor.executeTool()` passa a chamar `authorize()`+`rateLimit()`+`audit()` (novo `packages/mcp/src/tools/ToolPolicy.ts`) antes de executar qualquer tool. Não é um porte 1:1 de `policy.py` — as tools cobertas são diferentes (`read_file`/`write_file`/`list_directory`/`http_request`/`scrape_webpage`/`query_database`, não as do `plan_runner`), mas o padrão (perfis, scopes, rate-limit, audit JSONL) é o mesmo. Perfil por omissão é `strict` (fail-closed), diferente do `moderate` do Python. `MCPServer.ts` (autenticação HTTP) continua por fazer — ver C2/A8. Ver `tools-mcp-audit/AUDIT-TOOLS-MCP.md` secção 4 e `EXECUTION-PROMPTS.md` C1.**

### 2c. `packages/shared/src/types/governance.ts` — achado de duplicação interna

`TrustMetrics`, `AutonomyBoundary`, `Competence` estão definidos **duas vezes**, de forma independente e idêntica: uma vez em `packages/shared/src/types/governance.ts`, outra vez inline em `governance/TrustManager.ts`. Confirmado por busca de código: **nada no repo importa a versão de `packages/shared/`** — só o próprio `packages/shared/src/index.ts` a re-exporta, sem consumidor. É código morto/duplicado, não uma segunda fonte de verdade activa — mas é exactamente o tipo de sobreposição que a Fase 3/4 vai ter de vigiar também nos componentes externos.

## 3. Decomposição em camadas — quem cobre o quê, hoje

| Camada | Quem cobre, hoje | Estado |
|---|---|---|
| Identity | `SecurityManager.ts` (TS, MOCK) + nada em `packages/mcp/` | MOCK / AUSENTE |
| Authentication | `SecurityManager.ts` (MOCK) | MOCK |
| Discovery | `ToolRegistry.ts` (lista tools em memória) | PARCIAL |
| Trust | `TrustManager.ts` (INCOMPLETO) | PARCIAL |
| Policy | `DeliberationEngine.ts` (REAL, mas é scoring de risco, não policy declarativa tipo Cedar/OPA) | PARCIAL |
| Authorization | **Ausente em runtime de tool-call** — `ToolExecutor` não pergunta a ninguém "pode?" | AUSENTE |
| Delegation | **Ausente** | AUSENTE |
| Dispatch | `ToolExecutor.executeTool()` | PARCIAL (existe, mas sem governança à volta) |
| Execution | `ToolExecutor` (TS) / `execute_stub`+`execute_external_request` (Python, `plan_runner`) | FORTE (é o que já funciona bem, motor) |
| Observability | **Ausente em TS**; Python tem `events.jsonl` | PARCIAL, só do lado Python |
| Audit | Idem — só Python (`events.jsonl`, `audit.jsonl`) | PARCIAL |
| Revocation | Campo de estado em `TrustManager`, sem acção real | AUSENTE (enquanto mecanismo) |

## 4. O que isto muda, concretamente

1. **O `ADR-001` foi escrito sem saber que `packages/mcp/` existia.** Qualquer decisão sobre "Dispatch"/"MCP" no pipeline de 10 passos precisa de ser revista à luz desta peça — não é hipotética, já está no repo, e não tem nenhuma governança à volta.
2. **Há 2 implementações MCP no mesmo repo com maturidades opostas** (`mcp/plan_runner/` em Python, com auth+rate-limit+audit; `packages/mcp/` em TypeScript, sem nada disto). Isto é uma decisão que a Fase 4 tem de resolver explicitamente — não estava no radar de nenhum documento anterior.
3. **RBAC existe, ABAC não** — relevante directamente para a pergunta "Cedar substitui o quê" da Fase 3 (Cedar faz ambos).
4. **Rate limiting e audit já existem — mas só do lado Python**, não do lado TypeScript. Antes de adoptar `agentgateway`/AGT para isto, vale considerar só portar o que já existe em Python para o TS, sem dependência nova nenhuma.

## 5. Próxima fase

Fase 2 — Microsoft AGT (re-auditado alegação a alegação: Agent OS, AgentMesh, Runtime, SRE, Compliance, MCP Security Gateway, cada um separado) + agentgateway (standalone vs. exige Kubernetes/Envoy).
