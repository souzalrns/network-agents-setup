---
name: frontend-a11y
action: frontend_a11y
version: 1
role: meta_technique
priority: P1
---

# Skill — frontend-a11y

## Trigger

Escrever ou rever markup/componentes de frontend.

## Inputs

- Componente(s)/página(s) a rever

## Passos

1. Todo `<input>` precisa de label associado (`htmlFor`/`id`).
2. Elementos interactivos custom precisam de `role` e suporte a teclado — não só `onClick` num elemento não-semântico.
3. Cuidado com *Cumulative Layout Shift* em imagens sem `width`/`height` definidos — afecta Core Web Vitals (e por sua vez SEO).

## Done When

- [ ] Todo `<input>` tem label associado
- [ ] Elementos clicáveis custom navegáveis por teclado
- [ ] Imagens com dimensões definidas

## Anti-padrões

- `<input>` sem label
- Elemento clicável sem suporte a teclado
- Imagens sem `width`/`height`

## Knowledge Ref

Adaptado do skill **frontend-a11y** do ECC (Everything Claude Code, MIT).
