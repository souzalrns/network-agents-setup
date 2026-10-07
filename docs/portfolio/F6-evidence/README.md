# F6: evidence pack (cadeia F1 → F6)

> F6 da cadeia do prompt do maestro de 2026-10-05: **hardening + pacote de evidências + resumo de portfolio**. É o F6 do `docs/initiatives/PENDENCIAS_T6.md`. O F6 canónico do `PENDENCIAS.md` ("UM domínio de prova", D-EP8) é outro item e continua no §4 (P-23, opção A: "os 2").
> Estado a 2026-10-06. **Nenhuma escrita em produção foi feita para este pacote.** Não contém dumps de BD, segredos nem conteúdo de documentos.

| Ficheiro | O que tem |
|---|---|
| [`prs.md`](./prs.md) | Cada fase com os PRs (NAS e MCP), estado e link |
| [`decisions.md`](./decisions.md) | Decisões P-21 a P-36: escolha, data e quem decidiu |
| [`tests-and-ci.md`](./tests-and-ci.md) | Comandos para reproduzir os testes e a última corrida |
| [`run-e2e.md`](./run-e2e.md) | Provas contra produção: F0.7b, F3a (v2 activa) e o run real do F5 |
| [`hardening.md`](./hardening.md) | O checklist de hardening do F6 e o que foi corrigido |
| [`deferred.md`](./deferred.md) | O que ficou estacionado, porquê e o que o desbloqueia |

**Resumo de portfolio:** [`../WHAT-I-CONTRIBUTED.md`](../WHAT-I-CONTRIBUTED.md).

**Estado da cadeia:**

| Fase | Estado |
|---|---|
| F1 | ✅ FECHADO (#105–#110) |
| F2 | ✅ na cadeia (#111); no canónico continua EM CURSO (`discover`, fallback JS) |
| F3 | F3a, F3c e F3b-validade ✅ FECHADOS (#113, #119, #120; F3c confirmado em produção: 7 fontes, 15 chunks). O F3 fica BLOQUEADO só no que está estacionado: F3b-AUTH-1, F3b-GS-1 e F3-ART-1 |
| F4 | ✅ FECHADO (#114) |
| F5 | ✅ FECHADO (run real PASSOU, #115/#116) |
| F6-CADEIA | ✅ FECHADO (#121, merged 2026-10-06). O **F6 canónico** (domínio de prova, D-EP8) é outro item e continua BLOQUEADO |
