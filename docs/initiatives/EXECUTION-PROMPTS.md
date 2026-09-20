# EXECUTION-PROMPTS.md — Prompts de execução, padrão ouro

## Errata (2026-09-19 — verificação padrão ouro pós-escrita, 6 erros reportados)

Depois de todo o documento estar escrito (Grupos A-J), foi feita uma passagem de verificação dedicada sobre 6 suspeitas de erro de estrutura/contagem, cada uma confirmada ou refutada por leitura directa do texto (não por confiança na primeira versão). Nada foi apagado — as correções foram aplicadas nos pontos exactos abaixo, mantendo o formato original (tabelas, 4 fases por item).

1. **CONFIRMADO — contagem total errada.** O item **I8** (`Obsidian/Logseq = F10`) diz explicitamente, no seu próprio texto: *"Já tratado integralmente em G4.1 — este item não existe separadamente"*. Logo o Grupo I tem **10 itens efectivos**, não 11 — o próprio título do grupo ("10 itens", linha do cabeçalho) já estava certo; era só o fecho do grupo e a Contagem final que ainda diziam "11". Corrigido: fecho do Grupo I (11→10), "I(11)"→"I(10)" e total "109 itens"→"**108 itens**" na Contagem final, e a menção solta "(109+7 itens)" no item J7. Confirmação adicional: o preâmbulo já dizia "108" duas vezes (linhas 5 e 9, escritas antes da inconsistência aparecer) — o número certo sempre foi 108, o resto do documento é que não tinha sido actualizado.
2. **REFUTADO — G1 não precisa perder o item G1.14.** A alegação era que G1.14 ("Critério de 'pronto' do cluster inteiro") não é um item de trabalho porque a sua Fase 2 diz "não há execução de código aqui — é aprovação", e por isso G1 teria 13 itens + 1 critério, não 14. Mas o próprio Grupo G1 já tem precedente interno para isto: **G1.5** ("Isolar credenciais financeiras") também diz, na sua Fase 2, "não há 'execução' positiva aqui — é uma restrição a manter", e ninguém propôs tirá-lo da contagem de 14. O documento conta consistentemente itens de decisão/aprovação sem código como itens completos noutros grupos (F7, G2.2, G2.3, G4.1, H3, H4 são todos "Quem: Desenvolvedor" e são só decisão). G1.14 tem as 4 fases preenchidas com conteúdo real (checklist assinado, fecho do cluster) — é diferente em espécie do I8, que declara não existir como item separado. **Nada foi alterado** — G1 mantém-se em 14 itens.
3. **PARCIALMENTE CONFIRMADO, resolvido sem restruturar.** É verdade que 6 dos 7 itens do Grupo J (J1, J2, J3, J4, J5, J7) têm "nenhuma acção agora" nas Fases 2-4, o que os torna estruturalmente diferentes dos itens accionáveis A-I. Em vez de separar o documento em duas somas (o que obrigaria a reescrever o formato da Contagem final e possivelmente confundir mais), foi adicionada uma única frase de desagregação: **101 itens accionáveis (Grupos A-I) + 7 arquivados (Grupo J) = 108 itens**, mantendo a fórmula original A+B+...+J intacta.
4. **REFUTADO — C6 não é redundante.** A alegação era que, como C8e já está em `## Done` no `STATUS.md` desde 2026-09-17, o item C6 ("Confirmar C8e fechado") seria uma pendência falsa. Mas o próprio texto de C6 já assume isto — a sua Origem diz literalmente "já em Done, mas nunca revalidado nesta sessão" e a Fase 4 já diz "já está em Done — só adicionar nota de 'revalidado em [data]'". C6 não afirma que C8e está pendente; é um item de **revalidação** (rodar a suite de teste real e confirmar que continua a passar), o mesmo padrão "confiar mas verificar" usado em F2/F3/F4 para itens já migrados. **Nada foi alterado.**
5. **CONFIRMADO — e mais amplo do que reportado.** A colisão de nomenclatura não é só F3/F4 vs. Grupo G3/G4 deste documento: o `STATUS.md` tem a sua própria série "G" (Mapeamento/Governança, `docs/initiatives/STATUS.md` linhas 129-147): **G1**=fechar C8e, **G2**=16 skills, **G3**=5 knowledge packs, **G4**=13 agentes horizontais, **G5**=2 achados do MCP-MAPPING por resolver. Este documento reaproveita "G1/G2/G3/G4" para os seus próprios grupos (Financeiro/Gamedev/Avatar/Grafo de memória) — colisão total, não só nos dois casos apontados. Em vez de renumerar tudo (arriscado, toca em dezenas de referências cruzadas de G1.1 a H4), foi adicionada uma nota de nomenclatura em cada cabeçalho de grupo G1-G4 deste documento e em cada Origem de F2/F3/F4/C6, remetendo um para o outro. Nenhum ID foi renomeado.
6. **CONFIRMADO.** A Fase 1 de J6 afirmava como facto assente *"a necessidade pode ter chegado"*, mas D5/D6 (a razão apontada) ainda não foram executados nesta altura — só estão desenhados como itens pendentes no Grupo D deste mesmo documento. Isto contradizia a própria Fase 2 de J6, que já tratava isto correctamente como condicional ("quando D5/D6 forem executados, revisitar"). Corrigido: a Fase 1 agora deixa explícito que a necessidade **ainda não chegou** e só chega quando D5/D6 fecharem — sem alterar a Fase 2, que já estava certa.

**Achados adicionais encontrados durante esta verificação, fora do escopo dos 6 erros reportados — não corrigidos, a decidir depois:** (a) a linha do item F12/I11 ("ex. os 108 itens dos grupos A-H") está ela própria incorrecta — A-H somam 91, não 108 — mas não fazia parte dos 6 erros pedidos; (b) o item **G5** do `STATUS.md` ("2 achados não resolvidos do MCP-MAPPING.md") não tem nenhum item correspondente nos Grupos A-J deste documento — pode ser uma lacuna real de cobertura, a confirmar antes de assumir que "nenhum item do STATUS.md ficou de fora" (frase final da Contagem final).

**Adenda em 2026-09-19 (depois desta verificação, itens novos, não erros):** **A22** foi acrescentado (vulnerabilidades Dependabot reportadas no push do commit `2d03b4b`) — Grupo A passa de 21 para 22 itens. **D8** foi acrescentado (achado durante a execução real do A3: `prisma generate` em falta pós-install) — Grupo D passa de 7 para 8 itens. **E8**/**E9** foram acrescentados (achados durante a execução real do A2: `knowledge_sources` sem script de criação versionado; tabela `knowledge_log` não documentada) — Grupo E passa de 7 para 9 itens. **D9** foi acrescentado (achado durante a execução real do A7: suite do runner demora 12min, concentrados em 2 ficheiros lentos, fácil de confundir com bloqueio) — Grupo D passa de 8 para 9 itens. **D10** foi acrescentado (achado durante a execução real do A18: 5 itens desta sessão — C6, A1, A21, A14, A18 — revelaram-se diferentes do plano ao verificar; proposta de auditoria de escopo preventiva) — Grupo D passa de 9 para 10 itens. **A23** foi acrescentado (achado durante a execução real do A20: `cors()` totalmente aberto, contradição real com o CORP do helmet) — Grupo A passa de 22 para 23 itens. Total do documento passa de 108 para **115**. Consistente com a metodologia acima: cada mudança de contagem fica registada aqui, nunca só silenciosamente no número final.

**AVISO (acrescentado em 2026-09-19, depois do A18):** este documento foi escrito a partir do `STATUS.md`, que por sua vez cita documentos de mapeamento mantidos em sessões anteriores. **ANTES de executar qualquer item, revalidar contra o código real** — a Fase 1 de cada item já manda fazer isto, mas vale o aviso explícito: vários itens (**C6, A1, A21, A14, A18**) revelaram-se diferentes do descrito ao verificar, nalguns casos por o achado já ter sido resolvido antes do documento ser escrito, noutros por o escopo real ser muito maior ou menor do que o brief presumia. Ver **B14/D10** para a proposta de auditoria preventiva de todos os itens restantes.

---

Par deste ficheiro: `docs/initiatives/STATUS.md` (estado) + todas as auditorias em `docs/architecture/*-audit/` (achados). Cada item abaixo é um prompt autocontido — pode ser dado a uma sessão Claude Code futura sem contexto prévio desta conversa.

**Regra comum a todos os prompts**, para não repetir 108 vezes: antes de qualquer execução, ler `CLAUDE.md` (bootstrap + regras de trabalho), `docs/initiatives/STATUS.md` (estado atual — pode ter mudado desde que este documento foi escrito) e o(s) documento(s) de auditoria citado(s) no item. **Fase 1 de todo item é reconfirmar o achado por leitura directa — nunca executar em cima de uma alegação não reverificada.** É a lição central desta série de auditorias (o erro de `Orchestrator.ts`/`CORE-MAPPING.md`): documentação interna também pode estar errada, só código real prova.

**Convenção de fecho, igual em todos:** ao terminar, mover o item de pendente para `## Done` em `STATUS.md` com o que foi feito + commit; se o achado tinha um documento de auditoria próprio, marcar "RESOLVIDO em [data], ver commit [hash]" sem apagar o texto original do achado (disciplina de errata já usada nesta sessão).

Este documento é escrito em fases (grupos), cada uma numa sessão de escrita própria, para não perder qualidade tentando segurar 108 itens de uma vez.

---

## GRUPO A — Segurança (23 itens)

> **Nota de contagem (2026-09-19, achado durante o B14/D10):** o cabeçalho dizia "21 itens", desactualizado desde o A22/A23 — corrigido para 23, já batia com o fecho do grupo e a Contagem final.
>
> **Revalidação de escopo (B14/D10, 2026-09-19):** os itens ainda pendentes deste grupo (A4, A9-A13, A16-A17) foram confirmados **REAL** (escopo correcto) por leitura directa do código. A15 e A19 foram reclassificados **DIFERENTE**/**N/A** — ver notas nos próprios itens e `docs/architecture/meta-validation/AUDIT-SCOPE-2026-09-19.md`.

### A1 — Rotacionar senha hardcoded + placeholder consistente

**Quem:** Claude + Desenvolvedor
**Origem:** `security-audit-2026/AUDIT-SECURITY-2026.md` secção 7

**Fase 1 — Análise e Verificação**
Reabrir `k8s/secrets.yaml` por completo. Confirmar que a linha `database-url: postgresql://network:network123@postgres:5432/network_agents` continua com valor literal (não placeholder). Confirmar a forma da linha irmã (`openai-api-key: ${OPENAI_API_KEY}`) para replicar exactamente essa convenção.

**Fase 2 — Execução**
Claude troca o valor literal por `${DATABASE_URL}`. Desenvolvedor rotaciona a senha real no serviço Postgres correspondente (fora deste repo, na infra onde o serviço corre) e actualiza a env var real.

**Fase 3 — Teste e Validação**
`grep -rn "network123"` no repo inteiro devolve zero resultados. Confirmar (Desenvolvedor) que a conexão com a nova senha funciona antes de descartar a antiga. Rodar `detect-secrets`/Gitleaks uma vez mais sobre este ficheiro especificamente e confirmar 0 achados.

**Fase 4 — Atualização de Status**
Mover para Done em STATUS.md grupo A. Nota em `AUDIT-SECURITY-2026.md` secção 7: "RESOLVIDO em [data] — valor trocado por placeholder, senha real rotacionada pelo Desenvolvedor em [data]".

> **Status em 2026-09-19:** Fase 2 (Claude) executada — 5 ficheiros corrigidos (`.env.example`, `docker-compose.yml` ×2, `k8s/postgres.yaml`, `k8s/secrets.yaml`), zero `network123` restante. Fase 3 (Desenvolvedor) concluída — senha real rotacionada **fora do repo, directamente no Supabase**, durante esta sessão. **Resolvido do lado do repo.** Commit feito. Nova dependência registada separadamente para quando `k8s/` for aplicado a um cluster real — ver **A1b** abaixo.

---

### A1b — Passo de deploy real do `k8s/` (Secret + resolução de `${...}`)

**Quem:** Desenvolvedor
**Origem:** A1 (dependência nova, identificada em 2026-09-19) — a resolver **antes** de `k8s/postgres.yaml`/`k8s/secrets.yaml` serem aplicados a um cluster real; não bloqueia o fecho de A1 do lado do repo.

**Fase 1 — Análise e Verificação**
Confirmar qual é o pipeline de aplicação real destes manifestos (`kubectl apply` directo? `envsubst`? Helm? Kustomize?) — hoje não está decidido nem documentado.

**Fase 2 — Execução**
Criar o Secret real (fora do git, nunca commitado) com `POSTGRES_PASSWORD` e `DATABASE_URL` preenchidos com valores verdadeiros. Confirmar se o pipeline escolhido faz substituição de `${...}`. Se **não** fizer, os Pods não arrancam — resolver de uma das duas formas: (a) rodar `envsubst` sobre os manifestos antes do `kubectl apply`, ou (b) trocar `${...}` em `k8s/secrets.yaml` por `valueFrom: secretKeyRef` apontando para um Secret já aplicado por fora (mesma técnica já usada em `k8s/postgres.yaml` para `POSTGRES_PASSWORD`).

**Fase 3 — Teste e Validação**
Aplicar a um cluster de teste (não produção) e confirmar que os Pods arrancam — se não arrancarem por variável não resolvida, é sinal de que a Fase 2 não foi suficiente.

**Fase 4 — Atualização de Status**
Mover para Done em STATUS.md, junto de A1, só depois de confirmado num cluster real.

---

### A2 — RLS em `knowledge_chunks_t6`/`knowledge_sources`

**Quem:** Claude + Desenvolvedor
**Origem:** `security-audit-2026/AUDIT-SECURITY-2026.md` secção 6

**Fase 1 — Análise e Verificação**
Reabrir `scripts/create_t6_chunks_table.sql` por completo. Confirmar ausência de qualquer `ENABLE ROW LEVEL SECURITY`/`CREATE POLICY` nas duas tabelas. Confirmar, por leitura de `runner/plan_runner/knowledge.py`/`supabase_writer.py`, exactamente que colunas (`agent_id`, `kb`) já existem para servir de chave de isolamento — não inventar coluna nova se já existir uma que sirva.

**Fase 2 — Execução**
Claude escreve a migration SQL: `ALTER TABLE knowledge_chunks_t6 ENABLE ROW LEVEL SECURITY;` + `CREATE POLICY` restringindo `SELECT`/`INSERT`/`UPDATE`/`DELETE` por `agent_id` (decidir com o Desenvolvedor se `kb` também entra na policy ou se `agent_id` sozinho basta). Desenvolvedor aplica a migration ao Postgres real (Supabase) e confirma que a aplicação continua a autenticar com um `role`/`claim` que a policy consegue ler (ex. `current_setting('app.agent_id')` ou equivalente — decidir o mecanismo real de propagação de identidade antes de escrever a policy, senão ela fica sem sujeito a comparar).

**Fase 3 — Teste e Validação**
Escrever teste de integração: autenticado como agente A, tentar `SELECT` um chunk de `kb` pertencente ao agente B, confirmar 0 linhas devolvidas (RLS bem-feita nega silenciosamente, não lança erro). Rodar a suite existente de `knowledge.py`/`mcp_knowledge.py` (18+13 testes já documentados) e confirmar que os agentes autorizados continuam a ver os seus próprios dados sem regressão.

**Fase 4 — Atualização de Status**
Mover para Done, grupo A. Nota em `AUDIT-SECURITY-2026.md` secção 6.

> **Status em 2026-09-19: DONE.** Investigação real (Fase 1) revelou que o desenho original da migration estava errado em 3 pontos: (1) `agent-network-mcp` nunca toca `knowledge_chunks_t6` — usa `knowledge_chunks` num Supabase/projecto diferente, confirmado por `supabase_writer.py` e por zero ocorrências de `_t6` naquele repo; (2) o writer (`supabase_writer.py`) autentica como role `postgres` (`SELECT current_user, rolbypassrls` → `('postgres', True)`) — **BYPASSRLS**, logo nenhuma policy o afecta, tornando desnecessária qualquer policy `TO service_role`; (3) `knowledge_sources` existe e também precisava da mesma correcção (nunca tinha script de criação versionado — ver **E8**). Migration final, replicando o padrão já em uso em `knowledge_chunks`/`knowledge_log` (achada durante a investigação — ver **E9**): `scripts/migrations/enable_rls_knowledge_tables.sql` — `ENABLE ROW LEVEL SECURITY` + policy `*_anon_deny TO anon USING (false)` em `knowledge_chunks_t6` e `knowledge_sources`, sem isolamento por agente (modelo de identidade inexistente). Aplicado no Supabase pelo Desenvolvedor em 2026-09-19; verificado por query directa — as 4 tabelas `knowledge_*` têm agora `rowsecurity = true`. Nota em `AUDIT-SECURITY-2026.md` secção 6.

---

### A3 — Corrigir path traversal em `filesystem.ts`

**Quem:** Claude
**Origem:** `tools-mcp-audit/AUDIT-TOOLS-MCP.md` secção 3

*(prompt já desenhado por completo na mensagem anterior — reproduzido aqui para o documento ficar autocontido)*

**Fase 1 — Análise e Verificação**
Reabrir `packages/mcp/src/tools/built-in/filesystem.ts` na íntegra. Confirmar que `if (!resolved.startsWith(basePath))` continua exactamente assim. Reabrir `mcp/plan_runner/mcp_plan_runner/policy.py:sanitize_repo_path()` para confirmar o padrão de referência (`cand.relative_to(root)`) antes de o replicar.

**Fase 2 — Execução**
Substituir a guarda por:
```ts
const rel = path.relative(base, resolved);
if (rel === '..' || rel.startsWith('..' + path.sep) || path.isAbsolute(rel))
  throw new Error(`Path traversal blocked: "${filePath}" resolves outside "${base}"`);
```
Aplicar às três tools do ficheiro (`read_file`, `write_file`, `list_directory`). Não tocar em mais nada.

**Fase 3 — Teste e Validação**
1. Escrever o teste ANTES da correcção, confirmar que falha (prova o bypass real): `expect(() => resolveSafePath('/repo/app', '../app-secret/x')).toThrow()`.
2. Aplicar a correcção, confirmar que o teste passa.
3. Teste de não-regressão: `resolveSafePath('/repo/app', 'docs/readme.md')` devolve o path esperado.
4. Rodar toda a suite de `packages/mcp`, confirmar contagem de testes igual ou maior, zero falhas.

**Fase 4 — Atualização de Status**
Mover para Done, grupo A: "path traversal em filesystem.ts corrigido, 3 testes novos, 0 regressões" + commit. Nota em `AUDIT-TOOLS-MCP.md` secção 3.

> **Status em 2026-09-19: DONE.** Guarda corrigida nas 3 tools de `filesystem.ts`. Teste `tests/unit/filesystem.test.ts` (2 testes, não 3 — via `createFilesystemTools`/interface pública, `resolveSafePath` não existe como função exportada, ver nota abaixo) escrito antes da correção (falhou, provando o bug), passou depois. Suite completa: 91 testes, 0 falhas. Nota em `AUDIT-TOOLS-MCP.md` secção 3. Achados à parte durante a Fase 3 (não bloquearam o fecho, ambos pré-existentes, não causados por esta correção): 2 ficheiros de teste falharam a **carregar** (não a testes falhados) por causas distintas — `tests/integration/ExecutionFlow.test.ts` por `prisma generate` em falta pós-`pnpm install` (registado como **D8**); `tests/e2e/api.test.ts` por `supertest` não resolver (não registado como item novo, fora do escopo pedido para esta sessão).

---

### A4 — Restringir `query_database`

**Quem:** Claude + Desenvolvedor
**Origem:** `tools-mcp-audit/AUDIT-TOOLS-MCP.md` secção 1

**Fase 1 — Análise e Verificação**
Reabrir `packages/mcp/src/tools/built-in/database.ts` por completo. Confirmar que `pool.query(query, params)` continua a aceitar qualquer string SQL sem allowlist. Confirmar qual `role`/connection string o `Pool` usa hoje (provavelmente o mesmo role de escrita da aplicação inteira).

**Fase 2 — Execução**
Claude escreve `assertSafeSelect(query: string): string` — rejeita `;` adicional (permite só um `;` final opcional), exige que o primeiro token seja `SELECT`/`WITH`, rejeita keywords de escrita (`INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|COPY|CALL|DO`) via regex. Adiciona `SET statement_timeout = 5000` antes da query e `client.release(true)` depois (descartar a conexão, não devolver ao pool). Desenvolvedor cria o role Postgres `mcp_readonly` (`GRANT CONNECT`, `GRANT USAGE ON SCHEMA public`, `GRANT SELECT ON ALL TABLES IN SCHEMA public`, `ALTER DEFAULT PRIVILEGES ... GRANT SELECT`) e configura a tool para usar esse role em vez do actual.

**Fase 3 — Teste e Validação**
Teste unitário: `query_database({query: "DROP TABLE users; --"})` devolve erro `"forbidden keyword"` antes de chegar à base. Teste unitário: `query_database({query: "SELECT 1; COMMIT; DROP SCHEMA public CASCADE;"})` é rejeitado por conter `;` adicional (o mesmo bypass que descontinuou o servidor Postgres oficial da Anthropic). Teste de integração (Desenvolvedor, com o role real): confirmar que um `INSERT` enviado directamente pelo role `mcp_readonly` falha ao nível do próprio Postgres — prova que a allowlist não é a única linha de defesa.

**Fase 4 — Atualização de Status**
Mover para Done, grupo A. Nota em `AUDIT-TOOLS-MCP.md` secção 1, citando explicitamente o precedente do servidor Anthropic descontinuado como motivação.

---

### A5 — SSRF guard em `http_request`

**Quem:** Claude
**Origem:** `tools-mcp-audit/AUDIT-TOOLS-MCP.md` secção 2

**Fase 1 — Análise e Verificação**
Reabrir `packages/mcp/src/tools/built-in/web.ts`. Confirmar que `fetch(url, ...)` continua sem nenhuma validação de IP/esquema.

**Fase 2 — Execução**
Adicionar `ssrf-req-filter` (ou `request-filtering-agent`) como dependência; usar como `http.Agent`/`https.Agent` na chamada `fetch`. Validar esquema (`http:`/`https:` apenas) antes de qualquer coisa. Definir `redirect: 'manual'` e, se a resposta for um redirect (301/302/303/307/308), lançar erro em vez de seguir automaticamente.

**Fase 3 — Teste e Validação**
Teste: `http_request({url: 'http://169.254.169.254/'})` é bloqueado antes do fetch sair. Teste: `http_request({url: 'http://localhost:PORT_INTERNO'})` é bloqueado. Teste: `http_request({url: 'https://example.com'})` (caso legítimo) continua a funcionar — confirma que a mitigação não quebrou o caso de uso real.

**Fase 4 — Atualização de Status**
Mover para Done, grupo A. Nota em `AUDIT-TOOLS-MCP.md` secção 2.

