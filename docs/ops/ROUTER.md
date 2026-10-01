# Router hierárquico híbrido (D2)

> **Estado (2026-10-01):** implementado e testado offline: 37 testes em `runner/tests/test_router.py` e 10 a mais em `test_areas.py`.
> - **A escolha da área é real:** são keywords, sem LLM. Acerta os 14 casos do golden set.
> - **A escolha do agente usa um Gemini falso nos testes.** A qualidade real do Gemini a escolher o agente **ainda não foi medida**: a sessão não tinha `GEMINI_API_KEY`. Mede-se com `python -m plan_runner.router eval` (ver "Validar com o Gemini real").

Decisão: [DECISAO-2-maestro.md](../audit/DECISAO-2-maestro.md) §138-143 (C4 hierárquico híbrido, M3 registo, G1+G2+G3). Código: `runner/plan_runner/router.py`. Dados: `config/areas.yaml`.

## Como decide

```
pedido ──► 1. ÁREA (keywords; embeddings opcionais) ──► 2. AGENTE/PLANO (Gemini, só candidatos da área) ──► 3. EXECUÇÃO (plan_runner + worker)
              │                                            │
              ├─ nenhuma keyword ──► fallback_area         ├─ área sem agentes ──► HITL ("sem especialista")
              └─ ambíguo ──► clarificação | HITL (risco)    ├─ 1 só candidato ──► esse agente, sem LLM
                                                           └─ confiança baixa / clarify ──► clarificação | HITL (risco)
```

### 1. Área
- **Keywords** de cada área em `config/areas.yaml` (`keywords:`).
  - O texto é normalizado: minúsculas e sem acentos.
  - Keywords de até 5 caracteres casam só a palavra inteira (`lei` não apanha "leitura"). As mais longas são radicais (`contrat` apanha contrato/contratual).
  - **Pontuação** = número de keywords distintas que casam.
  - **Confiança** = `melhor / (melhor + segunda)`. Vale 1,0 quando só uma área casa e 0,5 num empate.
- **Embeddings** (opcional, `--embeddings`): só quando nenhuma keyword casa.
  - Comparam o pedido com o texto de cada área (id, descrição e keywords), via `gemini-embedding-001`.
  - Os cosenos são centrados na média de todas as áreas antes da mesma margem. Sem isso, como ficam todos entre 0,6 e 0,8, tudo pareceria ambíguo.
  - As áreas são embebidas uma vez por processo.
- **Nenhuma keyword (nem embeddings)** → `routing.fallback_area` (`horizontal`). O LLM escolhe entre o planeador e o `using_agent_skills` (G3).
- **Confiança < `routing.area_min_confidence` (0,6)** → **clarificação**, com uma pergunta que lista as áreas em causa. Passa a **HITL** se alguma delas tiver `hitl: required` (legal, finance, security; D2:141).

### 2. Agente ou plano (dentro da área)
- **Candidatos** = `agents[]` + `horizontals[]` da área (G2), cada um com o `description:` do frontmatter (J4). O LLM nunca vê agentes de outras áreas (R5).
- O Gemini (`gemini-flash-lite-latest`, ou `AGENT_MODEL`) responde em JSON: `{mode: agent|plan|clarify, agent, steps[{agent, task, depends_on}], confidence, reason, question}`.
- **Regras:**
  - área com `agents: []` (legal, gamedev, docs) → **HITL "sem especialista"**, sem LLM (areas.yaml, ponto 4);
  - 1 só candidato → esse agente, sem LLM;
  - `confidence < routing.agent_min_confidence` (0,6), ou `mode: clarify` → clarificação, ou HITL na área de risco;
  - `delegation` da área: `auto` (o LLM decide entre 1 agente e plano), `agent` (sempre 1) ou `plan` (sempre plano). A omissão é `auto`;
  - plano: até `budget.max_steps` da área (omissão 6) passos; `depends_on` refere-se a passos anteriores; sem ele, o plano é sequencial.
- **Resposta inválida** (id fora dos candidatos, `depends_on` partido, passos a mais, JSON inválido, HTTP) → `outcome: error` com o motivo. **Nunca** escolhe um agente por omissão: esse era o defeito do `Router.ts`, documentado em D2:31.

### 3. Execução (`--execute`)
A decisão vira um plano do `plan_runner` e corre em `--mode external --worker gemini`:

