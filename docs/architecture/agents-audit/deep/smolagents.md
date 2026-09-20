# smolagents (Hugging Face) — auditoria profunda

Repositório: https://github.com/huggingface/smolagents. Evidência de leitura direta de `pyproject.toml`, `src/smolagents/agents.py`, `local_python_executor.py`, `remote_executors.py`, `models.py`, `default_tools.py`, `SECURITY.md`.

## Tabela de capacidades

| Capacidade | O que o projeto alega | Evidência verificada (link) | Validado? |
|---|---|---|---|
| Identidade/proveniência | Mantido pela Hugging Face, "barebones library for agents that think in code" | Maintainers confirmados (Aymeric Roucher, Albert Villanova, Thomas Wolf, Leandro von Werra, Erik Kaunismäki); repo criado 2024-12-05 | Sim |
| Uso interno pela HF em produção | Implícito no marketing | Único uso interno confirmado: [Open Deep Research](https://github.com/huggingface/smolagents/tree/main/examples/open_deep_research), réplica do Deep Research da OpenAI, #1 entre submissões abertas no GAIA (55% pass@1 vs 67% do original) — mas é um exemplo em `examples/`, não evidência de uso em infra crítica | **Parcial** — showcase, não "produção crítica" |
| CodeAgent vs ToolCallingAgent | CodeAgent gera e executa código Python em vez de JSON de tool-calling | `src/smolagents/agents.py`: `CodeAgent` faz parse por regex do código gerado e executa via `LocalPythonExecutor`/executor remoto; `ToolCallingAgent` usa `model.get_tool_call()` nativo com execução paralela via `ThreadPoolExecutor`; ambos herdam de `MultiStepAgent` (loop ReAct) | Sim |
| "CodeAgent > tool calling JSON" (30% menos passos) | "uses 30% fewer steps... higher performance" | Cifra vem do paper externo **CodeAct** (Wang et al., ICML 2024, arXiv 2402.01030), citado no [blog oficial](https://huggingface.co/blog/smolagents) junto com mais 2 papers — o blog não reproduz esse benchmark com o próprio smolagents | **Parcial/enganoso** — marketing apoiado em papers de terceiros, não medição própria |
| Multi-agente / hierarquia | "multi-agent hierarchies" via `managed_agents` | `_setup_managed_agents()` regista cada agente filho como entrada em `self.managed_agents`, exposto ao pai **como se fosse uma tool** | Sim — recursão de "agente-como-tool", não protocolo de orquestração separado |
| Planning explícito | Task decomposition explícito | `planning_interval`, `_generate_planning_step()`, templates `initial_plan`/`update_plan_pre_messages`/`update_plan_post_messages` — plano inicial + replaneamento periódico | Sim |
| Runtime/execution engine | Implícito como robusto | Loop simples `while not returned_final_answer and step <= max_steps` (gerador `_run_stream`); **sem state machine**, **sem checkpoint/resume** (memória em `AgentMemory` em processo, não persiste entre runs), **sem retry/timeout** ao nível do framework; HITL limitado a `interrupt_switch`/`interrupt()` (parar, não pausar-e-retomar) e `final_answer_checks` | Sim — confirma loop simples, sem persistência |
| Sandbox do `LocalPythonExecutor` | Segurança "by design" via whitelist | `local_python_executor.py`: interpretador AST por **whitelist de nós**, bloqueia módulos (`os`, `subprocess`, `socket`, `sys`, `io`, `multiprocessing`, `pathlib`, `shutil`, `pty`, `builtins`) e funções perigosas (`eval`, `exec`, `os.system`, `os.popen`); módulos autorizados por omissão são poucos (`collections`, `datetime`, `itertools`, `math`, `queue`, `random`, `re`, `stat`, `statistics`, `time`, `unicodedata` — sem `requests`/`urllib`) | Sim, mas ver risco abaixo |
| "LocalPythonExecutor não é fronteira de segurança" | Admitido pelo próprio projeto | Docstring literal: **"It is not a security sandbox: for isolated execution of untrusted code, use a remote executor."** Reafirmado em `SECURITY.md`: escapes do executor local são explicitamente **out-of-scope** para reports de vulnerabilidade | Sim — admissão explícita e rara |
| Sandboxing real (E2B/Docker/Modal/Blaxel) | "secure sandboxed environments" | `remote_executors.py`: E2B = microVM cloud; Docker = container + Jupyter Kernel Gateway via WebSocket; Modal = sandbox cloud com túnel `wss://`; Blaxel = VM com hibernação. Aviso repetido: risco de deserialização de pickle | Sim, mecanismo real |
| Isolamento de rede nos sandboxes "seguros" | Implícito como "seguro" = isolado | **Nenhum dos 4 backends bloqueia rede por omissão de forma documentada no código.** E2B tem internet ativa por omissão salvo configuração explícita; Docker herda rede de bridge por omissão | **Não validado / risco real** — protege processo/filesystem, não necessariamente exfiltração via rede |
| Rede via tools nativas, mesmo em execução local | — | `default_tools.py` regista `DuckDuckGoSearchTool`, `GoogleSearchTool`, `ApiWebSearchTool`, `WebSearchTool`, `VisitWebpageTool`, `WikipediaSearchTool` — todas fazem HTTP real, fora do escopo da whitelist de AST | Sim — nuance importante |
| "Smol" (núcleo em ~1000 linhas) | "the logic for agents fits in ~1,000 lines of code" | Não contra-verificado linha a linha; `agents.py` sozinho, pela quantidade de mecanismos confirmados, é plausivelmente maior; repo tem 7.4MB e 163 contribuidores desde dez/2024 | **Não verificado com rigor** — plausível para o loop central, enganoso para o projeto inteiro |
| Maturidade | Ativo e popular | API GitHub: 29.390 estrelas, 2.975 forks, 818 issues abertas, 163 contribuidores, último push 2026-08-25, Apache-2.0 | Sim |
| Concentração de manutenção | — | Top-2 contribuidores (`albertvillanova`, `aymeric-roucher`) somam 677 de todas as contribuições — concentração alta, risco de bus factor | Sim (achado) |
| SECURITY.md / licença | Apache 2.0, uso comercial | `SECURITY.md` real, processo de disclosure privado, âmbito claro (escapes de sandbox = in-scope; escape do executor local = out-of-scope) | Sim |
| Operação local / agnóstico a provider | "any LLM — local, Hub, OpenAI, Anthropic..." | `models.py`: `TransformersModel`, `MLXModel`, `VLLMModel` (100% locais), `LiteLLMModel`/`LiteLLMRouterModel`, `OpenAIModel`, `AzureOpenAIModel`, `AmazonBedrockModel`; `InferenceClientModel` é a única classe dependente de infra HF, não é default forçado | Sim — agnosticismo real |

## Padrões extraíveis

1. **Interpretador Python por AST-whitelist** (`local_python_executor.py`) — em vez de blacklist, percorre a árvore AST e só executa tipos de nó explicitamente suportados, com `DANGEROUS_MODULES`/`DANGEROUS_FUNCTIONS` e `check_import_authorized()`. Primeira camada de defesa barata para executar "código gerado por LLM com risco moderado" — não substitui sandbox real.
2. **Abstração de múltiplos executores atrás de uma interface comum** (`remote_executors.py`) — `LocalPythonExecutor`/`E2BExecutor`/`DockerExecutor`/`ModalExecutor`/`BlaxelExecutor` partilham interface "enviar código, receber stdout+resultado estruturado". Padrão de "plugin de execução" aplicável ao Plan-Execute se algum passo precisar de executar código de forma pluggable.
3. **`managed_agents`-como-tool** — agente filho registado no pai com o mesmo contrato de uma tool. Padrão simples para compor hierarquias sem inventar protocolo de orquestração novo.
4. **Planning periódico com replaneamento** (`planning_interval`) — separar "plano inicial" de "atualização de plano" como templates distintos, disparado a cada N passos.
5. **Declaração explícita de fronteira de confiança no SECURITY.md** — separar por escrito "isto nunca foi pensado como sandbox" de "isto é sandbox e escapes contam como CVE" — copiável para `packages/mcp/ToolExecutor.ts`, que hoje tem ambiguidade equivalente (zero verificação de capacidade, ver `GOV-FASE1.md`).
6. **`final_answer_checks`** — lista de funções de validação aplicadas à resposta final antes de a aceitar como terminada — gate barato aplicável a qualquer Plan-Execute.

## Classificação e porquê

**EXTRACT** — extrair especificamente (a) o padrão "CodeAgent com sandbox adequado" (whitelist AST + abstração plugável de executores externos reais) e (b) o padrão de comunicação explícita de fronteira de confiança do `SECURITY.md`.

Não é ADOPT/ADAPT porque smolagents é um framework completo (loop, memória, modelo de mensagens próprios) que substituiria os contratos Plan-Execute próprios — contra a diretriz explícita. Não é REJECT total: o `LocalPythonExecutor` e a arquitetura de executores remotos são referência de implementação valiosa para um problema (execução segura de código gerado por LLM) que o PCU pode vir a ter de resolver, e que já tem uma lacuna equivalente (e mais grave) em `packages/mcp/ToolExecutor.ts`.

## O que NÃO adotar

- O framework inteiro (`MultiStepAgent`/`CodeAgent`/`ToolCallingAgent`, `AgentMemory`, loop `_run_stream`) — cede o controlo do ciclo de execução sem checkpoint/resume, sem state machine, sem persistência entre execuções.
- Confiar no `LocalPythonExecutor` como isolamento suficiente para código não confiável — o próprio projeto admite que não é fronteira de segurança.
- Assumir que "sandbox" = "sem rede" — nenhum backend bloqueia rede por omissão de forma garantida.
- Confiar nas tools de busca web nativas como cobertas pelo sandbox de imports — são chamadas de rede do processo host, fora do escopo da whitelist.
- Repetir a alegação de "30% menos passos" como benchmark do smolagents — é citação de paper externo, não medição própria.
- Assumir "uso interno da HF em produção" sem qualificar — única evidência é um projeto-exemplo.
- Copiar a alegação de "~1000 linhas de núcleo" como prova de simplicidade duradoura — descreve só o loop mais central.
