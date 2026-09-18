# ADR-001 — Governance Runtime

**Status:** proposto (ainda não implementado)
**Data:** 2026-09-17
**Fontes citadas:** `microsoft/agent-governance-toolkit` (spec `AGENTMESH-TRUST-COORDINATION-1.0`), `agentgateway` (solo.io), ContextForge (ambíguo, ver secção 9), `OpenA2A AIM`, Cedar/OPA, `draft-prakash-aip` e `draft-singla-agent-identity-protocol` (IETF, ambos chamados "AIP", ver secção 5), `aws-samples/sample-agentic-delegation`.

## 1. Contexto

O `ROADMAP-GOVERNANCE.md` identificou 3 lacunas que nenhuma ferramenta externa cobre por completo: **Delegation Graph**, **Action Receipts**, **Context Sync**. Investigação posterior (`AGENTMESH-TRUST-COORDINATION-1.0`) confirmou que não são 3 funcionalidades soltas — são 3 faces do mesmo problema: **uma acção de agente não tem hoje um ciclo de vida governado**, do pedido inicial até ao resultado final, com prova em cada passo.

Sem isto: um agente pode invocar uma tool sem se saber quem autorizou, com que âmbito, nem haver prova depois de que aconteceu. É exactamente o vazio que o `draft-prakash-aip` descreve: *"When an orchestrator delegates to a specialist that calls a tool, the delegation chain that led to the tool invocation is lost."*

Este ADR precede a implementação — define o contrato antes do código, como o `meta-workflow` já pede.

## 2. Decisão

Construir uma **Governance Runtime** como camada intermédia entre o pedido (humano ou agente) e a execução da tool — não substitui `plan_runner` nem `packages/core/`, intercepta entre eles. Reutiliza o que já está verificado externamente (AGT, agentgateway, OpenA2A AIM, Cedar/OPA) para identidade e política; constrói de raiz o que nenhum cobre (encadeamento de delegação multi-salto, sincronização de contexto federada, o formato final do recibo).

## 3. Pipeline (10 passos)

| # | Passo | O que faz | Componente |
|---|---|---|---|
| 1 | **Identify** | Resolve o DID do agente chamador a partir da credencial apresentada | AgentMesh (Ed25519+DID) |
| 2 | **Load Authority** | Carrega a cadeia de delegação até este agente (quem autorizou, com que tecto) | Delegation Graph (construir) |
| 3 | **Load Scope** | Carrega o `Scope Contract` activo para este agente+sessão | Construir (secção 4) |
| 4 | **Discover** | Encontra as tools/agentes disponíveis para o pedido | agentgateway / ContextForge (ambíguo) |
| 5 | **Filter** | Reduz a lista descoberta às que o scope actual permite | Construir, sobre Cedar/OPA |
| 6 | **Authorize** | Avalia a política (Cedar/Rego) contra a tool + recurso pedidos | Agent OS (AGT) |
| 7 | **Dispatch** | Envia a chamada real à tool/agente, já autorizada | agentgateway |
| 8 | **Receipt** | Regista o `Action Receipt` assinado e encadeado | Adaptar cadeia Merkle (AGT, Agent Hypervisor) |
| 9 | **State/Memory** | Separa o que fica imutável (receipt) do que fica mutável (memória de trabalho) | Construir (secção 7) |
| 10 | **Context Sync** | Propaga o novo estado a outros agentes com direito de o ver | Construir (secção 10, núcleo original) |

## 4. Contratos

Todos os campos abaixo são o mínimo — nenhum foi inventado sem uma fonte a apontar para a necessidade dele (citada por linha).

### Scope Contract
```
{
  agent: DID,                    // AgentMesh, did:mesh:...
  principal: DID,                // humano ou agente que originou a autoridade
  capabilities: [capability_id],  // formato action:resource:qualifier -- AGT §8.3
  resources: [resource_id],
  expires_at: timestamp           // AGT §8.3 usa o mesmo campo
}
```
Inspirado directamente no `CapabilityGrant` do AGT (§8.3): `granted_to`, `granted_by`, `capability`, `expires_at`. A diferença: o AGT só grava um salto; o `Scope Contract` é o que o Delegation Graph encadeia (secção 5).

### Tool Descriptor
```
{
  name: string,
  source: string,        // qual servidor MCP/agente a expõe
  version: string,
  capabilities: [capability_id],  // o que a tool PODE fazer
  requires: [capability_id]       // o que o CHAMADOR precisa de ter
}
```
`requires` é o que falta hoje no `retrieve_knowledge` e nas outras tools do `agent-network-mcp` — nenhuma declara formalmente do que precisa de quem a chama.

### Authorization Decision
```
{
  decision: "allow" | "deny",
  agent: DID,
  capability: capability_id,
  resource: resource_id,
  reason: string,          // Agent OS ja devolve isto (GovernanceEventSink)
  expires_at: timestamp,
  policy_version: string   // qual versao da politica decidiu isto
}
```

