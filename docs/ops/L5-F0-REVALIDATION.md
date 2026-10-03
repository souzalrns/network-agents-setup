# L5: revalidação F0 (EXECUTION-PLAN §7, F0)

> **Estado (2026-10-03):**
> - F0.5, F0.7a, F0.8 e F0.9 feitos neste repo, sem escrita em produção.
> - F0.1–F0.3 corridos pelo maestro (resultados em §0).
> - **F0.4 bloqueado tal como estava descrito:** o ingest não é incremental e salta o fim do MANIFEST (§2.1); proposta em §5.
> - F0.7b (medição real) só depois do F0.4.
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

**Queries que faltam** (só leitura; §3): `projecto`, a F0.1b por fonte, `ultima_t6`, e o `agent_id`/`project` da fonte ECC:

```sql
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
| Chunks esperados se as 38 estiverem ingeridas, com o chunker actual | **132**: marketing 84, produto-tech-transversal 15, `marketing+produto-tech-transversal` 11, saude 11, legal 7, imobiliario 4 | `chunk_markdown` sobre os 38 ficheiros (o mesmo chunker do ingest) |
| Comparação com o J3 | J3 = 121 linhas; esperado hoje = 132 | A diferença (11) **não está explicada**: ficheiros alterados ou acrescentados depois de 2026-09-30, ingest não corrido, ou chunker diferente. Explica-se com a query por fonte do F0.1 |
| Linhas inalcançáveis | **11** (`docs/item-13-ai-findability.md` com `agent_id` composto `marketing+produto-tech-transversal`) | O retrieve filtra por igualdade de `agent_id` (`agent-network-mcp/memory/schema.sql:55`), por isso nenhum `kb` as encontra. Já detectado no J3 (`RAG-CANONICAL.md:16`) e **continua no MANIFEST** |
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

Explica provavelmente a diferença 121 (J3) contra 132 (esperado hoje), a confirmar com a F0.1b.

## 3. F0.1–F0.3: queries só de leitura para o maestro

Correr no SQL Editor do Supabase (ou `psql "$DATABASE_URL"`). **São só `SELECT`s**: não escrevem nada. Colar os resultados no PR/conversa; não colar a `DATABASE_URL`.

```sql
-- F0.1  tabela canónica e RPC (J3 base: 121 / 322 / 1)
SELECT count(*) AS projecto FROM knowledge_chunks WHERE project = 'network-agents-setup';
SELECT count(*) AS total    FROM knowledge_chunks;
SELECT count(*) AS overloads FROM pg_proc WHERE proname = 'match_knowledge';      -- esperado 1

-- F0.1b por fonte (explica 121 vs 132 esperados): comparar com o quadro "Hoje"
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
- `projecto = 132` e por fonte igual ao quadro: cobertura completa;
- `< 132`: ver no F0.1b que fontes faltam ou estão antigas;
- `ultima_t6` posterior ao J3: há um writer antigo activo (pára e reporta);
- F0.2 `> 0`: alguém ingeriu à mão (registar).

## 4. O que fica para depois (não é F0.8/F0.9)

- **F0.4:** ver §5 (proposta; não executado).
- **F0.6** (DEV): teste real no conector MCP.
- **F0.7b** (DEV ou CI com segredos): `python -m plan_runner.l5_eval run --out <relatório>.json`, com `MCP_URL` + `MCP_API_KEY`. Antes do F0.4 o esperado é `chunk_hit@4 = 0`.
- **F3:** os buracos de provenance da §1 (locator, modelo do embedding por linha, fontes no `result.json`), a validade (`stale:`) e as 11 linhas inalcançáveis.

## 5. F0.4: proposta de PR (NÃO executado; escrita em produção no merge)

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
4. **(Opcional, decisão separada)** corrigir as §7, §23 e §29 do pack, que estão desactualizadas (CouncilSession e chairman existem desde o Bloco C). Fazê-lo **antes** da primeira ingestão evita meter conhecimento inválido no L5.

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
