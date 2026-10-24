---
name: follow_up
description: "Revê propostas e negócios parados (dias sem resposta, último contacto, próximo passo combinado) e redige follow-ups com um motivo novo e uma cadência que respeita quem pede para parar. Prepara: um humano revê e envia."
action: follow_up
version: 1
vertical: marketing
priority: P1
item_13: false
---

# Skill — follow_up

## Contrato do runner (obrigatório)

- Prepara; não envia mensagens nem altera o pipeline (`act_in_production: forbidden`; gate `plan_approve`).
- **Quem pediu para parar não recebe mais nada** (RGPD art. 21.º; LGPD art. 18.º): o negócio sai da lista com o motivo.
- Dados pessoais: só os do pipeline do plano. Nunca enriquecer contactos com fontes externas.
- Sem pressão: nada de urgência inventada, culpa ou "última oportunidade" falsa.
- A mensagem sai na língua do cliente (PT-PT ou PT-BR).

## Quando usar

- Passo `action: follow_up` sobre uma lista de propostas ou negócios em aberto (pipeline), ou para preparar a sequência de seguimento de uma proposta nova.

## Não usar

- Primeiro contacto a frio (isso é `cold_email` / `prospecting`).
- Enviar, agendar envios ou marcar reuniões.

## Grounding

- O pipeline (cliente, data da proposta, último contacto, próximo passo combinado, opt-out) vem dos `inputs` ou de `repo_files` do passo.
- A data de referência é a do plano (ou a de hoje, se o plano não disser); dias parados contam-se a partir do último contacto.

## Processo

1. Para cada negócio: dias desde o último contacto, próximo passo combinado e se já passou.
2. Classificar: `em dia` (nada a fazer), `follow-up` (parado, com motivo novo possível), `fechar` (sem resposta após a cadência completa) ou `parar` (pediu para parar ou disse que não).
3. Cadência por omissão, se o plano não der outra: D+3, D+7, D+14 a contar do envio; depois, uma mensagem de fecho educada que deixa a porta aberta.
4. Cada follow-up tem **um motivo novo**: responder a uma dúvida provável, uma informação útil, uma data concreta. Nunca "só para saber se viu".
5. Rascunho curto (≤ 80 palavras), com um só pedido claro.

## Saída

Markdown em `output_artifact`:

```markdown
# Follow-ups — <data de referência>

## Resumo
| Negócio | Dias parado | Estado (em dia/follow-up/fechar/parar) | Próximo contacto |
## Rascunhos
### <negócio>
- Motivo novo:
- Mensagem:
## Parar ou fechar (com o motivo)
## Lacunas
```

## done_when

- [ ] Todos os negócios do pipeline classificados
- [ ] Cada follow-up com um motivo novo explícito
- [ ] Nenhum rascunho para quem pediu para parar
- [ ] Nada marcado como "enviado"

## Anti-padrões

- "Só a confirmar se recebeu" sem motivo
- Mais de um pedido na mesma mensagem
- Inventar interesse do cliente ou prazos do negócio
