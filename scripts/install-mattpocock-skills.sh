#!/bin/sh
# Instala 6 skills de mattpocock/skills (adaptadas) no Claude Code de um repo.
# Gerado por scripts/vendor_mattpocock_skills.py; não editar à mão.
# Origem: mattpocock/skills@49dd158d1076134a641b33efb035946536778336 (MIT). Adaptações em vendor/mattpocock-skills/PROVENANCE.md.
#
# Corre TU, no teu terminal: o skill-scout recusa aprovações vindas de um agente de IA.
# Ao correr isto aprovas o conteúdo pelos hashes abaixo.
#   pip install -e oss/skill-scout            # uma vez
#   sh scripts/install-mattpocock-skills.sh .                     # neste repo (network-agents-setup)
#   sh scripts/install-mattpocock-skills.sh ../agent-network-mcp  # ou noutro
# Depois, no repo de destino: commit de .claude/skills/, skill-scout.lock.json e skill-scout.audit.jsonl.
# O hook do git-guardrails só fica activo depois do passo 3 da skill (settings.json): pede-o ao Claude.
set -eu
NAS="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:?uso: sh scripts/install-mattpocock-skills.sh <caminho do repo de destino>}"
cd "$DEST"
one() { skill-scout install "$NAS/vendor/mattpocock-skills/skills/$1" --dest .claude/skills --approve-sha256 "$2"; }
one git-guardrails-claude-code b971c5ef57c301f87674943d3e2d55117a7639fd03c80e3589e3b9b3bb35b877
one handoff 9c62a143a7fe682ffe26207f0ce89231e1523ec6163d73994d16d5113764175a
one retro 9615c30c5ebd6eabd98e1e4e8ab6bf65744339e6121f9473137f8805009cc590
one to-questionnaire 52d0c00a3c68e51c6497f61426c36da477d5b1db8a36d6ef39dcee78dac31302
one wizard 466f18ce420ffac902b767135da22e93f3eb3af1d1ea8611e29a811ba5ce363a
one writing-for-agents ec4e1bb536125d6de2ac2a7a14af877a9b4198ef085eac455fc237fc678645fb
skill-scout verify
echo "ok: 6 skills de mattpocock/skills instaladas em $DEST/.claude/skills"
