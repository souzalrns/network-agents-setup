---
name: dispatching-parallel-agents
action: dispatching_parallel_agents
version: 1
role: meta_technique
priority: P1
description: >-
  Quando ha 2+ problemas independentes (sem estado partilhado nem dependencias), despachar um subagente por dominio, em paralelo, com um prompt focado e auto-suficiente; depois rever, verificar conflitos e correr a suite completa. Activar perante varias falhas ou tarefas independentes.
requires: []
---

# Skill — dispatching-parallel-agents

## Trigger

Há 2 ou mais tarefas ou falhas **independentes** (ficheiros de teste diferentes, subsistemas diferentes, causas diferentes) que se percebem sem o contexto umas das outras.

**Não usar** quando as falhas estão relacionadas (corrigir uma pode corrigir as outras), quando é preciso ver o sistema inteiro, em debugging exploratório (ainda não se sabe o que está partido) ou quando os subagentes mexeriam nos mesmos ficheiros ou recursos.

## Inputs

- A lista de problemas, agrupada por domínio
- Para cada um: mensagens de erro, nomes dos testes, ficheiros envolvidos

## Passos

1. **Agrupar por domínio independente** (ex.: um ficheiro de teste ou um subsistema por grupo).
2. **Escrever um prompt por subagente**, com:
   - **âmbito específico** (um domínio);
   - **objectivo claro** (ex.: "pôr estes 3 testes a passar");
   - **todo o contexto necessário**, colado no prompt (o subagente não herda a sessão);
   - **restrições** ("não mexer em código de produção", "não aumentar timeouts: encontrar a causa");
   - **saída esperada** ("devolve a causa raiz e o que mudaste").
3. **Despachar em paralelo:** todas as chamadas na mesma resposta (uma por resposta é sequencial).
4. **Integrar:** ler cada resumo; verificar se 2 subagentes mexeram no mesmo código; correr a suite completa; só então integrar.

## Enforcement Note

Advisory -- esta skill orienta, nao aplica. O relatorio de um subagente nao e evidencia: confirma-se pelo diff e por testes corridos depois.

## Done When

- [ ] Cada subagente teve um domínio independente e um prompt auto-suficiente
- [ ] O diff de cada um foi lido (não só o resumo)
- [ ] A suite completa passou depois de integrar tudo

## Anti-padrões

- Âmbito largo ("corrige os testes todos"): o subagente perde-se
- Prompt sem contexto ("corrige a race condition"): não sabe onde
- Sem restrições: o subagente refaz meio repo
- Saída vaga ("corrige"): não se sabe o que mudou
- Confiar no "sucesso" relatado sem ver o diff e correr os testes

## Knowledge Ref

Adaptado de `obra/superpowers` (MIT), skill `dispatching-parallel-agents`, v6.4.2 (commit `8ca22db`). Resumido.
