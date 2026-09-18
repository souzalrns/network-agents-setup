# Auditoria de Governança — Fase 2: Microsoft AGT (alegação a alegação) + agentgateway

## Achado principal desta fase — revisa uma conclusão do `ADR-001`

**O `ADR-001` (secção 5) concluiu que o Delegation Graph é "trabalho próprio, o AGT não resolve por desenho"** — baseado na leitura da spec `AGENTMESH-TRUST-COORDINATION-1.0.md` (datada de 2026-07-09), que definia só `CapabilityGrant` de um salto e não-transitividade explícita (§17.1).

**Essa spec está desactualizada face ao pacote realmente publicado hoje.** Descarreguei e abri o `agentmesh-platform` **v3.7.0** (PyPI, real, 167 ficheiros Python, não simulado) e confirmei, em `agentmesh/identity/delegation.py`:

- `DelegationLink` — um salto de uma cadeia, com `parent_did`, `child_did`, `depth`, `parent_capabilities`, `delegated_capabilities`, **hash encadeado** (`link_hash`, `previous_link_hash`) e verificação de estreitamento de capacidade (`verify_capability_narrowing()` — cada capacidade delegada tem de ser subconjunto da do pai, com suporte a wildcards `action:*`).
- `ScopeChain` — a cadeia inteira, **multi-salto de facto** (`links: list[DelegationLink]`), com `root_sponsor_email` (humano na raiz), `leaf_did` (agente final), `max_depth` configurável (`DEFAULT_DELEGATION_MAX_DEPTH`), e `UserContext` para fluxos On-Behalf-Of com RBAC.
- `identity/revocation.py` — lista de revogação real (`RevocationEntry` com `revoked_at`, `reason`, `revoked_by`, `expires_at`), não um campo de estado como em `TrustManager.ts`.

**Isto é exactamente o "Delegation Graph" que o `ADR-001` propôs construir do zero.** Não é idêntico (as verificações de assinatura são "best-effort", só verificadas se o `known_identities` tiver a identidade do pai — não é 100% criptograficamente forçado), mas a estrutura de dados, o hash-chain, e o estreitamento de capacidade já existem, testados, num pacote MIT publicado hoje.

**Isto não é "redundante — apagar tudo do ADR"** — é "reavaliar antes de construir, porque a evidência mudou desde que o ADR foi escrito". Fica marcado para a Fase 4 decidir formalmente (ADOPTAR/ADAPTAR vs. CONSTRUIR).

## 1. Microsoft AGT — identificação exacta

- Repositório: `microsoft/agent-governance-toolkit`, MIT, **6.285 estrelas reais** (não confirmado antes com este número exacto), push mais recente há horas — activamente mantido, não abandonado.
- **Não é um projecto único e monolítico** — é um monorepo com pelo menos 5 linguagens de SDK (`agent-governance-dotnet/-golang/-python/-rust/-typescript`), mais um `policy-engine` em **Rust** à parte (com bindings `sdk/{dotnet,node,python,rust}`), mais integrações CLI para antigravity/claude-code/copilot-cli/opencode.
- Dentro de `agent-governance-python/`, há **17 pacotes nomeados separadamente**: `agent-compliance`, `agent-discovery`, `agent-hypervisor`, `agent-learning`, `agent-lightning`, `agent-marketplace`, `agent-mcp-governance` (**deprecado**), `agent-mesh`, `agent-os`, `agent-primitives`, `agent-rag-governance`, `agent-runtime`, `agent-sandbox`, `agent-sre`, mais os de infra (`-core`, `-cli`, `-integrations`, `-protocols`).

## 2. As 6 alegações, verificadas separadamente

