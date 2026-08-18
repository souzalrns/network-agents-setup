# Network Agents

## Plataforma Cognitiva Universal

### Estrutura

```
network-agents/
├── packages/
│   ├── core/           # Núcleo da rede (Orquestrador, Executor, Planner)
│   ├── memory/         # Memória persistente (PostgreSQL + Redis)
│   ├── mcp/            # MCP para ferramentas
│   ├── observability/  # Logs, métricas, tracing
│   ├── websocket/      # Comunicação em tempo real
│   ├── langgraph/      # Fluxos complexos com LangGraph
│   └── shared/         # Tipos e utilitários compartilhados
├── apps/
│   └── api/            # API REST + WebSocket
├── config/             # Configurações
├── tests/              # Testes (unitários, integração, e2e)
└── k8s/                # Kubernetes manifests
```

### Requisitos

- Node.js 18+
- pnpm 8+
- PostgreSQL 16+
- Redis 7+

### Instalação

```bash
pnpm install
cp .env.example .env
# Edite .env com suas credenciais
pnpm run build
pnpm run dev
```

### Docker

```bash
docker-compose up -d
```

### Kubernetes

```bash
kubectl apply -f k8s/
```

### Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/chat` | POST | Envia mensagem para a rede |
| `/chat/stream` | POST | Streaming de resposta |
| `/executions` | GET | Lista execuções |
| `/executions/:id` | GET | Detalhes de execução |
| `/agents` | GET | Lista agentes |
| `/hitl/pending` | GET | Solicitações HITL pendentes |
| `/metrics` | GET | Métricas detalhadas |
| `/health` | GET | Health check |
| `/ws` | WebSocket | Comunicação em tempo real |

### WebSocket

```javascript
const ws = new WebSocket('ws://localhost:3000/ws');

ws.on('open', () => {
  ws.send(JSON.stringify({
    id: 'msg-1',
    type: 'request',
    action: 'chat:send',
    payload: { message: 'Olá' },
    timestamp: new Date(),
  }));
});
```

### Testes

```bash
pnpm test
```

### Licença

MIT

---

## Documentação adicional

A documentação original de especificação ("PROVIDÊNCIAS IDENTIFICADAS — ESTRUTURA GERAL DE AGENTES", com as 121 providências P-AG-001 a P-AG-121f que fundamentaram esta arquitetura) está disponível em [`docs/estrutura-geral-agentes.md`](./docs/estrutura-geral-agentes.md).

## Nota sobre o estado do projeto

Este repositório reúne todo o código e documentação gerados ao longo do desenvolvimento incremental do projeto "network-agents", incluindo a camada de orquestração central, os módulos de governança organizacional (Conselho de Arquitetura, Deliberação, Confiança/Autonomia, Completude, Economia de Tokens, Segurança, Autopercepção, Radar de Oportunidades, Simulação Organizacional e Memória Imunológica), testes unitários e infraestrutura de deploy (Docker/Kubernetes).

Vários módulos contêm implementações declaradamente simplificadas/stub (documentadas no código-fonte), como: verificação de senha, MFA, coleta de estado em `SelfAwareness`, scanners externos do `OpportunityRadar`, e o motor de decisão do `OrganizationalSimulator` (baseado em `Math.random()`). Esses pontos foram sinalizados durante o desenvolvimento e devem ser tratados antes de qualquer uso em produção.
