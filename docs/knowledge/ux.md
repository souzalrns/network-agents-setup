# Knowledge Pack — ux

Conhecimento operacional para o agente UX Specialist.

---

## 1. Modelo de análise de jornada

Para qualquer fluxo (signup, checkout, orçamento, agendamento, onboarding):

1. **Objetivo do usuário** — o que ele quer concluir
2. **Etapas** — lista ordenada do início ao fim
3. **Pontos de decisão** — onde pode abandonar ou errar
4. **Fricção** — esforço, confusão, espera, dados excessivos
5. **Feedback** — o sistema confirma progresso e erros de forma clara?
6. **Recuperação** — dá para voltar, corrigir, salvar?

### Sinais de fricção comuns

| Sinal | Impacto típico |
|-------|----------------|
| Campos demais no primeiro passo | Abandono alto |
| Jargão ou labels ambíguos | Erro + suporte |
| Sem indicação de progresso | Ansiedade / drop |
| Erro só no submit final | Retrabalho |
| Ação crítica espalhada em muitas telas | Complexidade percebida |
| CTA principal competindo com secundários | Hesitação |

**Princípio já validado na rede:** concentrar ações críticas em poucas telas; evitar espalhar fluxos sem necessidade.

---

## 2. Hierarquia de problemas (priorização)

1. **Bloqueio** — usuário não consegue concluir
2. **Erro frequente** — conclui errado ou com retrabalho
3. **Fricção alta** — conclui, mas com esforço desproporcional
4. **Clareza** — entende, mas demora a entender
5. **Polimento** — microcopy, animação, detalhe

Nunca comece por polimento se há bloqueio.

---

## 3. Acessibilidade na jornada (o que UX deve exigir)

UX não implementa tokens, mas **exige** que o fluxo seja usável:

| Requisito | Por quê na jornada |
|-----------|---------------------|
| Ordem de foco lógica | Teclado / leitor de tela seguem o fluxo real |
| Erros associados ao campo | 3.3.1 / 3.3.3 — não só toast genérico |
| Labels persistentes | Placeholder some; label não |
| Target size adequado | Mobile e motor fino |
| Focus não coberto por sticky | 2.4.11 — usuário de teclado perde o lugar |
| Alternativa a drag | 2.5.7 — quem não arrasta ainda opera |
| Não pedir o mesmo dado de novo | 3.3.7 Redundant Entry |

Contraste e design system detalhado → agente **ui**. UX aponta o problema de usabilidade/a11y no fluxo.

---

## 4. Arquitetura de informação (rápido)

- Uma intenção primária por página/tela sempre que possível
- Navegação: o usuário sabe onde está, o que pode fazer, como voltar
- Agrupar por tarefa do usuário, não por organograma interno
- Empty states: explicar o que falta e a próxima ação
- Estados de loading e erro fazem parte da jornada — não são “detalhe de UI”

---

## 5. O que o agente NÃO faz

- Não define identidade visual, tokens ou componentes visuais (ui / diretor-arte)
- Não escreve copy final de venda (copywriter) — pode sugerir microcopy de interface
- Não inventa dados de analytics (taxa de abandono, heatmaps) sem contexto
- Não gera protótipos visuais finais

---

## 6. Formato de resposta preferido

1. Objetivo do usuário e contexto assumido
2. Mapa resumido do fluxo (etapas)
3. Problemas ordenados por severidade (bloqueio → polimento)
4. Recomendações concretas por problema
5. Premissas e o que precisa ser validado com dados reais (analytics, teste com usuário)
