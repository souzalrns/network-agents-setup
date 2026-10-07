# Relatório para Claude — `activate_for_task` + wire externo + SEC-1.3

**Repo:** `souzalrns/network-agents-setup`  
**Módulo:** `runner/plan_runner/`  
**Data:** 2026-10-07  
**Branch:** `feat/activate-for-task-sec13`

## Objectivo

1. O worker chama **`activate_for_task`** antes de executar.
2. O resultado entra no **prompt** / `pending_steps/<id>/`.
3. Quando **`should_search_external`**, pesquisar **SkillsCat** ou **`npx skills find`**.
4. **SEC-1.3:** allow-list de scripts por skill em `config/skills.yaml`.

## Onde entra no plan_runner

| Peça | Ficheiro | Passo |
|------|----------|--------|
| Resolução + activação | `runner/plan_runner/skills.py` | `activate_for_task(repo_root, step)` |
| Chamada antes do worker | `runner/plan_runner/executor.py` → `execute_external_request` | Após criar `pending_steps/<id>/`, **antes** de invocar o worker |
| Materialização | `materialize_activation` | `SKILL.md`, `AGENT.md`, `skill_activation.json` |
| Config SEC-1.3 | `config/skills.yaml` | `allow_scripts` deny-by-default |

## API

```python
from plan_runner.skills import activate_for_task
act = activate_for_task(repo_root, step)
# act.prompt_block() / act.to_request_fields()
# act.allowed_scripts / blocked_scripts / external_candidates
```

### should_search_external

Por passo: `should_search_external: true` ou `search_external: true`.  
Global: `config/skills.yaml` → `search_external_default: true` (só se skill local ausente).  
Providers: `npx skills find --json`, depois `https://skills.cat/api/search`. Não instala automaticamente.

### SEC-1.3

```yaml
allow_scripts:
  marketing/review:
    - scripts/check.sh
```

Default = deny scripts (`.sh`, shebang, `.py`, `.js`, …).

## Estado no git

- Branch `feat/activate-for-task-sec13`
- Já commitados: `config/skills.yaml`, `executor.py` (wire)
- Pendente push se não estiver neste commit: `skills.py` (implementação completa), `test_skills.py`, este relatório

## Testes a correr

```bash
cd runner && python -m pytest tests/test_skills.py -q
```

## Compatibilidade

Aditivo: planos sem flags novas mantêm o comportamento anterior.
