# Scopes e isolamento

## Hierarquia

```text
global ⊂ org? ⊂ project ⊂ (user | agent_role) ⊂ run
```

Leituras: o caller declara scope; o serviço **intersecta** com permissões do role.

## Exemplos genéricos

| Scope | Exemplos de dados |
|-------|-------------------|
| `global` | Constitution, skills base do framework |
| `org` | Políticas internas da organização (se multi-org) |
| `project` | KBs do projecto, decisões de arquitectura |
| `user` | Preferências de interface, idioma, restrições pessoais |
| `agent_role` | SEO worker só `kb_marketing`; sem write em L0 |
| `run` | Eventos e artefactos daquele plan |

## Regras

1. Write em `global` / L0: só humano.  
2. Agent não eleva scope sozinho.  
3. `retrieve_knowledge` exige `kb` ∈ allowlist do step.  
4. `remember` exige `scope` explícito; default recusar se omisso.  
5. Logs L2 podem referenciar ids de L4/L5 sem copiar PII em excesso.
