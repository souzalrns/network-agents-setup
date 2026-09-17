---
name: deploy-discipline
action: deploy_discipline
version: 1
role: meta_technique
priority: P1
description: >-
  Confirmar health checks e o projecto/ambiente certo antes de confiar num deploy automatico. Activar antes de qualquer deploy ou edicao de env vars de producao.
requires: []
---

# Skill — deploy-discipline

## Trigger

Fazer ou confiar num deploy automático (ex.: Vercel).

## Inputs

- Projecto/serviço a fazer deploy

## Passos

1. Plataformas como o Vercel já fazem deploy *rolling* por omissão (nova versão sobe, tráfego migra) — mas isso não substitui verificação própria.
2. Confirma sempre que endpoints de *health check* existem antes de confiar num deploy automático.
3. Nunca editar variáveis de ambiente de produção sem confirmar exactamente em qual projecto/ambiente estás — quando há vários projectos com nomes parecidos, o risco de editar o errado é real.

## Enforcement Note

Advisory -- esta skill orienta, nao aplica. Nada no runner ou no agente valida mecanicamente que estas praticas foram seguidas; a conformidade depende de quem aplica a skill.

## Done When

- [ ] Health check confirmado a existir e a responder antes do deploy
- [ ] Confirmado explicitamente qual projecto/ambiente antes de editar env vars de produção

## Anti-padrões

- Confiar em deploy automático sem health check
- Editar variável de ambiente de produção sem confirmar o projecto certo

## Knowledge Ref

Adaptado do skill **deployment-patterns** do ECC (Everything Claude Code, MIT).
