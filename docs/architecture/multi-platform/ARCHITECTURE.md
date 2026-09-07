# Arquitectura de agentes multi-plataforma

**Âmbito:** genérico — qualquer domínio e qualquer conjunto de canais.

**Problema:** o mesmo sistema cognitivo tem de falar com humanos e com outras máquinas via **vários transportes** (CLI, chat apps, web, MCP, API, jobs) sem duplicar agentes nem perder identidade, memória de scope, política e evidência.

**Princípio:** *one brain, many doors* — o **núcleo cognitivo** é um; cada plataforma é um **adaptador**.

```text
  CLI  Telegram  Slack  Web UI  MCP clients  Cron/API  A2A
    \     |        |       |         |          |      /
     \    |        |       |         |          |     /
      ▼   ▼        ▼       ▼         ▼          ▼    ▼
              ┌─────────────────────┐
              │   CHANNEL GATEWAY   │  auth, normalize, session map
              └──────────┬──────────┘
                         ▼
              ┌─────────────────────┐
              │  CONTROL / ORCH     │  plan, policy, HITL, budget
              └──────────┬──────────┘
                         ▼
              ┌─────────────────────┐
              │  AGENTS + TOOLS     │  roles, skills, MCP tools
              └──────────┬──────────┘
                         ▼
              ┌─────────────────────┐
              │  MEMORY L0–L6       │  scopes, KBs, events
              └─────────────────────┘
```

---

## 1. Camadas multi-plataforma

| Camada | Responsabilidade | Não faz |
|--------|------------------|--------|
| **Channel adapters** | Auth do canal, parse de mensagem, rich replies, webhooks | Lógica de negócio / plan |
| **Gateway** | Normalizar `InboundMessage`, mapear `channel_user → subject`, rate limit | Escolher tools de domínio |
| **Session router** | `thread_id` / `run_id` contínuo entre canais (se política permitir) | Persistência de factos L4 |
| **Orchestrator** | Plan-Execute, HITL, budget, allowlists | UI de cada app |
| **Agent runtime** | Steps, tools, skills | Conhecer Telegram vs Slack |
| **Memory + tools** | L0–L6, retrieve, remember | Formatação WhatsApp |

O agent **não** deve conter `if (platform === "telegram")` no raciocínio de domínio.

---

## 2. Identidade

| Conceito | Função |
|----------|--------|
| `subject_id` | Utilizador ou sistema canónico (org/project/user) |
| `channel_identity` | `{ platform, external_id }` ligado ao subject |
| `agent_id` / `role` | Quem executa (seo_worker, orchestrator, …) |
| `run_id` / `plan_id` | Unidade de trabalho e trilha L2 |
| `thread_id` | Conversação lógica (pode span canais se linked) |

```text
channel_identity ──binds──► subject_id ──owns──► memory L4 scopes
                                │
                                └── participates in thread_id / runs
```

Sem bind explícito, cada canal é subject isolado (mais seguro por omissão).

---

## 3. Contrato de mensagem normalizada

Todo o adaptador converte para:

```text
InboundMessage {
  message_id
  platform            # cli | telegram | slack | web | mcp | api | cron | a2a
  channel_identity
  subject_id?         # após auth/bind
  thread_id?
  text?
  attachments[]?
  metadata            # locale, reply_to, …
  received_at
}

OutboundMessage {
  platform
  channel_identity | subject_id
  thread_id?
  text?
  blocks[]?           # estruturado genérico; adapter renderiza
  attachments[]?
  run_id?
  requires_hitl?
}
```

Adapters **renderizam** `blocks` para markdown Slack, botões Telegram, JSON MCP, etc.

---

## 4. Superfícies de entrada (platforms)

