---
name: nestjs-modules
action: nestjs_modules
version: 1
role: meta_technique
priority: P1
description: >-
  Onde colocar codigo novo num projecto NestJS -- modulos por dominio, logica transversal em common/, configuracao validada. Activar ao decidir estrutura de pastas NestJS.
requires: []
---

# Skill — nestjs-modules

## Trigger

Decidir onde colocar código novo num projecto NestJS.

## Inputs

- Estrutura de pastas actual do projecto NestJS

## Passos

1. Organiza por módulos de domínio (ex.: `modules/reservas`, `modules/pedidos`), cada um com `controller`, `service`, `module` e `dto/` próprios.
2. Lógica transversal (filters, guards, interceptors, pipes) vai em `common/`.
3. Configuração validada fica em `config/`.

## Enforcement Note

Advisory -- esta skill orienta, nao aplica. Nada no runner ou no agente valida mecanicamente que estas praticas foram seguidas; a conformidade depende de quem aplica a skill.

## Done When

- [ ] Código novo colocado dentro do módulo de domínio certo, não espalhado
- [ ] Lógica transversal não duplicada dentro de um módulo específico
- [ ] Configuração validada, não lida directamente de `process.env` espalhado pelo código

## Anti-padrões

- Meter lógica transversal (guards, filters) dentro de um módulo de domínio
- Duplicar `dto`/`service` em vez de reutilizar `common/`
- Ler `process.env` directamente fora de `config/`

## Knowledge Ref

Adaptado do skill **nestjs-patterns** do ECC (Everything Claude Code, MIT).
