# Política de Privacidade e Protecção de Dados

**Versão:** 1.0. **Em vigor desde:** 2026-10-07.
**Aplica-se a:** este setup de agentes, o `network-agents-setup` (NAS, runner e agentes) e o `agent-network-mcp` (ANM, servidor MCP e memória no Supabase), e a qualquer cópia privada importada a partir dele (§2).
**Leis:** Lei n.º 13.709/2018 (LGPD, Brasil) e Regulamento (UE) 2016/679 (RGPD/GDPR). Aplica-se a lei do titular e do estabelecimento do responsável. Havendo diferença, aplica-se a regra mais protectora para o titular.
**Enquadramento:** avaliação de impacto em [`AI-MANAGEMENT-SYSTEM.md`](./AI-MANAGEMENT-SYSTEM.md) §5 (ISO/IEC 42001, 6.1.4). Mapeamento em [`ISO-42001-MAPPING.md`](./ISO-42001-MAPPING.md).

## 1. Responsável pelo tratamento e contacto

- **Responsável (controlador, LGPD art. 5.º VI; *controller*, GDPR art. 4.º 7):** quem implanta e opera este setup, isto é, quem detém o projecto Supabase, o deployment Vercel e as chaves de API. Num repo privado importado, é a entidade que o importa.
- **Contacto para privacidade:** o endereço em `config/deployment.yaml → privacy_contact`. Num repo marcado `repo_visibility: private` que trate dados de clientes, o campo é **obrigatório**: o teste `runner/tests/test_privacy_separation.py` falha se estiver vazio ou não for um e-mail.
- **Encarregado (DPO):**
  - LGPD: agentes de tratamento de pequeno porte estão dispensados de o indicar (Resolução CD/ANPD n.º 2/2022), mas o canal acima cumpre a obrigação de comunicação com os titulares;
  - GDPR: não é exigido (art. 37.º: não há controlo regular e sistemático em grande escala nem categorias especiais de dados);
  - quem ultrapassar esses limites indica um encarregado e regista-o aqui.

## 2. Repositório público vs. repositório privado

| | Repo **público** (este) | Repo **privado** (importado) |
|---|---|---|
| `config/deployment.yaml → repo_visibility` | `public` | `private` |
| Dados de clientes | **nunca**. Nem ficheiros `memory/<cliente>/`, nem exportações de tabelas, nem fixtures com dados reais | podem existir, nas localizações do §4 |
| `memory/*/` no `.gitignore` | sim, e um teste falha se algum ficheiro de cliente for versionado | recomendado manter: a memória por cliente fica fora do git (apagar um ficheiro do git não o apaga do histórico) |
| Contacto de privacidade | opcional | obrigatório (§1) |
| Conteúdo | código, documentação, conhecimento curado (`docs/knowledge/`), exemplos sintéticos | o mesmo, mais a configuração do responsável |

**Regra:** o repo público serve de modelo e de portfólio. Os dados de clientes vivem no Supabase e, quando existem ficheiros, fora do git.

## 3. Que dados são tratados

| Categoria | Titulares | Conteúdo | Origem |
|---|---|---|---|
| **Memória de trabalho do cliente** (`client_memory`) | clientes e pessoas de contacto do cliente | factos do projecto, preferências, decisões; pode incluir nomes, cargos e e-mails profissionais | escrita pelo responsável a partir do contrato e das reuniões |
| **Memória L4** (`memory_l4`) | clientes e terceiros referidos no trabalho | afirmações curtas (`subject`, `statement`) com âmbito (`scope_kind`, `scope_id`), etiquetas e um vector (`embedding`) | proposta pelos agentes; **só fica activa com aprovação humana** (`promote` exige `human:<id>`) |
| **Registo de execuções** (`agent_log`) | utilizadores do MCP | projecto, agente, resumo da execução, sucesso, custo estimado, origem | servidor MCP, a cada chamada |
| **Estado de projecto** (`project_state`) | utilizadores do MCP | pares chave/valor por projecto, autor da alteração (`updated_by`) | agentes e operador |
| **Uso de tokens** (`token_usage`) | — (sem conteúdo de prompts) | contagens, modelo, identificadores de run | runner e MCP |
| **Conteúdo público de terceiros** (`transcripts`, `image_posts`, `scrapes`) | autores de vídeos, publicações e páginas públicas | título, autor (`uploader`), descrição, transcrição ou texto, URL | ferramentas de análise de conteúdo público, a pedido do operador |
| **Conhecimento** (`knowledge_chunks`, `knowledge_sources`) | em regra, nenhum; documentos de cliente só se o responsável os ingerir | trechos de documentos com proveniência | ingestão a partir do `MANIFEST` |
| **Dados técnicos** (`code_tasks`, `visual_reviews`, `ci_debug_logs`) | o próprio operador | prompts técnicos, capturas dos sites do operador, logs | ferramentas internas |

