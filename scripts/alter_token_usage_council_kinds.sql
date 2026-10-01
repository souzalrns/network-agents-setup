-- Bloco C (CouncilSession): o ledger J6 passa a aceitar as chamadas do conselho.
--   council_member   -- INDEPENDENT (1 por membro e ronda)
--   council_peer     -- PEER_RANK   (1 por membro e ronda)
--   council_chairman -- SYNTHESIZE  (1 por ronda)
-- Tabela: agent-network-mcp/memory/token_usage.sql (projecto Supabase agent-network-memory).
-- Sem isto, as linhas do conselho ficam no token_usage.jsonl local e o envio para
-- o Supabase falha com o CHECK (registado como remote "error: HTTP 400" no jsonl;
-- o conselho nunca para por isso). Passos: docs/ops/COUNCIL.md, "Ledger".
-- Idempotente: pode correr mais de uma vez. NAO executado por agentes: passo do DEV.

alter table public.token_usage drop constraint if exists token_usage_call_kind_check;
alter table public.token_usage add constraint token_usage_call_kind_check
  check (call_kind in ('router', 'agent', 'embed_query', 'embed_doc',
                       'council_member', 'council_peer', 'council_chairman'));

-- Verificar (deve listar os 7 valores):
-- select pg_get_constraintdef(oid) from pg_constraint where conname = 'token_usage_call_kind_check';
