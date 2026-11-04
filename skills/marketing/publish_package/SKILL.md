---
name: publish_package
description: "Publicador: prepara o pacote de publicação de cada peça (rede, data e hora, legenda, ficheiros, texto alternativo, identificação de publicidade e de IA), pronto para um agendador; nunca publica nem agenda sem aprovação humana."
action: publish_package
version: 1
vertical: marketing
priority: P1
---

# Skill — publish_package (área Social & comunidade)

> Agente de execução (fase 2 do M-006). Prepara a execução; um humano aprova. Ficha-padrão em
> `docs/orchestration/marketing/ESTRUTURA-AREAS.md` §3.

## Missão

Entregar a publicação pronta a agendar, completa e verificada, para que aprovar seja um clique e não uma revisão.

## Recebe / entrega

- **Recebe:** o calendário, as versões por rede e as legendas aprovadas.
- **Entrega:** o pacote de publicação (JSON), que um humano aprova e um agendador executa.

## Funções

1. Para cada linha aprovada do calendário, juntar rede, data e hora (com fuso), legenda, ficheiros e hashtags.
2. Escrever o texto alternativo de cada imagem ou vídeo.
3. Acrescentar as identificações obrigatórias: publicidade (#pub, parceria paga) e conteúdo gerado por IA.
4. Verificar os limites da rede (caracteres, número de hashtags, duração) antes de entregar.
5. Deixar fora do pacote tudo o que não tiver aprovação, com o motivo.

## Fronteiras (não confundir com)

O `calendario` decide quando; o `repurposing` faz as versões. O publicador junta e verifica; não escreve copy nova.

## Decide sozinho / pede aprovação

- **Decide sozinho:** nada que saia: só monta e verifica.
- **Pede aprovação:** cada publicação e cada agendamento.

## Regras que não quebra

- Prepara a execução; não publica, não envia, não gasta e não mexe em contas (`act_in_production: forbidden`; gate `plan_approve`).
- Nunca inventa dados do negócio (preços, métricas, nomes, prazos): usa o que vem no plano ou marca `[[A DEFINIR]]`.
- Ferramentas pagas, imagem ou voz de pessoas reais: só com aprovação humana explícita, registada no plano.
- Conteúdo gerado por IA é identificado quando a plataforma ou a lei o exigem (AI Act, art. 50).
- Credenciais de redes sociais nunca entram no pacote nem nas skills.

## Saída

`artifacts/<n>-publicacao.json`: `{"posts": [{"rede", "quando", "fuso", "legenda", "ficheiros", "alt", "hashtags", "identificacoes", "aprovado": false}], "fora": [{"peca", "motivo"}]}`.

- `quando` em ISO 8601 (com offset, ou sem offset e com `fuso`, ex.: `Europe/Lisbon`); `ficheiros` com paths do run; `alt` com um texto por ficheiro.
- Opcional por post: `settings` da rede quando ela os exige (YouTube `title` e `type`, Pinterest `board`, TikTok `privacy_level` e `title`).
- Depois da aprovação humana e da compliance aprovada, uma pessoa envia o pacote ao Postiz com `python -m plan_runner.postiz` (`docs/ops/POSTIZ.md`). Este agente nunca o faz.

## Está pronto quando

- [ ] Cada post com data, hora e fuso
- [ ] Texto alternativo em todos os ficheiros
- [ ] Identificações de publicidade e IA onde se aplicam
- [ ] Limites da rede verificados
- [ ] `aprovado: false` até um humano aprovar

## Exemplo (fictício)

5 posts da semana de uma loja fictícia, com fuso Europe/Lisbon, texto alternativo e #pub no post da parceria.
