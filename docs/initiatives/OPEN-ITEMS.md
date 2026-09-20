# Itens em Aberto — Relatório Consolidado (2026-09-20)

Produzido na Tarefa 5 da auditoria autónoma desta sessão. Fontes lidas por completo: `STATUS.md` (446 linhas), `EXECUTION-PROMPTS.md` (2448 linhas, todos os Grupos A-J), `docs/architecture/meta-validation/AUDIT-SCOPE-2026-09-19.md` (192 linhas).

**Método:** todo item ainda **não fechado** nos 2 documentos, cruzado (os dois têm séries de ID independentes com os mesmos prefixos — ver nota de colisão em `STATUS.md` linha 5-14; itens equivalentes são marcados `(=X)`). Agrupado por **quem bloqueia**: 100% Claude (posso avançar sozinho), Precisa humano (decisão ou acção só do utilizador), Bloqueado por ambiente (hardware/rede/toolchain desta máquina).

Itens já fechados (Done/JÁ FEITO/N/A confirmado) **não estão nesta lista** — ver `## Done` em `STATUS.md` e as notas "Status em..." em `EXECUTION-PROMPTS.md` para o histórico completo. Este documento cobre só o que resta.

---

## 🟢 100% Claude — posso executar sem depender de decisão humana nem de infra externa

| ID | Descrição | Origem | Prioridade |
|---|---|---|---|
| **B7** (EXEC) | Expor `engine: "langgraph"` + `decision: "edit"` na superfície MCP (`tools_impl.py`) — hoje só `native`/`approve\|reject` são acessíveis via MCP, apesar do motor `langgraph` já suportar ambos | `agents-audit/FASE2-AGENTES.md` §1 | 🟠 Alto — fecha um gap real de capacidade já construída mas não exposta |
| **B13** (EXEC, =M6) | `GeminiProvider` (interface `LLMProvider`) + estender `Planner.ts` com `scope`/`unknowns`/`pre_mortem`/`not_doing` | STATUS.md M6 | 🟡 Médio |
| **D5** | Ler `model_tier` de facto (hoje só existe no schema, campo morto) — via LiteLLM Router | STATUS.md, achado da auditoria de Evaluation | 🟡 Médio |
| **D6** | Implementar `budget.max_cost_usd` (só `max_replans`/`max_steps` existem hoje) | STATUS.md, achado da auditoria de Evaluation | 🟡 Médio |
| **D7** | `MetricsDashboard`/`SelfAwareness` com dados reais (hoje têm comentários placeholder "Em produção, consulta...") | `packages/core/src/observability/SelfAwareness.ts:357-425` | 🟡 Médio |
| **E1-E7** | Adoptar Crawl4AI+Trafilatura, MarkItDown, Docling (condicional), ligar `yt-dlp`+`whisper` ao RAG, `gitingest` (com reservas), reavaliar ScrapeGraphAI, avaliar `google/skills` — pesquisa já feita (`AUDIT-INGESTION.md`), falta só a adopção de código | `ingestion-audit/AUDIT-INGESTION.md` | 🟡 Médio (mecânico, baixo risco arquitectural, mas adiciona dependências novas — considerar 1 confirmação rápida antes de instalar) |
| **E8** (=B11 em STATUS.md) | Script de criação versionado para `knowledge_sources` (hoje só existe manualmente no Supabase) | Achado durante A2 | 🟠 Alto — dívida de controlo de versão real |
| **E9** (=B12 em STATUS.md) | Investigar/documentar a tabela `knowledge_log` (RLS já activo, mas sem dono/propósito documentado) | Achado durante A2 | 🟡 Médio |
| **F8** (=INIT-094) | Reavaliar os 6 harnesses multi-provider (`deepseek-harness` etc.) com o mesmo rigor das auditorias desta sessão — a tabela actual nunca foi reverificada | STATUS.md, secção Harnesses | 🟢 Baixo |
| **S24** (novo, Tarefa 4 desta auditoria) | Escrever testes para `packages/mcp/src/server/MCPServer.ts` (hoje 0% de cobertura) — pode avançar já para os caminhos que **não** dependem da chave real de auth (ver A8 abaixo para a parte que depende de humano) | `docs/architecture/TEST-COVERAGE.md` | 🟠 Alto |

---

## 🟠 Precisa humano — decisão ou acção que só o utilizador pode dar

