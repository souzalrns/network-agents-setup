# Auditoria de Agentes — Fase 3: Knowledge / Ingestion

Continuação de `FASE1-AGENTES.md`/`FASE2-AGENTES.md`. Mesma disciplina: código > README.

**Nota de numeração:** esta fase cobre a secção 2.6 (Knowledge/Ingestion) da auditoria pedida — chamada "Fase 2" numa proposta de agrupamento entretanto sugerida pelo utilizador. A numeração sequencial deste repo (`FASE1`, `FASE2`, `FASE3`...) manteve-se pela ordem real de execução, não pela ordem da proposta; a tabela de reconciliação completa entre as duas fica em `AUDIT-AGENTS.md` (síntese final).

## 0. Baseline interna confirmada

O pipeline de conhecimento deste repo (`runner/plan_runner/knowledge.py`, `chunking.py`, `embedder.py`, `supabase_writer.py`) **só ingere Markdown** — zero menções a web/YouTube/GitHub/PDF/OCR/áudio no código, confirmado por busca. `MCP-MAPPING.md` (secção 7) confirma que `yt-dlp`+`faster-whisper base` **já existem** no repo irmão `agent-network-mcp`, mas só como pipeline de transcrição isolado (`.github/workflows/transcribe.yml` → Supabase `transcripts`) — **nunca ligado** ao pipeline de RAG. É um achado de fiação desligada, da mesma família dos já registados nas Fases 1-2 (`Orchestrator.ts` MOCK, superfície MCP mais estreita que o runtime).

## 1. Ingestão Web

| Ferramenta | Estrelas/Licença/Actividade | O que faz de facto | Local-first? | Classificação |
|---|---|---|---|---|
| **Firecrawl** (`firecrawl/firecrawl`) | 182.016★, AGPL-3.0 (núcleo), push 2026-09-19 | Scraping→Markdown/HTML/JSON, JS rendering, sitemap discovery. Self-host real, mas exige Postgres+Redis+RabbitMQ (+FoundationDB opcional) | Sim, stack pesada | **DEFER** — infraestrutura desproporcional ao pipeline actual |
| **Crawl4AI** (`unclecode/crawl4ai`) | 83.834★, Apache-2.0, push 2026-09-18 | Crawler→Markdown limpo, Playwright para JS, extracção estruturada, "zero keys, CLI and Docker" | Sim, `pip install` trivial | **ADOPT** |
| **Trafilatura** (`adbar/trafilatura`) | 6.836★, Apache-2.0, push 2026-09-11 (o mais maduro, desde 2019) | Extracção de texto/metadata de HTML já obtido — sem crawling nem JS rendering, mais leve | Sim | **ADOPT** (complementar, para páginas estáticas) |

## 2. Ingestão YouTube

| Ferramenta | Estrelas/Licença/Actividade | O que faz de facto | Local-first? | Classificação |
|---|---|---|---|---|
| **yt-dlp** | 191.984★, Unlicense, push 2026-09-16 | **Já em uso** (confirmado em `MCP-MAPPING.md`) — download + metadata completa | Sim | **ADOPT** (já adoptado — falta só ligar ao pipeline de Markdown) |
| **faster-whisper** | 25.459★, MIT, push **2025-11-19** (~10 meses parado) | **Já em uso**. Continua "pragmatic choice" por cobertura de 99+ idiomas, mas Voxtral Transcribe 2 (Mistral, Apache-2.0) já supera em WER e tem streaming nativo; Parakeet (NVIDIA) lidera em throughput | Sim | **ADOPT** (manter) + **DEFER** avaliar Voxtral/Parakeet como upgrade futuro |
| **youtube-transcript-api** | 8.344★, MIT, push 2026-09-10 | Só busca legendas já existentes — **sem fallback ASR**, sem metadata de canal/playlist. MarkItDown usa esta mesma biblioteca internamente para YouTube (herda a limitação) | Sim | **ADAPT** — atalho barato antes de acionar `yt-dlp`+Whisper, só quando há legendas |

## 3. Ingestão GitHub

| Ferramenta | Estrelas/Licença/Actividade | O que faz de facto | Local-first? | Classificação |
|---|---|---|---|---|
| **gitingest** (`coderamp-labs/gitingest`) | 15.541★, MIT, push 2026-09-19 | Repo→digest de texto único, filtra `.gitignore`/binários, contagem de tokens. **Só código — não issues/PRs** | Sim | **ADOPT** |
| **LlamaIndex/LangChain GitHub readers** | 52.219★/146.614★ | Readers separados código vs. issues/PRs (LlamaIndex inclui PRs no reader de issues) | Sim, mas arrasta o framework inteiro | **EXTRACT** — copiar o padrão de readers separados, não a dependência |

