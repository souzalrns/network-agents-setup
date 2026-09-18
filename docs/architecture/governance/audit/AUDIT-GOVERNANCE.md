# AUDIT-GOVERNANCE.md — Auditoria arquitectural de governança do plan_runner

## 1. Executive Summary

**A pergunta era: os 7 componentes do `ADR-001` são as peças certas, ou o ADR foi montado a partir de nomes de projecto em vez de responsabilidades? A resposta, com código real por trás de cada linha: parcialmente as peças certas, por razões diferentes das que o ADR original deu — e uma delas já não devia ser "construir do zero".**

1. **A maior revisão desta auditoria: o Delegation Graph não é "trabalho próprio".** O `ADR-001` concluiu isso com base numa spec do AgentMesh datada de Julho de 2026. O pacote real publicado hoje (`agentmesh-platform` v3.7.0, 167 ficheiros Python, verificado por download directo) já tem `ScopeChain`/`DelegationLink` — cadeia de delegação multi-salto, com hash encadeado, estreitamento de capacidade verificado, e limite de profundidade. **Veredicto revisto: ADAPTAR, não CONSTRUIR.**

2. **`packages/mcp/` (TypeScript) é uma peça que o `ADR-001` nunca soube que existia** — um `ToolExecutor` que executa qualquer tool sem verificar capacidade, scope ou identidade, e um `MCPServer` cujo handler HTTP não tem autenticação nenhuma. Isto é mais urgente do que qualquer decisão sobre ferramentas externas — é uma lacuna de segurança real, hoje, no código já existente.

3. **Duas correcções feitas a mim próprio a meio da auditoria, não escondidas:** o `AgentMesh` não tem SPIFFE real (tem o modelo de dados; a integração com SPIRE está simulada, "in production this would..." — o mesmo padrão MOCK já visto em `SecurityManager.ts`). E o `mcphound`, já citado no `SECURITY.md` como "confirmado, bem documentado", tem 1 estrela e está parado há mais de 6 meses.

4. **Nenhum dos componentes candidatos é zero-infra.** AgentMesh precisa de servidores próprios a correr (`trust_engine.py`, FastAPI); ContextForge exige Redis obrigatoriamente; agentgateway é standalone só na sua função de proxy, não resolve identidade/policy sozinho. A "arquitectura mais simples possível" tem de aceitar isto ou ficar sem estas capacidades.

5. **Veredicto final, sem ranking de "melhor ferramenta":** a combinação mínima que cobre as lacunas reais (ver secção 8) é **AgentMesh (ADAPTAR, só os módulos de identidade/delegação, sem o servidor completo) + Cedar via o `policy-engine` do próprio AGT (ADOPTAR) + fiação própria em `packages/mcp/` para dar à governança já existente em Python (`mcp/plan_runner/policy.py`) um equivalente em TypeScript (CONSTRUIR, mas pequeno — é portar um padrão já testado, não inventar um novo)**. ContextForge, agentgateway, SPIFFE/SPIRE standalone e OpenA2A AIM ficam **OPCIONAL/NÃO ADOPTAR AGORA** — resolvem problemas de escala (multi-cluster, federação entre organizações) que o `plan_runner` não tem hoje.

## 2. Metodologia

Mesma disciplina das Fases 1-3: código > testes > configuração real > releases > documentação oficial > specs > issues > changelog > advisories > OSV.dev/CVE > actividade do repositório. README nunca foi tratado como prova suficiente sozinho. Todas as afirmações de "existe X" foram verificadas por download/leitura directa do pacote real, não por confiança na descrição.

## 3. Estado actual do `plan_runner` (consolidado das Fases 1)

Ver `GOV-FASE1.md` na íntegra. Resumo: `packages/core/` tem 1 módulo REAL (`DeliberationEngine`), o resto INCOMPLETO/MOCK; `packages/mcp/` (nunca antes auditado) não tem nenhuma governança; `mcp/plan_runner/` (Python) já tem auth+rate-limit+audit reais, mas só nesse stack.

## 4. Auditoria do `ADR-001`

