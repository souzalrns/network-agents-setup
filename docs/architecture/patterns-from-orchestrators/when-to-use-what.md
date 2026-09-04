# Quando usar o quê (decisão)

## No setup (agora)

| Necessidade | Usar |
|-------------|------|
| Contratos, pilots, Spec Kit | O que já está no repo |
| Papéis marketing/código | Registry + skills |
| HITL conceptual | `human_gate` no plan |
| Prototipar “equipa” | Crew mental model; executar via plan |

## Lab runtime (médio prazo)

| Objectivo | Candidato de estudo |
|-----------|---------------------|
| Máximo controlo + HITL + estado | **LangGraph** (padrão; não obrigatório vendor lock) |
| Agent/Team/Workflow + serve/MCP | **Agno** (estudar AgentOS; não engolir prod) |
| HITL simples suspend/resume, core pequeno | **Timbal** |
| Outputs rígidos Python | **PydanticAI** |
| Stack TypeScript | **Mastra** |

## Produção MCP

- Continua **vossa**.  
- Framework externo só se houver decisão explícita e adaptação MCP, não “lift and shift”.

## Não escolher por estrelas

AG2/AutoGen: padrões de conversa úteis; lineage AutoGen em maintenance — não base nova.  
CrewAI: excelente demo de roles; fraco como SO de agentes com dezenas de áreas e auditoria dura.

## Combinação citada na shortlist (avaliar depois)

```text
[Contratos nossos] + [MCP prod] + [opcional LangGraph/Agno/Timbal no lab]
                 + [Temporal/Hatchet para jobs]
                 + [Control plane vosso]
```

Ordem: fechar padrões e Spec Kit → runner mínimo no setup → só então experimentar um framework no lab isolado.
