# MCP Mapping — 33 agentes (`agent-network-mcp`)

Mapeamento dos 33 agentes de `lib/agents.js`, por 3 eixos: **amplitude** (horizontal/vertical), **privacidade** (genérico/proprietário) e **origem** (processo/conhecimento). Objectivo: decidir o que vai para o setup público, o que fica no MCP, e o que dividir.

*(Ver também `docs/architecture/CORE-MAPPING.md` — mapeamento diferente, dos 39 ficheiros `.ts` de `packages/core/src/`. Os dois "39"/"33" não se referem à mesma coisa; não confundir os dois documentos.)*

## 1. Resumo

33 agentes, em **6 categorias**:

| Categoria | Quantos | Onde vão |
|---|---|---|
| Horizontal + genérico (inclui 7 "de processo") | 13 | Setup (com limpeza) |
| Vertical + genérico, com ingestão | 5 | Setup (migrar) |
| Vertical + genérico, casca (razão não documentada) | 3 | Futuro (ingerir) |
| Vertical, casca por design (privacidade mista) | 2 | MCP (manter) |
| Vertical + proprietário | 10 | MCP 🔒 |
| Mistos | 2 | Setup + MCP (dividir) |

*(G5: "Vertical + proprietário" corrigido de 9 para 10 — faltava `apps-produto`. "Vertical + genérico, casca por design" renomeado para "Vertical, casca por design (privacidade mista)" — tinha 1 agente proprietário (`hvac`) e 1 misto (`refrigeracao-hvac`), nunca foi "genérico" para os dois.)*

Os 7 "de processo" **não são um grupo à parte** — são o subconjunto de "Horizontal + genérico" cuja origem provável é um repo público (ECC/superpowers) em vez de processo desenhado de raiz. Contam uma vez só, dentro dos 13.

## 2. Tabela completa (33 agentes)

| Nome | Domínio | O que faz | Horizontal/Vertical | Privacidade | Origem |
|---|---|---|---|---|---|
| mesaflow | produto/tech | SaaS de gestão de restaurantes (NestJS/Prisma) | Vertical | Proprietário | Conhecimento |
| viannalegal | legal | Site de cidadania portuguesa para brasileiros | Vertical | Proprietário | Conhecimento |
| sst | segurança no trabalho | Consultoria SST Portugal | Vertical | Proprietário | Conhecimento |
| construtora | construção | TermoBuild (ICF, IMPIC) | Vertical | Proprietário | Conhecimento |
| hvac | climatização | TermoExpert (AC, bombas de calor, F-Gas) | Vertical | Proprietário | Casca por design |
| pladur | construção | Drywall/pladur | Vertical | Proprietário | Conhecimento |
| reformas | construção | Forma (renovações) | Vertical | Proprietário | Conhecimento |
| direito-br-pt | legal | Jurídico BR-PT (contratos, sucessões) | Vertical | Genérico | Conhecimento |
| canidelo | imobiliário | Vendas de apartamento (Canidelo) | Vertical | Proprietário | Conhecimento |
| apps-produto | produto/tech | Coordenação de apps (MesaFlow, Alivia) | Vertical | Proprietário | Conhecimento |
| investimentos-brasil | finanças | Investimentos B3 | Vertical | Genérico | Casca (razão não documentada) |
| gestao-empresarial | gestão | Visão estratégica do portefólio | Horizontal | Genérico (limpar) | Processo |
| contabilidade | contabilidade | Apoio contabilístico PT+BR | Horizontal | Genérico (limpar) | Conhecimento |
| design | design | Identidade visual transversal | Horizontal | Genérico (limpar) | Processo |
| cursos-formacoes | educação | Plataforma de cursos | Vertical | Proprietário | Conhecimento |
| imobiliario-digital | imobiliário | Análise de mercado (FipeZap, Apify) | Vertical | Misto | Conhecimento |
| engenharia-civil-arquitetura | engenharia | Eurocódigos + NBR | Vertical | Genérico | Casca (razão não documentada) |
| engenharia-eletrica-hidraulica | engenharia | Dimensionamento eléctrico/hidráulico | Vertical | Genérico | Casca (razão não documentada) |
| refrigeracao-hvac | engenharia | Refrigeração/HVAC (ISO, ASHRAE) | Vertical | Misto | Casca por design |
| eletrodomesticos | manutenção | Reparação de eletrodomésticos | Vertical | Proprietário | Conhecimento |
| cardiologia | saúde | AHA/ACC (diretrizes) | Vertical | Genérico | Conhecimento |
| dermatologia | saúde | AAD (critérios) | Vertical | Genérico | Conhecimento |
| oftalmologia | saúde | NIH (guias) | Vertical | Genérico | Conhecimento |
| revisor-codigo | engenharia | Revisão de segurança/qualidade | Horizontal | Genérico | Processo |
| qualidade-dados | engenharia | Revisão PostgreSQL | Horizontal | Genérico | Processo |
| guia-tdd | engenharia | TDD (red-green-refactor) | Horizontal | Genérico | Processo |
| arquitetura-agentes | meta | Custo LLM, MCP, GitHub Actions | Horizontal | Genérico | Processo |
| planejador | meta | Quebra pedidos em planos | Horizontal | Genérico | Processo |
| desenvolvimento | engenharia | Implementa código | Horizontal | Genérico | Processo |
| marketing | marketing | Copy, SEO, posicionamento | Horizontal | Genérico | Processo |
| comunicacoes-atendimento | atendimento | Triagem de clientes | Horizontal | Genérico | Processo |
| produto-tech-transversal | produto/tech | A11y, SEO, UX | Horizontal | Genérico | Processo |
| radar-ferramentas | meta | Memória de ferramentas | Horizontal | Genérico | Processo |

