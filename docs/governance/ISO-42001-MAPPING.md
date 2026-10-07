# ISO/IEC 42001:2023: mapeamento e Declaração de Aplicabilidade

**Política:** [`AI-MANAGEMENT-SYSTEM.md`](./AI-MANAGEMENT-SYSTEM.md). **Decisão:** P-40 (maestro, 2026-10-07). **Âmbito:** NAS + ANM.
**Natureza:** alinhamento voluntário, **não** certificação. Números e títulos das cláusulas em tradução livre. O texto da norma não é reproduzido. Confirmar a numeração contra o exemplar oficial na 1.ª auditoria (2027-01).
**Guarda em CI:** `runner/tests/test_governance_mapping.py` verifica:
- as 27 cláusulas e os 38 controlos estão todos aqui, uma só vez;
- os estados são válidos;
- cada evidência existe no repo (e o símbolo depois de `::` existe no ficheiro);
- cada `Parcial` ou `Falta` aponta para um item vivo do `PENDENCIAS.md`;
- o resumo abaixo bate com as tabelas.

As evidências `ANM:` só são verificadas quando o clone do `agent-network-mcp` está ao lado (local); no CI do NAS ficam por verificar.

**Formato da evidência:** `` `path` `` ou `` `path::símbolo` `` (NAS); `` `ANM:path::símbolo` `` (agent-network-mcp).
**Estados:** `Cumpre` · `Parcial` · `Falta` · `N/A`. Nas cláusulas 4–10, `N/A` não é permitido: são obrigatórias.

## Resumo

<!-- resumo: verificado pelo teste -->
| Tabela | Cumpre | Parcial | Falta | N/A |
|---|---:|---:|---:|---:|
| Cláusulas 4–10 | 9 | 15 | 3 | 0 |
| Anexo A | 22 | 11 | 5 | 0 |

**Leitura:** os controlos técnicos (dados, proveniência, V&V, HITL, deny-by-default) estão fortes. Falta sobretudo a camada de gestão: avaliação de impacto (**GOV-IMPACT-1**, Alta), avaliação de risco periódica, fornecedores, incidentes e revisões (**GOV-42001-1**). Nenhum controlo foi excluído: com memória de clientes no âmbito, todos se aplicam.

## Cláusulas 4–10 (obrigatórias)

| Cláusula | Título | Estado | Evidência | Item |
|---|---|---|---|---|
| 4.1 | Contexto da organização | Parcial | `docs/architecture/EXECUTION-PLAN.md`; `docs/PORTFOLIO.md` | GOV-42001-1 |
| 4.2 | Partes interessadas | Parcial | `docs/governance/AI-MANAGEMENT-SYSTEM.md::Partes interessadas` | GOV-42001-1 |
| 4.3 | Âmbito do AIMS | Cumpre | `docs/governance/AI-MANAGEMENT-SYSTEM.md::## 1. Âmbito` | — |
| 4.4 | Sistema de gestão de IA | Parcial | `docs/governance/AI-MANAGEMENT-SYSTEM.md`; `docs/governance/ISO-42001-MAPPING.md` | GOV-42001-1 |
| 5.1 | Liderança e compromisso | Cumpre | `docs/initiatives/PENDENCIAS.md::## 10. Decisões` | — |
| 5.2 | Política de IA | Cumpre | `docs/governance/AI-MANAGEMENT-SYSTEM.md::## 2. Política de IA` | — |
| 5.3 | Papéis, responsabilidades e autoridades | Cumpre | `docs/governance/AI-MANAGEMENT-SYSTEM.md::## 3. Papéis` | — |
| 6.1.1 | Riscos e oportunidades: geral | Parcial | `docs/initiatives/PENDENCIAS.md::## 4. Tabela única` | GOV-42001-1 |
| 6.1.2 | Avaliação de risco de IA | Parcial | `docs/governance/AI-MANAGEMENT-SYSTEM.md::## 4. Gestão de risco` | GOV-42001-1 |
| 6.1.3 | Tratamento de risco de IA | Parcial | `docs/governance/ISO-42001-MAPPING.md::## Anexo A` | GOV-42001-1 |
| 6.1.4 | Avaliação de impacto do sistema de IA | Falta | — | GOV-IMPACT-1 |
| 6.2 | Objectivos de IA e planeamento | Parcial | `docs/ops/L5-F0-REVALIDATION.md` | GOV-42001-1 |
| 6.3 | Planeamento de mudanças | Cumpre | `docs/architecture/EXECUTION-PLAN.md::### 15.4 Contract-first` | — |
| 7.1 | Recursos | Cumpre | `config/areas.yaml::budget`; `config/model-tiers.yaml`; `config/model-prices.yaml`; `docs/ops/BUDGET.md` | — |
| 7.2 | Competência | Parcial | `CLAUDE.md`; `docs/generated/SKILLS.md` | GOV-42001-1 |
| 7.3 | Consciencialização | Parcial | `CLAUDE.md` | GOV-42001-1 |
| 7.4 | Comunicação | Parcial | `docs/ops/PROGRESS-SESSAO.md` | GOV-42001-1 |
| 7.5 | Informação documentada | Cumpre | `docs/initiatives/PENDENCIAS.md`; `docs/architecture/adr/ADR-F3-PROVENANCE-RETRIEVE.md` | — |
| 8.1 | Planeamento e controlo operacional | Cumpre | `runner/plan_runner/engine.py`; `.github/workflows/runner-tests.yml` | — |
| 8.2 | Avaliação de risco de IA (operação) | Falta | — | GOV-42001-1 |
| 8.3 | Tratamento de risco de IA (operação) | Parcial | `runner/plan_runner/hitl.py::def write_request`; `config/skills.yaml::allow_scripts` | GOV-42001-1 |
| 8.4 | Avaliação de impacto (operação) | Falta | — | GOV-IMPACT-1 |
| 9.1 | Monitorização, medição, análise e avaliação | Parcial | `runner/plan_runner/l5_eval.py::provenance_v2_ok`; `runner/plan_runner/cost.py::def ledger_cost_usd` | GOV-42001-1 |
| 9.2 | Auditoria interna | Parcial | `docs/governance/AI-MANAGEMENT-SYSTEM.md::## 10. Auditoria interna`; `docs/architecture/governance/audit/AUDIT-GOVERNANCE.md` | GOV-42001-1 |
| 9.3 | Revisão pela gestão | Parcial | `docs/governance/AI-MANAGEMENT-SYSTEM.md::Revisão desta política` | GOV-42001-1 |
| 10.1 | Melhoria contínua | Cumpre | `docs/initiatives/PENDENCIAS.md::## 7. Histórico` | — |
| 10.2 | Não conformidade e acção correctiva | Parcial | `docs/initiatives/PENDENCIAS.md::## 8. Contradições resolvidas` | GOV-42001-1 |

