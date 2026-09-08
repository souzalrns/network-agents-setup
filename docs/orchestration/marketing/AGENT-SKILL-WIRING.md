# Integração agents ↔ skills ↔ runner

## Cadeia

```text
plan.yaml steps[].action
        │
        ▼
agents/marketing/<action>.agent.md   (identidade + system)
        │
        ▼
skills/marketing/<action>/SKILL.md   (processo + done_when)
        │
        ▼
plan_runner --mode external
        │
        ▼
pilots/<run>/pending_steps/<step_id>/
           request.json   (paths + previews)
           AGENT.md       (cópia)
           SKILL.md       (cópia)
           result.json    (worker preenche)
```

## Agent de pesquisa

- Definição: `agents/marketing/research.agent.md`  
- Skill: `skills/marketing/research/SKILL.md`  
- Templates que o usam: `seo_article`, `social_pack`, `internal_brief` (step `research` / `gather` usa action research)

Nota: no template internal-brief o step id é `gather` mas `action: research` → resolve skill/agent **research**.

## Como testar

```powershell
cd $env:USERPROFILE\Downloads\network-agents-setup
git pull
cd runner
python -m plan_runner run ..\docs\orchestration\marketing\templates\seo-article.plan.yaml --mode external --out ..\pilots\run-seo-external
```

Abre `..\pilots\run-seo-external\pending_steps\research\` e confirma `SKILL.md` + `AGENT.md` + `request.json`.

Worker (humano ou outra IA): executa a skill, grava artefacto ou `result.json` com `ok: true`, depois:

```powershell
python -m plan_runner resume ..\pilots\run-seo-external --decision approve
```

(Para `waiting_external`, o resume re-tenta o step; se já existir `result.json`, avança. Se estiver em human_gate, `--decision` aplica-se ao gate.)

## Stub vs external

| Mode | Skills |
|------|--------|
| stub | Não carrega (placeholder) |
| external | Copia skill+agent para pending |
| dry-run | Só ordem |
