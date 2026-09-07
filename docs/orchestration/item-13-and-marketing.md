# Item 13 vs orquestrador de marketing

## Item 13 tem orquestrador próprio?

**Não.** O Item 13 (descoberta / recomendação por sistemas de IA + SEO “para máquinas”) **não** é uma vertical com orchestrator separado.

É um **conjunto de requisitos e checks** que correm **dentro** de pipelines de conteúdo — em especial:

- `seo_brief`
- `copy_answer_first`
- `critic` (publish_ready / gaps Item 13)

Quem “orquestra” Item 13 hoje, no desenho do setup, é o **mesmo plan** de conteúdo (SEO → copy → critic → HITL), não um agent `item13_orchestrator`.

| Peça | Estado típico no setup |
|------|-------------------------|
| Critérios Item 13 no brief/critic | método / schemas / piloto |
| Orchestrator só Item 13 | **não existe de propósito** |
| Orchestrator marketing (vertical) | **este pacote** |

---

## Implicação

Fazer o orquestrador de **marketing** agora é o passo certo: ele **inclui** Item 13 nos steps de conteúdo, em vez de um segundo cérebro paralelo.