> **Status em 2026-09-19: DONE — com desvio importante do plano original, confirmado antes de codificar.** `ssrf-req-filter` **não funciona** com o `fetch` global do Node — devolve um `http.Agent` clássico, mas o `fetch` global (undici) não aceita `agent`, só `dispatcher`; confirmado empiricamente (`agent.createConnection` nunca chamado). Solução real: `packages/mcp/src/tools/built-in/SsrfGuard.ts` (novo) — `createSsrfSafeDispatcher()`, um `undici.Agent` com `connect` customizado via `buildConnector`, que resolve o hostname uma vez, valida o IP (`ipaddr.js`, fail-closed em IP não-parseável — mais estrito que o `ssrf-req-filter`, que trata isso como seguro) e liga directamente ao IP validado (fecha a janela de DNS-rebinding). `http_request` passa a usar `fetch` do `undici` explicitamente (não o global), com validação de esquema, `redirect: 'manual'` + throw em 3xx, timeout 5s via `AbortController`. Achado técnico à parte: o `undici` embrulha erros de ligação em `TypeError('fetch failed', {cause})` — a mensagem real fica em `error.cause`, não em `error.message`. `tests/unit/SsrfGuard.test.ts` (10 testes, classificação de IP incluindo `::ffff:127.0.0.1` e fronteira RFC1918) + `tests/unit/web.test.ts` (+8 testes de integração: esquemas, IPs internos reais, redirect, timeout, caso legítimo). Suite completa: 124/124 (subiu de 106).

---

### A6 — `scrape_webpage`: regex → parser DOM

**Quem:** Claude
**Origem:** `tools-mcp-audit/AUDIT-TOOLS-MCP.md` secção 2

**Fase 1 — Análise e Verificação**
Confirmar em `web.ts` que `scrape_webpage` continua a construir `new RegExp(...)` a partir do parâmetro `selector`.

**Fase 2 — Execução**
Adicionar `cheerio` como dependência. Trocar a extracção de título/matches por `cheerio.load(html)` + `$(selector).text()`/`$('title').text()`.

**Fase 3 — Teste e Validação**
Teste com `selector` contendo meta-caracteres de regex (ex. `"(a|a)*"`) confirmando que já não quebra nem gera comportamento anómalo (tratado como selector CSS comum, falha limpa se inválido). Teste positivo com selector válido (ex. `"p"`) confirmando extracção correcta de um HTML de teste conhecido.

**Fase 4 — Atualização de Status**
Mover para Done, grupo A.

> **Status em 2026-09-19: DONE.** `cheerio` adicionado como dependência de `packages/mcp`. Extracção de título/matches trocada para `cheerio.load(html)` + `$(selector).text()`/`$('title').text()` — `selector` nunca mais interpolado em `RegExp`. Teste novo `tests/unit/web.test.ts` (3 testes: selector com meta-caracteres não quebra; selector válido extrai conteúdo real; sem selector devolve só título) — 3/3 passou. Suite completa: 94/94 testes que correm passam (subiu de 91 para 94), 0 regressões. Nota em `AUDIT-TOOLS-MCP.md` secção 2 (SSRF de `http_request` continua pendente, ver A4/A5).

---

### A7 — `embedder.py`: Gemini key por header

**Quem:** Claude
**Origem:** `ingestion-audit/AUDIT-INGESTION.md` secção 6

**Fase 1 — Análise e Verificação**
Confirmar em `runner/plan_runner/embedder.py` que `httpx.post(GEMINI_URL, params={"key": key}, ...)` continua assim.

**Fase 2 — Execução**
Trocar por `httpx.post(GEMINI_URL, headers={"x-goog-api-key": key}, ...)`, removendo `key` de `params`.

**Fase 3 — Teste e Validação**
Teste de integração real (1 chamada) contra a API do Gemini confirmando resposta idêntica (768 dims). Grep confirma que `key` já não aparece em nenhuma URL montada no código.

**Fase 4 — Atualização de Status**
Mover para Done, grupo A.

> **Status em 2026-09-19: DONE.** Guarda trocada para `headers={"x-goog-api-key": key}`. `test_embedder.py` actualizado (2 dos 8 testes tinham `fake_post` com assinatura estrita sem `headers=` — corrigidos para reflectir o novo comportamento, não o antigo). Confirmado por chamada real contra a API Gemini: 768 dimensões, sem erro. Suite completa do runner (`pytest`, 172 testes): **172/172 passou, 0 regressões** — achado à parte durante esta verificação: `test_crash_recovery.py`/`test_real_plans.py` demoram a maior parte dos 12 minutos da suite (não estão bloqueados, só são lentos ao ponto de parecer presos com um timeout curto) — ver **D9**.

---

### A8 — Autenticação em `MCPServer.ts`

**Quem:** Claude + Desenvolvedor
**Origem:** `tools-mcp-audit/AUDIT-TOOLS-MCP.md` secção 4 / `GOV-FASE1.md`

**Fase 1 — Análise e Verificação**
Reabrir `packages/mcp/src/server/MCPServer.ts:createHttpHandler()`. Confirmar ausência total de verificação de header antes de `executeTool`. Reabrir `apps/api/src/middleware/auth.ts:assertAuthConfig()` para replicar o mesmo padrão fail-closed já usado ali.

**Fase 2 — Execução**
Claude adiciona middleware que exige `Authorization: Bearer <MCP_SERVER_KEY>`, fail-closed se a env var não estiver definida em produção (mesmo padrão de `assertAuthConfig`). Desenvolvedor define e distribui a key real.

**Fase 3 — Teste e Validação**
Teste: chamada sem header recebe 401. Teste: header inválido recebe 401. Teste: header correcto executa normalmente (não-regressão).

**Fase 4 — Atualização de Status**
Mover para Done, grupo A.

---

### A9 — Lockfile Python

**Quem:** Claude + Desenvolvedor
**Origem:** `security-audit-2026/AUDIT-SECURITY-2026.md` secção 2

**Fase 1 — Análise e Verificação**
Confirmar ausência de `poetry.lock`/`uv.lock`/`Pipfile.lock` no repo (`find . -iname "*.lock"`). Reler `requirements.txt`/`requirements-langgraph.txt` para confirmar quais pins já existem (ex. `mcp==1.30.0` fixo, `langgraph>=0.6.11` sem tecto).

**Fase 2 — Execução**
Tentar `uv lock` (ou `pip-compile --generate-hashes` a partir dos requirements existentes). Se a rede/registry da sandbox não permitir resolver, documentar exactamente o comando e passá-lo ao Desenvolvedor para rodar num ambiente com rede real.

**Fase 3 — Teste e Validação**
Ficheiro de lock commitado. CI passa a instalar com `--frozen`/verificação de hash em vez de resolver livre. Confirmar que `mcp==1.30.0` se mantém no lock (é um pin deliberado, documentado no próprio código por uma razão específica — não deixar o resolver subir a versão).

**Fase 4 — Atualização de Status**
Mover para Done, grupo A. Nota em `AUDIT-SECURITY-2026.md` secção 2: "LLM04 deixa de ser estruturalmente inverificável — lockfile gerado em [data]".

---

### A10 — Rodar `security_auditor` completo (8 ferramentas)

**Quem:** Claude + Desenvolvedor
**Origem:** STATUS.md item B2b

**Fase 1 — Análise e Verificação**
Reler `SECURITY-AUDIT-FULL.md` para confirmar exactamente quais das 8 ferramentas já correram com resultado real vs. quais ficaram "bloqueada"/"inconclusiva" por rede (OSV-Scanner, Trivy `vuln`).

**Fase 2 — Execução**
Rodar as ferramentas pendentes num ambiente com `api.osv.dev`/`api.deps.dev`/`mirror.gcr.io` liberados (Desenvolvedor). Claude compila o relatório actualizado.

**Fase 3 — Teste e Validação**
Relatório final mostra resultado real (não "bloqueado") para as 8 ferramentas.

**Fase 4 — Atualização de Status**
Mover B2b para Done. Actualizar `SECURITY-AUDIT-FULL.md` com a corrida completa.

---

### A11 — Triar achados em backlog real

**Quem:** Claude + Desenvolvedor
**Origem:** STATUS.md item B2c

**Fase 1 — Análise e Verificação**
Listar todos os achados de segurança desta sessão inteira (A1-A20 aqui, mais os de `SECURITY-AUDIT*.md`) num único inventário.

**Fase 2 — Execução**
Claude organiza por severidade (Crítico/Alto/Médio) num formato rastreável (issues do GitHub, ou uma tabela com ID/estado/dono). Desenvolvedor confirma prioridade final, aceita ou marca "risco aceite" cada um.

**Fase 3 — Teste e Validação**
Cada achado tem estado explícito (aberto/aceite-risco/fechado) — nenhum fica "só documentado" sem decisão.

**Fase 4 — Atualização de Status**
Mover B2c para Done.

---

### A12 — Criptografia em repouso

**Quem:** Desenvolvedor
**Origem:** STATUS.md, checklist de segurança item 5

**Fase 1 — Análise e Verificação**
Confirmar se este repo (camada pública/portfólio, per `CLAUDE.md`) realmente armazena algum dado sensível de facto, ou se a resposta correcta é "não há dado sensível real nesta camada".

**Fase 2 — Execução**
Se houver dado sensível real: decidir KMS/pgcrypto e implementar. Se não houver: documentar a decisão explicitamente.

**Fase 3 — Teste e Validação**
Decisão escrita com justificação — não implementação às cegas nem silêncio.

**Fase 4 — Atualização de Status**
Mover para Done com a decisão registada (mesmo que a decisão seja "não aplicável").

---

### A13 — Modelo RBAC

**Quem:** Claude + Desenvolvedor
**Origem:** STATUS.md, checklist item 7

**Fase 1 — Análise e Verificação**
Reabrir `packages/core/src/security/SecurityManager.ts` para confirmar o que já existe (hierarquia `admin > user > viewer > agent`, já citada em `GOV-FASE1.md`).

**Fase 2 — Execução**
Claude propõe verificação real de papel em cada endpoint de `apps/api` que hoje não a tem. Desenvolvedor aprova o modelo (papéis fixos vs. ABAC) antes da implementação.

**Fase 3 — Teste e Validação**
Teste: utilizador `viewer` recebe 403 ao tentar acção de `admin`.

**Fase 4 — Atualização de Status**
Mover para Done.

---

### A14 — Mass Assignment

**Quem:** Claude
**Origem:** STATUS.md, checklist item 8

**Fase 1 — Análise e Verificação**
Listar todos os schemas Zod de entrada em `apps/api`/`packages/mcp` que não usam `.strict()`.

**Fase 2 — Execução**
Adicionar `.strict()` (ou `.omit()` explícito para campos calculados) a cada um.

**Fase 3 — Teste e Validação**
Teste: payload com campo extra não declarado (ex. `{name: "x", isAdmin: true}`) é rejeitado, não silenciosamente ignorado nem aceite.

**Fase 4 — Atualização de Status**
Mover para Done.

> **VERIFICADO em 2026-09-19: N/A neste repo.** Zod não existe em nenhum `package.json` deste repo (`network-agents-setup`) — grep exaustivo por `z.object(`/`from 'zod'`/`"zod"` em `apps/api/src`, `packages/mcp/src` e todos os `package.json`, zero resultados. O Zod real está no `agent-network-mcp` (`app/api/mcp/route.js`), não como `z.object(...).strict()` directo — os schemas são um `shape` passado a `server.tool()` do `mcp-handler`, embrulhado internamente em `z.object(shape)` (modo `"strip"` por omissão). Fica registado como **S12** (STATUS.md), para uma sessão dedicada a esse repo separado.

---

### A15 — Flags de cookie

> **Revalidado em 2026-09-19 (B14/D10): DIFERENTE.** Não existe nenhuma configuração de sessão/cookie neste repo — grep exaustivo em `apps/api/src` por `httpOnly`/`secure`/`sameSite`/cookie, zero resultados. A autenticação é 100% via header `x-api-key` (`middleware/auth.ts`), sem cookie nenhum. Não há nada para "ajustar" tal como o item descreve — precisa de decisão humana (desenhar sessão por cookie de raiz, ou fechar como N/A). Ver `AUDIT-SCOPE-2026-09-19.md`.

**Quem:** Claude + Desenvolvedor
**Origem:** STATUS.md, checklist item 9

**Fase 1 — Análise e Verificação**
Reabrir a configuração de sessão/cookie actual (localizar o ficheiro exacto antes de assumir).

**Fase 2 — Execução**
Confirmar/ajustar `httpOnly: true, secure: true, sameSite: 'strict'` (ou `'lax'` com razão documentada).

**Fase 3 — Teste e Validação**
Inspeccionar `Set-Cookie` numa resposta real (Desenvolvedor, ambiente com HTTPS real para `secure` fazer sentido) e confirmar as 3 flags.

**Fase 4 — Atualização de Status**
Mover para Done.

---

### A16 — Rate limit no Node

**Quem:** Claude
**Origem:** STATUS.md, checklist item 11

**Fase 1 — Análise e Verificação**
Confirmar ausência de rate limit em `apps/api` (o rate limit confirmado existe só do lado `mcp/plan_runner` Python).

**Fase 2 — Execução**
Adicionar `express-rate-limit` (ou equivalente), espelhando 60 chamadas/60s por caller já usado no lado Python.

**Fase 3 — Teste e Validação**
Teste: 61ª chamada num minuto recebe 429.

**Fase 4 — Atualização de Status**
Mover para Done.

> **Status em 2026-09-20: DONE.** Fase 1 confirmada (5 ficheiros lidos por completo: `apps/api/src/server.ts` 41 linhas, `apps/api/src/index.ts` 133 linhas, `apps/api/src/middleware/auth.ts` 95 linhas, `packages/mcp/src/tools/ToolPolicy.ts` 161 linhas, `mcp/plan_runner/mcp_plan_runner/policy.py` 149 linhas — zero rate limit em `apps/api`). **Discrepância registada:** o "por caller" do Python (`policy.py:129`, `rate_limit(caller, limit=60, window=60.0)`) não é equivalente a "por IP" — `auth.ts:55-82` usa um `API_KEY` único partilhado por todos os clientes, sem conceito de identidade por chamador; IP é o único eixo disponível nesta API. Documentado no código (`server.ts`) e no `STATUS.md` item 11. Instalado `express-rate-limit@8.7.0` via `apps/api` (pnpm 8.0.0 tem um bug de fetch incompatível com Node 24 — `ERR_INVALID_THIS`; contornado com `corepack pnpm@8.15.9`, mantendo `lockfileVersion: '6.0'`). Rate limiter criado dentro de `createServer()` (não a nível de módulo, para não partilhar estado entre instâncias), 60/60s, excluído de `/health`. 3 testes novos em `server-rate-limit.test.ts`: 60 pedidos passam; 61º devolve 429; `/health` não é afectado mesmo com o limite esgotado noutra rota. Suite completa sem regressão.

---

### A17 — Bot protection

**Quem:** Claude + Desenvolvedor
**Origem:** STATUS.md, checklist item 12

**Fase 1 — Análise e Verificação**
Identificar quais endpoints públicos (se algum) justificam protecção de bot.

**Fase 2 — Execução**
Claude integra Cloudflare Turnstile/hCaptcha nos endpoints identificados; Desenvolvedor cria a conta/chaves.

**Fase 3 — Teste e Validação**
Fluxo manual sem token de captcha é rejeitado.

**Fase 4 — Atualização de Status**
Mover para Done.

> **Status em 2026-09-20: N/A neste repo (verificado, não "por fazer").** Fase 1: 6 ficheiros de rotas lidos por inteiro (99 linhas no total — `agents.ts` 11, `chat.ts` 14, `executions.ts` 11, `health.ts` 20, `hitl.ts` 14, `metrics.ts` 29), 19 endpoints inventariados (lista completa em `server-no-public-endpoints.test.ts`). Cruzado com `server.ts:41` (`app.use(authMiddleware)`, montado globalmente, sem excepção de path) e `auth.ts:55-82` (fail-closed: sem `X-API-Key` válida, devolve 503/401 antes de a rota ser sequer resolvida). **Nenhum endpoint desta API é público** — todos exigem uma chave partilhada única; bot protection (Turnstile/hCaptcha) existe para distinguir humano de bot em tráfego não-autenticado, o que não existe aqui (é M2M, gated por chave, não por captcha). Teste novo (`server-no-public-endpoints.test.ts`): as 19 rotas devolvem 503 sem `API_KEY`, confirmando a premissa empiricamente, não só por leitura. Classificação análoga ao A14 (item de checklist cujo cabeçalho já diz "aplica-se sobretudo ao `agent-network-mcp`, produção") — se esse repo tiver formulários públicos reais, é lá que este item se aplicaria. **Auto-crítica:** não verifiquei o `agent-network-mcp` (repo separado) para confirmar se ele tem endpoints públicos que precisem disto — a classificação N/A é só para *este* repo. Também não testei o comportamento com `ALLOW_UNAUTHENTICATED=true` (dev local) — nesse modo os endpoints ficam de facto abertos, mas é uma opção explícita de desenvolvimento, documentada como tal em `auth.ts`, não o comportamento por omissão.

---

### A18 — Auditar mensagens de erro

**Quem:** Claude
**Origem:** STATUS.md, checklist item 15

**Fase 1 — Análise e Verificação**
Grep sistemático por `error.message` devolvido directo ao chamador em `packages/mcp/**`, `apps/api/**` (já confirmado presente em `ToolExecutor.ts`, `web.ts`, `database.ts`, `filesystem.ts` nesta sessão).

**Fase 2 — Execução**
Trocar por mensagem genérica ao cliente + log interno detalhado (não perder a informação, só não expô-la).

**Fase 3 — Teste e Validação**
Teste: provocar erro real (query malformada) e confirmar que a resposta ao cliente não contém stack trace nem caminho de ficheiro do servidor.

**Fase 4 — Atualização de Status**
Mover para Done.

> **Status em 2026-09-19: DONE — escopo real 7× maior que o brief.** Fase 1 encontrou 29 sítios em 11 ficheiros (não 4): `packages/mcp/src/{client/MCPClient.ts, tools/ToolExecutor.ts, tools/built-in/{database,filesystem,web}.ts, tools/legal/{portuguese-law,brazilian-law}.ts}` (13 sítios) + `apps/api/src/{middleware/errorHandler.ts, controllers/{ChatController,HitlController}.ts, websocket.ts}` (16 sítios). Achado importante: `ChatController`/`HitlController`/`websocket.ts` fazem catch próprio e respondem directamente — nunca chegam ao `errorHandler.ts` central, que só apanha erros não tratados. Correcção: 2 helpers `toClientError(error, context)` (mesma assinatura, `packages/mcp/src/util/sanitizeError.ts` via `console.error`, `apps/api/src/utils/sanitizeError.ts` via logger de `@network-agents/observability`) aplicados nos 29 sítios. Excluídos deliberadamente 2 logs internos genuínos (`MCPClient.ts:19` `console.error`, `index.ts` `logger.error` ×3) — não são client-facing. Cuidado tomado em `web.ts`: as mensagens seguras já desenhadas no A5 (SSRF bloqueado, esquema não permitido, redirect bloqueado, timeout) **não foram generalizadas** — só o fallback genuinamente desconhecido passa por `toClientError`. Gap de infra encontrado e corrigido en passant: `vitest.config.ts` nunca tinha alias para `@network-agents/websocket` (impedia testar `apps/api/src/websocket.ts` de todo). 21 testes novos (`sanitizeError.test.ts`, `mcp-tools-errors.test.ts`, `api-errors.test.ts` + 1 adicionado a `filesystem.test.ts` e a `web.test.ts` cada). Suite completa: 145/145 (subiu de 124). Nota em `AUDIT-SECURITY-2026.md` (tabela OWASP, LLM02).

---

### A19 — Restringir uploads

> **Revalidado em 2026-09-19 (B14/D10): N/A neste repo.** `extrair-imagem` não existe em `network-agents-setup` — existe como workflow do GitHub Actions em `agent-network-mcp/.github/workflows/extrair-imagem.yml`, um repo diferente. STATUS.md já dava a pista ("**Produção** tem `extrair-imagem`" — "Produção" = `agent-network-mcp`). Este item não tem alvo neste repo tal como escrito. Ver `AUDIT-SCOPE-2026-09-19.md`.

**Quem:** Claude
**Origem:** STATUS.md, checklist item 16

**Fase 1 — Análise e Verificação**
Localizar `extrair-imagem` e confirmar que valida só extensão, não conteúdo/tamanho.

**Fase 2 — Execução**
Adicionar validação de MIME real (magic bytes, não extensão) + tamanho máximo.

**Fase 3 — Teste e Validação**
Teste: ficheiro `.exe` renomeado para `.jpg` é rejeitado por conteúdo real. Teste: ficheiro acima do tamanho máximo é rejeitado.

**Fase 4 — Atualização de Status**
Mover para Done.

---

### A20 — Security headers

**Quem:** Claude
**Origem:** STATUS.md, checklist item 18

**Fase 1 — Análise e Verificação**
Confirmar que `helmet` (já dependência, visto em `pnpm-lock.yaml`) não está configurado ou está com defaults insuficientes em `apps/api`.

**Fase 2 — Execução**
Configurar CSP/X-Frame-Options/etc. explicitamente.

**Fase 3 — Teste e Validação**
`curl -I` numa resposta real confirma os headers presentes.

**Fase 4 — Atualização de Status**
Mover para Done.

> **Status em 2026-09-19: DONE — verificado, já estava activo, 1 ajuste real aplicado (mesmo padrão do A21).** `helmet()` já estava configurado em `apps/api/src/server.ts:24`, confirmado por leitura e empiricamente (12 headers reais, incluindo CSP/X-Frame-Options/HSTS) — o checklist item 18 ("❌") estava desactualizado. Ajuste real encontrado e aplicado: `crossOriginResourcePolicy` do helmet (omissão `'same-origin'`) contradizia o `cors()` totalmente aberto na linha seguinte — corrigido para `'cross-origin'`, alinhado com a intenção já expressa pelo CORS aberto. CSP/HSTS/X-Frame-Options não foram tocados (já bons). Teste novo `tests/unit/server-security-headers.test.ts` (servidor real local, sem `supertest`) confirma o header correcto + os restantes intactos. Suite completa: 146/146. **S13** registado para o CORS em si (aceita qualquer origem — fora do escopo deste item, requer decisão humana sobre origens legítimas). Nota em `AUDIT-SECURITY-2026.md` (tabela OWASP).

---

### A23 — Restringir CORS a origens conhecidas

**Quem:** Claude + Desenvolvedor
**Origem:** STATUS.md item S13 (achado durante A20, 2026-09-19) — `apps/api/src/server.ts:25`, `app.use(cors())` sem opções, aceita qualquer origem; contradição detectada com o CORP do helmet (agora `cross-origin`, ver A20)

**Fase 1 — Análise e Verificação**
Confirmar com o Desenvolvedor: que origens (domínios de frontend) devem legitimamente poder chamar esta API? Sem esta resposta, não há lista para configurar.

**Fase 2 — Execução**
Claude aplica `cors({ origin: [...origens confirmadas], credentials: true se aplicável })` assim que a lista existir. Não implementar uma lista adivinhada.

**Fase 3 — Teste e Validação**
Teste: pedido com `Origin` na lista → `Access-Control-Allow-Origin` presente e correcto. Pedido com `Origin` fora da lista → header ausente/pedido rejeitado pelo browser. Suite completa.

**Fase 4 — Atualização de Status**
Mover S13 para Done em STATUS.md.

---

### A21 — CodeQL #6

**Quem:** Claude
**Origem:** STATUS.md, resumo 2026-09-17

