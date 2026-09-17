---
name: seo-tech-checklist
action: seo_tech_checklist
version: 1
role: meta_technique
priority: P1
---

# Skill — seo-tech-checklist

## Trigger

Rever ou planear SEO técnico de um site.

## Inputs

- Site ou secção do site a rever

## Passos

1. **Rastreabilidade**: `robots.txt` não deve bloquear páginas importantes; nenhuma página relevante deve estar `noindex` sem intenção; páginas importantes devem ser alcançáveis em poucos cliques; evitar cadeias de redirect com mais de 2 saltos; canonical tags consistentes e sem loop.
2. **Indexabilidade**: formato de URL preferido consistente; sitemap deve reflectir a superfície pública real; sem URLs duplicados a competir sem canonical a resolver.
3. Cada página deve ter uma intenção de pesquisa primária clara — evita páginas a competir pela mesma keyword.
4. Corrige sempre bloqueadores técnicos antes de optimizar conteúdo; prioriza sinais de qualidade a longo prazo em vez de padrões manipulativos (keyword stuffing, conteúdo fino duplicado).
5. Ao propores novo schema markup ou mudanças de metadata, valida que fica consistente com o que já existe no site.

## Done When

- [ ] `robots.txt` revisto — nada importante bloqueado
- [ ] Sem cadeias de redirect com mais de 2 saltos
- [ ] Sitemap reflecte a superfície pública real
- [ ] Cada página tem intenção de pesquisa primária única

## Anti-padrões

- Optimizar conteúdo antes de corrigir bloqueadores técnicos
- Keyword stuffing ou conteúdo fino duplicado
- Duas páginas a competir pela mesma keyword sem canonical

## Knowledge Ref

Adaptado do skill **seo** do ECC (Everything Claude Code, MIT).
