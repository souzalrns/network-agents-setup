# Visibilidade em IA (GEO/AEO): medir antes de mexer (M-006)

**O que é:** o agente `marketing.ai_visibility` (área Site & SEO) diagnostica se a marca aparece quando
alguém pergunta a um assistente de IA, e o que mudar para aparecer mais. Os números vêm de uma medição
feita com `python -m plan_runner.ai_visibility`: o agente nunca os inventa. Sem medição no input, entrega o
painel de perguntas e o protocolo.

O que move a citação, com o grau de evidência, está em [`docs/knowledge/ai-visibility.md`](../knowledge/ai-visibility.md):
SEO de base, resposta directa no topo, dados originais, entidade clara e conteúdo acessível no HTML. O
`llms.txt` e o "schema de IA" têm evidência fraca e não são vendidos como alavanca.

## Onde entra no trabalho

| Momento | Quem | O quê |
|---|---|---|
| Antes de escrever | `seo_brief` | queries como as pessoas perguntam aos assistentes, FAQ citável, entidades (Item 13) |
| A escrever | `copy_answer_first` | resposta directa no topo (template `seo-article`) |
| Antes de publicar | `critic_item13` | revisão de citabilidade: no `seo-article` e, desde agora, no template da área Site & SEO |
| Depois de publicar | `ai_visibility` + este comando | mede a marca num painel fixo de perguntas e diz onde falha |

## O painel

Um YAML com a marca, 0 a 6 concorrentes e 1 a 25 perguntas. É a régua: só se comparam medições do
mesmo painel e do mesmo motor. Exemplo fictício:
[`docs/orchestration/marketing/ai-visibility/painel-exemplo.yaml`](../orchestration/marketing/ai-visibility/painel-exemplo.yaml).
Os painéis reais e as medições ficam fora deste repo público (em `pilots/`, fora do git, ou no repo privado).

- **mencionada:** o nome da marca (ou um nome alternativo) aparece na resposta, sem contar acentos nem
  maiúsculas, como palavra inteira;
- **citada:** uma das fontes da resposta é de um domínio da marca (ou de um subdomínio).

## Medir

```bash
cd runner
# Gemini com pesquisa Google: simula por omissão (mostra as perguntas e quantos pedidos seriam)
python -m plan_runner.ai_visibility medir <painel.yaml> --out ../pilots/ai-visibility/<marca>
# medir de facto (1 pedido por pergunta, no máximo 25; precisa de GEMINI_API_KEY)
python -m plan_runner.ai_visibility medir <painel.yaml> --out ../pilots/ai-visibility/<marca> --run

# ChatGPT, Perplexity, Claude… sem API: cola as respostas num YAML e pontua igual
python -m plan_runner.ai_visibility importar <painel.yaml> respostas.yaml --motor chatgpt --out ../pilots/ai-visibility/<marca>
```

`respostas.yaml`: `[{pergunta: <id>, resposta: "<texto>", fontes: ["https://…"]}]`. Uma pergunta sem
resposta fica `nao_medida` e não conta para as percentagens.

**Saída:** `medicao-<motor>-<data>.json` (resposta, fontes e pesquisas feitas por pergunta),
`historico.jsonl` (uma linha por medição) e `resumo.md` (tabela por marca e concorrente, com a variação
face à medição anterior do mesmo painel e motor, e aviso quando a amostra tem menos de 10 perguntas).
Código de saída: `0` se todas as perguntas foram medidas; `2` se faltou alguma; `1` se foi recusado.

## Custo

- **Importar:** zero, em qualquer motor.
- **Medir com o Gemini:** usa a pesquisa Google do Gemini (grounding). A Google dá uma quota grátis desta
  pesquisa, mas os números publicados não são claros e mudam por modelo e por tipo de conta (uma fonte de
  maio de 2026 indica 5000 pedidos/mês nos modelos Gemini 3, em contas com faturação activa; acima disso
  é pago). Um painel de 25 perguntas por mês fica muito abaixo dessa quota, mas confirma na página de
  preços da API Gemini antes de medir com regularidade.
- Guardas do comando: simula sem `--run`; no máximo 25 pedidos por execução; sem novas tentativas; um
  `401`, `403` ou `429` (chave ou quota) pára de imediato e guarda o que já foi medido.

## Limites honestos

- Uma resposta de IA varia de uma pergunta para a seguinte: uma medição é uma amostra, não um ranking.
  Mede sempre com o mesmo painel e compara tendências, não um número isolado.
- O Gemini com pesquisa aproxima as respostas com fontes (tipo AI Overviews). Não é o mesmo que o ChatGPT
  ou o Perplexity: por isso o `importar` existe.

Prova: `runner/tests/test_ai_visibility.py` (Gemini falso com `groundingMetadata` como a API real).