## Anexo A (Declaração de Aplicabilidade)

| Controlo | Título | Aplicável | Estado | Evidência / justificação | Item |
|---|---|---|---|---|---|
| A.2.2 | Política de IA | Sim | Cumpre | `docs/governance/AI-MANAGEMENT-SYSTEM.md::## 2. Política de IA` | — |
| A.2.3 | Alinhamento com outras políticas | Sim | Cumpre | `docs/governance/AI-MANAGEMENT-SYSTEM.md::Alinhamento com outras políticas`; `docs/architecture/SECURITY-AGENTS.md` | — |
| A.2.4 | Revisão da política de IA | Sim | Parcial | `docs/governance/AI-MANAGEMENT-SYSTEM.md::semestral` (cadência decidida; 1.ª revisão por fazer) | GOV-42001-1 |
| A.3.2 | Papéis e responsabilidades de IA | Sim | Cumpre | `docs/governance/AI-MANAGEMENT-SYSTEM.md::## 3. Papéis` | — |
| A.3.3 | Reporte de preocupações | Sim | Cumpre | `docs/governance/AI-MANAGEMENT-SYSTEM.md::Reporte de preocupações`; `SECURITY.md::Reporting a vulnerability` | — |
| A.4.2 | Documentação de recursos | Sim | Cumpre | `docs/generated/AGENTS.md`; `docs/generated/SKILLS.md`; `config/model-tiers.yaml` | — |
| A.4.3 | Recursos de dados | Sim | Cumpre | `scripts/ingest_delta.py::MANIFEST`; `scripts/ingest_delta.py::EXCLUDED`; `docs/ops/RAG-CANONICAL.md` | — |
| A.4.4 | Recursos de ferramentas | Sim | Parcial | `runner/plan_runner/skill_activation.py::def is_script_allowed`; `runner/plan_runner/capabilities.py::LEVELS` (execução de tools por decidir: P-37) | AU-20 |
| A.4.5 | Recursos de sistema e computação | Sim | Cumpre | `config/areas.yaml::max_tokens`; `config/model-prices.yaml`; `runner/plan_runner/cost.py::def ledger_cost_usd` | — |
| A.4.6 | Recursos humanos | Sim | Parcial | `docs/governance/AI-MANAGEMENT-SYSTEM.md::## 3. Papéis` (competências humanas não documentadas) | GOV-42001-1 |
| A.5.2 | Processo de avaliação de impacto | Sim | Falta | memória de clientes no âmbito sem avaliação | GOV-IMPACT-1 |
| A.5.3 | Documentação das avaliações de impacto | Sim | Falta | idem | GOV-IMPACT-1 |
| A.5.4 | Impacto em indivíduos ou grupos | Sim | Falta | `runner/plan_runner/engine.py::def _load_client_memory` injecta a memória do cliente no prompt | GOV-IMPACT-1 |
| A.5.5 | Impactos sociais | Sim | Falta | idem | GOV-IMPACT-1 |
| A.6.1.2 | Objectivos de desenvolvimento responsável | Sim | Cumpre | `docs/architecture/EXECUTION-PLAN.md::## 15. Governança do próprio Execution Plan`; `CLAUDE.md` | — |
| A.6.1.3 | Processos de concepção e desenvolvimento responsáveis | Sim | Cumpre | `docs/architecture/EXECUTION-PLAN.md::### 15.4 Contract-first`; `.github/workflows/security-scan.yml` | — |
| A.6.2.2 | Requisitos e especificação | Sim | Cumpre | `docs/ops/SKILL-ACTIVATION.md`; `docs/architecture/AU-20-TOOL-EXECUTOR.md` | — |
| A.6.2.3 | Documentação de concepção e desenvolvimento | Sim | Cumpre | `docs/architecture/adr/ADR-F3-PROVENANCE-RETRIEVE.md`; `docs/architecture/adr/ADR-META-AGENTS.md` | — |
| A.6.2.4 | Verificação e validação | Sim | Cumpre | `runner/plan_runner/l5_eval.py`; `config/l5-golden-security.yaml`; `scripts/f5_evidence.py`; `.github/workflows/runner-tests.yml` | — |
| A.6.2.5 | Implantação | Sim | Cumpre | `docs/initiatives/PENDENCIAS.md::## 9. Como fechar um item`; `.github/workflows/release.yml` | — |
| A.6.2.6 | Operação e monitorização | Sim | Parcial | `config/areas.yaml::max_tokens`; `docs/ops/BUDGET.md` (limites de turnos/tool calls: P-37) | AU-20 |
| A.6.2.7 | Documentação técnica | Sim | Cumpre | `docs/ops/WORKER-EXTERNAL.md`; `docs/ops/ROUTER.md`; `docs/ops/MEMORY-L4.md` | — |
| A.6.2.8 | Registos de eventos | Sim | Parcial | `runner/plan_runner/events.py::class EventLog`; `ANM:lib/tokenLedger.js::recordTokenUsage` (sem retenção nem detecção de adulteração) | B16 |
| A.7.2 | Dados para desenvolvimento e melhoria | Sim | Cumpre | `config/l5-golden-security.yaml`; `config/router-golden.yaml` | — |
| A.7.3 | Aquisição de dados | Sim | Cumpre | `docs/ops/WEB-FETCH.md`; `scripts/ingest_delta.py::MANIFEST` | — |
| A.7.4 | Qualidade dos dados | Sim | Parcial | `runner/plan_runner/validity.py::def apply_validity`; `config/knowledge-validity.yaml` (autoridade e conflitos por fazer) | F3b-AUTH-1 |
| A.7.5 | Proveniência dos dados | Sim | Cumpre | `runner/plan_runner/provenance.py::def load_meta`; `ANM:lib/knowledge.js::match_knowledge_v2`; `runner/plan_runner/skill_activation.py::sha256` | — |
| A.7.6 | Preparação dos dados | Sim | Cumpre | `runner/plan_runner/chunking.py::def chunk_markdown`; `docs/ops/INGEST-DOCUMENT.md` | — |
| A.8.2 | Documentação e informação para utilizadores | Sim | Parcial | `docs/generated/AGENTS.md` (sem limites de uso por agente para quem usa o MCP) | GOV-42001-1 |
| A.8.3 | Reporte externo | Sim | Parcial | `SECURITY.md::Reporting a vulnerability` (só vulnerabilidades; não cobre impactos adversos de IA) | GOV-42001-1 |
| A.8.4 | Comunicação de incidentes | Sim | Parcial | `docs/governance/AI-MANAGEMENT-SYSTEM.md::## 9. Incidentes` (processo definido, nunca exercitado) | GOV-42001-1 |
| A.8.5 | Informação para partes interessadas | Sim | Cumpre | `docs/PORTFOLIO.md`; `docs/portfolio/WHAT-I-CONTRIBUTED.md` | — |
| A.9.2 | Processos de uso responsável | Sim | Cumpre | `config/areas.yaml::hitl: required`; `runner/plan_runner/memory_l4.py::def promote`; `runner/plan_runner/capabilities.py::act_in_production` | — |
| A.9.3 | Objectivos de uso responsável | Sim | Parcial | `docs/governance/AI-MANAGEMENT-SYSTEM.md::## 2. Política de IA` (sem objectivos mensuráveis) | GOV-42001-1 |
| A.9.4 | Uso previsto | Sim | Cumpre | `config/areas.yaml`; `agents/meta/security_auditor.agent.md::description` | — |
| A.10.2 | Atribuição de responsabilidades | Sim | Cumpre | `docs/governance/AI-MANAGEMENT-SYSTEM.md::## 3. Papéis`; `docs/governance/AI-MANAGEMENT-SYSTEM.md::## 7. Fornecedores` | — |
| A.10.3 | Fornecedores | Sim | Parcial | `docs/governance/AI-MANAGEMENT-SYSTEM.md::## 7. Fornecedores` (lista sem avaliação formal) | GOV-42001-1 |
| A.10.4 | Clientes | Sim | Falta | há clientes com memória no âmbito e nenhum acordo sobre o uso de IA | GOV-42001-1 |

## Ligação ao P-37 (executor de tools)

A tabela de controlos do executor ↔ norma está no contrato: `docs/architecture/AU-20-TOOL-EXECUTOR.md`, secção "ISO/IEC 42001". Quando o P-37 for implementado, A.4.4 e A.6.2.6 passam a `Cumpre` só com a evidência do código e dos testes.
