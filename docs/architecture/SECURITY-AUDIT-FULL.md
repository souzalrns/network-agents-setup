# Auditoria de Segurança COMPLETA — network-agents-setup (2026-09-18)

Execução completa do `security_auditor` (B2b) — as 8 ferramentas pedidas, todas correram de verdade (nenhuma simulada). Complementa `SECURITY-AUDIT.md` (auditoria parcial anterior, 5 ferramentas). Só leitura — nada corrigido nesta tarefa.

## 1. Resultado por ferramenta

| # | Ferramenta | Resultado |
|---|---|---|
| 1 | **Bandit** 1.9.4 | 2 achados LOW (mesmos já conhecidos: `cli.py:54`, `working_memory.py:52`) |
| 2 | **Semgrep** (ruleset local, 4 regras — `semgrep.dev` continua bloqueado nesta sandbox) | 0 achados, 82 ficheiros |
| 3 | **Gitleaks** 8.30.1 | 0 segredos, histórico completo (338 commits) |
| 4 | **OSV-Scanner** 2.6.0 | **Inconclusivo** — `api.osv.dev`/`api.deps.dev` continuam bloqueados; inventário extraído (307 npm + 4 pip), nada verificado |
| 5 | **mcpguard** | **Sem alvo** — nenhuma config MCP de cliente no repo (mesmo achado da auditoria anterior) |
| 6 | **offsec-ai** (só modos passivos: `mcp-scan`) | **3 achados reais + 7 categorias de referência** — ver secção 2. `ai-owasp-scan` não corrido — precisa de um endpoint de chat completions ao vivo, que não existe neste repo |
| 7 | **Trivy** 0.74.0 (`secret`+`misconfig`; `vuln` bloqueado — DB em `mirror.gcr.io`, fora do allowlist) | 0 segredos; **49 misconfigurações de K8s/Dockerfile** (10 HIGH, 12 MEDIUM, 27 LOW) |
| 8 | **detect-secrets** 1.5.0 | 10 hits após excluir `node_modules`/lockfiles (812 brutos, quase tudo ruído de checksums de dependências) — 9 falsos positivos, 1 achado de prática real |

## 2. offsec-ai mcp-scan — contra o nosso próprio servidor MCP local

Corrido com `stdio://local --cmd python3 -m mcp_plan_runner` — o `mcp/plan_runner` deste repo, **não** o `agent-network-mcp` (não tocado) nem nenhum endpoint de produção. Modo passivo apenas (`mcp-scan`, nunca `mcp-attack`).

**Tools descobertas:** `list_templates`, `get_status`, `run_plan`, `resume_plan`.

| ID | Severidade | O quê |
|---|---|---|
| `OFFSEC-MCP-AUTH-001` | HIGH | Endpoint sem autenticação — `auth_posture.notes` da própria ferramenta reconhece: *"stdio transport — no network auth layer"*. Mesma mitigação já documentada (`SECURITY-AUDIT.md`): stdio-only reduz a exposição real, a ferramenta não desconta isso da severidade |
| `OFFSEC-MCP-TI-001` | HIGH | `run_plan` tem a palavra "execute" na descrição da tool — padrão genérico de risco de tool-poisoning/prompt-injection, não uma injecção confirmada |
| `OFFSEC-MCP-SCOPE-001` | **CRITICAL** | "Shell/Execution Tool Exposed: `run_plan`" — **é o mesmo achado já conhecido e parcialmente mitigado** em `mcp/plan_runner/mcp_plan_runner/policy.py:73` (perfil `moderate` sem chave). Confirmação independente, não achado novo |

Mais 7 categorias de referência (`cve_matches`, sem evidência específica no nosso servidor — informativas, aplicam-se genericamente a qualquer MCP): tool-poisoning, comando injection via argumentos, segredos em descrições de tool, excessive agency, prompt injection via resposta de tool, rug-pull de definição de tool.

## 3. Trivy — 49 misconfigurações K8s/Dockerfile

