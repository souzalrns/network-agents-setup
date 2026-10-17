# `.claude/skills/` (gerado)

> **Não editar à mão.** Gerado por `python scripts/sync_claude_skills.py` a partir de `skills/meta/` e `skills/claude/`. Editar a skill na fonte e voltar a correr o script; o teste `runner/tests/test_claude_skills_sync.py` falha se esta pasta divergir da fonte.

Num nome repetido ganha a 1.ª fonte (`skills/meta/`). As skills de domínio (marketing, design, security) ficam de fora: são papéis dos agentes do runner.

As skills de terceiros instaladas pelo `skill-scout` (fixadas em `skill-scout.lock.json`) não vêm da fonte e o script não lhes toca; verificam-se com `skill-scout verify`.
