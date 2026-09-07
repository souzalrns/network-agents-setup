# Registry de actions (catálogo plugável)

Ids estáveis para `steps[].action` no Plan-Execute. Extensível: acrescentar linha = nova capacidade despachável.

## Marketing / conteúdo (método)

| action | output_schema | tools típicas | Notas |
|--------|---------------|---------------|--------|
| `seo_brief` | SeoBrief | read_repo_file, web_search | Item 13 notes no brief |
| `copy_answer_first` | CopyAnswerFirst | read_repo_file | Consome SeoBrief |
| `critic_item13` | CriticReport | read_repo_file | Verifier; publish_ready + human |
| `critic` | CriticReport | read_repo_file | Genérico |
| `research` | markdown | read_repo_file, web_search | |
| `trend_hunter` | markdown | web_search | Social |
| `storytelling` | markdown | read_repo_file | |
| `copy_social` | markdown | read_repo_file | |
| `ugc` | markdown | read_repo_file | Brief criador |
| `influencer` | markdown | read_repo_file | |
| `media_buyer` | markdown | read_repo_file | Sem spend sem HITL |
| `performance_analyst` | markdown | read_repo_file | |
| `editor_video` | markdown | read_repo_file | |
| `internal_brief` | markdown | read_repo_file | Brief interno criação (ASV M-01) |
| `creative_review` | CriticReport | read_repo_file | Rubrica creative-review-rubric |
| `seo_tech_audit` | markdown | read_repo_file, web_search | Checklist técnico |
| `status_report` | markdown | read_repo_file | Weekly client-facing outline |
| `qbr_outline` | markdown | read_repo_file | Trimestral |
| `handover_delivery` | markdown | read_repo_file | Sem credenciais |

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
2. Nome: `snake_case`, estável.  
3. Cada action de domínio aponta a output_schema ou artefacto path.  
4. Produção MCP pode ter registry próprio; este catálogo é do **setup**.  
5. Nunca action que solicite ou armazene passwords/tokens de cliente.  
