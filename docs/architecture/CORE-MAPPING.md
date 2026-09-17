# Core Mapping — `packages/core/src/`

Mapeamento de todos os módulos de `packages/core/src/`, produzido por leitura directa dos ficheiros (não por inferência a partir de nomes ou descrições). Objectivo: saber exactamente o que já funciona, o que funciona mas é volátil, e o que é só esqueleto, antes de planear qualquer trabalho em cima disto.

## 1. Resumo

**39 ficheiros `.ts`**, em 4 categorias:

| Categoria | Contagem | Definição |
|---|---|---|
| REAL | 5 | Faz o que promete e não depende de persistência para isso (cálculo puro, chamada a API externa, ou delega a um serviço injectado) |
| INCOMPLETO | 19 | Lógica funcional real, mas todo o estado vive num `Map`/array/objecto em memória do processo — perde-se num restart |
| MOCK | 14 | Tem comentário explícito de simulação/placeholder, ou uma implementação que finge fazer algo sem o fazer de facto |
| BARREL | 1 | `index.ts` — só re-exporta os outros módulos, zero lógica própria |

## 2. Tabela completa (39 ficheiros)

| Ficheiro | Classificação | Nota |
|---|---|---|
| `agents/AgentFactory.ts` | INCOMPLETO | Regista/filtra agentes num `Map` único |
| `agents/HorizontalAgents.ts` | MOCK | — |
| `compliance/ComplianceManager.ts` | MOCK | `processDataRequest` devolve strings fixas ("Dados removidos conforme solicitação") sem apagar nada; `getStats()` devolve `complianceScore: 80` hardcoded |
| `data/DataGovernance.ts` | MOCK | `observeData()` comentário explícito "Simula observação de dados... Em produção conectaria a sensores/APIs" |
| `development/RepositoryManager.ts` | MOCK | — |
| `domains/SpecialtyManager.ts` | MOCK | — |
| `economy/TokenEconomy.ts` | MOCK | — |
| `evolution/AccumulationCycle.ts` | INCOMPLETO | Ciclo de acumulação em `Map<string, AccumulationCycleState>` |
| `evolution/VersionManager.ts` | INCOMPLETO | Versionamento de artefactos em `Map`, sem histórico persistido |
| `governance/ArchitectureCouncil.ts` | INCOMPLETO | Propostas/decisões (ADRs) em `Map`; delegation por threshold funcional |
| `governance/CompletenessValidator.ts` | MOCK | — |
| `governance/Councils.ts` | INCOMPLETO | Orquestra os 3 conselhos, decisões em `Map` |
| `governance/DeliberationEngine.ts` | **REAL** | Scoring ponderado puro (impacto/incerteza/risco/reversibilidade/custo/dependências) — sem estado a guardar |
| `governance/DocumentationGovernance.ts` | INCOMPLETO | Versionamento de documentos + emendas constitucionais em `Map` |
| `governance/IngestionOrchestrator.ts` | MOCK | — |
| `governance/TrustManager.ts` | INCOMPLETO | Certificação de competências por 6 níveis de confiança, em `Map` |
| `governance/TrustOrchestrator.ts` | INCOMPLETO | Avaliações de confiança em `Map`, delega cálculo ao TrustManager |
| `hitl/HitlManager.ts` | INCOMPLETO | 5 `Map`s (pending/approved/rejected/expired/checkpoints) |
| `immunity/ImmunologicalMemory.ts` | INCOMPLETO | Eventos/padrões/anticorpos em 3 `Map`s |
| `index.ts` | BARREL | Só `export * from` — sem lógica própria |
| `infrastructure/InfrastructureManager.ts` | INCOMPLETO | Catálogo de componentes/planos em `Map`; ver achado crítico sobre `implementTokenEconomy` |
| `knowledge/CognitiveRepository.ts` | INCOMPLETO | Base de conhecimento reutilizável em `Map` |
| `llm/LLMService.ts` | **REAL** | Chamada `fetch` genuína à API da OpenAI, tratamento de erro por código HTTP |
| `observability/MetricsDashboard.ts` | INCOMPLETO | Painéis/métricas em `Map` |
| `observability/SelfAwareness.ts` | INCOMPLETO | Estado organizacional em objecto único + array de histórico, em memória |
| `operations/WorkerSupervisor.ts` | MOCK | — |
| `opportunity/OpportunityRadar.ts` | MOCK | — |
| `orchestrator/DeliberationOrchestrator.ts` | INCOMPLETO | Resultados de deliberação em `Map`, usa o `DeliberationEngine` (REAL) por baixo |
| `orchestrator/Executor.ts` | **REAL** | Não guarda estado próprio; delega a `MemoryManager` (pacote externo, não auditado aqui) |
| `orchestrator/Orchestrator.ts` | MOCK | — |
| `orchestrator/Planner.ts` | **REAL** | Chama `LLMService.chat()` de facto, com fallback determinístico se o parse falhar |
| `orchestrator/ReflectionEngine.ts` | INCOMPLETO | Reflexões pós-execução em `Map` |
| `orchestrator/Router.ts` | **REAL** | Routing por palavra-chave, autocontido |
| `products/ProductManager.ts` | INCOMPLETO | Produtos cognitivos em `Map` |
| `search/AIVisibilityEngine.ts` | MOCK | — |
| `security/SecurityManager.ts` | MOCK | Ver achados críticos — autenticação não funcional |
| `simulation/OrganizationalSimulator.ts` | MOCK | — |
| `ux/AdaptiveInterface.ts` | INCOMPLETO | Perfis de utilizador + configs em `Map` |
| `ux/AttentionEconomy.ts` | INCOMPLETO | Orçamentos de atenção + pedidos em `Map` |

