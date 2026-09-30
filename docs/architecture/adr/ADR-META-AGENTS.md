# ADR-META-AGENTS — Deliberação entre agentes e entre IAs (meta-agentes)

| Campo | Valor |
|---|---|
| **ID** | ADR-META-AGENTS |
| **Estado** | Aceite (visão registada; **nada implementado**) |
| **Data** | 2026-09-30 |
| **Decisores** | Dev (dono do produto), decisões D1–D3 fechadas pelo Grok; redigido pelo Claude |
| **Relacionados** | D1 ([DECISAO-1](../../audit/DECISAO-1-runtimes.md)), D2 ([DECISAO-2](../../audit/DECISAO-2-maestro.md)), D3 ([DECISAO-3](../../audit/DECISAO-3-memoria.md)), J5 (`config/areas.yaml`), AU-13 (`docs/audit/AUDIT-5-itens.md:30`) |

## 1. Contexto

O objectivo final do sistema é **deliberação**: agentes a discutir decisões de desenho estrutural entre si e, numa **Fase 2**, várias IAs (Claude, Grok, outras), cada uma representada por um agente-maestro, **sem um humano a fazer de pombo-correio** entre conversas.

Hoje:
- a deliberação existe só no TS e **bloqueia todos os pedidos**. O `Orchestrator` passa critérios em escala 0–1 (`packages/core/src/orchestrator/Orchestrator.ts:252-259`) a um motor que pontua em 0–10 (`packages/core/src/governance/DeliberationEngine.ts:31`), e tudo cai em TACTICAL/HITL (AU-13, `docs/audit/AUDIT-2-cadeia.md`, Q1);
- o `ArchitectureCouncil` (`packages/core/src/governance/ArchitectureCouncil.ts:33`, 249 linhas) é órfão: só é alcançável pelo ramo `STRATEGIC`, que nunca é atingido (`docs/audit/AUDIT-4-modulos.md:90,129`);
- D1 fixou o núcleo em Python (`runner/plan_runner`). O TS fica arquivado, não apagado.

## 2. Decisão

1. **Fase 1 — deliberação interna.** Ligar a deliberação entre agentes internos **reimplementando** no `plan_runner` (Python) as ideias do `DeliberationEngine` e do `ArchitectureCouncil`. **Não** é um *drop-in* do TS: portam-se os critérios e o protocolo, não o código nem a escala partida.
2. **Fase 2 — deliberação multi-IA.** Os mesmos protocolos, com participantes de `kind: external_ai` (campo introduzido em T2.3, ver `agents/README.md`). O agente-maestro de cada IA é um agente registado como os outros.
3. **Modo, forma e participantes** (T1.3; o Dev não respondeu, por isso executam-se as recomendadas A/A/A):
   - **Modo = assistido.** O Dev aprova o commit final.
   - **Forma = conselhos por tipo de decisão** (architecture, security, product).
   - **Participantes da Fase 2 = misto** (agentes internos + IAs externas).

## 3. Alternativas consideradas

| Nuance | Opção | Prós | Contras |
|---|---|---|---|
| Modo | **B — autónomo** | Zero fricção; o objectivo "sem pombo-correio" fica cumprido por inteiro | Decisões estruturais sem humano; sem ledger de tokens nem HITL durável, o erro e o custo acumulam sem ninguém ver |
| Modo | **C — híbrido** (assistido nas estruturais, autónomo nas operacionais) | Menos aprovações | Exige uma classificação fiável de "estrutural vs operacional", que não existe; o `DeliberationEngine` actual erra essa classificação (AU-13) |
| Forma | **B — conselho único global** | Um só protocolo, simples | Tudo compete pelo mesmo quórum; perde-se a especialização (segurança ≠ produto) |
| Forma | **C — global + sub-conselhos por área** | Máxima cobertura | Duas camadas de quórum e de custo antes de haver sequer uma a funcionar |
| Participantes | **B — só IAs externas** | Diversidade máxima de modelos | Perde o contexto interno (agentes com prompt e grounding do repo); custo por decisão mais alto |
| Participantes | **C — só internos; externas como consultoras sem voto** | Controlo total e custo previsível | Não cumpre a visão da Fase 2 (as IAs não deliberam, só opinam) |