| Alegação | Existe realmente? | Evidência |
|---|---|---|
| **Agent OS** — é runtime? policy engine? só documentação? | **Documentação + wrapper** no path `agent-governance-python/agent-os/` (sem `src/`, sem `pyproject.toml`, só docs/examples/benchmarks). **O código real vive no pacote `agent-os-kernel`** (PyPI, v3.7.0, 1.1MB, confirmado real) e no `policy-engine` Rust à parte | Código real existe, mas **não no path que o nome sugere** — é preciso saber isto para não concluir "não existe" por engano |
| **AgentMesh** — código funcional? Ed25519/DID/certificados/trust score, ou só documentação? | **Código real e substancial** — `agentmesh-platform` v3.7.0, 167 ficheiros .py | Confirmado: DID (`did:mesh:`), Ed25519 (identidade), **e também SPIFFE/SVID real** (`identity/spiffe.py`) — corrige a conclusão anterior desta auditoria (baseada só na spec de Julho) de que "não é SPIFFE-compliant". Também tem integração real com Microsoft Entra ID (`entra.py`, `managed_identity.py`) — relevante para "vendor neutrality": há acoplamento real ao ecossistema Azure em módulos opcionais |
| **Agent Runtime** — os 4 anéis existem? São enforceable ou conceptuais? | **Nome enganoso** — `agent-runtime/src/` tem só `deploy.py` (quase vazio). **Os anéis reais vivem em `agent-hypervisor/src/hypervisor/rings/`**, com `breach_detector.py`, `classifier.py`, `elevation.py`, `enforcer.py` — nomes de ficheiro consistentes com aplicação real, não só conceito | Enforceable, mas sob o nome errado — é preciso ir a `agent-hypervisor`, não a `agent-runtime`, para os anéis |
| **Agent SRE** — SLO? kill switch? circuit breaker? | **Muito mais rico do que eu tinha caracterizado antes** — `agent_sre/` tem `slo/`, `chaos/`, `cascade/`, `k8s/`, `replay/`, `incidents/`, `anomaly/`, `certification/`, `signing.py`, `sbom.py` como directórios/ficheiros reais | Isto cobre directamente 3 lacunas que confirmei **ausentes** em `packages/core/` na Fase 1 (SLO, replay, algo equivalente a circuit-breaker via `cascade/`) |
| **Agent Compliance** — implementação real ou documentação OWASP? | Tem `pyproject.toml` + `src` + `tests` — **estrutura de pacote real**, não só documentação (não abri o conteúdo interno de `src` nesta passagem — fica **NÃO VERIFICADO EM PROFUNDIDADE**, só confirmado que não é vazio) | — |
| **MCP Security Gateway** (`agent-mcp-governance`) — código executável? Que ataques detecta? | **DEPRECADO, oficialmente** — o próprio `__init__.py` emite `DeprecationWarning`, a apontar para `agent-governance-toolkit-protocols`. É descrito no seu README como "thin, typed re-export surface" sobre `agent-os-kernel` — nunca foi a "gateway" independente que o nome sugeria | **Achado que corrige `ROADMAP-GOVERNANCE.md`/`SECURITY.md` anteriores** — citavam isto como um componente MCP-específico a considerar; hoje é um alias descontinuado |

## 3. agentgateway (solo.io / agentgateway.dev)

- Repositório: `agentgateway/agentgateway`, **Apache-2.0**, 4.914 estrelas reais, Rust.
- **Standalone é caminho de primeira classe, documentado separadamente do Kubernetes** — "Standalone Quickstart" (config YAML plana) vs. "Kubernetes Quickstart" (controlador + Gateway API), dois modos oficiais, não um fallback informal.
- **Não exige Kubernetes nem Envoy** para correr — confirmado pela própria documentação, não inferido.
- Routing inteligente para modelos self-hosted usa extensões do "Kubernetes Inference Gateway" — **essa parte específica é K8s-only**, mas é uma funcionalidade adicional, não o modo base de operação.

**Resposta à pergunta central do pedido:** agentgateway é **infra externa opcional**, não componente obrigatório do núcleo — corre standalone, sem dependência forçada de K8s.

## 4. O que fica para a Fase 3

ContextForge (resolver a ambiguidade já conhecida de 2 projectos), Cedar, OPA, SPIFFE/SPIRE standalone (agora com a pergunta extra: já não é só "complementar ao AgentMesh", é preciso perceber se o `identity/spiffe.py` do AgentMesh já cobre o que o SPIRE standalone faria, ou se continuam a ser coisas distintas), mcphound, OpenA2A AIM.

## 5. Nota metodológica

Esta fase confirma o valor do método que estás a pedir: **a conclusão do `ADR-001` sobre Delegation Graph não estava errada por preguiça — estava certa para a evidência que existia em Julho, e ficou desactualizada porque o AgentMesh evoluiu depois disso.** Isto reforça por que não se deve tratar nenhuma verificação anterior como permanente — mesmo a minha própria, de há poucos dias.
