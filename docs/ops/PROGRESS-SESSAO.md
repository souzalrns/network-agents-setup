# Progresso da sessão — 2026-10-03

> Regra de persistência (maestro, 2026-10-03): este ficheiro é actualizado a cada item fechado ou PR aberto, para que o trabalho sobreviva a uma perda de contexto.
> O estado oficial dos pendentes continua a ser `docs/initiatives/PENDENCIAS.md`; este ficheiro é o diário da sessão.
> Horas em UTC, tiradas dos commits (`git log`).

## Estado actual
- **Branch actual:** `docs/progresso-sessao` (este ficheiro). Antes: `docs/pendencias-ronda-2` (`869673f`, PR #83).
- **Último commit de trabalho:** `869673f` (PENDENCIAS, revisão pós-merge).
- **`main` de referência:** NAS `d79d7be` (merges até #79 e #81); MCP `d635945` (merges #11–#14).
- **Itens em trabalho:** nenhum em código. Abertos só PRs de docs: NAS #80, #82, #83 e #84 (merge do maestro).

## Log (mais recente no topo)

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
| NAS #80 | `fix/INIT-094-harnesses` | INIT-094 | Aberto |
| NAS #82 | `fix/ING-5-6-analise` | ING-5, ING-6 | Aberto |
| NAS #83 | `docs/pendencias-ronda-2` | PENDENCIAS (2.ª ronda + revisão pós-merge) | Aberto |
| NAS #84 | `docs/progresso-sessao` | Protocolo de persistência | Aberto |

Já com merge: NAS #63–#79 e #81; MCP #10–#14. Os 4 abertos tocam em `docs/**/*.md`: cada merge dispara o `ingest-knowledge` (escreve em produção; incremental).

## Próximos 3 passos recomendados
1. **DEV, só leitura:** o SELECT F0.1b (esperado: 163 linhas com `project='network-agents-setup'`) e as 5 queries do R-001 (`docs/ops/KNOWLEDGE-LOG.md` §3). Fecham o R-002 e o R-001.
2. **Claude:** R-004, o filtro de `project` no `ingestDocument` do MCP (`ANM:lib/knowledge.js:163-169`), antes que as 2 pipelines colidam.
3. **DEV:** T-004 (preços em `config/model-prices.yaml`), S-003 (teste no connector) e 1 run do `transcribe.yml` (S28).
