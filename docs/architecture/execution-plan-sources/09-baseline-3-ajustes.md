Sim. Eu trataria este documento como o **baseline arquitetural consolidado** a partir de agora.

Há apenas **três pequenos ajustes de precisão** que eu faria antes de transformá-lo em ADR, porque evitam decisões erradas mais à frente:

### 1. `ingest_document()` não deve ficar preso a `path`

O contrato universal deveria aceitar uma fonte abstrata, porque amanhã a entrada pode ser ficheiro local, URL, objeto vindo de Drive, GitHub, upload, etc.

```text
ingest_document(source, options)
→ {
    content,
    source_meta,
    artifacts?,
    warnings?
}
```

`source` pode ser:

```text
path | url | bytes | connector_ref
```

O **MarkItDown é apenas um adapter**, não o contrato.

---

### 2. `web_research()` deve separar descoberta de aquisição

Eu colocaria explicitamente:

```text
discover(query)
    ↓
candidate URLs
    ↓
fetch/crawl(url, limits)
    ↓
normalize
    ↓
provenance
    ↓
research artifact
```

Isso será importante quando o Maestro tiver vários fornecedores de pesquisa.

Assim, Crawl4AI não vira “o agente de pesquisa”; ele é uma implementação de uma capacidade de aquisição.

---

### 3. Provenance deve existir em todos os artefactos, não apenas chunks

O modelo mais robusto seria:

```text
SOURCE
  ↓
DOCUMENT
  ↓
CONTENT
  ↓
CHUNK
  ↓
EMBEDDING
  ↓
RETRIEVAL
  ↓
ARTIFACT
```

Cada camada deve conseguir apontar para a anterior.

Isso permite posteriormente responder:

> “De onde veio esta afirmação?”

sem depender de memória do agente.

---

# Eu fecharia a arquitetura assim

```text
                    ┌──────────────────────────┐
                    │       PLAN RUNNER        │
                    │   único execution core   │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │      CAPABILITY LAYER    │
                    │ capabilities + policies  │
                    └────────────┬─────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ▼                      ▼                      ▼
   INGESTION PRIMITIVES    RESEARCH PRIMITIVES    OTHER TOOLS
   MarkItDown              Crawl4AI               OSV
   Docling                 web_fetch              Gitleaks
   OCR/etc.                                         Semgrep
          │                      │
          └──────────────┬───────┘
                         ▼
              ┌─────────────────────┐
              │   KNOWLEDGE CORE    │
              │                     │
              │ L4 Memory           │
              │ L5 Knowledge        │
              │ pgvector            │
              │ provenance          │
              │ temporal metadata   │
              └──────────┬──────────┘
                         │
             ┌───────────▼───────────┐
             │     DOMAIN PACKS      │
             │                       │
             │ security              │
             │ marketing             │
             │ legal                 │
             │ medicine              │
             │ trading               │
             │ manufacturing         │
             │ gamedev               │
             └───────────────────────┘
```

E o ponto mais importante:

**o Domain Pack não possui infraestrutura cognitiva própria.**

Ele consome a infraestrutura universal.

---

## A Fase 0 deve realmente vir antes do MarkItDown

Eu manteria a ordem:

### F0 — provar o que já existe

Antes de adicionar qualquer coisa:

```text
L5 security
   ↓
ingest realmente executado?
   ↓
embeddings realmente existem?
   ↓
query realmente recupera?
   ↓
chunk correto aparece?
   ↓
artefacto consegue citar origem?
```

Porque existe um risco arquitetural importante:

> construir uma excelente pipeline de ingestão para descobrir depois que o problema real estava no retrieval existente.

A prova deve ser pequena e objetiva.

Algo como:

```text
Golden set security = 10–20 perguntas

para cada pergunta:
    expected chunks
    retrieved chunks
    hit@k
    relevance
    provenance presente?
```

Não precisamos de um sistema sofisticado de avaliação ainda.

---

# F1 — MarkItDown

Depois disso, o spike deve ser **deliberadamente pequeno**.

```text
PDF
DOCX
PPTX
XLSX
   ↓
MarkItDown
   ↓
Markdown
   ↓
metadata/provenance
   ↓
ingest existente
   ↓
pgvector
```

E testar pelo menos:

* PDF textual;
* DOCX;
* XLSX ou outro formato estruturado.

**Não mexer no worker de steps.**

