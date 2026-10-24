# Escritório dos Agentes — contrato (OFFICE-A1)

> Decisão do maestro (2026-10-24, opção A): o escritório é uma **projecção de eventos reais**.
> Não guarda estado próprio, não anima trabalho que não existe e não esconde nenhum agente.
> O motor (planos, router, HITL, memória) não muda: o escritório só o lê.

## 1. Peças

| Peça | Onde | O que faz |
|---|---|---|
| Mapa de lugares | `config/office.yaml` | Departamentos (= áreas de `config/areas.yaml`) → lugares → agentes reais |
| Validação | `python -m plan_runner.office` (CI: `runner-tests.yml`) | Falha se o mapa puder mentir (§2) |
| Projecção | `plan_runner/office.py → project()` | `events.jsonl` dos runs → estado por agente, lugar e departamento |
| Snapshot | `python -m plan_runner.office --project RUN_DIR...` | JSON que a UI lê (§5) |
| Testes | `runner/tests/test_office.py` | Validação, cada evento, agregação e 1 run real em stub |

## 2. Regras do mapa

- `departments[].id` = os ids de `config/areas.yaml`, todos, pela mesma ordem.
- Cada agente de `areas[].agents[]` está em **exactamente um** lugar do departamento da sua área: sem órfãos, sem duplicados, sem inventados.
- `lead`: `null` ou um agente do próprio departamento. Só é Lead quem orquestra de facto (hoje só `marketing.marketing`).
- Áreas sem agentes (`legal`, `gamedev`, `docs`) ficam com `seats: []`; a UI mostra "sem agentes ainda".
- Nomes de lugar são **funções** (PESQUISA, QUALIDADE), nunca nomes humanos: quem usa o escritório tem de saber que fala com uma IA (AI Act, art. 50). A UI mostra sempre "agente IA".

## 3. Atribuição de um passo a um agente

1. O evento `step_started` traz a `action` do passo.
2. A `action` resolve-se pelo frontmatter de `agents/**/*.agent.md` (`action:`). A validação exige que cada `action` pertença a **um só** agente.
3. `plan_approve` é um gate humano, não trabalho de um agente: não se atribui.
4. Uma `action` sem dono vai para `unattributed` no snapshot. Fica à vista, não desaparece. O teste `test_todos_os_passos_dos_planos_sao_atribuiveis_a_um_agente` garante que hoje todos os planos de `docs/orchestration/` resolvem.

## 4. Evento → estado

Ordem de gravidade (do pior para o melhor): **erro → precisa de ti → a trabalhar → a pensar → à espera**.

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
- **departamento:** o mais grave dos seus lugares; `null` se não tiver lugares.

## 5. Snapshot

```json
{
  "version": 1,
  "generated_at": "…",
  "states": ["error", "needs", "working", "thinking", "idle"],
  "departments": [
    {"id": "marketing", "name": "Marketing", "lead": "marketing.marketing", "agent_count": 57, "state": "needs",
     "seats": [{"id": "marketing-qualidade", "name": "QUALIDADE", "does": "Revê tudo antes de sair", "state": "needs",
                "agents": [{"id": "marketing.critic_item13", "state": "needs", "run_id": "…", "step_id": "…", "at": "…", "event": "human_gate_requested"}]}]}
  ],
  "unattributed": []
}
```

**Privacidade:** o snapshot só leva metadados (ids, estado, hora, tipo de evento). Nunca leva o objectivo do plano, payloads, conteúdos ou nomes de clientes. Isto conta sobretudo para o Jurídico (sigilo profissional da OA e RGPD).

## 6. Próximas fases

| ID | Fase | Dono | Bloqueio |
|---|---|---|---|
| OFFICE-A2 | Eventos no Supabase (tabela só de acréscimo + Realtime) para o escritório ao vivo | AMBOS | O SQL em produção e as credenciais do runner são do maestro |
| OFFICE-A3 | Escritório 2D com 3 níveis (empresa → departamento → lugar) a ler o snapshot | CLAUDE | — (começa com snapshots de stub) |
| OFFICE-A4 | Caixa "precisa de ti": aprovar ou recusar gates a partir do escritório, com autenticação e registo de auditoria | AMBOS | Autenticação do escritório por decidir; OFFICE-A2 |
| RUNNER-WHY-1 | O "porquê" de cada passo, aberto a partir do lugar | CLAUDE | — (já no §4) |
| OFFICE-3D-1 | Pele 3D opcional (three.js + `@pixiv/three-vrm`, MIT) sobre o mesmo snapshot | CLAUDE | — |
| OFFICE-VOZ-1 | Voz local em pt-PT, nunca na cloud | AMBOS | Sem candidato confirmado |

Fora de âmbito (decisão de 2026-10-24): humanos fotorrealistas, multijogador, nomes humanos fictícios, voz na cloud e animação de trabalho que não existe.

**Proposta para o OFFICE-A2 (NÃO aplicada; o SQL em produção é do maestro):** tabela `office_events` só com metadados (`id`, `run_id`, `type`, `at`, `step_id`, `agent_id`, `state`), RLS ligado e sem políticas para `anon`/`authenticated` (escreve o runner com a service role; a UI lê por um endpoint do servidor), e entrada na publicação do Realtime. O SQL final vai num ficheiro em `scripts/migrations/`, com query de controlo, no PR do OFFICE-A2.
