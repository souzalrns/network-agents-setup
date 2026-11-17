---
name: research
description: "Monta o dossiê de investigação de uma pauta: contexto com ligações, cronologia, fontes primárias a consultar, perguntas em aberto e perguntas para entrevista; não escreve o artigo nem dá nada por confirmado."
action: editorial_research
version: 1
vertical: editorial
priority: P0
---

# Skill — Investigação

## Quando usar

- Numa redacção montada sobre a vertical editorial, para uma peça ou para o radar da publicação.

## O que faz

- Junta as referências da peça e as entradas do radar ligadas, com títulos parecidos ou as mesmas etiquetas.
- Constrói uma cronologia a partir das datas desse material.
- Sugere fontes primárias por consultar (INE, PORDATA, Diário da República, Portal BASE, Parlamento, Eurostat,
  Portal Autárquico, RCAAP), sempre como «por consultar», nunca como factos.
- Lista perguntas em aberto e perguntas para entrevista.
- Com modelo: resume só o material dado; cada ponto cita os itens que o sustentam (URL inventada = resposta rejeitada).

## Regras (impostas no código, não só aqui)

- **Propõe, nunca decide.** A saída é uma proposta (`proposal: true`) que uma pessoa aproveita ou descarta.
  O agente não aprova, não agenda, não publica e não altera o texto, os títulos ou as citações de uma peça.
- **Quatro tipos de afirmação** em todas as saídas: facto documentado (só fica verificado por uma pessoa, com
  evidência), declaração (diz sempre quem declarou), inferência (hipótese) e informação não confirmada (não vai
  para o artigo). Repetição noutros meios nunca torna uma afirmação verificada.
- **Fontes protegidas:** o agente não vê fontes, contactos nem comentários da redacção (RLS na base de dados).
- **Só o material dado:** o modelo, quando há, cita só o material entre `<material>`; o resto fica `unconfirmed`.
- **Limites:** chamadas, tokens de saída e custo em USD por execução (`EDITORIAL_AGENT_MAX_USD`, omissão 0,05).
  Ao passar o limite, o passo com modelo pára e fica registado o motivo; a parte determinística é guardada.
- **Rasto:** cada execução fica no `audit_log` (início, fim, paragem ou falha) com o `run_id`, as entradas,
  as URLs usadas e o custo.

## Saída

Uma proposta validada contra o contrato (`verticals/editorial/src/lib/agents/contracts.ts`): tipo, `agent_id`,
`run_id`, entradas, `sources_used`, custo e, por afirmação, o tipo e a evidência. Saída fora do contrato é rejeitada
e fica registada; nada é gravado.
