# Sistema de Gestão de IA (AIMS): política

**Referencial:** ISO/IEC 42001:2023, como **alinhamento voluntário**. Não é uma certificação, nem uma alegação de conformidade: certificar exige auditoria externa por um organismo acreditado.
**Decisão:** P-40 (maestro, 2026-10-07): âmbito NAS + ANM; papéis maestro / DEV / Claude; auditoria interna trimestral e revisão desta política semestral.
**Mapeamento cláusula a cláusula e Declaração de Aplicabilidade:** [`ISO-42001-MAPPING.md`](./ISO-42001-MAPPING.md).
**Estado dos pendentes:** `docs/initiatives/PENDENCIAS.md` (único documento de estado). Lacunas deste AIMS: **GOV-42001-1**. Avaliação de impacto: **GOV-IMPACT-1**, fechada com a [política de privacidade](./PRIVACY-POLICY.md) (§5). Seguimento: GOV-RET-1 (purga por data). GOV-PRIV-1 resolvido com a opção C (MCP #20); a opção A (limpar o histórico) é o GOV-PRIV-2.
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
9. **Dados pessoais.** Dados de clientes nunca no repo público (§11). Dados de clientes só seguem para o Gemini em nível pago. Tratamento conforme a [`PRIVACY-POLICY.md`](./PRIVACY-POLICY.md) (LGPD e GDPR).

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

**Feita a 2026-10-07 (GOV-IMPACT-1).** Política que dela resulta: [`PRIVACY-POLICY.md`](./PRIVACY-POLICY.md). Serve também de relatório de impacto à protecção de dados (LGPD art. 38) e de avaliação de impacto (GDPR art. 35.º) para o âmbito actual.

### 5.1 Processo (A.5.2) e documentação (A.5.3)

- **Quem:** o Claude prepara, o DEV confirma o que existe em produção, o maestro aceita o risco residual.
- **Onde fica:** esta secção, versionada no git. Cada revisão é um PR.
- **Quando se repete** (8.4):
  - categoria nova de dados ou tabela nova com dados pessoais;
  - sub-processador novo;
  - **1.º cliente real** ou 1.º `memory/<client_id>/MEMORY.md`;
  - capacidade nova de tools (P-37);
  - incidente;
  - e sempre na revisão semestral.

### 5.2 Estado medido (2026-10-07, SELECTs só de leitura ao Supabase do ANM)

| Fonte | Linhas | Dados pessoais |
|---|---:|---|
| `memory/<client_id>/MEMORY.md` (NAS) | 0 ficheiros | não |
| `memory_l4` | 0 | não |
| `agent_log` | 119 | nenhum e-mail, telefone ou CPF detectado (padrões; só projectos internos e produtos próprios) |
| `project_state` | 19 | idem |
| `transcripts` | 99 (52 autores, 2 plataformas) | **sim:** autor, descrição e fala de conteúdo **público** de terceiros |
| `image_posts` | 9 (1 autor) | sim, idem |
| `scrapes` | 2 | possível (páginas públicas) |

**Conclusão:**
- **Não há dados de clientes.**
- Há dados pessoais de terceiros obtidos de **conteúdo público**, cobertos pela política (§3, §5 e §7).
- O repo público do ANM versionava `transcripts/latest.json`, com a transcrição de um vídeo público de terceiros → **GOV-PRIV-1, resolvido (opção C, MCP #20):** removido do git, `/transcripts/` no `.gitignore` e um teste que falha se voltar (§11).

### 5.3 Impacto em indivíduos ou grupos (A.5.4)

| Risco | Quem | Probabilidade | Gravidade | Medidas | Residual |
|---|---|---|---|---|---|
| Memória de cliente exposta no git | clientes | baixa | alta | `/memory/*/` no `.gitignore`; `repo_visibility` + `test_privacy_separation.py`; dados no Supabase com RLS | baixo |
| Dados de cliente usados pela Google para treino (Gemini gratuito) | clientes | **alta** se houver dados de cliente no tier gratuito | média | regra da política §9: **dados de clientes só com Gemini pago**; no tier gratuito, só conteúdo sem dados de clientes | baixo, se a regra for cumprida |
| Facto errado sobre uma pessoa memorizado e reutilizado | clientes, terceiros | média | média | L4 só activa com aprovação humana (`promote`); correcção por `supersedes`; direito de rectificação | baixo |
| Prompt injection que leva um agente a revelar memória de outro cliente | clientes | baixa | alta | memória injectada só para o `client_id` do plano; o worker não tem tools (AU-20); output de tools como dados (P-37, contrato) | baixo |
| Dados guardados além do necessário | todos | **média** | média | prazos na política §7; L4 com `expires_at`; purga diária automática nas transcrições (60 dias, `pg_cron`); nos restantes, **ainda manual** → GOV-RET-1 | médio até ao GOV-RET-1 |
| Autor de conteúdo público analisado sem saber | terceiros | média | baixa | finalidade limitada (estudo), sem perfis nem contacto, oposição a qualquer momento (política §8) | baixo |
| Decisão automatizada com efeito numa pessoa | clientes | baixa | alta | HITL obrigatório em `legal`, `finance` e `security`; nenhuma decisão só automatizada (política §6) | baixo |

**Ponderação do legítimo interesse** (conteúdo público de terceiros):
- **finalidade legítima:** estudo de mercado e referências criativas;
- **necessidade:** só título, autor, descrição e transcrição; sem contactos nem perfis;
- **expectativa do titular:** o conteúdo foi publicado abertamente pelo autor;
- **salvaguardas:** transcrições apagadas 60 dias depois da criação (purga diária automática), os outros conteúdos públicos em 12 meses, oposição e eliminação, nada publicado no repo (GOV-PRIV-1).

Resultado: **o interesse prevalece**, com as salvaguardas acima.

### 5.4 Impactos sociais (A.5.5)

O setup produz conteúdo de marketing, análises e código para o próprio operador e para clientes. Riscos sociais identificados:
- desinformação por conhecimento desactualizado: mitigada pela validade (F3b) e pela proveniência obrigatória (F3a);
- conteúdo enganoso em marketing: mitigado pelo `grounding` obrigatório e pelo `design_critic`/HITL nas áreas sensíveis;
- consumo de recursos: mitigado pelo tecto de tokens por área.

Nenhum uso previsto envolve vigilância, avaliação de pessoas, crédito, emprego ou acesso a serviços essenciais. Esses usos ficam **fora do uso previsto** (A.9.4) e exigiriam uma nova avaliação antes de qualquer trabalho.

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
| Google Gemini API | modelo dos workers, do router e dos conselhos | prompts (que podem incluir memória de cliente) | chave só por header; tecto de tokens; tier gratuito **só sem dados de clientes** (no gratuito, a Google usa o conteúdo para melhorar produtos): política de privacidade §9 |
| Supabase | memória, conhecimento, ledger | conteúdo de memória, chunks, uso | SQL de RLS das tabelas de conhecimento versionado (`scripts/migrations/enable_rls_knowledge_tables.sql`); service role só no servidor |
| Vercel | alojamento do MCP | pedidos MCP | `MCP_API_KEY` fail-closed; protecção de deployment |
| skills.sh (API) | pesquisa de skills externas, opt-in | só a query de pesquisa | HTTPS, sem redirects, timeout; candidatas nunca instaladas |
| GitHub (Actions) | workflows (ex.: transcrição de conteúdo público) | conteúdo público processado; segredos cifrados | segredos só como secrets do repo; nada de dados de clientes nos logs |
| Oracle Cloud | VM do `bridge-worker`, quando activo | pedidos encaminhados | VM do operador (S20) |
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

## 11. Repositório público e repositório privado

| | Público (este repo, e o `agent-network-mcp`) | Privado (cópia importada para trabalhar com clientes) |
|---|---|---|
| Para quê | modelo, portfólio, código e conhecimento curado | o mesmo setup a operar com clientes reais |
| `config/deployment.yaml` | `repo_visibility: public` | `repo_visibility: private` + `privacy_contact` (e-mail do responsável) |
| Dados de clientes | **nunca**: nem `memory/<cliente>/`, nem exportações de tabelas, nem fixtures reais, nem transcrições ou artefactos de runs reais | no Supabase (UE) e, quando há ficheiros, fora do git |
| Guarda | `.gitignore` (`/memory/*/`) + `runner/tests/test_privacy_separation.py` (falha se um ficheiro de cliente for versionado) | o mesmo teste exige o `privacy_contact` |

**Para importar para um repo privado:**
1. muda `repo_visibility` para `private`;
2. preenche o `privacy_contact`;
3. revê a lista de sub-processadores (política §9);
4. usa uma chave **paga** do Gemini antes de pôr dados de clientes na memória;
5. repete a avaliação de impacto (§5.1) com o 1.º cliente.

**O repo público não guarda dados de clientes.** Verificado a 2026-10-07: 0 ficheiros `memory/<cliente>/` no git do NAS e 0 linhas na `memory_l4`. A excepção encontrada (uma transcrição de terceiros versionada no ANM) foi resolvida pelo GOV-PRIV-1 (§11.1).

### 11.1 Conteúdo de terceiros: transcrições (GOV-PRIV-1, opção C)

| Opção | O quê | Estado |
|---|---|---|
| **C (adoptada)** | As transcrições vivem **só no Supabase** (`public.transcripts`, gravadas pelo `transcribe.yml`). O repo público deixa de as versionar: `git rm --cached transcripts/latest.json`, `/transcripts/` no `.gitignore`, uma secção "Dados e privacidade" no README do MCP, e `tests/publicRepo.test.mjs`, que falha se uma transcrição voltar ao git | MCP #20 |
| A (upgrade) | Limpar também o **histórico** do git (o ficheiro continua no commit `fe3cc90`, de 2026-08-10). Exige `git filter-repo` + force push na `main` do MCP, e quem tiver um clone tem de clonar de novo | **GOV-PRIV-2** (decisão do DEV) |

**Como a separação funciona, nos dois repos:**

| Camada | NAS | MCP (ANM) |
|---|---|---|
| Onde vivem os dados | Supabase (UE) e, para a memória por cliente, ficheiros locais fora do git | Supabase (UE) |
| O que o git ignora | `/memory/*/` | `/transcripts/` |
| Teste que falha se algo escapar | `runner/tests/test_privacy_separation.py` (corre no CI) | `tests/publicRepo.test.mjs` (`npm test`; o MCP não tem CI para isto) |
| Declaração | `config/deployment.yaml` (`repo_visibility: public`) | secção "Dados e privacidade" do README |

