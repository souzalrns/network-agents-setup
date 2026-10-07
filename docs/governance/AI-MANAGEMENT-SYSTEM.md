# Sistema de Gestão de IA (AIMS): política

**Referencial:** ISO/IEC 42001:2023, como **alinhamento voluntário**. Não é uma certificação, nem uma alegação de conformidade: certificar exige auditoria externa por um organismo acreditado.
**Decisão:** P-40 (maestro, 2026-10-07): âmbito NAS + ANM; papéis maestro / DEV / Claude; auditoria interna trimestral e revisão desta política semestral.
**Mapeamento cláusula a cláusula e Declaração de Aplicabilidade:** [`ISO-42001-MAPPING.md`](./ISO-42001-MAPPING.md).
**Estado dos pendentes:** `docs/initiatives/PENDENCIAS.md` (único documento de estado). Lacunas deste AIMS: **GOV-42001-1**; avaliação de impacto: **GOV-IMPACT-1**.
**Texto da norma:** este documento cita só números e títulos curtos (tradução livre). O texto da ISO/IEC 42001 é protegido por direitos de autor e não é reproduzido aqui.

## 1. Âmbito (cláusulas 4.3 e 4.4)

| Dentro | Fora |
|---|---|
| **NAS** (`souzalrns/network-agents-setup`): `runner/plan_runner/` (único execution runtime, D1), os agentes (`agents/`), as skills (`skills/`), os planos (`docs/orchestration/`), a ingestão (`scripts/ingest_*.py`) e o conhecimento (`docs/knowledge/`) | `packages/core/` e o restante TS arquivado (D1). Os módulos `ComplianceManager`, `DataGovernance` e `SecurityManager` são MOCK e **não** são evidência deste AIMS |
| **ANM** (`souzalrns/agent-network-mcp`): servidor MCP na Vercel, agentes de negócio (`lib/agents.js`) e memória no Supabase (`project_state`, `agent_log`, `token_usage`, `knowledge_chunks`, `memory_l4`) | Repos de produto que só consomem o MCP (`mesaflow-api`, `viannalegal-site`): têm o seu próprio ciclo de vida |
| Os fornecedores usados por estes dois repos (§7) | Ferramentas de desenvolvimento local que não tocam em dados de clientes |

**Partes interessadas (4.2):** o maestro (dono do produto), o DEV (operação e credenciais), os clientes cujos dados entram na memória (`memory/<client_id>/MEMORY.md` no NAS, tabelas de memória no ANM) e os recrutadores que leem o portfólio (transparência, A.8).

## 2. Política de IA (5.2, A.2.2)

Os compromissos abaixo **já estão em vigor** nos dois repos; esta política consolida-os, não inventa regras novas. Cada um aponta para onde é aplicado.

1. **Deny-by-default.**
   - Scripts das skills: `config/skills.yaml` (SEC-1.3).
   - Tools por passo: `tools_allowed` ∩ registo, quando o P-37 entrar.
   - Ficheiros do repo: denylist do `repo_files` (SEC-1).
   - Nível `act`: recusado enquanto `act_in_production: forbidden` (`capabilities.py`).
2. **Aprovação humana (HITL) obrigatória:**
   - nas áreas `legal`, `finance` e `security` (`config/areas.yaml`, `hitl: required`);
   - para promover memória L4 (`memory_l4.promote` exige `human:<id>`);
   - para qualquer acção de nível `act`.
3. **Nenhuma escrita em produção sem o DEV.** Supabase, Vercel e workflows que escrevem são decisão do DEV. O SQL é versionado, não executado pelo Claude.
4. **Nenhum segredo em commits nem em respostas.** gitleaks no CI e localmente antes de cada commit.
5. **Proveniência obrigatória no conhecimento (L5).** `match_knowledge_v2` com `citation` e `metadata` (F3a); classes de validade (F3b); cada documento no MANIFEST ou no EXCLUDED com razão (F3c).
6. **Custo controlado.** Tecto de tokens por área (`config/areas.yaml`, `docs/ops/BUDGET.md`) e custo em USD (`cost.py`). Premissa de custo zero de infraestrutura. Só licenças MIT/Apache.
7. **Contract-first** (EXECUTION-PLAN §15.4). Toda a tool ou capability nova tem, antes de código:
   - contrato, input e output;
   - policy e fronteira de segurança;
   - proveniência e estados de erro;
   - validação, observabilidade e custo;
   - **e uma linha de risco (§4) e uma linha na Declaração de Aplicabilidade** (regra acrescentada por este AIMS).
