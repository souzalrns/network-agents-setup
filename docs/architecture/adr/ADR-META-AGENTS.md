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

---

> **Secções 9–13 acrescentadas em 2026-09-30.** Tudo o que está abaixo é **desenho**. Nenhuma linha de runtime foi escrita.

## 9. Estrutura em 4 camadas de controlo (C0–C3)

> **Convenção (E13):** C = Control layers (metacontrolo); L = Memory layers (L0–L6, `docs/architecture/memory/layers.md:1`).

| Camada | Papel | Quem |
|---|---|---|
| **C0 — HUMANO (HITL)** | Aprova, veta ou clarifica | Dev |
| **C1 — META (controlo)** | Router de área + chairman/moderator + trust/quorum | Meta-agentes (`kind: meta`, reservado) + router sobre `config/areas.yaml` |
| **C2 — CONSELHO (deliberação)** | Participantes + protocolo (secção 11) | Membros `kind: internal` \| `external_ai` |
| **C3 — EXECUÇÃO (objecto)** | Faz o trabalho | `runner/plan_runner` + tools + ledger de tokens (J6) |

**L4 (memória) atravessa todas as camadas de controlo.** Um veredicto nasce `candidate` e só é consolidado depois do gate e do HITL.

O contrato da L4 chama `active` ao estado consolidado, não `committed`: `"status": { "enum": ["candidate", "active"], "default": "candidate" }` em `docs/architecture/memory/contracts.md:29`. Neste ADR, "committed" = `active` do contrato. Ver E14 em `docs/audit/PLANO-DE-ACAO.md` §13.2.

**Regra de encaminhamento:**
- **Pedido normal** → C1 router → C3. Sem conselho.
- **Pedido estrutural, de alta incerteza, ou de uma área com `hitl: required`** (`config/areas.yaml`: legal, finance, security) → C1 abre conselho (C2) → veredicto `candidate` → C0 → L4 (`candidate` → `active`) → C3, se houver acção.

**Colisão de nomes resolvida (E13, 2026-09-30).** Estas camadas chamavam-se L0–L3 e colidiam com as camadas de memória L0–L6. Passaram a C0–C3; "L4" nesta secção é sempre a camada de memória.

## 10. Distinção meta vs. domínio

- **Meta-agente ≠ "agente mais inteligente".** É uma **camada de controlo** (C1): decide *quem* delibera e *quando* se fecha, não *o quê*.
- **Meta:** chairman, moderator, router-agent (futuro). `kind: meta`, **não usado hoje** (secção 7).
- **Domínio:** executa a tarefa (security, finance, marketing…). `kind: internal`.
- **Clarificação: o `security_auditor` NÃO é um meta-agente.**
  - Vive em `agents/meta/` por razões históricas (`agents/meta/security_auditor.agent.md`), mas no registo é um **especialista C3** da área `security` (`config/areas.yaml`, área `security`).
  - Tem `kind: internal`.
  - Um *Security Council* na Fase 1 pode incluí-lo como membro **`required`** (com veto), com um chairman meta **separado**.

## 11. Protocolo em estágios (Fase 1)

| # | Estágio | O que faz | LLM? |
|---|---|---|---|
| 1 | **INDEPENDENT** | Cada membro responde sem ver os outros | Sim (1 chamada por membro) |
| 2 | **PEER_RANK** | *Ranking* anónimo das respostas dos outros (contra a bajulação) | Sim (1 por membro) |
| 3 | **SYNTHESIZE** | O chairman produz o `Verdict` (decisão + *dissent* + próximo passo + `confidence`) | Sim (1) |
| 4 | **GATE** | `confidence ≥ τ` **e** regras de veto (um membro `required` que vete bloqueia) | **Não**: determinístico |
| 5 | **HITL** | O humano aprova, revê ou rejeita | Não |
| 6 | **PERSIST** | L4 `candidate` → `active` + registo no ledger | Não |

**Custo por ronda** = 2·N + 1 chamadas LLM (N = membros). Por isso o ledger J6 é pré-requisito (secção 4) e `max_rounds` é obrigatório por painel (secção 13).

## 12. Esboço do `CouncilSession` (LangGraph) — SÓ DESENHO

> **DESENHO. NÃO IMPLEMENTAR** antes de AU-13 + motor mínimo + Bloco A (J1–J11, `docs/audit/DECISAO-4-ordem.md` §4.4). Implementação agendada: J5-c, PLANO §13.2.
>
> **Proveniência `[ACRESCENTADO PELO AUDITOR]`.** O brief pede para "transcrever o esboço já produzido". Esse esboço **não existe em nenhum ficheiro** deste repo nem do `agent-network-mcp` (procura por `CouncilState`/`CouncilSession`/`councils.yaml`: 0 resultados). O que está abaixo foi **reconstituído a partir da especificação do brief**: `CouncilState`, a topologia, *reducers* com `operator.add` e `interrupt()` para HITL. Se o Dev tiver o original, substitui-se (E15).

