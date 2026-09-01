# Knowledge Pack — ai-findability

**Playbook canónico (humano):** [../item-13-ai-findability.md](../item-13-ai-findability.md)  
**Lead agent:** `ai-visibility` · **P0 técnico:** `seo-specialist` · **Não duplica:** `seo-specialist.md`, `ai-visibility.md`, `geo-agent.md` — cruza e aprofunda diagnóstico Item 13.

Este pack é **operacional para RAG**: cada secção numerada responde a uma pergunta isolada.

---

## 1. O que é Item 13 em uma frase

Item 13 (AI Findability) é o conjunto de regras para o site ser **encontrado, compreendido e citado** por pesquisa clássica e por sistemas de IA — sem prometer controlo sobre o modelo.

## 2. Quem é dono do quê

`ai-visibility` conduz a auditoria Item 13. `seo-specialist` fecha o P0 técnico. `copywriter`/`content-strategist` fazem answer-first. `critic-criativo` devolve PASS/FAIL. `marketing-orquestrador` dispara e ordena handoffs. `geo-agent` só se intent local real.

## 3. Quando disparar Item 13

Dispara se o pedido mencionar discoverability, “aparecer em IA”, site ilegível para bots, SPA, soft-404, canónicas erradas, ou auditoria findability.

## 4. Ordem de handoff obrigatória

1) `seo-specialist` P0 → 2) `ai-visibility` lead → 3) `geo-agent` se local → 4) `copywriter`/`content-strategist` se P1 conteúdo falhar → 5) `critic-criativo` PASS/FAIL. FAIL em P0 bloqueia trabalho a jusante como “pronto”.

## 5. Sintoma: HTML quase vazio no curl

Verificar: `curl -sL URL` sem texto útil, `#root` vazio, size ~5–10 KB. Correção: SSG/SSR ou prerender do conteúdo crítico. PASS: texto e H1 no 1.º response sem JS.

## 6. Sintoma: mesmo title em todas as rotas

Verificar: várias URLs com o mesmo `<title>`. Correção: metadata por rota. PASS: title único e descritivo por URL indexável.

## 7. Sintoma: canonical aponta sempre para a home

Verificar: `rel=canonical` em páginas internas = homepage. Correção: canonical autorreferente. PASS: cada página declara a sua própria canónica.

## 8. Sintoma: soft-404

Verificar: URL inventada devolve HTTP 200 + shell da app. Correção: HTTP 404 real. PASS: `curl -sI` à URL falsa → 404.

## 9. Sintoma: zero H1 ou vários H1

Verificar: count de `<h1>` no HTML estático. Correção: um H1 com o tema principal. PASS: exactamente 1 H1 com texto.

## 10. Sintoma: schema sem conteúdo visível

Verificar: FAQPage/JSON-LD sem FAQ no HTML. Correção: alinhar schema ao visível ou remover. PASS: cada `@type` reflecte blocos reais.

## 11. SSG vs SSR vs SPA — regra prática

SPA pura para conteúdo público de aquisição = risco alto de FAIL P0. SSG para páginas estáticas/marketing. SSR quando o HTML depende de dados por pedido. PASS Item 13: conteúdo prioritário legível sem JS.

## 12. Lab passou e domínio canónico não

PASS no preview (`*.vercel.app`) não conta como PASS no domínio oficial. Medir e declarar os dois ambientes em separado.

## 13. Política de bots — default do playbook

Allow: Googlebot e bots de answer/search (OAI-SearchBot, PerplexityBot, ClaudeBot e equivalentes de consulta). Disallow por defeito: GPTBot e Google-Extended (treino). Cliente pode Allow train com decisão registada.

## 14. Política de bots — proibido

Allow e Disallow no mesmo user-agent no mesmo robots (ou conflito repo vs Cloudflare sem nota) = FAIL de descoberta.

## 15. robots.txt — verificação

Abrir `/robots.txt`. Confirmar Allow em pesquisa/answer e Disallow em GPTBot/Google-Extended se o cliente não optou por train. Sitemap URL presente e válida.

## 16. llms.txt — papel

Ficheiro opcional de orientação para agentes; não substitui HTML real nem SEO. Deve alinhar a política de bots.

## 17. Cloudflare / WAF vs robots

Se a edge bloqueia bots que o `robots.txt` do repo permite, sem decisão explícita, o Item 13 marca FAIL de descoberta até alinhar.

## 18. Sitemap — regras

Só canónicas que se quer indexar. Sem preview, sem query de tracking, sem soft-404. Cada `<loc>` deve responder 200 na URL canónica.

