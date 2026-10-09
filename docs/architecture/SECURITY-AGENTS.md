# Security agents — pipeline defensivo + Capability First

## Pipeline (área `security`)

```text
security.triage → meta.security-auditor → security.reporter → HITL
```

| Agente | id | action | Ficheiro |
|--------|-----|--------|----------|
| Triage | `security.triage` | `security_triage` | `agents/security/security_triage.agent.md` |
| Auditor | `meta.security-auditor` | `security_audit` | `agents/meta/security_auditor.agent.md` |
| Reporter | `security.reporter` | `security_report` | `agents/security/security_report.agent.md` |

Registo: `config/areas.yaml` → área `security` (`hitl: required`, `max_tokens: 40000`).  
Cyber ≡ security (sem área separada).

## S34 — `vertical` nos planos

O executor resolve agentes com `vertical` do step (omissão = `marketing`).  
Planos security **devem** declarar:

- `vertical: security` em triage e report
- `vertical: meta` no audit (`meta.security-auditor`)

Ver `docs/orchestration/security/templates/examples/security-audit-demo.plan.yaml`.

## Capability First (não 8 agentes)

As capabilities vivem em `config/security-capabilities.yaml`.  
**Não** se cria um agente permanente por capability.

| Capability | Executor v1 | Nível max | status |
|------------|-------------|-----------|--------|
| triage | `security.triage` | READ | implemented |
| defensive_audit | `meta.security-auditor` | READ | implemented |
| security_report | `security.reporter` | READ / PREPARE | implemented |
| secrets_hygiene | auditor + CI (gitleaks) | READ | partial |
| sast | CI (semgrep + CodeQL + bandit) | READ | partial |
| workflow_security | CI (zizmor + actionlint) | READ | partial |
| supply_chain | CI (pip-audit) + OSV/Trivy guidance | READ | partial |
| mcp_surface | auditor (skill security-audit) | READ | partial |
| hardening_recommend | reporter → engenharia | PREPARE only | partial |
| agent_redteam_lab | CI/lab isolado (PyRIT/DeepTeam) | lab only | deferred |
| external_pentest_lab | Strix (CI/lab manual, repos próprios) | lab only | deferred (P-47 = A, piloto) |
| llm_redteam_lab | CI/lab manual (Garak/promptfoo) | lab only | deferred (P-48 = A) |

## READ / PREPARE / ACT

| Nível | Agentes security |
|-------|------------------|
| READ | Sim |
| PREPARE | Sim (relatório, checklist, plano de patch) |
| ACT (write prod, exploit, rotate live) | **Não** — só engenharia/ops após HITL |

## Conselho (deliberação)

`config/councils.yaml` → painel `security`: chairman `meta.chairman`, member **required** `meta.security-auditor`.  
Para decisões estruturais (threat model, política de segredos), não para cada triage diário.

## Validação automática (E7)

`python -m plan_runner.areas` (no CI, job `test`) valida o `config/security-capabilities.yaml` contra os agentes, as skills e a área (`runner/plan_runner/capabilities.py`):
- `policy.offensive` e `policy.act_in_production` só aceitam `forbidden`; `policy.hitl` tem de ser `required`, porque a área tem `hitl: required`;
- o nível `act` é recusado; `lab` só em capabilities `deferred` (fora do runner de produção);

**Strix (`external_pentest_lab`, P-47 = A):** pentester ofensivo de IA (usestrix/strix, Apache-2.0), só em `.github/workflows/strix-lab.yml` (manual, nunca bloqueia, contra repos próprios). Fica `deferred`/`lab`: fora do runner e de qualquer plano. A política da área não muda. Piloto e regras em `docs/ops/STRIX-LAB.md`.
- `implemented`/`partial`: o agente existe, está em agents[] da área `security`, tem o mesmo `action:` da capability, e a skill existe com o mesmo `action:`;
- qualquer `skill:` declarado por um agente tem de existir.

`python -m plan_runner.areas --inventory` lista, sem falhar o CI: agentes sem skill, skills sem agente, agentes que carregam o pack Claude e skills partilhadas.

## Routing (router D2)

