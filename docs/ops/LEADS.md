# LEADS: prospeção de empresas (ferramenta opcional)

Procura empresas no Google Maps e guarda nome, morada, telefone, site e email na tabela `leads`
do **seu** Supabase, para depois oferecer serviços. Desligada por omissão: só corre quando se dispara.

- Motor: [gosom/google-maps-scraper](https://github.com/gosom/google-maps-scraper) (MIT), via imagem Docker, no runner gratuito do GitHub Actions.
- Custo: zero (repo público). Sem chaves de API de terceiros.
- Código: `.github/workflows/leads.yml`, `scripts/leads_to_supabase.py`, `scripts/create_leads_table.sql`.

## Ligar (uma vez)

1. No SQL Editor do seu Supabase, correr `scripts/create_leads_table.sql`.
2. No repo, em Settings → Secrets → Actions, criar `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY`.
   Sem estes dois secrets o workflow corre em modo de teste (mostra o resumo e não grava nada).

## Usar

Actions → **leads** → Run workflow, ou por linha de comando:

```bash
gh workflow run leads.yml -f query="restaurantes Porto" -f nicho="restaurantes" -f depth=1
```

O Google Maps limita cada pesquisa: `depth=1` traz cerca de 16 empresas e `depth=8` cerca de 50 (medido em
"restaurantes Porto"). Mais profundidade não passa muito disso. **Para cobrir uma cidade, use várias pesquisas
por zona**, separadas por `;` (até 30 por corrida), por exemplo as freguesias do Porto:

```bash
gh workflow run leads.yml -f nicho="restaurantes" -f depth=5 -f query="restaurantes Bonfim; restaurantes Campanhã; restaurantes Paranhos; restaurantes Ramalde; restaurantes Cedofeita; restaurantes Sé Porto; restaurantes Miragaia; restaurantes Foz do Douro; restaurantes Lordelo do Ouro; restaurantes Aldoar; restaurantes Massarelos; restaurantes Vitória Porto"
```

Subir a profundidade aumenta o tempo e o risco de bloqueio pelo Google. Os duplicados entre zonas são ignorados.

Ver os resultados no Supabase: tabela `leads`, filtrar por `status = 'novo'` e por `nicho`.
Estados: `novo`, `contactado`, `respondeu`, `cliente`, `recusou`, `descartado`.

## Regras (RGPD / LGPD / lei do spam)

- Só empresas. Usar emails genéricos (`info@`, `geral@`); **não** enviar para emails de pessoas singulares sem base legal.
- Toda a mensagem leva identificação de quem envia e opção de recusa. Quem recusar passa a `recusou` e nunca mais é contactado.
- Retenção de 12 meses (`expires_at`); `cliente` e `recusou` não expiram. Limpeza: `select public.cleanup_expired_leads();`.
- Os termos de uso do Google Maps restringem a extracção automática. É um risco de termos de uso (conta ou IP
  podem ser bloqueados), não de custo. Usar volumes pequenos e só para prospeção B2B.
- Dados reais de leads ficam no Supabase de quem usa, **nunca** no repo.

## Avaliação (regra do catálogo)

| Cobrança | Segurança | Boa ferramenta | Serve o setup público |
|---|---|---|---|
| Não | Sim, moderado (imagem Docker de terceiros, dados pessoais, termos do Google) | Sim (MIT, mantida, CLI/API) | Sim |
