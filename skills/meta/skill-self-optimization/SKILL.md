---
name: skill-self-optimization
action: skill_self_optimization
version: 1
role: meta_technique
priority: P2
description: >-
  Usa um optimizador automatico (SkillOpt) para validar e melhorar o texto de SKILL.md com base em execucoes reais, em vez de reescrever skills manualmente as cegas. Activar quando ha skills instaladas cujo texto nunca foi validado na pratica.
requires: []
---

# Skill — skill-self-optimization

## Trigger

- Há várias skills instaladas mas nunca se validou se o texto delas está bem escrito na prática.
- Quer-se um ciclo recorrente (ex.: nocturno) que analisa execuções reais das skills e propõe edições — só aplicadas se passarem por um portão de validação.

## Inputs

- Skill(s) já instalada(s) cujo texto se quer validar/optimizar
- Registo de execuções reais dessa(s) skill(s), se disponível

## Passos

Ferramenta de referência: `microsoft/SkillOpt` (edita e valida o *texto* da skill, não mexe em pesos de modelo).

```bash
pip install "skillopt[claude]"
```

O extra `[claude]` traz suporte nativo para optimizar skills usadas via Claude Code/Claude Agent SDK.

**Atenção:** o pacote chama-se `skillopt` no PyPI mas instala três comandos separados, não um `skillopt` sozinho:

```bash
skillopt-sleep {run,dry-run,status,adopt,harvest,schedule,unschedule}
skillopt-eval
skillopt-train
```

Para evoluir skills já em uso, o relevante é `skillopt-sleep`:

```bash
skillopt-sleep dry-run   # harvest+mine+replay, só reporta, não aplica nada
skillopt-sleep status    # ver estado + última proposta pendente
skillopt-sleep run       # rodar o ciclo completo
skillopt-sleep adopt     # aplicar a última proposta em staging
skillopt-sleep schedule  # instalar entrada de cron para rodar periodicamente
```

## Enforcement Note

Advisory — esta skill orienta o processo de optimização, não aplica nada mecanicamente. O portão de validação do próprio SkillOpt (só aceita mudanças que passem por `dry-run`) é do SkillOpt, não desta skill.

## Done When

- [ ] `dry-run` corrido pelo menos uma vez antes de qualquer `adopt`
- [ ] Escolhida explicitamente qual skill testar primeiro (não tentar todas de uma vez)
- [ ] Definido onde o cron roda (não numa sandbox efémera que não persiste)

## Anti-padrões

- Rodar `adopt` sem ter corrido `dry-run` primeiro
- Agendar (`schedule`) numa máquina/sandbox que não persiste entre sessões
- Tratar isto como substituto de revisão humana da skill

## Knowledge Ref

Ferramenta externa (`microsoft/SkillOpt`) — não é uma skill do ECC, é uma ferramenta citada directamente.
