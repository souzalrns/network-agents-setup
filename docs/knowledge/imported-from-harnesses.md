# Importado de Ruflo, Hermes, Orca e disciplina de harness (DeepSeek / agent evals)

Conhecimento **portátil** — não instalamos esses runtimes no agent-network-mcp.
Extraímos regras, prompts-padrão e padrões de skill que melhoram orquestração, evidência e aprendizagem.

Fontes de referência (públicas, 2026):
- **Ruflo** (ruvnet/ruflo, ex-Claude Flow): meta-harness multi-agente, swarms, memória, MCP
- **Hermes** (NousResearch/hermes-agent): learning loop, SKILL.md, memória de sessão, agentskills.io
- **Orca** (várias linhas: stablyai/orca ADE, harness local com worktrees/PTY, pipelines QC): isolamento, verificação, paralelismo
- **DeepSeek + harness evals**: custo de orquestração, verificação, resistência a injection, não confiar em self-report de bench

Já alinhado com o que a rede LRNSdigital já usa (ECC + Superpowers): plano → teste → evidência; menor número de agentes útil.

---

## 1. Regras de orquestração (Ruflo + Orca + Superpowers)

### R1 — Objetivo limitado antes de spawn
Todo trabalho multi-agente começa com **definition of done** verificável (plano, feature testada, PR revisado, checklist de release). Sem isso, não spawnar especialistas.

### R2 — Menor número de agentes que resolve
Ruflo oferece 60–100+ tipos; a regra útil é a inversa: só adicionar agente quando há **papel distinto e handoff claro**. Um plano maior que o problema é desperdício (já na Constituição PCU / planejador).

### R3 — Papéis separados, evidência partilhada
Padrão estável:
- **Planner** — decompõe; não implementa
- **Builder / coder** — implementa segundo o plano
- **Reviewer / QC** — julga com critérios; não reescreve tudo de novo sem motivo
- **Orchestrator** — liga; não substitui o especialista

Orca (pipeline Brain → execução → QC) e Ruflo (planner / coder / reviewer / tester) convergem nisto.

### R4 — Isolamento de execução
Quando houver parallel agents ou experiências arriscadas:
- worktree / branch isolada por tentativa (Orca ADE)
- não misturar estado de duas execuções no mesmo working tree sem merge explícito
- “done” = processo terminou **e** critério de verificação passou — não só o modelo disse que acabou

### R5 — Fast-path vs full cycle
(Já no agente `planejador`.)  
FAST-PATH: pedido simples, 1–2 tools, sem ambiguidade.  
FULL CYCLE: plano → arquitetar → construir → revisar.  
Justificar a escolha em uma frase.

---

## 2. Regras de evidência e verificação (Orca + Superpowers + evals)

### R6 — Evidência fresca antes de “pronto”
Nunca afirmar sucesso sem output de verificação **nesta** resposta (teste, curl, log, screenshot). “Devia funcionar” não é prova.

### R7 — Verifier explícito quando possível
Padrão Orca-like: `exec` + comando de verificação (`test`, `lint`, health check). O harness só fecha a tarefa se o verifier passar.

### R8 — Distinguir estados de execução
Não colapsar:
- **live** — ainda a correr
- **exited** — terminou (sucesso ou falha conhecida)
- **unverifiable** — não conseguimos inspecionar (rede, PTY, permissão)

Tratar `unverifiable` como estado próprio, não como sucesso.

### R9 — QC com veredito estruturado
PASS / WARN / FAIL + o que falhou + ação de repair. Reviewer não inventa problemas para parecer rigoroso; zero findings é válido (já no `revisor-codigo`).

### R10 — Não confiar só em bench self-reported
Evals públicos (CAISI, METR, papers de harness): self-report do vendor ≠ desempenho em tarefas agentic / held-out. Para escolha de modelo ou harness, preferir evidência externa e custo real por tarefa.

---

## 3. Memória e aprendizagem (Hermes + Ruflo)

### R11 — Loop de aprendizagem fechado
Hermes: após tarefa complexa, **persistir** o que funcionou (skill / nota), não só o chat.  
Ruflo: memória de padrões bem-sucedidos entre sessões.

Na nossa rede: `radar-ferramentas` + `tool_evaluations` já é o equivalente para **ferramentas**. Estender o mesmo espírito a:
- padrões de campanha que funcionaram
- checklists de SEO/GEO por projeto
- anti-padrões descobertos em produção

### R12 — Formato SKILL.md (agentskills.io / Hermes)
Skill portátil mínima:

