# STATUS — {{REPO_NAME}}

> Última atualização: {{DATE}}.
> Este ficheiro é o índice **deste repositório**. Para a visão geral da LRNSdigital
> (todos os projetos, pendências cruzadas), consultar:
> - Supabase `system_inventory` + `pendencias_negocio` (fonte operacional)
> - `docs/STATUS-ECOSSISTEMA.md` no repo `network-agents-setup` (espelho legível no Git)

## Identidade

| Campo | Valor |
|-------|--------|
| **Repo** | `{{REPO_FULL_NAME}}` |
| **Camada** | `public-generic` \| `private-production` \| `product` |
| **Papel** | {{ROLE_ONE_LINE}} |
| **Relaciona-se com** | {{RELATED_REPOS}} |

## O que é este repo (1 parágrafo)

{{DESCRIPTION}}

## Estado real (não aspiracional)

| Peça | Estado |
|------|--------|
| {{COMPONENT}} | Implementado / Parcial / Só desenho / Nunca rodou |

## O que NÃO está aqui (e onde está)

- Conhecimento de produção / dados privados → `agent-network-mcp` + Supabase
- Demo pública / PCU genérico → `network-agents-setup`
- {{OTHER}}

## Como uma sessão futura deve retomar

1. Ler este `docs/STATUS.md`
2. Se existir: correr `pnpm validate:consistency` ou o script de docs do repo
3. Consultar `system_inventory` / `pendencias_negocio` para pendências abertas
4. Só depois propor alterações

## Documentação gerada automaticamente

Ficheiros sob `docs/generated/` são produzidos por scripts — **não editar à mão**.
Regenerar com:

```bash
pnpm --filter @network-agents/scripts docs:code-map
pnpm --filter @network-agents/scripts docs:agents
```

## Changelog curto

| Data | Nota |
|------|------|
| {{DATE}} | STATUS inicial / última revisão |
