# Knowledge Pack — security-agents-stack

**Âmbito:** área `security` (defensivo). Pipeline: triage → `meta.security-auditor` → reporter.  
**Não substitui:** `docs/architecture/SECURITY.md`, skill `security-audit`, agentes em `agents/security/`.  
**Ingestão:** entra no L5 pelo MANIFEST (`scripts/ingest_delta.py`, `agent_id: security`) e pelo workflow `ingest-knowledge` (markdown → chunk → embed → `knowledge_chunks`), incremental por `content_hash`. Consumido pelo bloco `knowledge:` (`kb: security`) do passo `audit` do plano demo.

Este pack é **operacional para RAG**: cada secção numerada responde a uma pergunta isolada.

---

## 1. Política da área security neste projecto

A área `security` é só defensiva: ler, classificar, auditar passivamente e reportar. Nunca ataque activo, exploit, nem escrita em produção pelos agentes de security. HITL é `required`. Cyber não é área separada — equivale a security.

## 2. Pipeline de agentes security

Ordem canónica: `security.triage` → `meta.security-auditor` (`action: security_audit`) → `security.reporter` → gate HITL. Fixes de código ficam para engenharia (`revisor-codigo` / `desenvolvimento`) após approve humano.

## 3. O que o triage faz e não faz

Triage classifica `severity`, `surfaces[]`, `needs_full_audit`, `rationale`, `out_of_scope`. Não corre scanners nem inventa CVEs. Pedidos ofensivos registam-se em `out_of_scope` como proibidos.

## 4. O que o security-auditor faz e não faz

Auditor defensivo OWASP Top 10 for LLM Applications 2026, mapeado a NIST AI RMF, MITRE ATLAS e MAESTRO. Pode orientar scanners passivos (Bandit, Semgrep, Gitleaks, OSV-Scanner, Trivy, mcp-scan passivo). Nunca modos `*-attack` nem `--i-have-authorization` ofensivo.

## 5. O que o reporter faz e não faz

Consolida triage + audit num relatório (executive summary, findings, mapped controls, next_steps). Não re-audita nem aplica patches. Zero findings é resultado válido.

## 6. ADOPTAR no stack (runtime, não "agentes cyber")

Adoptar como infraestrutura: LangGraph no `plan_runner` (planos + HITL), MCP Python SDK (tools), Postgres + pgvector (RAG/L4), gitleaks e semgrep no CI. Não substituem o registo `areas.yaml` nem os `.agent.md`.

## 7. LangGraph — papel na security

LangGraph orquestra passos e `interrupt` HITL. Não é um pack de agentes NICE. Security usa planos YAML no plan_runner. O CouncilSession de security já existe (Fase 1, desde 2026-10-01: `runner/plan_runner/council_session.py`, conselho `security` em `config/councils.yaml`) para decisões estruturais como threat model, política de segredos ou de acessos; o router escala para ele. O pipeline diário triage → audit → report não passa pelo conselho.

## 8. MCP Python SDK — papel

SDK oficial para servidores/clientes MCP. Relevante quando se audita configs MCP e tools expostas (LLM01, excessive agency). Não é um agente de pentest.

## 9. EXTRAIR — protocolo llm-council

De `karpathy/llm-council` (e forks MIT) extrai-se só o protocolo: respostas em paralelo → peer-review anónimo → chairman. Não se adopta a app nem OpenRouter como maestro. É o protocolo do CouncilSession (independent → peer_rank → synthesize), usado pelo conselho `security`; não pelo pipeline triage/audit/report diário.

## 10. EXTRAIR — papéis NICE / CIPHER

CIPHER mapeia papéis NICE a personas e modos T1/T2/T3 (aconselha / HITL / autónomo baixo risco). Extrair taxonomia e ideia de separation of duties. Não adoptar o monólito (SPIFFE, OPA, NATS, etc.) no caminho crítico zero-custo.

## 11. EXTRAIR — SOC multi-agente típico

Padrão repetido em demos SOC: Triage → Hunt/Audit → Forensics → Report + HITL em severidade alta. Neste repo a Fase 1 reduz a Triage → Audit → Report. Hunt/forensics com SIEM comercial ficam fora até haver necessidade e isolamento.