```markdown
---
name: nome-curto
description: quando invocar (1–3 frases, triggers claros)
---

# Título

## When to use
## Steps / checklist
## Examples
## Anti-patterns
```

Skills devem ser **curadas** (humano ou agente com review), não dumps automáticos de conversa inteira.

### R13 — Consultar memória antes de re-investigar
Antes de avaliar ferramenta, framework ou abordagem “nova”: consultar banco existente (`radar-ferramentas` / docs). Evitar re-diagnóstico do zero (lição já registada com Orca/node-pty, etc.).

---

## 4. Segurança e fronteiras (Orca SSH + DeepSeek harness papers)

### R14 — Execution host owns execution
Quem corre o processo (local vs remote) é a autoridade do estado de execução. UI/cliente não declara “pronto” sem consultar o host.

### R15 — Conteúdo não confiável ≠ ação sensível
Papers de injection em harness: texto/ficheiros de terceiros podem tentar desviar o agente.  
Regra prática: entre conteúdo não confiável e ações sensíveis (credenciais, deploy, pagamentos, delete) exigir confirmação ou policy explícita.

### R16 — Nenhuma API paga sem autorização
(Já na rede.) Harness novo não implica gastar quota/pago sem OK prévio.

---

## 5. Topologias úteis (Ruflo) — só o essencial

| Topologia | Quando usar |
|-----------|-------------|
| **Hierárquica** (orquestrador → especialistas) | Default para marketing e produtos |
| **Paralelo isolado** (N worktrees / N variantes) | Comparar abordagens; escolher vencedor com critério |
| **Pipeline QC** (plan → build → review) | Código e entregas com risco de regressão |

Evitar mesh completo / 15 agentes por defeito no dia a dia — custo e ruído sobem mais depressa que a qualidade.

---

## 6. Padrões de prompt importáveis

### Orquestrador (compacto)
```text
1) Objetivo e critério de pronto (evidência)
2) Fast-path ou full cycle (1 frase de porquê)
3) Agentes mínimos e handoffs
4) O que NÃO fazer nesta passagem
5) Não executar o trabalho do especialista se o especialista existir
```

### Executor
```text
Segue o plano recebido. Não redesenhes arquitetura.
Implementa → verifica com comando/evidência → reporta o que passou e o que falta.
Se o plano for ambíguo, para e pergunta — não inventes requisitos.
```

### Reviewer / QC
```text
Veredito: PASS | WARN | FAIL
Só reporta issues com >80% confiança e cenário de falha concreto.
Zero findings é válido. Não inventes problemas.
```

---

## 7. O que NÃO importar (de propósito)

| Item | Motivo |
|------|--------|
| 300+ MCP tools do Ruflo | Complexidade; a nossa rede é MCP próprio focado |
| Dependência de node-pty / desktop Orca | Já avaliado; bloqueios de ambiente |
| Swarm de 15 agentes por tarefa de marketing | Viola menor número de agentes |
| Auto-criação de skills sem review | Polui memória; Hermes inspira o loop, não o dump cego |
| Claims de bench DeepSeek self-reported como verdade absoluta | Evals independentes divergem |

---

## 8. Mapa: onde isto entra na nossa estrutura

| Import | Destino |
|--------|----------|
| R1–R5, prompts orquestrador | `marketing-orquestrador`, `planejador`, `arquitetura-agentes` |
| R6–R9 | `desenvolvimento`, `revisor-codigo`, `guia-tdd`, qualquer vertical de entrega |
| R11–R13 | `radar-ferramentas`, futuros knowledge packs, formato de skills |
| R14–R16 | política de rede / security-by-design |
| SKILL.md pattern | designer-skills, ECC skills, novos packs |

---

## 9. Status na tool memory (sugestão para radar-ferramentas)

| Nome | Status sugerido | Nota |
|------|-----------------|------|
| Ruflo / Claude Flow | `avaliado_nao_adotado` (runtime completo) | Importamos **regras**, não o produto |
| Hermes Agent | `avaliado_parcial` | Padrão SKILL.md + learning loop |
| Orca (ADE / harness) | `avaliado_nao_adotado` ou `pendente` conforme ambiente | Worktree + verify; PTY pode bloquear |
| DeepSeek como modelo único | decisão de custo/qualidade separada | Harness lessons > vendor bench |

---

*Documento de importação seletiva. Setup paralelo / knowledge — não altera por si o agent-network-mcp de produção.*