**Não são tratados:**
- categorias especiais (saúde, biometria, origem racial ou étnica, convicções, vida sexual; LGPD art. 5.º II, GDPR art. 9.º);
- dados de menores de forma intencional;
- dados de pagamento.

Se um destes dados aparecer, é eliminado e tratado como incidente (§11).

## 4. Onde estão

| Dados | Localização | Região |
|---|---|---|
| `memory_l4`, `agent_log`, `project_state`, `token_usage`, `transcripts`, `image_posts`, `scrapes`, `knowledge_*`, `code_tasks`, `visual_reviews`, `ci_debug_logs` | Supabase (PostgreSQL), esquema `public` | **UE: Frankfurt (`eu-central-1`)** |
| Memória de trabalho por cliente | `memory/<client_id>/MEMORY.md` na máquina de quem corre o runner; **fora do git** (§2) | local do operador |
| Artefactos de um run (`pilots/<run>/`: `events.jsonl`, `result.json`, `CLIENT_MEMORY.md` copiado) | disco de quem corre o runner; `pilots/` não guarda runs reais no repo público | local do operador |
| Prompts em trânsito | Google (API Gemini), Vercel (funções do MCP) | ver §9 |

## 5. Finalidades e bases legais

| Finalidade | Dados | LGPD | GDPR |
|---|---|---|---|
| Prestar o serviço contratado: memória entre sessões e contexto de projecto para os agentes | memória do cliente, L4, `project_state` | execução de contrato (art. 7.º V) | execução de contrato (art. 6.º 1 b) |
| Operar, auditar e proteger o serviço (registos, custos, segurança) | `agent_log`, `token_usage`, dados técnicos | legítimo interesse (art. 7.º IX, art. 10) e cumprimento de obrigação legal quando aplicável (art. 7.º II) | interesses legítimos (art. 6.º 1 f) |
| Analisar conteúdo publicado pelos próprios autores (estudo de mercado, referências criativas) | conteúdo público de terceiros | legítimo interesse, respeitando a finalidade e a boa-fé da publicação (art. 7.º IX e §§ 3.º e 4.º) | interesses legítimos (art. 6.º 1 f), com teste de ponderação (§12) |
| Dados que o cliente queira partilhar fora do âmbito do contrato | qualquer | consentimento (art. 7.º I, art. 8.º), revogável a qualquer momento | consentimento (art. 6.º 1 a, art. 7.º) |

**Não há:** venda de dados, publicidade, perfis de marketing, nem treino de modelos próprios com dados de clientes.

## 6. Decisões automatizadas

Os agentes produzem rascunhos, análises e propostas. **Nenhuma decisão com efeitos jurídicos ou igualmente significativos sobre uma pessoa é tomada só por meios automatizados** (GDPR art. 22.º):
- as áreas `legal`, `finance` e `security` exigem aprovação humana (`config/areas.yaml`, `hitl: required`);
- a memória L4 só fica activa com aprovação humana.

O titular pode pedir a revisão de qualquer resultado que o afecte (LGPD art. 20).

## 7. Retenção

