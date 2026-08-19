# Status dos projetos — LRNSdigital

> **Ficheiro único.** Se o utilizador disser “lê o status dos projetos” (ou equivalente),
> lê **este** ficheiro e responde com o resumo abaixo. Não peças lista de paths.

Atualizado: 19/08/2026 · Detalhe por repo: `docs/STATUS.md` em cada GitHub · Operacional ao vivo: Supabase `system_inventory` / `pendencias_negocio`

---

## Em 30 segundos

| # | Projeto | Camada | Estado |
|---|---------|--------|--------|
| 1 | **network-agents-setup** (PCU) | Pública / genérica | Demo + ingestão jurídica real; isolamento de banco **ainda aberto** |
| 2 | **agent-network-mcp** | Privada / produção | MCP em produção (Vercel), 30+ agentes, memória Supabase |
| 3 | **mesaflow-api** | Produto | API NestJS avançada; faturação fiscal ainda **mock** |
| 4 | **vianna-gestao** | Produto | Gestão processos; falta import Astrea + edição |
| 5 | **viannalegal-site** | Produto | Em produção (viannalegal.com.br), 82 artigos |
| 6 | **sst-portugal-site** | Produto | Conteúdo ok; **noindex** até TSST N6 |
| 7 | **canidelo / vistamar** | Produto | Sites venda imóvel em produção |
| 8 | **pcu-nucleo-generico** | Conceptual | Aponta para network-agents-setup |
| 9 | **ECC / ui-ux / designer-skills** | Mirror | **Não são produtos** — só referência |

**Arquitetura:** um sistema de agentes, duas deployments — PCU genérico (portfólio) + MCP privado (negócios reais).

---

## Links diretos (STATUS local)

### Núcleo
- [network-agents-setup/STATUS](https://github.com/souzalrns/network-agents-setup/blob/main/docs/STATUS.md)
- [agent-network-mcp/STATUS](https://github.com/souzalrns/agent-network-mcp/blob/main/docs/STATUS.md)
- [STATUS-ECOSSISTEMA (mapa completo)](https://github.com/souzalrns/network-agents-setup/blob/main/docs/STATUS-ECOSSISTEMA.md)

### Produtos
- [mesaflow-api](https://github.com/souzalrns/mesaflow-api/blob/main/docs/STATUS.md)
- [vianna-gestao](https://github.com/souzalrns/vianna-gestao/blob/main/docs/STATUS.md)
- [viannalegal-site](https://github.com/souzalrns/viannalegal-site/blob/main/docs/STATUS.md)
- [sst-portugal-site](https://github.com/souzalrns/sst-portugal-site/blob/main/docs/STATUS.md)
- [canidelo-vista-mar](https://github.com/souzalrns/canidelo-vista-mar/blob/main/docs/STATUS.md)
- [vistamar-gaia](https://github.com/souzalrns/vistamar-gaia/blob/main/docs/STATUS.md)

### Mirrors (não desenvolver produto aqui)
- [ECC](https://github.com/souzalrns/ECC/blob/main/docs/STATUS.md) · [ui-ux-pro-max-skill](https://github.com/souzalrns/ui-ux-pro-max-skill/blob/main/docs/STATUS.md) · [designer-skills](https://github.com/souzalrns/designer-skills/blob/main/docs/STATUS.md)

---

## Resposta esperada do assistente

1. Tabela ou bullets do estado atual (como acima).
2. Pendência transversal aberta principal: **isolamento de banco da demo PCU**.
3. Perguntar em qual projeto trabalhar, se ainda não estiver claro.
4. Só então aprofundar o `docs/STATUS.md` desse repo.
