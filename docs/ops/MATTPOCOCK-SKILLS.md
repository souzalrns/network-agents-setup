# Skills de mattpocock/skills (6, adaptadas)

**Data:** 2026-10-14 · **Decisão do maestro:** opção A (instalar só o que o setup não cobria, adaptado,
pelo caminho do skill-scout). **Origem:** [mattpocock/skills](https://github.com/mattpocock/skills) (MIT),
commit `49dd158d1076134a641b33efb035946536778336`.

## O que entra

| Skill | Para quê | Adaptação |
|---|---|---|
| `wizard` | Script bash que guia o humano no que só ele faz: abrir o dashboard, onde clicar, colar a chave escondida, gravar no `.env` / `gh secret`. Smoke testnet, publishers do PyPI, segredos do Vercel/Supabase | `write_env` **recusa** um `.env` que o git não ignora (o wizard pára). Regras: segredos só no ambiente, `.env` ignorado ou `gh secret`; produção com `confirm` próprio; chaves live fora (L4 bloqueado) |
| `git-guardrails-claude-code` | Hook PreToolUse que bloqueia comandos git perigosos **antes** de correrem: a regra "sem --force, sem rebase" passa a trava mecânica | Hook novo em Python (stdlib, sem subprocess nem variáveis de ambiente). O original bloqueava **todo** o `git push`; este deixa o push normal para branches e bloqueia force push, push para `main`/`master` (também um `git push` sem destino estando em main), apagar branches remotos, `rebase`, `filter-branch`/`filter-repo`, `reset --hard`, `clean -f`, `branch -D`, `checkout .`, `restore .` |
| `handoff` | Resume a conversa para outro agente continuar, sem segredos | nenhuma |
| `retro` | Retrospectiva da sessão: propõe verificações automáticas, cortes no CLAUDE.md, ferramentas mais baratas | nenhuma |
| `writing-for-agents` | Como escrever skills e CLAUDE.md (o `retro` usa-a) | nenhuma |
| `to-questionnaire` | Decisão que precisa de outra pessoa → questionário em Markdown para ela preencher | Grava fora do repo (pasta temporária, ou onde disseres), **nunca** em `docs/knowledge/` (vai para o RAG de produção) e nunca é commitado |

Ficaram de fora as outras 32 skills:

- **Já têm equivalente no setup:** `tdd`, `code-review`, `diagnosing-bugs`, `to-spec`, `grill-me`/`grilling`
  (temos o `interview-me`), `prototype`, `research`, e o `teach` (já existe na conta).
- **Criariam um segundo sistema de pendências:** `to-tickets`, `triage`, `wayfinder`,
  `setup-matt-pocock-skills`. Duplicariam o `PENDENCIAS.md` e o Supabase `pendencias_negocio`.
- **Específicas de TypeScript ou dos cursos dele:** `migrate-to-shoehorn`, `scaffold-exercises`,
  `setup-ts-deep-modules`, `ask-matt`.
- **Instáveis:** tudo em `in-progress/`.
- **Para depois:** `setup-pre-commit` e `improve-codebase-architecture`.

## Scan do skill-scout (no conteúdo adaptado)

| Skill | Veredicto | Porquê |
|---|---|---|
| `handoff`, `retro`, `to-questionnaire`, `writing-for-agents` | `SAFE` (0 achados) | — |
| `git-guardrails-claude-code` | `RISKY` (1 médio) | O SKILL.md manda copiar o hook e fazer `chmod +x`: é o propósito da skill. O `.py` não tem achados |
| `wizard` | `RISKY` (1 médio) | O SKILL.md manda gerar e verificar um script bash (`bash -n`, `chmod +x`): é o propósito da skill |

`RISKY` (médio) instala-se só com aprovação humana desse conteúdo exacto. É isso que o hash no
instalador faz quando **tu** o corres. Nenhum achado alto ou crítico.

## Instalar (corres tu)

```bash
pip install -e oss/skill-scout                          # uma vez
sh scripts/install-mattpocock-skills.sh .               # no network-agents-setup
# (opcional) sh scripts/install-mattpocock-skills.sh ../agent-network-mcp
git add .claude/skills skill-scout.lock.json skill-scout.audit.jsonl && git commit -m "skills: mattpocock (6)"
```

- O `.claude/skills/` do setup é gerado por `scripts/sync_claude_skills.py`. Este PR ensina-o a deixar
  em paz as skills fixadas no `skill-scout.lock.json`: não as apaga e não as conta como divergência.
- O hook do guardrail só fica activo depois do passo 3 da skill. Pede ao Claude
  "configura o git-guardrails neste projecto". Ele junta o `PreToolUse` ao `.claude/settings.json`,
  que já tem o `PostToolUse` do planwright, sem o apagar.

## Actualizar

Clonar o upstream num commit novo e correr
`python scripts/vendor_mattpocock_skills.py --src <checkout> --commit <commit>`. Cada adaptação tem de
encontrar o texto esperado; se o upstream mudou, o script falha em vez de deixar passar conteúdo não
revisto. O teste `runner/tests/test_mattpocock_vendor.py` falha se o vendor e o instalador divergirem.
