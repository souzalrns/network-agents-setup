# AGENTS — catálogo gerado automaticamente

> **Não editar à mão.** Regenerar com:
> `pnpm --filter @network-agents/scripts docs:agents`
>
> Gerado em: 2026-08-19
> Fonte: `config/agents.config.ts`
> Total: **22** agentes

## Resumo por camada

| Camada | Quantidade |
|--------|------------:|
| meta | 4 |
| horizontal | 5 |
| vertical | 13 |

## Por visibilidade

- **public**: 8
- **private**: 14

## Camada `meta`

| ID | Visibilidade | Domínio | Descrição |
|----|--------------|---------|-----------|
| `orchestrator-general` | public | — | Ponto de entrada de todas as demandas, roteia para o domínio correto. |
| `domain-router` | public | — | Identifica se a demanda é de Software, Medicina, Marketing, Construção, Direito, etc. |
| `context-manager` | public | — | Mantém o histórico e estado da conversa/projeto. |
| `task-planner` | public | — | Quebra demandas complexas em subtarefas. |

## Camada `horizontal`

| ID | Visibilidade | Domínio | Descrição |
|----|--------------|---------|-----------|
| `research-agent` | public | — | Pesquisa genérica (mercado, técnica, jurídica, médica…). |
| `critic-validator` | public | — | Revisa qualidade de qualquer saída. |
| `documentation-agent` | public | — | Gera textos, relatórios e documentação. |
| `methodology-legal` | public | — | Raciocínio jurídico genérico (fato × direito, hermenêutica). |
| `legal-research` | public | legal | Busca legislação, jurisprudência e doutrina com filtro por país. |

## Camada `vertical`

| ID | Visibilidade | Domínio | Descrição |
|----|--------------|---------|-----------|
| `lead-qualifier` | private | business | Analisa e qualifica oportunidades comerciais. |
| `proposal-agent` | private | business | Gera cotações e propostas comerciais. |
| `financial-analyst` | private | business | Análise financeira, contas a pagar/receber, conciliação. |
| `clinical-orchestrator` | private | medical | Coordena casos e fluxos clínicos. |
| `triage-agent` | private | medical | Classificação de risco (Protocolo de Manchester). |
| `cardiologist-agent` | private | medical | Avaliação e conduta cardiológica. |
| `marketing-orchestrator` | private | marketing | Recebe briefings e controla o fluxo criativo. |
| `copywriter-agent` | private | marketing | Headlines, textos de anúncios, scripts, storytelling. |
| `geo-agent` | private | marketing | Generative Engine Optimization — posicionamento em pesquisas de IA. |
| `construction-orchestrator` | private | construction | Organiza etapas e fluxo da obra/reforma. |
| `architect-agent` | private | construction | Plantas, layouts, fluxos, estética e soluções de espaço. |
| `civil-engineer` | private | construction | Cálculo estrutural, fundações, estabilidade, lajes, vigas e pilares. |
| `legal-orchestrator` | private | legal | Recebe a questão, identifica a jurisdição, decompõe o problema. |
| `civil-law-br` | private | legal | Direito Civil Brasileiro (contratos, responsabilidade civil, família). |
| `civil-law-pt` | private | legal | Direito Civil Português (contratos, responsabilidade civil, família). |

---
*Gerado a partir de agents.config.ts — alinhado com a regra public/private do PCU.*
