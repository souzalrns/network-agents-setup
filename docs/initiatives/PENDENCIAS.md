# PENDÊNCIAS: documento único de estado

> **Este é o ÚNICO documento com o estado dos pendentes** do `network-agents-setup` (e das partes do `agent-network-mcp` que este repo acompanha).
> **Criado em 2026-10-03**, por decisão do maestro, a partir da auditoria cruzada (PR #65), sobre `main` `e7a29ae`.
> **2.ª ronda (2026-10-03):** actualizado sobre `main` `2b27f66`, depois do merge dos PRs #63–#78. As evidências novas citam essa `main`; as siglas `P:`/`O:`/`E:` continuam ancoradas em `e7a29ae` (§0, item 7).
> **Privacidade (2026-10-07, `main` `c9de58f`, merge do #124):** GOV-IMPACT-1 → FECHADO com a política de privacidade (LGPD + GDPR), a avaliação de impacto (AIMS §5) e a separação repo público/privado (`config/deployment.yaml`, `.gitignore`, teste). Estado medido: 0 dados de clientes. Novos: GOV-RET-1 (purga por data), GOV-PRIV-1 (transcrição de terceiros no repo público do MCP), S-005 (`_prisma_migrations` sem RLS) e a decisão P-41 (prazos).
> **ISO/IEC 42001 e pós-merge (2026-10-07, `main` `7cda6f1`, merges #122 e #123):** SEC-1.3, W-011, R-006 e H-002 → FECHADO (§7). P-40 decidida pelo maestro (âmbito NAS + ANM; papéis maestro / DEV / Claude; auditoria trimestral e revisão semestral). Novos GOV-42001-1 (EM CURSO) e GOV-IMPACT-1 (ABERTO, Alta), prefixo GOV- no §3. Política e mapeamento em `docs/governance/` (PR do branch `docs/governance-iso42001`).
> **AU-20, pré-requisito (2026-10-07):** o branch `feat/activate-for-task-sec13` (outro agente) não importava: o `executor.py` chamava `activate_for_task`, que nunca chegou ao git (18 erros de colecção). Implementado e reforçado no mesmo branch, PR #123 (draft). Novos SEC-1.3 (EM CURSO) e SKILL-EXT-1 (BLOQUEADO, SkillsCat). O AU-20 continua ABERTO (P-37); contrato proposto em `docs/architecture/AU-20-TOOL-EXECUTOR.md`.
> **Revisão do EXECUTION-PLAN desde a Parte 1 (2026-10-07, 2.ª passagem):**
>   - **bloqueios desactualizados corrigidos:** R-005, 18 linhas G1/G2 ("F5 + D-EP8"), B1-bis-C, L4-2, L4-3, EX-B7;
>   - **compromissos do plano sem item, agora registados:** E-004, ING-008 a ING-011, R-007 a R-010;
>   - **R-010 é um achado real:** o `purge_one` nunca é chamado;
>   - **H-002 corrigido;** DOC do F4 medido (§7: F4-DOC); D-EP5 → P-39.
> **Revisão contra o EXECUTION-PLAN (2026-10-07):** #119, #120 e #121 com merge → **F3c, F3b-VALIDADE e F6-CADEIA FECHADOS** (§7; produção do F3c confirmada por SELECT: 7 fontes, 15 chunks com `locator`). O F3 passa a BLOQUEADO (só falta o que está estacionado). F3c-DESIGN-1 opção A aplicada (`repo_files` nos passos de design), com a razão do `EXCLUDED` corrigida (V42). W-011 e R-006 feitos em PR. Lacunas do Done do plano, novas: **F3-ART-1**, **F4-MAT-1** (P-38) e **F5-ROUTE-1**; a F2 regista a capability em falta. AU-20 → P-37 (recomendada B). §5 do DEV refeito.
> **Opção B confirmada pelo maestro (2026-10-06):** P-23 = A; **F6-CADEIA** (EM CURSO, fecha no merge do #121) e **F6 canónico** (BLOQUEADO, D-EP8) são 2 linhas distintas no §4; F3b-AUTH-1 no fim do §4, fora do caminho crítico. Ordem de merge: #119 → #120 (com CI na base `main`) → #121.
> **F6 da cadeia concluído (2026-10-06, PR #121):** hardening, evidence pack (`docs/portfolio/F6-evidence/`) e `docs/portfolio/WHAT-I-CONTRIBUTED.md`. P-23 = A decidida pelo maestro (2026-10-06, opção B confirmada): o F6 da cadeia fecha no `PENDENCIAS_T6.md`, e o F6 canónico (domínio de prova, D-EP8) continua no §4. Estacionados no fim do §4: **F3b-AUTH-1** (autoridade e conflitos: SQL da v3 + flag) e **F2-SEC-1** (DNS rebinding no `fetch`).
> **F3b, validade (2026-10-06):** P-27 a P-29 implementadas no PR do branch `feat/f3b-validity` (empilhado no do F3c): `config/knowledge-validity.yaml` (classes `legal`, `market_data` e `web` com TTL de 90 dias), `runner/plan_runner/validity.py` aplicado no `ingest_apply`, relatório local `scripts/validity_report.py`; sem SQL novo. Novo F3b-VAL-1: as 2 fontes de classe datada sem sidecar (o DEV dá as datas reais).
> **Decisões do F3b e do F3c (2026-10-06, maestro):** P-27 = C, P-28 = C, P-29 = A, P-30 = A, P-31 = D, P-32 = B, P-33 = B, P-34 = A, P-35 = A, P-36 = A (§10). O F3c é implementado no PR do branch `feat/f3c-knowledge-coverage` (MANIFEST + `EXCLUDED` + teste de cobertura; W-prod no merge). Itens novos, estacionados no fim do §4 com critério de desbloqueio: F3-MCP-1, F3c-DESIGN-1 e F3b-GS-1. O F0.12 ganha a prova de que a t6 está toda na canónica.
> **F3a FECHADO (2026-10-06):** prova directa da v2 em produção (`retrieve_knowledge` com `metadata` preenchido e `status` = `active`). O F3a passa para o §7; **o F3 continua EM CURSO** com o F3b e o F3c. O R-006 mantém-se (o `l5_eval` ainda não distingue a v1 da v2).
> **F3a em produção (2026-10-06):** o SQL está aplicado no Supabase, verificado com SELECTs ao catálogo (`match_knowledge_v2` e `match_knowledge` existem, as colunas novas e o CHECK do `status` também). O `l5_eval` do DEV com `KNOWLEDGE_RPC_V2=1` deu 18 casos, `chunk_hit@1/3/4` 0.611/0.889/0.944, `source_hit@4` 1.0, `mrr_chunk` 0.736, `no_hits` 0, `provenance_ok` 1.0: **iguais ao F0.7b, sem regressão**. Mas o `provenance_ok` só olha para o `citation.source`, que a v1 também devolve, por isso **não prova a v2**: a flag fica NÃO VERIFICADA até haver 1 hit com `metadata` preenchido. **O F3 continua EM CURSO** (faltam essa prova, o F3b e o F3c). Novo R-006 (o `l5_eval` passa a medir a proveniência da v2).
> **F5 FECHADO e F4 FECHADO (2026-10-06):** merges #113, #114 e #115 (`main` `0b7405a`) e MCP #19. O run real do DEV (3.º, `run_9017d441d1`) passou nos 5 critérios do `scripts/f5_evidence.py`. O F4 passa para o §7 pela regra do §9 (passo 5). O F3 continua EM CURSO: o SQL no Supabase e a flag `KNOWLEDGE_RPC_V2` são do DEV, e faltam o F3b e o F3c. Novos: W-011 (o runner valida o `MCP_URL` e o bypass à partida) e V41 (o runbook do F5 tinha o `MCP_URL` com `/api/mcp`).
> **F1 FECHADO e P-26 = A (2026-10-06):** merges #106–#112 (`main` `e10f772`). O F1 passa para o §7. O F3 arranca (EM CURSO) com a opção A do ADR-F3-PROVENANCE-RETRIEVE: SQL aditivo, `match_knowledge_v2` e o MCP atrás de feature flag.
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
> - **123 itens vivos** (§4): ABERTO 70, EM CURSO 6, BLOQUEADO 47;
> - **116 linhas de histórico** (§7): 95 fechadas, 21 obsoletas;
> - **42 contradições resolvidas** (§8): 26 da auditoria #65 + 16 novas;
> - **41 decisões** em A/B/C (§10): P-1 a P-10, P-12 a P-15 e P-18 decididas pelo maestro, P-26 a P-36 (2026-10-06) decididas pelo maestro e P-23 = A (2026-10-06) e P-40 (ISO/IEC 42001, 2026-10-07) decididas pelo maestro; pendentes P-11, P-16, P-17, P-19, P-20, P-21 (F1b), P-22 (upstream MarkItDown), P-24 (`scrape.yml`) e P-25 (allowlist por área).

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
| GOV- | **Acrescentado (2026-10-07):** governança de IA (ISO/IEC 42001, P-40) | `GOV-42001-1`, `GOV-IMPACT-1`; as excepções à política usam `GOV-EXC-<n>` (`docs/governance/AI-MANAGEMENT-SYSTEM.md` §8) |
| Q- | **Acrescentado:** qualidade / avaliação (EXECUTION-PLAN §15.12) | Recebe o DeepEval/Ragas (antes D3/D4) |
| L4- | Memória L4 (série existente) | L4-1b, L4-2, L4-3 já existiam; L4-4 é novo |
| ING- | Conectores de ingestão (D-EP6) | Já decididos; os que coincidem com F1/F1b/F2/AU-44/INIT-093 aparecem como alias |
| AU-, EX-, INIT-, SEC-, B*, A*, G*, H*, I*, J*, P*, U* | Séries antigas | Mantêm-se quando são únicas; quando colidem, a linha usa um ID novo e cita o antigo na coluna "IDs antigos" |


## 4. Tabela única (123 itens vivos)

Ordenada por grupo: F → R → S → C → T → W → M/L4/Q → E → H → backlog (G/H/I).


| ID | Título | Tipo | Estado | Dono | Sev | Bloqueio | Evidência | IDs antigos | Verif. |
|---|---|---|---|---|---|---|---|---|---|
| F0.6 | Passo 5 do J3: teste real no conector MCP (a resposta tem de citar a fonte) | FALTA-TESTE | BLOQUEADO | DEV | Média | **Conector do Claude.ai sem tools** (2026-10-05, no Claude.ai: "Este conector não possui ferramentas disponíveis"). Causa provável: a protecção da Vercel bloqueia o `tools/list`, e o conector não envia o cabeçalho `x-vercel-protection-bypass`. Desbloqueia com o bypass como query parameter nas settings do conector (posto de parte por agora: guarda o segredo no conector) ou com outra forma de expor o MCP ao conector | RC:69-70; E §7 F0; **decisão do maestro (2026-10-05): BLOQUEADO**, e o gate M1 fecha com o F0.7b como prova suficiente (o mesmo `retrieve_knowledge` contra produção: 18 de 18 com a fonte certa, `provenance_ok` 1.0). Registo em `docs/ops/L5-F0-REVALIDATION.md` §6.1. Tem de usar a tool `retrieve_knowledge` com `kb` = `security`: nenhum dos 33 agentes do MCP tem `agent_id` = `security`, por isso o `ask_agent_network` não chega ao pack | J3 passo 5 | VERIFICADO |
| F0.12 | Passo 6 do J3: apagar a `knowledge_chunks_t6` (irreversível, com backup; opcional) | FALTA-DECIDIR | ABERTO | DEV | Baixa | Backup + decisão (o F0.3 fechou: a t6 parou a 2026-09-29, com 110 linhas) | RC:72-75; E §7 F0; **2026-10-06 (SELECT só de leitura):** as 33 fontes da t6 (110 linhas) estão todas na `knowledge_chunks` com o mesmo n.º de chunks ou mais (o `docs/item-13-ai-findability.md` passa de 11 para 22, desdobrado por agente no J3): apagar a t6 não perde conteúdo. Continua opcional e irreversível, só com backup e decisão do DEV | J3 passo 6 | VERIFICADO |
| F1b | Docling, só se o benchmark do F1 o justificar (`docling-core>=2.48.4`) | FALTA-DECIDIR | BLOQUEADO | CLAUDE | Baixa | Documentos reais do domínio com perda de estrutura medida (P-21). O S5 do F1 (2026-10-05, fixtures sintéticas) mostra listas e tabelas a 100% e só os headings do PDF perdidos | E §7 F1b; AI:189 | ING-3 | VERIFICADO |
| F2 | Web research universal (discover/fetch) a partir do `scrape.yml` existente; Crawl4AI `>=0.9.3` só se o superar | FALTA-CONSTRUIR | EM CURSO | CLAUDE | Média | F2a (`fetch`) com merge no #111 (2026-10-05). Para o Done do E §7 F2 ("1 capability + 1 tool de fetch com provenance no artefacto") falta **a capability**: nenhum registo (`config/*-capabilities.yaml`) nem plano usa o `fetch` (revisão de 2026-10-07). O artefacto de research também não tem ainda o formato do E §3, ajuste 2 (`content`, `sources[]`, `limitations`, `artifacts`). Faltam também o `discover`, o fallback JavaScript e as decisões P-24 e P-25 | E §7 F2; AI:304; **F2a (2026-10-06):** `scripts/web_fetch.py` (allowlist em cada redirect, robots.txt RFC 9309, SSRF, tectos de bytes e de tempo, HTML → Markdown pelo adapter do F1 com `strict=True`, proveniência com `final_url`), `runner/tests/test_web_fetch.py` (42, servidor local), `docs/ops/WEB-FETCH.md` (corrida real no pypi.org); branch `feat/f2-web-fetch-provenance`; **candidato a adaptador de `fetch` (2026-10-05): Agent-Reach** (`Panniantong/Agent-Reach`, MIT, v1.5.0, commit `a19a171`): não acede por si, escolhe e testa ferramentas que já existem (Jina Reader, `yt-dlp`, `feedparser`, `gh`, Exa…); dependências `requests`, `feedparser`, `yt-dlp`, `pyyaml`; o `cookie_extract.py` lê cookies do browser localmente, sem envio de rede; o `install` usa `pipx`/`npm -g` (não corrido). Instalado num venv isolado: `agent-reach doctor` = 2/16 canais (RSS, web). **NÃO VERIFICADO:** os canais reais, porque a política de rede da sessão cloud recusa `r.jina.ai`, `www.youtube.com` e `github.com` (403 do proxy). Canais com cookies (Twitter/X, Reddit, XiaoHongShu, Facebook, Instagram) precisam de decisão de segurança antes de qualquer uso | ING-1 | VERIFICADO |
| F3 | Provenance formal + validade/conflitos + source authority + golden set alargado + cobertura dos 33 ficheiros fora do MANIFEST, pack a pack (D-EP2) | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Alta | **P-26 = A.** F3a, F3c e F3b-validade **FECHADOS** (§7; #113, #117, #119, #120). Falta, tudo estacionado ou noutro item: **F3b-AUTH-1** (autoridade e conflitos: SQL da v3 + flag no MCP), **F3b-GS-1** (golden set de marketing: quota) e **F3-ART-1** (proveniência na camada ARTIFACT, Done do E §7 F3). F3b-VAL-1 (datas de 2 fontes) é do DEV | E §7 F3; L5F0 §1–§2 (PR #63); `docs/architecture/adr/ADR-F3-PROVENANCE-RETRIEVE.md` (aceite, #112); **F3a (2026-10-06):** `scripts/migrations/f3_provenance_retrieve.sql` (aditiva, idempotente), `match_knowledge_v2`, `runner/plan_runner/provenance.py`, writer com `has_f3_columns`, `ingest_apply` com `INVALID_META`/`META_UPDATED`, testes `test_f3_provenance.py` + `test_provenance.py`; runbook em `docs/ops/RAG-CANONICAL.md`; PR #113 (merged; o SQL e o runbook chegaram antes à `main` no `2a9203a`); MCP: `agent-network-mcp` #19 (merged; flag `KNOWLEDGE_RPC_V2`); **produção (2026-10-06):** catálogo do Supabase com a `match_knowledge_v2`, as colunas novas da `knowledge_sources`, o `locator` e o `knowledge_sources_status_check`; prova directa da v2 (2026-10-06): `tools/call` do `retrieve_knowledge` em produção (`kb=security`, `top_k=1`): o hit traz `citation.uri` = `docs/knowledge/security-agents-stack.md` e `metadata` preenchido (`document_type` = `md`, `status` = `active`, `content_hash`). Na v1, o `metadata` é `null` e o `citation` não tem `uri`; e mesmo no fallback para a v1 com a flag ligada, `status` e `document_type` viriam `null`, porque só a `match_knowledge_v2` os devolve. O `locator` vem `null`, como esperado nas linhas antigas (preenche-se na re-ingestão); `l5_eval` do DEV com a flag: 18 casos, `chunk_hit@1/3/4` 0.611/0.889/0.944, `source_hit@4` 1.0, `mrr_chunk` 0.736, `no_hits` 0, `provenance_ok` 1.0 (iguais ao F0.7b) | — | VERIFICADO |
| F6 | **F6 canónico** (EXECUTION-PLAN §7, D-EP8): UM domínio de prova, com o Domain Onboarding Cost medido; escolhido só depois do F5, com uso real | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Média | D-EP8 (o F5 fechou a 2026-10-06; P-23 = A: o F6 da cadeia é outro item e fechou no `PENDENCIAS_T6.md`) | E §7 F6 e §9.5 (D-EP8); P:320 (AU-35) | AU-35; B1 (ST:100, "2.º domínio"); R2 (O:164) | VERIFICADO |
| R-001 | Investigar e documentar a tabela `knowledge_log` (existe no Supabase, 7 colunas, sem dono) | DOC-ERRADO | BLOQUEADO | AMBOS | Baixa | DEV corre as 5 queries só de leitura de `docs/ops/KNOWLEDGE-LOG.md` §3; depois A/B/C (§4 do doc) | #77 (`docs/ops/KNOWLEDGE-LOG.md`: 0 leitores/escritores nos 2 repos); A5 §5.2 (B12); O:22 (E9) | B12 (ST); E9 (O:22) | VERIFICADO |
| R-005 | Reclassificar o `kb` das 201 linhas do MCP (`project` NULL), todas com `kb` = marketing por omissão; as que não são de marketing (ex.: as 8 da fonte ECC "security-reviewer + database-reviewer", que vão para security) ficam com o `kb` errado. O destino do `agent_id` da ECC fica a confirmar | BUG | BLOQUEADO | CLAUDE | Alta | P-20 (a causa; proposta B). O F3a, de que dependia, fechou a 2026-10-06. Reclassificar as 201 linhas do MCP é escrita em produção (DEV) (revisão do EXECUTION-PLAN, 2026-10-07) | SELECTs do maestro (2026-10-05, 2.ª ronda): `SELECT kb, count(*) … WHERE project IS NULL GROUP BY kb` → marketing = 201, sem outro valor. **Causa confirmada:** `kb text DEFAULT 'marketing'` (`scripts/rag_schema.sql:51`), e o insert do MCP não define o `kb` (`ANM:lib/knowledge.js`, `ingestDocument`). Enquanto a causa não for corrigida, cada novo ingest do MCP grava `marketing`. 201 = 322 − 121: as linhas do MCP são as mesmas da revalidação de 2026-10-03 (L5F0 §0). Hoje o `match_knowledge` filtra só por `agent_id` (`scripts/rag_schema.sql:68`), por isso o `kb` errado ainda não muda a pesquisa; passa a mudar quando o retrieve filtrar por `kb` (F3). 1.ª ronda: a fonte ECC tem `agent_id` = revisor-codigo, `project` NULL e `kb` = marketing; `security-reviewer` não é um `agent_id` existente (o pack de security usa `security`, `scripts/ingest_delta.py:40`; o `docs/knowledge/imported-from-production/MANIFEST.md:9` mapeia a fonte para `revisor-codigo`). Severidade Alta por decisão do maestro (2026-10-05). Sucessor do R-003; correcção da causa (o insert do MCP passar a definir o `kb`) em A/B/C na §10 P-20 | — | VERIFICADO |
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
| B1-bis-C | Encurtar skills/prompt-base (meta <9k no `seo-article-demo`; base medida 10 136) | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Média | Ordem do maestro. Era "depois de F0–F3": o F0 (gate M1), o F1, o F2a, o F3a, o F3c e o F3b-validade já fecharam, e o F3 só tem estacionados (revisão do EXECUTION-PLAN, 2026-10-07) | P §6 #12; O:222; E §14.2; 6 prompts de agentes ainda dizem "Falha → `on_fail`" (`agents/design/ui`, `ux` e `ux_writer`; `agents/marketing/research`; `agents/security/security_report` e `security_triage`). O AU-22 não os mudou, para não mexer na base medida do `seo-article-demo`; reescrever aqui | — | VERIFICADO |
| T-001 | Medir o custo do pack Claude (`revisor-codigo`, `guia-tdd`) antes de cortar | FALTA-TESTE | ABERTO | AMBOS | Baixa | Run real (`GEMINI_API_KEY`) | E §9.2 | — | VERIFICADO |
| T-002 | Medir o conselho `security` no 1.º uso real | FALTA-TESTE | ABERTO | AMBOS | Baixa | 1.º uso real | E §9.2; `docs/ops/COUNCIL.md` | — | VERIFICADO |
| T-003 | Confirmar a 1.ª linha real em `token_usage` (MCP de produção) | FALTA-TESTE | ABERTO | DEV | Baixa | Acesso ao Supabase | O:118 | J6 (sub-item) | NÃO VERIFICADO |
| W-001 | `router eval` com o Gemini real: medir a escolha do agente | FALTA-TESTE | ABERTO | DEV | Média | `GEMINI_API_KEY` | O:163; E:784; P §10 (ressalvas) | R1 (Bloco B; colide com R1 do AUDIT-1) | VERIFICADO |
| W-003 | Robustez das keywords do router (negação, pesos) | FALTA-CONSTRUIR | BLOQUEADO | CLAUDE | Baixa | W-001 (casos reais) | O:166 | R4 | VERIFICADO |
| W-004 | Ledger central: as linhas do worker também no Supabase | FALTA-LIGAR | ABERTO | DEV | Média | Escrita em produção (DEV) | O:149 | B2 (Bloco B) | VERIFICADO |
| W-010 | Migrar o cliente MCP do runner (`runner/plan_runner/mcp_knowledge.py`) para a linha 2.x do pacote `mcp`, que mudou a API: o `streamable_http_client` devolve 2 valores, o `http_client` passa a ser `httpx2.AsyncClient` e o `CallToolResult` usa `is_error` | FALTA-CONSTRUIR | ABERTO | CLAUDE | Baixa | — | Achado do F0.7b (2026-10-05): `mcp` 2.0.0 saiu a 2026-07-28 e a 2.3.0 a 2026-10-02 (PyPI). Inspeccionado em `mcp==2.3.0`: `mcp/client/streamable_http.py` (`yield read_stream, write_stream`; `http_client: httpx2.AsyncClient`) e `mcp.types.CallToolResult` (`is_error`). Até lá, `runner/requirements.txt` fixa `mcp==1.30.0` e o cliente recusa a 2.x com uma mensagem clara (PR do branch `fix/F0-7b-mcp-versao`). A migração precisa de um teste com um servidor MCP real local, porque os testes actuais usam falsos | — | VERIFICADO |
| AU-20 | Tools: fonte do `tools_allowed` e execução no worker (hoje declarativo; o worker não executa tools) | FALTA-CONSTRUIR | ABERTO | AMBOS | Alta | Decisão **P-37** (porte do ToolExecutor TypeScript vs executor mínimo em Python; recomendada B) | P:305; O:150; `runner/tests/test_security_pipeline.py` ("Nao tens tools"); **2026-10-07:** os planos de design declaravam `tools_allowed: [read_repo_file]` sem efeito; contornado com `repo_files:` (F3c-DESIGN-1, opção A); pré-requisito SEC-1.3 (PR #123); contrato contract-first proposto em `docs/architecture/AU-20-TOOL-EXECUTOR.md` (2026-10-07, à espera da P-37); secção ISO/IEC 42001 no contrato (controlos do executor ↔ norma; PR do branch `docs/governance-iso42001`) | B3 (Bloco B, O:150); S33 (A5:169) | VERIFICADO |
| EX-B7 | Expor `engine: langgraph` + `decision: edit` na superfície MCP | FALTA-LIGAR | ABERTO | CLAUDE | Média | Era "depois do F5" (E §9.2): o F5 fechou a 2026-10-06, por isso pode avançar. Verificar o impacto no conector do Claude.ai, hoje sem tools (F0.6) (revisão do EXECUTION-PLAN, 2026-10-07) | P:351; O:15; E:793 | B7 (O:15) | VERIFICADO |
| AU-22b | Reescrever numa das 2 formas verificáveis a condição de `done_when` em linguagem livre do `paid-pack.plan.yaml` ("no ad_account_mutation without approve"); o evento `done_when_unverifiable` é o gatilho para encontrar outras | FALTA-CONSTRUIR | ABERTO | CLAUDE | Baixa | F3 (decisão do maestro, 2026-10-04) | `docs/orchestration/marketing/templates/paid-pack.plan.yaml`; `runner/plan_runner/done_when.py` (evento `done_when_unverifiable` com `item: AU-22b`); PR #90 | — | VERIFICADO |
| M-001 | Fase 2: Execution Broker (EXECUTE/REDIRECT/WAIT/DEFER/BLOCK) | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Média | F0–F6 + C-2 (D-EP5) | `docs/architecture/META-AGENTS-PHASE-2.md`; O §Fase 2; E §8.3 e §9.3 | — | VERIFICADO |
| M-002 | Fase 2: Execution Lease (1 tarefa → 1 lease activa) | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Média | F0–F6 + C-2 (D-EP5) | E §8.7 e §9.3; O §Fase 2 | — | VERIFICADO |
| M-003 | Fase 2: Execution Package (contexto para redirect) | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Baixa | M-002 | E §8.8 e §9.3 | — | VERIFICADO |
| M-004 | Fase 2: Learning (estimado vs real no ledger) | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Baixa | M-001 | E §8.11 e §9.3; O §Fase 2 | — | VERIFICADO |
| M-005 | PMO / Project Director (decisão organizacional) | FALTA-DECIDIR | ABERTO | DEV | Média | Decisão | O:53; A5 §5.4 | F7 (O:53; colide com as fases F*) | VERIFICADO |
| L4-1b | Teste real mínimo da L4 pela CLI (`remember` → `recall` → `promote` → `recall` → `forget`) | FALTA-TESTE | ABERTO | DEV | Média | `DATABASE_URL` | O:196; E:783; P §6 #9 | — | VERIFICADO |
| L4-2 | Spike comparativo do mem0 (só padrões, não substitui a L4) | FALTA-DECIDIR | ABERTO | AMBOS | Baixa | Era "depois do F3" (E §9.2): o F3 só tem estacionados, por isso pode avançar. Só padrões do mem0, sem substituir a L4 (D3; revisão do EXECUTION-PLAN, 2026-10-07) | O:197; E:789 | J11 | VERIFICADO |
| L4-3 | Ligar o MCP de produção à L4 | FALTA-LIGAR | ABERTO | AMBOS | Média | Era "depois do F5" (E §9.2): o F5 fechou a 2026-10-06, por isso pode avançar. Verificar o impacto no conector do Claude.ai, hoje sem tools (F0.6) (revisão do EXECUTION-PLAN, 2026-10-07) | O:198 | — | VERIFICADO |
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
| H-01 | Limpeza e organização para portfólio (opção C: README para negócio + `docs/` para técnico): lixo, arquivo dos históricos, índices, README, 3–5 casos de estudo, métricas e timeline | FALTA-CONSTRUIR | EM CURSO | AMBOS | Média | Faltam as partes 1 (limpeza), 2 (arquivo dos históricos) e 3 (índices), com os riscos do §4.1; o AU-12 e o H-001 são decisões prévias à parte 2 | Partes 4, 5 e 6 no PR #93 (merged 2026-10-05, `main` `92cc762`): README para portfólio em inglês, casos de estudo e números verificados, `LICENSE`, `SECURITY.md`, avisos de arquivado em `packages/` e `apps/`; Auditoria #65 (`docs/ops/PENDENCIAS-CRUZADAS.md`); adendo do maestro (03/10); âmbito, factos e riscos no §4.1; ID em §10 P-9; **README:** coberto pelo H-01 (decisão do maestro, 2026-10-03: A); 10 factos verificados no §4.1; vitrine para recrutadores (2026-10-05, PR do branch `docs/portfolio-recrutadores`): `docs/PORTFOLIO.md` novo, da plataforma (resumo EN de 60 s + PT, só números verificados), com o anterior, de marketing, preservado em `docs/PORTFOLIO-MARKETING.md`; linha "Start here" no README. A Description do NAS já está feita pelo maestro; os Topics estão vazios nos 2 repos (só na UI do GitHub); GIF do quickstart (`docs/assets/quickstart-demo.gif`, gerado a partir da saída real de um run stub) no README e no PORTFOLIO (PR do branch `docs/resolver-possiveis`); `docs/PORTFOLIO.md` expandido (PR do branch `docs/portfolio-recruiters`): títulos bilingues, números com a fonte de cada um, linha do tempo, guia do código; deixa de repetir o Quickstart e as histórias do README; bloco "For recruiters / visitors" no README | — | VERIFICADO |
| G1.1 | Trading: pesquisa padrão ouro de repos de trading/simulação | FALTA-DECIDIR | BLOQUEADO | AMBOS | Alta | D-EP8 (o F5 fechou a 2026-10-06) (domínio só com uso real) | A5 §5.4 (grupos G–J); EP:1618-2428 | J9 (parte) | VERIFICADO |
| G1.2 | Trading: World Monitor + Finance News Aggregator (licença AGPL a avaliar) | FALTA-DECIDIR | BLOQUEADO | DEV | Média | D-EP8 (o F5 fechou a 2026-10-06) | A5 §5.4 (grupos G–J); EP:1618-2428 | F20; F21 | VERIFICADO |
| G1.3 | Trading: competências dos papéis financeiros | FALTA-DECIDIR | BLOQUEADO | DEV | Alta | D-EP8 (o F5 fechou a 2026-10-06) | A5 §5.4 (grupos G–J); EP:1618-2428 | — | VERIFICADO |
| G1.4 | Trading: contratos de dados entre papéis | FALTA-DECIDIR | BLOQUEADO | DEV | Alta | D-EP8 (o F5 fechou a 2026-10-06) | A5 §5.4 (grupos G–J); EP:1618-2428 | D7 da Fase 3 (handoff) | VERIFICADO |
| G1.5 | Trading: isolar credenciais / garantir que não há execução real (pré-requisito de ordens autónomas) | FALTA-DECIDIR | BLOQUEADO | DEV | Crítica | D-EP8 (o F5 fechou a 2026-10-06); gate §6.3 do E | A5 §5.4 (grupos G–J); EP:1618-2428 | — | VERIFICADO |
| G1.6 | Trading: MiroFish e repos de simulação (AGPL) | FALTA-DECIDIR | BLOQUEADO | DEV | Baixa | D-EP8 (o F5 fechou a 2026-10-06) | A5 §5.4 (grupos G–J); EP:1618-2428 | B6 (ST) | VERIFICADO |
| G1.7 | Trading: agente de trading em simulação | FALTA-DECIDIR | BLOQUEADO | DEV | Alta | D-EP8 (o F5 fechou a 2026-10-06) | A5 §5.4 (grupos G–J); EP:1618-2428 | B3 (ST:101) | VERIFICADO |
| G1.8 | Trading: agente de investimentos | FALTA-DECIDIR | BLOQUEADO | DEV | Média | D-EP8 (o F5 fechou a 2026-10-06) | A5 §5.4 (grupos G–J); EP:1618-2428 | B12 (secção 09-14) | VERIFICADO |
| G1.9 | Trading: análise de volatilidade | FALTA-DECIDIR | BLOQUEADO | DEV | Média | D-EP8 (o F5 fechou a 2026-10-06) | A5 §5.4 (grupos G–J); EP:1618-2428 | B13 (secção 09-14) | VERIFICADO |
| G1.10 | Trading: agente jornalístico → investidor | FALTA-DECIDIR | BLOQUEADO | DEV | Baixa | D-EP8 (o F5 fechou a 2026-10-06) | A5 §5.4 (grupos G–J); EP:1618-2428 | F22; B14 | VERIFICADO |
| G1.11 | Trading: orquestrador do cluster financeiro | FALTA-DECIDIR | BLOQUEADO | DEV | Alta | D-EP8 (o F5 fechou a 2026-10-06) | A5 §5.4 (grupos G–J); EP:1618-2428 | B10 (secção 09-14) | VERIFICADO |
| G1.12 | Trading: tela de agentes financeiros | FALTA-DECIDIR | BLOQUEADO | DEV | Baixa | D-EP8 (o F5 fechou a 2026-10-06) | A5 §5.4 (grupos G–J); EP:1618-2428 | U3 | VERIFICADO |
| G1.13 | Trading: avatar financeiro | FALTA-DECIDIR | BLOQUEADO | DEV | Baixa | D-EP8 (o F5 fechou a 2026-10-06) | A5 §5.4 (grupos G–J); EP:1618-2428 | U7 | VERIFICADO |
| G1.14 | Trading: critério de "pronto" do cluster | FALTA-DECIDIR | BLOQUEADO | DEV | Alta | D-EP8 (o F5 fechou a 2026-10-06) | A5 §5.4 (grupos G–J); EP:1618-2428 | — | VERIFICADO |
| G2.1 | Gamedev: pesquisa padrão ouro (GDD, engine, loop) | FALTA-DECIDIR | BLOQUEADO | AMBOS | Alta | D-EP8 (o F5 fechou a 2026-10-06) | A5 §5.4 (grupos G–J); EP:1618-2428 | J9 (parte) | VERIFICADO |
| G2.2 | Gamedev: âmbito (documento vs protótipo jogável) | FALTA-DECIDIR | BLOQUEADO | DEV | Alta | D-EP8 (o F5 fechou a 2026-10-06) | A5 §5.4 (grupos G–J); EP:1618-2428 | — | VERIFICADO |
| G2.3 | Gamedev: engine-alvo | FALTA-DECIDIR | BLOQUEADO | DEV | Alta | D-EP8 (o F5 fechou a 2026-10-06) | A5 §5.4 (grupos G–J); EP:1618-2428 | — | VERIFICADO |
| G2.4 | Gamedev: implementar | FALTA-DECIDIR | BLOQUEADO | DEV | Alta | D-EP8 (o F5 fechou a 2026-10-06) | A5 §5.4 (grupos G–J); EP:1618-2428 | B4 (ST:102) | VERIFICADO |
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
| F3-MCP-1 | Estender a validade e a autoridade do F3b às linhas do MCP (`knowledge_chunks` com `project` NULL, 201 linhas): criar linhas na `knowledge_sources` pelo `ingestDocument` ou por migração controlada | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Média | Impacto no conector do Claude.ai e posse dos dados (P-30 = A: o F3b cobre só o T6) | Achado do F3b (2026-10-06): na `match_knowledge_v2` o JOIN com a `knowledge_sources` só existe para `project = 'network-agents-setup'` (`scripts/migrations/f3_provenance_retrieve.sql:108`); as linhas do MCP nunca expiram nem podem ser revogadas, e várias têm títulos datados ("verificado 12/09/2026") | — | VERIFICADO |
| F3c-DESIGN-1 | Migrar o pack `docs/knowledge/design/` (10 ficheiros, 22 chunks) para o RAG | FALTA-DECIDIR | BLOQUEADO | CLAUDE | Baixa | Um consumidor de `kb: design` (um plano do runner ou o conector, que espera pelo F0.6). P-36 = A | `scripts/ingest_delta.py` (`EXCLUDED`, razão P-36); o `runner/tests/test_knowledge_coverage.py` falha quando um plano passar a usar `kb: design`, o que desbloqueia este item; **opção A aplicada (maestro, 2026-10-07):** os 4 passos de design dos 2 planos de design recebem os ficheiros que as skills nomeiam por `repo_files:` (SEC-1); `runner/tests/test_plan_repo_files.py`. O item continua para a migração para o RAG | — | VERIFICADO |
| F3b-GS-1 | Golden set de marketing completo (~20 casos, medido contra o MCP real) | FALTA-TESTE | BLOQUEADO | AMBOS | Média | Quota de embeddings e prioridade (P-34 = A: os casos sintéticos de validade e conflito correm primeiro, no CI) | O marketing tem 16 dos 17 blocos `knowledge:` dos planos e 0 casos de avaliação; só existe o `config/l5-golden-security.yaml` (18 casos). O run real usa o `l5_eval run` do DEV (credenciais) | — | VERIFICADO |
| F3b-VAL-1 | Datas reais nas 2 fontes de classe datada do MANIFEST: `docs/knowledge/legal/direito-br-pt.md` (classe `legal`: `effective_from`) e `docs/knowledge/imobiliario/fipezap.md` (classe `market_data`: `effective_until`), num `<nome>.meta.yaml` ao lado | FALTA-DECIDIR | ABERTO | DEV | Média | — (só o autor sabe as datas; P-28 = C: não se inventam) | `python scripts/validity_report.py` assinala as 2 como `falta_data`; o `ingest_apply` dá um AVISO em cada corrida, sem falhar. Formato do sidecar em `docs/ops/RAG-CANONICAL.md` § F3b | — | VERIFICADO |
| F2-SEC-1 | `fetch` (F2a): SSRF por DNS rebinding entre a verificação do endereço e o pedido do httpx | FALTA-CONSTRUIR | ABERTO | CLAUDE | Baixa | — (mitigado pela allowlist explícita em cada chamada, P-25 B) | Limitação documentada em `docs/ops/WEB-FETCH.md:40`; registada no hardening do F6 (`docs/portfolio/F6-evidence/hardening.md`). Correcção: o pedido usa o IP já verificado (pinning) | — | VERIFICADO |
| F3-ART-1 | Proveniência na camada ARTIFACT (Done do E §7 F3: "provenance em todos os artefactos"): o bloco de conhecimento do runner mostra só `source @ locator`, sem o `uri`, o `status` nem a validade que a v2 já devolve, e o `result.json` não lista as fontes usadas | FALTA-CONSTRUIR | ABERTO | CLAUDE | Média | — | `runner/plan_runner/knowledge.py:118-121` (`grounding_block`); `docs/ops/L5-F0-REVALIDATION.md:137` ("fontes no result.json"); revisão de 2026-10-07 | — | VERIFICADO |
| F4-MAT-1 | Maturidade de capability com a escala do E §15.7 (`DRAFT → DECLARED → WIRED → EXECUTABLE → VALIDATED → PROVEN`). O F4 implementou `planned/deferred/partial/implemented` (`capabilities.py:39`), sem mapeamento: o `security.defensive_audit` não aparece como PROVEN apesar do run real do F5 | FALTA-DECIDIR | ABERTO | AMBOS | Média | Decisão **P-38** | E §7 F4 item 5 e §15.7; `config/security-capabilities.yaml:22-28`; revisão de 2026-10-07. O F4 continua FECHADO (o Done era o E7) | — | VERIFICADO |
| F5-ROUTE-1 | Run real que comece no `route` do runner (discover → select) e siga a cadeia do E §7 F5 (`discover → select → authorize → execute → validate → audit`); o run do F5 partiu do plano já escolhido | FALTA-TESTE | ABERTO | AMBOS | Baixa | Run do DEV (credenciais) | `runner/plan_runner/router.py:363` (`route()`); `docs/ops/F5-E2E-RUN.md`; revisão de 2026-10-07. O F5 continua FECHADO (o Done era o run real) | — | VERIFICADO |
| E-004 | Capabilities curtas de software (implementação, revisão, TDD) num `config/software-capabilities.yaml`, validado no E7, depois de medir o pack Claude (T-001) | FALTA-CONSTRUIR | ABERTO | AMBOS | Baixa | T-001 (medir antes de cortar) | E §5.16, ponto 3 ("depois do F4": o F4 fechou a 2026-10-06); revisão do EXECUTION-PLAN, 2026-10-07 | — | VERIFICADO |
| ING-008 | Completar o contrato do `ingest_document`: `source` = `path`, `url`, `bytes` ou `connector_ref` (E §3, ajuste 1). Hoje só há `path`; o `url` passa pelo `fetch` do F2, e o `connector_ref` liga com o AU-44 | FALTA-CONSTRUIR | ABERTO | CLAUDE | Baixa | — | `docs/architecture/adr/ADR-INGESTION-PRIMITIVES.md:28,45,88` (o spike ficou só com `path`, de propósito); revisão do EXECUTION-PLAN, 2026-10-07 | AU-44 | VERIFICADO |
| ING-009 | Document intelligence como capability de plataforma (E §4.4, ponto 4): o `ingest_document` existe como script, mas nenhuma capability nem plano o usa, e a área `docs` está vazia | FALTA-LIGAR | ABERTO | CLAUDE | Média | AU-20 / P-37 (para ser tool de um passo) ou um plano de ingestão | E §4.1 ("Document intelligence: gap"); revisão do EXECUTION-PLAN, 2026-10-07 | — | VERIFICADO |
| ING-010 | Avaliar o Instructor (extracção estruturada com LLM) | FALTA-DECIDIR | ABERTO | DEV | Baixa | Decisão de âmbito; contract-first (E §15.4) antes de código | E §2.3, categoria 1 ("A avaliar"); revisão do EXECUTION-PLAN, 2026-10-07 | — | VERIFICADO |
| ING-011 | Unstructured (60+ formatos) | FALTA-DECIDIR | BLOQUEADO | DEV | Baixa | DEFER: dependências de sistema pesadas (E §14.3); só reabre se o MarkItDown e o Docling falharem num formato real | E §2.3, categoria 1; `FASE3-AGENTES.md:42`; revisão do EXECUTION-PLAN, 2026-10-07 | — | VERIFICADO |
| R-007 | Modelo bi-temporal do Graphiti no próximo ADR de memória (`valid_from`, `valid_until`, `observed_at`, `confidence`, `supersedes`), como padrão e não como serviço | FALTA-DECIDIR | ABERTO | CLAUDE | Baixa | — | E §2.3, categoria 2; a L4 já tem `supersedes`/`expires_at` e o F3a já tem `effective_*` e `status` na L5; revisão do EXECUTION-PLAN, 2026-10-07 | — | VERIFICADO |
| R-008 | Camada de grafo e entidades ao estilo do LightRAG (padrão, nativo em Postgres) | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Baixa | A sequência do E §2.3: só depois da avaliação de retrieval alargada (F3b-GS-1) | E §2.3, categoria 2; E §10.1 ("LightRAG ou Graphiti como serviço": não); revisão do EXECUTION-PLAN, 2026-10-07 | — | VERIFICADO |
| R-009 | Sunset da `match_knowledge` v1 e da flag `KNOWLEDGE_RPC_V2` (E §15.10: `deprecated_at`, `replacement`, `reason`, `migration`) | FALTA-DECIDIR | BLOQUEADO | AMBOS | Baixa | A v2 estável em produção durante um período a decidir; depois, 1 PR no MCP (tirar a flag) e o SQL do DEV (`DROP FUNCTION match_knowledge`) | `docs/architecture/adr/ADR-F3-PROVENANCE-RETRIEVE.md` §4 ("O match_knowledge antigo sai num PR posterior, com decisão"); revisão do EXECUTION-PLAN, 2026-10-07 | — | VERIFICADO |
| R-010 | Purge no ingest: uma fonte que sai do MANIFEST ou do git tem de sair do índice (regra T6, E §15.8 e §15.12). O `purge_one` existe no `ingest_apply.py`, mas nada o chama | FALTA-LIGAR | ABERTO | AMBOS | Média | Escreve em produção (apaga linhas): o código é do Claude, a activação é do DEV | `scripts/ingest_apply.py:268` (definido, sem chamadas); `scripts/ingest_delta.py:221` (`apply_purge_stub`). Hoje o MANIFEST só cresce, por isso ainda não há órfãos; revisão do EXECUTION-PLAN, 2026-10-07 | — | VERIFICADO |
| F3b-AUTH-1 | Autoridade e conflitos do F3b (P-31 = D, P-32 = B, P-33 = B): `match_knowledge_v3` aditiva com a autoridade (`oficial`/`curado`/`experimental`, por path com override no sidecar) e o filtro `min_authority`; `superseded_by`; anotação de autoridade e data no bloco de conhecimento do runner e regra no prompt do worker; flag no MCP | FALTA-CONSTRUIR | BLOQUEADO | AMBOS | Média | Precisa de SQL em produção (o DEV corre a v3) e de um PR no MCP com flag; estacionado (maestro, 2026-10-06, opção B): não é pré-condição do F6-CADEIA | Decisões no §10; padrão do F3a (`scripts/migrations/f3_provenance_retrieve.sql`, `ANM:lib/knowledge.js`); a supersessão por `status: superseded` já funciona na v2 (`test_f3_provenance.py`) | — | VERIFICADO |
| SKILL-EXT-1 | Provider SkillsCat na pesquisa de skills externas (pedido no relatório do `activate_for_task`) | FALTA-DECIDIR | BLOQUEADO | AMBOS | Baixa | Contrato da API não verificável (sem documentação; o endpoint `skills.cat/api/search` não está confirmado) e serviço AGPL-3.0. Desbloqueia com o contrato documentado e a decisão do maestro sobre as licenças dos candidatos | `docs/ops/SKILL-ACTIVATION.md` (secção "SkillsCat: estacionado"); hoje `external_provider: skillscat` dá o aviso `provider_unsupported` e não pesquisa | — | VERIFICADO |
| GOV-42001-1 | ISO/IEC 42001 (P-40): sistema de gestão de IA, alinhamento voluntário (não certificação), âmbito NAS + ANM. Fechar as lacunas `Parcial`/`Falta` do mapeamento: avaliação de risco periódica (6.1.2, 8.2), objectivos mensuráveis (6.2, A.9.3), competências (7.2, A.4.6), fornecedores avaliados (A.10.3), clientes (A.10.4), reporte externo e incidentes (A.8.3, A.8.4), 1.ª auditoria interna (2027-01) e 1.ª revisão da política | FALTA-CONSTRUIR | EM CURSO | AMBOS | Média | #124 com merge (2026-10-07, `c9de58f`): política, mapeamento e teste em vigor. Falta fechar cada lacuna `Parcial`/`Falta` do mapeamento | `docs/governance/AI-MANAGEMENT-SYSTEM.md`; `docs/governance/ISO-42001-MAPPING.md` (27 cláusulas, 38 controlos, Declaração de Aplicabilidade); `runner/tests/test_governance_mapping.py` | — | VERIFICADO |
| GOV-RET-1 | Retenção por data (política de privacidade §7): purga automática no fim do contrato + 90 dias (memória do cliente, `project_state` e `agent_log` por `project`, L4 por `expires_at`), 24 meses no `token_usage` e 12 meses no conteúdo público de terceiros. Hoje a única limpeza (`cleanup_old_transcripts_if_needed`) apaga por tamanho da BD (acima de 70 % de 500 MB), não por idade | FALTA-CONSTRUIR | ABERTO | AMBOS | Média | SQL versionado (Claude) + agendamento e execução em produção (DEV); prazos da P-41 | `docs/governance/PRIVACY-POLICY.md` §7; definição da função lida no Supabase (2026-10-07, só leitura); AIMS §5.3 | — | VERIFICADO |
| GOV-PRIV-1 | O repo público `agent-network-mcp` versiona `transcripts/latest.json`, com a transcrição de um vídeo público de terceiros (título, autor, descrição, fala). Remover do git e pôr no `.gitignore`; decidir se se reescreve o histórico | FALTA-CONSTRUIR | ABERTO | AMBOS | Média | PR no MCP (Claude); reescrever o histórico é decisão do DEV (força push no `main` do MCP) | `git ls-files transcripts` no ANM (2026-10-07); política de privacidade §2; AIMS §5.2 e §11 | — | VERIFICADO |
| S-005 | Tabela `_prisma_migrations` no esquema `public` do Supabase sem RLS (as restantes 23 tabelas têm). Não tem dados pessoais, mas fica legível pela API se as permissões do `anon` o permitirem | FALTA-CONSTRUIR | ABERTO | DEV | Baixa | SQL versionado (activar RLS sem políticas, ou mover para outro esquema); o DEV aplica | SELECT ao `pg_class` (2026-10-07, só leitura): `relrowsecurity = false` só nesta tabela | — | VERIFICADO |


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
| "RAG fechado (C8, 6/6): 110 chunks de 33 ficheiros" (`:27`) | O C8 estava "fechado só no papel" (→ J3). Hoje: tabela canónica `knowledge_chunks`, MANIFEST com 39 fontes (46 com o F3c, P-35 = A), F0 fechado com o M1 a 2026-10-05 (o F0.6 ficou BLOQUEADO; o F0.12 é opcional); o n.º de linhas está por confirmar (F0.1b; esperado 163) | `scripts/ingest_delta.py` (`MANIFEST`: 39); corrida #169 do `ingest-knowledge` (`unchanged=39`); A5:190 |
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
| CLAUDE | 13 | F1b, F2, W-010, W-003, R-005, EX-B7, AU-22b, F3c-DESIGN-1, F2-SEC-1, F3-ART-1, ING-008, ING-009, R-007 |
| DEV | 69 | F0.6, F0.12, F3b-VAL-1, S20, S27, S19, S21, S28, S32, A12, A13, A19, A22, EX-C3, EX-C4, AU-25, T-003, W-001, W-004, M-005, L4-1b, L4-4, Q-001, E-001, M7, G6, E15, G1.2, G1.3, G1.4, G1.5, G1.6, G1.7, G1.8, G1.9, G1.10, G1.11, G1.12, G1.13, G1.14, G2.2, G2.3, G2.4, G3.1, G3.2, G3.3, G4.1, G4.2, H1, H2, H3, H4, I1, I2, I3, I4, I5, I6, I7, I9, I10, I11, T-004, T-005, S-003, H-004, ING-010, ING-011, S-005 |
| AMBOS | 41 | F3, F6, F3-MCP-1, F3b-GS-1, F3b-AUTH-1, R-001, AU-44, SEC-3, B2b, B2c, A9, B16, B1-bis-C, T-001, T-002, AU-20, M-001, M-002, M-003, M-004, L4-2, L4-3, Q-002, E-002, AU-36, INIT-093, AU-12, H-01, G1.1, G2.1, S-004, F4-MAT-1, F5-ROUTE-1, E-004, R-008, R-009, R-010, SKILL-EXT-1, GOV-42001-1, GOV-RET-1, GOV-PRIV-1 |

**Só do DEV, sem código** (refeito na revisão de 2026-10-07; a lista anterior citava merges e SELECTs já feitos):
- **merge** do PR do branch `docs/privacy-policy` (política de privacidade, avaliação de impacto, separação repo público/privado; fecha o GOV-IMPACT-1);
- **P-41** (prazos de retenção) e o e-mail de contacto de privacidade (`config/deployment.yaml → privacy_contact`; obrigatório num repo privado);
- **decisões:** P-37 (AU-20), P-38 (maturidade), P-11, P-16, P-17, P-19, P-20 e as propostas P-21, P-22, P-24, P-25;
- **F3b-VAL-1:** os 2 sidecars com as datas reais (`legal/direito-br-pt.md`, `imobiliario/fipezap.md`);
- **F3b-AUTH-1,** quando quiseres desbloquear: o SQL da v3 e a flag no MCP (o código é do Claude);
- **runs com credenciais:** F3b-GS-1 (golden set de marketing), F5-ROUTE-1 (run a partir do `route`), as 5 queries do R-001;
- **F0.6 / S-003:** uma forma de expor o MCP ao conector do Claude.ai (hoje sem tools);
- **F0.12** (opcional, irreversível): apagar a t6 com backup; já provado que está toda na canónica;
- **operação:** S20 (bridge-worker com 401; prazo proposto 2026-10-12), S27, S19, S28 (1 run do `transcribe.yml`), H-004 (`graphify update .`), L4-1b, W-001, T-004 (preços);
- **vitrine no GitHub** (só na UI): Topics, Description e Website do `agent-network-mcp` (`https://agent-network-mcp-oddn.vercel.app`).

## 6. Resumo por severidade

| Sev | N.º | IDs |
|---|---:|---|
| Crítica | 1 | G1.5 |
| Alta | 14 | R-005, F3, S20, AU-20, G1.1, G1.3, G1.4, G1.7, G1.11, G1.14, G2.1, G2.2, G2.3, G2.4 |
| Média | 50 | F0.6, F2, F6, F3-MCP-1, F3b-GS-1, F3b-VAL-1, F3b-AUTH-1, AU-44, S27, S19, S32, B2b, B2c, A9, A13, A22, EX-C3, EX-C4, B1-bis-C, W-001, W-004, EX-B7, M-001, M-002, M-005, L4-1b, L4-3, Q-001, Q-002, E-001, E-002, AU-36, M7, INIT-093, AU-12, H-01, G1.2, G1.8, G1.9, G4.1, G4.2, T-004, S-004, F3-ART-1, F4-MAT-1, ING-009, R-010, GOV-42001-1, GOV-RET-1, GOV-PRIV-1 |
| Baixa | 58 | F0.12, F1b, F3c-DESIGN-1, F2-SEC-1, W-010, R-001, S21, S28, SEC-3, A12, A19, B16, AU-25, T-001, T-002, T-003, W-003, AU-22b, M-003, M-004, L4-2, L4-4, G6, E15, G1.6, G1.10, G1.12, G1.13, G3.1, G3.2, G3.3, H1, H2, H3, H4, I1, I2, I3, I4, I5, I6, I7, I9, I10, I11, T-005, S-003, H-004, F5-ROUTE-1, E-004, ING-008, ING-010, ING-011, R-007, R-008, R-009, SKILL-EXT-1, S-005 |

**Por estado:** ABERTO 70 · EM CURSO 6 · BLOQUEADO 47.
**NÃO VERIFICADO (4):** S20, S27, A22, T-003.

## 7. Histórico (116 linhas: 95 FECHADO, 21 OBSOLETO)

Mais recente primeiro. Uma linha pode agrupar IDs fechados pelo mesmo PR ou decisão (separados por `/`). Às 4 colunas pedidas acrescentam-se 2 (`Estado final` e `Nota`).


| ID | Título | Fechado em | PR / evidência | Estado final | Nota |
|---|---|---|---|---|---|
| GOV-IMPACT-1 | Avaliação de impacto (ISO/IEC 42001 6.1.4, 8.4, A.5.2–A.5.5) e política de privacidade (LGPD + GDPR) | 2026-10-07 | PR do branch `docs/privacy-policy`: `docs/governance/PRIVACY-POLICY.md`, AIMS §5 e §11, `config/deployment.yaml`, `runner/tests/test_privacy_separation.py` | FECHADO | Fecha com o merge deste PR. Estado medido: 0 dados de clientes; conteúdo público de terceiros coberto. Seguimento: GOV-RET-1, GOV-PRIV-1, S-005, P-41 |
| SEC-1.3 | `activate_for_task` antes do worker + allow-list de scripts por skill (deny-by-default), sha256 e `pins:`, pesquisa externa opt-in | 2026-10-07 | #123 (merged 2026-10-07 10:31 UTC, `7cda6f1`); CI da `main` verde (11 checks) | FECHADO | Pré-requisito do AU-20, que continua ABERTO (P-37). SKILL-EXT-1 (SkillsCat) fica no §4 |
| W-011 / R-006 / H-002 | Validação do `MCP_URL` e do bypass; `provenance_v2_ok` no `l5_eval`; avisos do ruff em `scripts/` | 2026-10-07 | #122 (merged 2026-10-07 10:26 UTC, `4e38801`); CI da `main` verde | FECHADO | Mesmo PR da revisão do estado contra o EXECUTION-PLAN e do F3c-DESIGN-1 opção A |
| F4-DOC | Domain Onboarding Cost do F4 (E §15.9: "medido no F4") | 2026-10-07 | Medido a partir do diff do #114 (`git diff --stat 8c22d18 e66d1b1`): **DOC(core) = 1 ficheiro** (`runner/plan_runner/capabilities.py`, +41 linhas: a regra de maturidade que o próprio E §7 F4 pede); infraestrutura, runtime, persistência e orquestração novas = 0. O pack acrescentou 1 capability file (18 capabilities) e 32 testes | FECHADO | A alteração ao core foi a do plano (F4 item 5), não uma necessidade do domínio. Reuse Ratio fica para o F6 canónico, que o exige |
| F6-CADEIA | F6 da cadeia F1 → F6: hardening, evidence pack e WHAT-I-CONTRIBUTED | 2026-10-06 | #121 (merged 2026-10-06 21:24 UTC, `f7e7551`); CI verde (11 checks) | FECHADO | P-23 = A: o F6 canónico (domínio de prova, D-EP8) continua no §4 |
| F3b-VALIDADE | F3b, validade das fontes (P-27 = C, P-28 = C, P-29 = A) | 2026-10-06 | #120 (merged 21:23 UTC, `17d0b6a`); CI da `main` verde nesse merge, com `test-rag` e `test-ingest` | FECHADO | Sem SQL novo. Datas de 2 fontes: F3b-VAL-1 (DEV). Autoridade e conflitos: F3b-AUTH-1 |
| F3c | Cobertura de `docs/knowledge/`: 7 de marketing no MANIFEST, 25 no `EXCLUDED` com razão, teste de cobertura | 2026-10-06 | #119 (merged 21:22 UTC, `dc23bb5`). Produção (SELECT só de leitura, 2026-10-07): 7 fontes, 15 chunks, todos com `locator`, `status` active | FECHADO | P-35 = A, P-36 = A. Design: F3c-DESIGN-1 (opção A, `repo_files`, 2026-10-07). A razão do `EXCLUDED` do design foi corrigida (V42) |
| F3a | F3, 1.ª parte: proveniência no retrieve (SQL aditivo, `match_knowledge_v2`, writer com proveniência, MCP atrás da flag `KNOWLEDGE_RPC_V2`) | 2026-10-06 | NAS #113 (merged 2026-10-06, `8c22d18`; o SQL chegou antes à `main` no `2a9203a`) e MCP #19 (merged 2026-10-05). Produção: SQL aplicado (SELECTs ao catálogo do Supabase: `match_knowledge_v2`, colunas novas, `locator`, `knowledge_sources_status_check`); `l5_eval` com a flag igual ao F0.7b (sem regressão); **prova da v2:** `tools/call` do `retrieve_knowledge` em produção (`kb=security`, `top_k=1`): o hit traz `citation.uri` = `docs/knowledge/security-agents-stack.md` e `metadata` preenchido (`document_type` = `md`, `status` = `active`, `content_hash`). Na v1, o `metadata` é `null` e o `citation` não tem `uri`; e mesmo no fallback para a v1 com a flag ligada, `status` e `document_type` viriam `null`, porque só a `match_knowledge_v2` os devolve. O `locator` vem `null`, como esperado nas linhas antigas (preenche-se na re-ingestão) | FECHADO | P-26 = A. O F3 continua vivo no §4 com o F3b (validade e conflitos, autoridade, golden set alargado) e o F3c (33 ficheiros fora do MANIFEST). O R-006 continua aberto: o `l5_eval` ainda não mede a proveniência da v2 |
| F5 | Validação E2E de uma capability com run real | 2026-10-06 | Run real do DEV (`run_9017d441d1`, plano `example-security-audit-demo`, `--mode external --worker gemini`); `python scripts/f5_evidence.py pilots/f5-run-v3` → **PASSOU** nos 5 critérios: estado `done` (triage, audit, hitl_security_decision, report); L5 no passo audit com `kb=security` e 5 hits, fonte `docs/knowledge/security-agents-stack.md`; 3 chamadas a `gemini-3.5-flash-lite`, tokens 13670 / 2944 / 16614; 4 artefactos (`01-triage.json`, `02-audit.md`, `03-security-report.md`, `04-hitl.json`); 0 `worker_error` e 0 `knowledge_context_failed`. Código e runbook no #115 (merged 2026-10-06, `0b7405a`); evidência em `docs/ops/F5-E2E-RUN.md` §4 | FECHADO | 3.º run. O 1.º falhou pelo `MCP_URL` com `/api/mcp` (erro do runbook, V41) e o 2.º por um `VERCEL_PROTECTION_BYPASS` com 1 carácter; novo W-011. O run não usou conselhos: a prova do C-2 por um run real continua por fazer. O custo em dinheiro não foi medido (preços `null`, T-004) |
| F4 | `config/marketing-capabilities.yaml` validado no E7 + maturidade de capability | 2026-10-06 | #114 (merged 2026-10-06, `e66d1b1`): 18 capabilities (15 `implemented`, 1 `partial`, 2 `planned`), validadas no E7; maturidade medida em `runner/plan_runner/capabilities.py` (`implemented` exige um plano do runner com a action); `runner/tests/test_capabilities.py` (32) | FECHADO | Fechado pela regra do §9 (passo 5: depois do merge, no PR seguinte). O que falta fica marcado no próprio YAML: `transcript_analysis` em `partial` e `visual_identity` e `performance_analysis` em `planned` |
| F1 / ING-2 | Ingestão universal: ADR + spike MarkItDown → T6 | 2026-10-05 | PRs #105 (T6a), #106 (T6b), #107 (T6c), #108 (T6d), #109 (T6e), #110 (T6f), todos com merge (o último a 2026-10-05 19:09 UTC, `main` `f217f02`); CI verde, incluindo o job `test-ingest` | FECHADO | 3 formatos (PDF, DOCX, XLSX) com fixtures reprodutíveis; processo filho com timeout e `RLIMIT_DATA` medido; E2E pelo T6 provado contra Postgres + pgvector; S5 em `scripts/ingest_benchmark.py`. A 1.ª ingestão real em produção espera pela entrada no MANIFEST (DEV). Detalhe em `docs/initiatives/PENDENCIAS_T6.md` |
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


## 8. Contradições resolvidas (42)

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
| V41 | F5 *(nova; erro meu, no #115)* | `docs/ops/F5-E2E-RUN.md` §2: `$env:MCP_URL = "https://agent-network-mcp-oddn.vercel.app/api/mcp"` | O `MCP_URL` é só a base. O runner acrescenta sempre `/api/mcp` (`runner/plan_runner/mcp_knowledge.py:59` e `:119-121`), como já dizia o `docs/ops/L5-F0-REVALIDATION.md:241`. Corrigido no runbook | 1.º run do F5 do DEV (2026-10-06) falhou por isto; `runner/tests/test_mcp_knowledge.py:269-275` |
| V42 | F3c-DESIGN-1 *(nova; erro meu, no #119)* | `scripts/ingest_delta.py` (`EXCLUDE_DESIGN`) e `RAG-CANONICAL.md` § F3c: "as skills de design lêem o ficheiro" | Com o worker Gemini (modo external) as skills não lêem nada: o worker não executa tools (AU-20) e os passos de design não tinham `repo_files`. Só era verdade com um worker humano ou o Claude Code. Corrigido: `repo_files:` nos 4 passos de design (opção A) e a razão reescrita | `runner/plan_runner/external_worker.py:231-235` (pedido sem tools); `runner/tests/test_plan_repo_files.py` |


## 9. Como fechar um item

1. **Identificar:** o ID está no §4. Se o trabalho não tem ID, criar o item primeiro (§0, ponto 4).
2. **Implementar** num branch próprio; a mensagem de commit e o PR citam o ID (ex.: `F0.4:`).
3. **Testar:** o teste ou a verificação que prova o fecho fica no repo (ex.: `runner/tests/...`), ou fica descrito (query, run real) com o resultado.
4. **Citar no PR:** "Fecha `<ID>`".
5. **Depois do merge** (nunca antes): no mesmo PR, ou no seguinte, mover a linha do §4 para o §7, com a data e o PR, e actualizar as contagens (§5, §6 e o cabeçalho).
6. **Se o fecho revelar que um documento antigo estava errado:** acrescentar um V*n* no §8.
7. **Se o item deixar de fazer sentido:** propor OBSOLETO em A/B/C (§10). Só com a decisão do maestro passa para o §7.

## 10. Decisões (A/B/C, com recomendada)

**Decididas pelo maestro: P-1 a P-10, P-12 a P-15 (2026-10-03), P-18 = C (2026-10-04) e P-26 = A (2026-10-06); P-27 a P-36 (F3b e F3c, 2026-10-06); P-23 = A (2026-10-06, opção B confirmada); P-40 (ISO/IEC 42001: âmbito, papéis e cadência, 2026-10-07).** **Pendentes:** P-11, P-16, P-17, P-19 (limiar do F0.7b), P-20 (causa do R-005), P-21 (F1b), P-22 (upstream MarkItDown), P-24 (`scrape.yml`), P-25 (allowlist por área), P-37 (AU-20: executor de tools), P-38 (escala de maturidade), P-39 (D-EP5: ordem da Fase 2) e P-41 (prazos de retenção da política de privacidade). Nenhuma decisão pendente foi assumida.


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
| P-21 | F1b: Docling perante o S5 do F1 (`scripts/ingest_benchmark.py`, fixtures sintéticas: listas e tabelas 100% nos 3 formatos; o PDF perde os headings, e o `chunk_markdown`, que corta por H2/H3, não divide um PDF por secções) | **Não necessário por agora:** o F1b fica BLOQUEADO até haver documentos reais do domínio com perda medida (regra do prompt da cadeia F1–F6: só com benchmark que mostre perda material); nada se instala | **Benchmark real:** o DEV entrega 3 a 5 PDFs reais e não sensíveis do domínio; o Claude corre o `ingest_benchmark.py` sobre eles e compara o MarkItDown com o Docling (`docling-core>=2.48.4`) só nesses | Docling já como adapter do PDF (mais pesado; sem evidência em documentos reais) | **A** (proposta, 2026-10-05): é o que a regra do prompt manda sem benchmark real; passa a **B** quando houver PDFs reais do domínio para ingerir. **Pendente** (confirmação) |
| P-22 | Contribuição upstream no `microsoft/markitdown` (o prompt da cadeia F1–F6 pedia, no T6b, um PR contra o upstream; esta sessão não tem acesso a esse repo, e é uma acção pública na conta do DEV) | Não contribuir: as fixtures, os testes e os achados ficam na plataforma | **Issue primeiro:** o DEV abre, na conta dele, uma issue com os 2 achados reproduzíveis (com os conversores por omissão, um PDF ilegível volta em bruto pelo conversor de texto; uma tabela DOCX sem `w:tblHeader` sai com um cabeçalho vazio), com os geradores das fixtures; o PR só depois da resposta dos maintainers e com o CLA da Microsoft assinado | PR directo com a fixture e o teste | **B** (proposta, 2026-10-05): valida o interesse antes do trabalho, e os achados são concretos e reproduzíveis. **Pendente** |
| P-23 | F6: o F6 do prompt da cadeia ("hardening final + portfolio package") é diferente do F6 deste documento ("UM domínio de prova, com o Domain Onboarding Cost medido; depois do F5", D-EP8) | **Os 2:** o do prompt fica como etapa final da cadeia no `PENDENCIAS_T6.md` (sem ID novo no §4); o F6 canónico mantém-se como está | Substituir o F6 canónico pelo do prompt (reabre a D-EP8) | Fundir: o pacote de portfólio passa a ser parte do "done" do F6 canónico | **Decidida: A** (maestro, 2026-10-06, opção B confirmada). **2 itens distintos:** o **F6-CADEIA** (hardening + evidence pack + WHAT-I-CONTRIBUTED; fecha no merge do #121) e o **F6 canónico** (domínio de prova, D-EP8; continua BLOQUEADO). A autoridade e os conflitos do F3b (F3b-AUTH-1) não são pré-condição do F6-CADEIA |
| P-24 | F2: o destino do `ANM:.github/workflows/scrape.yml` (lê a página inteira, sem allowlist nem robots, e grava directamente na tabela `scrapes` do Supabase, por fora do T6) | **Manter como legado:** como o `ingest.yml` na D-EP9 = A; o que vai para o L5 passa pelo `scripts/web_fetch.py` e pelo T6 | Migrar o `scrape.yml` para chamar o `web_fetch.py` (allowlist, robots, tectos) e continuar a gravar em `scrapes` | Desactivar o `scrape.yml` | **A** (proposta, 2026-10-06): não mexe em produção e não corta nada; o `scrape.yml` só corre à mão (`workflow_dispatch`) com a URL dada pelo DEV. Rever para B se passar a ser usado com URLs que não são do DEV. **Pendente** |
| P-25 | F2: allowlist por área (ADR §3, item 4: "`fetch`: PREPARE, com allowlist por área") | `config/web-allowlist.yaml` por área do `config/areas.yaml`, com os domínios escolhidos pelo maestro e validados no E7 | **Só `--allow` por chamada**, como no F2a (a allowlist é explícita em cada uso e fica no registo do comando) | Uma allowlist global única | **B** (proposta, 2026-10-06) até ao 1.º uso real de research por uma área; nessa altura, A com os domínios dessa área. **Pendente** |
| P-26 | F3: como levar a proveniência ao retrieve (`docs/architecture/adr/ADR-F3-PROVENANCE-RETRIEVE.md`). Hoje o `match_knowledge` devolve só `id, content, source, similarity`, e o MCP chama-o (`ANM:lib/knowledge.js:68`) | **Aditiva, em 2 PRs:** colunas novas, RPC nova `match_knowledge_v2` com filtros e proveniência, o `ingest_apply` lê o `.meta.yaml`, SQL em `scripts/migrations/` corrido pelo DEV; depois, o MCP passa para a v2. O `match_knowledge` antigo fica intacto. Âmbito: F3a (critério do prompt), F3b (validade e conflitos, autoridade, golden set) e F3c (33 ficheiros fora do MANIFEST) | Mudar a assinatura do `match_knowledge` existente (o MCP parte entre o SQL e o deploy) | Proveniência só no runner, lida do `.meta.yaml` no git (o MCP fica sem ela, e os filtros continuam sem efeito) | **A** (**decidida pelo maestro, 2026-10-06**): nada parte em produção durante a transição, e o F3 canónico fica inteiro, por fases |
| P-27 | F3b, validade: que documentos têm data de expiração | Todos com `effective_until` | Nenhum: válidos até serem substituídos (`superseded`/`revoked` à mão) | **Híbrido por classe:** data obrigatória só em legal ou regulamentar, dados de mercado e páginas web do F2; config `config/knowledge-validity.yaml`; o ingest recusa com `INVALID_META` uma fonte de classe datada sem data | **Decidida: C** (maestro, 2026-10-06): os playbooks não caducam; evita datas inventadas |
| P-28 | F3b, validade: quem define a data | O autor, no sidecar `.meta.yaml` | O ingest, por TTL de classe (`retrieved_at` + N dias) | **O autor no sidecar para legal e mercado; TTL automático só para a web do F2 (90 dias desde o `retrieved_at`)** | **Decidida: C** (maestro, 2026-10-06): a data de uma lei vem da lei; a de uma página buscada não existe |
| P-29 | F3b, validade: o que acontece aos expirados | **Ficam na BD e são filtrados por omissão** (a v2 já o faz); consultáveis com `status: any` ou `valid_at`; script local de relatório (expirados e a expirar em 30 dias) | Apagados ao expirar (job que escreve em produção) | Ficam, mas descem no ranking | **Decidida: A** (maestro, 2026-10-06): histórico preservado; sem workflow pago |
| P-30 | F3b, âmbito: as linhas do MCP (`project` NULL) | **O F3b cobre só o T6; a limitação fica escrita e cria-se um item** | Estender ao MCP pelo `ingestDocument` | Migrar o conhecimento do MCP para o T6 | **Decidida: A** (maestro, 2026-10-06): não tocar no conector agora. Cria o **F3-MCP-1** (§4) |
| P-31 | F3b, conflitos: quando 2 fontes divergem | A mais recente | A de maior autoridade | C: as duas, e o LLM decide sem sinal. **D: supersessão explícita (`status: superseded` + `superseded_by` no sidecar) + as duas devolvidas com autoridade e data, com uma regra no prompt do worker** | **Decidida: D** (maestro, 2026-10-06): sem detecção semântica automática (cara e pouco fiável) |
| P-32 | F3b, autoridade: níveis e atribuição | Sem níveis | **3 níveis (`oficial`, `curado`, `experimental`) por regras de path no config, com override no sidecar; as 39 fontes actuais ficam `curado`; `match_knowledge_v3` aditiva (SQL do DEV + flag no MCP), mesmo padrão do F3a** | Pontuação numérica de 0 a 100 (D: allowlist por domínio, por cima da B) | **Decidida: B** (maestro, 2026-10-06): sem regressão nem breaking change |
| P-33 | F3b, autoridade: o retrieve filtra? | Filtra por omissão (exclui `experimental`) | **Devolve tudo, com a autoridade no `metadata`, e um filtro opcional `min_authority`** | Reordenar por semelhança × peso | **Decidida: B** (maestro, 2026-10-06): os planos legais ou de security podem exigir `oficial` |
| P-34 | F3b: golden set alargado | **Marketing (~20 casos) + casos sintéticos de validade e conflito no CI + R-006** | Só os sintéticos | Adiar | **Decidida: A** (maestro, 2026-10-06). Se a quota de embeddings apertar, os sintéticos correm primeiro e o de marketing fica no **F3b-GS-1** (§4) |
| P-35 | F3c: destino dos 32 `.md` de `docs/knowledge/` fora do MANIFEST | **Migrar os 7 de `marketing/`; `EXCLUDED` com razão para os outros 25; teste de cobertura** | Migrar os 32 (~120 chunks duplicados do MCP) | Não migrar nenhum e só documentar | **Decidida: A** (maestro, 2026-10-06). Nenhum ficheiro é apagado do git |
| P-36 | F3c: o pack `design/` | **Excluir até haver consumidor de `kb: design`** (D-EP2, pack a pack) | Migrar já com `agent_id: design` (só ajuda o conector, BLOQUEADO no F0.6) | — | **Decidida: A** (maestro, 2026-10-06). Cria o **F3c-DESIGN-1** (§4) |
| P-37 | AU-20: como o worker passa a executar tools (`read_repo_file`, `retrieve_knowledge`) | Portar o ToolExecutor TypeScript (`packages/mcp/src/tools/ToolExecutor.ts`, 82 linhas: registo, autorização, rate limit, auditoria) e chamá-lo do Python | **Executor mínimo em Python dentro do `plan_runner`**, que reaproveita o desenho do TS (allowlist por passo, auditoria com hash dos parâmetros) e o que já existe em Python (`repo_files.py`, `McpKnowledge`); `functionDeclarations` do Gemini; tecto de iterações e de tokens; eventos e ledger por chamada | Não fazer: manter `repo_files:` e blocos `knowledge:` (deterministas) | **B** (proposta, 2026-10-07): um só runtime (D1, "só o plan_runner é execution runtime"), sem ponte Node; as 2 tools já têm implementação Python testada. Contrato §15.4 (os 10 itens) proposto em `docs/architecture/AU-20-TOOL-EXECUTOR.md`, com base em pydantic-ai (`UsageLimits`, deferred tools), OpenAI Agents SDK (tool guardrails, `needs_approval`) e no desenho do `ToolExecutor.ts`. **Pendente** |
| P-38 | F4-MAT-1: escala de maturidade das capabilities | Adoptar a do E §15.7 nos YAML (`maturity: DECLARED…PROVEN`) a par do `status` | **Derivar a maturidade** a partir de evidência (skill/agent → DECLARED/WIRED; plano → EXECUTABLE; teste com Gemini falso → VALIDATED; run real registado → PROVEN), sem campo novo nos YAML; o `status` actual continua | Manter só o `status` e corrigir o E §15.7 | **B** (proposta, 2026-10-07): a maturidade é medida, não declarada (regra do F4), e o `defensive_audit` passa a PROVEN pelo run do F5. **Pendente** |
| P-39 | D-EP5: ordem 2a/2b da Fase 2 dos meta-agentes (Execution Broker vs Execution Lease). O plano diz "decidir só depois do F5", e o F5 fechou a 2026-10-06 | 2a primeiro: o Execution Broker (M-001) | 2b primeiro: a Execution Lease (M-002) | **Adiar a escolha até a Fase 2 estar desbloqueada:** a implementação continua presa ao F0–F6 canónico + C-2, e decidir sem uso real seria especulativo | **C** (proposta, 2026-10-07): a ordem decide-se com os dados do primeiro caso real. **Pendente** |
| P-40 | ISO/IEC 42001 (gestão de IA): âmbito, papéis e cadência do AIMS | Âmbito só NAS | **Âmbito NAS + ANM** (a memória de clientes está no ANM); papéis maestro (gestão de topo, aceita risco Alto, merge) / DEV (operação e produção) / Claude (desenvolvimento, propostas, nunca decide); auditoria interna trimestral e revisão da política semestral | Não adoptar referencial | **B — decidida pelo maestro (2026-10-07).** Alinhamento voluntário, não certificação. Política em `docs/governance/AI-MANAGEMENT-SYSTEM.md`; mapeamento em `docs/governance/ISO-42001-MAPPING.md`; itens GOV-42001-1 e GOV-IMPACT-1 |
| P-41 | Prazos de retenção que a P-40 não fixou (política de privacidade §7) | **`token_usage` 24 meses; conteúdo público de terceiros (`transcripts`, `image_posts`, `scrapes`) 12 meses ou até oposição** | `token_usage` 12 meses; conteúdo público 6 meses | Sem prazo (só limpeza por tamanho, como hoje) | **A** (proposta, 2026-10-07): 24 meses cobrem 2 ciclos de auditoria semestral de custos; 12 meses chegam para o estudo de conteúdo e minimizam o que se guarda de terceiros. Os dados de clientes já têm prazo dado pelo maestro (contrato + 90 dias). **Pendente**; a política já usa A até à decisão |


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
| ING-2 (= "E2" conector, O:20) | F1 | fechado (§7) |
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

