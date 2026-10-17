# Plano visual e de autonomia — economia-trader

**Data:** 2026-10-13  
**Estado:** plano baseado na auditoria do código e nos estados de PR consultados; não é autorização para ordens reais.

## Estado pós-merge (2026-10-13, decisão do maestro na #201)

| PR | Squash em `main` | O que ficou em `main` |
|---|---|---|
| #200 | `d87554e` | Runner usa os pacotes publicados: `doneproof` (done_when), `fetchtron` (web_fetch), `hitlwright` (hitl), `tokenwright` (cost). Independente do trader |
| #198 | `c972fb5` | Alertas: `auto_kill`, `grid_refused`, erros seguidos (`--errors-after`); Telegram, webhook e SMTP só por ambiente; `alerts.jsonl`; segredos redigidos; canal em baixo nunca pára o trader |
| #199 | `2c851ac` | Testnet/live: fill só quando a exchange confirma (parciais incluídos), stop pousado na exchange (Bybit; Alpaca GTC/DAY; MEXC fica client-side), cancelamento do stop antes de vender, `sync_positions` só ajusta para baixo (`reconcile_mismatch`), drawdown/auto-kill sobre o equity real |

Conflito resolvido: só no `oss/economia-trader/README.md` (#198 × #199), mantendo as duas secções. CI
verde nos três antes do merge; em `main`: economia-trader 148 passed, runner 966 passed.

Validado depois do merge, nesta sessão: regressão paper; `alerts --test` (o bug de pasta nova foi
corrigido no PR #202, sem merge); script do smoke testnet, offline (7/7). **Não** validado: chamadas
reais a Bybit testnet ou Alpaca paper, porque a rede da sessão as bloqueia (ver `SMOKE-TESTNET.md` §4).
Defaults inalterados: paper por omissão, testnet atrás de `ECONOMIA_TRADER_ALLOW_TESTNET=1`, live
fechado.

## Decisões

1. **Visual A:** manter `dashboard.py` como interface operacional e fonte de informação de risco.
2. **Visual B:** manter `office.py`/Star-Office-UI como complemento opcional; substituir assets não comerciais antes de uso comercial.
3. **Autonomia:** L2 paper é o modo por omissão; L3 só depois do smoke testnet (`SMOKE-TESTNET.md`); **L4 bloqueado** até haver evidência de testnet e decisão do maestro (`AUTONOMY_LEVELS.md`).
4. **Runner:** PR #200 mergeado por decisão do maestro (2026-10-13); não toca no trader.
5. **Extração:** continuar a incubação no monorepo até existir checklist de release, interfaces estáveis e decisão de extração; não criar cópia paralela.

## Fases

### Fase 0 — inventário (concluída nesta auditoria)
- Confirmados os estados dos PRs #185–#193, #195–#196 como merged; #198–#200 abertos e sem merge.
- Inspecionados README, pyproject, changelog, plano de auditoria, documentos de adapters/monitores e módulos-chave de risco, runner e visual.
- Limitação: não foi executada a suite local nem uma chamada real à exchange nesta auditoria; resultados de testes mencionados abaixo são os descritos pelos PRs/workflow.

### Fase 1 — fechar a segurança operacional
**Estado 2026-10-13:** #198 e #199 mergeados. Faltam o smoke testnet (`SMOKE-TESTNET.md`) e as lacunas G1/G2 (abaixo).
- Rever #198 (alertas), #199 (fills/stops/reconciliação/drawdown).
- Escrever testes de aceitação para partial fills, timeout após submissão, duplicação/retry, stop cancel/replace, reinício, divergência de equity/posição e falha de rede.
- Validar que divergência ou falha de stop bloqueia novas entradas e produz alerta acionável.
- Não fazer merge até reviews e CI passarem e os critérios estarem documentados.

### Fase 2 — provar L2/L3
- Executar backtests offline reproduzíveis, com estratégia/config/version hash guardados.
- Executar paper com mercado atual sem enviar ordens reais e avaliar taxas, slippage, drawdown, erros, rejeições, turnover e diferenças entre sinais e fills simulados.
- Para L3, executar teste controlado com chaves testnet/paper dedicadas. Guardar logs sanitizados e resultados; nunca guardar chaves.
- MEXC: documentar que a ordem de teste valida pedido mas não simula fill.

### Fase 3 — fechar camada visual
- Adicionar timestamp, fonte e idade do último evento por personagem/painel.
- Mostrar “sem atualização” se não houver evento recente; sem estados ativos inventados.
- Criar teste de contrato que cada estado visual corresponde a evento conhecido do diário.
- Substituir assets não comerciais por arte licenciada para uso comercial ou arte própria.
- Garantir que o escritório pode cair sem afetar trading; não expor segredos no `detail`.

### Fase 4 — preparar extração
- Tornar o pacote instalável/testável fora da estrutura do monorepo.
- Remover referências a caminhos relativos internos que sejam necessários só no monorepo; substituir por extras e interfaces públicas.
- Manter CI independente, SBOM/lockfile ou estratégia de pins, política de vulnerabilidades e release checklist.
- Preservar histórico quando tecnicamente viável e não manter duas fontes de verdade.
- Extração só depois de revisão de arquitetura e decisão explícita; sem publicar no PyPI nesta fase.

## Lacunas de segurança operacional que ficam depois dos merges

Encontradas ao rever `trader.py` e `alerts.py` em `main` contra as invariantes 7 e 8 de
`AUTONOMY_LEVELS.md`. Não foram implementadas aqui: esta tarefa era integrar e documentar.

**G1. A divergência e a degradação do stop não geram alerta.** O `AlertWatcher` só conhece
`auto_kill`, `grid_refused` e erros seguidos (`alerts.py`, `ERROR_KINDS`). `reconcile_mismatch`,
`stop_client_side` (a exchange recusou o stop) e `stop_dropped` (stop expirado/cancelado pela venue)
ficam só no diário.
- A) Acrescentar estas três regras ao `AlertWatcher` (nível `warning`; `critical` para
  `stop_client_side` fora da MEXC). **RECOMENDADA**: é a invariante 8 ("stop client-side não é
  equivalente") e usa o mecanismo que já existe; são uns 15 linhas mais testes.
- B) Mostrar só no painel. Não chega, porque ninguém está a olhar para o painel às 3 da manhã.
- C) Deixar como está. Não, porque viola a invariante 7.

