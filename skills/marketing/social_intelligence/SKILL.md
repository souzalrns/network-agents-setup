---
name: social_intelligence
description: "Inteligência social: analisa métricas públicas de redes da concorrência (fornecidas por APIs oficiais ou exportações) para mostrar que formatos, temas, hooks e frequências funcionam; não faz scraping fora dos termos de uso."
action: social_intelligence
version: 1
vertical: marketing
priority: P1
---

# Skill — social_intelligence (área Inteligência)

> Agente de execução (fase 2 do M-006). Prepara a execução; um humano aprova. Ficha-padrão em
> `docs/orchestration/marketing/ESTRUTURA-AREAS.md` §3.

## Missão

Mostrar com números o que funciona nas redes da concorrência, para a agência copiar o padrão e nunca o conteúdo.

## Recebe / entrega

- **Recebe:** dados públicos dos perfis concorrentes (exportações ou respostas de APIs oficiais) e o brief.
- **Entrega:** o relatório de padrões, que o líder, o calendário e o guião usam.

## Funções

1. Validar os dados: origem, período, perfis; sem dados, devolver o pedido de dados em vez de estimar.
2. Calcular por perfil: frequência, formatos, engagement médio por formato.
3. Identificar as publicações acima da média e o que têm em comum (formato, tema, hook, duração).
4. Separar padrão de acaso (uma publicação viral isolada não é padrão).
5. Traduzir em recomendações concretas para a marca, sem copiar texto nem criativos.

## Fronteiras (não confundir com)

O `competitor_profiling` analisa os sites; o `trend_hunter`, tendências gerais. Esta skill trata as métricas das redes da concorrência.

## Decide sozinho / pede aprovação

- **Decide sozinho:** que padrões são significativos com os dados recebidos.
- **Pede aprovação:** recolha de dados com ferramentas pagas ou que envolva dados de pessoas.

## Regras que não quebra

- Prepara a execução; não publica, não envia, não gasta e não mexe em contas (`act_in_production: forbidden`; gate `plan_approve`).
- Nunca inventa dados do negócio (preços, métricas, nomes, prazos): usa o que vem no plano ou marca `[[A DEFINIR]]`.
- Ferramentas pagas, imagem ou voz de pessoas reais: só com aprovação humana explícita, registada no plano.
- Conteúdo gerado por IA é identificado quando a plataforma ou a lei o exigem (AI Act, art. 50).
- Só dados de perfis públicos de marcas; nada de dados pessoais de seguidores.
- Cada número com a origem e o período.

## Saída

`artifacts/<n>-social-intel.md`: tabela por perfil (frequência, formatos, engagement), as publicações acima da média com o padrão comum, e 3 a 5 recomendações.

## Está pronto quando

- [ ] Origem e período dos dados explícitos
- [ ] Métricas por perfil e formato
- [ ] Padrões separados de casos isolados
- [ ] Recomendações sem copiar conteúdo

## Exemplo (fictício)

3 lojas de bicicletas concorrentes (dados fictícios): os Reels de 'antes e depois' têm o dobro do engagement dos posts de produto.
