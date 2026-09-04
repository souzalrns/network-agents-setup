# uv — package manager (notas)

Já usaste: instalar `uv` e `uv tool install specify-cli`.

## O que é

Gestor Python rápido (Rust) que unifica boa parte de: pip, pipx, virtualenv, poetry/rye (projectos), e instalação de versões de Python.

## Áreas principais

### 1. Tools (CLI isoladas) — o que usaste

| Comando | Efeito |
|---------|--------|
| `uvx <pkg>` | Corre tool em ambiente **temporário** (tipo npx) |
| `uv tool install <pkg>` | Instala tool no user PATH, venv isolado persistente |
| `uv tool list` | Lista tools instaladas |
| `uv tool upgrade <pkg>` / `--all` | Actualiza |
| `uv tool uninstall <pkg>` | Remove |

Exemplos:

```powershell
uv tool list
uvx ruff check .
uv tool install ruff
uv tool upgrade specify-cli
```

### 2. Projectos

```powershell
uv init meu-app
uv add requests
uv add --dev pytest
uv sync
uv lock
uv run pytest
uv tree
```

Lockfile universal; `.venv` local ao projecto.

### 3. Python versions

```powershell
uv python list
uv python install 3.12
uv python pin 3.12
```

### 4. Scripts

Scripts com dependências inline; `uv run script.py` resolve sem poluir o global.

### 5. pip interface (legado)

`uv pip install`, `uv venv` — compatível quando precisas de controlo fino.

### 6. Workspaces

Vários pacotes num monorepo, um lock partilhado (`tool.uv.workspace` no pyproject).

### 7. Manutenção

```powershell
uv self update
```

## Para este repo

- Spec Kit via `uv tool install specify-cli`
- Preferir `uvx` para one-shots (ruff, etc.) sem instalar tudo
- Não confundir `uv` (Python tooling) com o fluxo Spec Kit dos `/speckit-*` no agente