- As keywords da área (`threat model`, `superficie de ataque`, `security triage`, `hardening`, `pentest`…) mandam o pedido para a área `security`; o LLM do router escolhe entre os 3 agentes.
- **`threat model` / `modelo de ameacas` também são keywords de escalada do conselho `security`** (`config/councils.yaml`). Um pedido com elas vai para o **conselho**, não para o pipeline. Regra de uso: **1 conselho ≈ 1 SEO** (`docs/ops/COUNCIL.md`), por isso só para decisões estruturais.
- Um pedido ofensivo ("pentest", "atacar") cai na área: a triagem regista `out_of_scope: ataque activo proibido` e não sugere exploits.

## Quando usar cada skill de segurança

| Skill | Tamanho | Onde | Quando |
|---|---:|---|---|
| `skills/security/triage` | ~1,5 KB | runner (step `security_triage`) | Classificar o pedido: superfícies, severidade, se precisa de audit completo |
| `skills/meta/security-audit` | ~5,5 KB | runner (step `security_audit`, `meta.security-auditor`) | Auditoria defensiva OWASP LLM 2026 / NIST / ATLAS / MAESTRO |
| `skills/security/reporter` | ~1,7 KB | runner (step `security_report`) | Consolidar triagem + audit num relatório com próximos passos |
| `skills/claude/security-and-hardening` | ~24 KB | **pack Claude** (sessões de engenharia / harness) | Hardening ao **escrever** código (input não confiável, auth, dados pessoais). **Não** entra nos steps do runner: nenhum agente a declara, e o tamanho (24 KB) custaria ~6–7k tokens de entrada por passo, pelos 3,3–3,5 caracteres por token medidos no B1 (lição B1-bis) |

Não se fundem sem decisão explícita: uma audita (READ), a outra guia a implementação (ACT, fora desta área).

## Limites (verificados a 2026-10-03)

- **Em `--mode external`, o auditor vê só os ficheiros que o passo declara em `repo_files` (SEC-1, implementado a 2026-10-03).** Sem a flag `PLAN_RUNNER_TOOLS=1` (omissão), o worker continua sem tools: `tools_allowed: [read_repo_file]` é declarativo e o prompt diz "Nao tens tools neste passo". Com a flag, `read_repo_file` corre pelas mesmas regras do SEC-1 (AU-20, `runner/plan_runner/tool_executor.py`); o `retrieve_knowledge` só pesquisa os kb permitidos ao passo; uma tool de nível `act` nunca corre sem aprovação humana, pedida no HITL chamada a chamada (o run pára em `paused_human_gate`). O `knowledge_refs` do plano continua sem ser lido (AU-22; AUDIT-2 Y9).
  - **O que mudou:** o passo `audit` do plano demo declara 5 ficheiros (dependências, CI e política de capabilities). Com o Gemini falso, o prompt do auditor passou de **641 para 11 436 caracteres** (10 425 bytes de ficheiros). A triagem e o relatório não recebem ficheiros.
  - **Consequência:** a auditoria cobre esses ficheiros. O resto do repo continua fora, e a skill e o grounding obrigam a marcá-lo como lacuna.
  - `tests/test_security_pipeline.py` fixa este comportamento, e `tests/test_repo_files.py` (36 testes) cobre as regras.
  - **SEC-1: decidido A (maestro, 2026-10-03) e implementado.** Regras:

