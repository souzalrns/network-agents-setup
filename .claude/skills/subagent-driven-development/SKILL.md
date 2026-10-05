---
name: subagent-driven-development
action: subagent_driven_development
version: 1
role: meta_technique
priority: P1
description: >-
  Executar um plano com tarefas independentes despachando um subagente novo por tarefa, com review de cada tarefa (cumpre a spec + qualidade) e um review final do branch inteiro. Activar quando ha um plano aprovado e uma ferramenta de subagentes disponivel.
requires: []
---

# Skill — subagent-driven-development

## Trigger

Há um plano de implementação aprovado, com tarefas maioritariamente independentes, e uma ferramenta de subagentes disponível. Sem subagentes, ou com tarefas muito acopladas, executar o plano directamente (skill `meta-workflow`).

## Inputs

- O plano (tarefas, ordem, critério de "feito" de cada uma)
- A spec ou a decisão que o plano implementa

## Passos

1. **Por tarefa, despachar um implementador novo**, com um prompt auto-suficiente: a tarefa, a spec relevante, os ficheiros, as restrições e o critério de "feito". O subagente não herda o contexto da sessão.
2. **Tratar o relatório:** ler o diff, não só o resumo.
3. **Rever a tarefa** em 2 eixos: cumpre a spec (nem mais, nem menos)? Qualidade (testes, legibilidade, sem regressões)?
4. **Ciclo de correcção:** se o review encontrar falhas, devolver ao implementador (ou a um novo) com os achados concretos; repetir até passar.
5. **Fechar a tarefa** só com evidência (testes corridos depois do review).
6. **Review final do branch inteiro**, antes de propor o PR: coerência entre tarefas, nada esquecido do plano.

## Regras deste repo (sobrepõem-se ao original)

O original manda executar o plano todo sem parar e decidir sozinho os conflitos. **Aqui não:**
- **Parar e perguntar** em: decisões que são do maestro (opções A/B/C, `PENDENCIAS.md` §10), merges, escrita em produção (Supabase, Vercel, workflows que escrevem), operações irreversíveis ou destrutivas e acções sensíveis de segurança.
- **Não reabrir** decisões fechadas; um conflito entre o plano e uma decisão do §10 resolve-se a favor da decisão, e regista-se.
- Dentro do que já está decidido, avançar sem pedir confirmação a cada tarefa, e registar as escolhas menores (com o porquê) no diário (`docs/ops/PROGRESS-SESSAO.md`).

## Enforcement Note

Advisory -- esta skill orienta, nao aplica. O relatorio de um subagente nao e evidencia; o review e os testes sao.

## Done When

- [ ] Cada tarefa teve implementador novo, review (spec + qualidade) e evidência de testes
- [ ] O review final do branch foi feito antes do PR
- [ ] Nenhuma decisão do maestro foi tomada pelo agente

## Anti-padrões

- Um só contexto a fazer todas as tarefas e a acumular ruído
- Saltar o review por tarefa e só rever no fim
- Aceitar "concluído" do subagente sem ler o diff
- Usar "execução contínua" como desculpa para decidir o que é do maestro

## Knowledge Ref

Adaptado de `obra/superpowers` (MIT), skill `subagent-driven-development`, v6.4.2 (commit `8ca22db`). Resumido; a secção "Regras deste repo" substitui as regras de execução contínua do original, que contrariam a governança do maestro.
