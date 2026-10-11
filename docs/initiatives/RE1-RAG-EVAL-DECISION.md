# RE1 — dossier de decisão: rag-eval é 4.º repo autónomo, ou não?

A decisão é do maestro (regra do maestro: o Claude propõe, não assume). Este
dossier dá tudo para decidir: o que é, o estado real com evidência, o bloqueador,
as opções A/B/C com esforço/risco, e uma recomendação. Base:
`CAPABILITY-MATRIX-AUTONOMOUS.md` §3.

## O que é

Avaliar a recuperação (RAG) de um run contra um *golden set*: dado um conjunto de
perguntas com as respostas/fontes esperadas, medir se o pipeline recupera o certo.
Hoje é `runner/plan_runner/l5_eval.py` + `runner/tests/test_l5_eval.py`, **dentro**
do plan_runner.

## Estado real (evidência, não README)

| Capacidade | Estado | Evidência |
|---|---|---|
| Golden-set eval offline (`validate`) | **provado** | `l5_eval.py` · `test_l5_eval.py` |
| Métricas: provenance_ok, source_hit@k, chunk_hit, MRR | **provado** | `l5_eval.py` · testes |
| Gate de regressão (R-011) | **provado** | `l5_eval.py` (bloqueia) · teste |
| Backend pluggable (não preso a 1 MCP) | **ausente** | `from .mcp_knowledge import McpKnowledge` em `l5_eval.py:157` (import tardio no `run`) |

Ou seja: o **motor de avaliação é sólido**; o que falta para ser "repo" é
**desacoplar o backend** (hoje o `run` instancia `McpKnowledge` diretamente).

## Factos que pesam na decisão

- **Mercado saturado.** Avaliação de RAG/LLM é um espaço cheio e maduro: `ragas`,
  `deepeval`, `promptfoo`, `trulens`. Um `rag-eval` genérico entra **sem
  diferencial** contra estes.
- **O nosso diferencial não viaja.** O que torna o `l5_eval` valioso —
  `provenance_ok` e `source_hit@k` **ligados ao pipeline governado** (L5 + o
  runner) — é exatamente o que um backend genérico perde. O valor está em estar
  **acoplado ao runner**, não em ser genérico.
- **Nome.** `rag-eval` está **ocupado no PyPI** (HTTP 200, verificado 2026-10-10);
  `rageval` está livre. Um 4.º produto começaria já com problema de nome.
- **Foco.** Há trabalho de maior alavancagem por fechar (o teu publish XP1; o
  diferencial de *accountability* do doc C). Um 4.º repo dilui.

## Opções (A/B/C)

### A) GO — extrair para repo próprio com backend pluggable
Desacoplar (`Retriever` protocol: `search(query) -> hits`), empacotar, CI, PyPI.
- **Prós:** vira produto independente; fecha o critério E5.
- **Contras:** entra num mercado saturado sem diferencial; o valor (métricas de
  governança) não viaja para um backend genérico; nome `rag-eval` ocupado;
  consome foco/energia de XP1. **Esforço: médio-alto.**

### B) NO-GO como produto — fica no runner, mas **desacopla o backend** (hygiene)
Mantém o `l5_eval` como a avaliação do pipeline **governado** (onde é forte).
Introduz o mesmo `Retriever` protocol só para o testar sem `mcp_knowledge`
(fecha E5 como *hygiene interna*, não como produto). Sem repo novo, sem PyPI.
- **Prós:** preserva o diferencial onde ele existe; fecha a coupling/teste de
  autonomia; esforço pequeno; não dilui o foco.
- **Contras:** não há "4.º produto" para o portfolio. **Esforço: baixo.**

### C) ADIAR — não decidir agora
Deixar como está (acoplado) até haver um sinal concreto (ex.: um design partner
a pedir avaliação standalone).
- **Prós:** zero trabalho agora.
- **Contras:** a coupling (E5) e o teste de autonomia vermelho ficam como wart;
  decisão volta a aparecer. **Esforço: nenhum.**

## Recomendação — **B** (no-go como produto; desacoplar como hygiene)

**RECOMENDADA.** O leitura honesta (doc C) é que o nosso moat é
**governação/composição**, não avaliação de RAG genérica — um terreno já ganho
por `ragas`/`deepeval`/`promptfoo`. Como lib genérica, o `rag-eval` não tem
diferencial e o nome está ocupado; como avaliação **do runner governado**, é
forte. Logo: mantê-lo no runner, e desacoplar o backend (um `Retriever` protocol)
apenas para o tornar testável sem `mcp_knowledge` e fechar o E5 — sem gastar o
foco num 4.º repo. Revisitar **A** só com evidência de procura (um utilizador a
pedir avaliação standalone).

- **Se o maestro decidir B:** o próximo passo é pequeno — o `Retriever` protocol +
  injeção no `run` (default = `McpKnowledge`), + um teste com um retriever falso.
- **Se decidir A:** primeiro escolher nome (não `rag-eval`), depois o mesmo
  desacoplamento + empacotamento/CI/PyPI (padrão `auditron`/`skill-scout`).
- **Se decidir C:** nada agora; o item fica ABERTO.

## Decisão (2026-10-10): **B** — no-go como produto

Decidida sob a regra "padrão ouro, superar onde for viável" (autonomia delegada):
entrar no mercado de RAG-eval **não é terreno onde se supere** (ragas/deepeval/
promptfoo maduros; nome ocupado) — logo não se luta lá. O `l5_eval` fica no runner,
onde é diferenciado (métricas ligadas ao pipeline governado). **A** só se houver
procura concreta (um utilizador a pedir avaliação standalone).

**Correcção honesta ao dossier:** o desacoplamento que a opção B exigia **já estava
feito** — o motor `evaluate(golden, retrieve)` recebe um `Retrieve` (`(kb,query,k)
-> hits`) e nunca fala com um MCP; o acoplamento ao `McpKnowledge` existe só no
*default* `mcp_retrieve()`, já injectável, e os testes já corriam com retrievers
falsos. O critério **E5 (backend pluggable) está satisfeito**, não ausente como a
matriz dizia. Este PR apenas (1) **documenta** o seam `Retrieve` como ponto de
extensão de 1.ª classe e (2) acrescenta uma **guarda explícita**
(`test_backend_pluggavel_sem_mcp`) que prova que `evaluate` corre sem o MCP sequer
em memória. Zero reescrita — a decisão não precisava dela.

**Estado:** RE1 **FECHADO** (decisão B). Revisitar A só com evidência de procura.

## Adenda (2026-10-11): extraído como `groundwright`, sem contradizer o B

O maestro reabriu a extracção ("avance com todos"). A decisão B continua correcta no que
afirmava: **não entrar no mercado de `rag-eval` genérico** (ragas/deepeval/promptfoo
maduros; nome ocupado). A 5ª volta do flywheel extraiu o `l5_eval` como **`groundwright`**
(PyPI), mas enquadrado no diferencial que o próprio B identificava: uma **porta
determinística de proveniência/grounding de retrieval** (provenance_ok, source_hit@k,
chunk da âncora, gate de regressão), **sem LLM** — a pergunta *anterior* à qualidade da
resposta. Não é um avaliador de RAG genérico. PR #184; `oss/groundwright/POSITIONING.md`.
