# Maestro — decisão sobre o EXECUTION-PLAN v2

O rascunho está **ao nível padrão ouro**: evidência `ficheiro:linha`, correcções V1–V24 honestas, L5 reenquadrado como **revalidar** (não reconstruir), paths reais, dual-repo, R/W no F0, e o adendo §14 integrado. **Aprovo com as decisões abaixo.**

---

## Decisões D-EP1 … D-EP9 — **todas fechadas**

| ID | Decisão | **Escolha** |
|----|---------|-------------|
| **D-EP1** | Gravar o plano | **A** — gravar + arquivar fontes em `execution-plan-sources/` + OPEN-ITEMS F0–F6 + BOOTSTRAP |
| **D-EP2** | Lista de ingestão | **A** — só pack security no F0; restantes pack a pack (não os ~31 de uma vez) |
| **D-EP3** | C-2 (CHECK `council_*`) | **A** — DEV corre já (independente do F0; objectivo tokens) |
| **D-EP4** | Contrato F1 vs F0 | **A** — ADR/contrato em paralelo; **código MarkItDown só com F0 verde** |
| **D-EP5** | Ordem Fase 2a/2b | **A** — decidir depois do F5; **nada de Broker/Lease antes de F0–F6 + C-2** |
| **D-EP6** | Colisão “E” | **A** — neste plano, conectores = **ING-1..7**; E7 continua = validador `areas.py` |
| **D-EP7** | `MASTER-PLAN.md` | **A** — marcar histórico, apontar para EXECUTION-PLAN |
| **D-EP8** | Domínio F6 | **A** — escolher só após F5, com uso real |
| **D-EP9** | Duas pipelines ingest | **A** — **T6 canónico**; `ANM:ingest.yml` = JSON MCP / legado documentado |

Nada a reabrir em SEC, D1–D3, Dependabot, ou “security 100% pack”.

---

## Leitura do estado (aceite)

- **P0 ready ~19%** (3/16) — correcta; a % antiga 40–50% estava errada.  
- **L5:** existe + J3; falta cobertura, consumidor (`knowledge:`), golden set, passos 3/5.  
- **Security pack:** SEC-1/2 fechados; domain pack ainda partial + L5/run real UNVERIFIED.  
- **Marketing ready** só na cadeia SEO com Gemini real.  
- **LangGraph** dentro do plan_runner — OK; não é runtime paralelo.

---

## Instrução ao Claude Code (Etapa 1)

```text
D-EP1..D-EP9 = todas opção A (maestro 2026-10-03).

1. Gravar o rascunho consolidado v2 em:
   docs/architecture/EXECUTION-PLAN.md
   (remover o banner "RASCUNHO"; estado: aprovado maestro; main de referência 969d3ce / pós-#61.)

2. Arquivar fontes tal como estão em:
   docs/architecture/execution-plan-sources/
   (lista §17; o que não existir nesta sessão, omitir com nota "não fornecido".)

3. OPEN-ITEMS: registar F0–F6 (§9.4) + D-EP1..9 fechadas (A) + nota ING-1..7.
4. BOOTSTRAP.md: apontar para EXECUTION-PLAN.md.
5. MASTER-PLAN.md: cabeçalho histórico → EXECUTION-PLAN (D-EP7).
6. Commit + push + PR. Sem merge. Sem --force. Sem F1 código. Sem escrita prod (F0.4/F0.12).

Seguinte só após merge deste PR (ou ordem explícita): Etapa 2 = F0 só passos R.
```

---

## Ordem operacional imediata (humano + Claude)

| Quem | O quê |
|------|--------|
| Claude Code | Etapa 1 (gravar plano) |
| DEV | **C-2** (SQL council kinds) quando puder |
| DEV | Confirmar Oracle S27 (12 vs 24 GB) e S20 (bridge 401) |
| Depois | F0 passos R → PR → só então F0.4 (ingest security) com D-EP2 já A |

---

## O que **não** falta no documento

P0/P1/P2, F0 checklist R/W, Broker/Lease como norte, anti-padrões, dual-repo, provenance, DOC/Reuse, contract-first, maturidade de capability, T6 rule, peças desligadas (scrape/transcribe).

**Veredicto:** gravar (**D-EP1 = A**). Este ficheiro passa a ser o **plano de execução**; o estado vivo continua em STATUS/OPEN-ITEMS.