## 4. Consequências

**Positivas**
- A visão fica registada antes do código: nenhum trabalho futuro a contradiz sem um ADR novo.
- O schema fica preparado: o campo `kind` já existe em todos os agentes (T2.3), com `internal` por omissão.

**Negativas / obrigações**
- **Os tokens podem explodir em multi-IA.** N participantes × 3 estágios × rondas. Por isso o **ledger de tokens (J6) é obrigatório antes da Fase 2**.
- **HITL obrigatório** em decisões estruturais, coerente com o modo assistido.
- Reimplementar em Python custa mais do que reactivar o TS; é o preço da D1.

## 5. Protocolo a extrair (não adoptar como stack)

- **`karpathy/llm-council`.** Extrai-se só o protocolo de 3 estágios:
  1. **parallel** — cada participante responde sozinho, sem ver os outros;
  2. **blind peer** — cada um critica as respostas anonimizadas dos outros;
  3. **chairman** — síntese final com *dissent* explícito + próximo passo.

  Não se adopta o stack do repo.
- **Infra de fluxo: LangGraph.** Já é usado no `plan_runner` (`runner/requirements-langgraph.txt:3`; `runner/plan_runner/langgraph_engine.py:12`).
  - **Nota do auditor `[ACRESCENTADO PELO AUDITOR]`:** hoje os checkpoints são **SQLite** (`langgraph-checkpoint-sqlite`, `runner/requirements-langgraph.txt:4`; `langgraph_engine.py:223-224`), não Postgres. Passar a `langgraph-checkpoint-postgres` (checkpoints duráveis partilhados) é **trabalho futuro**, não algo que já existe.

## 6. Não-objectivos

- **Não** substitui o Orchestrator/maestro (D2: router hierárquico sobre `config/areas.yaml`).
- **Não** é um orquestrador paralelo: a deliberação é um **passo** que o maestro invoca, não uma segunda porta de entrada.
- **Não** se implementa antes de três condições: (1) motor mínimo a correr (worker `external` + Gemini, `docs/audit/DECISAO-4-ordem.md` §4.1, via A); (2) AU-13 resolvido quando se ligar a deliberação; (3) conselho **interno** a funcionar. A Fase 2 vem só depois disto **e** do ledger J6.

## 7. Notas de desenho `[ACRESCENTADO PELO AUDITOR]`

- **`kind: meta` ≠ `layer: 'meta'`.** O `layer` do TS (`packages/shared/src/types/agent.ts:4`) é a camada de orquestração. `kind` é a natureza do participante (`internal` | `external_ai` | `meta`). São eixos diferentes; os 4 agentes com `layer: 'meta'` em `config/agents.config.ts` ficam com `kind: 'internal'`.
- **O `kind` vai no agente, não na área** (regra aceite). Uma área pode misturar agentes internos e IAs externas.

## 8. Referências internas

- [`docs/audit/PLANO-DE-ACAO.md`](../../audit/PLANO-DE-ACAO.md): porta de entrada da auditoria.
- [`docs/audit/AUDIT-6-lacunas.md`](../../audit/AUDIT-6-lacunas.md) §6.4: repositórios e ferramentas a ligar, por área.
- [`docs/audit/DECISAO-1-runtimes.md`](../../audit/DECISAO-1-runtimes.md) e [`docs/audit/DECISAO-2-maestro.md`](../../audit/DECISAO-2-maestro.md).
- [`ADR-DB-PLAN-B.md`](./ADR-DB-PLAN-B.md): onde vivem os checkpoints e a memória, se o Supabase free deixar de servir.
- `config/areas.yaml`: registo de áreas v1 (J5).
