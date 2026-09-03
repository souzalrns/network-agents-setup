# Verificação e validação de código

Notas para agentes e CI no **setup**. Independente de clientes/conteúdo jurídico.

## Técnicas (camadas)

### 1. Estático (sem executar)

| Técnica | O que apanha | Exemplos de tools |
|---------|--------------|-------------------|
| Lint / estilo | Erros óbvios, estilo | ESLint, Ruff, Biome |
| Typecheck | Tipos, contratos | TypeScript `tsc`, mypy, pyright |
| SAST regras | Sinks conhecidos, taint simples | Semgrep, CodeQL, Bandit |
| Secrets | Chaves no diff | gitleaks, trufflehog |
| Dependências (SCA) | CVEs em libs | npm audit, pip-audit, osv-scanner |
| Schema / API | Contratos quebrados | JSON Schema, OpenAPI validate |

**Para agentes:** correr no `done_when` do passo *antes* de marcar implement done.

### 2. Dinâmico (executar)

| Técnica | O que apanha |
|---------|--------------|
| Unit / integration tests | Regressões de comportamento |
| Contract tests | Boundaries entre serviços |
| E2E | Fluxos críticos |
| Fuzzing | Inputs inesperados |
| Differential testing | Antes/depois do patch |

**Prove-it (TDD):** teste que falha → fix → teste passa (skill `test-driven-development` no setup).

### 3. Revisão / critic

| Técnica | Notas |
|---------|--------|
| PR review humano | Gates irreversíveis |
| LLM critic com rubric | Útil; **não** substitui SAST/testes |
| Adversarial verify | Segundo agente tenta falsificar o finding |

### 4. Segurança agentic (2025–2026)

Padrão emergente: **determinístico primeiro**, LLM depois.

1. Semgrep/CodeQL/regras → candidatos  
2. LLM tria FP / exploitability  
3. (Opcional) agente propõe fix  
4. Re-validar com testes + SAST no patch  

O modelo que **escreve** código não deve ser o único que **valida** (harness externo).

## Ferramentas por prioridade (stack tipico TS/Node ou Python)

### Must-have em CI

| Tool | Uso |
|------|-----|
| **ESLint / Biome** ou **Ruff** | Lint rápido no diff |
| **tsc --noEmit** / **pyright** | Tipos |
| **Vitest / Jest / pytest** | Testes |
| **Semgrep** (regras community + custom) | SAST leve, bom para agentes |
| **gitleaks** | Secrets |
| **osv-scanner** ou audit nativo do package manager | SCA |

### Strong when scaling

| Tool | Uso |
|------|-----|
| **CodeQL** | SAST profundo (GitHub) |
| **SonarQube / Sonar** | Quality + security gate |
| **Playwright** | E2E |
| **JSON Schema** (como no Plan-Execute) | Validar artefactos de agentes |

### Agentic / research (avaliar, não obrigatório)

| Projecto | Nota |
|----------|------|
| Semgrep + LLM triage | Híbrido estável |
| deepsec, ai-deep-sast, VVAH, raptor | Pipelines SAST agentic — complexidade alta |
| Agent Verify | Foco em permissões/tools de *agentes*, não só app code |
| CodeMender (research) | Fix + validate com análise de programas |

## Padrão recomendado no setup de agentes

```text
/implement (ou executor)
    → unit tests (done_when)
    → lint + typecheck
    → semgrep (se security-relevant)
    → critic/checklist (spec vs código)
    → human_gate se produção / secrets / auth
```

Alinhar com:

- `skills/claude/test-driven-development`
- `skills/claude/security-and-hardening`
- `skills/claude/code-review-and-quality`
- `docs/architecture/plan-execute/` (`done_when`, `verify`)

## Anti-padrões

- Só “o modelo disse que está OK”
- SAST sem triagem → fadiga de alertas
- LLM sozinho como SAST (coverage baixa ou FP/FN opacos)
- Merge com testes a vermelho
- Agent com tools amplas sem verify de patch

## Relação com Spec Kit

`/speckit.analyze` e `/speckit.checklist` cobrem **consistência de artefactos**.  
Verificação de **código** continua a ser lint + types + tests + SAST no `/speckit.implement` e na CI.