```python
# DESENHO — não é código do repo. Nomes indicativos.
import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt  # já usado em runner/plan_runner/langgraph_engine.py:79,99


class Answer(TypedDict):
    member_id: str
    kind: Literal["internal", "external_ai"]
    content: str


class Rank(TypedDict):
    ranker_id: str
    order: list[str]          # ids anonimizados, melhor → pior


class Verdict(TypedDict):
    decision: str
    dissent: list[str]
    next_step: str
    confidence: float         # 0..1 — atenção à lição do AU-13 (escalas)


class CouncilState(TypedDict):
    council_id: str           # ex.: "architecture" (councils.yaml)
    question: str
    members: list[str]
    round: int
    answers: Annotated[list[Answer], operator.add]   # reducer: acumula por membro
    ranks: Annotated[list[Rank], operator.add]
    verdict: Verdict | None
    gate: Literal["pass", "veto", "low_confidence"] | None
    human: Literal["approve", "revise", "reject"] | None
    tokens: Annotated[list[int], operator.add]        # alimenta o ledger (J6)


def assemble(s: CouncilState) -> dict: ...     # lê councils.yaml; resolve membros e τ
def independent(s: CouncilState) -> dict: ...  # N respostas, cada uma sem ver as outras
def peer(s: CouncilState) -> dict: ...         # ranking anonimizado
def synthesize(s: CouncilState) -> dict: ...   # chairman → Verdict
def gate(s: CouncilState) -> dict: ...         # determinístico: confidence ≥ τ e sem veto de required


def hitl(s: CouncilState) -> dict:
    return {"human": interrupt({"verdict": s["verdict"], "gate": s["gate"]})}


def persist(s: CouncilState) -> dict: ...      # L4 candidate → active (só se approve) + ledger


def after_hitl(s: CouncilState) -> str:
    return "independent" if s["human"] == "revise" else "persist"   # max_rounds limita o ciclo


g = StateGraph(CouncilState)
for name, fn in [("assemble", assemble), ("independent", independent), ("peer", peer),
                 ("synthesize", synthesize), ("gate", gate), ("hitl", hitl), ("persist", persist)]:
    g.add_node(name, fn)
g.add_edge(START, "assemble")
g.add_edge("assemble", "independent")
g.add_edge("independent", "peer")
g.add_edge("peer", "synthesize")
g.add_edge("synthesize", "gate")
g.add_edge("gate", "hitl")                 # veto/low_confidence também vão ao humano, marcados
g.add_conditional_edges("hitl", after_hitl, ["independent", "persist"])
g.add_edge("persist", END)
# compile(checkpointer=...) — ver nota de dependência abaixo
```

**Nota de dependência.** O checkpointer hoje é **SQLite** (`runner/requirements-langgraph.txt:4`; `runner/plan_runner/langgraph_engine.py:224`). O `langgraph-checkpoint-postgres` só entra quando houver **multi-instância** (mais de um processo a retomar a mesma sessão). **Não é "já usado".**

## 13. `councils.yaml` v0 — config de painéis (NÃO criado agora)

> **Este ficheiro NÃO é criado agora.** A criação é o item J5-b e o local é o E12 (recomendado: `config/councils.yaml`), ambos no PLANO §13.2.
>
> **Proveniência:** o exemplo "já produzido" também **não existe em ficheiro**. Foi reconstituído a partir do brief (painéis architecture, security, product; campos chairman, members, required, max_rounds, confidence_threshold). Os IDs são os reais de `config/areas.yaml`. O chairman é um ID **futuro** (`kind: meta`) que ainda **não existe**.

```yaml
# councils.yaml v0 — EXEMPLO (não existe no repo)
version: 0
councils:
  - id: architecture
    chairman: meta.chairman            # futuro (kind: meta) — não existe
    members: [meta.arquitetura-agentes, engenharia.desenvolvimento, engenharia.revisor-codigo, meta.planejador]
    required: [meta.arquitetura-agentes]
    max_rounds: 2
    confidence_threshold: 0.7

  - id: security
    chairman: meta.chairman            # separado do auditor (secção 10)
    members: [meta.security-auditor, engenharia.revisor-codigo, engenharia.desenvolvimento]
    required: [meta.security-auditor]  # com veto
    max_rounds: 2
    confidence_threshold: 0.8

  - id: product
    chairman: meta.chairman
    members: [produto.produto-tech-transversal, design.ux, marketing.marketing, gestao.gestao-empresarial]
    required: []
    max_rounds: 1
    confidence_threshold: 0.6
```
