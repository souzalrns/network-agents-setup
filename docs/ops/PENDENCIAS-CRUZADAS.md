# Pendências cruzadas: PLANO-DE-ACAO × OPEN-ITEMS × EXECUTION-PLAN

> **Auditoria só de leitura (2026-10-03).** Não alterei nenhum dos 3 documentos; este ficheiro só regista o cruzamento.
> **Base auditada:** `main` `e7a29ae` (pós-#62).
> Os PRs abertos **#63** (F0.5/F0.7a/F0.8/F0.9) e **#64** (F0.4) já corrigem algumas linhas; estão assinalados como "em PR".
>
> **Documentos:**
> - **P** = `docs/audit/PLANO-DE-ACAO.md` (616 linhas);
> - **O** = `docs/initiatives/OPEN-ITEMS.md` (318 linhas);
> - **E** = `docs/architecture/EXECUTION-PLAN.md` (1194 linhas).
>
> **Evidência:** `P:linha`, `O:linha`, `E:linha` nas versões de `main`.

## Resposta curta

**Não estão sincronizados.** Encontrei **26 contradições** (§3) e **9 colisões de IDs** (§4). Nenhum dos três está errado por inteiro. Cada um tem partes congeladas em datas diferentes que nunca foram actualizadas:

| Doc | Natureza real | Partes que **não** são estado actual |
|---|---|---|
| **P** | Auditoria de 30/09 + acrescentos | O §3 ("4 decisões **pendentes**", `P:117`), o §5 (bloqueios por D1–D3, que já foram tomadas), o §9 (índice-mestre, com quase tudo "NÃO INICIADO"), o §11 (contagens de 30/09) e o §15 ("nada implementado", `P:605`). **Contradizem o §10 do próprio P** ("Fecho de 2026-10-01: 11/11", `P:433`) e o §13.1 (decisões tomadas) |
| **O** | Retrato de **20/09** (antes da auditoria e da D1, `O:1`) + registo **cumulativo** de secções datadas | As tabelas 🟢/🟠/🔴 do topo (`O:11-67`) nunca foram regeneradas (é o próprio AU-46). Têm itens fechados ou tornados obsoletos pela D1. O resto do ficheiro é correcto, mas está espalhado por 10 secções |
| **E** | Plano (o que deve acontecer e porquê) | O §9 é um retrato de 03/10 dos pendentes. Pela sua própria regra **não é fonte de estado** (`E:1020`, §15.1) |

## 1. Pendentes extraídos de cada documento

- **P:**
  - §4: J1–J11;
  - §6: top-12;
  - §9: AU-01…AU-50 e as séries S/M/EX/B/D/E/A/G–J;
  - §13.2: decisões E1–E15, J5-b e J5-c.
- **O:**
  - topo de 20/09 (🟢 ~10, 🟠 ~23, 🔴 3);
  - secções datadas: J3, Dependabot, Bloco B (B2–B4, R1–R4), L4 (L4-1b/2/3), Bloco C (C-2), Fase 2 (Broker/Lease/Learning), Security (SEC-1…3), EXECUTION-PLAN (D-EP1..11, F0–F6).
- **E:**
  - §9.1 (SEC);
  - §9.2 (pendentes operacionais, `E:778`);
  - §9.3 (Fase 2);
  - §9.4 (F0–F6);
  - §9.5 (D-EP, `E:824`).

## 2. Tabela cruzada

Legenda:
- ✅ fechado
- 🔴 aberto
- ⚪ não menciona
- ⚠ diz algo errado ou desactualizado
- "Real" = o que o repo ou os registos mais recentes provam

### 2.1 Itens que pelo menos um documento dá como abertos e estão fechados ou obsoletos

| # | Item | P | O | E | Real (evidência) | Conflito? |
|---|---|---|---|---|---|---|
| 1 | **AU-19 / J3** RAG canónico | ⚠ §9 NÃO INICIADO (`P:304`); §4 FEITO, "falta apagar a t6" (`P:140`) | ✅ código + migração; 🔴 passos 3/5/6 (`O:111`) | 🔴 F0.3, F0.6, F0.12 | Reparado (PR #31). Abertos: passos 3/5 (F0.3 parcial: escrita activa às 14:25) e 6 | **Sim**: o P contradiz-se e esquece os passos 3/5 |
| 2 | **AU-47 / J1** keep-alive | ⚠ §9 NÃO INICIADO (`P:332`); §4 FEITO | ✅ (`O:104`) | ⚪ | Fechado (run #6 verde) | **Sim** (interno ao P) |
| 3 | **AU-05 / J7** `tests/package.json` | ⚠ §9 "MORTO" (`P:290`); §4 FEITO | ✅ (PR #30) | ⚪ | Fechado | **Sim** (rótulo) |
| 4 | **AU-16 / AU-49** tokens e orçamento | ⚠ §9 NÃO INICIADO (`P:301,334`); §6 #4 "EM PR" (`P:198`); §10 ✅ | ✅ B5 Feito (#42) | 🟡 ledger Supabase sem `council_*` (C-2) | Fechado; a C-2 continua aberta | **Sim** (P §9/§6 contra §10) |
| 5 | **AU-23** worker `external` | ⚠ §9 "EM PR" (`P:308`); §5 "bloqueado D1" (`P:164`) | ✅ merged #40 | ✅ operacional | Fechado | **Sim** |
| 6 | **AU-26/30/33/34** áreas e router | ⚠ §9 NÃO INICIADO (`P:311,318`); §6 #7 "EM PR" (`P:201`) | ⚠ "Feito (…, **sem merge**)" (`O:157`) | ✅ | Fechado (#41, J5, E7) | **Sim**, em P e em O |
| 7 | **AU-09** testes lentos no CI | ⚠ §9 NÃO INICIADO (`P:294`); §6 #10 COMPLETO | ✅ #43 | ⚪ | Fechado | **Sim** (interno ao P) |
| 8 | **S29** memória L4 | ⚠ §9 NÃO INICIADO (`P:341`); §6 #9 FEITO | ✅ #47 + L4-1; 🔴 L4-1b | 🔴 L4-1b | Fechado; L4-1b aberto | **Sim** (interno ao P) |
| 9 | **J4** `description:` nos agentes | ⚠ §4 sem estado (`P:142`) | ✅ "descrições J4" no fecho do Bloco A | ⚪ | Fechado: 38/38 `.agent.md` têm `description:` (verificado) | **Sim** |
| 10 | **J5** registo de áreas | ⚠ §4 sem estado (`P:143`); §10 ✅ | ✅ | ✅ | Fechado | **Sim** (interno ao P) |
| 11 | **J10** gate de segurança no CI | ⚠ §4 sem estado (`P:148`) | ✅ SEC-2; ⚠ ainda com a linha "SEC-2 (DEV): J10…" (`O:259`) | ✅ §9.1 | Fechado (#59–#61) | **Sim** |
| 12 | **B2b/B2c (=A10/A11)** ferramentas e triagem de segurança | ⚠ "EM CURSO" (`P:355`) | 🔴 A10/A11 no topo (`O:38-39`); ✅ SEC-2/2d | 🟡 supply chain `partial` (OSV) | Gitleaks, semgrep e triagem feitos; **OSV/Trivy por fazer** | **Parcial** |
| 13 | **AU-50** `agent_id` composto | ⚠ NÃO INICIADO (`P:335`) | ⚪ (#63 corrige) | ⚪ | **Resolvido pela migração J3 e pelo writer** (`scripts/migrate_t6_to_knowledge_chunks.sql:37-48`) | **Sim** |
| 14 | **S15a** secret do Actions do `agent-network-mcp` | ✅ "Verificados" (`P:376`) | ⚠ 🟠 **Crítico, aberto** (`O:33`) | ⚪ | Fechado: `STATUS.md:36` "DONE em 2026-09-20" | **Sim** |
| 15 | **M6 / B13** `GeminiProvider` TS | ⚠ NÃO INICIADO (`P:342`) | ⚠ 🟢 aberto (`O:16`) | ✅ Gemini no worker Python | **Obsoleto pela D1** (VIA A) | **Sim** |
| 16 | **C2 / EX-C2** TS vs Python | ⚠ NÃO INICIADO (`P:346`) | ⚠ 🟠 aberto (`O:50`) | ✅ D1 fechada | **Decidido** (D1, `P` §13.1) | **Sim** |
| 17 | **B3/B5/B6 (=EX-B3/M3/M4)** cadeia TS `apps/api`, HITL TS | ⚠ NÃO INICIADO | ⚠ 🟠 abertos (`O:46-48`) | ✅ HITL Python durável | **Obsoleto pela D1** | **Sim** |
| 18 | **S24** cobertura do `MCPServer` TS | ⚠ "EM CURSO" (`P:356`) | ⚠ 🟢 aberto (`O:24`) | ⚪ | **Obsoleto** (TS arquivado) | **Sim** |
| 19 | **A8 (=S11)** auth do `MCPServer` TS | ⚪ | ⚠ 🟠 **Crítico** (`O:36`); "Fechados: A8" é **outro** A8 (`O:102`) | ⚪ | Obsoleto (TS arquivado). Colisão de ID (§4) | **Sim** |
| 20 | **AU-01/02/13–15/17/18/21/38/41–43/48** (TS) | ⚠ NÃO INICIADO / EM CURSO | ⚪ / parcial | ⚪ | Arquivados pela D1 (o próprio P §5 diz "só valem em B/C") | **Sim** (rótulo: deviam estar OBSOLETO) |
| 21 | **D7** dashboards TS | ⚠ NÃO INICIADO | ⚠ 🟢 aberto (`O:19`) | ⚪ (TS arquivado, §1.2) | Obsoleto | **Sim** |
| 22 | Integrar a `claude/audit-completo` na `main` | ⚪ | ⚠ "em aberto" (`O:121`) | ⚪ | Integrado: o conteúdo do A8 (resolução por frontmatter) está em `main` via **#33**; os SHAs originais não, porque o merge não os preservou | **Sim** |
| 23 | **As 4 decisões** D1–D4 | ⚠ §3 "pendentes" (`P:117`); §13.1 "TOMADAS" | ✅ fechadas (30/09) | ✅ | Tomadas | **Sim** (interno ao P) |
| 24 | **Fase 1 meta-agentes** (CouncilSession) | ⚠ §15 "nada implementado" (`P:605`) | ✅ #54 + C-1 | ✅ §8.2 | Implementado | **Sim** |
| 25 | **Security pipeline v1** | ⚪ | ⚠ título "(branch …, sem merge)" (`O:246`) | ✅ #57 | Merged | **Sim** (texto) |
| 26 | **D-EP10/D-EP11** | ⚪ | ⚠ "em aberto" (`O:290`) | ⚠ "em aberto" (`E:843-844`) | **Fechadas (A)** pelo maestro; corrigido no **#63** (em PR) | Temporário |

### 2.2 Itens realmente abertos: o que cada documento diz

| Item | P | O | E | Real / nota | Conflito? |
|---|---|---|---|---|---|
| **C-2** ledger dos conselhos no Supabase | ⚪ | 🔴 (`O:221`) | 🔴 D-EP3 "DEV corre já" (`E:781`) | Aberto | **Lacuna no P** |
| **L4-1b** teste real da L4 | 🔴 §6 #9, §10 | 🔴 (`O:196`) | 🔴 (`E:783`) | Aberto | Não |
| **R1** `router eval` real | 🔴 §10 ressalvas | 🔴 (`O:163`) | 🔴 (`E:784`) | Aberto | Não |
| **R2–R4** router (agentes legal/gamedev/docs, clarificação com estado, pesos) | ⚪ | 🔴 | ⚪ | Aberto | **Só no O** |
| **B2 / B3 / B4** do worker (ledger central, tools, langgraph inline) | ⚪ | 🔴 (`O:149-151`) | ⚪ | Aberto | **Só no O** |
| **L4-2 (=J11)** spike mem0 | 🔴 J11 | 🔴 (`O:197`) | 🔴 (`E:789`) | Aberto | Não |
| **L4-3** MCP de produção → L4 (ADR-M7, ≈ E5) | 🟡 E5 em §13.2 | 🔴 (`O:198`) | 🔴 | Aberto | Não (IDs diferentes para o mesmo) |
| **S20 (=J2)** bridge Oracle com erro 401 | 🔴 (`P:347`) | 🔴 (`O:32`) | 🔴 (`E:794`) | Aberto | Não |
| **S19 / S27** Oracle | 🔴 (`P:360`) | 🔴 S19 "24 GB" (`O:65`) | 🔴 "12 GB por confirmar" (`E:795`) | Aberto | **Sim** nos números (24 contra 12 GB) |
| **AU-22** campos de plano mortos | 🔴 "bloqueado D1" (`P:307`, motivo caducado) | 🟡 só a linha do E | 🔴 resolver no F0.5/F3 (`E:791`) | Aberto | Motivo de bloqueio errado no P |
| **AU-44** reels → RAG | 🔴 (`P:329`) | 🟡 só a linha do E | 🔴 candidato do F1 (`E:792`) | Aberto | Não |
| **B7 / EX-B7** langgraph/edit no MCP | 🔴 (`P:351`) | 🔴 (`O:15`) | 🔴 depois do F5 (`E:793`) | Aberto | Não |
| **E1–E7 → ING-1..7** conectores de ingestão | 🔴 "E1–E7" (`P:352`) | 🔴 "E1-E7" (`O:20`) | 🔴 F1/F2, renomeados ING-1..7 (D-EP6) | Aberto | **Nome** (§4) |
| **E8 / B11** script versionado de `knowledge_sources` | 🔴 (`P:366`) | 🔴 (`O:21`) | ⚪ | Aberto: a DDL só existe em teste (`runner/tests/test_rag_canonical.py`) | **Lacuna no E** |
| **E9 / B12** `knowledge_log` | 🔴 | 🔴 | ⚪ | Aberto | Lacuna no E |
| **D5** `model_tier` | 🔴 | 🔴 | ⚪ | Aberto | Lacuna no E |
| **D6** `max_cost_usd` | 🔴 (`P:349`) | 🔴 (`O:18`) | 🟡 "falta `cost`" (§8.5) | Aberto | Não |
| **A9** lockfile Python | 🔴 (`P:353`) | 🔴 (`O:37`) | ⚪ | Aberto; é supply chain | **Lacuna no E** |
| **A13** RBAC | 🔴 (`P:354`) | 🔴 (`O:41`) | 🟡 Identity = gap | Aberto | Não |
| **A22** alertas do Dependabot | ⚪ | 🔴 9 alertas (`O:44`) | 🟡 "0 PRs abertos" (`E:800`) | Os alertas estão por confirmar (PRs ≠ alertas) | A confirmar |
| **S12** `.strict()` nos Zod do MCP | ⚪ | 🔴 | ⚪ | Aberto (repo `agent-network-mcp`) | Só no O |
| **F7 / S32** PMO | 🔴 | 🔴 | ⚪ | Aberto (organizacional) | Não |
| **C3 / C4** AgentMesh / Cedar | 🔴 | 🔴 | 🟡 Identity = gap; "não adoptar monólito" | Aberto / em reavaliação | Não |
| **D3 / D4** DeepEval / Ragas | 🔴 (`P:362`) | 🔴 (`O:63`) | 🔴 bloqueado por S19 (§15.12) | Aberto | **Nome**: "D3" também é a decisão da memória |
| **J8** higiene de docs (AU-45, AU-46, AU-37, AU-12, AU-08) | 🔴 | ⚪ | ⚪ | Aberto. **Esta auditoria é a prova do AU-45/46** | Só no P |
| **J6** 1.ª linha real do `token_usage` | ⚪ | 🔴 (`O:118`) | ⚪ | Por confirmar | Só no O |
| **`log_execution`** (4 campos, PR no `agent-network-mcp`) | ⚪ | 🔴 (`O:120`) | ⚪ | Por confirmar | Só no O |
| **B1-bis-C** encurtar o prompt-base | 🔴 "não agora" (§6 #12) | 🔴 "não agora" | 🔴 depois de F0–F3 | Aberto, adiado | Não |
| **Pack Claude, estado da L4 no C-1, medir o conselho security** | ⚪ | 🟡 | 🔴 (§9.2) | Abertos | Só no E |
| **C-3** não escalar `hitl: required` para o conselho | ⚪ | ⚪ | 🔴 (§9.2) | Regra | Só no E |
| **Fase 2** Broker / Lease / Learning | 🟡 §15 (visão) | 🔴 registo | 🔴 §9.3, depois de F0–F6 + C-2 | Aberto (não implementar) | Não |
| **F0–F6** | ⚪ | 🔴 (`O:299…`; #63/#64 actualizam) | 🔴 §9.4 | F0.5/7a/8/9 feitos no **#63**; F0.4 no **#64** | Temporário |
| **E1 (§13.2)** onde corre o motor (Q2) | 🔴 recomendada B | ⚪ | ⚪ | Aberto (prazo de 7 dias) | Só no P |
| **G1–G4 / H / I / B3–B4 (nichos)** | 🔴 backlog | 🔴 bloco | 🟡 substituído pelas matrizes P1/P2 e "um vertical com uso real" | Backlog | **Critério diferente** |

## 3. Contradições, por gravidade

1. **O P contradiz-se a si próprio.** O §3, o §5, o §9, o §11 e o §15 dizem "pendente", "não iniciado" ou "nada implementado". O §10 ("11/11 pernas") e o §13.1 ("decisões TOMADAS") dizem o contrário. Quem lê o §9 (índice-mestre) fica com uma imagem errada de cerca de 20 itens.
2. **O topo do O (20/09) lista como abertos itens fechados ou obsoletos**, alguns como 🔴 **Crítico**: S15a, A8/S11, B13/M6, C2, B3/B5/B6, S24, D7. Quem abre o OPEN-ITEMS vê primeiro o que já não existe.
3. **Itens fechados nos registos mas abertos noutro documento:** AU-23 e o router "EM PR" no P; o router "sem merge" no O; o pipeline de security "sem merge" no O.
4. **O J3 está "FEITO, falta só apagar a t6" no P**, mas os passos 3 e 5 também estão abertos (O, E).
5. **AU-50** continua aberto no P, mas está resolvido desde o J3.
6. **A C-2 não existe no P** e é pré-requisito da Fase 2 (E, ADR §4).
7. **E8/B11, A9, D5 e E9/B12 não existem no E.** Se o E for a única referência, perdem-se.
8. **S19 diz 24 GB, S27 diz 12 GB**, por confirmar na consola.
9. **D-EP10/11** constam como abertos no O e no E (main), mas estão fechados (#63 corrige).
10. **Nichos:** o P e o O mantêm o backlog G1–G4/H/I como plano; o E diz "um vertical, só com uso real". O critério do E (decisão do maestro) prevalece, mas o P e o O não o dizem.

## 4. Colisões de IDs (o AU-45 continua activo)

| ID | Significados diferentes |
|---|---|
| **A8** | auth do `MCPServer` TS (`O:36`, =S11) · resolução de agentes/skills por frontmatter (`O:102`) |
| **B3** | correr `apps/api` real (`O:46`) · tools do worker (`O:150`) · trading (`P` "B3/B4") |
| **B5** | e2e do HITL TS (`O:47`, =M3) · orçamento de tokens (`O:152`) |
| **B6, B7, B1** | séries do EXECUTION-PROMPTS · "B1" do run real do worker · "B7" verificado no P |
| **D3** | decisão da memória L4 · DeepEval (`O:63`, `P:362`) |
| **D4** | decisão da ordem · Ragas |
| **E1–E7** | conectores de ingestão (`O:20`, `P:352`) · decisões E1–E7 (`P` §13.2; **E7 = validador `areas.py`**) |
| **C2/C3/C4** | decisões TS/AgentMesh/Cedar (O) · "C-1/C-2/C-3" do Bloco C (conselho) |
| **L4 / L5** | camadas de memória · lacunas estruturais L1–L10 (`P` §10) |

## 5. Fonte de verdade única: recomendação

| Opção | Como | Vantagem | Custo / risco |
|---|---|---|---|
| **A (recomendada)** | **O = única fonte do estado dos pendentes**, como já dizem o E §15.1 e o `BOOTSTRAP.md`. **Regenerar o topo** com uma só tabela "Pendentes vivos" (ID único, dono, estado, evidência), a partir do §2 deste ficheiro. As secções datadas passam a "Histórico" no fim. **P congelado:** banner "auditoria de 30/09; estado em OPEN-ITEMS"; o §13 (decisões) continua a ser o registo de decisões. **E** fica só com o plano: os §9.x passam a apontar para os IDs do O, sem estado próprio | Uma tabela, um sítio; fecha o AU-46; não apaga histórico (P e as secções datadas ficam) | 1 PR de docs (~1–2 h). O merge dispara o `ingest-knowledge`, mas com o #64 isso já não gasta embeddings em ficheiros iguais |
| B | P = fonte (é a mais estruturada: AU, decisões, prioridades) | Já tem ID, tipo, gravidade e dono | É um documento de auditoria, grande (616 linhas) e mistura análise com estado; o E e o BOOTSTRAP apontam para o O, por isso seria preciso mudar a hierarquia |
| C | Ficheiro novo (ex.: `BACKLOG.md`) gerado dos três | Começa limpo | **Um 4.º documento**: é exactamente o problema (AU-45/46) |

**Regras para não voltar a divergir** (aplicam o E §15.1/§15.11):
1. **Um item só muda de estado no O.** O P e o E citam o ID e não repetem o estado.
2. **IDs únicos:** prefixo por série (ex.: `EP-`, `ING-`, `SEC-`, `L4-`, `F0.x`). Os IDs históricos colididos ficam com alias (`A8≡AUTH-TS`).
3. **No fecho de cada PR**, o item correspondente passa a fechado no O, com o número do PR.
4. Item **obsoleto pela D1** marca-se **OBSOLETO (D1)**, não "aberto" nem "fechado".

## 6. Os pendentes vivos, em resumo (se só leres isto)

- **Teus (maestro/DEV), sem código:**
  - merge do #63 e depois do #64 (escreve em produção);
  - SELECTs em falta (P3);
  - C-2 (SQL no Supabase);
  - S20 (bridge 401);
  - S27/S19 (12 ou 24 GB);
  - L4-1b;
  - R1;
  - J3 passos 5/6;
  - F0.6;
  - F0.7b (precisa de `MCP_URL`/`MCP_API_KEY`);
  - A22 (confirmar alertas);
  - E1 de §13.2 (onde corre o motor).
- **Do Claude Code, por ordem do plano:**
  - depois do F0 verde: F1 (contrato + MarkItDown) → F2 → F3 → F4 → F5 → F6;
  - avulsos sem bloqueio: E8/B11 (DDL de `knowledge_sources`), A9 (lockfile), AU-22, AU-44, B7, R2–R4, J8/AU-45/AU-46 (a opção A acima).
- **Não fazer agora** (decisão do maestro): B1-bis-C, Fase 2 (Broker/Lease/Learning), L4-2, nichos G1–G4.
- **Obsoletos pela D1** (deixar de listar como abertos): S24, A8/S11, B13/M6, C2/EX-C2, B3/B5/B6 do TS, D7, AU-01/02/13–15/17/18/21/38/41–43/48.