Se o spike funcionar, o MarkItDown passa a ser uma implementação de primitive.

---

# F1b — Docling

Só existe se houver uma pergunta concreta:

> “O MarkItDown perdeu estrutura que precisamos preservar?”

Por exemplo:

```text
tabelas
layout
colunas
figuras
PDF complexo
documentos técnicos
```

Se não houver perda relevante:

**não entra.**

Isso é exatamente o princípio “não construir/adotar o que já existe”.

---

# F2 — Research

Aqui há uma distinção que vale ouro para o futuro:

```text
RESEARCH ≠ WEB SCRAPING
```

Research é uma capability.

Crawl4AI é uma ferramenta que pode implementar parte dela.

O resultado deve ser algo parecido com:

```json
{
  "content": "...",
  "sources": [
    {
      "uri": "...",
      "title": "...",
      "retrieved_at": "...",
      "content_hash": "..."
    }
  ],
  "limitations": [],
  "artifacts": []
}
```

Assim, amanhã pode existir:

```text
Crawl4AI
GitHub
Crossref
legislation source
medical source
financial source
connector
```

sem mudar o contrato da capability.

---

# F3 — Provenance

Eu acrescentaria uma regra ao ADR:

> **Nenhum conhecimento externo entra no L5 sem provenance mínima.**

Mínimo:

```text
uri
title
publisher
document_type
retrieved_at
content_hash
```

Quando aplicável:

```text
author
jurisdiction
published_at
effective_from
effective_until
version
authority
```

Isso é especialmente importante para:

* Direito;
* Medicina;
* legislação;
* segurança;
* finanças;
* normas técnicas.

E evita criar agora uma “solução temporal” gigante só porque alguns domínios precisarão dela.

---

# F4 — Capability Registry

Aqui a decisão Security → Marketing é excelente.

Security já responde:

> “Como uma capability é declarada?”

Marketing responderá:

> “Como uma segunda área reutiliza o mesmo mecanismo?”

Só depois faria sentido perguntar:

> “Como generalizamos o registry?”

Isso evita abstração prematura.

---

# F5 — Validation

Aqui eu faria uma distinção fundamental:

```text
YAML válido
       ≠
capability válida
```

O teste precisa provar:

```text
discover
   ↓
select
   ↓
authorize
   ↓
execute
   ↓
validate
   ↓
audit
```

Essa cadeia é, na prática, uma das melhores provas de que o Maestro está deixando de ser uma coleção de agentes e virando uma **plataforma operacional**.

---

# E a F6 fica exatamente como você corrigiu

Nada de:

```text
Legal
Trading
Medicine
Manufacturing
GameDev
```

todos simultaneamente.

Escolhe-se **um domínio real**.

E aí vem o teste definitivo:

```text
Novo domínio
     ↓
knowledge
skills
capabilities
plans
policies
validation
tools
     ↓
CORE NÃO ALTERADO
```

Se for necessário mexer em:

```text
plan_runner
memory engine
RAG engine
executor
orchestrator
```

para adicionar o domínio, temos uma evidência objetiva de que alguma abstração do Universal Core ainda está incompleta.

---

## Portanto, o backlog imediato fica muito limpo

### AGORA

**F0**

* prova real L5 Security;
* confirmar ingest → embedding → retrieval;
* confirmar provenance atual;
* confirmar estado dos merges SEC.

**F1**

* contrato `Universal Ingestion & Research Primitives`;
* spike MarkItDown;
* 3 formatos;
* zero alteração do execution runtime.

### DEPOIS

**F1b**

* Docling somente se benchmark justificar.

**F2**

* Crawl4AI como implementação de research/fetch;
* limites;
* cache;
* provenance.

**F3**

* provenance formal;
* metadata;
* golden set;
* métricas de retrieval.

**F4**

* `marketing-capabilities.yaml`.

**F5**

* capability E2E real.

**F6**

* **um** domínio real como prova de extensibilidade.

---

### E há uma consequência estratégica importante

Neste ponto, eu **pararia de procurar novos frameworks de agentes**.

A pesquisa de repos muda de natureza.

Em vez de:

> “Que agente podemos adicionar?”

a pergunta passa a ser:

> **“Que primitive madura podemos incorporar ao Universal Core sem criar uma segunda arquitetura?”**

Isso muda completamente o projeto.

E mantém a regra central:

**Construir uma vez. Evoluir para sempre.**