| ID | Descrição | O que falta decidir/fazer | Prioridade |
|---|---|---|---|
| **S17/S20** | VM Oracle (`130.61.213.226`) com `SUPABASE_SERVICE_ROLE_KEY` provavelmente ainda antiga | SSH + `pm2 restart --update-env` — **explicitamente fora do âmbito de qualquer sessão Claude nesta máquina** (instrução repetida do utilizador) | 🔴 Crítico |
| **S15a** | GitHub Actions de `agent-network-mcp` (7 workflows) ainda com a `SUPABASE_SERVICE_ROLE_KEY` antiga | Actualizar a secret no GitHub Actions desse repo (utilizador já confirmou que vai fazer) | 🔴 Crítico |
| **S21** | Screenshots da migração GCP→Oracle podem conter a chave antiga ou a nova | Confirmar timing (antes/depois de 2026-09-19) | 🟡 Médio |
| **A1b** | Passo de deploy real do `k8s/` (Secret + resolução de `${...}`) | Decidir pipeline (`kubectl`/Helm/Kustomize) e criar o Secret real fora do git | 🟢 Baixo (só relevante quando `k8s/` for aplicado a um cluster real) |
| **A8** (=S11) | Autenticação em `MCPServer.ts` — hoje zero verificação de header antes de `executeTool` | Desenvolvedor define/distribui a `MCP_SERVER_KEY` real; Claude implementa o middleware fail-closed | 🔴 Crítico — é o mesmo achado que **S11** já regista como bloqueando o C1 ser útil de facto |
| **A9** | Lockfile Python (`uv.lock`/`poetry.lock`) — zero lockfile hoje | `uv lock` pode falhar por rede da sandbox — precisa de ambiente com rede real ou confirmação de que a rede está liberada | 🟠 Alto |
| **A10** (=B2b) | Rodar as 8 ferramentas completas do `security_auditor` (só ~5 correram) | Rede liberada para `api.osv.dev`/`mirror.gcr.io` (Trivy `vuln`, OSV-Scanner ficaram bloqueados) | 🟡 Médio |
| **A11** (=B2c) | Triar todos os achados de segurança num backlog rastreável com dono/estado | Desenvolvedor confirma prioridade final de cada achado | 🟡 Médio |
| **A12** | Criptografia de dados em repouso | Confirmar se há mesmo dado sensível nesta camada (provavelmente não — decisão a registar explicitamente) | 🟢 Baixo |
| **A13** | Modelo RBAC real (`SecurityManager.checkRBAC()` existe, mas zero chamada em `apps/api`) | Desenvolvedor aprova papéis fixos vs. ABAC antes da implementação | 🟠 Alto |
| **A15** | Flags de cookie — **item não tem alvo real** (autenticação é 100% via `x-api-key`, sem cookies) | Decisão: fechar como N/A, ou desenhar sessão por cookie de raiz (mudança de arquitectura) | 🟢 Baixo |
| **A19** | Restringir uploads — **item aponta para o repo errado** (`extrair-imagem` só existe em `agent-network-mcp`) | Decisão: mover o item para esse repo, ou remover do plano deste | 🟢 Baixo |
| **A22** (=M8) | 9 alertas Dependabot (3 críticas + 1 alta em dev; 5 moderadas incl. `uuid`, único pacote de produção) | Confirmar changelogs antes do bump; `uuid` precisa de teste de regressão em `apps/api` | 🟠 Alto |
| **A23** (=S13) | CORS totalmente aberto (`app.use(cors())` sem opções) — contradiz o CORP do helmet já corrigido (A20) | Desenvolvedor confirma a lista de origens legítimas — sem isso não há o que configurar | 🟠 Alto |
| **B3** | Correr `apps/api` contra Postgres/OpenAI reais (nunca validado) | Desenvolvedor fornece `.env` real ou de staging | 🟠 Alto — é a peça que fecha "o pipeline TS funciona ponta-a-ponta?" |
| **B5** (=M3) | Teste e2e HITL Python→Node→Python | **Depende de B3** (precisa da API `apps/api` real a correr) — sem isso fica só desenhado, não executável | 🟠 Alto |
| **B6** (=M4) | HITL durável em Postgres (Supabase) | Depende de B5 fechado primeiro (não migrar de ficheiro para BD sem o e2e provado) | 🟡 Médio |
| **B12** (=M5) | Mover módulos sem consumidor para `packages/experimental/` | Desenvolvedor aprova a lista final antes de qualquer `git mv` (a lista original de "~14" está desactualizada desde a correcção do `Orchestrator.ts` não-mock — precisa de recontagem) | 🟢 Baixo |
| **C2** | Decisão TS vs. Python MCP (duplicação de implementação) | Desenvolvedor escolhe: TS fino delegando a Python / descontinuar TS / coexistência documentada — registar como ADR | 🟠 Alto — decisão estrutural que outros itens (C3, C4, S11) dependem indirectamente de conhecer |
| **C3** | Adoptar AgentMesh (identity/delegation) | Desenvolvedor aprova nova dependência de produção antes do merge | 🟡 Médio |
| **C4** | Adoptar Cedar (policy engine) | Idem | 🟡 Médio |
| **F7** | Decisão PMO/Project Director (queixa original que abriu a auditoria de Agentes) | Nenhum dos ~45 projectos avaliados resolve isto — é decisão de arquitectura organizacional pura, não técnica | 🟡 Médio |
| **S12** | Adicionar `.strict()` aos schemas Zod do `mcp-handler` — repo `agent-network-mcp` (separado) | Requer sessão dedicada nesse outro repo | 🟠 Alto (mas fora deste repo) |
| **G1-G4/H/I** (~40 itens) | Clusters de trabalho futuro: agente financeiro (14), gamedev (4), avatar (3), grafo de memória (2), integração final (4), backlog de pesquisa não triado (10) | Decisões de escopo/prioridade humanas antes de qualquer execução — ver `EXECUTION-PROMPTS.md` para o detalhe item a item | 🟢 Baixo — deliberadamente deixado para depois de A-F fechados |

