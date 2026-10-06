# Hardening do F6 (2026-10-06)

| # | Verificação | Resultado | Evidência |
|---|---|---|---|
| 1 | Segredos, tokens e `.env` versionados | ✅ Sem fugas; nenhum `.env` versionado | `gitleaks dir .` e `gitleaks git .` (todo o histórico) |
| 2 | Paths absolutos da máquina local | ✅ **Corrigido:** 13 ocorrências de `C:\Users\<utilizador>\…` em 4 docs → `%USERPROFILE%` | Commit `7cf5280`. O histórico do git mantém-nas (sem reescrita, regra "sem `--force`") |
| 3 | Todo o `.md` de `docs/knowledge/` no MANIFEST ou no `EXCLUDED` | ✅ Teste de cobertura verde; corre também quando muda `docs/knowledge/**` | `runner/tests/test_knowledge_coverage.py` (#119) |
| 4 | Segurança de entrada (F1) | ✅ Processo filho com timeout, `RLIMIT_DATA` (1 GiB), `max_bytes`, ZIP/OOXML verificado | `docs/ops/INGEST-DOCUMENT.md`; `runner/tests/test_ingest_security.py` (18) |
| 5 | Web fetch (F2) | ✅ Allowlist em cada redirect, robots.txt (RFC 9309), SSRF (loopback, privados, link-local, `169.254.169.254`), tectos de bytes e de tempo | `docs/ops/WEB-FETCH.md`; `runner/tests/test_web_fetch.py`. Limitação já documentada (DNS rebinding) → **F2-SEC-1** |
| 6 | Retrieve aditivo | ✅ `match_knowledge` intacta; `match_knowledge_v2` aditiva e idempotente (testada 2×); flag `KNOWLEDGE_RPC_V2` com fallback PGRST202 | `scripts/migrations/f3_provenance_retrieve.sql`; `runner/tests/test_f3_provenance.py`; `ANM:tests/knowledgeV2.test.mjs`. A v3 está estacionada (F3b-AUTH-1) |
| 7 | Dry-run vs escrita em produção | ✅ **Corrigido:** o `RAG-CANONICAL.md` §3 ainda dizia que um push escrevia na t6 | Ver a tabela abaixo |
| 8 | Dependências | ✅ 2 alertas do Dependabot corrigidos (#118); `pnpm audit` limpo | #118 |
| 9 | Testes no âmbito tocado | ✅ | [`tests-and-ci.md`](./tests-and-ci.md) |

## O que escreve em produção

| Comando | Escreve? |
|---|---|
| `scripts/ingest_apply.py` (corrido pelo `ingest-knowledge` num push para a `main` que toque em `docs/**/*.md` ou nos scripts de ingest) | **Sim:** Supabase (`knowledge_chunks`, `knowledge_sources`) e embeddings Gemini |
| `scripts/ingest_apply.py --dry-run` | Não |
| `scripts/ingest_delta.py` (com ou sem `--apply`, que só tem stubs) | Não |
| `scripts/ingest_document.py`, `scripts/web_fetch.py` | Só ficheiros locais (`.md` + `.meta.yaml`) |
| `scripts/validity_report.py`, `scripts/f5_evidence.py` | Não (só leitura) |
| `scripts/migrations/*.sql` | Só quando o DEV os corre no SQL Editor do Supabase |
| `workflow_dispatch` do `ingest-knowledge` | Não (só dry-run) |
