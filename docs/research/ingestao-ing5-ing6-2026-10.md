# ING-5 (gitingest) e ING-6 (ScrapeGraphAI): análise para decisão

> **Data:** 2026-10-03. **IDs:** ING-5 e ING-6 em `docs/initiatives/PENDENCIAS.md` (antes "E5"/"E6" em `OPEN-ITEMS.md:20`).
> **Natureza:** análise técnica, pronta para o maestro decidir. **Nada instalado.**
> **Base:** `docs/architecture/ingestion-audit/AUDIT-INGESTION.md` (2026-09-19), reverificada hoje na página pública de cada projecto (resumo automático; confirmar antes de adoptar).
> **Enquadramento:** o ADR do F1 (`docs/architecture/adr/ADR-INGESTION-PRIMITIVES.md`, PR #81) trata qualquer ferramenta de aquisição como **adapter** de `ingest_document`/`fetch`, a alimentar o T6.

## ING-5 — gitingest (repositório de código → texto)

| Facto | 2026-09-19 (AUDIT-INGESTION) | 2026-10-03 (hoje) |
|---|---|---|
| Última versão | 0.3.1, de 31/07/2025 (`AUDIT-INGESTION.md:246`) | **Igual**: 0.3.1, de 31/07/2025 (PyPI). Mais de 14 meses sem release |
| Issue #605: o token (PAT) vai para os logs e para as mensagens de `RuntimeError` | Aberta a 08/09/2026, sem resposta (`:247`) | **Continua aberta**, sem resposta de maintainer e sem PR |
| Validação do host (`github.*`, por prefixo ou sufixo?) | NÃO VERIFICADO (`:243`) | Continua NÃO VERIFICADO (não li o código) |
| Limites | 10 MB por ficheiro, 500 MB no total, 60 s de timeout; o clone pode encher o disco antes do timeout (`:242-243`) | Sem mudança conhecida |

**Necessidade real neste repo:** nenhuma hoje.
- Nenhum plano, MANIFEST ou capability pede "repositório → texto".
- O caso mais próximo, ler ficheiros do próprio repo, já é servido pelo `repo_files` (SEC-1, `runner/plan_runner/repo_files.py`), que lê do disco sem clone.

| | Opção |
|---|---|
| **A (recomendada)** | **Não adoptar.** Se aparecer a necessidade (ex.: indexar um repo público de referência), fazer um **EXTRACT**: um adapter próprio de `ingest_document` com `connector_ref=git`, usando `git clone --depth 1 --filter=blob:none` e um sparse-checkout com tecto de bytes. A mitigação vem do próprio AUDIT-INGESTION (`:250`) |
| B | Adoptar com reservas, como o audit dizia: pin `==0.3.1`, só repos públicos e nunca com token enquanto a #605 estiver aberta |
| C | Rejeitar de vez e retirar do backlog |

**Porque A:**
- B traz uma dependência órfã com uma falha de credenciais aberta, sem caso de uso;
- C fecha uma porta que o EXTRACT deixa aberta a custo baixo;
- A não corta: regista o caminho para quando houver necessidade.

## ING-6 — ScrapeGraphAI (scraping com LLM)

| Facto | Evidência (2026-10-03) |
|---|---|
| "Python scraper based on AI": um LLM + grafo de passos cria o pipeline de extracção | Página do repo `ScrapeGraphAI/Scrapegraph-ai` |
| **Precisa de um LLM em cada extracção** (OpenAI, Groq, Gemini, Azure ou Ollama local) | Idem |
| MIT, 31,5k ★, não arquivado | Idem |
| Ainda sem veredicto ScrapeGraphAI vs Crawl4AI | `docs/architecture/meta-validation/AUDIT-SCOPE-2026-09-19.md:96` |

**Encaixe neste repo:**
- **Duplica o que já existe.**
  - O `fetch` (F2) obtém o conteúdo: hoje o `ANM:.github/workflows/scrape.yml`, e o Crawl4AI se o superar.
  - A extracção semântica já é feita pelo **worker Gemini** num passo do plano (`external_worker.py`), com orçamento (BUDGET/D6), ledger e provenance.
  - O ScrapeGraphAI juntaria as 2 coisas numa caixa negra, **fora** do ledger e do tecto de custo.
- **Custo:** com o Gemini free tier o custo pode ser zero, mas cada página gasta tokens fora do `token_usage`. Com o Ollama local, precisa de infraestrutura (S19, bloqueado).

| | Opção |
|---|---|
| **A (recomendada)** | **Não adoptar.** No F2, o padrão fica `fetch` (`scrape.yml`/Crawl4AI) → conteúdo normalizado com provenance → passo do worker para a extracção. Reavaliar só se o F2 mostrar, com evidência, um site que esse padrão não resolve |
| B | Spike no F2, lado a lado com `fetch` + worker, com o mesmo golden set |
| C | Rejeitar de vez |

**Porque A:**
- mantém o custo e a provenance dentro do ledger e do D6;
- não acrescenta um 2.º sítio a chamar LLMs;
- B só faz sentido se o F2 mostrar uma lacuna;
- C fecha cedo demais.

## Resumo

| ID | Recomendação | Reabrir quando |
|---|---|---|
| ING-5 | A: não adoptar; EXTRACT próprio se houver necessidade | Aparecer um caso "repo → L5" |
| ING-6 | A: não adoptar; `fetch` + worker no F2 | O F2 mostrar uma lacuna com evidência |
