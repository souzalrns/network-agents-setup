---
name: python-patterns
action: python_patterns
version: 1
role: meta_technique
priority: P1
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
