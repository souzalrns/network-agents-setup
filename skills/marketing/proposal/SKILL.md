---
name: proposal
description: "Transforma o brief de um cliente numa proposta comercial pronta a rever (âmbito incluído e excluído, entregáveis, prazos, preço só com dados fornecidos, condições) e no email de envio. Prepara: um humano revê, completa e envia."
action: proposal
version: 1
vertical: marketing
priority: P1
item_13: false
---

# Skill — proposal

## Contrato do runner (obrigatório)

- Prepara; não envia, não publica e não compromete o negócio (`act_in_production: forbidden`; gate `plan_approve`).
- **Nunca inventar** preço, prazo, desconto, garantia, referência de cliente ou certificação. O que não vier no plano fica `[[A DEFINIR: o quê]]` e entra em "Lacunas".
- Dados pessoais: só os do pedido, só para responder a esse pedido (RGPD art. 6.º, n.º 1, al. b); LGPD art. 7.º, V). Não copiar dados do cliente para fora do artefacto.
- Negócios com sigilo profissional (ex.: advocacia): a proposta não cita factos do caso para além do necessário ao âmbito, e respeita as regras deontológicas indicadas no contexto do negócio.
- A peça sai na língua do pedido (PT-PT ou PT-BR, conforme o cliente).

## Quando usar

- Passo `action: proposal` depois de um pedido qualificado (`lead_qualification`) ou de um brief do maestro.

## Não usar

- Enviar a proposta ou marcar reuniões.
- Calcular preços sem tabela ou valores no plano.
- Material de vendas genérico (one-pagers, decks): isso é `sales_enablement`.

## Grounding

- O pedido do cliente e o contexto do negócio vêm dos `inputs` ou de `repo_files` do passo (incluindo a qualificação anterior, se existir).
- Preços, prazos e condições: só de uma tabela ou de valores explícitos no plano.

## Processo

1. Reescrever o pedido em 2–3 frases, com as palavras do cliente (o que quer, onde, quando).
2. Definir o âmbito: o que está **incluído** e o que está **excluído** (as exclusões evitam disputas).
3. Listar entregáveis e marcos; prazos só se houver dados, senão `[[A DEFINIR]]`.
4. Preço: linha a linha a partir da tabela do plano, com o total e o que depende de visita ou medição; IVA indicado à parte quando o contexto o disser.
5. Condições: validade da proposta, pagamento, o que o cliente tem de garantir; só as do contexto.
6. Próximo passo único e concreto (ex.: "confirmar a visita técnica numa destas datas").
7. Email de envio curto (≤ 120 palavras), que diz o que vai em anexo e o próximo passo.
8. Lacunas: tudo o que o humano tem de completar antes de enviar.

## Saída

Markdown em `output_artifact`:

```markdown
# Proposta — <cliente/projecto>

## O pedido (nas palavras do cliente)
## Âmbito
### Incluído
### Excluído
## Entregáveis e prazos
## Preço
| Item | Qtd | Preço unit. | Total | Fonte (tabela/linha) |
## Condições
## Próximo passo
## Email de envio (rascunho)
## Lacunas a completar antes de enviar
```

## done_when

- [ ] Cada preço tem fonte (tabela/linha do plano) ou está `[[A DEFINIR]]`
- [ ] Âmbito com incluído e excluído
- [ ] Um só próximo passo, concreto
- [ ] Lacunas listadas; nada marcado como "enviado"

## Anti-padrões

- Preço "de mercado" ou "aproximado" sem fonte
- Promessas de prazo que o plano não dá
- Urgência falsa ("só hoje") ou descontos não autorizados
- Copiar o pedido inteiro, com dados pessoais, para o email
