# Checklist cronológico — Item 13 + Marketing

**Objectivo:** não perder o fio. Ordem de execução sugerida.  
**Âmbito:** setup lab (`network-agents-setup`). Produção MCP só com decisão explícita.  
**Legenda de tipo**

| Tag | Significado |
|-----|-------------|
| **DOC** | Documentação e regras (L0 / playbooks / policy) |
| **DEV** | Desenvolvimento (runner, schemas, wiring) |
| **ING** | Ingestão de conhecimento (L3 skills / L5 packs) |
| **TEST** | Teste e validação |

**Estados:** `[ ]` todo · `[~]` parcial / já avançado no repo · `[x]` feito de forma verificável

Marcações iniciais reflectem o estado **remoto GitHub** à data deste ficheiro (docs + runner stub + templates; pull local pode estar pendente).

---

# PARTE A — Fundação comum (antes de “só Item 13” ou “só marketing”)

Ordem fixa: sem isto, Item 13 e marketing ficam soltos.

| # | Tipo | Item | Critério de fecho |
|---|------|------|-------------------|
| A1 | DOC | Constitution / policy lab≠prod, least privilege, publish só HITL | Ficheiro de regras referenciado pelo orchestrator |
| A2 | DOC | Memória L0–L6 + contratos remember/recall/retrieve | `docs/architecture/memory/` presente e lido pela equipa |
| A3 | DOC | Orquestrador marketing + relação Item 13 (sem orchestrator Item 13 isolado) | `docs/orchestration/marketing/` + `item-13-and-marketing.md` |
| A4 | DEV | Runner plan-execute (dry-run / stub / external + HITL resume) | `runner/` executa template sem erro |
| A5 | TEST | `dry-run` no `seo-article.plan.yaml` | JSON com ordem de steps correcta |
| A6 | TEST | `stub` + `resume --decision approve` | `events.jsonl` + `status.json` state `done` |

**Estado esperado agora:** A2–A3 `[~]`/`[x]` no remoto; A4 `[x]` código no remoto; A5–A6 `[ ]` até correres localmente após `git pull`.

---

# PARTE B — Item 13 (AI Findability)

Item 13 **não** é vertical própria: é **método + checks** dentro de conteúdo/SEO.

## B0 — Já existente (verificar, não recomeçar)

| # | Tipo | Item | Critério |
|---|------|------|----------|
| B0.1 | DOC | Playbook canónico Item 13 | `docs/item-13-ai-findability.md` legível PASS/FAIL |
| B0.2 | ING | Knowledge operacional / chunks | `docs/knowledge/ai-findability.md` (ou equivalente) |
| B0.3 | DOC | Schemas SeoBrief / CriticReport com campos Item 13 | schemas em plan-execute ou docs |
| B0.4 | DOC | Item 13 nos steps seo_brief + critic do template seo_article | YAML referencia critic_item13 / notas |

## B1 — Documentação e regras (fechar ambiguidades)

| # | Tipo | Item | Critério de fecho |
|---|------|------|-------------------|
| B1.1 | DOC | Checklist PASS/FAIL Item 13 **uma página** (aceitação) | Lista numerada; critic mapeia 1:1 |
| B1.2 | DOC | O que é P0 vs P1 vs P2 (prioridade de implementação em peças) | Tabela no playbook |
| B1.3 | DOC | Regra: falha Item 13 → `on_fail` human vs block | Escrito no ORCHESTRATOR / template |
| B1.4 | DOC | Separar “método Item 13” de “site X migrado” | Nota explícita (genérico ≠ cliente) |

## B2 — Ingestão de conhecimento

| # | Tipo | Item | Critério de fecho |
|---|------|------|-------------------|
| B2.1 | ING | Pack L5: entidades, FAQ, citabilidade, schema markup, anti-padrões | Ficheiros em `docs/knowledge/` estáveis |
| B2.2 | ING | Skill L3 `seo_brief` com triggers + done_when Item 13 | SKILL.md ou secção skill |
| B2.3 | ING | Skill L3 `critic_item13` com rubrica PASS/FAIL | SKILL.md alinhada a B1.1 |
| B2.4 | ING | (Opcional) exemplos few-shot bom/mau | 2–3 pares em knowledge |
| B2.5 | DEV | (Depois) indexar pack Item 13 em KB `kb_method` | retrieve_knowledge devolve chunks |

