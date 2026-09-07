# Pendência — sync local e docs recentes

**Estado:** aberta  
**Criada:** 2026-09-07  
**Motivo:** operador não corre `git pull` no PowerShell neste momento.

---

## Acção pendente (local)

Quando for conveniente, no PC:

```powershell
cd $env:USERPROFILE\Downloads\network-agents-setup
git pull
```

Confirmar que existem, entre outras:

- `docs/architecture/memory/`
- `docs/architecture/multi-platform/`
- `docs/architecture/patterns-from-rag/` (incl. llamaindex-deep)
- `docs/architecture/patterns-from-orchestrators/` (incl. MASTER-EXTRACTION)
- `docs/architecture/patterns-from-hermes/`
- `docs/architecture/patterns-from-harness/`

---

## Já no remoto (GitHub `main`) — não bloqueado pelo pull

| Item | Notas |
|------|--------|
| Arquitectura memória L0–L6 | Especificação genérica; **não** runtime |
| Arquitectura multi-plataforma | Especificação genérica; **não** adapters implementados |
| Padrões orquestradores / RAG / Hermes / dsh | Só docs |

---

## Não fazer ao fechar só o pull

- Não assumir que memória ou multi-plataforma estão “implantadas” em produção  
- Não tocar `agent-network-mcp` por causa deste sync  

---

## Fecho desta pendência

Marcar fechada quando `git pull` tiver corrido com sucesso e o operador confirmar pastas acima no disco local.
