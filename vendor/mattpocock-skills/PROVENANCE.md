# Proveniência de `vendor/mattpocock-skills/`

> Gerado por `scripts/vendor_mattpocock_skills.py`. Não editar à mão: correr o script outra vez.

- **Origem:** [mattpocock/skills](https://github.com/mattpocock/skills) (MIT, ver `LICENSE`)
- **Commit:** `49dd158d1076134a641b33efb035946536778336`
- **Skills:** 6 de 38 (decisão do maestro, 2026-10-14, opção A). As outras ficaram de
  fora por já terem equivalente no setup, por criarem um segundo sistema de pendências (issue
  tracker), por serem específicas de TypeScript ou por estarem em `in-progress/`. Ver
  `docs/ops/MATTPOCOCK-SKILLS.md`.
- **Adaptações:** `git-guardrails-claude-code` (hook novo em Python: deixa o push normal e bloqueia
  --force, push para main, rebase…), `wizard` (o `write_env` recusa `.env` que o git não ignora; regras
  de segredos), `to-questionnaire` (grava fora do repo, nunca em `docs/knowledge/`).
- **Scan:** `skill-scout scan` em cada skill adaptada: ver `docs/ops/MATTPOCOCK-SKILLS.md`.

| Skill | Para quê | Adaptada | sha256 do SKILL.md (12) |
|---|---|---|---|
| `wizard` | guia bash para o que só o humano faz (chaves, dashboards, secrets) | texto | `bdb516bd5714` |
| `git-guardrails-claude-code` | hook que bloqueia --force, push para main, rebase e comandos que deitam trabalho fora | ficheiros nossos | `3117e26538a2` |
| `handoff` | passa a conversa a outro agente, sem segredos | não | `4cbb043950da` |
| `retro` | retrospectiva da sessão: melhorias ao ambiente do agente | não | `33fbc28568e3` |
| `writing-for-agents` | como escrever skills e CLAUDE.md | não | `551adca94222` |
| `to-questionnaire` | decisão que precisa de outra pessoa → questionário | texto | `22674c18cf8a` |
