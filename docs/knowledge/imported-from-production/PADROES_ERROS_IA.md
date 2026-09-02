<!-- COPIA de agent-network-mcp/PADROES_ERROS_IA.md — 2026-09-02 — histórico de padrões; exemplos de projeto são genéricos de aprendizagem -->
# Padrões de Erros Recorrentes — Código/Trabalho Gerado por IA

Registo de erros reais já cometidos por IA e apanhados. Objetivo: revisões futuras mais rápidas.

**Como usar:** antes de aprovar PR/mudança gerada por IA, verificar se algum destes padrões se repete.

---

## Segurança de dados

### 1. RLS ausente ou incompleta em tabela nova
- Políticas só com `USING` sem `WITH CHECK` — permite alterar colunas visíveis.
- Verificar: `rowsecurity = true`; escrita precisa de `USING` **e** `WITH CHECK`.

### 2. IDOR — endpoint que confia só no ID
- Query por ID sem confirmar dono do recurso.
- Todo endpoint com ID deve escopar pelo dono autenticado.

### 3. Credenciais hardcoded
- Usar env vars; Gitleaks no histórico.

---

## Onboarding de infraestrutura

### 4. Agente novo sem registo na tabela de projetos
- FK silenciosa em save de estado.
- Ao criar agente: sincronizar catálogo código ↔ DB.

### 5. Formulário de contacto na plataforma errada
- Ex.: `data-netlify` em site Vercel — falha silenciosa.
- Confirmar mecanismo = plataforma de deploy.

---

## Honestidade sobre dados/estado

### 6. Apresentar relatório antigo como estado atual
- Cruzar com fonte viva antes de reportar.

### 7. Estimar tempo "de cabeça"
- Usar timestamps reais (`created_at` / `started_at`).

### 8. Afirmar número sem verificar
- Contar na fonte no momento de escrever docs públicos.

---

## Infraestrutura/CI

### 9. Upgrade major quebra CI silenciosamente
- Após major: CI verde antes de fechar a tarefa.

---

*Adicionar entradas novas quando um padrão real for identificado e corrigido.*
