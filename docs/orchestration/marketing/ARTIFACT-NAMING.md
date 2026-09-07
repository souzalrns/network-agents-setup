# Naming de artefactos (marketing)

Padrão genérico para runs do plan_runner e workers.

```text
artifacts/
  NN-short-name.ext

NN = ordem no plan (01, 02, …)
short-name = kebab-case
ext = md | json | yaml
```

Exemplos:

```text
01-research.md
02-seo-brief.json
03-copy.md
04-critic.json
05-hitl.json
```

Versionamento em rework:

```text
03-copy.md
03-copy-r2.md      # rodada 2 de revisão
03-copy-final.md   # após approve
```

Proibido: espaços, acentos no filename, secrets no nome ou conteúdo commitável.
