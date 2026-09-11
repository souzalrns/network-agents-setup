# Design — agents ↔ skills ↔ runner

```text
plan steps[].action
  → agents/design/<name>.agent.md
  → skills/design/<action>/SKILL.md
  → plan_runner --mode external
```

| action | agent | skill |
|--------|-------|-------|
| ux_flow | ux.agent.md | ux_flow/SKILL.md |
| ui_spec | ui.agent.md | ui_spec/SKILL.md |
| ux_writing | ux_writer.agent.md | ux_writing/SKILL.md |
| design_critic | design_critic.agent.md | design_critic/SKILL.md |

## Teste

```powershell
cd $env:USERPROFILE\Downloads\network-agents-setup
git pull
cd runner
python -m plan_runner run ..\docs\orchestration\design\templates\examples\design-flow-demo.plan.yaml --mode stub --out ..\pilots\run-design-stub
```
