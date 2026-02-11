#!/bin/bash
set -e

# OPTR Plugin Installation Script
# Usage: ./install.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="$HOME/.claude/plugins/optr"

echo "Installing OPTR skill..."

# Create destination directory
mkdir -p "$HOME/.claude/skills"

# Copy skill files
rm -rf "$HOME/.claude/skills/optr"
cp -r "$SCRIPT_DIR/optr-plugin/skills/optr" "$HOME/.claude/skills/"

# Make scripts executable
chmod +x "$HOME/.claude/skills/optr/scripts/*.py" 2>/dev/null || true

echo "OPTR skill installed successfully to ~/.claude/skills/optr"
echo ""
echo "Usage:"
echo "  1. Run: claude"
echo "  2. Type: /optr"
echo ""
echo "To uninstall: rm -rf ~/.claude/skills/optr"
