# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OPTR (Optimizer & Team Runner) is a Claude Code skill plugin that automates project plan optimization and task execution. When a user types `/optr`, it:
1. Reads and optimizes `PLAN.md` using professional tool matching
2. Creates a team to execute the defined tasks
3. Coordinates task distribution among team members

The core innovation is **intelligent tool matching**: OPTR scans available Claude plugins (skills/agents/commands) and matches PLAN.md content to relevant professional tools, then applies their best practices to optimize tasks.

## Installation

Run the installation script:
```bash
./install.sh
```

Or manually copy the skill to Claude's skills directory:
```bash
cp -r optr-plugin/skills/optr ~/.claude/skills/optr
```

## Utility Scripts

### Documentation Sync
```bash
python3 optr-plugin/skills/optr/scripts/sync-docs.py
```
Automatically updates PLAN.md, README.md, and CLAUDE.md after task completion.

### Tool Discovery
```bash
python3 optr-plugin/skills/optr/scripts/discover-tools.py [path/to/PLAN.md]
```
Scans `~/.claude/plugins` for available skills/agents/commands, extracts keywords from their descriptions, and matches them to PLAN.md content with relevance scores.

### Plan Analysis
```bash
python3 optr-plugin/skills/optr/scripts/optimize-plan.py [path/to/PLAN.md]
```
Analyzes PLAN.md for vague tasks, oversized tasks, and missing acceptance criteria. Outputs optimization suggestions without creating a team.

## Architecture

### Skill Structure (Progressive Disclosure)

The skill follows Claude's progressive disclosure pattern to minimize context usage:

1. **Metadata** (always loaded): SKILL.md frontmatter with `name` and `description` containing trigger phrases like "run optr", "optimize PLAN.md", "automate task execution"

2. **SKILL.md body** (~2000 words): Core workflow - 8 steps from checking PLAN.md to team shutdown. Includes tool mapping table for keyword matching.

3. **References/** (loaded as needed):
   - `tool-mapping.md` - Complete keyword → skill/agent/command mappings
   - `team-workflow.md` - Team coordination patterns (TaskCreate, TaskUpdate, SendMessage, TeamDelete)
   - `plan-optimization.md` - PLAN.md formatting best practices

4. **Examples/** (working code): `plan-template.md`, `task-creation.py`

5. **Scripts/** (executable utilities): `discover-tools.py`, `optimize-plan.py`

### Tool Matching Algorithm

The `discover-tools.py` script implements the matching logic:

1. **Scan**: Find all SKILL.md, *-agent.md, *-command.md files in `~/.claude/plugins`
2. **Extract**: Parse YAML frontmatter for name/description, extract quoted trigger phrases
3. **Match**: Score tools by keyword overlap with PLAN.md content
4. **Rank**: Sort by relevance score, return top matches

Example mappings:
- `"create skill"` → `skill-development` (plugin-dev/skills/skill-development)
- `"build frontend"` → `frontend-design` (frontend-design/skills/frontend-design)
- `"code review"` → `code-review` (code-review/commands/code-review)

### SKILL.md Workflow

The 8-step workflow in SKILL.md is designed for AI execution:

- **Step 0**: Check for PLAN.md, create template if missing
- **Step 1**: Read and analyze PLAN.md content
- **Step 2**: Discover relevant tools (scan plugins, match keywords)
- **Step 3**: Optimize with professional guidance (apply matched tools' best practices)
- **Step 4-8**: Team creation, task generation, spawning, assignment, shutdown

Each step includes concrete bash commands and tool usage examples.

## Writing Style

All skill content uses **imperative/infinitive form** (not second person):
- ✅ "Create a team using TeamCreate tool"
- ❌ "You should create a team using TeamCreate tool"

Descriptions use **third-person** with specific trigger phrases:
```yaml
description: This skill should be used when the user asks to "run optr", "optimize PLAN.md"...
```

## Plugin Metadata

`optr-plugin/.claude-plugin/plugin.json` defines the plugin:
```json
{
  "name": "optr",
  "description": "Optimize PLAN.md and create teams to handle tasks",
  "version": "0.1.0"
}
```

## Local Permissions

`.claude/settings.local.json` allows necessary permissions:
- WebSearch, Bash for git operations, Python script execution, chmod

## Testing

After installing the plugin, test with:
```bash
cd /Users/sujie/workspace/dev/apps/optr
claude
# In Claude CLI, type: /optr
```
