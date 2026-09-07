# Channel adapters

## Responsabilidades

1. Validar origem (secret, signature, TLS).  
2. Mapear evento nativo → `InboundMessage`.  
3. Resolver ou criar `channel_identity`; opcional bind a `subject_id`.  
4. Entregar ao gateway/orchestrator.  
5. Receber `OutboundMessage` e renderizar no canal.  
6. Nunca aplicar policy de domínio (isso é orchestrator).

## Checklist por adapter

- [ ] Auth documentada  
- [ ] Limite de tamanho / media  
- [ ] Idempotency (`message_id`)  
- [ ] Mapa de erros → user-visible genérico  
- [ ] Redaction de secrets na saída  
- [ ] Healthcheck / webhook verify  

## Exemplos de mapeamento (ilustrativo)

| Canal | external_id típico | thread |
|-------|-------------------|--------|
| CLI | `os_user@host` | cwd ou flag |
| Telegram | `user_id` | `chat_id` |
| Slack | `user_id` | `channel_id` + `thread_ts` |
| Web | `account_id` | `session_id` |
| MCP | `client_id` + token subject | `session_id` MCP |
| Cron | `system:scheduler` | `job_id` |
