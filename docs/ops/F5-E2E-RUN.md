# F5: validação E2E de uma capability com run real

> F5 do `docs/initiatives/PENDENCIAS.md` (AMBOS, Alta) e da cadeia F1–F6 (`docs/initiatives/PENDENCIAS_T6.md`).
> **Só o DEV corre isto:** precisa do `GEMINI_API_KEY`, do `MCP_API_KEY` e do `VERCEL_PROTECTION_BYPASS`. O Claude preparou o comando, o recolhedor de evidência (`scripts/f5_evidence.py`, testado) e este molde.

> **Estado: PASSOU (2026-10-06, 3.º run do DEV).** Evidência na §4. Os 2 primeiros runs falharam por 2 erros de configuração, que estão agora na §5.

## 1. O que o run prova

Uma capability do domínio `security` (as `implemented` do `config/security-capabilities.yaml`), de ponta a ponta, pelo caminho de produção:

```
ingest (T6, já feito: o pack docs/knowledge/security-agents-stack.md está no L5; F0.7b)
  → retrieve (MCP de produção, retrieve_knowledge, kb=security; bloco `knowledge:` do passo audit)
  → plan_runner (security-audit-demo: triage → audit → report, worker Gemini real)
  → resposta (artefactos + gate humano hitl_security_decision)
```

Plano: `docs/orchestration/security/templates/examples/security-audit-demo.plan.yaml`. É um caso real e não sensível: uma auditoria defensiva do próprio repo, só leitura, sem acções ofensivas.

**O que escreve e onde:**
- só no directório do run, em `pilots/f5-run/` (ou `pilots/f5-run-v2/`, `-v3`…), que é ignorado pelo git (`.gitignore`: `pilots/f5-run*/`);
- o retrieve só lê;
- **não escreve em produção.** Excepção opcional: com `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` definidas, o ledger de tokens também grava na tabela `token_usage`. Para o F5 **não é preciso**: o ledger local (`token_usage.jsonl`) chega.

## 2. Comandos (PowerShell, na tua máquina)

```powershell
cd network-agents-setup\runner
# venv com as dependências do runner (mcp==1.30.0; ver L5-F0-REVALIDATION.md §6.2)
python -c "import importlib.metadata as m; print(m.version('mcp'))"   # tem de dar 1.30.0

# Segredos sem ficarem no histórico (não colar valores em lado nenhum)
$env:GEMINI_API_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'GEMINI_API_KEY' -AsSecureString)).Password
$env:MCP_API_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'MCP_API_KEY' -AsSecureString)).Password
$env:VERCEL_PROTECTION_BYPASS = [System.Net.NetworkCredential]::new('', (Read-Host 'VERCEL_PROTECTION_BYPASS' -AsSecureString)).Password
# MCP_URL é SÓ a base: o runner acrescenta /api/mcp (runner/plan_runner/mcp_knowledge.py).
# Desde o W-011 (2026-10-07), um /api/mcp a mais é tirado sozinho e um bypass truncado falha logo com mensagem clara.
$env:MCP_URL = "https://agent-network-mcp-oddn.vercel.app"

# Confirmar que nenhum segredo ficou truncado (mostra só o tamanho, nunca o valor).
# 0 ou 1 carácter quer dizer que a colagem falhou: colar outra vez.
"GEMINI {0} · MCP {1} · BYPASS {2} caracteres" -f $env:GEMINI_API_KEY.Length, $env:MCP_API_KEY.Length, $env:VERCEL_PROTECTION_BYPASS.Length

# O run (tecto de tokens; o plano já tem budget.max_tokens = 40000)
python -m plan_runner run ..\docs\orchestration\security\templates\examples\security-audit-demo.plan.yaml `
  --mode external --worker gemini --max-tokens 40000 --out ..\pilots\f5-run

# Evidência (sem segredos nem conteúdo): colar a saída na §4
cd ..
python scripts\f5_evidence.py pilots\f5-run