**G2. A divergência não bloqueia novas entradas.** `sync_positions` ajusta o livro para baixo e
regista, mas o tick seguinte pode voltar a comprar o mesmo símbolo.
- A) Pausar as entradas no símbolo com `reconcile_mismatch` até um `unkill`/ack humano, mantendo as
  saídas. **RECOMENDADA**: é literalmente a invariante 7, e as saídas continuam livres.
- B) Activar o kill switch global em qualquer divergência. É mais simples, mas pára tudo por causa
  de um símbolo.
- C) Só alertar (G1). Não fecha a invariante.

Ordem proposta: smoke testnet → G1 → G2 → L3 prolongado. Cada um num PR próprio, sem merge
automático.

## Camada visual: gaps documentados (sem reconstruir)

`dashboard.py` continua a ser a interface operacional principal. Star-Office-UI (`office.py`) é
opcional: o código é MIT, mas a arte é **não comercial**, por isso não se usa em contexto comercial
enquanto não for substituída. Os gaps que se seguem ficam registados; a implementação vem depois do
smoke e só se houver tempo.

- **V1. Frescura:** o painel não mostra quando foi gerado nem a idade do último `run`. Falta um card
  "último tick há N min" com o estado `SEM ATUALIZAÇÃO` acima de um limiar.
