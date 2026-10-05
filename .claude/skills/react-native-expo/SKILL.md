---
name: react-native-expo
action: react_native_expo
version: 1
role: meta_technique
priority: P1
description: >-
  Padroes Expo Router e separacao de estado num app React Native. Activar ao trabalhar num app com Expo Router.
requires: []
---

# Skill — react-native-expo

## Trigger

Trabalhar num app React Native com Expo Router.

## Inputs

- Estrutura de rotas/ecrãs do app

## Passos

1. Routing por ficheiros com Expo Router — mantém os ficheiros de rota finos (só leem/validam params e delegam a um componente de ecrã).
2. Separa claramente: estado de servidor (ex.: TanStack Query), estado de cliente, params de rota, e estado de formulário — não misturar tudo em `useState`.
3. Não assumas padrões de browser (não há `<div>`, não há URL bar) — isto não é React web.

## Enforcement Note

Advisory -- esta skill orienta, nao aplica. Nada no runner ou no agente valida mecanicamente que estas praticas foram seguidas; a conformidade depende de quem aplica a skill.

## Done When

- [ ] Ficheiros de rota finos, sem lógica de negócio dentro deles
- [ ] Estado de servidor, cliente, rota e formulário claramente separados
- [ ] Nenhum padrão assumido de browser web

## Anti-padrões

- Lógica de negócio directamente no ficheiro de rota
- Misturar estado de servidor com estado local no mesmo `useState`
- Assumir elementos/comportamento de browser web

## Knowledge Ref

Adaptado do skill **react-native-patterns** do ECC (Everything Claude Code, MIT).
