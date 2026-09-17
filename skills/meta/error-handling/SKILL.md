---
name: error-handling
action: error_handling
version: 1
role: meta_technique
priority: P1
description: >-
  Tratamento de erros -- falhar rapido, erros tipados, separar mensagem de utilizador de mensagem de developer. Activar ao escrever ou rever blocos try/catch.
requires: []
---

# Skill — error-handling

## Trigger

Escrever ou rever tratamento de erros em qualquer camada de código.

## Inputs

- Código com blocos `try`/`catch` (ou equivalente) a rever

## Passos

1. Falha rápido e alto — não engolir erros em silêncio; todo `catch` tem de tratar, relançar, ou fazer log.
2. Usa erros como classes tipadas em vez de strings soltas.
3. Mensagem para o utilizador ≠ mensagem para o developer — mostra texto amigável ao utilizador final, regista o contexto completo no servidor.
4. Documenta cada código de erro que um cliente da API pode receber.

## Enforcement Note

Advisory -- esta skill orienta, nao aplica. Nada no runner ou no agente valida mecanicamente que estas praticas foram seguidas; a conformidade depende de quem aplica a skill.

## Done When

- [ ] Nenhum `catch` vazio ou que só faz `console.log`
- [ ] Erros representados como classes/tipos, não strings
- [ ] Mensagem ao utilizador não expõe detalhe interno (stack trace, nome de tabela, etc.)
- [ ] Códigos de erro documentados

## Anti-padrões

- `catch` vazio ("engolir" o erro)
- Strings soltas em vez de erros tipados
- Mostrar stack trace ou detalhe interno ao utilizador final
- Códigos de erro sem documentação

## Knowledge Ref

Adaptado do skill **error-handling** do ECC (Everything Claude Code, MIT).
