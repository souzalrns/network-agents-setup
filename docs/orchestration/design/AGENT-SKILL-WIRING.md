# Design — agents ↔ skills ↔ runner

```text
plan steps[].action
  → agents/design/<name>.agent.md
  → skills/design/<action>/SKILL.md
  → plan_runner --mode external
  → pending_steps/<id>/{AGENT,SKILL,request,result}.json
```

| action | agent | skill |
|--------|-------|-------|
| ux_flow | ux.agent.md | ux_flow/SKILL.md |
| ui_spec | ui.agent.md | ui_spec/SKILL.md |
| design_critic | design_critic.agent.md | design_critic/SKILL.md |

## Teste

```powershell
cd $env:USERPROFILE\Downloads\network-agents-setup\runner
python -m plan_runner run ..\docs\orchestration\design\templates\design-flow.plan.yaml --mode stub --out ..\pilots\run-design-stub
```
