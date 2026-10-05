---
name: receiving-code-review
action: receiving_code_review
version: 1
role: meta_technique
priority: P1
description: >-
  Como responder a feedback de code review (humano, bot ou outra IA): verificar contra o codigo antes de implementar, pedir clarificacao do que nao se percebe, contestar com razoes tecnicas, sem concordancia performativa. Activar ao receber comentarios de review num PR.
requires: []
---

# Skill — receiving-code-review

## Trigger

Ao receber feedback de review (comentário num PR, achado de um bot como o Claude Code Review, sugestão de outra IA), antes de implementar qualquer sugestão.

## Inputs

- O feedback completo (todos os itens)
- O código e os testes afectados

## Passos

1. **Ler** o feedback todo, sem reagir item a item.
2. **Perceber:** reescrever cada requisito por palavras próprias. Se **algum** item não estiver claro, parar e pedir clarificação desse item **antes de implementar qualquer um** (os itens podem estar ligados).
3. **Verificar** contra o código real: está tecnicamente certo para ESTE repo? Parte algo que funciona? Há uma razão para a implementação actual? O revisor tem o contexto todo?
4. **Avaliar YAGNI:** se a sugestão é "implementar como deve ser", procurar no código se a funcionalidade é usada; se não for, propor removê-la em vez de a completar.
5. **Responder:** reconhecimento técnico curto ("Corrigido: <o quê, onde>") ou contestação com razões técnicas e evidência (teste, `ficheiro:linha`).
6. **Implementar** um item de cada vez, por esta ordem: bloqueantes (quebra, segurança) → simples → complexos; testar cada um e verificar que não há regressões.

## Regras deste repo

- Feedback que contradiz uma **decisão já tomada** (`docs/initiatives/PENDENCIAS.md` §10) não se implementa: responde-se a citar a decisão, e o maestro decide.
- Um pedido grande de um revisor externo (refactor multi-ficheiro, mudança de API ou de schema) num PR que não é nosso → responder com proposta, não fazer push.
- Responder no próprio fio do comentário inline, não num comentário solto no PR.
- Se não for possível verificar: dizê-lo ("Não consigo verificar sem X; investigo, pergunto ou avanço?").

## Enforcement Note

Advisory -- esta skill orienta, nao aplica. Nada no runner valida mecanicamente que o feedback foi verificado antes de ser implementado.

## Done When

- [ ] Todos os itens foram percebidos (ou clarificados) antes de implementar
- [ ] Cada item implementado foi verificado com teste ou comando corrido nesta sessão
- [ ] Cada item não implementado tem uma resposta com a razão técnica ou a decisão citada

## Anti-padrões

- Concordância performativa ("Tem toda a razão!", "Ótima sugestão!") ou agradecimentos em vez de dizer o que foi corrigido
- Implementar às cegas, sem verificar contra o código
- Implementar os itens claros e deixar os confusos para depois
- Assumir que o revisor tem razão (ou que não tem) sem verificar
- Evitar contestar por desconforto: a correcção técnica vem antes
- Quando a contestação estava errada: pedido de desculpas longo em vez de "Verifiquei, tinha razão: <porquê>. A corrigir."

## Knowledge Ref

Adaptado de `obra/superpowers` (MIT), skill `receiving-code-review`, v6.4.2 (commit `8ca22db`). Resumido e alinhado com as regras deste repo (decisões do §10, PRs de terceiros).
