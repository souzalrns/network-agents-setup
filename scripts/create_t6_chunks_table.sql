- T6: tabela exclusiva de chunks (network-agents-setup).
-- Nao partilha com agent-network-mcp (que usa knowledge_chunks).
-- Idempotente: IF NOT EXISTS. Requer pgvector.

CREATE TABLE IF NOT EXISTS knowledge_chunks_t6 (
  id TEXT PRIMARY KEY,
  source_path TEXT NOT NULL REFERENCES knowledge_sources(source_path) ON DELETE CASCADE,
  content_hash TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  content TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  kb TEXT NOT NULL DEFAULT 'marketing',
  embedding vector(768),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (source_path, chunk_index)
);

CREATE INDEX IF NOT EXISTS knowledge_chunks_t6_kb_agent_idx
  ON knowledge_chunks_t6 (kb, agent_id);

CREATE INDEX IF NOT EXISTS knowledge_chunks_t6_hash_idx
  ON knowledge_chunks_t6 (content_hash);