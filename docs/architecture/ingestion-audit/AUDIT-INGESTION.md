# AUDIT-INGESTION.md — Auditoria técnica profunda: Knowledge/Ingestion (Web, Documentos, GitHub, YouTube)

**Estado deste documento:** reescrita completa, padrão ouro (mesmo rigor das auditorias de
Governança/Memória/Agentes). A versão anterior era essencialmente metadados do GitHub
(estrelas/licença/actividade) recitados de uma fase anterior da auditoria de Agentes — não uma
auditoria de segurança nova. Esta versão tem: (0a) leitura completa do pipeline interno
(989 linhas, 5 ficheiros), (0b) estado real S9/S10, (1-5) verificação de segurança das ferramentas
de Web/Documentos com CVEs reais (muda 2 classificações), (5b) verificação de segurança das
ferramentas de GitHub/YouTube com CVEs reais (muda 1 classificação — gitingest), (6) uma correcção
concreta de código já identificada. Regra seguida em todas as secções: **toda alegação de
segurança está ligada a uma fonte primária (advisory GHSA/CVE, OSV.dev, ficheiro de código real)**
— o que não foi possível verificar está marcado **NOT VERIFIED**, nunca assumido.

## 0a. Estado interno real do pipeline (verificado por leitura completa de código, não por resumo de auditoria anterior)

Antes de qualquer ferramenta nova, o pipeline actual foi lido por inteiro nesta auditoria — `knowledge.py`, `mcp_knowledge.py`, `chunking.py`, `embedder.py`, `supabase_writer.py` (989 linhas ao todo) — para estabelecer uma baseline real, não recitada.

**O que está bem desenhado, confirmado por leitura, não por confiança:**
- `chunking.py` — chunking consciente de estrutura (secções H2/H3), com `_split_oversized`/`_merge_small` para respeitar limites de 200-600 tokens sem cortar no meio de parágrafos; usa `4 chars ≈ 1 token` como heurística (aproximação razoável para inglês/português, não confirmada contra um tokenizer real — risco baixo, não crítico).
- `mcp_knowledge.py` — tratamento de erro genuinamente cuidadoso: distingue `httpx.TimeoutException`/`httpx.HTTPError`/`BaseExceptionGroup` (o `anyio.TaskGroup` embrulha falhas de rede de forma não óbvia — o código documenta que isto foi confirmado com um teste real de ligação recusada, não assumido); documenta explicitamente a limitação do runner ser síncrono (`anyio.run()` para uma chamada assíncrona isolada) e avisa que isto quebraria se o runner alguma vez passasse a assíncrono.
- `supabase_writer.py` — todas as queries são parametrizadas (sem risco de SQL injection); `replace_chunks()` é atómico (`with conn:` envolve upsert+delete+insert numa única transação).

**Achados novos desta auditoria, por leitura directa:**
1. **O bloco `knowledge:` usado por `knowledge_wiring.py` (`kb`/`query`/`top_k`/`filters`) não está declarado em `docs/architecture/plan-execute/schemas/Plan.schema.json`** — confirmado por grep: o schema só tem `knowledge_refs` (campo diferente, de outro contexto, dentro de `brand`/`audience`/`constraints`). O bloco é lido via `step.raw.get("knowledge")`, um acesso a dict solto, **sem validação de schema nenhuma**. Um plano com `knowledge: {kb: 123}` (tipo errado) não seria apanhado por nenhuma validação antes de chegar a `knowledge_wiring.py` — que tem os seus próprios checks ad-hoc (`if not kb or not query`), mas isso não é o mesmo que um schema JSON validado no carregamento do plano.
2. **`embedder.py` passa a API key do Gemini como query parameter** (`params={"key": key}`) — ver secção 6 abaixo, com verificação directa na documentação oficial da Google.
3. **`mcp_knowledge.py` depende de `mcp==1.30.0` pinned exactamente**, por uma razão documentada no próprio código (mudança de `httpx` para `httpx2` nas versões 2.x do SDK oficial) — isto é uma dependência que precisa de vigilância activa: se o `requirements.txt` for actualizado sem se rever este comentário, o pin pode ser removido por engano.
4. **Sem RLS na tabela `knowledge_chunks_t6`** (`supabase_writer.py` não impõe isolamento nenhum ao nível do Postgres) — já registado em `security-audit-2026/AUDIT-SECURITY-2026.md`, não repetido em detalhe aqui, só referenciado porque é directamente relevante a quem for ligar novas fontes de ingestão a esta mesma tabela.

## 0b. Estado do S9 vs. S10 (não confundir — achado já registado, mantido aqui por completude)

`knowledge_wiring.py` (S10 — liga o L5 a `engine.py`) está **feito e funcional**, mas com adopção mínima (1 de 12 templates usa o bloco `knowledge:`). `hitl.py` (S9 — HITL) está **desligado** (zero chamadas de `engine.py`/`langgraph_engine.py`/`cli.py`). Detalhe completo em `meta-validation/AUDIT-META-VALIDATION.md` secção 2 e 7.

