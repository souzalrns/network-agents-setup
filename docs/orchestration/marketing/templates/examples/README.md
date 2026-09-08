# Exemplos de plan (objective preenchido)

| Ficheiro | Uso |
|----------|-----|
| [seo-article-demo.plan.yaml](./seo-article-demo.plan.yaml) | Demo Item 13 / AI Findability — nao e cliente real |

```powershell
cd $env:USERPROFILE\Downloads\network-agents-setup\runner
python -m plan_runner run ..\docs\orchestration\marketing\templates\examples\seo-article-demo.plan.yaml --mode external --out ..\pilots\run-seo-demo
```

Worker: preencher cada `pending_steps/<id>/result.json` (+ artefactos) e `resume`.
