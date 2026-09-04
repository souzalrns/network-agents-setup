# Roadmap de adopção dos padrões

## Agora (com Spec Kit / docs)

- [x] Plan-Execute + depends_on + schemas  
- [x] Constitution draft (least privilege, evidência, setup≠prod)  
- [x] Este pacote de padrões (P01–P15 inventário)  
- [ ] Commit local `.specify/` + skills Spec Kit se limpos  
- [ ] `/speckit-constitution` + `/speckit-specify` usando estes docs  

## Curto prazo

- [ ] Expandir `registry-actions.md` quando novos agentes de método nascerem  
- [ ] Piloto 002 genérico que cite `action` ids do registry  
- [ ] Checklist verify = policy pipeline em forma de markdown  

## Médio prazo (runtime lab no setup)

- [ ] Runner que lê `plan.yaml`, respeita allowlist, escreve event stubs  
- [ ] `execute_verified_action` (registo + verify)  
- [ ] Profiles: `content-pipeline` | `code-speckit`  

## Não fazer

- [ ] Vendor Cordis / dsh como dependência core  
- [ ] Ligar runner lab a produção MCP sem gate humano formal  
