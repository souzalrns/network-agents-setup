# Autonomous candidates — o inventário de repos extraíveis

> Inventário dos candidatos a repo autónomo (pacote OSS pluggable) que já vivem
> dentro do `plan_runner`. Cada linha é **evidência** (`file:line` / LOC reais),
> não opinião — o critério do playbook (`REPO-EVAL-PLAYBOOK.md`, §Prime directive).
> Avaliado em `main` `f72ec6c`. Companheiro de `CAPABILITY-MATRIX-AUTONOMOUS.md`
> (os 3 já feitos) e `CAPABILITY-MATRIX-PLANWRIGHT.md` (o kernel).

## Para que serve este inventário

A pergunta do maestro — **"o conceito deve ser tudo plugin"** — quer dizer: o que
no runner é, na verdade, um módulo de propósito único que podia viver sozinho,
ser testado sozinho, e ser a escolha recomendada na sua categoria? Este documento
responde com uma lista fechada de **19 itens**, cada um com nome, frase, esforço,
diferencial e o que analisar na concorrência antes de extrair.

O método de extração (o *flywheel*) está em `REPO-EVAL-PLAYBOOK.md`, secção
"The flywheel". A regra curta: **extrair não é perder tempo — é investigar o
concorrente, endurecer o módulo com o que se aprende, e devolver essa melhoria ao
`plan_runner`.** Cada extração torna o todo mais forte, não só o pacote.

## Como ler os campos

- **Nome** — o nome do pacote candidato (inglês, como no código).
- **Frase** — o que faz, numa linha.
- **Esforço** — custo de extração: **baixo** (<150 LOC, baixo acoplamento),
  **médio** (150–350 LOC ou 1 contrato), **alto** (>350 LOC ou acoplamento fundo).
- **Diferencial** — o que o nosso tem que a concorrência tende a não ter.
- **Concorrência** — quem comparar e **o que** verificar com evidência (não README).

Grupos: **Publicados (3)** · **Fortes (5, prioridade)** · **Médios (5)** · **Não
extrair (6, o núcleo)**.

---

## Prioridade (a ordem de ataque)

Os 5 **fortes** primeiro (maior valor de portfólio / menor esforço / diferencial
claro), depois os médios. Os 3 já **publicados** (no PyPI) só evoluem. O núcleo
não se extrai.

| Ordem | Candidato | Grupo | Esforço | Porquê esta posição |
|-------|-----------|-------|---------|----------------------|
| **1** | **doneproof** | forte | baixo | diferencial puro (aceitação por **evidência**), 83 LOC, quase zero acoplamento — o melhor rácio valor/esforço |
| **2** | **safe-fetch** | forte | baixo-médio | segurança (SSRF + deny-by-default), categoria com procura, política em config |
| **3** | **hitl-gate** | forte | médio | já tem contrato versionado (`hitl-request-v1.json`); aprovações **tipadas** é raro |
| **4** | **token-budget** | forte | médio | guarda **projectiva** (pausa ANTES da chamada) — a concorrência mede *depois* |
| **5** | **groundeval** | forte | — (RE1=B) | decidido **não** extrair como produto (mercado saturado); fica no runner. Ver nota |
| 6 | model-tiers | médio | baixo | pequeno e limpo, mas categoria já ocupada (litellm router) |
| 7 | chunker | médio | baixo-médio | útil, mas concorrência madura (langchain/llama-index splitters) |
| 8 | provenance | médio | baixo-médio | diferencial de *accountability*, mas valor só com o grounding ao lado |
| 9 | tool-executor | médio | alto | valor alto, mas acoplamento fundo ao worker — extrair tarde |
| 10 | skill-activation | médio | alto | idem; depende do `agentic-skills-manager` e do SEC-1.3 |

> Nota groundeval: está na lista dos **fortes** como *capacidade*, mas a decisão
> RE1 (`RE1-RAG-EVAL-DECISION.md`) é **B = no-go como produto** — o mercado
> (ragas/deepeval/promptfoo) está ganho e o nome `rag-eval` está ocupado. Fica no
> runner, onde o diferencial (proveniência ligada ao pipeline governado) existe.
> Revisitar só com procura concreta.

---

## Publicados (3) — extraídos e no PyPI