**Fase 1 — Análise e Verificação**
Reabrir `packages/scripts/src/docs/generate-agents-doc.ts:85`, confirmar o padrão exacto de escaping incompleto.

**Fase 2 — Execução**
Escapar `\` antes de `|` ao gerar a tabela Markdown.

**Fase 3 — Teste e Validação**
Re-rodar o scan CodeQL, confirmar que o alerta específico fecha. Teste unitário com um valor de campo contendo `|` real, confirmar que a tabela gerada não quebra.

**Fase 4 — Atualização de Status**
Mover para Done, fechar o alerta #6 (o #5 — `verifyPassword` — já está fechado, confirmado nesta sessão).

> **Status em 2026-09-19: DONE — sem Fase 2, não havia nada para corrigir.** `escapeMdCell()` já escapava backslash antes de pipe correctamente desde o commit `a828bf2` (2026-09-17 21:17), 2 dias antes desta sessão e antes do próprio `EXECUTION-PROMPTS.md` ter sido escrito — mesmo padrão do **C6** (item já resolvido, documento nunca revalidado). Verificado empiricamente (6 casos, incluindo `\|` e `path\to|file`) e por `git log`. Único gap real: o commit prometia "testable" mas não tinha teste — confirmado que `tests/unit/generate-agents-doc.test.ts` já o tem (`describe('escapeMdCell — CodeQL #6 ...')`, 4 testes, 4/4 a passar), por isso nem esse teste precisou de ser escrito de novo. Nota em `STATUS.md`, resumo 2026-09-17 (linha do alerta #6).

**Alerta geral (padrão recorrente, 3ª ocorrência nesta sessão — C6, A1, A21):** pelo menos 3 itens deste documento descreviam como pendente algo que o código já tinha resolvido antes do documento ser escrito. Fase 1 de todo item já manda "reconfirmar por leitura directa antes de executar" — mas vale registar explicitamente: **antes de assumir Fase 2 necessária em qualquer item futuro deste documento, confirmar por `git log -- <ficheiro>` se já não há um commit posterior à Origem citada que resolva o mesmo achado.** Um "achado real" pode ter sido corrigido depois de documentado e antes de ser lido de novo — a data da Origem não é garantia de estado actual.

---

### A22 — Vulnerabilidades Dependabot pós-push (9 alertas)

**Quem:** Claude + Desenvolvedor
**Origem:** STATUS.md item M8 (GitHub Dependabot, reportado no push do commit `2d03b4b`, 2026-09-19)

**Fase 1 — Análise e Verificação**
Abrir `github.com/souzalrns/network-agents-setup/security/dependabot` e confirmar, alerta a alerta, a lista actual: 3 críticas (`vitest`), 1 alta (`vite`), 5 moderadas (`vite`, `uuid` ×2, `launch-editor`, `esbuild`, `vitest`) — confirmar que a contagem e os pacotes batem com o que o GitHub mostra agora (pode ter mudado desde o push). Confirmar quais são `devDependencies` (via `package.json`/`pnpm-lock.yaml`) vs. dependência real de produção — `uuid`, usado em `apps/api`, é o único caso a confirmar com atenção.

**Fase 2 — Execução**
Para as 8 de dev (`vitest`, `vite`, `esbuild`, `launch-editor`): `pnpm update` para a versão corrigida (confirmar changelog de breaking changes antes, mesmo sendo dev). Para `uuid` (produção, prioridade): confirmar a versão corrigida pelo advisory, verificar se é major bump com breaking changes (ex. mudança CommonJS→ESM entre v8/v9), actualizar `apps/api` conforme necessário.

**Fase 3 — Teste e Validação**
Rodar a suite de testes completa (`vitest`) depois do bump — nenhuma regressão. Rodar os testes/integração de `apps/api` especificamente para confirmar que a troca de `uuid` não quebra nenhum ID gerado/consumido. Confirmar em `github.com/souzalrns/network-agents-setup/security/dependabot` que os 9 alertas fecham (0 abertos).

**Fase 4 — Atualização de Status**
Mover M8 para Done em STATUS.md. Nota: "9 alertas Dependabot resolvidos em [data] — 8 dev via pnpm update, 1 prod (uuid) com teste de regressão em apps/api".

---

*(Fim do Grupo A — 23/23 itens.)*

---

### S15a — Rotação de credenciais incompleta no GitHub Actions do `agent-network-mcp`

> **Nota:** item da série `S` (STATUS.md 🔴 Crítico), não contabilizado nos 23 itens do Grupo A acima — mesmo padrão de `S9`/`S11`-`S14`, cross-referenciados mas fora da contagem A-J.

**Quem:** Desenvolvedor (é quem tem acesso ao GitHub Actions/Supabase de `agent-network-mcp`)
**Origem:** achado durante a sessão de 2026-09-20, ao investigar a falha 401 do `transcribe.yml`

**Fase 1 — Análise e Verificação (feita nesta sessão)**
Lidos os 9 `.github/workflows/*.yml` de `agent-network-mcp` (repo clonado em `C:\Users\souza\Claude Code\agent-network-mcp`). **7 dos 9** usam `SUPABASE_SERVICE_ROLE_KEY`: `audit-tools.yml`, `diagnostico-playwright-portal.yml`, `extrair-imagem.yml` (2 jobs), `scrape.yml`, `testar-portal-justica.yml`, `transcribe.yml`, `visual-review.yml`. Os outros 2 (`heartbeat.yml`, `ingest.yml`) usam `INGEST_URL`/`INGEST_SECRET`, não Supabase directamente. Dos 7 afectados, só **`audit-tools.yml` corre por `schedule`** (cron `"0 10 1,15 * *"` — dias 1 e 15, 10h UTC); os restantes 6 são `workflow_dispatch` (só falham quando corridos manualmente). Confirmado pelo utilizador: as 3 credenciais rotacionadas hoje foram `SUPABASE_SERVICE_ROLE_KEY`, a password da BD, e `GEMINI_API_KEY` — todas expostas durante a sessão.

**Fase 2 — Execução (Desenvolvedor)**
Actualizar a secret `SUPABASE_SERVICE_ROLE_KEY` no GitHub Actions de `souzalrns/agent-network-mcp` (Settings → Secrets and variables → Actions) com o valor novo gerado na rotação de hoje.

**Fase 3 — Teste e Validação**
Re-correr `transcribe.yml` manualmente **só depois de confirmada a actualização da secret, e só com autorização explícita do utilizador para disparar** — com o reel que falhou originalmente. Confirmar HTTP 200/sucesso em vez de 401. **Estado actual: a aguardar essa autorização — não disparado ainda.**

**Fase 4 — Atualização de Status**
Mover S15a para Done em STATUS.md quando a secret estiver confirmada actualizada e `transcribe.yml` re-testado com sucesso.

---

### S15b — Verificar se `SUPABASE_ANON_KEY` também foi rotacionada

> **Status em 2026-09-20: N/A, fechado.** Confirmado pelo utilizador: só as 3 credenciais acima foram rotacionadas — a `ANON_KEY` **não foi tocada, por decisão consciente** (é pública por design, não foi exposta nesta sessão, e rotacioná-la sem necessidade partiria clientes existentes sem ganho de segurança real). `keep-alive.yml` (`network-agents-setup`, corre por `schedule` a cada 3 dias) **continua funcional** — usa a mesma `ANON_KEY` de antes da sessão, nunca esteve em risco. `ci.yml`/`ingest-knowledge.yml`/`runner-tests.yml` não usam nenhuma credencial Supabase.

---

### S18 — `README.md` (raiz) desactualizado

> **Status em 2026-09-20: DONE.** Achado durante a auditoria de cobertura (2f), corrigido de imediato (item pequeno, 15 min). `README.md` (171 linhas, lido por inteiro): "50 skills + 21 agentes" → **67 + 35** (confirmado por `find`); secção "Falta" tinha 3 itens já fechados (F3, F4, B1/S9) — removidos, mantido só Delegation Graph/Context Sync/AgentMesh/Cedar, com nota sobre Action Receipts (C5) já parcialmente feito; diagrama de pastas do `agents/` só listava 3 de 8 domínios reais — corrigido. Reler o ficheiro completo no fim confirma coerência; links/exemplos verificados a apontar para ficheiros reais.

---

## GRUPO B — Fiação interna / HITL / validação de execução real (13 itens)

> **Revalidação de escopo (B14/D10, 2026-09-19):** todos os 8 itens ainda pendentes (B1, B3-B9) confirmados **REAL** (escopo correcto, nada resolvido entretanto) por leitura directa do código. Ver `docs/architecture/meta-validation/AUDIT-SCOPE-2026-09-19.md`.

### B1 — Ligar `hitl.py` aos engines *(= S9)*

**Quem:** Claude
**Origem:** `agents-audit/meta-validation/AUDIT-META-VALIDATION.md` secção 2; STATUS.md item S9

**Fase 1 — Análise e Verificação**
Reabrir `runner/plan_runner/hitl.py` na íntegra (confirmar que `write_request()`/`read_decision()` continuam como documentado). Grep em `engine.py`, `langgraph_engine.py`, `cli.py` por `import hitl`/`hitl\.` — confirmar que continua zero (era o achado central).

**Fase 2 — Execução**
Em `engine.py`/`langgraph_engine.py`: no ponto onde `human_gate_requested` já é escrito em `events.jsonl`, adicionar chamada a `hitl.write_request(run_dir, step=..., run_id=..., plan_id=..., completed=...)` (dupla-escrita, aditivo — não remover o que já existe). Em `cli.py`, o comando `resume` passa a tentar `hitl.read_decision(run_dir)` primeiro; se não houver decisão lá, cair no `--decision` explícito da CLI (não-regressão: o uso actual via `--decision` continua a funcionar).

**Fase 3 — Teste e Validação**
Rodar um plano real com `human_gate` até parar; confirmar `hitl-requests.jsonl` escrito no directório do run com o schema `hitl-request-v1`. Escrever manualmente uma decisão em `hitl-decisions.jsonl`; confirmar que `plan_runner resume` a lê e continua sem precisar de `--decision`. Rodar a suite completa (167+ testes documentados) e confirmar zero regressão.

**Fase 4 — Atualização de Status**
Mover S9 para Done em STATUS.md. Nota em `hitl/README.md`: trocar "Status: design. Not implemented." pelo estado real, já que a Fase A.2b passou a existir.

> **Status em 2026-09-20: DONE.** `hitl.write_request()` ligado nos 2 pontos `human_gate_requested` de `engine.py` (`run_plan`+`resume_run`) e nos 2 pontos análogos de `langgraph_engine.py` (`run_plan_langgraph`+`resume_plan_langgraph`), sempre em dupla-escrita ao lado do `log.append(...)` já existente (nada removido). Em `cli.py`, o comando `resume` agora resolve `decision = hitl.read_decision(args.out)["response"] if ... else args.decision` antes do branching langgraph/native — não-regressão confirmada (`--decision` continua a funcionar quando não há ficheiro de decisão). Testado ponta-a-ponta nos 2 motores com `docs/orchestration/design/templates/examples/design-flow-demo.plan.yaml` em modo `stub`: plano pára em `paused_human_gate`, `hitl-requests.jsonl` escrito com `schema: "hitl-request-v1"`; decisão escrita manualmente via `hitl.write_decision()` (simulando o lado Node) e lida por `resume` sem `--decision` — confirmado com decisão `reject` (não só `approve`, que é o omissão do argparse, para excluir falso positivo). Suite completa: 146/146 testes TS (2 falhas pré-existentes não relacionadas: `supertest` em falta, `prisma generate` não corrido) + 172/172 testes Python, 0 regressões. Nota em `hitl/README.md` ainda por fazer (marcada acima, não bloqueia o fecho de B1/S9).

---

### B2 — Corrigir `ExecutionFlow.test.ts`

**Quem:** Claude
**Origem:** `orchestration-audit/AUDIT-ORCHESTRATION.md` secção 3

**Fase 1 — Análise e Verificação**
Reabrir `tests/integration/ExecutionFlow.test.ts`. Confirmar que `new Orchestrator(mockAgentFactory, router, planner, executor, memory as any)` continua com 5 argumentos (falta `hitlManager`, o 6º, já definido no próprio teste como `mockHitl` mas nunca passado).

**Fase 2 — Execução**
Adicionar `mockHitl` como 6º argumento na chamada ao construtor.

**Fase 3 — Teste e Validação**
Rodar o teste ANTES da correcção e registar se passa ou falha (confirma ou refuta a hipótese registada na auditoria — "provavelmente só passa porque nenhum caminho do input de teste chega a invocar hitlManager"). Depois da correcção, forçar deliberadamente um cenário que exija aprovação humana (`deliberation.approved = false` ou critérios que disparem `requiresApproval`) e confirmar que não lança `TypeError: Cannot read properties of undefined`.

**Fase 4 — Atualização de Status**
Mover para Done, grupo B. Registar em `AUDIT-ORCHESTRATION.md` secção 3 se o teste passava ou falhava antes da correcção — é um dado novo que a auditoria não pôde confirmar por falta de `node_modules`.

> **Status em 2026-09-19: DONE (correcção); verificação por execução pendente.** 2 bugs corrigidos: (a) `mockHitl` como 6º argumento; (b) `vi` em falta no import de `vitest` (achado durante a correcção, não estava no achado original — o ficheiro usava `vi.fn()` 6 vezes sem o importar, com `globals: false` no `vitest.config.ts`). `tsc --noEmit` (config equivalente ao `tsconfig.typecheck.json`, estendida para cobrir `tests/`) confirma zero erros no ficheiro — os únicos erros restantes são no `packages/memory/src/*`, todos `Module '@prisma/client' has no exported member 'PrismaClient'`, o mesmo bloqueio pré-existente de **B10/D8**. Não foi possível correr o teste de facto (mesma razão) — a hipótese da auditoria ("passava por acaso, sem invocar `hitlManager`") continua NOT VERIFIED, a confirmar quando B10/D8 fechar. Nota em `AUDIT-ORCHESTRATION.md` secção 3.

> **Actualização em 2026-09-20 (B10/D8 fechado, ver B17 em `STATUS.md`): hipótese REFUTADA.** `prisma generate` corrido, o teste finalmente carregou e correu — e o teste **invoca `hitlManager` a sério** (`DeliberationOrchestrator.deliberate()` chama `requestApproval()` de facto). Não "passava por acaso sem invocar" — nunca tinha sequer chegado a correr. O `mockHitl.requestApproval: vi.fn()` sem valor resolvido causava `Cannot read properties of undefined (reading 'id')` em `DeliberationOrchestrator.ts:121`; corrigido com `.mockResolvedValue({ id: 'hitl-test-id' })`. `ExecutionFlow.test.ts` passa 1/1 agora.

---

### B3 — Correr `apps/api` contra Postgres/OpenAI reais

**Quem:** Claude + Desenvolvedor
**Origem:** `orchestration-audit/AUDIT-ORCHESTRATION.md` secção 7

**Fase 1 — Análise e Verificação**
Reler `apps/api/src/index.ts` por completo, listar todas as env vars exigidas (`DATABASE_URL`, `OPENAI_API_KEY`, `REDIS_URL` opcional, `FILESYSTEM_BASE`, `PUBLIC_MODE`, `PORT`, `HITL_EXPIRE_MINUTES`). Confirmar com o Desenvolvedor que valores reais (ou de staging) estão disponíveis.

**Fase 2 — Execução**
Desenvolvedor fornece o `.env` real (ou de staging). Claude sobe o servidor (`pnpm --filter api dev` ou equivalente), envia 1 pedido real via `processRequest` (ex. curl para o endpoint que o expõe).

**Fase 3 — Teste e Validação**
Resposta HTTP 200 com `content` preenchido. `orchestrator.getSystemStatus()` devolve dados não-nulos em pelo menos `security`/`trust`/`health`. Nenhum erro não tratado no log do processo durante o pedido. Confirmar que os `AGENT_CONFIGS` (24 agentes) foram todos registados no arranque (log "Agents loaded: 24").

**Fase 4 — Atualização de Status**
Mover para Done. Esta é a peça que fecha definitivamente a pergunta "o pipeline TS funciona de ponta a ponta?" levantada em `AUDIT-ORCHESTRATION.md` — registar o resultado lá também (secção dedicada, não só STATUS.md).

---

### B4 — `HitlManager.importFromFile/exportToFile` *(= M2)*

**Quem:** Claude
**Origem:** `hitl/README.md` Fase A.3; STATUS.md item M2
**Depende de:** B1

**Fase 1 — Análise e Verificação**
Confirmar que B1 está fechado (sem isso não há ficheiro real para importar/exportar). Reabrir `packages/shared/src/types/hitl.ts` e comparar campo a campo com `docs/architecture/hitl/hitl-request-v1.json`.

**Fase 2 — Execução**
Implementar `HitlManager.importFromFile(path)` (lê `hitl-requests.jsonl`, converte para `HitlRequest` interno) e `exportToFile(path)` (escreve `hitl-decisions.jsonl` na forma do contrato). Alinhar `hitl.ts` com os campos do contrato v1 (`schema`, `source`, `run_id`, `plan_id`, `step_id`, `allow`) se ainda faltar algum.

**Fase 3 — Teste e Validação**
Teste de round-trip: criar um `HitlRequest` no `HitlManager`, exportar, reimportar num segundo `HitlManager` limpo, confirmar igualdade de campos.

**Fase 4 — Atualização de Status**
Mover M2 para Done.

> **Status em 2026-09-20: DONE.** Discrepância na Fase 1: `hitl.ts` tinha `agentId`/`domain`/`category`/`description`/`proposedAction` obrigatórios e não-nulos, mas o contrato v1 marca-os `nullable` e o `hitl.py` (B1) escreve `null` de facto quando o plano não os fornece — resolvido tornando-os `| null` em `hitl.ts` (não quebra `requestApproval()`, que continua a exigi-los como `string` nos parâmetros). `response` também divergia (`'approved'|'rejected'` interno vs `'approve'|'reject'|'edit'` do contrato) — resolvido com tradução na fronteira dentro de `toContractRecord()`/`fromContractRecord()`, sem tocar em `approveRequest()`/`rejectRequest()`. Ambiguidade adicional entre a Fase 2 deste item (que descreve `exportToFile` como escrevendo `hitl-decisions.jsonl`) e a Fase 3 (teste de round-trip completo de campos, que só faz sentido com o formato de pedido completo): resolvida fazendo `importFromFile`/`exportToFile` operarem sobre o formato de **pedido** (contrato v1, `hitl-requests.jsonl`) — serve o round-trip da Fase 3 e o caso de uso real do `hitl/README.md` Opção A ("HitlManager lê hitl-requests.jsonl quando a API é consultada"); escrever `hitl-decisions.jsonl` a partir do Node (quando um humano aprova via `POST /hitl/:id/approve`) fica para o B5. 4 testes novos + 10 antigos = 14/14 em `HitlManager.test.ts`; `tsc --noEmit` sem novos erros.

---

### B5 — Teste e2e HITL Python→Node→Python *(= M3)*

**Quem:** Claude + Desenvolvedor
**Origem:** `hitl/README.md` Fase A.4; STATUS.md item M3
**Depende de:** B1, B4

**Fase 1 — Análise e Verificação**
Reler o cenário de 5 passos já desenhado no `hitl/README.md` ("Run design-flow-demo.plan.yaml... Node API aprova via POST /hitl/:id/approve...").

**Fase 2 — Execução**
Escrever script de teste automatizado cobrindo os 5 passos: (1) rodar plano até pausar; (2) confirmar `hitl-requests.jsonl` escrito; (3) Node API lê via `GET /hitl` (precisa de B3 — API real a correr); (4) Node aprova via `POST /hitl/:id/approve`, escreve `hitl-decisions.jsonl`; (5) `plan_runner resume` lê a decisão e completa.

**Fase 3 — Teste e Validação**
Script falha explicitamente (não silenciosamente) se qualquer um dos 5 passos não completar. Rodar 2 vezes (idempotência) e confirmar mesmo resultado.

**Fase 4 — Atualização de Status**
Mover M3 para Done.

---

### B6 — HITL durável em Postgres *(= M4)*

**Quem:** Claude + Desenvolvedor
**Origem:** `hitl/README.md` Fase 2 (Option B); STATUS.md item M4
**Depende de:** B1, B4, B5 (implementados e testados em ficheiro — só depois migrar para Postgres, não antes)

**Fase 1 — Análise e Verificação**
Confirmar B1/B4/B5 fechados e o teste e2e a passar com o ficheiro (`hitl-requests.jsonl`). Reler a secção "Option B — Supabase" do `hitl/README.md` para o schema de tabela já desenhado.

**Fase 2 — Execução**
Criar tabela `hitl_requests` no Supabase com o mesmo schema do contrato v1. Trocar a implementação de leitura/escrita de `hitl.py` (Python, via `supabase-py`) e `HitlManager.ts` (via `@supabase/supabase-js`) para ler/escrever da tabela em vez do ficheiro, mantendo a mesma interface pública.

**Fase 3 — Teste e Validação**
Rodar o mesmo teste e2e de B5, agora contra a tabela, confirmando comportamento observável idêntico (o consumidor não deveria notar diferença).

**Fase 4 — Atualização de Status**
Mover M4 para Done.

---

### B7 — Expor `langgraph`+`edit` via MCP

**Quem:** Claude
**Origem:** `agents-audit/FASE2-AGENTES.md` secção 1

**Fase 1 — Análise e Verificação**
Reabrir `mcp/plan_runner/mcp_plan_runner/tools_impl.py` e `tools-catalog.md`. Confirmar que `run_plan` não tem parâmetro `engine` e `resume_plan` só aceita `approve|reject`.

**Fase 2 — Execução**
Adicionar `engine: "native"|"langgraph"` (default `"native"`, não-regressão) a `run_plan`, delegando a `run_plan_langgraph` quando `"langgraph"`. Adicionar `decision: "edit"` + `payload` opcional a `resume_plan`, delegando a `resume_plan_langgraph` quando aplicável.

**Fase 3 — Teste e Validação**
Chamar a tool MCP `run_plan` com `engine: "langgraph"`, confirmar `checkpoints.db` criado no directório do run. Chamar `resume_plan` com `decision: "edit"` + payload, confirmar que o artefacto reflecte o conteúdo editado (não o stub por omissão). Confirmar que chamadas sem `engine`/com `decision` antigo continuam a funcionar exactamente como antes.

**Fase 4 — Atualização de Status**
Mover para Done, grupo B. Actualizar `tools-catalog.md` com os novos parâmetros.

---

### B8 — Propagar `knowledge:` aos templates

**Quem:** Claude
**Origem:** `ingestion-audit/AUDIT-INGESTION.md` secção 1

**Fase 1 — Análise e Verificação**
Listar os 12 templates em `docs/orchestration/` e confirmar que só `seo-article-demo-s9.plan.yaml` usa o bloco `knowledge:`.

**Fase 2 — Execução**
Para cada um dos 11 restantes, avaliar se algum step se beneficia de contexto de RAG (ex. um step de pesquisa/redacção que já tenha uma KB correspondente em `docs/knowledge/`); adicionar o bloco onde fizer sentido, deixar os que não precisam sem alteração.

**Fase 3 — Teste e Validação**
Para cada template alterado, rodar em modo `stub`, confirmar `knowledge_context.md` escrito com hits reais (ou falha graciosa documentada, se a KB não tiver conteúdo para aquela query).

**Fase 4 — Atualização de Status**
Mover para Done, grupo B, com a contagem final (ex. "5/12 templates usam knowledge:, os restantes 7 não têm KB aplicável").

> **Status em 2026-09-20: DONE.** Confirmados os 12 templates da Fase 1 (só `seo-article-demo-s9.plan.yaml` tinha `knowledge:`). **Achado real da Fase 2** — `scripts/ingest_delta.py` (`MANIFEST`) e `scripts/ingest_apply.py` (`_kb_for()`) mostram que o `kb` não é livre: só existem 3 buckets com conteúdo real ingerido — `marketing` (~25 ficheiros), `produto-tech` (2 ficheiros) e `global` (fallback, cobre `saude`/`legal`/`imobiliario`). **Não existe bucket `design`** — `docs/knowledge/design/*.md` nunca foi adicionado ao `MANIFEST`, e `ux.md`/`ui.md` (nível de topo) estão etiquetados `marketing`, não `design`. Um `knowledge: {kb: design, ...}` nos templates de design devolveria sempre vazio, silenciosamente — pior que não ter o bloco. Resultado: **7/12** templates (marketing, com conteúdo real na KB) ganharam `knowledge:` — `approval-rounds` (3 steps `creative_review`), `influencer-pack`, `internal-brief`, `paid-pack`, `seo-article` (espelha os 3 blocos do S9), `social-pack` (2 steps), `ugc-video-pack` (2 steps); **5/12** ficaram sem alteração, cada um por razão distinta: `seo-article-demo-s9.plan.yaml` (já tinha), `seo-article-demo.plan.yaml` (o próprio ficheiro documenta que fica intencionalmente intacto — é o "antes" do S9), `ship-parallel.plan.yaml` (code/security/test review, sem correspondência em nenhum KB de marketing), `design-flow.plan.yaml`/`design-flow-demo.plan.yaml` (sem bucket `design` — ver achado acima; candidato a item novo de backlog, não registado aqui por ser fora do escopo do B8). Testado: os 7 templates alterados correm em `stub`, os 12 blocos `knowledge:` (novos + os 3 do S9) disparam `knowledge_wiring.py` e escrevem `knowledge_context.md` com falha graciosa documentada (`MCP_API_KEY não definida` — sem credenciais neste ambiente, resultado esperado por `hitl/README.md`/`RATE-LIMITS.md`).

---

### B9 — Schema `knowledge:` no `Plan.schema.json`

**Quem:** Claude
**Origem:** `ingestion-audit/AUDIT-INGESTION.md` secção 1

**Fase 1 — Análise e Verificação**
Confirmar em `docs/architecture/plan-execute/schemas/Plan.schema.json` que o bloco `knowledge` (distinto de `knowledge_refs`) continua ausente.

**Fase 2 — Execução**
Declarar `knowledge: {kb: string (required), query: string (required), top_k?: number, require_citations?: boolean, filters?: object}` no schema do step.

**Fase 3 — Teste e Validação**
Um plano de teste com `knowledge: {kb: 123}` (tipo errado) falha na validação do schema, antes de chegar a `knowledge_wiring.py`. Um plano com `knowledge` bem formado continua a validar e a funcionar como antes (não-regressão sobre B8).

**Fase 4 — Atualização de Status**
Mover para Done, grupo B.

> **Status em 2026-09-20: DONE.** Discrepância na Fase 1: `docs/architecture/plan-execute/` (onde vive o `Plan.schema.json`) é **documentação/design desligada do runtime real** — o próprio `README.md` do directório diz "Não liga sozinho ao `agent-network-mcp`", e nenhum `.py`/`.ts` do repo importa ou valida contra `Plan.schema.json` (confirmado por grep; a validação real dos planos usados por `engine.py`/`langgraph_engine.py` é feita em Python puro por `graph.py`/`models.py`, sem JSON Schema). O brief da Fase 3 ("um plano com `knowledge: {kb: 123}` falha na validação do schema, antes de chegar a `knowledge_wiring.py`") pressupõe uma ligação viva que não existe — não há forma de um plano real chegar a ser validado por este ficheiro. Classificação: **DIFERENTE** (execução ajustada, sem parar, por não ser decisão de arquitectura — só um documento de design, sem tocar em `graph.py`/`models.py`). Resolução: adicionado o campo `knowledge` (opt-in, `kb`+`query` obrigatórios, `top_k`/`require_citations`/`filters` opcionais) a `Plan.schema.json`, alinhado ao formato real de `knowledge_wiring.py`; teste novo em `test_plan_schema_json.py` valida o **schema em si** contra o único exemplo real do directório (`examples/piloto-netos.plan.yaml`, que já conformava ao schema antes desta alteração) — 6 testes (schema tem a propriedade; exemplo real continua válido após a alteração — não-regressão; bloco bem formado valida; `kb` de tipo errado falha; `query` em falta falha; propriedade desconhecida falha por `additionalProperties: false`). `jsonschema>=4.26.0` adicionado a `runner/requirements.txt` (já estava instalado transitivamente, agora declarado). Nenhuma tentativa de wire real validation ao `plan_runner` — isso quebraria todos os planos reais de `docs/orchestration/` (que não têm `plan_id`/`created_at`/`goal`/`context.brand`/`verify`/`status`/`model_tier`, todos exigidos por este schema) e seria uma mudança de arquitectura fora do escopo pedido.

---

### B10 — Confirmar S5 fechado

**Quem:** Claude + Desenvolvedor
**Origem:** STATUS.md item S5

**Fase 1 — Análise e Verificação**
Reler `ci.yml` para confirmar que o passo `validate:consistency` existe.

**Fase 2 — Execução**
Desenvolvedor confirma, no histórico real de GitHub Actions, runs recentes com esse passo verde.

**Fase 3 — Teste e Validação**
Link do run de CI mais recente com o passo verde, anexado ao fecho do item.

**Fase 4 — Atualização de Status**
Mover S5 para Done com o link do run.

---

### B11 — Session search FTS5 *(= M1)*

**Quem:** Claude
**Origem:** STATUS.md item M1

**Fase 1 — Análise e Verificação**
Reabrir `runner/plan_runner/events.py`, confirmar o formato exacto de `EventLog.append()` (`{id, type, run_id, at, payload}`).

**Fase 2 — Execução**
Criar índice FTS5 (SQLite) derivado de `events.jsonl` — tabela virtual indexando `payload` como texto pesquisável, com `run_id`/`type`/`at` como colunas auxiliares. Script de (re)indexação que lê o JSONL e popula o índice (aditivo, não substitui o ficheiro original).

**Fase 3 — Teste e Validação**
Inserir eventos de teste conhecidos, buscar por um termo presente num deles, confirmar que só esse é devolvido (sem falsos positivos/negativos).

**Fase 4 — Atualização de Status**
Mover M1 para Done.

> **Status em 2026-09-20: DONE.** Sem discrepâncias na Fase 1 — `EventLog.append()` confirmado exactamente como descrito (`{id, type, run_id, at, payload}`, mais `**extra` opcional como `actor`, já previsto pela assinatura). `runner/plan_runner/session_search.py` (novo): `build_index()`/`search()` sobre `events_fts.db` (SQLite FTS5), aditivo — `events.py` intocado. 7/7 testes novos, incluindo o cenário pedido (termo presente num único evento não devolve falsos positivos/negativos) e reindexação idempotente após novo evento.

---

### B12 — Mover módulos para `experimental/` *(= M5)*

**Quem:** Claude + Desenvolvedor
**Origem:** STATUS.md item M5

**Fase 1 — Análise e Verificação**
**Crítico:** a lista original de "~14 módulos sem consumidor" foi feita antes de se confirmar que `Orchestrator.ts` é real (não mock) e consome ~30 módulos de facto. Recontar, módulo a módulo, com `grep -r "from.*NomeDoModulo"` em todo `packages/`, quais continuam sem nenhum importador **depois** dessa correcção — a lista antiga pode estar errada pela mesma razão.

**Fase 2 — Execução**
Só mover os módulos que a recontagem confirmar sem consumidor algum. Desenvolvedor aprova a lista final antes de qualquer `git mv`.

**Fase 3 — Teste e Validação**
Depois de mover, `tsc --noEmit` limpo (confirma que nada dependia do path antigo sem ter aparecido no grep). Suite de testes completa sem regressão.

**Fase 4 — Atualização de Status**
Mover M5 para Done com a lista final (provavelmente menor que 14).

---

### B13 — GeminiProvider + Planner melhorado *(= M6)*

**Quem:** Claude
**Origem:** STATUS.md item M6

**Fase 1 — Análise e Verificação**
Reabrir `packages/core/src/llm/` para confirmar a interface `LLMProvider` que `OpenAIProvider` já implementa, e `Planner.ts` (já lido nesta sessão) para confirmar o schema de saída actual.

**Fase 2 — Execução**
Implementar `GeminiProvider` seguindo a mesma interface. Estender o prompt e o schema de saída do `Planner.ts` com `scope`, `unknowns`, `pre_mortem`, `not_doing`.

**Fase 3 — Teste e Validação**
Gerar um plano real via `GeminiProvider`, confirmar JSON de saída com os 4 campos novos preenchidos de forma substantiva (não vazios/genéricos — revisão manual do conteúdo, não só presença da chave).

**Fase 4 — Atualização de Status**
Mover M6 para Done.

---

*(Fim do Grupo B — 13/13 itens.)*

---

## GRUPO C — Governança / MCP / Autorização (7 itens)

> **Revalidação de escopo (B14/D10, 2026-09-19):** C2-C5 confirmados **REAL**. C7 reclassificado **JÁ FEITO** (ver nota no próprio item). C6 mantém-se como já discutido na errata do topo (revalidação genuína, não pendência falsa). Ver `docs/architecture/meta-validation/AUDIT-SCOPE-2026-09-19.md`.

### C1 — Portar pipeline de `policy.py` para `ToolExecutor.ts`

**Quem:** Claude
**Origem:** `tools-mcp-audit/AUDIT-TOOLS-MCP.md` secção 4; `GOV-FASE1.md`

**Fase 1 — Análise e Verificação**
Reabrir `mcp/plan_runner/mcp_plan_runner/policy.py` na íntegra (`authorize`, `rate_limit`, `sanitize_repo_path`, `audit`) e `tools_impl.py` para ver como as 4 tools Python os compõem. Reabrir `packages/mcp/src/tools/ToolExecutor.ts` (25 linhas) para confirmar o estado actual (só valida presença de parâmetros).

**Fase 2 — Execução**
Traduzir para TS: `authorize(caller, toolName)` com mapa `SCOPES` (`namespace:resource:action` por tool) e perfis `permissive/moderate/strict` (ler de env var, mesmo padrão `PLAN_RUNNER_MCP_KEY`/`PLAN_RUNNER_MCP_ALLOW_MUTATE`); `rateLimit(caller)` in-process (60/60s, `Map<string, number[]>` protegido — decidir se precisa de lock em Node, dado que é single-threaded por padrão, diferente do `threading.Lock` do Python); `audit(event)` append-only em JSONL. Integrar os 3 em `ToolExecutor.executeTool()` antes de `tool.execute(params)`.

**Fase 3 — Teste e Validação**
Portar a mesma matriz de casos que `test_policy.py` (Python) já cobre: perfil `strict` sem key rejeita mutação; perfil `moderate` sem key permite com `reason: "moderate_lab_open"`; perfil `permissive` permite tudo; tool desconhecida rejeitada (`unknown_tool`). Confirmar `audit.jsonl` (TS) com o mesmo formato do Python.

**Fase 4 — Atualização de Status**
Mover para Done, grupo C. Nota em `AUDIT-TOOLS-MCP.md` secção 4 e em `GOV-FASE1.md` (o achado original desta lacuna).

> **Status em 2026-09-19: DONE.** Discrepâncias reais entre o brief e `policy.py` (assinaturas, SCOPES de outras tools, perfis mais granulares — ver relatório da Fase 1 na conversa) — resultado é um **desenho novo inspirado no padrão**, não um porte 1:1. `packages/mcp/src/tools/ToolPolicy.ts` (novo): `authorize()`/`rateLimit()`/`audit()`, SCOPES próprio para as 6 tools reais, 7 razões replicadas fielmente do Python. Perfil por omissão `strict` (decisão consciente, diferente do `moderate` do Python — fail-closed). Integrado em `ToolExecutor.executeTool()` com 3º parâmetro novo `context: {caller?, providedKey?}` (não existia nenhum conceito de caller/key antes). `tests/unit/ToolPolicy.test.ts` novo (12 testes, cobre os 7 reasons + rate-limit + audit) — 12/12. Suite completa: 106/106 (subiu de 94). Nota em `AUDIT-TOOLS-MCP.md` secção 4 e `GOV-FASE1.md` (secção 2b). `MCPServer.ts`/`MCPClient.ts` (autenticação HTTP/transporte) continuam pendentes — ver C2.

---

### C2 — Decisão TS vs. Python MCP

**Quem:** Desenvolvedor
**Origem:** `GOV-FASE1.md` secção 4; `orchestration-audit/AUDIT-ORCHESTRATION.md` secção 4

**Fase 1 — Análise e Verificação**
Reler as duas implementações lado a lado (`packages/mcp/` vs. `mcp/plan_runner/`) — já mapeadas em detalhe nesta sessão — e o achado de que a duplicação se repete também na camada de planeamento (TS `Planner.ts` com LLM real vs. Python sem LLM).

**Fase 2 — Execução**
Desenvolvedor decide: (a) TS fica como camada fina que delega ao Python; (b) TS é descontinuado; (c) ambos coexistem com responsabilidades diferentes e documentadas.

**Fase 3 — Teste e Validação**
Decisão escrita como ADR em `docs/architecture/adr/`, não uma escolha implícita nem adiada de novo.

**Fase 4 — Atualização de Status**
Mover para Done com o link do ADR.

---

### C3 — Adotar AgentMesh (identity/delegation)

**Quem:** Claude + Desenvolvedor
**Origem:** `AUDIT-GOVERNANCE.md` secção 12

**Fase 1 — Análise e Verificação**
Reler `AUDIT-GOVERNANCE.md` secções 5-6 (o que foi verificado do `agentmesh-platform` v3.7.0 — `ScopeChain`/`DelegationLink`). Confirmar que a versão continua a mesma ou se houve release nova a reverificar.

**Fase 2 — Execução**
Claude integra só os módulos `identity`/`delegation` (sem `server/` completo). Desenvolvedor aprova a dependência nova antes do merge.

**Fase 3 — Teste e Validação**
Teste que cria uma cadeia de delegação de 2 saltos e confirma que `ScopeChain` rejeita um 3º salto além do limite de profundidade configurado (não-transitividade, já confirmada na auditoria de governança).

**Fase 4 — Atualização de Status**
Mover para Done, grupo C.

---

### C4 — Adotar Cedar (policy engine)

**Quem:** Claude + Desenvolvedor
**Origem:** `AUDIT-GOVERNANCE.md` secção 12

**Fase 1 — Análise e Verificação**
Reler a razão da escolha de Cedar sobre OPA na auditoria de governança (redundante se os dois coexistirem).

**Fase 2 — Execução**
Ligar Cedar via `policy-engine` do AGT como motor de decisão (`ALLOW`/`DENY`/`REQUIRE_HUMAN_APPROVAL`) por trás do `authorize()` de C1.

**Fase 3 — Teste e Validação**
Escrever 3 políticas Cedar de teste (allow, deny, require-approval) e confirmar que `authorize()` devolve a decisão certa para cada uma.

**Fase 4 — Atualização de Status**
Mover para Done, grupo C.

---

### C5 — Action Receipt

**Quem:** Claude
**Origem:** `AUDIT-GOVERNANCE.md` secção 12 (item "CONSTRUIR")

**Fase 1 — Análise e Verificação**
Reler o desenho de `DelegationLink.compute_hash()` do AgentMesh (a peça mais próxima já confirmada real, citada como inspiração).

**Fase 2 — Execução**
Desenhar o formato próprio: hash encadeado por acção (`actor`, `tool`, `params_hash`, `result_hash`, `prev_receipt_hash`), persistido junto do `audit.jsonl` já existente (aditivo).

**Fase 3 — Teste e Validação**
Executar uma sequência de 3 acções e confirmar que o hash da 3ª depende do conteúdo das 2 anteriores — cadeia verificável, não um log solto. Teste de adulteração: alterar manualmente um receipt do meio da cadeia e confirmar que a verificação subsequente detecta a quebra.

**Fase 4 — Atualização de Status**
Mover para Done, grupo C.

> **Status em 2026-09-20: DONE, com escopo deliberadamente reduzido face ao ADR-001 §4.** Fase 1: lido `ADR-001-governance-runtime.md` (187 linhas) por inteiro — o contrato completo de "Action Receipt" (secção 4) exige `agent`/`principal` como DID (AgentMesh, Ed25519) e uma `AuthorizationDecision` vinda de Cedar/OPA — nenhum dos dois existe neste repo (`agentmesh-platform` **não é sequer uma dependência instalada**, confirmado por `pip show`; foi só revisto externamente durante a auditoria). `AUDIT-GOVERNANCE.md` (189 linhas, secção 8 linha 81 e secção 11 linha 146) e `GOV-FASE1.md` (85 linhas, secção 2a linha 39) confirmam: Action Receipt está genuinamente por implementar, e o roadmap (`AUDIT-GOVERNANCE.md` §13) só prevê a integração AgentMesh/Cedar na "Fase 1", ainda não feita — construir o contrato completo agora exigiria inventar campos DID/AuthorizationDecision sem nenhuma implementação real por trás. **Decisão:** implementar a versão reduzida exactamente como o brief da Fase 2 já descrevia (`actor`/`tool`/`params_hash`/`result_hash`/`prev_receipt_hash`/`at`), não o contrato completo do ADR — documentado como decisão explícita, não silenciada. `packages/mcp/src/tools/ActionReceipt.ts` (novo): `computeReceiptHash()`, `hashResult()`, `appendReceipt()`, `verifyChain()`; persistido em `MCP_RECEIPTS_LOG_PATH` ou `${MCP_AUDIT_LOG_PATH}.chain` (aditivo, `audit.jsonl` intocado). Integrado em `ToolExecutor.executeTool()` no caminho de sucesso (depois do `audit()` já existente). 8 testes novos: `ActionReceipt.test.ts` (4 — cadeia de 3 acções depende das anteriores; adulteração do meio detectada com `broken_at` correcto; cadeia vazia/inexistente é válida; `hashResult()` determinístico) + `ToolExecutor.test.ts` (1 novo — integração real grava no `.chain`). Suite completa sem regressão.

---

### C6 — Confirmar C8e fechado

**Quem:** Claude
**Origem:** STATUS.md, já em Done, mas nunca revalidado nesta sessão (C8e corresponde também ao item **G1** da série de mapeamento G1-G5 do `STATUS.md` — nota de nomenclatura, ver correção nº5 do errata)

**Fase 1 — Análise e Verificação**
Reabrir `runner/plan_runner/mcp_knowledge.py` (já lido por completo nesta sessão) e confirmar que a tool `retrieve_knowledge` continua acessível.

**Fase 2 — Execução**
Nenhuma mudança de código esperada — só revalidação.

**Fase 3 — Teste e Validação**
Rodar `mcp/plan_runner/test_client.py` e confirmar que a tool aparece na lista e responde com sucesso contra um servidor MCP real (ou mock, se o real não estiver disponível — documentar qual dos dois).

**Fase 4 — Atualização de Status**
Já está em Done — só adicionar nota de "revalidado em [data]" se a suite passar, ou reabrir o item se não passar.

> **Status em 2026-09-20: REVALIDADO, continua Done.** **Discrepância na Fase 1 (Regra 5):** o brief apontava `mcp/plan_runner/test_client.py` como o teste a correr, mas esse ficheiro (141 linhas, lido por inteiro) testa o servidor **stdio** de `mcp_plan_runner` — envia `initialize`/`tools/list`/`tools/call → list_templates`, nenhuma relação com `retrieve_knowledge`. A suite que realmente cobre C8e é `runner/tests/test_mcp_knowledge.py` (274 linhas, lida por inteiro) — 13 testes, mocka os 3 níveis do transporte MCP (`httpx.AsyncClient`, `streamable_http_client`, `ClientSession`), não precisa de servidor real. Rodada: **13/13 passam**. `mcp_knowledge.py` (200 linhas, lido por inteiro) confirmado intacto, `MCP_TOOL_NAME = "retrieve_knowledge"` presente (linha 54). Verificação extra (não pedida, mas informativa): `curl` ao deployment real (`https://agent-network-mcp-oddn.vercel.app/api/mcp`) devolve `401` — confirma que o serviço real está no ar e a exigir auth, tal como documentado; sem `MCP_API_KEY` neste ambiente para uma chamada autenticada real. Nota em `STATUS.md` (entrada C8e).

---

### C7 — Resolver contradições `MCP-MAPPING.md`

> **Revalidado em 2026-09-19 (B14/D10): JÁ FEITO.** `MCP-MAPPING.md` já tem as 2 correcções aplicadas e visíveis no próprio texto ("Correcção G5", linhas 20/108/183 do documento): `apps-produto` já está na secção 3.5, `hvac` já está reclassificado, contagem já corrigida para 12. Só falta actualizar `STATUS.md` (item G5, ainda marcado pendente) para Done. Mesmo padrão do C6/A1/A21/A20. Ver `AUDIT-SCOPE-2026-09-19.md`.

**Quem:** Claude
**Origem:** STATUS.md item G5

**Fase 1 — Análise e Verificação**
Reabrir `MCP-MAPPING.md` e o `lib/agents.js` real (já clonado nesta sessão em `agent-network-mcp/`) — confirmar se `apps-produto` já foi classificado nalguma das 6 secções de detalhe, e se a contradição de `hvac` (tabela diz "Proprietário", secção de detalhe original dizia "genérico") já foi corrigida (parece que sim, pela nota "Correcção G5" já presente no documento — confirmar se ficou mesmo fechada ou só parcialmente).

**Fase 2 — Execução**
Se `apps-produto` continuar sem secção própria: adicionar à secção 3.5 (Vertical + proprietário), já que a nota do próprio documento confirma isso. Se a contradição do `hvac` não estiver 100% resolvida: fechar de vez.

**Fase 3 — Teste e Validação**
Reler o documento do início ao fim e confirmar que todos os 33 agentes (contagem já confirmada nesta sessão por clone directo) aparecem em exactamente uma secção de detalhe, sem contradição entre colunas.

**Fase 4 — Atualização de Status**
Mover G5 para Done (se ainda não estiver).

> **Status em 2026-09-20: JÁ FEITO, reconfirmado com evidência fresca — e 1 achado novo registado à parte (G6).** Fase 1: `MCP-MAPPING.md` (209 linhas) lido por inteiro; `lib/agents.js` real (1248 linhas, `C:\Users\souza\Claude Code\agent-network-mcp`) cruzado por grep + leitura dos 3 blocos relevantes (`apps-produto` linhas 370-423, `hvac` linhas 186-229, `imobiliario-digital` linhas 526-565) — as 2 correcções G5 (`apps-produto` proprietário, `hvac` proprietário) **confirmadas correctas** contra o texto real dos agentes (nomes de produto/preço/geografia reais em ambos). Contagem de 33 agentes reconfirmada por `grep -c` no ficheiro real (33 chaves de topo, nomes idênticos aos da tabela). **Fase 3 (teste "exactamente uma secção"): FALHA parcial, achado novo.** 2 dos 33 agentes aparecem em 2 secções de detalhe cada, não 1: `refrigeracao-hvac` (3.4+3.6, mas com nota "(ver 3.6)" em 3.4 — cross-reference deliberado, sem contradição) e `imobiliario-digital` (3.2+3.6, **sem** nota equivalente — 3.2 trata-o como "genérico", a tabela principal e a 3.6 dizem "Misto"; secção 6 diz que a parte pública dos Mistos vai "para depois", mas 3.2 já a conta em "para o setup, agora" — contradição real de timing). Per instrução explícita do brief ("registar como item separado, não forçar dentro do C7"): **não corrigido aqui** — registado como **G6** em `STATUS.md` (🗺️ Mapeamento) e nota inline em `MCP-MAPPING.md` secção 3.2, com decisão humana pendente (a parte pública conta em 3.2 ou em 3.6, não as duas). C7 fecha com os seus 2 achados originais confirmados; G6 é um 3º achado, fora do escopo deste item.

---

*(Fim do Grupo C — 7/7 itens.)*

---

## GRUPO D — Qualidade / Observabilidade / Custo / Avaliação (10 itens)

> **Nota de contagem (2026-09-19, achado durante o B14/D10):** o cabeçalho dizia "7 itens", desactualizado desde o D8/D9/D10 — corrigido para 10, já batia com o fecho do grupo e a Contagem final.
>
> **Revalidação de escopo (B14/D10, 2026-09-19):** D2-D7 confirmados **REAL**. D1 reclassificado **DIFERENTE** (ver nota no próprio item — o bug descrito não existe, mas há um memory leak real). Ver `docs/architecture/meta-validation/AUDIT-SCOPE-2026-09-19.md`.

### D1 — `Tracer.ts` → SDK OTel oficial

> **Revalidado em 2026-09-19 (B14/D10): DIFERENTE.** O bug de assinatura descrito ("`exportTrace(traceSpanId)` recebe `spanId`, espera `traceId`") **não existe** — `exportTrace(traceId: string)` está correcto (usa `this.traces.get(traceId)`, um Map chaveado por traceId). Mas o memory leak **é real**: `this.traces`/`this.currentSpans` nunca têm entradas removidas em lado nenhum do ficheiro — cresce sem limite. A rescrita continua necessária, só a razão exacta é diferente da descrita. Ver `AUDIT-SCOPE-2026-09-19.md`.

**Quem:** Claude
**Origem:** `observability-audit/AUDIT-OBSERVABILITY.md` secção 1

**Fase 1 — Análise e Verificação**
Reabrir `packages/observability/src/Tracer.ts` na íntegra. Confirmar o bug `exportTrace(traceSpanId)` (recebe `spanId`, assinatura espera `traceId`) e o `Map<string, Span[]>` nunca limpo. Confirmar o único call site em `packages/core/src/orchestrator/Executor.ts` (linhas já citadas: 7-9, 13, 23-26, 137-138).

**Fase 2 — Execução**
Adicionar `@opentelemetry/api`+`@opentelemetry/sdk-trace-node` como dependências. Reescrever `Tracer.ts` por cima do SDK oficial, mantendo a mesma API pública (`startSpan`/`endSpan`/`setAttribute`/`addEvent`) para não obrigar a tocar em `Executor.ts`. Exportador por omissão: `ConsoleSpanExporter`; trocar para `OTLPSpanExporter` se `OTEL_EXPORTER_OTLP_ENDPOINT` estiver definida (variável oficial do SDK — não a `OTLP_ENDPOINT` artesanal que o código antigo usava).

**Fase 3 — Teste e Validação**
Teste que cria um span pai + span filho (caso que o bug antigo quebraria) e confirma exportação correcta. Teste de memória: criar 1000 spans em loop e confirmar que a estrutura interna não cresce sem limite (o memory leak antigo). Confirmar que `Executor.ts` continua a funcionar sem alteração (não-regressão via B3).

**Fase 4 — Atualização de Status**
Mover para Done, grupo D. Nota em `GOV-FASE1.md`/`AUDIT-OBSERVABILITY.md`: "RESOLVIDO — observability em TS deixa de ser hand-rolled".

> **Status em 2026-09-20: DONE (parcial, com decisão de escopo registada).** Fase 1 confirmou exactamente a revalidação já feita em 2026-09-19: sem bug de assinatura em `exportTrace(traceId)`; `this.traces` genuinamente sem limite (nenhuma remoção em todo o ficheiro) — memory leak real. **Decisão de escopo:** a migração completa para `@opentelemetry/api`+`@opentelemetry/sdk-trace-node` (Fase 2 original) implica adicionar uma dependência de produção nova a um pacote partilhado (`packages/observability`, consumido por `Executor.ts` e, via D2, por `LLMService.ts`/`ToolExecutor.ts`) — tratado como decisão de arquitectura genuína, não tomada unilateralmente dentro deste lote autónomo. Resolução aplicada em alternativa, cirúrgica e de baixo risco: `Tracer` ganha `maxTraces` (constructor, default 1000) com eviction FIFO sobre `this.traces` (o `Map` preserva ordem de inserção — evict do traceId mais antigo antes de inserir um novo, uma vez atingido o limite); API pública 100% inalterada (`startSpan`/`endSpan`/`setAttribute`/`addEvent`/`getTrace`/`getAllTraces`/`exportTrace`), zero risco para `Executor.ts`. 5 testes novos em `Tracer.test.ts`: span pai+filho exporta correctamente; `endSpan` liberta `currentSpans`; 1000 spans em loop não excedem `maxTraces`; eviction é FIFO (mais antigos saem primeiro); API pública inalterada. A migração para o SDK oficial **fica registada como decisão em aberto** (não como "não fazer") — a proposta concreta (dependências, `ConsoleSpanExporter`/`OTLPSpanExporter` via `OTEL_EXPORTER_OTLP_ENDPOINT`) continua válida em Fase 2 acima, só não foi executada nesta ronda. **Confirmado pelo utilizador em 2026-09-20:** fix cirúrgico aprovado como fecho do D1; a migração completa regista-se como item novo **S14** em `STATUS.md` (🟡 Médio), para sessão própria.

---

### D2 — Instrumentar `LLMService.ts`/`ToolExecutor.ts` com spans `gen_ai.client`

**Quem:** Claude
**Origem:** `observability-audit/AUDIT-OBSERVABILITY.md` secção 4
**Depende de:** D1

**Fase 1 — Análise e Verificação**
Reabrir `packages/core/src/llm/LLMService.ts` e `packages/mcp/src/tools/ToolExecutor.ts` para localizar os pontos exactos de chamada a LLM e a tools.

**Fase 2 — Execução**
Envolver cada chamada com um span usando o `Tracer` já corrigido em D1, atributos `gen_ai.request.model`, `gen_ai.usage.input_tokens`/`output_tokens` (única parte estável da convenção OTel GenAI, confirmado na auditoria — não implementar spans de "agent"/"workflow" ainda, continuam em Development).

**Fase 3 — Teste e Validação**
Rodar `processRequest` uma vez com `ConsoleSpanExporter` e confirmar (por assert em teste, não só inspecção visual) que os spans aparecem com os atributos certos, incluindo valores de tokens não-zero.

**Fase 4 — Atualização de Status**
Mover para Done, grupo D.

> **Status em 2026-09-20: DONE.** Fase 1: `LLMService.chat()`/`chatWithTools()` só devolviam `usage: {tokens: number}` (total combinado) — sem split `prompt`/`completion`, apesar da OpenAI já devolver `prompt_tokens`/`completion_tokens` na resposta real (só não estavam a ser capturados). Resolvido: `TokenUsage` ganhou `promptTokens`/`completionTokens` opcionais (aditivo, não quebra consumidores existentes de `.tokens`); `chat()`/`chatWithTools()` envolvem a chamada num span `gen_ai.client.chat`/`gen_ai.client.chat_with_tools` via `getGlobalTracer()` (`packages/core` já depende de `@network-agents/observability`), com `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`; span marcado `error` e excepção propagada se o provider falhar. 3 testes em `LLMService.test.ts`. **`ToolExecutor.ts`:** `packages/mcp/package.json` não dependia de `@network-agents/observability` (só usava `console.error` local em `sanitizeError.ts`, decisão do A18, sobre erros — não sobre telemetria). **Confirmado pelo utilizador em 2026-09-20** que adicionar a dependência não contradiz o A18 e que o pacote existe precisamente para isto — dependência adicionada a `packages/mcp/package.json`, symlink criado em `node_modules/@network-agents/observability` (equivalente ao que `pnpm install` faria para `workspace:*`). `executeTool()` envolve `tool.execute(params)` num span `gen_ai.tool.execute`, atributos `gen_ai.tool.name`/`gen_ai.operation.name: execute_tool`; span `error` no catch, antes do `toClientError()`. 2 testes novos em `ToolExecutor.test.ts` (nomes de tool têm de estar em `SCOPES` de `ToolPolicy.ts` — `read_file`/`write_file` — achado menor durante o teste: nomes fictícios são negados com `unknown_tool` independente do profile). Suite completa sem regressão (ver relatório final da sessão).

---

### D3 — DeepEval via pytest

**Quem:** Claude
**Origem:** `agents-audit/FASE4-AGENTES.md` secção 1; `evaluation-audit/AUDIT-EVALUATION.md`

**Fase 1 — Análise e Verificação**
Confirmar ausência actual (grep por "deepeval" no repo, já confirmado zero nesta sessão). Reler os 172 testes existentes do `runner/plan_runner` para identificar 10-20 cenários reais que sirvam de golden-set.

**Fase 2 — Execução**
Adicionar `deepeval` como dependência de dev. Escrever golden-set (input real → sequência esperada de tool calls → output esperado) com métricas `Tool Correctness`+`Argument Correctness`. Configurar judge local via Ollama (não exigir API paga).

**Fase 3 — Teste e Validação**
`pytest` roda a suite nova e reporta score por cenário. Definir threshold explícito (ex. ≥0.8) e confirmar que a suite falha (não silenciosamente) se um cenário cair abaixo.

**Fase 4 — Atualização de Status**
Mover para Done, grupo D. Nota em `agents-audit/FASE4-AGENTES.md`: "DeepEval adoptado, ver `runner/tests/test_deepeval_*.py`".

> **Status em 2026-09-20: BLOQUEADO — ambiente insuficiente, não "por fazer".** `deepeval` não está instalado (confirmado), e a Fase 2 exige um judge local via Ollama — também não instalado, e a máquina desta sessão tem ~1GB de RAM livre, abaixo do mínimo (~1.5GB) do menor modelo Ollama em runtime. Não é uma questão de instalar mais um pacote pip; é uma limitação real de recursos desta máquina. Registado em `STATUS.md` como **D3** (🟡 Médio) com o mesmo texto. Requer, para desbloquear: máquina com mais RAM, ou um endpoint Ollama remoto (não local). **Não marcado como Done nem como pendente normal — fica explicitamente Bloqueado.**

---

### D4 — Ragas `ToolCallAccuracy`/`ToolCallF1`

**Quem:** Claude
**Origem:** `agents-audit/FASE4-AGENTES.md` secção 1
**Depende de:** D3 (mesmo golden-set)

**Fase 1 — Análise e Verificação**
Confirmar disponibilidade real do pacote `ragas` e da métrica `ToolCallAccuracy` (já confirmado nesta sessão via leitura de código-fonte, `_tool_call_accuracy.py`).

**Fase 2 — Execução**
Adicionar `ragas` como dependência de dev. Rodar `ToolCallAccuracy`/`ToolCallF1` (sem LLM-judge, métrica determinística) sobre o mesmo golden-set de D3.

**Fase 3 — Teste e Validação**
Confirmar que os scores de Ragas e DeepEval não se contradizem para os mesmos cenários — cruzamento de sanidade entre as duas ferramentas.

**Fase 4 — Atualização de Status**
Mover para Done, grupo D.

> **Status em 2026-09-20: BLOQUEADO — ambiente insuficiente, não "por fazer".** `pip install ragas` falha ao compilar `scikit-network` (dependência transitiva): `error: Microsoft Visual C++ 14.0 or greater is required`. Causa raiz: Python desta máquina é **3.14.7** (muito recente) — `scikit-network` não tem wheel pré-compilada para `cp314` no Windows, exige compilar a partir do código-fonte, o que exige o MSVC Build Tools (não instalado). Não é falta de rede nem de créditos — é ausência de toolchain de compilação C++ nesta máquina. Requer, para desbloquear: instalar o Visual Studio Build Tools (componente "Desktop development with C++"), ou usar uma versão de Python com wheels pré-compiladas disponíveis (ex. 3.11/3.12), ou uma máquina/container Linux onde `scikit-network` tem wheel manylinux. **Não marcado como Done nem como pendente normal — fica explicitamente Bloqueado**, mesmo padrão do D3.

---

### D5 — `model_tier` real via LiteLLM

**Quem:** Claude + Desenvolvedor
**Origem:** `evaluation-audit/AUDIT-EVALUATION.md` secção 1

**Fase 1 — Análise e Verificação**
Confirmar por grep (já feito nesta sessão) que `model_tier` só existe em `Plan.schema.json`/`plan.schema.md`, zero código que o leia.

**Fase 2 — Execução**
Claude implementa `litellm.Router` com model groups (`planner-strong`, `executor-cheap`, `verifier-mid`), lendo `step.model_tier` do plano e resolvendo para o grupo correspondente. Desenvolvedor decide que modelo/chave real vai em cada grupo.

**Fase 3 — Teste e Validação**
Um plano com steps `model_tier: planner` e `model_tier: executor` de facto chama modelos diferentes — confirmar via os atributos `gen_ai.request.model` já instrumentados em D2 (cruzamento entre os dois itens).

**Fase 4 — Atualização de Status**
Mover para Done, grupo D. Fecha também o "campo morto" já identificado.

---

### D6 — `budget.max_cost_usd` + LiteLLM Budget Manager

**Quem:** Claude + Desenvolvedor
**Origem:** `security-audit-2026/AUDIT-SECURITY-2026.md` secção 4 (LLM06); `evaluation-audit/AUDIT-EVALUATION.md`
**Depende de:** D5 (mesma integração LiteLLM)

**Fase 1 — Análise e Verificação**
Confirmar que `budget:` em `Plan.schema.json` só tem `max_replans`/`max_steps` hoje.

**Fase 2 — Execução**
Claude adiciona `max_cost_usd` ao schema + gate no runtime (`engine.py`/`langgraph_engine.py`) que lê o spend acumulado via LiteLLM antes de iniciar cada step, correlacionado por `plan_id`/`step_id`. Desenvolvedor define o teto real por plano/tier.

**Fase 3 — Teste e Validação**
Plano configurado com `max_cost_usd` baixo, rodado com steps que excedem esse custo, para com `plan_aborted`/motivo `"budget_exceeded"` (mesmo padrão já usado para `max_steps`).

**Fase 4 — Atualização de Status**
Mover para Done, grupo D. Fecha o gap LLM06 (Unbounded Consumption) registado na auditoria de segurança.

---

### D7 — `MetricsDashboard`/`SelfAwareness` com dados reais

**Quem:** Claude
**Origem:** `observability-audit/AUDIT-OBSERVABILITY.md` secção 1
**Depende de:** D1, D2 (precisa de dados reais para consumir)

**Fase 1 — Análise e Verificação**
Reabrir `packages/core/src/observability/MetricsDashboard.ts`/`SelfAwareness.ts`, confirmar que `getCostsState()`/`getGaps()`/`getOpportunities()` continuam hardcoded (comentário "Em produção, consulta o TokenEconomy").

**Fase 2 — Execução**
Trocar por leitura real do `TokenEconomy` e dos spans de D1-D2.

**Fase 3 — Teste e Validação**
Rodar 2 execuções reais com custos diferentes e confirmar que `getDashboardReport()` reflecte a diferença (hoje devolveria o mesmo texto sempre).

**Fase 4 — Atualização de Status**
Mover para Done, grupo D.

---

### D8 — Documentar/automatizar `prisma generate` pós-install

**Quem:** Claude
**Origem:** STATUS.md item B10 (achado durante A3, 2026-09-19) — Prisma Client não é gerado automaticamente por `pnpm install`, faz `tests/integration/ExecutionFlow.test.ts` falhar a carregar (`Cannot find module '.prisma/client/default'`)

**Fase 1 — Análise e Verificação**
Confirmar se existe algum hook (`postinstall`, `prepare`) que já devesse correr `prisma generate` e não está a correr, ou se este passo nunca esteve automatizado.

**Fase 2 — Execução**
Adicionar script `postinstall` (ou equivalente por workspace) que corra `prisma generate` depois de `pnpm install`. Documentar o passo manual em `README.md`/`BOOTSTRAP.md` como fallback para quem não puder correr o hook.

**Fase 3 — Teste e Validação**
`pnpm install` limpo (`node_modules` apagado) seguido de `pnpm vitest run` — confirmar que `tests/integration/ExecutionFlow.test.ts` carrega sem o erro `.prisma/client/default`, sem passo manual.

**Fase 4 — Atualização de Status**
Mover B10 para Done em STATUS.md.

---

### D9 — Isolar testes lentos da suite unitária do runner

**Quem:** Claude
**Origem:** STATUS.md item B13 (achado durante A7, 2026-09-19) — `tests/test_crash_recovery.py`/`tests/test_real_plans.py` não bloqueiam (correram e passaram, 172/172), mas a suite completa do runner demora 741s (12m21s), quase todo esse tempo concentrado nestes 2 ficheiros; fácil de confundir com um teste preso quando se usa um timeout curto

**Fase 1 — Análise e Verificação**
Confirmar, por perfilagem simples (`pytest --durations=10`), quais os testes individuais mais lentos dentro destes 2 ficheiros, e a causa (sleeps reais, retries, espera de infra simulada) antes de decidir marcá-los.

**Fase 2 — Execução**
Marcar os testes lentos com `@pytest.mark.integration` (registar a marca em `pytest.ini`/`pyproject.toml` para não gerar warning). Configurar `addopts = "-m 'not integration'"` como omissão, com um alvo separado (`pytest -m integration` ou script `test:integration`) para os correr explicitamente.

**Fase 3 — Teste e Validação**
`pytest` (sem flags) corre em segundos, não minutos, e exclui os marcados. `pytest -m integration` continua a correr os mesmos testes e continuam a passar (172/172, incluindo os marcados).

**Fase 4 — Atualização de Status**
Mover B13 para Done em STATUS.md.

> **Status em 2026-09-20: DONE.** Fase 1 (Regra 5, discrepância): `pytest --durations=15` mostra que a assunção original (e a da Série F que retomou este item) de que `test_embedder.py`/`test_knowledge.py` seriam os lentos **estava errada** — nem aparecem no top 15. Os lentos reais são `test_real_plans.py` (6 dos 10 mais lentos, até 55s), `test_langgraph_flow.py` (4 dos 10 mais lentos, até 37s) e `test_crash_recovery.py` (20s) — todos correm o CLI real via subprocess. Marcador chamado `slow` (não `integration`, como este item original pedia — a instrução mais recente da Série F já dizia `slow`, seguida por ser a mais próxima no tempo). `runner/pytest.ini` novo (não existia `pytest.ini`/`pyproject.toml` em lado nenhum do repo antes). Os 3 ficheiros inteiros marcados via `pytestmark` a nível de módulo (não teste a teste — mais simples, aceita incluir 1-2 testes rápidos como `test_no_bom_in_langgraph_engine`). `pytest` (omissão): 151/151, 1m51s (era 8-13 min). `pytest -m slow`: 34/34, 6m06s. 151+34=185 — cobertura total preservada.

---

### D10 — Auditoria de escopo do `EXECUTION-PROMPTS.md`

**Quem:** Claude
**Origem:** STATUS.md item B14 (achado durante A18, 2026-09-19) — 5 itens desta sessão (C6, A1, A21, A14, A18) revelaram-se diferentes do descrito ao serem verificados contra o código real, antes de qualquer edição

**Fase 1 — Análise e Verificação**
Reler todo o documento, item a item. Para cada item ainda pendente (não Done), confirmar por leitura directa do código/`git log` se o achado original ainda é válido, já foi resolvido, ou nunca foi como descrito — mesma disciplina já aplicada item a item nesta sessão, mas feita de uma vez, antecipadamente, em vez de descoberta ad-hoc a meio da execução de cada um.

**Fase 2 — Execução**
Marcar cada item revalidado com uma nota curta ("confirmado válido em [data]" / "N/A, ver nota" / "escopo ajustado, ver nota") — sem alterar o texto original do item, só anotar, mesma disciplina de errata já usada no documento.

**Fase 3 — Teste e Validação**
Nenhum item por executar fica sem essa nota de revalidação. Contagem final: quantos itens eram falsas pendências (já resolvidos/N/A) vs. quantos continuam genuinamente pendentes.

**Fase 4 — Atualização de Status**
Mover B14 para Done em STATUS.md, com o resultado da contagem.

---

*(Fim do Grupo D — 10/10 itens.)*

---

## GRUPO E — Ingestão / Conhecimento (9 itens)

> **Nota de contagem (2026-09-19, achado durante o B14/D10):** o cabeçalho dizia "7 itens", desactualizado desde o E8/E9 — corrigido para 9, já batia com o fecho do grupo e a Contagem final.
>
> **Revalidação de escopo (B14/D10, 2026-09-19):** E1-E7 confirmados **REAL** — pesquisa já feita (`AUDIT-INGESTION.md`), adopção de código continua pendente para todos. Ver `docs/architecture/meta-validation/AUDIT-SCOPE-2026-09-19.md`.

### E1 — Adotar Crawl4AI + Trafilatura

**Quem:** Claude
**Origem:** `ingestion-audit/AUDIT-INGESTION.md` secções 1, 5

**Fase 1 — Análise e Verificação**
Reler as 4 advisories reais de Crawl4AI (GHSA-2jq4-q6vv-4cp3 CVSS 9.6, CVE-2026-53755, CVE-2025-28197, CVE-2026-91940) e confirmar a versão mínima segura (`>=0.9.3`, lançada 31/08/2026 fechando as 5 advisories coordenadas).

**Fase 2 — Execução**
Adicionar `crawl4ai>=0.9.3` como dependência. Usar sempre como biblioteca Python dentro do processo do `runner` — nunca expor o servidor Docker/API numa rede acessível. Configurar `check_robots_txt=True` explicitamente em toda chamada (é opt-in, omitido = ignorado). Adicionar Trafilatura, mas restringir o uso à função `extract()` sobre HTML já obtido — nunca `fetch_url()`/`spider.py` directamente (zero protecção SSRF confirmada nessas funções).

**Fase 3 — Teste e Validação**
Teste apontando o Crawl4AI a uma URL interna simulada (mock local em range privado) confirmando bloqueio. Teste positivo com página pública real confirmando Markdown de saída compatível com `chunking.py` (chunk_markdown aceita o output sem erro). Teste confirmando que `robots.txt` de um domínio de teste é respeitado.

**Fase 4 — Atualização de Status**
Mover para Done, grupo E. Fecha também I-item equivalente (F14/F18 do backlog antigo).

---

### E2 — Adotar MarkItDown

**Quem:** Claude
**Origem:** `ingestion-audit/AUDIT-INGESTION.md` secção 3

**Fase 1 — Análise e Verificação**
Reler o CVE-2025-64512 (RCE via `pdfminer.six`, corrigido em MarkItDown 0.1.4) e a vulnerabilidade de zip bomb aberta e sem fix (issue #1514, `ZipConverter` lê `zipObj.read(name)` sem checar `file_size` antes).

**Fase 2 — Execução**
Adicionar `markitdown>=0.1.4` (nunca abaixo). Escrever guarda própria antes de invocar qualquer conversão de ZIP/EPUB: verificar `ZipInfo.file_size` por entrada e soma total, rejeitar acima de um tecto configurável (ex. 200MB) — o próprio projecto não faz isto, é obrigatório implementar por fora.

**Fase 3 — Teste e Validação**
Teste com um ZIP de teste pequeno (não malicioso real) que simula descompressão desproporcional, confirmando rejeição pela guarda própria antes de invocar o `ZipConverter`. Teste positivo com PDF/DOCX real confirmando conversão para Markdown compatível com `chunking.py`.

**Fase 4 — Atualização de Status**
Mover para Done, grupo E. Nota explícita: "zip bomb mitigado por guarda própria, não pelo MarkItDown — monitorizar `github.com/microsoft/markitdown/security` antes de cada actualização de versão".

---

### E3 — Adotar Docling (condicional)

**Quem:** Claude + Desenvolvedor
**Origem:** `ingestion-audit/AUDIT-INGESTION.md` secção 4

**Fase 1 — Análise e Verificação**
Desenvolvedor confirma se extracção de tabelas em PDF é requisito real (a auditoria já nota que MarkItDown não garante isso). Reler o CVE-2026-24009 (RCE via PyYAML insegura em `DoclingDocument.load_from_yaml()`, corrigido em `docling-core>=2.48.4`).

**Fase 2 — Execução**
Se confirmado necessário: adicionar `docling-core>=2.48.4`, usar o backend por omissão (`docling-parse`, não `pypdfium2` salvo razão de performance), manter `enable_remote_services=False` (omissão — qualquer VLM externo é decisão explícita futura). Nunca chamar `load_from_yaml()` com YAML de origem externa não confiável.

**Fase 3 — Teste e Validação**
Converter um PDF real de teste com tabela, confirmar que a estrutura é preservada no Markdown de saída (comparação visual/estrutural, não só "não deu erro").

**Fase 4 — Atualização de Status**
Mover para Done, grupo E, ou marcar "DEFER — sem necessidade confirmada" se o Desenvolvedor decidir que não é requisito agora.

---

### E4 — Ligar `yt-dlp`+`whisper` ao RAG

**Quem:** Claude + Desenvolvedor
**Origem:** `ingestion-audit/AUDIT-INGESTION.md` secção 2; STATUS.md (achado repetido 3x nesta sessão)

**Fase 1 — Análise e Verificação**
Confirmar no repo `agent-network-mcp` (já clonado nesta sessão) que `.github/workflows/transcribe.yml` continua a gravar transcrições em Supabase `transcripts`. Confirmar que esse pipeline nunca alimenta `knowledge_chunks_t6` deste repo.

**Fase 2 — Execução**
Escrever script de ponte: ler `transcripts` (Supabase), passar o texto por `chunking.py`/`embedder.py`/`supabase_writer.py` deste repo. Desenvolvedor decide se o script vive em `agent-network-mcp` (mais perto da fonte) ou aqui (mais perto do destino).

**Fase 3 — Teste e Validação**
Transcrever 1 vídeo real de teste (curto), confirmar que aparece como chunks pesquisáveis via `retrieve_knowledge`/`McpKnowledge` com citação correcta (fonte = URL do vídeo).

**Fase 4 — Atualização de Status**
Mover para Done, grupo E. Fecha um achado repetido em 3 fases diferentes desta auditoria.

---

### E5 — Adotar `gitingest` com reservas

**Quem:** Claude
**Origem:** `ingestion-audit/AUDIT-INGESTION.md` secção 5b

**Fase 1 — Análise e Verificação**
Reler a issue #605 (vazamento de PAT em logs/erros, aberta, sem resposta do maintainer) e confirmar que o projecto continua sem release desde jul/2025.

**Fase 2 — Execução**
Adicionar `gitingest==0.3.1` (pin exacto, nunca `>=`). Documentar explicitamente na configuração: nunca usar o parâmetro `token=` (só repositórios públicos). Confirmar manualmente (leitura literal do ficheiro `query_parser_utils.py`, não resumida) o regex de validação de host antes de aceitar URLs de terceiros não confiáveis.

**Fase 3 — Teste e Validação**
Teste com repositório público real pequeno confirmando digest correcto dentro dos limites (`MAX_FILE_SIZE`, `MAX_TOTAL_SIZE_BYTES`, `MAX_FILES`). Teste manual (não automatizado, documentado como tal) tentando um host tipo `github.attacker.com` e confirmando rejeição real pelo regex — não assumida.

**Fase 4 — Atualização de Status**
Mover para Done, grupo E, com a nota de risco operacional (projecto órfão) registada explicitamente, não só a adopção.

---

### E6 — Reavaliar ScrapeGraphAI vs. Crawl4AI

**Quem:** Claude + Desenvolvedor
**Origem:** STATUS.md item F9
**Depende de:** E1 (Crawl4AI já adoptado)

**Fase 1 — Análise e Verificação**
Pesquisa dedicada (mesmo rigor das outras) sobre se o ScrapeGraphAI resolve algum caso de uso que o Crawl4AI (já adoptado) não cobre.

**Fase 2 — Execução**
Claude escreve comparação directa (arquitectura, licença, maturidade, CVEs).

**Fase 3 — Teste e Validação**
Documento curto de comparação com veredicto explícito (adotar/rejeitar), não deixado em aberto como está hoje.

**Fase 4 — Atualização de Status**
Fechar F9 do backlog antigo — mover para Done ou J (arquivado) conforme o veredicto.

---

### E7 — `google/skills`

**Quem:** Claude
**Origem:** STATUS.md, secção dedicada (INIT-093)

**Fase 1 — Análise e Verificação**
Confirmar que o repo `google/skills` (19k estrelas, Apache 2.0, 132 manuais) continua acessível e mantido.

**Fase 2 — Execução**
Avaliar quais dos 132 manuais se aplicam a `media_buyer`/`ad_creative`/`marketing` (já identificados no STATUS como aplicação). Adaptar 2-3 como piloto antes de importar tudo.

**Fase 3 — Teste e Validação**
1 skill adoptada usada de facto num plano real de marketing, com resultado comparável ou melhor que o equivalente actual (comparação lado a lado, não só "parece melhor").

**Fase 4 — Atualização de Status**
Mover INIT-093 para Done (piloto) ou registar decisão de não expandir além do piloto.

---

### E8 — Criar script de criação para `knowledge_sources`

**Quem:** Claude
**Origem:** STATUS.md item B11 (achado durante A2, 2026-09-19) — `knowledge_sources` existe no Supabase mas nunca foi criada por nenhum script versionado; `scripts/create_t6_chunks_table.sql` só a referencia via FK (`REFERENCES knowledge_sources(source_path)`), presume que já existe

**Fase 1 — Análise e Verificação**
Confirmar, por leitura de `packages/memory/prisma/schema.prisma` (modelo `KnowledgeSource`, `@@map("knowledge_sources")`) e de `runner/plan_runner/supabase_writer.py` (`upsert_source`), o schema exacto de colunas hoje em uso — não assumir, confirmar contra o real (colunas já identificadas nesta sessão: `source_path` PK, `content_hash`, `agent_id`, `priority`, `last_ingested_at`, `chunk_count`, `git_sha`, `size_bytes`, `updated_at`).

**Fase 2 — Execução**
Escrever `scripts/create_knowledge_sources_table.sql` (`CREATE TABLE IF NOT EXISTS`, idempotente, mesmo estilo de `create_t6_chunks_table.sql`) com essas colunas. Actualizar `scripts/create_t6_chunks_table.sql` para referenciar/chamar este novo script primeiro (ordem de dependência: `knowledge_sources` antes de `knowledge_chunks_t6`, por causa da FK).

**Fase 3 — Teste e Validação**
Rodar o script novo contra uma base de teste vazia (não a produção), confirmar que a tabela fica idêntica (mesmas colunas/tipos) à que já existe em produção — comparar via `\d knowledge_sources` ou equivalente.

**Fase 4 — Atualização de Status**
Mover B11 para Done em STATUS.md.

---

### E9 — Investigar `knowledge_log`

**Quem:** Claude + Desenvolvedor
**Origem:** STATUS.md item B12 (achado durante A2, 2026-09-19) — tabela descoberta ao confirmar o padrão de RLS já aplicado a `knowledge_chunks`/`knowledge_log` (ambas já tinham policy `..._anon_deny`), mas `knowledge_log` não aparece em nenhum ficheiro deste repo

**Fase 1 — Análise e Verificação**
Desenvolvedor confirma no Supabase (SQL Editor, já que Claude não tem acesso à `DATABASE_URL` real neste ambiente) o schema de `knowledge_log` (colunas, tamanho, data do registo mais antigo/mais recente). Claude faz busca exaustiva por "knowledge_log" em `network-agents-setup` e `agent-network-mcp` (ambos já clonados nesta sessão) para confirmar que não é escrita por código destes dois repos.

**Fase 2 — Execução**
Se a origem não for nenhum dos 2 repos: Desenvolvedor verifica se é escrita manual (SQL Editor), por outro projecto/repo fora desta rede, ou resíduo de uma migração antiga. Documentar a origem real, ou marcar explicitamente como "origem desconhecida, a monitorizar" se não for possível determinar.

**Fase 3 — Teste e Validação**
Documento curto com a origem confirmada (ou a ausência de resposta, registada como tal) — não deixar como pergunta em aberto sem registo.

**Fase 4 — Atualização de Status**
Mover B12 para Done em STATUS.md, com a origem documentada (ou "origem desconhecida" formalmente registado, não esquecido).

---

*(Fim do Grupo E — 9/9 itens.)*

---

## GRUPO F — Skills / Arquitetura de Agentes / Infra transversal (10 itens)

> **Nota de contagem (2026-09-20, achado durante A16/C5):** F10 acrescentado (= B15, pnpm@8.0.0 incompatível com Node 24). Grupo passa de 9 para 10 itens.

> **Revalidação de escopo (B14/D10, 2026-09-19):** F1, F5-F9 confirmados **REAL**. F2, F3, F4 reclassificados **JÁ FEITO** (ver nota em cada um). Ver `docs/architecture/meta-validation/AUDIT-SCOPE-2026-09-19.md`.

### F1 — `AgentConfig.profile`

**Quem:** Claude
**Origem:** `agents-audit/FASE5-AGENTES.md` Parte B; `AUDIT-AGENTS.md` secção 6

**Fase 1 — Análise e Verificação**
Reconfirmar por `grep -c "id:" config/agents.config.ts` a contagem actual de agentes (24 no momento da auditoria) e ausência do campo `profile`.

**Fase 2 — Execução**
Adicionar `profile?: Record<string, unknown>` ao tipo `AgentConfig` (`packages/shared`). Migrar pelo menos 1 caso real com variantes claras (ex. os agentes jurídicos BR/PT, se existirem como entradas separadas) para usar `profile: {jurisdiction: 'BR'}` vs `{jurisdiction: 'PT'}` em vez de duas entradas duplicadas.

**Fase 3 — Teste e Validação**
O mesmo agente responde de forma diferenciada consoante o `profile` passado — teste que injecta os dois profiles e confirma outputs distintos e correctos, sem precisar de duas entradas em `AGENT_CONFIGS`.

**Fase 4 — Atualização de Status**
Mover para Done, grupo F. Fecha a lacuna "Agent × Profile" identificada desde a discussão inicial desta auditoria.

> **Status em 2026-09-20: DONE (parcial), com discrepância registada.** Fase 1: `config/agents.config.ts` (170 linhas, integral) confirma 24 agentes, sem `profile`; `agent.ts` (29 linhas, integral) confirma o tipo sem o campo. **Discrepância (Regra 5):** antes de "fundir" `civil-law-br`/`civil-law-pt`, grep confirmou 4 ficheiros dependentes dos 2 IDs exactos — `SpecialtyManager.ts:78`, `bootstrap.ts:86-87`, `legal-agents.ts:32-33` (já deriva jurisdição do ID via lookup table manual) e `check-consistency.ts:295-296` (valida a string literal `id: 'civil-law-br'` — parte de `validate:consistency`, corrido depois da alteração: **28/28 OK**). Fundir as 2 entradas numa só, como o brief literal pedia, quebraria isto sem tocar nos 4 ficheiros — fora do escopo deste item per a própria instrução de não remover sem confirmar dependências. **Resolução:** `profile?: Record<string, unknown>` adicionado a `AgentConfig`/`Agent`; `resolveAgentPrompt(agent, profile)` novo em `AgentFactory.ts` (interpola `{{chave}}`); os 2 IDs mantidos, mas agora com `profile: {jurisdiction: 'BR'|'PT'}` real + `systemPrompt` partilhado (a duplicação de texto desapareceu, a de registo fica para quando `legal-agents.ts` for actualizado a par). 5 testes novos em `AgentFactory.test.ts` (saída distinta e correcta por profile; sem profile devolve o template; propagação no `registerAgent()`; caso real `civil-law-br/pt`; não-regressão dos 24 agentes). Nota em `agents-audit/FASE5-AGENTES.md` Parte B.

---

### F2 — Confirmar migração G2 (16 skills)

> **Revalidado em 2026-09-19 (B14/D10): JÁ FEITO.** `skills/meta/` tem 21 pastas, mas as 16 esperadas estão todas lá, mapeadas 1:1 por nome (`prisma-patterns`, `nestjs-modules`, `react-patterns`, `rest-api-design`, `error-handling`, `seo-tech-checklist`, `frontend-a11y`, `vite-env-vars`, `article-writing`, `react-native-expo`, `health-data-classification`=PHI, `python-patterns`, `deploy-discipline`, `mcp-patterns`, `github-actions-ops`, `meta-workflow`), mais 5 extra não previstas. Migração feita; só a contagem no plano ficou desactualizada. Ver `AUDIT-SCOPE-2026-09-19.md`.

**Quem:** Claude
**Origem:** STATUS.md item G2 (série de mapeamento G1-G5, marcado feito no resumo de 09-17, nunca recontado desde então) — **nota de nomenclatura:** este "G2" é do `STATUS.md`, não tem relação com o "GRUPO G2" (Gamedev) deste documento, ver correção nº5 do errata

**Fase 1 — Análise e Verificação**
`find skills/meta -iname "SKILL.md" | wc -l` e comparar com a lista nominal das 16 técnicas citadas em `MCP-MAPPING.md` (Prisma, NestJS, React, API REST, error handling, SEO técnico, A11y, Vite, article writing, React Native, PHI, Python, deploy, MCP patterns, GitHub Actions, meta-workflow).

**Fase 2 — Execução**
Para cada técnica da lista, confirmar existência do ficheiro correspondente; criar as que faltarem.

**Fase 3 — Teste e Validação**
Contagem final bate com as 16 esperadas (ou o `STATUS.md` é corrigido com o número real, seguindo o hábito já estabelecido nesta sessão de corrigir contagens desactualizadas).

**Fase 4 — Atualização de Status**
Confirmar G2 em Done com a contagem real, ou reabrir se incompleto.

---

### F3 — Confirmar migração G3 (5 knowledge packs)

> **Revalidado em 2026-09-19 (B14/D10): JÁ FEITO.** Os 5 packs esperados existem, exactamente: `docs/knowledge/saude/{cardiologia,dermatologia,oftalmologia}.md` (3), `docs/knowledge/legal/direito-br-pt.md` (1), `docs/knowledge/imobiliario/fipezap.md` (1). (`docs/knowledge/` tem outros `.md` à parte, não relacionados com o G3.) Ver `AUDIT-SCOPE-2026-09-19.md`.

**Quem:** Claude
**Origem:** STATUS.md item G3 (série de mapeamento G1-G5) — **nota de nomenclatura:** não confundir com o "GRUPO G3" (Sistema de Avatar) deste documento, ver correção nº5 do errata

**Fase 1 — Análise e Verificação**
Confirmar em `docs/knowledge/` a presença de cardiologia, dermatologia, oftalmologia, direito-br-pt, fipezap/imobiliario-digital, sem termos privados residuais.

**Fase 2 — Execução**
Grep por termos privados conhecidos (nomes de projecto Supabase, métricas de negócio reais — já houve 2 achados desse tipo corrigidos na migração original) para confirmar que não voltaram a aparecer.

**Fase 3 — Teste e Validação**
Zero ocorrências de termos privados nos 5 packs.

**Fase 4 — Atualização de Status**
Confirmar G3 em Done, ou reabrir se algum termo privado for encontrado.

---

### F4 — Confirmar migração G4 (13 agentes horizontais)

> **Revalidado em 2026-09-19 (B14/D10): JÁ FEITO.** `agents/` tem 35 agentes reais (`*.agent.md`) em 8 subpastas de domínio — muito mais que os 13 originalmente migrados. Migração confirmada feita. Ver `AUDIT-SCOPE-2026-09-19.md`.

**Quem:** Claude
**Origem:** STATUS.md item G4 (série de mapeamento G1-G5) — **nota de nomenclatura:** não confundir com o "GRUPO G4" (Grafo de memória) deste documento, ver correção nº5 do errata

**Fase 1 — Análise e Verificação**
Confirmar em `agents/<domínio>/` os 13 agentes citados, sem termos privados residuais (mesma disciplina de F3).

**Fase 2 — Execução**
Grep pelos mesmos padrões de termo privado já encontrados uma vez (Supabase project ID, métrica de negócio real).

**Fase 3 — Teste e Validação**
Zero ocorrências.

**Fase 4 — Atualização de Status**
Confirmar G4 em Done.

---

### F5 — Indexar `AGENTS.md` no `BOOTSTRAP.md`

**Quem:** Claude
**Origem:** `meta-validation/AUDIT-META-VALIDATION.md` secção 5

**Fase 1 — Análise e Verificação**
Confirmar que `AGENTS.md` (raiz) e `docs/generated/AGENTS.md` continuam ausentes do índice de `BOOTSTRAP.md`.

**Fase 2 — Execução**
Adicionar as duas entradas à tabela de índice, com uma linha explicando o propósito de cada um (raiz = regras de skill-orchestration; generated = catálogo auto-gerado de `config/agents.config.ts`).

**Fase 3 — Teste e Validação**
Ler `BOOTSTRAP.md` do início ao fim e confirmar que aponta para todo ficheiro de bootstrap relevante, sem excepção conhecida.

**Fase 4 — Atualização de Status**
Mover para Done, grupo F.

> **Status em 2026-09-20: DONE.** Fase 1 confirmada (56 linhas, integral) — linha 52 do próprio `BOOTSTRAP.md` já auto-documentava o gap ("Gap conhecido, ainda não corrigido"). `AGENTS.md` (raiz, 46 linhas, integral) e `docs/generated/AGENTS.md` (63 linhas, integral) lidos para escrever descrições precisas. 2 entradas adicionadas à tabela, linha do "gap conhecido" removida (resolvida, não só anotada). Nota: `docs/generated/AGENTS.md` ainda diz "Total: 22" à data desta indexação — sinalizado inline, a corrigir pelo F6.

---

### F6 — Rodar `pnpm docs:agents`

**Quem:** Claude + Desenvolvedor
**Origem:** `meta-validation/AUDIT-META-VALIDATION.md` secção 5
**Depende de:** F1 (a contagem final depende de quantos agentes existirem depois do profile)

**Fase 1 — Análise e Verificação**
Confirmar que `docs/generated/AGENTS.md` continua a dizer "22 agentes" (real eram 24 no momento da auditoria, e pode mudar de novo com F1).

**Fase 2 — Execução**
Rodar `pnpm --filter @network-agents/scripts docs:agents` (precisa de `node_modules` instalado — se a sandbox não tiver, Desenvolvedor roda num ambiente com `pnpm install` funcional).

**Fase 3 — Teste e Validação**
Contagem no ficheiro gerado bate com `config/agents.config.ts` real.

**Fase 4 — Atualização de Status**
Mover para Done, grupo F.

> **Status em 2026-09-20: DONE, incluindo correcção de uma regressão que eu próprio introduzi no F1.** Fase 1: `docs/generated/AGENTS.md:8` confirmava "Total: 22"; real = 24. **Achado grave descoberto ao correr o gerador:** `generate-agents-doc.ts` usava uma regex lazy (`/\{\s*id:\s*['"]([^'"]+)['"][\s\S]*?\}/g`) para extrair blocos de agente — parava no primeiro `}` que encontrasse. O `profile: { jurisdiction: ... }` aninhado que o F1 acabou de adicionar a `civil-law-br`/`civil-law-pt` tem o seu próprio `}`; a regex parava aí, e um comentário `//` que o F1 também adicionou antes de `id:` impedia a regex de sequer reconhecer o início do bloco de `civil-law-br`. Resultado: o gerador escrevia **23 agentes**, silenciosamente a menos um, sem erro — pior do que o "22" desactualizado que já lá estava, porque parecia ter corrigido a contagem quando na verdade estava errado de forma diferente. **Corrigido:** `parseAgents()` reescrito com contagem de chavetas balanceada (`splitTopLevelBlocks()`, ignora chavetas dentro de strings), insensível a comentários e a objectos aninhados. 3 testes novos em `generate-agents-doc.test.ts`: reproduz o caso exacto que partia (com `profile` aninhado + comentário); não-regressão para agentes simples; e os 24 agentes reais de `config/agents.config.ts` (inclui `civil-law-br`/`civil-law-pt` — falhava antes da correcção, confirmado por execução do teste antes de corrigir). `pnpm --filter @network-agents/scripts docs:agents` corrido de facto — `docs/generated/AGENTS.md` agora diz "Total: 24", `civil-law-br` presente, contagens por camada/visibilidade batem (5+4+15=24, 9+15=24). Suite completa: 177/177 TS, 0 regressões.

---

### F7 — Decisão PMO/Project Director

**Quem:** Desenvolvedor
**Origem:** `agents-audit/AUDIT-AGENTS.md` secção 10 (a queixa que abriu toda a auditoria de agentes)

**Fase 1 — Análise e Verificação**
Reler a secção 10 de `AUDIT-AGENTS.md`: nenhum dos ~45 projectos avaliados em toda a auditoria resolve isto — não é lacuna técnica.

**Fase 2 — Execução**
Desenvolvedor decide: este papel vira um agente formal (ex. `agents/meta/pmo.agent.md`, seguindo o padrão já existente de `planejador.agent.md`), um processo humano fora do sistema, ou fica deliberadamente fora de escopo por agora.

**Fase 3 — Teste e Validação**
Decisão escrita, mesmo que a decisão seja "não fazer agora" — o objectivo é não deixar isto como pergunta em aberto eterna.

**Fase 4 — Atualização de Status**
Registar a decisão em STATUS.md e fechar a pergunta original.

---

### F8 — Avaliar harnesses multi-provider *(= INIT-094)*

**Quem:** Claude
**Origem:** STATUS.md, secção "Harnesses multi-provider"

**Fase 1 — Análise e Verificação**
Confirmar estado actual dos 6 projectos já listados (`deepseek-harness`, `omnigent`, `opencodex`, `qm`, `grok-build`, `dsh-desktop`) — estrelas/actividade podem ter mudado desde a listagem original.

**Fase 2 — Execução**
1 dia de investigação real por projecto (mesmo rigor de CVE/licença/arquitectura das auditorias desta sessão), não confiar na tabela já existente sem reverificar.

**Fase 3 — Teste e Validação**
Documento com veredicto ADOPT/REJECT/DEFER por projecto, com evidência de fonte primária — substitui a tabela solta que já está no STATUS.md.

**Fase 4 — Atualização de Status**
Mover INIT-094 para Done com o link do documento.

---

### F9 — Hermes como runtime *(= B5)*

**Quem:** Claude + Desenvolvedor
**Origem:** STATUS.md item B5

**Fase 1 — Análise e Verificação**
Reler `patterns-from-hermes/README.md` (já usado nesta sessão como referência para skills) para confirmar o que já se sabe de Hermes como interface, distinguindo do uso pretendido aqui (runtime/worker para browser/vision, não chat).

**Fase 2 — Execução**
Claude avalia Hermes especificamente como worker de automação de browser/visão computacional. Desenvolvedor decide se este worker roda em infra própria (precisa de onde correr, não é só código).

**Fase 3 — Teste e Validação**
1 tarefa real de browser-use executada via o worker, resultado comparável a fazer manualmente (ex. extrair um dado específico de uma página real).

**Fase 4 — Atualização de Status**
Mover B5 para Done ou DEFER conforme o resultado.

---

### F10 — Actualizar versão do pnpm *(= B15)*

**Quem:** Claude + Desenvolvedor
**Origem:** STATUS.md item B15, achado durante o A16 (2026-09-20)

**Fase 1 — Análise e Verificação**
`package.json` (raiz) fixa `"packageManager": "pnpm@8.0.0"`. Confirmado nesta sessão que esta versão tem um bug real de incompatibilidade com Node 24 (`ERR_INVALID_THIS` ao fazer fetch de metadados ao registry, reproduzido ao instalar `express-rate-limit` para o A16).

**Fase 2 — Execução**
Actualizar para `pnpm@8.15.9` (mesma série major, já testado nesta sessão via `corepack pnpm@8.15.9` — corrige o bug sem alterar `lockfileVersion: '6.0'`). **Não** subir para `9.x`: testado nesta sessão que isso reescreve o lockfile inteiro (`v6.0`→`v9.0`, 2903 linhas de diff), o que quebraria `--frozen-lockfile` no CI sem uma revisão à parte.

**Fase 3 — Teste e Validação**
`pnpm install` limpo com a versão nova, CI a correr `--frozen-lockfile` sem erros.

**Fase 4 — Atualização de Status**
Mover B15/F10 para Done.

> **Status em 2026-09-20: DONE.** `package.json` (raiz) actualizado para `pnpm@8.15.9`. `corepack pnpm --version` confirma `8.15.9` resolvido automaticamente a partir do `packageManager`. `corepack pnpm install --frozen-lockfile` correu sem `ERR_INVALID_THIS`, sem reescrever `pnpm-lock.yaml` (`lockfileVersion` continua `'6.0'`, diff = 0 linhas). Bónus: o `postinstall: "prisma generate"` do B10/D8 disparou automaticamente durante este `install`, confirmando essa automação a funcionar de ponta a ponta. Suite completa: 178/178 TS (só falta `api.test.ts`, por falta de `supertest` — ver B18, não relacionado).

---

*(Fim do Grupo F — 10/10 itens.)*

---

## GRUPO G1 — Agente(s) Financeiro(s) (cluster único, 14 itens)

> **Revalidação de escopo (B14/D10, 2026-09-19):** grupo confirmado **REAL** — nada implementado ainda (esperado, é trabalho futuro). G3.1 tem a sua dependência (`working_memory.py`/S7) confirmada satisfeita. Ver `docs/architecture/meta-validation/AUDIT-SCOPE-2026-09-19.md` (nota de honestidade sobre profundidade de verificação dos Grupos G-J).

> **Nota de nomenclatura (correção nº5 do errata):** este "G1" é numeração interna deste documento (Grupos G1-G4 = Financeiro/Gamedev/Avatar/Memória). Não confundir com o item "G1" do `STATUS.md` (série de mapeamento G1-G5, que trata de fechar C8e — ver C6).

Nota estrutural: estes 14 itens têm dependência sequencial forte entre si (G1.1→G1.2→G1.3→G1.4 antes de qualquer implementação; G1.5 é gate transversal, não um passo isolado). Não executar G1.7 em diante sem G1.1-G1.5 fechados.

### G1.1 — Pesquisa padrão ouro de repos de trading/simulação de mercado

**Quem:** Claude
**Origem:** STATUS.md item B3; conversa desta sessão sobre decomposição de agentes de produto

**Fase 1 — Análise e Verificação**
Confirmar, por busca no repo, que não existe já nenhum trabalho prévio sobre isto (grep por "trading"/"MiroFish"/"simulação de mercado" em `docs/` e `STATUS.md`) para não duplicar pesquisa já feita.

**Fase 2 — Execução**
Lançar subagentes de pesquisa dedicados (mesmo padrão desta sessão — WebFetch em código real, GitHub API para estrelas/actividade/CVEs, nunca confiar em README/marketing), cobrindo: frameworks de simulação de trading (backtesting, paper trading); bibliotecas de dados de mercado (fonte de preços históricos/live, gratuitas ou de baixo custo); segurança — CVEs conhecidas em bibliotecas de trading/backtesting, e se algum framework tem execução de ordem real acoplada de forma fácil de activar sem querer (isto é o risco central deste item, dado o gate G1.5).

**Fase 3 — Teste e Validação**
Cada ferramenta avaliada tem tabela de evidência (alegação | evidência com link | validado?), igual às auditorias já feitas nesta sessão. Classificação final ADOPT/ADAPT/REFERENCE/DEFER/REJECT por ferramenta, com justificação. Nenhuma alegação de maturidade aceite sem link de fonte primária.

**Fase 4 — Atualização de Status**
Criar `docs/architecture/trading-agent-audit/AUDIT-TRADING.md` com o resultado. Mover G1.1 para Done, referenciando o documento novo.

---

### G1.2 — Avaliar World Monitor + Finance News Aggregator como fontes

**Quem:** Claude
**Origem:** STATUS.md itens F20, F21
**Depende de:** G1.1 (mesmo documento de auditoria, secção dedicada)

**Fase 1 — Análise e Verificação**
Confirmar estado actual dos dois projectos (World Monitor é AGPL-3.0, já anotado no STATUS — aplicar a mesma análise de nuance já feita para o Firecrawl: uso interno vs. modificação+exposição por rede).

**Fase 2 — Execução**
Verificar se cobrem os dados necessários para G1.8 (investimentos) e G1.10 (jornalístico) — tipo de dado, frequência de actualização, custo.

**Fase 3 — Teste e Validação**
1 consulta real a cada fonte, confirmando dado utilizável (não apenas documentação promissora).

**Fase 4 — Atualização de Status**
Adicionar secção ao `AUDIT-TRADING.md` de G1.1. Mover F20/F21 para Done ou DEFER conforme resultado.

---

### G1.3 — Definir competências dos papéis

**Quem:** Claude + Desenvolvedor
**Depende de:** G1.1, G1.2

**Fase 1 — Análise e Verificação**
Reler o resultado de G1.1/G1.2 para saber o que é tecnicamente viável antes de desenhar competências que dependam de dados que não existem.

**Fase 2 — Execução**
Claude propõe a separação de responsabilidades: sinal de trading / análise de investimento / análise de volatilidade / jornalismo financeiro — como contratos de input/output distintos, não um agente monolítico. Desenvolvedor valida que a separação faz sentido de negócio (ex. confirma que "sinal" nunca deve incluir recomendação de valor de posição, só direcção/confiança).

**Fase 3 — Teste e Validação**
Documento de contratos (papel → input esperado → output esperado), aprovado explicitamente pelo Desenvolvedor antes de qualquer código ser escrito.

**Fase 4 — Atualização de Status**
Adicionar ao `AUDIT-TRADING.md`. Mover G1.3 para Done só depois da aprovação explícita.

---

### G1.4 — Contratos de dados/saída entre papéis

**Quem:** Claude
**Depende de:** G1.3

**Fase 1 — Análise e Verificação**
Reler os contratos aprovados em G1.3.

**Fase 2 — Execução**
Escrever JSON Schema para cada um: "sinal" (papel trading→consumidor), "relatório de investimento", "score de volatilidade", "resumo jornalístico".

**Fase 3 — Teste e Validação**
Um exemplo real de cada schema, validado contra o JSON Schema correspondente (não só desenhado, testado com dado real ou sintético representativo).

**Fase 4 — Atualização de Status**
Mover G1.4 para Done.

---

### G1.5 — Isolar credenciais financeiras / garantir ausência de execução real

**Quem:** Claude + Desenvolvedor
**Depende de:** nada (é um gate transversal, deve ser verificado antes de G1.7 em diante, e re-verificado depois de cada um)

**Fase 1 — Análise e Verificação**
Confirmar, por grep/revisão de código, que nenhum caminho do cluster financeiro (nesta fase) tem acesso a qualquer SDK de corretora/execução de ordens.

**Fase 2 — Execução**
Não há "execução" positiva aqui — é uma restrição a manter. Se algum framework escolhido em G1.1 vier com capacidade de execução de ordem embutida, desactivá-la explicitamente ou não a integrar.

**Fase 3 — Teste e Validação**
Teste que tenta simular uma "ordem" através de qualquer componente do cluster e confirma que não existe nenhuma função capaz de executar isso — a ausência é o resultado esperado, testável por "não existe símbolo/endpoint para isto no código" (grep negativo como asserção de teste, não só inspecção manual).

**Fase 4 — Atualização de Status**
Este item nunca "fecha" definitivamente — reconfirmar antes de G1.7, G1.11, e antes de qualquer expansão futura do cluster. Registar cada reconfirmação com data.

---

### G1.6 — Avaliar MiroFish e repos de simulação/visualização

**Quem:** Claude
**Origem:** STATUS.md item B6
**Depende de:** G1.1

**Fase 1 — Análise e Verificação**
Confirmar a licença AGPL do MiroFish e a nota "uso interno" já registada no STATUS — aplicar a mesma disciplina de nuance AGPL já usada para Firecrawl.

**Fase 2 — Execução**
Mesma disciplina de G1.1 aplicada especificamente à visualização/simulação.

**Fase 3 — Teste e Validação**
Documento de auditoria dedicado (secção do `AUDIT-TRADING.md`), com decisão de adopção explícita.

**Fase 4 — Atualização de Status**
Mover B6 para Done ou DEFER.

---

### G1.7 — Implementar agente de trading (simulação only) *(= B3)*

**Quem:** Claude
**Depende de:** G1.3, G1.4, G1.5 (reconfirmado), G1.6

**Fase 1 — Análise e Verificação**
Confirmar que G1.3-G1.6 estão fechados. Reconfirmar G1.5 antes de escrever qualquer linha de código deste item.

**Fase 2 — Execução**
Implementar o agente usando os contratos de G1.3/G1.4, gerando sinais contra dados históricos (nunca mercado ao vivo nesta fase).

**Fase 3 — Teste e Validação**
Rodar contra um dataset histórico conhecido (ex. um período de mercado já documentado publicamente) e confirmar que os sinais gerados são auditáveis (justificação rastreável, não caixa-preta). Reconfirmar G1.5 (ausência de execução real) como parte explícita da suite de testes deste item, não só uma vez no passado.

**Fase 4 — Atualização de Status**
Mover B3 para Done com nota explícita: "simulação only, sem ordens — confirmado por teste em [data]".

---

### G1.8 — Agente de investimentos *(= B12)*

**Quem:** Claude
**Depende de:** G1.2, G1.3, G1.4

**Fase 1 — Análise e Verificação**
Confirmar fontes de dados de G1.2 disponíveis e funcionais.

**Fase 2 — Execução**
Implementar consumindo G1.2 (fontes) + G1.4 (contratos).

**Fase 3 — Teste e Validação**
Relatório de investimento gerado para um caso de teste conhecido, revisado manualmente pelo Desenvolvedor quanto a plausibilidade (não há "resposta certa" objectiva aqui — validação é humana, documentar isso explicitamente em vez de fingir um teste automatizado que não existe).

**Fase 4 — Atualização de Status**
Mover B12 para Done só depois da revisão humana explícita.

---

### G1.9 — Análise de volatilidade *(= B13)*

**Quem:** Claude
**Depende de:** G1.2, G1.4

**Fase 1 — Análise e Verificação**
Confirmar método de cálculo escolhido (ex. desvio padrão de retornos, VIX-like) antes de implementar.

**Fase 2 — Execução**
Implementar cálculo sobre dados históricos reais.

**Fase 3 — Teste e Validação**
Comparar o número calculado com um valor de referência conhecido publicamente (ex. VIX ou equivalente para o mesmo período) — deve estar na mesma ordem de grandeza, não exactamente igual (métricas diferentes podem variar legitimamente).

**Fase 4 — Atualização de Status**
Mover B13 para Done.

---

### G1.10 — Agente jornalístico → jornalismo-investidor *(= F22 + B14)*

**Quem:** Claude
**Depende de:** G1.2

**Fase 1 — Análise e Verificação**
Confirmar que F22 ("a desenhar", o menos maduro do cluster todo) tem agora escopo definido a partir de G1.2/G1.4 — se não tiver, este item não está pronto para implementação, só para desenho.

**Fase 2 — Execução**
Implementar geração de resumo formatado para consumo de investidor a partir das fontes de G1.2.

**Fase 3 — Teste e Validação**
Resumo gerado para uma notícia real de teste, revisado quanto a fidelidade à fonte (não inventar dado — mesma disciplina já usada no pipeline de conhecimento jurídico deste repo, `agents/_shared/grounding.directive.md`).

**Fase 4 — Atualização de Status**
Mover F22 e B14 para Done juntos (são a mesma entrega).

---

### G1.11 — Operação financeira (orquestrador do cluster) *(= B10)*

**Quem:** Claude
**Depende de:** G1.7, G1.8, G1.9, G1.10 (todos os papéis precisam existir antes do orquestrador ter o que coordenar)

**Fase 1 — Análise e Verificação**
Confirmar que os 4 papéis (G1.7-G1.10) estão implementados e testados individualmente.

**Fase 2 — Execução**
Implementar a camada que coordena os 4, decidindo quando cada um é chamado (pode reutilizar o padrão Router/Planner já existente no repo, ou um `AgentConfig.profile` financeiro específico, cruzando com F1).

**Fase 3 — Teste e Validação**
Um cenário real que dispara os 4 papéis em sequência e produz uma saída consolidada coerente.

**Fase 4 — Atualização de Status**
Mover B10 para Done.

---

### G1.12 — Tela de agentes financeiros *(= U3)*

**Quem:** Claude
**Depende de:** G1.11

**Fase 1 — Análise e Verificação**
Confirmar G1.11 fechado e com uma interface (API/eventos) que a tela possa consumir.

**Fase 2 — Execução**
Implementar UI que mostra o estado/output de G1.11 em tempo real.

**Fase 3 — Teste e Validação**
Teste manual: abrir a tela, rodar G1.11, confirmar que a tela reflecte o resultado sem refresh manual.

**Fase 4 — Atualização de Status**
Mover U3 para Done.

---

### G1.13 — Avatar financeiro *(= U7)*

**Quem:** Claude
**Depende de:** G1.11 + Grupo G3 (sistema de avatar genérico) fechado

**Fase 1 — Análise e Verificação**
Confirmar que G3 (avatar genérico) existe e expõe uma interface de "skin"/especialização antes de tentar implementar este item.

**Fase 2 — Execução**
Implementar skin financeira sobre o sistema de avatar genérico.

**Fase 3 — Teste e Validação**
Teste de fumaça confirmando que o avatar renderiza com o contexto financeiro correcto (dados de G1.11 reflectidos na apresentação do avatar).

**Fase 4 — Atualização de Status**
Mover U7 para Done.

---

### G1.14 — Critério de "pronto" do cluster inteiro

**Quem:** Desenvolvedor
**Depende de:** G1.1 até G1.13, todos fechados

**Fase 1 — Análise e Verificação**
Reler o estado de todos os 13 itens anteriores.

**Fase 2 — Execução**
Não há execução de código aqui — é aprovação.

**Fase 3 — Teste e Validação**
Checklist assinado pelo Desenvolvedor confirmando: simulação auditável, zero caminho para execução real (G1.5 reconfirmado uma última vez), critério de "pronto" atingido para cada papel individual.

**Fase 4 — Atualização de Status**
Mover o cluster G1 inteiro para Done com a aprovação registada. Qualquer expansão futura (ex. conectar a uma corretora real) é um novo item, com o seu próprio gate, nunca uma extensão implícita deste.

---

*(Fim do Grupo G1 — 14/14 itens.)*

---

## GRUPO G2 — Agente de Gamedev (4 itens)

> **Revalidação de escopo (B14/D10, 2026-09-19):** confirmado **REAL** — nada implementado (esperado). Ver `docs/architecture/meta-validation/AUDIT-SCOPE-2026-09-19.md`.

> **Nota de nomenclatura:** não confundir com o item "G2" do `STATUS.md` (16 skills migradas — ver F2).

### G2.1 — Pesquisa padrão ouro (GDD, engine, loop)

**Quem:** Claude
**Origem:** STATUS.md item B4

**Fase 1 — Análise e Verificação**
Confirmar, por busca no repo, ausência de trabalho prévio sobre isto.

**Fase 2 — Execução**
Pesquisa dedicada sobre frameworks/repos de agentes para geração de GDD (Game Design Document), loop de jogo, integração de engine (Godot/Unity/Unreal) — mesma disciplina de verificação de maturidade/licença/CVEs.

**Fase 3 — Teste e Validação**
Documento de auditoria no mesmo formato das outras (tabela de evidência, classificação, "o que NÃO adoptar").

**Fase 4 — Atualização de Status**
Criar `docs/architecture/gamedev-agent-audit/AUDIT-GAMEDEV.md`. Mover G2.1 para Done.

---

### G2.2 — Definir escopo (documento vs. protótipo jogável)

**Quem:** Desenvolvedor
**Depende de:** G2.1

**Fase 1 — Análise e Verificação**
Reler o resultado de G2.1 para saber o que é tecnicamente viável em cada direcção.

**Fase 2 — Execução**
Desenvolvedor decide: o agente gera só o documento (GDD), ou também código de protótipo jogável.

**Fase 3 — Teste e Validação**
Decisão escrita, não implícita.

**Fase 4 — Atualização de Status**
Registar decisão, mover G2.2 para Done.

---

### G2.3 — Escolher engine-alvo

**Quem:** Desenvolvedor
**Depende de:** G2.2 (só relevante se G2.2 decidir por protótipo jogável)

**Fase 1 — Análise e Verificação**
Se G2.2 decidiu só GDD, este item fica DEFER — não escolher engine sem necessidade.

**Fase 2 — Execução**
Se protótipo jogável: decidir Godot/Unity/Unreal com base em G2.1.

**Fase 3 — Teste e Validação**
Decisão escrita.

**Fase 4 — Atualização de Status**
Mover para Done ou DEFER.

---

### G2.4 — Implementar

**Quem:** Claude
**Depende de:** G2.1, G2.2, G2.3

**Fase 1 — Análise e Verificação**
Confirmar escopo e engine decididos.

**Fase 2 — Execução**
Implementar o agente conforme escopo definido.

**Fase 3 — Teste e Validação**
Gerar 1 GDD real de teste (e/ou protótipo, conforme escopo) e revisão humana de qualidade (mesma disciplina de G1.8 — validação humana explícita onde não há "resposta certa" objectiva).

**Fase 4 — Atualização de Status**
Mover B4 para Done.

---

*(Fim do Grupo G2 — 4/4 itens.)*

---

## GRUPO G3 — Sistema de Avatar genérico (3 itens)

> **Revalidação de escopo (B14/D10, 2026-09-19):** confirmado **REAL** — nada implementado. Dependência do G3.1 (`working_memory.py`/S7) confirmada satisfeita. Ver `docs/architecture/meta-validation/AUDIT-SCOPE-2026-09-19.md`.

> **Nota de nomenclatura:** não confundir com o item "G3" do `STATUS.md` (5 knowledge packs migrados — ver F3).

### G3.1 — Pesquisa/desenho da infra de avatar

**Quem:** Claude
**Origem:** STATUS.md itens B11, U2, U6

**Fase 1 — Análise e Verificação**
Confirmar dependência já registada (U2 depende de "B11 + S7"; S7 — working memory por cliente — já está em Done).

**Fase 2 — Execução**
Pesquisa/desenho de uma interface de avatar genérica (não específica de domínio), reutilizável por G1.13 (financeiro) e outros futuros.

**Fase 3 — Teste e Validação**
Documento de arquitectura com a interface de "skin"/especialização definida (o contrato que G1.13 e outros consumidores vão implementar).

**Fase 4 — Atualização de Status**
Mover B11 para Done (desenho).

---

### G3.2 — Implementar avatar genérico

**Quem:** Claude
**Depende de:** G3.1

**Fase 1 — Análise e Verificação**
Confirmar S7 (working memory) disponível como fonte de contexto do avatar.

**Fase 2 — Execução**
Implementar o avatar base, consumindo S7 para contexto por cliente.

**Fase 3 — Teste e Validação**
Teste manual: avatar reflecte o histórico/contexto real de um cliente de teste.

**Fase 4 — Atualização de Status**
Mover U2 para Done.

---

### G3.3 — Avatar boneco (skin)

**Quem:** Claude
**Origem:** STATUS.md item U6
**Depende de:** G3.2

**Fase 1 — Análise e Verificação**
Confirmar interface de skin de G3.1 disponível.

**Fase 2 — Execução**
Implementar a skin "boneco" sobre o avatar genérico.

**Fase 3 — Teste e Validação**
Teste de fumaça — renderiza correctamente.

**Fase 4 — Atualização de Status**
Mover U6 para Done.

---

*(Fim do Grupo G3 — 3/3 itens.)*

---

## GRUPO G4 — Grafo de memória (2 itens)

> **Revalidação de escopo (B14/D10, 2026-09-19):** confirmado **REAL** — decisão G4.1 (Obsidian vs. Logseq) continua por tomar. Ver `docs/architecture/meta-validation/AUDIT-SCOPE-2026-09-19.md`.

> **Nota de nomenclatura:** não confundir com o item "G4" do `STATUS.md` (13 agentes horizontais migrados — ver F4).

### G4.1 — Decidir Obsidian vs. Logseq *(= F10)*

**Quem:** Desenvolvedor
**Origem:** STATUS.md item F10 ("candidate")

**Fase 1 — Análise e Verificação**
Reler a nota "candidate" do STATUS — nunca foi decidido qual dos dois.

**Fase 2 — Execução**
Desenvolvedor decide com base em uso pessoal/preferência (é uma ferramenta de visualização pessoal, decisão legítima de gosto/fluxo de trabalho, não só técnica).

**Fase 3 — Teste e Validação**
Decisão escrita.

**Fase 4 — Atualização de Status**
Mover F10 para Done.

---

### G4.2 — Implementar grafo *(= U1)*

**Quem:** Claude
**Depende de:** G4.1

**Fase 1 — Análise e Verificação**
Confirmar ferramenta escolhida em G4.1 e o formato de exportação que ela espera.

**Fase 2 — Execução**
Implementar a geração do grafo de memória (provavelmente a partir de `events.jsonl`/`working_memory.py`, ligando com B11 — session search — se fizer sentido reaproveitar o índice).

**Fase 3 — Teste e Validação**
Grafo gerado a partir de dados reais de um cliente de teste, aberto na ferramenta escolhida, confirmando nós/relações coerentes com o histórico real.

**Fase 4 — Atualização de Status**
Mover U1 para Done.

---

*(Fim do Grupo G4 — 2/2 itens. Fim de todo o Grupo G — 14+4+3+2 = 23/23 itens.)*

---

## GRUPO H — Integração final (4 itens, só depois de G1+G3+G4 existirem)

> **Revalidação de escopo (B14/D10, 2026-09-19):** confirmado **REAL** — nenhum dos pré-requisitos (G1/G3/G4) está fechado, portanto nada aqui pode ter começado. Ver `docs/architecture/meta-validation/AUDIT-SCOPE-2026-09-19.md`.

### H1 — Dashboard/integração *(= U4)*

**Quem:** Claude
**Origem:** STATUS.md item U4
**Depende de:** G1.12 (tela financeira), G3.2 (avatar genérico), G4.2 (grafo de memória)

**Fase 1 — Análise e Verificação**
Confirmar que os 3 componentes dependentes estão fechados e cada um expõe uma interface consumível (API/eventos) para agregação.

**Fase 2 — Execução**
Implementar dashboard único que integra os 3.

**Fase 3 — Teste e Validação**
Teste manual: os 3 componentes aparecem correctamente agregados, sem um quebrar a renderização dos outros.

**Fase 4 — Atualização de Status**
Mover U4 para Done.

---

### H2 — JARVIS *(= U8)*

**Quem:** Claude
**Origem:** STATUS.md item U8
**Depende de:** todos os itens U1-U7 (G1.12, G1.13, G3.2, G3.3, G4.2, H1)

**Fase 1 — Análise e Verificação**
Confirmar que U1-U7 estão todos fechados — este é o item de maior dependência de todo o plano, não começar cedo demais.

**Fase 2 — Execução**
Implementar a camada de integração final descrita como "JARVIS" — escopo exacto depende do que os componentes individuais já oferecem (não inventar escopo novo aqui, só integrar o que já existe).

**Fase 3 — Teste e Validação**
Teste de fumaça cobrindo interacção com cada componente integrado.

**Fase 4 — Atualização de Status**
Mover U8 para Done.

---

### H3 — VOS *(= U9)*

**Quem:** Desenvolvedor
**Origem:** STATUS.md item U9 ("Clarificar")

**Fase 1 — Análise e Verificação**
O próprio STATUS.md nunca definiu o escopo deste item ("Clarificar" é a dependência registada, literalmente).

**Fase 2 — Execução**
Nenhuma execução possível sem escopo. Desenvolvedor define o que "VOS" significa e o que se espera dele antes de qualquer trabalho.

**Fase 3 — Teste e Validação**
N/A até haver escopo.

**Fase 4 — Atualização de Status**
Não mover para nenhuma fase de execução até este item ganhar uma definição real — fica marcado "aguardando escopo", não "backlog" (categorias diferentes: backlog implica que já se sabe o que fazer).

---

### H4 — Grafo de conexões *(= U5)*

**Quem:** Desenvolvedor
**Origem:** STATUS.md item U5 (sem dependência registada, mas também sem escopo definido)

**Fase 1 — Análise e Verificação**
Confirmar que este item nunca teve escopo além do título — distinto de U1 (grafo de memória), que já tem escopo claro via G4.

**Fase 2 — Execução**
Desenvolvedor define o que distingue este item de U1/U4 antes de qualquer trabalho (risco real de ser duplicado/redundante com o dashboard de H1).

**Fase 3 — Teste e Validação**
N/A até haver escopo.

**Fase 4 — Atualização de Status**
Mesma nota de H3 — "aguardando escopo".

---

*(Fim do Grupo H — 4/4 itens.)*

---

## GRUPO I — Backlog de pesquisa não triado (10 itens)

> **Revalidação de escopo (B14/D10, 2026-09-19):** I1, I3-I7, I9-I11 confirmados **REAL**. I2 e I8 já tinham a sua própria discrepância auto-documentada no texto original (não é achado novo desta auditoria) — confirmado que continua correcto. Ver `docs/architecture/meta-validation/AUDIT-SCOPE-2026-09-19.md`.

Nota honesta sobre este grupo: a primeira versão deste documento reduziu vários destes itens a "mesmo padrão de I1" — isso não é um prompt, é uma citação vazia, exactamente o erro já apontado nesta sessão. Reescrito abaixo item a item, sem atalho.

### I1 — `agent-skills` (Addy Osmani) *(= F1)*

**Quem:** Claude
**Origem:** STATUS.md, secção Ferramentas F1-F22

**Fase 1 — Análise e Verificação**
Identificar o repositório exacto (Addy Osmani é autor confirmado, mas o nome "agent-skills" é genérico o suficiente para haver mais de um projecto com nome parecido — confirmar por GitHub API que é mesmo o dele, não um homónimo, antes de avaliar). Confirmar se ainda está mantido (data do último commit).

**Fase 2 — Execução**
Ler o conteúdo real do repositório: é uma colecção de skills/prompts, um framework de execução, ou documentação? Verificar licença, estrelas, contribuidores.

**Fase 3 — Teste e Validação**
Documento de auditoria com tabela de evidência (alegação | link | validado?), classificação ADOPT/ADAPT/REFERENCE/DEFER/REJECT com justificação — mesmo formato usado em todas as outras auditorias desta sessão, não um veredicto de uma linha.

**Fase 4 — Atualização de Status**
Mover F1 para Done (avaliado, com documento) ou DEFER com razão registada.

---

### I2 — Graphify *(= F2)*

**Quem:** Claude
**Origem:** STATUS.md, secção Ferramentas F1-F22

**Fase 1 — Análise e Verificação**
**Atenção — achado de discrepância, não avaliação em branco:** o `CLAUDE.md` do repo `agent-network-mcp` (clonado nesta sessão) já documenta Graphify como ferramenta em uso real e activo: *"Grafo de código local em `graphify-out/` (gitignored — gerar na máquina, não commitar artefactos)"*, com comandos reais (`graphify query`, `graphify path`, `graphify update .`) e regra de uso ("preferir graphify query quando graphify-out/graph.json existir"). Isto contradiz a categoria "research" que o STATUS.md deste repo (`network-agents-setup`) ainda atribui ao item F2 — são dois repos diferentes do mesmo ecossistema com estados de conhecimento desalinhados sobre a mesma ferramenta.

**Fase 2 — Execução**
Confirmar, correndo `graphify query` real num checkout do `agent-network-mcp`, que a ferramenta de facto funciona como documentado (não confiar só na descrição do `CLAUDE.md` de lá — mesma disciplina "código > README" desta sessão inteira, aplicada agora a outro repo).

**Fase 3 — Teste e Validação**
Uma consulta real (`graphify query "..."`) devolve resultado coerente com o código real do `agent-network-mcp`.

**Fase 4 — Atualização de Status**
Corrigir a categoria de F2 neste STATUS.md de "research" para "em uso (confirmado em `agent-network-mcp`)" — e avaliar se `network-agents-setup` (este repo) também se beneficiaria da mesma ferramenta, já que é um projecto TypeScript/Python de tamanho comparável.

---

### I3 — OmniRoute *(= F3)*

**Quem:** Claude
**Origem:** STATUS.md, secção Ferramentas F1-F22

**Fase 1 — Análise e Verificação**
**Cuidado de nomenclatura, a resolver antes de pesquisar:** o STATUS.md tem, na secção "Harnesses multi-provider", um projecto chamado `omnigent-ai/omnigent` ("Meta-harness sobre Claude Code, Codex, Cursor") já catalogado separadamente como F8/INIT-094. "OmniRoute" (F3) é nome parecido mas está listado como item distinto — confirmar por busca directa que não são o mesmo projecto mal referenciado duas vezes antes de gastar esforço avaliando algo já coberto por F8.

**Fase 2 — Execução**
Se confirmado distinto: identificar o repositório real, ler arquitectura (é um router de modelos, um proxy, algo diferente?), licença, maturidade.

**Fase 3 — Teste e Validação**
Documento de auditoria com veredicto explícito. Se se confirmar que é o mesmo projecto que F8, fechar F3 como duplicado, referenciando F8 — não escrever uma segunda avaliação do mesmo código.

**Fase 4 — Atualização de Status**
Mover F3 para Done (avaliado ou reconciliado com F8).

---

### I4 — Obscura *(= F4, duplica com F17 "Obscura + obscura-mcp")*

**Quem:** Claude
**Origem:** STATUS.md, secções F1-F22 (14/09) e adição posterior (F17)

**Fase 1 — Análise e Verificação**
Confirmar se F4 e F17 descrevem o mesmo projecto (Obscura) em momentos diferentes, ou se F17 acrescenta um componente novo (`obscura-mcp`, sugerindo um servidor MCP dedicado que talvez não existisse quando F4 foi registado). Ler o nome/descrição de ambos lado a lado antes de decidir.

**Fase 2 — Execução**
Reconciliar num único item: se `obscura-mcp` é um componente adicional (não um projecto concorrente), F4+F17 viram uma avaliação só, cobrindo os dois. Avaliar arquitectura, licença, maturidade de ambos.

**Fase 3 — Teste e Validação**
Documento de auditoria único cobrindo Obscura + obscura-mcp, com veredicto para cada componente separadamente se fizerem sentido como adopções independentes.

**Fase 4 — Atualização de Status**
Fechar F4 e F17 juntos, com nota explícita "reconciliados, ver documento único".

---

### I5 — Plugin de segurança Anthropic *(= F5, duplica com F16)*

**Quem:** Claude
**Origem:** STATUS.md, secções F1-F22 e F17-22

**Fase 1 — Análise e Verificação**
Confirmar que F5 e F16 apontam para o mesmo plugin (o nome genérico "plugin de segurança Anthropic" tem risco real de se referir a coisas diferentes em momentos diferentes — verificar se há um link/repo específico registado em qualquer conversa anterior antes de assumir que é um só). Confirmar que é de facto mantido pela Anthropic (não uma imitação de terceiros com nome parecido — mesmo cuidado já aplicado a `ai-memory-mcp`/`ContextForge` nas auditorias de memória/governança, onde nomes ambíguos geraram confusão real).

**Fase 2 — Execução**
Avaliar o plugin real: o que cobre, como se integra com o `security_auditor` já existente neste repo (B2, já em Done) — evitar sobreposição/redundância.

**Fase 3 — Teste e Validação**
Documento de auditoria único (F5+F16 reconciliados), com veredicto de adopção considerando o que o `security_auditor` já cobre.

**Fase 4 — Atualização de Status**
Fechar F5 e F16 juntos.

---

### I6 — Ruflo *(= F7, "parked")*

**Quem:** Desenvolvedor
**Origem:** STATUS.md, secção Ferramentas F1-F22

**Fase 1 — Análise e Verificação**
Reler o contexto original de por que Ruflo foi "parked" (o STATUS.md não regista a razão — isto por si só é um problema: um item arquivado sem razão escrita não pode ser avaliado quanto a "ainda faz sentido revisitar" sem primeiro reconstruir por que foi pausado).

**Fase 2 — Execução**
Desenvolvedor decide: se a razão de pausa ainda não é conhecida, primeiro reconstruir isso (procurar em histórico de conversas/commits); só depois decidir reabrir ou mover para Grupo J definitivamente.

**Fase 3 — Teste e Validação**
Razão de pausa (original ou reconstruída) e decisão final escritas — não deixar "parked" sem justificação para sempre.

**Fase 4 — Atualização de Status**
Mover F7 para Grupo J (com razão) ou reabrir como avaliação nova.

---

### I7 — gstack *(= F8)*

**Quem:** Claude
**Origem:** STATUS.md, secção Ferramentas F1-F22

**Fase 1 — Análise e Verificação**
Identificar o projecto real por trás do nome "gstack" — nome curto e genérico, risco real de ambiguidade (pode haver múltiplos projectos com esse nome; confirmar qual é o pretendido antes de avaliar, mesmo cuidado já usado noutras auditorias desta sessão para nomes ambíguos).

**Fase 2 — Execução**
Depois de identificado com confiança: avaliar arquitectura, licença, maturidade, relevância para este repo.

**Fase 3 — Teste e Validação**
Documento de auditoria com veredicto; se não for possível identificar o projecto pretendido com confiança razoável, registar explicitamente como **NOT VERIFIED** (nome insuficiente para avaliação) em vez de avaliar o projecto errado.

**Fase 4 — Atualização de Status**
Mover F8 para Done (avaliado) ou NOT VERIFIED com nota explicando a ambiguidade.

---

### I8 — Obsidian/Logseq *(= F10)*

Já tratado integralmente em **G4.1** — este item não existe separadamente; a entrada F10 do STATUS.md deve ser fechada com referência cruzada a G4.1, não avaliada duas vezes.

---

### I9 — SOUL.md *(= F11)*

**Quem:** Claude
**Origem:** STATUS.md, secção Ferramentas F1-F22

**Fase 1 — Análise e Verificação**
Reler `patterns-from-hermes/README.md` secção "H01 + H09 — Memória em camadas": o padrão H09 ("USER / SOUL / MEMORY separados") já mapeia exactamente este conceito — SOUL como "voz e regras imutáveis (ou quase)", já correlacionado com `CONSTITUTION-DRAFT`/Spec Kit constitution deste repo. Confirmar se "SOUL.md" (F11) é literalmente esse mesmo conceito ou algo adicional não coberto por H09.

**Fase 2 — Execução**
Se for o mesmo conceito: F11 não é pesquisa nova, é *aplicação* do que H09 já encontrou — a acção passa a ser "escrever o `SOUL.md` real deste repo seguindo o padrão H09", não "pesquisar SOUL.md". Se houver uma ferramenta/formato específico chamado "SOUL.md" com proveniência própria (fora do Hermes), pesquisar essa fonte separadamente.

**Fase 3 — Teste e Validação**
Documento curto explicando a reclassificação (se aplicável) +, se a acção virar "escrever o ficheiro", o `SOUL.md` real criado e revisado quanto a coerência com `CONSTITUTION-DRAFT`.

**Fase 4 — Atualização de Status**
Mover F11 para Done, com nota "reclassificado como aplicação de H09" se for o caso — não como pesquisa fechada sem produto nenhum.

---

### I10 — Andrej Karpathy Skills *(= F15)*

**Quem:** Claude
**Origem:** STATUS.md, secção Ferramentas F1-F22

**Fase 1 — Análise e Verificação**
Identificar o repositório real (Andrej Karpathy é figura pública conhecida, mas confirmar por GitHub API o repo exacto de "skills" atribuído a ele — mesmo cuidado de identificação de I1/I7, nunca assumir pelo nome sozinho). Confirmar estado de manutenção.

**Fase 2 — Execução**
Ler o conteúdo real: são skills no formato já usado neste repo (frontmatter + trigger + passos), prompts soltos, ou algo mais amplo (ex. relacionado aos cursos/material educacional dele, o que mudaria completamente a aplicabilidade)?

**Fase 3 — Teste e Validação**
Documento de auditoria com veredicto — se aplicável, 1 skill adaptada como piloto e testada num plano real (mesma disciplina de E7/`google/skills`).

**Fase 4 — Atualização de Status**
Mover F15 para Done ou DEFER.

---

### I11 — Soup (fine-tuning) *(= F12)*

**Quem:** Desenvolvedor
**Origem:** STATUS.md, secção Ferramentas F1-F22, "F12 (Soup) | C8 (RAG alimentada) ✅ desbloqueado"

**Fase 1 — Análise e Verificação**
Confirmar que a dependência registada ("só após C8") está de facto resolvida — C8 (RAG alimentado, 110+ chunks, pipeline completo) está em Done desde 2026-09-17, confirmado nesta sessão por leitura directa do `STATUS.md`.

**Fase 2 — Execução**
Desenvolvedor reavalia prioridade agora que a dependência caiu — o item ficou "parked" antes de estar desbloqueado; a passagem do tempo desde então pode ter mudado a relevância de fine-tuning face a outras prioridades deste plano (ex. os 108 itens dos grupos A-H).

**Fase 3 — Teste e Validação**
Decisão de prioridade escrita, com posição explícita no plano geral (não deixar "desbloqueado" sem dizer quando entra na fila).

**Fase 4 — Atualização de Status**
Mover F12 para "candidate activo" com prioridade relativa definida, ou manter "parked" com razão actualizada (não a razão antiga, que já não se aplica).

---

*(Fim do Grupo I — 10 itens efectivos, cada um com as 4 fases completas, nenhum reduzido a citação de outro. I8 não conta como item — ver correção nº1 do errata.)*

---

## GRUPO J — Arquivado (7 itens, não fazer agora, registados individualmente para não desaparecer)

> **Revalidação de escopo (B14/D10, 2026-09-19):** confirmado **REAL** — todos continuam arquivados, sem gatilho novo. Ver `docs/architecture/meta-validation/AUDIT-SCOPE-2026-09-19.md`.

### J1 — PCU Constitution *(= P1)*

**Quem:** Desenvolvedor (só ele pode reabrir)
**Razão original:** formalismo, não resolve problema real.
**Fase 1 — Análise e Verificação (só se revisitado):** confirmar se algum dos achados desta sessão (ex. a necessidade de um contrato formal de segurança/governança, Grupo C) criou uma razão nova e concreta para isto, distinta do formalismo vazio original.
**Fase 2-4:** nenhuma acção agora. Revisitar só com gatilho explícito (ex. C3/C4 — AgentMesh/Cedar — amadurecerem a ponto de precisarem de um documento constitucional real por trás).

### J2 — META Compiler / MCL *(= P2)*

**Quem:** Desenvolvedor
**Razão original:** over-engineering.
**Fase 1-4:** nenhuma acção. Nenhum achado desta sessão (Governança, Agentes, ou qualquer auditoria) sugeriu necessidade nova — a razão original mantém-se sem contestação.

### J3 — AR-000 a AR-015 *(= P3)*

**Quem:** Desenvolvedor
**Razão original:** idem P2 (over-engineering).
**Fase 1-4:** nenhuma acção. Mesma nota de J2.

### J4 — A2A (agentes a conversar) *(= P4)*

**Quem:** Desenvolvedor
**Razão original:** complexidade prematura.
**Fase 1 — Análise e Verificação:** esta é a única entrada de J que teve reavaliação real nesta sessão — `agents-audit/FASE2-AGENTES.md` auditou A2A a fundo (spec 1.0, 25,6k estrelas, adoptado por Google ADK e Microsoft Agent Framework) e concluiu, por via independente, o mesmo veredicto (REFERENCE, não ADOPT — resolve comunicação entre agentes de organizações diferentes, problema que este repo não tem hoje).
**Fase 2-4:** manter arquivado — a razão original ("complexidade prematura") sai desta sessão *reforçada com evidência real*, não só repetida. Revisitar apenas se este repo vier a precisar de expor ou consumir um agente de terceiros fora do seu controlo (cenário descrito em `AUDIT-AGENTS.md` secção 7, Fase 3 do roadmap).

### J5 — UI visual (Langflow, n8n) *(= P5)*

**Quem:** Desenvolvedor
**Razão original:** sem dor real.
**Fase 1-4:** nenhuma acção. Nenhuma das telas desenhadas no Grupo H (dashboard, JARVIS) é isto — são interfaces de produto, não ferramentas de authoring visual de fluxo; não confundir os dois ao revisitar no futuro.

### J6 — Multi-provider LLM *(= P6)*

**Quem:** Desenvolvedor
**Razão original:** só quando houver necessidade.
**Fase 1 — Análise e Verificação:** **a necessidade ainda não chegou, mas a razão original ("só quando houver necessidade") deixou de ser incondicional.** D5 (`model_tier` real via LiteLLM Router) e D6 (Budget Manager), desenhados nesta mesma sessão mas **ainda não executados** (ver Grupo D), implementam exactamente multi-provider LLM, motivados por um problema concreto (LLM06, Unbounded Consumption). Enquanto D5/D6 não estiverem em Done, este item mantém-se arquivado sem contradição — a necessidade só "chega" de facto quando eles forem fechados (ver Fase 2).
**Fase 2 — Execução:** quando D5/D6 forem executados, revisitar este item e fechá-lo como "superseded by D5/D6", não deixá-lo como arquivado ao lado de uma implementação real do mesmo conceito.
**Fase 3-4:** decisão de fecho registada assim que D5/D6 estiverem em Done.

### J7 — Caveman *(= F6)*

**Quem:** Desenvolvedor
**Razão original:** "N/A" — sem descrição no registo original.
**Fase 1 — Análise e Verificação:** antes de qualquer decisão, descobrir o que "Caveman" sequer é — a entrada original não tem link nem descrição, só o nome. Procurar em histórico de conversas anteriores a esta sessão.
**Fase 2-4:** sem acção possível até isso ser resolvido. Este é o único item de todo o plano (108 itens) onde a Fase 1 não tem por onde começar sem informação externa a este documento.

---

*(Fim do Grupo J — 7/7 itens.)*

---

## Contagem final

A(23) + B(13) + C(7) + D(10) + E(9) + F(10) + G1(14) + G2(4) + G3(3) + G4(2) + H(4) + I(10) + J(7) = **116 itens** (109 accionáveis nos Grupos A-I + 7 arquivados no Grupo J — A22, A23, D8, D9, D10, E8 e E9 acrescentados em 2026-09-19, F10 acrescentado em 2026-09-20 (achado durante A16/C5), ver nota de correção nº1 do errata para a metodologia de contagem), cobrindo integralmente `STATUS.md` (todas as séries: Prompts pendentes, Crítico/Alto/Médio/Baixo, Arquivado, checklist de segurança de 20, Harnesses, google/skills, Mapeamento G1-G7, F1-F22, B1/B3-B16, U1-U9, Dependências críticas) + todas as auditorias desta sessão (Governança, Memória, Agentes Fases 1-6, Ingestão, Tools/MCP, Orquestração, Segurança 2026, Avaliação, Observabilidade, Meta-Validação).

Nenhum item de `STATUS.md` ficou de fora. Onde havia duplicação entre séries antigas (F4/F17, F5/F16), foi sinalizado para reconciliação em vez de ser tratado duas vezes.

> **B14/D10 — Auditoria de escopo concluída em 2026-09-19.** Todos os itens pendentes (Grupos A-J) revalidados contra o código real. Resultado: 61 REAL, 4 DIFERENTE (A15, A19, D1, I2 — este já auto-documentado), 2 N/A (A19, I8 — este já auto-documentado), 4 JÁ FEITO (C7, F2, F3, F4). Relatório completo: `docs/architecture/meta-validation/AUDIT-SCOPE-2026-09-19.md`. 3 inconsistências de contagem adicionais encontradas e corrigidas nos cabeçalhos dos Grupos A/D/E (diziam 21/7/7, deviam dizer 23/10/9 — já batiam no fecho de cada grupo e na Contagem final, só o cabeçalho estava desactualizado).

