# CLAUDE.md — network-agents-setup (PCU)

## Frase curta do utilizador

Se disser **“lê o status dos projetos”** (ou “status dos projetos”, “como estão os projetos”):

1. Abrir **`docs/STATUS-PROJETOS.md`** (ficheiro único).
2. Resumir a tabela e a pendência aberta principal.
3. Perguntar em qual projeto trabalhar, se ainda não estiver claro.

Não pedir lista de paths nem ler os 13 STATUS um a um a menos que peçam detalhe.

## Bootstrap obrigatório (sessão de código neste repo)

No **início de cada sessão** ou antes da **primeira alteração de código**:

1. Ler `docs/STATUS.md` (estado deste repo).
2. Se a pergunta for transversal: `docs/STATUS-PROJETOS.md` ou `docs/STATUS-ECOSSISTEMA.md`.
3. Se existirem, consultar `docs/generated/AGENTS.md` e `docs/generated/CODE_MAP.md`.
4. Resumir em 3–5 linhas: camada, o que está real, pendências abertas, restrições.
5. Só depois propor ou executar trabalho.

Não esperar o utilizador dizer “lê o STATUS” para o bootstrap **deste** repo.

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
- Isolamento de banco para demo pública: ver pendência em STATUS (ainda aberta).
- Commits claros; não inventar estado que o STATUS contradiz.

## Onde está o resto

| Precisas de… | Vai a… |
|--------------|--------|
| Status de todos os projetos (1 ficheiro) | `docs/STATUS-PROJETOS.md` |
| Produção MCP + memória | `agent-network-mcp` |
| Inventário operacional ao vivo | Supabase `system_inventory` / `pendencias_negocio` |
| Produto restaurantes | `mesaflow-api` |
| Gestão processos Vianna | `vianna-gestao` |
