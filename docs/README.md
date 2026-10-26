# Documentação — o que está onde

> Índice da pasta `docs/` (H-01, 2026-10-25). Regra: **um documento por papel**. O estado vive só
> no `PENDENCIAS.md`; o passado vive só no [`PENDENCIAS-HISTORICO.md`](./initiatives/PENDENCIAS-HISTORICO.md)
> (itens fechados, decisões tomadas e, no §13, a ficha de cada documento antigo com o link para o texto integral).

## Documentos vivos (por papel)

| Papel | Documento |
|---|---|
| Índice curto do repo | [`STATUS.md`](./STATUS.md) |
| Estado e pendentes (fonte única) | [`initiatives/PENDENCIAS.md`](./initiatives/PENDENCIAS.md) |
| Plano | [`architecture/EXECUTION-PLAN.md`](./architecture/EXECUTION-PLAN.md) |
| Visão do sistema | [`architecture/ECOSYSTEM.md`](./architecture/ECOSYSTEM.md) |
| Onde está cada fonte de verdade | [`architecture/BOOTSTRAP.md`](./architecture/BOOTSTRAP.md) |
| Governança | [`architecture/GOVERNANCE.md`](./architecture/GOVERNANCE.md) |
| Decisões de arquitectura | [`architecture/adr/`](./architecture/adr/) |

## Pastas

| Pasta | Conteúdo |
|---|---|
| [`ops/`](./ops/) | Runbooks e contratos operacionais (fecho do setup, escritório, router, orçamento, RAG, web fetch…) |
| [`architecture/`](./architecture/) | Arquitectura, ADRs, auditorias técnicas e padrões estudados |
| [`knowledge/`](./knowledge/) | Conhecimento dos domínios (entra no RAG pelo MANIFEST) |
| [`orchestration/`](./orchestration/) | Planos e templates por domínio |
| [`governance/`](./governance/) | Governança de IA (ISO 42001, políticas) |
| [`initiatives/`](./initiatives/) | Pendências e iniciativas em curso |
| [`audit/`](./audit/) | Auditorias e decisões do maestro |
| [`research/`](./research/) | Investigação de ferramentas externas |
| [`portfolio/`](./portfolio/) | Evidência para portfólio |
| [`generated/`](./generated/) | Gerado por scripts; não editar à mão |

## Documentos antigos (H-01, 2026-10-25)

`initiatives/STATUS.md` (108 KB), `ops/PROGRESS-SESSAO.md` (133 KB), `audit/PLANO-DE-ACAO.md`,
`initiatives/OPEN-ITEMS.md`, `architecture/MASTER-PLAN.md`, `initiatives/PENDENCIAS_T6.md`,
`ops/PENDENCIAS-CRUZADAS.md`, `STATUS-PROJETOS.md`, `STATUS-ECOSSISTEMA.md` e o `STATUS.md`
anterior saíram da árvore. Nada se perdeu: a ficha de cada um (o que era, período, o que o substituiu)
e o link permanente para o texto integral estão no §13 do
[`PENDENCIAS-HISTORICO.md`](./initiatives/PENDENCIAS-HISTORICO.md). O último commit com os ficheiros
na árvore é o `007907e`.
