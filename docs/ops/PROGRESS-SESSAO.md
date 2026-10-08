# Progresso da sessão — 2026-10-03

> Regra de persistência (maestro, 2026-10-03): este ficheiro é actualizado a cada item fechado ou PR aberto, para que o trabalho sobreviva a uma perda de contexto.
> O estado oficial dos pendentes continua a ser `docs/initiatives/PENDENCIAS.md`; este ficheiro é o diário da sessão.
> Horas em UTC, tiradas dos commits (`git log`).

## Estado actual
- **Branch actual:** `docs/close-scout-and-allowlist-v1` (a partir da `main` `908491a`, merge do #144 com todos os commits).
- **`main` de referência:** NAS `908491a` (merges até #144; #140, #142, #143 e #144 levaram todos os commits); MCP `855057d`.
- **Itens em trabalho** (2026-10-07): **cadeia F1 → F6 fechada** (#119, #120 e #121 com merge). Neste branch:
  - F3c-DESIGN-1 opção A (`repo_files` nos passos de design) e a correcção V42;
  - W-011 e R-006;
  - a revisão do estado contra o EXECUTION-PLAN, com as lacunas novas F3-ART-1, F4-MAT-1 e F5-ROUTE-1.
  ISO/IEC 42001 (P-40): PR do branch `docs/governance-iso42001`; o #122 e o #123 já tiveram merge.
  Decisões pendentes de alto impacto: P-37 (AU-20) e P-38 (maturidade). O F6 canónico (D-EP8) continua BLOQUEADO.

### Fila activa (no máximo 5; o resto do PENDENCIAS é inventário)
1. **CLAUDE — cadeia F1:** T6b (PDF) → T6c (DOCX/XLSX) → T6d (segurança de entrada, com a mitigação 3) → T6e (encaixe no T6) → T6f (fecho). Estado em `PENDENCIAS_T6.md`.
2. **Maestro — P-19:** registar a opção do limiar. O 1.º run real cumpre as 3 opções, por isso a escolha já não muda o veredicto.
3. **DEV — S20:** bridge-worker da VM Oracle com 401. Corrigir ou adiar com data (proposta 2026-10-12).
4. **CLAUDE — R-005, só a causa:** ver as opções A/B/C no relatório de 2026-10-05 (P-20). A reclassificação das 201 linhas espera pelo F3.
5. *(livre)*

Feitos e fora da fila: F0.1 e R-002 (SELECTs da 2.ª ronda); AU-22 (#96); **F0.7b** (run do DEV, 3.ª tentativa); **gate M1**.
Bloqueados por decisão: **F0.6** e **S-003** (o conector do Claude.ai não mostra tools).

**Gate:** M1 fechado a 2026-10-05 (decisão do maestro); o código do F1 está autorizado (D-EP4, P-13). Até lá não se abrem domínios nem meta-agentes novos.

## Log (mais recente no topo)

### Fechos com padrão ouro + allowlist v1 (F2-ALLOW-1) (2026-10-08)
- **Fechados (§7), com a regra do §9 (só depois do merge):**
  - **SKILL-SCOUT-1:** #143, `085d9d5`, 10 commits no `main`, CI 17/17;
  - **SKILL-SCAN-1:** #142, `a0a5efe`, 4 commits, CI 12/12;
  - **AU-20b:** #140, `e0424bf`, 1 commit. O CI do merge tem 3 checks cancelados pelo `cancel-in-progress` (o #141 entrou 39 s depois); o merge seguinte, `37eccca`, contém-no e tem 11/11 verdes.

  Os testes de prova foram re-corridos no `main` `908491a`: tool_executor 48, skill_scan 33, skill-scout 168 + 1 skipped.
- **Contagens:** 125 vivos (EM CURSO 10 → 7); §7 com 125 linhas (104 FECHADO). O SKILL-SCOUT-2 deixa de esperar pelo SKILL-SCOUT-1. O F2-ALLOW-1 passa a CLAUDE: a parte do maestro, os domínios, está dada.
- **Allowlist v1 (maestro):**
  - 122 domínios em 9 áreas, aplicados tal como dados; a `software` fica vazia (deny-by-default);
  - um teste fixa a v1 e apanha uma edição silenciosa;
  - `--area` passa a ser obrigatória no resolver e na CLI (saída 2, sem rede);
  - o modo só com `--allow` e o aviso `no_area_allowlist` saem.
- **Sonda:**
  - `scripts/check_web_allowlist.py`: as regras do `fetch` em cada salto, mais o robots;
  - o workflow `web-allowlist-probe.yml` usa rede real, é informativo e nunca bloqueia;
  - aqui não dá para sondar, porque o proxy da sessão bloqueia os hosts.
- **P-46 (pendente, recomendada A):**
  - 5 domínios aprovados redireccionam para o endereço oficial actual, fora da área: cve.org, developer.hashicorp.com, dev.epicgames.com, docs.astral.sh, docs.claude.com;
  - o `openapi.org` deve ser `openapis.org`;
  - `fazenda.gov.br`, `cvm.gov.br` e `doi.org` ficam, e o porquê está documentado.

### P-44 = A e P-45 = A (2026-10-08)
- **P-45:**
  - `description` nas 20 skills internas sem ela (4 de design, 16 de marketing). Em português, como o corpo, no formato da spec ("o que faz. Usar quando …"), entre 1 e 267 caracteres, validadas com `yaml.safe_load`, nomes iguais;
  - findings de spec no `skills/`: 37 → 19 (ficam 17 `invalid-name` e 2 low);
  - `docs/generated/SKILLS.md` regenerado com o gerador oficial (`generate-skills-doc.ts`).
- **Custo em tokens, verificado:** zero no modo `opt` (o de omissão: o worker tira o frontmatter) e +2,7% no `legacy` (só A/B e rollback). Dois testes novos em `test_context_opt.py`.

  O teste de calibração contra o B1 real falhou (+353 tokens no legacy), porque o B1 correu antes das descrições. Em vez de alargar a margem, a projecção ganhou `drop_skill_keys`, para reproduzir as entradas da época.
- **P-44:** registada, mais uma nota no docstring do `runner/plan_runner/skill_scan.py`.
- **Merge do #143 verificado:** `085d9d5`, com todos os commits até `fa6ee96`.

### SKILL-SCOUT-1: o que faltava para ser a escolha + renome para `skill-scout` (P-43 = A) (2026-10-08)
- **Pergunta do maestro:** "qual escolherias, sem contar reputação nem estrelas?" A resposta honesta foi não o nosso como ferramenta única: faltava o dia-a-dia. Implementado:
  - `list`, e `update` com diff e nova aprovação (`--check` para o CI, pin a commit nunca se move);
  - `uninstall`;
  - `--agent`, com a tabela do skills CLI (79 agentes; uma aprovação para várias pastas);
  - lock com **chave pelo caminho de instalação**;
  - `waive`: uma finding, um conteúdo exacto, motivo, prazo, humano e auditoria; nunca `critical`; só vale com registo numa cadeia íntegra;
  - `find` (skills.sh, `--scan N`) e a validação da spec Agent Skills.
- **Encontrado e corrigido por mim:**
  - o `install` aplicava excepções escritas à mão no lock; agora só as que a auditoria confirma;
  - a limpeza de ANSI deixava `[31m` no texto: corrigida em 4 sítios, 2 deles no `runner/plan_runner`;
  - as regras da spec saíam no SARIF como segurança: passaram a qualidade;
  - a linha comparativa do `skill-guard` (tem `suppress` com motivo).
- **Testes:** 169 (3.10, 3.12 e 3.13; motor Cisco real), 45 mutantes apanhados e 1 equivalente. O runner continua verde.
- **Renome (P-43 = A):**
  - `oss/skill-notary` → `oss/skill-scout`, módulo `skill_scout`, CLI `skill-scout`;
  - ficheiros `skill-scout.lock.json` e `.audit.jsonl`, workflow `skill-scout.yml`;
  - itens SKILL-SCOUT-1..3 (alias no §11), `docs/ops/SKILL-SCOUT.md`.

  Ficam com o nome antigo o branch do PR #143, o histórico do PROGRESS e o caminho da entrada do `.gitleaksignore`.
- **Novas decisões:** P-45 (skills internas e a spec; recomendada A: acrescentar `description`).

### SKILL-NOTARY-1: projecto autónomo `skill-notary`, Fase 1 (2026-10-08)
- **Pesquisa antes de construir:**
  - `skill-guard` está ocupado no PyPI (Apache-2.0, porta de PR para skills): nome de trabalho `skill-notary`, P-43;
  - importados: `agentic-skills-manager` (MIT) como motor por omissão, o scanner da Cisco (Apache-2.0) como 2.º motor opcional (medido: ~8 s, ~650 MB), a lista de detecção de agentes do `@vercel/detect-agent` (Apache-2.0) e a sintaxe `owner/repo@skill` do skills CLI;
  - o hash do `skills-lock.json` do skills CLI depende do locale (`localeCompare`): o nosso é determinístico;
  - o esquema SARIF da OASIS não é MIT/Apache: não é distribuído, os testes descarregam-no num commit fixo com sha256.
- **Código (`oss/skill-notary/`):** `scan`, `install` e `verify`. Pontos-chave:
  - aprovação humana presa ao hash e recusada a agentes de IA;
  - cópia só dos ficheiros aprovados, re-verificados;
  - lockfile e auditoria encadeada;
  - SARIF validado e sem segredos.
- **Pacote:** `pyproject.toml`, wheel e sdist com `twine check --strict`, wheel testada numa venv limpa (Python 3.11).
- **CI:** `.github/workflows/skill-notary.yml` com 4 jobs: testes em 3.10 e 3.13; motor Cisco real; build e smoke da wheel; upload para o code scanning. Validado com actionlint e semgrep.
- **Testes:** 132 testes, 22 mutantes apanhados (os 2 que sobreviveram na 1.ª ronda geraram 2 testes novos). Corrigidos por mim antes do commit:
  - 2 fugas de caminhos absolutos no SARIF;
  - um teste de setuid que não provava nada;
  - o `pipefail` em falta no workflow;
  - a tabela comparativa (o skills CLI mostra classificações remotas; o skill-guard não tem SARIF).
- **Prova real:** `scan anthropics/skills@pdf` (2 motores, RISKY, commit `683bc88`); `install` recusado neste ambiente de agente (exit 4). Doc: `docs/ops/SKILL-NOTARY.md`.
- **CI do PR #143:**
  - 1.º push (`80a9b6d`): 12 de 13 verdes; o gitleaks (histórico completo) apanhou a chave FICTÍCIA de teste, porque o comentário acima dela citava a armadura PEM por extenso e o gitleaks juntou-o ao corpo. Corrigido o comentário; o commit `86d1802` foi para o `.gitleaksignore` com o motivo (sem force-push);
  - 2.º push (`f7e9007`): 13 de 13 verdes;
  - o check `skill-notary` da app `github-advanced-security` confirma que o GitHub code scanning processou o SARIF: "No new alerts in code changed by this pull request"; os 2 medium das skills do repo ficam como alertas do branch.

### SKILL-SCAN-1: scan das skills externas candidatas (2026-10-07)
- **Decisão do maestro:** opção A, `agentic-skills-manager` (scan estático, bloqueia high/critical, modo CI, não executa código).
- **Verificado antes de integrar:** 1.0.4 no PyPI, MIT, só stdlib (um ficheiro, `skills_manager.py`); `skills scan <pasta> --ci` dá um JSON com `safe`, `risk_level` e `findings`, e o exit code 0/1 confere com `safe`. A revisão por IA chama um CLI de agente local (claude, codex, cursor), por isso fica desligada (custo e código não confiável).
- **Código:** `runner/plan_runner/skill_scan.py`, chamado no `activate_for_task` depois da pesquisa externa:
  - clone raso e endurecido do `owner/repo` da candidata (1 por repo), numa pasta temporária apagada no fim;
  - localiza a pasta da skill pelo `name:` da SKILL.md (senão, o repo inteiro);
  - `python -I -m skills_manager scan --ci` com timeout e um ambiente mínimo, sem segredos;
  - veredicto `safe`/`risky`/`dangerous`, ou `not_scanned` (fail-closed) quando não há resultado;
  - rastreabilidade: o commit analisado (lido do `.git`, sem correr o `git`) e o sha256 da SKILL.md; o veredicto vale só para esse conteúdo.
  Nunca instala: `installed` e `trusted` continuam `false`. No prompt vai só o veredicto, sem paths do repo.
- **Testes:** 33 em `test_skill_scan.py`, com skills sintéticas safe, risky e malicious contra o scanner real, mais 1 ajustado em `test_skill_activation.py`. 10 mutantes apanhados. Suite completa verde.
- **CI do 1.º push (`4c79dd8`):** 10 de 11 verdes (o `test` correu os testes contra o scanner real); o `test-slow` falhou na recolha: a exigência "no CI o scanner tem de estar instalado" estava ao nível do módulo, e esse job não instala o `requirements-test.txt`. Passou a ser um teste (`test_no_ci_o_scanner_tem_de_estar_instalado`); reproduzido localmente nos 2 sentidos.
- **ISO 42001:** A.10.3 (fornecedores: skills de terceiros) e A.7.5 (proveniência: commit e sha256) com a evidência nova; o A.10.3 continua Parcial (GOV-42001-1).
- **Prova real (fora dos testes):** clone de `anthropics/skills`: `pdf` e `skill-creator` → `risky`, e um repo inexistente → `not_scanned`, em 2 s; o `pdf` com `commit: 683bc88`.
- **Merges verificados:** o #140 (AU-20b) e o #141 (F2-ALLOW-1) entraram na `main` `37eccca` com todos os commits. O AU-20b fica por fechar no PENDENCIAS quando o maestro confirmar.

### F2-ALLOW-1: allowlist do `fetch` por área (2026-10-07)
- **P-25 = A:**
  - `config/web-allowlist.yaml` com as 10 áreas do `config/areas.yaml`, todas com a lista vazia. Os domínios são do maestro.
  - `runner/plan_runner/web_allowlist.py`:
    - `validate` no E7: áreas existentes; domínios DNS em minúsculas, sem esquema, caminho, porta, `*` nem IP; sem repetidos;
    - `resolve_allowlist`: a área dá a política e o `--allow` só a estreita.
  - `scripts/web_fetch.py --area`: recusa antes de qualquer pedido de rede. Só com `--allow` mantém o F2a e acrescenta o aviso `no_area_allowlist`.
  - O CI do runner passa a correr quando muda o `config/web-allowlist.yaml`.
- **Transição:** o `--area` ainda é opcional, porque com as listas vazias torná-lo obrigatório desligava o `fetch`. Fica obrigatório quando o maestro der os domínios (opções no relatório).
- **Testes:** 25 em `test_web_allowlist.py`, 7 mutantes apanhados. Os 40 do `test_web_fetch.py` continuam a passar.
- **Docs:** `WEB-FETCH.md` §2.1. F2-ALLOW-1 → EM CURSO (ABERTO 69, EM CURSO 8).

### AU-20b: a flag desligada fica escrita no `result.json` (2026-10-07)
- **Pedido do maestro:** "P-42 = A (aprovada). Avança com AU-20b e depois F2-ALLOW-1".
- **Código:**
  - `tool_executor.flag_off_meta(tools_allowed)`;
  - no `GeminiWorker._run`, sem a flag e com `tools_allowed`, o resultado ganha `meta.tools = {"enabled": false, "reason": "PLAN_RUNNER_TOOLS desligada", "flag": ..., "tools_allowed": [...]}`;
  - um passo sem `tools_allowed` fica sem `meta.tools`.
- **Testes:** 2 ajustados (deixaram de exigir a ausência do campo) e 1 novo (passo sem `tools_allowed`). 2 mutantes apanhados (sem o ramo; o ramo sem a condição do `tools_allowed`).
- **Docs:** WORKER-EXTERNAL ("Tools do worker"), contrato AU-20 (tabela e "Prova em run real"). AU-20b → EM CURSO.

### AU-20 FECHADO: run real com a tool (2026-10-07)
- **Merge do #138** (`d4151e9`): o commit `9fe2a2f` está no `main`.
- **Run real do DEV com `PLAN_RUNNER_TOOLS=1`:** `run_2382ec5b5c`, plano `au20-force-read`, `state: done`.
  - Evento `tool_called`: `read_repo_file`, `ok: true`, `bytes: 10948`, `sources: [docs/ops/BUDGET.md]`, `ms: 37`, `turn: 1`, `args_sha256` `cefd6578…`.
  - `meta.tools` presente no `result.json`.
- **PENDENCIAS:**
  - AU-20 → FECHADO (§7);
  - **P-42 = A** registada: com a flag desligada, o `result.json` diz `meta.tools.enabled: false`;
  - novo **AU-20b** (Baixa, CLAUDE) para a implementar;
  - 124 vivos (ABERTO 71, EM CURSO 6, BLOQUEADO 47); histórico com 122 linhas; 42 decisões, todas decididas.
- **Docs:** contrato AU-20 (estado e "Prova em run real"), F6-evidence/deferred e PORTFOLIO deixam de dizer "falta 1 run real".

### AU-20: plano de prova para o run real (2026-10-07)
- **Contexto:** no 1.º run do DEV com o `design-flow-demo` não apareceu `meta.tools`. O maestro trouxe o diagnóstico do Grok (4 pontos).
- **O que o código confirma:**
  - O `request.json` não leva `functionDeclarations`: certo, o worker monta-as na chamada.
  - O `design-flow-demo` não obriga à tool: certo, o `repo_files` injecta os ficheiros. **Mas isso não tira o `meta.tools`:** com a flag, qualquer passo com `read_repo_file` no `tools_allowed` grava `meta.tools` (`calls: []` se o modelo não chamar nada).
  - Por isso a causa provável é a do ponto 3: a flag não chegou ao processo. Em PowerShell é `$env:PLAN_RUNNER_TOOLS = "1"`, na mesma sessão.
  - Um `meta: {}` vazio não vem do worker Gemini, porque o `result.json` dele tem sempre `meta` com `worker`, `model` e `tokens`. Esse `meta` vazio deve ser de outro ficheiro, ou de um run em stub.
- **Feito:**
  - `docs/orchestration/au20/au20-force-read.plan.yaml`: 1 passo, `planejador`/`meta`, `tools_allowed: [read_repo_file]`, sem `repo_files`, com `tool_limits` 3/2 e `budget.max_tokens` 30 000. As 3 perguntas só têm resposta no `docs/ops/BUDGET.md`.
  - 2 testes com o Gemini falso: com a flag, o BUDGET não está no 1.º pedido, só chega pela tool, e o `meta.tools` tem a chamada com `sources`; sem a flag, não há `meta.tools`.
  - Suite completa: 905 passed.

### R-011 e F4-MAT-1 fechados (2026-10-07)
- **Merges:**
  - #135 (`fc372d5`, head `eaaf21d`);
  - #136 (`e74a610`, head `49cfbba`);
  - os 2 commits estão no `main` (`git merge-base --is-ancestor`).
- **Decisão do maestro:** a opção A da evidência do F4-MAT-1 (registo de runs + verificação contra os documentos) está aprovada.
- **Verificado no `main`:**
  - `test_l5_eval.py`, `test_capabilities.py` e `test_areas.py`: 98 passed;
  - `python -m plan_runner.areas --maturity` dá `security.defensive_audit: PROVEN`.
- **PENDENCIAS:**
  - R-011 e F4-MAT-1 passam a FECHADO (§7); P-19 e P-38 dadas como aplicadas;
  - 124 itens vivos (ABERTO 70, EM CURSO 7, BLOQUEADO 47); histórico com 121 linhas (100 fechadas).

### F4-MAT-1: maturidade das capabilities medida (2026-10-07)
- **P-38 = B:** a maturidade é derivada da evidência e não há campo novo nos YAML de capabilities. O `status` continua a ser o âmbito declarado.
- **Código:**
  - `capabilities.capability_maturity`: DRAFT → DECLARED → WIRED → EXECUTABLE → VALIDATED → PROVEN, cada nível a exigir o anterior;
  - `validated_plans`: testes que citam o plano e trocam o `httpx_transport`;
  - `load_runs`: o registo `config/capability-runs.yaml`, com o F5 e o B1, verificado contra os documentos de evidência no E7;
  - `python -m plan_runner.areas --maturity`.
- **Tecto:** o que não é `implemented` fica em EXECUTABLE. As `partial` de security partilham a action do auditor, e um run dele não prova a parte que falta.
- **Medido:**
  - security: `triage`, `defensive_audit` e `security_report` são PROVEN (F5, `run_9017d441d1`);
  - marketing: `market_research`, `seo_brief`, `answer_first_copy` e `ai_findability_review` são PROVEN (B1);
  - as outras 11 de marketing ficam em EXECUTABLE (falta um teste com o Gemini falso);
  - `transcript_analysis` WIRED, `visual_identity` DECLARED, `performance_analysis` e `agent_redteam_lab` DRAFT.
- **Testes:** 18 novos em `test_capabilities.py` (32 → 50) (cada nível, tecto do `status`, registo inválido em 7 formas, `failed` não prova, tabela real do repo, CLI). 8 mutantes apanhados.
- **Docs:** `docs/ops/CAPABILITY-MATURITY.md`. F4-MAT-1 → EM CURSO (ABERTO 70, EM CURSO 9).

### R-011: o limiar da P-19 passa a regressão no `l5_eval` (2026-10-07)
- **Pedido do maestro:** "Recomendação A aprovada": primeiro o R-011, depois o F4-MAT-1.
- **Código:**
  - `l5_eval.regression_failures(summary)`: `provenance_ok` = 1.0 e `source_hit@k` ≥ 0.8 (P-19, opção A);
  - o `run` imprime `REGRESSAO …` e `gate P-19: passou/FALHOU`, sai com 1 abaixo do limiar e grava o bloco `gate` no `--out`.
- **Testes:** 8 novos em `test_l5_eval.py` (25 no total): limiar nos 2 lados, nenhum hit, `k` do golden, `main(["run"])` que passa com os chunks reais e que falha com a fonte errada. 4 mutantes apanhados (`<` → `<=`, sem a regra da proveniência, sem o caso "nenhum hit", sempre `return 0`).
- **Docs e estado:** `L5-F0-REVALIDATION.md` §6.2; R-011 → EM CURSO (ABERTO 71, EM CURSO 8).

### R-005 fechado em produção (2026-10-07)
- **Merges:** #132 (`ecb27d3`), #133 (`a1716f1`) e MCP #22 (`855057d`). Os 3 levaram todos os commits (confirmado no `git log`). O deploy de produção do MCP na Vercel terminou às 18:29 UTC.
- **SQL do R-005 aplicado pelo DEV.** SELECTs de confirmação (maestro e Claude, só leitura):
  - `column_default` do `kb` = NULL;
  - trigger `knowledge_chunks_default_kb`: `BEFORE INSERT ... FOR EACH ROW`, activo (`tgenabled = O`), função com `search_path` vazio;
  - marca "R-005 aplicado" no COMMENT da coluna `kb`, por isso uma 2.ª aplicação não reclassifica nada;
  - 201 linhas do MCP, 19 valores de `kb`, 0 NULL; em todas, `kb` = `agent_id`, menos as 8 da ECC de segurança (`kb` = security, `agent_id` = revisor-codigo);
  - marketing tem 3 linhas, as do agente `marketing`.
- **PENDENCIAS:**
  - R-005 → FECHADO (§7);
  - 126 itens vivos (ABERTO 72, EM CURSO 7, BLOQUEADO 47); histórico com 119 linhas;
  - a linha do AU-20 só espera pelo run real com `PLAN_RUNNER_TOOLS=1`.

### P-22: texto para o upstream do MarkItDown (2026-10-07)
- **Verificação:** os 2 achados reproduzem-se com o MarkItDown 0.1.8, a versão mais recente (venv isolado, script em `docs/ops/upstream/MARKITDOWN-UPSTREAM.md` §4).
- **Pesquisa no upstream:**
  - o achado da tabela DOCX sem cabeçalho já está na issue [#2157](https://github.com/microsoft/markitdown/issues/2157), aberta;
  - o PR #2160 trata só do escape, não do cabeçalho;
  - não há issue para o `.pdf` em texto, mas esse comportamento parece pretendido (o tipo é detectado pelo conteúdo).
- **Opções A/B/C, RECOMENDADA B:** um comentário na #2157 com a reprodução mínima e a oferta de um PR para o cabeçalho. Não se abre uma issue nova, que seria duplicada.
- **Texto pronto, em inglês:** `MARKITDOWN-UPSTREAM.md` §3. Publica o DEV, na conta dele. ING-012 actualizado.

### AU-20, seguimento: `act` pára no HITL e kb por passo (2026-10-07)
- **Pedido do maestro:** "aprovação humana para o nível act (pára no HITL)" e "`retrieve_knowledge` com kb permitido ao passo".
- **Executor (`tool_executor.py`):**
  - `LEVELS_APPROVAL = ("act",)`;
  - o loop pára **antes** de correr qualquer chamada do turno (`ToolApprovalRequired`, com o estado da conversa em JSON);
  - retoma com `resume=` e `approvals=`; cada decisão vale para 1 chamada;
  - args inválidos não chegam ao humano;
  - `step_kbs` (`tool_kbs:` ou `knowledge.kb`), `kb` como enum na declaração, `kb_not_allowed` e `refused_policy`.
- **Worker:**
  - pedido `hitl-request-v1` com os args em `context.tool_calls`, validado contra o contrato;
  - `tool_approval.json` e os eventos `tool_approval_requested`/`tool_approval_resolved`;
  - a decisão é procurada **pelo id do pedido** (a do Node manda; uma aprovação antiga nunca aprova um pedido novo);
  - os tokens de antes da pausa entram no total.
- **Motores:** `paused_human_gate` + `status.tool_approval` + `HITL.md`; o resume grava a decisão e volta a correr o passo. `reject` recusa a chamada, não o run. Nativo e LangGraph (e o fallback por waves).
- **Achado na revisão adversarial:** o `plan_runner resume` usava a última decisão do `hitl-decisions.jsonl` (de qualquer pedido) e, sem `--decision`, aprovava por omissão. Numa tool `act`, passa a contar só a decisão deste pedido, e o `--decision` é obrigatório.
- **Achado e correcção:** o `tool_limits:` do #131 não estava no `plan.schema.json` (step com `additionalProperties: false`), por isso um plano com ele chumbava no W-006. Entra agora, com o `tool_kbs:`.
- **Testes:**
  - `test_tool_executor.py` passa de 25 para 45;
  - 12 mutantes apanhados. Um sobreviveu (a decisão sem filtro por id), e o teste de defesa em profundidade passou a apanhá-lo;
  - suite completa: 875 passed.
- **CI do #132:** o `test-rag` falhou na 1.ª corrida. Era o meu teste: a ordem dos empates do `match_knowledge` muda depois do UPDATE. Reproduzi com a imagem `pgvector/pgvector:pg16`, corrigi (`1144dd4`) e o CI ficou verde nos 11 checks.

### Decisões do maestro, P-20 e regra A/B/C (2026-10-07)
- **Pedido:** "Decisões tomadas pelo maestro. Executa pela ordem indicada": P-20/R-005 → §10 + `CLAUDE.md` → AU-20 → P-22.
- **P-20 verificada (só leitura, Supabase):** `kb` text, `DEFAULT 'marketing'::text`, nullable. As 201 linhas do MCP são de 18 `agent_id`, todas com `kb` = marketing. O `match_knowledge_v2` devolve o `kb`, mas não filtra por ele, por isso a pesquisa ainda não era afectada.
- **Assimetria confirmada:** o `ingest_knowledge` recebe `agent` e o `retrieve_knowledge` recebe `kb`; os 2 vão para o `agent_id`. O insert não mapeava mal: omitia o `kb`.
- **MCP #22 (2 commits: confirmar o head antes do merge):**
  - `ingestDocument` grava `kb` = `agent_id`, ou o `kb` opcional validado do `ingest_knowledge`;
  - regra A/B/C no `CLAUDE.md` do MCP;
  - testes: unitários 31/31 e e2e 14/14; a mutação (tirar o `kb` do insert) é apanhada.
- **Este PR:**
  - `scripts/migrations/r005_kb_default.sql`: sem DEFAULT; trigger que põe `kb = agent_id`; reclassificação uma só vez (marca no COMMENT); ECC de segurança → `security`;
  - `scripts/rag_schema.sql` sem o DEFAULT;
  - `runner/tests/test_r005_kb_default.py`: 6 testes, com 6 mutações apanhadas e 2 equivalentes; está no job `test-rag`.
- **Ordem para o DEV:** primeiro o deploy do MCP #22 e só depois o SQL. A ordem inversa também é segura, porque o trigger a cobre.
- **§10:** as 11 decisões ficam registadas (P-11 = A, P-16 confirmada, P-17 adiada para o H-01, P-19 mantida, P-20, P-21 = A, P-22 = Sim, P-24 = A, P-25 = A, P-38 = B, P-39 = C). Ficam 0 pendentes.
- **Itens novos:**
  - AU-11b (P-11);
  - R-011 (P-19);
  - F2-ALLOW-1 (P-25);
  - ING-012 (P-22).
- **Itens actualizados:**
  - F4-MAT-1 sem bloqueio;
  - F1b, F2, F2-SEC-1 e H-01 anotados;
  - R-005 → EM CURSO.
- **Contagens:** 127 vivos (ABERTO 72, EM CURSO 8, BLOQUEADO 47).
- **`CLAUDE.md`:** a regra "toda a apresentação de opções vem com recomendação explícita. SEM EXCEPÇÃO", com o motivo. Foi pedida porque 11 decisões tinham sido listadas sem recomendação.
- **Nota do maestro:** a base fictícia (`seed_fake_clients`) é infra de teste. Não substitui um cliente real e não desbloqueia a Fase 2 (P-39 = C) nem o F6 canónico.

### AU-20: executor de tools implementado (2026-10-07)
- **Pedido do maestro:** "a P-37 já foi decidida (B); avance e implemente". Antes disto não havia código: confirmado no `main`, sem `functionDeclarations` nem loop.
- **Feito no PR do branch `feat/au20-tool-executor`:**
  - `runner/plan_runner/tool_executor.py`:
    - registo com `read_repo_file` (SEC-1) e `retrieve_knowledge` (L5);
    - autorização = `tools_allowed` ∩ registo, só `read`;
    - validação JSON Schema;
    - limites `max_turns`/`max_tool_calls` com `tool_limits:` por passo;
    - orçamento antes de cada turno;
    - dados, não instruções;
    - thought signatures preservadas;
    - evento `tool_called` com o sha256 dos args.
  - `external_worker.py`: `gemini_generate` aceita a conversa e as declarações; `GeminiWorker(tools=..., knowledge_backend=...)`; `_run_with_tools`.
- **Flag `PLAN_RUNNER_TOOLS`, desligada por omissão.** 42 passos já declaram `read_repo_file`; ligar por omissão mudava o custo e o comportamento deles, incluindo o `seo-article-demo`, base das medições do B1-bis.
- **Testes:** `runner/tests/test_tool_executor.py`, 25 testes, com 5 mutações apanhadas. Os testes do worker que já existiam continuam a passar.
- **Docs:** contrato (secção "Implementação"), WORKER-EXTERNAL, SECURITY-AGENTS, mapeamento ISO (A.4.4 e A.6.2.6 → Cumpre; Anexo A 28/10/0) e evidence pack do F6.
- **PENDENCIAS:** AU-20 → EM CURSO. Fecha com o merge e 1 run real com a flag (DEV).

### Decisões revistas: P-37 = B (2026-10-07)
- **Correcção do maestro:** a P-37 já estava decidida (B, executor mínimo em Python), aprovada numa sessão anterior. O PENDENCIAS tinha-a como proposta pendente. Registada nas decididas, com a contradição V43 no §8.
- **Efeitos:**
  - o AU-20 deixa de esperar por decisão: o bloqueio passa a "implementar o contrato";
  - `AU-20-TOOL-EXECUTOR.md` passa a "contrato aprovado, B decidida";
  - o evidence pack do F6 (`deferred.md`) foi actualizado.
- **Revisão das outras pendentes** (estado real, sem assumir escolhas):
  - P-16: aplicada de facto (os valores A entraram no MCP #14, com merge; o S-001 está fechado). Falta só a confirmação formal.
  - P-17: A aplicada (#70); falta a parte B, com o H-01.
  - P-19: o M1 já fechou por decisão do maestro; só serve como regra de regressão.
  - P-11, P-20, P-21, P-22, P-24, P-25, P-38 e P-39: pendentes de verdade.
- **Contagens:** 41 decisões (30 decididas, 11 pendentes), 43 contradições.

### Retenção confirmada em produção (2026-10-07)
- **Merges:** MCP #21 (12:42 UTC, `c689feb`) e NAS #128 (12:42 UTC, `85d06ff`), com todos os commits (desta vez verificado commit a commit).
- **O DEV aplicou `memory/retention.sql`.** Confirmação do maestro, e SELECT só de leitura desta sessão:
  - a função `purge_expired_content` existe;
  - job `purge-expired-content`, `17 3 * * *`, `select public.purge_expired_content()`, ao lado do `cleanup-agent-logs-daily` (03:00);
  - `anon` sem execução; RLS activo na `retention_own_domains` (`viannalegal.com.br`).
- **À espera da 1.ª purga** (2026-10-08 03:17 UTC): 35 de 99 `transcripts` e as 9 `image_posts` estão expiradas. Os 2 `scrapes` expiram a 2027-07-31. O `token_usage` (38 linhas) não perde nada antes de 2028-10.
- **PENDENCIAS:**
  - GOV-RET-1 (FECHADO) com a evidência de produção;
  - P-41 decidida por inteiro;
  - a lista do DEV deixa de pedir o merge do MCP #20 e a aplicação do SQL, e passa a pedir a confirmação da 1.ª purga.

### P-41 decidida e GOV-RET-1 fechado (2026-10-07)
- **Achado:** os merges do MCP #20 (12:01 UTC) e do NAS #127 (12:02 UTC) levaram só o 1.º commit de cada PR. A retenção (`5efcda9`, `eadecb2` no MCP; `0d07e1e`, `3eeac82` no NAS) ficou fora do `main`. Foi reaplicada sem conflitos: MCP #21 (branch de sessão recomeçado a partir do `main`, com rebase) e NAS no branch `docs/retention-all` (cherry-pick).
- **Decisão do maestro (P-41):** `token_usage` com 24 meses.
- **MCP #21:**
  - `purge_expired_content()` passa a cobrir 4 tabelas;
  - a limpeza do `agent_log` (90 dias), que corria em produção fora do git, fica versionada;
  - testado 2x na imagem do Supabase com o `schema.sql` e o `token_usage.sql` reais.
- **NAS:**
  - política 1.1 §7 (`token_usage` 24 meses, `agent_log` 90 dias);
  - **GOV-RET-1 → FECHADO**;
  - novo **GOV-RET-2** (dados de clientes, BLOQUEADO até haver o 1.º cliente real);
  - P-41 nas decididas.
- **Contagens:** 123 vivos (ABERTO 69, EM CURSO 6, BLOQUEADO 48), 118 de histórico (97 FECHADO), 41 decisões.

### Retenção alargada a `image_posts` e `scrapes` (2026-10-07)
- **Levantamento** (só leituras):
  - `image_posts` vem do `extrair-imagem.yml` (gallery-dl, Instagram): 9 linhas de 1 autor de terceiros, todas tentativas falhadas (3 a pedir login, 6 sem imagens). O bucket `post-images` não tem nenhuma imagem do Instagram: 23 capturas `visual-review` e 3 `diagnostico-portal`.
  - `scrapes` vem do `scrape.yml`: 2 linhas, ambas de `viannalegal.com.br` (site próprio).
  - Nenhum dos fluxos traduz.
- **Decisão do maestro:** `image_posts` com 60 dias; `scrapes` opção B (60 dias por omissão, 12 meses nos sites próprios).
- **MCP #20 → #21:** `memory/retention.sql`, que substitui o `transcripts_retention.sql`:
  - tabela `retention_own_domains` (RLS activo);
  - trigger nos `scrapes`;
  - `purge_expired_content()` e um só job, `purge-expired-content`, às 03:17 UTC.
  - Testado 2x na imagem do Supabase com `pg_cron`.
- **NAS #127:** política 1.1 (§7), AIMS §5.3 e §5.4, P-41 (falta só o `token_usage`), GOV-RET-1, lista do DEV.

### Retenção das transcrições: 60 dias (2026-10-07)
- **Decisão do maestro:** apagar 60 dias depois da criação, sem período de graça ("se for o caso transcrevemos novamente"). Só `transcripts`.
- **Verificado:** nenhum código lê a tabela `transcripts`. Só o `transcribe.yml` escreve e o `content_analyst` lê a transcrição acabada de fazer. O fluxo do reel não muda.
- **MCP #20 → #21:** `memory/transcripts_retention.sql` (`expires_at` preenchido a partir de `created_at`, default `now() + 60 dias`, `purge_expired_transcripts()` sem acesso para `anon`/`authenticated`, job diário do `pg_cron` às 03:17 UTC) e o README.
  - Testado 2x em Postgres 16 e na imagem `supabase/postgres:15.8.1.085` com `pg_cron`: 1 só job, o `anon` não executa, a purga apaga só o expirado.
  - O DEV aplica. Na 1.ª corrida saem 35 de 99.
- **NAS #127:** política de privacidade 1.1 (§7); P-41 decidida para as transcrições; GOV-RET-1 com as transcrições feitas; AIMS §5.3 e §5.4.

### GOV-PRIV-1: transcrições fora do git do MCP (2026-10-07)
- **Merge do #126** (`c487129`): os testes com clientes fictícios estão no `main`.
- **MCP #20** (branch `claude/reels-analysis-tools-access-hwudk9`, recomeçado a partir da `main` porque o #19 já tinha merge):
  - `git rm --cached transcripts/latest.json`;
  - `/transcripts/` no `.gitignore`;
  - secção "Dados e privacidade" no README;
  - `tests/publicRepo.test.mjs`.
  - `npm test`: 28 de 28. A mutação sem a correcção dá 2 falhas.
- **Decisão do maestro:** "Resolvido: C. Transcrições no Supabase. A fica como upgrade." GOV-PRIV-1 → §7. Novo **GOV-PRIV-2** (limpar o histórico, decisão do DEV). AIMS §11.1.
- **Contagens:** 123 vivos (ABERTO 70, EM CURSO 6, BLOQUEADO 47), 117 de histórico (96 FECHADO), 41 decisões.

### Clientes fictícios para testes (2026-10-07)
- **Merge do #125** (`4c99fdd`): política de privacidade em vigor; GOV-IMPACT-1 FECHADO.
- **Pedido:** Faker + testcontainers, seed de clientes fictícios, teste da L4 e da memória do cliente, `docs/ops/TESTING.md`.
- **Correcção ao pedido:** não existe a tabela `client_memory` no ANM. A memória do cliente é o `memory/<client_id>/MEMORY.md` (working memory, S30) mais a `memory_l4` no âmbito `project:<client_id>`. O seed escreve nas duas.
- **Feito no PR do branch `test/fake-clients`:**
  - `runner/requirements-test.txt` (Faker 40.41.0 MIT, testcontainers 4.15.0 Apache-2.0, pins exactos);
  - `scripts/seed_fake_clients.py`: seed fixa, prefixo `FAKE-`, e-mails RFC 2606, só BD local, recusa o Supabase, nunca lê o `DATABASE_URL`;
  - fixture `disposable_pg` no `conftest.py` (RAG_TEST_DATABASE_URL → testcontainers → skip ou erro);
  - `runner/tests/test_fake_clients.py`;
  - CI: `requirements-test.txt` nos jobs `test` e `test-rag`;
  - `docs/ops/TESTING.md`.
- **Verificação:**
  - testes passam com o Postgres local **e** com testcontainers (dockerd arrancado nesta sessão: contentor `pgvector/pgvector:pg16` real);
  - smoke do CLI numa BD descartável: 12 linhas em 3 clientes, limpeza a 0, Supabase recusado;
  - mutação: sem Docker, skip; com `RAG_TEST_REQUIRED=1`, erro.

### Política de privacidade e fecho do GOV-IMPACT-1 (2026-10-07)
- **Merge do #124** (11:03 UTC, `c9de58f`): política do AIMS, mapeamento ISO e teste de evidências no `main`.
- **Estado medido** (só leituras ao Supabase do ANM): **0 dados de clientes**. Ficheiros `memory/<cliente>/`: 0. `memory_l4`: 0 linhas. `agent_log` (119) e `project_state` (19): sem e-mail, telefone nem CPF detectados.
- **Dados pessoais de terceiros:** `transcripts` tem 99 linhas de 52 autores de conteúdo público. O Supabase está na UE (Frankfurt). O RLS está activo em todas as tabelas excepto `_prisma_migrations`.
- **Feito no PR do branch `docs/privacy-policy`:**
  - `docs/governance/PRIVACY-POLICY.md` (LGPD + GDPR, completa);
  - avaliação de impacto real no AIMS §5, com a separação repo público/privado no §11;
  - `config/deployment.yaml` (`repo_visibility`, `privacy_contact`), `/memory/*/` no `.gitignore` e `runner/tests/test_privacy_separation.py`. As mutações foram apanhadas: um ficheiro de cliente versionado num repo público e um repo privado sem contacto;
  - mapeamento: 6.1.4, 8.4 e A.5.2–A.5.5 → Cumpre; A.10.4 corrigido (dizia "há clientes": não há).
- **Achado relevante:** no Gemini gratuito, a Google usa o conteúdo para melhorar produtos. A regra passa a ser "dados de clientes só com Gemini pago".
- **Novos:** GOV-RET-1, GOV-PRIV-1, S-005, P-41.
- **Contagens:** 123 vivos (ABERTO 70, EM CURSO 6, BLOQUEADO 47), 116 de histórico (95 FECHADO), 41 decisões.

### ISO/IEC 42001 e pós-merge do #122 e do #123 (2026-10-07)
- **Merges do maestro:** #122 (10:26 UTC, `4e38801`) e #123 (10:31 UTC, `7cda6f1`). A CI da `main` está verde (11 checks, incluindo o `delta` do ingest).
- **Fechados (§7):** SEC-1.3 (#123); W-011, R-006 e H-002 (#122).
- **P-40 decidida pelo maestro:**
  - âmbito NAS + ANM;
  - papéis maestro / DEV / Claude;
  - auditoria interna trimestral e revisão da política semestral.
- **Feito no PR do branch `docs/governance-iso42001`:**
  - `docs/governance/AI-MANAGEMENT-SYSTEM.md` (política);
  - `docs/governance/ISO-42001-MAPPING.md`: 27 cláusulas e 38 controlos. Cláusulas: 9 Cumpre, 15 Parcial, 3 Falta. Anexo A: 22 Cumpre, 11 Parcial, 5 Falta;
  - `runner/tests/test_governance_mapping.py` (7 testes; evidências e símbolos verificados contra o repo; os resumos à mão estavam errados e o teste apanhou-os);
  - secção ISO no contrato do AU-20.
- **O #123 já tinha merge:** a secção ISO do contrato do AU-20 vai neste PR novo, não no #123.
- **Novos:** GOV-42001-1 (EM CURSO) e GOV-IMPACT-1 (ABERTO, Alta: avaliação de impacto da memória de clientes); prefixo GOV- no §3.
- **Contagens:** 121 vivos (ABERTO 68, EM CURSO 6, BLOQUEADO 47), 115 de histórico (94 FECHADO), 40 decisões.

### AU-20, pré-requisito: verificação do `activate_for_task` (2026-10-07)
- **Pedido do maestro:** verificar a implementação e a documentação do branch `feat/activate-for-task-sec13` (outro agente), testar, corrigir e reforçar, com pesquisa de projectos maduros.
- **Estado encontrado:**
  - o `executor.py` importava `activate_for_task` e `materialize_activation`, que nunca chegaram ao git;
  - a suite não corria (18 erros de colecção; no `main`, 754 passed);
  - o wire perdia o `skill_preview_head` e o `agent_preview_head`;
  - o `test_skills.py` anunciado ia sobrescrever o do `main`.
- **Feito no mesmo branch, PR #123 (draft):**
  - `skill_activation.py` + 39 testes (sem rede);
  - SEC-1.3 deny-by-default e fail-closed, com sha256 + `pins:` (OWASP Agentic Skills: update drift);
  - pesquisa externa pela API skills.sh por HTTPS directo, em vez de `npx skills find --json`: o `find` não tem `--json` no `skills@1.7.1`, e o `npx` executa código descarregado;
  - o `SKILL_ACTIVATION.md` entra no prompt só quando há algo a dizer.
  - Suite local: **793 passed**.
- **Docs:**
  - `docs/ops/SKILL-ACTIVATION.md`;
  - secção "Verificação" no `docs/REPORT-ACTIVATE-FOR-TASK.md`;
  - `docs/architecture/AU-20-TOOL-EXECUTOR.md`: contrato §15.4 proposto para a P-37, B recomendada.
- **PENDENCIAS:** novos SEC-1.3 (EM CURSO) e SKILL-EXT-1 (BLOQUEADO: SkillsCat, API sem contrato e serviço AGPL). O AU-20 continua ABERTO.
- **Contagens:** 123 vivos (ABERTO 67, EM CURSO 9, BLOQUEADO 47).

### Revisão do EXECUTION-PLAN desde a Parte 1, 2.ª passagem (2026-10-07)
- **Pedido do maestro:** a revisão é desde o início (A), não só o roadmap. Li o plano por partes:
  - Parte 1 (§1 a §3: estado de partida, arquitectura e os 3 ajustes);
  - Parte 2 (§4 a §6: matrizes P0, P1 e P2, e os gates);
  - Parte 3 (§8 a §12: meta-agentes, pendentes, anti-padrões, teste definitivo e instruções);
  - Parte 4 (§14 e §15: adendo e governança).
- **Bloqueios desactualizados corrigidos:**
  - R-005 dizia "F3"; agora depende da P-20;
  - as 18 linhas G1/G2 diziam "F5 + D-EP8"; agora só a D-EP8;
  - B1-bis-C dizia "depois de F0–F3";
  - L4-2 dizia "depois do F3"; L4-3 e EX-B7 diziam "depois do F5". Todos já podem avançar.
- **Compromissos do plano sem item, agora registados:**
  - E-004: capabilities de software (§5.16);
  - ING-008: o contrato do `ingest_document` com `url`, `bytes` e `connector_ref` (§3, ajuste 1);
  - ING-009: document intelligence como capability (§4.4);
  - ING-010 e ING-011: Instructor e Unstructured (§2.3);
  - R-007 e R-008: Graphiti e LightRAG como padrões (§2.3);
  - R-009: sunset da v1 e da flag (§15.10, ADR-F3 §4);
  - **R-010: o purge nunca é chamado** (§15.8, regra T6). É um achado real.
- **F2:** o artefacto de research ainda não tem o formato do §3, ajuste 2.
- **Correcções feitas:**
  - H-002 (os 2 avisos do ruff; um deles foi introduzido por mim no #120);
  - o docstring do `mcp_knowledge.py`, que dizia que o `metadata` e o `locator` vêm sempre `None`;
  - o DOC do F4 medido (§15.9; §7 F4-DOC): 1 ficheiro do core, o que o próprio F4 pedia.
- **D-EP5** ("decidir depois do F5") → **P-39** (recomendada C: decidir com o primeiro caso real).
- **Contagens:** 121 vivos (ABERTO 67, EM CURSO 8, BLOQUEADO 46), 113 de histórico (92 FECHADO), 42 contradições, 39 decisões.

### Revisão contra o EXECUTION-PLAN e correcções (2026-10-07)
- **Merges do maestro** (2026-10-06, 21:22–21:24 UTC): #119, #120, #121.
  - A CI da `main` está verde em cada merge, incluindo `test-rag` e `test-ingest` no #120. Assim, o código do #120 foi validado na `main`, embora o PR não tenha tido CI própria antes do merge.
  - Produção do F3c (SELECT só de leitura): 7 fontes, 15 chunks, todos com `locator`.
- **F3c-DESIGN-1, opção A:** `repo_files:` nos 4 passos de design dos 2 planos de design, com os ficheiros que cada skill nomeia; o crítico recebe os 2 que o pack lhe destina.
  - Novo `test_plan_repo_files.py`: sem a alteração, 3 dos 4 testes falham.
  - V42: a razão "as skills de design lêem o ficheiro" estava errada para o worker Gemini.
- **W-011:** o `MCP_URL` com `/api/mcp` já não duplica o caminho; um bypass com menos de 16 caracteres falha logo, sem mostrar o valor.
- **R-006:** `provenance_v2_ok` no `l5_eval`.
- **Revisão do Done de cada fase do E §7:**
  - F2: falta a capability que use o `fetch`;
  - F3: proveniência no artefacto → **F3-ART-1**;
  - F4: escala de maturidade do §15.7 → **F4-MAT-1** / P-38;
  - F5: run a partir do `route` → **F5-ROUTE-1**.
  - F1, F4 e F5 continuam FECHADOS: o Done que os fechou está cumprido.
- **Estado no `PENDENCIAS.md`:**
  - F3c, F3b-VALIDADE e F6-CADEIA → §7;
  - o F3 passa a BLOQUEADO (só tem estacionados);
  - AU-20 → P-37 (recomendada B: executor mínimo em Python);
  - §5 do DEV refeito;
  - contagens: 112 vivos (ABERTO 61, EM CURSO 7, BLOQUEADO 44), 112 de histórico, 42 contradições, 38 decisões.
- **Portfolio:** README e `PORTFOLIO.md` com os números de hoje (836 testes pytest, 100 PRs com merge, mais 195 de TypeScript) e o link para o WHAT-I-CONTRIBUTED; evidence pack actualizado.

### Opção B confirmada pelo maestro (2026-10-06)
- **P-23 = A decidida.** No `PENDENCIAS.md` §4 ficam 2 linhas distintas: **F6-CADEIA** (EM CURSO, fecha no merge do #121) e **F6 canónico** (BLOQUEADO, D-EP8).
- **F3b-AUTH-1:** passa para o último lugar do §4; não é pré-condição do F6-CADEIA.
- **Contagens:** 110 vivos (ABERTO 60, EM CURSO 7, BLOQUEADO 43).
- **C.2 a C.6:** já estavam feitos no #121, a partir do inventário `0687c5c`, e não se refazem. Depois dos merges #119 → #120: actualizar o #121 com a `main` e confirmar a CI.

### F6 C.6 feito: PR #121 (2026-10-06)
- PR **#121** `docs: F6 hardening, evidence pack and portfolio summary` (branch `docs/f6-hardening-portfolio`, base `main`). O corpo diz: pré-condições, o que entra, estacionados, "no production writes" e "do not merge yet". Ordem de merge: #119 → #120 → #121.
- A base do #120 passou a `main`, para correr a CI (com a base `feat/f3c-knowledge-coverage` os workflows não corriam).
- Validação local antes do PR: runner contra Postgres **754 passed**, 29 skipped; ruff OK. A 1.ª corrida deu 66 erros porque o Postgres local tinha parado; com ele a correr, passa tudo.

### F6: mini-relatório (§E)
```
FASE: F6 da cadeia (hardening + evidence pack + portfolio)
DATA: 2026-10-06
ESTADO: 🔒 (C.1 parado) → ✅ por instrução do maestro ("Fez o f6 como no prompt"); o merge é do maestro
PRÉ-CONDIÇÕES: F1, F4, F5, F3a ✅; F2 ✅ na cadeia; F3c #119 e F3b-validade #120 em PR; F3b-autoridade estacionado (F3b-AUTH-1)
HARDENING: gitleaks (árvore e histórico) limpo; 13 paths locais removidos; nota de escrita em produção corrigida; MANIFEST ou EXCLUDED testado; F1 e F2 documentados e testados; DNS rebinding → F2-SEC-1
ARTEFACTOS: docs/portfolio/F6-evidence/ (7 ficheiros), docs/portfolio/WHAT-I-CONTRIBUTED.md
CANÓNICO: PENDENCIAS_T6 F6 ✅; PENDENCIAS P-23 = A aplicada, F3b-AUTH-1 e F2-SEC-1 novos, 109 vivos; F6 canónico (D-EP8) continua aberto
PR: #121 (sem merge). Produção: nenhuma escrita
TESTES: runner + Postgres 754 passed, 29 skipped; ruff OK
PRÓXIMO PASSO: o maestro faz o merge do #119 → #120 → #121; depois, quando quiser, o F3b-AUTH-1 (v3) e o F3b-VAL-1 (datas)
```

### F6 C.5 feito: canónico e PENDENCIAS (2026-10-06)
- `PENDENCIAS_T6.md`: **F6 ✅** (PR aberto; o merge é do maestro); F3 com o F3b-autoridade estacionado; o risco "F6 do prompt ≠ canónico" fica resolvido pela P-23 = A.
- `PENDENCIAS.md`:
  - a P-23 fica **aplicada: A** (instrução do maestro), registada no §10;
  - o F6 canónico continua BLOQUEADO, agora só pela D-EP8;
  - 2 itens novos no fim do §4: **F3b-AUTH-1** (BLOQUEADO: SQL da v3 + flag) e **F2-SEC-1** (ABERTO: DNS rebinding);
  - o F1 a F5 não foram reabertos;
  - contagens: 109 vivos (ABERTO 60, EM CURSO 6, BLOQUEADO 43).

### F6 C.4 feito: resumo de portfolio (2026-10-06)
- `docs/portfolio/WHAT-I-CONTRIBUTED.md`: 10 pontos factuais em inglês (a língua do `docs/PORTFOLIO.md` para recrutadores), cada um com o PR, mais o link para o evidence pack. Diz também o que ficou por fazer (F3b-AUTH-1).

### F6 C.3 feito: evidence pack (2026-10-06)
- `docs/portfolio/F6-evidence/` (commit `c5eba44`): `README.md` (índice e estado da cadeia), `prs.md` (21 PRs NAS e MCP com link), `decisions.md` (P-21 a P-36), `tests-and-ci.md` (comandos e última corrida), `run-e2e.md` (F0.7b, F3a v2, F5), `hardening.md` (checklist do C.2 e o que escreve em produção), `deferred.md` (14 estacionados com o critério de desbloqueio).
- Sem dumps de BD, segredos nem conteúdo de documentos. As afirmações técnicas foram conferidas contra as fontes (`INGEST-DOCUMENT.md:34-39`, `ANM:lib/knowledge.js`).

### F6 C.2 feito: hardening (2026-10-06)

| Item | Resultado |
|---|---|
| Segredos | `gitleaks dir .` e `gitleaks git .` (todo o histórico): sem fugas. Nenhum `.env` versionado |
| Paths absolutos da máquina | **Corrigido:** 13 `C:\Users\<utilizador>\…` em 4 docs → `%USERPROFILE%` (commit `7cf5280`). O histórico do git mantém-nos (sem reescrita) |
| MANIFEST ou EXCLUDED | `test_knowledge_coverage.py` verde (#119) |
| Segurança de entrada | `docs/ops/INGEST-DOCUMENT.md` (timeout, `RLIMIT_DATA`, `max_bytes`, ZIP) + `test_ingest_security.py` (18) |
| F2 | `docs/ops/WEB-FETCH.md` (allowlist em cada redirect, robots RFC 9309, SSRF incluindo `169.254.169.254`) + `test_web_fetch.py`. Limitação já documentada (DNS rebinding) → item novo **F2-SEC-1** |
| Retrieve aditivo | `match_knowledge` intacta; `match_knowledge_v2` aditiva; flag `KNOWLEDGE_RPC_V2` documentada (`RAG-CANONICAL.md` § F3a, `ANM:docs/RAG_GROUNDING.md`). A `v3` está estacionada (F3b-AUTH-1) |
| Dry-run vs escrita | **Corrigido:** o `RAG-CANONICAL.md` §3 dizia que um push ainda escrevia na t6 (falso desde o J3). Agora diz o que escreve em produção (só o `ingest_apply.py` sem `--dry-run`, no workflow) e o que não escreve |
| Testes no âmbito tocado | coverage, segurança de entrada, web fetch e validade: 95 passed, 4 skipped |

### F6: retomado por instrução do maestro (2026-10-06, "Fez o f6 como no prompt")
- **Leitura aplicada** (regra B do prompt do F6: estacionar o que não pode ser implantado, sem apagar):
  - F3b, autoridade e conflitos (P-31 a P-33) precisa de SQL em produção e da flag no MCP → estaciona como **F3b-AUTH-1** no fim das pendências;
  - F3c (#119) e F3b-validade (#120) estão concluídos em PR; o merge é do maestro;
  - "F6 ✅" = o F6 da cadeia (hardening + portfolio). O F6 canónico (domínio de prova, D-EP8) continua no §4, como na P-23 A ("os 2").
- **C.2 a C.6 seguem neste branch;** cada subpasso fica gravado aqui.

### F6 C.1 feito: pré-condições NÃO cumpridas, parado (2026-10-06)
Prompt "FECHAR F6", protocolo A.3(b): falta trabalho grande antes do F6, por isso não se finge um F6 completo. Estado lido do disco (`PENDENCIAS.md`, `PENDENCIAS_T6.md`), não do chat.

| Pré-condição | Estado no disco | OK? |
|---|---|---|
| F1 | §7 FECHADO (2026-10-05) | ✅ |
| F2 | Cadeia: ✅ merged (#111). Canónico: EM CURSO (`discover`, fallback JS, P-24, P-25), por desenho (F2a fechou o critério do prompt) | ✅ na cadeia |
| F3a | §7 FECHADO (2026-10-06; v2 activa em produção) | ✅ |
| F3c | PR #119 aberto, **sem merge** (W-prod no merge) | ❌ |
| F3b, validade | PR #120 aberto (empilhado no #119), **sem merge** | ❌ |
| F3b, autoridade e conflitos (P-31 = D, P-32 = B, P-33 = B) | **Não começado.** Trabalho grande: `match_knowledge_v3` aditiva (SQL do DEV), anotação no runner e regra no prompt, PR no MCP com flag | ❌ |
| F4 | §7 FECHADO | ✅ |
| F5 | §7 FECHADO (run real PASSOU) | ✅ |
| P-23 (F6 da cadeia vs F6 canónico) | **Pendente.** O F6 canónico é "UM domínio de prova" (D-EP8, BLOQUEADO). Marcar "F6 ✅" no canónico sem a P-23 redefinia um ID decidido | ❌ |

- **Decisões P-21 a P-36:**
  - P-26 a P-36: decididas pelo maestro;
  - P-21, P-22, P-24 e P-25: propostas, por confirmar (não bloqueiam o F6);
  - P-23: pendente (bloqueia).
- **PRs relevantes:**
  - com merge: #105–#117 e MCP #19;
  - abertos: #118 (Dependabot), #119 (F3c), #120 (F3b, validade).
- **O que NÃO foi feito** (C.2 a C.6): hardening, evidence pack, WHAT-I-CONTRIBUTED, F6 ✅ e PR do F6. Ficam para depois da decisão.
- **Opções para desbloquear** (A/B/C no relatório; a recomendada é B, a confirmar pelo maestro).

### F3b, validade implementada (2026-10-06)
- **P-27 = C, P-28 = C, P-29 = A**, no branch `feat/f3b-validity` (empilhado no #119). **Sem SQL novo:** a `match_knowledge_v2` já filtra por validade.
- **`config/knowledge-validity.yaml`:** classes `legal` (exige `effective_from`), `market_data` (exige `effective_until`) e `web` (TTL de 90 dias desde o `retrieved_at`). Override com `validity_class` no sidecar.
- **`runner/plan_runner/validity.py`, aplicado no `ingest_apply`:**
  - sidecar de classe datada sem a data → `INVALID_META`;
  - classe datada sem sidecar → AVISO, sem falhar. É o caso das 2 fontes de hoje (`legal/direito-br-pt.md`, `imobiliario/fipezap.md`): zero breaking change no merge e nenhuma data inventada. Novo **F3b-VAL-1** (DEV).
- **`scripts/validity_report.py`:** local, só leitura do git; `--at` e `--strict`. No repo: `falta_data 2, sem_data 44`.
- **Testes:**
  - `test_validity.py`: 30, sem BD;
  - `test_f3b_validity.py`: 4, contra Postgres. A web expira pelo TTL e sai do retrieve, mas fica na BD; a lei sem vigência não entra; a classe datada sem sidecar entra com aviso;
  - o `test-rag` da CI passa a correr o `test_f3b_validity.py`.
- **Contagens:** 107 vivos (ABERTO 59, EM CURSO 6, BLOQUEADO 42).

### F3c implementado e decisões do F3b registadas (2026-10-06)
- **Decisões do maestro:** P-27 = C, P-28 = C, P-29 = A, P-30 = A, P-31 = D, P-32 = B, P-33 = B, P-34 = A, P-35 = A, P-36 = A (`PENDENCIAS.md` §10).
- **Itens novos**, estacionados no fim do §4 com critério de desbloqueio:
  - F3-MCP-1 (validade e autoridade nas linhas do MCP);
  - F3c-DESIGN-1 (pack de design, quando houver consumidor);
  - F3b-GS-1 (golden set de marketing).
- **F0.12:** ganha a prova de que a t6 está toda na canónica.
- **F3c** (branch `feat/f3c-knowledge-coverage`):
  - `scripts/ingest_delta.py`: 7 `.md` de `marketing/` no MANIFEST (`marketing`, P1); o `EXCLUDED` com 25 entradas, cada uma com a razão;
  - `runner/tests/test_knowledge_coverage.py` (5 testes; falham sem a alteração):
    - todo o `.md` de `docs/knowledge/` está no MANIFEST ou no `EXCLUDED`;
    - os duplicados têm o cabeçalho de cópia do `ingestion/` do MCP;
    - o design só fica de fora enquanto nenhum plano usar `kb: design`;
    - o pack de marketing tem consumidor e cabe no orçamento;
  - `runner-tests.yml`: o filtro de paths passa a incluir `docs/knowledge/**`;
  - `docs/ops/RAG-CANONICAL.md` § F3c: tabela e SELECT de controlo.
- **W-prod no merge:** o `ingest-knowledge` ingere os 7 de marketing (~15 chunks); as 39 fontes anteriores ficam UNCHANGED.
- **Contagens:** 106 vivos (ABERTO 58, EM CURSO 6, BLOQUEADO 42); 36 decisões.

### F3a FECHADO: v2 activa em produção (2026-10-06)
- **Prova do DEV:** `tools/call` do `retrieve_knowledge` (`kb=security`, query "chairman security council", `top_k=1`).
  - O hit traz `citation.uri` = `docs/knowledge/security-agents-stack.md`.
  - O `metadata` vem preenchido: `document_type` = `md`, `status` = `active`, `content_hash`.
- **Porque prova a v2:**
  - na v1 (`ANM:lib/knowledge.js`), o `metadata` é `null` e o `citation` nem tem `uri`;
  - no fallback para a v1 com a flag ligada (PGRST202), o `status` e o `document_type` viriam `null`, porque só a `match_knowledge_v2` os devolve.
- **`locator` `null`:** esperado nas linhas antigas; preenche-se quando cada fonte for re-ingerida.
- **Registado:**
  - F3a no §7 (FECHADO);
  - F3 continua EM CURSO (F3b, F3c);
  - o R-006 mantém-se (o `l5_eval` não distingue as versões);
  - contagens: §4 sem alteração (103 vivos), §7 109 linhas (88 FECHADO).
- **PR:** continuação do #117 (branch `docs/f3a-production`).

### F3a em produção: SQL verificado; a v2 ainda sem prova (2026-10-06)
- **O DEV pediu F3 → FECHADO**, com o `l5_eval` contra produção e `KNOWLEDGE_RPC_V2=1`: 18 casos, `chunk_hit@1/3/4` 0.611/0.889/0.944, `source_hit@4` 1.0, `mrr_chunk` 0.736, `no_hits` 0, `provenance_ok` 1.0.
- **Verificação do Claude (só leituras):**
  - Supabase `agent-network-memory`, SELECTs ao catálogo: existem a `match_knowledge` e a `match_knowledge_v2`, as colunas `uri`, `status`, `document_type`, `meta` e `effective_from` da `knowledge_sources`, o `locator` da `knowledge_chunks` e o `knowledge_sources_status_check`. **O SQL do F3a está aplicado.**
  - Vercel: a leitura das env vars foi recusada pelo modo de permissões, por isso a flag não foi vista pelo Claude.
- **Porque não fechou:**
  - (1) o `provenance_ok` é `bool(hits) and all(sources)` e só olha para o `citation.source`, que a v1 também devolve. Os números são iguais aos do F0.7b, que correu na v1. **Provam que não houve regressão, não que a v2 está activa;**
  - (2) o F3 canónico inclui o F3b (validade e conflitos, autoridade, golden set) e o F3c (33 ficheiros fora do MANIFEST). Fechá-lo cortava-os.
- **Registado:**
  - F3 com a evidência de produção (continua EM CURSO);
  - novo R-006 (o `l5_eval` passa a medir o `metadata` da v2);
  - comando de 1 linha no `RAG-CANONICAL.md`, que imprime `v1` ou `v2`;
  - contagens: 103 vivos (ABERTO 58, EM CURSO 6, BLOQUEADO 39).
- **Opções para o maestro:** A/B/C no relatório (a recomendada mantém o F3 vivo e fecha o F3a numa linha própria quando o comando der `v2`).

### F5 PASSOU: F5 e F4 FECHADOS (2026-10-06)
- **Evidência do DEV** (`scripts/f5_evidence.py pilots/f5-run-v3`): `run_9017d441d1`, plano `example-security-audit-demo`, `external`, estado `done`.
  - L5: passo audit com `kb=security` e 5 hits, fonte `docs/knowledge/security-agents-stack.md`.
  - Modelo: 3 chamadas a `gemini-3.5-flash-lite`, tokens 13670 / 2944 / 16614.
  - 4 artefactos, 0 erros. Veredicto **PASSOU** (5 de 5).
- **Os 2 primeiros runs falharam por configuração:**
  - o 1.º pelo `MCP_URL` com `/api/mcp`. **O erro era meu, no runbook do #115:** o runner acrescenta sempre `/api/mcp`, como já dizia o `L5-F0-REVALIDATION.md:241`. Corrigido no runbook; V41 no §8;
  - o 2.º por um `VERCEL_PROTECTION_BYPASS` com 1 carácter. O runbook ganhou uma linha que mostra o tamanho dos 3 segredos sem os valores. Novo W-011: o runner deve validar os dois à partida.
- **`.gitignore`:** o 3.º run usou `pilots/f5-run-v3`, que não estava ignorado. O padrão passa a `pilots/f5-run*/`.
- **`PENDENCIAS.md`:**
  - F5 e F4 → §7. O F4 fecha pela regra do §9 (passo 5), porque o #114 entrou;
  - F3 continua EM CURSO, com os merges registados; faltam o SQL e a flag (DEV), o F3b e o F3c;
  - o F6 deixa de ter o F5 no bloqueio (fica a D-EP8 e a P-23);
  - contagens: 102 vivos (ABERTO 57, EM CURSO 6, BLOQUEADO 39), 108 de histórico, 41 contradições.
- **PR:** branch `docs/f5-closed` (só docs e `.gitignore`).

### F5: preparado para o run real do DEV (2026-10-06)
- **Escolha do caso:** o plano `security-audit-demo`.
  - Liga o T6 (o pack de security já está no L5), o retrieve no MCP de produção (bloco `knowledge:` do passo audit) e o Gemini real (triage, audit e report), e pára no gate humano.
  - É real e não sensível, e só lê.
- **`scripts/f5_evidence.py`:** resume o directório do run (estado, eventos, L5 com hits e fontes, tokens por modelo, artefactos com hash) e dá o veredicto pelos 5 critérios. Nunca imprime prompts, conteúdo nem variáveis de ambiente.
  - 11 testes: um run stub real dá INCOMPLETO, e um segredo plantado num artefacto e no contexto não aparece na saída.
- **Achados da verificação do runbook** (corrigidos antes do commit):
  - o `pilots/f5-run/` não estava no `.gitignore`, o que punha os artefactos do run real em risco de ir para um commit;
  - escrevi que o worker tinha retry a 429, e é falso (só o `ingest_apply` tem);
  - os preços em `config/model-prices.yaml` estão `null` (T-004), e com `--max-cost-usd` o worker recusa chamar o modelo. O runbook usa só `--max-tokens`.
- **CI do GitHub sem runners:** os PRs #113 e #114 têm jobs "not acquired by Runner". Fiz 1 re-execução em cada; a validação local e o resto do CI estão verdes.
- **Regra 9:** o F5 fica 🔒 à espera do run do DEV. O F6 não arranca sem o F5 (e depende também da P-23).

### F4: `marketing-capabilities.yaml` com maturidade medida (2026-10-06)
- **F3a fechado em PR:** #113 (NAS) e MCP #19.
  - O CI do #113 está verde no código.
  - Na cabeça final, o semgrep, o CodeQL e um `test` não tiveram runner do GitHub. Fiz uma re-execução, com o mesmo resultado (infraestrutura).
  - O delta entre as 2 cabeças é só documentação, e cada check passou numa delas. Ficou 1 comentário no PR.
- **`config/marketing-capabilities.yaml`:** 18 capabilities, com a mesma estrutura de security.
  - 15 `implemented`, cada uma com agente, skill e pelo menos 1 plano real;
  - 1 `partial` (`transcript_analysis`: tem executor mas nenhum plano);
  - 2 `planned` (`visual_identity`, que tem o agente mas não tem skill, e `performance_analysis`, que tem o pack de conhecimento mas não tem agente).
  - Política: ofensivo e acção em produção proibidos, nível por omissão `prepare`, HITL obrigatório (publicar e gastar é sempre humano).
- **Maturidade medida** (o "maturidade de capability" do F4 canónico): o E7 passa a exigir, para `implemented`, pelo menos 1 plano do runner com a action. Senão, a capability é `partial`.
  - Security continua válido.
  - Verificado à mão: promover a `transcript_analysis` sem plano é recusado pelo E7.
- **Testes:** `test_capabilities.py` com 32. Novos: a regra e a leitura das actions em qualquer profundidade (só de planos do runner); os ficheiros reais; as capabilities `implemented` de marketing com planos válidos no schema do runner (W-006).
- **Canónico:** F4 BLOQUEADO → EM CURSO (103 vivos: ABERTO 56, EM CURSO 7, BLOQUEADO 40).

### F3a, etapa 5: MCP atrás de feature flag (2026-10-06)
- **Branch:** `claude/reels-analysis-tools-access-hwudk9` no `agent-network-mcp`. O branch designado foi recriado a partir da `main` `880d492`, porque o #18 já teve merge e o branch remoto tinha sido apagado.
- **`lib/knowledge.js`:** `KNOWLEDGE_RPC_V2=1` liga a `match_knowledge_v2`.
  - Sem a flag, o pedido e o hit são idênticos aos de hoje.
  - Com a flag, os filtros passam por lista branca e validação (`sanitizeKnowledgeFilters`), e os hits ganham `citation.locator`, `uri`, `title` e `metadata`, sem perder campos.
  - O contexto dos agentes também exclui documentos revogados ou expirados.
- **Melhoria encontrada ao documentar:** ligar a flag antes do SQL deixaria o RAG vazio em silêncio, porque o `retrieveKnowledgeHits` engole erros. Agora o MCP detecta `PGRST202`, regista um aviso e cai para a `match_knowledge`. Há um teste para isto.
- **Testes:**
  - `tests/knowledgeV2.test.mjs` (7); `npm test` 26/26;
  - e2e (`next build` + 13 testes) 13/13, sem alterações ao `CLAUDE.md`;
  - mutação: com a v2 sempre ligada, o teste da flag desligada falha;
  - gitleaks e semgrep limpos.
  - O MCP não tem workflows de PR: a validação é local, e está descrita no PR.
- **Documentação:** `docs/RAG_GROUNDING.md` (flag, ordem segura, fallback, rollback) e `.env.example`.
- **PR:** `agent-network-mcp` #19, par do #113.

### F3a, etapas 2 a 4: SQL, writer e testes no NAS (2026-10-06)
- **Migração aditiva:** `scripts/migrations/f3_provenance_retrieve.sql` acrescenta 10 colunas à `knowledge_sources` (com um CHECK do status), o `locator` à `knowledge_chunks` e a função `match_knowledge_v2`, com filtros e proveniência por `LEFT JOIN`, só nas linhas do T6. O `match_knowledge` antigo fica igual.
  - Verificada à mão e no CI: corre 2 vezes sobre dados antigos sem erro.
- **Risco tratado:**
  - o merge deste PR toca em `docs/**/*.md` e dispara o `ingest-knowledge` contra produção antes de o DEV correr o SQL;
  - por isso o writer **detecta** a migração (`has_f3_columns`) e, sem ela, escreve exactamente como antes;
  - está testado nos 2 schemas.
- **`runner/plan_runner/provenance.py`:**
  - valida o `.meta.yaml`: campos, hash, status e datas, incluindo comparar datas com e sem fuso sem `TypeError`;
  - converte-o nas colunas.
- **`ingest_apply`:**
  - `INVALID_META` não escreve nada e conta como falha da corrida;
  - `META_UPDATED` acontece quando o `.md` é igual e só o sidecar muda, sem embeddings, e é o que torna possível uma revogação ter efeito;
  - sem sidecar, a proveniência vem do git.
- **Testes:**
  - `test_f3_provenance.py` (11, Postgres): a migração 2 vezes sobre dados antigos, o CHECK, o writer sem e com a migração, a v2 com proveniência e cada filtro, o `match_knowledge` antigo igual, as linhas do MCP sem herdar proveniência, `INVALID_META` e `META_UPDATED`;
  - `test_provenance.py` (10).
  - Verificação por mutação: sem a detecção, ou sem a condição `project` no JOIN, os testes respectivos falham.
- **Defeitos meus apanhados na validação:**
  - acrescentei uma chave ao retorno do `replace_chunks`, o que partia um contrato testado (revertido);
  - o `has_f3_columns` não tratava um cursor sem linha;
  - o refactor separou o `nosemgrep` da chamada a que se aplicava (o semgrep apanhou).
- **Validação:** sem extras, `pytest` 700 passed e 29 skipped; com extras e Postgres, 144 passed; semgrep 0; gitleaks limpo.
- **Documentação:** runbook do DEV em `docs/ops/RAG-CANONICAL.md` § F3a (ordem merge → SQL → MCP → flag; rollback desligando a flag).

### F3a, etapa 1: P-26 = A, F1 FECHADO (2026-10-06)
- **Maestro:** o merge do #110, do #111 e do #112 está feito, e a **P-26 = A**. Pedido explícito: implementar o F3 (SQL aditivo, v2, writer, testes e MCP mínimo ou com feature flag) e só depois o F4.
- **Pergunta do maestro, "porque não levou o prompt até ao fim":** parei no F3 por excesso de cautela. A opção A é aditiva e o SQL só corre pela mão do DEV, por isso podia ter implementado num PR sem merge. Fica registado como lição: com uma opção aditiva e sem escrita em produção, avança-se em PR e a decisão fica para o merge.
- **Canónico:**
  - o F1 passa para o §7 como FECHADO (merge do #105 ao #110; providência 2);
  - o F3 passa a EM CURSO;
  - a P-26 fica decidida;
  - o alias ING-2 aponta para o §7.
  - Ficam 103 vivos (ABERTO 56, EM CURSO 6, BLOQUEADO 41) e 106 linhas no §7 (85 FECHADO). Recontagem validada.
- **ADR do F3:** o estado passa a Aceite (opção A). **`PENDENCIAS_T6.md`:** o T6f e o F2 ficam ✅ Merged, e o F3 fica ⏳.

### F3: ADR proposto e paragem na decisão P-26 (2026-10-06)
- **F2 fechado:** o PR #111 tem CI verde nas 2 cabeças. Registo e mini-relatório no `PENDENCIAS_T6.md`.
- **Porque o F3 não tem código:**
  - leva a proveniência ao retrieve, o que muda o schema e a RPC `match_knowledge` de produção, que o MCP chama (`ANM:lib/knowledge.js:68`);
  - mudar a assinatura parte o MCP;
  - o F3 canónico (AMBOS, Alta) é bem mais largo do que o do prompt.
  - Seguiu-se o padrão do F1 neste repo: ADR primeiro (contract-first, §15.4), e código só com decisão.
- **ADR (`docs/architecture/adr/ADR-F3-PROVENANCE-RETRIEVE.md`):**
  - opção A (recomendada) aditiva: colunas novas, RPC nova `match_knowledge_v2` com filtros e proveniência, o `ingest_apply` passa a ler o `.meta.yaml`, SQL corrido pelo DEV, e depois o MCP passa para a v2. O `match_knowledge` antigo fica intacto;
  - âmbito F3a (critério do prompt), F3b e F3c (o resto do F3 canónico, sem corte).
- **Canónico:** P-26 no §10 (25 → 26 decisões), e a linha do F3 aponta para o ADR e para a P-26.
- **Regra 9 do prompt:** bloqueio documentado; a cadeia pára aqui até à decisão. F4, F5 e F6 exigem a fase anterior concluída.
- **Registo:** a 1.ª tentativa de editar este ficheiro falhou (erro de sintaxe no meu script de edição) depois do push do ADR; corrigido neste commit.

### F2a: `fetch` com proveniência (2026-10-06)
- **Contexto:**
  - o maestro fez o merge do #106 ao #109 (17:39–17:40 UTC). A `main` `cd8aeb3` ficou com o CI verde, e o `ingest-knowledge` correu com sucesso;
  - o registo dos merges foi para o #110 (`5afbd34`, CI verde).
- **Decisão de base:** a canónica do F2 é "a partir do `scrape.yml`; Crawl4AI só se o superar". O prompt dizia "Crawl4AI preferencial", e seguiu-se a canónica (registado no `PENDENCIAS_T6.md`).
- **`scripts/web_fetch.py`:** leva a lógica do `scrape.yml` para o contrato do ADR, e acrescenta:
  - allowlist verificada em cada redirect;
  - robots.txt pela RFC 9309;
  - bloqueio de SSRF (privados, loopback, link-local e metadados da cloud);
  - tecto de bytes em streaming e prazo total do pedido;
  - verificação do content-type;
  - conversão pelo adapter do F1 (`HtmlConverter` com `strict=True`, porque sem ele um HTML muito aninhado cai em silêncio para texto, verificado no 0.1.8; no processo filho);
  - proveniência com `final_url`, `http_status` e `content_type`, e o `uri` sem credenciais nem fragmento;
  - saída pelo `write_ingested`. Nunca escreve no Supabase.
- **Testes:** `runner/tests/test_web_fetch.py` (42, servidor HTTP local em thread).
  - Verificação por mutação: sem o prazo total, ou sem a allowlist por redirect, os testes respectivos falham.
  - O teardown do servidor passou de 0,5 s para 0,05 s por teste (suite em 2,8 s).
- **Corrida real:**
  - `example.com`, `python.org` e `wikipedia.org` dão 403 no proxy desta sessão (política de rede do ambiente);
  - no `pypi.org` (acessível), 3 páginas com 200, o título certo e tabelas;
  - o robots.txt real do pypi.org proíbe `/simple/`, e o fetch recusou;
  - um domínio fora da allowlist foi recusado.
  - Evidência em `docs/ops/WEB-FETCH.md` §3.
- **Corrigido durante a corrida:** a mensagem do `robots_disallowed` escondia a causa (dizia só `http_error`). Agora inclui o detalhe, por exemplo `ProxyError: 403`.
- **Apanhado na validação, antes do commit:**
  - a suite com extras falhou num teste, e encontrei um defeito real: o `fetch` reconhecia o erro do conversor pela **classe**, e o `ingest_benchmark` recarregava o `ingest_document`, trocando a classe em `sys.modules`. Agora o `fetch` reconhece o erro pelo `code`, e qualquer outra excepção vira `conversion_failed`; o benchmark reutiliza o módulo já carregado. Há 2 testes de regressão;
  - o semgrep marcou `addr.is_private` e `response.is_redirect` (regra `is-function-without-parentheses`). São propriedades, ou seja, falsos positivos, mas reescrevi sem `nosemgrep`: uma lista explícita de propriedades e os códigos de redirect (301, 302, 303, 307 e 308) à vista. O semgrep com a configuração do CI dá 0 achados.
- **Validação:** sem extras, `pytest` 679 passed e 29 skipped; com MarkItDown e Postgres, 133 passed nos 6 ficheiros de ingest e fetch.
- **Canónico:**
  - o F2 passa de BLOQUEADO a EM CURSO (104 vivos: ABERTO 56, EM CURSO 6, BLOQUEADO 42; recontagem validada);
  - decisões novas P-24 (`scrape.yml`: recomendada A, manter como legado) e P-25 (allowlist por área: recomendada B, `--allow` por chamada até ao 1.º uso real); 23 → 25.

### T6f: fecho do F1, S5 e decisões novas (2026-10-05)
- **T6e fechado:** o PR #109 tem CI verde nas 2 cabeças, com o `test-ingest` a correr com o Postgres.
- **S5 do ADR, que faltava:** `scripts/ingest_benchmark.py`, reprodutível, com um teste que o corre no CI e fixa a estrutura medida.
  - Listas e tabelas ficam a 100% nos 3 formatos.
  - O PDF perde os headings, e por isso o `chunk_markdown`, que corta por H2/H3, não divide um PDF por secções.
  - Nem o PDF nem o DOCX devolvem o título dos metadados.
  - Custo: cerca de 1 s e 150 MiB por documento.
  - Resultados em `docs/ops/INGEST-DOCUMENT.md` §8.
- **Corrigido antes do commit:**
  - o script importava `resource` no topo, e isso partia em Windows, que é a máquina do DEV. Agora a coluna de memória sai `n/d` em Windows;
  - o semgrep local apanhou uma concatenação implícita de f-strings numa lista; a linha da tabela passa a ser montada numa função.
- **Done do F1, no ADR §9:** 3 formatos, E2E pelo T6 existente (provado contra Postgres com pgvector) e path estável.
  - No canónico, o F1 **continua EM CURSO**: só fecha com o merge dos PRs da cadeia (providência 2).
  - A 1.ª ingestão em produção espera pela entrada no MANIFEST, que é decisão do maestro.
- **F1b:** não há documentos reais do domínio no repo, só fixtures sintéticas. Pela regra do prompt (Docling só com benchmark de perda material), o F1b fica **não necessário por agora** no `PENDENCIAS_T6.md`; no canónico continua BLOQUEADO, com o bloqueio exacto.
- **Decisões novas no §10** (A/B/C com recomendada; 20 → 23):
  - **P-21:** F1b; recomendada A (não necessário), que passa a B com PDFs reais;
  - **P-22:** contribuição upstream no MarkItDown; recomendada B (issue primeiro, na conta do DEV);
  - **P-23:** F6 do prompt vs F6 canónico; recomendada A (os 2, sem reabrir a D-EP8).

### T6e: encaixe na pipeline T6 (2026-10-05)
- **T6d fechado:** o PR #108 ficou verde (11 checks) depois da correcção do semgrep; registo e mini-relatório no `PENDENCIAS_T6.md`.
- **Ponto de chamada:**
  - o `ingest_document` é chamado pelo DEV ou pela CLI (`--out-dir`) e grava em `docs/knowledge/ingested/`;
  - o `.md` entra no MANIFEST, e o merge corre o T6 real (`ingest-knowledge` → `ingest_apply.apply_one`).
  - Não se criou nenhuma pipeline nova (ADR §2, regra 2).
- **Código (`scripts/ingest_document.py`):**
  - `write_ingested`: grava o `.md` byte a byte e o `.meta.yaml`, e não sobrepõe ficheiros;
  - `validate_ingested`: regra 3 do ADR (sidecar, campos mínimos, hash);
  - `slugify`;
  - CLI `--out-dir`, `--name` e `--overwrite`.
- **Privacidade:** o `uri` passa a ser relativo ao repo. Um ficheiro de fora do repo fica `external:<nome>`, com o aviso `uri_outside_repo`. Antes, o `.meta.yaml`, que vai para o git, guardaria um caminho da máquina do DEV (por exemplo `C:\Users\…`).
- **Testes:**
  - `test_ingest_pipeline.py` (14): o hash do `.md` é o `sha256_file` do T6, o validador, a guarda do MANIFEST, o chunker real do T6 nos 3 formatos (as linhas de tabela chegam inteiras) e a CLI;
  - `test_ingest_pipeline_rag.py` (4): o caminho completo contra Postgres com pgvector, com as fixtures do `test_rag_canonical`. Provam que o `content_hash` do T6 é o do `source_meta`, que o retrieve devolve o documento com a linha da tabela, que a 2.ª corrida é UNCHANGED, e que sem orçamento dá SKIPPED_QUOTA, sem embeddings nem escrita parcial.
- **CI:** o job `test-ingest` ganha o serviço Postgres com pgvector (como o `test-rag`) e `RAG_TEST_REQUIRED=1`.
- **Não feito, de propósito:** nenhuma entrada no MANIFEST, porque isso escreve em produção no merge e é decisão do maestro.

### T6d: segurança de entrada (2026-10-05)
- **T6c fechado:** o PR #107 tem CI verde nas 2 cabeças (11 checks).
- **Mitigação 3 do ADR §5:** a conversão corre num processo filho (`isolated_converter`).
  - O filho aplica o limite de memória a si próprio antes de carregar o MarkItDown.
  - O resultado volta por ficheiro JSON, por isso o stdout das bibliotecas não interfere.
  - Ao fim do timeout, o filho é morto.
  - Se morrer sem resultado, o erro é `conversion_failed`, com o sinal ou o código de saída, o limite e as últimas linhas do stderr.
- **O limite foi medido, não escolhido a olho** (3 a 5 corridas por valor):
  - o `RLIMIT_AS` não é monótono com o onnxruntime do magika (768 MiB falhava sempre e 512 MiB só às vezes), por isso foi recusado;
  - o `RLIMIT_DATA` foi estável, e o MarkItDown precisa de pelo menos 384 MiB;
  - fica 1 GiB por omissão, e está verificado que trava alocações grandes e acumuladas.
  - Fora de Linux não há limite de memória, e o resultado traz o aviso `memory_limit_unavailable`.
- **Contrato:**
  - códigos novos `timeout` e `memory_limit`, registados no ADR §9;
  - a CLI ganha `--timeout-s` e `--memory-limit-mb`;
  - o JSON de erro da CLI deixa de repetir o código dentro do `message`.
- **Defeitos corrigidos:**
  - um DOCX/XLSX truncado dava `unsupported_format` ("não é DOCX"). Agora dá `conversion_failed` ("ZIP corrompido");
  - com pouca memória, o import do MarkItDown falhava com "o pacote markitdown não está instalado", o que era falso. Agora a mensagem distingue "não instalado", "falta uma dependência" e "não carregou".
- **Testes:** `runner/tests/test_ingest_security.py`, com 22 testes. Os alvos do filho que simulam o abuso (dormir, esgotar memória, `os.abort()`, lixo no stdout) são escritos em `tmp_path`, por isso a maioria corre sem o MarkItDown. O CI corre-os no job `test-ingest`.
  - Sem os extras: 629 passed, 18 skipped. Com os extras e `INGEST_TEST_REQUIRED=1`: 72 passed.
- **Documentação:** `docs/ops/INGEST-DOCUMENT.md` (limites, a medição, códigos de erro, avisos, e o comportamento do MarkItDown por formato).
- **CI do 1.º push: o semgrep falhou.** Reproduzi localmente com a mesma versão (1.179.0) e as regras no mesmo commit, e saíram 4 achados:
  - 2 do T6d: o `globals()[func]` (substituído por uma lista branca de alvos) e o `subprocess.run(cmd)` (falso positivo de auditoria: lista sem shell e só com valores nossos; fica `nosemgrep` com o motivo);
  - 1 do T6b: `import_module` no helper de testes, que passa a ter lista branca e `nosemgrep` com o motivo;
  - 1 do T6a: concatenação implícita de bytes numa lista, que passa a `+` explícito.
  - Depois disto, o semgrep com a configuração do CI e `--error` dá 0 achados em `scripts/`, `runner/` e nos workflows.

### T6c: DOCX e XLSX (2026-10-05)
- **T6b fechado:** o PR #106 tem CI verde nas 2 cabeças, com 11 checks incluindo o `test-ingest`. Registo e mini-relatório no `PENDENCIAS_T6.md`.
- **Fixtures** (`runner/tests/fixtures/ingest/`):
  - `docx/simple_synthetic.docx` (34 652 bytes): heading 1, parágrafo, lista de 3 itens, tabela com cabeçalho;
  - `xlsx/simple_synthetic.xlsx` (5 491 bytes): 2 folhas, texto, números, 1 fórmula e 1 célula vazia.
- **Geradores reprodutíveis** (python-docx 1.2.0 e openpyxl 3.1.5, pins exactos):
  - `reproducible_zip.py` re-empacota o ZIP com datas fixas;
  - o openpyxl reescreve o `dcterms:modified` ao guardar, por isso é corrigido depois de guardar;
  - o teste compara o conteúdo de cada entrada do ZIP, e não os bytes comprimidos, porque a zlib pode variar entre a máquina local e o CI.
- **Achados com o MarkItDown 0.1.8:**
  - DOCX: sem `w:tblHeader` na 1.ª linha, a tabela sai com um cabeçalho vazio e a 1.ª linha como dados. A fixture marca o cabeçalho, e o docstring do gerador explica porquê;
  - DOCX: os headings saem como `#`. No PDF não saem, porque o PDF não tem headings semânticos;
  - no meu código, apanhado pela suite sem extras: os geradores punham `fixtures/ingest/` no `sys.path`, e a pasta `docx/` passava a importar como `docx`, a fazer-se passar pelo python-docx. Agora carregam o helper pelo caminho, e há um teste de regressão;
  - XLSX: uma fórmula sem valor em cache e uma célula vazia saem as 2 como `NaN`, e uma coluna inteira com `NaN` passa a float (300 aparece como `300.0`). O `ingest_document` passa a avisar com `xlsx_nan_cells=<n>`, sem alterar o conteúdo, e há 3 testes de contrato para o aviso.

### Cadeia F1 → F6: arranque e T6b (PDF) (2026-10-05)
- **Pedido do maestro:** prompt único, fase a fase, com o estado sempre gravado ("não deixar só na memória").
- **Ficheiro de estado:** `docs/initiatives/PENDENCIAS_T6.md`, com a estrutura exacta do prompt. O `PENDENCIAS.md` canónico não muda de forma; a linha do F1 aponta para o ficheiro novo.
- **4 conflitos do prompt com regras já decididas, resolvidos e registados no ficheiro de estado:**
  - o PENDENCIAS canónico mantém-se e o estado da cadeia vai para o `_T6`;
  - o PR para o `microsoft/markitdown` fica como decisão do maestro: sem acesso, e é uma acção pública em nome do DEV;
  - o F6 do prompt é diferente do F6 canónico (D-EP8);
  - entre "parar por fase" e a autonomia dada, avanço fase a fase com o critério de saída cumprido.
- **T6b, o que se fez:**
  - fixture `runner/tests/fixtures/ingest/pdf/simple_synthetic.pdf` (1748 bytes, 1 página): título, parágrafo, lista de 3 itens e tabela de 3 colunas com cabeçalho e 2 linhas;
  - gerador `generate_simple_synthetic.py` (fpdf2, pin exacto em `runner/requirements-fixtures.txt`), com bytes iguais em cada corrida; um teste prova que a fixture é a saída do gerador;
  - `runner/tests/test_ingest_fixtures.py`: regras da fixture, reprodutibilidade, `MarkItDown().convert` (API pública) e `ingest_document`, sempre contra o mesmo golden set (as constantes do gerador);
  - `runner/tests/optional_deps.py`: sem as dependências opcionais dá skip em local e erro no CI (`INGEST_TEST_REQUIRED=1`, o mesmo padrão do `RAG_TEST_REQUIRED`). Os smoke do T6a passam a usá-lo;
  - CI: novo job `test-ingest` (MarkItDown real + gerador). O filtro `paths` do workflow passa a incluir `scripts/ingest_document.py`: antes, uma alteração só ao script não corria os testes.
- **Observações para o F1b e o T6e:**
  - o PDF não tem headings semânticos, por isso o título sai como texto simples, sem `#`;
  - o `PdfConverter` não lê o `/Title` dos metadados, por isso o `source_meta.title` vem do nome do ficheiro, com aviso;
  - a tabela com bordas é reconstruída em Markdown.

### T6a: spike MarkItDown, esqueleto do `ingest_document` (2026-10-05)
- **Branch:** `feat/F1-markitdown-spike`, empilhado sobre o #104. O código do F1 só chega à `main` depois da declaração do M1.
- **Contrato** (ADR-INGESTION-PRIMITIVES §2–§4, só `kind = path`): `ingest_document(path) -> {content, source_meta, warnings}`.
- **Ficheiros:**
  - `scripts/ingest_document.py`. Não está ligado ao worker nem ao T6, e não escreve ficheiros; a CLI só imprime JSON. Faz o seguinte:
    - recusa antes do adapter: `unsupported_format`, também quando a assinatura não bate com a extensão; `too_large`; `decompression_limit`, a mitigação 2 do §5, que lê só o directório central do ZIP;
    - normaliza o `content` e calcula o `content_hash` com o mesmo SHA-256 do T6;
    - gera o `source_meta` com o schema mínimo do §4;
  - `runner/requirements-ingest.txt`: `markitdown[docx,pdf,xlsx]>=0.1.4`, à parte do runner, porque puxa o onnxruntime;
  - `runner/tests/test_ingest_document.py`: 26 testes de contrato (correm sempre) e 6 smoke com o MarkItDown real, com documentos sintéticos gerados no teste e nenhum binário no repo. No CI, os 6 smoke ficam em skip documentado.
- **2 achados com o MarkItDown 0.1.8, ambos com teste:**
  - um `.pdf` que é texto sai como texto, sem erro;
  - um PDF que o pdfminer não lê cai no conversor de texto e volta em bruto como "Markdown".
  - Nos 2 casos, o `source_meta` diria `pdf` com conteúdo falso.
  - **Correcção:** só o conversor do formato (`enable_builtins=False` + `register_converter`) e a verificação da assinatura antes de converter.
- **Testes:**
  - sem o `markitdown` (como no CI): `pytest` 600 passed, 7 skipped (574 + 26 novos; 6 skips novos);
  - com o `markitdown` 0.1.8: o ficheiro novo dá 32 passed;
  - `ruff check` limpo.
- **Fica para o T6b:** a mitigação 3 (processo filho com limite de memória do SO), o evento de observabilidade (§3, item 8) e o S2 a S5 do §9.
- **Ingest:** nenhum ficheiro tocado está no MANIFEST. O merge deve dar `chunks=0`.

### Decisão do maestro: F0.6 BLOQUEADO e gate M1 FECHADO (2026-10-05)

`M1 F0 VERDE — F1 código autorizado (decisão do maestro, 2026-10-05: o F0.7b é prova suficiente; o F0.6 fica BLOQUEADO porque o conector do Claude.ai não mostra tools)`

- **Facto (DEV, no Claude.ai):** o conector `agent-network-mcp` mostra "Este conector não possui ferramentas disponíveis."
- **Causa provável:** a protecção da Vercel bloqueia o `tools/list`, e o conector não envia o `x-vercel-protection-bypass`. Não está verificada do lado da Vercel.
- **Porque o F0.7b chega:**
  - prova o mesmo caminho (`/api/mcp` com `Bearer` → `retrieve_knowledge` → `knowledge_chunks`) contra produção;
  - foram 18 casos, todos com a fonte certa, e `provenance_ok` 1.0.
- **Posto de parte por agora:** o bypass como query parameter nas settings do conector, porque guarda o segredo no conector.
- **Registo:**
  - PENDENCIAS: F0.6 ABERTO → BLOQUEADO, com o motivo; o S-003 (teste no conector) também → BLOQUEADO, pelo mesmo motivo; cabeçalho e §5 actualizados; nota na P-19;
  - `L5-F0-REVALIDATION.md` §6.1: tabela preenchida com o veredicto BLOQUEADO, a causa provável e as 2 formas de desbloquear.
- **Contagens:** 104 vivos (ABERTO 58 → 56, BLOQUEADO 41 → 43). Recontagem validada.
- **Atenção (fora do M1):** sem tools no conector, todo o uso do MCP pelo Claude.ai está parado, e não só o F0.6.
- **Próxima micro-tarefa:** T6a no branch `feat/F1-markitdown-spike`, empilhado sobre este.

### F0.7b PASSOU: `l5_eval run` contra o MCP de produção (2026-10-05, DEV)
- **Run do DEV (3.ª tentativa):** venv com `mcp` 1.30.0 (guarda do #102) e `VERCEL_PROTECTION_BYPASS` definida (cabeçalho do #103).
- **Resultado** (`kb=security`, fonte `docs/knowledge/security-agents-stack.md`, k=4, 18 casos):

| Métrica | Valor |
|---|---|
| `chunk_hit@1` / `@3` / `@4` | 0.611 (11/18) · 0.889 (16/18) · 0.944 (17/18) |
| `source_hit@4` | 1.0 |
| `mrr_chunk` | 0.736 |
| `no_hits` | 0 |
| `provenance_ok` | 1.0 |

- **Veredicto:** PASSOU. Cumpre as 3 opções da P-19 (`chunk_hit@4 > 0`; ≥ 15 dos 18; `provenance_ok = 1.0`).
- **O que o run também prova:**
  - o caminho completo funciona com o código de produção (`880d492`): auth Bearer, protecção da Vercel com bypass, `retrieve_knowledge` e o pack `security` ingerido;
  - a correcção do F0.4 chegou à produção (antes, `chunk_hit@4` era 0);
  - 1 caso não tem o excerto esperado no top 4, mas a fonte está certa (`source_hit@4` = 1.0). O ID do caso não foi colado, por isso fica por identificar.
- **Registo:**
  - `L5-F0-REVALIDATION.md` §6.2: tabela preenchida, veredicto e o JSON do resumo;
  - PENDENCIAS: F0.7b passa para o §7 como FECHADO; sai do §5 (DEV) e do §6 (Média); nota na P-19.
- **Contagens:** 105 → 104 vivos (ABERTO 58, EM CURSO 5, BLOQUEADO 41); §7 104 → 105 linhas (84 FECHADO). Recontagem validada pelo script.
- **Ingest:** nenhum dos 3 ficheiros está no MANIFEST de `scripts/ingest_delta.py`, por isso o merge dá `chunks=0`.

**T5, reavaliação do gate M1:**

`M1 INCOMPLETO — F1 bloqueado; faltam: F0.6 (evidência em docs/ops/L5-F0-REVALIDATION.md §6.1), P-19 por registar (o 1.º run do F0.7b cumpre qualquer opção)`

| Critério do M1 | Estado | Evidência |
|---|---|---|
| F0.3 (t6 parada) | FEITO | PENDENCIAS §7; #95 |
| F0.1 e R-002 | FEITO | PENDENCIAS §7; #97 |
| F0.7b (`l5_eval run` contra o MCP real) | **FEITO** | §6.2; este PR |
| F0.6 (conector MCP com a fonte citada) | **Falta** (DEV) | Molde em §6.1, campos NÃO VERIFICADO |
| Limiar do F0.7b | Falta registar (maestro) | P-19; o resultado cumpre as 3 opções |
| R-005 | Documentado | BLOQUEADO (F3); a causa é a P-20, pendente |

O T6 (F1 MarkItDown) **não arrancou**, como pede o gate.

- **Próxima micro-tarefa:** o DEV faz o F0.6 no Claude.ai. Se o conector receber um 400 da Vercel, a causa é a mesma protecção, e fica para decisão (A/B/C) como expor o MCP ao conector.

### F0.7b, 2.ª tentativa: 400 da Vercel "Standard Protection" (2026-10-05, ~14:10 UTC)
- **Diagnóstico anterior (sem código):**
  - o protocolo completa de ponta a ponta com o código de produção (`880d492`) a correr localmente;
  - os logs de produção da última hora só tinham 401 (`POST`, `GET` e `HEAD` às 13:50:51–53 UTC) e nenhum 400.
- **Causa (DEV):** a Vercel tem a **Standard Protection** activa (plano Hobby, não se desliga) e bloqueia os pedidos com 400 antes da função. Isso explica a falta de corpo do servidor e de linhas nos logs de runtime.
- **Correcção (PR do branch `fix/F0-7b-vercel-bypass`):**
  - `mcp_knowledge.py` (`_request_headers`): se a env `VERCEL_PROTECTION_BYPASS` estiver definida e não vazia, envia `x-vercel-protection-bypass` em todos os pedidos; senão, nada muda;
  - 4 testes: ausente, vazia, presente, e o segredo nunca numa mensagem de erro;
  - **verificação real** contra um servidor MCP local (`mcp` 1.30.0) que regista os cabeçalhos: o bypass foi nos 4 pedidos da sessão (`initialize`, notificação, `tools/call`, `tools/list`) e em nenhum sem a variável;
  - `L5-F0-REVALIDATION.md` §6.2: o segredo é lido sem ficar no histórico e apagado no fim; onde se cria e como se roda.
- **Atenção (F0.6):** o conector do Claude.ai não envia este cabeçalho; se a protecção o bloquear, o F0.6 falha pela mesma razão. Fica registado no §6.2.
- **Testes:** `pytest` 574 passed (569 + 5 casos novos); `ruff` limpo.
- **Próxima micro-tarefa:** o DEV repete o F0.7b com a env `VERCEL_PROTECTION_BYPASS` definida.

### F0.7b, 1.ª tentativa do DEV: `not enough values to unpack` (2026-10-05, ~13:30 UTC)
- **Erro do DEV:** `ValueError: not enough values to unpack (expected 3, got 2)` em `runner/plan_runner/mcp_knowledge.py:138`, com Python 3.14 global.
- **Causa:** o ambiente tinha o pacote `mcp` da linha **2.x**, e o `runner/requirements.txt` fixa `mcp==1.30.0`. Nada no repo puxa a 2.x.
  - Na 1.30.0, o `streamable_http_client` devolve `(read_stream, write_stream, get_session_id)`.
  - Na 2.x (2.0.0 a 2026-07-28; 2.3.0 a 2026-10-02), devolve só `(read_stream, write_stream)`.
  - A 2.x mudou mais 2 coisas, e por isso aceitar 2 ou 3 valores não chegava:
    - o `http_client` passa a ser `httpx2.AsyncClient`;
    - o `CallToolResult` usa `is_error` em vez de `isError`.
- **Reproduzido aqui:** o código da `main` com a `mcp` 2.3.0 dá o mesmo erro.
  - Com a 1.30.0, o cliente chega à rede.
  - O `mcp` 1.30.0 suporta Python 3.10 a 3.14 (classifiers do PyPI; há wheels `cp314` do `pydantic-core` para Windows).
- **Correcção (PR do branch `fix/F0-7b-mcp-versao`):**
  - guarda de versão em `mcp_knowledge.py`: com outra linha que não a 1.x, pára antes da rede, com uma mensagem que diz a versão e o comando a correr;
  - 3 testes novos: o guarda rejeita a 2.x, deixa passar a 1.x, e um canário confirma que o `mcp` instalado é o do `requirements.txt` (os 3 falhavam sem a alteração);
  - checklist do §6.2 com o venv (`pip install -r requirements.txt` e a confirmação `1.30.0`);
  - novo **W-010**: migração para a 2.x, com um teste contra um servidor MCP real local.
- **Testes:** `pytest` 569 passed (566 + 3); `ruff` limpo.
- **Contagens:** 104 → 105 vivos (W-010).
- **Próxima micro-tarefa:** o DEV repete o F0.7b no venv (checklist do §6.2).

### T5: declaração do gate M1 (2026-10-05, ~12:55 UTC)

`M1 INCOMPLETO — F1 bloqueado; faltam: F0.6 (evidência em docs/ops/L5-F0-REVALIDATION.md §6.1), F0.7b (evidência em §6.2), P-19 (limiar do F0.7b, PENDENCIAS §10)`

| Critério do M1 | Estado | Evidência |
|---|---|---|
| F0.3 (t6 parada) | FEITO | PENDENCIAS §7; #95 |
| F0.1 e R-002 | FEITO | PENDENCIAS §7; #97 |
| F0.6 (conector MCP com a fonte citada) | **Falta** (DEV) | Molde em §6.1, campos NÃO VERIFICADO |
| F0.7b (`l5_eval run` contra o MCP real) | **Falta** (DEV) | Molde em §6.2, campos NÃO VERIFICADO |
| Limiar do F0.7b | **Falta** (maestro) | P-19 pendente |
| R-005 | Documentado | BLOQUEADO (F3); a causa é a P-20, pendente |

O T6 (F1 MarkItDown) **não arrancou**, como pede o gate.

## Relatório sessão 2026-10-05 (campanha "gate M1")
- **Repo, branch e commit de partida:** NAS `main` `098034e`; branch `docs/m1-moldes-f0`. MCP `main` `880d492` (não tocado).
- **PRs abertos vistos:** 0 no NAS e 0 no MCP. O #100 entrou às 12:06 UTC; a corrida #183 do ingest deu `chunks=0 unchanged=39`.
- **Micro-tarefas:**
  - T0 (arranque);
  - T1: o #100 já tinha entrado, por isso o S1 está feito sem trabalho;
  - T2 e T3 (moldes do F0.6 e do F0.7b, comando verificado);
  - T4 (S20 e R-005);
  - T5 (M1 = NÃO).
- **IDs do PENDENCIAS alterados:**
  - F0.6 e F0.7b: evidência aponta para os moldes;
  - S20: caminho e prazo proposto 2026-10-12;
  - R-005: nota da P-20;
  - novas P-19 e P-20 (§10). Contagens sem mudança: 104 vivos.
- **M1:** NÃO. Faltam o F0.6, o F0.7b e a P-19.
- **F1:** não iniciado (bloqueado pelo M1).
- **Bloqueios do DEV:**
  - correr o F0.6 e o F0.7b (checklist PowerShell na entrada T2/T3) e colar o output no §6;
  - decidir a P-19 e a P-20;
  - confirmar ou mudar o prazo do S20 (2026-10-12).
- **Próxima micro-tarefa exacta:** quando o output do F0.6 e do F0.7b estiver no §6, repetir o T5. Com o M1 verde, segue o T6a (contrato + pin `markitdown>=0.1.4` + esqueleto, branch `feat/F1-markitdown-spike`).
- **git status:** limpo depois do push deste branch.

### T4: S20 e R-005 no PENDENCIAS (2026-10-05, ~12:45 UTC)
- **S20** deixa de estar "ABERTO sem data nem caminho". Opções:
  - **A:** o DEV corrige já por SSH. Caminho: `ANM:CONFIGURACAO_VM_BRIDGE_WORKER.md`, passo 4: pôr a `SUPABASE_SERVICE_ROLE_KEY` actual onde o `pm2` a lê, depois `pm2 restart bridge-worker --update-env` e `pm2 save`.
  - **B (recomendada):** prazo até **2026-10-12**. Se nessa data não estiver corrigido, o DEV decide entre uma data nova e tirar a "execução remota" do README do MCP.
  - **C:** ABERTO sem data. Rejeitada pelo maestro.
  - Fica registado como **prazo proposto, a confirmar pelo DEV**. O estado continua ABERTO e NÃO VERIFICADO (não há SSH nesta sessão).
- **R-005:** continua BLOQUEADO (F3), com os factos dos SELECTs (#97). A correcção da causa estava só no chat; passa a **P-20** no §10 (recomendada B: esperar pelo F3).
- **P-19 (nova):** limiar do F0.7b para o gate. Recomendada A: `provenance_ok` = 1.0 e `source_hit@4` ≥ 0.8 (pelo menos 15 dos 18 casos).
- **Contagens:** sem mudança (104 vivos). §10 com 20 decisões; pendentes P-11, P-16, P-17, P-19 e P-20.
- **Próxima micro-tarefa:** T5 (declaração do M1).

### T2 e T3: moldes de evidência do F0.6 e do F0.7b (2026-10-05, ~12:35 UTC)
- **Feito:** `docs/ops/L5-F0-REVALIDATION.md` §6 (6.1 F0.6, 6.2 F0.7b). Todos os campos estão em NÃO VERIFICADO até o DEV colar o output.
- **Achado (F0.6):** nenhum dos 33 agentes do MCP tem `agent_id` = `security`.
  - Uma pergunta por `ask_agent_network` não chega ao pack de security.
  - O teste tem de usar `retrieve_knowledge` com `kb` = `security` (`ANM:app/api/mcp/route.js`, parâmetros `kb`, `query`, `top_k`).
  - Pergunta sugerida: o caso `sec-01` do golden set; resultado esperado: fonte `docs/knowledge/security-agents-stack.md`.
- **Comando do F0.7b verificado** (`runner/plan_runner/l5_eval.py`):
  - `l5_eval validate` → `18 casos; 0 erros`;
  - `l5_eval run` sem chave → falha logo, sem medir;
  - o `MCP_URL` é a base (`https://agent-network-mcp-oddn.vercel.app`), e o código acrescenta `/api/mcp` (`mcp_knowledge.py:73-74`).
- **Checklist do DEV (PowerShell, em `runner\`, venv activo):**
  1. `$env:MCP_URL = "https://agent-network-mcp-oddn.vercel.app"`
  2. `$env:MCP_API_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'MCP_API_KEY' -AsSecureString)).Password` (a chave não fica no histórico)
  3. `python -m plan_runner.l5_eval run --out "$env:TEMP\f0-7b-report.json"`
  4. `Remove-Item Env:MCP_API_KEY`
  5. Colar o `summary` e os casos `--` na §6.2; fazer a pergunta do F0.6 no Claude.ai e colar na §6.1.
- **Achado (critério):** o F0.7b não tinha limiar para o gate. Abro a **P-19** (A/B/C) no PENDENCIAS §10. Não fecho nada sem ela.
- **Próxima micro-tarefa:** T4 (S20 e R-005 no PENDENCIAS).

### T0: arranque da campanha "gate M1" (2026-10-05, ~12:20 UTC)
- **`main`:** NAS `098034e` (#100 merged a 2026-10-05 12:06 UTC); MCP `880d492`.
- **PRs abertos:** 0 no NAS, 0 no MCP.
- **Slots da fila:**
  - S1 (#100): **feito**, merged;
  - S2 (F0.6) e S3 (F0.7b): ABERTO, DEV;
  - S4: R-005 BLOQUEADO (F3); S20 ABERTO, **sem data**;
  - S5 (F1): EM CURSO só no ADR; o spike está bloqueado pelo M1.
- **M1:** incompleto (F0.6 e F0.7b sem evidência no git).
- **Próxima micro-tarefa:** T2 (molde de evidência do F0.6).

### Portfólio para recrutadores (2026-10-05)
**Pedido do maestro:** confirmar e expandir o `docs/PORTFOLIO.md`, com um bloco "For recruiters / visitors" no README, só números verificáveis e sem duplicar o README.

**Estado encontrado:**
- o `docs/PORTFOLIO.md` já existia (#98);
- o README tinha uma linha "Start here" com os mesmos links;
- o portfólio repetia o Quickstart e 3 das 4 histórias do README.

**Feito:**
- **PORTFOLIO, expandido para complementar o README:**
  - títulos bilingues;
  - tabela "Números e fontes": cada número com o documento onde se confirma;
  - linha do tempo de 10 marcos, com as datas de merge tiradas da API;
  - guia do código em 6 passos;
  - 4 histórias novas (o README fica com as suas 4);
  - o Quickstart e as histórias repetidas passam a links.
- **Números:**
  - 13 130 → 12 998 → 10 136 tokens (B1 e B1-bis-R2, `WORKER-EXTERNAL.md`);
  - 11 760 tokens (C-1, `COUNCIL.md`);
  - 590+ testes, 75+ PRs, 38 agentes, 72 skills, 14 planos, `chunks=0 unchanged=39`.
  - O "SEO ~13k" do pedido é o 1.º run real (13 130), e está no portfólio com a fonte.
- **"Supabase para `council_*`":** escrito como está, ou seja, o schema aceita as chamadas dos conselhos (C-2), mas ainda não houve um run real de conselho a gravar lá (F5).
- **README:** a linha "Start here" passa a bloco "For recruiters / visitors (60 seconds)", com os mesmos destinos. Links e âncoras verificados nos 2 ficheiros (0 partidos).
- **PENDENCIAS:** H-003, W-009, H-005 e H-006 → FECHADO (#99 e MCP #18 merged).
  - A corrida #182 do `ingest-knowledge`, a 1.ª com os pins novos, deu `success`, `chunks=0` e não mostrou o aviso de Node 20.
  - Contagens: 108 → **104** vivos (ABERTO 58, EM CURSO 5, BLOQUEADO 41); histórico 100 → 104.

### "Resolve o que for possível" (maestro, 2026-10-05)
**Feito (2 PRs):**
- **H-003, re-pin das Actions para Node 24.**
  - Passou a ser possível: o `git ls-remote` lê as tags dos repos `actions/*`, que são públicos.
  - Regra: em cada Action, a última versão da 1.ª linha principal com `using: node24`, lida no `action.yml` da tag, e não assumida.
  - Armadilhas evitadas:
    - `upload-artifact` v3.2.2 (seria downgrade, e o serviço v3 foi desligado) e v5 (ainda Node 20). Fica a v6.0.0.
    - `setup-node` v5 activa a cache pelo `packageManager`: com o `pnpm` instalado antes, funciona.
  - NAS: 23 pins. MCP: `checkout` e `cache` pinados por SHA (PR MCP #18).
  - O `continue-on-error` do Codecov fica como rede: a v5 é composite.
- **W-009:** o exemplo de budget do `ORCHESTRATOR.md` fica só com o `max_steps`, e uma nota explica o `max_retrieve_calls`.
- **W-008 → FECHADO, falso positivo meu.** O `piloto-netos` é do formato do plan-execute e valida contra o seu schema (0 erros; `test_plan_schema_json.py`).
- **R-004 → FECHADO.** O MCP #15 tinha entrado a 2026-10-03. A linha estava desactualizada, como o C-2.
- **S-004:** o MCP #17 entrou. Só faltam os alertas da aba Security, e a API do Dependabot dá 403 a esta sessão (DEV).
- **H-005 e H-006 (PR MCP #18):**
  - README do MCP sem links mortos nem TODO, com 33 agentes, o repo irmão e uma nota honesta sobre o S20;
  - `LICENSE` MIT;
  - `diagnostico-vm.txt` → `docs/ops/`;
  - `docs/STATUS.md` corrigido.
  - Domínio de produção confirmado na Vercel: `agent-network-mcp-oddn.vercel.app`. O Website no About do repo está errado (UI).
- **GIF do quickstart:** `docs/assets/quickstart-demo.gif`, 59 KB, gerado a partir da saída real de um run stub (`run_66a9cbadca`; capturada para ficheiros, não escrita à mão). Está no README e no PORTFOLIO. O `pilots/demo` foi apagado a seguir.

**Não é possível nesta sessão:**
- Topics, Description e Website do About, e bio e pins do perfil (o proxy dá 403);
- alertas do Dependabot (403);
- os itens do gate F0 (F0.6, F0.7b);
- S20 (SSH);
- os itens bloqueados por decisão (F1, F1b, F2, F4, AU-22b, H-002, EX-B7, R-005).

**Contagens:** 110 → **108** vivos (ABERTO 58, EM CURSO 9, BLOQUEADO 41); histórico 98 → 100.

### Vitrine para recrutadores (2026-10-05)
O maestro colou um plano de textos para recrutadores: perfil, About, `PORTFOLIO.md`, bloco no README e LinkedIn. Antes de escrever, confrontei-o com o repo.

**Ajustes ao plano:**
- **O `docs/PORTFOLIO.md` já existia:** era o portfólio de marketing, de antes do `plan_runner`. Não o apaguei: passou a `docs/PORTFOLIO-MARKETING.md` (`git mv`), com uma nota no topo e os 4 links actualizados (README, ONE-PAGER, CONCLUSAO).
- **O `docs/PORTFOLIO.md` novo é da plataforma:** abre com um resumo em inglês de 60 segundos (o recrutador que não lê português fica-se pelo topo) e segue em português.
- **Só números verificados:**
  - 590+ testes (566 + 34 lentos);
  - 75+ PRs com merge (76 no NAS e 11 no MCP);
  - 10 136 tokens no SEO e 11 760 numa ronda de conselho;
  - −22% (#45, #55) e `chunks=0 unchanged=39` (#64);
  - 38 agentes, 72 skills e 14 planos.
- **Corrigido do plano colado:**
  - "local-first": o motor corre local, mas o L4, o L5 e o MCP dependem do Supabase, do Gemini e da Vercel;
  - "security pipeline" como provado: está testado em stub, e o run real é o F5;
  - "Supabase ledger": é do MCP; o do runner é local (W-004).
- **README:** linha "Start here" (Portfolio, Quickstart, MCP, Open work); PRs 70+ → 75+.

**Encontrado e registado (H-006, novo):** defeitos no README do `agent-network-mcp`, que é público:
- links mortos no rodapé;
- uma nota de TODO à vista e um `docs/DEPLOY.md` que não existe;
- "33" e "32 agentes" no mesmo texto;
- 2 URLs de produção diferentes;
- "execução remota" anunciada com o S20 aberto;
- sem `LICENSE`;
- `diagnostico-vm.txt` na raiz (sem segredos).

O merge no MCP faz redeploy na Vercel, por isso fica para decisão do maestro.

**Só na UI do GitHub (maestro):** Topics nos 2 repos (estão vazios); Description do MCP (está em português e desactualizada); bio; repos fixados. A Description do NAS já está feita.

**Contagens:** 109 → 110 vivos (ABERTO 63, EM CURSO 6, BLOQUEADO 41).

### 2 SELECTs do F0 (2.ª ronda, maestro, 2026-10-05)
**Resultados (colados pelo maestro):**
1. **F0.1b com `WHERE project = 'network-agents-setup'`:**
   - lista completa das fontes do projecto;
   - `security-agents-stack.md` com 20 chunks;
   - ~8 ficheiros com contagens altas, re-embedados em todas as corridas até ao #64;
   - ~28 ficheiros com 1–4 chunks, que ficaram iguais desde a 1.ª ingestão.
2. **`SELECT kb, count(*) … WHERE project IS NULL GROUP BY kb`:** marketing = 201.

**O que fecha:**
- **F0.1 → FECHADO.** O total `projecto` não veio no resultado colado.
  - Esperado: 163 (121 do J3 + 42 da corrida #156).
  - Fica uma confirmação opcional: `SELECT project, count(*) … GROUP BY project`.
- **R-002 → FECHADO.** Os 28 ficheiros estão na tabela. Batem com o V38: estavam iguais ao repo e a corrida incremental deu-os `UNCHANGED`.
- **AU-22 → FECHADO.** O #96 entrou na `main` (`9531ec3`) durante esta ronda (providência 2).
- **R-005 → actualizado.** Passa a cobrir as 201 linhas do MCP, com severidade **Alta** (decisão do maestro) e bloqueio no F3.
  - Causa confirmada: `DEFAULT 'marketing'` (`scripts/rag_schema.sql:51`), e o insert do MCP não define o `kb`.
  - Coerência: 201 = 322 − 121, ou seja, o MCP não ingeriu nada desde 2026-10-03.
  - Nem todas estão erradas: as fontes de marketing estão certas por acaso. O trabalho é reclassificar as que não são de marketing.

**`--max-chunks 150`:** registei como nota no F0.4, mas com a leitura corrigida.
- Nas corridas incrementais, o valor por omissão (50) chega: as #174–#178 usaram 0/50 e nenhuma deu `SKIPPED_QUOTA`. Não há ficheiros de fora para recuperar.
- Só uma re-ingestão total (`--force`) precisa de um orçamento ≥ ao total do projecto (163 esperado). Aí, 150 não chega.

**Contagens:**
- antes: 112 vivos (ABERTO 62, EM CURSO 8, BLOQUEADO 42);
- depois: **109** (ABERTO 62, EM CURSO 6, BLOQUEADO 41);
- histórico: 95 → 98 (77 FECHADO, 21 OBSOLETO).

**Gate F0:** faltam o F0.6 e o F0.7b. O F0.12 (apagar a t6) é opcional e não bloqueia o gate.

### AU-22: `on_fail` e `max_replans` removidos (2.ª metade da P-10, 2026-10-05)
- **Fila activa aprovada pelo maestro:** A + B em paralelo. O maestro faz os SELECTs, o F0.6 e o F0.7b; eu faço o AU-22. A opção C (H-01 parte 1) fica para depois do gate F0. O #95 entrou (`c15a6d8`).
- **Feito:**
  - `plan.schema.json`: sem `steps[].on_fail` nem `budget.max_replans`; um `$comment` regista a decisão (P-10 = A; fora até ao F3). A `description` do `done_when` já não diz "ignorado".
  - 13 planos de `docs/orchestration/`: 48 linhas retiradas.
  - `models.py`: sem `Step.on_fail` nem `Plan.budget_max_replans` (nada os lia).
  - Um plano antigo que ainda os declare corre na mesma e fica no evento `plan_fields_ignored`. Só falha o `plan_schema`.
- **Porque não muda o comportamento:**
  - um passo que falha já parava o run em `failed` (`engine.py:290-291`);
  - o prompt do worker só lê `objective`, `audience` e `task` (`external_worker.py:452-455`), por isso os tokens medidos não mudam.
- **Testes:**
  - 4 novos falham sem a alteração (os 2 casos do schema, o guarda "nenhum plano do repo os declara" e o modelo sem os campos); o 5.º (plano antigo continua a correr) passa nas duas versões, como devia;
  - o `test_planos_reais_declaram_campos_ignorados` (premissa antiga) foi substituído pelo guarda;
  - totais: `pytest` 566 passed, `-m slow` 34 passed, `ruff` limpo, E7 válido, `plan_schema` 14 planos sem erros;
  - quickstart do README: `paused_human_gate` → `approve` → `done`.
- **Não mudei, e registei:**
  - os 6 prompts de agentes com "Falha → `on_fail`", para não mexer na base medida do B1-bis → B1-bis-C;
  - o `max_retrieve_calls` do exemplo de budget do `ORCHESTRATOR.md`, que não está no schema → W-009 (novo);
  - o formato antigo do plan-execute (`piloto-netos`) → W-008.
- **Contagens:** 111 → 112 vivos (ABERTO 62, EM CURSO 8, BLOQUEADO 42). O AU-22 passa a EM CURSO e entra o W-009.

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
| NAS (PR do branch) | `docs/f3c-design-repo-files` | F3c-DESIGN-1 (opção A), W-011, R-006, revisão do estado contra o EXECUTION-PLAN | Aberto |

Já com merge: NAS #63–#121 (o #104 entrou antes do commit `63719de`, que chegou à `main` pelo #105; #106–#109 a 2026-10-05 17:39–17:40 UTC; #110–#112 a 2026-10-05 19:09–19:22 UTC; #113–#115 a 2026-10-06 16:32–16:35 UTC; #116–#118 a 2026-10-06 18:41–18:57 UTC; #119–#121 a 2026-10-06 21:22–21:24 UTC); MCP #10–#19 (o #19 a 2026-10-05 22:06 UTC).

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
1. **Maestro:**
   - merge do PR do branch `docs/f3c-design-repo-files`;
   - decidir a **P-37** (AU-20; recomendada B: executor mínimo em Python) e a **P-38** (maturidade; recomendada B: derivada da evidência);
   - confirmar as propostas P-21, P-22, P-24 e P-25.
2. **DEV:**
   - F3b-VAL-1 (os 2 sidecars com as datas reais);
   - F0.6 (expor o MCP ao conector);
   - quando quiser, o F3b-AUTH-1 (SQL da v3 + flag) e o F5-ROUTE-1 (run a partir do `route`);
   - S20 até 2026-10-12.
3. **Claude, por esta ordem, sem tocar em produção:**
   - **F3-ART-1:** proveniência no artefacto, com `uri`, estado e validade no bloco de conhecimento e as fontes no `result.json`;
   - **a capability do F2:** um registo e um plano que usem o `fetch`;
   - depois da P-37, o **AU-20**, e da P-38, o **F4-MAT-1**.
