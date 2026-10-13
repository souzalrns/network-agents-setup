# Níveis de autonomia — economia-trader

**Data:** 2026-10-13  
**Regra central:** autonomia de análise ≠ autorização financeira.

| Nível | Capacidade | Estado atual | Portão necessário |
|---|---|---|---|
| L0 — observar | Recolher dados públicos, notícias, macro e sinais read-only | Implementado por monitores opcionais | Limites de taxa, proveniência e disponibilidade dos dados |
| L1 — propor | Gerar candidatos/propostas explicadas com evidências | Implementado | Contrato validado; evidência com timestamps; proposta não executa |
| L2 — paper autónomo | Fazer entradas/saídas simuladas, aplicar limites, guardar estado e diário | Implementado pelo runner/grid, com paper como padrão | Testes determinísticos, backtest sem look-ahead, limites explícitos, kill switch |
| L3 — testnet/paper da corretora | Enviar ordens de teste a ambiente de simulação da corretora | Gate/adapters presentes | Chaves dedicadas, ambiente explicitamente configurado, teste de integração e reconciliação |
| L4 — live com aprovação humana por ordem | Enviar ordens reais só após risk gate e aprovação individual | Código de gate existe; **não considerar pronto para uso** enquanto #198/#199 não forem integrados e validados | Aprovação explícita por ordem, chave sem levantamento, stops/reconciliação/fills reais, alertas e critérios formais de lançamento |
| L5 — live sem aprovação por ordem | Sistema decide e executa operações reais sem aprovação humana individual | Fora de âmbito | Não habilitar nesta fase; exigiria decisão de governança separada e análise de risco reforçada |

## Invariantes de segurança

1. O analista/LLM só emite proposta; não recebe chaves de exchange nem chama diretamente o broker para enviar ordens.
2. Cada proposta passa por motor determinístico de risco e gate de execução; qualquer avaliação ausente ou falha deve resultar em recusa.
3. Limites financeiros são explícitos; não criar valores monetários predefinidos silenciosos.
4. Kill switch interrompe novas operações; reativação é manual e auditável.
5. Modo de execução deve ser visível na CLI e painel. A mudança de paper para testnet/live não pode ser implícita.
6. Chaves de paper/testnet/live são separadas; segredos não entram em prompts, traces, evidências LLM ou logs.
7. Divergência entre estado local e corretora bloqueia novas entradas até reconciliação; não adotar saldo/posição desconhecida sem decisão humana.
8. Stops e ordens de saída têm comportamento de falha documentado por exchange. Stop client-side não deve ser descrito como equivalente a stop na exchange.
9. O diário é evidência operacional, não garantia de correção; monitorizar continuidade, integridade, backup e retenção.
10. Nenhum indicador, previsão, votação de agentes ou backtest autoriza sozinho uma operação real.

## Critérios de progressão

- L0→L1: proveniência, timestamps e schema validados.
- L1→L2: simulação reproduzível, limites de risco fail-closed, diário verificável e testes de look-ahead.
- L2→L3: configuração isolada, chaves de teste e testes de integração por exchange; MEXC exige cuidado porque `/order/test` não executa nem prova fill.
- L3→L4: critérios de lançamento aprovados pelo maestro, ensaios de falhas, fills parciais, stops, reconciliação, alertas, drawdown de equity e idempotência. Aprovação humana por ordem continua obrigatória.
- L4→L5: **não planeado**; requer decisão explícita de governança e não é uma consequência automática do bom resultado em paper.

## Critérios quantitativos a definir antes de qualquer lançamento

Não existem valores universais seguros. O responsável deve definir e aprovar previamente:
- drawdown máximo por sessão/dia e desde o pico;
- perda diária e por trade;
- exposição máxima e número de posições;
- tolerância para divergência de posição/equity;
- número de erros consecutivos e timeout de feed/exchange;
- latência máxima de monitorização e idade máxima de dados;
- duração e amostra mínima de paper, separadas por mercado/estratégia;
- condições de parar, recuperar e recomeçar após incidente.

## Decisão atual

Manter L0–L2 como âmbito de desenvolvimento e validação. L3 só após ensaio em ambientes de teste. L4 continua bloqueado para declaração de prontidão enquanto os PRs #198/#199 e os testes de integração estiverem pendentes. Não habilitar L5.
