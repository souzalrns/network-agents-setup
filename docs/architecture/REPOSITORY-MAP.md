# Mapa de Repositórios Locais — 2026-09-20

Inventário dos repositórios git presentes nesta máquina, produzido durante a auditoria de cobertura desta sessão (2a) e consolidado no item S23. Método: `Get-ChildItem -Recurse -Directory -Filter ".git"` a partir das pastas de trabalho (`Claude Code`, `Downloads`, `Documents`), depois `git remote -v` + `git branch --show-current` + `git log -1` em cada clone encontrado.

---

## Tabela

| Repo (nome remoto) | Clonado em | Remote | Branch actual | Última actividade | Papel |
|---|---|---|---|---|---|
| `agent-network-mcp` | `C:\Users\souza\Claude Code\agent-network-mcp` | SSH (`git@github.com:souzalrns/agent-network-mcp.git`) | `main` | 2026-09-17 — `feat(mcp): add retrieve_knowledge tool` | Cópia de trabalho principal — produção (Vercel), verticais/agentes de negócio, MCP server |
| `agent-network-mcp` | `C:\Users\souza\Documents\projetos\agent-network-mcp` | HTTPS (`https://github.com/souzalrns/agent-network-mcp.git`) | `main` | 2026-09-17 — mesmo commit que a cópia acima | Cópia secundária, mesmo repo GitHub, mesma branch/commit — **espelho, não diverge** |
| `network-agents-setup` | `C:\Users\souza\Claude Code\network-agents-setup` | SSH (`git@github.com:souzalrns/network-agents-setup.git`) | `main` | 2026-09-20 — `fix: corrigir regressão do gerador...` | Cópia de trabalho principal desta sessão — núcleo (PCU), motor + governança + horizontais |
| `network-agents-setup` | `C:\Users\souza\Downloads\network-agents-setup` | HTTPS (`https://github.com/souzalrns/network-agents-setup.git`) | `main` | 2026-09-20 — mesmo commit (`git pull` confirmado nesta sessão) | Cópia secundária/mirror — usada nesta sessão só para validar `git push`/`git pull`; **tinha 2 `.env` com credencial morta, já removidos (S16)** |
| `viannalegal-site` | `C:\Users\souza\Downloads\repo-vianna` | HTTPS (`https://github.com/souzalrns/viannalegal-site.git`) | `feat/prazos-interativo` | 2026-09-07 — `seo: title curto + link das vias...` | Cópia de trabalho de uma feature branch específica |
| `viannalegal-site` | `C:\Users\souza\Downloads\viannalegal-site` | HTTPS (`https://github.com/souzalrns/viannalegal-site.git`) | `design-local` | 2026-09-01 — `design: header, footer e estilos...` | Cópia de trabalho de outra branch (design local) — **mesmo repo GitHub que `repo-vianna`, branches diferentes e não sincronizadas entre si** |

---

## Repos com múltiplas cópias locais

1. **`agent-network-mcp`** (2 clones) — mesma branch (`main`), mesmo commit. Não há risco de divergência actualmente, mas **2 pontos de trabalho para o mesmo remote** significa que um `git push` feito a partir de um dos dois não é visível no outro até um `git pull` manual — já foi a causa indirecta de confusão nesta sessão (nenhuma neste caso específico, mas é o mesmo padrão que gerou o S16 no outro par).
2. **`network-agents-setup`** (2 clones) — mesma branch (`main`), mesmo commit (confirmado sincronizado nesta sessão via push+pull). É o par que gerou o achado **S16**: a cópia `Downloads` tinha 2 ficheiros `.env` (raiz + `packages/memory/`) com uma variável mal nomeada (`SUPABASE_SERVICE_KEY`) e a chave antiga — nenhum dos dois tinha equivalente na cópia `Claude Code` (que não tem `.env` nenhum). Ambos apagados nesta sessão.
3. **`viannalegal-site`** (2 clones, nomes de pasta diferentes: `repo-vianna` e `viannalegal-site`) — **mesmo remote GitHub, branches diferentes** (`feat/prazos-interativo` vs. `design-local`) e **não sincronizadas entre si** (a última actividade de cada uma é de datas diferentes, 2026-09-07 vs. 2026-09-01, nenhuma delas é a mais recente da outra). Isto é o caso mais arriscado dos 3: se alguém trabalhar numa branch sem saber que a outra pasta tem trabalho não integrado na mesma branch remota, há risco real de perda de contexto ou merge manual complicado mais tarde.

## Repos órfãos ou com papel mal definido

Nenhum encontrado — os 6 clones mapeiam para 3 repos GitHub reais (`agent-network-mcp`, `network-agents-setup`, `viannalegal-site`), todos com papel identificável (produção MCP, núcleo PCU, site jurídico). Não há clones "soltos" sem remote configurado, nem pastas com `.git` mas sem correspondência a nenhum destes 3 projectos conhecidos.

**Item a registar (S23):** as **2 branches divergentes** de `viannalegal-site` (`feat/prazos-interativo` vs. `design-local`) não têm dono/critério documentado sobre qual delas é a "actual" ou qual vai ser integrada em `main` primeiro — não é um problema de repo órfão, mas de **papel ambíguo entre 2 cópias do mesmo repo**. Requer decisão humana (fora do âmbito desta auditoria automática).

---

*Gerado durante a auditoria de cobertura de 2026-09-20 (Tarefa 3, S23). Baseado em `git remote -v`/`git branch --show-current`/`git log -1` reais, não em suposição.*
