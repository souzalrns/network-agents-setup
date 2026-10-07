# Portfolio — Network Agents Platform

> **English summary (60 seconds)**
>
> **What it is.** A governed runtime for AI agent workflows. One Python execution engine (`plan_runner`) runs declarative YAML plans step by step. It enforces human approval gates, token and cost ceilings, and completion criteria, and writes an append-only audit log for every run. Business domains (marketing, security, engineering…) plug in as **domain packs**: agents, skills, plans and knowledge, with no change to the engine.
>
> **Proof you can check** (every number below has a source in [Numbers and sources](#números-e-fontes-numbers-and-sources)).
> - 830+ automated tests in CI (Python), plus 195 TypeScript unit tests;
> - 100 merged pull requests, each with evidence;
> - security scanning on every PR (gitleaks, semgrep, CodeQL), with every GitHub Action pinned to a commit SHA;
> - token usage measured on real model runs: a multi-step SEO plan went from **13,130** to **10,136** tokens (−22%) after a measured optimisation, and one round of a multi-agent council costs **11,760**.
>
> **What it is not (yet).** Agents do not execute tools, and the knowledge layer's provenance is still partial. Only the marketing (SEO) pack has been measured with a real model; the security pack is tested in stub mode. Every open item is tracked publicly in [`PENDENCIAS.md`](./initiatives/PENDENCIAS.md).
>
> **Try it in 5 minutes, without an API key:** [Quickstart in the README](../README.md#quickstart), with a GIF of a real run.

Este documento complementa o [README](../README.md): o README diz **o que** o sistema garante e **onde** está o código; este diz **em que estado** está cada parte, **de onde vêm** os números e **por onde** começar a ler.

---

## Problema (Problem)

Quem adopta uma stack "multi-agente" acaba muitas vezes num de dois sítios:

- **custo e controlo sem limite:** agentes que chamam modelos sem tecto de tokens, sem aprovação humana e sem registo do que fizeram;
- **uma pilha de prompts:** cada domínio com o seu framework, sem um motor de execução comum, sem testes e sem segurança de base.

## Solução (Solution)

**Um só motor de execução** (`plan_runner`, Python) e domínios que se ligam a ele, em vez de um framework novo por domínio.

- Um **plano YAML**, validado contra um JSON Schema, declara passos, dependências, artefactos, gates humanos e critérios de conclusão.
- O **motor** corre os passos (sequencial ou em ondas paralelas com LangGraph) e aplica as garantias:
  - pausa no gate humano (approve / reject / edit, e depois `resume`);
  - pára no tecto de tokens ou de custo da área;
  - só declara `done` se os critérios de conclusão passarem.
- Os **workers externos** (hoje o Gemini) registam os tokens de cada chamada.
- Cada **domain pack** traz skills, capabilities, conhecimento e, quando faz falta, agentes. Consome o motor sem o mudar.

Repo companheiro: [`agent-network-mcp`](https://github.com/souzalrns/agent-network-mcp), o servidor MCP em produção (Vercel) que expõe os agentes ao Claude.ai e serve o retrieve do conhecimento.

**Escolha de desenho:** a maioria dos frameworks de agentes optimiza a autonomia. Este optimiza o **controlo e a evidência**.

## Arquitectura (Architecture)

O README tem o mesmo fluxo em diagrama Mermaid ([How a run works](../README.md#how-a-run-works)). Aqui, a versão em texto, com as camadas:

```text
Pedido
  → Router (área → agente ou plano; clarificação limitada)
  → Plano YAML (schema validado)
  → plan_runner (nativo | LangGraph)
       → passo = agente + skill → worker (stub | Gemini)
       → gate humano · tecto de tokens/custo · ledger de tokens · done_when
       → status.json · events.jsonl · artifacts/
  → (opcional) memória L4 (Postgres + pgvector) · conhecimento L5 (RAG, via MCP)
  → Domain pack (marketing, segurança, engenharia, …)
```

## O que corre hoje (What runs today)

O README lista as garantias e o código de cada capacidade ([Capabilities](../README.md#capabilities)). Esta tabela diz o **estado** de cada uma:

| Capacidade | Estado | Onde |
|---|---|---|
| Planos declarativos com schema | Operacional; os 14 planos do repo são validados no CI | [`plan.schema.json`](../runner/plan_runner/plan.schema.json) |
| 2 engines (nativo e LangGraph) | Operacional; o worker corre inline nos 2 (#79) | [`engine.py`](../runner/plan_runner/engine.py), [`langgraph_engine.py`](../runner/plan_runner/langgraph_engine.py) |
| Gates humanos e `resume` | Operacional | [`hitl.py`](../runner/plan_runner/hitl.py) |
| Tectos de tokens e de custo (`paused_budget`) | Operacional | [`BUDGET.md`](./ops/BUDGET.md) |
| Critérios de conclusão (`done_when`) | Operacional desde 2026-10-05 (#90, #96) | [`done_when.py`](../runner/plan_runner/done_when.py) |
| Worker Gemini com tokens medidos | Medido em runs reais de SEO | [`WORKER-EXTERNAL.md`](./ops/WORKER-EXTERNAL.md) |
| Conselho multi-agente (posições, ranking anónimo, síntese, sign-off humano) | 1 ronda real medida | [`COUNCIL.md`](./ops/COUNCIL.md) |
| Router (texto livre → área → agente) | Operacional; a avaliação com o modelo real está por fazer (W-001) | [`router.py`](../runner/plan_runner/router.py) |
| Memória L4 (promoção só com aprovação humana) | Código e testes; o teste real pela CLI está por fazer (L4-1b) | [`MEMORY-L4.md`](./ops/MEMORY-L4.md) |
| Conhecimento L5 (RAG) | Ingest incremental em produção; a revalidação (F0) está quase fechada; a provenance formal fica no F3 | [`RAG-CANONICAL.md`](./ops/RAG-CANONICAL.md) |
| Pack de segurança (triage → audit → report) | Testado em stub; o run real com modelo está por fazer (F5) | [`security-audit-demo.plan.yaml`](./orchestration/security/templates/examples/security-audit-demo.plan.yaml) |

## O que não afirmamos (Explicit non-claims)

- **Não** é uma plataforma "enterprise" completa: é um runtime orientado a produção, com as lacunas listadas.
- **Os agentes não executam tools:** o `tools_allowed` é declarativo (AU-20).
- **Nem todos os packs estão provados.** O marketing (SEO) foi medido com o modelo real; o de segurança está testado em stub. Ter 38 agentes e 72 skills não quer dizer 38 capacidades prontas.
- O TypeScript em `packages/` e `apps/` está **arquivado** (decisão D1): o runtime é Python.
- O conhecimento L5 ainda não tem provenance formal nem filtro por `kb` no retrieve (F3, R-005).
- **Todos os pendentes** estão em [`PENDENCIAS.md`](./initiatives/PENDENCIAS.md), com dono, severidade e evidência.

## Prova (Proof: engineering signals)

- **Testes:** suite grande no runner Python, a correr no GitHub Actions, incluindo:
  - ingest → retrieve contra um Postgres + pgvector descartável;
  - runs lentos de planos reais de ponta a ponta.

  Ver [`runner-tests.yml`](../.github/workflows/runner-tests.yml).
- **Segurança em PRs e na `main`:** segredos (gitleaks), SAST (semgrep, CodeQL) e GitHub Actions presas a um SHA de commit, em versões Node 24. Ver [`security-scan.yml`](../.github/workflows/security-scan.yml).
- **Tokens medidos por run:**
  - o worker regista cada chamada (tokens de entrada e de saída, modelo, run, passo) no log do run;
  - no Supabase, a tabela `token_usage` do MCP aceita as chamadas dos conselhos (`council_*`, C-2). A prova com um run real de conselho a gravar lá fica no F5.
- **Runs medidos, documentados em `docs/ops`:** ver a tabela abaixo.
- **Governação:**
  - um único ficheiro de pendentes;
  - ADRs em [`docs/architecture/adr/`](./architecture/adr/);
  - um plano de execução por fases ([`EXECUTION-PLAN.md`](./architecture/EXECUTION-PLAN.md));
  - cada escolha aberta em opções A/B/C com recomendação.

### Números e fontes (Numbers and sources)

Nenhum número deste portfólio vem de estimativa. Cada um tem a fonte onde se confirma:

| Número | O que mede | Fonte |
|---|---|---|
| **13 130** tokens | 1.º run real do `seo-article-demo` com o Gemini (4 chamadas, 2026-10-01) | [`WORKER-EXTERNAL.md`](./ops/WORKER-EXTERNAL.md), "Primeiro run real (B1)" |
| **12 998 → 10 136** tokens (**−22%**) | Mesmo plano, prompt antigo contra prompt optimizado, medidos com o modelo real | [`WORKER-EXTERNAL.md`](./ops/WORKER-EXTERNAL.md), "Medição real (B1-bis-R2)"; PRs #45 e #55 |
| **11 760** tokens | 1 ronda real do conselho `architecture` (14,7% do tecto de 80k) | [`COUNCIL.md`](./ops/COUNCIL.md), "Custo medido (C-1)" |
| `chunks=0 unchanged=39` | Corrida do ingest em produção quando nada mudou: nenhum embedding gasto | PR #64; corridas do workflow `ingest-knowledge` |
| **830+** testes | `pytest` do runner: 802 rápidos + 34 lentos (836, 2026-10-07; eram 600 a 2026-10-05). Mais 195 de TypeScript (vitest) | [`runner-tests.yml`](../.github/workflows/runner-tests.yml) |
| **100** PRs com merge | Contados pela API do GitHub (2026-10-07; eram 75+ a 2026-10-05) | Histórico de PRs do repo |
| **38** agentes · **72** skills · **14** planos | Ficheiros `*.agent.md`, `SKILL.md` e `*.plan.yaml` no repo | [`agents/`](../agents/), [`skills/`](../skills/), [`docs/orchestration/`](./orchestration/) |

### Linha do tempo (Timeline)

Marcos com data de merge (API do GitHub):

| Data | PR | Marco |
|---|---|---|
| 2026-09-30 | #31 | RAG canónico: o retrieve passa a ler a tabela onde o ingest escreve |
| 2026-10-01 | #36 | O CI volta a conseguir falhar (`pipefail`) |
| 2026-10-01 | #45 | Optimização de contexto do worker (pin + resumos) |
| 2026-10-03 | #55 | Medição real: −22% de tokens; custo real de 1 ronda de conselho |
| 2026-10-03 | #59 | gitleaks + semgrep em cada PR |
| 2026-10-03 | #64 | Ingest incremental por hash de conteúdo, em produção |
| 2026-10-03 | #79 | Worker inline no engine LangGraph (paridade com o nativo) |
| 2026-10-05 | #90, #96 | `done_when` verificado; campos de plano sem efeito removidos |
| 2026-10-05 | #93 | README para portfólio, `LICENSE`, `SECURITY.md` |
| 2026-10-05 | #99 | GitHub Actions em Node 24, pinadas por SHA; GIF do quickstart |

### Histórias de engenharia (Engineering stories)

As 4 principais estão no README ([Selected engineering stories](../README.md#selected-engineering-stories)). Estas complementam-nas:

| Problema | Como foi encontrado | Correcção |
|---|---|---|
| Um plano podia declarar-se `done` sem cumprir os seus próprios critérios de conclusão | Auditoria dos campos de plano que o motor ignorava | `done_when` verificado no fim do run, nos 2 engines (#90) |
| A 1.ª versão Node 24 do `upload-artifact` era a v3, um downgrade para um serviço já desligado | Ler o `action.yml` de cada tag, em vez de assumir pela versão | Regra: a última versão da 1.ª linha principal com `node24`; ficou a v6 (#99) |
| As 201 linhas de conhecimento do MCP tinham `kb` = marketing, fosse qual fosse o domínio | Um SELECT de revalidação mostrou o valor por omissão da coluna | Registado como R-005 (Alta), com a causa no schema; a correcção fica no F3, com a provenance |
| 2 itens do registo de pendências esperavam por merges que já tinham acontecido | Revisão cruzada do registo com a API do GitHub | Fechados com o PR e os testes (C-2, R-004); o resto do registo foi revisto da mesma forma |

## Quickstart

Os comandos e um GIF de um run real estão no [Quickstart do README](../README.md#quickstart). São 5 minutos, sem chave de API.

A CLI completa e o worker real (Gemini) estão em [`runner/README.md`](../runner/README.md).

## Por onde começar a ler o código (Code tour)

Para uma revisão técnica de 20 minutos, por esta ordem:

1. **Um plano real:** [`seo-article-demo.plan.yaml`](./orchestration/marketing/templates/examples/seo-article-demo.plan.yaml), para ver o que um domínio declara.
2. **O contrato:** [`plan.schema.json`](../runner/plan_runner/plan.schema.json) e [`models.py`](../runner/plan_runner/models.py).
3. **O motor:** [`engine.py`](../runner/plan_runner/engine.py) (`run_plan`, `resume_run`).
4. **As garantias:** [`hitl.py`](../runner/plan_runner/hitl.py), [`cost.py`](../runner/plan_runner/cost.py) e [`done_when.py`](../runner/plan_runner/done_when.py).
5. **O worker real e o ledger:** [`external_worker.py`](../runner/plan_runner/external_worker.py).
6. **A prova:** [`runner/tests/`](../runner/tests/), por exemplo `test_done_when.py` e `test_plan_fields.py`.

## Decisões de desenho (Design choices recruiters ask about)

| Escolha | Porquê |
|---|---|
| Um só runtime | Evitar um 2.º "cérebro" por domínio. O core TypeScript anterior está arquivado (decisão D1) |
| Gates humanos e tectos de tokens por omissão | Agentes sem controlo de custo nem aprovação são demos |
| Capabilities antes de mais agentes | O pack de segurança é o modelo: um domínio novo entra por configuração, não por código no motor |
| Repo público com higiene de segredos | gitleaks no CI, uma lista de ficheiros que os agentes não podem ler, nenhum segredo em prompts |
| Dois repos | Orquestração e governação aqui; a superfície MCP de produção no `agent-network-mcp` |

## Domínios (Domains)

- **Marketing (1.º domínio):** agência multi-agente com papéis limitados, knowledge packs e o playbook de descoberta por IA. Ver [`PORTFOLIO-MARKETING.md`](./PORTFOLIO-MARKETING.md).
- **Segurança defensiva:** pipeline triage → audit → report com capabilities declaradas. É o modelo para os próximos domínios.
- **Engenharia:** gate de revisão (código, segurança e testes) antes de um ship, com `done_when` verificável ([`ship-gate.plan.yaml`](./orchestration/engenharia/templates/ship-gate.plan.yaml)).

## Contacto (Contact)

- GitHub: [souzalrns](https://github.com/souzalrns)
- Repos: [`network-agents-setup`](https://github.com/souzalrns/network-agents-setup) · [`agent-network-mcp`](https://github.com/souzalrns/agent-network-mcp)

Documentação interna em português · Licença [MIT](../LICENSE)
