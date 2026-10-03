# Conselho interno: `CouncilSession` (Fase 1 do ADR-META-AGENTS)

> **Estado (2026-10-01):** implementado e testado (Bloco C, PLANO J5-b, J5-c e E12):
> - 45 testes sem BD (`runner/tests/test_council.py`);
> - 5 testes contra Postgres + pgvector (`runner/tests/test_council_l4.py`, job `test-rag`).
>
> **Critério de DONE cumprido com mock** (Gemini falso, L4 real num Postgres local): o conselho `architecture` corre de ponta a ponta, dá um veredicto estruturado, o HITL aprova, e a L4 passa de `candidate` a `active` (secção "Evidência").
>
> **Custo real medido (C-1, 2026-10-03, run do maestro):** 1 ronda do `architecture` = **11 760 tokens** (14,7% do tecto de 80k). Veredicto real `conditional`, gate `pass`, HITL `approve`, estado `done`. Ver "Custo medido (C-1)" e "Evidência real".
>
> **Por fazer:** migração do ledger no Supabase, passo do DEV (C-2, secção "Ledger").

Desenho: [ADR-META-AGENTS](../architecture/adr/ADR-META-AGENTS.md) §9–§13. Contrato da L4: [contracts.md](../architecture/memory/contracts.md). HITL: [hitl-request-v1](../architecture/hitl/hitl-request-v1.json).

## O que é

Um **passo de deliberação** que o maestro invoca (ADR §6), não uma segunda porta de entrada:
- **C2:** 2–3 membros internos (`kind: internal`) dão posições independentes e criticam-se às cegas;
- **C1:** um chairman (`kind: meta`) sintetiza;
- **gate determinístico:** decide o que o humano pode fazer a seguir;
- **C0:** o humano decide;
- **L4:** o veredicto nasce `candidate` e só passa a `active` por decisão humana (ADR §9, `contracts.md:29,34`).

| Peça | Ficheiro |
|---|---|
| Sessão, estágios, gate, HITL, L4, CLI, `countTokens` | `runner/plan_runner/council_session.py` |
| Painéis (architecture, security, product) | `config/councils.yaml` |
| Chairman (`kind: meta`, só decide) | `agents/meta/chairman.agent.md` |
| Validação (corre no E7 do CI) | `runner/plan_runner/areas.py:145-197` + `council_session.py:127` |
| Escalada a partir do router | `runner/plan_runner/router.py:345` (`escalate`), `:442` (`execute`) |
| `call_kind` do conselho no Supabase (por correr) | `scripts/alter_token_usage_council_kinds.sql` |

## Desenho: técnicas escolhidas e descartadas

| # | Técnica sugerida | Decisão | Porquê / evidência |
|---|---|---|---|
| 1 | Subgrafo LangGraph **ou** sequência Python | **Sequência Python**, com os estágios com os nomes dos nós do ADR §12 | O worker inline só corre no engine `native` (`cli.py`: "--worker inline so no engine native"). O HITL durável já é por ficheiros e funciona entre processos e com o lado Node sem checkpointer (`hitl.py`). O LangGraph é opcional (`runner/requirements-langgraph.txt`). Como cada estágio é uma função `(estado) → estado`, embrulhá-los num `StateGraph` é mecânico, se um dia for preciso (ADR §12) |
| 2 | Estado do conselho | **Sim**, em `<dir>/council.json`: `topic`, `context`, `council_type`, `participant_ids`, `rounds[]` (por ronda: `labels`, `positions`, `ballots`, `peer_scores`, `verdict`, `gate`, `hitl`, `memory`), `verdict`, `gate_ok`, `hitl_decision`, `status`, `ledger[]` | `positions` e `ballots` são mapas `membro → …` (e não listas) para cada estágio ser **idempotente**: um `resume` só repete o que falhou (`council_session.py:712-757`) |
| 3 | Papéis | **member**, **critic** e **chairman** | O `critic_item13` foi **descartado**: avalia o "Item 13" (citabilidade por IAs) de peças de marketing (`agents/marketing/critic_item13.agent.md`), não serve para arquitectura. Como críticos ficaram o `engenharia.revisor-codigo` (architecture, security) e o `design.design_critic` (product), com um prompt de ataque a riscos. **Chairman:** agente `meta.chairman` dedicado (`kind: meta`), o que o ADR §13 previa |
| 4 | Protocolo | **Os 6 estágios** do ADR §11 | O veredicto vai para a L4 como `candidate` **quando o pedido HITL abre**, e o pedido leva o id da memória: uma só decisão humana fecha o conselho e a memória. Ver "Fluxo" |
| 5 | `config/councils.yaml` | **Sim** (E12: ao lado do `areas.yaml`, validado pelo E7) | Diferenças para o esboço do ADR §13: 2–3 membros (decisão do maestro), por isso saem `meta.planejador` (architecture) e `marketing.marketing`/`gestao.gestao-empresarial` (product); acrescentam-se `area`, `hitl_category`, `role` e `escalation` |
| 6 | Ledger | **Sim**: `call_kind` = `council_member` \| `council_peer` \| `council_chairman`, `step_id` = `council/r<ronda>/<estágio>/<participante>` | No Supabase, o `CHECK` do `token_usage` ainda recusa estes valores (`agent-network-mcp/memory/token_usage.sql:12`). Ver "Ledger" |
| 7 | Orçamento | **Sim**: o tecto é o `budget.max_tokens` da **área do conselho** (ou `--max-tokens`) | É o mesmo mecanismo do worker (`external_worker.check_budget`, antes de cada chamada). Quando vem do router, os tokens do router entram no mesmo ledger e contam no tecto |