## 3. As 6 categorias (detalhe)

### 3.1 Horizontal + genérico (13) — inclui os 7 "de processo"

**Vão para o setup.** Precisam de limpeza (tirar nomes de clientes/negócios).

| Agente | Termo privado a tirar | Subgrupo |
|---|---|---|
| gestao-empresarial | lista nominal de 9 negócios | — |
| contabilidade | "LRNSdigital" | — |
| design | lista de negócios + "Canva ligado" | — |
| comunicacoes-atendimento | lista de negócios | — |
| produto-tech-transversal | "vianna-gestao", "MesaFlow", "Alivia" | — |
| marketing | já tem a regra certa ("não inventes dados") | — |
| radar-ferramentas | "tabela tool_evaluations", "Orca/node-pty" | de processo |
| planejador | "rede LRNSdigital", "Luiz" | de processo |
| desenvolvimento | idem | de processo |
| revisor-codigo | idem | de processo |
| qualidade-dados | idem | de processo |
| guia-tdd | idem | de processo |
| arquitetura-agentes | lista de projectos Vercel | de processo |

### 3.2 Vertical + genérico, com ingestão (5)

**Vão para o setup.** Já têm conteúdo substantivo.

> **Achado G6 (2026-09-20, durante C7, não corrigido — ver `STATUS.md` G6):** `imobiliario-digital` está listado aqui como "genérico", mas a tabela principal (secção 2) e a secção 3.6 classificam-no como **Misto** — e é dual-listado (também aparece em 3.6), ao contrário dos outros 32 agentes. Ao contrário do `refrigeracao-hvac` (o outro Misto, também dual-listado), esta linha não tem uma nota "(ver 3.6)" a sinalizar que é intencional. Decisão humana pendente: a parte pública dele conta para "setup, agora" (aqui) ou "depois, dividir" (secção 6)? Não pode ser as duas.

| Agente | Conteúdo embutido | Fonte |
|---|---|---|
| cardiologia | Limiares troponina, janelas repetição | AHA/ACC 2021/2025 |
| dermatologia | Critério ABCDE, ugly duckling | AAD |
| oftalmologia | Mecanismo descolamento, triagem | NIH |
| direito-br-pt | Regimes bens, usucapião | CC brasileiro |
| imobiliario-digital | FipeZap, Apify | FipeZap (público) |

### 3.3 Vertical + genérico, casca (razão não documentada) — 3

**Não vão agora.** Falta ingerir as normas — e não há, no texto destes 3 agentes, nenhuma frase equivalente à do `refrigeracao-hvac` ("consultar via RAG") que explique a ausência de conteúdo como intencional. Por isso "razão não documentada", não "descuido": não há evidência no ficheiro para afirmar nenhuma das duas coisas.

| Agente | O que falta |
|---|---|
| engenharia-civil-arquitetura | Ingerir Eurocódigos + NBR |
| engenharia-eletrica-hidraulica | Ingerir normas |
| investimentos-brasil | Ingerir dados B3 |

### 3.4 Vertical, casca por design — 2 (privacidade varia por agente)

**Ficam no MCP.** São roteamento/triagem, não conteúdo — e o texto de ambos diz isso explicitamente. *Correcção G5: esta secção chamava-se "Vertical + genérico", mas isso estava errado para o `hvac` — a coluna Privacidade da tabela principal já dizia "Proprietário" para ele, e o texto confirma (nomeia "TermoExpert", geografia e marca reais). A secção agora reflecte a privacidade real de cada um, em vez de assumir "genérico" para os dois.*

| Agente | Privacidade | Porquê |
|---|---|---|
| hvac (comercial) | **Proprietário** | Tem uma "matriz de roteamento" explícita — decide orçamento/triagem, encaminha o resto. Nomeia negócio real (TermoExpert) e contexto real (Porto/Gaia, identidade visual) |
| refrigeracao-hvac | Misto (ver 3.6) | Diz explicitamente "consultar via RAG" — sabe onde procurar, não tem o valor; e espera know-how humano ainda não capturado |

### 3.5 Vertical + proprietário — 10

**Ficam no MCP.** Têm dado privado.

mesaflow, viannalegal, sst, construtora, pladur, reformas, canidelo, cursos-formacoes, eletrodomesticos, **apps-produto**.

