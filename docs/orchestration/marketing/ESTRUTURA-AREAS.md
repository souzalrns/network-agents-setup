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
lead e não se criam chefes decorativos. Ver a decisão **P-89** no §10 do PENDENCIAS.

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
ficar **provado** (§5). Nesta fase **nenhum agente sai**: só se reagrupam os lugares. As fusões
abaixo esperam pela decisão P-89 (como o herdeiro carrega o conhecimento sem engordar o prompt).

| Agente actual | Fica / herdeiro proposto | Área | Porquê |
|---|---|---|---|
| `marketing_ideas` | funde-se em `marketing` | Direção | ideação é trabalho do coordenador |
| `marketing_council` | funde-se em `marketing` | Direção | painel de especialistas como modo do coordenador |
| `marketing_loops` | funde-se em `marketing` | Direção | rotinas recorrentes são planos do coordenador |
| `launch` | funde-se em `marketing_plan` | Estratégia | um lançamento é um plano de campanha |
| `pricing` | funde-se em `offers` | CRM e vendas | oferta e preço decidem-se juntos |
| `popups` | funde-se em `cro` | Site & SEO | popups são uma táctica de conversão |
| `free_tools` | funde-se em `lead_magnets` | CRM e vendas | ambos são iscos de captação |
| `competitors` | funde-se em `seo_brief` | Site & SEO | páginas comparativas são páginas SEO |
| `revops` | funde-se em `inbound_qualification` | CRM e vendas | ciclo e scoring do lead |
| `co_marketing` | funde-se em `referrals` | CRM e vendas | parcerias e indicações |
| `events` | funde-se em `community_marketing` | Social & comunidade | eventos servem a comunidade |
| `aso`, `signup`, `onboarding`, `paywalls`, `churn_prevention` | ficam, no pacote **SaaS & apps** | SaaS & apps | só servem quem vende software |
| `proposals`, `follow_ups`, `inbound_qualification` | ficam | CRM e vendas | pack COM-1, já testado |
| `critic_item13` | fica | Qualidade | ligado aos templates do Item 13 |
| todos os outros | ficam | a área do §2 | função própria e sem sobreposição |

**Como fica o conhecimento de um agente fundido.** O texto integral de cada skill vinda do
`marketingskills` já vive em `vendor/marketingskills/skills/<nome>/` (regenerado pelo
`scripts/vendor_marketingskills.py`). A capability (a função) **não se apaga**: passa a apontar
para o herdeiro. O agente fundido sai do repo e fica recuperável no histórico do git, com o
commit indicado no PR que o retira.

## 5. Prova de cada transferência (antes de retirar um agente)

1. **Capability re-apontada:** a função continua registada em `config/marketing-capabilities.yaml`,
   agora com o agente herdeiro (`python -m plan_runner.areas` tem de passar).
2. **Encaminhamento:** 2 a 3 pedidos típicos do agente antigo entram no
   `config/router-golden.yaml` e têm de cair no herdeiro (`tests/test_router.py`).
3. **Conteúdo:** o herdeiro cumpre a checklist (`done_when`) do agente antigo num plano de teste.
4. **Relatório:** uma linha por agente: herdeiro, testado sim/não, PR.

Só com os 4 pontos verdes o agente é retirado.

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