Ver `GOV-FASE1.md` secção 1 — tabela completa. As premissas sobre identidade (Ed25519+DID) e não-transitividade (§17.1) mantêm-se validadas; a premissa sobre Delegation Graph foi revista (secção 1 acima); o pressuposto implícito de que `packages/core/` era o único lugar a mapear foi refutado.

## 5. Microsoft AGT — resumo das 6 alegações (detalhe em `GOV-FASE2.md`)

| Alegação | Veredicto de existência |
|---|---|
| Agent OS | Real, mas sob o nome `agent-os-kernel` (PyPI), não no path óbvio |
| AgentMesh | Real e substancial (167 ficheiros), com ressalva sobre SPIFFE (secção 6.4) |
| Agent Runtime | Quase vazio — os 4 anéis reais estão em `agent-hypervisor`, não aqui |
| Agent SRE | Real e rico (SLO, chaos, cascade, replay, k8s) |
| Agent Compliance | Estrutura real (`src`+`tests`), conteúdo interno não aprofundado — NÃO VERIFICADO em profundidade |
| MCP Security Gateway (`agent-mcp-governance`) | **Deprecado oficialmente**, substituído por `agent-governance-toolkit-protocols` |

## 6. agentgateway, ContextForge, Cedar, OPA, SPIFFE/SPIRE, mcphound, OpenA2A AIM

Ver `GOV-FASE2.md` (agentgateway) e `GOV-FASE3.md` (os restantes). Resumo dos números reais:

| Tecnologia | Estrelas reais | Licença | Infra |
|---|---|---|---|
| AGT (agentmesh-platform) | — (monorepo, 6.285⭐ no todo) | MIT | Servidor próprio (`trust_engine.py`) |
| agentgateway | 4.914 | Apache-2.0 | Nenhuma (standalone confirmado) |
| ContextForge (IBM) | 4.492 | Apache-2.0 | Redis obrigatório |
| Cedar | 1.738 | Apache-2.0 | Nenhuma (biblioteca) |
| OPA | 12.248 | Apache-2.0 | Nenhuma (biblioteca/binário) |
| SPIFFE/SPIRE | 2.542 (SPIRE) | Apache-2.0 | Servidor SPIRE dedicado |
| mcphound | 1 | MIT | Nenhuma, mas 6+ meses parado |
| OpenA2A AIM | 66 | Apache-2.0 | NÃO VERIFICADO em profundidade |

## 7. Licenças, maturidade, CVEs

Todas as licenças acima são permissivas (MIT/Apache-2.0) — nenhum risco de licença encontrado nesta auditoria (ao contrário da auditoria de memória, onde `Memori` teve `NOASSERTION`). Nenhuma CVE nova encontrada para estes componentes especificamente nesta fase (a CVE do Graphiti já tinha sido encontrada na auditoria de memória, não é um componente de governança). Maturidade: MADURO (OPA, Cedar, SPIRE, ContextForge, agentgateway) vs. EM EVOLUÇÃO (AGT — push diário, API ainda "Public Preview" para AgentMesh) vs. EXPERIMENTAL/PROTÓTIPO-ABANDONADO (mcphound).

## 8. Matriz de capacidades (30 critérios × tecnologias principais)