**Acrescentado** (não estava na lista):
- **Dissent determinístico:** toda a posição que votou diferente da decisão entra no `dissent`, mesmo que o chairman a omita (`council_session.py:376`). É anti-bajulação sem LLM.
- **Anonimização activa:**
  - letras baralhadas por sessão e ronda;
  - os ids dos membros são apagados do texto que chega ao chairman e aos pares (`_scrub`);
  - o chairman sabe *que* há um veto de membro obrigatório, não *de quem*.
- **Escala de `confidence`:** fora de [0, 1] é **inválida**, nunca reescalada (lição do AU-13, `council_session.py:291`).
- **Gate que bloqueia:**
  - com veto, `low_confidence`, `no_quorum`, `incomplete` ou `invalid`, o humano só pode `reject` ou `edit` (revisão), nunca `approve`;
  - sem rondas livres, só `reject`.
- **Quorum:** sem posição válida de um membro `required`, ou com menos de 2 posições, a sessão fica em `error`, e o `resume` volta a pedir só a quem falhou.
- **Validação no E7:**
  - chairman com `kind: meta` e fora de todas as áreas (o router nunca o escolhe);
  - um agente meta sem conselho é órfão;
  - membros só `internal` (o `external_ai` é Fase 2);
  - τ em ]0, 1];
  - `max_rounds` obrigatório;
  - keywords de escalada sem acentos e sem repetições.
- **Tectos de saída por estágio:** 1024 / 512 / 1536 (`OUTPUT_CAPS`), para limitar o custo de cada chamada.
- **`chairman_model` opcional** por conselho: outro modelo para o chairman.
- **`pilots/council-*/` no `.gitignore`:** o tema e o contexto podem ser sensíveis.

**Não feito (por regra):** Fase 2 (IAs externas), `llm-council` como dependência, tools para o chairman, escrita em produção.

## Fluxo

```
run ─► INDEPENDENT (N) ─► PEER_RANK (N, anónimo) ─► SYNTHESIZE (chairman) ─► GATE (sem LLM)
        └─ L4 remember (candidate) + pedido HITL (hitl-requests.jsonl) ─► awaiting_human
decide approve ─► L4 promote (active) ─► done        (verdict.json)
decide reject  ─► L4 forget (archived) ─► rejected
decide revise  ─► L4 forget (archived) ─► ronda+1, com o comentário humano no prompt (até max_rounds)
```

Estados: `running`, `awaiting_human` (`status.json` → `paused_human_gate`), `paused_budget`, `error`, `done`, `rejected`.

**Custo por ronda: 2N + 1 chamadas** (N = membros); com 3 membros, são 7.

## Veredicto (`verdict`)

