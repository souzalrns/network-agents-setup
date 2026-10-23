---
name: market_analysis
description: "Analisa um mercado ou activo a partir de fontes públicas permitidas (reguladores, bolsas, bancos centrais), separando factos com fonte de hipóteses e sem nunca recomendar ordens. Usar no início de um plano de trading; a revisão de risco e a decisão humana ficam para os passos seguintes."
action: market_analysis
version: 1
vertical: trading
priority: P1
---

# Skill — market_analysis

## Quando usar

- Passo `action: market_analysis` no início de um plano de trading (contexto macro, regulatório ou de mercado).

## Não usar

- Propor ou enviar ordens (nenhum agente deste domínio executa: `act_in_production: forbidden`).
- Rever trades fechados (`post_trade_review`) ou validar limites (`risk_review`).
- Prever preços com números que nenhuma fonte deu.

## Grounding

Seguir `agents/_shared/grounding.directive.md` (trading é domínio de alto risco):

- Factos **só** com fonte: a tool `fetch_url` (domínios da área `trading`) ou os ficheiros em `repo_files`.
- Sem fonte → lacuna explícita; nunca um número plausível de memória.
- Ler `docs/knowledge/trading/risk-policy.md`: qualquer ideia de entrada tem de dizer o stop e caber nos limites.

## Processo

1. Ler o `objective` do plano e as perguntas-chave.
2. Buscar 1 a 3 páginas relevantes com `fetch_url` (só domínios permitidos).
3. Escrever os factos com a fonte (URL final e data), as hipóteses à parte e as lacunas.
4. Se o objectivo pedir uma ideia de entrada: descrever o cenário, o stop e a perda no stop estimada, marcados como **hipótese**, e dizer que precisa de `risk_review` e de aprovação humana.

## Saída

JSON em `output_artifact`:

```json
{
  "content": "Markdown: contexto, factos (cada um com a fonte), hipóteses, lacunas",
  "sources": [{"url": "...", "title": "...", "retrieved_at": "..."}],
  "limitations": ["o que não foi possível confirmar"],
  "artifacts": []
}
```

## done_when

- [ ] Cada facto tem fonte da tool ou de `repo_files`
- [ ] Hipóteses separadas dos factos
- [ ] Nenhuma ordem proposta como acção; qualquer ideia de entrada marcada como hipótese, com stop
- [ ] Lacunas listadas

## Anti-padrões

- "Compra agora" ou qualquer instrução de execução
- Preço-alvo sem fonte
- Tratar uma notícia como confirmação de direcção do preço
