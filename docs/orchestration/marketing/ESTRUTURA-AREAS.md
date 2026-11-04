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
- Faltavam funções de execução (produzir vídeo, publicar, medir redes sociais) que nenhum agente
  cobria. A fase 2 (§6) juntou-as: 9 agentes que preparam a execução.

## 2. Organização: direção + áreas + qualidade

```
Direção de marketing (marketing.marketing: dispatch pelo router, sem skill)
 ├─ Estratégia            líder: marketing.lider_estrategia
 ├─ Inteligência          líder: marketing.lider_inteligencia
 ├─ Conteúdo              líder: marketing.lider_conteudo
 ├─ Vídeo & criativos     líder: marketing.lider_video
 ├─ Social & comunidade   líder: marketing.lider_social
 ├─ Site & SEO            líder: marketing.lider_site_seo
 ├─ Anúncios              líder: marketing.lider_anuncios
 ├─ CRM e vendas          líder: marketing.lider_crm   (= departamento Comercial)
 └─ Qualidade             (revê tudo antes de sair; sem líder: é uma camada, não uma área)
 + SaaS & apps            (pacote opcional, só para quem vende software; sem líder)
```

No escritório ([`config/office.yaml`](../../../config/office.yaml)) cada área é um lugar do
departamento Marketing; a área **CRM e vendas** é o departamento Comercial. O router não muda:
continua a escolher pela área `marketing` do [`config/areas.yaml`](../../../config/areas.yaml).

**Líderes de área (P-90 = B, decisão do maestro de 2026-11-04).** Cada líder coordena como o
`marketing.marketing`, mas só com os especialistas da sua área: decide o âmbito, o caminho e a ordem
e entrega o **brief da área** (`artifacts/00-brief-<área>.md`), que é o input de todos os passos dos
especialistas. Não faz o trabalho deles nem os chama (sem mesh): quem corre os passos é o plano.

- **Onde orquestram:** nos templates de área em [`templates/areas/`](./templates/areas/), um por área:
  líder → especialistas (em paralelo quando são independentes) → `critic` → aprovação humana.
- **Quando o router os escolhe:** a descrição de cada líder diz "usar quando o pedido é um projecto
  completo da área". Para um entregável simples, o router continua a ir directo ao especialista.
- **Regra do escritório:** um `lead` só é aceite se orquestrar de facto num plano real (um passo de
  outro agente do lugar depende do passo dele). Os 8 líderes têm essa evidência nos templates; se um
  template deixar de depender do líder, o CI falha (`plan_runner/office.py`, `tests/test_m006_lideres.py`).
- **Testes:** cada líder tem a ficha-padrão completa; a tabela de especialistas da skill bate com o
  lugar (ou departamento) no escritório e com os modos reais; o template só usa especialistas da área,
  começa no líder e acaba num gate humano; e corre de ponta a ponta com o brief a chegar ao prompt de
  cada especialista (`tests/test_m006_lideres.py`).

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

**Líder de vídeo** (agente de área, `marketing.lider_video`)

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

## 6. Fase 2: agentes de execução (feita)

Os 9 agentes têm a ficha do §3 com uma secção a mais, **Fronteiras (não confundir com)**, porque
cada um encosta a um especialista que já existia. Todos **preparam** a execução: nenhum publica,
agenda nem gasta. Uma ferramenta paga ou uma publicação real só acontece com aprovação humana e com a
ferramenta ligada (próximo passo, fora deste repo).

| Área | Agente | Action | Faz | Usado em |
|---|---|---|---|---|
| Estratégia | `marketing.guardiao_marca` | `brand_guardian` | Livro de marca que todos leem (voz, tom, claims permitidos) | `estrategia.plan.yaml` |
| Inteligência | `marketing.social_intelligence` | `social_intelligence` | Padrões das redes da concorrência, a partir de dados fornecidos ou de APIs oficiais | `inteligencia.plan.yaml` |
| Inteligência | `marketing.performance_social` | `social_performance` | Lê os resultados publicados e devolve o que funcionou | `inteligencia.plan.yaml` |
| Vídeo & criativos | `marketing.produtor_video` | `video_production` | Folha de produção: origem e custo de cada cena (gerar só com aprovação) | `video.plan.yaml` |
| Vídeo & criativos | `marketing.audio_voz` | `audio_voice` | Narração, música com licença, legendas | `video.plan.yaml` |
| Vídeo & criativos | `marketing.repurposing` | `repurposing` | 1 vídeo em versões por rede; longo em vários curtos | `video.plan.yaml` |
| Social & comunidade | `marketing.calendario` | `editorial_calendar` | Calendário editorial | `social.plan.yaml` |
| Social & comunidade | `marketing.publicador` | `publish_package` | Pacote de publicação em JSON, pronto a agendar (não publica) | `social.plan.yaml` |
| Qualidade | `marketing.compliance` | `compliance_check` | Publicidade identificada, IA identificada (AI Act, art. 50), direitos de imagem, voz e música, claims regulados, consentimento; veredicto em JSON | **todos** os templates de área |

Cadeias novas: no Vídeo, `guiao → (producao ∥ imagem ∥ audio) → edicao → versoes`; no Social,
`(comunidade ∥ criadores) → calendario → publicacao`. Em todas as áreas, `critic` e `compliance`
revêem em paralelo e o `hitl` só abre depois dos dois. Prova: `runner/tests/test_m006_execucao.py`.

Referências públicas para os desenhar (licença a confirmar antes de copiar texto):
[`msitarzewski/agency-agents`](https://github.com/msitarzewski/agency-agents) (MIT),
[`aaron-he-zhu/aaron-marketing-skills`](https://github.com/aaron-he-zhu/aaron-marketing-skills) (Apache-2.0,
modelo de disciplina com ciclo de 4 fases), [`social-media-skills/skills`](https://github.com/social-media-skills/skills) (MIT)
e [`indranilbanerjee/digital-marketing-pro`](https://github.com/indranilbanerjee/digital-marketing-pro) (MIT, compliance).