Tipos HIGH mais comuns (achados genéricos de *security context*, não específicos de dado sensível):
- `DS-0002` — imagem corre como `root`
- `KSV-0014` — sistema de ficheiros root não é read-only
- `KSV-0118` — security context por omissão (não restringido)

Concentrados em `k8s/redis.yaml` e outros manifestos — típico de setup de desenvolvimento/demo, não necessariamente already-exploited, mas vale endurecer antes de qualquer deploy real.

## 4. detect-secrets — achado de prática

9/10 hits são falsos positivos claros (placeholders de `.env.example`, `docker-compose.yml`, guard-clauses tipo `!== 'your-openai-api-key-here'`, fixture de teste). **1 real, de prática:** `k8s/secrets.yaml` está **commitado no git** — mesmo com valor placeholder (`network123`), um manifesto `Secret` do Kubernetes nunca devia estar em controlo de versões (deveria vir de `kubectl create secret` fora do repo, ou de um cofre externo — Sealed Secrets/External Secrets Operator/Vault).

## 5. Mapeamento OWASP Top 10 for LLM Applications 2026 (actualizado)

| # | Risco | Estado nesta auditoria completa |
|---|---|---|
| LLM01 | Prompt Injection | **Agora coberto** — `offsec-ai mcp-scan` confirma `OFFSEC-MCP-TI-001` (genérico, sem exploração confirmada) |
| LLM02 | Sensitive Information Disclosure | Coberto — Gitleaks + Trivy + detect-secrets, todos limpos de segredos reais; achado de prática (`k8s/secrets.yaml` no git) |
| LLM03 | Excessive Agency | **Confirmado de forma independente** — `OFFSEC-MCP-SCOPE-001` (CRITICAL) corrobora o achado já conhecido de `policy.py:73` |
| LLM04 | Supply Chain | Continua **inconclusivo** — OSV-Scanner bloqueado outra vez |
| LLM05 | Data and Model Poisoning | Não coberto — fora do âmbito das 8 ferramentas |
| LLM06 | Unbounded Consumption | Não re-testado nesta corrida |
| LLM07 | Misinformation | Não coberto (não é alvo de scanner automático) |
| LLM08 | Hidden Context Exposure | Não coberto nesta corrida |
| LLM09 | Vector and Embedding Weaknesses | Não coberto nesta corrida |
| LLM10 | Improper Output Handling | Coberto, limpo (Bandit+Semgrep, igual à auditoria anterior) |

**4 de 10 cobertos com confiança (subiu de 3 para 4 — LLM01 passou a coberto); 1 inconclusivo; 5 continuam fora do âmbito das 8 ferramentas usadas.**

## 6. O que é novo vs. já conhecido

- **Novo:** achado de prática do `k8s/secrets.yaml` no git; 49 misconfigs K8s do Trivy; confirmação independente via `offsec-ai` de LLM01/LLM03.
- **Já conhecido, reconfirmado, não corrigido de novo:** `policy.py:73` (mitigado parcialmente, não fechado — ver `SECURITY-AUDIT.md`); OSV-Scanner continua bloqueado pela rede desta sandbox.

## 7. Recomendações novas desta corrida

1. Remover `k8s/secrets.yaml` do controlo de versões (baixo esforço, prática correcta mesmo sem segredo real hoje).
2. Endurecer `k8s/redis.yaml` (e outros manifestos com o mesmo padrão): `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `capabilities.drop: [ALL]`.
3. Re-avaliar a descrição da tool `run_plan` — a palavra "execute" por si só não é o problema, mas vale rever a redacção à luz do achado `OFFSEC-MCP-TI-001`.
4. OSV-Scanner e Trivy `vuln` continuam por resolver — precisam de um ambiente com acesso a `api.osv.dev`/`api.deps.dev`/`mirror.gcr.io`, que esta sandbox não tem.

Nada corrigido nesta tarefa. `packages/core/` só foi lido (Bandit/Semgrep), não alterado; `agent-network-mcp` não foi tocado nem escaneado.
