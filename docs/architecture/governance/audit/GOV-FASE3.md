# Auditoria de Governança — Fase 3: ContextForge, Cedar, OPA, SPIFFE/SPIRE, mcphound, OpenA2A AIM

## 1. ContextForge — ambiguidade resolvida com números, não escolha arbitrária

| | `IBM/mcp-context-forge` | `waterflane/ContextForge` |
|---|---|---|
| Estrelas reais | **4.492** | 4 |
| Licença | Apache-2.0 | Apache-2.0 |
| Push mais recente | Minutos antes desta verificação | NÃO VERIFICADO nesta fase |
| O que é | Gateway/registry/proxy MCP+A2A+REST, federação, discovery, guardrails | Plataforma de context engineering para desenvolvimento de código assistido por IA |

**Resolvido: é o `IBM/mcp-context-forge`**, por 1000x mais adopção e por corresponder exactamente ao propósito (discovery/registry/gateway), não por escolha arbitrária.

**Infra necessária, confirmado no `pyproject.toml`:** `redis>=8.0.1` está nas dependências **obrigatórias** (não em `optional-dependencies`). O quickstart oficial também usa PostgreSQL. **Não é zero-infra** — precisa sempre de, no mínimo, Redis a correr. O `.env` exige segredos reais (`JWT_SECRET_KEY`, `AUTH_ENCRYPTION_SECRET`) — o gateway recusa-se a arrancar com placeholders (confirmado no próprio README).

**Classificação:** INFRA NECESSÁRIA, não INFRA OPCIONAL.

## 2. Cedar

- `cedar-policy/cedar`: **1.738 estrelas reais**, Apache-2.0, Rust.
- **Bindings Python reais confirmados**: `cedarpy` no PyPI, v4.12.0, histórico de versões maduro (desde 0.1.0 até 4.12.0) — não é um wrapper amador recente.
- Linguagem de policy própria (Cedar), com schema, entities, attributes, relationships — suporta RBAC e ABAC (atributos contextuais), ao contrário do RBAC simples que já existe em `SecurityManager.ts`.
- **Nota relevante para o `plan_runner`:** o `policy-engine` do próprio Microsoft AGT (achado da Fase 2) já é escrito em Rust e aceita Cedar como uma das linguagens de policy suportadas — ou seja, adoptar Cedar directamente pode já vir "de borla" se se adoptar o `agent-os-kernel` do AGT, em vez de ser uma escolha independente.

## 3. OPA (Open Policy Agent)

- `open-policy-agent/opa`: **12.248 estrelas reais** — mais que o dobro do Cedar, e é projecto **CNCF graduado** (conhecimento estável, não re-verificado a fundo nesta pesquisa por ser um facto já consolidado antes do meu corte de conhecimento, não por preguiça — sinalizado explicitamente para seres tu a decidir se queres verificação adicional).
- Go, Apache-2.0.
- Rego (linguagem própria), modos embedded/sidecar/HTTP API/WASM — todos documentados e estáveis há anos.

**Cedar vs. OPA, sem declarar vencedor (como o pedido exige):**

| Capacidade | Cedar | OPA |
|---|---|---|
| Linguagem | Cedar (própria, pensada para autorização) | Rego (mais geral, não só autorização) |
| Popularidade | 1.738⭐ | 12.248⭐ |
| Bindings Python | `cedarpy`, maduro | Nativo via HTTP API; WASM também possível |
| Explicabilidade | Desenhado para ser analisável estaticamente (verificação formal é objectivo do projecto) | Rego é mais expressivo, mais difícil de analisar estaticamente |
| Encaixe no AGT | Suportado nativamente pelo `policy-engine` Rust do AGT | Também suportado pelo AGT (confirmado na pesquisa da Fase 2/`ROADMAP-GOVERNANCE.md`) |

## 4. SPIFFE/SPIRE — correcção ao que escrevi na Fase 2

