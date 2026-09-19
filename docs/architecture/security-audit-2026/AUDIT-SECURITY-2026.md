# AUDIT-SECURITY-2026.md — Auditoria de segurança, extensão 2026-09-19

Consolida `SECURITY-AUDIT.md`/`SECURITY-AUDIT-FULL.md` (8 ferramentas já corridas, resultado auto-declarado: 4/10 riscos OWASP LLM Top 10 2026 cobertos com confiança, 1 inconclusivo, 5 fora do âmbito) com pesquisa de fontes primárias para fechar o que a sandbox original não conseguiu (rede bloqueada para `api.osv.dev`/`api.deps.dev`/`mirror.gcr.io`).

## 1. Correção ao inventário assumido

O inventário real de dependências (lido do `pnpm-lock.yaml` resolvido, não do `package.json`) é diferente do assumido por auditorias anteriores: **não há LangChain, Anthropic SDK, Supabase-js nem Zod** como dependências directas confirmadas. O que existe de facto: `express@4.22.3`, `helmet@7.2.0`, `ws@8.21.3`, `pg@8.23.0`, `ioredis@5.11.1`, `@prisma/client@5.22.0`, `axios@1.20.0` (resolvido — o `package.json` pede `^1.6.0`, mas a versão que importa é a resolvida), `bcryptjs@3.0.3`; Python: `mcp==1.30.0` (pinned), `langgraph>=0.6.11` (**sem tecto de versão**).

**Achado estrutural mais importante desta secção:** não existe nenhum lockfile Python (`poetry.lock`/`uv.lock`/`Pipfile.lock`) no repo. Isto significa que LLM04 (Supply Chain) do lado Python é **inverificável mesmo com rede livre** — não é só que o scanner estava bloqueado, é que não há registo do que fica de facto instalado num build. Isto é mais fundamental do que a limitação de rede já conhecida.

## 2. LLM04 — Supply Chain (verificação real, não mais "inconclusivo")

| Dependência | Achado |
|---|---|
| `mcp==1.30.0` | CVE-2025-66416 (DNS rebinding), CVE-2026-52869, CVE-2026-52870 — todas afetam versões anteriores a 1.23.0/1.27.2. **1.30.0 é posterior a todas → não vulnerável.** |
| `axios@1.20.0` | Posterior aos fixes confirmados (CVE-2026-40175 CRLF corrigido em 1.15.0; prototype pollution corrigido em 1.18.0). OSV.dev lista mais 10 GHSA sem range exato confirmado — não fechado por completo. |
| `ws@8.21.3` | Posterior ao fix de CVE-2024-37890 → não vulnerável. |
| `langgraph>=0.6.11` (sem tecto) | CVE-2026-28277 (deserialização msgpack insegura em checkpoints) afeta `<=1.0.9`, corrigido em 1.0.10. **Não é possível confirmar qual versão está instalada de facto** — sem tecto no requirements, resolve para "o que houver" no momento do build. |

**Classificação:** NOT VERIFIED (parcial, transitivas) / **BUILD prioritário: gerar lockfile Python** (`uv lock` ou `pip-compile --generate-hashes`) — sem isto, nenhum scanner futuro resolve o problema de raiz.

## 3. LLM05 — Data/Model Poisoning (pipeline RAG)

A base de conhecimento é Markdown **git-tracked** (`docs/knowledge/**`), ingerida via manifesto hardcoded — superfície bem menor que o cenário genérico "upload arbitrário envenenado". Risco residual real: `content_hash` (SHA-256) só deteta mudança, não prova legitimidade — uma conta comprometida ou PR mal revisto passa direto para o pgvector, sem gate de autenticidade além da revisão de PR (se estiver de facto imposta por branch protection — a confirmar).

**Classificação:** ADOPT (mínimo) — confirmar que `docs/knowledge/**` tem branch protection real, não só convenção.

## 4. LLM06 — Unbounded Consumption

Confirmado por leitura direta (`policy.py:129`): rate limit é 60 chamadas/60s por caller, em memória de processo, **sem qualquer contagem de tokens ou custo**. Cruza diretamente com o achado da auditoria de Evaluation/Cost-Routing desta mesma sessão: `model_tier` é só schema (zero implementação), e não há tecto de custo em lado nenhum do `budget:` do Plan schema (só `max_replans`/`max_steps`).

**Recomendação mínima:** LiteLLM Router com `max_budget`/`budget_duration` por `model_tier` (ver `evaluation-audit/AUDIT-EVALUATION.md`), correlacionado por `plan_id`/`step_id`.

## 5. LLM08 — Hidden Context Exposure

Sem achado novo — aponta para a mesma lacuna já conhecida (LLM03, `ToolExecutor.ts` sem verificação de scope): tool schemas expostos amplificam a superfície deste risco. Não é um problema separado, é o mesmo problema visto de outro ângulo.

## 6. LLM09 — Vector and Embedding Weaknesses

**Achado concreto e acionável, novo:** `knowledge_chunks_t6` **não tem Row Level Security (RLS) ativada**. O isolamento por `agent_id`/`kb` é feito (presumivelmente) só na camada de aplicação — qualquer código com acesso a `DATABASE_URL` lê/escreve chunks de qualquer agente/kb sem precisar de contornar nada. A Supabase documenta o padrão exato para isto ("RAG with Permissions").

**Classificação:** ADOPT — adicionar políticas RLS chaveadas por `agent_id`/`kb`; é uma mudança pequena (`CREATE POLICY`) sobre um schema que já tem as colunas certas.

