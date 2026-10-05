---
name: react-patterns
action: react_patterns
version: 1
role: meta_technique
priority: P1
description: >-
  Padroes React para estado derivado, waterfalls, listas longas e acessibilidade basica. Activar ao escrever ou rever componentes React web.
requires: []
---

# Skill — react-patterns

## Trigger

Escrever ou rever componentes React (web).

## Inputs

- Componente(s) a escrever/rever

## Passos

1. Deriva estado durante o render em vez de o duplicar em `useState`+`useEffect` quando dá para calcular a partir de props/state já existente.
2. Evita *waterfalls* — não faças `await` sequencial de coisas independentes; dispara-as em paralelo.
3. Em listas longas, cuidado com re-renders desnecessários — usa `memo`/`key` estável.
4. Todo `<input>` precisa de label associado (`htmlFor`/`id`).
5. Todo elemento clicável custom precisa de `role` e suporte a teclado — não só `onClick` num `<div>`.
6. Cuidado com *Cumulative Layout Shift* em imagens sem `width`/`height` definidos — afecta Core Web Vitals.

## Enforcement Note

Advisory -- esta skill orienta, nao aplica. Nada no runner ou no agente valida mecanicamente que estas praticas foram seguidas; a conformidade depende de quem aplica a skill.

## Done When

- [ ] Nenhum estado derivável duplicado em `useState`
- [ ] Nenhum `await` sequencial de operações independentes
- [ ] Elementos interactivos custom têm `role` + suporte a teclado
- [ ] Imagens têm `width`/`height` definidos

## Anti-padrões

- Guardar em `useState` algo que dá para calcular de props/state existente
- `await` em série para coisas que não dependem umas das outras
- `onClick` num `<div>` sem `role`/teclado
- Imagens sem dimensões definidas

## Knowledge Ref

Adaptado dos skills **react-patterns**, **react-performance** e **frontend-a11y** do ECC (Everything Claude Code, MIT).
