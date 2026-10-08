# skill-scout: projecto autónomo de segurança de skills

**Estado:** Fase 1 implementada, mais o que faltava para ser a escolha (SKILL-SCOUT-1, EM CURSO até ao merge do PR #143, branch `feat/skill-notary-phase1`; o branch mantém o nome de trabalho para não quebrar o PR aberto).
**Código:** `oss/skill-scout/` (pacote Python autocontido, MIT). Documentação técnica, em inglês por ser publicável: `oss/skill-scout/README.md`.
**CI:** `.github/workflows/skill-scout.yml`.
**Pedido:** maestro, 2026-10-08. Estratégia: "fazer o que os outros fazem + o que eles não fazem".

## 1. Nome (P-43 = A, `skill-scout`, decidida pelo maestro a 2026-10-08)

O nome pedido, `skill-guard`, **está ocupado no PyPI** por outro projecto da mesma área ([vaibhavtupe/skill-guard](https://github.com/vaibhavtupe/skill-guard), Apache-2.0, v0.9.0). Publicar com esse nome era impossível, e documentar `pip install skill-guard` instalaria o pacote de outra pessoa.

O nome de trabalho foi `skill-notary`. Com o `find`, o projecto passou a cobrir descoberta e validação, e o maestro escolheu **`skill-scout`**. Disponibilidade verificada a 2026-10-08:

| Nome | PyPI | npm |
|---|---|---|
| `skill-scout` / `skillscout` | livre | livre |
| `skill-broker` | livre | livre (`skillbroker` ocupado no npm) |
| `skill-radar` | livre | ocupado |
| `skill-auditor` | ocupado | ocupado |

O renome está feito em todo o lado:
- a pasta `oss/skill-scout/`, o módulo `skill_scout` e o CLI `skill-scout`;
- os ficheiros do projecto: `skill-scout.lock.json` e `skill-scout.audit.jsonl`;
- os formatos: hash `skill-scout-tree-v1`, relatório `skill-scout/report-v1`, SARIF `skill-scout` com fingerprint `skillScoutFinding/v1`;
- o workflow `.github/workflows/skill-scout.yml`, a variável `SKILL_SCOUT_ACTOR` e os itens SKILL-SCOUT-1..3 (alias no `PENDENCIAS.md` §11).

Ficam com o nome antigo, de propósito:
- o branch do PR, para não o quebrar;
- os registos históricos do PROGRESS;
- a entrada do `.gitleaksignore`, que identifica um commit antigo pelo caminho que ele tinha.

## 2. O que já existia, e o que foi importado

| Projecto | Licença | O que faz | Como entra no skill-scout |
|---|---|---|---|
| [agentic-skills-manager](https://github.com/mazen160/skills-manager) 1.0.4 | MIT | scan estático; instala se passar | **motor por omissão** (`asm`), dependência |
| [Cisco skill-scanner](https://github.com/cisco-ai-defense/skill-scanner) 2.2.1 | Apache-2.0 | YARA, AST dataflow, correlação, SARIF | **segundo motor opcional** (`cisco`, extra `[cisco]`), só os analisadores offline |
| [@vercel/detect-agent](https://github.com/vercel/vercel/tree/main/packages/detect-agent) 1.2.5 | Apache-2.0 | detecta se o processo corre dentro de um agente de IA | **lista portada** para Python (recusa de auto-aprovação) |
| [skills CLI](https://github.com/vercel-labs/skills) 1.7.1 | MIT | instala `owner/repo@skill`, `skills-lock.json` | **sintaxe da fonte** igual. O hash do lock não foi copiado: ordena com `localeCompare`, que depende do locale |
| [skill-guard](https://github.com/vaibhavtupe/skill-guard) 0.9.0 | Apache-2.0 | porta de PR (validar, segurança, conflitos de triggers) | nada importado: é um *gate* do repo próprio, não instala. Ver §5 |
| SARIF 2.1.0 (OASIS) | OASIS IPR | formato | o esquema **não** é distribuído; os testes descarregam-no num commit fixo e verificam o sha256 |

Medido antes de decidir: o motor da Cisco corre offline em ~8 s por skill e ocupa ~650 MB com as dependências. Por isso é opcional e não uma dependência.

## 3. Fase 1: implementada

| Pedido | Feito | Superação (o que os outros não fazem) |
|---|---|---|
| `install <owner/repo@skill>` | sim, também `owner/repo`, URL do GitHub, pasta local e `--ref` (branch, tag ou commit) | fetch endurecido (só HTTPS, sem hooks, sem config git do sistema nem do utilizador, ambiente sem segredos); nunca executa nada da skill |
| Scan antes de instalar | 1 ou 2 motores fundidos; `dangerous` e `not_scanned` nunca instalam | fail-closed: falha de um motor = sem instalação |
| Aprovação humana, nunca automática | prefixo de 12 caracteres do hash, escrito num terminal, ou `--approve-sha256` com o hash completo | a aprovação fica **presa ao conteúdo**: se a fonte mudar entre a revisão e a instalação, recusa; **um agente de IA não consegue aprovar**, nem com o hash certo |
| Pin sha256 | `skill-scout.lock.json` com `content_sha256` (`skill-scout-tree-v1`), commit, motores, aprovação | hash **determinístico** (por code point, com o bit de execução); cópia só dos ficheiros do manifesto, cada um re-verificado (sem TOCTOU); setuid e group-write removidos |
| Auditoria | `skill-scout.audit.jsonl` | **cadeia de hashes**: editar, apagar ou reordenar parte a cadeia; o lock aponta para o registo `installed`, o que apanha um corte no fim |
| — | `verify` | drift dos ficheiros instalados, lock editado à mão, skills não geridas na pasta |
| SARIF + Code Scanning | `scan --format sarif`; job `code-scanning` faz upload do scan das 72 skills deste repo | validado contra o **esquema oficial**; `security-severity` e fingerprints estáveis; **nenhum segredo** (snippets e descrições dos motores são descartados) e nenhum caminho absoluto |
| Pacote publicável | `pyproject.toml` (PEP 621, licença PEP 639), CLI `skill-scout`, `python -m skill_scout`, sdist + wheel | `twine check --strict`; wheel com LICENSE e NOTICE e sem testes; testado numa venv limpa |
| Testes safe/risky/dangerous | 132 testes, com skills sintéticas criadas no teste e um "GitHub" local (git real por `file://`) | 22 mutantes apanhados; Python 3.10, 3.12 e 3.13; ruff com regras de segurança (bandit) |

**Prova real (2026-10-08, fora dos testes):**
- `scan anthropics/skills@pdf` com os dois motores: `RISKY` (1 medium: `executable-file-mode`), commit `683bc88`, conteúdo `dd06afcb…`;
- `install` com o hash certo, **neste ambiente** (que é um agente: Claude Code) → recusado, exit 4, nada instalado, auditoria com `scan` e `approval_rejected`.

A instalação real por um humano fica para o maestro (§6).

## 3b. O que faltava para ser a escolha (2026-10-08)

Pergunta do maestro: comparando com os outros, e sem contar reputação nem estrelas, qual escolheria? Resposta honesta: **antes disto, não o `skill-scout` como ferramenta única.** Era o melhor no momento de confiar numa skill nova, mas falhava no dia-a-dia. O que faltava, e como ficou:

| Faltava | Quem já tinha | Feito, com a superação |
|---|---|---|
| `list`, `update`, `uninstall` | skills CLI, agentic-skills-manager | `update` mostra o **diff** (ficheiros +, ~, -) e exige **nova aprovação do novo hash**. `--check` dá exit 1 para o CI. Um pin a commit nunca se move. Alterações locais nunca são sobrescritas. `uninstall` recusa uma cópia modificada |
| Vários agentes | skills CLI (~80), agentic-skills-manager (4) | `--agent` repetível, com a **tabela do skills CLI importada** (MIT, 79 agentes); **uma aprovação** instala em várias pastas; o lock passa a ter a chave pelo caminho de instalação |
| Saída para falsos positivos | agentic-skills-manager (`--exclude`, `--unsafe-install`), skill-guard (`suppress` com motivo) | `waive`: **uma** finding, **um** conteúdo exacto (hash), motivo, prazo (90 dias por omissão, máximo 365), aprovação humana e registo na auditoria. Só conta se a cadeia de auditoria a confirmar: uma excepção escrita à mão no lock é ignorada. Nunca para `critical` |
| Descoberta | skills CLI (`find`) | `find` com a mesma API do skills.sh, por HTTPS e sem `npx`; `--scan N` mostra veredicto e hash por resultado |
| Validação da spec | skill-guard (`validate`) | verificações da spec Agent Skills em cada scan; no SARIF são regras de qualidade, não de segurança |

Bug encontrado durante esta ronda, também no `runner`: a limpeza de caracteres de controlo só tirava o `ESC` das sequências ANSI e deixava, por exemplo, `[31m` no texto. Agora remove as sequências CSI e OSC inteiras (a OSC muda o título do terminal), em `oss/skill-scout` e em `runner/plan_runner/skill_scan.py` e `skill_activation.py`, com testes de regressão.

**Agora a escolha seria esta,** para quem instala skills de terceiros. Gaps que ficam, honestos:
- a detecção de conflitos de triggers do skill-guard (importável, Apache-2.0; Fase 3);
- a análise por LLM da Cisco, desligada de propósito por custo e por enviar o código para fora;
- a sandbox e os testes de comportamento (Fase 2).

**As skills deste repo e a spec:** o scan do `skills/` dava 37 findings de spec: 17 `invalid-name` (usam `_`, como `ux_flow`) e 20 `missing-description`. São skills internas do `plan_runner`, resolvidas pelo `action:`.

**P-45 = A** (maestro, 2026-10-08), aplicada: as 20 skills ganharam `description` (o que fazem e quando usar, em português como o corpo, 1-267 caracteres), sem mudar nomes. O scan passa de 37 para 19 findings de spec: ficam os 17 `invalid-name` (alertas de qualidade conhecidos; mudar os nomes seria a opção B) e 2 `name-folder-mismatch` (low).

**Custo em tokens:**
- no modo `opt` (o de omissão), zero: o worker tira o frontmatter da skill (há teste);
- no `legacy` (o prompt antigo byte a byte, só para A/B e rollback), +2,7% no plano SEO de demonstração (há teste com tecto de 3%).

A calibração da projecção contra o B1 real usa as entradas da época (`token_projection.project(drop_skill_keys=("description",))`).

**P-44 = A** (maestro, 2026-10-08): o `runner/plan_runner/skill_scan.py` e o `skill-scout` ficam separados até à Fase 3 (nota no docstring do módulo).

## 4. Fase 2 (SKILL-SCOUT-2): diferenciar

- **Sandbox** para os scripts de uma skill: processo filho com limites de CPU, memória, ficheiros e tempo (`resource`/`setrlimit`), sem rede (namespaces ou `unshare` quando houver; senão, recusa), sistema de ficheiros temporário.
- **Testes de comportamento:** correr os scripts da skill na sandbox e registar o que tentam fazer (ficheiros, rede, processos), comparando com o que a SKILL.md declara (`allowed-tools`).
- Candidatos a importar, a avaliar nessa fase: o analisador comportamental da Cisco (já em uso, só estático), `bubblewrap`/`firejail` (licenças a verificar), `seccomp` via `pyseccomp`.

## 5. Fase 3 (SKILL-SCOUT-3): consolidar

- Repo próprio (o DEV cria), docs e CI próprios: o pacote e o workflow já são autocontidos, a extracção é mover `oss/skill-scout/` e o workflow.
- Publicação no PyPI com **Trusted Publishing** (OIDC, sem token guardado) e atestações de proveniência. É uma acção pública do DEV.
- P-44: o `plan_runner/skill_scan.py` passa a depender do `skill-scout` publicado (recomendada A).
- Ideias de superação registadas: aprovações assinadas (Sigstore), `pre-commit` hook, detecção de conflitos de triggers como o `skill-guard` (importar o deles, Apache-2.0, em vez de reescrever), política por ficheiro (`skill-scout.yaml`: fontes permitidas, regras excluídas com motivo e prazo).

## 6. Como o maestro instala a primeira skill real (no seu terminal)

```bash
pip install ./oss/skill-scout
skill-scout scan anthropics/skills@pdf          # ler o veredicto e as findings; copiar o hash
skill-scout install anthropics/skills@pdf       # escrever os 12 primeiros caracteres do hash
skill-scout verify --dest .claude/skills
```

Dentro do Claude Code (ou de outro agente) o `install` recusa, e é isso que se quer: a aprovação é humana.
