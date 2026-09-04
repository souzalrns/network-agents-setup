# Padrões portáveis (DeepSeek Harness / Cordis) — sem o monólito

**Regra:** copiar *padrões de desenho*, não o kernel Cordis, não o runtime dsh como core do setup.

Origem de inspiração: DeepSeek Harness (everything-is-a-plugin), Cordis (efeitos reversíveis, deps, eventos), workflow/subagent isolation.

Alvo: `network-agents-setup` +, mais tarde, alinhamento conceptual com produção MCP — **sem** substituir `agent-network-mcp` por dsh.

---

## Inventário de padrões

| ID | Padrão | Fase | Estado no setup |
|----|--------|------|-----------------|
| P01 | Registry plugável (chaves estáveis) | 1 | Parcial (actions no plan + skills) |
| P02 | Tools com policy (pre/post gate) | 1–2 | Parcial (`tools_allowed`) |
| P03 | Model-visible → log (evidência) | 1 | Parcial (pilots + verify) |
| P04 | Sub-fluxos com contexto isolado | 1–2 | Parcial (passos + artefactos) |
| P05 | depends_on / inject de deps | 1 | Feito no Plan schema |
| P06 | Human / approval gate | 1 | Feito (`human_gate`) |
| P07 | Budget (max steps / replans) | 1 | Feito no plan |
| P08 | Prompt em camadas | 2 | Documentar |
| P09 | Seam provider/consumer | 2 | Documentar |
| P10 | Session/event append-only | 2–3 | Depois (runtime) |
| P11 | Waterfall de política | 2–3 | Depois (runtime) |
| P12 | Efeitos reversíveis (mount/unmount) | 3 | Depois |
| P13 | Profiles / bundles de composição | 3 | Depois |
| P14 | Subagent fork vs fresh | 2 | Documentar |
| P15 | Workflow fan-out scripted | 3 | Depois |

---

## Fase 1 — já / imediato (contratos, sem runtime Cordis)

### P01 Registry plugável

- Toda capacidade de domínio tem **id estável**: `seo_brief`, `copy_answer_first`, `critic_item13`, …
- O plano referencia `action`, não prosa livre.
- Ficheiro canónico: [`registry/actions.md`](./registry-actions.md) (catálogo).
- Skills em `skills/claude/` = procedimentos; actions = *o que* o orquestrador pode despachar.

### P02 Tools com policy

- Por passo: só `tools_allowed`.
- Default-deny: tool ausente da lista = impossível nesse passo.
- Policy textual (constitution): planner sem tools destrutivas; produção MCP fora do lab.
- Evolução: `tools/pre-execute` conceptual = validar args + allowlist antes de correr.

### P03 Model-visible → log

- Tudo o que influenciou uma decisão ou output de agente deve ter **artefacto ou evento** recuperável.
- Pilotos: `00`…`03` + plan yaml.
- Verify não aceita “o modelo disse OK” sem ficheiro/checklist.
- Mais tarde: log append-only de tool calls (P10).

### P04 Contexto isolado por sub-fluxo

- Cada passo escreve o seu `output_artifact`; o seguinte lê só o que `inputs` / `depends_on` permitem.
- Worker não herda o “cérebro” completo do orquestrador (evita goal drift).
- Analogia dsh: `subagent` (fresh) vs `subagent_fork` (com histórico) — no setup preferir **fresh + artefactos explícitos** por omissão.

### P05–P07

Já no `docs/architecture/plan-execute/`.

---

## Fase 2 — próximo estágio (docs + contratos mais ricos)

### P08 Prompt em camadas

1. Estável (identidade / constitution)  
2. Projecto (knowledge_refs)  
3. Volátil (turno / passo actual)  

Melhora cache e reduz mistura de regras de cliente no framework.

### P09 Seam (definition / provider / consumer)

- **Definition:** interface (ex. `SeoBrief` JSON Schema)  
- **Provider:** quem implementa (agente + modelo)  
- **Consumer:** passo seguinte ou critic  

Trocar provider sem mudar o contrato.

### P11 Waterfall de política (conceptual)

Cadeia ordenada antes de side-effect:

1. allowlist tool  
2. validação de schema de args  
3. scope paths (não tocar produção)  
4. human_gate se high-impact  
5. execute  
6. log resultado  

### P14 Subagent fresh vs fork

| Modo | Quando |
|------|--------|
| Fresh (só goal + artefacto) | Default; isolation máxima |
| Fork (histórico pai) | Raro; debug ou continuação explícita |

---

## Fase 3 — runtime (só no setup lab, não prod MCP)

### P10 Session log append-only

- Eventos: `plan_approved`, `step_start`, `tool_call`, `tool_result`, `step_done`, `verify`, `human_gate`.
- Replay e auditoria; “feito” = eventos + artefactos.

### P12 Mount/unmount limpo

- Activar skill/agent no registry com teardown (sem estado fantasma entre pilots).

### P13 Profiles

- Ex.: `profile: content-pipeline` vs `profile: code-speckit` — conjuntos de actions + tools + gates.

### P15 Fan-out

- Orquestrador despacha N workers isolados; merge explícito no supervisor (não peer-to-peer livre).

---

## Explicitamente fora de scope

- Vendor do kernel Cordis no setup  
- Substituir `agent-network-mcp` por `dsh`  
- UI web do Harness como produto  
- Hot-reload Cordis em produção  

---

## Ligação Spec Kit / constitution

Estes padrões reforçam `CONSTITUTION-DRAFT.md`:

- least privilege (P02)  
- evidência (P03)  
- plan-execute (P04–P07)  
- setup ≠ produção  

Ao correr `/speckit-plan` / implement, preferir acções do [registry](./registry-actions.md).
