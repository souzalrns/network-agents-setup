---
name: editor
description: "Revê um artigo e aponta problemas de título, estrutura, clareza, linguagem carregada, citações sem atribuição e números sem fonte; propõe adaptações para Instagram, YouTube e podcast como rascunho; nunca altera o texto."
action: editorial_edit_review
version: 1
vertical: editorial
priority: P0
---

# Skill — Edição assistida

## Quando usar

- Numa redacção montada sobre a vertical editorial, para uma peça ou para o radar da publicação.

## O que faz

- Título longo, resumo/subtítulo/SEO em falta, parágrafos e frases longas, voz passiva, vaguezas.
- Palavras carregadas («chocante», «escândalo», «polémica» sem atribuição…), generalizações, rumores.
- Citações sem atribuição por perto; números, percentagens, valores e datas sem fonte.
- Afirmações não confirmadas no artigo e factos por verificar são bloqueios.
- Rascunhos de carrossel, guião de reel (45–60 s), descrição de YouTube e pontos de podcast.
- Com modelo: até 8 sugestões de reescrita, cada uma a citar um excerto que existe mesmo no texto.

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
