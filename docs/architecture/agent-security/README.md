# Agent security — best practices (setup)

## Ideia central

Não dá para garantir que o modelo resiste a prompt injection. Assume que pode ser manipulado e **limita o que ele pode fazer**.

> System prompt **não** é controlo de segurança.

## Checklist (alta alavancagem)

| # | Controlo | Porquê |
|---|----------|--------|
| 1 | **Least-privilege tools** (allowlist por agente e por passo) | Tool que não existe não pode ser abusada |
| 2 | **Default-deny** + política fora do modelo | Gate em runtime, não no texto do prompt |
| 3 | **Input não confiável** (user, web, RAG, tool output) delimitado; nunca como instrução | Injection indirecta |
| 4 | **Output validation** / sandbox para código | Execução inesperada |
| 5 | **PII e secrets** redigidos na fronteira; credenciais short-lived | Exfiltração |
| 6 | **Human-in-the-loop** em acções de alto impacto | Deploy, delete, pagamento, produção |
| 7 | **Identidade por agente** (não partilhar admin humano) | Atribuição e blast radius |
| 8 | **Audit log** de tool calls e planos | Forense e “feito com evidência” |
| 9 | **Separar leitura sensível de escrita externa** (agentes diferentes) | Comprometer um não completa o ataque |
| 10 | **Budget** (max steps, replans, tokens) | Loops e custo |

## Alinhamento com Plan-Execute

- `tools_allowed` por step = task-scoped tools
- Planner sem tools de escrita em produção
- `human_gate` / `on_fail: human` = HITL
- `verify` + CriticReport = segunda opinião antes de publish

## OWASP (orientação)

Riscos agentic típicos: goal hijack, tool misuse, privilege abuse, memory poisoning, excessive agency. Mitigação principal = **agency mínima** + gates, não “melhor prompt”.

## Prática no setup

1. Constitution com bans de produção e secrets
2. Nenhum secret no git; rever `.gitignore` após Spec Kit init
3. Skills de `security-and-hardening` / TDD no verify de código
4. Produção (`agent-network-mcp`) só com mudança deliberada