| Regra | Valor | Onde |
|---|---|---|
| Activação | **opt-in por passo**: `repo_files: [path, ...]` no passo do plano. Sem o campo, o prompt é igual ao de antes, nos dois modos (`opt`/`legacy`) | `runner/plan_runner/external_worker.py` (`build_prompt_ctx`) |
| Acesso | **só leitura**; o worker lê e injecta o texto no fim do prompt do utilizador, na secção "Ficheiros do repo (so leitura)", marcada como dados e não instruções | `runner/plan_runner/repo_files.py` |
| Paths | explícitos e relativos à raiz do repo; recusados: absolutos, `..`, globs, directórios, e symlinks que saiam do repo | idem |
| Exclusões fixas | `.env*`, `*.pem`, `*.key`, `secrets/`, `.git/`, `node_modules/` (decisão do maestro), mais `*.p12`, `*.pfx`, `*.keystore`, `*.jks`, `id_rsa*`, `id_ecdsa*`, `id_ed25519*`, `id_dsa*`, `.npmrc`, `.pypirc`, `.netrc` e `credentials*`. Valem também no **destino** de um symlink. Comparação sem maiúsculas | `DENY_NAME_PATTERNS`, `DENY_DIRS` |
| Limite | **50 KB no total** por passo (`MAX_TOTAL_BYTES`). O ficheiro que passa o limite é cortado, com marcador, e os seguintes ficam de fora (`over_limit`) | idem |
| Binários | ficam de fora (`binary`) | idem |
| Rastreio | `result.json → meta.context.repo_files`: por entrada, `status` (`included`, `truncated`, `excluded`, `invalid`, `missing`, `over_limit`, `binary`), bytes e motivo. **Nunca** o conteúdo de um excluído | idem |

  - Opções que estavam em cima da mesa:
    - **A (escolhida):** campo opt-in por passo (ex.: `repo_files: [...]`), só para os passos que o declarem. Paths dentro do repo, só leitura, cortados por tamanho, com uma denylist fixa (`.env*`, `*.pem`, `*.key`, `secrets/`…). Planos existentes ficam iguais; é uma parte do AU-22.
    - **B:** implementar o `knowledge_refs` para todos os planos (o AU-22 tal como está escrito). Muda os prompts de todos os planos com `knowledge_refs`, incluindo o `seo-article-demo`, e invalida a base medida no B1-bis-R2.
    - **C:** manter. Em external, o audit fica de âmbito e lacunas; a auditoria real faz-se com `gitleaks`/`semgrep` (J10) e revisão humana.
- **Segredos nunca entram num prompt.** O `repo_files` recusa `.env*`, chaves e credenciais (lista acima), e um teste prova que o conteúdo de um `.env` declarado não chega ao prompt (`tests/test_repo_files.py`). A `secrets_hygiene` faz-se com `gitleaks` **local** ou no CI (J10), nunca mandando ficheiros a um LLM externo.
- **Os conselhos usam só o AGENT.md, não a skill.** O `engenharia.revisor-codigo` (crítico nos conselhos `security`/`architecture`) aponta para uma skill do pack Claude (`code-review-and-quality`), que só é carregada quando corre como passo de plano.

## CI de segurança: gitleaks + semgrep (SEC-2, 2026-10-03)

Workflow `.github/workflows/security-scan.yml`, em cada PR para `main`, em cada push para `main` e à mão. O repo é público, por isso os minutos são gratuitos.

| Job | O que faz | Bloqueia? |
|---|---|---|
| **gitleaks** `v8.30.1` (instalado com `go install`, verificado em `sum.golang.org`) | Segredos no **histórico git completo**, com valores redigidos | **Sim**, em qualquer fuga que não esteja no `.gitleaksignore` |
| **semgrep** `1.179.0` + regras open source `semgrep/semgrep-rules` fixadas no commit `a84ff9cc` (python, github-actions, secrets, javascript, typescript; sem login, registo nem métricas) | SAST | **PR:** sim, mas só achados **novos** face à base do PR (`--baseline-commit`), de severidade ERROR/WARNING. **main/manual:** não; varrimento completo com relatório (resumo no job e artefacto `semgrep.json`) |

As actions estão fixadas por SHA, e o workflow passa no `actionlint` e nas regras de GitHub Actions do próprio semgrep.

**Linha de base medida localmente (2026-10-03), com as mesmas versões e regras do CI:**
- **gitleaks:** 501 commits, **2 achados históricos**, mais 1 no ficheiro actual, todos da mesma linha.
  - Era um **fragmento truncado** (prefixo + "...") da antiga `SUPABASE_SERVICE_ROLE_KEY`, citado no `docs/initiatives/STATUS.md` (S20) como "rotacionada e apagada no Supabase em 2026-09-19".
  - O fragmento foi **removido** do ficheiro actual.
  - As 2 ocorrências do histórico estão no `.gitleaksignore`, com o motivo; reescrever o histórico exigiria force-push.
  - Depois disto: **0 achados**.
  - Teste negativo: um token falso novo num commit faz o gitleaks sair com 1.
