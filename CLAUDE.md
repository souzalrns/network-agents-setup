# CLAUDE.md — network-agents-setup (PCU)

## Frase curta do utilizador

Se disser **“lê o status dos projetos”** (ou “status dos projetos”, “como estão os projetos”):

1. Abrir **`docs/STATUS.md`** deste repo e o `docs/STATUS.md` do `agent-network-mcp`.
2. Resumir o estado a partir do **`docs/initiatives/PENDENCIAS.md`** (§4, abertos e em curso).
3. Perguntar em qual projeto trabalhar, se ainda não estiver claro.

O resumo antigo do ecossistema (`STATUS-PROJETOS.md`, `STATUS-ECOSSISTEMA.md`, 19/08/2026) está
em `docs/archive/` e é histórico: não responder a partir dele.

## Bootstrap obrigatório (sessão de código neste repo)

No **início de cada sessão** ou antes da **primeira alteração de código**:

1. Ler `docs/STATUS.md` (índice curto: duas camadas e onde está cada coisa).
2. Ler `docs/initiatives/PENDENCIAS.md` (**único documento com o estado** deste repo: tabela §4,
   decisões §10). Não ler `docs/archive/` para saber o estado: é tudo histórico.
3. Ler `docs/architecture/GOVERNANCE.md` (camada de governança) se a tarefa tocar em
   `packages/core/`, segurança, ou políticas.
4. Números (agentes, lugares, capabilities): correr os validadores (`python -m plan_runner.areas`,
   `python -m plan_runner.office`); nunca copiar números de documentos.
5. Se existirem, consultar `docs/generated/AGENTS.md` e `docs/generated/CODE_MAP.md`.
6. Resumir em 3–5 linhas: camada, o que está real, pendências abertas (do `PENDENCIAS.md`), restrições.
7. Só depois propor ou executar trabalho.

**Regra da documentação (H-01):** um documento por papel. Não criar documentos de estado novos;
o estado actualiza-se no `PENDENCIAS.md`. O índice está em `docs/README.md`.

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

## Graphify

Grafo de código local em `graphify-out/` (**gitignored**: gerar na máquina, não commitar artefactos). Mesma regra
do `agent-network-mcp` (decisão do maestro, 2026-10-17).

- Instalar uma vez: `uv tool install graphifyy` (com dois "y" no PyPI) e gerar com `graphify update .`. É só AST
  (tree-sitter), sem rede e sem custo de API; neste repo leva ~30 s.
- Perguntas sobre o código: preferir `graphify query "..."`, `graphify path "A" "B"` e `graphify explain "..."`
  quando `graphify-out/graph.json` existir; `GRAPH_REPORT.md` só para visão ampla de arquitectura.
- Após mudanças relevantes de código: `graphify update .`.
- **Não** usar a extracção semântica com chave de LLM, nem ligar o Graphify a GitHub Actions: custo zero,
  actualização local/manual.

## Regras de trabalho

- Preferir alterações mínimas e verificáveis.
- Não misturar conhecimento privado de negócios neste repo.
- Isolamento de banco para demo pública: não há item vivo no `PENDENCIAS.md` (a nota antiga está em `docs/archive/STATUS-ate-2026-08-18.md`); se voltar a ser preciso, abre-se um item.
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
| Status dos projetos | `docs/STATUS.md` de cada repo + `docs/initiatives/PENDENCIAS.md` |
| Produção MCP + memória | `agent-network-mcp` |
| Inventário antigo no Supabase | `system_inventory` / `pendencias_negocio` (desactualizado desde 08/2026; não usar como estado) |
| Produto restaurantes | `mesaflow-api` |
| Gestão processos Vianna | `vianna-gestao` |