## 3. O que é reutilizável tal como está (5 REAL)

Estes 5 não precisam de trabalho de persistência — o que fazem não depende de guardar estado entre execuções:

- **`governance/DeliberationEngine.ts`** — motor de scoring que decide o nível de aprovação necessário (operational/tactical/strategic/constitutional) a partir de critérios ponderados. Função pura, zero dependências de outros módulos.
- **`llm/LLMService.ts`** — cliente real da API da OpenAI (chat e chat com tools), com tratamento de erro por código HTTP (401/429/5xx) e mensagens de diagnóstico específicas.
- **`orchestrator/Router.ts`** — classificador de domínio por palavra-chave, autocontido.
- **`orchestrator/Planner.ts`** — gera um plano de execução chamando o `LLMService` de facto, com fallback determinístico se o parse da resposta falhar.
- **`orchestrator/Executor.ts`** — orquestra a execução de um plano delegando a serviços injectados (`MemoryManager`, `LLMService`, `HitlManager`) em vez de guardar estado próprio.

## 4. O que precisa de persistência (19 INCOMPLETO)

Todos partilham o mesmo padrão: lógica de negócio funcional, `EventEmitter` para eventos, mas armazenamento num `Map`/array/objecto que vive só na memória do processo — reinicia e perde tudo.

`AgentFactory`, `AccumulationCycle`, `VersionManager`, `ArchitectureCouncil`, `Councils`, `DocumentationGovernance`, `TrustManager`, `TrustOrchestrator`, `HitlManager`, `ImmunologicalMemory`, `InfrastructureManager`, `CognitiveRepository`, `MetricsDashboard`, `SelfAwareness`, `DeliberationOrchestrator`, `ReflectionEngine`, `ProductManager`, `AdaptiveInterface`, `AttentionEconomy`.

O trabalho aqui é sempre da mesma natureza: trocar o `Map` interno por uma camada de persistência real (base de dados ou ficheiro), sem mudar a lógica de negócio já escrita.

## 5. O que precisa de implementação (14 MOCK)

