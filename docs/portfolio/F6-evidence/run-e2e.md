# Provas contra produção (corridas pelo DEV)

Os runs reais precisam de credenciais (Gemini, MCP, bypass da Vercel), que só o DEV tem. Aqui ficam só os resultados agregados, sem conteúdo.

## F0.7b: golden set de security contra o MCP de produção (2026-10-05)
`python -m plan_runner.l5_eval run`: 18 casos, `source_hit@4` 1.0, `provenance_ok` 1.0, `chunk_hit@1/3/4` 0.611/0.889/0.944, `mrr_chunk` 0.736, `no_hits` 0. Registo em `docs/ops/L5-F0-REVALIDATION.md` §6.2.

## F3a: proveniência activa em produção (2026-10-06)
- **SQL aplicado:** SELECTs só de leitura ao catálogo. Existem a `match_knowledge_v2` e a `match_knowledge` antiga, as colunas novas e o CHECK do `status`.
- **Sem regressão:** o `l5_eval` com `KNOWLEDGE_RPC_V2=1` deu os mesmos números do F0.7b.
- **Prova da v2:** um `tools/call` do `retrieve_knowledge` (`kb=security`, `top_k=1`) devolveu `citation.uri` e `metadata` preenchido (`document_type` = `md`, `status` = `active`). Na v1 o `metadata` é `null`.
- Registo em `docs/ops/RAG-CANONICAL.md` § F3a.

## F5: validação E2E com run real (2026-10-06)
`scripts/f5_evidence.py pilots/f5-run-v3`: **PASSOU**, 5 de 5 critérios.
- Run `run_9017d441d1`, plano `example-security-audit-demo`, `external`, estado `done`.
- Passos: triage, audit, gate humano e report.
- L5 no passo audit: `kb=security`, 5 hits, fonte `docs/knowledge/security-agents-stack.md`.
- 3 chamadas a `gemini-3.5-flash-lite`, 16614 tokens; 4 artefactos; 0 erros.
- Os 2 primeiros runs falharam por configuração: o `MCP_URL` com `/api/mcp` e o bypass truncado. Os dois estão corrigidos no runbook (V41, W-011).
- Registo em `docs/ops/F5-E2E-RUN.md` §4.
