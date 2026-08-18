# STATUS-ECOSSISTEMA — LRNSdigital

> **Índice unificado** para tomar pé do que está a acontecer no conjunto de repositórios.
> Última atualização: 19/08/2026.
>
> Fonte operacional canónica: Supabase `agent-network-memory` → tabelas
> `system_inventory` e `pendencias_negocio`.
> Este ficheiro é o **espelho legível no Git** (portfólio + sessões sem acesso ao banco).
> Cada repo mantém o seu próprio `docs/STATUS.md` para detalhe local.

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
| [agent-network-mcp](https://github.com/souzalrns/agent-network-mcp) | Público | Privada / produção | `docs/STATUS.md` (se existir) | MCP em produção; 30+ agentes com systemPrompt + conhecimento |
| [pcu-nucleo-generico](https://github.com/souzalrns/pcu-nucleo-generico) | Público | Núcleo conceptual | — | Núcleo genérico PCU |

### Produtos / negócios

| Repo | Visibilidade | Domínio |
|------|--------------|---------|
| [mesaflow-api](https://github.com/souzalrns/mesaflow-api) | Privado | SaaS restaurantes |
| [vianna-gestao](https://github.com/souzalrns/vianna-gestao) | Privado | Gestão processos ViannaLegal |
| [viannalegal-site](https://github.com/souzalrns/viannalegal-site) | Público | Cidadania PT |
| [viannalegal](https://github.com/souzalrns/viannalegal) | Público | — |
| [sst-portugal-site](https://github.com/souzalrns/sst-portugal-site) | Público | SST |
| [canidelo-vista-mar](https://github.com/souzalrns/canidelo-vista-mar) | Público | Imobiliário |
| [vistamar-gaia](https://github.com/souzalrns/vistamar-gaia) | Público | Imobiliário |

### Skills / espelhos

| Repo | Notas |
|------|-------|
| [ECC](https://github.com/souzalrns/ECC) | Espelho Everything Claude Code |
| [ui-ux-pro-max-skill](https://github.com/souzalrns/ui-ux-pro-max-skill) | Design system skill |
| [designer-skills](https://github.com/souzalrns/designer-skills) | UX/UI skills |

## Pendências transversais (resumo)

Atualizar quando o Supabase mudar; detalhe fino fica em `pendencias_negocio`.

| ID / tema | Estado | Onde |
|-----------|--------|------|
| Conteúdo real no pipeline jurídico do PCU | Concluído (18/08/2026) | network-agents-setup |
| Isolamento de banco para demo pública | Aberto | network-agents-setup (docker-compose local / schema isolado) |
| STATUS.md por repo de produto | Parcial | só PCU tem STATUS completo |
| Documentação automática de código | Em curso | scripts `docs:*` neste repo |

## Como uma sessão (Claude ou humana) deve começar

1. Ler **este** ficheiro se a pergunta for “o que está a acontecer no conjunto”.
2. Ler o `docs/STATUS.md` **do repo em que se está a trabalhar**.
3. Se houver scripts: `validate:consistency`, `docs:code-map`, `docs:agents`.
4. Supabase `system_inventory` / `pendencias_negocio` para estado operacional fino.

## Ferramentas de documentação (neste monorepo PCU)

```bash
# Mapa de pacotes, entrypoints e árvore relevante
pnpm --filter @network-agents/scripts docs:code-map

# Documentação dos agentes a partir de config/agents.config.ts
pnpm --filter @network-agents/scripts docs:agents

# Consistência STATUS ↔ seeds ↔ agents
pnpm --filter @network-agents/scripts validate:consistency
```

Saídas em `docs/generated/` — geradas, não editar à mão.
