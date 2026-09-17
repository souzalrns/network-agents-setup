# Auditoria de Segurança — network-agents-setup (2026-09-17)

Primeira execução real do `security_auditor` (B2) contra este repositório, seguindo `skills/meta/security-audit/SKILL.md`. Ferramentas correram de verdade, em venv isolado, contra um clone completo do repo (`303 commits`) — não é uma simulação. Só leitura: nada foi corrigido nem alterado.

## 1. Resultado por ferramenta

| Ferramenta | Alvo | Resultado | Nota |
|---|---|---|---|
| **Bandit** 1.9.4 | `runner/plan_runner/` (2289 linhas) | 2 achados LOW | Ver secção 2 |
| **Bandit** 1.9.4 | `mcp/plan_runner/mcp_plan_runner/` (275 linhas) | 0 achados | Limpo |
| **Semgrep** 1.177.0 | `runner/`, `packages/core/src/`, `scripts/`, `apps/` | 0 achados (4 regras) | **Cobertura reduzida** — `semgrep.dev` bloqueado pelo allowlist de rede desta sandbox; corri um ruleset local mínimo (4 regras: segredo hardcoded, `eval`/`exec`, `subprocess shell=True`) em vez do registo completo (`p/security-audit`, centenas de regras). **Não tratar como equivalente a uma corrida completa** |
| **Gitleaks** 8.30.1 | Histórico git completo (303 commits) | 0 segredos encontrados | Alta confiança — histórico inteiro, não só o snapshot actual |
| **OSV-Scanner** 2.6.0 | `pnpm-lock.yaml` (307 pacotes), `runner/requirements.txt` (4 pacotes) | **Inconclusivo** | Inventário de pacotes extraído correctamente, mas a consulta à base de dados de vulnerabilidades (`api.osv.dev`, `api.deps.dev`) foi bloqueada pelo allowlist de rede desta sandbox. **Não é "0 vulnerabilidades confirmadas"** — é "não foi possível verificar" |
| **mcpguard** | Configs MCP (`.mcp.json`, `claude_desktop_config.json`) | **Sem alvo** | Não existe nenhum ficheiro de config MCP neste repo — o que existe é `mcp/plan_runner/`, uma **implementação** de servidor MCP, não uma config de cliente. Fiz revisão manual do código-fonte desse servidor em vez de forçar uma ferramenta sem alvo — ver secção 3 |

## 2. Achados do Bandit (com ficheiro/linha)

**LOW — `runner/plan_runner/cli.py:54`** (B110, `try_except_pass`)
```python
except Exception:
    pass
```
Excepção engolida em silêncio — se `load_status` falhar por uma razão inesperada (não só "ficheiro não existe"), fica sem rasto nenhum.

**LOW — `runner/plan_runner/working_memory.py:52`** (B101, `assert_used`)
```python
assert out_dir is not None
```
`assert` é removido quando o código corre com `python -O` (bytecode optimizado) — se isto é uma invariante que tem mesmo de se verificar em produção, um `assert` não garante isso.

## 3. Revisão manual — `mcp/plan_runner/` (servidor MCP)

Como não havia config de cliente MCP para o `mcpguard` escanear, revi o código-fonte do servidor directamente (`policy.py`, `tools_impl.py`, `server.py`).

**O que está bem feito:**
- Sanitização de caminho contra directory traversal (`sanitize_repo_path`, `policy.py`) — todo acesso a ficheiros é confinado à raiz do repo.
- Rate limiting por caller (`policy.py:~100`, 60 pedidos/60s).
- Log de auditoria em `audit.jsonl` para toda chamada de tool, com sucesso/falha e razão.
- Transporte só `stdio` (`server.py`, `mcp.run(transport="stdio")`) — não está exposto pela rede por omissão, o que reduz bastante o risco real do achado abaixo.

**Achado MEDIUM — `mcp/plan_runner/mcp_plan_runner/policy.py:73`** (mapeia a **OWASP LLM03 — Excessive Agency**)
```python
if prof == "moderate":
    # Lab default: allow mutate without key but record reason (audit still runs)
    return AuthContext(prof, caller, True, "moderate_lab_open")
```
O perfil por omissão (`PLAN_RUNNER_MCP_PROFILE`, default `"moderate"`) permite chamar `run_plan`/`resume_plan` — as duas tools que **executam código** via `plan_runner.engine` — **sem nenhuma chave de autenticação**, desde que `PLAN_RUNNER_MCP_KEY` não esteja definida. É um comportamento intencional e comentado como "lab default", não um bug escondido — mas se este servidor alguma vez correr fora de um contexto de laboratório local, isto é uma porta aberta para execução sem controlo. Mitigado parcialmente pelo transporte `stdio`-only.

