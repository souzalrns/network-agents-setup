# Rotina de revisão de segurança (read-only)

> **Estado:** activo 2026-10-31 — absorção mercado / vibe-coding-toolkit Prompts 13 e 16.
> **Política:** só leitura e relatório. Sem pentest activo, sem mutação em produção, sem clientes.
> Alinha com `config/security-capabilities.yaml` (`offensive: forbidden`, `act_in_production: forbidden`).

## 1. Diário / por PR (equivalente Prompt 13 — baseline/diff)

**Quando:** cada PR que mexe em `runner/`, `scripts/`, workflows, MCP tools, ou deps.

**Quem:** CI (já) + triagem humana só se o CI assinalar ou o PR tocar superfície de confiança.

**Checklist (copiar para o PR):**
- [ ] `gitleaks` / `semgrep` / `CodeQL` / `pip-audit` verdes (ou justificados)
- [ ] Diff não introduz segredos, URLs de produção hardcoded, nem `danger-full-access` em paths de produção
- [ ] Novas tools MCP: auth, validação de input, e tecto de tamanho (S-001)
- [ ] Workflows: `persist-credentials: false` onde não há push; permissões mínimas no job
- [ ] Se há `B608` / SQL: valores parametrizados (ver [SECURITY-TOOLS.md](./SECURITY-TOOLS.md) §3)

**Saída:** comentário no PR ou issue com severidade (info/low/med/high) e ficheiro:linha. Sem PoC ofensiva.

## 2. Profundo (equivalente Prompt 16 — audit batch)

**Quando:** mensal, ou após mudança grande no MCP / ingest / worker.

**Modo:** quatro artefactos **privados** (gist ou `docs/audit/` só se não houver dados de clientes):

| Artefacto | Conteúdo |
|---|---|
| AUDIT | superfície de ataque actual (tools, endpoints, secrets, CI) |
| PLAN | itens priorizados com ID de PENDENCIAS ou novos S-NNN |
| FIX | PRs propostos (um por risco alto) |
| VERIFY | como provar o fecho (teste CI, comando read-only) |

**Proibições:**
- Não correr Strix/Garak/promptfoo fora de lab e sem autorização do DEV
- Não escrever em Supabase/Vercel
- Não colar chaves nem dados de clientes nos artefactos

## 3. Ligação ao escritório

- Triagem: agentes `security.triage` / `meta.security-auditor` / `security.reporter` (`config/office.yaml`)
- Itens vivos: prefixo `S` / `S-` / `SEC-` em [`PENDENCIAS.md`](../initiatives/PENDENCIAS.md)
- Lab: [STRIX-LAB.md](./STRIX-LAB.md) e SEC-3 (deferred)
- Arsenal e CI: [SECURITY-TOOLS.md](./SECURITY-TOOLS.md)

## 4. Critério de done desta rotina

- [x] Este ficheiro ligado a partir de `docs/ops/SECURITY-TOOLS.md`
- [ ] Uma linha em PENDENCIAS (S-010) a apontar a rotina (quando o maestro actualizar a tabela)
- [ ] Um ciclo diário coberto pelo CI existente; um ciclo profundo agendado no calendário do DEV
