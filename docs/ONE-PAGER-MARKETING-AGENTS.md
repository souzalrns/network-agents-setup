# One-Pager — Multi-Agent Marketing Architecture

**LRNSdigital · network-agents-setup · 2026**

---

## Em uma frase

Agência multi-agente: especialistas com limites claros, knowledge packs operacionais e playbook para **IA encontrar e recomendar** a marca — sem misturar papéis nem inventar métricas.

---

## Problema → Solução

| Problema | Abordagem |
|----------|-----------|
| Um prompt faz “tudo” | Horizontais + verticais + orquestrador |
| Só system prompt genérico | Knowledge pack por papel |
| SEO ≠ visibilidade em IA | SEO + AI Visibility + GEO local (Item 13) |
| UI misturado com campanha | UI (design system) ≠ Diretor de Arte |
| Claims inventados | Evidência obrigatória; anti-padrões nos packs |

---

## Arquitetura (vista rápida)

```text
Objetivo de negócio
        │
 marketing-orquestrador  (plano, handoffs, consolidação)
        │
 ┌─────────┼─────────┐
 Horizontais      Verticais        Qualidade
 (SEO, AI, UI,    (IG, TikTok,     (critic,
  copy, media…)    paid, AV…)      brand-guard)
        │
 [KNOWLEDGE] + [CLIENT fiche]
```

**~19 horizontais** com prompt + knowledge · **Verticais** com ficha de cliente · **Skills map** (designer-skills / ECC)

---

## Entregáveis no repo

| Artefacto | Descrição |
|-----------|-----------|
| `docs/marketing-agency-agents.md` | System prompts + limites |
| `docs/knowledge/*.md` | Packs operacionais |
| `docs/knowledge/item-13-ai-findability.md` | Playbook AI Findability |
| `docs/knowledge/skills-map.md` | Skill → agente |
| `docs/knowledge/imported-from-harnesses.md` | Regras Ruflo / Hermes / Orca |
| `docs/PORTFOLIO.md` | Narrativa completa de portfolio |

---

## Como testar

```text
[SYSTEM] + [KNOWLEDGE] + [CLIENT] + [TASK]
```

Critério: resposta baseada em pack/cliente · premissas explícitas · zero dados inventados.

---

## Maturidade

| ✅ Feito | ⏳ Seguinte |
|---------|-------------|
| Desenho documental completo | Piloto live (Item 13) |
| Packs + playbooks | Skills no runtime |
| Setup paralelo isolado | Portar para produção se fizer sentido |

---

## Links

- Portfolio: [PORTFOLIO.md](./PORTFOLIO.md)  
- Agentes: [marketing-agency-agents.md](./marketing-agency-agents.md)  
- Knowledge: [knowledge/](./knowledge/)  
- Conclusão: [CONCLUSAO-SETUP-MARKETING.md](./CONCLUSAO-SETUP-MARKETING.md)  

**Repo:** https://github.com/souzalrns/network-agents-setup
