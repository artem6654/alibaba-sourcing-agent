#!/usr/bin/env bash
# Manual install: copies the skill into ~/.claude/skills (alternative to /plugin install).
# Keeps only the most recent backup of the previous version; set KEEP_BACKUPS=N to keep more, 0 for none.
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)/skills/alibaba-sourcing"
CONFIG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
DEST="$CONFIG/skills/alibaba-sourcing"
BACKUP_DIR="$CONFIG/skill-backups"
KEEP="${KEEP_BACKUPS:-1}"
if [ -d "$DEST" ] && [ "$KEEP" -gt 0 ]; then
  # Keep backups outside skills/, or Claude Code would load the old copy as a second skill.
  BACKUP="$BACKUP_DIR/alibaba-sourcing-$(date +%Y%m%d%H%M%S)"
  mkdir -p "$BACKUP_DIR"
  cp -R "$DEST" "$BACKUP"
  echo "Previous version backed up to $BACKUP"
fi
if [ -d "$BACKUP_DIR" ]; then
  # Delete older backups of this skill, newest first, keeping $KEEP of them.
  OLD=$(ls -1dt "$BACKUP_DIR"/alibaba-sourcing* 2>/dev/null | tail -n +$((KEEP + 1)) || true)
  if [ -n "$OLD" ]; then
    echo "$OLD" | while IFS= read -r dir; do rm -rf -- "$dir"; echo "Removed old backup $dir"; done
  fi
fi
rm -rf -- "$DEST"
mkdir -p "$DEST"
cp -R "$SRC"/. "$DEST/"
echo "Installed: $DEST"
echo "Restart Claude Code, then type /alibaba-sourcing <product>"
