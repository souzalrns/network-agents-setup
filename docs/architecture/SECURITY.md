# Segurança — frameworks e ferramentas aplicados ao setup

Este documento aplica 4 frameworks de segurança e 8 ferramentas OSS especificamente aos componentes deste repositório. É a referência de conhecimento por trás de `skills/meta/security-audit/SKILL.md` e `agents/meta/security_auditor.agent.md`.

**Nota de verificação:** os dados sobre as 8 ferramentas e a lista OWASP 2026 foram confirmados por pesquisa directa nesta tarefa (2026-09-17), não por memória. Onde havia ambiguidade real (nome de ferramenta partilhado por vários projectos), isso está assinalado explicitamente em vez de resolvido a adivinhar.

## 1. OWASP Top 10 for LLM Applications 2026 — aplicado ao setup

Lista oficial (publicada 3 Agosto 2026, substitui a de 2025):

| # | Risco | Onde isto se aplica neste setup |
|---|---|---|
| LLM01 | Prompt Injection | `agent-network-mcp` (tool descriptions do MCP), qualquer skill que processe conteúdo externo (ex.: `transcript_analysis`) |
| LLM02 | Sensitive Information Disclosure | `security/SecurityManager.ts` (MOCK — ver `CORE-MAPPING.md`), logs do `plan_runner` |
| LLM03 | Excessive Agency | `dispatch_code_task` do MCP (executa Claude Code numa máquina real), qualquer agente com permissão de escrita |
| LLM04 | Supply Chain | `requirements.txt`/`package.json` de ambos os repos, dependências do `packages/core/` |
| LLM05 | Data and Model Poisoning | Pipeline de ingestão RAG (`ingest_delta.py`, `ingest_apply.py`) — quem pode escrever em `knowledge_chunks` |
| LLM06 | Unbounded Consumption | Chamadas ao Gemini (embeddings) e a qualquer LLM via `LLMService.ts` (REAL, mas sem rate limiting confirmado) |
| LLM07 | Misinformation | Grounding do RAG (`grounding_block()` em `knowledge.py`) — já tem a defesa "não inventar" embutida |
| LLM08 | Hidden Context Exposure | System prompts dos agentes verticais (`lib/agents.js`) — já identificámos dados privados a vazar por aqui (G4) |
| LLM09 | Vector and Embedding Weaknesses | `knowledge_chunks` (Supabase/pgvector) — quem pode inserir vectores directamente? |
| LLM10 | Improper Output Handling | Qualquer output de agente que vire código/SQL/HTML sem sanitização — `revisor-codigo` já cobre parte disto |

## 2. NIST AI RMF — aplicado ao setup

| Função | O que significa aqui |
|---|---|
| **Govern** | `docs/architecture/GOVERNANCE.md` já existe — políticas de policy/identity/delegation/compliance definidas, mesmo que parcialmente implementadas |
| **Map** | Este documento + `CORE-MAPPING.md`/`MCP-MAPPING.md` — mapear onde cada risco vive no sistema real, não em teoria |
| **Measure** | Correr as 8 ferramentas listadas abaixo — medição concreta, não opinião |
| **Manage** | `docs/initiatives/STATUS.md` — os achados desta skill entram no backlog como qualquer outro item, não ficam só num relatório esquecido |

## 3. MITRE ATLAS — aplicado ao setup

MITRE ATLAS cataloga tácticas de ataque contra sistemas de IA (paralelo ao ATT&CK, mas para ML/IA). Usar para descrever o "como" de um achado desta auditoria, não só o "quê". Tácticas mais relevantes para este setup:

- **ML Model Access** — quem pode chamar `LLMService`/Gemini directamente
- **Execution** — `dispatch_code_task` (execução remota via bridge-worker)
- **Exfiltration** — qualquer caminho que tire dado de `knowledge_chunks` ou `project_state` para fora do sistema
- **Persistence** — RAG poisoning (uma entrada envenenada em `knowledge_chunks` persiste e é servida a todos os agentes desse `kb`)

