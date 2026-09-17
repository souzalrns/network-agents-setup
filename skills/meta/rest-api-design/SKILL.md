---
name: rest-api-design
action: rest_api_design
version: 1
role: meta_technique
priority: P1
---

# Skill — rest-api-design

## Trigger

Desenhar ou rever endpoints de uma API REST.

## Inputs

- Lista de recursos/endpoints a desenhar

## Passos

1. Recursos como substantivos no plural, `kebab-case` (`/api/v1/reservas`, não `/api/v1/getReserva`).
2. Sub-recursos para relações (`/api/v1/reservas/:id/itens`).
3. Versiona a API desde já (`/v1/`) para poderes evoluir sem quebrar clientes existentes.

## Done When

- [ ] Nenhum endpoint com verbo no nome (`getX`, `createX`)
- [ ] Relações modeladas como sub-recursos, não como parâmetros soltos
- [ ] API versionada desde o primeiro endpoint

## Anti-padrões

- Endpoints tipo RPC (`/getReserva`, `/updateStatus`)
- Sem versionamento desde o início
- Relações achatadas em vez de sub-recursos

## Knowledge Ref

Adaptado do skill **api-design** do ECC (Everything Claude Code, MIT).