```json
{"decision": "approve|conditional|reject|defer", "summary": "...", "rationale": "...",
 "conditions": ["... (obrigatório em conditional)"],
 "dissent": [{"position": "B", "member_id": "engenharia.revisor-codigo", "point": "...", "source": "chairman|gate"}],
 "kill_criteria": ["sinal observável que invalida a decisão"],
 "next_actions": [{"action": "...", "owner": "..."}], "risks": ["..."], "confidence": 0.85,
 "participants": {"chairman": "meta.chairman", "members": {"<id>": {"role", "vote", "confidence", "veto"}}}}
```

## Gate (determinístico)

| Ordem | Resultado | Quando | O humano pode |
|---|---|---|---|
| 1 | `invalid` | `decision` fora dos 4 valores, ou `confidence` fora de [0, 1] | reject, edit |
| 2 | `no_quorum` | Falta a posição válida de um membro `required` | reject, edit |
| 3 | `veto` | Um membro `required` votou `reject` ou `veto: true`, **e** a decisão é `approve`/`conditional` | reject, edit |
| 4 | `low_confidence` | `confidence < confidence_threshold` (τ) | reject, edit |
| 5 | `incomplete` | `approve`/`conditional` sem kill criteria ou sem próximos passos; `conditional` sem condições | reject, edit |
| — | `pass` | Nenhum dos anteriores | approve, reject, edit |

- **Na última ronda** (`max_rounds`) não há `edit`.
- **Veto contra uma decisão `reject` não bloqueia:** aprovar significa aceitar o veredicto "não avançar".

## Como correr

```bash
cd runner
python -m plan_runner council validate
python -m plan_runner council cost architecture "Passar os checkpoints do LangGraph para Postgres?"   # countTokens, grátis
python -m plan_runner council run architecture "Passar os checkpoints do LangGraph para Postgres?" \
  --context-file ../docs/architecture/adr/ADR-META-AGENTS.md      # -> pilots/council-architecture-<id>/
python -m plan_runner council status ../pilots/council-architecture-<id>
python -m plan_runner council decide ../pilots/council-architecture-<id> approve --by maestro
python -m plan_runner council decide ../pilots/council-architecture-<id> revise --comment "mede o custo primeiro"
python -m plan_runner council resume ../pilots/council-architecture-<id>    # decisão escrita pelo lado Node, orçamento, erro
```

- **Lado Node:** escreve a decisão em `<dir>/hitl-decisions.jsonl` (contrato v1, `response: approve|reject|edit`) e o `council resume` aplica-a.
- **Quem decide:** fica `human:<responder_id>` na L4.

**Pelo router** (D2), um pedido estrutural escala sozinho:
```bash
python -m plan_runner route "Decisão de arquitetura: o backend deve passar a API para filas?" --execute
python -m plan_runner route "..." --no-council      # desliga a escalada
```

Regra de escalada (`config/councils.yaml`, `escalation`):
- o pedido tem de ser de uma das áreas listadas **e** casar uma das keywords;
- não há LLM nesta decisão;
- a lista é curta e explícita, porque um conselho custa 2N+1 chamadas contra 1–2 de um agente.

## L4

- **Âmbito:** `memory_scope` do `councils.yaml` (`project:network-agents-setup`) ou `--scope`. Só `project`/`user`/`agent`: o chairman é um agente, e `org`/`global` são só humanos (`scopes.md:23-24`). Fora disso, `start` recusa.
- **Linha:**
  - `subject` = `council:<tipo>`;
  - `statement` = decisão, resumo, condições, kill criteria, próximos passos e dissent (≤ 2000 caracteres);
  - `tags` = `council`, `council:<tipo>`, `decision:<…>`, `gate:<…>`;
  - `metadata` = veredicto completo, gate e participantes;
  - `source_run_id` = id da sessão;
  - `created_by` = `agent:meta.chairman`.
- **Sem `DATABASE_URL`:** a L4 fica desligada (`memory.status = disabled`). O veredicto fica em `council.json` e, se aprovado, em `verdict.json`.
- **Falha da L4:** a L4 nunca parte o conselho. O erro fica em `memory.error`.

## Ledger