## 4. MAESTRO — as 7 camadas aplicadas ao setup

Framework da Cloud Security Alliance para threat modeling de sistemas multi-agente (7 camadas). Mapeamento directo:

| Camada MAESTRO | Componente do setup |
|---|---|
| Foundation Models | Gemini (embeddings), o LLM por trás de cada agente MCP |
| Data Operations | Pipeline RAG (`ingest_delta.py`, `chunking.py`, `embedder.py`) |
| Agent Frameworks | `plan_runner` (motor), `packages/core/` (governança) |
| Deployment Infrastructure | Vercel (`agent-network-mcp`), Supabase, GitHub Actions |
| Security & Compliance (camada vertical) | `packages/core/security`, `packages/core/compliance` — ambos MOCK hoje (ver `CORE-MAPPING.md`) |
| Agent Ecosystem | Os 33 agentes do `agent-network-mcp` + os horizontais migrados para o setup |
| Evaluation & Observability | `MetricsDashboard`, `SelfAwareness` (ambos INCOMPLETO — ver `CORE-MAPPING.md`) |

## 5. Ferramentas OSS

### SAST (código)

| Ferramenta | O quê | Nota |
|---|---|---|
| **Bandit** | SAST para Python — relevante para `runner/plan_runner/` | Madura, estável |
| **Semgrep** | SAST multi-linguagem (regras custom possíveis) | Cobre o lado TypeScript de `packages/core/` que o Bandit não cobre |

### Específicas de MCP

| Ferramenta | O quê | Nota |
|---|---|---|
| **mcpguard** | Scanner de configs/servidores MCP | **Nome ambíguo** — existem pelo menos 5 projectos GitHub distintos e não relacionados com este nome exacto (`ChenLaoshiYF/mcpguard`, `peedrolzz/mcpguard`, `SaravanaGuhan/mcp-guard`, `General-Analysis/mcp-guard`, `GenTelLab/MCP-Guard`), mais uma versão comercial na Smithery. **Confirmar qual antes de instalar** — não assumir que é o mesmo projecto só porque o nome bate (mesmo padrão de ambiguidade já visto com "ContextForge" no `ROADMAP-GOVERNANCE.md`) |
| **offsec-ai** | Scanner MCP + toolkit ofensivo (`pypi.org/project/offsec-ai`) | Tem `ai-owasp-scan` e `mcp-scan` (passivos, usar livremente) e `mcp-attack`/`openclaw-attack`/`k8s-attack` (activos, exigem `--i-have-authorization`). **Este setup só usa os modos passivos** — os modos activos estão fora do âmbito do `security_auditor` por desenho |
| **mcphound** | Reputação pública + `mcp-policy.yaml` para bloquear PRs com configs MCP arriscadas em CI (`tayler-id/mcphound`, também no PyPI) | Confirmado sem ambiguidade — projecto único, bem documentado. Mapeia achados directamente a OWASP LLM/Agentic Top 10 |

### Segredos e dependências

| Ferramenta | O quê |
|---|---|
| **Gitleaks** | Segredos no histórico git — já mencionado como recomendação em `skills/meta/ai-code-review-checklist/SKILL.md` |
| **OSV-Scanner** | Vulnerabilidades de dependências (CVE/OSV database) |
| **Trivy** | Vulnerabilidades de imagens de container, filesystem, IaC |

## 6. Referências

- [`skills/meta/security-audit/SKILL.md`](../../skills/meta/security-audit/SKILL.md) — skill que opera com base neste documento
- [`agents/meta/security_auditor.agent.md`](../../agents/meta/security_auditor.agent.md) — agente que usa a skill acima
- [`GOVERNANCE.md`](./GOVERNANCE.md) — camada de governança geral (policy/identity/delegation/compliance)
- [`CORE-MAPPING.md`](./CORE-MAPPING.md) — estado REAL/INCOMPLETO/MOCK de `packages/core/`
