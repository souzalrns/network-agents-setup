---
name: factcheck
description: "Extrai do texto as afirmações verificáveis (números, datas, valores, instituições, citações), classifica-as em facto, declaração, inferência ou não confirmada e regista-as como pendentes; nunca marca nada como verificado."
action: editorial_factcheck
version: 1
vertical: editorial
priority: P0
---

# Skill — Verificação

## Quando usar

- Numa redacção montada sobre a vertical editorial, para uma peça ou para o radar da publicação.

## O que faz

- Separa as frases verificáveis e classifica-as: não confirmada («alegadamente», «terá recebido», rumores),
  declaração (com quem declarou), inferência («poderá», «deverá»), facto.
- Regista-as como afirmações pendentes, sem duplicar numa nova execução e sem tocar nas que uma pessoa registou.
- Aponta números contraditórios para a mesma entidade e métrica.
- Lista como evidência candidata os documentos e dados das referências; artigos de outros meios contam só como repetição.
- Com modelo: segunda opinião sobre a classificação, só no relatório.

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