- **Local:** cada chamada grava uma linha em `<dir>/token_usage.jsonl` (`call_kind`, `step_id = council/r1/independent/<membro>`, `run_id` = uuid da sessão) e uma entrada em `council.json → ledger[]`, com ronda, estágio, participante, tokens e caracteres do prompt.
- **Por ronda:** `council status` mostra `tokens_by_round`.
- **Supabase (passo do DEV, por correr):**
  - o `CHECK` actual só aceita `router|agent|embed_query|embed_doc` (`agent-network-mcp/memory/token_usage.sql:12`);
  - até correr a migração, o envio das linhas do conselho falha e fica registado como `remote: "error: HTTP 400…"` no jsonl local; o conselho não pára.

  ```
  Supabase → agent-network-memory → SQL Editor → scripts/alter_token_usage_council_kinds.sql
  verificar: select pg_get_constraintdef(oid) from pg_constraint where conname = 'token_usage_call_kind_check';
  ```
  Testado 2× seguidas num Postgres 16 local, com a tabela criada pelo `token_usage.sql` real:
  - antes da migração, `council_member` é recusado;
  - depois, os 3 valores novos e os 4 antigos são aceites;
  - um valor inválido continua a ser recusado.

## Custo medido (C-1, 2026-10-03, run do maestro, Gemini real)

Conselho `architecture` (3 membros + chairman, `flash-lite`), 1 ronda.

| Medida | Valor | Fonte |
|---|---:|---|
| Chamadas | **7** (3 member + 3 peer + 1 chairman) | run real |
| Entrada fixa da ronda (`council cost`) | **5 860** | **`countTokens`** (estimativa exacta do tokenizer, sem gerar texto) |
| Intervalo previsto da ronda | **5 860 – 22 756** (floor – ceiling) | `countTokens` + tectos de saída |
| `tokens_in` real | **9 502** | `usageMetadata` (ledger) |
| `tokens_out` real | **2 258** | `usageMetadata` (ledger) |
| **`tokens_total` real (1 ronda)** | **11 760** | `usageMetadata` (ledger) |
| % do tecto da área `software` (80 000) | **14,7%** | 11 760 / 80 000 |
| 2 rondas (`max_rounds` = 2) | ≈ 23 500 (29%) | **extrapolação** (2 × a ronda medida), não medido |

- **O real cai dentro do intervalo previsto**, a 35% do caminho entre floor e ceiling: (11 760 − 5 860) / (22 756 − 5 860). A parte que depende das saídas (posições reinjectadas nos pares e no chairman, mais as próprias saídas) vale ~5,9k, metade do total.
- **Comparação:** uma ronda de conselho (11 760) custa mais do que o `seo-article-demo` inteiro em `opt` (10 136, B1-bis-R2), com 7 chamadas contra 4.

**Conclusão: o conselho é viável a este custo, sem cortes.**
- **architecture:** 1 ronda usa 14,7% do tecto; com a ronda máxima (2), ≈ 29%. A regra de paragem 4 (custo > tecto) não se aplica.
- **Não proponho cortar membros nem rondas.** O ganho de 2 membros (5 chamadas por ronda) não justifica perder o crítico. Fica como alavanca se o uso real crescer (opções abaixo).
- **security** (tecto de 40k) não foi medido. Com um tamanho parecido, 1 ronda daria ~29% e 2 rondas ~59%: cabe, mas com menos folga. É uma estimativa; mede-se no primeiro run real de security.
- **Por medir:** os tokens **por estágio** (independent / peer / synthesize). O run do maestro tem-nos em `council.json → ledger[]` (por participante) e no `token_usage.jsonl` (`call_kind`), mas este registo só traz os totais.

### Regra de uso (maestro, 2026-10-03)

> **1 conselho ≈ 1 SEO.** Não disparar o conselho por omissão: só para uma decisão estrutural (`architecture` / `security` / `product`), invocada explicitamente (`council run`), ou quando o router escala o pedido (keywords de `escalation` no `config/councils.yaml`).

