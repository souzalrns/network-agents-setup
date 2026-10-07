# L5: revalidação F0 (EXECUTION-PLAN §7, F0)

> **Estado (2026-10-03):**
> - F0.5, F0.7a, F0.8 e F0.9 feitos neste repo, sem escrita em produção.
> - F0.1–F0.3 corridos pelo maestro (resultados em §0).
> - **F0.4:** opção A (P1) aprovada pelo maestro; **PR aberto, sem merge** (§5). O merge escreve em produção.
> - F0.7b (medição real) só depois do F0.4.
>
> **Actualização (2026-10-05):**
> - F0.1, F0.2, F0.3 e F0.4 fechados (PENDENCIAS §7).
> - Para o **gate M1 (F0 verde)** faltam o **F0.6** e o **F0.7b**, os 2 com credenciais que só o DEV tem.
> - **F0.7b PASSOU (2026-10-05):** 18 casos, `source_hit@4` 1.0, `provenance_ok` 1.0, `chunk_hit@4` 0.944, `mrr_chunk` 0.736 (§6.2).
> - **Gate M1 FECHADO (2026-10-05, decisão do maestro):** o F0.7b é prova suficiente. O F0.6 fica **BLOQUEADO**: o conector do Claude.ai não mostra tools (§6.1). O código do F1 (T6a) fica autorizado.
> - Os moldes de evidência e os comandos estão na **§6**.
>
> Base: main `e7a29ae` (pós-#62). Plano: [`docs/architecture/EXECUTION-PLAN.md`](../architecture/EXECUTION-PLAN.md) §7.

## 0. F0.1–F0.3: resultados do maestro (SELECTs, 2026-10-03)

| Passo | Resultado | Leitura |
|---|---|---|
| F0.1 | Overloads de `match_knowledge` = **1** | ✅ A ambiguidade do J3 continua resolvida |
| F0.1 | `knowledge_chunks` total = **322** | Igual ao J3 (322). As linhas do projecto (esperado 121) **estão por confirmar**: falta a query `projecto` e a F0.1b por fonte |
| F0.2 | **8 chunks** com `source ILIKE '%security%'`, todos de **1 fonte**: "ECC security-reviewer + database-reviewer" | Pack importado (ECC) que já estava na tabela; **não é** o `security-agents-stack.md`. **Confirmado: o pack de security não está ingerido.** O `agent_id`/`project` dessas 8 linhas não foi reportado: se for `global`, aparece em qualquer `kb` (incluindo `security`) |
| F0.3 | Última escrita = **2026-10-03 14:25 UTC** | ✅ O L5 está activo. Coincide com o merge do #62 (`e7a29ae`, 11:24 −03 = 14:24 UTC), que tocou em `docs/**/*.md` e disparou o `ingest-knowledge`. Ver §2.1: essa corrida re-embedou os 10 primeiros ficheiros do MANIFEST, não ficheiros novos |
| F0.3 | `ultima_t6` | Não reportado (o passo 3 do J3 fica a meio: falta confirmar que a t6 parou) |

**Queries que faltam** (só leitura; §3): `projecto`, a F0.1b por fonte, `ultima_t6`, o `agent_id`/`project` da fonte ECC e a confirmação de que não há `agent_id` composto:

```sql
SELECT count(*) AS compostos FROM knowledge_chunks WHERE agent_id LIKE '%+%';   -- esperado 0
SELECT agent_id, project, kb, count(*) FROM knowledge_chunks
WHERE source ILIKE '%security%' GROUP BY agent_id, project, kb;
```

## 1. F0.8: provenance que existe hoje, camada a camada

Modelo-alvo (EXECUTION-PLAN §3, ajuste 3): `SOURCE → DOCUMENT → CONTENT → CHUNK → EMBEDDING → RETRIEVAL → ARTIFACT`, com cada camada a apontar para a anterior. Hoje:

| Camada | O que fica registado | Onde | O que falta para o schema mínimo (§3) | Evidência |
|---|---|---|---|---|
| SOURCE | Path no git; `agent_id`; prioridade P0/P1 | MANIFEST fixo, 38 entradas | `uri` canónico, `title`, `publisher`, `document_type`, `retrieved_at`; `jurisdiction`/`effective_*`/`version`/`authority`; `status` (active/superseded/…) | `scripts/ingest_delta.py:32-71` |
| DOCUMENT | `knowledge_sources`: `source_path` (PK), `content_hash`, `agent_id`, `priority`, `last_ingested_at`, `chunk_count`, `git_sha`, `size_bytes` | Supabase | A mais completa das camadas: tem hash, commit e data de ingestão. **Não é lida pelo retrieve** | `runner/plan_runner/supabase_writer.py:6-8,72-74` |
| CONTENT / CHUNK | `knowledge_chunks`: `agent_id`, `source`, `content`, `project`, `content_hash`, `chunk_index`, `kb`, `created_at`, `updated_at` | Supabase (tabela canónica, J3) | **O `locator` (`l.<início>-<fim>`) é calculado pelo chunker mas não é gravado** (a tabela não tem a coluna) | `runner/plan_runner/chunking.py:164,194`; `supabase_writer.py:8-9` |
| EMBEDDING | `vector(768)` com `gemini-embedding-001` | Supabase | O modelo e as dimensões **não são gravados por linha**; são uma convenção do código. Uma troca de modelo não deixa rasto | `runner/plan_runner/embedder.py:9,23-24` |
| RETRIEVAL | `id, content, source, similarity` | RPC `match_knowledge` | O hit que chega ao runner traz só `citation.source`. Ficam de fora `metadata` (sempre `None`), `locator` (sempre `None`) e o `similarity`; os `filters` são aceites mas não têm efeito | `agent-network-mcp/memory/schema.sql:45-58` (`:50`); `runner/plan_runner/mcp_knowledge.py:23-29` |
| ARTIFACT | `pending_steps/<passo>/knowledge_context.md`, com cada excerto como `[Fonte: <source> @ ?]`; evento `knowledge_context_injected` com `hit_count` | Disco do run + `events.jsonl` | As fontes usadas **não ficam estruturadas** no `result.json` (o `meta.context` regista os inputs, não o L5) nem no ledger. O artefacto final (`02-audit.md`) não aponta para os chunks que o fundamentaram | `runner/plan_runner/knowledge.py:121`; `knowledge_wiring.py` (eventos); `external_worker.py:432,442` |

**Resumo F0.8:** hoje a provenance é **só o `source` (path no git)**, de ponta a ponta. A informação mais rica (`content_hash`, `git_sha`, `last_ingested_at`) existe na camada DOCUMENT mas perde-se no retrieve. O `locator` perde-se na escrita. Na camada ARTIFACT a ligação existe apenas como ficheiro de texto. Tudo isto é **entrada do F3**, não do F0: o F0 só mede.

**Validade do conhecimento (§15.8):** o próprio pack de security tem afirmações desactualizadas. A §7 diz que o "CouncilSession de security é desenho futuro" e a §23 diz que o chairman é "futuro". Desde o Bloco C (2026-10-01) existem `runner/plan_runner/council_session.py`, o conselho `security` em `config/councils.yaml` e `agents/meta/chairman.agent.md`. O golden set marca estes casos com `stale:` (sec-07, sec-16). É um exemplo real de "retrieval relevante ≠ retrieval válido".

## 2. F0.9: C8 → J3 → hoje

| Momento | Onde escrevia o ingest | Onde lia o retrieve | Números | Estado | Evidência |
|---|---|---|---|---|---|
| **C8** (dado como fechado, 6/6) | `knowledge_chunks_t6` | `knowledge_chunks` | t6: 110 chunks / 33 fontes; `knowledge_chunks`: 210 / 88 (outro projecto) | **Partido na junção** (AU-19): o que se ingeria não se recuperava. Só 1 fonte sobreposta (`ai-findability.md`, copiada à mão) | `docs/initiatives/STATUS.md:17,236`; `docs/audit/AUDIT-2-cadeia.md:16`; `docs/ops/RAG-CANONICAL.md:9-16` |
| **J3** (2026-09-30, PR #31) | `knowledge_chunks` (canónica) | `knowledge_chunks` | 121 linhas do projecto / 322 no total / 1 `match_knowledge` (ambiguidade de overloads resolvida); retrieve de `geo-agent.md`: SIM | Reparado. **Abertos:** passo 3 (confirmar que o ingest escreve na tabela canónica), passo 5 (teste real no MCP), passo 6 (apagar a t6) | `docs/ops/RAG-CANONICAL.md:1-3,33-42`; `docs/initiatives/OPEN-ITEMS.md:111` |
| **Hoje** (2026-10-03) | idem | idem | Total 322 (= J3); 1 overload; última escrita 14:25 UTC; 8 chunks "security" de 1 fonte ECC importada; **pack de security ausente** | L5 activo. Mas o ingest **não é incremental** e 28 dos 38 ficheiros do MANIFEST nunca são actualizados (§2.1) | §0; este documento |

**Hoje, medido no repo (sem BD):**

| Medida | Valor | Como foi medido |
|---|---|---|
| Entradas no MANIFEST | **38** (todas existem no disco) | `scripts/ingest_delta.py:32-71` |
| Chunks esperados se as 38 estiverem ingeridas, com o chunker actual | **132 chunks = 143 linhas**: marketing 84, produto-tech-transversal 15, item-13 11 (com `agent_id` composto `marketing+produto-tech-transversal`, que o writer grava como **2 linhas por chunk**, uma por agente: `runner/plan_runner/supabase_writer.py`, `insert_chunks`), saude 11, legal 7, imobiliario 4 | `chunk_markdown` sobre os 38 ficheiros (o mesmo chunker do ingest) |
| Comparação com o J3 | J3 = 121 linhas = a t6 inteira (33 fontes): 99 linhas simples + 22 do composto desdobrado (`scripts/migrate_t6_to_knowledge_chunks.sql:13-15`); esperado hoje = 143 linhas | As 5 fontes do MANIFEST que não estavam na t6 e as diferenças de chunking só entram se o ingest lá chegar, e a §2.1 mostra que não chega. Confirma-se com a F0.1b |
| Linhas com `agent_id` composto | ⚠ **Corrigido (2026-10-03):** a 1.ª versão deste doc dizia "11 linhas inalcançáveis". **Está errado.** A migração J3 desdobrou-as (`migrate_t6_to_knowledge_chunks.sql:37-48`), e o writer faz o mesmo desde o J3 (`supabase_writer.py`, `insert_chunks`: "agent_id composto ('a+b') gera uma linha por agente"). Como o item-13 é o 1.º do MANIFEST, é re-ingerido em todas as corridas. **Esperado: 0 linhas com `+` no `agent_id`** (query em §0) | Leitura do writer e do SQL da migração |
| `.md` em `docs/knowledge/` fora do MANIFEST | **33** de 69: design 11, imported-from-production 11, marketing 7, raiz 4 (`README.md`, `imported-from-harnesses.md`, **`security-agents-stack.md`**, `skills-map.md`); inclui READMEs/MANIFEST | Varrimento de `docs/knowledge/**/*.md` contra o MANIFEST. O plano dizia "~31": o número exacto é 33 |
| Pack de security no MANIFEST | **Não** | Daí o F0.4 (D-EP2 = A) |
| Consumidores do L5 (planos com bloco `knowledge:`) | 9 ficheiros; `kb`: marketing 16 blocos, **security 1** (novo, F0.5) | `grep` em `docs/orchestration/**/*.yaml` |
| Prova automática ingest → retrieve | Job `test-rag` (Postgres descartável, embedder falso) | `runner/tests/test_rag_canonical.py`; `RAG-CANONICAL.md:67` |
| Medição de qualidade do retrieve | Golden set security, 18 casos (F0.7a); medição real por fazer (F0.7b) | `config/l5-golden-security.yaml`; `python -m plan_runner.l5_eval` |

### 2.1 Achado: o ingest do workflow não é incremental e nunca chega ao fim do MANIFEST

**Evidência:**
- `.github/workflows/ingest-knowledge.yml` corre `scripts/ingest_apply.py` **sem argumentos** em cada push para main que toque em `docs/**/*.md`, `scripts/ingest_apply.py` ou `scripts/ingest_delta.py`.
- O `ingest_apply.py` percorre **todo** o MANIFEST por ordem (`:246`) e re-embeda cada ficheiro (`apply_one`, `:139-197`).
- **Não compara o `content_hash`** com o que já está gravado, e o passo `ingest_delta.py --dry-run` do workflow é só informativo.
- O orçamento por corrida é `--max-chunks 50` por omissão (`:220-222`); quando é atingido, os ficheiros seguintes ficam `SKIPPED_QUOTA` (`:163-175`).

**Simulação com o chunker real, sobre os 38 ficheiros:**

| | Ficheiros | Chunks |
|---|---:|---:|
| Re-embedados em cada corrida (os 10 primeiros do MANIFEST) | 10 | 50 |
| **Saltados em todas as corridas** | **28** | **82** |

Os 28 saltados incluem `saude/*`, `legal/direito-br-pt.md`, `imobiliario/fipezap.md`, `orquestrador-playbook.md`, `marketing-orquestrador.md`, `critic-criativo.md`, `docs/T6-INGEST-PIPELINE.md`, entre outros. O conteúdo que têm na BD vem da migração da t6 (J3). Se mudarem no git, a BD **não acompanha**.

**Consequências:**
1. **Viola a regra T6** (EXECUTION-PLAN §15.12): a ingestão devia ser incremental e baseada em hash.
2. **Gasta quota do Gemini** a re-embedar 50 chunks iguais em cada push de docs.
3. **O F0.4 "à letra" não funciona:** com o pack (20 chunks) no fim do MANIFEST, a simulação dá `SKIPPED_QUOTA` em todas as corridas. Pô-lo no início funciona para ele, mas empurra mais 2 ficheiros para a zona saltada (30 em vez de 28).
4. O `_kb_for("security")` devolve `"global"` (`scripts/ingest_apply.py:114-122`). O retrieve filtra por `agent_id`, por isso não parte nada, mas a coluna `kb` ficava errada.

Explica provavelmente porque as fontes que não estavam na t6 nunca entraram (121 linhas no J3 contra 143 esperadas hoje), a confirmar com a F0.1b.

## 3. F0.1–F0.3: queries só de leitura para o maestro

Correr no SQL Editor do Supabase (ou `psql "$DATABASE_URL"`). **São só `SELECT`s**: não escrevem nada. Colar os resultados no PR/conversa; não colar a `DATABASE_URL`.

```sql
-- F0.1  tabela canónica e RPC (J3 base: 121 / 322 / 1)
SELECT count(*) AS projecto FROM knowledge_chunks WHERE project = 'network-agents-setup';
SELECT count(*) AS total    FROM knowledge_chunks;
SELECT count(*) AS overloads FROM pg_proc WHERE proname = 'match_knowledge';      -- esperado 1

-- F0.1b por fonte (explica 121 vs 143 linhas esperadas): comparar com o quadro "Hoje"
SELECT source, agent_id, count(*) AS chunks, max(updated_at) AS ultima
FROM knowledge_chunks WHERE project = 'network-agents-setup'
GROUP BY source, agent_id ORDER BY source;

-- F0.2  pack de security (esperado 0: não está no MANIFEST)
SELECT source, agent_id, count(*) FROM knowledge_chunks
WHERE source ILIKE '%security%' OR agent_id = 'security'
GROUP BY source, agent_id;

-- F0.3  passo 3 do J3: o ingest escreve na canónica e a t6 parou
SELECT max(updated_at) AS ultima_canonica FROM knowledge_chunks WHERE project = 'network-agents-setup';
SELECT max(updated_at) AS ultima_t6 FROM knowledge_chunks_t6;   -- não deve ser posterior a 2026-09-30
SELECT source_path, chunk_count, git_sha, last_ingested_at FROM knowledge_sources ORDER BY last_ingested_at DESC LIMIT 10;
```

**Como ler:**
- `projecto = 143` e por fonte igual ao quadro: cobertura completa;
- `< 143`: ver no F0.1b que fontes faltam ou estão antigas;
- `ultima_t6` posterior ao J3: há um writer antigo activo (pára e reporta);
- F0.2 `> 0`: alguém ingeriu à mão (registar).

## 4. O que fica para depois (não é F0.8/F0.9)

- **F0.4:** ver §5 (proposta; não executado).
- **F0.6** (DEV): teste real no conector MCP.
- **F0.7b** (DEV ou CI com segredos): `python -m plan_runner.l5_eval run --out <relatório>.json`, com `MCP_URL` + `MCP_API_KEY`. Antes do F0.4 o esperado é `chunk_hit@4 = 0`.
- **F3:** os buracos de provenance da §1 (locator, modelo do embedding por linha, fontes no `result.json`), e a validade (`stale:`). O ponto das "11 linhas inalcançáveis" foi retirado (ver a correcção no quadro "Hoje"); fica só a query de confirmação.

## 5. F0.4: proposta de PR (opção A aprovada; PR aberto, sem merge)

**O que o F0.4 tem de garantir:**
- o pack entra no `knowledge_chunks` com `agent_id = security`, o mesmo `kb` do F0.5 (`security-audit-demo.plan.yaml`) e do golden set (`config/l5-golden-security.yaml`);
- passa a ser mantido pelo workflow quando mudar no git.

O MANIFEST sozinho não chega (§2.1).

**Conteúdo do PR proposto (opção A, recomendada):**
1. **`scripts/ingest_apply.py` incremental por hash** (regra T6):
   - antes de embedar, ler o `content_hash` de `knowledge_sources` para o `source_path` e saltar o ficheiro (`UNCHANGED`) se for igual;
   - o orçamento de 50 passa a cobrir **só** ficheiros novos ou alterados;
   - nas corridas seguintes, os 28 ficheiros hoje saltados entram por ordem, até 50 chunks por corrida;
   - testes contra o Postgres descartável do job `test-rag` (como em `test_rag_canonical.py`).
2. **MANIFEST:** `("docs/knowledge/security-agents-stack.md", "security", "P0")`.
3. **`_kb_for`:** `security` → `kb = "security"`, em vez de `global`.
4. **Feito no mesmo PR (P2 = A):** pack corrigido (§7, §9, §23, §29 e o preâmbulo) **antes** da 1.ª ingestão.
5. **Ordem no MANIFEST:** o pack fica no grupo P0. Mesmo que todos os P0 anteriores fossem novos, cabe no orçamento da 1.ª corrida (teste `test_pack_cabe_no_orcamento_da_primeira_corrida_no_pior_caso`).

**Efeito no merge (W-prod):**
- o workflow corre;
- a primeira corrida ingere o pack (20 chunks) e começa a recuperar os ficheiros que mudaram, dentro do orçamento;
- os ficheiros iguais ficam `UNCHANGED`, sem gastar embeddings.

**Verificação depois do merge:**
- F0.2 (esperado: 20 linhas `agent_id = security`);
- F0.6 (teste real no MCP);
- F0.7b (`python -m plan_runner.l5_eval run`).

**Alternativas:**
- **B:** só a entrada no MANIFEST + `python scripts/ingest_apply.py --only docs/knowledge/security-agents-stack.md` corrido uma vez pelo DEV. Ingere o pack já, mas o workflow continua a não o actualizar e o problema da §2.1 fica.
- **C:** pôr o pack no **início** do MANIFEST, sem mais nada. Ingere-o em cada corrida, mas empurra mais 2 ficheiros para a zona saltada e mantém o desperdício de quota.

## 6. Gate M1: evidência do F0.6 e do F0.7b (2026-10-05; M1 FECHADO)

O gate M1 (F0 verde) autoriza o código do F1 (spike MarkItDown → T6). Fecha quando as 2 secções abaixo tiverem **evidência real colada neste ficheiro**, num PR. Uma conversa não conta.

**Como fechou (2026-10-05):** o F0.7b tem evidência real (§6.2); o F0.6 ficou BLOQUEADO (§6.1), e o maestro decidiu que o F0.7b é prova suficiente para o M1.

**Segurança:**
- Nunca colar a `MCP_API_KEY`, o URL com credenciais nem tokens.
- Os excertos de resposta vêm do pack de security, que é público no repo.

### 6.1 F0.6: pergunta real no conector MCP, com a fonte citada

**O que prova:** que o caminho completo Claude.ai → conector MCP (`/api/mcp`, com `Bearer`) → `retrieve_knowledge` → `match_knowledge` → `knowledge_chunks` devolve um excerto **com fonte**.

**Atenção:** nenhum dos 33 agentes do MCP tem `agent_id` = `security`. Uma pergunta feita por `ask_agent_network` **não** chega ao pack de security, porque cada agente procura no seu `agent_id` e no `global`. Por isso o teste usa a tool `retrieve_knowledge` com `kb: "security"`.

**Passos (DEV, no Claude.ai com o conector `agent-network-mcp` ligado):**
1. Pedir ao Claude.ai, por exemplo: *"Usa a tool `retrieve_knowledge` com `kb` = `security`, `query` = `Os agentes de segurança podem fazer ataques activos ou alterar a produção?` e `top_k` = 4. Mostra os hits com a `citation.source`."*
2. Copiar para a tabela abaixo a pergunta, o excerto (máximo ~15 linhas) e a fonte citada.
3. **Resultado esperado:** pelo menos 1 hit com `citation.source` = `docs/knowledge/security-agents-stack.md`, e um excerto com "Nunca ataque activo" (caso `sec-01` do golden set).

| Campo | Valor |
|---|---|
| Data (UTC) | 2026-10-05 |
| Ambiente | Claude.ai, conector `agent-network-mcp` (produção `agent-network-mcp-oddn.vercel.app`) |
| Tool e parâmetros | Não chegou a ser chamada |
| Pergunta | Não chegou a ser feita |
| Excerto da resposta | Nenhum. O Claude.ai mostra: "Este conector não possui ferramentas disponíveis." |
| **Fonte citada** (obrigatória para FECHADO) | Nenhuma |
| Veredicto | **BLOQUEADO** (decisão do maestro, 2026-10-05) |

**Causa provável (não verificada do lado da Vercel):**
- a protecção da Vercel bloqueia o `tools/list` antes da função, como fez com o `l5_eval` na 2.ª tentativa do F0.7b (§6.2);
- o conector do Claude.ai só envia o `Authorization: Bearer`, e não o cabeçalho `x-vercel-protection-bypass`.

**Porque o M1 fecha na mesma (decisão do maestro):**
- o F0.7b já provou o que o F0.6 provaria, pelo mesmo caminho (`/api/mcp` com `Bearer` → `retrieve_knowledge` → `match_knowledge` → `knowledge_chunks`) e contra o MCP em produção;
- foram 18 perguntas em vez de 1, e as 18 vieram com a fonte certa (`source_hit@4` 1.0, `provenance_ok` 1.0);
- o que o F0.6 acrescentava era só o elo Claude.ai → conector, e esse é o que está bloqueado.

**Como desbloquear (decisão do maestro; nenhuma escolhida):**
- o bypass como query parameter no URL do conector, nas settings do Claude.ai. Funciona, mas guarda o segredo nas settings do conector;
- outra forma de expor o MCP ao conector, sem a protecção nesse caminho. É uma mudança de produção na Vercel.

Com o desbloqueio, o F0.6 corre com os passos acima, e o S-003 (PENDENCIAS §4) pode ir no mesmo teste.

### 6.2 F0.7b: golden set contra o MCP real

**Comando canónico:** `python -m plan_runner.l5_eval run` (`runner/plan_runner/l5_eval.py`).
- O golden set é o `config/l5-golden-security.yaml`: 18 casos, `kb: security`, `k: 4`, fonte `docs/knowledge/security-agents-stack.md`.
- Verificado em 2026-10-05, sem credenciais:
  - `l5_eval validate` (offline) → `18 casos; 0 erros`;
  - `l5_eval run` sem `MCP_API_KEY` → falha logo (`McpKnowledgeError`), sem medir nada.
- **Alternativa** (não usar para o gate): o teste offline `runner/tests/test_l5_eval.py` prova as métricas com um backend falso. Não mede o MCP real.
- **Regra de regressão (R-011, P-19 mantida pelo maestro, 2026-10-07):** o `run` aplica o limiar do gate M1 a cada medição: `provenance_ok` = 1.0 e `source_hit@4` ≥ 0.8 (15 dos 18 casos).
  - **Abaixo do limiar:** o run imprime `REGRESSAO <métrica> = <valor> (exige …)`, termina com `gate P-19: FALHOU (n)` e sai com o código 1.
  - **Acima do limiar:** imprime `gate P-19: passou` e sai com 0.
  - **Relatório:** o `--out` grava o bloco `gate` (`passed`, `failures` e os 2 mínimos).
  - **Sem alvo:** o `chunk_hit` e o MRR continuam só registados, porque a P-19 não lhes fixou alvo.
  - **Linha de base do F0.7b:** 1.0 / 1.0, por isso passa.

**Passos (DEV, PowerShell, a partir de `network-agents-setup\runner`):**

O cliente MCP é da linha 1.x do pacote `mcp` (o `requirements.txt` fixa `mcp==1.30.0`). Um Python global com a 2.x falha (1.ª tentativa, 2026-10-05: `not enough values to unpack (expected 3, got 2)`), por isso o comando corre num venv com o `requirements.txt`. Desde o PR do branch `fix/F0-7b-mcp-versao`, o cliente pára logo com uma mensagem clara se a versão não for 1.x.

```powershell
py -3.14 -m venv .venv          # ou -3.12; o mcp 1.30.0 suporta 3.10 a 3.14
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -c "import importlib.metadata as m; print(m.version('mcp'))"   # tem de dar 1.30.0
```

Depois, no mesmo terminal:

```powershell
$env:MCP_URL = "https://agent-network-mcp-oddn.vercel.app"   # base; o código acrescenta /api/mcp
$env:MCP_API_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'MCP_API_KEY' -AsSecureString)).Password
$env:VERCEL_PROTECTION_BYPASS = [System.Net.NetworkCredential]::new('', (Read-Host 'VERCEL_PROTECTION_BYPASS' -AsSecureString)).Password
python -m plan_runner.l5_eval run --out "$env:TEMP\f0-7b-report.json"
Remove-Item Env:MCP_API_KEY, Env:VERCEL_PROTECTION_BYPASS
```

Em bash: `MCP_URL=https://agent-network-mcp-oddn.vercel.app MCP_API_KEY=… VERCEL_PROTECTION_BYPASS=… python -m plan_runner.l5_eval run --out /tmp/f0-7b-report.json`, com os segredos lidos sem ficarem no histórico.

#### Vercel "Standard Protection" e o segredo de bypass (2026-10-05)

**O que bloqueia:** o projecto Vercel do MCP tem a **Standard Protection** activa. No plano Hobby não se pode desligar. Segundo o DEV, bloqueia os pedidos ao `/api/mcp` com **400**, antes de chegarem à função; por isso o 400 não aparecia nos logs de runtime nem tinha corpo do servidor.

**Como passa:** com a "Protection Bypass for Automation" da Vercel.
- **Onde se cria o segredo:** Vercel → projecto `agent-network-mcp-oddn` → Settings → Deployment Protection → Protection Bypass for Automation.
- **Onde fica:** só na variável de ambiente local `VERCEL_PROTECTION_BYPASS`, lida como acima. **Nunca** no repo, num `.env` com commit, no histórico do terminal nem em mensagens.
- **O que o cliente faz** (`runner/plan_runner/mcp_knowledge.py`, `_request_headers`):
  - com a variável definida (e não vazia), envia o cabeçalho `x-vercel-protection-bypass` em **todos** os pedidos da sessão MCP;
  - sem ela, não envia nada, por isso os runs locais e os servidores sem protecção ficam iguais.

**Verificação (2026-10-05):**
- 4 testes em `runner/tests/test_mcp_knowledge.py`: sem a variável não há cabeçalho; vazia é ignorada; com ela o cabeçalho vai; o segredo nunca aparece numa mensagem de erro.
- Um run contra um servidor MCP local (`mcp` 1.30.0) que regista os cabeçalhos recebidos: o cabeçalho foi nos 4 pedidos da sessão (`initialize`, notificação, `tools/call`, `tools/list`) e não foi em nenhum sem a variável.

**Rotação:** se o segredo vazar, gera-se um novo no mesmo ecrã da Vercel; o antigo deixa de valer.

**Atenção ao F0.6:** a mesma protecção pode bloquear o conector do Claude.ai, que não envia este cabeçalho. Se o F0.6 falhar com 400, a causa é provavelmente a mesma; decide-se então à parte (por exemplo, uma regra da Vercel para o caminho `/api/mcp`).

**O que colar abaixo:**
- o bloco `summary` que o comando imprime em JSON;
- a lista de casos sem `chunk_rank` (linhas que começam por `--`).

O relatório completo (`--out`) fica fora do repo.

| Campo | Valor |
|---|---|
| Data (UTC) e commit do NAS | 2026-10-05, branch `fix/F0-7b-vercel-bypass` (PR #103: guarda de versão do `mcp` + cabeçalho de bypass da Vercel); contra produção `agent-network-mcp-oddn.vercel.app` (deployment `880d492`). Hora exacta não colada |
| `cases` / `k` | **18 / 4** (como esperado) |
| `chunk_hit@1` · `chunk_hit@3` · `chunk_hit@4` | **0.611** (11/18) · **0.889** (16/18) · **0.944** (17/18) |
| `source_hit@4` | **1.0** (18/18) |
| `mrr_chunk` | **0.736** |
| `no_hits` | **0** |
| `provenance_ok` | **1.0** (todos os hits com `citation.source`) |
| Casos falhados (`--`) | 1 caso sem o excerto nos 4 primeiros (17/18), mas com a fonte certa; o ID do caso não foi colado |
| Veredicto | **PASSOU.** O retrieve real devolve sempre a fonte certa, com proveniência, e o excerto certo nos 4 primeiros em 17 de 18 perguntas. Cumpre as 3 opções da P-19 (A: `provenance_ok` 1.0 e `source_hit@4` ≥ 0.8; C: mais `chunk_hit@4` ≥ 0.7 e `mrr_chunk` ≥ 0.5) |

**Resumo colado pelo DEV (2026-10-05):**

```json
{"kb": "security", "source": "docs/knowledge/security-agents-stack.md", "k": 4, "cases": 18,
 "chunk_hit@1": 0.611, "chunk_hit@3": 0.889, "chunk_hit@4": 0.944, "source_hit@4": 1.0,
 "mrr_chunk": 0.736, "no_hits": 0, "provenance_ok": 1.0}
```

**O que este run também prova:** o caminho completo cliente Python → Vercel (com a Standard Protection passada pelo cabeçalho de bypass) → `/api/mcp` → `retrieve_knowledge` → `match_knowledge` → `knowledge_chunks` funciona em produção, depois das 2 tentativas falhadas (versão do `mcp` e protecção da Vercel).

**Critério de fecho:** métricas registadas aqui, num PR. O limiar mínimo para o M1 é uma decisão do maestro (**P-19**, PENDENCIAS §10). Até lá:
- a medição fica registada como linha de base;
- o M1 só se declara verde se a P-19 estiver decidida e cumprida.

