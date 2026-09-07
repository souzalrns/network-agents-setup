# Orquestrador — vertical Marketing (genérico)

**Âmbito:** agência / conteúdo / performance / social — **sem** área administrativa.  
**Domínio:** qualquer marca ou projecto (não amarrado a um cliente).

**Papel:** único ponto que monta o **plan**, aplica policy (`tools_allowed`, budget, HITL), despacha **actions** do registry e grava evidência L2. Os workers não orquestram uns aos outros em mesh.

---

## 1. Posição na arquitectura

```text
Pedido (brief de campanha / peça / auditoria)
        │
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

Item 13 = **checks e campos** nos steps `seo_brief` / `copy_*` / `critic`, não um ramo órfão.

---

## 2. Inputs do orquestrador

| Campo | Obrigatório | Notas |
|-------|-------------|--------|
| `objective` | sim | O quê e porquê (sem stack) |
| `deliverable_type` | sim | ver secção 4 |
| `audience` | recomendado | |
| `constraints` | não | tom, legal, canais proibidos |
| `knowledge_refs` | não | paths L5 / playbooks |
| `channels` | se social | instagram, tiktok, … |
| `hitl_policy` | default | quando exigir humano |

---

## 3. Policy fixa (sempre)

1. Workers só com `tools_allowed` do step.  
2. Default-deny em publish / spend / alteração de ads.  
3. Saídas com **schema** quando existir (`SeoBrief`, `CopyAnswerFirst`, `CriticReport`, …).  
4. Item 13: critic deve reportar gaps de descoberta/IA explicitamente.  
5. `status: candidate` em memória L4 / skills — sem auto-promote.  
6. Setup ≠ produção: este playbook é do **lab/método**; produção MCP só por decisão explícita.  
7. Evidência: cada step → artefacto path + evento L2.

---

## 4. Tipos de deliverable → template de plan

| `deliverable_type` | Pipeline típico (actions) |
|--------------------|---------------------------|
| `seo_article` | research? → seo_brief → copy_answer_first → critic → HITL |
| `landing_copy` | seo_brief (intent) → copy_answer_first → critic → HITL |
| `social_pack` | research/trend_hunter → copy_social / storytelling → ugc_notes? → critic_light → HITL |
| `campaign_brief` | research → media_buyer_notes + channel_plan → critic → HITL |
| `performance_review` | performance_analyst → critic → HITL (sem publish) |
| `creative_script` | storytelling → editor_video_notes → critic → HITL |
| `full_content_piece` | research → seo_brief (Item 13) → copy → storytelling polish? → critic → HITL |

O orquestrador **escolhe template**, preenche `depends_on`, não inventa mesh livre.

---

## 5. Roles / actions (mapa)

| Action / role | Função |
|---------------|--------|
| `research` | factos, fontes, ângulos |
| `trend_hunter` | sinais de tendência (social) |
| `seo_brief` | intent, SERP/IA, outline, **Item 13 notes** |
| `copy_answer_first` | peça com resposta cedo |
| `storytelling` | narrativa / arco |
| `copy_social` | variantes por canal |
| `ugc` / `influencer` | guias de brief criador |
| `media_buyer` | estrutura de media (sem gastar $ sem HITL) |
| `performance_analyst` | leitura de métricas / hipóteses |
| `editor_video` | notas de corte/roteiro |
| `design_ui` / `design_ux` | se o deliverable incluir produto digital |
| `critic` | qualidade + Item 13 + publish_ready |
| `orchestrator` | só plan, verify, gates — **não** escreve copy final |

Nomes alinháveis ao `registry-actions` do setup; estender registry quando faltar action estável.

---

## 6. HITL (marketing)

| Situação | Gate |
|----------|------|
| `publish_ready` do critic = false | bloqueia; humano ou replan |
| Publish real (CMS, ads, social API) | **sempre** HITL (confirmation) |
| Spend / media buy | HITL + payload editável |
| Só draft interno | HITL opcional (output_review) |
| Item 13 gaps críticos | humano decide aceitar risco ou rework |

---

## 7. Budget default

```yaml
budget:
  max_steps: 12
  max_replans: 2
  max_retrieve_calls: 20
```

Ajustável por `deliverable_type` (performance_review pode ser mais curto).

---

## 8. Verify (done)

Plan só `plan_done` se:

1. Todos os steps obrigatórios do template com artefacto  
2. Schemas válidos onde aplicável  
3. Critic executado nos templates que o exigem  
4. HITL resolvido se `requires_hitl`  
5. Nenhum publish externo sem evento `human_gate_resolved: approve`  

---

## 9. Relação com Item 13

No template `seo_article` / `full_content_piece` / `landing_copy`:

- `seo_brief` **deve** incluir bloco Item 13 (entidades, FAQs, citabilidade, estrutura máquina-legível)  
- `critic` **deve** pontuar ou listar gaps Item 13  
- Falha Item 13 ≠ sempre fail hard: `on_fail` pode ser `human` com risco explícito  

---

## 10. O que este orquestrador não faz

- Financeiro, RH, legal binding da agência (admin fora de scope)  
- Substituir MCP produção  
- Auto-post em redes  
- Escolher modelo de ads e gastar verba sozinho  

---

Playbooks executáveis: [templates/](./templates/) · exemplo YAML: [templates/seo-article.plan.yaml](./templates/seo-article.plan.yaml)