- **Porquê:** uma ronda (11 760 tokens) custa o mesmo que o `seo-article-demo` inteiro em `opt` (10 136): 1,16×.
- **Como já está no código:** o router só escala com keywords explícitas, nas áreas listadas (`router.py:345`, `escalate`); `route --no-council` desliga a escalada. Nenhum plano nem agente abre um conselho sozinho.
- **Escalar todas as áreas `hitl: required` (ADR §9) continua desligado.** Multiplicaria o custo de cada pedido de security, finance e legal por cerca de 1 SEO.

### Análise do Grok (parceiro de design, 2026-10-03), sobre o B1-bis-R2 e o C-1

1. **SEO em `opt` ~10k: saudável.** O critic deixou de ser o buraco do `tokens_in` (3759 → 2091, −44%).
2. **Conselho ~12k por ronda: saudável para uma decisão estrutural.** 1 conselho ≈ 1 SEO.
3. **Não abrir o B1-bis-C só porque não está <9k.** O ganho real já apareceu (−22%).
4. **Não migrar SQLite → Postgres só porque o conselho falou nisso.** O veredicto é `conditional` e as condições não foram validadas. O SQLite continua certo para um só processo, que é o que o ADR §12 já dizia ("só quando houver multi-instância").
5. **Não baixar o tecto do conselho para 15k agora.**

**Decisões que ficam registadas:**
- **Tecto:** o conselho não tem um `max_tokens` próprio; usa o da área do conselho (80k em `architecture`/`product`, 40k em `security`). Fica assim. Um tecto de 15k cobriria 1 ronda medida (11 760), mas não 2 (≈ 23 500, extrapolado), por isso mudá-lo exige decidir primeiro se a 2.ª ronda se mantém.
- **Veredicto aprovado não executa nada.** O `approve` no HITL torna o veredicto conhecimento `active`; não aplica a decisão. Executar o que o veredicto propõe (aqui, a migração do checkpointer) é trabalho separado, que só começa depois de validadas as condições, por ordem do maestro.

### Antes do run (referência)

**Lição do B1-bis aplicada: não se decide nada com caracteres.** O que existia antes do C-1:

| Medida | Valor | Natureza |
|---|---|---|
| Chamadas por ronda (architecture, 3 membros) | **7** (3 member + 3 peer + 1 chairman) | exacto |
| `maxOutputTokens` por chamada | 1024 / 512 / 1536 | exacto (tecto) |
| Parte variável máxima de 1 ronda (saídas no tecto + posições reinjectadas) | **16 896 tokens** | exacto (fórmula de `estimate_cost`) |
| Entrada fixa de 1 ronda | **5 860** (medido no C-1) | `countTokens` |
| Run real | **por medir** (7 chamadas `flash-lite`) | precisa de `GEMINI_API_KEY` |

Tamanho dos prompts reais do repo, só para referência de **forma** (não são tokens), num run com saídas curtas do Gemini falso:

| Chamada | Caracteres do prompt |
|---|---:|
| member `meta.arquitetura-agentes` | 5 812 |
| member `engenharia.desenvolvimento` | 3 910 |
| member `engenharia.revisor-codigo` (critic) | 5 752 |
| peer (×3) | 1 379–1 400 |
| chairman | 5 262 |
| **Total** | **24 905** |

Os prompts dos membros e do chairman são dominados pelo AGENT.md e pela directiva de grounding; os dos pares são curtos (sem AGENT.md, só a perspectiva numa linha). Com saídas reais, os prompts dos pares e do chairman crescem com as posições (no máximo, a parte variável acima).

**Tecto:** architecture e product usam a área `software` (80k); security usa `security` (40k). Uma ronda cabe folgada mesmo com a parte variável no máximo; o `max_rounds` (2/2/1) limita o resto.

**Se o run real mostrar um custo proibitivo**, há estas alavancas (decisão do maestro, com o número na mão):
- **A:** 2 membros em vez de 3, o que dá 5 chamadas por ronda;
- **B:** PEER_RANK sem o contexto (só o tema e as posições);
- **C:** os membros sem a directiva de grounding completa (`slim`), **só** em `architecture`/`product`; `security` fica `full`.

## Testes

