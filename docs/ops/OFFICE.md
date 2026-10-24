# Escritório dos Agentes — contrato (OFFICE-A1)

> Decisões do maestro (2026-10-24): **opção A**, o escritório é uma **projecção de eventos reais**;
> **D1 = A**, os departamentos são do escritório e não as áreas do router.
> Não guarda estado próprio, não anima trabalho que não existe e não esconde nenhum agente.
> O motor (planos, router, HITL, memória) não muda: o escritório só o lê.

**Hoje:** 100 agentes (79 do runner + 21 só do MCP de produção), 18 departamentos em 2 alas, 41 lugares.

## 1. Peças

| Peça | Onde | O que faz |
|---|---|---|
| Mapa de lugares | `config/office.yaml` | 2 alas (funções, negócios) → departamentos → lugares → agentes reais |
| Inventário do MCP | `config/mcp-agents.yaml` | Os 34 agentes de `agent-network-mcp/lib/agents.js`; `runtime:` liga os 13 que também existem no runner |
| Validação | `python -m plan_runner.office` (CI: `runner-tests.yml`) | Falha se o mapa puder mentir (§2) |
| Projecção | `plan_runner/office.py → project()` | `events.jsonl` dos runs → estado por agente, lugar e departamento |
| Snapshot | `python -m plan_runner.office --project RUN_DIR...` | JSON que a UI lê (§5) |
| Testes | `runner/tests/test_office.py` | Validação, cada evento, agregação e 1 run real em stub |

## 2. Regras do mapa

- **Os departamentos não são as áreas do router (D1 = A).** O router continua a escolher pela área; o escritório agrupa para pessoas lerem. Mudar um lugar não mexe no routing nem no conector do Claude.ai.
- Duas alas: `funcoes` (Direção, Marketing, Comercial, Atendimento, Finanças, Jurídico & Compliance, Software, Segurança, Pesquisa, Trading, Jogos, Documentação) e `negocios` (Construção & Técnica, ViannaLegal, Imobiliário, Produto Digital, Formação & SST, Saúde).
- Cada agente do runner (`areas[].agents[]`) está em **exactamente um** lugar: sem órfãos, sem duplicados, sem inventados.
- Cada agente **só do MCP** (`runtime: null` em `config/mcp-agents.yaml`) está em exactamente um lugar, escrito `mcp:<id>`. Os 13 que existem nos dois sítios entram pelo id do runner, uma vez só (o snapshot diz `"mcp": "<id>"`).
- `lead`: `null` ou um agente do próprio departamento. Só é Lead quem orquestra de facto (hoje só `marketing.marketing`).
- Departamentos sem agentes (Jogos, Documentação) ficam com `seats: []`; a UI mostra "sem agentes ainda".
- Nomes de lugar são **funções** (PESQUISA, QUALIDADE), nunca nomes humanos: quem usa o escritório tem de saber que fala com uma IA (AI Act, art. 50). A UI mostra sempre "agente IA".

## 3. Atribuição de um passo a um agente

1. O evento `step_started` traz a `action` do passo.
2. A `action` resolve-se pelo frontmatter de `agents/**/*.agent.md` (`action:`). A validação exige que cada `action` pertença a **um só** agente.
3. `plan_approve` é um gate humano, não trabalho de um agente: não se atribui.
4. Uma `action` sem dono vai para `unattributed` no snapshot. Fica à vista, não desaparece. O teste `test_todos_os_passos_dos_planos_sao_atribuiveis_a_um_agente` garante que hoje todos os planos de `docs/orchestration/` resolvem.

## 4. Evento → estado

Ordem de gravidade (do pior para o melhor): **erro → precisa de ti → a trabalhar → a pensar → à espera → sem telemetria**.

**Sem telemetria** (`untracked`): os agentes do MCP de produção ainda não emitem eventos. Nunca aparecem "à espera" como se soubéssemos; só ganham estado real quando o MCP registar chamadas (OFFICE-A2).

| Evento do runner | Estado | Vai para |
|---|---|---|
| `step_started`, `tool_called`, `budget_resumed` | a trabalhar | agente do passo |
| `step_waiting_external` | a pensar | agente do passo |
| `step_finished`, `human_gate_resolved` | à espera | agente do passo (ou o último activo do run) |
| `step_failed` | erro | agente do passo |
| `human_gate_requested`, `tool_approval_requested`, `budget_exceeded` | precisa de ti | agente do passo; num gate `plan_approve`, o último agente activo do run (é o trabalho dele que espera decisão) |
| `plan_aborted`, `done_when_failed` | erro | último agente activo do run |
| `plan_done` | à espera | todos os agentes do run |