| Capacidade | plan_runner (hoje) | AGT | ContextForge | Cedar | OPA | SPIFFE/SPIRE |
|---|---|---|---|---|---|---|
| Identity | PARCIAL (MOCK) | FORTE | AUSENTE | AUSENTE | AUSENTE | FORTE |
| Authentication | PARCIAL (MOCK) | FORTE | FORTE | AUSENTE | AUSENTE | FORTE |
| Authorization | AUSENTE (`packages/mcp/`) | FORTE | PARCIAL | FORTE | FORTE | AUSENTE |
| RBAC | PARCIAL (`SecurityManager`) | FORTE | FORTE | FORTE | FORTE | AUSENTE |
| ABAC | AUSENTE | FORTE (via Cedar/OPA) | PARCIAL | FORTE | FORTE | AUSENTE |
| Policy engine | PARCIAL (`DeliberationEngine`, não declarativo) | FORTE (Rust, aceita Cedar/OPA) | PARCIAL | NATIVO | NATIVO | AUSENTE |
| Delegation | AUSENTE | **FORTE** (`ScopeChain`, corrigido nesta auditoria) | AUSENTE | AUSENTE | AUSENTE | AUSENTE |
| Trust | PARCIAL (`TrustManager`) | FORTE | AUSENTE | AUSENTE | AUSENTE | PARCIAL |
| Discovery | PARCIAL (`ToolRegistry`) | FORTE (`agent-discovery`) | FORTE (é a proposta central) | AUSENTE | AUSENTE | AUSENTE |
| Registry | PARCIAL | FORTE | FORTE | AUSENTE | AUSENTE | AUSENTE |
| MCP | PARCIAL (2 implementações díspares) | FORTE (`agent-governance-toolkit-protocols`) | FORTE (é MCP-nativo) | AUSENTE | AUSENTE | AUSENTE |
| A2A | AUSENTE | NÃO VERIFICADO em profundidade | FORTE | AUSENTE | AUSENTE | AUSENTE |
| Tool governance | AUSENTE | FORTE | FORTE | Provider | Provider | AUSENTE |
| Runtime enforcement | AUSENTE | FORTE (`agent-hypervisor/rings`) | PARCIAL | N/A (decide, não aplica) | N/A | AUSENTE |
| Secrets | PARCIAL (`.env`) | NÃO VERIFICADO | FORTE (exige segredos reais) | AUSENTE | AUSENTE | FORTE (SVID = credencial) |
| Workload identity | AUSENTE | PARCIAL (modelo, não integração real) | AUSENTE | AUSENTE | AUSENTE | **FORTE** |
| Audit | PARCIAL (só Python) | FORTE | FORTE | PARCIAL (decision logs via integração) | FORTE (decision logs nativos) | PARCIAL |
| Provenance | PARCIAL (`events.jsonl`) | FORTE | PARCIAL | AUSENTE | AUSENTE | AUSENTE |
| Receipts | AUSENTE (desenhado no ADR, não implementado) | PARCIAL (hash-chain do `DelegationLink` é próximo) | AUSENTE | AUSENTE | AUSENTE | AUSENTE |
| Revocation | PARCIAL (campo de estado, sem acção) | **FORTE** (`RevocationEntry` real) | AUSENTE | AUSENTE | AUSENTE | FORTE (rotação de SVID) |
| Kill switch | AUSENTE | FORTE (`agent-sre`) | AUSENTE | N/A | N/A | AUSENTE |
| Observability | PARCIAL (só Python) | FORTE (`agent-sre/tracing`) | FORTE (OpenTelemetry nativo) | AUSENTE | PARCIAL | AUSENTE |
| SLO | AUSENTE | FORTE (`agent-sre/slo`) | AUSENTE | N/A | N/A | AUSENTE |
| Federation | AUSENTE | PARCIAL (roadmap) | FORTE (multi-cluster) | AUSENTE | AUSENTE | FORTE (federation entre trust domains) |
| Local-first | FORTE (motor Python) | AUSENTE (servidores próprios) | AUSENTE (Redis obrigatório) | FORTE | FORTE | AUSENTE |
| Portability | FORTE | PARCIAL (multi-linguagem, mas pesado) | PARCIAL | FORTE | FORTE | PARCIAL |
| Vendor neutrality | FORTE | PARCIAL (Entra ID opcional, mas presente) | FORTE | FORTE | FORTE | FORTE |

## 9. Matriz de sobreposição

| Capacidade | plan_runner | AGT | ContextForge | Cedar/OPA | SPIFFE/SPIRE |
|---|---|---|---|---|---|
| Discovery/Registry | Parcial | Forte | Forte | — | — |
| Policy/Authorization | Fraco | Forte (aceita Cedar/OPA) | Parcial | Forte | — |
| Identity | Fraco | Forte | — | — | Forte |
| Delegation | Ausente | Forte | — | — | — |