8. **Honestidade de estado.** Um item só fecha depois do merge, com evidência. Nada é "fechado só no papel" (lição do V34).

**Alinhamento com outras políticas (A.2.3):** `docs/architecture/SECURITY-AGENTS.md`, `CLAUDE.md` dos dois repos e o EXECUTION-PLAN §15. Em conflito, ganha a regra mais restritiva até o maestro decidir.

## 3. Papéis e responsabilidades (5.1, 5.3, A.3.2)

| Papel | Quem | Responsabilidades | Não pode |
|---|---|---|---|
| **Gestão de topo / dono da política** | maestro | aprovar e rever esta política; decidir A/B/C (§10 do PENDENCIAS); aceitar riscos Altos e Críticos; aprovar excepções; **merge** | delegar a aceitação de risco Alto |
| **Operador** | DEV | produção (Supabase, Vercel), credenciais e variáveis de ambiente, runs com credenciais, SELECTs de prova, workflows que escrevem | correr SQL não versionado |
| **Fornecedor e desenvolvedor de IA** | Claude (sessões Claude Code) | código, testes, documentação, propostas A/B/C com recomendação e evidência; manter o PENDENCIAS e o `PROGRESS-SESSAO.md`; reportar desvios | decidir, fazer merge, escrever em produção, imprimir ou commitar segredos, reactivar workflows pagos |

**Reporte de preocupações (A.3.3):** qualquer papel regista uma preocupação como item no `PENDENCIAS.md` §4, ou como contradição no §8. Um risco de segurança ou de dados pessoais entra com Sev Alta, no mínimo, e é dito ao maestro na mesma sessão.

## 4. Gestão de risco (6.1.2, 6.1.3, 8.2, 8.3)

- **Registo de riscos:** o próprio `PENDENCIAS.md` §4 (dono, severidade, bloqueio, evidência). Um risco de IA leva, na coluna Título, o prefixo `Risco:` ou cita a cláusula ou controlo.
- **Escala:** a coluna Sev do PENDENCIAS (Crítica · Alta · Média · Baixa).
  - **Crítica:** dano a pessoas ou dados de clientes, ou acção irreversível em produção.
  - **Alta:** fuga de dados ou segredo possível, decisão automática sem HITL numa área `hitl: required`, ou custo sem tecto.
  - **Média:** degradação de qualidade ou de proveniência, dependência sem fornecedor avaliado.
  - **Baixa:** higiene e documentação.
- **Critério de aceitação:** só o maestro aceita riscos Altos e Críticos, por escrito (decisão no §10). Médios e Baixos: o DEV ou o maestro.
- **Tratamento (6.1.3):** a Declaração de Aplicabilidade em `ISO-42001-MAPPING.md` diz, para cada controlo do Anexo A, se se aplica, como é cumprido e qual é o item que fecha a lacuna.
- **Planeamento de mudanças (6.3):** uma mudança no router, nas tools MCP ou no executor verifica o impacto no conector do Claude.ai (regra do `CLAUDE.md` do ANM) e passa pelo contract-first.

## 5. Avaliação de impacto (6.1.4, 8.4, A.5)

**Ainda não existe.** É a maior lacuna deste AIMS → **GOV-IMPACT-1** (Sev Alta). Âmbito mínimo:

- a working memory por cliente (`memory/<client_id>/MEMORY.md`, injectada no prompt: S30, `runner/plan_runner/engine.py::_load_client_memory`);
- a memória L4 (`scripts/create_memory_l4_table.sql`, `runner/plan_runner/memory_l4.py`), com retenção (`expires_at`) e esquecimento (`forget`);
- as tabelas de memória do ANM (`agent_log`, `project_state`).

