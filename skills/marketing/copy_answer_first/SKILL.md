---
name: copy_answer_first
description: "Escreve a peça a partir do seo_brief com a resposta directa nas primeiras linhas, H2 com valor e FAQ citável, para humanos e para assistentes de IA (ChatGPT, Claude, Gemini, Perplexity). Usar depois de seo_brief; não inventa dados."
action: copy_answer_first
version: 2
vertical: marketing
priority: P0
---

# Skill — copy_answer_first

## Quando usar

- Apos `seo_brief`.

## Descoberta

Escrever para **humanos + assistentes/motores generativos** (GPT, Claude, Gemini, Perplexity, …), nao apenas para snippet de um unico buscador.

## Processo

1. Respeitar brief (intent, unique promise, item_13).
2. **Resposta directa** nas primeiras linhas.
3. H2 com valor; FAQ citavel.
4. Claims verificaveis; assumptions explicitas.
5. Evitar promessas do tipo "vais aparecer no ChatGPT".

## done_when

- [ ] Resposta util cedo
- [ ] FAQ se o brief tinha item_13.faq
- [ ] Sem inventar dados
- [ ] Tom multi-IA quando o tema e Findability

## Anti-padroes

- Intro vaga; ignorar brief; keyword stuffing
- Reduzir tudo a "ranquear no Google" quando o objective e AI Findability
