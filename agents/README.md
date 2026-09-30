# Agents

Definições de agent (identidade + skill + action).

| Vertical | Path |
|----------|------|
| **Marketing** P0/P1 | [marketing/](./marketing/) |
| **Design** P0 (UX + UI + writer + critic) | [design/](./design/) |
| **Shared** | [_shared/](./_shared/) — grounding obrigatório |
| Meta | [meta/](./meta/) se existir |

## Campo `kind`

Todo `*.agent.md` declara `kind:` no frontmatter, a seguir ao `id:`:

| Valor | Uso |
|-------|-----|
| `internal` | Agente deste repo (omissão; todos os actuais) |
| `external_ai` | Maestro que representa uma IA externa (Claude, Grok…) — reservado para a Fase 2 |
| `meta` | Meta-agente de deliberação — reservado para a Fase 2 |

O `kind` é do agente, não da área (`config/areas.yaml`). Não confundir com `layer: 'meta'` de `config/agents.config.ts`. Ver [ADR-META-AGENTS](../docs/architecture/adr/ADR-META-AGENTS.md).

## Campo `description`

Todo `*.agent.md` declara `description:` no frontmatter, a seguir ao `action:` (J4). É o texto que um router semântico (LLM ou embeddings, Bloco C) lê para escolher o agente:

- 1–2 frases em português, a começar por um verbo ("Revê…", "Escreve…");
- específica: o que o agente faz **e**, quando ajuda a desempatar, o que não faz (ex.: `ux_writer` não faz copy de marketing);
- entre aspas duplas (as descrições têm `:`, `—`, `→`).

## Grounding

Todo agent novo deve respeitar [_shared/grounding.directive.md](./_shared/grounding.directive.md).

Integração com runner: mode `external` inclui `agent_path` e `skill_path` no `pending_steps/<id>/request.json`.