*(Correcção G5: `apps-produto` estava ausente desta lista — não constava em nenhuma das 6 secções de detalhe, só na tabela principal. Confirmado por leitura do texto em `lib/agents.js`: nomeia produtos reais (MesaFlow, Alivia), preço real (R$34,90), contagem real de ecrãs de protótipo — é proprietário sem ambiguidade.)*

### 3.6 Mistos — 2

**Dividir.** A parte pública vai para o setup; a privada fica no MCP.

| Agente | Parte pública | Parte privada |
|---|---|---|
| refrigeracao-hvac | Normas (ISO, ASHRAE) | Know-how prático |
| imobiliario-digital | FipeZap (público) | Produto a construir |

## 4. Blocos genéricos extraíveis (17)

Técnicas presas dentro de agentes verticais que podem virar skills horizontais.

| # | Técnica | Onde está presa | Vira skill? |
|---|---|---|---|
| 1 | Objetivo→Plano→Teste→Execução→Revisão→Evidência | 3 agentes | ✅ (1 skill) |
| 2 | Padrões Prisma | mesaflow | ✅ |
| 3 | Estrutura NestJS | mesaflow | ✅ |
| 4 | React (derive state, waterfalls) | mesaflow, viannalegal | ✅ |
| 5 | Design de API REST | mesaflow | ✅ |
| 6 | Tratamento de erros (fail fast) | mesaflow | ✅ |
| 7 | Checklist SEO técnico | viannalegal | ✅ |
| 8 | A11y de frontend | viannalegal | ✅ |
| 9 | Padrão Vite env vars | viannalegal | ✅ |
| 10 | Escrita de artigos | viannalegal | ✅ |
| 11 | Fórmula de posicionamento | apps-produto | ❌ (já existe no `marketing`) |
| 12 | Padrões React Native/Expo | apps-produto | ✅ |
| 13 | Classificar dado de saúde (PHI) | apps-produto | ✅ |
| 14 | Padrões Python | refrigeracao-hvac | ✅ |
| 15 | Disciplina de deploy | arquitetura-agentes | ✅ |
| 16 | Padrões MCP (Zod, idempotência) | arquitetura-agentes | ✅ |
| 17 | Operação GitHub Actions | arquitetura-agentes | ✅ |

**16 skills novas** (17 técnicas − #11, que já existe no `marketing`).

## 5. Achados críticos

- **`refrigeracao-hvac`** diz explicitamente: *"consultar via RAG antes de apresentar valores como definitivos"* — sabe onde procurar, não sabe o valor.
- **`cardiologia`** tem o número embutido: *"repetir entre 1-2h ou 3-6h"* — responde sem consultar.
- **A diferença:** *"sei o número"* vs. *"sei onde procurar o número"*.
- **`refrigeracao-hvac`** é duplamente vazio: não tem valores (manda consultar ISO) e não tem know-how (espera que o utilizador o dê).

## 6. Implicação para o setup

### O que vem para o setup (agora) — 34 items

| Categoria | Quantos |
|---|---|
| Horizontal + genérico (já inclui os 7 de processo) | 13 |
| Vertical + genérico, com ingestão | 5 |
| Blocos extraíveis (skills novas) | 16 |
| **Total** | **34** |

### O que fica no MCP

| Categoria | Quantos |
|---|---|
| Vertical + proprietário | 10 |
| Casca por design (privacidade mista, ver 3.4) | 2 |

**Total: 12 agentes.** *(G5: era 11 — faltava `apps-produto` na contagem de proprietários.)*

### O que fica para depois

| Categoria | Quantos | O que falta |
|---|---|---|
| Casca (razão não documentada) | 3 | Ingerir normas |
| Mistos (parte pública) | 2 | Dividir |

**Total: 5 items.**

## 7. Ferramentas horizontais (já existentes)

| Ferramenta | Onde vive | Estado |
|---|---|---|
| Transcrição (`yt-dlp` + `faster-whisper base`) | MCP (`.github/workflows/transcribe.yml`) | ✅ Funciona |
| Resultado | Supabase (`transcripts`) | ✅ Guardado |
| Análise de transcrições | Manual (na cabeça) | ✅ Formalizada (`transcript_analysis`) |
| Orquestração do disparo | Manual (`bash_tool` + `curl`) | ❌ Não formalizada |

**Skills já criadas** (não recriar): `transcript_analysis`, `content_analyst` (agente). **Skill em falta**: `transcript` (disparo da transcrição).

---

*Mapeamento produzido por leitura directa do `lib/agents.js` (33 agentes confirmados).
Análise por 3 eixos: amplitude, privacidade, origem.
Correcções aplicadas sobre o rascunho: contagem de 3.1 (13, não 12), 7 "de processo" marcado como subconjunto de 3.1 (não grupo adicional), Secção 4 com 17 técnicas (não 16), "16 skills novas" (não 15), e reclassificação dos 3 "casca por descuido" para "casca (razão não documentada)".*