---

## 🔴 Bloqueado por ambiente — esta máquina não consegue avançar sem mudança de infra

| ID | Descrição | Bloqueio exacto | Desbloqueio |
|---|---|---|---|
| **D3** | DeepEval via pytest (judge local via Ollama) | ~1GB RAM livre nesta máquina; menor modelo Ollama precisa de ~1.5GB | Máquina com mais RAM, ou Ollama remoto via HTTP |
| **D4** | Ragas `ToolCallAccuracy`/`ToolCallF1` | `pip install ragas` falha a compilar `scikit-network` — precisa de MSVC Build Tools (C++), sem wheel para Python 3.14/Windows | Visual Studio Build Tools, ou Python 3.11/3.12 (wheels disponíveis), ou ambiente Linux |
| **S19** | Oracle Free Tier como infraestrutura alternativa (24GB RAM, 4 OCPU ARM) desbloquearia D3+D4 | Requer confirmar IP público, acesso SSH e decidir âmbito — **já confirmado activo (S17)**, mas âmbito de uso ainda por decidir pelo utilizador | Ver S17/S20 acima — mesma VM, uso ainda por decidir |

---

## Ordem de execução sugerida

1. **Crítico de segurança primeiro** (fora do controlo directo desta sessão, mas é o que desbloqueia mais coisas): S15a + S17/S20 (rotação de credenciais, ambos já em curso pelo utilizador).
2. **100% Claude, alto valor, sem dependência:** B7 (expor langgraph+edit via MCP), E8 (script `knowledge_sources`), S24 (testes de `MCPServer.ts` na parte não-auth).
3. **Decisões humanas rápidas que desbloqueiam mais trabalho:** A23/S13 (CORS — 1 lista de origens), C2 (ADR TS-vs-Python, desbloqueia clareza sobre C3/C4/S11), A8 (key real do MCPServer — desbloqueia S11 e a parte crítica do S24).
4. **Cadeia B3→B5→B6** (precisa do `.env` real do Desenvolvedor) — uma vez desbloqueada, é a validação mais importante pendente ("o pipeline TS funciona ponta-a-ponta?").
5. **Resto do Grupo D (D5-D7)** — 100% Claude, sem pressa.
6. **Grupo E restante (E1-E7, E9)** — mecânico, baixo risco, pode ser feito em qualquer ordem.
7. **A9/A10** — assim que houver uma janela com rede liberada.
8. **Grupos G1-J** — só depois de A-F genuinamente fechados; G1 (financeiro) sozinho é maior que todo o Grupo A.

---

## Nota sobre completude

Cruzado contra `EXECUTION-PROMPTS.md` linha a linha (todos os 23+13+7+10+9+10+14+4+3+2+4+11+7 itens dos Grupos A-J, mais S15a/S15b/S18) e contra `STATUS.md` (secções 🔴🟠🟡🟢, checklist de 20 itens, mapeamento G1-G7, `## Done`). Nenhum item pendente de `EXECUTION-PROMPTS.md` ficou de fora desta lista — os únicos omitidos são os já fechados (Done/JÁ FEITO/N/A confirmado) e os ~30 itens dos Grupos G1-J que são resumidos como um bloco único (detalhe item-a-item preservado no documento original, não duplicado aqui para manter este relatório legível).

**Auto-crítica:** não recontei manualmente cada um dos ~40 itens dos Grupos G1-J individualmente neste documento (resumidos em bloco) — se algum deles tiver uma dependência ou prioridade especial não capturada no resumo, só está visível no `EXECUTION-PROMPTS.md` original.
