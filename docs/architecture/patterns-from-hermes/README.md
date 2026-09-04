# Padrões portáveis — Hermes Agent (Nous Research)

**Fonte:** Hermes Agent (MIT) — learning loop, memória em camadas, skills SKILL.md, multi-provider.

**Regra (igual ao dsh):** roubar *padrões*; não adoptar o monólito Hermes, gateway multi-canal, nem auto-evolução sem gates no setup/prod.

Já constava no addendum de orquestradores: resolvedor multi-modelo, memória em camadas, skill pós-execução **com cautela**.

---

## Inventário

| ID | Padrão | Fase | Adoptar? |
|----|--------|------|----------|
| H01 | Memória em camadas (não misturar tudo no prompt) | 1 | **Sim** |
| H02 | Skills como memória procedural (SKILL.md) | 1 | **Já** (`skills/claude/`) |
| H03 | Progressive disclosure de skills | 1–2 | **Sim** |
| H04 | Multi-model / provider routing | 2 | **Sim** (conceito) |
| H05 | Skill *candidate* pós-tarefa complexa | 2 | **Sim, com human gate** |
| H06 | Patch de skill > rewrite total | 2 | **Sim** |
| H07 | Curator / arquivo de skills stale | 3 | Opcional |
| H08 | Session search (FTS) + sumário LLM | 3 | Opcional lab |
| H09 | USER / SOUL / MEMORY separados | 1 | **Sim** (mapear) |
| H10 | Nudges para persistir factos estáveis | 2 | Opcional |
| H11 | Skill bundles (grupo sob um comando) | 2 | Útil |
| H12 | Subagents / parallel workstreams | 2 | Alinhado Plan-Execute |
| H13 | Terminal backends / sandbox options | 3 | Só se runtime lab |
| H14 | Gateway Telegram/Discord… | — | **Não** no core setup |
| H15 | Auto-improve skill sem humano | — | **Não** em prod |

---

## H01 + H09 — Memória em camadas

Hermes separa tipos de memória para não poluir o context window.

| Camada Hermes | O quê | Mapa no nosso setup |
|---------------|--------|---------------------|
| **SOUL / identity** | Voz e regras imutáveis (ou quase) | `CONSTITUTION-DRAFT` + Spec Kit constitution |
| **USER.md** | Preferências estáveis do operador (curto) | Perfil operador / constraints de projecto (não secrets) |
| **MEMORY.md** | Factos de ambiente, lições compactas (curto, editável) | Notas de setup em `docs/` + knowledge_refs; **não** dumps de chat |
| **Session / FTS** | O que aconteceu (episódico), on-demand | `pilots/`, event log futuro, git history |
| **Skills** | *Como* fazer (procedimental) | `skills/claude/**/SKILL.md` |
| **Honcho / user model** (opcional) | Modelo do utilizador | Fora de scope framework genérico |

**Regra de ouro roubada:**  
Factos estáveis ≠ procedimentos ≠ transcriptos.  
Transcriptos não vão para MEMORY “sempre on”; skills não guardam preferências de pessoa.

---

## H02 + H03 — Skills + progressive disclosure

- Skill = procedimento reutilizável (trigger + passos + verificação).  
- Formato portável tipo agentskills / SKILL.md (já usamos).  
- **Progressive disclosure:** no routing só nome/descrição; carregar corpo completo **só** quando a action/skill é escolhida → controla tokens (como registry de actions).

Ligar: `patterns-from-harness/registry-actions.md` ↔ skills.

---

## H05 + H06 — Learning loop **com cautela**

Hermes: após tarefa complexa (ex. muitos tool calls, recuperação de erro), propõe/escreve SKILL.md; em uso posterior pode **patchar** a skill.

**No nosso setup / prod:**

```text
Tarefa complexa bem-sucedida
  → gerar skill CANDIDATE (artefacto em pilots/ ou skills/_candidates/)
  → NUNCA merge automático para skills/claude/ ou produção
  → human_gate + (opcional) critic
  → só então promover
```

Preferir **patch** a reescrita total (menor risco de partir skill boa).

Isto espelha o addendum: *skill pós-execução = candidate*.

---

## H04 — Multi-model resolver

- Um sítio mapeia `(papel | action | tier) → provider/modelo`.  
- Agentes não hardcodam API.  
- Ex.: planner = modelo forte; executor copy = mais barato; verifier = médio.

Já alinhado a `model_tier` no Plan schema (`planner | executor | verifier`).

---

## H11 — Skill bundles

Grupo de skills sob um intent (ex. “implement feature” → TDD + review + security).

Mapa: profile Spec Kit / profile `code-speckit` no roadmap harness patterns.

---

## Explicitamente **não** roubar para o core

| Item | Motivo |
|------|--------|
| Gateway multi-canal como núcleo | Ruído; não é o problema do framework de agentes empresariais/método |
| Auto-write skills em produção | Contaminação, skills más eternizadas |
| MEMORY.md partilhado multi-writer | Hermes avisa: um home por agente/perfil |
| Substituir MCP por Hermes | Dois mundos; setup continua contratos + lab |

---

## Relação com padrões dsh / event sourcing

| Hermes | dsh / nosso |
|--------|-------------|
| Skills on disk | Registry + SKILL.md |
| Session search | Event log / pilots (P03, event sourcing) |
| Learning loop | Candidate + human_gate |
| Camadas de memória | Prompt em camadas (P08) |
| Multi-model | model_tier + resolver |

---

## Ficheiros deste pacote

| Ficheiro | Conteúdo |
|----------|----------|
| `README.md` | Este inventário |
| `memory-layers.md` | Regras práticas de camadas |
| `skill-lifecycle.md` | Candidate → promote → patch → archive |