| Dados | Prazo | Como se cumpre |
|---|---|---|
| Memória do cliente, L4, `project_state` e `agent_log` do projecto do cliente | **enquanto durar o contrato + 90 dias** | no fim do contrato, o operador marca `expires_at` na L4, apaga a pasta `memory/<client_id>/` e corre a eliminação por `project` (procedimento em §8). Hoje não há purga automática por data: **GOV-RET-1** |
| `token_usage` (sem conteúdo) | 24 meses (custos e auditoria) | idem, GOV-RET-1 |
| Conteúdo público de terceiros | **12 meses** após a recolha, ou até o titular se opor | a função `cleanup_old_transcripts_if_needed` só apaga por tamanho da base de dados (acima de 70 % de 500 MB), não por idade: **GOV-RET-1** |
| Artefactos locais de runs | apagados no fim do trabalho, no máximo com o contrato + 90 dias | responsabilidade de quem corre o runner |
| Cópias de segurança do Supabase | o ciclo do plano Supabase | um dado apagado sai das cópias quando o ciclo roda |

Depois do prazo, os dados são eliminados ou anonimizados (LGPD art. 16; GDPR art. 5.º 1 e).

## 8. Direitos do titular e como exercê-los

| Direito | LGPD (art. 18) | GDPR | O que fazemos |
|---|---|---|---|
| Confirmação e **acesso** | I, II | art. 15.º | exportação dos registos do titular (L4 por `scope_id`, linhas por `project`, ficheiro de memória) |
| **Correcção** | III | art. 16.º | edição; na L4, uma afirmação nova substitui a antiga (`supersedes`) |
| **Eliminação**, anonimização, bloqueio | IV, VI | art. 17.º, 18.º | `memory_l4.forget(...)`; `DELETE` por `project`/`scope_id` nas tabelas do §4; remoção do ficheiro `memory/<client_id>/` |
| **Portabilidade** | V | art. 20.º | JSON estruturado com os registos do titular |
| Informação sobre partilhas | VII | art. 13.º, 14.º | lista de sub-processadores (§9) |
| Revogação do consentimento | IX | art. 7.º 3 | efeito imediato para o futuro |
| **Oposição** (incluindo ao conteúdo público analisado) | § 2.º | art. 21.º | eliminação das linhas do autor em `transcripts`, `image_posts` e `scrapes` |
| Revisão de decisões automatizadas | art. 20 | art. 22.º | revisão humana (§6) |
| Reclamação à autoridade | — | art. 77.º | ANPD (Brasil) ou a autoridade de controlo do Estado-Membro (em Portugal, a CNPD) |

**Como exercer:**
1. e-mail para o contacto do §1, com o pedido e um dado que identifique o registo (nome do projecto, URL do conteúdo, etc.);
2. confirmamos a identidade sem pedir mais dados do que os necessários;
3. **resposta:** até 15 dias (LGPD art. 19 II) e, no máximo, 1 mês (GDPR art. 12.º 3, prorrogável por 2 meses em pedidos complexos, com aviso). Aplica-se o prazo mais curto;
4. gratuito, salvo pedidos manifestamente infundados ou excessivos.

## 9. Sub-processadores (operadores)

| Sub-processador | Função | Dados | Localização | Garantia |
|---|---|---|---|---|
| **Supabase** | base de dados (memória, registos, conhecimento) | todas as tabelas do §4 | UE (Frankfurt) | DPA do Supabase; dados em repouso na UE |
| **Vercel** | alojamento do servidor MCP (funções serverless) | pedidos e respostas do MCP em trânsito | global (EUA e edge) | DPA da Vercel; SCC ou EU-US Data Privacy Framework (DPF), conforme a certificação em vigor |
| **Google (API Gemini)** | modelo de linguagem dos agentes, do router e dos conselhos | prompts, que podem conter memória do cliente | EUA e global | termos da API Gemini; **ver a regra abaixo** |
| **GitHub (Actions)** | execução de workflows (ex.: transcrição de conteúdo público) | conteúdo público processado; segredos cifrados | EUA | DPA da GitHub; SCC/DPF |
| **Oracle Cloud** | VM do `bridge-worker`, quando activo | pedidos encaminhados pelo bridge | região da VM | DPA da Oracle |

