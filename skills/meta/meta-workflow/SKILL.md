---
name: meta-workflow
action: meta_workflow
version: 2
role: meta_technique
priority: P0
description: >-
  Disciplina de processo (Objetivo->Plano->Teste->Execucao->Revisao->Evidencia) para qualquer tarefa nao-trivial de codigo. Activar antes de tocar em qualquer ficheiro.
requires: []
---

# Skill — meta-workflow

## Trigger

Qualquer tarefa não-trivial que envolva escrever ou alterar código — antes de tocar em qualquer ficheiro.

## Inputs

- O pedido/tarefa a resolver
- Acesso para correr comandos de verificação (testes, build, lint)

## Passos

1. **Objetivo** — define claramente o que precisa de acontecer.
2. **Plano** — esboça a sequência de passos antes de escrever código.
3. **Teste** — identifica como vais verificar que funciona, antes de implementar.
4. **Execução** — implementa.
5. **Revisão** — relê o que fizeste.
6. **Evidência** — corre o comando de verificação NESTA sessão e mostra o output completo. "Devia funcionar" não é prova.

### Gate de evidência (antes de qualquer "está feito", "passa" ou "corrigido")

1. **Identificar** o comando que prova a afirmação.
2. **Correr** esse comando completo, agora.
3. **Ler** o output todo: código de saída e número de falhas.
4. **Afirmar** só o que o output confirma; se não confirma, dizer o estado real, com a evidência.

| Afirmação | Exige | Não chega |
|---|---|---|
| "Os testes passam" | Output do comando de testes com 0 falhas | Um run anterior; "deve passar" |
| "Lint limpo" | Output do linter com 0 erros | Verificar só uma parte |
| "Build OK" | Build com código de saída 0 | O lint passou |
| "Bug corrigido" | O sintoma original testado e a passar | Mudei o código, logo está corrigido |
| "O teste de regressão funciona" | Vermelho-verde: falha sem a correcção, passa com ela | Passou uma vez |
| "O subagente concluiu" | O diff confirma as mudanças | O relatório do subagente diz "sucesso" |
| "Requisitos cumpridos" | Lista verificada linha a linha contra o pedido | Os testes passam |

## Enforcement Note

Advisory -- esta skill orienta, nao aplica. Nada no runner ou no agente valida mecanicamente que estas praticas foram seguidas; a conformidade depende de quem aplica a skill.

## Done When

- [ ] Os 6 passos foram seguidos, nessa ordem
- [ ] Existe output real de um comando de verificação corrido nesta sessão
- [ ] Nenhuma afirmação de sucesso sem essa evidência anexada

## Anti-padrões

- Complicar uma tarefa simples
- Inventar API que não existe
- Partir algo que já funcionava
- Dizer "pronto" sem testar
- Afirmar sucesso sem evidência fresca
- Linguagem de esperança em vez de evidência ("deve", "provavelmente", "parece que")
- Confiar no relatório de um subagente sem ver o diff

## Knowledge Ref

Adaptado do projecto **obra/superpowers** (MIT) — framework de skills focado em disciplina de processo, não em conhecimento de domínio. Versão 2 (2026-10-05): o gate de evidência e a tabela vêm da skill `verification-before-completion`, v6.4.2 (commit `8ca22db`). As outras skills extraídas na mesma revisão: `receiving-code-review`, `dispatching-parallel-agents`, `subagent-driven-development` (em `skills/meta/`).
