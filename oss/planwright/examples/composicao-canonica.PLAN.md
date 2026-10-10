# Cenário canónico — a composição planwright → plan_runner

A planwright **descreve** este plano; o `plan_runner` **executa-o** com
governação (porta humana, tecto de orçamento, `done_when` por evidência). É a
mesma tabela de sempre — o que a torna canónica é o caminho que percorre:

```
planwright graph   examples/composicao-canonica.PLAN.md
planwright action  examples/composicao-canonica.PLAN.md
planwright export  examples/composicao-canonica.PLAN.md > contract.json
```

O `export` emite o contrato `planwright-plan/v1`; o runner importa-o
(`python -m plan_runner.plan_import contract.json --id composicao-canonica`) num
esqueleto de plano, que um humano/router completa no plano executável. O caminho
completo, com o delta esqueleto → plano, está em
`docs/architecture/CANONICAL-SCENARIO.md`.

O item `decide` é `Autonomy=human`: no contrato vira `human_gate`, e no runner é
a porta que pausa o run à espera de uma decisão. `Complexity` viaja como
**sinal** de routing, nunca como política de runtime.

| ID       | Title                                  | Status | Owner   | Est | Depends  | Track      | Autonomy | Complexity |
|----------|----------------------------------------|--------|---------|-----|----------|------------|----------|------------|
| research | Levantar requisitos e contexto         | todo   | agent   | 2h  | -        | discovery  | auto     | C2         |
| decide   | Aprovar o rumo antes de investir       | todo   | maestro | 1h  | research | governance | human    | C3         |
| draft    | Redigir a proposta                     | todo   | agent   | 3h  | decide   | build      | auto     | C2         |
| finalize | Consolidar e publicar o resultado      | todo   | agent   | 1h  | draft    | build      | auto     | C1         |