## B3 — Desenvolvimento

| # | Tipo | Item | Critério de fecho |
|---|------|------|-------------------|
| B3.1 | DEV | Validar JSON de SeoBrief/Critic no runner (schema check) | Step falha se schema inválido |
| B3.2 | DEV | Mode `external`: request inclui bloco Item 13 obrigatório | `request.json` documenta campos |
| B3.3 | DEV | (Opcional) action `seo_tech_audit` no path de página | Template ou step opcional |

## B4 — Teste e validação

| # | Tipo | Item | Critério de fecho |
|---|------|------|-------------------|
| B4.1 | TEST | Fixture: brief que **falha** Item 13 → critic `publish_ready: false` | Caso guardado em `pilots/` |
| B4.2 | TEST | Fixture: brief/copy que **passa** Item 13 → ready true ou só P2 gaps | Caso guardado |
| B4.3 | TEST | Stub run seo_article até HITL | events: step_finished × N + human_gate |
| B4.4 | TEST | Revisão humana da rubrica B1.1 em 1 peça real anónima | Notas no pilot |
| B4.5 | TEST | Regressão: mudar playbook não quebra template YAML | dry-run OK |

## B — Definição de “Item 13 fechado (método v1)”

Tudo B1 + B2.1–B2.3 + B4.1–B4.3.  
**Não** exige: todos os sites do mundo optimizados, nem MCP prod.

---

# PARTE C — Marketing (vertical)

## C0 — Já existente (verificar)

| # | Tipo | Item | Critério |
|---|------|------|----------|
| C0.1 | DOC | ORCHESTRATOR.md + policy | Publish/spend HITL; sem admin |
| C0.2 | DOC | Templates seo_article, social_pack, internal_brief, approval_rounds | YAML no repo |
| C0.3 | DOC | Registry actions marketing | `registry-actions.md` |
| C0.4 | DOC | Providências ASV M-01…M-15 | `PROVIDENCIAS-ADOTADAS.md` |
| C0.5 | ING | Knowledge packs por especialidade (se já no repo) | `docs/knowledge/` |
| C0.6 | DOC | Portfolio / one-pager | docs portfolio |

## C1 — Documentação e regras

| # | Tipo | Item | Critério de fecho |
|---|------|------|-------------------|
| C1.1 | DOC | Tabela deliverable_type → template completo (todos os tipos v1) | Secção 4 ORCHESTRATOR actualizada |
| C1.2 | DOC | Matriz role → action → skill path | Uma linha por role core |
| C1.3 | DOC | HITL matrix (draft / publish / spend / 3 rodadas) | Tabela única |
| C1.4 | DOC | ARTIFACT-NAMING obrigatório nos templates | Paths NN-kebab |
| C1.5 | DOC | Explicit ban: auto-post, fake growth, store passwords | Policy L0/orchestrator |
| C1.6 | DOC | Quais roles são P0 (MVP) vs P1 | Lista curta P0 |

### C1.6 sugerido — P0 MVP marketing

1. orchestrator (plan only)  
2. research  
3. seo_brief (+ Item 13)  
4. copy_answer_first  
5. critic_item13  
6. creative_review (opcional no MVP se critic cobre)  
7. plan_approve (HITL)  

P1: trend_hunter, copy_social, storytelling, media_buyer, performance_analyst, ugc, influencer, editor_video, design_ui/ux, status_report, seo_tech_audit.

## C2 — Ingestão de conhecimento (por ordem P0 → P1)

| # | Tipo | Item | Critério de fecho |
|---|------|------|-------------------|
| C2.1 | ING | Skill research | triggers, inputs, done_when, anti-padrões |
| C2.2 | ING | Skill seo_brief | + link Item 13 pack |
| C2.3 | ING | Skill copy_answer_first | |
| C2.4 | ING | Skill critic_item13 | |
| C2.5 | ING | Pack brand-kit **genérico** (template vazio para project) | `docs/knowledge/marketing/brand-kit-template.md` |
| C2.6 | ING | Rubrica creative-review (já) + skill creative_review | |
| C2.7 | ING | Checklist seo_tech_audit (já) + skill | |
| C2.8 | ING | P1 skills: social, storytelling, media_buyer, performance, ugc, … | Uma skill estável por action P1 |
| C2.9 | ING | (Depois) KB embed `kb_marketing` + `kb_method` | retrieve real |

