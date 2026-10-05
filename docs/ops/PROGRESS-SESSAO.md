# Progresso da sessão — 2026-10-03

> Regra de persistência (maestro, 2026-10-03): este ficheiro é actualizado a cada item fechado ou PR aberto, para que o trabalho sobreviva a uma perda de contexto.
> O estado oficial dos pendentes continua a ser `docs/initiatives/PENDENCIAS.md`; este ficheiro é o diário da sessão.
> Horas em UTC, tiradas dos commits (`git log`).

## Estado actual
- **Branch actual:** `docs/f0-selects` (só documentação).
- **`main` de referência:** NAS `81e6364` (merges até #94); MCP `4916872` (merges #15, #16 e #17).
- **Itens em trabalho:** F0.1 (falta a contagem `projecto` e a F0.1b com o filtro `project`); H-01 (partes 1, 2 e 3).

### Fila activa (no máximo 5; o resto do PENDENCIAS é inventário)
1. **DEV — F0.1 + R-002 + R-005:** contagem `projecto`, F0.1b com o filtro `project` (esperado 163) e `kb` das linhas com `project` NULL. São só SELECTs (§5 do PENDENCIAS).
2. **DEV — F0.6:** pergunta real no conector MCP; a resposta tem de citar a fonte (`[Fonte: …]`).
3. **DEV — F0.7b:** `python -m plan_runner.l5_eval run` contra o MCP real (hit@k, MRR, proveniência).
4. **CLAUDE — AU-22:** 2.ª metade da P-10 (retirar o `on_fail` e o `max_replans` dos planos e do schema, com testes).
5. **DEV — S20:** bridge-worker da VM Oracle com 401. Corrigir ou adiar com data.

**Gate:** o código do F1 (spike MarkItDown) só arranca com 1, 2 e 3 feitos (D-EP4, P-13). Até lá não se abrem domínios nem meta-agentes novos.

## Log (mais recente no topo)

### Análise externa do projecto: confronto com o estado real (2026-10-05)
O maestro colou uma análise e um plano em fases (A–F). Confrontei-os com o PENDENCIAS na `main` `81e6364`. Várias acções já estavam feitas:
- **P-10 e P-12 a P-15:** decididas = A a 2026-10-03 (§10). A P-10 já tem o `done_when` implementado (#90); falta a 2.ª metade (AU-22).
- **C-2:** feito. A DB foi alterada pelo DEV a 2026-10-03 e o MCP #16 entrou no mesmo dia. **A linha estava desactualizada (erro meu de fecho)** e passou a FECHADO neste PR. Falta só a prova por um run real de conselho, que entra no F5.
- **README e quickstart:** feitos (#93). O README já não fala no C8 nem no core TS como estado actual; o quickstart (stub → HITL → `done`) foi testado.
- **F0.3:** fechado (t6 parada a 2026-09-29).

**Válido e adoptado:**
- fila activa de no máximo 5 itens (acima);
- gate do F1 em F0.1, F0.6 e F0.7b;
- não abrir domínios nem meta-agentes;
- as 3 métricas: F0 verde, custo de onboarding de um domínio ≈ 0 e tempo até valor < 30 min.

**Contagens:** 112 → **111** vivos (ABERTO 62, EM CURSO 7, BLOQUEADO 42); histórico 94 → 95 (74 FECHADO).

### 4 SELECTs F0 corridos (maestro, 2026-10-05)
**Resultados (colados pelo maestro):**
1. **Contagem por fonte (top 20; apresentada como F0.1b):**
   - `docs/knowledge/13_ai_findability.md`: 22
   - `docs/knowledge/security/security-agents-stack.md`: 20
   - ECC planner+architect+code-architect-network+doc_updater+docs-lookup: 13
   - `docs/knowledge/06_INGEST_PIPELINE.md`: 12
   - `docs/knowledge/orquestrador_playbook.md`: 11
   - `docs/knowledge/skills_visibility.md`: 11
   - `docs/knowledge/agoo_agent.md`: 9
   - `docs/knowledge/13_findability.md`: 9
   - ECC security-reviewer + database-reviewer: 8
   - (restantes abaixo)
2. **`ultima_t6`:** `total_t6` = 110; `ultima` = 2026-09-29 10:06:33+00. A t6 está congelada.
3. **Fonte ECC "security-reviewer + database-reviewer":** `agent_id` = revisor-codigo, `project` NULL, `kb` = marketing. O `kb` está errado.
4. **Linhas compostas** (`agent_id LIKE '%+%'`): 0.

**O que fecha e o que não fecha** (o F0 não fecha todo):
- **F0.3 → FECHADO.** A t6 parou a 2026-09-29, antes do limite de 2026-09-30, e tem 110 linhas (igual ao C8). Desbloqueia o F0.12.
- **R-003 → FECHADO.** A fonte ECC não é `global`, por isso não entra em todas as pesquisas.
- **R-005 (novo):** reclassificar o `kb` (e o `agent_id`) da fonte ECC. BUG, CLAUDE, Média, BLOQUEADO pelo F3 (provenance formal).
  - Causa provável: `kb text DEFAULT 'marketing'` em `scripts/rag_schema.sql:51`, e o insert do MCP não define o `kb`.
  - Se for isso, todas as linhas com `project` NULL têm `kb` = marketing. Há um SELECT só de leitura para o confirmar.
  - Não muda a pesquisa: o `match_knowledge` filtra só por `agent_id` (`scripts/rag_schema.sql:68`).
- **F0.2:** já estava FECHADO (2026-10-03, resultado "NÃO está"). Acrescentei à nota que agora está: 20 chunks, entrados pelo F0.4 (#64).
  - O caminho foi reportado com `security/`. No repo e no MANIFEST é `docs/knowledge/security-agents-stack.md` (não existe a pasta `docs/knowledge/security/`). Pode ser gralha na cópia ou outra fonte: confirmar na F0.1b filtrada.
  - As fontes `13_ai_findability.md`, `06_INGEST_PIPELINE.md`, `orquestrador_playbook.md`, `skills_visibility.md`, `agoo_agent.md` e `13_findability.md` não existem no repo com esses nomes (são nomes antigos). A F0.1b filtrada diz de que `project` são.
- **"P4":** não há item com este ID no PENDENCIAS. O resultado (0 compostos) é a verificação do F0.1 e confirma o AU-50, já fechado; ficou registado nos dois.
- **F0.1 continua EM CURSO.** A contagem por fonte recebida é da tabela inteira: inclui a fonte ECC, que tem `project` NULL. Não é a F0.1b de `docs/ops/L5-F0-REVALIDATION.md` §3, que filtra `project = 'network-agents-setup'`. Faltam a contagem `projecto` e a F0.1b filtrada, que também fecham o R-002 (esperado: 163).
- **Ainda abertos no F0:** F0.1, F0.6 (teste no conector), F0.7b (golden set) e F0.12 (apagar a t6).

**Contagens:**
- antes: 113 vivos (ABERTO 63, EM CURSO 9, BLOQUEADO 41);
- depois: **112** (ABERTO 62, EM CURSO 8, BLOQUEADO 42);
- histórico: 92 → 94 (73 FECHADO, 21 OBSOLETO).

### H-01 actualizado depois dos merges #91 e #93 (2026-10-05)
- **#91 e #93 mergeados; `main` em `92cc762`.**
- **Ingest #176** (`92cc762`): `chunks=0 deleted=0 unchanged=39`. Nada foi escrito em produção. A #175 (`b11591b`, merge do #91) foi cancelada porque a #176 a substituiu.
- **H-01 actualizado: partes 1–3 pendentes** (limpeza, arquivo dos históricos, índices):
  - o bloqueio deixa de ser o "merge do PR #93";
  - as partes 4, 5 e 6 passam para a evidência, com o #93 e a `main` `92cc762`.
  - O H-01 fica EM CURSO, com o dono AMBOS.
- **Contagens:** sem alteração. Recalculadas a partir da tabela §4: 113 vivos (ABERTO 63, EM CURSO 9, BLOQUEADO 41). §5 e §6 batem com a §4 e não há sobreposição §4/§7.
- **Description e Topics do repo:** a sessão não os pode escrever. O proxy responde 403 tanto ao `PATCH /repos` como ao `PUT /topics`, embora a conta tenha admin. Ficam para o maestro, no GitHub ou com `gh repo edit` local.

### PR #93 sem merge possível: conflito resolvido (2026-10-05)
- **Causa:** o #90 e o #93 mudavam as mesmas 2 linhas de contagens do `PENDENCIAS.md` (cabeçalho e "Por estado"). Era o conflito previsto; mais nada colidia.
- **Correcção:** merge da `main` `a52fc74` na branch do #93 (merge commit, sem rebase nem `--force`). As contagens foram recalculadas a partir da tabela §4 fundida, e não escolhidas de um dos lados.
- **Fecho dos merges #88, #89, #90 e #92 (providência 2):**
  - E-003 → FECHADO no §7 (#90, `test_engenharia_ship_gate.py`, 3 testes);
  - AU-22 → ABERTO sem bloqueio: o `done_when` entrou no #90, mas a remoção do `on_fail` e do `max_replans` (2.ª metade da P-10) continua por fazer;
  - H-003 continua ABERTO: o #89 é uma mitigação (Codecov com `continue-on-error`), e o re-pin das actions Node 20 continua por fazer.
- **Contagens:** 113 vivos (ABERTO 63, EM CURSO 9, BLOQUEADO 41); 92 no histórico (71 FECHADO, 21 OBSOLETO). §5 e §6 batem com a §4, e não há IDs repetidos nem sobreposição §4/§7.
- **README** (a somar ao que já estava no #93):
  - linhas "Completion criteria" (`done_when.py`) e "Skill usage" (`skill_ref`) nas Capabilities;
  - `.claude/skills/` (gerado) no mapa do repositório;
  - números actualizados: 590+ testes (562 + 34 lentos) e 70+ PRs merged (70 contados pela API);
  - 57 links relativos verificados, 0 partidos.
- **Ingest pós-merge:** corrida #174 (`388d86b`) com `chunks=0 deleted=0 unchanged=39`; a #173 foi cancelada pela concorrência. Os ficheiros deste PR não estão no `scripts/ingest_delta.py`.
- **Testes na branch fundida:**
  - `pytest -q`: 562 passed;
  - `pytest -q -m slow`: 34 passed;
  - `ruff` limpo; E7 válido; `sync_claude_skills.py --check` sem drift.

### Decisões confirmadas (consulta cruzada com uma 2.ª IA)
- **Registo:** P-10, P-12, P-13, P-14 e P-15 = **A** (maestro, 2026-10-03). INIT-094, ING-5 e ING-6 → **OBSOLETO** no §7 (não FECHADO). Contagens: **112 vivos** (ABERTO 62, EM CURSO 8, BLOQUEADO 42), **91 no histórico** (70 FECHADO, 21 OBSOLETO).
  - O prompt previa 110 vivos, mas partia de 113; o #86 já tinha acrescentado o S-004 e o H-005 (115 − 3 = 112).
- **Nota da P-10:** as `description` do `done_when`, do `on_fail` e do `max_replans` no `runner/plan_runner/plan.schema.json` dizem agora "a remover; fora até ao F3, por decisão, não por esquecimento" (o `done_when`, "vai ser verificado no fim do run"). O AU-22 fica ABERTO, sem bloqueio, até haver código e testes.
- **Condição da P-18:** verificada, e **não apliquei A**. O `ship-parallel.plan.yaml` é um exemplo do motor:
  - criado com o engine LangGraph (`5cd7c27`) como "Template fan-out";
  - "Generic plan" em `plug-in-agents.md:178`;
  - fixture de `conftest.py:36` e `test_real_plans.py:116`;
  - a pasta `marketing/` foi por conveniência.

  Volta ao maestro em A/B/C. O E-003 continua BLOQUEADO.
- **Acrescentado:**
  - o ADR do F1 passa a "Aceite" (P-13);
  - as 2 análises (#80, #82) levam a decisão no topo;
  - o §11 tem os 3 aliases a apontar para o §7;
  - validação nova: todos os aliases do §11 apontam para a secção certa (0 inconsistências).
- **Verificado antes:** merges MCP #15 → #16 → #17 e NAS #86. Vercel `success` e 0 erros de runtime desde as 22:55 UTC; ingest #171 com `chunks=0`; `npm test` 19/19 na `main` do MCP.
- **Testes:** runner 539 passed; `ruff` limpo; E7 válido; todos os `*.plan.yaml` validados contra o schema.

### Auto-auditoria ("executou tudo com padrão ouro?")
- **Erro meu, apanhado e corrigido:** o R-004 (MCP #15) desloca 3 linhas no `lib/knowledge.js`, e o `ANM:docs/ops/TOKEN-LEDGER.md` cita `:175` e `:231`.
  - A 1.ª correcção, igual nos PRs #15 e #16, dava **conflito** entre eles. Vi-o na simulação local dos merges, antes de qualquer push.
  - Correcção final: só no #16 (commit `5e5aa25`), a citar as funções (`ingestDocument`, `retrieveContextDetailed`, `retrieveKnowledgeHits`) em vez das linhas.
  - Simulei os merges de #15, #16 e #17 por 3 ordens diferentes: sem conflitos.
  - Ordem recomendada: #17 → #16 → #15.
- **Achado novo, H-005:** o `docs/STATUS.md` do MCP diz que o GitHub Actions está "desligado", mas o `heartbeat` e o `audit-tools` correm por `schedule` (última corrida a 2026-10-01, `success`). Registado, sem correcção (seria mais um redeploy; juntar a outro PR do MCP).
- **`pnpm audit` do NAS (workspace TS):** 0 vulnerabilidades. Registado no A22. As dependências Python e os alertas do Dependabot continuam NÃO VERIFICADOS.
- **Ainda em falta do lado do maestro:** os factos 2 e 3 do adendo do C-2 (só chegou o 1.º) e o fim do prompt principal (cortado na Prioridade 4).

### Verificação pedida pelo maestro: README vs estado real, e inconsistências do meu trabalho
- **README da raiz:** confirmadas as inconsistências da análise. Mais uma que ela não tinha: "50 chunks RAG" no `ai-findability.md`, quando o chunker actual dá 9. Os 10 factos, com evidência, estão no `PENDENCIAS.md` §4.1, no H-01; pela decisão do maestro, o H-01 cobre o README (A). Só corrigi já o ponteiro dos pendentes (`README.md:36`); o resto fica para o PR do H-01.
- **Erro meu (V40):** o H-001 (#70) foi dado como FECHADO, mas deixou 4 ponteiros para o `STATUS.md` como fonte de pendentes: `README.md:36`, `BOOTSTRAP.md:75` (que contradizia a `:27` do mesmo ficheiro), `SECURITY.md:31` e `docs/STATUS.md:3`. Corrigidos neste PR. O `check-consistency.ts` só exige frases no `docs/STATUS.md`, e a alteração só acrescenta texto.
- **S-004** (novo; o S-003 já existia, é o teste do connector):
  - `npm audit` no MCP deu `next` 16.3.5 com vulnerabilidade **crítica** (GHSA-vcvr-r3jv-pc5j, RCE no `next/og`; o código não o usa) e `ip-address` moderada;
  - PR MCP #17: `next` 16.3.8 e `ip-address` 10.7.3, refeito com npm 11 para o lockfile mudar só versões (a 1.ª tentativa, com npm 10, apagava os campos `libc`);
  - `npm audit` = 0; `npm test` 16/16; `next build` OK.
- **Não verificado:** `pnpm audit` do TS arquivado (`packages/`) e a aba Security dos 2 repos (403 para esta sessão; A22 no NAS).

### Relatório da sessão "continuação operacional"
- **Feito (com evidência):**
  - **R-004** (MCP #15): `.is("project", null)` no delete do `ingestDocument`. Novo `tests/ingestDocument.test.mjs`, 3 testes; o 1.º falhava antes da correcção. `npm test` 19/19; `next build` OK.
  - **C-2, lado repo** (MCP #16): o CHECK em `memory/token_usage.sql` passa a ter os 7 valores, os mesmos da produção. O lado DB já tinha sido feito pelo DEV (adendo do maestro). Validado num Postgres 16 local: ficheiro 2× sem erro; constraint `token_usage_call_kind_check` com 7 valores; valor inválido recusado.
  - **Registo (NAS, este PR):**
    - `PENDENCIAS.md`:
      - R-004 e C-2 passam a EM CURSO;
      - E-003 → decisão nova P-18;
      - H-002 → BLOQUEADO pelo F3 (P-7 = A);
      - H-003 com o inventário completo das actions em Node 20;
      - F0.6 e F0.7b deixam de esperar pelo F0.4, que fechou no #64; o F0.7b passa a ABERTO;
      - nota de que a recomendação do maestro para P-10 e P-12–P-15 é A, ainda pendente de confirmação.
    - `docs/ops/COUNCIL.md`: o ALTER do conselho deixa de estar "por correr".
  - **Testes do runner:** suite rápida 539 passed, 1 skipped (`mem0` não instalado), com o Postgres RAG local; `ruff` limpo; E7 (`python -m plan_runner.areas`) válido.
- **Não feito, e porquê:**
  - **E-003:** não é mecânico. `research`/`critic` resolvem sempre para agentes de marketing (`skills.py:28-39`), e mudar as actions mexe numa fixture dos testes. Fica na decisão P-18.
  - **H-003:** para pinar SHA novos é preciso ler as tags dos repos `actions/*`, fora do âmbito da sessão. Não toquei em workflows.
  - **H-002** (F3), **EX-B7** (depois do F5), **AU-22** (P-10): fora desta sessão, pelas decisões e pelo plano.
  - **P-10 e P-12–P-15:** não marquei FECHADO; falta a confirmação do maestro.

### Merges #80, #82, #83 e #84 (verificação, só leitura)
- **Ordem dos merges:** #82 → #80 → #83 → #84. Ficheiros independentes, só docs; a ordem não muda nada.
- **`ingest-knowledge`:**
  - #166, #167 e #168 foram canceladas pelo próprio workflow: `concurrency` com `cancel-in-progress: true` (`.github/workflows/ingest-knowledge.yml:14-16`);
  - a #169 (`b74ea42`) correu sobre a `main` final: `chunks=0 deleted=0 unchanged=39`, `success`. Nada escrito em produção (os 4 ficheiros não estão na lista do ingest).
- **Antes destes, verificado também:** NAS #79/#81 (ingest #164/#165 com `chunks=0`; CI da `d79d7be` verde) e MCP #13 → #14 → #12 → #11 (Vercel `d635945` a `success`; 0 erros de runtime desde as 21:45 UTC; nenhum workflow do MCP disparado).
- **CI da `main` `b74ea42`:** os 7 checks a `success` (`test`, `delta`, gitleaks, semgrep e CodeQL nas 3 linguagens).
- **PENDENCIAS:** INIT-094, ING-5 e ING-6 deixam de esperar pelo merge; só falta a decisão (P-12, P-14, P-15).

### Auto-auditoria (pedido do maestro: "nada ficou mal feito ou deixou de ser feito?")
- **Mal feito, corrigido no #83 (`869673f`):**
  - o §10 só marcava P-1, P-2, P-6 e P-9 como decididas; faltavam P-3 (B), P-4 (B), P-5 (A), P-7 (A) e P-8 (A);
  - o P-9 mostrava a recomendação B (renomear), não a decisão do maestro (manter `H-01`); o `H-01` não foi tocado;
  - o PENDENCIAS ainda tinha como EM CURSO itens cujos PRs já tiveram merge: W-005 (#79), S17 (MCP #11), AU-06 (MCP #13), S-001/S-002 (MCP #14). Passaram ao §7; o §11 e as contagens foram recalculados (113 vivos; 88 no histórico).
- **Deixado por fazer, agora registado:**
  - **H-004:** `graphify update .` (o `CLAUDE.md` pede-o depois de mudanças de código; a ferramenta não existe nesta sessão; local, do DEV);
  - **S-003:** testar o Claude.ai connector depois dos tectos de input do S-001 (o `CLAUDE.md` do MCP pede-o; precisa do conector real).
- **Verificado em leitura:** deploy do MCP `d635945` no Vercel a `success`; corridas #164 e #165 do `ingest-knowledge` a `success`; nenhuma corrida do `transcribe.yml` depois do merge do MCP #12 (o S28 continua à espera de 1 run).
- **Por fazer (CLAUDE, viáveis, não iniciados):** R-004, E-003 e H-003.

### 21:07 — CI consolidado (D-EP10, verificação única)
- **Feito:** lidos os check runs dos 10 PRs abertos, uma vez e sem polling.
- **Evidência:**
  - **NAS #79:** os 10 checks a `success`: `test`, `test-rag`, `test-slow`, gitleaks, semgrep e CodeQL nas 3 linguagens;
  - **NAS #80–#84:** os 7 checks a `success` em cada um (`test`, gitleaks, semgrep, CodeQL);
  - **MCP #11–#14:** `Vercel` (status) e `Vercel Preview Comments` a `success` em cada um. O repo MCP não tem CI de testes (`npm test` 16/16 e `next build` OK correram localmente no #14).
- **Próximo:** merges do maestro.

### 20:51 — PROTOCOLO
- **Feito:** criado este ficheiro (regra de persistência).
- **Evidência:** este PR.
- **Próximo:** verificação de CI às 21:07; actualizar este ficheiro a cada evento.

### 20:50 — PENDENCIAS (2.ª ronda)
- **Feito:**
  - 18 itens fechados com PR e/ou teste;
  - estados actualizados;
  - novos R-004, E-003, H-003, T-004 e T-005;
  - V35–V39 no §8 e P-10..P-17 no §10.
- **Evidência:**
  - PR #83 (`35088cd`): 116 vivos (ABERTO 62, EM CURSO 13, BLOQUEADO 41); 84 no histórico;
  - validação por script: colunas, IDs únicos, §5/§6 recalculados.
- **Próximo:** merge do maestro.

### 20:47 — ING-5 / ING-6
- **Feito:** análise para decisão (gitingest e ScrapeGraphAI). Recomendada A nos 2: não adoptar.
- **Evidência:** PR #82 (`ba65826`); reverificado o gitingest 0.3.1 (31/07/2025) com a #605 aberta; o ScrapeGraphAI exige LLM.
- **Próximo:** decisões §10 P-14 e P-15.

### 20:46 — F1 (ADR)
- **Feito:** ADR *Universal Ingestion & Research Primitives* (Proposto) + plano do spike S1–S5 (não executado).
- **Evidência:** PR #81 (`49d6bd5`).
- **Próximo:** decisão §10 P-13; o spike só com o F0 verde.

### 20:44 — S-001 / S-002 (MCP)
- **Feito:** `.max()` em todas as strings das 9 tools MCP. O S-002 foi verificado sem código: a saída já tem limite.
- **Evidência:** PR MCP #14 (`38889a4`); `npm test` 16/16; `next build` OK.
- **Próximo:** decisão §10 P-16 (valores).

### 20:42 — INIT-094
- **Feito:** reavaliação dos 6 harnesses (os 6 existem; licenças e descrições corrigidas). Recomendada A: não adoptar.
- **Evidência:** PR #80 (`359cb3e`).
- **Próximo:** decisão §10 P-12.

### 20:40 — W-005
- **Feito:** worker inline no engine langgraph; merge da `main` no branch, com o conflito do AU-22 resolvido mantendo os 2 lados.
- **Evidência:** PR #79 (`157b039`); suite 539 passed e 34 lentos passed.
- **Próximo:** merge.

### 20:30 — W-002
- **Feito:** clarificação com estado (`route --clarify-from`).
- **Evidência:** PR #78 (**merge feito**); 8 testes.

### 20:25 — R-001
- **Feito:** investigação da `knowledge_log` (0 leitores e escritores nos 2 repos) + 5 queries só de leitura, validadas num Postgres local.
- **Evidência:** PR #77 (**merge feito**).
- **Próximo:** o DEV corre as queries.

### 20:24 — AU-11
- **Feito:** `scripts/rag_schema.sql` canónico e idempotente; o teste RAG passa a carregá-lo.
- **Evidência:** PR #76 (**merge feito**).

### ~20:20 — Leitura de produção (só logs públicos)
- **Feito:** lidos os logs do `ingest-knowledge`.
- **Evidência:**
  - corrida #156: `security-agents-stack.md chunks=20`, `unchanged=33`;
  - corrida #163: `unchanged=39`, `0/50` de orçamento.
- **Próximo:** SELECT F0.1b (esperado: 163 linhas) para fechar o R-002.

### 19:40 — W-006
- **Feito:** schema JSON dos planos do runner + CLI de validação.
- **Evidência:** PR #75 (**merge feito**); 25 testes.

### 19:36 — AU-22 (parte)
- **Feito:** `max_steps` no langgraph + evento `plan_fields_ignored`.
- **Evidência:** PR #74 (**merge feito**); 6 testes.
- **Próximo:** decisão §10 P-10.

### 19:31 — D5
- **Feito:** o worker lê o `model_tier` (`config/model-tiers.yaml`, tudo a `null`).
- **Evidência:** PR #73 (**merge feito**); 7 testes.
- **Próximo:** T-005 (opcional).

### 19:28 — D6
- **Feito:** `budget.max_cost_usd` (falha fechada sem preço).
- **Evidência:** PR #72 (**merge feito**); 12 testes.
- **Próximo:** T-004 (preços, DEV).

### 19:22 — AU-32
- **Feito:** `vertical: design` no design-flow + guarda.
- **Evidência:** PR #71 (**merge feito**).

### 19:20 — AU-06, S28, S17 (MCP)
- **Feito:**
  - AU-06: `ingest.yml` marcado como legado;
  - S28: removida a cache do apt (causa confirmada no log do run #108);
  - S17: o doc da VM passa a Oracle.
- **Evidência:** PRs MCP #13 (`20d3d41`), #12 (`14faa89`) e #11 (`aea4593`).
- **Próximo:** merge; no S28, 1 run limpo do DEV.

### 19:17 — H-001
- **Feito:** o bootstrap aponta para o PENDENCIAS; papel do STATUS.
- **Evidência:** PR #70 (**merge feito**).

### 19:16 — AU-37
- **Feito:** errata no `CORE-MAPPING.md`.
- **Evidência:** PR #69 (**merge feito**).

### 19:15 — AU-10
- **Feito:** `skills/claude/PROVENANCE.md` gerado pelo sync.
- **Evidência:** PR #68 (**merge feito**).

### 19:13 — AU-08
- **Feito:** `.env.example` com as 41 variáveis lidas pelo código.
- **Evidência:** PR #67 (**merge feito**).

### ~19:05 — P1 (F0.5, F0.7a, F0.8, F0.9)
- **Feito:** verificação no branch do #63.
- **Evidência:**
  - 454 passed com o Postgres RAG local;
  - `l5_eval validate`: 18 casos, 0 erros;
  - citações conferidas;
  - merge limpo #63 → #64 → #65 → #66.
- **Resultado:** os 4 itens fecharam com o merge do #63.

## PRs / branches abertos por mim

| PR | Branch | Item | Estado |
|---|---|---|---|
| NAS (este) | `docs/decisoes-p10-p18` | Decisões P-10, P-12–P-15; OBSOLETO de INIT-094/ING-5/ING-6; condição da P-18 | Aberto. Merge = `ingest-knowledge` (deve dar `chunks=0`) |

Já com merge: NAS #63–#86; MCP #10–#17.

## Checklist para o DEV (comandos prontos a colar; não executados pelo Claude)

**Supabase → `agent-network-memory` → SQL Editor. São só `SELECT`s:**

```sql
-- F0.1 / F0.1b (fecha o R-002): esperado 163 linhas do projecto
SELECT count(*) AS projecto FROM knowledge_chunks WHERE project = 'network-agents-setup';
SELECT count(*) AS compostos FROM knowledge_chunks WHERE agent_id LIKE '%+%';   -- esperado 0
SELECT source, agent_id, count(*) AS chunks, max(updated_at) AS ultima
FROM knowledge_chunks WHERE project = 'network-agents-setup'
GROUP BY source, agent_id ORDER BY source;

-- F0.3: a t6 parou (não deve ser posterior a 2026-09-30)
SELECT max(updated_at) AS ultima_t6 FROM knowledge_chunks_t6;

-- R-004 (MCP #15): só deve haver NULL (MCP) e 'network-agents-setup' (T6)
SELECT project, count(*) AS linhas, count(DISTINCT source) AS fontes
FROM knowledge_chunks GROUP BY project ORDER BY project NULLS FIRST;
```

As 5 queries do R-001 (`knowledge_log`) estão em `docs/ops/KNOWLEDGE-LOG.md` §3.

**PowerShell (máquina local, com `MCP_URL` e `MCP_API_KEY` no ambiente; não colar os valores em lado nenhum):**

```powershell
# F0.7b: golden set security contra o MCP real (com o F0.4 fechado, espera-se chunk_hit@4 > 0)
cd network-agents-setup\runner
python -m plan_runner.l5_eval run --out ..\l5-eval-security.json

# H-004: grafo de código local (os 2 repos)
cd ..\..\network-agents-setup; graphify update .
cd ..\agent-network-mcp;        graphify update .
```

**Manual:**
- **F0.6 / S-003:** no Claude.ai connector, fazer 1 pergunta de security que deva citar a fonte, e 1 chamada normal a uma tool, para confirmar que os limites de tamanho dos inputs (S-001) não a recusam.
- **S28:** GitHub → `agent-network-mcp` → Actions → "Transcrever vídeo/reel" → Run workflow (1 corrida limpa).
- **T-004:** preencher os preços confirmados em `config/model-prices.yaml`.
- **Não tocar sem decisão:** F0.12 (apagar a t6), S20/S27/S19 (Oracle), W-004.

## Próximos 3 passos recomendados
1. **Maestro:** P-18 em A/B/C (ver o relatório desta sessão; recomendada C), e P-11, P-16 e P-17.
2. **Claude:** AU-22, a implementação da P-10 = A: verificar o `done_when` no fim do run e remover o `on_fail` e o `max_replans` do schema e dos 13 planos que os usam, com testes.
3. **DEV:** a checklist acima (F0.1b, F0.3, R-004, F0.7b, F0.6/S-003, S28, T-004).
