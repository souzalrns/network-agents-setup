---
name: cheap-entity-extraction
action: cheap_entity_extraction
version: 1
role: meta_technique
priority: P1
description: >-
  Decide quando extrair entidades ou classificar texto com um modelo pequeno local (GLiNER2) em vez de gastar uma chamada a um agente LLM completo. Activar para reconhecimento de padrao simples -- extraccao de nomes/datas, classificacao em categorias fixas, estruturacao de dados soltos.
requires: []
---

# Skill — cheap-entity-extraction

## Trigger

- Extrair nomes/empresas/datas de texto solto (e-mails, mensagens, dados vindos de scraping) — não precisa de raciocínio, só reconhecimento de padrão.
- Classificar mensagens em categorias fixas conhecidas de antemão (ex.: "dúvida" vs "reclamação" vs "spam").
- Estruturar dados bagunçados num formato fixo antes de um agente LLM processar — reduz tokens gastos no agente de verdade.

## Inputs

- Texto solto a processar
- Lista de labels/categorias-alvo (para extracção de entidades ou classificação)

## Passos

Modelo de referência: `fastino/gliner2-base-v1` (~205M parâmetros, roda em CPU, sem GPU, sem chamar API de LLM nenhuma).

```bash
pip install gliner2
```

```python
from gliner2 import GLiNER2

model = GLiNER2.from_pretrained("fastino/gliner2-base-v1")

resultado = model.extract_entities(
    "texto solto aqui",
    ["pessoa", "empresa", "data"]
)
```

Para classificação de texto, a API `classify_text` espera um schema mais elaborado do que uma lista simples de labels — consultar a documentação oficial do projecto antes de assumir a forma do schema.

**Nota de ambiente:** precisa de acesso à internet para baixar os pesos do modelo na primeira execução (fica em cache local depois). Não funciona em sandboxes com allowlist de rede restrita que bloqueiam o host de download dos pesos.

## Enforcement Note

Advisory — esta skill orienta a escolha de ferramenta, não aplica nada mecanicamente. Nada impede o agente de chamar um LLM completo mesmo quando esta skill recomendaria o modelo local.

## Done When

- [ ] Confirmado que a tarefa é reconhecimento de padrão, não raciocínio
- [ ] Modelo local usado em vez de chamada a agente LLM completo
- [ ] Custo comparativo (tokens poupados) mencionado se relevante

## Anti-padrões

- Usar isto para tarefas que exigem raciocínio/contexto — não substitui um agente LLM
- Assumir que `classify_text` aceita a mesma forma de schema que `extract_entities` sem checar

## Knowledge Ref

Modelo externo (`fastino/gliner2-base-v1`) — não é uma skill do ECC, é uma biblioteca/modelo citado directamente.
