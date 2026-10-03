# Maestro — revisão do PROCESSO DE EXECUÇÃO

O documento está **forte e accionável**. Cobre o essencial do que discutimos. Abaixo: o que está completo, o que falta (pequeno), e o veredicto para o Claude Code.

---

## Completo (não reabrir)

| Bloco | Estado |
|--------|--------|
| Universal Core → Domain Packs + teste definitivo | OK |
| 4 categorias de repos + rejeição de runtimes | OK |
| 3 ajustes (ingest genérico, discover/fetch, provenance) | OK |
| Matrizes P0 / P1 + scorecards | OK |
| F0–F6 com critérios de done | OK |
| Security 100% (#57–#61) | OK |
| Pendentes operacionais + Fase 2 Broker/Lease | OK |
| Anti-padrões + instruções Claude Code | OK |
| Domain Onboarding Cost | OK |

---

## O que ainda falta (não bloqueia gravação — acrescentar numa secção 14)

### 1. Matriz P2 (resumo)
Uma tabela curta: **nenhum vertical ready**; partial só imobiliário/saúde/ficha cliente; regra “um vertical com uso real”. Sem isto, P2 some do processo.

### 2. Objectivo nº 1 — tokens
Está no §1.1; falta **métrica operacional** no processo, por exemplo:
- ledger obrigatório em plans externos;
- tectos por área (já em `areas.yaml`: 80k/40k/30k/20k);
- B1-bis-C = optimização **depois** de F0–F3, não paralelo a MarkItDown.

### 3. Restrições de infra (1 parágrafo)
Oracle ~12GB, zero custo recorrente, local-first, Supabase free, MCP da casa, licenças MIT/Apache. Evita o Claude Code propor Neo4j/GraphRAG MS “porque a pesquisa citou”.

### 4. Ligações explícitas a ficheiros existentes
Lista canónica para o executor não inventar caminhos:

- `docs/architecture/adr/ADR-META-AGENTS.md`
- `docs/architecture/memory/contracts.md` / `docs/ops/MEMORY-L4.md`
- `config/areas.yaml`, `config/security-capabilities.yaml`, `config/councils.yaml`
- `docs/audit/PLANO-DE-ACAO.md`, `docs/initiatives/OPEN-ITEMS.md`, `STATUS.md`
- `docs/architecture/SECURITY-AGENTS.md`

### 5. SEC-1 detalhe útil
`repo_files`: opt-in, denylist, 50 KB, só leitura — para ninguém “generalizar knowledge_refs” (opção B que rejeitámos).

### 6. Ordem F0 em checklist executável
Sub-passos concretos (para não ficar vago):

1. Query SQL/`knowledge_chunks` por `source` contendo `security` / `SECURITY` / `security-agents-stack`  
2. Se vazio → correr workflow ingest do pack  
3. 10–20 Qs golden + `hit@k`  
4. Só então F1  

### 7. J11 / mem0
Já em Categoria 2; uma linha: **spike J11 = EXTRAIR padrões, não substituir L4** (D3).

### 8. Dependabot
Já implícito no SEC-2c; uma linha: **manter** `github-actions` no dependabot — não reabrir pin SHA.

### 9. Dual-repo
Onde cabe: `network-agents-setup` vs `agent-network-mcp` (C-2 ledger no MCP). Evita o agente mexer no sítio errado.

---

## O que **não** precisa entrar (correcto ter omitido)

- Lista de 50 agentes novos  
- Implementação do Execution Broker agora  
- LightRAG/Graphiti como serviço  
- Cinco domínios F6 em paralelo  
- Transcript completo da conversa  

---

## Veredicto

| Pergunta | Resposta |
|----------|----------|
| Está completo o bastante para ser o baseline? | **Sim** |
| Falta algo crítico? | **Não** — só o bloco §14 acima (P2 + infra + paths + F0 checklist) |
| Pode ir para o Claude Code? | **Sim**, com o adendo |

---

## Instrução única para o Claude Code

```text
Grava as 3 partes + o adendo abaixo em docs/architecture/EXECUTION-PLAN.md.
Regista em docs/initiatives/OPEN-ITEMS.md os itens F0–F6 (§9.4) com dono/fase.
NÃO implements F1–F6 ainda.
Começa APENAS pelo F0: prova L5 (security pack no pgvector) + golden set 10–20 + hit@k.
Se F0 falhar (pack não ingerido), resolve ingest antes de qualquer MarkItDown.
Não reabrir SEC/D1–D3. Não segundo runtime. Não novos agentes de domínio.
Commit + push no branch; PR se política do repo exigir. Sem --force.

ADENDO OBRIGATÓRIO (§14):
- Matriz P2: zero vertical ready; partial imobiliário/saúde; um vertical só com uso real.
- Restrições: Oracle ~12GB RAM, zero SaaS pago, local-first, MIT/Apache, MCP da casa.
- Objectivo #1 tokens: ledger + tectos areas.yaml; B1-bis-C só após F0–F3.
- Paths canónicos: ADR-META-AGENTS, memory contracts, areas.yaml, security-capabilities,
  OPEN-ITEMS, STATUS, SECURITY-AGENTS, PLANO-DE-ACAO.
- repo_files: opt-in, denylist, 50KB, read-only (não generalizar knowledge_refs).
- C-2 ledger = agent-network-mcp; resto do plano = network-agents-setup.
- mem0/J11 = padrões só; L4 própria permanece.
```

---

**Resumo:** o plano de execução **não deixa passar** o núcleo do que falámos. Acrescenta o **§14** (P2, infra, paths, F0 checklist, dual-repo) e manda gravar + **só F0**. Depois F0 verde, o mesmo documento já manda F1 sem reabrir arquitectura.