**Achado LOW — `tools_impl.py` (múltiplas linhas: 40, 55, 91, 118)** (roça **OWASP LLM02 — Sensitive Information Disclosure**)
```python
except Exception as e:
    return {"ok": False, "error": str(e)}
```
Repetido em `get_status`, `run_plan`, `resume_plan` — a mensagem de erro interna (`str(e)`, que pode incluir caminhos de ficheiro do sistema) é devolvida directamente ao chamador MCP, sem sanitização.

## 4. Mapeamento OWASP Top 10 for LLM Applications 2026

| # | Risco | Coberto nesta auditoria? |
|---|---|---|
| LLM01 | Prompt Injection | **Não coberto** — precisaria de `mcp-scan`/`mcphound`/`offsec-ai` contra o servidor MCP a correr ao vivo; não estava no âmbito desta corrida |
| LLM02 | Sensitive Information Disclosure | Parcial — Gitleaks limpo (segredos), mas achado LOW acima (erros internos expostos) |
| LLM03 | Excessive Agency | **Coberto, achado real** — ver secção 3 (MEDIUM) |
| LLM04 | Supply Chain | **Inconclusivo** — OSV-Scanner bloqueado pela rede da sandbox |
| LLM05 | Data and Model Poisoning | Não coberto nesta corrida (fora do âmbito das 5 ferramentas pedidas) |
| LLM06 | Unbounded Consumption | Parcial — rate limiting confirmado no MCP server (`policy.py`); não verificado do lado do `LLMService`/Gemini |
| LLM07 | Misinformation | Não coberto (não é alvo de scanner automático) |
| LLM08 | Hidden Context Exposure | Não coberto nesta corrida (já tratado separadamente em G4, mas isso foi no `agent-network-mcp`, não neste repo) |
| LLM09 | Vector and Embedding Weaknesses | Não coberto nesta corrida |
| LLM10 | Improper Output Handling | **Coberto, limpo** — Bandit + Semgrep sem achados de `eval`/`exec`/injecção |

**3 de 10 cobertos com confiança nesta corrida; 1 inconclusivo; 6 fora do âmbito desta execução específica** (exigem ferramentas ou alvo que esta corrida não teve — não é o mesmo que "seguro").

## 5. NIST AI RMF aplicado a esta auditoria

| Função | Estado |
|---|---|
| **Govern** | Política já documentada em `GOVERNANCE.md`/`SECURITY.md`, mas o `SecurityManager.ts` continua MOCK (`CORE-MAPPING.md`) — governança no papel, não em código, para autenticação real |
| **Map** | Este relatório + `SECURITY.md` |
| **Measure** | Feito nesta tarefa — com as limitações de rede da sandbox documentadas, não escondidas |
| **Manage** | Secção 6 abaixo — recomendações para entrar no `STATUS.md` |

## 6. Recomendações, por prioridade

1. **[Corrigir primeiro] `policy.py:73` — perfil `moderate` por omissão permite execução sem chave.** Documentar bem alto (README do `mcp/plan_runner/`) que `moderate` é só para uso local de laboratório, ou mudar o default para `strict` fora de um flag explícito de ambiente de dev.
2. **Sanitizar `str(e)` antes de devolver ao chamador MCP** nas 3 funções de `tools_impl.py` — mensagem genérica para o chamador, detalhe completo só no `audit.jsonl` local.
3. **Re-correr o OSV-Scanner** num ambiente com acesso a `api.osv.dev`/`api.deps.dev` — esta sandbox não consegue confirmar nem descartar vulnerabilidades de dependências; ficou genuinamente por saber.
4. **Re-correr o Semgrep com o registo completo** (`p/security-audit`, `p/owasp-top-ten`) num ambiente com acesso a `semgrep.dev`, ou vendorizar esses rulesets localmente — as 4 regras caseiras desta corrida são um substituto fraco.
5. **Cobrir LLM01 (Prompt Injection) numa próxima passagem**, correndo `mcphound`/`offsec-ai mcp-scan` contra o servidor MCP a correr de facto — não foi feito aqui.
6. `B110`/`B101` do Bandit — baixa prioridade, mas de correcção trivial (logar a excepção; trocar o `assert` por uma verificação explícita se for invariante real).

## 7. O que ficou por saber (honestidade sobre os limites desta corrida)

- Supply chain (LLM04): inconclusivo, não "seguro".
- Prompt injection (LLM01), poisoning (LLM05), embeddings (LLM09): fora do âmbito das 5 ferramentas pedidas nesta tarefa — não testados, não assumir que estão bem.
- Cobertura Semgrep: 4 regras caseiras, não o registo completo.

Nada foi corrigido. `packages/core/` e `agent-network-mcp` não foram tocados (nem sequer clonados para esta auditoria — só o `network-agents-setup`, como pedido).