### Dispatch Contract
```
{
  action_id: uuid,
  authorization: AuthorizationDecision,
  tool: ToolDescriptor,
  arguments: object,
  transport: "mcp" | "a2a" | "http"   // draft-prakash-aip cobre exactamente estes 3
}
```

### Action Receipt
```
{
  action_id: uuid,
  session_id: uuid,
  agent: DID,
  principal: DID,
  capability: capability_id,
  tool: string,
  authorization: AuthorizationDecision,
  started_at: timestamp,
  completed_at: timestamp,
  result_hash: sha256,     // nao o resultado inteiro -- so a prova
  status: "success" | "failure" | "denied"
}
```
`result_hash` em vez do resultado completo é decisão deliberada: o recibo prova que uma acção aconteceu com um resultado específico, sem duplicar dados sensíveis no log de auditoria.

## 5. Modelo de Delegation — reutilizar AIP + AWS + AGT

**Nota de ambiguidade, não escondida:** "AIP" tem **duas fontes distintas com o mesmo nome**, ambas rascunhos IETF actuais chamados "Agent Identity Protocol":
- `draft-prakash-aip` — Invocation-Bound Capability Tokens (IBCTs): JWT/Ed25519 para um único salto, Biscuit (blocos append-only + Datalog) para cadeias multi-salto, com atenuação de âmbito garantida criptograficamente a cada salto.
- `draft-singla-agent-identity-protocol` — DIDs (W3C) + Capability Manifests assinados, com a **Regra D-1**: um agente filho nunca pode receber uma capacidade que o pai delegante não tenha ele próprio, e `max_delegation_depth` limita a profundidade da cadeia.

As duas convergem no mesmo princípio central, que é o que este ADR adopta, citando as duas: **uma cadeia de delegação só pode estreitar o âmbito a cada salto, nunca alargar** (a Regra D-1 do `singla`, e a "atenuação de âmbito" do `prakash`).

**AWS** — `aws-samples/sample-agentic-delegation`: referência concreta e real (não um SDK a instalar, é um blueprint de referência da AWS, explicitamente "não pronto para produção"). Confirma o mesmo princípio em produção real: *"Scope attenuation — every hop can only narrow, never widen permissions"*, implementado com Cedar no Amazon Bedrock AgentCore, com encadeamento de tokens pai→filho por hash SHA-256.

**AGT** — `CapabilityGrant` (§8.3) dá o primitivo de um salto; a **não-transitividade** confirmada em §17.1 (`AGENTMESH-TRUST-COORDINATION-1.0`) é precisamente o motivo por que este Delegation Graph tem de existir como construção própria — o AGT recusa propagar confiança automaticamente entre saltos, por desenho.

**Síntese adoptada por este ADR:** o Delegation Graph é uma cadeia de `CapabilityGrant`s (schema AGT), validada a cada salto contra a Regra D-1 (nunca alargar o âmbito do pai), com o encadeamento provado por hash (padrão AWS), não por confiança transitiva automática (que o AGT já provou, com evidência, não fazer).

## 6. Modelo de Identity — Ed25519 + DID; SPIFFE é separado

Adopta o modelo do AgentMesh confirmado por leitura directa da spec: chaves **Ed25519**, DIDs no formato `did:mesh:{hex}`, handshake por desafio/resposta assinado (não OAuth, não mTLS-SPIFFE).

**Nota já registada no `ROADMAP-GOVERNANCE.md` e reafirmada aqui:** o AgentMesh **não é SPIFFE-compliant** — mTLS usa X.509 genérico com o DID no SAN, não SPIFFE-SVID. Se este projecto precisar de identidade de *workload* interoperável com infra-estrutura SPIFFE externa a este sistema de agentes, isso continua a ser o **SPIRE/SPIFFE standalone**, como dependência distinta, não substituída pelo AgentMesh.

## 7. Separação State × Memory (imutável vs. mutável)

| | State (imutável) | Memory (mutável) |
|---|---|---|
| O que é | `Action Receipt` — prova de que algo aconteceu | Contexto de trabalho corrente do agente |
| Muda depois de escrito? | Nunca — é o log de auditoria | Sim, a cada passo |
| Onde vive | Cadeia encadeada por hash (adaptar Merkle do AGT) | `working_memory.py` (já existe, `plan_runner`) já é o precedente deste padrão |
| Falha de escrita | Bloqueia a acção — sem recibo, a acção não é considerada válida | Não bloqueia — memória é auxiliar, não prova |

Este padrão já existe parcialmente no `plan_runner` (`working_memory.py` é mutável, `events.jsonl` é append-only) — a Governance Runtime generaliza o mesmo princípio a qualquer chamada MCP/A2A, não só a planos.

