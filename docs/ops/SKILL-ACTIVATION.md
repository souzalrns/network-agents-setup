# Activação da skill antes do worker (`activate_for_task`) + SEC-1.3

**Estado:** implementado no branch `feat/activate-for-task-sec13` (PR draft, sem merge).
**Item:** SEC-1.3 (registado em `docs/initiatives/PENDENCIAS.md` §4 pelo PR de estado #122, para não conflituar). É um pré-requisito do AU-20 e **não fecha o AU-20**: o worker continua sem tools (P-37 por decidir).
**Código:** `runner/plan_runner/skill_activation.py`, chamado em `runner/plan_runner/executor.py` → `execute_external_request`.
**Testes:** `runner/tests/test_skill_activation.py` (39 testes, sem rede).

## Fluxo

```
execute_external_request(out_root, step)
  └─ pending_steps/<id>/
  └─ activation = activate_for_task(repo_root, step)
       ├─ resolve agente + skill (com o `vertical:` do passo, S34)
       ├─ sha256 de SKILL.md e AGENT.md (+ pin opcional)
       ├─ inventaria scripts da pasta da skill → allow-list SEC-1.3 (deny-by-default)
       └─ (opt-in) pesquisa skills externas → candidatas, nunca instaladas
  └─ request.json += activation.to_request_fields()
  └─ materialize_activation(pending, activation)
       ├─ SKILL.md, AGENT.md          (como antes)
       ├─ skill_activation.json       (sempre: rasto de auditoria)
       └─ SKILL_ACTIVATION.md         (só se a skill tem scripts ou houve pesquisa externa)
  └─ worker.process(...)              → o prompt ganha "Activacao da skill (SEC-1.3)" só se o .md existir
```

## Compatibilidade

- O plano não precisa de mudar nada. Sem scripts na skill e sem flags novas, **o prompt fica igual ao de antes**, nos dois modos (`opt`/`legacy`). Há teste para isto.
- Só o `request.json` ganha campos novos. Mantém `agent_path`, `skill_path`, `skill_preview_head` (2000) e `agent_preview_head` (1500), e acrescenta:

| Campo | Conteúdo |
|---|---|
| `skill_sha256`, `agent_sha256` | integridade no momento da activação |
| `allowed_scripts`, `blocked_scripts` | resultado da SEC-1.3 (paths relativos à pasta da skill) |
| `external_skill_candidates` | candidatas saneadas (`installed: false`, `trusted: false`) |
| `skill_activation` | `"skill_activation.json"` |

## SEC-1.3: allow-list de scripts

Config: `config/skills.yaml`.

| Regra | Valor |
|---|---|
| Omissão | **deny**: nenhum script é autorizado |
| O que conta como script | tudo em `scripts/`, extensão executável (`.sh`, `.py`, `.js`, `.ts`, `.ps1`, …), bit de execução ou shebang. Docs/dados (`.md`, `.txt`, `.json`, `.yaml`, `.csv`, imagens) não contam |
| Chave | path da SKILL.md (prioridade) ou `vertical/action` |
| Valor | lista de paths relativos à pasta da skill, ou `true` (todos, com aviso `allow_all`) |
| `allow_scripts: true` global | aceite, com aviso "evitar em produção" |
| Entradas inválidas | absolutas, com `..`, drive Windows, não-string → ignoradas, aviso `allow_list_invalid` |
| Entradas obsoletas | path que já não existe como script → aviso `allow_list_missing` |
| Symlinks | **nunca** autorizados, nem com `true`; aviso `symlink_blocked` |
| Config em falta | deny, sem pesquisa externa |
| Config inválida | **fail-closed**: deny + aviso `config_invalid`; o passo nunca rebenta por causa da config |
| Inventário | máximo 500 ficheiros por skill; acima disso, aviso `scan_truncated` |
| Pin (`pins:`) | sha256 esperado da SKILL.md. Se não conferir, aviso `pin_mismatch` e **todos** os scripts dessa skill ficam bloqueados |
| Enforcement | hoje o worker não executa nada (não tem tools). `is_script_allowed(activation, path)` é o ponto de controlo que o executor de tools do AU-20 (P-37) **tem** de consultar |

O prompt diz ao modelo o que está autorizado e bloqueado e que não executa scripts neste passo.

Estado do repo real: só `skills/claude/idea-refine/scripts/idea-refine.sh` é script, e fica bloqueado (teste `test_skill_real_com_script_fica_bloqueada`).

## Pesquisa de skills externas (opt-in)

| Regra | Valor |
|---|---|
| Activação | `should_search_external: true` (ou `search_external: true`) no passo; ou `search_external_default: true` **e** skill local em falta. Valores não booleanos são ignorados, com aviso |
| Query | `skill_query:` do passo, ou `"<action> <vertical>"` |
| Provider | `skills_sh`: `GET {SKILLS_API_URL ou https://skills.sh}/api/search?q=&limit=10` por HTTPS directo (`httpx`), só `https`, sem redirects, timeout de 5 s, máximo de 256 KB lido em streaming |
| Saneamento | remove controlo/ANSI; nomes e slugs fora de `[A-Za-z0-9._/@:-]` são descartados; máximo de 10, ordenadas por installs |
| Instalação | **nunca**. Candidatas com `installed: false` e `trusted: false`, só para revisão humana; o prompt diz para não seguir instruções delas |
| Falhas | rede, timeout ou JSON inválido → `external.status = "error: <Tipo>"`; o passo segue |
| Sem rede | `PLAN_RUNNER_SKILLS_OFFLINE=1` |
| Testes | nunca tocam na rede (`_http_get` e `httpx.stream` bloqueados por fixture; o provider é injectado) |

### Porque não `npx skills find` (desvio do relatório original, com evidência)

1. **`find` não tem `--json`** no `skills@1.7.1` (MIT, vercel-labs/skills). Em `dist/cli.mjs`, o `--json` só existe noutros comandos; o `find` imprime texto com códigos ANSI. Fazer o parsing disso seria frágil.
2. **`npx` descarrega e executa código do npm em runtime.** É o risco "Supply Chain Compromise" (crítico) do OWASP Agentic Skills Top 10, e foi assinalado ao `find-skills` por usar `npx` sem versão fixa.
3. **A fonte de dados é a mesma.** O `find` chama `searchSkillsAPI` → `GET ${SKILLS_API_URL ou https://skills.sh}/api/search?q&limit`, resposta `{skills:[{name,id,source,installs}]}`. O provider Python chama esse endpoint directamente e honra o mesmo `SKILLS_API_URL`.

Resultado: os mesmos dados, sem execução de código de terceiros e sem custo.

### SkillsCat: estacionado (SKILL-EXT-1)

O relatório original pedia `https://skills.cat/api/search`. Não foi implementado:
- não há contrato público verificável desse endpoint (sem documentação de API; a egress desta sessão também o bloqueia);
- o serviço é AGPL-3.0. Consultar uma API não importa código, mas os candidatos podem trazer licenças fora de MIT/Apache.

Fica como **SKILL-EXT-1** (BLOQUEADO), no fim do §4. Critério de desbloqueio: contrato da API documentado + decisão do maestro sobre licenças dos candidatos. `external_provider: skillscat` dá hoje aviso `provider_unsupported` e não pesquisa.

## `skill_activation.json` (versão 1)

```json
{
  "version": 1,
  "activated_at": "2026-10-07T10:00:00+00:00",
  "action": "review", "vertical": "marketing",
  "skill": {"path": "skills/marketing/review/SKILL.md", "sha256": "…", "pinned": null, "name": "review", "allowed_tools": null},
  "agent": {"path": "agents/marketing/review.agent.md", "sha256": "…"},
  "scripts": {"policy": "deny_by_default", "policy_key": null, "found": ["scripts/check.sh"], "allowed": [], "blocked": ["scripts/check.sh"]},
  "external": {"requested": false, "status": "not_requested", "candidates": []},
  "warnings": []
}
```

## Fontes

- Agent Skills specification (agentskills/agentskills, `docs/specification.mdx`): `SKILL.md`, `scripts/`, `references/`, `assets/`, `allowed-tools` (experimental), progressive disclosure. O `allowed-tools` da skill é registado em `skill.allowed_tools` (informativo).
- OWASP Agentic Skills Top 10 (Malicious Skills, Supply Chain Compromise, Over-Privileged Skills, Update Drift → pinning por hash).
- vercel-labs/skills `skills@1.7.1` (MIT), `dist/cli.mjs` (`searchSkillsAPI`, `parseFindOptions`).
