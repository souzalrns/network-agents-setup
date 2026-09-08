# Skills, instincts, continuous learning

## Skills ECC

- Carregadas **quando a tarefa precisa** (progressive disclosure)  
- Triggers na description  
- Placement + **provenance** policy  
- Stocktake / scout / comply (governança do catálogo)  

### Skills ECC de interesse transversal (referência, não dump)

| Skill ECC (nome) | Uso no setup |
|------------------|--------------|
| tdd-workflow, verification-loop | Engenharia |
| security-scan, security-review | Agent security |
| continuous-learning-v2 | Instincts / observe hooks |
| unified-memory | Alinhar L4 |
| context-budget, strategic-compact | L1 budget |
| delivery-gate | done_when |
| agent-eval, agent-self-evaluation | TEST no checklist |
| mcp-server-patterns | MCP hardening |
| brand-voice, brand-discovery, seo, content-engine, marketing-campaign, article-writing | **Referência** marketing — reescrever para P0 skills |
| design-system | UI/UX vertical |
| team-agent-orchestration | Orchestrator patterns |

## Instincts

- Padrões aprendidos de sessões reais  
- **Confidence score**  
- Observação em Pre/Post tool use (não só no Stop — evita perda se a sessão crasha)  
- **Promote** com critérios (ex. multi-project + confidence ≥ limiar)  
- Project-scoped para não misturar stacks  

## Nosso equivalente

```text
observe (L2 events)
  → instinct/memory/skill candidate
  → human_gate / policy
  → active L3 or L4
```

Já alinhado a Hermes skill lifecycle; ECC reforça: **confidence + multi-observação + scope**.

## Anti-padrão (community)

Skill router sem `max_call_depth` → loops de tokens.  
**Providência:** budget no runner + profundidade máxima de re-chamada de skill.
