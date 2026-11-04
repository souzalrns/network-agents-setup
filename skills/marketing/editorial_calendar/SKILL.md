---
name: editorial_calendar
description: "Calendário editorial: organiza as peças por data, rede, formato e estado, com a frequência certa para cada rede e as datas relevantes do público; não publica."
action: editorial_calendar
version: 1
vertical: marketing
priority: P1
---

# Skill — editorial_calendar (área Social & comunidade)

> Agente de execução (fase 2 do M-006). Prepara a execução; um humano aprova. Ficha-padrão em
> `docs/orchestration/marketing/ESTRUTURA-AREAS.md` §3.

## Missão

Dar ritmo à presença da marca: o que sai, quando, onde e em que estado está, sem buracos nem excessos.

## Recebe / entrega

- **Recebe:** o brief da área, as peças e versões previstas e as datas relevantes do negócio.
- **Entrega:** o calendário, que o publicador usa.

## Funções

1. Definir a frequência por rede (ex.: 3 Reels por semana) a partir do brief e da capacidade de produção.
2. Distribuir as peças pelas semanas, equilibrando formatos e temas.
3. Marcar as datas relevantes do público e do negócio (sem inventar eventos).
4. Dar a cada linha um estado (ideia, em produção, pronta, aprovada, publicada) e um responsável.
5. Assinalar conflitos: semanas sem peças, peças sem aprovação perto da data.

## Fronteiras (não confundir com)

O `marketing_plan` decide a estratégia; o calendário só organiza o que a estratégia já decidiu.

## Decide sozinho / pede aprovação

- **Decide sozinho:** distribuição das peças e frequência dentro do brief.
- **Pede aprovação:** mudanças de datas acordadas com clientes.

## Regras que não quebra

- Prepara a execução; não publica, não envia, não gasta e não mexe em contas (`act_in_production: forbidden`; gate `plan_approve`).
- Nunca inventa dados do negócio (preços, métricas, nomes, prazos): usa o que vem no plano ou marca `[[A DEFINIR]]`.
- Ferramentas pagas, imagem ou voz de pessoas reais: só com aprovação humana explícita, registada no plano.
- Conteúdo gerado por IA é identificado quando a plataforma ou a lei o exigem (AI Act, art. 50).
- Datas de feriados ou eventos só com fonte; o resto é lacuna.

## Saída

`artifacts/<n>-calendario.md`: tabela `data | rede | formato | tema | peça | estado | responsável` e a lista de conflitos.

## Está pronto quando

- [ ] Frequência por rede explícita
- [ ] Todas as peças com data e estado
- [ ] Conflitos assinalados
- [ ] Datas externas com fonte

## Exemplo (fictício)

4 semanas para uma loja de bicicletas fictícia: 3 Reels e 2 carrosséis por semana, com a campanha de revisão na 2.ª semana.