**Gap real:** nenhuma ferramenta leve cobre código+issues/PRs junta. Mínimo: `gitingest` (código) + script pequeno contra a API REST do GitHub (issues/PRs).

## 4. Documentos (PDF/DOCX/HTML/CSV)

| Ferramenta | Estrelas/Licença/Actividade | O que faz de facto | Local-first? | Classificação |
|---|---|---|---|---|
| **MarkItDown** (Microsoft) | 185.423★, MIT, push 2026-09-16 | PDF/PPTX/DOCX/XLSX/imagens/áudio/HTML/CSV/JSON/XML/ZIP/EPub/**YouTube** → Markdown directo, dependências modulares | Sim, footprint leve | **ADOPT** (primeira escolha) |
| **Docling** (IBM) | 66.686★, MIT, push 2026-09-18 | Melhor extracção estrutural de PDF (tabelas, layout, fórmulas) via VLM próprio; cobre áudio/vídeo também | Sim, mas GPU recomendada | **ADOPT** (condicional — só se extracção de tabelas em PDF for requisito real) |
| **Unstructured** | 15.450★, Apache-2.0, push 2026-09-15 | 60+ formatos, mas exige `poppler`/`tesseract`/`libreoffice` (dependências de sistema pesadas) | Sim, footprint pesado | **DEFER** — só se aparecer formato legado que MarkItDown/Docling não cubram |

## 5. Multimodal (OCR, áudio, vídeo)

| Ferramenta/Prática | Estado | Classificação |
|---|---|---|
| Tesseract (OCR clássico) | 76.565★, Apache-2.0, ainda bom para texto impresso limpo, mas VLMs modernos superam-no em manuscritos/má qualidade | **DEFER/REJECT** — sem necessidade documentada neste repo ainda |
| OCR via VLM (LLM multimodal já usado no pipeline) | Prática recomendada 2026: híbrida — OCR clássico em volume, VLM como fallback em baixa confiança; reaproveitar as APIs OpenAI/Gemini já chamadas para embeddings | **REFERENCE** — anotar para quando a necessidade surgir |
| faster-whisper (áudio/vídeo) | Já coberto acima | **ADOPT** (já adoptado) |

## 6. Recomendação mínima

Sem gold-plating, dado que o pipeline só sabe consumir Markdown:

1. **Web** → Crawl4AI + Trafilatura (páginas estáticas).
2. **YouTube** → nenhuma ferramenta nova — ligar `yt-dlp`+`faster-whisper` (já existentes) ao writer Markdown/Supabase. É trabalho de fiação (glue code), não adopção.
3. **GitHub** → gitingest (código) + script pequeno contra a API REST (issues/PRs).
4. **Documentos** → MarkItDown por omissão; Docling só se/quando tabelas em PDF forem requisito real.

Este conjunto mantém a filosofia do pipeline actual: saída sempre em Markdown, dependências leves, sem serviços pagos obrigatórios.

## 7. O que NÃO adotar

- Firecrawl como omissão — AGPL-3.0 + stack de 4 serviços desproporcional; fica como opção só se algum dia for preciso lidar com sites anti-bot difíceis.
- LlamaIndex/LangChain como dependência wholesale só para 2-3 readers — contradiz o pipeline próprio já deliberadamente simples.
- Unstructured por omissão — dependências de sistema pesadas para formatos que MarkItDown já resolve mais leve.
- Stack OCR dedicada agora — sem necessidade documentada; a prática de 2026 já está a migrar para híbrido OCR+VLM de qualquer forma.

## 8. Cruzamento com achados anteriores

O padrão "peça já existe, nunca foi ligada" repete-se pela terceira vez nesta auditoria: `Orchestrator.ts` MOCK apesar de Router/Planner/Executor REAL (Fase 1); superfície MCP mais estreita que o runtime (Fase 2); e agora `yt-dlp`+`faster-whisper` já em produção para transcrição, mas isolados do RAG. Isto não é acaso — é um sinal recorrente de que o maior retorno imediato deste repo está em **fiação entre peças já construídas**, não em adoptar mais ferramentas novas.
