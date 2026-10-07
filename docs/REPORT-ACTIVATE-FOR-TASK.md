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
from plan_runner.skill_activation import activate_for_task  # (corrigido: era plan_runner.skills)
act = activate_for_task(repo_root, step)
# act.prompt_block() / act.to_request_fields()
# act.allowed_scripts / blocked_scripts / external_candidates
```

### should_search_external

Por passo: `should_search_external: true` ou `search_external: true`.  
Global: `config/skills.yaml` → `search_external_default: true` (só se skill local ausente).  
Providers pedidos: `npx skills find --json`, depois `https://skills.cat/api/search`. Não instala automaticamente.
**Implementado:** só a API skills.sh por HTTPS directo (ver "Verificação", linhas 6 e 7).

### SEC-1.3

```yaml
allow_scripts:
  marketing/review:
    - scripts/check.sh
```

Default = deny scripts (`.sh`, shebang, `.py`, `.js`, …).

## Estado no git

- Branch `feat/activate-for-task-sec13`.
- ~~Pendente push: `skills.py` (implementação completa), `test_skills.py`~~: **nunca chegaram ao branch**; existiam só na máquina do outro agente. Ver "Verificação" abaixo.

## Testes a correr

```bash
cd runner && python -m pytest tests/test_skill_activation.py tests/test_executor.py tests/test_skills.py -q
```

## Compatibilidade

Aditivo: planos sem flags novas mantêm o comportamento anterior. O prompt só muda quando a skill tem scripts ou o passo pede pesquisa externa.

## Verificação (Claude, 2026-10-07)

**Estado encontrado:** o branch estava partido. O `executor.py` importava `activate_for_task` e `materialize_activation` de `plan_runner.skills`, que não os tem. Isso dava `ImportError` e **18 erros de colecção**: a suite não corria (contra 754 testes a passar no `main`). Não havia PR nem CI no branch. O `test_skills.py` anunciado teria sobrescrito o `runner/tests/test_skills.py` que já existe no `main` (resolução de paths, S34).

**Correcções e reforço, no mesmo branch:**

| # | O quê | Porquê |
|---|---|---|
| 1 | Implementação nova em `runner/plan_runner/skill_activation.py` (módulo próprio, para não inflar `skills.py` nem criar import circular); `executor.py` importa daí | o código original não estava acessível; reconstruído a partir do contrato deste relatório |
| 2 | Testes em `runner/tests/test_skill_activation.py` (39), sem tocar no `test_skills.py` existente | evitar sobrescrever testes do `main`; rede proibida por fixture |
| 3 | Mantidos `skill_preview_head` / `agent_preview_head` no `request.json` e o `vertical:` do passo (S34) | o wire removia-os; agora `to_request_fields()` repõe-nos (há teste) |
| 4 | SEC-1.3 fail-closed: config inválida = deny + aviso; symlinks nunca autorizados; entradas absolutas/`..` ignoradas; entradas obsoletas avisadas | deny-by-default tem de sobreviver a config errada |
| 5 | sha256 de SKILL.md/AGENT.md + `pins:` opcional (pin que não confere bloqueia todos os scripts) | OWASP Agentic Skills Top 10: update drift |
| 6 | Pesquisa externa: HTTPS directo à API skills.sh, em vez de `npx skills find --json` | `find` não tem `--json` no `skills@1.7.1`, e `npx` executa código descarregado em runtime. É a mesma fonte de dados; detalhe em `docs/ops/SKILL-ACTIVATION.md` |
| 7 | SkillsCat estacionado como **SKILL-EXT-1** | contrato da API não verificável; serviço AGPL |
| 8 | `SKILL_ACTIVATION.md` entra no prompt (`external_worker.build_prompt_ctx`), nos dois modos, só quando existe | "o resultado entra no prompt" (objectivo 2), sem mudar prompts existentes |
| 9 | `is_script_allowed()` exposto como ponto de controlo | o worker não executa scripts; quem os vier a executar (AU-20/P-37) tem de passar por aqui |

**API final:**

```python
from plan_runner.skill_activation import activate_for_task, materialize_activation, is_script_allowed
act = activate_for_task(repo_root, step)          # nunca levanta por config/rede
act.prompt_block(); act.to_request_fields(); act.to_json()
act.allowed_scripts / act.blocked_scripts / act.external_candidates
```

**O que isto NÃO é:** não fecha o AU-20. O worker continua sem tools (single-shot Gemini, "Nao tens tools neste passo"). O contrato do executor de tools está em `docs/architecture/AU-20-TOOL-EXECUTOR.md` (proposta, à espera do P-37).

Contrato completo: [`docs/ops/SKILL-ACTIVATION.md`](ops/SKILL-ACTIVATION.md).
