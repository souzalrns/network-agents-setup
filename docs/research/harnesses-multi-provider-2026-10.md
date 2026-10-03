# Harnesses multi-provider: reavaliação (INIT-094)

> **Data:** 2026-10-03. **ID:** INIT-094 em `docs/initiatives/PENDENCIAS.md` (antes F8 no OPEN-ITEMS e EX-F8).
> **Natureza:** análise e proposta. **Nada foi adoptado nem instalado.**
> **Origem do item:** a tabela de `docs/initiatives/STATUS.md` (secção "Harnesses multi-provider") nunca tinha sido reverificada (`docs/initiatives/OPEN-ITEMS.md:23`).

## 1. Método e limites

- **Fonte:** a página pública de cada repo no GitHub, lida a 2026-10-03.
- **Como foi lida:** através de uma ferramenta que resume a página com um modelo pequeno. Os números (estrelas, licença, commits) são os que a página mostrava, tal como resumidos.
- **Limite:** antes de qualquer decisão de adopção, o DEV deve confirmar estrelas e licença na página (ou com `gh api repos/<owner>/<repo>`).
- **O que não foi feito:** não li o código de nenhum harness nem corri nenhum. A data do último commit não aparecia na página resumida.

## 2. Verificação (tabela antiga → hoje)

| Repo | STATUS dizia | Página a 2026-10-03 | Diferenças |
|---|---|---|---|
| `deepseek-ai/deepseek-harness` | 200k, MIT, "everything is a plugin" | **Existe.** 242,9k ★, MIT, não arquivado, 20 736 commits. "Everything-is-a-plugin agent harness built on Cordis", em *developer preview* | Estrelas a subir; está em *preview* |
| `omnigent-ai/omnigent` | 9k, meta-harness sobre Claude Code, Codex e Cursor | **Existe.** 10,4k ★, **Apache-2.0**, não arquivado, 4 389 commits. "Meta-harness: orchestrate Claude Code, Codex, Cursor, Pi, and custom agents" | A licença não estava na tabela |
| `lidge-jun/opencodex` | 12k, proxy universal | **Existe.** 16,9k ★, MIT, não arquivado, 12 253 commits, 50 issues e 63 PRs abertos. Proxy local com dashboard: qualquer LLM (Claude, Gemini, Grok, DeepSeek, Ollama) no Codex, Claude Code, Claude Desktop e Grok Build | Também serve o Claude Code, não só o Codex |
| `yc-software/qm` | 14k, harness multiplayer | **Existe.** 15,3k ★, MIT, não arquivado, 799 commits. "Multiplayer agent harness for work. In Slack and on the web. Run it in your own cloud, with your own models and keys" | — |
| `xai-org/grok-build` | 26k, harness xAI | **Existe.** 27,2k ★, **Apache-2.0**, não arquivado, **51 commits**. TUI de coding agent (edita ficheiros, corre shell, pesquisa na web) | A licença não estava na tabela; tem poucos commits (projecto novo ou espelho) |
| `anywhere-labs/dsh-desktop` | 21k, desktop para DeepSeek | **Existe.** 29,9k ★, MIT, não arquivado, 13 628 commits, 262 issues. Cliente desktop do **ecossistema de plugins do DeepSeek Harness** | Não é um "desktop DeepSeek" genérico: depende do `deepseek-harness` |

**Contradição para o §8 do PENDENCIAS:** a tabela do STATUS tinha estrelas desactualizadas, não indicava as licenças Apache-2.0 do omnigent e do grok-build, e descrevia mal o `dsh-desktop`.

## 3. Relevância para este repo

O critério é o que o runner precisa hoje, e não a popularidade. Do lado do repo:
- o runtime é o `plan_runner` Python com worker Gemini (D1, VIA A), com premissa de custo zero ou próximo de zero (`docs/architecture/EXECUTION-PLAN.md:39`);
- o fallback multi-provider é desenho preliminar (EXECUTION-PLAN §8.5–8.6);
- o `model_tier` (D5) já escolhe o modelo por passo, mas só dentro da Gemini API.

| Repo | Para que serviria aqui | Encaixe hoje | Riscos |
|---|---|---|---|
| deepseek-harness | Substituir o runtime | **Não**: seria um 2.º runtime, contra a D1 (`docs/audit/DECISAO-1-runtimes.md`) e o EXECUTION-PLAN §10.1 ("Segundo runtime… Não fazer agora", `:854`) | Plugin-everything = superfície grande; em *preview* |
| omnigent | Orquestrar coding agents externos (Claude Code, Codex) | Baixo: o repo orquestra agentes de domínio, não coding agents | Mais uma camada sobre ferramentas pagas |
| **opencodex** | **Proxy de providers**: o worker passava a falar com vários LLMs por uma API | **Médio, só no F3/§8.6**, quando houver mais de um provider. É a mesma necessidade do LiteLLM (AUDIT-EVALUATION §4) | Proxy local que vê todas as chaves e prompts; 63 PRs abertos |
| qm | Agentes em Slack/web | Baixo: o canal deste repo é o MCP (Claude.ai connector) | Dados em Slack |
| grok-build | Coding agent em TUI | Nenhum: é uma ferramenta de developer, não uma peça do runner | Corre shell; 51 commits |
| dsh-desktop | Cliente do deepseek-harness | Nenhum: depende de um runtime que não se adopta | Herda os riscos do deepseek-harness |

## 4. Proposta (decisão do maestro)

| | Opção |
|---|---|
| **A (recomendada)** | **Não adoptar nenhum agora.** Registar o `opencodex` (e o LiteLLM, AUDIT-EVALUATION §4) como candidatos do F3/§8.6, quando o runner precisar de um 2.º provider. Os outros 5 ficam como referência, sem acção |
| B | Spike do `opencodex` já, com o worker a apontar para o proxy local (exige um 2.º provider e chaves: custo e decisão do DEV) |
| C | Fechar o INIT-094 como OBSOLETO (nenhum encaixa) e retirar a secção do STATUS |

**Porque A:**
- B gasta tempo e chaves antes de existir a necessidade (hoje só há Gemini);
- C perde o único candidato com encaixe real (o proxy de providers);
- A não corta nada e fixa o momento certo para reabrir (F3/§8.6).