**Duplicação directa identificada:** AGT vs. ContextForge sobrepõem-se em Discovery/Registry/MCP — **não fazem sentido os dois juntos** para o mesmo propósito. AGT vs. SPIFFE/SPIRE sobrepõem-se em Identity **só na superfície** — a implementação real do AGT ainda não faz a parte pesada (integração SPIRE), pelo que não são redundantes hoje, só o seriam se o AGT terminasse essa integração.

**Complementaridade real:** Cedar/OPA são *providers* de política, não substituem o AGT nem o ContextForge — encaixam dentro de qualquer um dos dois.

**Complexidade prematura identificada:** adoptar AGT completo (identidade+mesh+SRE+hypervisor+compliance) e ContextForge (gateway+discovery) e SPIFFE/SPIRE standalone ao mesmo tempo seria exactamente a sobreengenharia que o pedido original avisou contra — 3 sistemas de identidade/discovery concorrentes para um `plan_runner` que hoje corre um motor sequencial com ~5 templates de plano.

## 10. Arquitectura recomendada — testando a hipótese alternativa

A hipótese de 3 Providers (Identity/Policy/Discovery) proposta como alternativa ao desenho original do `ADR-001` **sobrevive à auditoria, com um ajuste**: Delegation não é uma sub-parte de "Policy", é a sua própria responsabilidade, porque o AgentMesh a trata como módulo próprio (`identity/delegation.py`), não como regra de política.

```
                    PLAN_RUNNER CORE
                    (Execution Context, HITL, Action Receipt — próprios, ver secção 12)
                           │
        ┌──────────────────┼──────────────────┬─────────────────┐
        ▼                  ▼                  ▼                 ▼
   IDENTITY            POLICY            DELEGATION         DISCOVERY
   PROVIDER            PROVIDER           PROVIDER           PROVIDER
        │                  │                  │                 │
  AgentMesh (só      Cedar OU OPA        AgentMesh          ToolRegistry
  identity/*,        (via policy-engine   (ScopeChain,       próprio, ADAPTADO
  sem servidor        do proprio AGT)      já real)           com verificação
  completo)                                                    de capacidade
        │                  │                  │                 │
        └──────────────────┴──────────────────┴─────────────────┘
                           ▼
                     DISPATCH LAYER
                  (packages/mcp/, CONSTRUIR
                   pequeno — portar o padrão
                   ja testado de mcp/plan_runner/
                   policy.py para TypeScript)
```

**Nota honesta:** isto é uma hipótese testada pela evidência das Fases 1-3, não uma certeza — a Fase de implementação real (fora do âmbito desta auditoria) pode revelar fricções não previstas aqui.

## 11. Donos de responsabilidade

| Responsabilidade | Dono recomendado |
|---|---|
| Identity | AgentMesh (módulos `identity/*`, sem o servidor `trust_engine.py` completo) |
| Policy/Authorization | Cedar ou OPA, via `policy-engine` do AGT |
| Delegation | AgentMesh (`ScopeChain`/`DelegationLink`) |
| Discovery/Registry | `ToolRegistry` próprio (já existe em `packages/mcp/`), adaptado com verificação de capacidade |
| Dispatch | `ToolExecutor` próprio, **construído** para chamar o Policy Provider antes de executar (hoje não chama nada) |
| Execution | `plan_runner` (Python) — já funciona, não mexer |
| HITL | `hitl.py` (Python) — já funciona |
| Action Receipt | **Construir no core** — nenhum candidato externo tem exactamente este formato; o `DelegationLink.compute_hash()` do AgentMesh é a peça mais próxima a reaproveitar como inspiração de formato |
| Audit/Provenance | Portar o padrão já real de `mcp/plan_runner/` (Python) para `packages/mcp/` (TypeScript) |
| Observability | OpenTelemetry (padrão, não específico de nenhum destes projectos) |
| Revocation | AgentMesh (`RevocationEntry`) |
| Kill switch/SLO | `agent-sre` do AGT, **opcional**, só quando/se houver operação 24/7 real a monitorizar |

## 12. Veredictos individuais

