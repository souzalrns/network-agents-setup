# Spec Kit (GitHub) — notas de instalação e fluxo

**Setup only.** Não liga à produção `agent-network-mcp`.

## O que é

Toolkit de **Spec-Driven Development**: constitution → specify → plan → tasks → implement (e comandos extra: clarify, checklist, analyze, converge).

CLI: `specify` (pacote `specify-cli`).

## Pré-requisitos

- Python 3.11+
- Git
- [uv](https://docs.astral.sh/uv/) (recomendado)
- Agente de código: Claude Code, Copilot, Gemini CLI, etc.

## Windows (PowerShell) — instalar uv

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Fecha e abre o terminal. Confirma:

```powershell
uv --version
```

## Instalar Specify (persistente)

```powershell
uv tool install specify-cli
```

Ou versão pinada / a partir do git:

```powershell
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

One-shot sem instalar:

```powershell
uvx --from git+https://github.com/github/spec-kit.git specify init nome-do-projeto
```

## Inicializar projecto

```powershell
specify init meu-projeto
# ou pasta actual:
specify init --here --integration copilot
# CI / não interactivo:
specify init meu-projeto --non-interactive --integration claude
```

## Ordem dos comandos no agente

1. `/speckit.constitution` — princípios e bans
2. `/speckit.specify` — o quê / porquê (sem stack)
3. `/speckit.clarify` — ambiguidades
4. `/speckit.plan` — como técnico
5. `/speckit.checklist` — qualidade
6. `/speckit.tasks` — tarefas verificáveis
7. `/speckit.analyze` — consistência entre artefactos
8. `/speckit.implement` — executar task a task
9. `/speckit.converge` — gaps vs codebase

## Relação com Plan-Execute do setup

| Spec Kit | network-agents-setup |
|----------|----------------------|
| constitution | `context.constraints` |
| specify | `goal` + audience |
| plan | `plan.yaml` + arquitectura |
| tasks | `steps[]` + `depends_on` + `done_when` |
| implement | executor por passo |
| analyze / checklist | `verify` + CriticReport |

Usar Spec Kit em **repos de software**. Pipelines de conteúdo/marketing mantêm `docs/architecture/plan-execute/`.

## Nota de ambiente sandbox

Instalação via PyPI pode falhar por proxy 502; no PC do utilizador com rede normal deve funcionar.
