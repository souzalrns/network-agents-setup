# Matriz P1 — capacidades profissionais vs `network-agents-setup`

**Critério “pronto”:** knowledge + skill + agente/composição no registo + caminho de execução + validação mínima.  
**Legenda:** `ready` | `partial` | `gap`  
**Nota:** P1 = domínios profissionais. Muitos reutilizam P0 (planning, HITL, knowledge, security). Onde a área só declara keywords sem agentes, o estado é **gap** de execução, não de intenção.

---

## 1. Cybersecurity

| Capacidade | Knowledge | Skills | Tools | Agente / composição | **Ready?** | Nota |
|------------|-----------|--------|-------|---------------------|------------|------|
| Triage | pack security | `security/triage` | — | `security.triage` | **ready** | |
| Defensive audit | `SECURITY.md` | `meta/security-audit` | `repo_files`, scanners orientados | `meta.security-auditor` | **partial–ready** | L5 ingest NÃO VERIFICADO |
| Security report | pack | `security/reporter` | — | `security.reporter` | **ready** | |
| Secrets hygiene | SECURITY.md | via audit | gitleaks CI | composição | **partial** | CI em PR; histórico ignorado justificado |
| Supply chain / deps | SECURITY.md | via audit | OSV/Trivy guidance | auditor | **partial** | Sem job dedicado OSV |
| MCP surface | SECURITY.md | audit | — | auditor | **partial** | |
| Hardening recommend | — | report next_steps | — | reporter → engenharia | **partial** | PREPARE only |
| Threat model / council | councils | — | council_session | security council | **partial** | Deliberação; não pipeline diário |
| Agent red-team lab | pack §B | — | PyRIT/DeepTeam | — | **gap** | deferred, fora prod |
| SOC / SIEM / IR | — | — | — | — | **gap** | Fora de âmbito zero-custo |
| Compliance formal (ISO/SOC2) | GOVERNANCE parcial | — | — | — | **gap** | |

**Área:** `security` · **capabilities.yaml:** sim · **hitl:** required · **act:** forbidden nos agents security

---

## 2. Software engineering

| Capacidade | Knowledge | Skills | Tools | Agente | **Ready?** | Nota |
|------------|-----------|--------|-------|--------|------------|------|
| Implementation | imported TDD/prod | desenvolvimento | — | `engenharia.desenvolvimento` | **partial** | |
| TDD / tests | guia-tdd knowledge | guia-tdd (+ Claude pack longo) | — | `engenharia.guia-tdd` | **partial** | Custo tokens |
| Code review | revisor + security/DB | revisor (+ Claude pack) | — | `engenharia.revisor-codigo` | **partial** | |
| Data quality | — | qualidade-dados | — | `engenharia.qualidade-dados` | **partial** | |
| Agent architecture | ADRs, estrutura | — | — | `meta.arquitetura-agentes` | **partial** | Council architecture |
| Product/tech transversal | a11y/SEO import | — | — | `produto.produto-tech-transversal` | **partial** | |
| CI/CD / deploy | skills meta deploy, GHA | ci-cd skills (claude) | GHA | composição humana/CI | **partial** | Não capability formal |
| Repo understanding | — | — | `repo_files` | steps que declaram | **partial** | Opt-in por step |
| Refactor / migration | claude pack | skills longas | — | via desenvolvimento | **gap** | Só se skill carregada |
| Observability product | — | — | ledger tokens | — | **partial** | Runs, não APM app |

**Área:** `software` · **capabilities.yaml:** não · **hitl:** null

---

## 3. Design & media

