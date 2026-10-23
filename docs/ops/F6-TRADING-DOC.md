# F6 — domínio de prova trading: Domain Onboarding Cost medido

> EXECUTION-PLAN §7 F6 e §15.9; P-79 = A (domínio = trading) e âmbito A + área nova A
> (maestro, 2026-10-23: "segue com tudo o que recomendou").
> Âmbito: pack de **análise, sem execução**. A execução (paper/testnet/live) continua no
> `oss/economia-trader`, fora do runner, com os seus próprios gates. Dinheiro real bloqueado.

## 1. O que o pack acrescenta

| Tipo | Quantidade | Ficheiros |
|---|---|---|
| Knowledge packs | 2 | `docs/knowledge/trading/risk-policy.md`, `post-trade-review-method.md` (escritos a partir do README e do código do economia-trader) |
| Skills | 3 | `skills/trading/{market_analysis,risk_review,post_trade_review}/SKILL.md` |
| Agentes | 3 | `agents/trading/*.agent.md` |
| Tools novas | 0 | Reusa `fetch_url` (F2) e `repo_files` (SEC-1) |
| Capability file | 1 | `config/trading-capabilities.yaml` (níveis `read`/`prepare`; `act` proibido) |
| Planos | 2 | `docs/orchestration/trading/templates/examples/{market-analysis-demo,post-trade-review-demo}.plan.yaml` |
| Validation suite | 1 | `runner/tests/test_f6_trading_pack.py` (10 testes) |
| Fixture | 1 | `fixtures/paper-review-sample.json`: saída real do `economia-trader review` sobre um journal fictício em paper |
| Registo | 3 ficheiros de dados | `config/areas.yaml` (área `trading`; `trading`, `bolsa` e `cripto` saem da `finance`), `config/web-allowlist.yaml` (área `trading`, só domínios já aprovados para a `finance`), `scripts/ingest_delta.py` (2 linhas no `EXCLUDED`, ver A-1) |

## 2. Domain Onboarding Cost

```
DOC = core files modified + core code changes + new infrastructure + new runtime
      + new persistence + new orchestration logic
    = 0 + 0 + 0 + 0 + 0 + 0 = 0
```

- **Core files modified = 0:** `git diff main -- runner/plan_runner scripts/ingest_apply.py` vazio. Há um teste que o guarda: `test_core_nao_sabe_que_o_dominio_existe` falha se algum ficheiro do core passar a nomear `trading`.
- **Fora do core, mas com nota:**
  - `scripts/ingest_delta.py` mudou (2 entradas de dados no `EXCLUDED`): é um registo, mas vive num `.py` (A-2);
  - 2 testes de inventário tiveram de ser actualizados (`test_capabilities.py`: lista exacta dos ficheiros de capabilities; `test_web_allowlist.py`: a allowlist do maestro). O segundo é intencional: a allowlist só muda por decisão do maestro.

**Reuse Ratio** = capacidades universais reutilizadas / capacidades necessárias = **6 / 9 = 0,67**:

- **Reutilizadas (6):**
  - router por área;
  - `fetch_url` com allowlist e proveniência;
  - `repo_files`;
  - grounding completo em área de risco;
  - gate humano `plan_approve`;
  - `meta.sources` no artefacto (F3-ART-1).
- **Novas, de domínio (3):** as 3 capabilities de trading.

## 3. Provas

| Prova | Evidência |
|---|---|
| E7 válido com o domínio novo | `python -m plan_runner.areas` → 11 áreas, 79 agentes, 3 ficheiros de capabilities válidos |
| Maturidade medida | `--maturity` → as 3 capabilities `EXECUTABLE` |
| Router | pedidos com `backtest`, `cripto`, `bolsa` e `trader` caem só na área `trading` |
| Ponta a ponta (stub) | os 2 planos correm e param no gate humano |
| Ponta a ponta (external, Gemini falso) | o passo recebe a skill de trading, grounding `full`, o método e o JSON da revisão |
| Sem execução | nenhuma capability com `act`; `policy.act_in_production: forbidden` |
| Suite completa | 1121 testes do runner a passar |

**Falta para o "done" do F6:** 1 run real de cada plano com Gemini (o DEV; o `market-analysis-demo` precisa de `PLAN_RUNNER_TOOLS=1`). Comandos no topo de cada plano.

## 4. Achados: abstracções incompletas (o objectivo do F6 é encontrá-las)

- **A-1 — o ingest não conhece kbs novas.**
  - `scripts/ingest_apply.py::_kb_for` tem uma lista fixa (`security`, `marketing`, `design`, `produto-tech`).
  - Uma fonte com `agent_id` `trading` ficaria com `kb = global`. O retrieve ainda a encontrava (filtra por `agent_id`), mas com a etiqueta errada, que é o que o R-005 corrigiu.
  - Por isso o conhecimento do pack entra pelos planos via `repo_files` e fica no `EXCLUDED`, até à decisão **P-80**.
- **A-2 — o MANIFEST e o EXCLUDED são dados dentro de um `.py`.** Registar conhecimento de um domínio novo obriga a editar um script.
- **A-3 — um teste fixa a lista exacta de domínios.** `test_capabilities.py` exige uma lista exacta de ficheiros, por isso cada domínio novo tem de o editar. Baixo impacto.
- **A-4 — `pilots/` não está todo no `.gitignore`.** Só `pilots/_pytest_*` está. Um run manual deixa pastas por seguir no git. Baixo impacto.
