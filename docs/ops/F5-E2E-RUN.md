# F5: validação E2E de uma capability com run real

> F5 do `docs/initiatives/PENDENCIAS.md` (AMBOS, Alta) e da cadeia F1–F6 (`docs/initiatives/PENDENCIAS_T6.md`).
> **Só o DEV corre isto:** precisa do `GEMINI_API_KEY`, do `MCP_API_KEY` e do `VERCEL_PROTECTION_BYPASS`. O Claude preparou o comando, o recolhedor de evidência (`scripts/f5_evidence.py`, testado) e este molde.

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
- só no directório do run, em `pilots/f5-run/`, que é ignorado pelo git (`.gitignore`);
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
$env:MCP_URL = "https://agent-network-mcp-oddn.vercel.app/api/mcp"

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
| Data (UTC) | NÃO VERIFICADO |
| Commit do NAS | NÃO VERIFICADO |
| Saída do `scripts/f5_evidence.py` | NÃO VERIFICADO (colar o Markdown completo) |
| Observações (qualidade do relatório, tempo total) | NÃO VERIFICADO |

## 5. Se falhar

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `knowledge_context_failed` com 400 | Protecção da Vercel | Confirmar o `VERCEL_PROTECTION_BYPASS` (L5-F0-REVALIDATION.md §6.2) |
| `knowledge_context_failed` com `not enough values to unpack` | `mcp` 2.x no ambiente | `pip install -r requirements.txt` no venv (#102) |
| `worker_error` com 429 | Quota do Gemini (tier gratuito) | Esperar uns minutos e correr de novo (o worker do runner não tem retry a 429; só o `ingest_apply` o tem) |
| `paused_budget` | Tecto de tokens atingido | Ver `docs/ops/BUDGET.md`; `resume` com um tecto maior |
