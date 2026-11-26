# Catálogo de ferramentas opcionais

> Decisões de 2026-11-25 (maestro). Este documento é um **catálogo de capacidades opcionais**, não
> um registo de estado: o estado vive no [`PENDENCIAS.md`](../initiatives/PENDENCIAS.md).
> Nada daqui vem ligado: **cada ferramenta está desligada por omissão** e só se liga por decisão
> explícita de quem usa o repo.

## Para quem é

Este repo é público e serve qualquer negócio, não só o de quem o mantém. Por isso cada ferramenta
foi avaliada com quatro perguntas, sempre com resposta sim/não:

1. **Risco de cobrança?** (custo directo, licença paga a partir de certa dimensão, consumo de quota)
2. **Risco de segurança?** (código de terceiros, binários, contas, dados pessoais, termos de uso)
3. **Boa ferramenta?** (mantida, útil, sem armadilhas conhecidas)
4. **Serve o setup público?** (útil para outros, não só para um utilizador)

Regra geral do repo: **nada pago e nada instalado sem aprovação explícita**. Tudo o que está abaixo
funciona em modo gratuito; os avisos dizem quando uma escala ou um uso diferente deixa de o ser.

## Opcionais (desligadas por omissão)

| Ferramenta | Para quê | Cobrança | Segurança | Requisitos e avisos |
|---|---|---|---|---|
| **Agent Reach** | Dar a agentes leitura e pesquisa de web, YouTube, GitHub e outras fontes | Não (MIT) | Sim, moderado | Usar só os canais **sem login**; os canais com login são experimentais. Fixar a versão ao instalar. |
| **Maxun** | Extracção de dados web sem código, com agendamento e MCP | Não, em self-host (a versão cloud é paga e não se usa) | Sim, moderado | Licença **AGPL-3.0**: quem a integrar num produto fechado tem obrigações de disponibilização do código. |
| **ScrapeGraphAI** | Extracção com LLM a partir de páginas | Não, com modelo local; API na cloud e modelos pagos só com aprovação | Sim | **RGPD/LGPD:** usar apenas para dados públicos de empresas; nunca para varrer contactos pessoais em massa. |
| **Remotion** | Vídeo programático em React | Não para indivíduos e equipas até 3 pessoas; **sim para 4 ou mais** | Não (pacote npm; tem telemetria de renders) | Equipas de 4 ou mais pessoas precisam de licença de empresa. Ver a página de licenças do Remotion antes de usar. |
| **Wan 2.x** (vídeo por IA, Alibaba) | Gerar vídeo localmente | Não (Apache-2.0) | Não | Precisa de **GPU**. O modelo T2V-1.3B pede cerca de 8 GB de VRAM; os de 14B pedem 24 GB ou mais. Sem GPU, não instalar. |
| **ComfyUI** | Fluxos de geração de imagem e vídeo, integra com o Wan | Não | Sim, moderado | Extensões ("custom nodes") de terceiros correm código: instalar só de fontes que se auditou. Precisa de GPU. |
| **Duix Avatar** | Avatar digital e clonagem de voz offline | Não para uso pequeno | Sim | Licença própria (DUIX.COM Community License, não OSI): exige atribuição e licença comercial acima de certos limites de utilizadores. **Clonar rosto ou voz só com consentimento escrito da pessoa.** Precisa de GPU NVIDIA. |
| **Caveman** | Reduzir tokens de saída dos agentes | Não (MIT) | Não | Acrescenta tokens de entrada e pode piorar respostas curtas. **Medir antes de ligar** em agentes de produção. |
| **Orca** | Orquestração de agentes Claude Code numa app de desktop | Não (MIT) | Sim, moderado | App de terceiros com acesso aos repositórios; serve quem trabalha num PC local. |
| **Wren AI** | Perguntas em linguagem natural sobre bases de dados (texto para SQL), com camada semântica e servidor MCP | Não (núcleo Apache-2.0; existe versão comercial) | Sim | Dá a um modelo acesso a dados reais: ligar **só com utilizador de base de dados só de leitura**. Precisa de chave de um modelo de linguagem. |
| **agenttrace** | Relatórios locais de custo, tokens e lentidão das sessões de agentes de código | Não | Sim, baixo | Corre localmente e não envia prompts para fora. Instala-se por script (`curl … \| sh`): ler o script antes de correr e confirmar a licença no repositório. Só serve a quem usa o Claude Code no próprio computador. |

