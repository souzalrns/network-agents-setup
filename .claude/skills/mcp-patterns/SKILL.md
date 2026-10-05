---
name: mcp-patterns
action: mcp_patterns
version: 1
role: meta_technique
priority: P1
description: >-
  Boas praticas para tools de servidor MCP -- schema de input validado, erros estruturados, idempotencia. Activar ao construir ou alterar um servidor MCP.
requires: []
---

# Skill — mcp-patterns

## Trigger

Construir ou alterar um servidor MCP (ex.: com `mcp-handler` + Zod).

## Inputs

- Definição de tools do servidor MCP

## Passos

1. Define sempre um schema de input para cada tool, com Zod (ou equivalente de validação tipada).
2. Devolve erros estruturados que o modelo consiga interpretar, em vez de stack traces cruas.
3. Prefere tools idempotentes, para retries serem seguros.
4. Documenta rate limits/custo na própria descrição da tool, quando ela chama uma API externa.

## Enforcement Note

Advisory -- esta skill orienta, nao aplica. Nada no runner ou no agente valida mecanicamente que estas praticas foram seguidas; a conformidade depende de quem aplica a skill.

## Done When

- [ ] Toda tool tem schema de input validado
- [ ] Erros devolvidos como texto interpretável, não stack trace
- [ ] Tools que chamam API externa idempotentes ou documentadas como não-idempotentes

## Anti-padrões

- Tool sem schema de input
- Devolver stack trace cru como resposta de erro
- Tool que muda estado de forma não-idempotente sem aviso na descrição

## Knowledge Ref

Sem atribuição externa explícita no agente de origem (o texto original diz apenas "relevante para este próprio repo, que usa mcp-handler + Zod") — a diferença dos outros 15, aqui não há um nome de skill ECC citado no texto de origem.