- **V2. Sinais do #198/#199 sem destaque:** stops na exchange (`exchange_stops`), ordens pendentes,
  `reconcile_mismatch`, `stop_client_side` e o último alerta de `alerts.jsonl` só aparecem na linha
  do tempo genérica. Faltam cards/tabela.
- **V3. Escritório:** `office.map_entry` ignora os eventos novos (`stop_*`, `reconcile_mismatch`,
  `order_unfilled`), e o `detail` de `error` vai em bruto. As mensagens de erro da exchange não
  levam chaves, mas devem passar pelo mesmo `_redact` dos alertas antes de sair do processo.
- **V4. DEMO:** qualquer estado do escritório que não venha do diário (agentes de demonstração do
  Star-Office-UI) tem de aparecer marcado como DEMO.

## Extração para repositório próprio: critérios (não extrair agora)

Extrai-se `oss/economia-trader/` para um repo próprio só quando houver, ao mesmo tempo:
(1) o smoke testnet aprovado e G1/G2 fechados, para não mudar de casa a meio da validação de segurança;
(2) CI verde em py3.10 e py3.13 que instale e teste o pacote fora do monorepo, sem caminhos relativos
ao monorepo (o CI de hoje já instala `-e ../hitlwright`, portanto essa dependência tem de vir do
PyPI);
(3) interfaces estáveis durante pelo menos 2 semanas sem breaking changes: `Exchange`/`Reconciling`,
`TradeProposal`, o formato do diário e o `AlertWatcher`;
(4) decisão explícita do maestro, com o histórico preservado (`git filter-repo` do caminho) e uma só
fonte de verdade a partir desse dia.

## Matriz de rastreabilidade

| Lacuna | Evidência | Risco | Ação | Aceitação |
|---|---|---|---|---|
| Alertas operacionais | **#198 mergeado** (`c972fb5`); fix de pasta nova no #202 | Divergência/stop degradado ainda sem alerta (G1) | G1-A | Testes de canais e sanitização (feitos); regras novas cobertas por testes |
| Fills/stops/reconciliação | **#199 mergeado** (`2c851ac`), 11 testes de reconcile | Divergência não bloqueia entradas (G2); sem prova contra exchange real | Smoke testnet + G2-A | `SMOKE-TESTNET.md` 7/7 em Bybit testnet; teste de bloqueio por símbolo |
| Runner devolve pacotes publicados | **#200 mergeado** (`d87554e`) | Nenhum para o trader | Nenhuma | Runner 966 passed em `main` |
| Assets de escritório não comerciais | Comentário do módulo `office.py` e PR #190 | Restrição de redistribuição/uso comercial | Substituir assets e guardar licenças | Licença de cada asset documentada |
| Estado visual pode ficar obsoleto | Ponte lê eventos do diário e mantém offset | Avatar parece ativo sem prova de atividade atual | Timestamp/frescura/estado desconhecido | Teste que estado deriva de evento recente |
| Testes reais de exchange ausentes | Script `examples/smoke_testnet.py` validado offline; rede da sessão bloqueia as testnets | Diferenças de API não capturadas por mocks | Maestro corre `SMOKE-TESTNET.md` | JSON 7/7 + diário sanitizado anexados à #201 |
| Projeto ainda é incubado no monorepo | `EXEC-PLAN-AUDIT-PHASE.md` §0 decide A | Acoplamento a caminhos internos | Checklist de extração | Instalação e CI fora do monorepo passam |
| Pesos/licenças de modelo Kronos por validar | PR #192 / changelog | Uso sem direitos claros ou sem benefício comprovado | Verificar licença dos pesos e A/B com dados | Licença arquivada + resultado reproduzível |

## Próxima ação única

**Correr o smoke testnet de `SMOKE-TESTNET.md` na Bybit testnet**, numa máquina com rede e chaves de
teste, e anexar o JSON 7/7 à #201. Sem isto, G1/G2 e L3 prolongado ficam à espera e L4 continua
bloqueado.
