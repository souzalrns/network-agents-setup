# Memory Vault ECC → L4 / handoff

## Contrato ECC (resumo)

- Formato **`ecc.memory.v1`** legível por humanos  
- **Markdown = source of truth**; SQLite/embeddings = índices  
- Project/team: `.ecc/memory/` · User: `~/.ecc/memory/`  
- CLI + MCP stdio opcional: create/read/search/doctor  
- MCP **sem** tool de promote/review (humano governa)  
- Adapters de harness **finos**  

## Mapa para a nossa memória

| ECC | Nosso |
|-----|--------|
| User vault | L4 scope `user` |
| Project vault | L4 scope `project` |
| Team commit de memória | human gate → active |
| Agent writes unreviewed | `status: candidate` |
| Handoff entre harnesses | multi-plataforma + mesmo subject/run |
| Procedural em rules/instincts | L0 + L3 |
| Session distill | L2 → candidate L4 |

## Providência adoptada

1. Preferir **ficheiros auditáveis** para L4 lab antes de vector-only.  
2. `remember` default **candidate**.  
3. Promote/forget = humano ou policy explícita.  
4. Não um único vector store para todos os roles (isolamento por scope — lição alinhada a multi-KB).  