| Capacidade | Knowledge | Skills | Tools | Agente | **Ready?** |
|------------|-----------|--------|-------|--------|------------|
| UI spec | ui.md, design/* | ui_spec | — | `design.ui` | **partial–ready** |
| UX flow | ux.md, heuristics | ux_flow | — | `design.ux` | **partial–ready** |
| UX writing | ux-writing packs | ux_writing | — | `design.ux_writer` | **partial–ready** |
| Design critic | — | design_critic | — | `design.design_critic` | **partial** |
| Identidade visual | diretor-arte, etc. | — | — | `design.identidade-visual` | **partial** |
| Video edit checklist | editor-video | — | — | `marketing.editor_video` | **partial** |

**Área:** software (design agents) + marketing (identidade) · **capabilities.yaml:** não

---

## 4. Marketing

| Capacidade | Knowledge | Skills | Tools | Agente | **Ready?** |
|------------|-----------|--------|-------|--------|------------|
| Orchestration / brief | orquestrador, playbook | internal_brief | — | `marketing.marketing`, internal_brief | **ready** |
| Research | research-marketing | research | — | `marketing.research` | **ready** |
| SEO brief | seo-specialist, geo | seo_brief | — | `marketing.seo_brief` | **ready** |
| Copy (answer-first) | copywriter | copy_answer_first | — | `marketing.copy_answer_first` | **ready** |
| Copy social | — | copy_social | — | `marketing.copy_social` | **ready** |
| Storytelling | storytelling | storytelling | — | `marketing.storytelling` | **ready** |
| Creative / ads | — | ad_creative, creative_review | — | ad_creative, creative_review | **ready** |
| Critic / item-13 | item-13, findability | critic, critic_item13 | — | critic* | **ready** |
| Trends | trend-hunter | trend_hunter | — | `marketing.trend_hunter` | **partial–ready** |
| Content analysis | content-strategist | — | — | `marketing.content_analyst` | **partial** |
| Media buy | media-buyer | — | — | `marketing.media_buyer` | **partial** |
| Influencer / UGC | packs | — | — | influencer, ugc | **partial** |
| Analytics / conversion | performance-analyst | — | APIs ads | — | **gap** (sem wiring API) |
| Brand guard | brand-guard-cliente | — | — | — | **partial** (knowledge) |

**Área:** `marketing` · **capabilities.yaml:** não (candidato #2) · **grounding:** slim · Planos SEO medidos (tokens)

---

## 5. Administration / operations / business ops

| Capacidade | Knowledge | Skills | Tools | Agente | **Ready?** |
|------------|-----------|--------|-------|--------|------------|
| Gestão empresarial | — | — | — | `gestao.gestao-empresarial` | **partial** |
| Atendimento / comunicações | imported comunicações | — | — | `atendimento.comunicacoes-atendimento` | **partial** |
| Tasks / projects / calendar | — | — | — | — | **gap** |
| Approvals workflows (negócio) | HITL runner | — | human_gate | runtime | **partial** (só plans, não BPM) |
| KPIs / reporting ops | — | — | — | — | **gap** |
| RH / recrutamento | keywords ops | — | — | — | **gap** |
| Procurement | keywords fornecedor | — | — | — | **gap** |

**Área:** `ops` · **capabilities.yaml:** não

---

## 6. Finance & accounting

| Capacidade | Knowledge | Skills | Tools | Agente | **Ready?** |
|------------|-----------|--------|-------|--------|------------|
| Contabilidade PT/BR | — | — | — | `gestao.contabilidade` | **partial** |
| Orçamento / fluxo caixa | keywords | — | — | via contabilidade? | **gap** |
| Faturação / impostos | keywords | — | — | — | **gap** |
| Análise financeira | — | — | — | — | **gap** |
| **Trading / markets** (research) | — | — | — | — | **gap** (área finance menciona trading; zero agent) |
| Trading execution | — | — | — | — | **gap** + **act forbidden** por política recomendada |
| Risk / portfolio | — | — | — | — | **gap** |

**Área:** `finance` · **hitl:** required · **capabilities.yaml:** não

---

## 7. Sales & CRM

| Capacidade | Knowledge | Skills | Tools | Agente | **Ready?** |
|------------|-----------|--------|-------|--------|------------|
| Leads / pipeline | — | — | CRM API | — | **gap** |
| Propostas / follow-up | atendimento parcial | — | — | comunicações | **gap** |
| CRM integration | — | — | — | — | **gap** |

**Área dedicada:** não (só keywords em ops) · **Ready:** **gap**

---

## 8. Legal

| Capacidade | Knowledge | Skills | Tools | Agente | **Ready?** |
|------------|-----------|--------|-------|--------|------------|
| Direito PT/BR base | `legal/direito-br-pt.md` | — | — | — | **partial** (só knowledge fino) |
| Contratos / cláusulas | keywords | — | — | — | **gap** |
| Jurisprudência / pesquisa | — | — | — | — | **gap** |
| RGPD / compliance | keywords | — | — | — | **gap** |
| Jurisdição + vigência metadata | — | — | — | — | **gap** (bloqueia “ready”) |

**Área:** `legal` · **agents: []** · **hitl:** required · **Ready execução:** **gap**

---

## 9. Medicine & health

| Capacidade | Knowledge | Skills | Tools | Agente | **Ready?** |
|------------|-----------|--------|-------|--------|------------|
| Literatura / especialidades | `saude/*` (cardio, derma, oftalmo) | — | — | — | **partial** (packs só) |
| Protocolos / guidelines | — | — | — | — | **gap** |
| Apoio clínico com rastreio | — | — | — | — | **gap** |
| Policy clínica (não prescrever) | — | — | — | — | **gap** |

**Área:** não existe · **Ready:** **gap** (knowledge isolado ≠ produto)

---

## 10. HR

| Capacidade | Knowledge | Skills | Agente | **Ready?** |
|------------|-----------|--------|--------|------------|
| Recrutamento / onboarding / políticas | keywords em ops | — | — | **gap** |

---

## 11. Manufacturing / production / supply chain

| Capacidade | Knowledge | Skills | Agente | **Ready?** |
|------------|-----------|--------|--------|------------|
| Production planning, OEE, maintenance | — | — | — | **gap** |
| Inventory / supply chain | keywords ops | — | — | **gap** |
| Quality / SOPs | — | — | — | **gap** |

---

## 12. Engineering & science (não-software)

| Capacidade | Knowledge | Skills | Agente | **Ready?** |
|------------|-----------|--------|--------|------------|
| Engenharia de campo / normas | — | — | — | **gap** |
| Ciência / literatura / simulação | — | — | — | **gap** |
| HVAC / construção (P2 overlap) | — | — | — | **gap** |

---

## 13. Education

| Capacidade | Knowledge | Skills | Agente | **Ready?** |
|------------|-----------|--------|--------|------------|
| Tutoria / avaliação / curricula | — | — | — | **gap** |

---

## 14. Game development & production

| Capacidade | Knowledge | Skills | Agente | **Ready?** |
|------------|-----------|--------|--------|------------|
| Game design / programming / art / QA | — | — | — | **gap** |
| Reuso software + design + marketing | via outras áreas | — | composição futura | **gap** (área `gamedev` vazia) |

**Área:** `gamedev` · **agents: []**

---

## 15. Scorecard P1

| Ready (utilizável em plans) | Partial | Gap |
|----------------------------|---------|-----|
| Marketing (maioria das subcaps) | Security (quase ready), Software, Design, Ops, Finance contabilidade, Research radar | Legal execução, Sales/CRM, Medicine produto, HR, Manufacturing, Supply chain, Education, Science/Eng campo, Games, Trading |
| Security pipeline (triage/audit/report) | Memory/L5 depth, CI supply chain | SOC/IR, red-team lab, compliance formal |

**Cobertura P1 (grosseira):**  
- **~1 domínio ready** (Marketing)  
- **~4 partial fortes** (Security, Software, Design, Ops/Finance fino)  
- **Resto gap** ou só keywords/knowledge

---

## 16. Ordem recomendada (P1, sem inflação de agentes)

1. **Fechar Security** → L5 prova + merges SEC + (opcional) capabilities já feitas.  
2. **Marketing capabilities.yaml** (espelhar security) — já tem agents/skills; formaliza Capability First.  
3. **Software capabilities** curtas (impl, review, tdd) e **medir** pack Claude.  
4. **Finance:** alargar knowledge + skills **sem** trading execution.  
5. **Legal:** metadata de fonte/jurisdição no knowledge **antes** do 1.º agente.  
6. **Gamedev / Sales / Medicine / Manufacturing:** só depois de Research + Documents P0 melhores.

---

## 17. Regra de ouro P1

| Evitar | Fazer |
|--------|--------|
| Um agente por subárea da tabela | Capability + skill curta + plan; agente só se identidade estável |
| Trading com `act` de execução | Research/risco partial; execution forbidden até permissões |
| Medicina “pronta” por ter `saude/*.md` | Policy + provenance + HITL clínico explícito |
| Duplicar marketing em “Sales agent” | Capability CRM quando houver tool real |

---

**Resumo:** em P1, **Marketing está à frente**; **Security é o modelo de capabilities**; **Software/Design/Ops/Finance são partial**; **Legal/Games/Medicine/HR/Produção/Sales/Trading estão gap de execução**. O próximo artefacto natural não é mais agentes P1 — é **capabilities.yaml de marketing** + **fecho L5 security**, reutilizando o padrão já validado no E7.
