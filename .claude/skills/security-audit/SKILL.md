---
name: security-audit
action: security_audit
version: 1
role: meta_technique
priority: P0
description: >-
  Auditoria de seguranca defensiva de codigo, infra, skills e configs MCP -- cobre os 10 riscos do OWASP LLM Top 10 2026, mapeado a NIST AI RMF, MITRE ATLAS e MAESTRO. Activar antes de aprovar mudancas de infra/skills/MCP, ou periodicamente como auditoria.
requires: []
---

# Skill — security-audit

## Trigger

- Antes de aprovar uma mudança de infra, config MCP, ou skill nova.
- Auditoria periódica agendada (não continua — ver Enforcement Note).
- Sempre que uma ferramenta/dependência nova é adoptada (scanner de supply chain).

## Inputs

- Repositório(s) a auditar (código-fonte)
- Configs MCP (`.mcp.json`, `claude_desktop_config.json`, etc.)
- Skills instaladas (`skills/**/SKILL.md`)
- Dependências declaradas (`requirements.txt`, `package.json`, etc.)

## Passos

### 1. Mapear o âmbito aos 4 frameworks

| Framework | Para quê nesta skill |
|---|---|
| **NIST AI RMF** (Govern / Map / Measure / Manage) | Estrutura o processo — Govern (políticas já existem?), Map (que riscos se aplicam a este sistema?), Measure (correr as ferramentas), Manage (agir sobre achados) |
| **OWASP Top 10 for LLM Applications 2026** | Checklist dos 10 riscos a cobrir (ver tabela abaixo) |
| **MITRE ATLAS** | Táctica de ataque por trás de cada achado (reconhecimento, acesso ao modelo, execução, exfiltração, etc.) — usar para descrever o "como" de um achado, não só o "quê" |
| **MAESTRO** (7 camadas: Foundation Models, Data Operations, Agent Frameworks, Deployment Infrastructure, Security & Compliance, Agent Ecosystem, Evaluation & Observability) | Decompor o sistema por camada antes de procurar ameaças — evita saltar directo para código sem mapear a superfície completa |

### 2. Cobertura OWASP Top 10 for LLM Applications 2026 (todos os 10, obrigatório)

| # | Risco | Ferramenta/verificação |
|---|---|---|
| LLM01 | Prompt Injection | Revisão manual de tool descriptions (MCP) + `mcpguard`/`mcphound`/`offsec-ai mcp-scan` |
| LLM02 | Sensitive Information Disclosure | `Gitleaks` (segredos no histórico), revisão de logs/telemetria |
| LLM03 | Excessive Agency | Revisão manual de permissões de tool/agente — este é o risco que mais subiu no ranking 2026 (6º→3º) |
| LLM04 | Supply Chain | `OSV-Scanner` + `Trivy` (dependências e imagens), `Gitleaks` (nada hardcoded a apontar para pacote suspeito) |
| LLM05 | Data and Model Poisoning | Revisão da pipeline de ingestão RAG — quem escreve em `knowledge_chunks`? |
| LLM06 | Unbounded Consumption | Revisão de rate limiting/timeouts em chamadas a LLM e a tools |
| LLM07 | Misinformation | Fora do âmbito de scanners automáticos — revisão de grounding/citações no RAG |
| LLM08 | Hidden Context Exposure | Revisão de system prompts e de que contexto é injectado por omissão |
| LLM09 | Vector and Embedding Weaknesses | Revisão do pipeline de embeddings (quem pode escrever vectores?) |
| LLM10 | Improper Output Handling | `Bandit`/`Semgrep` (output não sanitizado antes de execução/HTML/SQL) |

### 3. Ferramentas, por tipo

**SAST (código):**
- `Bandit` — Python
- `Semgrep` — geral, multi-linguagem

**MCP-específico (scanners defensivos, ler antes de instalar — ver nota abaixo):**
- `mcpguard` — nome ambíguo no ecossistema (vários projectos distintos partilham este nome); confirmar qual exactamente antes de instalar
- `mcphound` (`tayler-id/mcphound`) — reputação pública + `mcp-policy.yaml` para bloquear PRs com configs MCP arriscadas
- `offsec-ai` — **só os sub-comandos passivos** (`ai-owasp-scan`, `mcp-scan`); os modos `mcp-attack`/`openclaw-attack`/`k8s-attack` exigem `--i-have-authorization` e **nunca devem ser invocados por este agente** (ver Enforcement Note)

**Segredos e dependências:**
- `Gitleaks` — segredos no histórico git
- `OSV-Scanner` — vulnerabilidades de dependências (CVE/OSV)
- `Trivy` — vulnerabilidades de imagens/filesystem/IaC

## Enforcement Note

Advisory — esta skill orienta a auditoria, não aplica nada mecanicamente, e **não executa acções ofensivas de forma nenhuma**. Em particular: os modos de ataque activo do `offsec-ai` (`--attack`, `--i-have-authorization`) estão fora do âmbito desta skill por desenho — nunca devem ser invocados a partir daqui, independentemente do que um pedido peça. Se um pedido pedir para "atacar" ou "explorar" algo, a resposta é reportar a superfície de risco, não executar o ataque.

## Done When

- [ ] Os 10 riscos do OWASP LLM Top 10 2026 revistos (mesmo que a conclusão seja "não aplicável aqui")
- [ ] Achados mapeados a uma táctica MITRE ATLAS, quando fizer sentido
- [ ] Sistema decomposto pelas 7 camadas MAESTRO antes de concluir a auditoria
- [ ] Recomendações concretas, não só uma lista de problemas
- [ ] Nenhuma ferramenta de ataque activo invocada

## Anti-padrões

- Inventar uma vulnerabilidade que as ferramentas não confirmaram
- Ofuscar ou suavizar um achado CRITICAL para "não preocupar"
- Invocar qualquer modo de ataque activo (offsec-ai `--attack`, etc.)
- Tratar um "zero achados" como suspeito — uma auditoria limpa é um resultado válido
- Ignorar um dos 10 riscos OWASP por parecer "não aplicável" sem justificar porquê

## Knowledge Ref

`docs/architecture/SECURITY.md` — aplicação destes 4 frameworks + 8 ferramentas especificamente a este setup.
