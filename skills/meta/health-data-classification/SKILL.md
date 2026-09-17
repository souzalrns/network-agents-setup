---
name: health-data-classification
action: health_data_classification
version: 1
role: meta_technique
priority: P1
description: >-
  Classificar dado de saude sensivel antes de decidir onde/como guardar, mesmo em apps local-first. Activar em qualquer app que trate sintomas, diagnosticos ou medicacao.
requires: []
---

# Skill — health-data-classification

## Trigger

Um app que trata de qualquer dado de saúde (sintomas, diagnósticos, medicação), mesmo que hoje seja local-first/sem backend.

## Inputs

- Modelo de dados do app relacionado com saúde

## Passos

1. Mesmo sendo local-first (ex.: SQLite sem backend), qualquer expansão futura com sincronização na nuvem precisa de classificar o que é dado de saúde sensível (sintomas, diagnósticos, medicação) antes de decidir onde/como guardar.
2. Se um dia houver conta de utilizador com sync, aplica Row Level Security desde o desenho inicial, não como correcção depois.

## Enforcement Note

Advisory -- esta skill orienta, nao aplica. Nada no runner ou no agente valida mecanicamente que estas praticas foram seguidas; a conformidade depende de quem aplica a skill.

## Done When

- [ ] Dados de saúde sensíveis identificados explicitamente no modelo de dados
- [ ] Se houver sync planeado, RLS desenhado desde o início (não adiado)

## Anti-padrões

- Tratar dado de saúde como dado genérico sem classificação
- Adicionar RLS só depois de já haver sync em produção

## Knowledge Ref

Adaptado do skill **healthcare-phi-compliance** do ECC (Everything Claude Code, MIT).
