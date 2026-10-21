#!/usr/bin/env bash
# Manual install: copies the skill into ~/.claude/skills (alternative to /plugin install).
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)/skills/alibaba-sourcing"
DEST="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/alibaba-sourcing"
if [ -d "$DEST" ]; then
  cp -R "$DEST" "$DEST.backup-$(date +%Y%m%d%H%M%S)"
  echo "Existing skill backed up next to $DEST"
fi
mkdir -p "$DEST"
cp "$SRC/SKILL.md" "$DEST/SKILL.md"
echo "Installed: $DEST"
echo "Restart Claude Code, then type /alibaba-sourcing"
