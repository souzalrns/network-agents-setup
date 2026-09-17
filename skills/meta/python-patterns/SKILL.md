---
name: python-patterns
action: python_patterns
version: 1
role: meta_technique
priority: P1
description: >-
  Codigo Python legivel, com type hints e docstrings em calculo de dominio. Activar ao escrever codigo Python, sobretudo com calculo de engenharia.
requires: []
---

# Skill — python-patterns

## Trigger

Escrever código Python, sobretudo com cálculo de engenharia/domínio.

## Inputs

- Código Python a escrever/rever

## Passos

1. Código legível antes de código esperto — nomes claros, funções pequenas e com type hints.
2. Prefere list/dict comprehensions simples a loops manuais, quando não perdem legibilidade.
3. Docstrings nas funções que fazem cálculo de domínio, para se recuperar o raciocínio depois sem ter de o reconstruir.

## Enforcement Note

Advisory -- esta skill orienta, nao aplica. Nada no runner ou no agente valida mecanicamente que estas praticas foram seguidas; a conformidade depende de quem aplica a skill.

## Done When

- [ ] Funções pequenas, com type hints
- [ ] Comprehensions usadas onde tornam o código mais legível (não onde o complicam)
- [ ] Funções de cálculo de domínio com docstring explicando o raciocínio

## Anti-padrões

- Código "esperto" ilegível em vez de claro
- Comprehension aninhada que piora a legibilidade
- Função de cálculo sem docstring, obrigando a reconstruir o raciocínio depois

## Knowledge Ref

Adaptado do skill **python-patterns** do ECC (Everything Claude Code, MIT).
