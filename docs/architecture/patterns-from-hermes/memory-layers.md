# Memória em camadas (padrão Hermes → setup)

## O que vai aonde

| Camada | Conteúdo permitido | Conteúdo proibido | Persistência |
|--------|-------------------|-------------------|--------------|
| Constitution / SOUL | Princípios, bans, setup≠prod | Detalhes de um cliente | Git |
| Operator / USER (curto) | Preferências de trabalho estáveis | Secrets, tokens, PII sensível | Local / git privado se preciso |
| Project knowledge | marketing-base, plan-execute, Item 13 método | Chat logs | `docs/knowledge/` |
| Episódica | pilots, events.jsonl, commits | Misturar em constitution | Git / lab |
| Procedural | SKILL.md | Factos de utilizador | `skills/` |

## Carregamento

1. **Sempre:** constitution + (opcional) operator curto.  
2. **Por plan:** `knowledge_refs`.  
3. **Por passo:** skill/action body (progressive disclosure).  
4. **On-demand:** pilot anterior ou event log (não despejar o histórico inteiro).

## Compressão

Se “MEMORY” de projecto crescer: resumir lições estáveis para docs versionados; arquivar episódios em pilots — não inflacionar o system prompt.
