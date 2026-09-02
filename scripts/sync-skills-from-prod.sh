#!/usr/bin/env bash
# Copia .claude/skills de agent-network-mcp (publico) para skills/claude neste setup.
# Producao NAO e alterada. Correr a partir da raiz de network-agents-setup:
#   bash scripts/sync-skills-from-prod.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
git clone --depth 1 https://github.com/souzalrns/agent-network-mcp.git "$TMP/prod"
mkdir -p "$ROOT/skills"
rm -rf "$ROOT/skills/claude"
cp -a "$TMP/prod/.claude/skills" "$ROOT/skills/claude"
find "$ROOT/skills/claude" -type f \( -name '*.md' -o -name '*.sh' \) | while read -r f; do
  rel="${f#$ROOT/skills/claude/}"
  if ! head -1 "$f" | grep -q 'COPIA de agent-network'; then
    { echo "<!-- COPIA de agent-network-mcp/.claude/skills/${rel} — sync script — setup only -->"; cat "$f"; } > "$f.tmp"
    mv "$f.tmp" "$f"
  fi
done
echo "OK: $(find "$ROOT/skills/claude" -type f | wc -l) ficheiros em skills/claude"