| Tecnologia | Veredicto | Motivo |
|---|---|---|
| **AgentMesh** (`agentmesh-platform`) | **ADAPTAR** | Delegation/Identity reais e maduros, mas exige servidor próprio — usar só os módulos Python (`identity/*`), não o `server/` completo |
| **Cedar** (via `policy-engine` do AGT) | **ADOPTAR** | Maduro, bindings Python reais, evita construir motor de policy do zero |
| **OPA** | **OPCIONAL** | Alternativa válida a Cedar, mais popular, mas redundante se Cedar for escolhido — não adoptar os dois |
| **agentgateway** | **NÃO ADOPTAR AGORA** | Resolve escala multi-cluster/data-plane que o `plan_runner` não tem hoje; standalone é viável, mas é complexidade prematura para 1 motor sequencial |
| **ContextForge (IBM)** | **NÃO ADOPTAR AGORA** | Exige Redis obrigatório; sobrepõe-se ao que o `ToolRegistry` próprio, uma vez corrigido, já cobre à escala actual |
| **SPIFFE/SPIRE standalone** | **NÃO ADOPTAR AGORA** | Resolve identidade de workload distribuída que não é o problema actual; reavaliar se/quando a federação (`ADR-001`) avançar a sério |
| **mcphound** | **NÃO ADOPTAR** | Abandonado há 6+ meses, 1 estrela — risco de manutenção real, apesar do código ser tecnicamente rico |
| **OpenA2A AIM** | **REDUNDANTE** | Sobrepõe-se directamente ao que o AgentMesh já resolve, com muito menos adopção (66⭐ vs. AGT no seu todo) |
| **`packages/mcp/` (ToolExecutor/MCPServer) actual** | **AUSENTE — CONSTRUIR** (a parte de governança em cima do que já existe) | O dispatcher em si fica; falta-lhe verificação de capacidade antes de executar — isto é trabalho próprio, pequeno, não um projecto externo |

## 13. Roadmap

**Fase 0 — agora:** fechar a lacuna de segurança real em `packages/mcp/` (ToolExecutor sem verificação de capacidade, MCPServer sem autenticação) — isto não devia esperar por nenhuma decisão de ferramenta externa, é urgente por si só.

**Fase 1 — integração:** adoptar `agentmesh-platform` só para `identity`/`delegation` (sem o servidor completo); ligar Cedar via `policy-engine`; portar o padrão de auditoria já testado em Python (`mcp/plan_runner/policy.py`) para `packages/mcp/`.

**Fase 2 — evolução:** só se houver necessidade real de escala — agentgateway (multi-cluster), ContextForge (federação de múltiplos servidores MCP), SPIFFE/SPIRE (identidade de workload distribuída entre organizações).

## 14. Riscos

- **AgentMesh está em "Public Preview"** (API pode mudar antes de GA) — adoptar hoje implica aceitar possível trabalho de migração futuro.
- **Acoplamento a Microsoft Entra**, mesmo que opcional nos módulos usados — vigiar se alguma dependência transitiva o força.
- **`packages/mcp/` e `mcp/plan_runner/` continuam como 2 implementações MCP separadas** — esta auditoria não resolveu qual delas deve ser "a" definitiva, só documentou a disparidade. Decisão humana pendente.
- Nenhuma das verificações desta auditoria testou em código real deste repositório — é avaliação estática, tal como a auditoria de memória.

## 15. Questões não resolvidas

1. `packages/mcp/` (TypeScript) vs. `mcp/plan_runner/` (Python) — qual fica, qual se descontinua, ou fundem-se?
2. `agent-compliance` do AGT nunca foi aberto por dentro — pode ter substância real para LGPD/GDPR que evitaria manter o `ComplianceManager.ts` (MOCK).
3. A.2A não foi verificado em profundidade em nenhum candidato — se o `plan_runner` vier a precisar de facto de A2A, falta essa parte da auditoria.

---

**Nada ficou por decidir sem razão declarada.** As 3 questões acima dependem de uma decisão humana (1) ou de uma leitura de código ainda não feita (2, 3) — não de evasão.
