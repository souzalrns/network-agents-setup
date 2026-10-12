# Pesquisa fundamental com os plugins oficiais da Anthropic (fora do loop autónomo)

> **Decisão P-66 = A** (maestro, 2026-10-12). Fonte: `anthropics/financial-services` (commit `574ed36`,
> 2026-09-21, Apache-2.0). Nada aqui é recomendação de investimento: os agentes produzem rascunhos para
> revisão humana (aviso do próprio repositório).

## Para que serve aqui

O loop autónomo (`economia-trader run`) decide com regras e travas. Estes plugins servem **a ti**, no Claude
Code, para perceberes um ativo antes de rever o mandato, de aprovar uma ordem real ou de afinar uma versão:

| Comando | O que dá |
|---|---|
| `/earnings` · `/earnings-preview` | Leitura de resultados (call + filings) e o que esperar do próximo |
| `/catalysts` | Calendário de catalisadores do ativo (complementa o bloqueio macro do trader) |
| `/thesis` | Tese e o que a invalidaria (útil para rever um veto ou uma compra do sistema) |
| `/screen` · `/sector` | Ideias e panorama do setor (comparar com o que a triagem de fluxo e os insiders encontraram) |
| Market Researcher / Earnings Reviewer | As mesmas tarefas como agentes ponta a ponta |

## Instalar (Claude Code, na tua máquina)

```bash
claude plugin marketplace add anthropics/financial-services
claude plugin install financial-analysis@claude-for-financial-services   # base: skills + conectores
claude plugin install equity-research@claude-for-financial-services
claude plugin install market-researcher@claude-for-financial-services
claude plugin install earnings-reviewer@claude-for-financial-services
```

**Dados:** os conectores MCP que vêm incluídos (FactSet, Morningstar, PitchBook, Moody's, LSEG, S&P/Kensho,
Daloopa, Aiera) são **pagos e institucionais**: sem conta, ficam desligados. As skills funcionam com os filings
da SEC (o `economia-trader monitor --insiders` já os usa) e com o que lhes deres.

## O que não entra (P-67)

Os vários "Osiris" ficam de fora:
- **OSINT "alternativa ao Palantir":** é infraestrutura e vigilância (P-64), com forks duvidosos (um promove um
  token cripto).
- **Memória:** já temos memória L4, o diário e o estado persistido.
- **CS2:** é um cheat de jogo.
- **"Vector Osiris":** não se encontrou. A descrição corresponde ao TradingAgents, que já está integrado.