| Ficheiro | O que prova |
|---|---|
| `tests/test_council.py` (45) | 2N+1 chamadas e a ordem dos estágios; veredicto estruturado nos 4 valores; dissent determinístico; gate (veto de required, veto de não-required ignorado, veto + reject passa, low_confidence, confidence fora de escala inválida, incomplete); HITL pára, `resume` sem decisão não chama o LLM; pedido valida contra o schema v1; decisão escrita pelo lado Node; revise abre nova ronda com o comentário e respeita `max_rounds`; chairman nunca vê ids; peer não vê a própria posição; ballot inválido não bloqueia; Borda; quorum + `resume` só repete quem falhou; orçamento pausa e retoma sem repagar; tecto por omissão = área; ledger por ronda com `call_kind` e envio remoto; sem `DATABASE_URL`; `chairman_model`; escalada do router (com e sem keyword, `--no-council`, só nas áreas do conselho); CLI run/decide/status/validate; `countTokens`; validador (10 configurações inválidas, chairman não-meta, meta numa área, meta órfão) |
| `tests/test_council_l4.py` (5, Postgres + pgvector) | **DONE:** candidate → HITL approve → active, e o recall devolve-o; reject → archived com motivo; revise → archived + novo candidate; com veto nunca chega a active; âmbito `org` recusado |

## Evidência real (C-1, 2026-10-03, run do maestro, Gemini real)

| Campo | Valor |
|---|---|
| Conselho | `architecture` (1 ronda, 7 chamadas) |
| Decisão | **`conditional`**, confidence **0,85** (τ = 0,7) |
| Conteúdo | **3 condições, 2 kill criteria, 2 next_actions** |
| Gate | **`pass`** (coerente com as regras: `conditional` com condições, kill criteria e próximos passos; confidence ≥ τ) |
| HITL | **`approve`** por **`human:souza`** |
| Estado final | **`done`** |

É a primeira prova funcional com o modelo real: as saídas do `flash-lite` passaram na normalização (posições, ballots e veredicto em JSON válido, `confidence` em 0–1), e o protocolo correu de ponta a ponta.

**Tema:** a migração dos checkpoints do LangGraph de SQLite para Postgres (segundo a análise do Grok, ponto 4). **Seguimento:** nenhum. O veredicto é `conditional`, as condições não estão validadas, e o SQLite fica (ver "Análise do Grok").

**Por registar:** o texto das condições, dos kill criteria e dos próximos passos (`verdict.json` do run do maestro), e o estado da L4 neste run (`candidate` → `active`, ou `disabled` se correu com `--no-memory`).

## Evidência (2026-10-01, Gemini falso, L4 num Postgres 16 + pgvector local)

O run usou o `config/councils.yaml` real, os AGENT.md reais e a BD criada com os 2 SQL da L4 (o mesmo SQL que está em produção desde o L4-1):

```
apos run: awaiting_human | gate: pass | allow: ['approve', 'reject', 'edit'] | memoria: candidate f3bff10a-…
veredicto: approve, confidence 0.85, kill_criteria ["resume > 2s em p95"], next_actions [spike …]
L4 antes do HITL: candidate agent:meta.chairman project:network-agents-setup
L4 depois do HITL: active human:maestro
recall active: ['f3bff10a-…']
estado final: done | 7 chamadas (3 council_member, 3 council_peer, 1 council_chairman)
ficheiros: council.json events.jsonl hitl-requests.jsonl hitl-decisions.jsonl memory_l4.jsonl status.json token_usage.jsonl verdict.json
```

## Limites

- **Fase 1 só:** membros `internal`. A Fase 2 (IAs externas, `kind: external_ai`) fica para depois, sobre o mesmo protocolo (ADR §2).
- **Anonimato parcial:**
  - o texto livre de uma posição pode revelar o papel do autor ("como revisor…");
  - só os ids são apagados;
  - o veto de membro obrigatório é visível como veto.
- **Escalada só por keywords:**
  - a regra do ADR §9, que manda conselho para todas as áreas com `hitl: required`, **não** está ligada, porque multiplicaria o custo de todos os pedidos de security/finance/legal (ver pendentes no relatório do Bloco C);
  - um passo de plano que abra um conselho também não existe ainda.
- **Sem checkpointer partilhado:** a sessão vive num directório; duas máquinas não retomam a mesma sessão (o mesmo limite do runner).
