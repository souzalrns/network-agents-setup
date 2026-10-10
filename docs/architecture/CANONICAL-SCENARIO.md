# Cenário canónico — a composição planwright → plan_runner, provada

O contrato (`PLAN-CONTRACT.md`) tornou a composição **viável**. Este cenário
torna-a **provada**: um único plano que percorre todo o caminho — da tabela
planwright à execução governada — e exercita, num só run, as três garantias que
distinguem o `plan_runner` de "um modelo que escreve um plano bonito":

1. **porta humana (HITL)** — o run pausa à espera de uma decisão;
2. **tecto de orçamento** — o run pausa quando gasta o que lhe foi dado;
3. **`done_when` por evidência** — o run só fica `done` se a prova existir (ficheiros + o gate resolvido), não por "os passos correram".

É a última linha da `CAPABILITY-MATRIX-PLANWRIGHT.md` (critério 10 + a linha
"integrar"): a composição deixa de ser uma afirmação e passa a ser um teste.

## Os ficheiros

| Papel | Ficheiro |
|-------|----------|
| Plano planwright (a fonte humana) | `oss/planwright/examples/composicao-canonica.PLAN.md` |
| Plano executável (completado do esqueleto) | `docs/architecture/plan-execute/examples/composicao-canonica.plan.yaml` |
| A prova (execução) | `runner/tests/test_canonical_composition.py` |
| A prova (export) | `oss/planwright/tests/test_export.py::test_canonical_plan_exports_the_expected_contract` |

## O caminho, comando a comando

### 1. planwright descreve e prioriza

```bash
cd oss/planwright
PYTHONPATH=src python3 -m planwright.cli graph examples/composicao-canonica.PLAN.md
```

```
plan: 4 items  (todo 4, doing 0, blocked 0, done 0)
READY NOW (1): research
CRITICAL PATH: 7h — research -> decide -> draft -> finalize
```

O item `decide` é `Autonomy=human`: a planwright marca-o como ponto de decisão.

### 2. Export → o contrato `planwright-plan/v1`

```bash
PYTHONPATH=src python3 -m planwright.cli export examples/composicao-canonica.PLAN.md > contract.json
```

Emite um item por linha, com `id, title, status, owner, estimate_hours, depends,
track, autonomy, complexity`. `autonomy`/`complexity` viajam como **sinais**,
nunca como política de runtime.

### 3. Import → o esqueleto do runner

```bash
cd ../../runner
PYTHONPATH=. python3 -m plan_runner.plan_import ../oss/planwright/contract.json \
  --id composicao-canonica --validate
```

Produz um plano **schema-válido** (`plan.schema.json`), mas um **esqueleto** — a
planwright não conhece as *actions* do runner:

```json
{
  "id": "composicao-canonica",
  "steps": [
    {"id": "research", "action": "discovery", "task": "Levantar requisitos e contexto"},
    {"id": "decide", "action": "governance", "task": "Aprovar o rumo antes de investir",
     "depends_on": ["research"], "human_gate": true},
    {"id": "draft", "action": "build", "task": "Redigir a proposta", "depends_on": ["decide"]},
    {"id": "finalize", "action": "build", "task": "Consolidar e publicar o resultado", "depends_on": ["draft"]}
  ]
}
```

Repare: `autonomy=human` em `decide` virou `human_gate: true`; `track` virou o
`action` *placeholder*.

### 4. Um humano/router completa o esqueleto no plano executável

O que o esqueleto **traz** (id, task, depends_on, human_gate) fica. O que um
humano ou o router **acrescenta** (marcado `[+]` no YAML) é tudo o que o contrato
deliberadamente **não** carrega:

| Campo | Esqueleto | Plano executável | Porquê não vem no contrato |
|-------|-----------|------------------|-----------------------------|
| `action` | `discovery`/`governance`/`build` (do track) | `research`/`plan_approve`/`research` | a escolha da *action* real é do router/humano |
| `objective` | — | a frase do run | contexto de execução, não de planeamento |
| `budget.max_tokens` | — | `1500` | orçamento é política de runtime (fica no runner) |
| `output_artifact` | — | `artifacts/NN-*.{md,json}` | onde o output vive é do executor |
| `human_gate` | `true` | objecto `{level, kind, allow}` | a planwright dá a *intenção*; a HITL do runner é a autoridade |
| `done_when` | — | evidência (ficheiros + gate) | verificação de conclusão é do runner |

### 5. O runner executa, com governação

```bash
PYTHONPATH=. python3 -m plan_runner run \
  ../docs/architecture/plan-execute/examples/composicao-canonica.plan.yaml \
  --mode external --worker gemini --max-tokens 1500 --out ../pilots/canon
```

O que acontece, num único run:

1. `research` corre (955 tokens; 0 < 1500).
2. `decide` tem porta humana → **PAUSA** em `paused_human_gate`. Escreve `HITL.md`.
   Retomar: `python -m plan_runner resume ../pilots/canon --decision approve`
3. a decisão fecha `decide` (grava `artifacts/02-decision.json` e o evento
   `human_gate_resolved`); `draft` corre (955; 1910 total).
4. `finalize` bate no tecto (1910 ≥ 1500) → **PAUSA** em `paused_budget`. Escreve `BUDGET.md`.
   Retomar: `python -m plan_runner resume ../pilots/canon --max-tokens 5000`
5. `finalize` corre; o `done_when` é verificado **por evidência** — os dois
   ficheiros existem e `decide` foi resolvido → o run fica `done`.

Tirar qualquer prova (ex.: apagar `artifacts/02-decision.json` antes do fim) faz
o run terminar em `failed` com `detail: done_when`, não em `done`.

## O que isto prova (e o que não)

- **Prova:** planwright e plan_runner compõem de ponta a ponta sem acoplar; o
  plano executável é uma completação fiel do esqueleto do contrato (mesmos ids,
  dependências e porta); as três garantias de governação funcionam juntas no
  mesmo run; a conclusão é por evidência verificável.
- **Não prova** (nem tenta): execução real com um LLM a sério (o Gemini é falso
  no teste, de propósito — determinista e sem rede); a escolha automática de
  `action`/`model_tier` a partir dos sinais `complexity`/`autonomy` (a linha
  "integrar" da matriz, o próximo passo para lá deste cenário).

## Correr a prova

```bash
# execução (runner): 4 testes
cd runner && PYTHONPATH=. python3 -m pytest tests/test_canonical_composition.py -v
# export (planwright): a outra ponta
cd oss/planwright && PYTHONPATH=src python3 -m pytest tests/test_export.py -v
```