**Achado que corrige a Fase 2 desta mesma auditoria:** descrevi o `agentmesh/identity/spiffe.py` como "SPIFFE real". Ao abrir o ficheiro por inteiro (315 linhas), encontrei **3 comentários explícitos de simulação**: *"In production, this would request an SVID from the SPIRE server"*, *"would integrate with SPIRE"*, *"would verify against the SPIRE bundle"*. É o **mesmo padrão MOCK** já visto em `SecurityManager.ts` ("Em produção, verificar contra hash armazenado"). Correcção: o AgentMesh tem o **modelo de dados** SPIFFE (classe `SVID`, parsing de `spiffe://trust-domain/path`), **não a integração real** com um servidor SPIRE.

- `spiffe/spire` (implementação): **2.542 estrelas reais**, Apache-2.0, Go.
- `spiffe/spiffe` (especificação): 1.855 estrelas, Apache-2.0.

**Resposta à pergunta central:** com esta correcção, a resposta muda de "pode ser redundante com o AgentMesh" para **"continua distinto e necessário se se quiser SPIFFE de verdade"** — o AgentMesh não substitui o SPIRE standalone, porque a sua própria implementação SPIFFE ainda não está ligada a um SPIRE real.

## 5. mcphound — correcção séria ao `SECURITY.md`

**Achado que exige correcção num documento já publicado.** O `SECURITY.md` (produzido há dias) cita `mcphound` (`tayler-id/mcphound`) como "confirmado sem ambiguidade — projecto único, bem documentado", ao lado do `offsec-ai` como ferramenta activa de auditoria MCP.

Reverifiquei agora, mais a fundo:
- **1 estrela real** no GitHub.
- **Último push: 2026-03-05 — mais de 6 meses parado** à data de hoje.
- **Mas é código real e substancial**: 910 ficheiros, workflow de CI, integração real com OSV.dev para scan de vulnerabilidades, motor de "3-layer capability tagging", grafo interactivo de topologia de ameaças, exportação de relatório "Safety Seal". Os artefactos internos (`_bmad-output/`) sugerem que foi construído com um método de desenvolvimento assistido por IA estruturado (BMAD), não é um projecto amador improvisado — só **não teve adopção externa nem manutenção recente**.

**Classificação correcta:** não é "scanner activo e mantido" como descrito antes — é **código real, funcionalmente rico, mas efectivamente abandonado**. Continua a poder ser usado localmente (é só código, corre independentemente de estrelas), mas não há ninguém a corrigir bugs novos nem a acompanhar mudanças no protocolo MCP.

**Acção recomendada:** corrigir o `SECURITY.md` para reflectir isto — não remover a ferramenta da lista (o código funciona), mas remover a linguagem "confirmado sem ambiguidade, bem documentado" sem qualificar a maturidade real.

## 6. OpenA2A AIM

- `opena2a-org/agent-identity-management`: **66 estrelas reais**, Apache-2.0, push ontem — activo, mas modesto em adopção (não é um projecto dominante, é um entre vários candidatos nesta área ainda imatura).
- **Pergunta central do pedido:** "qual problema concreto resolve que o próprio contrato de identidade/delegação não resolve?" — dado o achado da Fase 2 (AgentMesh já tem `ScopeChain`/`DelegationLink` reais e mais maduros, com 167 ficheiros de código e integração Entra), **a resposta provável é: pouco, se o AGT for adoptado** — seria sobreposição directa de responsabilidade (identidade+delegação de agentes), não complementaridade. Fica para a matriz de sobreposição da Fase 4 confirmar isto formalmente.

## 7. Resumo das correcções feitas a mim próprio nesta fase

1. AgentMesh SPIFFE: de "real" para "modelo de dados real, integração simulada".
2. mcphound: de "confirmado, bem documentado" para "código real, mas 6+ meses abandonado, 1 estrela".

Nenhuma destas correcções significa que os achados anteriores foram inventados — significa que a primeira passagem parou um nível acima de onde devia. É exactamente o que o método pede: verificar até ao código, não até ao README ou à existência do repositório.

## 8. Próxima fase

Fase 4 — padrões/specs, CVEs, licenças (registo formal), maturidade (tabela), MCP (classificação formal), as 3 matrizes (capacidades/comparação/sobreposição), arquitectura recomendada (testar a hipótese Identity/Policy/Discovery Provider), donos de responsabilidade, veredictos individuais (ADOPTAR/ADAPTAR/EXTRAIR/etc.), roadmap, riscos, questões em aberto, `AUDIT-GOVERNANCE.md` final.
