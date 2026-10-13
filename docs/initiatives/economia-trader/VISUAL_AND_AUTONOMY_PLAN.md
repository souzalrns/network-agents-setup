# Plano visual e de autonomia — economia-trader

**Data:** 2026-10-13  
**Estado:** plano baseado na auditoria do código e nos estados de PR consultados; não é autorização para ordens reais.

## Decisões

1. **Visual A:** manter `dashboard.py` como interface operacional e fonte de informação de risco.
2. **Visual B:** manter `office.py`/Star-Office-UI como complemento opcional; substituir assets não comerciais antes de uso comercial.
3. **Autonomia:** considerar L2 paper como o alvo imediato; não declarar L4 live pronto até concluir integração e testes dos PRs #198 e #199.
4. **Runner:** PR #200 é independente das lacunas de trading e explicitamente requer decisão do maestro; não o mesclar automaticamente.
5. **Extração:** continuar a incubação no monorepo até existir checklist de release, interfaces estáveis e decisão de extração; não criar cópia paralela.

## Fases

### Fase 0 — inventário (concluída nesta auditoria)
- Confirmados os estados dos PRs #185–#193, #195–#196 como merged; #198–#200 abertos e sem merge.
- Inspecionados README, pyproject, changelog, plano de auditoria, documentos de adapters/monitores e módulos-chave de risco, runner e visual.
- Limitação: não foi executada a suite local nem uma chamada real à exchange nesta auditoria; resultados de testes mencionados abaixo são os descritos pelos PRs/workflow.

### Fase 1 — fechar a segurança operacional
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

## Matriz de rastreabilidade

| Lacuna | Evidência | Risco | Ação | Aceitação |
|---|---|---|---|---|
| Alertas operacionais ainda não integrados | PR #198 aberto | Falha crítica pode ficar só no diário/painel | Revisar e integrar depois de aprovação | Testes de canais, sanitização de segredos, canal indisponível não afeta trader |
| Fills/stops/reconciliação live incompletos na main | PR #199 aberto | Livro local pode divergir da corretora | Revisar, testar e integrar | Fills parciais, stop exchange, recuperação e mismatch cobertos |
| Runner externo em discussão | PR #200 aberto, pede decisão | Alteração de control plane sem autorização | Decisão separada do maestro | Contrato e regressão do runner aprovados |
| Assets de escritório não comerciais | Comentário do módulo `office.py` e PR #190 | Restrição de redistribuição/uso comercial | Substituir assets e guardar licenças | Licença de cada asset documentada |
| Estado visual pode ficar obsoleto | Ponte lê eventos do diário e mantém offset | Avatar parece ativo sem prova de atividade atual | Timestamp/frescura/estado desconhecido | Teste que estado deriva de evento recente |
| Testes reais de exchange ausentes | PRs descrevem transportes falsos; workflow não usa credenciais | Diferenças de API não capturadas por mocks | Testes controlados em testnet/paper account | Relatório de integração por exchange |
| Projeto ainda é incubado no monorepo | `EXEC-PLAN-AUDIT-PHASE.md` §0 decide A | Acoplamento a caminhos internos | Checklist de extração | Instalação e CI fora do monorepo passam |
| Pesos/licenças de modelo Kronos por validar | PR #192 / changelog | Uso sem direitos claros ou sem benefício comprovado | Verificar licença dos pesos e A/B com dados | Licença arquivada + resultado reproduzível |

## Próxima ação única

**Revisão técnica do PR #199 antes do #198**, porque reconciliação, fills e stops são a barreira principal para avaliar qualquer execução fora de paper. Isto não autoriza merge: primeiro revisar diffs, cobertura de testes e cenários de falha; a decisão final continua com o maestro.
