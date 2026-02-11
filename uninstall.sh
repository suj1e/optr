#!/bin/bash

# OPTR Skill Uninstall Script
# Usage: ./uninstall.sh

SKILL_DIR="$HOME/.claude/skills/optr"

if [ -d "$SKILL_DIR" ]; then
    rm -rf "$SKILL_DIR"
    echo "OPTR skill uninstalled successfully"
else
    echo "OPTR skill not found at $SKILL_DIR"
fi
