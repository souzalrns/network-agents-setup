# STATUS-ECOSSISTEMA — LRNSdigital

> **Atalho:** para “lê o status dos projetos”, preferir o resumo único:
> [docs/STATUS-PROJETOS.md](./STATUS-PROJETOS.md)
>
> Este ficheiro é o **mapa completo**. Fonte operacional canónica: Supabase
> `system_inventory` + `pendencias_negocio`.
>
> Última atualização: 19/08/2026.

## Princípio de arquitetura

Uma única arquitetura de agentes, **duas camadas de deployment**:

1. **Pública / genérica** — `network-agents-setup` (PCU): motor transversal, pluggable, portfólio.
2. **Privada / produção** — `agent-network-mcp`: agentes dos negócios reais + memória Supabase.

Conhecimento de domínio público (leis, doutrina curada) vive na camada genérica.
Agentes de negócio e dados sensíveis ficam na camada privada.

## Mapa de repositórios

### Núcleo de agentes

| Repo | Visibilidade | Camada | STATUS local | Notas |
|------|--------------|--------|--------------|-------|
| [network-agents-setup](https://github.com/souzalrns/network-agents-setup) | Público | Genérica / PCU | [docs/STATUS.md](./STATUS.md) | Demo + ingestão jurídica real; isolamento de banco ainda pendente |
| [agent-network-mcp](https://github.com/souzalrns/agent-network-mcp) | Público | Privada / produção | [docs/STATUS.md](https://github.com/souzalrns/agent-network-mcp/blob/main/docs/STATUS.md) | MCP em produção |
| [pcu-nucleo-generico](https://github.com/souzalrns/pcu-nucleo-generico) | Público | Núcleo conceptual | [docs/STATUS.md](https://github.com/souzalrns/pcu-nucleo-generico/blob/main/docs/STATUS.md) | Aponta para network-agents-setup |

### Produtos / negócios

| Repo | Visibilidade | STATUS |
|------|--------------|--------|
| [mesaflow-api](https://github.com/souzalrns/mesaflow-api) | Privado | [docs/STATUS.md](https://github.com/souzalrns/mesaflow-api/blob/main/docs/STATUS.md) |
| [vianna-gestao](https://github.com/souzalrns/vianna-gestao) | Privado | [docs/STATUS.md](https://github.com/souzalrns/vianna-gestao/blob/main/docs/STATUS.md) |
| [viannalegal-site](https://github.com/souzalrns/viannalegal-site) | Público | [docs/STATUS.md](https://github.com/souzalrns/viannalegal-site/blob/main/docs/STATUS.md) |
| [viannalegal](https://github.com/souzalrns/viannalegal) | Público | [docs/STATUS.md](https://github.com/souzalrns/viannalegal/blob/main/docs/STATUS.md) |
| [sst-portugal-site](https://github.com/souzalrns/sst-portugal-site) | Público | [docs/STATUS.md](https://github.com/souzalrns/sst-portugal-site/blob/main/docs/STATUS.md) |
| [canidelo-vista-mar](https://github.com/souzalrns/canidelo-vista-mar) | Público | [docs/STATUS.md](https://github.com/souzalrns/canidelo-vista-mar/blob/main/docs/STATUS.md) |
| [vistamar-gaia](https://github.com/souzalrns/vistamar-gaia) | Público | [docs/STATUS.md](https://github.com/souzalrns/vistamar-gaia/blob/main/docs/STATUS.md) |

### Skills / espelhos

| Repo | STATUS | Notas |
|------|--------|-------|
| [ECC](https://github.com/souzalrns/ECC) | [docs/STATUS.md](https://github.com/souzalrns/ECC/blob/main/docs/STATUS.md) | Mirror — não é produto |
| [ui-ux-pro-max-skill](https://github.com/souzalrns/ui-ux-pro-max-skill) | [docs/STATUS.md](https://github.com/souzalrns/ui-ux-pro-max-skill/blob/main/docs/STATUS.md) | Mirror skill |
| [designer-skills](https://github.com/souzalrns/designer-skills) | [docs/STATUS.md](https://github.com/souzalrns/designer-skills/blob/main/docs/STATUS.md) | Mirror skill |

## Pendências transversais (resumo)

| ID / tema | Estado | Onde |
|-----------|--------|------|
| Conteúdo real no pipeline jurídico do PCU | Concluído (18/08/2026) | network-agents-setup |
| Isolamento de banco para demo pública | Aberto | network-agents-setup |
| STATUS.md por repo | **Concluído** | produtos + mirrors |
| Entrada única “status dos projetos” | **Concluído** | [STATUS-PROJETOS.md](./STATUS-PROJETOS.md) |
| docs/generated | Seed no Git | regenerar com scripts docs:* |

## Como uma sessão deve começar

- **“Lê o status dos projetos”** → abrir [STATUS-PROJETOS.md](./STATUS-PROJETOS.md) e resumir.
- Trabalho num repo → `docs/STATUS.md` desse repo + `CLAUDE.md`.
- Operacional fino → Supabase `system_inventory` / `pendencias_negocio`.

## Ferramentas de documentação (monorepo PCU)

```bash
pnpm --filter @network-agents/scripts docs:code-map
pnpm --filter @network-agents/scripts docs:agents
pnpm --filter @network-agents/scripts docs:all
pnpm --filter @network-agents/scripts validate:consistency
```

No `agent-network-mcp`: `node scripts/document-agents.js`