## 8. Ciclo completo de uma chamada MCP/A2A

```
Agente A quer chamar a tool T de Agente B
  1. Identify: resolve o DID de A
  2. Load Authority: encontra a cadeia de delegação de A até à raiz humana
  3. Load Scope: confirma que o Scope Contract de A ainda não expirou
  4. Discover: agentgateway/ContextForge encontra T
  5. Filter: T está dentro do que A pode pedir? (capabilities ∩ scope)
  6. Authorize: Cedar/OPA avalia -- Authorization Decision (allow/deny)
  7. Dispatch: se allow, agentgateway envia a chamada real a T (via MCP/A2A/HTTP)
  8. Receipt: regista Action Receipt (result_hash, nao o resultado inteiro)
  9. State/Memory: o Receipt fica imutavel; a Memory de A actualiza-se
  10. Context Sync: se B precisa de saber que isto aconteceu, propaga-se
      (nucleo original, secção 10 -- ninguem cobre isto hoje)
```
Se qualquer passo 1-6 falhar, o ciclo pára ali — nunca chega a "Dispatch" sem uma `Authorization Decision` explícita.

## 9. Componentes — reutilizar vs. adaptar vs. construir

| Componente | Reutilizar | Adaptar | Construir |
|---|---|---|---|
| Agent OS (policy engine) | ✅ Cedar/Rego já prontos | | |
| AgentMesh (identidade) | ✅ Ed25519+DID | | |
| `CapabilityGrant` (grant de 1 salto) | ✅ schema do AGT §8.3 | | |
| Cadeia de Merkle (auditoria) | | ✅ adaptar ao formato de `Action Receipt` | |
| agentgateway (data plane) | ✅ Bind/Listener/Route/Backend | | |
| **ContextForge** | | | ⚠️ **ambíguo** — `mcp-context-forge` (gateway/discovery, melhor encaixe) vs. `waterflane/ContextForge` (não relacionado); confirmar qual antes de adoptar |
| OpenA2A AIM | ✅ identidade+auditoria complementar | | |
| Delegation Graph (cadeia multi-salto) | | | ✅ núcleo próprio — nenhuma fonte cobre isto pronto (secção 5) |
| Context Sync | | | ✅ núcleo original (secção 10) |
| Scope/Tool/Dispatch Contracts (secção 4) | | | ✅ desenhados aqui, sobre primitivos existentes |

## 10. Núcleo original — Federated State Model

Esta secção **não vem de nenhuma fonte externa** — é a proposta original deste ADR para a única lacuna que nem o AGT, nem o agentgateway, nem o OpenA2A AIM resolvem: como é que dois agentes, potencialmente em processos/máquinas diferentes, partilham o mesmo contexto de tarefa sem um único processo central a fazer de árbitro.

**Modelo proposto:**

- Cada agente mantém a sua própria `Memory` local (mutável, secção 7) — nunca partilhada directamente.
- Eventos de `State` (os `Action Receipts`, imutáveis) são o **único** veículo de sincronização entre agentes — um agente nunca lê a `Memory` de outro directamente, só os `Receipts` que esse outro publicou.
- Cada `Action Receipt` carrega `session_id`, permitindo a qualquer agente reconstruir "o que já aconteceu nesta tarefa" filtrando pelos `Receipts` dessa sessão, em vez de pedir estado a outro agente ao vivo.
- Isto torna o "Federated State" **eventualmente consistente por desenho**, não fortemente consistente — um agente pode estar a agir com um Receipt por chegar; o `Scope Contract` (com `expires_at` curto) limita o dano de uma decisão tomada com estado ligeiramente desactualizado.

Isto resolve o gap identificado no `ROADMAP-GOVERNANCE.md` ("Context Sync — o item com menos cobertura externa") sem inventar um mecanismo de sincronização em tempo real que nenhuma das fontes citadas oferece — reaproveita o que já é imutável (o Receipt) como o próprio mecanismo de sincronização, em vez de construir um canal novo.

**O que este núcleo não resolve, por desenho, e fica assinalado para decisão futura:** não há aqui nenhum mecanismo de "notificação" activa (um agente não é avisado de um Receipt novo, tem de o ir procurar) — é pull, não push. Se algum caso de uso precisar de latência baixa entre um evento e outro agente reagir, isto precisa de uma camada adicional não coberta por este ADR.

## Referências

- [`ROADMAP-GOVERNANCE.md`](../governance/ROADMAP-GOVERNANCE.md) — origem das 3 lacunas (Delegation Graph, Action Receipts, Context Sync)
- [`GOVERNANCE.md`](../GOVERNANCE.md) — visão consolidada da camada de governança
- [`CORE-MAPPING.md`](../CORE-MAPPING.md) — estado real de `packages/core/`