| Decisão | Plano gerado |
|---|---|
| `agent` | 1 passo (`p1_<action>`, `vertical` do agente). O worker corre-o (AU-23) |
| `plan` | N passos com `depends_on` e `task:` por passo. O worker põe a tarefa no prompt |
| área com `hitl: required` | + gate humano `aprovacao` no fim |
| `hitl` | 1 passo `triagem` com `human_gate`. Pedido durável em `hitl-requests.jsonl` |
| `clarify` / `error` | Não corre; devolve a pergunta ou o motivo |

**Rastreio (R7):**
- **Ledger:** cada chamada do router grava uma linha `call_kind='router'` (`embed_query` para embeddings) no ledger J6. A linha fica no mesmo `run_id` dos passos, em `<run>/token_usage.jsonl`, e vai também para o Supabase se `SUPABASE_*` estiver configurado, como no worker.
- **Ficheiros:** o run guarda a decisão em `route.json`. Cada `route` acrescenta uma linha a `pilots/router-decisions.jsonl` (área, agente/plano, confianças, motivo, tokens), um ficheiro gitignored.

## Como correr

```bash
cd runner
export GEMINI_API_KEY=...        # o andar do agente precisa; a área não

python -m plan_runner route "Faz um post de Instagram para o lançamento da coleção"            # só decide
python -m plan_runner route "Revê o código deste PR" --execute                                  # decide e corre
python -m plan_runner route "..." --execute --out ../pilots/run-router-x --worker gemini --embeddings
python -m plan_runner resume ../pilots/run-router-x --decision approve                          # depois de um gate
```

Código de saída: 0 quando há decisão (incluindo clarificação/HITL); 1 em `error`.

## Validar com o Gemini real

`config/router-golden.yaml` tem 10 pedidos, 3 ambíguos e a regressão (sem área → `horizontal`), com a área, o resultado e o agente esperados. O mesmo ficheiro serve:
- **os testes offline**, onde o LLM responde `llm_reply`;
- **a avaliação real:**

```bash
python -m plan_runner.router eval      # 1 chamada flash-lite por caso que chega ao LLM (~10), tier gratuito
```

Imprime OK/ERR por caso e `N/14 certos`, e sai com 1 se algum falhar. Um ERR na escolha do agente ajusta-se nas `description:` dos agentes (J4) ou nas keywords, não no código.

## Custo

| Andar | Custo por pedido |
|---|---|
| Área por keywords | 0 tokens |
| Área por embeddings (opcional) | 1 `embedContent` (+ 10 na 1.ª vez do processo) |
| Agente | 1 `generateContent` com ~0,3k (área de 2 candidatos) a ~1,2k (marketing, 20 candidatos) tokens de entrada (chars/4, não medido) |

Para comparação, o router plano de produção (MCP) usa ~1,5k tokens por pedido e cresce com cada agente (D2:17). Áreas sem agentes ou com 1 candidato não chamam o LLM.

## Afinar sem código

| Quero… | Mexo em… |
|---|---|
| Que um pedido caia noutra área | `keywords:` da área em `config/areas.yaml` (sem acentos; uma keyword só pode estar numa área) |
| Mais ou menos clarificações | `routing.area_min_confidence` / `routing.agent_min_confidence` |
| Que uma área peça sempre aprovação | `hitl: required` |
| Planos ou 1 agente por área | `delegation: auto` \| `agent` \| `plan` |
| Limitar passos | `budget: {max_steps: N}` |

O validador E7 (`python -m plan_runner.areas`, no CI do runner) rejeita:
- keywords com acentos ou repetidas entre áreas;
- limiares fora de ]0, 1];
- um `fallback_area` inexistente;
- valores inválidos de `budget`, `hitl` ou `delegation`.

## Limites actuais
- **Agente sem LLM real medido:** falta correr o `eval` com a chave (pendente R1 em OPEN-ITEMS).
- **Keywords ingénuas:** não há negação nem contexto ("não é sobre marketing" conta `marketing`). O caso SEO do golden set passa com 0,67, perto do limiar de 0,6.
- **Execução só no engine `native`**, porque é o worker inline (AU-23).
- **Pedidos que só tocam em áreas sem agentes** (legal, gamedev, docs) acabam sempre em HITL até haver agentes (decisão do `areas.yaml`).
- **A clarificação não tem estado:** devolve a pergunta; a resposta do utilizador é um novo `route` com o pedido reformulado.
