# Maturidade das capabilities (F4-MAT-1, P-38 = B)

**A maturidade é medida, não declarada.** Os YAML de capabilities (`config/*-capabilities.yaml`) não têm campo de maturidade, e o `status` (`implemented`/`partial`/`deferred`/`planned`) continua a dizer o âmbito declarado. O nível de cada capability é calculado a partir da evidência que existe no repo, em `runner/plan_runner/capabilities.py` (`capability_maturity`).

```
cd runner && python -m plan_runner.areas --maturity
```

## Escala (EXECUTION-PLAN §15.7)

Cada nível exige o anterior:

| Nível | Evidência que o sustenta |
|---|---|
| DRAFT | a capability não tem `action` |
| DECLARED | tem `action`, mas falta o agente ou a skill (ou não existem) |
| WIRED | `action` + agente + skill existentes: o executor está ligado |
| EXECUTABLE | pelo menos 1 plano do runner (`docs/orchestration/**/*.plan.yaml`) usa a `action` |
| VALIDATED | um teste de `runner/tests/` corre esse plano com o Gemini falso: o ficheiro cita o path do plano e troca o `httpx_transport` do worker |
| PROVEN | um run real desse plano está registado em `config/capability-runs.yaml`, e o E7 verifica-o contra o documento de evidência |

**Tecto pelo `status`:** uma capability que não está `implemented` fica no máximo em EXECUTABLE. Várias capabilities partilham a mesma `action` e o mesmo agente; por exemplo, `secrets_hygiene`, `supply_chain` e `mcp_surface` usam o `security_audit`. Um run do auditor não prova a parte que o `status: partial` diz que falta.

## Registar um run real (PROVEN)

Depois de um run com o provider real (`--worker gemini`) que passou:
1. Escreve a evidência num documento do repo: o veredicto, o plano e o `run_id`. Por exemplo, a §4 do `docs/ops/F5-E2E-RUN.md`.
2. Acrescenta uma entrada a `config/capability-runs.yaml` com:
   - `id`, `date`, `run_id` (se houver);
   - `plan`;
   - `worker: gemini`;
   - `verdict: passed`;
   - `evidence` (o documento);
   - `anchor` (um texto que esse documento contém).
3. `python -m plan_runner.areas` (E7), que o CI corre quando muda o registo ou um destes documentos, recusa a entrada se:
   - o documento não contiver o `anchor`, o nome do plano e o `run_id`;
   - o plano não existir;
   - o `worker` não for `gemini`.

Um run `failed` é aceite no registo, mas não prova nada.

## Estado medido (2026-10-07)

| Domínio | PROVEN | VALIDATED | EXECUTABLE | WIRED | DECLARED | DRAFT |
|---|---|---|---|---|---|---|
| security | `triage`, `defensive_audit`, `security_report` (F5, `run_9017d441d1`) | — | `secrets_hygiene`, `supply_chain`, `mcp_surface`, `hardening_recommend` (tecto do `partial`) | — | — | `agent_redteam_lab` |
| marketing | `market_research`, `seo_brief`, `answer_first_copy`, `ai_findability_review` (B1, `seo-article-demo`) | — | 11 `implemented` com plano mas sem teste com o Gemini falso | `transcript_analysis` | `visual_identity` | `performance_analysis` |

O teste `runner/tests/test_capabilities.py::test_maturidade_real_do_repo` fixa as linhas-chave desta tabela. Se a evidência mudar e a tabela deixar de bater, o CI falha.

**Para subir um nível:**
- **de EXECUTABLE a VALIDATED:** um teste com o Gemini falso que corra o plano dessa `action`. É o caso das 11 de marketing.
- **de VALIDATED a PROVEN:** um run real registado.