## 12. REJEITAR como núcleo

Não adoptar AutoGen em maintenance como motor, CrewAI/MetaGPT como substituto do plan_runner, PoCs de exploitation com Kali no mesmo host de produção, nem "41 agentes NICE" sem conteúdo nem HITL.

## 13. Família B — red team dos vossos agentes (não SOC de negócio)

Ferramentas para testar o sistema de agentes: PyRIT (MIT, Microsoft), DeepTeam (Apache-2.0), Garak, Promptfoo. Usar em lab/CI contra prompts e agents — não como passos do pipeline security de produção sem sandbox.

## 14. PyRIT em uma frase

Framework open-source de red teaming multi-turn para sistemas generativos; avalia se o agente pode ser coagido a comportamento nocivo. Incorporação: pipeline de teste, não agente `areas.yaml`.

## 15. DeepTeam em uma frase

Framework de red team para LLMs/agentes com mapeamento OWASP LLM / agents. Incorporação: avaliação e CI de prompts, não substituto do `security_auditor`.

## 16. Gitleaks e Semgrep

Gitleaks: segredos no git. Semgrep: SAST multi-linguagem. São ferramentas CI/audit passivo alinhadas à skill security-audit; não são agentes.

## 17. mem0 e L4

mem0 OSS: extrair padrões de extracção de factos se houver spike; L4 do projecto é contrato próprio sobre Supabase, não drop-in mem0. Security findings em L4 só com status candidate e HITL se a política o exigir.

## 18. LightRAG / GraphRAG

Candidatos a EXTRAIR depois do RAG vector estável. Não são estrutura de agentes cybersecurity. Não no caminho crítico do pipeline security.

## 19. LiteLLM

Opcional no worker para multi-provider e usage. Não organiza agentes security.

## 20. Quando usar needs_full_audit true

Severity ≥ medium ou superfícies code, deps, mcp, secrets ou ci no repo. Pedidos só conceptuais podem ficar em triage + resposta sem audit completo, conforme o plan.

## 21. HITL na área security

`hitl: required` em `areas.yaml`. Achados de segurança não se fecham só com o modelo. O reporter não declara risco CRITICAL aceitável sem assinalar decisão humana.

## 22. Budget da área security

Tecto de tokens da área (freio): da ordem de 40k por pedido na fase B5-bis — rever após optimização de prompt-base se necessário. Não é desculpa para ofensiva nem para saltar HITL.

## 23. security_auditor não é meta-agente

Vive historicamente em `agents/meta/` mas é especialista C3 da área security (`kind: internal`). O chairman dos conselhos, incluindo o `security`, é o `meta.chairman` (`kind: meta`, `agents/meta/chairman.agent.md`), separado do auditor (ADR-META-AGENTS §10); no conselho `security` o auditor é membro obrigatório, com veto.

## 24. Knowledge refs úteis num plan security

`docs/architecture/SECURITY.md`, skill `skills/meta/security-audit/SKILL.md`, agentes triage/auditor/reporter, este pack após ingerido.

## 25. Anti-padrão: importar SOC CrewAI completo

Traz segundo orquestrador, tools pagas e papéis sem grounding do repo. Preferir três agentes no registo existente + plan YAML.

## 26. Anti-padrão: offsec no mesmo runner de prod

Mesmo que uma tool tenha subcomandos de ataque, a skill e o auditor proíbem invocá-los. Pedido do utilizador não override essa regra.

## 27. Done when de uma ronda security

Triage JSON válido; audit com cobertura OWASP LLM 2026 (N/A justificado conta); relatório com summary e next_steps; HITL resolvido; zero writes de produção pelos agentes security.

## 28. Relação com software horizontal

`meta.security-auditor` pode aparecer como horizontal em software. Implementação de fix continua em engenharia, não no auditor.

## 29. O que este pack não cobre

Instalação de scanners no PATH da VM · Contas VirusTotal/SIEM · Detalhes de implementação do CouncilSession (ver `docs/ops/COUNCIL.md`) · Ingestão fora do MANIFEST/workflow · Garantias legais de conformidade.

---

## Fora de âmbito deste pack

Código de exploit · Substituição do plan_runner · Área `cyber` separada · Métricas inventadas de redução de risco