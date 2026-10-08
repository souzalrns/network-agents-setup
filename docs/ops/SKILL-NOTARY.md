# skill-notary: projecto autónomo de segurança de skills

**Estado:** Fase 1 implementada (SKILL-NOTARY-1, EM CURSO até ao merge do PR do branch `feat/skill-notary-phase1`).
**Código:** `oss/skill-notary/` (pacote Python autocontido, MIT). Documentação técnica, em inglês por ser publicável: `oss/skill-notary/README.md`.
**CI:** `.github/workflows/skill-notary.yml`.
**Pedido:** maestro, 2026-10-08. Estratégia: "fazer o que os outros fazem + o que eles não fazem".

## 1. Nome (P-43, por decidir)

O nome de trabalho `skill-guard` **está ocupado no PyPI** por outro projecto da mesma área ([vaibhavtupe/skill-guard](https://github.com/vaibhavtupe/skill-guard), Apache-2.0, v0.9.0, "PR gate for Agent Skills"). Com esse nome não é possível publicar. Pior: documentar `pip install skill-guard` instalaria o pacote de outra pessoa, um risco de confusão de dependências numa ferramenta que existe precisamente para evitar isso.

O nome usado no código é **`skill-notary`** (livre no PyPI e no npm a 2026-10-08), que é a recomendação A da P-43 (`PENDENCIAS.md` §10). Trocar de nome é uma substituição de texto em `oss/skill-notary/`.

## 2. O que já existia, e o que foi importado

| Projecto | Licença | O que faz | Como entra no skill-notary |
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
| Pin sha256 | `skill-notary.lock.json` com `content_sha256` (`skill-notary-tree-v1`), commit, motores, aprovação | hash **determinístico** (por code point, com o bit de execução); cópia só dos ficheiros do manifesto, cada um re-verificado (sem TOCTOU); setuid e group-write removidos |
| Auditoria | `skill-notary.audit.jsonl` | **cadeia de hashes**: editar, apagar ou reordenar parte a cadeia; o lock aponta para o registo `installed`, o que apanha um corte no fim |
| — | `verify` | drift dos ficheiros instalados, lock editado à mão, skills não geridas na pasta |
| SARIF + Code Scanning | `scan --format sarif`; job `code-scanning` faz upload do scan das 72 skills deste repo | validado contra o **esquema oficial**; `security-severity` e fingerprints estáveis; **nenhum segredo** (snippets e descrições dos motores são descartados) e nenhum caminho absoluto |
| Pacote publicável | `pyproject.toml` (PEP 621, licença PEP 639), CLI `skill-notary`, `python -m skill_notary`, sdist + wheel | `twine check --strict`; wheel com LICENSE e NOTICE e sem testes; testado numa venv limpa |
| Testes safe/risky/dangerous | 132 testes, com skills sintéticas criadas no teste e um "GitHub" local (git real por `file://`) | 22 mutantes apanhados; Python 3.10, 3.12 e 3.13; ruff com regras de segurança (bandit) |

**Prova real (2026-10-08, fora dos testes):**
- `scan anthropics/skills@pdf` com os dois motores: `RISKY` (1 medium: `executable-file-mode`), commit `683bc88`, conteúdo `dd06afcb…`;
- `install` com o hash certo, **neste ambiente** (que é um agente: Claude Code) → recusado, exit 4, nada instalado, auditoria com `scan` e `approval_rejected`.

A instalação real por um humano fica para o maestro (§6).

## 4. Fase 2 (SKILL-NOTARY-2): diferenciar

- **Sandbox** para os scripts de uma skill: processo filho com limites de CPU, memória, ficheiros e tempo (`resource`/`setrlimit`), sem rede (namespaces ou `unshare` quando houver; senão, recusa), sistema de ficheiros temporário.
- **Testes de comportamento:** correr os scripts da skill na sandbox e registar o que tentam fazer (ficheiros, rede, processos), comparando com o que a SKILL.md declara (`allowed-tools`).
- Candidatos a importar, a avaliar nessa fase: o analisador comportamental da Cisco (já em uso, só estático), `bubblewrap`/`firejail` (licenças a verificar), `seccomp` via `pyseccomp`.

## 5. Fase 3 (SKILL-NOTARY-3): consolidar

- Repo próprio (o DEV cria), docs e CI próprios: o pacote e o workflow já são autocontidos, a extracção é mover `oss/skill-notary/` e o workflow.
- Publicação no PyPI com **Trusted Publishing** (OIDC, sem token guardado) e atestações de proveniência. É uma acção pública do DEV.
- P-44: o `plan_runner/skill_scan.py` passa a depender do `skill-notary` publicado (recomendada A).
- Ideias de superação registadas: aprovações assinadas (Sigstore), `pre-commit` hook, detecção de conflitos de triggers como o `skill-guard` (importar o deles, Apache-2.0, em vez de reescrever), política por ficheiro (`skill-notary.yaml`: fontes permitidas, regras excluídas com motivo e prazo).

## 6. Como o maestro instala a primeira skill real (no seu terminal)

```bash
pip install ./oss/skill-notary
skill-notary scan anthropics/skills@pdf          # ler o veredicto e as findings; copiar o hash
skill-notary install anthropics/skills@pdf       # escrever os 12 primeiros caracteres do hash
skill-notary verify --dest .claude/skills
```

Dentro do Claude Code (ou de outro agente) o `install` recusa, e é isso que se quer: a aprovação é humana.