## Práticas adoptadas (não são instalação)

| Prática | O que fazer |
|---|---|
| **Loops de agente** (`/loop`, `/goal`, `/schedule` do Claude Code) | Usar com critério de paragem e **teto de ciclos** definidos; consomem a quota de utilização. |
| **GSAP + ScrollTrigger** | Opção de animação para projectos visuais novos; confirmar os termos da licença no momento de usar. |
| **Plugin `security-guidance`** (Anthropic) | O Claude revê o próprio código à procura de vulnerabilidades durante a sessão | Gratuito, mas as revisões consomem quota de utilização. Em sessões na nuvem, declarar `enabledPlugins` em `.claude/settings.json` do repo. Activar só nos repos que vão para produção. |
| **public-apis** | Lista de consulta para o agente de radar de ferramentas; nada a instalar. Cada API listada tem regras próprias e algumas são pagas. |
| **Metodologia de análise de conteúdo** | Dissecar gancho, virada e fecho de conteúdos de referência (links fornecidos pelo utilizador, transcritos pelo pipeline existente). **Não** descarregar posts de redes sociais com contas pessoais: viola os termos das plataformas e arrisca bloqueio. |

## Avaliadas e não adoptadas

| Ferramenta | Razão |
|---|---|
| **AirLLM** | Sem caso de uso no setup; lenta, carrega o modelo por camadas. |
| **Amazon Chronos** | Previsão de séries temporais genérica, fora do âmbito de uma rede de agentes de negócio. |
| **Obscura** (navegador headless em Rust) | Projecto muito novo, binário de terceiros, anti-fingerprint com uso dual. Reabrir só com versão estável 1.x e um caso real de falha do Playwright. |
| **gstack** | Modo de equipa que se actualiza sozinho em silêncio, compila um binário e inclui um comando de cookies do navegador. Fica só como link de referência. |
| **LearnHarness** | App de estudo imatura (v0.6), instalador sem assinatura; os cursos continuam na skill `/teach`. |
| **Agency Agents** (e o fork do contains-studio) | Biblioteca de mais de 200 personas de agentes em texto. Instalar tudo duplica os agentes da rede e gasta contexto. Fica como **fonte de consulta** de prompts, nunca instalada em bloco. |
| **Ruflo** | Meta-harness de agentes em enxame; sobrepõe-se ao router e aos agentes da rede, e a regra do repo é não substituir os agentes com contexto real por templates genéricos. |
| **Vanna AI** | Repositório principal arquivado (só leitura) a 2026-03-29. A alternativa mantida é o Wren AI, nos opcionais. |
| **PlanExe** | Precisa de chave de um modelo pago (OpenRouter) ou de conta no serviço alojado, e o `planwright` já cobre o planeamento com Gantt (ver `PLANWRIGHT-2`). |
| **NotebookLM como memória externa** | Sobrepõe-se à memória em Supabase e enviaria o contexto das sessões (que pode incluir dados de clientes) para um serviço de terceiros. |
| **Cognee** | Sobrepõe-se à memória e ao RAG existentes e gastaria a quota do modelo sem ganho demonstrado. Reabrir só se a memória actual mostrar limites. |
| **LangGraph, CrewAI, PydanticAI** | Todos MIT e mantidos, mas a rede tem runtime próprio. Ficam como **referência** de desenho, sem dependência. |

## Como acrescentar uma ferramenta a este catálogo

1. Responder às quatro perguntas acima, **com sim/não**, e decidir na hora (instalar ou não). Não deixar "para avaliar".
2. Confirmar licença, custos e requisitos na fonte oficial, e citar a fonte.
3. Entrar sempre **desligada por omissão**, com os avisos de custo, licença e segurança na tabela.
4. Qualquer ferramenta que escreva em produção ou use contas pessoais precisa de decisão do maestro (regra 7 do `PENDENCIAS.md`).
