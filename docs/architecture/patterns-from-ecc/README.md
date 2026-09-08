# Padrões extraídos do ECC (Everything Claude Code)

**Fonte:** [affaan-m/ECC](https://github.com/affaan-m/ECC) (MIT), ecc.tools  
**O que é:** sistema operativo de **harness** (Claude Code, Codex, Cursor, …) — skills, agents, hooks, rules, memory vault, AgentShield.  
**O que não é:** orquestrador da vossa rede de negócio / substituto do `agent-network-mcp`.

**Mantra ECC a internalizar:** *Optimize the context window. Persist everything else.*

**Loop canónico:**

```text
plan → test → implement → review → verify → remember → improve
```

---

## Mapa mental ECC → nosso setup

| ECC | Nosso |
|-----|--------|
| Skills (286) | L3 SKILL.md + registry actions |
| Agents (68) | Roles / workers com tools_allowed e contexto isolado |
| Rules | L0 constitution / rules selectivas por projecto |
| Hooks | Enforcement **fora** do LLM (runner, CI, PreToolUse) |
| Instincts + promote | skill_candidate / memory_candidate + human gate |
| Memory Vault (`ecc.memory.v1`) | L4 (+ handoff); markdown source of truth |
| Commands / shims | Entrypoints DX; skills-first a longo prazo |
| AgentShield | Scanner de config/MCP/hooks/secrets |
| Cross-harness adapters | Multi-plataforma: thin adapters, one brain |
| Selective install | Não carregar 286 skills no contexto |

Detalhe: [loop-and-gates.md](./loop-and-gates.md) · [memory-vault.md](./memory-vault.md) · [skills-instincts.md](./skills-instincts.md) · [security-agentshield.md](./security-agentshield.md) · [PROVIDENCIAS.md](./PROVIDENCIAS.md)

---

## O que adoptar (padrões)

1. Loop plan→…→improve como **template de plan** de engenharia  
2. Review em **contexto fresco** (outro step/agent, não o mesmo que implementou)  
3. TDD / verify com **evidência** (done_when = testes)  
4. Memória em **markdown auditável**; índices (vector) secundários  
5. Scopes project vs user memory  
6. Instincts = padrões observados com **confidence** + promote gate  
7. Hooks para checks determinísticos (não “lembra-te de correr testes”)  
8. Profile de hooks: minimal | standard | strict  
9. Skill placement policy + provenance  
10. Supply-chain: só fontes oficiais; não empilhar installs  
11. AgentShield-class scan antes de hooks/MCP em prod  
12. Context budget / strategic compact  
13. Delivery gate antes de “done”  
14. Catalogar skills de **marketing/brand** do ECC como *referência* seletiva (seo, brand-voice, content-engine, marketing-campaign) — reescrever, não vendor dump  

## O que não adoptar por inteiro

- Plugin ECC como cérebro da rede multi-negócio  
- 68 agents + 286 skills no mesmo runtime  
- Dependência de Pro/GitHub App paga (OSS basta para padrões)  
- Memory vault ECC como único L4 de produção sem revisão  
- Stack de installs duplicados no mesmo harness  