> **RESOLVIDO em 2026-09-19 — RLS activado em `knowledge_chunks_t6` e `knowledge_sources`, replicando o padrão já aplicado a `knowledge_chunks` e `knowledge_log` (policy `*_anon_deny` TO anon USING false). O writer (`supabase_writer.py`, role `postgres` + BYPASSRLS) não é afectado. Sem isolamento por agente (modelo de identidade inexistente). Ver `EXECUTION-PROMPTS.md` A2.**

## 7. Secrets management — achado mais grave do que a caracterização original

Confirmado: a linha `database-url: postgresql://network:network123@postgres:5432/network_agents` em `k8s/secrets.yaml` é um **valor literal hardcoded**, nem sequer um placeholder `${...}` como a linha irmã (`openai-api-key: ${OPENAI_API_KEY}`) já usa — inconsistência dentro do próprio ficheiro.

**Classificação:** ADOPT (SOPS, não ESO/Vault — desproporcional para a escala deste repo) + ação imediata: rodar a password, trocar o valor por um placeholder inequívoco.

> **RESOLVIDO do lado do repo em 2026-09-19 (item A1 de `EXECUTION-PROMPTS.md`):** Claude trocou os 5 valores literais `network123` (`.env.example`, `docker-compose.yml` ×2, `k8s/postgres.yaml`, `k8s/secrets.yaml`) por placeholders/env vars (`CHANGE_ME`, `${POSTGRES_PASSWORD}`, `${DATABASE_URL}`, `secretKeyRef`), replicando a convenção já usada em `openai-api-key: ${OPENAI_API_KEY}`. Verificado por grep: zero ocorrências de `network123` nos 5 ficheiros. A senha real foi rotacionada pelo Desenvolvedor **fora do repo, directamente no Supabase**, durante esta mesma sessão. **Dependência nova registada:** ver item **A1b** em `EXECUTION-PROMPTS.md` — antes de este `k8s/` ser aplicado a um cluster real, é preciso criar o Secret real fora do git e confirmar que o pipeline de deploy resolve `${...}`.

## 8. Cobertura OWASP LLM Top 10 2026 — tabela final

| Risco | Estado após auditoria original | Estado após esta extensão |
|---|---|---|
| LLM01 Prompt Injection | Coberto (genérico) | Sem mudança — scan estático só, runtime por implementar |
| LLM02 Sensitive Info Disclosure | Coberto | Achado mais grave confirmado (`k8s/secrets.yaml` valor literal). **RESOLVIDO em 2026-09-19 (A18)**: 29 sítios de leakage de `error.message` cru (stack traces, IPs internos, paths, mensagens de driver de BD/Prisma) em 11 ficheiros — `packages/mcp/src/**` (7 ficheiros) e `apps/api/src/**` (4 ficheiros, incluindo `websocket.ts`/`ChatController`/`HitlController`, que fazem catch próprio e nunca chegam ao `errorHandler.ts` central). Corrigidos via 2 helpers `toClientError(error, context)` (um por pacote, mesma assinatura) — nomeiam a operação ao cliente, nunca o detalhe; log interno completo preservado. Escopo real era 7× o estimado no brief original (que citava só 4 ficheiros). Testado: 21 testes novos, suite completa 145/145. Ver `EXECUTION-PROMPTS.md` A18. |
| LLM03 Excessive Agency | Confirmado | Sem mudança |
| LLM04 Supply Chain | Inconclusivo | Parcialmente resolvido (JS); Python **estruturalmente inverificável sem lockfile** |
| LLM05 Data/Model Poisoning | Não coberto | Modelo de ameaça mapeado, risco pequeno mas real |
| LLM06 Unbounded Consumption | Não re-testado | Gap confirmado, recomendação concreta (LiteLLM) |
| LLM07 Misinformation | Não coberto | Não investigado (fora do âmbito desta extensão) |
| LLM08 Hidden Context Exposure | Não coberto | Sem achado novo — mesma raiz que LLM03 |
| LLM09 Vector/Embedding Weaknesses | Não coberto | **Gap concreto e acionável: falta RLS** |
| LLM10 Improper Output Handling | Coberto, limpo | Sem mudança |

**A20 verificado 2026-09-19** — `helmet()` já estava activo em `apps/api/src/server.ts:24` com 12 headers (CSP/X-Frame-Options/HSTS/etc.), confirmado por leitura e empiricamente (pedido real, servidor local). Contradiz o checklist item 18 ("❌"), desactualizado. Ajuste aplicado: `crossOriginResourcePolicy` para `'cross-origin'` (o omissão `'same-origin'` do helmet contradizia o `cors()` aberto logo a seguir). **S13** registado para o CORS em si (aceita qualquer origem, decisão humana necessária sobre quais origens são legítimas).

**Honestidade:** pesquisa de fontes primárias não substitui scanner a correr. LLM04/06/09 ganharam recomendação concreta; LLM05/07/08 continuam sem qualquer ferramenta ou teste, só análise manual.

## 9. O que NÃO fazer

- Não montar billing multi-tenant com Redis para LLM06 — um contador simples persistido chega para o estado actual.
- Não adoptar ESO/Vault para um único ficheiro `k8s/secrets.yaml` — overkill para a escala deste repo (SOPS é o encaixe certo).
- Não adicionar detecção de anomalia em embeddings já — a KB é pequena e git-controlada; o gate de PR já cobre o vetor mais provável.
- Não adoptar scanner de prompt injection em runtime (LLM Guard/Rebuff) antes de fechar LLM03 (`moderate_lab_open`) — seria sequenciar trabalho de superfície antes da raiz.
- Não continuar a caçar CVEs manualmente biblioteca-a-biblioteca — a partir daqui só rede liberada + OSV-Scanner/`pnpm audit` fecha isto por completo.
