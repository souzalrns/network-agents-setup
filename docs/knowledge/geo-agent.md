# Knowledge Pack — geo-agent

Conhecimento operacional para o agente GEO (presença e relevância geográfica / local). Complementa `seo-specialist` e `ai-visibility`; não os substitui.

---

## 1. O que é “GEO” neste agente

Aqui **GEO = Geographic / local relevance**, não Generative Engine Optimization (isso é `ai-visibility`).

Foco:
- Como a marca é encontrada em intenções **locais** (cidade, região, “near me”, área de serviço)
- Consistência de dados geográficos (NAP, área de atuação)
- Conteúdo e entidades úteis por território — sem spam de cidades

---

## 2. Intenção local (tipos)

| Tipo | Exemplo | Implicação |
|------|---------|------------|
| Explícita local | “pladur Vila Nova de Gaia” | Página ou secção com prova de atuação na zona |
| Implicitamente local | “reparação bomba de calor” (com localização do utilizador) | GBP / LocalBusiness / área de serviço claros |
| Serviço multi-cidade | “SST Portugal” | Não forçar 50 landing pages de cidade sem conteúdo real |
| Navegação a local | nome da loja + cidade | NAP e perfil canônico |

**Regra:** só criar página por cidade/zona se houver **prova e utilidade** (equipa, casos, deslocação, preços de deslocação). Caso contrário, uma página de área de serviço bem feita > dezenas de thin pages.

---

## 3. NAP e consistência

**NAP** = Name, Address, Phone

- Uma grafia canónica do nome comercial
- Morada e telefone iguais no site, Google Business Profile (ou equivalente), rodapés e schema
- Divergências (morada antiga, telefone diferente, nome com/sem Lda) confundem motores e utilizadores

Checklist:
- [ ] NAP idêntico nas propriedades controladas pela marca
- [ ] Horários alinhados (se aplicável)
- [ ] Área de serviço / deslocação descrita com honestidade (ex.: Porto/Gaia)
- [ ] Schema LocalBusiness (ou subtipo) só com dados verdadeiros

Nunca inventar morada, avaliações, coordenadas ou “abrimos em 12 cidades”.

---

## 4. Conteúdo local útil (não spam)

| Bom | Mau |
|-----|-----|
| Política de deslocação real | Repetir o nome da cidade 40 vezes |
| Projetos / casos na região (com permissão) | Landing idêntica só a mudar “Porto” → “Braga” |
| Dúvidas locais (licenças, normas, clima/obra) | Keyword stuffing “melhor X cidade” |
| Mapa / indicações se houver local físico | Schema de local inexistente |

Ligar a intent de pesquisa local à **prova de relevância territorial**, não só à palavra da cidade.

---

## 5. Local + AI visibility

Modelos e AI Overviews também usam sinais locais quando a query é local:

- Factos de localização **consistentes** no site aumentam confiança da entidade
- LocalBusiness + sameAs + páginas clear sobre área de serviço ajudam desambiguação
- Avaliações e menções de terceiros são sinais externos — o agente **não as inventa**; pode recomendar pedir reviews reais

Fronteira:
- Detalhe de citação LLM / answer-first global → `ai-visibility`
- Rankings orgânicos gerais → `seo-specialist`
- NAP, área, intent local, inconsistências geográficas → **geo-agent**

---

## 6. Checklist operacional rápido

1. Qual é a área de atuação real? (lista curta)
2. NAP está consistente onde a marca controla a informação?
3. O site declara a área de forma explícita e verificável?
4. Há thin pages de cidade a canibalizar ou a enfraquecer qualidade?
5. Schema local reflete a realidade?
6. Queries locais prioritárias têm uma URL óbvia que as responde?
7. Dados em falta: pedir ao cliente (não preencher com inventário fictício)

---

## 7. O que o agente NUNCA faz

1. Inventar endereços, telefones, horários, avaliações ou número de lojas
2. Recomendar dezenas de landings de cidade sem conteúdo real
3. Substituir SEO técnico geral ou estratégia de AI visibility
4. Gerir tráfego pago local (media-buyer)
5. Afirmar posições no Maps ou “pack local” sem dados

---

## 8. Formato de resposta preferido

1. Área de serviço assumida vs confirmada
2. Inconsistências NAP / geográficas encontradas (ou “insuficiente info”)
3. Intent local prioritária e URLs que a cobrem (ou gaps)
4. Recomendações priorizadas (consertar consistência antes de criar páginas novas)
5. O que precisa de validação humana / dados do cliente

---

*Pack alinhado ao item 13 (fase E do playbook AI Findability).*
