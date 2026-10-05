# PENDENCIAS — Cadeia F1 → F6

Última atualização: 2026-10-05 18:05 UTC

> Ficheiro de estado da cadeia F1 → F6 (prompt do maestro de 2026-10-05). É lido no início de cada sessão e actualizado no fim de cada fase.
> **Não substitui** o `docs/initiatives/PENDENCIAS.md`, que continua a ser o documento único de estado do repo (tabela de 10 colunas, regra permanente). A linha do F1 no canónico aponta para este ficheiro.
> **Estados:** 🔒 Bloqueado · ⏳ Em curso · ✅ Concluído (critério de saída cumprido: PR aberto e CI verde; **o merge é do maestro**) · ❌ Bloqueado permanentemente.
> No canónico, um item só passa a FECHADO depois do merge (providência 2). Por isso o F1 lá continua EM CURSO enquanto os PRs desta cadeia estiverem abertos.

## Tabela de estado
| ID   | Descrição                                      | Estado     | Artefactos / Links                  | Critério de saída cumprido? |
|------|------------------------------------------------|------------|-------------------------------------|-----------------------------|
| T6a  | (pré-existente)                                | ✅ Merged  | PR #105 (merge `99b2cee`)           | Sim                         |
| T6b  | PDF funcional (fixture + teste + PR)           | ✅         | PR #106 (CI verde, 11 checks, incl. `test-ingest`); branch `feat/t6b-pdf-functional-fixture-and-test`; fixture `runner/tests/fixtures/ingest/pdf/` | Sim (merge pendente)        |
| T6c  | DOCX + XLSX                                    | ⏳         |                                     | Não                         |
| T6d  | Segurança de entrada                           | 🔒         |                                     | Não                         |
| T6e  | Encaixe na pipeline T6                         | 🔒         |                                     | Não                         |
| T6f  | Fecho F1 no PENDENCIAS                         | 🔒         |                                     | Não                         |
| F1b  | Docling (só se perda de estrutura)             | 🔒         |                                     | Não                         |
| F2   | Research web (Crawl4AI / scrape + provenance)  | 🔒         |                                     | Não                         |
| F3   | Provenance no retrieve                         | 🔒         |                                     | Não                         |
| F4   | marketing-capabilities.yaml                    | 🔒         |                                     | Não                         |
| F5   | Validação E2E real (1 run Gemini)              | 🔒         |                                     | Não                         |
| F6   | Hardening final + portfolio package            | 🔒         |                                     | Não                         |

## Histórico de fases
- 2026-10-05 · T6a · ✅ merged no #105 (`99b2cee`): esqueleto do `ingest_document` + adapter MarkItDown + 32 testes.
- 2026-10-05 · T6b · ✅ PR #106 aberto, CI verde: fixture PDF + gerador reprodutível + testes + job `test-ingest`.

## Riscos / bloqueios abertos
- **PR upstream no `microsoft/markitdown` (T6b, passo 6 do prompt): decisão do maestro.** Esta sessão só tem acesso aos repos `souzalrns/*`, e um PR num repo da Microsoft é uma acção pública em nome do DEV (fork, CLA da Microsoft, contacto com maintainers). Os PRs desta cadeia vão para a `main` da plataforma. As fixtures e os testes ficam prontos para servir de base a uma contribuição upstream, se o maestro a quiser.
- **F5 precisa de credenciais** (run real com Gemini): só o DEV o pode correr. O Claude prepara o comando e o molde de evidência.
- **F6 do prompt ≠ F6 do canónico.** No `PENDENCIAS.md`, o F6 é "UM domínio de prova, com o Domain Onboarding Cost medido; escolhido só depois do F5" (D-EP8). Neste ficheiro, F6 é "hardening final + portfolio package". Não se redefine um ID decidido: quando se chegar lá, o maestro escolhe (A/B/C) entre fazer os 2, renomear o do prompt ou fundi-los.
- **F4 do prompt ≈ F4 do canónico**, que também pede validação no E7 e maturidade de capability; e **F3 do canónico é mais largo** (validade/conflitos, source authority, golden set alargado, 33 ficheiros fora do MANIFEST). Cada fase cumpre o critério do prompt **e** regista o que falta do canónico, sem o cortar.
- **Escrita em produção:** pôr ficheiros convertidos no MANIFEST (`scripts/ingest_delta.py`) faz o merge escrever no Supabase. É decisão do maestro e fica fora do T6e (o T6e prova o encaixe contra Postgres local).

## Decisões de interpretação (registadas para revisão do maestro)
| Ponto do prompt | Conflito | Como foi feito |
|---|---|---|
| "criar PENDENCIAS.md com esta estrutura exacta" | Já existe o `PENDENCIAS.md` canónico, com 10 colunas fixas por regra permanente | Usada a alternativa que o próprio prompt prevê: `PENDENCIAS_T6.md` |
| "Abrir PR contra upstream/main" (T6b) | Sem acesso ao `microsoft/markitdown`; acção pública em nome do DEV | PR para a `main` da plataforma; o upstream fica como decisão (riscos, acima) |
| "Parar no fim de cada fase e esperar instrução" | O maestro, na mesma mensagem: "tens autonomia para prosseguir com tudo" | Fases em sequência, cada uma só com o critério da anterior cumprido; PRs empilhados, sem merge |
| "fixture em `tests/fixtures/pdf/`" | Os testes do repo vivem em `runner/tests/` | Caminho canónico: `runner/tests/fixtures/ingest/<formato>/` |
| "commits em inglês" | Os commits anteriores do repo estão em português | Commits desta cadeia em inglês (Conventional Commits); documentação em português, como o resto do repo |

## Mini-relatórios

```
FASE: T6b
DATA: 2026-10-05
ESTADO ANTERIOR → NOVO ESTADO: ⏳ → ✅ (merge pendente, do maestro)
ARTEFACTOS:
- runner/tests/fixtures/ingest/pdf/simple_synthetic.pdf (1748 bytes, 1 página) + generate_simple_synthetic.py
- runner/requirements-fixtures.txt (fpdf2==2.8.9), runner/tests/optional_deps.py
- runner/tests/test_ingest_fixtures.py (5 testes); test_ingest_document.py passa a exigir as deps no CI
- .github/workflows/runner-tests.yml: job test-ingest + scripts/ingest_document.py no filtro paths
- docs/initiatives/PENDENCIAS_T6.md (novo), PENDENCIAS.md (linha F1), PROGRESS-SESSAO.md
LINKS:
- PR: https://github.com/souzalrns/network-agents-setup/pull/106
- Branch: feat/t6b-pdf-functional-fixture-and-test
- Commits: 4598d9b, e256934, c84684e, 069aeb5
TESTES: pytest 602 passed, 10 skipped (sem extras); 37 passed com extras e INGEST_TEST_REQUIRED=1; CI 11/11 verde
PENDENCIAS.md: atualizado (sim: PENDENCIAS_T6.md e a linha F1 do canónico)
PRÓXIMO PASSO RECOMENDADO: T6c (DOCX + XLSX)
BLOQUEIOS: nenhum para a plataforma; o PR upstream no microsoft/markitdown fica como decisão do maestro
```