## C3 — Desenvolvimento

| # | Tipo | Item | Critério de fecho |
|---|------|------|-------------------|
| C3.1 | DEV | Templates YAML para P0 todos dry-run OK | plan_runner dry-run |
| C3.2 | DEV | Templates P1: campaign_brief, performance_review, content_sprint_2w | ficheiros + registry |
| C3.3 | DEV | Runner: schema validation opcional por output_schema | falha controlada |
| C3.4 | DEV | Mode external documentado para workers humanos/outras IAs | README runner |
| C3.5 | DEV | Mapa knowledge_refs no plan → paths repo | campo usado nos templates P0 |
| C3.6 | DEV | (Opcional) CLI `plan_runner list-templates` | DX |
| C3.7 | DEV | **Não** ligar MCP prod neste checklist | gate explícito |

## C4 — Teste e validação

| # | Tipo | Item | Critério de fecho |
|---|------|------|-------------------|
| C4.1 | TEST | dry-run todos templates P0 | exit 0 |
| C4.2 | TEST | stub seo_article → HITL → resume approve → done | events completos |
| C4.3 | TEST | stub social_pack → HITL | idem |
| C4.4 | TEST | approval-rounds pausa em cada gate | 2+ human_gate_requested |
| C4.5 | TEST | Caso external: um step com result.json manual | step_finished |
| C4.6 | TEST | Revisão humana: 1 peça gerada (external/outra IA) passa critic | pilot documentado |
| C4.7 | TEST | Checklist “MVP marketing método v1” abaixo | todos `[x]` |

## C — Definição de “Marketing método v1 fechado”

- C1 completo  
- C2.1–C2.5  
- C3.1, C3.4, C3.5  
- C4.1–C4.4  
- Item 13 método v1 (Parte B) **incluído** no path seo_article  

**Não** exige: campanhas reais em redes, media buy, nem admin de agência.

---

# PARTE D — Cronologia única (ordem de trabalho recomendada)

Trabalhar **de cima para baixo**. Não saltar TEST do bloco anterior.

| Fase | Quando | Itens |
|------|--------|-------|
| **0** | Já / já | A1–A3, B0, C0 — inventário e leitura |
| **1** | Dia 1 local | `git pull` · A4–A6 (provar runner) |
| **2** | A seguir | B1 (regras Item 13 aceites) |
| **3** | | B2.1–B2.3 + C2.1–C2.4 (skills P0 + knowledge Item 13) |
| **4** | | C1.1–C1.6 (fechar regras marketing MVP) |
| **5** | | C3.1 + C4.1–C4.2 (templates P0 + stub seo) |
| **6** | | B3.1 se possível + B4.1–B4.3 (validação Item 13) |
| **7** | | C4.3–C4.4 + C2.5–C2.6 |
| **8** | | C3.2 templates P1 + C2.8 skills P1 (incremental) |
| **9** | Opcional | B2.5 / C2.9 RAG real · C3.3 schema no runner |
| **10** | Só com decisão | Wiring MCP produção / canais reais |

---

# PARTE E — Quadro rápido “onde estamos”

Preencher na equipa (actualizar este ficheiro ou copiar para pending):

| Área | DOC | DEV | ING | TEST |
|------|-----|-----|-----|------|
| Fundação A | | | — | |
| Item 13 B | | | | |
| Marketing C | | | | |

Sugestão de preenchimento inicial (remoto, sem pull local validado):

| Área | DOC | DEV | ING | TEST |
|------|-----|-----|-----|------|
| Fundação A | forte | runner existe | n/a | local pendente |
| Item 13 B | forte playbook | parcial schemas | knowledge no repo; skills a uniformizar | fixtures formais pendentes |
| Marketing C | orchestrator + templates | templates+runner | packs parciais | stub formal pendente |

---

# PARTE F — Fora de scope deste checklist

- Admin ASV (finanças, RH, cobrança)  
- Auto-publish redes  
- Site de cliente específico como prova do método  
- Substituir agent-network-mcp  

---

*Actualizar estados `[x]/[~]` quando um critério de fecho for verificado (idealmente com path de pilot ou comando).*