- **semgrep:** **85 achados** (11 ERROR, 63 WARNING, 11 INFO). Triagem:
  - **11 ERROR são falsos positivos:**
    - SQL (9): as f-strings só interpolam constantes (`COLUMNS`, `CHUNKS_TABLE`), e os valores vão como parâmetros `%s` (ex.: `runner/plan_runner/memory_l4.py:132`, `runner/plan_runner/supabase_writer.py:233`);
    - `subprocess.Popen` (2): lista de argumentos com `sys.executable`, num cliente de teste (`mcp/plan_runner/test_client.py:51`).
  - **20 WARNING reais (supply chain):** actions dos workflows existentes fixadas por tag e não por SHA (`runner-tests.yml` 8, `ci.yml` 5, `release.yml` 5, `ingest-knowledge.yml` 2). Pendente: SEC-2c. **FEITO (SEC-2c, 2026-10-03):** as 17 `uses:` por tag dos 4 workflows antigos ficaram fixadas por SHA, no commit para onde a tag móvel apontava, logo sem mudar de versão. O semgrep passou a 0 achados de GitHub Actions; o repo passou de 85 para 65 achados (WARNING de 63 para 43, todos de código, SEC-2d). Os SHAs são actualizados pelo Dependabot (`package-ecosystem: github-actions` em `.github/dependabot.yml`).
  - **O resto** (path traversal / fs com nomes não literais, sobretudo em `packages/`, que é o TS arquivado pela D1; i18n; formatação) fica na linha de base. Só achados **novos** falham um PR. **Triado no SEC-2d** (secção abaixo).
  - Teste do modo PR: um commit limpo passa (exit 0); um commit com `subprocess.call(cmd, shell=True)` falha (exit 1).

**Reproduzir localmente:**
```bash
go install github.com/zricethezav/gitleaks/v8@v8.30.1 && "$(go env GOPATH)/bin/gitleaks" git --redact --no-banner .
pip install semgrep==1.179.0 && git clone https://github.com/semgrep/semgrep-rules /tmp/sr && git -C /tmp/sr checkout a84ff9cc2453ca91d581380de4b8b3f272f6f4be
semgrep scan --metrics=off --config /tmp/sr/python --config /tmp/sr/yaml/github-actions --config /tmp/sr/generic/secrets --config /tmp/sr/javascript --config /tmp/sr/typescript .
```

### SEC-2d: triagem da linha de base (2026-10-03)

**Resultado:** 65 → **49 achados, todos em código arquivado pela D1** (`packages/`, `apps/`; `docs/audit/DECISAO-1-runtimes.md:89`). **Código activo: 0 ERROR, 0 WARNING, 0 INFO.**

**Código activo: 16 falsos positivos marcados** (11 ERROR + 5 WARNING). Cada um tem duas linhas: o motivo e, logo por baixo, `# nosemgrep: <regra>` (`//` em TS).
- O id curto da regra chega, e a marcação é **específica da regra**: um `nosemgrep` com outra regra não silencia esta. Isto foi testado localmente antes de aplicar.
- Só se acrescentaram linhas de comentário (30 linhas, nenhuma alterada). Ruff limpo; 399 testes verdes.

| Regra | Onde (linha do achado antes da marcação) | Porque é falso positivo |
|---|---|---|
| `sqlalchemy-execute-raw-query` (ERROR ×9) | `runner/plan_runner/memory_l4.py` 132, 185, 241, 267, 289; `runner/plan_runner/supabase_writer.py` 108, 156, 228, 233 | As f-strings só interpolam constantes do módulo (`COLUMNS`, `memory_l4.py:51`; `CHUNKS_TABLE`, `supabase_writer.py:30`); os valores vão sempre como parâmetros `%s`. O `candidates()` só junta placeholders |
| `python36-compatibility-Popen2` + `dangerous-subprocess-use-audit` (ERROR ×2) | `mcp/plan_runner/test_client.py` 51 | Lista de argumentos fixa (`sys.executable`, sem shell), num cliente de teste do lab |
| `string-concat-in-list` (WARNING ×3) | `runner/plan_runner/council_session.py` 876; `runner/plan_runner/external_worker.py` 398, 479 | Concatenação implícita **intencional** (mensagem partida em 2 linhas), não é uma vírgula em falta |
| `return-not-in-function` (WARNING ×1) | `runner/plan_runner/models.py` 11 | É uma `lambda` num `default_factory` |
| `path-join-resolve-traversal` (WARNING ×1) | `vitest.config.ts` 9 | `name` vem dos nomes fixos de packages do próprio ficheiro (linhas 14–20) |

