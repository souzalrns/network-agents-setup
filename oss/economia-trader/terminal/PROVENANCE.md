# Proveniência de `oss/economia-trader/terminal/`

- **Origem:** [ErTasselli/OpenTerminal](https://github.com/ErTasselli/OpenTerminal), licença **MIT** (ver `LICENSE`,
  que fica intacto).
- **Commit:** `aed097c680cd8ec1c391ae06966babe7d6d91fc6` (2026-10-06).
- **Incluído em:** 2026-10-17, decisão do maestro de complementar o economia-trader com o terminal ("parcial ou
  integral, para complementar ou substituir"). A revisão completa está em
  `docs/initiatives/economia-trader/OPENTERMINAL.md`.

## O que mudou face ao upstream

| Ficheiro | Alteração | Porquê |
|---|---|---|
| `web/components/widgets/TvWidget.tsx`, `hls.js` | **removidos** | A "Live TV" retransmite canais com direitos (CNBC e Cheddar via `tier1streams.com`, um restream de terceiros). Não se distribui |
| `.github/`, `.claude/`, `docs/screenshots/` | removidos | Workflow e configuração próprios do upstream; o nosso CI é `.github/workflows/economia-trader-terminal.yml` |
| `README.md` → `UPSTREAM-README.md` | renomeado | O `README.md` passa a ser o nosso, em PT |
| `web/package.json` (`next` 15.5 → 16.4) e `server/package.json` (`fast-xml-parser` 4 → 5) + `package-lock.json` | dependências | `npm audit` de produção de 6 avisos (1 crítico, 3 altos) para **0**. Sem mudanças de código: 26 testes e os builds passaram |
| `server/package.json` (`vitest` 2 → 4.1.11) + `package-lock.json` | dependência de desenvolvimento | O `vitest` 2 arrastava `tinypool`, `vite` e `esbuild` com avisos (2 críticos, 1 alto, 3 moderados) que o alerta do Dependabot não conseguiu corrigir sozinho. `npm audit` completo a **0**; produção só muda o `nanoid` 3.3.19 → 3.3.20 |
| `server/vitest.config.ts` | novo | O vitest apanhava o `vitest.config.ts` da raiz do monorepo e não encontrava testes |
| `web/lib/api-key.ts` | `turbopackIgnore` | O Next 16 avisava que ler `../data/.api-key` puxava o projecto inteiro para o build |
| `server/src/providers/nasdaq.ts` | `replace("%")` → `replace(/%/g)` | Achado do semgrep (substituição incompleta) |
| `server/src/providers/tradingview.ts` | 2 × `// nosemgrep` com motivo | Falso positivo: o símbolo é chave de um `Map`, não de um objecto |
| `web/components/Terminal.tsx` | `Object.hasOwn` nos atalhos | `map["constructor"]` devolvia a função nativa |
| `server/src/agent.ts`, `server/src/routes/agent.ts`, `server/src/agent.test.ts`, `server/src/index.ts` | **novo**: ponte para o economia-trader | `GET /api/agent`, só leitura, protegido pela mesma chave do portfolio |
| `server/src/index.ts`, `server/package.json` (`express-rate-limit` 8) | limite de pedidos em `/api/portfolios` e `/api/agent` | Achado do CodeQL: rotas que lêem disco/SQLite sem um limitador que ele reconheça (o `rateLimit` próprio continua no resto da `/api`) |
| `server/src/routes/market.ts` (séries `EU_YIELD_SERIES`) | `// gitleaks:allow` | Falso positivo: são ids públicos de séries do BCE, não chaves |
| `web/components/widgets/AgentWidget.tsx`, `store/terminal.ts`, `Workspace.tsx`, `Sidebar.tsx` | **novo**: widget AGENT (⌥0) | Posições, stops (na exchange ou no cliente), caixa, grid, último tick (com `STALE`), decisões e alertas do agente |
| `web/components/Terminal.tsx`, `web/lib/symbol.ts` | **novo**: `/?symbol=SYM` | O painel do economia-trader liga cada ticker ao terminal; `BTCUSDT` abre `BTC` |

Cada alteração nossa está marcada no código com "network-agents-setup" ou "economia-trader bridge".

## Actualizar o upstream

Fazer clone do upstream num commit novo, comparar com este directório (`diff -r`, ignorando `node_modules`, `.next` e
`dist`), reaplicar as alterações da tabela e voltar a correr `npm ci && npm test -w server && npm run build &&
npm audit --omit=dev --audit-level=high`.
