<!-- COPIA de agent-network-mcp/.claude/skills/idea-refine/scripts/idea-refine.sh — 2026-09-02 — setup only -->
#!/bin/bash
set -e

# This script helps initialize the ideas directory for the idea-refine skill.

IDEAS_DIR="docs/ideas"

if [ ! -d "$IDEAS_DIR" ]; then
  mkdir -p "$IDEAS_DIR"
  echo "Created directory: $IDEAS_DIR" >&2
else
  echo "Directory already exists: $IDEAS_DIR" >&2
fi

echo "{\"status\": \"ready\", \"directory\": \"$IDEAS_DIR\"}"