**Código arquivado (D1, VIA A: "arquivado, não apagado"): 49 achados. Decisão do maestro (opção A): "arquivado, não aplicável"; não bloqueia o CI.**

| Package | Regra | Sev. | N |
|---|---|---|---:|
| `packages/mcp` | `path-join-resolve-traversal` | WARNING | 9 |
| `packages/mcp` | `detect-non-literal-fs-filename` | WARNING | 8 |
| `packages/mcp` | `jquery-insecure-selector` | WARNING | 1 |
| `packages/mcp` | `unsafe-formatstring` | INFO | 1 |
| `packages/scripts` | `path-join-resolve-traversal` | WARNING | 7 |
| `packages/scripts` | `detect-non-literal-fs-filename` | WARNING | 6 |
| `packages/scripts` | `detect-non-literal-regexp` | WARNING | 1 |
| `packages/scripts` | `unsafe-formatstring` | INFO | 5 |
| `packages/core` | `no-stringify-keys` | WARNING | 3 |
| `packages/core` | `detect-non-literal-fs-filename` | WARNING | 2 |
| `packages/core` | `missing-template-string-indicator` | INFO | 1 |
| `packages/websocket` | `unsafe-dynamic-method` | WARNING | 1 |
| `apps/web` | `jsx-not-internationalized` | INFO | 4 |
| **Total** | | | **49** (38 WARNING, 11 INFO) |

- **Porque continuam a ser varridos** (em vez de ficarem num `.semgrepignore`):
  - um PR que **acrescente** um achado ERROR/WARNING em `packages/` ou `apps/` continua a falhar (modo diff-aware), por isso não se perde cobertura;
  - um `.semgrepignore` substituiria as exclusões por omissão do semgrep.
- **O relatório do `main` separa** o código activo (esperado 0, e cada achado listado) do código arquivado.
- **Se o TS for reactivado** (revertendo a D1), estes 49 têm de ser triados um a um antes. O `packages/mcp` lê ficheiros com paths dinâmicos (`path-join-resolve-traversal`, `detect-non-literal-fs-filename`) e merece revisão real nesse caso.

## Verificação

```text
cd runner
python -m plan_runner.areas                 # E7 (+ --inventory)
python -m pytest tests/test_capabilities.py tests/test_security_pipeline.py -q
python -m plan_runner run ../docs/orchestration/security/templates/examples/security-audit-demo.plan.yaml --mode stub --out ../pilots/run-security-demo
```

**Resultado (2026-10-03, ambiente com todas as dependências, incluindo `mcp`):**
- E7 verde: 10 áreas, 37 agentes, 3 conselhos, 1 ficheiro de capabilities;
- testes: **34 novos** (`test_capabilities.py` 28, `test_security_pipeline.py` 6); suite rápida 363 passed (41 skipped precisam de Postgres e correm no CI, job `test-rag`); suite lenta 34 passed;
- plano demo:
  - em stub, chega a `paused_human_gate` com os 3 artefactos;
  - em external (Gemini falso), cada passo recebe o AGENT.md e a SKILL.md certos, com grounding `full` e política `opt`;
  - o ledger regista os 3 agentes, e a triagem já não é pedida em resumo (`context.full` no report).

## O que não fazer

- Ataque activo / pentest ofensivo no runner de produção
- Escrever em produção a partir destes agentes
- Aceitar risco CRITICAL/HIGH sem HITL
- Tratar `security_auditor` como meta-agente de deliberação (é C3 domínio)
- Criar 8 agentes permanentes para as 8 capabilities
- Omitir `vertical:` em planos security (S34)
