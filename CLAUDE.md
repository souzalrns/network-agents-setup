# CLAUDE.md — network-agents-setup (PCU)

## Frase curta do utilizador

Se disser **“lê o status dos projetos”** (ou “status dos projetos”, “como estão os projetos”):

1. Abrir **`docs/STATUS-PROJETOS.md`** (ficheiro único).
2. Resumir a tabela e a pendência aberta principal.
3. Perguntar em qual projeto trabalhar, se ainda não estiver claro.

Não pedir lista de paths nem ler os 13 STATUS um a um a menos que peçam detalhe.

## Bootstrap obrigatório (sessão de código neste repo)

No **início de cada sessão** ou antes da **primeira alteração de código**:

1. Ler `docs/architecture/ECOSYSTEM.md` (ponto de entrada — visão geral do repo, setup vs. plugin MCP).
2. Ler `docs/initiatives/PENDENCIAS.md` (**único documento com o estado dos pendentes** deste
   repo, desde 2026-10-03: tabela §4, decisões §10, aliases de IDs antigos §11).
   - `docs/initiatives/STATUS.md` fica com o estado dos sistemas (Done, infra, credenciais,
     resumos do dia); as listas de pendentes dele são históricas.
   - `docs/audit/PLANO-DE-ACAO.md`, `docs/initiatives/OPEN-ITEMS.md` e o estado do
     `docs/architecture/EXECUTION-PLAN.md` são históricos (o plano em si continua válido).
   - `docs/STATUS.md` é histórico até 18/08/2026.
3. Ler `docs/architecture/GOVERNANCE.md` (camada de governança) se a tarefa tocar em
   `packages/core/`, segurança, ou políticas.
4. Se a pergunta for transversal a vários repos: `docs/STATUS-PROJETOS.md` ou
   `docs/STATUS-ECOSSISTEMA.md` (histórico, ver `docs/architecture/BOOTSTRAP.md` antes de confiar
   nas datas).
5. Se existirem, consultar `docs/generated/AGENTS.md` e `docs/generated/CODE_MAP.md`.
6. Resumir em 3–5 linhas: camada, o que está real, pendências abertas (do `PENDENCIAS.md`), restrições.
7. Só depois propor ou executar trabalho.

**Documentos de arquitectura produzidos em 2026-09-18** (mapeamento, governança, segurança,
memória) — consultar `docs/architecture/BOOTSTRAP.md` para o índice completo antes de assumir
que algo não foi feito.

Não esperar o utilizador dizer "lê o STATUS" para o bootstrap **deste** repo.

## Identidade deste repo

- **Camada:** pública / genérica (PCU — Plataforma Cognitiva Universal).
- **Papel:** motor transversal, pluggable, portfólio e demo com ingestão jurídica real.
- **Não é** a instância de produção com dados dos negócios → isso é `agent-network-mcp`.
- Agentes `public` em `config/agents.config.ts` são transversais; `private` são exemplos de domínio plugáveis, não dados reais de clientes.

## Automação de documentação e consistência

Quando o utilizador pedir “atualizar docs”, “gerar mapa”, “verificar consistência”, ou após mudanças grandes em agentes/config/seeds:

```bash
pnpm --filter @network-agents/scripts docs:all
pnpm --filter @network-agents/scripts validate:consistency
```

- `docs/generated/*` — **não editar à mão**; regenerar com os scripts.
- Template de STATUS para outros repos: `docs/templates/STATUS.repo.md`.

## Regras de trabalho

- Preferir alterações mínimas e verificáveis.
- Não misturar conhecimento privado de negócios neste repo.
- Isolamento de banco para demo pública: ver pendência em STATUS (ainda aberta; o estado vivo dos pendentes está em `docs/initiatives/PENDENCIAS.md`).
- Commits claros; não inventar estado que o `PENDENCIAS.md` contradiz. Commits e PRs citam o ID do item (ex.: `AU-08: ...`).

## Decisões e opções (regra do maestro, 2026-10-07)

**Toda a apresentação de opções vem com recomendação explícita. SEM EXCEPÇÃO.**
Formato: A/B/C + recomendação + razão curta. Se não houver recomendação, a decisão não está pronta.

- Vale para relatórios, PRs, a §10 do `docs/initiatives/PENDENCIAS.md` e qualquer lista de decisões, curta ou longa.
- Marcar a escolhida como **RECOMENDADA**, com a evidência (ficheiro:linha, SELECT, teste, run) que a sustenta.
- Motivo da regra: numa sessão, foram listadas 11 decisões sem recomendação explícita, o que violou a regra do maestro.
- Quem decide é o maestro; o Claude propõe e nunca assume uma decisão pendente como tomada.

## Onde está o resto

| Precisas de… | Vai a… |
|--------------|--------|
| Status de todos os projetos (1 ficheiro) | `docs/STATUS-PROJETOS.md` |
| Produção MCP + memória | `agent-network-mcp` |
| Inventário operacional ao vivo | Supabase `system_inventory` / `pendencias_negocio` |
| Produto restaurantes | `mesaflow-api` |
| Gestão processos Vianna | `vianna-gestao` |
