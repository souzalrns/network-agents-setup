# Registry de actions (catálogo plugável)

Ids estáveis para `steps[].action` no Plan-Execute. Extensível: acrescentar linha = nova capacidade despachável.

## Marketing / conteúdo (método)

| action | output_schema | tools típicas | Notas |
|--------|---------------|---------------|--------|
| `seo_brief` | SeoBrief | read_repo_file, web_search | Item 13 notes no brief |
| `copy_answer_first` | CopyAnswerFirst | read_repo_file | Consome SeoBrief |
| `critic_item13` | CriticReport | read_repo_file | Verifier; publish_ready + human |

## Engenharia / repo

| action | output_schema | tools típicas | Notas |
|--------|---------------|---------------|--------|
| `speckit_constitution` | markdown | read_repo_file | Spec Kit |
| `speckit_specify` | markdown | read_repo_file | |
| `speckit_plan` | markdown | read_repo_file | |
| `speckit_tasks` | markdown | read_repo_file | |
| `implement_task` | code+tests | git, test runner | done_when = tests |
| `code_review` | review report | read_repo_file | |
| `security_scan` | findings | semgrep/lint | Fase 2+ |

## Meta / orquestração

| action | Função |
|--------|--------|
| `plan_approve` | human_gate explícito |
| `verify_plan` | checks globais do plan |
| `register_evidence` | grava evento/artefacto (P03) |

## Regras

1. Novas actions: documentar aqui **antes** de usar em plan.yaml.  
2. Nome: `snake_case`, estável (não renomear de ânimo leve).  
3. Cada action de domínio aponta a um output_schema ou artefacto path.  
4. Produção MCP pode ter registry próprio; este catálogo é do **setup**.  