## 19. Answer-first — definição

A resposta útil à intenção principal aparece nos primeiros blocos, antes de storytelling longo.

## 20. Answer-first — verificação

Ler os primeiros 150–300 palavras do HTML. Se só houver slogan sem factos, FAIL P1 conteúdo.

## 21. unique_promise por URL

Cada URL indexável tem um ângulo ou promessa distinta. Se dez páginas partilham o mesmo outline, há canibalização.

## 22. Canibalização — sintoma

Vários posts “guia X 2025/2026” a competir. Correção: fundir, 301 da origem, uma canónica por intent.

## 23. Thin content / locais

Páginas “serviço em [cidade]” quase iguais. Correção: fundir num hub útil ou não publicar. Não criar 20 clones para GEO.

## 24. Clusters temáticos

Um pilar por intent head + spokes com links internos. Spokes não repetem o pilar.

## 25. Schema Organization

Usar em home/sobre: `name`, `url`, `sameAs` reais. Não inventar perfis sociais.

## 26. Schema Person

Usar para profissional/autor verificável. Ligar à Organization. Credenciais só se verdadeiras.

## 27. Schema LocalBusiness

Só com NAP real e intent local. Sem endereço fictício.

## 28. Schema FAQPage

Só se perguntas e respostas estiverem visíveis no HTML.

## 29. Schema Article / BlogPosting

Headline, author Person, dates quando conhecidos. Alinhar ao visível.

## 30. Schema Service / LegalService

Serviço real descrito na página. Não marcar serviço que a página não explica.

## 31. BreadcrumbList

Útil em hierarquias hub → via → artigo. Deve espelhar a navegação real.

## 32. YMYL jurídico — cuidado

Factos com fonte, datas, disclaimer. Agents não inventam prazos nem taxas de sucesso sem base no brief.

## 33. YMYL SST / B2B

Claims de conformidade só com documentação do cliente. Preferir processo a percentagens inventadas.

## 34. SaaS / produto digital

HTML real nas landing de aquisição; entity do produto; pricing só se público.

## 35. Medição GSC — páginas

Indexadas vs excluídas (canónica, not found, soft-404, noindex) na superfície prioritária.

## 36. Medição GSC — desempenho

Impressões e cliques por URL e query para priorizar 301 e fusões — não inventar baselines.

## 37. Inspeção de URL

Confirmar canónica escolhida pelo Google e se o HTML rastreado tem o conteúdo esperado.

## 38. PASS lab vs PASS canónico

PASS lab = P0/P1 no preview. PASS domínio canónico = mesmos critérios no host oficial + GSC sem falhas graves nas URLs prioritárias.

## 39. Anti-padrão: preview como marca

Não promover `*.vercel.app` como site oficial. Canónico = domínio oficial.

## 40. Anti-padrão: claims inventados

Remover ou substituir por factos verificáveis do cliente.

## 41. O que o ai-visibility NÃO faz

Não implementa framework; não promete ranking em ChatGPT; não inventa menções; não substitui seo-specialist em P0.

## 42. O que o seo-specialist NÃO faz no Item 13

Não escreve copy de marca; não é dono de llms.txt/citabilidade; não gere mídia paga.

## 43. O que o copywriter NÃO faz

Não inventa números ou prémios; não define arquitectura técnica; não declara PASS Item 13 sozinho.

## 44. O que o research-marketing faz neste fluxo

Recolhe factos citáveis com fonte. Facto sem fonte não entra no conteúdo findable.

## 45. O que o critic devolve

PASS/FAIL por item do checklist — nunca só “parece bom”. Bloqueadores P0 primeiro.

## 46. Checklist mínimo por URL prioritária

P0.1 HTML texto · P0.2 title · P0.3 description · P0.4 canonical · P0.5 H1 · P0.6 404 site · P0.7 schema · P1 answer-first · P1 unique_promise.

## 47. Quantas URLs no piloto

5–15 URLs prioritárias por ronda. Fundir thin antes de auditar dezenas de posts.

## 48. Quando geo-agent entra

Só com intent local comprovado. Caso contrário: fora de scope.

## 49. Conflito playbook vs knowledge

Prevalece `docs/item-13-ai-findability.md`.

## 50. Output mínimo de uma auditoria Item 13

URLs prioritárias · tabela PASS/FAIL · política de bots · lab vs canónico · top 3 acções · bloqueios P0.

---

## Fora de âmbito deste pack

Implementação de código · Cutover DNS · Runtime agent-network-mcp · Métricas inventadas · Garantias de citação por um modelo específico