Remove-Item Env:GEMINI_API_KEY, Env:MCP_API_KEY, Env:VERCEL_PROTECTION_BYPASS
```

**Porque não `--max-cost-usd`:** os preços em `config/model-prices.yaml` estão `null` (o item T-004 está por confirmar), e com um tecto de custo activo o worker **recusa** chamar o modelo, por falha fechada. O tecto deste run é em tokens. Quando o T-004 estiver preenchido, pode acrescentar-se `--max-cost-usd 0.50`.

## 3. Critérios (aplicados pelo `scripts/f5_evidence.py`)

| Critério | Como se verifica |
|---|---|
| O run chegou ao fim ou ao gate humano | `status.json`: `state` = `done` ou `paused_human_gate` |
| O L5 entrou | Pelo menos 1 evento `knowledge_context_injected` com `hit_count` > 0, e as fontes citadas no `knowledge_context.md` |
| O modelo correu | Pelo menos 1 linha no `token_usage.jsonl` com tokens |
| Sem erros | 0 `worker_error` e 0 `knowledge_context_failed` |
| Há resposta | Pelo menos 1 artefacto escrito |

O recolhedor sai com 0 se o veredicto for PASSOU e 1 se for INCOMPLETO, e diz qual critério falhou. Um run em `--mode stub` dá sempre INCOMPLETO, e há um teste que o prova (`runner/tests/test_f5_evidence.py`).

## 4. Evidência do run (preencher pelo DEV)

| Campo | Valor |
|---|---|
| Data | 2026-10-06 (dia do relatório do DEV; a hora não veio no resultado) |
| Commit do NAS | NÃO VERIFICADO (não veio no resultado) |
| Directório do run | `pilots/f5-run-v3` (3.º run) |
| Veredicto | **PASSOU** (5 de 5 critérios) |
| Observações | 3.º run. O 1.º falhou pelo `MCP_URL` com `/api/mcp` (o runbook estava errado: V41 no `PENDENCIAS.md`) e o 2.º por um `VERCEL_PROTECTION_BYPASS` com 1 carácter. Corrigidos os dois, o 3.º passou. Qualidade do relatório e tempo total: NÃO VERIFICADO (não vieram no resultado) |

Saída do `python scripts/f5_evidence.py pilots/f5-run-v3` enviada pelo DEV (só reformatada em tabelas Markdown; os valores são os do DEV):

**Veredicto: PASSOU**

| Campo | Valor |
|---|---|
| run_id / plano | `run_9017d441d1` / `example-security-audit-demo` |
| modo / estado | `external` / `done` |
| passos concluídos | audit, hitl_security_decision, report, triage |
| L5 (knowledge) | audit: kb=security, hits=5 |
| fontes citadas | `docs/knowledge/security-agents-stack.md` |
| chamadas ao modelo | 3 (gemini-3.5-flash-lite ×3) |
| tokens in / out / total | 13670 / 2944 / 16614 |
| artefactos | `01-triage.json`, `02-audit.md`, `03-security-report.md`, `04-hitl.json` |

| Critério | OK? |
|---|---|
| estado_final | sim |
| l5_injectado | sim |
| modelo_correu | sim |
| sem_erros | sim |
| artefactos | sim |

Eventos: knowledge_context_injected ×1, human_gate_requested ×1, human_gate_resolved ×1, plan_done ×1.

## 5. Se falhar

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| O L5 não entra (`knowledge_context_failed`) e o pedido vai para `/api/mcp/api/mcp` | `MCP_URL` com `/api/mcp` no fim (1.º run do F5) | Pôr só a base: `https://agent-network-mcp-oddn.vercel.app` |
| `knowledge_context_failed` com 400 | Protecção da Vercel | Confirmar o `VERCEL_PROTECTION_BYPASS` (L5-F0-REVALIDATION.md §6.2) |
| O bypass é recusado, mas o segredo parece certo | `VERCEL_PROTECTION_BYPASS` truncado na colagem (2.º run do F5: 1 carácter) | Ver o tamanho com a linha de verificação da §2 e colar outra vez |
| `knowledge_context_failed` com `not enough values to unpack` | `mcp` 2.x no ambiente | `pip install -r requirements.txt` no venv (#102) |
| `worker_error` com 429 | Quota do Gemini (tier gratuito) | Esperar uns minutos e correr de novo (o worker do runner não tem retry a 429; só o `ingest_apply` o tem) |
| `paused_budget` | Tecto de tokens atingido | Ver `docs/ops/BUDGET.md`; `resume` com um tecto maior |
