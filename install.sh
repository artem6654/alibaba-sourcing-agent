#!/usr/bin/env bash
# Manual install: copies the skill into ~/.claude/skills (alternative to /plugin install).
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)/skills/alibaba-sourcing"
DEST="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/alibaba-sourcing"
if [ -d "$DEST" ]; then
  # Keep backups outside skills/, or Claude Code would load the old copy as a second skill.
  BACKUP="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skill-backups/alibaba-sourcing-$(date +%Y%m%d%H%M%S)"
  mkdir -p "$(dirname "$BACKUP")"
  cp -R "$DEST" "$BACKUP"
  echo "Existing skill backed up to $BACKUP"
fi
mkdir -p "$DEST"
cp "$SRC"/* "$DEST/"
echo "Installed: $DEST"
echo "Restart Claude Code, then type /alibaba-sourcing <product>"
