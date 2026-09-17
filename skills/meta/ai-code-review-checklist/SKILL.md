---
name: ai-code-review-checklist
action: ai_code_review_checklist
version: 1
role: meta_technique
priority: P0
---

# Skill — ai-code-review-checklist

## Papel

Checklist vivo de erros recorrentes já cometidos por IA em código/trabalho gerado, genericamente aplicável antes de aprovar qualquer PR/mudança gerada por IA — não é teoria, é padrão observado repetir-se.

## Como usar

Antes de aprovar qualquer PR/mudança gerada por IA, verificar se algum destes padrões se repete. Adicionar entrada nova ao checklist do projecto sempre que um erro novo for identificado e corrigido, para que revisões futuras sejam mais rápidas.

## Segurança de dados

### RLS ausente ou incompleta em tabela nova
- **Padrão:** políticas de Row Level Security criadas só com `USING` (o que se vê), sem `WITH CHECK` (o que se pode escrever) — permite alterar qualquer coluna desde que se consiga ver a linha.
- **Outros bugs da mesma família:** política sem escopo de role explícito aplica-se também a utilizadores anónimos; políticas com JOIN a tabelas relacionadas podem ser contornadas.
- **Verificação rápida:** confirmar que toda tabela tem row-level security activa, e que toda política de escrita tem `USING` E `WITH CHECK` juntos.

### IDOR — endpoint que confia só no ID, não no dono do recurso
- **Padrão:** endpoint consulta um recurso só pelo ID, sem confirmar que pertence ao utilizador autenticado.
- **Verificação rápida:** todo endpoint que recebe um ID de recurso deve escopar a query pelo dono, não só pelo ID.

### Credenciais/segredos hardcoded em vez de variável de ambiente
- **Verificação rápida:** correr um scanner de segredos (ex. Gitleaks) sobre o histórico completo antes de assumir que "nunca aconteceu".

## Onboarding de infraestrutura

### Registo novo (agente/serviço/entidade) sem linha correspondente na tabela de registo
- **Padrão:** ao adicionar uma nova entidade a um sistema com tabela de registo central, a inserção correspondente fica esquecida — tende a repetir-se mesmo depois de "corrigido" uma vez.
- **Verificação rápida:** todo processo de onboarding de entidade nova deve terminar com uma validação explícita de que a linha existe na tabela de registo, não só assumir que existe.

## done_when

- [ ] Checklist consultado antes de aprovar a mudança
- [ ] Padrões novos identificados adicionados ao checklist do projecto

## Anti-padrões

- Aprovar mudança gerada por IA sem passar pelo checklist
- Tratar um erro corrigido uma vez como resolvido permanentemente sem verificação recorrente
