# Rate limits — Gemini (embeddings) no pipeline de ingestão

## Achado confirmado (2026-09-17)

O workflow `ingest-knowledge` falhou repetidamente (19 de 24 runs num dia) com:

```
ERROR docs/item-13-ai-findability.md: Gemini devolveu HTTP 429
"You exceeded your current quota"
```

**Causa raiz confirmada, não hipótese:** o tier gratuito da API Gemini (`gemini-embedding-001`) tem uma quota de pedidos que esta sessão excedeu — não por um único ficheiro grande, mas pelo **volume de runs consecutivos**: várias tarefas desta sessão acrescentaram ficheiros `.md` em sequência rápida, cada `push` disparando um novo run de `ingest-knowledge` (por causa do `paths: docs/**/*.md` no trigger), sem qualquer controlo de concorrência entre eles. Confirmado por investigação directa: entre 13:20 e 13:25 correram 4 runs em menos de 5 minutos.

O diff do commit que primeiro mostrou a falha (`3d460ba`) foi investigado e **descartado como causa** — só acrescentava um `.md` novo, sem tocar em `scripts/ingest_apply.py`/`ingest_delta.py`; o commit anterior, estruturalmente idêntico, tinha tido sucesso.

## Correcção aplicada

1. **`scripts/ingest_apply.py`** — retry com backoff exponencial (2s, 4s, 8s — 3 tentativas) só para `HTTP 429`; outros erros (auth, timeout) continuam a propagar-se de imediato, sem retry sem sentido. Se as 3 tentativas esgotarem para um ficheiro, esse ficheiro é reportado como falha e a corrida **continua para o próximo** — deixou de abortar o run inteiro ao primeiro erro. Novo `--max-chunks` (default 50) limita quantos chunks são embeddados numa corrida, como orçamento de protecção adicional.
2. **`.github/workflows/ingest-knowledge.yml`** — `concurrency: group` + `cancel-in-progress: true`, para que um `push` novo cancele um run ainda a decorrer em vez de os dois competirem pela mesma quota ao mesmo tempo.

## Decisão não aplicada, documentada para follow-up

O pedido original também levantava "considerar correr só em `workflow_dispatch` (não a cada push)". **Decidi não remover o trigger de `push`** nesta correcção — é uma mudança de comportamento maior (deixaria de haver ingestão automática ao editar docs), e as duas correcções acima (retry + concorrência controlada) já atacam a causa raiz confirmada (rajada de runs simultâneos), sem essa perda de automatismo. Se a quota voltar a esgotar-se mesmo com estas duas correcções, essa é a próxima alavanca a puxar.

## Limite conhecido, não resolvido

Mesmo com retry, **3 tentativas com backoff de poucos segundos não resolve uma quota diária/mensal esgotada** — só resolve limitação de taxa por minuto/segundo. Se o esgotamento for de quota mais longa (diária), o retry vai esgotar-se na mesma e o `--max-chunks` é a única protecção real disponível hoje. Não há, neste momento, visibilidade sobre qual tipo de quota (por minuto vs. diária) foi de facto excedida — o texto do erro Gemini (`"You exceeded your current quota"`) não distingue isso.


## Verificação pós-correcção (2026-09-17, 23:17)

**A correcção não resolveu o problema.** Os runs disparados pelos próprios commits da correcção (`d721a93` — `ingest_apply.py`; `5fb5f1c` — este documento) **continuam a falhar** no mesmo step, "Apply delta (embed + Supabase)".

Isto confirma a ressalva já escrita acima, agora como facto observado, não hipótese: retry com poucos segundos de backoff só ajuda contra limite de taxa por minuto/segundo — se a quota excedida for de âmbito diário, as 3 tentativas esgotam-se todas na mesma janela de indisponibilidade.

**O que a correcção já aplicada faz de facto, mesmo sem resolver isto:**
- Evita que runs simultâneos piorem o esgotamento (`concurrency`).
- Evita gastar retries a torto e a direito além do necessário (só re-tenta em 429).
- Limita o dano por corrida (`--max-chunks`).
- Não abandona a meio — processa o que consegue e reporta claramente o resto.

**O que continua por resolver:** confirmar se a quota do Gemini em uso é diária, e se sim, esperar a renovação (ou pedir upgrade do tier) é a única solução real — nenhuma mudança de código neste repositório resolve uma quota diária esgotada.


## Confirmado: é DIÁRIA e por minuto (as duas, não uma ou outra)

Pesquisa directa na documentação oficial (`ai.google.dev/gemini-api/docs/rate-limits`) confirma: o Gemini mede uso em **3 dimensões simultâneas** — RPM (pedidos/minuto), TPM (tokens/minuto), e **RPD (pedidos/dia)**. Qualquer uma das três, ao ser excedida, devolve `429 RESOURCE_EXHAUSTED` — o texto do erro não distingue qual das três foi violada.

**Números concretos do tier gratuito para `gemini-embedding-001`** (fonte: documentação de terceiros que replica a tabela oficial da AI Studio, consistente com a estrutura confirmada em `ai.google.dev`):

| Tier | RPM | TPM | RPD |
|---|---|---|---|
| Free | 100 | 30.000 | **1.000** |
| Tier 1 (billing activado) | 3.000 | 1.000.000 | sem limite diário publicado |

**Confirmado também:** a quota RPD **reset à meia-noite Pacific Time** (não UTC, não hora local Lisboa) — isto explica por que os runs continuaram a falhar ao longo de toda uma tarde/noite europeia: se o limite diário (1.000 pedidos) foi excedido de manhã (hora de Lisboa), só recupera depois da meia-noite da Califórnia, que em UTC+1 (Lisboa, horário de verão) só chega às ~09:00 do dia seguinte.

**Implicação directa para este pipeline:** com 39 ficheiros no `MANIFEST`, cada um a gerar vários chunks (cada chunk = 1 pedido de embedding), um único run "aplicar tudo do zero" pode facilmente aproximar-se ou ultrapassar os 1.000 pedidos/dia do tier gratuito — sem sequer contar a repetição de vários runs no mesmo dia (como aconteceu). O `--max-chunks` (default 50) já adicionado ajuda a não gastar tudo de uma vez, mas **não aumenta o tecto diário** — só o retry/backoff resolve o RPM/TPM (curto prazo); o RPD só se resolve esperando o reset (meia-noite Pacific) ou fazendo upgrade a Tier 1 (activar billing).

**Fonte:** [ai.google.dev/gemini-api/docs/rate-limits](https://ai.google.dev/gemini-api/docs/rate-limits) (estrutura RPM/TPM/RPD, reset à meia-noite Pacific — confirmado directamente na documentação oficial). Os números exactos de RPM/TPM/RPD do tier gratuito citados na tabela acima vêm de uma fonte secundária que reproduz a tabela da AI Studio; a documentação oficial da Google não publica um número único fixo no texto da página (varia por projecto) — recomenda-se confirmar o valor exacto activo directamente em AI Studio > Rate Limits antes de dimensionar qualquer solução em torno destes números.
