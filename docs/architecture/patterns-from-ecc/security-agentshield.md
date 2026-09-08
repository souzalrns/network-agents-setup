# AgentShield e segurança de harness

## O que scaneia (classe de regras)

- Secrets em config  
- Permissions / tools excessivas  
- Hook injection (interpolação shell, exfiltração curl, `2>/dev/null` a esconder falhas)  
- MCP server risks  
- Prompt injection vectors em agent files  
- SessionStart que descarrega e executa remoto  

## Providências

| ID | Regra |
|----|--------|
| E-SEC-01 | Antes de hooks em prod: scan tipo AgentShield (`npx ecc-agentshield` em lab OK) |
| E-SEC-02 | Hooks: sem interpolação não sanitizada de input de user/file |
| E-SEC-03 | Falha de hook de segurança **não** pode ser silenciada |
| E-SEC-04 | MCP: least privilege; review de servers novos |
| E-SEC-05 | Install ECC/outros **só** canais oficiais |
| E-SEC-06 | Não empilhar dois métodos de install no mesmo harness |

Lab: correr scan no `.claude/` / configs do bridge **antes** de productionize.
