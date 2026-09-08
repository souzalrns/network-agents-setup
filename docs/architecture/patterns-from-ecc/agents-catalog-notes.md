# Agents ECC — como usar o catálogo

ECC expõe dezenas de agents (planner, code-reviewer, security-reviewer, build-error-resolver, a11y, domain, …).

## Regra de extracção

Não importar 68 runtimes. Para cada agent ECC relevante:

1. Extrair **responsabilidade** + **limites**  
2. Mapear a uma `action` no registry  
3. Isolar tools_allowed  
4. Garantir que **review ≠ implement**  

## Famílias prioritárias para o setup

| Família | Actions nossas |
|---------|----------------|
| Plan / architecture | tech_plan, adr |
| Implement | implement_task |
| Review | code_review |
| Security | security_scan |
| Build repair | fix_build |
| Eval | agent_eval |
| Docs | write_docs |
| A11y | a11y_audit |

Marketing continua no registry de marketing; agents ECC de brand/seo são **fonte de skill text**, não nomes de processo obrigatórios.