Agregação:
- **agente:** o estado do evento mais recente que lhe foi atribuído, em qualquer run;
- **lugar:** o mais grave dos seus agentes. Um lugar nunca parece calmo com um agente em erro;
- **departamento:** o mais grave dos seus lugares; `null` se não tiver lugares;
- `untracked` só ganha quando nenhum agente do lugar tem eventos possíveis (um lugar com um agente do runner à espera e um do MCP fica "à espera").

## 5. Snapshot

```json
{
  "version": 1,
  "generated_at": "…",
  "states": ["error", "needs", "working", "thinking", "idle", "untracked"],
  "agent_count": 100,
  "departments": [
    {"id": "marketing", "wing": "funcoes", "name": "Marketing", "lead": "marketing.marketing", "agent_count": 50, "state": "needs",
     "seats": [{"id": "marketing-qualidade", "name": "QUALIDADE", "does": "Revê tudo antes de sair", "state": "needs",
                "agents": [{"id": "marketing.critic_item13", "source": "runtime", "mcp": null, "state": "needs", "run_id": "…", "step_id": "…", "at": "…", "event": "human_gate_requested"}]}]},
    {"id": "negocio-viannalegal", "wing": "negocios", "name": "ViannaLegal", "lead": null, "agent_count": 2, "state": "untracked",
     "seats": [{"id": "viannalegal-site", "name": "CIDADANIA", "does": "…", "state": "untracked",
                "agents": [{"id": "mcp:viannalegal", "source": "mcp", "mcp": "viannalegal", "state": "untracked", "run_id": null, "step_id": null, "at": null, "event": null}]}]}
  ],
  "unattributed": []
}
```

**Privacidade:** o snapshot só leva metadados (ids, estado, hora, tipo de evento). Nunca leva o objectivo do plano, payloads, conteúdos ou nomes de clientes. Isto conta sobretudo para o Jurídico (sigilo profissional da OA e RGPD).

## 6. Próximas fases

| ID | Fase | Dono | Bloqueio |
|---|---|---|---|
| OFFICE-A2 | Eventos no Supabase (tabela só de acréscimo + Realtime) para o escritório ao vivo, do runner e das chamadas ao MCP | AMBOS | O SQL em produção e as credenciais do runner são do maestro |
| OFFICE-MCP-SYNC | Verificação automática entre `lib/agents.js` (MCP) e `config/mcp-agents.yaml` | CLAUDE | — |
| COM-1 | Pack Comercial: propostas, follow-ups e qualificação inbound (D2 = A) | CLAUDE | — |
| OFFICE-A3 | Escritório 2D com 3 níveis (empresa → departamento → lugar) a ler o snapshot | CLAUDE | — (começa com snapshots de stub) |
| OFFICE-A4 | Caixa "precisa de ti": aprovar ou recusar gates a partir do escritório, com autenticação e registo de auditoria | AMBOS | Autenticação do escritório por decidir; OFFICE-A2 |
| RUNNER-WHY-1 | O "porquê" de cada passo, aberto a partir do lugar | CLAUDE | — (já no §4) |
| OFFICE-3D-1 | Pele 3D opcional (three.js + `@pixiv/three-vrm`, MIT) sobre o mesmo snapshot | CLAUDE | — |
| OFFICE-VOZ-1 | Voz local em pt-PT, nunca na cloud | AMBOS | Sem candidato confirmado |

Fora de âmbito (decisão de 2026-10-24): humanos fotorrealistas, multijogador, nomes humanos fictícios, voz na cloud e animação de trabalho que não existe.

**Proposta para o OFFICE-A2 (NÃO aplicada; o SQL em produção é do maestro):** tabela `office_events` só com metadados (`id`, `run_id`, `type`, `at`, `step_id`, `agent_id`, `state`), RLS ligado e sem políticas para `anon`/`authenticated` (escreve o runner com a service role; a UI lê por um endpoint do servidor), e entrada na publicação do Realtime. O SQL final vai num ficheiro em `scripts/migrations/`, com query de controlo, no PR do OFFICE-A2.
