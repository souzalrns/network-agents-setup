# economia-trader: alertas

> Pedido do maestro (2026-10-13, passo 1 de 3): avisar quando o trader se trava sozinho ou continua a falhar.
> Antes disto, um auto-kill só aparecia no painel e no diário.

## O que avisa

| Regra | Quando | Nível |
|---|---|---|
| `auto_kill` | o loop acionou o kill switch (drawdown ou falhas seguidas) | crítico |
| `grid_refused` | um grid não cabe nos limites de risco e recusou negociar | aviso |
| `errors_in_row` | N erros (`run_error`/`error`) sem um tick bom (`run`) pelo meio; por omissão N = 3 | aviso, uma vez por série |

## Como funciona

- O vigia lê o **diário** a partir de onde parou da última vez (`alerts.offset.json`). Não mexe no código do
  trader, serve qualquer pasta de estado (ações em `.economia-trader`, grid em `.economia-trader/grid`) e não
  depende de o trader estar vivo.
- Cada alerta fica também em `alerts.jsonl`.
- Um canal em baixo fica registado nesse ficheiro e nunca interrompe o trader nem os outros canais.
- Os segredos (token, password, URL do webhook) **são tirados** das mensagens de erro antes de ficarem gravados.

## Canais (só variáveis de ambiente, todos opcionais e grátis)

| Canal | Variáveis |
|---|---|
| Telegram | `ECONOMIA_TRADER_ALERT_TELEGRAM_TOKEN`, `ECONOMIA_TRADER_ALERT_TELEGRAM_CHAT_ID` |
| Webhook (Slack, Discord, ntfy…) | `ECONOMIA_TRADER_ALERT_WEBHOOK` (só https) |
| E-mail (SMTP com SSL, p. ex. Gmail com palavra-passe de app) | `ECONOMIA_TRADER_ALERT_SMTP_HOST`, `..._SMTP_PORT` (465), `..._SMTP_USER`, `..._SMTP_PASSWORD`, `..._EMAIL_TO` |

## Usar

```bash
economia-trader alerts --state-dir .economia-trader --test        # 1 alerta de teste em cada canal
economia-trader run  ... --once --alerts                          # verifica logo a seguir ao tick
economia-trader grid ... --once --alerts --state-dir .economia-trader/grid
economia-trader alerts --state-dir .economia-trader --every-min 5 # ou um vigia à parte
```
