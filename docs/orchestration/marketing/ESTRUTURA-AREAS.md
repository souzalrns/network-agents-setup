# Estrutura da agência de marketing por áreas (M-006)

> Desenho de referência da vertical de marketing: como se organizam os agentes, que funções
> cada um tem e para onde vai cada função quando um agente é substituído. **Não é um documento
> de estado**: o estado está no item `M-006` do [`PENDENCIAS.md`](../../initiatives/PENDENCIAS.md).
> Os exemplos são fictícios (este repo é público).

## 1. Porquê

- Os agentes de marketing cresceram para ~60. Cerca de 40 vêm do
  [`coreyhaines31/marketingskills`](https://github.com/coreyhaines31/marketingskills) (MIT), feito para
  empresas de software. Parte deles só serve quem vende uma app (paywalls, ASO, signup).
- Estavam agrupados por tipo de tarefa, não por área de uma agência. Para quem lê o escritório,
  era difícil saber "quem faz o quê".
- Faltam funções de execução (produzir vídeo, publicar, medir redes sociais) que nenhum agente
  cobre hoje. Ficam para a fase 2 (§6).

## 2. Organização: direção + áreas + qualidade

```
Direção de marketing (marketing.marketing: o único lead real hoje)
 ├─ Estratégia
 ├─ Inteligência
 ├─ Conteúdo
 ├─ Vídeo & criativos
 ├─ Social & comunidade
 ├─ Site & SEO
 ├─ Anúncios
 ├─ CRM e vendas  (= departamento Comercial)
 └─ Qualidade     (revê tudo antes de sair)
 + SaaS & apps    (pacote opcional, só para quem vende software)
```

No escritório ([`config/office.yaml`](../../../config/office.yaml)) cada área é um lugar do
departamento Marketing; a área **CRM e vendas** é o departamento Comercial. O router não muda:
continua a escolher pela área `marketing` do [`config/areas.yaml`](../../../config/areas.yaml).

**Líderes de área.** A regra do escritório é que só é lead quem orquestra de facto. Hoje só o
`marketing.marketing` distribui trabalho (planos com vários passos). Um líder por área exige que
o router saiba descer mais um nível (área → sub-área → agente). Até lá, as áreas são lugares sem
lead e não se criam chefes decorativos. Ver a decisão **P-90**.

## 3. Ficha-padrão de um agente

Cada agente (líder ou especialista) tem a mesma ficha. A diferença essencial: **o líder coordena
e decide; o especialista executa uma especialidade a fundo.**

| Campo | O que diz |
|---|---|
| Missão | Uma frase: o resultado que entrega |
| Recebe de / entrega a | Quem lhe passa o trabalho e a quem o entrega |
| Funções | Passos concretos, com verbos (o que faz, por ordem) |
| Decide sozinho | O que pode resolver sem perguntar |
| Pede aprovação | Gastos, publicação, uso de imagem ou voz de pessoas reais |
| Ferramentas | O que usa para executar (e se é pago) |
| Regras que não quebra | Limites legais e de marca |
| Está pronto quando | Checklist verificável (vira `done_when` no plano) |
| Herda de | Funções de agentes substituídos que passou a cobrir |

### Exemplo fictício: uma loja de bicicletas quer um Reel sobre a revisão de inverno

**Líder de vídeo** (agente de área, fase 2)

- **Missão:** entregar vídeos prontos a publicar, dentro do orçamento, coordenando os especialistas de vídeo.
- **Funções:** interpretar o pedido (objetivo, rede, prazo) → escolher o formato (short de 30 s) →
  escolher o caminho de produção do mais barato para o mais caro (material real da loja → stock
  gratuito → clips gerados por IA) → fixar o orçamento por vídeo → montar o plano (guião → imagem e
  áudio em paralelo → edição → versões por rede) → rever o guião antes de gastar → juntar o pacote final.
- **Decide sozinho:** formato e ordem do trabalho. **Pede aprovação:** qualquer gasto pago e a publicação.
- **Está pronto quando:** cumpre o pedido, o custo está dentro do orçamento e a Qualidade aprovou.

**Guião UGC** (especialista; hoje `marketing.ugc`)

- **Missão:** escrever o guião falado e visual de um vídeo curto que prende nos primeiros 3 s.
- **Funções:** ler o brief e os factos do `research` (nunca inventa preços nem prazos) → escrever
  3 hooks alternativos ("A tua bicicleta aguenta o inverno?") → estruturar hook, problema, prova,
  CTA → acertar a duração (~2,5 palavras por segundo, ~75 palavras para 30 s) → indicar a cena de
  cada trecho → marcar a identificação de publicidade e de IA quando se aplica.
- **Está pronto quando:** 3 hooks, guião dentro da duração, cena por trecho, CTA claro, factos com fonte.

## 4. Inventário de funções e herdeiros

Antes de um agente sair, a função dele tem de passar para outro que fica activo e isso tem de
ficar **provado** (§5). Com a **P-89 = A** (decisão do maestro, 2026-11-04), o herdeiro carrega a
função como um **modo** da sua skill: `skills/marketing/<skill do herdeiro>/modes/<modo>.md`, que só
entra no prompt do passo com `mode: <modo>` (o prompt dos outros passos não cresce).

| Agente que saiu | Herdeiro + modo | Área | Porquê |
|---|---|---|---|
| `marketing_ideas` | `marketing_plan` + `ideas` | Estratégia | ideação é parte do plano |
| `marketing_council` | `marketing_plan` + `council` | Estratégia | o painel de especialistas decide a estratégia |
| `marketing_loops` | `marketing_plan` + `loops` | Estratégia | uma rotina recorrente é um plano que se repete |
| `launch` | `marketing_plan` + `launch` | Estratégia | um lançamento é um plano de campanha |
| `pricing` | `offers` + `pricing` | CRM e vendas | oferta e preço decidem-se juntos |
| `popups` | `cro` + `popups` | Site & SEO | popups são uma táctica de conversão |
| `free_tools` | `lead_magnets` + `free_tools` | CRM e vendas | ambos são iscos de captação |
| `competitors` | `seo_brief` + `competitors` | Site & SEO | páginas comparativas são páginas SEO |
| `revops` | `inbound_qualification` + `revops` | CRM e vendas | ciclo e scoring do lead |
| `co_marketing` | `referrals` + `co_marketing` | CRM e vendas | parcerias e indicações |
| `events` | `community_marketing` + `events` | Social & comunidade | eventos servem a comunidade |

Ficam, sem fusão: `aso`, `signup`, `onboarding`, `paywalls`, `churn_prevention` (pacote **SaaS & apps**,
só para quem vende software); `proposals`, `follow_ups`, `inbound_qualification` (pack COM-1);
`critic_item13` (templates do Item 13); e todos os outros, cada um na sua área do §2.

**Porquê o `marketing_plan` e não o `marketing.marketing`** (a proposta da fase 1 punha ideias, painel e
rotinas no coordenador): o coordenador não tem skill (`skill: null`, faz o dispatch para o catálogo),
por isso não tem onde guardar modos. O `marketing_plan` já é o agente de estratégia e tem skill.

**Como fica o conhecimento.** O modo é gerado pelo `scripts/vendor_marketingskills.py` (tabela
`MERGED`) com o conhecimento upstream integral e o contrato do runner, incluindo as notas de
conformidade. A capability **mantém o id** e passa a apontar para o herdeiro + `mode`. O agente e a
skill antigos saem do repo e ficam recuperáveis no histórico do git (commit anterior ao PR do M-006).

## 5. Prova de cada transferência

Os 4 pontos, para cada uma das 11, em `runner/tests/test_m006_transferencias.py` (corre no CI):

1. **Capability re-apontada:** mantém o id, aponta para o herdeiro + `mode`, e o agente e a skill
   antigos já não existem (`test_1_*`; o validador `python -m plan_runner.areas` também passa).
2. **Conhecimento preservado:** o texto do modo é igual ao conhecimento upstream, com o contrato do
   runner e as notas de conformidade (`test_2_*`).
3. **Encaminhamento:** um pedido típico do agente antigo (`transfers:` do `config/router-golden.yaml`)
   cai na área marketing pelas keywords reais e, com o LLM do router falso, no herdeiro com o modo
   certo; o prompt do router mostra o modo ao LLM (`test_3_*`). A qualidade do Gemini real nestes
   pedidos ainda não foi medida (a sessão não tinha chave): fica no item M-006.
4. **Execução:** um plano com o herdeiro + modo corre de ponta a ponta com o worker falso, o modo
   entra no prompt **só** nesse passo, o conhecimento chega ao modelo e o `done_when` passa (`test_4_*`).

**Relatório:**

| Agente que saiu | Herdeiro + modo | Capability | Testado (4 pontos) |
|---|---|---|---|
| `marketing_ideas` | `marketing_plan` + `ideas` | `marketing_ideas` | sim |
| `marketing_council` | `marketing_plan` + `council` | `marketing_council` | sim |
| `marketing_loops` | `marketing_plan` + `loops` | `marketing_loops` | sim |
| `launch` | `marketing_plan` + `launch` | `launch_plan` | sim |
| `pricing` | `offers` + `pricing` | `pricing_strategy` | sim |
| `popups` | `cro` + `popups` | `popups_overlays` | sim |
| `free_tools` | `lead_magnets` + `free_tools` | `free_tools` | sim |
| `competitors` | `seo_brief` + `competitors` | `comparison_pages` | sim |
| `revops` | `inbound_qualification` + `revops` | `revenue_operations` | sim |
| `co_marketing` | `referrals` + `co_marketing` | `co_marketing` | sim |
| `events` | `community_marketing` + `events` | `events_marketing` | sim |

## 6. Fase 2 (não incluída aqui)

Agentes novos previstos, todos com a ficha do §3:

| Área | Agente novo | Faz |
|---|---|---|
| Estratégia | guardião de marca | Mantém o contexto da marca que todos leem (evolui do `product_marketing`) |
| Inteligência | social intelligence | Métricas públicas de redes da concorrência (APIs oficiais) |
| Inteligência | performance social | Lê os resultados publicados e devolve o que funcionou |
| Vídeo & criativos | produtor IA | Gera os clips (ferramentas pagas só com aprovação) |
| Vídeo & criativos | áudio e voz | Narração, música sem direitos, legendas |
| Vídeo & criativos | repurposing | 1 vídeo em versões por rede; vídeo longo em vários curtos |
| Social & comunidade | calendário | Calendário editorial |
| Social & comunidade | publicador | Agenda a publicação (só com aprovação humana) |
| Qualidade | compliance | Regras de publicidade, identificação de IA (AI Act, art. 50), direitos de imagem e música |

Referências públicas para os desenhar (licença a confirmar antes de copiar texto):
[`msitarzewski/agency-agents`](https://github.com/msitarzewski/agency-agents) (MIT),
[`aaron-he-zhu/aaron-marketing-skills`](https://github.com/aaron-he-zhu/aaron-marketing-skills) (Apache-2.0,
modelo de disciplina com ciclo de 4 fases), [`social-media-skills/skills`](https://github.com/social-media-skills/skills) (MIT)
e [`indranilbanerjee/digital-marketing-pro`](https://github.com/indranilbanerjee/digital-marketing-pro) (MIT, compliance).
