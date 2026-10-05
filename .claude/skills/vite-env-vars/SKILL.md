---
name: vite-env-vars
action: vite_env_vars
version: 1
role: meta_technique
priority: P2
description: >-
  Regra do prefixo VITE_ para variaveis de ambiente expostas ao cliente. Activar ao adicionar ou rever env vars num projecto Vite.
requires: []
---

# Skill — vite-env-vars

## Trigger

Adicionar ou rever variáveis de ambiente num projecto Vite.

## Inputs

- Ficheiro `.env`/`.env.*` do projecto

## Passos

1. Variáveis de ambiente só ficam expostas ao código do cliente (browser) se tiverem o prefixo `VITE_`.
2. Nunca pões uma chave sensível numa env var sem esse prefixo à espera que fique privada só por não ter o prefixo — confirma sempre o comportamento real, não assumas.
3. Nunca pões uma env var sem o prefixo `VITE_` à espera que o browser a veja — sem o prefixo, fica só do lado do build/servidor.

## Enforcement Note

Advisory -- esta skill orienta, nao aplica. Nada no runner ou no agente valida mecanicamente que estas praticas foram seguidas; a conformidade depende de quem aplica a skill.

## Done When

- [ ] Nenhuma chave sensível com prefixo `VITE_`
- [ ] Nenhuma env var que o frontend precisa de ler sem o prefixo `VITE_`

## Anti-padrões

- Chave sensível com prefixo `VITE_` (fica exposta no bundle do browser)
- Assumir que uma env var sem prefixo está disponível no cliente

## Knowledge Ref

Adaptado do skill **vite-patterns** do ECC (Everything Claude Code, MIT).
