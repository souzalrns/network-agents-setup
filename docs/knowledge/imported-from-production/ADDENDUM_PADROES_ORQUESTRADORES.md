<!-- COPIA de agent-network-mcp/docs/ADDENDUM_PADROES_ORQUESTRADORES.md — 2026-09-02 — só padrões em texto; sem importar código de terceiros -->
# Addendum — Padrões Extraídos de Orquestradores Open Source

**Regra:** padrões arquiteturais em texto; **não** importar código-fonte de originais. Reimplementar do zero se necessário.

## Sistemas avaliados (resumo)

| Sistema | O que oferece de útil |
|---|---|
| DeepSeek Harness | Tudo é plugin / registro plugável |
| Hermes Agent | Resolvedor multi-modelo, memória em camadas, skill pós-execução (com cautela) |
| OpenClaw | Loop planeamento vs execução; roteamento semântico |
| LangGraph DeepAgents | Plano explícito (`write_todos`), grafo auditável |

## Padrões adotáveis no setup

### 1. Resolvedor de modelo (multi-IA)
Um sítio mapeia `(provedor, modelo)` → config. Agentes não falam com API diretamente.

### 2. Prompt em camadas
Estável (identidade) → contexto projeto → volátil (turno). Melhora cache/custo.

### 3. Compressão de contexto
Resumir meio da conversa acima de limiar; log original preservado.

### 4. Skill pós-execução = candidate
Só rascunho; nunca auto-aprovar sem humano.

### 5. Planeamento como tool de 1ª classe
Plano explícito antes de multi-step; auditável.

## Não adotar agora (no setup)

- Sandboxes Docker/SSH pesados sem necessidade
- Gateway multicanal (Telegram/Discord…) como núcleo
- DAG multi-agente a 50+ agentes concorrentes
- Kernel Cordis inteiro (só o padrão de registro)
