# Material para o spike J11 (mem0 vs L4 própria) — AVALIAÇÃO, não adopção (D3).
# Origem: criado por engano em agent-network-mcp/runner/tests/ (nunca commitado
# lá); movido para aqui em 2026-09-30. Ver docs/audit/DECISAO-3-memoria.md §3.3:
# tal como está, falha com ImportError de `vecs` (dependência do store Supabase
# do mem0) e o modelo `gemini-3.1-flash-lite` NÃO está verificado.
#
# Teste manual de ligação ao mem0 (Gemini + Supabase). Precisa do .env local
# e de `pip install mem0ai python-dotenv`. Correr com:
#   python runner/tests/test_mem0_connection.py
# Sem essas dependências (ex.: CI), o pytest ignora este ficheiro.
import pytest

pytest.importorskip("mem0")
pytest.importorskip("dotenv")

import os

from dotenv import load_dotenv
from mem0 import Memory

load_dotenv()

config = {
    "llm": {
        "provider": "gemini",
        "config": {
            "model": "gemini-3.1-flash-lite",
            "api_key": os.getenv("GEMINI_API_KEY")
        }
    },
    "embedder": {
        "provider": "gemini",
        "config": {
            "model": "models/gemini-embedding-001",
            "api_key": os.getenv("GEMINI_API_KEY"),
            "embedding_dims": 768
        }
    },
    "vector_store": {
        "provider": "supabase",
        "config": {
            "connection_string": os.getenv("SUPABASE_DB_CONNECTION_STRING"),
            "collection_name": "mem0_test",
            "embedding_model_dims": 768,
            "index_method": "hnsw"
        }
    }
}

m = Memory.from_config(config)

# Teste 1: adicionar um facto
m.add("Estou a trabalhar no projecto network-agents-setup", user_id="test_user")
print("OK: add funcionou")

# Teste 2: pesquisar
results = m.search("Em que projecto estou a trabalhar?", user_id="test_user")
print("OK: search funcionou")
print("Resultado:", results)
