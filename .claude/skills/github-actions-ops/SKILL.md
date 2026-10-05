---
name: github-actions-ops
action: github_actions_ops
version: 1
role: meta_technique
priority: P1
description: >-
  Diagnostico de falhas de workflow do GitHub Actions -- distinguir falha transitoria de erro de logica. Activar ao investigar um run que falhou.
requires: []
---

# Skill — github-actions-ops

## Trigger

Diagnosticar uma falha de workflow do GitHub Actions.

## Inputs

- Run que falhou (link/id)

## Passos

1. Antes de assumir que um workflow falhou por erro de lógica, verifica se foi falha transitória — um *rerun* costuma resolver.
2. Logs detalhados de steps ficam em blob storage (não na API do GitHub) — quando precisares de depurar a fundo, pode ser preciso correr localmente em vez de tentar ler o log completo via API.

## Enforcement Note

Advisory -- esta skill orienta, nao aplica. Nada no runner ou no agente valida mecanicamente que estas praticas foram seguidas; a conformidade depende de quem aplica a skill.

## Done When

- [ ] Confirmado se é falha transitória (rerun) antes de investigar como erro de lógica
- [ ] Se precisar de log detalhado e a API não o der, corrido localmente em vez de assumir

## Anti-padrões

- Assumir erro de lógica sem primeiro tentar rerun
- Insistir em ler log detalhado via API do GitHub quando ele está em blob storage externo

## Knowledge Ref

Sem atribuição externa explícita no agente de origem (mesma situação da skill mcp-patterns — não há nome de skill ECC citado para esta técnica no texto original).