**Regra do Gemini.** No nível **gratuito** (*Unpaid Services*), a Google usa o conteúdo enviado para melhorar os seus produtos, e revisores humanos podem lê-lo. No nível **pago**, não o usa para isso: só o regista por tempo limitado para detectar abusos. Por isso:
- **dados pessoais de clientes só seguem para o Gemini em nível pago** (ou num modelo com garantia equivalente);
- no nível gratuito, só conteúdo sem dados pessoais de clientes (conhecimento curado, conteúdo público, testes);
- **quem importar o setup com o objectivo de custo zero não pode pôr dados de clientes na memória** até ter uma chave paga.

A lista de sub-processadores é actualizada **antes** de se acrescentar um novo (AIMS §7).

## 10. Transferências internacionais

- **Armazenamento:** os dados em repouso ficam na UE (Supabase, Frankfurt).
- **Para fora da UE** (Google, Vercel, GitHub; EUA):
  - **GDPR (cap. V):** decisão de adequação (EU-US DPF) para os sub-processadores certificados; os restantes, cláusulas contratuais-tipo (Decisão (UE) 2021/914) dos respectivos DPA.
  - **LGPD (art. 33):** cláusulas-padrão contratuais (Resolução CD/ANPD n.º 19/2024) quando o sub-processador as ofereça, ou a necessidade para a execução do contrato com o titular (art. 33 IX, com art. 7.º V).
- O titular pode pedir informação sobre o mecanismo usado em cada transferência (§8).

## 11. Segurança

| Medida | Onde |
|---|---|
| **RLS activo** em todas as tabelas com dados do §3; o acesso de servidor é feito com a `service_role`, que só existe no backend (variáveis de ambiente da Vercel e do runner), nunca no cliente nem no git | Supabase; `scripts/migrations/enable_rls_knowledge_tables.sql` |
| Servidor MCP **fail-closed**: sem `MCP_API_KEY` válida, não responde | ANM, `app/api/mcp/route.js` |
| **Deny-by-default**: scripts de skills só com allow-list e pins sha256 (`config/skills.yaml`); ficheiros do repo só por lista explícita, com denylist de segredos (`repo_files`); nível `act` proibido em produção | `runner/plan_runner/skill_activation.py`, `repo_files.py`, `capabilities.py` |
| Aprovação humana nas áreas sensíveis e na memória L4 | `config/areas.yaml`; `memory_l4.promote` |
| Segredos nunca no git: gitleaks em cada PR, e antes de cada commit | `.github/workflows/security-scan.yml` |
| Proveniência do conhecimento (fonte, URI, datas, validade) | F3a/F3b |
| Tecto de tokens e de custo por área | `docs/ops/BUDGET.md` |

**Incidentes:**
- comunicação à ANPD e aos titulares afectados em **3 dias úteis** (LGPD art. 48; Resolução CD/ANPD n.º 15/2024);
- à autoridade de controlo da UE em **72 horas** (GDPR art. 33.º), e aos titulares sem demora quando o risco for elevado (art. 34.º).

Processo interno em AIMS §9.

## 12. Avaliação de impacto e ponderação

A avaliação de impacto (ISO/IEC 42001 6.1.4; LGPD art. 38 – relatório de impacto; GDPR art. 35.º) está em [`AI-MANAGEMENT-SYSTEM.md`](./AI-MANAGEMENT-SYSTEM.md) §5. Inclui o teste de ponderação do legítimo interesse para o conteúdo público de terceiros. É revista quando aparece uma categoria nova de dados, um sub-processador novo, o 1.º cliente real ou uma capacidade nova de tools (P-37).

## 13. Alterações a esta política

- Versionada no git: cada alteração é um PR com o motivo, aprovado pelo responsável (maestro).
- Uma alteração **material** (nova finalidade, novo sub-processador, novo tipo de dados ou prazo maior) é comunicada aos clientes com **30 dias** de antecedência. Quando a base legal é o consentimento, é pedido de novo.
- Revisão obrigatória semestral, junto com o AIMS (P-40).

| Versão | Data | Alteração |
|---|---|---|
| 1.0 | 2026-10-07 | Primeira versão (GOV-IMPACT-1) |