Para cada uma, a avaliação responde:
- que dados pessoais entram (LGPD e GDPR);
- quem os vê;
- por quanto tempo ficam;
- como um titular pede para apagar;
- o que acontece se um prompt os expuser.

## 6. Operação e monitorização (8.1, 9.1, A.6.2.6, A.6.2.8)

- **Registos:**
  - `events.jsonl` por run (só acrescento);
  - `token_usage.jsonl` local e a tabela `token_usage` no Supabase;
  - `result.json → meta` (o que entrou no prompt);
  - `skill_activation.json` (sha256 da skill e scripts autorizados ou bloqueados).
- **Métricas que se medem hoje:**
  - `l5_eval` (`source_hit@k`, `provenance_ok`, `provenance_v2_ok`);
  - golden sets (`config/l5-golden-security.yaml`, `config/router-golden.yaml`);
  - custo por run;
  - CI (testes, gitleaks, semgrep, CodeQL).
- **Lacunas** (GOV-42001-1): retenção dos registos e detecção de adulteração (o `ActionReceipt` do ADR-001 continua por construir: B16).

## 7. Fornecedores e terceiros (A.10.2, A.10.3)

| Fornecedor | Para quê | Dados que recebe | Controlo actual |
|---|---|---|---|
| Google Gemini API | modelo dos workers, do router e dos conselhos | prompts (que podem incluir memória de cliente) | chave só por header; tecto de tokens; tier gratuito preferido |
| Supabase | memória, conhecimento, ledger | conteúdo de memória, chunks, uso | SQL de RLS das tabelas de conhecimento versionado (`scripts/migrations/enable_rls_knowledge_tables.sql`); service role só no servidor |
| Vercel | alojamento do MCP | pedidos MCP | `MCP_API_KEY` fail-closed; protecção de deployment |
| skills.sh (API) | pesquisa de skills externas, opt-in | só a query de pesquisa | HTTPS, sem redirects, timeout; candidatas nunca instaladas |
| Skills de terceiros | instruções e scripts | — | SEC-1.3 deny-by-default; `pins:` sha256; revisão humana |

Um fornecedor novo entra nesta tabela antes de ser usado (GOV-42001-1).

## 8. Excepções

Uma excepção a esta política, por exemplo `allow_scripts: true`, um passo sem HITL numa área `hitl: required`, ou um tecto de tokens desligado:
1. é aprovada pelo maestro;
2. fica registada como item `GOV-EXC-<n>` no `PENDENCIAS.md` §4, com motivo, âmbito e **data de expiração**;
3. expira sozinha na data: na auditoria trimestral, uma excepção vencida é uma não conformidade (10.2).

## 9. Incidentes (A.8.4, 10.2)

**É incidente:**
- dados de cliente ou segredos expostos;
- uma acção executada sem a aprovação humana exigida;
- escrita em produção fora do processo;
- prompt injection que mudou o comportamento de um agente;
- um tecto de custo ultrapassado.

**Resposta:**
1. o papel que detecta avisa o maestro na mesma sessão;
2. o DEV contém o problema (revoga a chave, desliga a flag, faz rollback);
3. regista-se no PENDENCIAS com Sev Alta ou Crítica e a causa;
4. a correcção entra por PR com teste de regressão.

Se houver dados pessoais, a comunicação aos titulares e às autoridades segue a lei aplicável (decisão do maestro).

## 10. Auditoria interna e revisão (9.2, 9.3, 10.1)

| Actividade | Cadência | Quem | Saída |
|---|---|---|---|
| **Auditoria interna** | **trimestral** (Janeiro, Abril, Julho, Outubro) | Claude prepara; o maestro aprova | revisão do `ISO-42001-MAPPING.md` contra o repo (o teste de evidências tem de passar), excepções vencidas, itens Altos parados; relatório em `docs/governance/audits/AAAA-Qn.md` |
| **Revisão desta política** | **semestral**, e sempre que houver uma decisão estrutural (ex.: P-37) | maestro | nova versão deste ficheiro; decisões no §10 do PENDENCIAS |
| **Melhoria contínua** | contínua | todos | itens no PENDENCIAS; contradições no §8 |

**Primeira auditoria:** 2027-01 (o trimestre seguinte a esta política).