Detalhe e scorecard em `CAPABILITY-MATRIX-AUTONOMOUS.md`. Estado no PyPI verificado
com `pip index versions` (2026-10-11): **planwright 0.3.0**, **skill-scout 0.1.0**,
**auditron 0.1.0**. Nota: o `oss/planwright/pyproject.toml:7` já está em `0.4.0`
(views `gantt`/`load`/`cost` do #172) — falta a tag `planwright-v0.4.0` para o PyPI
apanhar essa versão; os pacotes **estão publicados**, não "à espera de PyPI".

### 1. planwright — *motor determinístico de planeamento*
- **Frase:** plano como dados (tabela Markdown) → ready/parallel/critical-path,
  validação, export/import; zero dependências.
- **Esforço:** feito (`oss/planwright/`, 48 testes, CI). **PyPI: 0.3.0 publicado**
  (local em 0.4.0; falta a tag).
- **Diferencial:** zero-dep + contrato `planwright-plan/v1` que o `plan_runner`
  importa; separa *descrever o plano* de *executá-lo*.
- **Concorrência:** ver `CAPABILITY-MATRIX-PLANWRIGHT.md` (os 10 critérios).

### 2. skill-scout — *gestão segura de skills (pre-trust + ciclo de vida)*
- **Frase:** vetta skills de terceiros antes de um agente confiar nelas (scan +
  SARIF + aprovação presa ao hash + lockfile).
- **Esforço:** feito (`oss/skill-scout/`, ~169 testes, CI próprio). **PyPI: 0.1.0
  publicado.**
- **Diferencial:** aprovação recusada a agentes de IA (só humano), pin sha256,
  ~80 alvos de agente.
- **Concorrência:** `CAPABILITY-MATRIX-AUTONOMOUS.md` §1. Gap real: sandbox de
  runtime (SKILL-SCOUT-2).

### 3. auditron — *gate defensivo de segurança (SCA + SAST + workflow)*
- **Frase:** um só gate que orquestra `pip-audit` + `bandit` + `zizmor` num
  modelo e SARIF comuns, com uma política e um exit code.
- **Esforço:** feito (`oss/auditron/`, 25 testes, CI próprio). **PyPI: 0.1.0
  publicado.**
- **Diferencial:** orquestrador honesto (não reinventa engines); pluggable em
  qualquer repo sem alterações.
- **Concorrência:** `CAPABILITY-MATRIX-AUTONOMOUS.md` §2.

---

## Fortes (5) — a prioridade

### 4. doneproof — *aceitação por evidência* ✅ EXTRAÍDO (1ª volta do flywheel)
- **Estado:** **extraído** para `oss/doneproof/` (pacote `doneproof`, nome escolhido
  pelo maestro 2026-10-11; ex-`done-when`; 16 testes, CI `doneproof.yml`, publish
  `publish-doneproof.yml`). Falta a tag `doneproof-v0.1.0` para o PyPI (passo do
  maestro). O runner devolve-lhe o seam (`gate_resolved`): ver
  `runner/plan_runner/done_when.py` (`_evaluate`); o módulo do runner mantém o nome
  `done_when` (o campo `done_when:` do plano), só o pacote se chama `doneproof`.
- **Frase:** confirma que um passo acabou verificando **evidência objectiva**
  (um ficheiro existe / um gate humano foi resolvido), não "o agente disse que acabou".
- **Esforço:** **baixo** — `done_when.py` (83 LOC), reconhece só 2 formas
  verificáveis sem interpretar texto livre; acoplamento quase nulo.
- **Diferencial:** a maioria dos frameworks aceita a auto-declaração do agente
  (`status: done`). O nosso **recusa** o que não tem prova. É o critério 7 do
  playbook ("validação por evidência") num pacote.
- **Concorrência a analisar:**
  - `DeepEval`, `guardrails-ai`, `openai-evals`, `ragas` — medem *qualidade da
    resposta*, não *aceitação de tarefa*. Verificar: algum confirma conclusão por
    artefacto/exit-code, ou só por score de LLM-as-judge?
  - CI gates (pytest, `test ... && exit`) — verificar se alguém empacota isto
    como *primitiva de aceitação de tarefa de agente* reutilizável (provável nicho
    vazio → o nosso diferencial).

### 5. token-budget — *orçamento e ledger de tokens com guarda projectiva*
- **Frase:** ledger de tokens → custo USD por `config/model-prices.yaml`, com um
  tecto que **pausa o run ANTES** de uma chamada que o ultrapassaria.
- **Esforço:** **médio** — `cost.py` (77 LOC) + `token_projection.py` (223 LOC) +
  o `check_budget_projected()` do `external_worker` (countTokens verificado,
  ADR-002).
- **Diferencial:** a concorrência mede custo **depois** (observabilidade); nós
  **impedimos** o estouro com projecção via `:countTokens` real antes de gastar.
- **Concorrência a analisar:**
  - `tokencost`, `litellm` (cost tracking), `langfuse`, `helicone` — verificar: é
    *post-hoc* (dashboard) ou *pre-call* (bloqueia)? Têm tecto **rígido** que
    pausa a execução, ou só alertam?
  - Verificar se a projecção deles usa o `countTokens` oficial do provider ou um
    estimador não-verificado (o nosso risco antigo, hoje fechado no #173).

### 6. hitl-gate — *aprovações humanas tipadas*
- **Frase:** pede uma decisão humana num contrato tipado e versionado, pausa o
  run, e retoma com a decisão registada e auditável.
- **Esforço:** **médio** — `hitl.py` (273 LOC) + o contrato já existe
  (`docs/architecture/hitl/hitl-request-v1.json`), o que facilita a extração.
- **Diferencial:** aprovação **tipada** (schema do pedido e da decisão) com
  retoma — a maioria oferece "interrupt" genérico sem contrato nem auditoria.
- **Concorrência a analisar:**
  - `LangGraph` (interrupts / human-in-the-loop), `Temporal` (signals),
    `Inngest`, `Humanlayer` — verificar: a decisão é **tipada** (schema) ou texto
    livre? É auditável e resumível após reinício? Há contrato versionado?
  - `Humanlayer` é o mais próximo: comparar o nosso contrato v1 com a API deles.

### 7. safe-fetch — *fetch HTTP seguro (allowlist por área, deny-by-default)*
- **Frase:** busca HTTP onde cada área só alcança os domínios que a política
  (`config/web-allowlist.yaml`) permite; lista vazia = não busca nada.
- **Esforço:** **baixo-médio** — `web_allowlist.py` (152 LOC), política em config.
- **Diferencial:** **deny-by-default por área** (política = decisão do maestro),
  pensado contra SSRF num contexto de agente. Raro ter isto como primitiva.
- **Concorrência a analisar:**
  - `requests`/`httpx` crus (sem protecção), libs anti-SSRF (ex. `advocate`),
    ferramentas web de `smolagents`/`langchain` — verificar: bloqueiam IPs
    privados/metadata? Permitem **allowlist por domínio** como política externa?
  - Verificar se alguém junta *allowlist + anti-SSRF + política em ficheiro* num
    só pacote pequeno (provável lacuna → diferencial).

### 8. groundeval — *porta de proveniência / grounding* (RE1 = B)
- **Frase:** avalia o retrieve de um run contra um golden set (provenance_ok,
  source_hit@k, chunk_hit, MRR) e bloqueia regressões.
- **Esforço:** **—** — decidido **não extrair como produto** (RE1 = B). Fica em
  `l5_eval.py` (209 LOC), com o seam `Retrieve` já pluggable (E5 ✅).
- **Diferencial:** `provenance_ok` ligado ao **pipeline governado** (L5 + runner)
  — exactamente o que não viaja para um avaliador genérico.
- **Concorrência a analisar (já feito no RE1):**
  - `ragas`, `deepeval`, `promptfoo`, `trulens` — mercado maduro e saturado; nome
    `rag-eval` ocupado no PyPI. Dossier: `RE1-RAG-EVAL-DECISION.md`.
  - Revisitar **A** (extrair) só com evidência de procura (um utilizador a pedir
    avaliação standalone).

---

## Médios (5) — depois dos fortes

### 9. tool-executor — *executor de tools com deny-by-default*
- **Frase:** executa as tools de um passo com autorização explícita por tool
  (nada corre sem estar permitido), auditável.
- **Esforço:** **alto** — `tool_executor.py` (507 LOC), acoplamento fundo ao
  worker e ao contrato AU-20.
- **Diferencial:** deny-by-default por tool + mapeamento à ISO/IEC 42001.
- **Concorrência a analisar:** `LangChain` tool calling, MCP, `smolagents`,
  function calling da OpenAI, `E2B` — verificar: autorização **por tool** (não
  tudo-ou-nada), sandbox, registo auditável. A maioria confia na tool assim que
  está ligada.

### 10. skill-activation — *activação de skills com allow-list*
- **Frase:** antes do worker correr, resolve agente+skill, inventaria os scripts
  da skill e aplica a allow-list SEC-1.3.
- **Esforço:** **alto** — `skill_activation.py` (531 LOC); depende do
  `agentic-skills-manager` e do contrato SEC-1.3.
- **Diferencial:** inventário de scripts + allow-list **antes** da execução (não
  depois do estrago). Complementa o skill-scout (vetta) com o *activar seguro*.
- **Concorrência a analisar:** `agentic-skills-manager`, Claude Skills, MCP —
  verificar: alguém inventaria e restringe scripts no momento da **activação**?

### 11. provenance — *metadados de proveniência*
- **Frase:** lê e valida o `.meta.yaml` de cada fonte (nada entra no L5 sem
  `source_meta` válido) e converte-o em metadados de citação.
- **Esforço:** **baixo-médio** — `provenance.py` (121 LOC).
- **Diferencial:** gate de *accountability* na ingestão (origem provada antes de
  indexar). Valor real só com o grounding ao lado.
- **Concorrência a analisar:** `W3C PROV`, `OpenLineage`, `sigstore` (artefactos)
  — verificar: fazem gate de **ingestão de knowledge** (RAG) por proveniência, ou
  só linhagem de dados/pipelines? Nicho de agentes provavelmente vazio.

### 12. model-tiers — *mapa papel→modelo*
- **Frase:** resolve o modelo de um passo pelo seu `model_tier`
  (planner/executor/verifier) + sinal de complexidade + disponibilidade.
- **Esforço:** **baixo** — `model_tiers.py` (98 LOC), limpo.
- **Diferencial:** precedência clara (role > sinal complexity > default) +
  degradação por disponibilidade.
- **Concorrência a analisar:** `litellm` router, `OpenRouter`, config de modelos
  do `LangChain` — categoria **já ocupada**. Verificar se o nosso role-based +
  availability acrescenta algo; se não, manter interno (não extrair).

### 13. chunker — *pipeline de indexação (chunking de markdown)*
- **Frase:** parte markdown por secções `##`/`###` auto-contidas (~200–600
  tokens) para indexação.
- **Esforço:** **baixo-médio** — `chunking.py` (199 LOC).
- **Diferencial:** section-aware com limites de token; simples e sem deps pesadas.
- **Concorrência a analisar:** `langchain` text splitters, `llama-index` node
  parsers, `unstructured`, `semantic-chunkers` — concorrência **madura**.
  Verificar se o nosso section-aware zero-dep ganha em simplicidade; caso
  contrário, é candidato fraco.

---

## Não extrair (6) — o núcleo do runner

Estes **são** o `plan_runner`. Extrair qualquer um esvazia o runner (falha o
"teste de autonomia" do playbook: não dá para apagar o runner e mantê-los). Ficam
documentados aqui para fechar o inventário e evitar a tentação futura.

| # | Módulo | Ficheiro | LOC | Porque fica |
|---|--------|----------|-----|-------------|
| 14 | engine | `engine.py` | 518 | o motor de execução do plano; é o runner |
| 15 | worker | `external_worker.py` | 1119 | o worker que fala com o LLM + orçamento + tools; é o runner |
| 16 | executor | `executor.py` | 167 | liga engine↔worker; cola interna |
| 17 | council | `council_session.py` | 1120 | sessão multi-agente específica do nosso domínio |
| 18 | memory | `memory_l4.py` | 462 | memória L4 ligada ao Supabase/esquema nosso |
| 19 | areas | `areas.py` | 258 | routing por área do nosso ecossistema; não genérico |

---

## Fecho

- **19 itens**, todos com evidência (`file:line` / LOC em `main` `f72ec6c`).
- **Prioridade:** doneproof → safe-fetch → hitl-gate → token-budget → (groundeval
  = RE1=B, fica) → depois os médios.
- **Método:** o *flywheel* em `REPO-EVAL-PLAYBOOK.md`. Cada extração endurece o
  pacote **e** devolve a melhoria ao runner.
- **Quem decide quais extrair e quando é o maestro** (regra do maestro). Este doc
  é a proposta com evidência, não uma decisão tomada.