## 0. Contexto de ameaça (por que SSRF importa aqui)

O pipeline hoje (`chunking.py` → `embedder.py` → `supabase_writer.py`) só recebe Markdown já
escrito por alguém do repo — superfície de confiança alta. Assim que se liga ingestão Web, isso
muda: um agente (ex. o agente de marketing/SEO) vai tipicamente pedir para "ler este URL" onde o
URL pode vir de resultados de pesquisa, de um link dentro de uma página já raspada, ou de um
input de utilizador — nenhum destes é uma fonte de confiança total. **SSRF (o crawler a fazer um
pedido HTTP para `169.254.169.254`, `localhost`, ou um IP `10.x`/`172.16-31.x`/`192.168.x` interno
da própria rede onde o pipeline corre) é por isso o risco dominante desta secção**, não um detalhe
académico. As cinco ferramentas abaixo têm posturas muito diferentes perante isto — e, como se vê
em baixo, a diferença só aparece lendo advisories e código, nunca no README.

## 1. Crawl4AI (`unclecode/crawl4ai`)

| Alegação | Evidência (link) | Validado? |
|---|---|---|
| Tem protecção SSRF (bloqueio de IP privado/metadata) | [Proxy & Security docs](https://docs.crawl4ai.com/advanced/proxy-security/) | Parcial — existe, mas com histórico de bypass repetido (ver abaixo) |
| Respeita `robots.txt` por omissão | [`arun()` docs](https://docs.crawl4ai.com/api/arun/) | **Falso** — é opt-in via `check_robots_txt=True` em `CrawlerRunConfig`; se omitido, não há verificação nenhuma |
| Sem CVEs relevantes | busca directa em OSV.dev/GHSA | **Falso** — pelo menos 4 advisories críticos/altos em 2026, ver tabela abaixo |
| Playwright é a dependência de renderização JS | [PyPI crawl4ai](https://pypi.org/project/crawl4ai/) | Confirmado — "using Playwright for web crawling", instala Chromium headless completo via `crawl4ai-setup` |

**Histórico de CVEs (fonte primária, não segunda mão):**

| CVE / GHSA | Mecanismo | Versões afectadas | Corrigido em | Severidade |
|---|---|---|---|---|
| [GHSA-2jq4-q6vv-4cp3](https://github.com/advisories/GHSA-2jq4-q6vv-4cp3) | Path traversal → RCE: filename extraído do header `Content-Disposition` sem sanitização, escrito via `aiofiles.open()` em `async_crawler_strategy.py`; permite sobrescrever `~/.ssh`, cron, ficheiros de shell | ≤ 0.8.9 | 0.9.0 | **Crítico, CVSS 9.6** |
| [CVE-2026-53755](https://www.sentinelone.com/vulnerability-database/cve-2026-53755/) | SSRF via proxy: a API Docker valida o URL-alvo do crawl mas não valida `browser_config.proxy_config.server` — atacante aponta o proxy para IP interno/IMDS da cloud, o Chromium salta a validação | < 0.8.9 | 0.8.9 | **Alto, CVSS 8.6** |
| [CVE-2025-28197](https://www.miggo.io/vulnerability-database/cve/CVE-2025-28197) | SSRF nos endpoints `/crawl`, `/crawl/stream`, `/md`, `/llm` — fetch de URL arbitrário sem validação; bypass da blocklist via endereços IPv6-mapped-IPv4 | < 0.8.7 | 0.8.7 | Alto |
| [CVE-2026-91940](https://osv.dev/vulnerability/CVE-2026-91940) | `PDFContentScrapingStrategy._filter_untrusted_fields` não valida `image_save_dir` — escrita arbitrária de ficheiros | 0.9.0–0.9.2 | 0.9.3 | **Alto, CVSS v4 8.7** |

Padrão visível: **quatro variantes do mesmo tipo de falha (validação incompleta de input em fronteira de rede/ficheiro) em menos de 12 meses**, cada uma corrigida só depois de exploração demonstrada publicamente. A versão actual (0.9.3, lançada 31/08/2026) é descrita pelos próprios mantenedores como *"a security release closing five coordinated-disclosure advisories"* — ou seja, o projecto está activamente a fechar isto, mas a cadência de novos achados (o mais recente, CVE-2026-91940, é de 15/09/2026 — 4 dias antes de hoje) sugere que a superfície de ataque ainda não está esgotada.

**Classificação funcional:** ADOPT (condicional).
**Classificação de risco de segurança:** **ALTO** se exposto a URLs não confiáveis ou correndo como serviço Docker acessível; **MÉDIO** se usado só como biblioteca local (`arun()` chamado directamente pelo pipeline, sem o servidor Docker/API exposto) com pin de versão ≥0.9.3 e `check_robots_txt` activado explicitamente.

**Mitigação concreta se adoptado:**
1. Pin `crawl4ai>=0.9.3` — nunca instalar sem fixar o mínimo, dado o histórico.
2. **Não** expor o Docker/API server deste projecto num host acessível pela rede — usar sempre como biblioteca Python dentro do próprio processo do `runner`.
3. Activar `check_robots_txt=True` explicitamente (o omisso é "ignorar").
4. Correr atrás de um egress proxy/firewall que bloqueia IPs privados e o endpoint de metadata da cloud (`169.254.169.254`) — como defesa em profundidade independente do código do Crawl4AI, porque o histórico mostra que a validação interna já falhou 3 vezes.
5. Nunca aceitar `image_save_dir`/paths de configuração vindos de input externo sem validação própria adicional (a causa-raiz do CVE-2026-91940 era exactamente confiar num campo de config).

## 2. Firecrawl (`firecrawl/firecrawl`)

| Alegação | Evidência (link) | Validado? |
|---|---|---|
| Licença AGPL-3.0 no núcleo, SDKs MIT | [`LICENSE`](https://github.com/firecrawl/firecrawl/blob/main/LICENSE) lido directamente — "GNU AFFERO GENERAL PUBLIC LICENSE Version 3" | **Confirmado** |
| Tem protecção SSRF nativa | `safeFetch.ts`, checagem `isIPv4Private` no fetch | Confirmado que existe, mas historicamente incompleta (ver abaixo) |
| Uso comercial interno não-modificado é permitido sem obrigação de publicar código | análise de nuance AGPL (ver abaixo) | Confirmado com ressalva |

**Nuance AGPL-3.0 (a pergunta específica do pedido):** a cláusula de "network use" da AGPL-3.0
dispara quando se **modifica** o software e se **oferece essa versão modificada como serviço de
rede** a terceiros — nesse caso, o código modificado tem de ser disponibilizado. Correr o
Firecrawl **sem modificações**, self-hosted, como serviço interno chamado pela própria aplicação
(sem o expor como produto a terceiros), **não** obriga a aplicação chamadora a ficar AGPL — a
obrigação é sobre o próprio Firecrawl, não sobre quem o consome via API/rede. Ou seja: uso interno
sim, mas **se este repo alguma vez modificar o motor do Firecrawl e o expor a clientes externos do
`agent-network-mcp`, essa cópia modificada teria de ser publicada**. Recomenda-se confirmação
jurídica antes de qualquer modificação + exposição externa — a alegação da auditoria anterior
("AGPL impede uso comercial") estava a mais; a correcta é "AGPL impede *redistribuição fechada de
modificações servidas por rede*", que é uma barra mais baixa mas não zero.

**Histórico de SSRF (dois casos distintos, fonte primária):**

| Caso | Mecanismo | Versões | Corrigido | Fonte |
|---|---|---|---|---|
| [GHSA-vjp8-2wgg-p734](https://github.com/mendableai/firecrawl/security/advisories/GHSA-vjp8-2wgg-p734) | Redirect para IP local — site malicioso redireciona o scraper para endereço interno; CVSS 7.4 | < 1.1.1 | 1.1.1 (29/12/2024) — mantenedores recomendam **explicitamente** *"usar um proxy seguro configurado para bloquear tráfego IP link-local"* como mitigação adicional, mesmo depois do patch | Advisory oficial GitHub |
| [Issue #2070](https://github.com/firecrawl/firecrawl/issues/2070) | `isIPv4Private()` não reconhece o intervalo RFC1918 completo `172.16.0.0–172.31.255.255` como privado — bypass da checagem existente | Reportado 29/08/2025 | **Sem confirmação de fix visível na issue** (marcado open, sem resposta de mantenedor documentada no momento da verificação) | Issue directa no repo |

**Classificação funcional:** DEFER (mantém-se — infraestrutura de 4 serviços continua
desproporcional a um pipeline que hoje só sabe consumir Markdown).
**Classificação de risco de segurança:** **MÉDIO-ALTO** — tem protecção SSRF, mas com um
histórico de duas gerações de bypass (redirect-based e range-incompleto), e a própria Vidoc
Security Lab/mantenedores recomendam proxy externo como camada adicional — ou seja, mesmo o
projecto não confia inteiramente na sua própria checagem interna.

**Mitigação concreta se algum dia adoptado:** nunca confiar só no `isIPv4Private` interno —
colocar sempre atrás de um proxy de egress com allowlist/denylist de rede própria, exactamente
como o próprio advisory recomenda; e não modificar o motor sem rever a obrigação AGPL de
publicação se for exposto por rede.

## 3. MarkItDown (`microsoft/markitdown`)

| Alegação | Evidência (link) | Validado? |
|---|---|---|
| PDF via `pdfminer.six` | [Issue #1504](https://github.com/microsoft/markitdown/issues/1504) | Confirmado |
| Teve CVE de execução de código via PDF | CVE-2025-64512 | **Confirmado** — mas com processo de disclosure questionável (ver abaixo) |
| Tem protecção contra zip bomb no `ZipConverter`/EPUB | [Issue #1514](https://github.com/microsoft/markitdown/issues/1514) | **Falso — vulnerabilidade aberta, não corrigida** |
| XLSX via `openpyxl` tem histórico de XXE | [GHSA-chqf-hx79-gxc6](https://github.com/advisories/GHSA-chqf-hx79-gxc6) (CVE-2017-5992) | Confirmado, mas é de 2017, corrigido a montante desde openpyxl 2.4.2 — risco só se a versão vier fixada antiga |

**Detalhe do CVE-2025-64512:** `pdfminer.six` (dependência de que o parser de PDF do MarkItDown
depende directamente) tinha uma falha de execução de código arbitrário; o MarkItDown 0.1.3 herdava-a
por transitividade. Corrigido no MarkItDown 0.1.4, ao subir a versão fixada de `pdfminer.six` para
`20251107`. **Ponto relevante levantado no próprio issue #1504, ainda sem resposta de mantenedor
visível no momento da verificação:** a 0.1.4 foi publicada como release "menor"/de funcionalidades,
sem nenhum aviso de segurança formal — quem só lê changelogs (não CVE feeds) não saberia que
precisava de actualizar urgentemente. Isto é um sinal de processo, não só de código: **a auditoria
não pode confiar em "olhar o changelog" como sinal de que uma versão é segura para este pacote.**

**Zip bomb — vulnerabilidade real e ainda aberta:** o `ZipConverter` lê o conteúdo completo de
cada ficheiro dentro do ZIP via `zipObj.read(name)` **sem verificar `file_size` do `ZipInfo`
antes**, i.e. um ZIP de poucos KB que descomprime para gigabytes esgota a memória do processo.
Confirmado por leitura directa da issue #1514 (que descreve o mecanismo exacto no próprio código),
estado **open, sem milestone, sem PR associado** — não há indicação de que os mantenedores tenham
sequer triado isto. Isto cobre directamente a pergunta do pedido sobre EPUB/ZIP: **não há
protecção nenhuma hoje**, ao contrário do que a auditoria anterior tinha implicitamente assumido
ao listar MarkItDown como "ADOPT por omissão" sem verificar este ponto.

**Classificação funcional:** ADOPT (mantém-se — continua a ser a opção mais leve e mais completa
em formatos), **mas com mitigação obrigatória, não opcional.**
**Classificação de risco de segurança:** **MÉDIO** — sem RCE conhecida activa (a de PDF está
corrigida se a versão for actual), mas com um DoS de memória trivial de explorar (zip bomb) e sem
fix a caminho.

**Mitigação concreta:**
1. Pin `markitdown>=0.1.4` (nunca abaixo — CVE-2025-64512 continua explorável em <0.1.4).
2. **Não confiar no `ZipConverter`/handler de EPUB do MarkItDown para ficheiros de origem não
   confiável** — envolver a chamada num limite próprio: verificar `ZipInfo.file_size` de cada
   entrada e o tamanho total descomprimido *antes* de invocar o MarkItDown, rejeitando acima de um
   tecto (ex. 200MB), já que o próprio projecto não o faz.
3. Correr a conversão num processo/worker com limite de memória do SO (`ulimit`/cgroup) como rede
   de segurança adicional — barato e independente do código do MarkItDown.
4. Monitorizar `github.com/microsoft/markitdown/security` directamente (não só releases) antes de
   cada actualização de versão fixada, dado o precedente do CVE-2025-64512 não ter tido aviso
   formal claro.

## 4. Docling (IBM, `docling-project/docling`)

| Alegação | Evidência (link) | Validado? |
|---|---|---|
| Motor de PDF próprio, não PyMuPDF/pdfminer | [`pyproject.toml`](https://github.com/docling-project/docling/blob/main/pyproject.toml) lido directamente | **Confirmado** — `docling-parse>=7.20.0` (extra `format-pdf-docling`) é o backend por omissão; `pypdfium2` é a alternativa (extra `format-pdf-pypdfium2`); nem PyMuPDF nem pdfminer aparecem em nenhuma extra |
| Evitou PyMuPDF deliberadamente por causa da licença AGPL | Technical Report (arXiv 2408.09869) + issues de terceiros que confirmam PyMuPDF = AGPL-3.0 | Confirmado — motivo duplo: licença E qualidade/velocidade insuficientes nas alternativas |
| VLM (GraniteDocling) corre localmente, sem enviar dados para fora | [Vision Models docs](https://docling-project.github.io/docling/usage/vision_models/) | Confirmado — Transformers/MLX local por omissão; chamadas remotas só com `enable_remote_services=True` explícito (Ollama/LM Studio/cloud) |
| Sem CVEs relevantes | busca OSV.dev/GHSA | **Falso** — 1 CVE relevante encontrado, ver abaixo |

**CVE relevante:** [CVE-2026-24009](https://osv.dev/vulnerability/CVE-2026-24009) — RCE via
`PyYAML` insegura em `docling_core.types.doc.DoclingDocument.load_from_yaml()`: se a aplicação
chamadora invocar esta função com YAML **não confiável** e tiver PyYAML <5.4 disponível, o
carregamento usava `yaml.FullLoader` em vez de `yaml.SafeLoader`. Afecta `docling-core` (dependência
directa de `docling`) 2.21.0–2.48.3; corrigido em 2.48.4. **Nota de precisão:** existe também um
CVE-2026-40047/GHSA-rpv3-6645-2vqc no componente **Apache Camel `camel-docling`** — isso é uma
integração Java/Camel que invoca o binário `docling` via `ProcessBuilder` com argumentos não
validados; **não se aplica** a este pipeline (que usaria a biblioteca Python `docling` directamente,
não via Camel) — mas é um bom exemplo de como confundir "docling" com "qualquer projecto que use a
palavra docling" gera falsos positivos/negativos, por isso separado explicitamente aqui.

**Classificação funcional:** ADOPT (condicional — mantém-se, agora com evidência mais forte a
favor do que a auditoria anterior tinha).
**Classificação de risco de segurança:** **BAIXO-MÉDIO** — a escolha de motor de PDF próprio
(evitando o histórico de CVEs de `pdfminer.six` e a licença AGPL do PyMuPDF) e a execução 100%
local do VLM são pontos fortes reais, verificados em código; o único vector conhecido
(`load_from_yaml` com PyYAML antiga) só dispara se este pipeline algum dia desserializar YAML
vindo de fora sem controlo — o que hoje não é o caso (o pipeline consome Markdown/PDF, não YAML de
terceiros).

**Mitigação concreta:**
1. Pin `docling-core>=2.48.4` (fecha CVE-2026-24009).
2. Nunca chamar `DoclingDocument.load_from_yaml()` com YAML de origem externa não confiável, e se
   algum dia for necessário, confirmar que a versão instalada usa `SafeLoader`.
3. Preferir o backend por omissão (`docling-parse`) em vez de forçar `pypdfium2`, a menos que haja
   razão de performance — não muda o perfil de risco de forma relevante (ambos evitam PyMuPDF/AGPL
   e pdfminer/histórico de CVE), mas o `docling-parse` é o caminho mais testado pelo próprio
   projecto.
4. Manter `enable_remote_services=False` (omissão) — qualquer necessidade futura de VLM externo
   deve ser uma decisão explícita documentada, não um efeito colateral de configuração.

## 5. Trafilatura (`adbar/trafilatura`)

**Correcção importante ao pressuposto do pedido:** a premissa era que Trafilatura "não faz fetch,
só extrai texto de HTML já obtido" — **isto é só parcialmente verdade**, confirmado por leitura
directa de [`trafilatura/downloads.py`](https://github.com/adbar/trafilatura/blob/master/trafilatura/downloads.py):

| Alegação | Evidência (link) | Validado? |
|---|---|---|
| Só extrai texto, nunca faz pedidos de rede | leitura de `downloads.py` | **Falso, parcialmente** — o pacote **inclui** `fetch_url()`, `fetch_response()`, `is_live_page()`, que fazem pedidos HTTP reais via `urllib3` (ou `pycurl` se instalado); há ainda um módulo `spider.py` para crawling recursivo |
| Sem protecção SSRF | leitura directa de `downloads.py` | **Confirmado** — zero validação de IP privado/localhost/link-local, zero bloqueio de `file://`/`gopher://`; o único filtro é uma blacklist regex opcional (`add_to_compressed_dict`), configurável mas não activa por omissão |
| Sem verificação de `robots.txt` | leitura directa de `downloads.py` | **Confirmado** — nenhuma lógica de `robots.txt` na camada de download |

A afirmação correcta, então, é mais estreita do que a do pedido: **se este pipeline usar
Trafilatura apenas na função `extract()` sobre HTML que já chegou por outro canal (ex. resposta já
obtida por outra camada com as suas próprias validações), a superfície de risco é de facto quase
zero** — é um parser de texto puro, sem side effects de rede nessa função. **Mas se o pipeline
usar as funções de fetch/spider embutidas do próprio Trafilatura para ir buscar URLs, herda os
mesmos riscos de SSRF do Crawl4AI/Firecrawl, sem nenhuma das mitigações que esses dois têm (nem
robots.txt opt-in, nem checagem de IP privado nenhuma).** Isto é o oposto do que a pergunta
assumia implicitamente ("deve ser bem menor por não fazer rede") — o código mostra que a ferramenta
*pode* fazer rede, e quando o faz, é a menos protegida das três (Crawl4AI e Firecrawl pelo menos
tentam bloquear IP privado; Trafilatura não tenta nada).

**Classificação funcional:** ADOPT (mantém-se — como extractor puro sobre HTML já obtido).
**Classificação de risco de segurança:** **BAIXO se usado só como extractor** (função `extract()`
sobre conteúdo já obtido por outro meio) — **ALTO se usado para fazer o fetch dos URLs
directamente** (funções `fetch_url`/`fetch_response`/`spider`), porque não tem nenhuma das
protecções que as outras ferramentas desta lista pelo menos tentam ter.

**Mitigação concreta:** usar **exclusivamente** a função `extract()` de Trafilatura sobre HTML já
obtido por uma camada de fetch própria (ou pelo Crawl4AI, já com as suas mitigações aplicadas) —
**nunca** chamar `trafilatura.fetch_url()` directamente sobre um URL de origem não confiável sem
primeiro passar por validação de IP própria (allowlist de esquemas `http`/`https`, resolução DNS e
checagem contra intervalos privados/link-local/metadata antes do pedido).

## 5b. GitHub (gitingest) e YouTube (yt-dlp, faster-whisper, youtube-transcript-api)

Pesquisa dedicada, mesmo rigor (fontes primárias: OSV.dev, GitHub Advisory Database, issues reais, não estrelas/licença).

### gitingest (`coderamp-labs/gitingest`)

| Alegação | Evidência | Validado? |
|---|---|---|
| Clona via GitPython com `depth=1` (shallow), timeout de 60s (`@async_timeout`) | [`clone.py`](https://github.com/coderamp-labs/gitingest/blob/main/src/gitingest/clone.py), [`config.py`](https://github.com/coderamp-labs/gitingest/blob/main/src/gitingest/config.py) | Sim |
| Limites reais: `MAX_FILE_SIZE=10MB`, `MAX_TOTAL_SIZE_BYTES=500MB`, `MAX_FILES=10_000` | `config.py` | Sim, mas aplicam-se ao **digest de saída** — o `git clone` em si pode transferir mais dados para disco antes do timeout de 60s cortar, i.e. DoS local por disco continua teoricamente possível (limitado no tempo, não no espaço) |
| Só aceita URLs `http`/`https`, valida host contra padrão `github.*`/`gitlab.*`/`git.*` | `query_parser_utils.py` | Parcial — **NOT VERIFIED se é prefixo de string ou validação de domínio própria**; um domínio `github.attacker.com` poderia teoricamente passar se for `startswith`, não `endswith` de sufixo público. Requer confirmação manual literal do regex antes de expor a input não confiável |
| Sem telemetria escondida na lib core (`pip install gitingest`, sem extra `[server]`) | `pyproject.toml` — `posthog`/`sentry-sdk` só em `[project.optional-dependencies] server` | Confirmado |
| **Projecto activamente mantido** | **Refutado** — último commit visível 16/08/2025, último release PyPI 31/07/2025 (v0.3.1) — **>13 meses parado**, apesar de 15,5k estrelas | Confirmado, contradiz suposição de manutenção activa |
| **Vazamento de token de acesso (PAT) em logs/mensagens de erro ao clonar repos privados** | [Issue #605](https://github.com/coderamp-labs/gitingest/issues/605), aberta 08/09/2026, **sem resposta de maintainer, sem PR** | **Confirmado, crítico se usado com repos privados** — a redacção do URL falha em ocultar o header `Authorization: Basic <base64>` (reversível, não hash) |

**Classificação funcional: ADAPT com reservas** (revista de ADOPT — o projecto está órfão e tem uma issue de segurança real e aberta).
**Risco de segurança: MÉDIO.** **Risco operacional: ALTO** (>13 meses sem release, issue de segurança sem resposta).

**Mitigação se adoptado:** fixar `0.3.1` exacto; **nunca** usar para repos privados (token) enquanto #605 estiver aberta; confirmar manualmente o regex de validação de host antes de aceitar URLs de input não confiável; considerar EXTRACT (só a lógica de parsing/chunking, reimplementar o clone com `git sparse-checkout --filter=blob:none` internamente) em vez de depender de um projecto órfão para a parte que toca rede+subprocess.

### yt-dlp (já em uso no ecossistema, agora auditado a fundo em segurança)

Histórico real de CVEs, confirmado directamente no OSV.dev (16 entradas): CVE-2023-46121 (SSRF/MITM via injecção de proxy, CVSS 5.0), CVE-2024-38519 (RCE via sanitização insuficiente de extensão de ficheiro, CVSS 7.8, com **bypass documentado depois do fix**), CVE-2023-40581 (injecção via `--exec`+`%q` no Windows), **CVE-2026-26331 (injecção de comandos via `--netrc-cmd`, CVSS 8.8, corrigido em 2026.02.21)**, mais uma onda de advisories 2026 (RCE via manifests com `aria2c`, fuga de cookies via `curl` externo, bypass de `--exec`).

**Achado que importa para uso seguro:** todos os 16 CVEs exigem uma flag opcional perigosa (`--exec`, `--netrc-cmd`, downloader externo `aria2c`/`curl`) ou o Generic Extractor a processar um site malicioso — **nenhum atinge o uso "por omissão"** (download simples, sem essas flags).

**Classificação funcional: ADOPT** (mantém-se, já em uso). **Risco de segurança: MÉDIO** (ALTO se as flags perigosas forem usadas) — **BAIXO-MÉDIO com as mitigações abaixo. Risco operacional: ALTO por desenho** (releases muito frequentes por causa de mudanças no YouTube — não é instabilidade, é o modelo do projecto).

**Mitigação obrigatória em modo automatizado:** `--no-config` sempre (impede leitura de `yt-dlp.conf` malicioso plantado no directório); nunca `--exec`/`--netrc-cmd`; nunca downloader externo; `--ies youtube` para desactivar o Generic Extractor (elimina a classe CVE-2023-46121); pinning de versão + Dependabot/Renovate dado o ritmo de patches.

### faster-whisper (já em uso)

Confirmado: **10 meses sem commit é real e ainda válido** (último commit 19/11/2025, hoje 19/09/2026) — não é achado desactualizado de auditoria anterior, é estado actual confirmado de novo. Zero CVEs conhecidos (faster-whisper e CTranslate2, verificado em OSV.dev/GHSA), mas isso é ausência de evidência, não prova de ausência — CTranslate2 é C++ compilado (parsing de modelo binário), superfície de memory-safety diferente, não auditada publicamente por nenhuma fonte encontrada. Exposição prática baixa porque o modelo usado é fixo (Whisper pré-treinado), não fornecido por utilizador não confiável.

**Classificação: ADAPT (mantém-se). Risco de segurança: BAIXO-MÉDIO. Risco operacional: MÉDIO-ALTO** (estagnação confirmada, sem melhoria). **Mitigação:** vigilância activa de releases/CVE + plano B documentado (`whisper.cpp` ou `openai/whisper` oficial).

### youtube-transcript-api

Achado novo e concreto: [issue #592](https://github.com/jdepoix/youtube-transcript-api/issues/592) (aberta 25/04/2026) documenta que o sistema "PoToken" do YouTube (2025-2026) quebrou a extracção para um subconjunto de vídeos **sem workaround conhecido** — diferente do padrão histórico "quebra e corrige-se em dias". Múltiplas issues sem resolução completa ao longo de 2026.

**Classificação: DEFER para uso como caminho crítico único** (mantém-se ADAPT como optimização best-effort). **Risco de segurança: BAIXO. Risco operacional: ALTO e a piorar.** **Mitigação:** nunca usar como método único — a arquitectura já existente (`yt-dlp`+`faster-whisper`) já contorna esta fragilidade por completo, por não depender de legendas oficiais nem do scraping do frontend.

## 6. A pergunta lateral: Gemini API key em query parameter

Confirmado no código deste repo (`runner/plan_runner/embedder.py`, linha 79):
`httpx.post(GEMINI_URL, params={"key": key}, ...)`.

| Alegação | Evidência (link) | Validado? |
|---|---|---|
| A API do Gemini aceita autenticação por header em vez de query param | [`ai.google.dev/gemini-api/docs/api-key`](https://ai.google.dev/gemini-api/docs/api-key) — a própria página oficial mostra um exemplo REST usando `x-goog-api-key: YOUR_API_KEY` | **Confirmado — existe alternativa por header, suportada pela própria Google** |
| A documentação oficial da Google recomenda explicitamente o header em vez do query param, citando risco de logs | leitura directa da página oficial | **NOT VERIFIED** — a página mostra o header como uma forma de autenticação válida (um dos exemplos), mas não encontrei, na própria página, uma frase explícita a desaconselhar `?key=` por risco de logs; essa recomendação explícita aparece em fontes secundárias/blogs de terceiros, não na doc primária lida |
| Risco genérico de query params (logs de proxy, browser history, ficheiros de acesso de servidor) é reconhecido na indústria em geral | [Google Cloud — Best practices for managing API keys](https://docs.cloud.google.com/docs/authentication/api-keys-best-practices) | Confirmado como prática geral de segurança de API keys (não específico ao Gemini) |

**Conclusão sobre este ponto:** a alternativa por header (`x-goog-api-key`) existe e é suportada —
`embedder.py` pode ser alterado para usar `headers={"x-goog-api-key": key}` em vez de
`params={"key": key}` sem mudança de comportamento, eliminando o risco real (a key aparecer em
logs de acesso HTTP de qualquer proxy/CDN/load balancer entre o pipeline e a Google, e em
ferramentas de tracing de rede que redigem headers mas não query strings por omissão). Não
encontrei uma frase explícita da Google a dizer "não uses query param por causa disto" na
documentação primária — por isso a motivação é catalogada aqui como boa prática geral de segurança
de HTTP (OWASP: não colocar segredos em URLs), não como correcção de uma falha documentada pela
própria Google. Isto é ainda assim suficiente para justificar a mudança, dado o custo de a fazer
ser praticamente zero.

> **RESOLVIDO em 2026-09-19 — `embedder.py` passa a enviar a key via header `x-goog-api-key` (era `params={'key': key}`). Confirmado com chamada real contra a API Gemini (768 dimensões). Testes unitários actualizados (8/8). Suite completa do runner: 172/172 passou, 0 regressões. Ver `EXECUTION-PROMPTS.md` A7.**

## Recomendação mínima revista

| Área | Ferramenta | Classificação funcional | Risco de segurança |
|---|---|---|---|
| Web (crawl) | Crawl4AI, pin ≥0.9.3, `check_robots_txt=True`, nunca expor o servidor Docker | ADOPT condicional | Médio (biblioteca local, versão actual) / Alto (servidor exposto ou versão antiga) |
| Web (extracção de texto) | Trafilatura, só a função `extract()` sobre HTML já obtido | ADOPT | Baixo (uso restrito) / Alto (se usado para fetch) |
| Documentos (omissão) | MarkItDown ≥0.1.4, com limite de tamanho próprio antes de qualquer ZIP/EPUB | ADOPT com mitigação obrigatória | Médio (zip bomb sem fix a montante) |
| Documentos (tabelas em PDF) | Docling, `docling-core`≥2.48.4 | ADOPT condicional | Baixo-Médio |
| Web (crawl com anti-bot difícil) | Firecrawl | DEFER | Médio-Alto (infra + histórico SSRF) |
| GitHub (código) | gitingest, pin `0.3.1`, só repos públicos | **ADAPT com reservas** (revisto de ADOPT — projecto órfão >13 meses, issue de segurança aberta) | Médio (segurança) / **Alto (operacional — sem manutenção activa)** |
| YouTube (download+transcrição) | yt-dlp + faster-whisper, com `--no-config`/sem `--exec`/sem downloader externo | ADOPT (já em uso) | Médio→Baixo-Médio com mitigação / Alto operacional (yt-dlp, por desenho) |
| YouTube (legendas, optimização opcional) | youtube-transcript-api, só best-effort com fallback | DEFER como caminho crítico | Baixo segurança / Alto operacional (PoToken sem workaround para subconjunto de vídeos) |

Nenhuma das ferramentas deve ser adoptada "por omissão total" sem as mitigações listadas
secção a secção acima — a diferença desta auditoria para a anterior não é a lista de ferramentas
(mantém-se quase igual), é que **agora cada uma vem com uma mitigação específica derivada de um
CVE/advisory real**, não uma nota genérica de "correr com cuidado" — e pelo menos uma classificação
mudou de facto (gitingest: ADOPT → ADAPT com reservas, por ter sido encontrado órfão com uma
vulnerabilidade real aberta, não por ter sido "revisto por rever").

Alteração concreta recomendada ao `embedder.py`: trocar `params={"key": key}` por
`headers={"x-goog-api-key": key}` — mudança de uma linha, sem risco de regressão, remove a key dos
logs de qualquer camada HTTP intermédia.

## O que NÃO adoptar

- **Firecrawl como omissão** — mantém-se a razão da auditoria anterior (infra desproporcional),
  reforçada agora por dois SSRF históricos e uma recomendação dos próprios mantenedores para pôr
  um proxy externo à frente porque não confiam inteiramente na própria checagem.
- **Trafilatura para fazer fetch de URLs directamente** — só para extracção sobre conteúdo já
  obtido; usá-lo como crawler herda todo o risco de SSRF sem nenhuma das mitigações que Crawl4AI
  pelo menos tem (mesmo que imperfeitas).
- **Qualquer versão de Crawl4AI <0.9.3** — três CVEs de alta/crítica severidade cobertos só até
  essa versão.
- **MarkItDown para processar ZIP/EPUB de origem não confiável sem limite de tamanho próprio** —
  vulnerabilidade de zip bomb confirmada e aberta, sem PR em curso.
- **`DoclingDocument.load_from_yaml()` sobre YAML de origem externa** sem confirmar
  `docling-core>=2.48.4`.
- **Unstructured, LlamaIndex/LangChain como dependência wholesale** — mantém-se a razão da
  auditoria anterior (peso desproporcional a 2-3 readers necessários); não foi reavaliado a fundo
  nesta ronda por não ter sido pedido, fica como **NOT VERIFIED** para uma futura auditoria se
  vier a ser candidato real.
- **gitingest com token de acesso para repositórios privados** — issue #605 aberta, vazamento
  confirmado, sem fix nem resposta de maintainer há mais de 1 ano de inactividade do projecto.
- **yt-dlp com `--exec`, `--netrc-cmd`, ou downloaders externos (`aria2c`/`curl`)** em qualquer
  contexto automatizado/não supervisionado — são exactamente os vectores dos CVEs reais mais
  graves encontrados (CVSS até 8.8).
- **youtube-transcript-api como único mecanismo de transcrição** — histórico activo de quebras
  por "PoToken" em 2026 sem workaround conhecido para um subconjunto de vídeos.

## Referências primárias usadas (não secundárias)

- Advisories GitHub: GHSA-2jq4-q6vv-4cp3, GHSA-vjp8-2wgg-p734, GHSA-chqf-hx79-gxc6
- OSV.dev: CVE-2026-91940, CVE-2026-24009
- CVSS/analyses técnicas: SentinelOne (CVE-2026-53755), Miggo (CVE-2025-28197)
- Ficheiros de código lidos directamente: `docling/pyproject.toml` (GitHub raw),
  `trafilatura/downloads.py` (GitHub), `firecrawl/LICENSE` (GitHub raw), `embedder.py` (este repo)
- Issues primárias (não triadas/sem fix confirmado, tratadas como tal): microsoft/markitdown#1504,
  microsoft/markitdown#1514, firecrawl/firecrawl#2070
- Documentação oficial: `ai.google.dev/gemini-api/docs/api-key`, `docs.crawl4ai.com`,
  `docling-project.github.io/docling`