Não é só trocar armazenamento — falta lógica de facto:

`agents/HorizontalAgents.ts`, `compliance/ComplianceManager.ts`, `data/DataGovernance.ts`, `development/RepositoryManager.ts`, `domains/SpecialtyManager.ts`, `economy/TokenEconomy.ts`, `governance/CompletenessValidator.ts`, `governance/IngestionOrchestrator.ts`, `operations/WorkerSupervisor.ts`, `opportunity/OpportunityRadar.ts`, `orchestrator/Orchestrator.ts`, `search/AIVisibilityEngine.ts`, `security/SecurityManager.ts`, `simulation/OrganizationalSimulator.ts`.

Dois destes já têm o comportamento simulado documentado com detalhe (ver secção 6): `ComplianceManager` e `DataGovernance`.

## 6. Achados críticos

- **`security/SecurityManager.ts` — `verifyPassword()` devolve sempre `true`.** Comentário explícito no código: `// Em produção, verificar contra hash armazenado`. Qualquer password passa.
- **`security/SecurityManager.ts` — hash sem salt.** `hashPassword()` usa `SHA-256` puro (`crypto.createHash('sha256')`), sem salt — vulnerável a rainbow tables. O hash gerado nem chega a ser guardado no objecto `User`.
- **`security/SecurityManager.ts` — `verifyMFA()` aceita o código fixo `'123456'`.** Não há verificação TOTP real.
- **`infrastructure/InfrastructureManager.ts` — `implementTokenEconomy()` usa `Math.random()` para fabricar resultado.** Tanto a estratégia escolhida como o valor de "poupança" (`savings`) são gerados aleatoriamente, não medidos — isto é uma simulação sem o comentário habitual a admiti-lo.
- **Parâmetros de construtor recebidos e nunca usados:**
  - `compliance/ComplianceManager.ts` recebe `SecurityManager` e `CognitiveRepository` no construtor, mas nenhum dos dois é referenciado no corpo da classe (prefixados com `_`).
  - `data/DataGovernance.ts` recebe `ImmunologicalMemory` no construtor, também nunca usada.
  - Indício de acoplamento planeado entre módulos que ainda não foi ligado.

## 7. Implicação para o cronograma

O que isto **encurta**, porque já está feito e não precisa de ser reconstruído do zero:

- **Motor de decisão/escalonamento** (`DeliberationEngine`) já existe e está correcto — a lógica de "isto precisa de aprovação humana ou não" não precisa de ser desenhada de novo.
- **Integração com LLM** (`LLMService`) já é uma chamada real e funcional à OpenAI, com tratamento de erro — não é preciso construir o cliente HTTP.
- **Orquestração de execução de plano** (`Executor`, `Planner`, `Router`) já tem o esqueleto de coordenação certo, incluindo o padrão de delegar a serviços injectados em vez de guardar estado.
- Os 19 INCOMPLETO representam trabalho de **persistência**, não de desenho — a lógica de negócio (certificação de confiança, versionamento, governança documental, HITL, etc.) já está escrita e só precisa de uma camada de armazenamento por baixo.

O que isto **não encurta**, e continua a exigir trabalho desde o início:

- Qualquer coisa que dependa de `security/SecurityManager.ts` funcionar de verdade — autenticação real (hash com salt, verificação de password, MFA real) tem de ser construída, o ficheiro actual não serve de base seguramente reutilizável, mesmo estruturalmente.
- Os 14 MOCK não têm lógica de negócio para aproveitar — o trabalho aqui é dimensionalmente diferente do dos 19 INCOMPLETO (é "escrever a lógica", não "trocar o armazenamento").
- O acoplamento entre `ComplianceManager`/`DataGovernance`/`SecurityManager` está desenhado nas assinaturas dos construtores mas não implementado — decidir e implementar essa ligação é trabalho novo, não é óbvio a partir do código actual qual era a intenção original.
