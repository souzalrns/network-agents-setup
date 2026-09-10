# Orquestrador — vertical Marketing (generico)

**Ambito:** agencia / conteudo / performance / social — **sem** area administrativa.  
**Dominio:** qualquer marca ou projecto (nao amarrado a um cliente).

**Papel:** unico ponto que monta o **plan**, aplica policy (`tools_allowed`, budget, HITL), despacha **actions** do registry e grava evidencia L2. Os workers nao orquestram uns aos outros em mesh.

**Descoberta de skills:** se o pedido ainda nao e um plan, correr antes  
`skills/meta/using-agent-skills` (ver `docs/orchestration/SKILL-ORCHESTRATION.md`).  
Com plan activo, a invocacao e **deterministica**: `action` → `skills/marketing/<action>/SKILL.md`.

---

## 1. Posicao na arquitectura

```text
Pedido (brief de campanha / peca / auditoria)
        │
        ▼
┌───────────────────────────┐
│  using-agent-skills       │  so se ainda nao ha plan
│  (meta mapa)              │
└─────────────┬─────────────┘
              ▼
┌───────────────────────────┐
│  MARKETING ORCHESTRATOR   │  plan · gates · budget · verify
└─────────────┬─────────────┘
              │ depends_on / foreach
    ┌─────────┼─────────┬──────────┬────────────┐
    ▼         ▼         ▼          ▼            ▼
 research  seo+item13  copy/story  social/ugc  performance
    │         │         │          │            │
    └─────────┴─────────┴──────────┴────────────┘
                      │
                      ▼
              critic → HITL → done
```

Item 13 = **checks e campos** nos steps `seo_brief` / `copy_*` / `critic`, multi-IA (nao so Google).

---

## 2. Inputs do orquestrador

| Campo | Obrigatorio | Notas |
|-------|-------------|--------|
| `objective` | sim | O que e porquê (sem stack) |
| `deliverable_type` | sim | ver seccao 4 |
| `audience` | recomendado | |
| `constraints` | nao | tom, legal, canais proibidos |
| `knowledge_refs` | nao | paths L5 / playbooks |
| `channels` | se social | instagram, tiktok, … |
| `hitl_policy` | default | quando exigir humano |

---

## 3. Policy fixa (sempre)

1. Workers so com `tools_allowed` do step.  
2. Default-deny em publish / spend / alteracao de ads.  
3. Saidas com **schema** quando existir (`SeoBrief`, `CopyAnswerFirst`, `CriticReport`, …).  
4. Item 13: critic deve reportar gaps de descoberta/IA (multi-modelo) explicitamente.  
5. `status: candidate` em memoria L4 / skills — sem auto-promote.  
6. Setup ≠ producao: este playbook e do **lab/metodo**; producao MCP so por decisao explicita.  
7. Evidencia: cada step → artefacto path + evento L2.
8. Skills invocadas pelo plan (action) ou pela meta-skill — nao por mesh de workers.

---

## 4. Tipos de deliverable → template de plan

| `deliverable_type` | Pipeline tipico (actions) |
|--------------------|---------------------------|
| `seo_article` | research? → seo_brief → copy_answer_first → critic → HITL |
| `landing_copy` | seo_brief (intent) → copy_answer_first → critic → HITL |
| `social_pack` | trend_hunter → research → copy_social → storytelling → critic → HITL |
| `campaign_brief` | research → media_buyer_notes + channel_plan → critic → HITL |
| `performance_review` | performance_analyst → critic → HITL (sem publish) |
| `creative_script` | storytelling → editor_video_notes → critic → HITL |
| `full_content_piece` | research → seo_brief (Item 13) → copy → storytelling polish? → critic → HITL |
| `internal_brief` | research → internal_brief → HITL |
| `approval_rounds` | creative_review loops + HITL |

O orquestrador **escolhe template**, preenche `depends_on`, nao inventa mesh livre.

---

## 5. Roles / actions (mapa)

Ver `docs/architecture/patterns-from-harness/registry-actions.md`.

Meta: `using_agent_skills` — so descoberta.

---

## 6. HITL (marketing)

| Situacao | Gate |
|----------|------|
| `publish_ready` do critic = false | bloqueia; humano ou replan |
| Publish real (CMS, ads, social API) | **sempre** HITL |
| Spend / media buy | HITL + payload editavel |
| So draft interno | HITL opcional |
| Item 13 gaps criticos | humano decide |

---

## 7. Budget default

```yaml
budget:
  max_steps: 12
  max_replans: 2
  max_retrieve_calls: 20
```

---

## 8. Verify (done)

1. Steps obrigatorios com artefacto  
2. Schemas validos onde aplicavel  
3. Critic quando o template exige  
4. HITL resolvido se `requires_hitl`  
5. Nenhum publish externo sem approve  

---

## 9. Relacao com Item 13

Multi-IA (ChatGPT, Claude, Gemini, Perplexity, …) + SEO classico complementar.  
Ver `docs/knowledge/marketing/multi-ai-findability.md`.

---

## 10. O que este orquestrador nao faz

- Financeiro, RH, legal binding  
- Substituir MCP producao  
- Auto-post em redes  
- Substituir o CLI addyosmani no IDE de engenharia  

Playbooks: [templates/](./templates/) · wiring: [AGENT-SKILL-WIRING.md](./AGENT-SKILL-WIRING.md) · meta: [../SKILL-ORCHESTRATION.md](../SKILL-ORCHESTRATION.md)
