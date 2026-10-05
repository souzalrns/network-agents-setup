---
name: prisma-patterns
action: prisma_patterns
version: 1
role: meta_technique
priority: P1
description: >-
  Armadilhas conhecidas do Prisma sobre PostgreSQL directo (sem Supabase) -- updateMany, transaccoes, migrations, soft-delete, connection pooling. Activar ao escrever ou rever codigo Prisma.
requires: []
---

# Skill — prisma-patterns

## Trigger

Trabalhar com Prisma directamente sobre PostgreSQL (sem Supabase por baixo).

## Inputs

- `schema.prisma` do projecto
- Código que já usa `PrismaClient`

## Passos

1. `updateMany`/`deleteMany` devolvem só `{ count }`, nunca os registos — se precisares dos registos afectados, captura os IDs com `findMany` antes, actualiza, e vai buscar de novo pelos IDs.
2. `$transaction` interactivo (callback) expira aos 5s por omissão — nunca fazer chamadas externas (email, APIs) dentro da transacção; se for processamento em lote genuíno, sobe o timeout explicitamente.
3. `migrate dev` pode resetar a base de dados ao detectar drift — nunca correr em staging/produção partilhada, só `migrate deploy` nesses ambientes.
4. Editar um ficheiro de migration já aplicado quebra checksums (erro P3006) em todos os outros ambientes — cria sempre uma migration nova.
5. `@updatedAt` não dispara em `updateMany`/bulk writes — define `updatedAt: new Date()` manualmente nesses casos.
6. `findUniqueOrThrow` não detecta soft-delete (linha existe, só está marcada) — usa `findFirstOrThrow` com `deletedAt: null` quando há soft delete no modelo.
7. Em serverless (se algum endpoint correr assim), usar `connection_limit=1` com pooler externo, para não esgotar ligações.

## Enforcement Note

Advisory -- esta skill orienta, nao aplica. Nada no runner ou no agente valida mecanicamente que estas praticas foram seguidas; a conformidade depende de quem aplica a skill.

## Done When

- [ ] Nenhum `updateMany`/`deleteMany` a assumir que devolve os registos
- [ ] Nenhuma chamada externa dentro de `$transaction` interactivo sem timeout ajustado
- [ ] Nenhum `migrate dev` em ambiente partilhado
- [ ] Nenhum ficheiro de migration já aplicado editado directamente

## Anti-padrões

- Assumir que `updateMany` devolve os registos alterados
- Chamar API externa dentro de transacção sem subir o timeout
- Correr `migrate dev` em staging/produção
- Editar migration já aplicada em vez de criar uma nova
- Confiar em `findUniqueOrThrow` para modelos com soft-delete

## Knowledge Ref

Adaptado do skill **prisma-patterns** do ECC (Everything Claude Code, MIT).