| Platform | Padrão de uso | Notas |
|----------|---------------|--------|
| **CLI / TUI** | Operador, debug, Spec Kit | Mesmo orchestrator |
| **Chat apps** | Operação diária humana | Gateway + webhooks |
| **Web control plane** | Aprovações, runs, métricas | HITL UI |
| **MCP server** | Outros agents/IDEs chamam tools/runs | Auth, scopes, `continue_run` |
| **MCP client** | Nossos agents consomem tools externas | Policy tools_allowed |
| **HTTP API** | Integrações backend | Idempotency keys |
| **Cron / queue** | Jobs, ingest L5, auditor D | Sem chat user |
| **A2A** | Agent-to-agent entre orgs/sistemas | Cards, trust boundaries |

Nem todas são obrigatórias no dia 1. O desenho **admite** plugar sem reescrever agents.

---

## 5. Sessão cross-platform

| Modo | Comportamento |
|------|----------------|
| **Isolated (default)** | Cada platform×identity tem threads próprias |
| **Linked subject** | Mesmo `subject_id` partilha L4; threads podem continuar com `thread_id` explícito |
| **Handoff** | Run começa no web, HITL no Slack, resume com mesmo `run_id` |

Handoff exige L2 persistente (eventos + estado de pausa), não só histórico do chat app.

---

## 6. HITL multi-plataforma

```text
Agent pausa (human_gate)
  → evento L2 human_gate_requested
  → notificar canal preferido do approver (web / slack / …)
  → continue_run com decisão (approve|reject|edit)
  → mesmo run_id, independentemente do canal da decisão
```

Aprovação **não** está presa ao canal que iniciou o run.

---

## 7. MCP como plataforma de primeira classe

**Expor (server):** tools estáveis, runs, `continue_run` / `cancel_run`, retrieve com ACL — descriptions para o *caller* model.

**Consumir (client):** tools externas sob allowlist por step.

MCP é mais um adaptador + contrato de tools; **não** substitui orchestrator nem memory layers.

---

## 8. Segurança multi-plataforma

| Risco | Mitigação |
|-------|-----------|
| Channel spoofing | Verificar assinaturas webhook; nunca confiar só em external_id |
| Privilege via MCP | Scopes OAuth/JWT; tool allowlist; session ownership |
| Data leak entre subjects | Isolamento L4/L5 por scope; default isolated threads |
| Prompt injection via canal | Tratar texto de canal como **untrusted**; L0 policy |
| Secrets em replies | Redaction no adapter de saída |

---

## 9. Relação com memória L0–L6

| Plataforma traz | Vai para |
|-----------------|----------|
| Texto do user | L1 → opcional extract L4 candidate |
| Ficheiro enviado | Ingest path → L5 se corpus; senão attachment L2 |
| Aprovação HITL | L2 `human_gate_resolved` |
| Preferência “responde no Slack” | L4 user |
| Corpus partilhado | L5 project/org |

---

## 10. Deployment mental

```text
[Adapters]     escalam / falham por canal
[Gateway]      stateless ou sticky sessions
[Orchestrator] + [Agents]  estado de run em store partilhado
[Memory]       Postgres/vector/graph — único lógico por env
[Prod vs lab]  gateways e secrets separados (constitution)
```

Lab pode ter só CLI + MCP; produção acrescenta canais sem mudar roles/skills.

---

## 11. O que não fazer

- Um “agent Telegram” e outro “agent Slack” com prompts divergentes para o mesmo role  
- Estado só na sessão do fornecedor do chat (impossível resume/audit)  
- Expor write destrutivo em MCP sem HITL + scope  
- Misturar subject de canais públicos sem bind  

---

## 12. Maturidade por fases

| Fase | Superfícies |
|------|-------------|
| 1 | CLI + artefactos + (opcional) API interna |
| 2 | MCP server/client + control plane web (HITL) |
| 3 | 1–2 chat adapters |
| 4 | Cron/ingest, A2A se necessário |

---

Ver: [adapters.md](./adapters.md) · [identity.md](./identity.md) · contratos em [contracts.md](./contracts.md).
