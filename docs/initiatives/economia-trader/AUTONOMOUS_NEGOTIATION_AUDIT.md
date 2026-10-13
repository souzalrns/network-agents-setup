# Auditoria de negociação autónoma — economia-trader

**Data:** 2026-10-13  
**Base principal:** `main` do `souzalrns/network-agents-setup`, código em `oss/economia-trader/` e estados confirmados dos PRs relacionados.

## Resumo executivo

O núcleo de negociação e a autonomia em paper já estão implementados em grande parte. **Não é correto tratar o sistema como pronto para operação autónoma real.** Os PRs #198 e #199, que completam alertas e reconciliação/fills/stops/drawdown de exchange, continuam abertos e sem merge. O PR #200 é de infraestrutura do runner e diz explicitamente que não deve ser mergeado sem decisão do maestro.

## Estado verificado dos PRs

| PR | Estado verificado | O que representa |
|---|---|---|
| [#185](https://github.com/souzalrns/network-agents-setup/pull/185) | merged | Plano da fase de auditoria |
| [#186](https://github.com/souzalrns/network-agents-setup/pull/186) | merged | Contratos, risco, gate, paper broker, diário e adapters iniciais |
| [#187](https://github.com/souzalrns/network-agents-setup/pull/187) | merged | Loop autónomo, estado persistente, saídas antes de entradas e auto-kill |
| [#188](https://github.com/souzalrns/network-agents-setup/pull/188) | merged | Reutilização de ccxt e alpaca-py |
| [#189](https://github.com/souzalrns/network-agents-setup/pull/189) | merged | OpenBB e TradingAgents como monitor/segunda opinião |
| [#190](https://github.com/souzalrns/network-agents-setup/pull/190) | merged | Painel, ponte Star-Office-UI e traces opcionais |
| [#191](https://github.com/souzalrns/network-agents-setup/pull/191) | merged | Sinais SEC/insiders, FinBERT e Adanos |
| [#192](https://github.com/souzalrns/network-agents-setup/pull/192) | merged | Confirmação de previsão Kronos |
| [#193](https://github.com/souzalrns/network-agents-setup/pull/193) | merged | Segunda opinião ai-hedge-fund em ambiente separado |
| [#195](https://github.com/souzalrns/network-agents-setup/pull/195) | merged | Polymarket read-only e export de pesquisa FinRL |
| [#196](https://github.com/souzalrns/network-agents-setup/pull/196) | merged | Grid spot limitado |
| [#198](https://github.com/souzalrns/network-agents-setup/pull/198) | **aberto, sem merge** | Alertas para auto-kill, grid recusado e erros repetidos |
| [#199](https://github.com/souzalrns/network-agents-setup/pull/199) | **aberto, sem merge** | Fills reais, stops na exchange e reconciliação/drawdown para testnet/live |
| [#200](https://github.com/souzalrns/network-agents-setup/pull/200) | **aberto, sem merge** | Devolver pacotes ao runner; o próprio PR diz que a decisão de merge pertence ao maestro |

O PR #194 não apareceu no conjunto auditado e não se presume que exista ou que seja necessário. O estado de qualquer PR deve ser reconsultado antes de uma decisão futura.

## O que existe no código merged

- Contratos: `EconomicEvent`, `TradeProposal`, `RiskAssessment`, `OrderIntent`, `Fill`, `SimulationRun` (descritos no changelog).
- Motor de risco determinístico fail-closed, com limites explícitos para valor da ordem, perda por operação, perda diária, símbolos permitidos, posições e exposição.
- Gate de execução por modo, kill switch, verificação de permissões da chave e aprovação humana por ordem para live; o aprovador predefinido é deny-all.
- Paper broker com taxas/slippage, backtest offline, diário JSONL encadeado por hash e verificação do diário.
- Runner persistente com saídas antes de entradas, controlo de repetição de evidência e auto-kill por drawdown/erros segundo o código merged.
- Adapters atuais baseados em ccxt para cripto spot e alpaca-py para ações/ETFs.
- Monitores OpenBB, analistas TradingAgents, sinais adicionais e grid spot limitado.
- Painel estático e integração visual opcional.

Fontes de código principais: `contracts.py`, `risk.py`, `safety.py`, `trader.py`, `runner.py`, `journal.py`, `exchanges/ccxt_spot.py`, `exchanges/alpaca_py.py`, `dashboard.py`, `office.py`.

## Lacunas e riscos bloqueantes

### P0 — não declarar live autónomo pronto

1. **Reconciliação, fills e stops reais:** o PR #199 ainda não está merged. A descrição do PR diz que pretende registar fills reais/parciais, colocar stops na exchange onde suportado e calcular drawdown sobre equity da exchange. Até integração e testes de aceitação, o caminho de live não tem evidência suficiente para ser considerado robusto.
2. **MEXC:** não tem testnet segundo a documentação interna; a rota de teste `/order/test` valida parâmetros/assinatura, mas não simula fills. O stop referido no PR #199 é client-side para MEXC, criando dependência de processo/rede.
3. **Alertas operacionais:** o PR #198 não está merged. O auto-kill aparece no painel/diário, mas a notificação externa resiliente descrita no PR ainda não está integrada em `main`.
4. **Teste de exchange real:** os próprios PRs indicam que os testes usam transportes falsos e não validam chamadas reais às exchanges. Isto é apropriado para CI, mas deixa integração de testnet como teste de aceitação pendente.
5. **Mandato de operação real:** PR #190 regista P-57 = “real autónomo depois de ≥ 2 semanas em paper”. Isso é uma condição insuficiente por si só: tempo decorrido sem critérios mensuráveis não prova qualidade, estabilidade, adequação do risco nem recuperação após falhas. Não converter esse mandato em autorização implícita para ativar live.

### P1 — risco, dados e reprodutibilidade

- Verificar em testes o comportamento perante fills parciais, ordem pendente, timeout depois de submissão, resposta duplicada, stop rejeitado/expirado, divergência de posição, relógio errado e reinício do runner.
- A regra “reconciliação só reduz posições locais” descrita no PR #199 é conservadora contra adoção de posições desconhecidas, mas divergências precisam de bloquear novas entradas e gerar intervenção, não apenas reduzir silenciosamente o livro.
- Confirmar idempotência de `client_order_id`, tratamento de rate limits e recuperação após falha de rede em cada adapter.
- Validar as fontes e tempos `event_at`, `published_at`, `observed_at`, `available_at`; nenhum backtest deve usar informação que ainda não estava disponível.
- Kronos: o changelog/PR deixa claro que a comparação A/B com dados reais e a licença dos pesos precisam de verificação; não tratar a previsão como alfa validado.
- Sinais de insiders/social/sentimento e opiniões LLM devem ser tratados como evidência incerta, nunca como substituto do motor de risco.
- Dependências opcionais pesadas (Torch/Transformers/LLM stacks) devem permanecer isoladas e não podem receber chaves de exchange.

### P2 — extração e operação

- O projeto ainda está incubado no monorepo, por decisão documentada em `EXEC-PLAN-AUDIT-PHASE.md`; não é ainda um repositório autónomo.
- Confirmar pacote/wheel instalado num ambiente limpo, suporte Python/CI e documentação do caminho de instalação fora do monorepo.
- Definir monitorização de serviço, retenção/backup do diário, política de rotação de logs, gestão de segredos e procedimento de incidente antes de qualquer live.

## Candidatos de negociação reutilizáveis

| Candidato | Uso apropriado | Decisão |
|---|---|---|
| TradingAgents (commit referenciado pelo projeto) | Segunda opinião de analistas/debate; não é motor de execução/risco | Já integrado como extra opcional; manter separado do gate |
| ai-hedge-fund | Segunda opinião de fundamentos em venv próprio | Já integrado como extra opcional; falha deve vetar, não executar |
| FinRobot | Candidato de pesquisa/benchmark; esta auditoria não confirmou aqui, ficheiro a ficheiro, o estado de licença/testes e a fronteira de execução da versão atual | Não adicionar sem auditoria específica |
| OpenTrade.ai | Candidato experimental para comparar UX/estratégias, não para substituir o núcleo de risco | Não adotar sem inspeção de licença, testes e caminhos de ordem |
| TradingAgents-AShare | A documentação preliminar aponta restrições PolyForm Noncommercial e termos adicionais | Rejeitar reutilização comercial até parecer jurídico |
| HashTrade / ClawTrade | Candidatos de comparação, não dependências atuais confirmadas | Não adicionar antes de auditar licença, execução live e segurança de credenciais |

## Níveis de maturidade

- **L0 — pesquisa/observação:** presente em monitores e sinais read-only.
- **L1 — propostas e simulação:** presente; propostas, risco, paper broker, backtest e diário.
- **L2 — ciclo autónomo em paper:** implementado no runner/grid, sujeito a validação operacional independente.
- **L3 — testnet/paper de corretora:** gate/adapters existem; a qualidade da integração externa precisa de testes de aceitação específicos.
- **L4 — live com aprovação humana por ordem:** o desenho/gate existe, mas não considero a operação real aprovada sem reconciliação/fills/stops, testes de integração, alertas e critérios de lançamento.
- **L5 — live autónomo sem aprovação por ordem:** fora de âmbito e não recomendado nesta fase.

## Critério mínimo antes de reavaliar live

1. Decisão explícita do maestro; nenhum desbloqueio por simples decurso de duas semanas.
2. #198 e #199 revistos, testados e integrados somente após aprovação.
3. Testes de falha/recuperação e reconciliação, mais ensaio em testnet/paper de corretora sem dinheiro real.
4. Critérios escritos e mensuráveis para drawdown, erro, divergência, latência, stop, exposição e desligamento.
5. Chaves de teste separadas; nenhuma chave de levantamento; segredo fora de logs/processos LLM.
6. Operação paper prolongada com amostra suficiente, métricas e relatório reproduzível; avaliação humana antes de qualquer autorização real.

## Conclusão

O que falta não é mais um agente de trading. É **concluir a camada de segurança operacional e provar a integração externa**. Prioridade: auditar/rever #198 e #199, desenhar critérios de aceitação e manter live bloqueado. O #200 é decisão separada de infraestrutura do runner e não deve ser mesclado automaticamente.
