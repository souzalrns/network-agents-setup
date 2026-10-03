#!/usr/bin/env bash
# Copia .claude/skills de agent-network-mcp (publico) para skills/claude neste setup.
# Producao NAO e alterada. Correr a partir da raiz de network-agents-setup:
#   bash scripts/sync-skills-from-prod.sh
#
# AU-10: a proveniencia fica em skills/claude/PROVENANCE.md (repo, commit, sha256 por
# ficheiro). Nao se escreve cabecalho nos ficheiros: um comentario antes do `---`
# parte o frontmatter, que os leitores exigem na 1.a linha
# (runner/plan_runner/skills.py:20, context_policy.py:60).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
git clone --depth 1 https://github.com/souzalrns/agent-network-mcp.git "$TMP/prod"
SRC_SHA=$(git -C "$TMP/prod" rev-parse HEAD)
mkdir -p "$ROOT/skills"
rm -rf "$ROOT/skills/claude"
cp -a "$TMP/prod/.claude/skills" "$ROOT/skills/claude"
N=$(find "$ROOT/skills/claude" -type f | wc -l)
{
  echo "# Proveniência de \`skills/claude/\`"
  echo
  echo "> Gerado por \`scripts/sync-skills-from-prod.sh\`. Não editar à mão: correr o script outra vez."
  echo
  echo "- **Origem:** \`souzalrns/agent-network-mcp\`, pasta \`.claude/skills/\`"
  echo "- **Commit da origem:** \`$SRC_SHA\`"
  echo "- **Data do sync:** $(date -u +%Y-%m-%d)"
  echo "- **Ficheiros:** $N"
  echo
  echo "Cópia de trabalho: editar aqui não altera a produção. Um ficheiro cujo sha256 já não"
  echo "bate com esta tabela foi editado depois do sync."
  echo
  echo "| Ficheiro | sha256 (12) |"
  echo "|---|---|"
  (cd "$ROOT/skills/claude" && find . -type f | sed 's|^\./||' | LC_ALL=C sort | while read -r f; do
    echo "| \`$f\` | \`$(sha256sum "$f" | cut -c1-12)\` |"
  done)
} > "$TMP/PROVENANCE.md"
mv "$TMP/PROVENANCE.md" "$ROOT/skills/claude/PROVENANCE.md"
echo "OK: $N ficheiros em skills/claude (origem $SRC_SHA)"
