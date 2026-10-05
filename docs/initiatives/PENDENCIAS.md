# PENDÊNCIAS: documento único de estado

> **Este é o ÚNICO documento com o estado dos pendentes** do `network-agents-setup` (e das partes do `agent-network-mcp` que este repo acompanha).
> **Criado em 2026-10-03**, por decisão do maestro, a partir da auditoria cruzada (PR #65), sobre `main` `e7a29ae`.
> **2.ª ronda (2026-10-03):** actualizado sobre `main` `2b27f66`, depois do merge dos PRs #63–#78. As evidências novas citam essa `main`; as siglas `P:`/`O:`/`E:` continuam ancoradas em `e7a29ae` (§0, item 7).
> **Gate M1 FECHADO (2026-10-05, decisão do maestro):** o F0.7b é prova suficiente (18 de 18 com a fonte certa contra produção, `provenance_ok` 1.0). O F0.6 passa a BLOQUEADO: o conector do Claude.ai não mostra tools (causa provável: a protecção da Vercel no `tools/list`, sem o cabeçalho de bypass); o S-003 fica com o mesmo bloqueio. O código do F1 (T6a, spike MarkItDown) fica autorizado.
> **F0.7b PASSOU (2026-10-05):** 18 casos contra produção, `source_hit@4` 1.0, `provenance_ok` 1.0, `chunk_hit@4` 0.944, `mrr_chunk` 0.736 → F0.7b FECHADO. Para o gate M1 falta o F0.6 (e a decisão da P-19, que o resultado já cumpre em qualquer opção).
> **F0.7b, 2.ª tentativa (2026-10-05):** 400 da Vercel "Standard Protection"; o cliente passa a enviar o cabeçalho de bypass se a env `VERCEL_PROTECTION_BYPASS` existir (PR do branch `fix/F0-7b-vercel-bypass`). Atenção: a mesma protecção pode bloquear o conector do Claude.ai (F0.6).
> **F0.7b, 1.ª tentativa (2026-10-05):** falhou por `mcp` 2.x no ambiente do DEV (o repo fixa 1.30.0); guarda de versão e checklist com venv (PR do branch `fix/F0-7b-mcp-versao`); novo W-010 (migração para a 2.x).
> **Gate M1 (2026-10-05, `main` `098034e`):** moldes de evidência do F0.6 e do F0.7b (`L5-F0-REVALIDATION.md` §6); S20 com caminho e prazo proposto (2026-10-12); novas P-19 (limiar do F0.7b) e P-20 (causa do R-005). M1 incompleto; o F1 código continua bloqueado.
> **Portfólio para recrutadores (2026-10-05, `main` `5736621`):** H-003, W-009, H-005 e H-006 → FECHADO (#99 e MCP #18 merged; corrida #182 com os pins novos); `docs/PORTFOLIO.md` expandido; bloco "For recruiters / visitors" no README.
> **"Resolve o que for possível" (2026-10-05, `main` `4056fb5`):** R-004 e W-008 → FECHADO; H-003 (re-pin Node 24, NAS e MCP), W-009, H-005 e H-006 → EM CURSO (PR do branch `docs/resolver-possiveis` e PR MCP #18); S-004 só espera pelos alertas que o DEV vê; GIF do quickstart.
> **Vitrine para recrutadores (2026-10-05):** `docs/PORTFOLIO.md` da plataforma (o de marketing passa a `docs/PORTFOLIO-MARKETING.md`); evidência no H-01; novo H-006 (README do MCP).
> **Gate F0, 2.ª ronda de SELECTs (2026-10-05, `main` `9531ec3`):** F0.1 e R-002 → FECHADO (F0.1b filtrada); AU-22 → FECHADO (#96 merged); R-005 sobe para Alta (201 linhas do MCP com `kb` = marketing por omissão); F0.4 com a nota do `--max-chunks`. No F0 faltam o F0.6, o F0.7b e o F0.12 (opcional).
> **AU-22, 2.ª metade da P-10 (2026-10-05, `main` `c15a6d8`):** AU-22 → EM CURSO (PR do branch `fix/AU-22-remover-on-fail-max-replans`); novo W-009 (exemplo de budget com um campo fora do schema); 6 prompts com `on_fail` registados no B1-bis-C.
> **SELECTs do F0 (2026-10-05, `main` `81e6364`):** F0.3 e R-003 → FECHADO; C-2 → FECHADO (o MCP #16 já tinha entrado a 2026-10-03; a linha estava desactualizada); novo R-005 (`kb` errado na fonte ECC); F0.2 (já fechado) e AU-50 com a evidência nova; o F0.1 continua EM CURSO (falta a contagem `projecto` e a F0.1b com o filtro `project`, que fecham o R-002).
> **Pós-merge (2026-10-05, `main` `92cc762`, merges #91 e #93):** H-01 continua EM CURSO (as partes 4, 5 e 6 entraram no #93; faltam as partes 1, 2 e 3); F2 com a evidência do Agent-Reach (#91). Contagens sem alteração.
> **Pós-merge (2026-10-05, `main` `a52fc74`, merges #88, #89, #90 e #92):** E-003 → FECHADO (#90); AU-22 → ABERTO (o `done_when` entrou no #90; falta a 2.ª metade da P-10); H-003 com a mitigação do #89; H-01 EM CURSO (PR #93).
> **AU-22/E-003 (2026-10-05, `main` `492acff`):** P-18 = C; AU-22 e E-003 EM CURSO (PR #90); novos AU-22b e W-008.
> **Decisões confirmadas (2026-10-03, `main` `e4a9f5e`):** P-10 e P-12 a P-15 = A, com consulta cruzada; INIT-094, ING-5 e ING-6 → OBSOLETO; a condição da P-18 devolveu-a a A/B/C.
> **Sessão "continuação operacional" (2026-10-03, `main` `c9edd72`):** R-004 com PR (MCP #15); C-2: lado DB feito pelo DEV, lado repo com PR (MCP #16); E-003 → P-18; H-002 e H-003 com o bloqueio actualizado; F0.6 e F0.7b deixam de esperar pelo F0.4 (fechado no #64; o F0.7b passa a ABERTO). Depois, a pedido do maestro: S-004 (PR MCP #17), factos do README no H-01 (§4.1) e V40 (ponteiros que o H-001 deixou). Auto-auditoria: H-005 (STATUS do MCP desactualizado); `pnpm audit` do NAS = 0 (A22).
> **Revisão pós-merge (2026-10-03):** `main` `d79d7be` (NAS, merges #79 e #81) e `d635945` (MCP, merges #11–#14); §10 com as decisões P-1 a P-9.
> Substitui, **para o estado**, os três documentos que ficam históricos, sem alterações de conteúdo (só uma linha de aviso no topo):
> - `docs/audit/PLANO-DE-ACAO.md` (P);
> - `docs/initiatives/OPEN-ITEMS.md` (O);
> - `docs/architecture/EXECUTION-PLAN.md` (E): continua a ser o **plano** (o que fazer e porquê); só o seu estado passa para aqui.
>
> **Contagens:**
> - **104 itens vivos** (§4): ABERTO 56, EM CURSO 5, BLOQUEADO 43;
> - **105 linhas de histórico** (§7): 84 fechadas, 21 obsoletas;
> - **40 contradições resolvidas** (§8): 26 da auditoria #65 + 14 novas;
> - **20 decisões** em A/B/C (§10): P-1 a P-10, P-12 a P-15 e P-18 decididas pelo maestro; pendentes P-11, P-16, P-17, P-19 e P-20.

## 0. Como usar este documento

**Para IAs** (Claude Code, Grok, GPT, futuras):
1. **Ler o estado só aqui.** Se um documento antigo (P, O, E) disser outra coisa, vale este (os antigos têm o aviso HISTÓRICO).
2. **Procurar por ID** na tabela §4 (vivos) ou §7 (fechados/obsoletos). Se só conhecer um ID antigo (ex.: `A8`, `R1`, `E5`), procurar no **índice de aliases** (§11).
3. **Ler a tabela por colunas:** as 10 colunas de §4 são fixas e todas as linhas têm exactamente essas colunas. Separador `|`; nenhuma célula contém `|`. As 8 primeiras são as pedidas pelo maestro; as 2 últimas (`IDs antigos`, `Verif.`) foram acrescentadas.
4. **Para propor um item novo:**
   - escolher o prefixo (§3) e o próximo número livre do formato `<prefixo>-<NNN>`;
   - preencher as 10 colunas, com evidência (`ficheiro:linha`, PR ou teste);
   - nunca reutilizar um ID, nem um antigo.
5. **Para fechar um item:** seguir o §9. Nunca marcar FECHADO sem PR ou teste citado.
6. **Para cortar um item:** não se corta. Propõe-se em A/B/C (§10) e espera-se a decisão do maestro.
7. **Siglas de evidência** (linhas de `main` `e7a29ae`):
   - `P:` = PLANO-DE-ACAO;
   - `O:` = OPEN-ITEMS;
   - `E:` = EXECUTION-PLAN;
   - `A5` = `docs/audit/AUDIT-5-itens.md`;
   - `ST:` = `docs/initiatives/STATUS.md`;
   - `L5F0` = `docs/ops/L5-F0-REVALIDATION.md` (PR #63);
   - `AI:` = `docs/architecture/ingestion-audit/AUDIT-INGESTION.md`;
   - `RC:` = `docs/ops/RAG-CANONICAL.md`;
   - `EP:` = `docs/initiatives/EXECUTION-PROMPTS.md`.
   - Nos ficheiros actuais de P, O e E, a linha HISTÓRICO acrescentou 2 linhas no topo: para abrir a linha citada no ficheiro de hoje, somar 2 (ou usar `git show e7a29ae:<ficheiro>`).

**Para humanos (revisão):**
1. Começar pelo **§5 (por dono)**: a lista do DEV é o que só tu podes fazer.
2. O **§10** tem as decisões que esperam por ti, todas com recomendada.
3. A coluna **Verif.**: `NÃO VERIFICADO` quer dizer que o estado não foi confirmado nesta consolidação (ex.: precisa de SSH, consola ou Supabase).
4. O **§8** mostra, para cada contradição antiga, quem estava errado e porquê.

## 1. Regras

1. **Este é o ÚNICO documento com o estado dos pendentes.** P, O e E são históricos: não se apagam e não se actualizam. O E continua a ser o plano.
2. **Cada item tem:** ID único, título, tipo, estado, dono, severidade, bloqueio, evidência, IDs antigos e verificação.
3. **Sem duplicados:** um item que aparecia em 2 ou 3 documentos é **uma** linha; os outros IDs vão para a coluna "IDs antigos".
4. **Fechar = citar o PR ou o teste que fechou** (§9). Itens que deixaram de fazer sentido por decisão ficam **OBSOLETO**, com a decisão citada.
5. **Os estados vivos são só ABERTO, EM CURSO e BLOQUEADO.** FECHADO e OBSOLETO vivem no §7.
6. **Item EM CURSO com PR aberto:** o estado só passa a FECHADO depois do merge.
7. **Escrita em produção** (Supabase, Vercel, workflow que escreve) é sempre decisão do DEV, mesmo que o código seja do CLAUDE.
8. **Um erro de um documento antigo corrige-se no §8**, com o padrão V*n*: onde estava, o que é verdade, e a evidência.

## 2. Legenda

| Campo | Valores | Significado |
|---|---|---|
| Tipo | BUG · FALTA-LIGAR · FALTA-DECIDIR · FALTA-CONSTRUIR · DOC-ERRADO · FALTA-TESTE | Natureza do trabalho que falta (o mesmo vocabulário do AUDIT-5) |
| Estado | ABERTO · EM CURSO · BLOQUEADO · FECHADO · OBSOLETO | EM CURSO = há trabalho feito (PR aberto ou passo parcial); BLOQUEADO = depende de outro item ou decisão, citado na coluna Bloqueio; OBSOLETO = deixou de fazer sentido por uma decisão citada |
| Dono | CLAUDE · DEV · AMBOS | CLAUDE = uma IA consegue fazer sozinha no repo; DEV = precisa de humano (decisão, credencial, consola, produção); AMBOS = a IA faz e o DEV valida ou executa uma parte |
| Sev | Crítica · Alta · Média · Baixa | Herdada do documento de origem quando existia; nos IDs novos é proposta por esta consolidação (revisível) |
| Verif. | VERIFICADO · NÃO VERIFICADO | **Acrescentado.** Se o estado foi confirmado com evidência (repo, PR, teste ou auditoria datada) ou não |

## 3. Prefixos de ID

**Formato dos IDs novos:** `<prefixo>-<NNN>` (3 dígitos, ex.: `R-001`). Nenhum documento antigo usa este formato (verificado por `grep -E "\b[A-Z]-[0-9]{3}\b" docs/` → 0 ocorrências), por isso **não pode colidir**. Os IDs antigos únicos mantêm-se tal como estavam (decisão P-1).


| Prefixo | Âmbito | Nota |
|---|---|---|
| F | Fases F0–F6 do EXECUTION-PLAN (e passos F0.x) | Já existiam no E; ficam. Os F1–F22 antigos do STATUS (ferramentas, sessão 09-14) **não** são fases: estão como aliases dos I*/G* |
| R- | RAG / L5 | Novos `R-NNN`. O R1–R4 do router e o R1–R13 do AUDIT-1 **não** são RAG (ver W-) |
| S | Security | Antigos S* do STATUS (ex.: S20, S27) e SEC-* mantêm-se; novos `S-NNN` |
| C- | Council (conselhos) | Mantêm-se C-1/C-2/C-3 (Bloco C). **C-2 ≠ C2** (o C2 antigo é o EX-C2, fechado) |
| M- | Meta-agentes (Fase 2) e organização | Novos `M-NNN`. Os M3–M7 antigos (STATUS) mantêm o seu significado |
| D | Dependabot / dependências | Não houve itens novos com D-. Os D5/D6 antigos (model_tier, max_cost) mantêm-se; D3/D4 (DeepEval/Ragas) colidiam com as decisões D3/D4 → Q-001/Q-002 |
| H- | Housekeeping (docs, IDs) | Novos `H-NNN`. Os H1–H4 antigos são backlog (dashboard, JARVIS…) e mantêm-se |
| E- | Estrutura / domínios | Novos `E-NNN`. E1–E7 conectores → ING-1..7 (D-EP6); E1–E15 decisões do P §13.2: as abertas que colidiam → E-001/E-002; o E15 mantém-se (único) |
| T- | **Acrescentado:** tokens / custo / medição | O objectivo n.º 1 merece um prefixo próprio |
| W- | **Acrescentado:** worker / runtime / router / planos | Separa o runtime do RAG (o R1 do router colidia) |
| Q- | **Acrescentado:** qualidade / avaliação (EXECUTION-PLAN §15.12) | Recebe o DeepEval/Ragas (antes D3/D4) |
| L4- | Memória L4 (série existente) | L4-1b, L4-2, L4-3 já existiam; L4-4 é novo |
| ING- | Conectores de ingestão (D-EP6) | Já decididos; os que coincidem com F1/F1b/F2/AU-44/INIT-093 aparecem como alias |
| AU-, EX-, INIT-, SEC-, B*, A*, G*, H*, I*, J*, P*, U* | Séries antigas | Mantêm-se quando são únicas; quando colidem, a linha usa um ID novo e cita o antigo na coluna "IDs antigos" |


## 4. Tabela única (104 itens vivos)

Ordenada por grupo: F → R → S → C → T → W → M/L4/Q → E → H → backlog (G/H/I).


| ID | Título | Tipo | Estado | Dono | Sev | Bloqueio | Evidência | IDs antigos | Verif. |
|---|---|---|---|---|---|---|---|---|---|
| F0.6 | Passo 5 do J3: teste real no conector MCP (a resposta tem de citar a fonte) | FALTA-TESTE | BLOQUEADO | DEV | Média | **Conector do Claude.ai sem tools** (2026-10-05, no Claude.ai: "Este conector não possui ferramentas disponíveis"). Causa provável: a protecção da Vercel bloqueia o `tools/list`, e o conector não envia o cabeçalho `x-vercel-protection-bypass`. Desbloqueia com o bypass como query parameter nas settings do conector (posto de parte por agora: guarda o segredo no conector) ou com outra forma de expor o MCP ao conector | RC:69-70; E §7 F0; **decisão do maestro (2026-10-05): BLOQUEADO**, e o gate M1 fecha com o F0.7b como prova suficiente (o mesmo `retrieve_knowledge` contra produção: 18 de 18 com a fonte certa, `provenance_ok` 1.0). Registo em `docs/ops/L5-F0-REVALIDATION.md` §6.1. Tem de usar a tool `retrieve_knowledge` com `kb` = `security`: nenhum dos 33 agentes do MCP tem `agent_id` = `security`, por isso o `ask_agent_network` não chega ao pack | J3 passo 5 | VERIFICADO |
| F0.12 | Passo 6 do J3: apagar a `knowledge_chunks_t6` (irreversível, com backup; opcional) | FALTA-DECIDIR | ABERTO | DEV | Baixa | Backup + decisão (o F0.3 fechou: a t6 parou a 2026-09-29, com 110 linhas) | RC:72-75; E §7 F0 | J3 passo 6 | VERIFICADO |
| F1 | Ingestão universal: ADR do contrato *Universal Ingestion & Research Primitives* (pode avançar já) + spike MarkItDown → T6 (só com o F0 verde; pin `>=0.1.4` e mitigações) | FALTA-CONSTRUIR | EM CURSO | CLAUDE | Alta | ADR aceite (#81; §10 P-13 = A). Gate M1 fechado (2026-10-05). Spike em curso: T6a merged (#105). Cadeia T6b → T6f (fixtures por formato, segurança de entrada com a mitigação 3, encaixe no T6) acompanhada em `docs/initiatives/PENDENCIAS_T6.md` | E §7 F1; AI:140-156; PR #81 (`docs/architecture/adr/ADR-INGESTION-PRIMITIVES.md`); **T6a (2026-10-05):** `scripts/ingest_document.py` (path → `content`, `source_meta`, `warnings`), pin `markitdown[docx,pdf,xlsx]>=0.1.4` em `runner/requirements-ingest.txt`, `runner/tests/test_ingest_document.py` (26 testes de contrato; 6 smoke com o MarkItDown real, em skip documentado no CI); PR #105 (merged, `99b2cee`); **T6b (2026-10-05):** fixture PDF sintética versionada + gerador reprodutível (`runner/tests/fixtures/ingest/pdf/`), `runner/tests/test_ingest_fixtures.py`, job `test-ingest` no CI (MarkItDown real; `INGEST_TEST_REQUIRED=1`); PR #106; **T6c (2026-10-05):** fixtures DOCX e XLSX sintéticas + geradores reprodutíveis, aviso `xlsx_nan_cells` no `ingest_document`; PR #107; **T6d (2026-10-05):** mitigação 3 do ADR §5 (processo filho com timeout e `RLIMIT_DATA` 1 GiB, medido), códigos `timeout` e `memory_limit`, ZIP corrompido distinguido de formato errado, `runner/tests/test_ingest_security.py`, `docs/ops/INGEST-DOCUMENT.md`; PR #108; **T6e (2026-10-05):** S4 do ADR sem a entrada no MANIFEST (`write_ingested`, `validate_ingested` da regra 3, `uri` relativo ao repo), caminho completo provado contra Postgres + pgvector no CI (`test_ingest_pipeline_rag.py`); branch `feat/t6e-pipeline-integration` | ING-2 (= "E2" conector, O:20) | VERIFICADO |
| F1b | Docling, só se o benchmark do F1 o justificar (`docling-core>=2.48.4`) | FALTA-DECIDIR | BLOQUEADO | CLAUDE | Baixa | Resultado do F1 | E §7 F1b; AI:189 | ING-3 | VERIFICADO |
| F2 | Web research universal (discover/fetch) a partir do `scrape.yml` existente; Crawl4AI `>=0.9.3` só se o superar | FALTA-CONSTRUIR | BLOQUEADO | CLAUDE | Média | F1 | E §7 F2; AI:304; **candidato a adaptador de `fetch` (2026-10-05): Agent-Reach** (`Panniantong/Agent-Reach`, MIT, v1.5.0, commit `a19a171`): não acede por si, escolhe e testa ferramentas que já existem (Jina Reader, `yt-dlp`, `feedparser`, `gh`, Exa…); dependências `requests`, `feedparser`, `yt-dlp`, `pyyaml`; o `cookie_extract.py` lê cookies do browser localmente, sem envio de rede; o `install` usa `pipx`/`npm -g` (não corrido). Instalado num venv isolado: `agent-reach doctor` = 2/16 canais (RSS, web). **NÃO VERIFICADO:** os canais reais, porque a política de rede da sessão cloud recusa `r.jina.ai`, `www.youtube.com` e `github.com` (403 do proxy). Canais com cookies (Twitter/X, Reddit, XiaoHongShu, Facebook, Instagram) precisam de decisão de segurança antes de qualquer uso | ING-1 | VERIFICADO |
| F3 | Provenance formal + validade/conflitos + source authority + golden set alargado + cobertura dos 33 ficheiros fora do MANIFEST, pack a pack (D-EP2) | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Alta | F0–F2 | E §7 F3; L5F0 §1–§2 (PR #63) | — | VERIFICADO |
| F4 | `config/marketing-capabilities.yaml` validado no E7 + maturidade de capability | FALTA-CONSTRUIR | BLOQUEADO | CLAUDE | Média | F3 | E §7 F4 | — | VERIFICADO |
| F5 | Validação E2E de uma capability com **run real** | FALTA-TESTE | BLOQUEADO | AMBOS | Alta | F4 | E §7 F5 | — | VERIFICADO |
| F6 | UM domínio de prova, com o Domain Onboarding Cost medido; escolhido só depois do F5, com uso real | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Média | F5 + D-EP8 | E §7 F6 e §9.5 (D-EP8); P:320 (AU-35) | AU-35; B1 (ST:100, "2.º domínio"); R2 (O:164) | VERIFICADO |
| R-001 | Investigar e documentar a tabela `knowledge_log` (existe no Supabase, 7 colunas, sem dono) | DOC-ERRADO | BLOQUEADO | AMBOS | Baixa | DEV corre as 5 queries só de leitura de `docs/ops/KNOWLEDGE-LOG.md` §3; depois A/B/C (§4 do doc) | #77 (`docs/ops/KNOWLEDGE-LOG.md`: 0 leitores/escritores nos 2 repos); A5 §5.2 (B12); O:22 (E9) | B12 (ST); E9 (O:22) | VERIFICADO |
| R-005 | Reclassificar o `kb` das 201 linhas do MCP (`project` NULL), todas com `kb` = marketing por omissão; as que não são de marketing (ex.: as 8 da fonte ECC "security-reviewer + database-reviewer", que vão para security) ficam com o `kb` errado. O destino do `agent_id` da ECC fica a confirmar | BUG | BLOQUEADO | CLAUDE | Alta | F3 (provenance formal) | SELECTs do maestro (2026-10-05, 2.ª ronda): `SELECT kb, count(*) … WHERE project IS NULL GROUP BY kb` → marketing = 201, sem outro valor. **Causa confirmada:** `kb text DEFAULT 'marketing'` (`scripts/rag_schema.sql:51`), e o insert do MCP não define o `kb` (`ANM:lib/knowledge.js`, `ingestDocument`). Enquanto a causa não for corrigida, cada novo ingest do MCP grava `marketing`. 201 = 322 − 121: as linhas do MCP são as mesmas da revalidação de 2026-10-03 (L5F0 §0). Hoje o `match_knowledge` filtra só por `agent_id` (`scripts/rag_schema.sql:68`), por isso o `kb` errado ainda não muda a pesquisa; passa a mudar quando o retrieve filtrar por `kb` (F3). 1.ª ronda: a fonte ECC tem `agent_id` = revisor-codigo, `project` NULL e `kb` = marketing; `security-reviewer` não é um `agent_id` existente (o pack de security usa `security`, `scripts/ingest_delta.py:40`; o `docs/knowledge/imported-from-production/MANIFEST.md:9` mapeia a fonte para `revisor-codigo`). Severidade Alta por decisão do maestro (2026-10-05). Sucessor do R-003; correcção da causa (o insert do MCP passar a definir o `kb`) em A/B/C na §10 P-20 | — | VERIFICADO |
| AU-44 | Reels/transcrições (yt-dlp + faster-whisper → `transcripts`) sem template nem ponte para o RAG | FALTA-LIGAR | ABERTO | AMBOS | Média | Candidato do F1 | P:329; E §9.2; `agent-network-mcp/.github/workflows/transcribe.yml` | ING-4 | VERIFICADO |
| S20 | VM Oracle: o bridge-worker usa a chave antiga e falha com 401 | BUG | ABERTO | DEV | Alta | Acesso SSH (só o DEV). **Caminho:** `ANM:CONFIGURACAO_VM_BRIDGE_WORKER.md`, passos de recuperação, passo 4: pôr a `SUPABASE_SERVICE_ROLE_KEY` actual (rodada a 2026-09-19) onde o `pm2` a lê, e depois `pm2 restart bridge-worker --update-env` e `pm2 save`. **Prazo proposto: 2026-10-12** (opção B no PROGRESS de 2026-10-05; a confirmar pelo DEV). Se não for corrigido até lá, o DEV decide entre adiar com uma data nova e desligar a funcionalidade do README do MCP | P:347; O:32; E:794; ST:42 | J2 | NÃO VERIFICADO |
| S27 | Oracle A1: reduzido para 2 OCPU/12 GB? (o S19 diz 24 GB) | FALTA-DECIDIR | ABERTO | DEV | Média | Consola Oracle | ST:46; E:795 | — | NÃO VERIFICADO |
| S19 | Oracle Free Tier: decidir o âmbito de uso (desbloqueia Q-001/Q-002) | FALTA-DECIDIR | ABERTO | DEV | Média | S27 + acesso SSH | P:360; O:65; ST:41 | — | VERIFICADO |
| S21 | Screenshots da migração GCP→Oracle podem conter a chave antiga | FALTA-DECIDIR | ABERTO | DEV | Baixa | Confirmação humana | O:34; A5 §5.2 | — | VERIFICADO |
| S28 | Warning de cache no `transcribe.yml` (repo MCP) | BUG | EM CURSO | DEV | Baixa | 1 run limpo do `transcribe.yml` (DEV); o merge do MCP #12 já foi feito | A5 §5.2 (ST:99); causa no log do run MCP #108 (job 108666727482); PR MCP #12; V36 | — | VERIFICADO |
| S32 | Os agentes não se descobrem entre si (por desenho): confirmar ou reverter `AGENTS.md:15` | FALTA-DECIDIR | ABERTO | DEV | Média | Decisão | A5 §5.2 (ST:71); P §9 (S32/F7) | — | VERIFICADO |
| SEC-3 | Red-team lab dos agentes (`agent_redteam_lab`): só em lab, nunca no runner de produção | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Baixa | Adiado por decisão (deferred) | `config/security-capabilities.yaml:78`; O:260; E §9.1 | — | VERIFICADO |
| B2b | Ferramentas do auditor: faltam Trivy (`vuln`) e OSV-Scanner; gitleaks e semgrep já correm no CI | FALTA-TESTE | EM CURSO | AMBOS | Média | Rede para `api.osv.dev`/`mirror.gcr.io` | P:355; O:38; `.github/workflows/security-scan.yml`; E §2.3 | A10 | VERIFICADO |
| B2c | Converter os achados de `SECURITY-AUDIT*.md` num backlog com dono e estado (a triagem do semgrep já está feita, SEC-2d) | FALTA-DECIDIR | ABERTO | AMBOS | Média | Decisão de prioridade | P:355; O:39; A5 §5.2 | A11 | VERIFICADO |
| A9 | Lockfile Python (`uv.lock`) | FALTA-CONSTRUIR | ABERTO | AMBOS | Média | Rede para `uv lock` | P:353; O:37; A5 §5.5 #20 | checklist #20 | VERIFICADO |
| A12 | Criptografia em repouso: decidir se há dado sensível | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão | O:40; A5 §5.5 #5 | checklist #5 | VERIFICADO |
| A13 | RBAC/identidade no runtime (Identity = gap na matriz P0) | FALTA-DECIDIR | ABERTO | DEV | Média | Decisão do modelo; EX-C3/EX-C4 | P:354; O:41; E §4.1 | checklist #7 | VERIFICADO |
| A19 | Restringir uploads: o alvo (`extrair-imagem`) está no repo MCP; mover o item para lá | DOC-ERRADO | ABERTO | DEV | Baixa | Decisão | O:43; A5 §5.4 | checklist #16 | VERIFICADO |
| A22 | Alertas do Dependabot (o O diz 9; em 03/10 havia 0 PRs abertos; os alertas estão por confirmar) | FALTA-TESTE | ABERTO | DEV | Média | Aba Security do GitHub (a API devolve 403 a esta sessão); decisão §10 P-5 | O:44; E:800; A5 §5.4 ("A22 = M8 fechado"); `pnpm audit` do workspace TS (2026-10-03): 0 vulnerabilidades (não substitui os alertas do Dependabot nem cobre as dependências Python) | M8 | NÃO VERIFICADO |
| EX-C3 | Adoptar AgentMesh (identidade/delegação) | FALTA-DECIDIR | ABERTO | DEV | Média | Decisão de dependência | P §9 (EX-C3); O:51 | C3 (O:51) | VERIFICADO |
| EX-C4 | Adoptar Cedar (policy engine) | FALTA-DECIDIR | ABERTO | DEV | Média | Decisão de dependência | P §9 (EX-C4); O:52 | C4 (O:52) | VERIFICADO |
| B16 | `ActionReceipt` com o contrato ADR-001 completo | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Baixa | EX-C3/EX-C4 | A5 §5.2 (ST:111,201) | G7 (ST) | VERIFICADO |
| AU-25 | `mcp/plan_runner` em `moderate` por omissão autoriza `run_plan` sem chave | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão (omissão `strict` fora de stdio) | `mcp/plan_runner/mcp_plan_runner/policy.py:33`; P:310 | — | VERIFICADO |
| B1-bis-C | Encurtar skills/prompt-base (meta <9k no `seo-article-demo`; base medida 10 136) | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Média | Ordem do maestro; depois de F0–F3 | P §6 #12; O:222; E §14.2; 6 prompts de agentes ainda dizem "Falha → `on_fail`" (`agents/design/ui`, `ux` e `ux_writer`; `agents/marketing/research`; `agents/security/security_report` e `security_triage`). O AU-22 não os mudou, para não mexer na base medida do `seo-article-demo`; reescrever aqui | — | VERIFICADO |
| T-001 | Medir o custo do pack Claude (`revisor-codigo`, `guia-tdd`) antes de cortar | FALTA-TESTE | ABERTO | AMBOS | Baixa | Run real (`GEMINI_API_KEY`) | E §9.2 | — | VERIFICADO |
| T-002 | Medir o conselho `security` no 1.º uso real | FALTA-TESTE | ABERTO | AMBOS | Baixa | 1.º uso real | E §9.2; `docs/ops/COUNCIL.md` | — | VERIFICADO |
| T-003 | Confirmar a 1.ª linha real em `token_usage` (MCP de produção) | FALTA-TESTE | ABERTO | DEV | Baixa | Acesso ao Supabase | O:118 | J6 (sub-item) | NÃO VERIFICADO |
| W-001 | `router eval` com o Gemini real: medir a escolha do agente | FALTA-TESTE | ABERTO | DEV | Média | `GEMINI_API_KEY` | O:163; E:784; P §10 (ressalvas) | R1 (Bloco B; colide com R1 do AUDIT-1) | VERIFICADO |
| W-003 | Robustez das keywords do router (negação, pesos) | FALTA-CONSTRUIR | BLOQUEADO | CLAUDE | Baixa | W-001 (casos reais) | O:166 | R4 | VERIFICADO |
| W-004 | Ledger central: as linhas do worker também no Supabase | FALTA-LIGAR | ABERTO | DEV | Média | Escrita em produção (DEV) | O:149 | B2 (Bloco B) | VERIFICADO |
| W-010 | Migrar o cliente MCP do runner (`runner/plan_runner/mcp_knowledge.py`) para a linha 2.x do pacote `mcp`, que mudou a API: o `streamable_http_client` devolve 2 valores, o `http_client` passa a ser `httpx2.AsyncClient` e o `CallToolResult` usa `is_error` | FALTA-CONSTRUIR | ABERTO | CLAUDE | Baixa | — | Achado do F0.7b (2026-10-05): `mcp` 2.0.0 saiu a 2026-07-28 e a 2.3.0 a 2026-10-02 (PyPI). Inspeccionado em `mcp==2.3.0`: `mcp/client/streamable_http.py` (`yield read_stream, write_stream`; `http_client: httpx2.AsyncClient`) e `mcp.types.CallToolResult` (`is_error`). Até lá, `runner/requirements.txt` fixa `mcp==1.30.0` e o cliente recusa a 2.x com uma mensagem clara (PR do branch `fix/F0-7b-mcp-versao`). A migração precisa de um teste com um servidor MCP real local, porque os testes actuais usam falsos | — | VERIFICADO |
| AU-20 | Tools: fonte do `tools_allowed` e execução no worker (hoje declarativo; o worker não executa tools) | FALTA-CONSTRUIR | ABERTO | AMBOS | Alta | Porte do ToolExecutor (D1) | P:305; O:150; `runner/tests/test_security_pipeline.py` ("Nao tens tools") | B3 (Bloco B, O:150); S33 (A5:169) | VERIFICADO |
| EX-B7 | Expor `engine: langgraph` + `decision: edit` na superfície MCP | FALTA-LIGAR | ABERTO | CLAUDE | Média | Recomendado depois do F5 (E §9.2) | P:351; O:15; E:793 | B7 (O:15) | VERIFICADO |
| AU-22b | Reescrever numa das 2 formas verificáveis a condição de `done_when` em linguagem livre do `paid-pack.plan.yaml` ("no ad_account_mutation without approve"); o evento `done_when_unverifiable` é o gatilho para encontrar outras | FALTA-CONSTRUIR | ABERTO | CLAUDE | Baixa | F3 (decisão do maestro, 2026-10-04) | `docs/orchestration/marketing/templates/paid-pack.plan.yaml`; `runner/plan_runner/done_when.py` (evento `done_when_unverifiable` com `item: AU-22b`); PR #90 | — | VERIFICADO |
| M-001 | Fase 2: Execution Broker (EXECUTE/REDIRECT/WAIT/DEFER/BLOCK) | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Média | F0–F6 + C-2 (D-EP5) | `docs/architecture/META-AGENTS-PHASE-2.md`; O §Fase 2; E §8.3 e §9.3 | — | VERIFICADO |
| M-002 | Fase 2: Execution Lease (1 tarefa → 1 lease activa) | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Média | F0–F6 + C-2 (D-EP5) | E §8.7 e §9.3; O §Fase 2 | — | VERIFICADO |
| M-003 | Fase 2: Execution Package (contexto para redirect) | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Baixa | M-002 | E §8.8 e §9.3 | — | VERIFICADO |
| M-004 | Fase 2: Learning (estimado vs real no ledger) | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Baixa | M-001 | E §8.11 e §9.3; O §Fase 2 | — | VERIFICADO |
| M-005 | PMO / Project Director (decisão organizacional) | FALTA-DECIDIR | ABERTO | DEV | Média | Decisão | O:53; A5 §5.4 | F7 (O:53; colide com as fases F*) | VERIFICADO |
| L4-1b | Teste real mínimo da L4 pela CLI (`remember` → `recall` → `promote` → `recall` → `forget`) | FALTA-TESTE | ABERTO | DEV | Média | `DATABASE_URL` | O:196; E:783; P §6 #9 | — | VERIFICADO |
| L4-2 | Spike comparativo do mem0 (só padrões, não substitui a L4) | FALTA-DECIDIR | ABERTO | AMBOS | Baixa | Recomendado depois do F3 (E §9.2) | O:197; E:789 | J11 | VERIFICADO |
| L4-3 | Ligar o MCP de produção à L4 | FALTA-LIGAR | ABERTO | AMBOS | Média | Recomendado depois do F5 (E §9.2) | O:198 | — | VERIFICADO |
| L4-4 | Confirmar o estado da L4 no veredicto do C-1 (`active` ou `--no-memory`) | FALTA-TESTE | ABERTO | DEV | Baixa | — | E §9.2 ("Estado L4 no C-1") | — | VERIFICADO |
| Q-001 | DeepEval via pytest (judge local) | FALTA-TESTE | BLOQUEADO | DEV | Média | RAM/ambiente (S19) | P:362; O:63; E §15.12 | D3 (DeepEval; colide com a decisão D3) | VERIFICADO |
| Q-002 | Ragas `ToolCallAccuracy`/`ToolCallF1` | FALTA-TESTE | BLOQUEADO | AMBOS | Média | Wheel da máquina Windows; desbloqueável no CI Linux | P:362; O:64; A5 §5.2 (D4) | D4 (Ragas; colide com a decisão D4) | VERIFICADO |
| E-001 | Q2: onde corre o motor em serviço (Oracle / PC local / serverless); recomendada B até S20 e S27 fecharem | FALTA-DECIDIR | ABERTO | DEV | Média | S20, S27 | P:537 | E1 (decisão §13.2; colide com o conector E1) | VERIFICADO |
| E-002 | Os 33 agentes do MCP de produção no registo `areas.yaml` (ADR-M7; recomendada: v2 depois do validador) | FALTA-DECIDIR | ABERTO | AMBOS | Média | — (o validador E7 já existe, #35) | P:541 | E5 (decisão §13.2; colide com o conector E5) | VERIFICADO |
| AU-36 | 3 nomenclaturas de marketing: decidido `vertical.nome` (E6, aplicado no `areas.yaml`); falta alinhar o MCP | FALTA-DECIDIR | ABERTO | AMBOS | Média | E-002 | P:321; P:542 | — | VERIFICADO |
| M7 | Piloto real de marketing | FALTA-DECIDIR | ABERTO | DEV | Média | Caso real do utilizador | P:358 | — | VERIFICADO |
| G6 | Contradição `imobiliario-digital` no `MCP-MAPPING.md` (§3.2 vs §3.6) | DOC-ERRADO | ABERTO | DEV | Baixa | Decisão | A5 §5.2 (ST:201) | — | VERIFICADO |
| INIT-093 | Adoptar `google/skills` (`media_buyer`, `ad_creative`) | FALTA-DECIDIR | ABERTO | AMBOS | Média | Decisão | A5 §5.2 (ST:174-178); O:20 | ING-7 | VERIFICADO |
| E15 | Proveniência do esboço do CouncilSession/`councils.yaml`: substituir a reconstituição se aparecerem os originais | DOC-ERRADO | BLOQUEADO | DEV | Baixa | Aparecerem os originais | P:553; O:105 | — | VERIFICADO |
| AU-12 | `STATUS.md` de 95 KB e docs pesados: o bootstrap custa tokens | FALTA-DECIDIR | ABERTO | AMBOS | Média | Decisão (partir/arquivar) | P:297; A5 §5.1 | J8 (parte) | VERIFICADO |
| H-002 | Avisos do ruff que já existiam em `scripts/` (`ingest_apply.py:62` I001, `ingest_delta.py:102` UP017; `main` `2b27f66`), fora do lint do CI | BUG | BLOQUEADO | CLAUDE | Baixa | F3 (§10 P-7 = A: registar e tratar no F3) | ruff 0.16.10 local (2.ª ronda, 03/10): 2 avisos, ambos `--fix`; `runner-tests.yml` só faz lint de `plan_runner/` e `tests/` | — | VERIFICADO |
| H-01 | Limpeza e organização para portfólio (opção C: README para negócio + `docs/` para técnico): lixo, arquivo dos históricos, índices, README, 3–5 casos de estudo, métricas e timeline | FALTA-CONSTRUIR | EM CURSO | AMBOS | Média | Faltam as partes 1 (limpeza), 2 (arquivo dos históricos) e 3 (índices), com os riscos do §4.1; o AU-12 e o H-001 são decisões prévias à parte 2 | Partes 4, 5 e 6 no PR #93 (merged 2026-10-05, `main` `92cc762`): README para portfólio em inglês, casos de estudo e números verificados, `LICENSE`, `SECURITY.md`, avisos de arquivado em `packages/` e `apps/`; Auditoria #65 (`docs/ops/PENDENCIAS-CRUZADAS.md`); adendo do maestro (03/10); âmbito, factos e riscos no §4.1; ID em §10 P-9; **README:** coberto pelo H-01 (decisão do maestro, 2026-10-03: A); 10 factos verificados no §4.1; vitrine para recrutadores (2026-10-05, PR do branch `docs/portfolio-recrutadores`): `docs/PORTFOLIO.md` novo, da plataforma (resumo EN de 60 s + PT, só números verificados), com o anterior, de marketing, preservado em `docs/PORTFOLIO-MARKETING.md`; linha "Start here" no README. A Description do NAS já está feita pelo maestro; os Topics estão vazios nos 2 repos (só na UI do GitHub); GIF do quickstart (`docs/assets/quickstart-demo.gif`, gerado a partir da saída real de um run stub) no README e no PORTFOLIO (PR do branch `docs/resolver-possiveis`); `docs/PORTFOLIO.md` expandido (PR do branch `docs/portfolio-recruiters`): títulos bilingues, números com a fonte de cada um, linha do tempo, guia do código; deixa de repetir o Quickstart e as histórias do README; bloco "For recruiters / visitors" no README | — | VERIFICADO |
| G1.1 | Trading: pesquisa padrão ouro de repos de trading/simulação | FALTA-DECIDIR | BLOQUEADO | AMBOS | Alta | F5 + D-EP8 (domínio só com uso real) | A5 §5.4 (grupos G–J); EP:1618-2428 | J9 (parte) | VERIFICADO |
| G1.2 | Trading: World Monitor + Finance News Aggregator (licença AGPL a avaliar) | FALTA-DECIDIR | BLOQUEADO | DEV | Média | F5 + D-EP8 | A5 §5.4 (grupos G–J); EP:1618-2428 | F20; F21 | VERIFICADO |
| G1.3 | Trading: competências dos papéis financeiros | FALTA-DECIDIR | BLOQUEADO | DEV | Alta | F5 + D-EP8 | A5 §5.4 (grupos G–J); EP:1618-2428 | — | VERIFICADO |
| G1.4 | Trading: contratos de dados entre papéis | FALTA-DECIDIR | BLOQUEADO | DEV | Alta | F5 + D-EP8 | A5 §5.4 (grupos G–J); EP:1618-2428 | D7 da Fase 3 (handoff) | VERIFICADO |
| G1.5 | Trading: isolar credenciais / garantir que não há execução real (pré-requisito de ordens autónomas) | FALTA-DECIDIR | BLOQUEADO | DEV | Crítica | F5 + D-EP8; gate §6.3 do E | A5 §5.4 (grupos G–J); EP:1618-2428 | — | VERIFICADO |
| G1.6 | Trading: MiroFish e repos de simulação (AGPL) | FALTA-DECIDIR | BLOQUEADO | DEV | Baixa | F5 + D-EP8 | A5 §5.4 (grupos G–J); EP:1618-2428 | B6 (ST) | VERIFICADO |
| G1.7 | Trading: agente de trading em simulação | FALTA-DECIDIR | BLOQUEADO | DEV | Alta | F5 + D-EP8 | A5 §5.4 (grupos G–J); EP:1618-2428 | B3 (ST:101) | VERIFICADO |
| G1.8 | Trading: agente de investimentos | FALTA-DECIDIR | BLOQUEADO | DEV | Média | F5 + D-EP8 | A5 §5.4 (grupos G–J); EP:1618-2428 | B12 (secção 09-14) | VERIFICADO |
| G1.9 | Trading: análise de volatilidade | FALTA-DECIDIR | BLOQUEADO | DEV | Média | F5 + D-EP8 | A5 §5.4 (grupos G–J); EP:1618-2428 | B13 (secção 09-14) | VERIFICADO |
| G1.10 | Trading: agente jornalístico → investidor | FALTA-DECIDIR | BLOQUEADO | DEV | Baixa | F5 + D-EP8 | A5 §5.4 (grupos G–J); EP:1618-2428 | F22; B14 | VERIFICADO |
| G1.11 | Trading: orquestrador do cluster financeiro | FALTA-DECIDIR | BLOQUEADO | DEV | Alta | F5 + D-EP8 | A5 §5.4 (grupos G–J); EP:1618-2428 | B10 (secção 09-14) | VERIFICADO |
| G1.12 | Trading: tela de agentes financeiros | FALTA-DECIDIR | BLOQUEADO | DEV | Baixa | F5 + D-EP8 | A5 §5.4 (grupos G–J); EP:1618-2428 | U3 | VERIFICADO |
| G1.13 | Trading: avatar financeiro | FALTA-DECIDIR | BLOQUEADO | DEV | Baixa | F5 + D-EP8 | A5 §5.4 (grupos G–J); EP:1618-2428 | U7 | VERIFICADO |
| G1.14 | Trading: critério de "pronto" do cluster | FALTA-DECIDIR | BLOQUEADO | DEV | Alta | F5 + D-EP8 | A5 §5.4 (grupos G–J); EP:1618-2428 | — | VERIFICADO |
| G2.1 | Gamedev: pesquisa padrão ouro (GDD, engine, loop) | FALTA-DECIDIR | BLOQUEADO | AMBOS | Alta | F5 + D-EP8 | A5 §5.4 (grupos G–J); EP:1618-2428 | J9 (parte) | VERIFICADO |
| G2.2 | Gamedev: âmbito (documento vs protótipo jogável) | FALTA-DECIDIR | BLOQUEADO | DEV | Alta | F5 + D-EP8 | A5 §5.4 (grupos G–J); EP:1618-2428 | — | VERIFICADO |
| G2.3 | Gamedev: engine-alvo | FALTA-DECIDIR | BLOQUEADO | DEV | Alta | F5 + D-EP8 | A5 §5.4 (grupos G–J); EP:1618-2428 | — | VERIFICADO |
| G2.4 | Gamedev: implementar | FALTA-DECIDIR | BLOQUEADO | DEV | Alta | F5 + D-EP8 | A5 §5.4 (grupos G–J); EP:1618-2428 | B4 (ST:102) | VERIFICADO |
| G3.1 | Avatar: pesquisa/desenho da infra | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão de âmbito | A5 §5.4 (grupos G–J); EP:1618-2428 | B11 (ST); U2; U6 | VERIFICADO |
| G3.2 | Avatar: implementar o avatar genérico | FALTA-DECIDIR | BLOQUEADO | DEV | Baixa | G3.1 | A5 §5.4 (grupos G–J); EP:1618-2428 | — | VERIFICADO |
| G3.3 | Avatar: skin (boneco) | FALTA-DECIDIR | BLOQUEADO | DEV | Baixa | G3.2 | A5 §5.4 (grupos G–J); EP:1618-2428 | U6 | VERIFICADO |
| G4.1 | Decidir Obsidian vs Logseq como vista humana da memória (fase posterior) | FALTA-DECIDIR | ABERTO | DEV | Média | Decisão de âmbito | A5 §5.4 (grupos G–J); EP:1618-2428 | F10; I8; E10 (§13.2) | VERIFICADO |
| G4.2 | Implementar o grafo de memória | FALTA-DECIDIR | BLOQUEADO | DEV | Média | G4.1 | A5 §5.4 (grupos G–J); EP:1618-2428 | U1 | VERIFICADO |
| H1 | Dashboard/integração | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão de âmbito | A5 §5.4; EP:2100-2178 | U4 | VERIFICADO |
| H2 | JARVIS | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão de âmbito | A5 §5.4; EP:2100-2178 | U8 | VERIFICADO |
| H3 | VOS (o âmbito nunca foi definido: "Clarificar") | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão de âmbito | A5 §5.4; EP:2100-2178 | U9 | VERIFICADO |
| H4 | Grafo de conexões | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão de âmbito | A5 §5.4; EP:2100-2178 | U5 | VERIFICADO |
| I1 | Avaliar `agent-skills` (Addy Osmani) | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão de âmbito | A5 §5.4; EP:2188-2383 | F1 (ST, ferramentas) | VERIFICADO |
| I2 | Avaliar Graphify (o repo MCP já o usa localmente: discrepância a resolver) | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão de âmbito | A5 §5.4; EP:2188-2383 | F2 (ST, ferramentas) | VERIFICADO |
| I3 | Avaliar OmniRoute (nomenclatura a confirmar) | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão de âmbito | A5 §5.4; EP:2188-2383 | F3 (ST, ferramentas) | VERIFICADO |
| I4 | Avaliar Obscura (+ obscura-mcp) | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão de âmbito | A5 §5.4; EP:2188-2383 | F4; F17 | VERIFICADO |
| I5 | Avaliar o plugin de segurança da Anthropic | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão de âmbito | A5 §5.4; EP:2188-2383 | F5; F16 | VERIFICADO |
| I6 | Avaliar Ruflo ("parked" sem razão escrita) | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão de âmbito | A5 §5.4; EP:2188-2383 | F7 (ST, ferramentas) | VERIFICADO |
| I7 | Avaliar gstack | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão de âmbito | A5 §5.4; EP:2188-2383 | F8 (ST, ferramentas) | VERIFICADO |
| I9 | Avaliar SOUL.md | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão de âmbito | A5 §5.4; EP:2188-2383 | F11 (ST, ferramentas) | VERIFICADO |
| I10 | Avaliar as Karpathy Skills (identificar o repo exacto) | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão de âmbito | A5 §5.4; EP:2188-2383 | F15 (ST, ferramentas) | VERIFICADO |
| I11 | Avaliar Soup (fine-tuning; a dependência "só após C8" já caiu) | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão de âmbito | A5 §5.4; EP:2188-2383 | F12 (ST, ferramentas) | VERIFICADO |
| T-004 | Preencher os preços confirmados em `config/model-prices.yaml` (a `null`: um plano com `max_cost_usd` pára no 1.º passo) | FALTA-LIGAR | ABERTO | DEV | Média | Página oficial de preços (bloqueada na sessão do D6) | PR #72; `config/model-prices.yaml` | — | VERIFICADO |
| T-005 | (Opcional) Escolher os modelos por tier em `config/model-tiers.yaml` | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão | PR #73; `config/model-tiers.yaml` | — | VERIFICADO |
| S-003 | Testar no Claude.ai connector uma chamada real às tools do MCP depois dos tectos de input do S-001 (pedido normal passa; acima do tecto dá erro de validação legível) | FALTA-TESTE | BLOQUEADO | DEV | Baixa | Conector real (só o DEV). Mesmo bloqueio do F0.6 (2026-10-05): o conector do Claude.ai não mostra tools ("Este conector não possui ferramentas disponíveis"), por isso não há chamada a testar | `ANM:CLAUDE.md` ("Alterações ao router e tools MCP: verificar impacto no Claude.ai connector"); PR MCP #14 §Impacto | — | VERIFICADO |
| S-004 | Triagem de segurança do MCP: vulnerabilidades de dependências (`npm audit`) e backlog com IDs e severidade (não reutiliza o S-003, que é o teste do connector) | BUG | EM CURSO | AMBOS | Média | Os alertas da aba Security do MCP (só o DEV vê: a API do Dependabot dá 403 a esta sessão; como o A22 no NAS) | `npm audit` na `main` MCP `d635945`: `next` 16.3.5 **crítica** (GHSA-vcvr-r3jv-pc5j, RCE no `next/og`; o código não usa `next/og`) e `ip-address` 10.5.0 moderada (transitiva); PR MCP #17 (`next` 16.3.8, `ip-address` 10.7.3; `npm audit` = 0; `npm test` 16/16; `next build` OK); MCP #17 merged a 2026-10-03 (`4916872`) | — | VERIFICADO |
| H-004 | Correr `graphify update .` localmente nos 2 repos depois das mudanças de código desta ronda (o `graphify-out/` é gitignored; a ferramenta não existe na sessão cloud) | FALTA-LIGAR | ABERTO | DEV | Baixa | Máquina local do DEV | `ANM:CLAUDE.md` §Graphify ("Após mudanças relevantes de código: graphify update ."); `which graphify` vazio na sessão | — | VERIFICADO |


### 4.1 Detalhe do H-01 (adendo do maestro, 2026-10-03; registado, NÃO executado)

**Âmbito (texto do maestro, sem cortes):**
1. Limpeza de lixo:
   - duplicados (2 `STATUS.md`, 2 `item-13-ai-findability.md`);
   - ficheiros órfãos;
   - `pilots/run-*` e `test-gemini.json` (lixo de teste);
   - ficheiros gerados mal colocados.
2. Arquivo dos históricos em `docs/archive/`, com o aviso HISTÓRICO no topo de cada um:
   - `PLANO-DE-ACAO.md`;
   - `OPEN-ITEMS.md`;
   - `MASTER-PLAN.md`;
   - `docs/STATUS.md` (o antigo);
   - `STATUS-PROJETOS.md` e `STATUS-ECOSSISTEMA.md`.
3. Índices:
   - `docs/README.md` (o que está onde);
   - `docs/architecture/README.md` (índice da arquitectura).
4. README para portfólio (opção C):
   - topo para negócio (o que é, o que resolve);
   - baixo para técnico (como está construído, stack, decisões).
5. Casos de estudo (3–5), com a evidência de partida na tabela abaixo.
6. Métricas e timeline:
   - métricas: n.º de PRs, testes, linhas, o que foi construído;
   - timeline: Blocos A/B/C, L4, security, F0.

**Factos do âmbito, verificados nesta sessão (`main` `e7a29ae`):**

| Facto | Evidência |
|---|---|
| Há 2 `STATUS.md` | `docs/STATUS.md` e `docs/initiatives/STATUS.md` (`git ls-files`) |
| Há 2 `item-13-ai-findability.md`, ambos ingeridos | `docs/item-13-ai-findability.md` e `docs/knowledge/item-13-ai-findability.md`; MANIFEST em `scripts/ingest_delta.py:33-34`, com `agent_id` diferentes |
| `pilots/run-*` não está versionado | Ignorado pelo `.gitignore` (ex.: `:99`, `:101`); a limpeza é só no disco de quem corre os pilotos |
| `test-gemini.json` | **NÃO VERIFICADO:** não está no git nem no disco desta sessão; pode existir no PC do maestro |
| Locais dos históricos a arquivar | `docs/architecture/MASTER-PLAN.md`; `docs/STATUS-PROJETOS.md`; `docs/STATUS-ECOSSISTEMA.md`; P e O já têm o aviso HISTÓRICO (este PR) |

**Casos de estudo (evidência de partida):**

| Caso | IDs | Evidência |
|---|---|---|
| O RAG partido: o ingest escrevia numa tabela que o retrieve não lia | AU-19 / C8 → J3 | A5:190 (C8 "fechado só no papel"); PR #31 |
| O ingest não incremental: 10 ficheiros re-embedados em cada corrida, 28 nunca | F0.4 / R-002 | L5F0 §2.1 (PR #63); correcção no PR #64 |
| O CI que mentia: sem `pipefail`, o job não conseguia falhar | — | PR #36 (commit `f587cfb`) |
| O `toolsAllowed` morto: dado como "DONE", mas sem fonte | S33 → AU-20 | ST:62 ("DONE"); A5:169 ("FECHADO-SÓ-NO-PAPEL") |
| A medição inválida apanhada a tempo: o 1.º run real deu −2,6% contra −16% projectado, mas o braço "opt" tinha corrido com o prompt `legacy` (detectado ao comparar os prompts token a token); repetido, deu **−22% real** | B1-bis-R / B1-bis-R2 | `docs/ops/WORKER-EXTERNAL.md:116,259`; PRs #45 e #55 (corrigido a 2026-10-05: antes dizia "hipótese refutada") |

**README da raiz: factos verificados (2026-10-03, `main` `c9edd72`).** O maestro decidiu que o H-01 cobre o README (A). **Todos corrigidos no PR #93 (merged 2026-10-05, `main` `92cc762`):** README reescrito em inglês para portfólio, com factos verificáveis, quickstart testado e os casos de estudo; o histórico fica abaixo.

| README diz | Estado verificado | Evidência |
|---|---|---|
| Governança em `packages/core/` (TypeScript) (`README.md:18`; o mesmo em `docs/architecture/ECOSYSTEM.md:21`) | O TS está arquivado pela D1. A governança viva é Python + YAML: `config/areas.yaml`, capabilities, E7, HITL e orçamento do `plan_runner` | `docs/architecture/EXECUTION-PLAN.md:98`; `docs/audit/DECISAO-1-runtimes.md`; `python -m plan_runner.areas` |
| "5 REAL, 19 INCOMPLETO, 14 MOCK" (`:28`) | Errata do AU-37: REAL 6, MOCK 13 | `docs/architecture/CORE-MAPPING.md:3-4` (#69) |
| "RAG fechado (C8, 6/6): 110 chunks de 33 ficheiros" (`:27`) | O C8 estava "fechado só no papel" (→ J3). Hoje: tabela canónica `knowledge_chunks`, MANIFEST com 39 fontes, F0 fechado com o M1 a 2026-10-05 (o F0.6 ficou BLOQUEADO; o F0.12 é opcional); o n.º de linhas está por confirmar (F0.1b; esperado 163) | `scripts/ingest_delta.py` (`MANIFEST`: 39); corrida #169 do `ingest-knowledge` (`unchanged=39`); A5:190 |
| "67 skills + 35 agentes, em 8 domínios" (`:29`) | 72 `SKILL.md` (claude 26, meta 24, marketing 16, design 4, security 2; eram 69 até às 3 skills de `obra/superpowers` de 2026-10-05) e 38 `*.agent.md`; falta o domínio `security` na lista | `find skills -name SKILL.md`; `find agents -name '*.agent.md'` |
| "Detalhe completo e actualizado: `docs/initiatives/STATUS.md`" (`:36`) | Pendentes só no `PENDENCIAS.md` (P-6 = A) | **Corrigido** (V40) |
| Os verticais "não vivem aqui", vêm do MCP (`:22`; `ECOSYSTEM.md:13`) | Também há agentes de domínio no setup (ex.: `agents/security`, `agents/marketing`), ligados por áreas | `config/areas.yaml` (10 áreas, 37 agentes; E7) |
| Requisitos "Node.js 18+" e "Redis 7+"; instalação `pnpm run build`/`dev` (`:107-122`) | O caminho operacional é o `runner/` (pip; Python 3.12 no CI). O TS precisa de Node 22 (`undici@8`), não 18. O Redis só aparece no TS arquivado (6 ficheiros em `packages/`), nada no `runner/`, `scripts/` ou `config/` | `.github/workflows/ci.yml` (Node 22 e comentário do `undici`); `runner-tests.yml:70`; `grep -ril redis` |
| `docs/knowledge/ai-findability.md` "(50 chunks RAG)" (`:50`) | 9 chunks com o chunker actual | `plan_runner.chunking.chunk_markdown` sobre o ficheiro |
| Sem menção a `PENDENCIAS.md`, `EXECUTION-PLAN.md`, pipeline de security, CouncilSession ou L4 | Lacuna, não contradição | — |
| AgentMesh e Cedar por integrar (`:33-34`) | **Correcto** | EX-C3, EX-C4, B16 (§4) |

**Riscos para a execução** (não cortam o âmbito, condicionam o como):
- **Mover `docs/STATUS.md` parte o CI.**
  - O `packages/scripts/src/validate/check-consistency.ts:66-73` dá `error` quando o ficheiro falta, e corre no `ci.yml:129`.
  - O validador tem de mudar no mesmo PR (é código).
- **Mover `STATUS-PROJETOS.md` e `STATUS-ECOSSISTEMA.md` parte o bootstrap.**
  - Apontam para eles: `CLAUDE.md:7,22-23,65` (este repo), `docs/architecture/BOOTSTRAP.md:9` e `agent-network-mcp/CLAUDE.md:9-10` (outro repo).
  - 10 ficheiros citam um destes ficheiros ou o `MASTER-PLAN.md`.
- **Tirar um dos `item-13` exige mudar o MANIFEST e purgar a `source` antiga no Supabase.**
  - É escrita em produção, por isso é do DEV.
  - Sem isso, os chunks antigos ficam órfãos no L5.
- **Mover P e O muda os caminhos das siglas `P:` e `O:`** deste documento: actualizar o §0, item 7, no mesmo PR.
- **O merge dispara o ingest:** qualquer merge que toque em `docs/**/*.md` corre o `ingest-knowledge`, que escreve em produção.

**Relação com itens existentes** (sem duplicar):
- O AU-12 (STATUS de 95 KB: partir ou arquivar) e o H-001 (papel do STATUS e ponteiros, §10 P-6) são decisões prévias ao passo 2.
- O H-01 não os substitui: na execução, fecham em conjunto ou ficam citados.

## 5. Resumo por dono

| Dono | N.º | IDs |
|---|---:|---|
| CLAUDE | 10 | F1, F1b, F2, W-010, F4, W-003, R-005, EX-B7, AU-22b, H-002 |
| DEV | 65 | F0.6, F0.12, S20, S27, S19, S21, S28, S32, A12, A13, A19, A22, EX-C3, EX-C4, AU-25, T-003, W-001, W-004, M-005, L4-1b, L4-4, Q-001, E-001, M7, G6, E15, G1.2, G1.3, G1.4, G1.5, G1.6, G1.7, G1.8, G1.9, G1.10, G1.11, G1.12, G1.13, G1.14, G2.2, G2.3, G2.4, G3.1, G3.2, G3.3, G4.1, G4.2, H1, H2, H3, H4, I1, I2, I3, I4, I5, I6, I7, I9, I10, I11, T-004, T-005, S-003, H-004 |
| AMBOS | 29 | F3, F5, F6, R-001, AU-44, SEC-3, B2b, B2c, A9, B16, B1-bis-C, T-001, T-002, AU-20, M-001, M-002, M-003, M-004, L4-2, L4-3, Q-002, E-002, AU-36, INIT-093, AU-12, H-01, G1.1, G2.1, S-004 |

**Só do DEV, sem código:**
- merges: o PR `docs/m1-moldes-f0` (só documentação); os #88 a #100 e o MCP #18 já entraram (2026-10-05, `main` `098034e`);
- gate M1: FECHADO (2026-10-05, decisão do maestro: o F0.7b chega). O F0.6 e o S-003 estão BLOQUEADOS porque o conector do Claude.ai não mostra tools; desbloquear é uma decisão (bypass por query parameter nas settings do conector, ou outra forma de expor o MCP). Falta decidir a P-19 (o 1.º run cumpre qualquer opção) e a P-20 (causa do R-005); S20 até 2026-10-12 (ou outra data);
- vitrine no GitHub (só na UI): Topics nos 2 repos, Description e Website do `agent-network-mcp` (o Website certo é `https://agent-network-mcp-oddn.vercel.app`), bio e repos fixados no perfil;
- decisões: P-11, P-16 e P-17;
- S28 (1 run limpo do `transcribe.yml`) e H-004 (`graphify update .` local); o S-003 (teste no connector) está BLOQUEADO como o F0.6;
- R-004: merge do PR MCP #15 e, antes ou depois, a query só de leitura do PR (`SELECT project, count(*) ... GROUP BY project`);
- F0.1, F0.3 e R-002 fecharam a 2026-10-05. Confirmação opcional do total: `SELECT project, count(*) FROM knowledge_chunks GROUP BY project` (esperado: NULL 201, `network-agents-setup` 163);
- gate F0: fechado com o M1 (2026-10-05); o F0.6 ficou BLOQUEADO e o F0.12 (apagar a t6) continua opcional;
- as 5 queries do R-001 (`docs/ops/KNOWLEDGE-LOG.md` §3);
- T-004 (preços em `config/model-prices.yaml`);
- S20, S27, S19;
- L4-1b;
- W-001;
- as decisões do §10.

## 6. Resumo por severidade

| Sev | N.º | IDs |
|---|---:|---|
| Crítica | 1 | G1.5 |
| Alta | 16 | F1, R-005, F3, F5, S20, AU-20, G1.1, G1.3, G1.4, G1.7, G1.11, G1.14, G2.1, G2.2, G2.3, G2.4 |
| Média | 40 | F0.6, F2, F4, F6, AU-44, S27, S19, S32, B2b, B2c, A9, A13, A22, EX-C3, EX-C4, B1-bis-C, W-001, W-004, EX-B7, M-001, M-002, M-005, L4-1b, L4-3, Q-001, Q-002, E-001, E-002, AU-36, M7, INIT-093, AU-12, H-01, G1.2, G1.8, G1.9, G4.1, G4.2, T-004, S-004 |
| Baixa | 47 | F0.12, F1b, W-010, R-001, S21, S28, SEC-3, A12, A19, B16, AU-25, T-001, T-002, T-003, W-003, AU-22b, M-003, M-004, L4-2, L4-4, G6, E15, H-002, G1.6, G1.10, G1.12, G1.13, G3.1, G3.2, G3.3, H1, H2, H3, H4, I1, I2, I3, I4, I5, I6, I7, I9, I10, I11, T-005, S-003, H-004 |

**Por estado:** ABERTO 56 · EM CURSO 5 · BLOQUEADO 43.
**NÃO VERIFICADO (4):** S20, S27, A22, T-003.

## 7. Histórico (105 linhas: 84 FECHADO, 21 OBSOLETO)

Mais recente primeiro. Uma linha pode agrupar IDs fechados pelo mesmo PR ou decisão (separados por `/`). Às 4 colunas pedidas acrescentam-se 2 (`Estado final` e `Nota`).


| ID | Título | Fechado em | PR / evidência | Estado final | Nota |
|---|---|---|---|---|---|
| F0.7b | Medir o golden set contra o MCP real (hit@k, MRR, proveniência) | 2026-10-05 | Run do DEV (`python -m plan_runner.l5_eval run`, branch do PR #103) contra produção: 18 casos, `source_hit@4` 1.0, `provenance_ok` 1.0, `chunk_hit@1/3/4` 0.611/0.889/0.944, `mrr_chunk` 0.736, `no_hits` 0. Registado em `docs/ops/L5-F0-REVALIDATION.md` §6.2 (PR do branch `docs/f0-7b-evidencia`) | FECHADO | 3.ª tentativa. A 1.ª falhou por `mcp` 2.x no ambiente (#102) e a 2.ª pela Vercel Standard Protection (#103). Cumpre as 3 opções da P-19. 1 caso (ID não colado) sem o excerto nos 4 primeiros, mas com a fonte certa |
| H-003 | Actions pinadas em versões Node 20 (NAS e MCP) | 2026-10-05 | #99 (merged, `5736621`): 23 pins no NAS; PR MCP #18 (merged, `880d492`): `checkout` e `cache`. Em cada Action, a última versão da 1.ª linha principal com `using: node24`, lida no `action.yml` da tag. Prova: CI do #99 sem o aviso "Node.js 20 is deprecated"; corrida #182 do `ingest-knowledge` (1.ª com os pins novos) `success`, `chunks=0 unchanged=39` | FECHADO | Só o `release.yml` (corre com tags) e os 2 workflows do MCP (`ingest.yml`, `transcribe.yml`) ficam por provar numa corrida real |
| W-009 | O exemplo de budget do `ORCHESTRATOR.md` tinha o `max_retrieve_calls`, que não está no schema | 2026-10-05 | #99 (merged): o exemplo fica com o `max_steps`, e uma nota explica o campo (nunca implementado; limite de retrieves no F3) | FECHADO | — |
| H-005 | O `docs/STATUS.md` do MCP dizia que o GitHub Actions estava desligado | 2026-10-05 | PR MCP #18 (merged, `880d492`): Actions agendadas activas (`heartbeat.yml`, `audit-tools.yml`); 33 agentes; linha no histórico | FECHADO | — |
| H-006 | README do `agent-network-mcp` com links mortos, TODO à vista, contagens incoerentes; sem `LICENSE`; `diagnostico-vm.txt` na raiz | 2026-10-05 | PR MCP #18 (merged, `880d492`): links reais, texto factual de deploy e de ligação MCP, 33 agentes, repo irmão, nota sobre o S20, `LICENSE` MIT, `diagnostico-vm.txt` → `docs/ops/` | FECHADO | O Website no About do repo continua errado (`agent-network-mcp.vercel.app`; o certo é `agent-network-mcp-oddn.vercel.app`): só na UI do GitHub |
| R-004 | O `ingestDocument` do MCP apagava por `agent_id`+`source` sem filtrar `project` (podia apagar linhas do T6) | 2026-10-05 | PR MCP #15 (merged 2026-10-03, `a80ab5c`): `.is("project", null)` no delete; `tests/ingestDocument.test.mjs` (3 testes; `npm test` 19/19) | FECHADO | Fechado com atraso: a linha ficou à espera de um merge que já tinha acontecido. A distribuição por `project` é coerente com os SELECTs do maestro: 201 linhas NULL (MCP), e as fontes do projecto na F0.1b. A confirmação explícita fica opcional: `SELECT project, count(*) … GROUP BY project` |
| W-008 | O `piloto-netos.plan.yaml` não passava no schema dos planos | 2026-10-05 | Falso positivo: é do formato do plan-execute, e valida contra o seu próprio schema (`docs/architecture/plan-execute/schemas/Plan.schema.json`, 0 erros), como já testa o `runner/tests/test_plan_schema_json.py`. O `plan_schema.py` declara que o formato do runner é outro | FECHADO | Erro de registo meu (2026-10-04): validei-o contra o schema errado |
| AU-22 | Campos de plano mortos: `done_when` verificado; `on_fail` e `max_replans` removidos (P-10 = A) | 2026-10-05 | #90 (`done_when.py`; `tests/test_done_when.py`, 16 testes) e #96 (merged, `9531ec3`): schema, 13 planos e `models.py` sem `on_fail`/`max_replans`; `test_plan_fields.py` e `test_plan_schema.py` (4 testes falham sem a alteração) | FECHADO | O `knowledge_refs` continua ignorado e assinalado no `plan_fields_ignored` (o L5 entra pelo bloco `knowledge:`). Seguem-se o AU-22b (condição livre do `paid-pack`, F3), o W-009 e os 6 prompts com `on_fail` (B1-bis-C) |
| F0.1 | Revalidar a tabela canónica do L5 (overload de `match_knowledge`, total, linhas do projecto por fonte, `agent_id` compostos) | 2026-10-05 | SELECTs do maestro (2026-10-05, 2.ª ronda): F0.1b com `WHERE project = 'network-agents-setup'`, lista completa das fontes do projecto (`security-agents-stack.md` 20 chunks; ~8 ficheiros com mais chunks e ~28 com 1–4); 1.ª ronda: compostos = 0; 2026-10-03: 1 overload e 322 linhas | FECHADO | O total `projecto` não veio no resultado colado: esperado 163 (121 do J3 + 42 da corrida #156), com total 364 e 201 do MCP. Confirmação opcional: `SELECT project, count(*) FROM knowledge_chunks GROUP BY project` |
| R-002 | Recuperar os 28 ficheiros do MANIFEST que o workflow nunca re-ingeriu (82 chunks) | 2026-10-05 | SELECTs do maestro (2026-10-05, 2.ª ronda): a F0.1b filtrada lista todas as fontes do projecto, incluindo os ~28 ficheiros com 1–4 chunks; corridas #156 (`unchanged=33`) e #163–#178 (`unchanged=39`, `orcamento_usado=0/50`) | FECHADO | Não faltava nada: os 28 ficheiros estavam na tabela desde a 1.ª ingestão e iguais ao repo (V38). Nenhuma corrida incremental deu `SKIPPED_QUOTA` |
| C-2 | Ledger dos conselhos: CHECK do `token_usage` com os 3 `council_*` | 2026-10-05 | DB: ALTER corrido pelo DEV a 2026-10-03 (`token_usage_call_kind_check` com 7 valores); repo: MCP #16 (merged 2026-10-03, `a4f46e1`; `ANM:memory/token_usage.sql:14-16`) | FECHADO | Fechado com atraso: o #16 entrou a 2026-10-03, mas a linha ficou EM CURSO até à revisão de 2026-10-05. Ainda não há a prova por um run real de conselho com linhas no ledger (entra no F5) |
| F0.3 | Passo 3 do J3: confirmar que a t6 parou (`ultima_t6`) | 2026-10-05 | SELECT do maestro (2026-10-05): `ultima_t6` = 2026-09-29 10:06:33+00 (≤ 2026-09-30), `total_t6` = 110 | FECHADO | A t6 está congelada; as 110 linhas batem com o C8 (F0.9). Desbloqueia o F0.12 (apagar a t6, com backup e decisão) |
| R-003 | Confirmar `agent_id`/`project` das 8 linhas da fonte "ECC security-reviewer + database-reviewer" | 2026-10-05 | SELECT do maestro (2026-10-05): `agent_id` = revisor-codigo, `project` NULL, `kb` = marketing | FECHADO | Não é `global`, por isso não aparece em todas as pesquisas. O `kb` está errado → R-005 |
| E-003 | `ship-parallel.plan.yaml` (reviews de código/segurança/testes) resolvia sempre para agentes de marketing | 2026-10-05 | #90 (§10 P-18 = C); `runner/tests/test_engenharia_ship_gate.py` (3 testes) | FECHADO | Os 3 reviews passam a agentes reais em `docs/orchestration/engenharia/templates/ship-gate.plan.yaml` (`revisor_codigo`, `security_audit`, `guia_tdd`), com `done_when` verificável; o `ship-parallel` fica como exemplo do motor (só comentário) |
| INIT-094 | Reavaliar os 6 harnesses multi-provider | 2026-10-03 | §10 P-12 = A (maestro, consulta cruzada); análise: PR #80 (`docs/research/harnesses-multi-provider-2026-10.md`) | OBSOLETO | Não adoptar; opencodex + LiteLLM ficam como candidatos do F3/§8.6 |
| ING-5 | gitingest (repo → texto): ADAPT com reservas (pin `0.3.1`, só repos públicos) | 2026-10-03 | §10 P-14 = A (maestro, consulta cruzada); análise: PR #82 (`docs/research/ingestao-ing5-ing6-2026-10.md`) | OBSOLETO | Não adoptar; EXTRACT próprio se houver necessidade |
| ING-6 | Reavaliar ScrapeGraphAI | 2026-10-03 | §10 P-15 = A (maestro, consulta cruzada); análise: PR #82 (`docs/research/ingestao-ing5-ing6-2026-10.md`) | OBSOLETO | Não adoptar; `fetch` + worker no F2 |
| S-001 / S-002 | S-001: validação de inputs (checklist #14), re-apontada para o MCP (P-4 = B) / S-002: trim das respostas (checklist #17) | 2026-10-03 | MCP #14; `ANM:tests/inputLimits.test.mjs` (4 testes; `npm test` 16/16) | FECHADO | S-001: `lib/inputLimits.js` + `.max()` nas 15 strings e no array das tools. S-002 sem código: limites já existentes, verificados no PR (`lib/agentRuntime.js:35,50`; `route.js:457`, `:272-273`). Valores em vigor = P-16 A, ainda por confirmar (§10); teste no connector → S-003 |
| AU-06 | Duas pipelines de ingestão: documentar o `ingest.yml` do MCP como legado (D-EP9) | 2026-10-03 | MCP #13 (`ingest.yml` + `ingestion/MANIFEST.md`) | FECHADO | Só docs; o bug de apagar por `source` ficou como R-004 |
| S17 | O doc da VM, no repo MCP, ainda dizia GCP | 2026-10-03 | MCP #11 (`CONFIGURACAO_VM_BRIDGE_WORKER.md`) | FECHADO | Oracle no topo; secções GCP marcadas HISTÓRICO; shape/região da VM Oracle NÃO VERIFICADO (precisa de consola) |
| W-005 | Worker inline no engine langgraph (antes só no `native`) | 2026-10-03 | #79; `runner/tests/test_langgraph_worker.py` (6 testes) | FECHADO | Mesmo contrato do `native`: tecto de tokens/custo, `paused_budget` e resume |
| W-002 | Clarificação com estado no router (hoje a resposta é um novo `route`) | 2026-10-03 | #78; `runner/tests/test_router_clarify.py` (8 testes) | FECHADO | `route --clarify-from`; `docs/ops/ROUTER.md` actualizado |
| AU-11 | Schema do RAG versionado num só sítio: DDL de `knowledge_chunks` e `knowledge_sources` (hoje a de `knowledge_sources` só existe em teste) | 2026-10-03 | #76; `test_rag_canonical.py::test_schema_canonico_e_idempotente` | FECHADO | DDL canónico `scripts/rag_schema.sql`; modelos Prisma da t6 → decisão §10 P-11 |
| W-006 | Os planos YAML do runner não têm schema validado (o `Plan.schema.json` é de outro formato; `repo_files`/`context` não estão declarados) | 2026-10-03 | #75; `runner/tests/test_plan_schema.py` (25 testes) | FECHADO | `plan_runner/plan.schema.json` + `python -m plan_runner.plan_schema` |
| D5 | Ler o `model_tier` de facto | 2026-10-03 | #73; `runner/tests/test_model_tier.py` (7 testes) | FECHADO | Resolver próprio (sem LiteLLM); escolher os modelos → T-005 |
| D6 | `budget.max_cost_usd` (hoje o orçamento é só em tokens) | 2026-10-03 | #72; `runner/tests/test_budget.py` (12 testes novos) | FECHADO | Mecanismo feito; os preços estão a `null` → T-004 |
| AU-32 | `design-flow.plan.yaml` sem `vertical:` (0 de 5 passos) | 2026-10-03 | #71; `runner/tests/test_skills.py` (2 testes) | FECHADO | O `ship-parallel` (marketing/) ficou de fora → E-003 |
| H-001 | Ponteiros para este documento: `BOOTSTRAP.md`, `CLAUDE.md` e o papel do `STATUS.md` | 2026-10-03 | #70 (decisão §10 P-6 = A) | FECHADO | Listas do STATUS marcadas HISTÓRICO; remover → §10 P-17 / H-01 |
| AU-37 | `CORE-MAPPING.md` desactualizado (Orchestrator "MOCK" é REAL): falta a errata no próprio ficheiro | 2026-10-03 | #69 | FECHADO | Errata no topo do `CORE-MAPPING.md`; o MFA `'123456'` continua (`SecurityManager.ts:239`) |
| AU-10 | `skills/claude/` sem proveniência (cabeçalho de sync) | 2026-10-03 | #68 | FECHADO | `skills/claude/PROVENANCE.md` gerado pelo sync |
| AU-08 | `.env.example` omite as variáveis lidas pelo código (ex.: `GEMINI_API_KEY`, `MCP_API_KEY`, `MCP_URL`) | 2026-10-03 | #67 | FECHADO | 26 variáveis acrescentadas (41 no total) |
| AU-46 | `OPEN-ITEMS.md` desactualizado | 2026-10-03 | #66 | FECHADO | O OPEN-ITEMS tem o aviso HISTÓRICO |
| AU-45 | Colisões de IDs entre documentos | 2026-10-03 | #66 | FECHADO | IDs canónicos (§3) e índice de aliases (§11) |
| F0.4 | Pack de security no L5: ingest incremental por `content_hash` + entrada no MANIFEST + `_kb_for(security)` + pack corrigido antes da 1.ª ingestão | 2026-10-03 | #64; corrida #156 do `ingest-knowledge` (`security-agents-stack.md chunks=20`); corrida #163 (`unchanged=39`) | FECHADO | Prova em produção do ingest incremental. **Orçamento (`--max-chunks`, 2026-10-05):** o workflow usa o valor por omissão, 50 (`scripts/ingest_apply.py:250-253`; `.github/workflows/ingest-knowledge.yml:42`). Nas corridas incrementais chega: as #174–#178 usaram 0/50 e nenhuma deu `SKIPPED_QUOTA`. Só uma re-ingestão total (`--force`, ex.: troca de embedder ou de chunker) precisa de um orçamento ≥ ao total de chunks do projecto (163 esperado), ou de várias corridas; 150 não chegaria |
| F0.9 | Comparação C8 (110, t6) → J3 (121/322) → hoje | 2026-10-03 | #63 (L5F0 §2) | FECHADO | — |
| F0.8 | Documentar a provenance actual, camada a camada | 2026-10-03 | #63 (L5F0 §1) | FECHADO | — |
| F0.7a | Golden set do L5 security (18 casos) + `python -m plan_runner.l5_eval` | 2026-10-03 | #63; `runner/tests/test_l5_eval.py` (14 testes); `l5_eval validate`: 18 casos, 0 erros | FECHADO | A medição (F0.7b) continua do DEV |
| F0.5 | Consumidor do L5: bloco `knowledge:` (kb `security`) no passo `audit` do plano demo de security | 2026-10-03 | #63; `test_security_pipeline.py::test_audit_recebe_o_l5_de_security_com_a_fonte_citada` | FECHADO | — |
| W-007 | O `log_execution` do MCP perde 4 campos (`capacidade_id`, `fast_path`, `custo_estimado`, `justificativa_full_cycle`) | 2026-10-03 | MCP #10 (`840d8a8`); teste e2e `b29752e` (`tests/e2e/mcp-tools.e2e.test.mjs`) | FECHADO | `ANM:lib/memory.js:95-98`; ver V35 |
| F0.2 | Confirmar se o pack de security está no L5 | 2026-10-03 | SELECT do maestro; registo em L5F0 §0 (PR #63) | FECHADO | Resultado: NÃO está (as 8 linhas "security" são de um pack ECC → R-003). **2026-10-05:** já está. A contagem por fonte do maestro dá 20 chunks, iguais aos da corrida #156 (F0.4, #64). A fonte foi reportada como `docs/knowledge/security/security-agents-stack.md`; no repo e no MANIFEST o caminho é `docs/knowledge/security-agents-stack.md` |
| F0.10 | Merges SEC em main | 2026-10-03 | #61 (`969d3ce`) | FECHADO | — |
| F0.11 | Cobertura dos ficheiros fora do MANIFEST: decisão | 2026-10-03 | D-EP2 = A (#62) | FECHADO | A execução vive no F3 |
| D-EP1..D-EP9 | Decisões sobre o EXECUTION-PLAN | 2026-10-03 | #62 | FECHADO | Todas na opção A |
| D-EP10 | Refinar as regras de commit e de verificação de CI | 2026-10-03 | Decisão do maestro (A); registo no PR #63 | FECHADO | — |
| D-EP11 | Passos W-repo do F0 entram na Etapa 2 | 2026-10-03 | Decisão do maestro (A); registo no PR #63 | FECHADO | — |
| SEC-2d | Triagem do semgrep (código activo: 0) | 2026-10-03 | #61 | FECHADO | — |
| SEC-2b | Confirmar a revogação da chave antiga | 2026-10-03 | #61 (registo; confirmado pelo maestro) | FECHADO | `rotated-2026-09-19` |
| SEC-2c | Actions fixadas por SHA | 2026-10-03 | #60 | FECHADO | — |
| SEC-2 | gitleaks + semgrep no CI | 2026-10-03 | #59 | FECHADO | Fecha o J10 |
| J10 | Gate de segurança no CI | 2026-10-03 | #59 | FECHADO | = SEC-2 |
| SEC-1 | `repo_files` para o auditor | 2026-10-03 | #58 | FECHADO | — |
| Security pipeline v1 | triage → auditor → reporter + capabilities | 2026-10-03 | #57 | FECHADO | O título no O ainda diz "sem merge" (V25) |
| C-1 | Custo real do conselho (11 760 tokens por ronda) | 2026-10-03 | #55 | FECHADO | — |
| B1-bis-R2 | Run real do modo `opt` (−22% medido; ~−16% atribuível) | 2026-10-03 | #55 | FECHADO | — |
| J5-c | CouncilSession (Fase 1 dos meta-agentes) | 2026-10-03 | #54 | FECHADO | P §15 ainda diz "nada implementado" (V24) |
| J5-b | `councils.yaml` v0 | 2026-10-03 | #54 | FECHADO | — |
| E12 | Onde vive o `councils.yaml` (`config/`) | 2026-10-03 | #54 | FECHADO | Decisão §13.2 |
| D-EP7 / MASTER-PLAN | `MASTER-PLAN.md` marcado como histórico | 2026-10-03 | #62 | FECHADO | — |
| S29 | Memória L4 (código + SQL) | 2026-10-01 | #47 | FECHADO | L4-1 (SQL em produção) feito pelo maestro; falta o L4-1b |
| L4-1 | Correr os 2 SQL da L4 em produção | 2026-10-01 | DEV (verificação 4/4), O:195 | FECHADO | Sem PR (escrita em produção) |
| B5-bis | Tectos de tokens por área | 2026-10-01 | #46 | FECHADO | — |
| B1-bis | Optimização de contexto (`opt`) | 2026-10-01 | #45 | FECHADO | — |
| PLANO item 10 / L1 | Teste e2e no CI (lentos + ingest→retrieve) | 2026-10-01 | #43 + #44 | FECHADO | — |
| AU-09 | CI Python ignora os testes lentos | 2026-10-01 | #43 | FECHADO | P §9 ainda diz "NÃO INICIADO" (V7) |
| AU-49 | Orçamento de tokens aplicado | 2026-10-01 | #42 (+ tectos #46) | FECHADO | Alias: B5 (Bloco B, O:152) |
| AU-16 | Tokens somados e persistidos | 2026-10-01 | #40 (ledger do worker) + J6 (`agent-network-mcp` PR #8) | FECHADO | — |
| AU-26 / AU-30 / AU-33 / AU-34 | Áreas + router hierárquico híbrido | 2026-10-01 | #41 (+ J5 em #33) | FECHADO | Inclui as decisões E2, E3 e E4 (§13.2) |
| AU-23 | Worker do modo `external` | 2026-10-01 | #40 | FECHADO | — |
| AU-07 | Dois orquestradores sem ponte / maestro por escolher | 2026-10-01 | D1/D2 (#33) + #41 | FECHADO | — |
| B1 (worker) | 1.º run real do worker (13 130 tokens) | 2026-10-01 | Registo no fecho do dia (#53) | FECHADO | Colide com B1 do ST (2.º domínio, alias de F6) |
| AU-19 / J3 | RAG canónico (`knowledge_chunks`) | 2026-09-30 | #31 | FECHADO | Restam F0.3, F0.6 e F0.12 |
| AU-50 | `agent_id` composto na t6 | 2026-09-30 | #31 (`scripts/migrate_t6_to_knowledge_chunks.sql:37-48` + `insert_chunks`) | FECHADO | Verificado em 03/10 (V13); 2026-10-05: 0 `agent_id` compostos na canónica (SELECT do maestro, `agent_id LIKE '%+%'`) |
| AU-05 / J7 | `tests/package.json` órfão (Dependabot #11) | 2026-09-30 | #30 | FECHADO | — |
| AU-47 / J1 | Keep-alive do Supabase | 2026-09-30 | Run #6 do `keep-alive.yml` verde (secrets + tabela) | FECHADO | Sem PR (configuração do DEV) |
| J6 | Ledger de tokens no MCP de produção | 2026-09-30 | `agent-network-mcp` PR #8 | FECHADO | Sub-item aberto: T-003 |
| AU-31 / A8 (frontmatter) | Resolução de agente↔skill pelo frontmatter | 2026-09-30 | #32 | FECHADO | Colide com A8 (= S11) |
| J4 | `description:` nos agentes | 2026-09-30 | #34 | FECHADO | Verificado em 03/10: 38/38 |
| E7 | Validador do `areas.yaml` no CI | 2026-09-30 | #35 | FECHADO | — |
| J5 | Registo de áreas como dados (`areas.yaml`) | 2026-09-30 | #33 | FECHADO | — |
| D1 / D2 / D3 / D4 | Decisões de runtime, maestro, memória e ordem | 2026-09-30 | #33 (P §13.1) | FECHADO | P §3 ainda diz "pendentes" (V23) |
| EX-C2 | TS vs Python MCP | 2026-09-30 | D1 (#33) | FECHADO | Alias C2 (O:50) |
| E6 / E8 / E9 / E11 / E13 / E14 | Decisões §13.2 aplicadas (nomenclatura, trader em finance, cyber = security, integração T1.1, C0–C3, `active`) | 2026-09-30 | #33 | FECHADO | — |
| S29-bis | `@vitest/coverage-v8` alinhado com vitest 5 | 2026-09-30 | PR #38 (via #39) | FECHADO | — |
| S15a | Secret do Actions do `agent-network-mcp` rodada | 2026-09-20 | ST:36 | FECHADO | O:33 ainda a lista como Crítica (V14) |
| S11 / A8 (auth) | Auth do `MCPServer` (TS) | anterior a 2026-09-29 | P:376 ("Verificados: S11"); A5 §5.4 | FECHADO | O:36 ainda o lista como Crítico (V19); hoje TS arquivado |
| S12 | `.strict()` nos Zod do `mcp-handler` | anterior a 2026-09-29 | P:376 ("Verificados: S12"); A5 §5.5 #8 | FECHADO | O:54 ainda o lista como aberto (V27) |
| S5 | `validate:consistency` no CI | anterior a 2026-09-29 | `ci.yml:129` (commit `6dc3f65`, directo na `main`, sem PR); A5 §5.2 | FECHADO | O STATUS não o moveu para Done |
| AU-01 / AU-02 / AU-03 / AU-04 | Build TS, Docker/k8s, `apps/web`, `packages/langgraph` | 2026-09-30 | D1 (P §13.1; #33) | OBSOLETO | TS arquivado |
| AU-13 / AU-14 / AU-15 / AU-17 / AU-18 / AU-21 | Quebras do `/chat` TS, HITL TS, streaming | 2026-09-30 | D1; P:161-171 ("só valem em B/C") | OBSOLETO | A deliberação vive no CouncilSession Python |
| AU-24 / AU-27 / AU-28 / AU-29 | Regex anti-injecção, `systemPrompt`, profiles, `PUBLIC_MODE` (TS) | 2026-09-30 | D1; `SecurityManager.ts`, `Executor.ts`, `apps/api/src/index.ts` | OBSOLETO | — |
| AU-38 / AU-39 / AU-40 / AU-41 / AU-42 / AU-43 | Órfãos TS, `HitlManager` import/export, repos/Redis, `MCPServer` TS, MFA fixo, `getHitlStats` | 2026-09-30 | D1 (P §13.1) | OBSOLETO | — |
| AU-48 / A4 | `query_database` com SQL arbitrário (TS) | 2026-09-30 | D1 | OBSOLETO | — |
| M3 / M4 / M5 | e2e HITL Py→Node→Py, HITL durável em Postgres, mover órfãos | 2026-09-30 | D1 (o HITL Python já é durável) | OBSOLETO | Aliases: EX-B5/B5 (O:47), EX-B6/B6 (O:48), EX-B12/B12 (O:49) |
| M6 / EX-B13 / B13 | `GeminiProvider` + Planner TS | 2026-09-30 | D1; Gemini no worker Python (#40) | OBSOLETO | O:16 ainda o lista (V15) |
| P6 | Multi-provider arquivado (contradizia o M6) | 2026-09-30 | D1 + #40 | OBSOLETO | Contradição P6↔M6 resolvida |
| EX-B3 / B3 (O:46) | Correr `apps/api` contra infra real | 2026-09-30 | D1 | OBSOLETO | — |
| S24 / EX-S24 | Cobertura TS (`MCPServer.ts`) | 2026-09-30 | D1; a parte do MCPServer fechou via S11 (A5 §5.4) | OBSOLETO | V18 |
| S13 / A23 | CORS aberto (`apps/api`) | 2026-09-30 | D1 | OBSOLETO | — |
| S14 | Migrar `Tracer.ts` para OTel (TS) | 2026-09-30 | D1 | OBSOLETO | — |
| A1b | Deploy real do `k8s/` (TS) | 2026-09-30 | D1 | OBSOLETO | — |
| D7 | `MetricsDashboard`/`SelfAwareness` com dados reais (TS) | 2026-09-30 | D1; `AUDIT-4-modulos.md:143` | OBSOLETO | V21 |
| B5 (ST) | Hermes como runtime | 2026-10-03 | E §2.3 ("só o `plan_runner` é execution runtime") + regra do maestro "não criar um segundo runtime" | OBSOLETO | O worker que pedia já existe (#40) |
| A15 | Flags de cookie (não há cookies) | anterior a 2026-09-29 | A5 §5.4 | OBSOLETO | — |
| S25 | Autorização por identidade (caller) | 2026-09-27 | A5 §5.2 (defer consciente) | OBSOLETO | Reabrir com A13 se houver multi-tenant |
| P1–P5 / J1–J7 (backlog) | Constitution, META Compiler, AR-000…015, A2A, UI visual, Caveman | anterior a 2026-09-29 | A5 §5.2 e §5.4 (arquivados) | OBSOLETO | J1–J7 do backlog ≠ J1–J11 das frentes do P §4 |


## 8. Contradições resolvidas (40)

Padrão do EXECUTION-PLAN §16: onde estava o erro, o que é verdade e a evidência. V1–V26 são as 26 da auditoria cruzada (PR #65, `docs/ops/PENDENCIAS-CRUZADAS.md` §2.1); V27 em diante são novas desta consolidação.


| # | Item | Documento errado (onde) | Estado correcto | Evidência |
|---|---|---|---|---|
| V1 | AU-19 / J3 | P:304 "NÃO INICIADO"; P:140 "FEITO, falta só apagar a t6" | Fechado (#31); abertos F0.3, F0.6 e F0.12 | #31; RC:44-75 |
| V2 | AU-47 / J1 | P:332 "NÃO INICIADO" (o P §4 diz FEITO) | Fechado | Run #6 do keep-alive; O:104 |
| V3 | AU-05 / J7 | P:290 "MORTO" | Fechado | #30 |
| V4 | AU-16 / AU-49 | P:301/334 "NÃO INICIADO"; P:198 "aplicar orçamento: EM PR" | Fechados | #40, #42, #46; P §10 |
| V5 | AU-23 | P:308 "EM PR"; P:164 "bloqueado por D1" | Fechado | #40 |
| V6 | AU-26/30/33/34 | P:311/318 "NÃO INICIADO"; P:201 "EM PR"; O:157 "sem merge" | Fechados | #41, #33 |
| V7 | AU-09 | P:294 "NÃO INICIADO" (o P §6 #10 diz COMPLETO) | Fechado | #43 |
| V8 | S29 | P:341 "NÃO INICIADO" (o P §6 #9 diz FEITO) | Fechado; L4-1b aberto | #47 |
| V9 | J4 | P:142 sem estado | Fechado | #34; 38/38 agentes com `description:` |
| V10 | J5 | P:143 sem estado | Fechado | #33; P §10 |
| V11 | J10 | P:148 sem estado; O:259 linha "SEC-2 (DEV): J10" ao lado de "FEITO" | Fechado | #59 |
| V12 | B2b / B2c | P:355 "EM CURSO"; O:38-39 abertos sem nota do SEC-2 | B2b: só faltam Trivy/OSV; B2c: falta o backlog dos SECURITY-AUDIT | #59, #61 |
| V13 | AU-50 | P:335 "NÃO INICIADO" | Fechado desde o J3 | `migrate_t6_to_knowledge_chunks.sql:37-48` |
| V14 | S15a | O:33 "Crítico, aberto" | Fechado a 2026-09-20 | ST:36; P:376 |
| V15 | M6 / B13 | P:342 e O:16 "aberto" | Obsoleto (D1; Gemini no worker Python) | #40 |
| V16 | EX-C2 / C2 | P:346 e O:50 "aberto" | Fechado (decisão D1) | #33 |
| V17 | B3/B5/B6 (= EX-B3/M3/M4) | O:46-48 "abertos" | Obsoletos (D1) | P §13.1 |
| V18 | S24 | P:356 "EM CURSO"; O:24 aberto | Obsoleto (D1); a parte do MCPServer fechou via S11 | A5 §5.4 |
| V19 | A8 (= S11) | O:36 "Crítico"; e O:102 "Fechados: A8" é **outro** A8 | S11 fechado; o A8 de O:102 é o AU-31 (#32) | P:376; #32 |
| V20 | AU-01/02/13–15/17/18/21/38/41–43/48 | P §9 "NÃO INICIADO/EM CURSO" | Obsoletos (D1) | P:161-171; P §13.1 |
| V21 | D7 | O:19 aberto | Obsoleto (TS arquivado) | `AUDIT-4-modulos.md:143` |
| V22 | Integrar `claude/audit-completo` | O:121 "em aberto" | Integrado (o conteúdo do A8 está em main via #32/#33) | `git log` #32, #33 |
| V23 | D1–D4 | P:117 "As 4 decisões pendentes" | Tomadas (P §13.1) | #33 |
| V24 | Fase 1 dos meta-agentes | P:605 "nada implementado" | Implementada | #54; C-1 (#55) |
| V25 | Security pipeline v1 | O:246 "(branch, sem merge)" | Merged | #57 |
| V26 | D-EP10 / D-EP11 | O:290 e E:843-844 "em aberto" | Fechadas (A) | Decisão do maestro; PR #63 |
| V27 | S12 *(nova)* | O:54 "aberto" | Fechado | P:376; A5 §5.5 #8 |
| V28 | A22 *(nova)* | O:44 "9 alertas abertos" vs A5 §5.4 "A22 = M8 fechado" | NÃO VERIFICADO: mantido aberto até confirmar (§10 P-5) | E:800 (0 PRs abertos em 03/10) |
| V29 | E1–E7 conectores *(nova)* | O:20 e A5 §5.4 numeram de forma diferente (o A5 separa Crawl4AI e Trafilatura e omite `google/skills`) | ING-1..7 seguem O:20, como decidido na D-EP6 | E §9.5 (D-EP6) |
| V30 | AU-11 *(nova)* | A5 §5.1: "Prisma **ou** SQL" | O Prisma é TS arquivado (D1): o item reduz-se a SQL versionado e absorve B11/E8 | D1; O:21 |
| V31 | L4-3 vs ADR-M7 *(nova)* | O:198 diz "L4-3 … (ADR-M7)" | O ADR-M7 é "os 33 agentes do MCP no registo" (P:541) = E-002; o L4-3 é MCP → L4. Ficam separados | P:541 |
| V32 | R1–R4 do router *(nova)* | O:163-166 usam R1–R4; o AUDIT-1 usa R1–R13 para outra coisa | W-001..W-003; o R2 passa a alias do F6 | P:500 (`AUDIT-1` R1–R13) |
| V33 | "11 linhas inalcançáveis" *(nova; erro do PR #63, já corrigido lá)* | 1.ª versão do L5F0 §2 | Não existem: a migração J3 e o writer desdobram `a+b` | PR #63, commit `18616ad` |
| V34 | S33 / S15b / C8 *(nova)* | ST:62 (S33 "DONE"); ST:37 (S15b "N/A, fechado"); ST:17 (C8 "fechado 6/6") | Fechados só no papel. O objectivo de cada um vive noutro item: S33 → AU-20 (aberto); S15b → AU-47/J1 (keep-alive, fechado); C8 → AU-19/J3 (fechado, #31). Nenhum é um item a mais | A5:163; A5:169; A5:190; A5:296 |
| V35 | W-007 *(nova)* | O:120 "PR em curso" (30/09); este documento: NÃO VERIFICADO | Fechado: PR MCP #10 com merge (`840d8a8`) e teste e2e (`b29752e`) | `ANM:lib/memory.js:95-98` |
| V36 | S28 *(nova)* | ST:99 "tipicamente espaço em disco ou um ficheiro que mudou de tamanho" | A causa são permissões: `lock` e `partial/` do apt só são legíveis pelo root, e o `actions/cache` corre sem root | Log do run MCP #108 (job 108666727482); PR MCP #12 |
| V37 | INIT-094 *(nova)* | ST, secção Harnesses: estrelas antigas, licenças em falta, `dsh-desktop` descrito como "desktop para DeepSeek" | Ver §2 do doc: omnigent e grok-build são Apache-2.0; o dsh-desktop é o cliente do deepseek-harness | `docs/research/harnesses-multi-provider-2026-10.md` (PR #80) |
| V38 | R-002 *(nova)* | L5F0 §2.1: "28 dos 38 ficheiros nunca são actualizados" | O risco era real (o ingest não era incremental), mas os ficheiros estavam iguais: a 1.ª corrida incremental deu-os `UNCHANGED` | Corridas #156 (`unchanged=33`) e #163 (`unchanged=39`) |
| V39 | AU-10 *(nova)* | A5: "0/30 cabeçalhos do sync" (parecia esquecimento) | O sync punha o cabeçalho antes do `---` (partia o frontmatter) e apagava o README | `scripts/sync-skills-from-prod.sh` antes do #68; `runner/plan_runner/skills.py:20` |
| V40 | H-001 *(nova; erro desta consolidação)* | O fecho do H-001 (#70) deixou 4 ponteiros para o `STATUS.md` como fonte de pendentes: `README.md:36`, `docs/architecture/BOOTSTRAP.md:75` (que contradizia a própria `:27`), `docs/architecture/SECURITY.md:31` e `docs/STATUS.md:3` | Os pendentes estão só no `PENDENCIAS.md`; os 4 foram corrigidos no PR desta revisão. As referências históricas (ex.: `agents/meta/security_auditor.agent.md:44`) ficam | `grep -rn 'initiatives/STATUS.md'` na `main` `c9edd72` |


## 9. Como fechar um item

1. **Identificar:** o ID está no §4. Se o trabalho não tem ID, criar o item primeiro (§0, ponto 4).
2. **Implementar** num branch próprio; a mensagem de commit e o PR citam o ID (ex.: `F0.4:`).
3. **Testar:** o teste ou a verificação que prova o fecho fica no repo (ex.: `runner/tests/...`), ou fica descrito (query, run real) com o resultado.
4. **Citar no PR:** "Fecha `<ID>`".
5. **Depois do merge** (nunca antes): no mesmo PR, ou no seguinte, mover a linha do §4 para o §7, com a data e o PR, e actualizar as contagens (§5, §6 e o cabeçalho).
6. **Se o fecho revelar que um documento antigo estava errado:** acrescentar um V*n* no §8.
7. **Se o item deixar de fazer sentido:** propor OBSOLETO em A/B/C (§10). Só com a decisão do maestro passa para o §7.

## 10. Decisões (A/B/C, com recomendada)

**Decididas pelo maestro: P-1 a P-10, P-12 a P-15 (2026-10-03) e P-18 = C (2026-10-04).** **Pendentes:** P-11, P-16, P-17, P-19 (limiar do F0.7b) e P-20 (causa do R-005). Nenhuma decisão pendente foi assumida.


| # | Decisão | A | B | C | Recomendada |
|---|---|---|---|---|---|
| P-1 | Formato dos IDs | **Aplicada:** manter os IDs antigos que são únicos; dar IDs novos `<prefixo>-<NNN>` (3 dígitos) só aos itens que colidem ou não tinham ID; coluna "IDs antigos" + índice §11 | Renumerar tudo no formato novo (IDs antigos só como alias) | Manter os IDs antigos com sufixos (`A8-auth`, `A8-fm`) | **Decidida: A** (maestro). **Aplicada** (§3, §11) |
| P-2 | Backlog de nichos/ferramentas (G1–G4, H1–H4, I1–I11: 37 linhas) | **Aplicada:** uma linha por item (BLOQUEADO pelo F5/D-EP8 nos nichos; ABERTO por decisão de âmbito no resto) | Juntar numa linha guarda-chuva | Marcar OBSOLETO, substituído pelas matrizes P1/P2 do E | **Decidida: A** (maestro). **Aplicada** (37 linhas no §4); re-triar no F6 |
| P-3 | R-002: recuperar os 28 ficheiros nunca re-ingeridos | Deixar convergir com os pushes de docs (50 chunks por corrida) | O DEV corre uma vez `python scripts/ingest_apply.py --max-chunks 150` depois do merge do #64 (escreve em produção) | Subir o orçamento por omissão | **Decidida: B** (maestro, 2026-10-03): o DEV corre o ingest; esta sessão não toca. Nota: as corridas #156 e #163 já deram os ficheiros `UNCHANGED`; o SELECT F0.1b (R-002, esperado 163 linhas) confirma se ainda é preciso |
| P-4 | S-001/S-002 (checklist #14/#17): alvo por confirmar | OBSOLETO (o alvo era o `apps/api` TS) | Re-apontar para o MCP de produção (porta de entrada real) e verificar lá | Manter abertos como estão | **Decidida: B** (maestro, 2026-10-03). **Aplicada:** MCP #14 (S-001/S-002 no §7) |
| P-5 | A22: alertas do Dependabot | O DEV verifica a aba Security e fecha ou actualiza o item | Fechar já, segundo o A5 ("= M8 fechado") | Manter aberto sem prazo | **Decidida: A** (maestro, 2026-10-03): o DEV verifica a aba Security (A22) |
| P-6 | H-001: o papel do `STATUS.md` e os ponteiros | `BOOTSTRAP.md` e `CLAUDE.md` passam a apontar para este documento; o `STATUS.md` fica com o estado dos sistemas (Done/infra), sem lista de pendentes | Marcar também o `STATUS.md` como histórico | Não mexer | **Decidida: A** (maestro). **Aplicada:** #70 |
| P-7 | H-002: avisos do ruff que já existiam em `scripts/` | Registar e tratar no F3 | PR pequeno agora (o merge dispara o ingest; com o #64 é inofensivo) | Alargar o ruff do CI a `scripts/` | **Decidida: A** (maestro, 2026-10-03): fica no H-002, tratado no F3 |
| P-8 | PR #65 (`docs/ops/PENDENCIAS-CRUZADAS.md`) | Fazer merge do #65 antes deste (fica como evidência histórica da auditoria) | Fechar o #65 sem merge (o §8 deste documento incorpora as 26 contradições) | Fazer merge depois deste | **Decidida: A** (maestro). **Aplicada:** merge do #65 antes do #66 |
| P-9 | ID do item de portfólio: o maestro deu `H-01`; o formato do P-1 é `<prefixo>-<NNN>` | **Aplicada:** manter `H-01` como dado (regra: não inventar IDs para itens que já têm ID) | Renomear para `H-003`, com `H-01` como alias no §11 | Passar H-001/H-002 a 2 dígitos | **Decidida: A** (maestro, 2026-10-03: "H-01 mantém-se como está (não renomeies)"). A recomendação era B (`H-01` e `H-001` lêem-se quase iguais); fica registada, sem efeito |
| P-10 | AU-22: `done_when`, `on_fail` e `max_replans` (o runner ignora-os) | Implementar o `done_when` (verificação no fim); remover `max_replans` e `on_fail` | Implementar os 3 (F3) | Remover os 3 e só documentar | **Decidida: A** (maestro, 2026-10-03; consulta cruzada: uma 2.ª IA concordou). **Nota de execução (revisora):** a remoção do `on_fail` e do `max_replans` leva uma nota explícita no `plan.schema.json` ("a remover; fora até ao F3, por decisão, não por esquecimento"), já acrescentada às `description` dos 3 campos. O AU-22 fecha com o código e os testes |
| P-11 | AU-11: modelos Prisma da t6 (`KnowledgeSource`/`KnowledgeChunk`) | Removê-los num PR à parte, depois de confirmar que o `packages/memory` não os usa | Manter com o comentário de legado (#76) | Reapontá-los para `knowledge_chunks` | **A**: um só dono do DDL (`scripts/rag_schema.sql`) |
| P-12 | INIT-094: harnesses multi-provider | Não adoptar; opencodex + LiteLLM como candidatos do F3/§8.6 | Spike do opencodex já | Fechar como OBSOLETO | **Decidida: A** (maestro, 2026-10-03; consulta cruzada: uma 2.ª IA concordou). INIT-094 → OBSOLETO (§7) |
| P-13 | F1: ADR *Universal Ingestion & Research Primitives* | Aceitar o contrato e o spike, a correr depois do F0 verde | Aceitar o contrato; spike depois do F3 | Rever o contrato | **Decidida: A** (maestro, 2026-10-03; consulta cruzada: uma 2.ª IA concordou). ADR com o estado "Aceite"; o spike continua a esperar pelo F0 verde (F1 fica EM CURSO) |
| P-14 | ING-5: gitingest | Não adoptar; EXTRACT próprio se houver necessidade | Adoptar `==0.3.1` com reservas | Rejeitar de vez | **Decidida: A** (maestro, 2026-10-03; consulta cruzada: uma 2.ª IA concordou). ING-5 → OBSOLETO (§7) |
| P-15 | ING-6: ScrapeGraphAI | Não adoptar; `fetch` + worker no F2 | Spike no F2 | Rejeitar de vez | **Decidida: A** (maestro, 2026-10-03; consulta cruzada: uma 2.ª IA concordou). ING-6 → OBSOLETO (§7) |
| P-16 | S-001: valores dos tectos de input do MCP | Os do PR MCP #14 (`text` 200k, `request` 20k, …) | Mais apertados | Configuráveis por env | **A**: não partem nenhum uso real conhecido |
| P-17 | H-001: as listas de pendentes do `STATUS.md` | Marcadas HISTÓRICO (**aplicada**, #70) | Movê-las para `docs/archive/` no H-01 | Apagá-las | **A** agora e **B** no H-01; C corta conteúdo |
| P-18 | E-003: `ship-parallel.plan.yaml` usa `research`/`critic`, que resolvem sempre para agentes de marketing | Re-apontar os 3 reviews para agentes reais (`revisor_codigo` e `guia_tdd` em `engenharia`; `security_audit` em `meta`), com `vertical:`, e mover o ficheiro para `docs/orchestration/engenharia/examples/` (o guarda do AU-32, `test_skills.py:75`, passa a cobri-lo); ajustar `conftest.py` e `test_real_plans.py` | Manter o ficheiro como fixture do motor (wave paralela) e escrever no topo que não é um plano de domínio | Re-apontar as actions sem mover o ficheiro | **Decidida: C** (maestro, 2026-10-04): o ficheiro é um exemplo do motor (verificação da condição acima), por isso fica onde está com uma nota no topo, e acrescenta-se um plano de engenharia real à parte; C acrescenta sem cortar. Aplicada no PR #90 |
| P-19 | F0.7b: limiar mínimo do golden set para declarar o gate M1 (F0 verde) | **Mínimo de proveniência e de fonte:** `provenance_ok` = 1.0 e `source_hit@4` ≥ 0.8 (pelo menos 15 dos 18 casos). O `chunk_hit` e o MRR ficam registados como linha de base | Sem limiar: basta medir e registar (um run com 0 hits passaria o gate) | Limiar completo: o anterior, mais `chunk_hit@4` ≥ 0.7 e `mrr_chunk` ≥ 0.5 | **A** (proposta, 2026-10-05): impede um gate verde com o retrieve partido, sem inventar alvos de qualidade antes da 1.ª medição. Os limiares de qualidade ficam para o F3, com a linha de base na mão. **Pendente.** O 1.º run real (2026-10-05) cumpre as 3 opções (`provenance_ok` 1.0, `source_hit@4` 1.0, `chunk_hit@4` 0.944, `mrr_chunk` 0.736), por isso a escolha já não muda o veredicto do M1. Fica a valer para os runs seguintes, como teste de regressão. O M1 fechou a 2026-10-05 por decisão do maestro |
| P-20 | R-005: a causa do `kb` errado (o insert do MCP não define o `kb`, e a coluna tem `DEFAULT 'marketing'`) | Corrigir já no MCP: o `ingestDocument` passa a gravar o `kb` a partir do `agent_id`, com teste. As 201 linhas antigas ficam para o F3 | Esperar pelo F3 e fazer a causa e a reclassificação juntas | Versionar só a mudança do `DEFAULT` da coluna (SQL, sem executar) | **B** (proposta, 2026-10-05): o MCP não ingeriu nada desde 2026-10-03 (201 = 322 − 121), por isso o problema não cresce. Um PR no MCP faz redeploy na Vercel e mexe numa tool do connector. **Pendente** |


## 11. Índice de aliases (ID antigo → onde está agora)

Para quem chega com um ID antigo. Uma linha por item com aliases (§4) e por linha do histórico (§7).


| ID(s) antigo(s) | ID canónico | Onde |
|---|---|---|
| S33 | AU-20 | §4 (vivo); ver V34 |
| S15b | AU-47 / J1 | fechado (§7); ver V34 |
| C8 | AU-19 / J3 | fechado (§7); ver V34 |
| J3 passo 3 | F0.3 | fechado (§7) |
| J3 passo 5 | F0.6 | vivo (§4) |
| J3 passo 6 | F0.12 | vivo (§4) |
| ING-2 (= "E2" conector, O:20) | F1 | vivo (§4) |
| ING-3 | F1b | vivo (§4) |
| ING-1 | F2 | vivo (§4) |
| AU-35; B1 (ST:100, "2.º domínio"); R2 (O:164) | F6 | vivo (§4) |
| B12 (ST); E9 (O:22) | R-001 | vivo (§4) |
| B11 (ST); E8 (O:21) | AU-11 | fechado (§7) |
| ING-4 | AU-44 | vivo (§4) |
| "E5" conector (O:20) | ING-5 | obsoleto (§7) |
| "E6" conector (O:20) | ING-6 | obsoleto (§7) |
| J2 | S20 | vivo (§4) |
| A10 | B2b | vivo (§4) |
| A11 | B2c | vivo (§4) |
| checklist #20 | A9 | vivo (§4) |
| checklist #5 | A12 | vivo (§4) |
| checklist #7 | A13 | vivo (§4) |
| checklist #16 | A19 | vivo (§4) |
| M8 | A22 | vivo (§4) |
| C3 (O:51) | EX-C3 | vivo (§4) |
| C4 (O:52) | EX-C4 | vivo (§4) |
| G7 (ST) | B16 | vivo (§4) |
| checklist #14 | S-001 | fechado (§7) |
| checklist #17 | S-002 | fechado (§7) |
| J6 (sub-item) | T-003 | vivo (§4) |
| R1 (Bloco B; colide com R1 do AUDIT-1) | W-001 | vivo (§4) |
| R3 | W-002 | fechado (§7) |
| R4 | W-003 | vivo (§4) |
| B2 (Bloco B) | W-004 | vivo (§4) |
| B4 (Bloco B) | W-005 | fechado (§7) |
| B3 (Bloco B, O:150) | AU-20 | vivo (§4) |
| B7 (O:15) | EX-B7 | vivo (§4) |
| F7 (O:53; colide com as fases F*) | M-005 | vivo (§4) |
| J11 | L4-2 | vivo (§4) |
| D3 (DeepEval; colide com a decisão D3) | Q-001 | vivo (§4) |
| D4 (Ragas; colide com a decisão D4) | Q-002 | vivo (§4) |
| E1 (decisão §13.2; colide com o conector E1) | E-001 | vivo (§4) |
| E5 (decisão §13.2; colide com o conector E5) | E-002 | vivo (§4) |
| ING-7 | INIT-093 | vivo (§4) |
| F8; EX-F8 | INIT-094 | obsoleto (§7) |
| J8 (parte) | AU-45 | fechado (§7) |
| J8 (parte) | AU-46 | fechado (§7) |
| J8 (parte) | AU-08 | fechado (§7) |
| J8 (parte) | AU-10 | fechado (§7) |
| J8 (parte) | AU-12 | vivo (§4) |
| J8 (parte) | AU-37 | fechado (§7) |
| J9 (parte) | G1.1 | vivo (§4) |
| F20; F21 | G1.2 | vivo (§4) |
| D7 da Fase 3 (handoff) | G1.4 | vivo (§4) |
| B6 (ST) | G1.6 | vivo (§4) |
| B3 (ST:101) | G1.7 | vivo (§4) |
| B12 (secção 09-14) | G1.8 | vivo (§4) |
| B13 (secção 09-14) | G1.9 | vivo (§4) |
| F22; B14 | G1.10 | vivo (§4) |
| B10 (secção 09-14) | G1.11 | vivo (§4) |
| U3 | G1.12 | vivo (§4) |
| U7 | G1.13 | vivo (§4) |
| J9 (parte) | G2.1 | vivo (§4) |
| B4 (ST:102) | G2.4 | vivo (§4) |
| B11 (ST); U2; U6 | G3.1 | vivo (§4) |
| U6 | G3.3 | vivo (§4) |
| F10; I8; E10 (§13.2) | G4.1 | vivo (§4) |
| U1 | G4.2 | vivo (§4) |
| U4 | H1 | vivo (§4) |
| U8 | H2 | vivo (§4) |
| U9 | H3 | vivo (§4) |
| U5 | H4 | vivo (§4) |
| F1 (ST, ferramentas) | I1 | vivo (§4) |
| F2 (ST, ferramentas) | I2 | vivo (§4) |
| F3 (ST, ferramentas) | I3 | vivo (§4) |
| F4; F17 | I4 | vivo (§4) |
| F5; F16 | I5 | vivo (§4) |
| F7 (ST, ferramentas) | I6 | vivo (§4) |
| F8 (ST, ferramentas) | I7 | vivo (§4) |
| F11 (ST, ferramentas) | I9 | vivo (§4) |
| F15 (ST, ferramentas) | I10 | vivo (§4) |
| F12 (ST, ferramentas) | I11 | vivo (§4) |
| F0.2 | F0.2 | fechado (§7) |
| F0.10 | F0.10 | fechado (§7) |
| F0.11 | F0.11 | fechado (§7) |
| D-EP1..D-EP9 | D-EP1..D-EP9 | fechado (§7) |
| D-EP10 | D-EP10 | fechado (§7) |
| D-EP11 | D-EP11 | fechado (§7) |
| SEC-2d | SEC-2d | fechado (§7) |
| SEC-2b | SEC-2b | fechado (§7) |
| SEC-2c | SEC-2c | fechado (§7) |
| SEC-2 | SEC-2 | fechado (§7) |
| J10 | J10 | fechado (§7) |
| SEC-1 | SEC-1 | fechado (§7) |
| Security pipeline v1 | Security pipeline v1 | fechado (§7) |
| C-1 | C-1 | fechado (§7) |
| B1-bis-R2 | B1-bis-R2 | fechado (§7) |
| J5-c | J5-c | fechado (§7) |
| J5-b | J5-b | fechado (§7) |
| E12 | E12 | fechado (§7) |
| D-EP7 / MASTER-PLAN | D-EP7 / MASTER-PLAN | fechado (§7) |
| S29 | S29 | fechado (§7) |
| L4-1 | L4-1 | fechado (§7) |
| B5-bis | B5-bis | fechado (§7) |
| B1-bis | B1-bis | fechado (§7) |
| PLANO item 10 / L1 | PLANO item 10 / L1 | fechado (§7) |
| AU-09 | AU-09 | fechado (§7) |
| AU-49 | AU-49 | fechado (§7) |
| AU-16 | AU-16 | fechado (§7) |
| AU-26 / AU-30 / AU-33 / AU-34 | AU-26 / AU-30 / AU-33 / AU-34 | fechado (§7) |
| AU-23 | AU-23 | fechado (§7) |
| AU-07 | AU-07 | fechado (§7) |
| B1 (worker) | B1 (worker) | fechado (§7) |
| AU-19 / J3 | AU-19 / J3 | fechado (§7) |
| AU-50 | AU-50 | fechado (§7) |
| AU-05 / J7 | AU-05 / J7 | fechado (§7) |
| AU-47 / J1 | AU-47 / J1 | fechado (§7) |
| J6 | J6 | fechado (§7) |
| AU-31 / A8 (frontmatter) | AU-31 / A8 (frontmatter) | fechado (§7) |
| J4 | J4 | fechado (§7) |
| E7 | E7 | fechado (§7) |
| J5 | J5 | fechado (§7) |
| D1 / D2 / D3 / D4 | D1 / D2 / D3 / D4 | fechado (§7) |
| EX-C2 | EX-C2 | fechado (§7) |
| E6 / E8 / E9 / E11 / E13 / E14 | E6 / E8 / E9 / E11 / E13 / E14 | fechado (§7) |
| S29-bis | S29-bis | fechado (§7) |
| S15a | S15a | fechado (§7) |
| S11 / A8 (auth) | S11 / A8 (auth) | fechado (§7) |
| S12 | S12 | fechado (§7) |
| S5 | S5 | fechado (§7) |
| AU-01 / AU-02 / AU-03 / AU-04 | AU-01 / AU-02 / AU-03 / AU-04 | obsoleto (§7) |
| AU-13 / AU-14 / AU-15 / AU-17 / AU-18 / AU-21 | AU-13 / AU-14 / AU-15 / AU-17 / AU-18 / AU-21 | obsoleto (§7) |
| AU-24 / AU-27 / AU-28 / AU-29 | AU-24 / AU-27 / AU-28 / AU-29 | obsoleto (§7) |
| AU-38 / AU-39 / AU-40 / AU-41 / AU-42 / AU-43 | AU-38 / AU-39 / AU-40 / AU-41 / AU-42 / AU-43 | obsoleto (§7) |
| AU-48 / A4 | AU-48 / A4 | obsoleto (§7) |
| M3 / M4 / M5 | M3 / M4 / M5 | obsoleto (§7) |
| M6 / EX-B13 / B13 | M6 / EX-B13 / B13 | obsoleto (§7) |
| P6 | P6 | obsoleto (§7) |
| EX-B3 / B3 (O:46) | EX-B3 / B3 (O:46) | obsoleto (§7) |
| S24 / EX-S24 | S24 / EX-S24 | obsoleto (§7) |
| S13 / A23 | S13 / A23 | obsoleto (§7) |
| S14 | S14 | obsoleto (§7) |
| A1b | A1b | obsoleto (§7) |
| D7 | D7 | obsoleto (§7) |
| B5 (ST) | B5 (ST) | obsoleto (§7) |
| A15 | A15 | obsoleto (§7) |
| S25 | S25 | obsoleto (§7) |
| P1–P5 / J1–J7 (backlog) | P1–P5 / J1–J7 (backlog) | obsoleto (§7) |


## 12. Limites desta consolidação

- **Base:** `main` `e7a29ae`. Os PRs #63, #64 e #65 estão abertos; os itens que eles fecham aparecem como **EM CURSO**.
- **2.ª ronda (`main` `2b27f66`):**
  - 18 itens fechados com PR e/ou teste (§7);
  - em curso: #79–#82 (NAS) e #11–#14 (MCP);
- **Revisão pós-merge (`main` `d79d7be`; MCP `d635945`):**
  - fechados: W-005 (#79), S17 (MCP #11), AU-06 (MCP #13), S-001 e S-002 (MCP #14);
  - F1 continua EM CURSO (ADR com merge no #81; falta P-13 e o spike); S28 espera 1 run limpo;
  - novos: S-003 (connector) e H-004 (Graphify);
  - §10: P-1 a P-9 marcadas com a decisão do maestro (antes só P-1, P-2, P-6 e P-9 apareciam como decididas, e o P-9 mostrava a recomendação B, não a decisão).
- **Depois do merge de #80, #82, #83 e #84 (`main` `b74ea42`):** INIT-094, ING-5 e ING-6 já só esperam pelas decisões P-12, P-14 e P-15; continuam EM CURSO (análise feita), sem mudança nas contagens.
  - novos: R-004, E-003, H-003, T-004, T-005;
  - estado de produção do L5 lido dos logs públicos do `ingest-knowledge` (corridas #156 e #163), sem acesso ao Supabase.
- **Fontes lidas por completo:** P, O e E, mais o AUDIT-5 (inventário de ~175 itens, de onde vêm as linhas G/H/I e os S*/A* que o P e o O resumiam em bloco).
- **Não verificado nesta consolidação:** tudo o que precisa de SSH, da consola Oracle, do Supabase de produção ou da aba Security do GitHub (coluna `Verif.`).
- **Verificação das citações (antes do commit):**
  - as 188 citações `P:`/`O:`/`E:`/`ST:` e as de código foram conferidas por script contra `e7a29ae`;
  - 16 estavam desfasadas e foram corrigidas: 11 em `ST:` (+1), `O:195`, `P:500`, `ci.yml:129`, `ingest_delta.py:98` e o `ST:174-178` do INIT-093.
- **Lacuna corrigida depois do 1.º commit:**
  - os 4 "FECHADO-SÓ-NO-PAPEL" do A5:296 (C8, keep-alive, S33, S15b) não tinham entrada própria;
  - ficaram como aliases dos itens onde o objectivo vive (V34, §11).
  - Foi encontrado ao verificar a evidência do H-01.
- **Severidade dos grupos I/H/G3:** o A5 dá "Baixa–Média" em bloco; foi atribuída Baixa. Revisível sem decisão (não muda o âmbito).

