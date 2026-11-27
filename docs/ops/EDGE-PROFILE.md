# Perfil de pouca capacidade (sem servidor, sem custo)

Tudo o que o PCU precisa para funcionar num portátil fraco, num Raspberry ou num servidor pequeno, sem Postgres,
sem Supabase e sem chave paga.

| Peça | Perfil leve | Como |
|---|---|---|
| Instalação | núcleo, cerca de 23 MB | `pip install -e .` |
| Modelo | Ollama, llama.cpp ou outro servidor local | `--worker local` (ver [`LOCAL-WORKER.md`](./LOCAL-WORKER.md)) |
| Memória do agente (L4) | um ficheiro SQLite | `export L4_SQLITE=~/.pcu/memoria.db` (ou `DATABASE_URL=sqlite:///caminho.db`) |
| Estado dos runs, recibos, ledger | ficheiros na pasta do run | já é assim, não precisa de nada |
| Governança | `config/governance.yaml` e `receipts.jsonl` | já é local |

## Memória em SQLite: o que é igual e o que muda

- **Igual:** o contrato (`remember`, `recall`, `forget`, promoção por humano), as regras de âmbito e as protecções:
  factos não se editam (corrige-se com um facto novo) e nunca se apagam (tombstone `archived`). A própria base recusa
  `UPDATE` do texto e `DELETE`.
- **Muda:** a similaridade por embedding calcula-se em Python, sem pgvector. Serve para milhares de memórias, não
  para milhões. Sem embedding, o recall ordena por recência, como no Postgres.
- **Prioridade:** se `DATABASE_URL` apontar para Postgres, usa o Postgres. `L4_SQLITE` só vale sem `DATABASE_URL`.
- **Cópia de segurança:** copiar o ficheiro `.db` com o runner parado.

## Fora do perfil leve (continua a pedir Postgres)

O RAG com pgvector (`test-rag`), a ingestão de conhecimento e o MCP de produção (`agent-network-mcp`) não fazem
parte deste perfil. Não há equivalente SQLite para eles, e isto não os substitui.
