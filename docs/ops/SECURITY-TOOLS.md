# Arsenal de segurança (SEC-SUITE-1, SEC-LLMRT-1, P-48 = A)

> A área `security` é **defensiva** por política (`config/security-capabilities.yaml`): `offensive: forbidden`,
> `act_in_production: forbidden`, `hitl: required`. As ferramentas defensivas correm no CI (lêem e relatam).
> As ofensivas (pentest, red-team de LLM) só em **laboratório** (`lab`/`deferred`), em workflows manuais, nunca no runner.

## 1. Defensivo — corre no CI

| Ferramenta | Licença | Onde | Alvo | Bloqueia? |
|---|---|---|---|---|
| gitleaks | MIT | `security-scan.yml` (SEC-2) | segredos no histórico git | sim |
| semgrep | LGPL-2.1 (regras OSS) | `security-scan.yml` (SEC-2) | SAST multilinguagem | achados novos vs base |
| CodeQL | — (grátis em repo público) | `codeql.yml` | SAST (Python, JS/TS, Actions) | sim |
| **pip-audit** | Apache-2.0 | `security-suite.yml` (P-48) | vulnerabilidades nas dependências Python | **sim** (base limpa) |
| **bandit** | Apache-2.0 | `security-suite.yml` (P-48) | SAST Python (`runner/`, `scripts/`) | informativo (ver §3) |
| **zizmor** | MIT/Apache-2.0 | `security-suite.yml` (P-48) | segurança dos workflows do Actions | informativo (ver §3) |

## 2. Linha de base (2026-10-09)

Medida nesta sessão, para tornar a promoção a bloqueante honesta (como o semgrep começou com uma base de achados):

- **pip-audit:** os 5 `runner/requirements*.txt` → *No known vulnerabilities found*. Por isso bloqueia já.
- **bandit** (`-ll -ii`, média+): **0 High, 12 Medium, 9 Low.** As 12 Medium são todas `B608`
  (`hardcoded_sql_expressions`) em `runner/plan_runner/supabase_writer.py` (7) e `memory_l4.py` (5) — SQL
  construído com nome de tabela/coluna constante e **valores sempre parametrizados**. Candidatas a falso
  positivo, por confirmar uma a uma.
- **zizmor** (`--persona=regular`): **1 High, 16 Medium** (1 info).
  - *High* `excessive-permissions`: `release.yml` tem `contents: write` ao nível do workflow (devia ser ao nível do job).
  - *Medium* `artipacked`: vários `actions/checkout` sem `persist-credentials: false`.

## 3. Promoção a bloqueante (SEC-SUITE-1, trabalho que falta)

O bandit e o zizmor entram **informativos** (`continue-on-error`) para não partir os PRs em aberto. Passam a
bloquear depois da triagem:

1. **bandit:** confirmar que cada `B608` usa parâmetros (sem interpolação de valores), marcar com
   `# nosec B608` + motivo, e tirar o `continue-on-error`.
2. **zizmor:** pôr `persist-credentials: false` nos checkouts que não fazem push; mover o `contents: write`
   do `release.yml` para o job que cria a release; e tirar o `continue-on-error`.

Enquanto não estiver feito, os dois relatam no CI mas não chumbam.

## 4. Ofensivo — só laboratório (nunca no runner)

Capabilities `lab`/`deferred` em `config/security-capabilities.yaml`; workflows manuais, `continue-on-error`,
gated no segredo `LLM_API_KEY`, modelo Gemini Flash Lite (custo zero), só contra os nossos próprios alvos.

| Ferramenta | Licença | Capability | Workflow | O que faz |
|---|---|---|---|---|
| Strix | Apache-2.0 | `external_pentest_lab` | `strix-lab.yml` | pentest de app: confirma falhas OWASP com PoC (`docs/ops/STRIX-LAB.md`) |
| Garak | Apache-2.0 | `llm_redteam_lab` | `llm-redteam-lab.yml` | red-team de LLM: prompt injection, jailbreak, fuga de dados |
| promptfoo | MIT | `llm_redteam_lab` | `llm-redteam-lab.yml` | avaliação/red-team de prompts (TODO: `promptfooconfig.yaml`) |
| PyRIT / DeepTeam | MIT | `agent_redteam_lab` | — | red-team dos próprios agentes (**SEC-3**, deferred) |

Correr qualquer um precisa de 1 run do DEV com a chave do LLM; o custo mede-se antes de qualquer compromisso.
Apontar a repos privados (ANM) manda código/prompts ao fornecedor do LLM — decisão à parte do maestro.

## 5. Ainda por incorporar (futuro)

- **osv-scanner** e **Trivy** (Apache-2.0): binários Go para vulnerabilidades de dependências e imagens.
  Ficam para **SEC-SCA-2**, porque precisam de um pin por versão + checksum que esta sessão não conseguiu fixar.
- **actionlint** já se usa na revisão local; podia virar um passo de CI junto do zizmor.
