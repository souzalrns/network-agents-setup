# STATUS — network-agents-setup

> Índice curto e **actual** deste repo (refeito a 2026-10-25, H-01). Não guarda listas de
> pendentes nem números escritos à mão: o estado está num só sítio e as contagens vêm dos
> validadores. O conteúdo anterior deste ficheiro (até 18/08/2026) está em
> [`docs/archive/STATUS-ate-2026-08-18.md`](./archive/STATUS-ate-2026-08-18.md).

## O que é: duas camadas

- **Pública/genérica (este repo):** o motor (`plan_runner`, Python), a governança à volta dele e
  as capacidades horizontais (agentes, skills, domain packs) que qualquer negócio pode ligar.
- **Privada/produção:** o servidor MCP [`agent-network-mcp`](https://github.com/souzalrns/agent-network-mcp)
  (Vercel + Supabase), com os agentes que conhecem cada negócio. Dados de clientes nunca entram aqui.

## Onde está cada coisa

| Preciso de… | Vou a… |
|---|---|
| Estado e pendentes (fonte única) | [`docs/initiatives/PENDENCIAS.md`](./initiatives/PENDENCIAS.md) |
| O plano | [`docs/architecture/EXECUTION-PLAN.md`](./architecture/EXECUTION-PLAN.md) |
| Visão do sistema e fontes de verdade | [`docs/architecture/ECOSYSTEM.md`](./architecture/ECOSYSTEM.md) · [`BOOTSTRAP.md`](./architecture/BOOTSTRAP.md) |
| Governança | [`docs/architecture/GOVERNANCE.md`](./architecture/GOVERNANCE.md) |
| Sessão de fecho do setup | [`docs/ops/SETUP-CLOSE-SESSION.md`](./ops/SETUP-CLOSE-SESSION.md) |
| Escritório dos agentes | [`config/office.yaml`](../config/office.yaml) · [`docs/ops/OFFICE.md`](./ops/OFFICE.md) |
| Índice completo da documentação | [`docs/README.md`](./README.md) |
| Documentos históricos | [`docs/archive/`](./archive/) |

## Números (nunca à mão)

```bash
cd runner
python -m plan_runner.areas    # áreas, agentes do runner e capabilities
python -m plan_runner.office   # departamentos, lugares e todos os agentes (runner + MCP)
```
