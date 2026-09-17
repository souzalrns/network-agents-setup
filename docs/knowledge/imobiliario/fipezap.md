# Mercado imobiliário brasileiro — fontes públicas de referência

**Fonte:** Índice FipeZap (FIPE + Grupo ZAP); ferramentas de scraping de terceiros (Apify) para dados pontuais.

## Âmbito

Fontes de dados para avaliação de imóveis e análise de mercado no Brasil, priorizando fontes gratuitas/públicas sobre alternativas pagas.

## Índice FipeZap

Referência oficial do mercado imobiliário brasileiro (FIPE + Grupo ZAP):
- Gratuito
- Cobre 56 cidades, incluindo 22 capitais
- Actualização mensal
- Série histórica desde 2008 (vendas) / ~2010 (arrendamento)

É o benchmark que qualquer avaliador profissional usa para comparar se um preço pedido está acima ou abaixo da tendência de mercado numa região.

## Ferramentas de scraping (uso pontual, com moderação)

**⚠️ Custo — requer aprovação explícita antes de usar.** As duas ferramentas abaixo são pagas por evento. Regra geral do projecto: nada pago é chamado sem aprovação prévia — manter em tier gratuito por omissão (pesquisa web directa, não scraping) até essa aprovação existir.

Duas ferramentas Apify identificadas para dados pontuais de imóveis (pagas por evento, ~$0,005/imóvel):

| Ferramenta | Cobertura | Taxa de sucesso observada |
|---|---|---|
| `viralanalyzer/brazil-real-estate-scraper` | OLX, QuintoAndar, ImovelWeb, Airbnb | ~53,5% — testar antes de confiar |
| `jungle_synthesizer/brazil-vivareal-zap-imoveis-scraper` | Menos plataformas, mais estável | ~100% |

Para consultas gratuitas/pontuais de imóveis específicos, priorizar pesquisa web directa em vez de scraping pago, para poupar custo.

## Recomendação de uso

Ao comparar um preço pedido com o mercado, referenciar o índice FipeZap sempre que possível — é mais fiável e gratuito, ao contrário de scraping pontual. Scraping só faz sentido para dados que o FipeZap não cobre (imóveis específicos, plataformas de anúncio individuais).
