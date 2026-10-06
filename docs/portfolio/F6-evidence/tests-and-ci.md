# Testes e CI: como reproduzir

Sem credenciais nem rede. A BD é sempre um Postgres descartável com pgvector, nunca o Supabase.

```bash
# runner (Python 3.12), a partir de runner/
pip install -r requirements.txt pytest
python -m pytest -q                                   # unitários (os de Postgres ficam skipped)

# com Postgres + pgvector local (os testes criam e apagam schemas próprios)
RAG_TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ragtest RAG_TEST_REQUIRED=1 \
  python -m pytest -q

# ingestão de documentos (F1): extras do MarkItDown
pip install -r requirements-ingest.txt
INGEST_TEST_REQUIRED=1 python -m pytest -q tests/test_ingest_*.py

# lint do runner (o mesmo da CI)
python -m ruff check plan_runner/ tests/

# relatórios locais, só leitura
python ../scripts/ingest_delta.py                     # dry-run do MANIFEST
python ../scripts/validity_report.py --strict         # validade das fontes (F3b)

# TypeScript (raiz): o mesmo que o ci.yml
pnpm install --frozen-lockfile && pnpm run ci:typecheck && pnpm exec vitest run tests/unit
```

## Última corrida (2026-10-06)

| Âmbito | Resultado | Onde |
|---|---|---|
| Runner + Postgres + pgvector | **754 passed**, 29 skipped | Local, branch `feat/f3b-validity` (inclui o F3c) |
| Runner, só o âmbito do hardening do F6 | 95 passed, 4 skipped | Local, este branch |
| TypeScript | typecheck OK; vitest **195/195**; cobertura 28,6% das linhas (mínimo 25%); smoke test contra Postgres OK; `pnpm audit` limpo | Local, #118 |
| CI do #119 | 12 checks verdes (test, test-rag, test-ingest, test-slow, semgrep, gitleaks, CodeQL ×3) | GitHub |
| Segredos | `gitleaks dir .` e `gitleaks git .`: sem fugas | Local, este branch |
| SAST | semgrep (python, github-actions, secrets): 0 achados nos ficheiros tocados | Local |

Jobs da CI (`.github/workflows/`): `runner-tests.yml` (test, test-rag, test-ingest, test-slow), `ci.yml` (TypeScript), `security-scan.yml` (semgrep, gitleaks), CodeQL (default setup).
