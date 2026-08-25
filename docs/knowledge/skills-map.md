# Mapa Skill → Agente

Ligação explícita entre skills existentes (repos) e agentes do setup de marketing.  
**Estado:** referência para invocação / prioridade de integração — não significa que o runtime já carrega a skill automaticamente.

---

## designer-skills (souzalrns/designer-skills)

| Skill / comando | Agente primário | Apoio |
|-----------------|-----------------|-------|
| design-token | `ui` | diretor-arte (identidade) |
| component-spec | `ui` | ux |
| theming-system | `ui` | |
| naming-convention | `ui` | |
| pattern-library | `ui` | ux |
| accessibility-audit | `ui` + `ux` | produto-tech (produção) |
| design-system-governance | `ui` | brand-guard |
| motion-system | `ui` / `diretor-arte` | editor-video |
| icon-system | `ui` | diretor-arte |
| documentation-template | `ui` | |
| localization-design | `ux` + `ui` | |

---

## ECC (Everything Claude Code) — skills relevantes a marketing/produto

| Skill (padrão ECC) | Agente primário | Notas |
|--------------------|-----------------|-------|
| seo | `seo-specialist` | Já refletido em agentes de produção (ex. viannalegal) |
| marketing-campaign | `marketing-orquestrador` / estrategista | Posicionamento antes de copy |
| brand-discovery | estrategista-marca / research | |
| content-engine | `content-strategist` | |
| article-writing | `copywriter` + seo | |
| frontend-a11y | `ux` + `ui` | |
| design-system | `ui` | |
| social-publisher | social / verticais | se existir no fork usado |

---

## Knowledge packs (injeção de conhecimento, não skill executável)

| Pack | Agente |
|------|--------|
| ui.md | ui |
| ux.md | ux |
| ai-visibility.md | ai-visibility |
| seo-specialist.md | seo-specialist |
| copywriter.md | copywriter |
| geo-agent.md | geo-agent |
| diretor-arte.md | diretor-arte |
| content-strategist.md | content-strategist |
| social-media-manager.md | social-media-manager |
| marketing-orquestrador.md | marketing-orquestrador |
| item-13-ai-findability.md | ai-visibility + seo + geo (fluxo) |
| imported-from-harnesses.md | orquestração / rede |

---

## Gaps (sem skill madura no ecossistema atual)

| Necessidade | Agente | Ação |
|-------------|--------|------|
| GEO/AEO automation (auditoria em massa) | ai-visibility | Pack + playbook bastam por agora; skills externas só após avaliação no radar-ferramentas |
| Media buying / Ads API | media-buyer | Sem skill obrigatória; dados do cliente |
| Influencer discovery data | influencer-strategist | Não inventar métricas; tooling futuro |
| Video edit automation | editor-video | Fora de scope de skill de texto |

---

## Prioridade de integração runtime (quando for a produção)

1. **P0** — ui + accessibility + design-token (designer-skills)  
2. **P0** — seo + knowledge packs item 13 (ai-visibility, seo, geo)  
3. **P1** — marketing-campaign / brand-discovery (ECC) no orquestrador  
4. **P1** — content-engine + copy packs  
5. **P2** — social nativo / publisher  

---

*Mapa vivo — atualizar quando skills novas forem adotadas no radar-ferramentas.*
