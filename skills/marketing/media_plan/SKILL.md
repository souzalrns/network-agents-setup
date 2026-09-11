---
name: media_plan
action: media_plan
version: 1
vertical: marketing
priority: P1
---

# Skill — media_plan

## Quando usar

Step `action: media_plan` — estrutura paid, budget, audiência, tracking checklist.

## Não usar

- Executar spend / alterar contas
- Criativos finais → `ad_creative`
- UGC script → `ugc_brief`

## Processo

1. Objective + KPI (CPA, ROAS, leads…) — se faltar, gap.
2. Plataforma recomendada + porquê.
3. Estrutura: campanha → ad sets → ads (lógica, não IDs reais inventados).
4. Budget bands e **stop-loss** (quando pausar).
5. Audiências: hipótese + exclusões óbvias.
6. Compliance: claims, restrições de sector.
7. Tracking: pixels/UTM/GA4 checklist (não afirmar que está live).

## Saída

`artifacts/0N-media-plan.md` com secções Platform, Structure, Budget & stop-loss, Audience, Compliance, Tracking, Gaps.

## done_when

- [ ] KPI declarado ou gap
- [ ] Plataforma justificada
- [ ] Stop-loss explícito
- [ ] Sem claim de publicação

## Anti-padrões

- "Já lancei a campanha"
- Budget sem critério de kill
- Audiência genérica "todos 18-65" sem hipótese
