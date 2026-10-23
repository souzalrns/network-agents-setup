# Fecho do setup — a sessão do maestro (por ordem)

> Preparado a 2026-10-23 (opção A do maestro). Tudo o que **não** precisa das tuas credenciais
> já está feito. Os passos abaixo são só os que precisam delas, por ordem. Os valores das chaves
> nunca vão para ficheiros, commits nem chats.

**Antes de começar** (no teu computador, na raiz do `network-agents-setup`):

```powershell
git pull origin main
pip install -r runner/requirements.txt -r runner/requirements-langgraph.txt
$env:GEMINI_API_KEY = "<a tua chave>"
$env:MCP_URL = "https://agent-network-mcp-oddn.vercel.app"
$env:MCP_API_KEY = "<a chave do MCP>"
```

## 1. Autoridade das fontes em produção (F3b-AUTH-1)

1. No SQL Editor do Supabase (`agent-network-memory`):
   - Corre a **query de controlo ANTES**, que está no fim de `scripts/migrations/f3b_authority_v3.sql`. Tem de dar 0 linhas. Já a corri a 23/10 (só leitura): 0 violações.
   - Corre o ficheiro inteiro. É idempotente.
2. Na Vercel, projecto `agent-network-mcp-oddn` → Settings → Environment Variables (Production):
   - acrescenta `KNOWLEDGE_RPC_V3` = `1`;
   - faz **Redeploy**.
3. Para voltar atrás: tira a variável e faz redeploy. Não é preciso SQL.

## 2. Conector do Claude.ai (F0.6)

1. Em Claude.ai → Settings → Connectors, muda o URL do conector para:
   `https://agent-network-mcp-oddn.vercel.app/api/mcp/k/<MCP_API_KEY>`.
2. Teste: pergunta "Usa o retrieve_knowledge com kb security: qual é a política defensiva da área security?".
   - A resposta tem de citar `docs/knowledge/security-agents-stack.md`.
   - Com o passo 1 feito, o `metadata` traz também `authority: curado`.

## 3. Publicar o fetchtron 0.2.0 (F2-SEC-1, fecha o DNS rebinding)

1. Depois do merge do PR do F2-SEC-1: GitHub → Actions → **Publish fetchtron to PyPI** → Run workflow (`main`).
   - Publicar é público e irreversível: uma versão no PyPI não se substitui.
2. Diz-me "sobe o pin do fetchtron". É 1 linha em `runner/requirements.txt` (`fetchtron==0.2.0`). Os testes do runner já passam com o 0.2.0.

## 4. Runs reais e evidência (F2, F3b-GS-1, F6, F5-ROUTE-1, F3-ART-1)

```powershell
python scripts/setup_close_runs.py --check   # tem de dizer "ambiente e ficheiros prontos"
python scripts/setup_close_runs.py           # corre tudo (~15–30 min, Gemini grátis)
```

- **Relatório:** `pilots/setup-close-<data>/REPORT.md`, com PASS/FAIL por item, os paths dos `result.json` e um excerto do `meta.sources`.
- **Cópia versionável:** `pilots/evidence/setup-close-<data>.md`.
- **Repetir só o que falhou:** `python scripts/setup_close_runs.py --only F2,F6-MARKET`.
- **`MCP-V3` em FAIL com "v2":** o passo 1 ainda não está activo; repete-o.
- **Os runs param no gate humano:** é o previsto. Nada é aprovado nem executado por este script.
- **No fim:** `git add pilots/evidence/setup-close-*.md`, faz commit e manda-me o `REPORT.md`. Eu fecho os itens no `PENDENCIAS.md`.

## 5. Datas reais de 2 fontes (F3b-VAL-1)

Só tu sabes as datas, e não se inventam (P-28 = C). Cria 1 sidecar ao lado de cada `.md`:

- `docs/knowledge/legal/direito-br-pt.meta.yaml` (classe `legal`: exige `effective_from`);
- `docs/knowledge/imobiliario/fipezap.meta.yaml` (classe `market_data`: exige `effective_until`).

```yaml
uri: docs/knowledge/legal/direito-br-pt.md
title: Direito Civil brasileiro — regimes de bens, usucapião, inventário, locação
document_type: md
retrieved_at: 2026-10-23T00:00:00+00:00
content_hash: <SHA-256 do .md>
status: active
jurisdiction: BR
effective_from: <AAAA-MM-DD, a data da própria fonte>
```

- **`content_hash`:** `Get-FileHash -Algorithm SHA256 <ficheiro.md>`.
  - Valores a 23/10: `direito-br-pt.md` = `c60c0d43…b389`, `fipezap.md` = `0c82a315…c749`.
  - Se o `.md` mudar, o hash muda.
- **No `fipezap.meta.yaml`:** troca `effective_from` por `effective_until`, a data até à qual os dados valem.
- **Verificar:** `python scripts/validity_report.py` deixa de assinalar `falta_data`.

## 6. (Opcional) Apagar a `knowledge_chunks_t6` (F0.12)

**Não fazer sem backup.** É irreversível. Passos em `docs/ops/RAG-CANONICAL.md` §6:
1. `pg_dump` da tabela;
2. `scripts/drop_knowledge_chunks_t6.sql`, que aborta sozinho se faltar alguma fonte.

## Decisões que continuam contigo

| Decisão | Recomendada | Porquê |
|---|---|---|
| **P-81:** conhecimento de trading no L5 | **A**: `_kb_for` genérico, kb = id da área | 1 função, sem regressão nas kbs actuais; desbloqueia o golden de trading |
| Nome das skills de domínio (alerta do `skill-scout`) | **A**: manter `_`, como todo o repositório | A pasta = `action` = `name`; renomear só o `name` quebra a spec de outra forma |
