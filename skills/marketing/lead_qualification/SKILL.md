---
name: lead_qualification
description: "Qualifica pedidos que chegam (formulário, email, WhatsApp) contra os critérios do negócio — encaixe, necessidade, prazo, orçamento declarado, decisor — com evidência citada, e propõe a resposta e a próxima acção. Prepara: um humano responde."
action: lead_qualification
version: 1
vertical: marketing
priority: P1
item_13: false
---

# Skill — lead_qualification

## Contrato do runner (obrigatório)

- Prepara; não responde, não marca reuniões e não cria registos (`act_in_production: forbidden`; gate `plan_approve`).
- **Orçamento e decisor só se o pedido os disser.** Inferir pelo nome, morada, profissão ou forma de escrever é proibido: fica `lacuna`.
- Dados pessoais: só os do pedido, para responder a esse pedido (RGPD art. 6.º, n.º 1, al. b); LGPD art. 7.º, V). Nada de pesquisar a pessoa fora do pedido.
- Negócios com sigilo profissional (ex.: advocacia): a qualificação não copia factos do caso para além do necessário, e um pedido urgente de natureza jurídica vai sempre para o humano.
- A resposta proposta sai na língua do pedido (PT-PT ou PT-BR).

## Quando usar

- Passo `action: lead_qualification` sobre um ou mais pedidos inbound, antes da proposta.

## Não usar

- Listas de prospects a frio (isso é `prospecting`).
- Decidir preços ou prometer disponibilidade.

## Grounding

- O pedido vem dos `inputs` ou de `repo_files` do passo, tal como chegou.
- Os critérios do negócio (serviços, zona, mínimos, o que não faz) vêm do contexto do plano. Sem critérios, usar os da secção Processo e dizê-lo.

## Processo

1. Encaixe: o serviço pedido está no que o negócio faz? A zona é servida? Citar a frase.
2. Necessidade: há um problema concreto ou é curiosidade?
3. Prazo: o cliente disse quando? (`declarado` / `lacuna`)
4. Orçamento: o cliente disse um valor ou intervalo? (`declarado` / `lacuna`; nunca estimado)
5. Decisor: quem decide, se o pedido o disser (`declarado` / `lacuna`).
6. Classificar: `quente` (encaixa, necessidade e prazo claros), `morno` (encaixa, falta informação), `frio` (encaixe fraco ou sem necessidade concreta), `fora de âmbito` (o negócio não faz isto: sugerir a quem encaminhar, se o contexto o disser).
7. Propor a resposta (≤ 120 palavras) com as perguntas que fecham as lacunas, e a próxima acção (ex.: proposta, visita técnica com datas a confirmar pelo humano, encaminhar).

## Saída

Markdown em `output_artifact`:

```markdown
# Qualificação — <pedido>

## O pedido (resumo, sem dados a mais)
## Critérios
| Critério | Resultado | Evidência (frase do pedido) |
## Classificação: <quente/morno/frio/fora de âmbito>
## Resposta proposta (rascunho)
## Próxima acção
## Lacunas
```

## done_when

- [ ] Cada critério com evidência citada ou `lacuna`
- [ ] Orçamento e decisor nunca estimados
- [ ] Uma classificação e uma próxima acção
- [ ] Nada respondido nem marcado

## Anti-padrões

- "Cliente com poder de compra" deduzido da morada ou do email
- Classificar como quente sem prazo nem necessidade
- Prometer datas ou preços na resposta
