# Análise competitiva — planwright + plan_runner vs. o mercado (2026-10)

O passo C da Fase 4: agora que a composição está **provada** (contrato #164,
cenário canónico #165, sinais lidos #166, matriz 100% — `CAPABILITY-MATRIX-PLANWRIGHT.md`),
responder com honestidade: *perante as alternativas, escolheríamos isto?* E onde
**não** competimos. Para enviar ao GPT/Grok e afinar o posicionamento.

> Método: comparo por **categoria** (o que cada coisa É), não feature-a-feature
> entre coisas diferentes. Números de estrelas/tamanho são de directórios de
> terceiros (Out/2026) — indicativos, a confirmar no repo de cada um.

## O mapa: três categorias, não uma

| Categoria | O que é | Exemplos | O que planwright/plan_runner faz aqui |
|---|---|---|---|
| **Framework de agentes** | SDK para *construir* agentes (runtime, memória, tools, multi-provider, observabilidade) | **VoltAgent** (TS, MIT, supervisor multi-agente, tools tipadas com Zod, MCP, consola VoltOps) | não competimos — não somos um SDK de runtime |
| **Coleção de personas/subagentes** | Biblioteca de *definições* de agentes (markdown: papel, quando invocar, modelo) | **wshobson/agents** (~194 agentes, 88 plugins, 158 skills, model-tiered Haiku/Sonnet/Opus), **contains-studio/agents** | não competimos — não somos uma biblioteca de personas |
| **Orquestrador de execução paralela** | Correr N agentes em paralelo (worktrees git isolados, tracks, quality gates) | **Conductor** (app Mac, Melty Labs), **code-conductor** (CLI OSS), **Conductor Orchestrator** (plugin Claude Code) | parcialmente — mas o nosso foco é *governar*, não paralelizar |

**planwright + plan_runner é uma quarta categoria:** a **disciplina de planeamento
determinística** (plano-como-dados + caminho crítico calculado + hook que impede
o plano de apodrecer) mais o **contrato de execução governada** (HITL + tecto de
orçamento + `done_when` por evidência, *provado por testes*). Não é o runtime do
agente nem a biblioteca de personas — é a **camada que torna qualquer um deles
responsável**.

## Onde os rivais ganham (honesto, sem vender)

- **VoltAgent** tem um runtime multi-provider a sério (OpenAI/Anthropic/Google),
  tools tipadas, e uma consola de observabilidade (VoltOps). Nós temos um worker
  único (Gemini) e um log `events.jsonl`. Em *runtime de produção genérico*, o
  VoltAgent é mais completo.
- **wshobson/agents** tem amplitude e ecossistema que não temos: ~194 personas de
  domínio, skills e comandos, dezenas de milhares de estrelas, instalável pelo
  sistema de plugins do Claude Code. Em *catálogo de especialistas prontos*, ganha.
- **Conductor** tem UX de paralelismo polida (worktrees isolados, app nativa). Em
  *tocar 5-10 agentes ao mesmo tempo com bom DX*, ganha; nós somos CLI.

Não competimos em amplitude, polimento de produto, nem ecossistema/estrelas.

## Onde nós ganhamos (com evidência, não marketing)

| Diferencial | Porquê é nosso | Evidência no repo |
|---|---|---|
| **Plano-como-dados, zero-dep, sem lock-in** | um ficheiro Markdown em git que a equipa já possui; nada de runtime | `oss/planwright/` (0 deps), `POSITIONING.md` |
| **Horário determinístico** | *ready / paralelo / caminho crítico* são **factos** calculados, não o palpite de um modelo | `planwright/graph.py` · `tests/` (53) |
| **Disciplina imposta** | um hook **bloqueia** um plano com ciclo/dependência pendente — nenhuma persona faz isto | hook `PostToolUse` · `test_hook*` |
| **Execução governada provada** | HITL + tecto de orçamento + `done_when` por evidência, **num só run** | cenário canónico: `runner/tests/test_canonical_composition.py` (#165) |
| **Composição sem acoplar** | `export`→`import` contratual; sinais (`complexity`/`autonomy`) lidos pela selecção | `docs/architecture/PLAN-CONTRACT.md` (#164), seleção por sinal (#166) |
| **Fronteira honesta** | planeamento ≠ execução; sinais ≠ política de runtime; nada é imposto que o runner recusaria | `POSITIONING.md`, `PLAN-CONTRACT.md` |

A diferença de fundo: os rivais são **personas** (prompts) ou **frameworks**
(runtime) ou **paralelizadores** (DX). Nenhum entrega *disciplina determinística
+ governação verificável + portabilidade zero-dep*. O "agente PM" típico é um
persona sem estado — produz um plano e esquece-o; nós invertemos isso (fonte de
verdade em ficheiro, horário calculado, disciplina imposta por hook).

## Comparação directa (a tabela da POSITIONING, alargada)

| | persona PM (VoltAgent-as-PM, contains-studio) | wshobson (personas) | Conductor (paralelo) | **planwright + plan_runner** |
|---|---|---|---|---|
| Fonte de verdade do plano | nenhuma (efémera) | nenhuma | worktrees/tracks | **1 ficheiro Markdown em git** |
| Caminho crítico / paralelismo calculado | não | não | não | **sim, determinístico** |
| Impõe disciplina (bloqueia plano insano) | não | não | quality gates (próprias) | **sim (hook)** |
| Porta humana + tecto de orçamento + conclusão por evidência | não | não | parcial/ad-hoc | **sim, provado (1 run)** |
| Dependências de runtime | SDK | Claude Code | app/CLI | **zero (planwright)** |
| Lock-in | ao SDK | ao Claude Code | à app | **mínimo (1 ficheiro)** |
| Reutilizável por qualquer agente/CI/humano | via SDK | Claude Code | — | **CLI + lib + plugin + contrato** |

## Veredicto — escolheríamos isto?

**Sim, para o que ele é — e com honestidade sobre o que não é.** Não é um
substituto do VoltAgent (framework) nem do wshobson (personas); é a **camada de
disciplina e governação** que falta a ambos. O posicionamento vencedor não é
"mais um framework de agentes" (perdíamos) — é **"a maneira de tornar os teus
agentes responsáveis": plano determinístico que não apodrece + execução com
porta humana, orçamento e prova por evidência, sem lock-in."**

Isto também é **complementar, não rival**: podes correr personas do wshobson,
manter o plano honesto com planwright, e gatear/orçamentar/verificar com o
plan_runner. O único que batemos de frente é o "persona PM sem estado".

## Recomendação (regra A/B/C)

Como afinar o posicionamento a partir daqui:

- **A) Dobrar na governação como diferencial** — levar a mensagem "accountability
  layer" ao README/POSITIONING e ao primeiro release PyPI (badges + o cenário
  canónico como demo). **RECOMENDADA.** Razão: é o único quadrante onde ganhamos
  com evidência (os testes do #165), e é o que o mercado de frameworks/personas
  *não* tem. Evidência: esta análise + a matriz 100%.
- **B) Interop com os rivais** — um adaptador para importar personas do wshobson
  como passos de um plano planwright (amplitude emprestada). Útil, mas é trabalho
  novo e dilui o foco antes de termos tracção.
- **C) Competir em amplitude** — construir a nossa biblioteca de personas.
  **Não recomendado**: perdemos para quem tem 194 agentes e 37k estrelas; não é
  o nosso quadrante.

Recomendo **A**: afinar a narrativa de *accountability* e prová-la no 1.º publish
(XP1), em vez de competir onde os outros já ganharam.

## Fontes (Out/2026, a reconfirmar)

- VoltAgent — <https://github.com/voltagent>
- wshobson/agents — <https://www.sourcepulse.org/projects/11025561> ; panorama: <https://dev.to/voltagent/100-claude-code-subagent-collection-1eb0>
- Conductor (Melty Labs) — <https://www.morphllm.com/conductor-ai-coding> ; code-conductor — <https://github.com/ryanmac/code-conductor>
- Padrão "conductor → orchestrator" (Addy Osmani) — <https://addyosmani.com/blog/future-agentic-coding/>
