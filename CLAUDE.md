# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OPTR (Optimizer & Team Runner) is a Claude Code skill plugin that automates project plan optimization and task execution. When a user types `/optr`, it:
1. Checks for PLAN.md, creates template if missing
2. Reads and analyzes PLAN.md content
3. Discovers relevant tools using a two-phase workflow:
   - **Phase 1**: Scan local tools, show matches, ask about GitHub search
   - **Phase 2**: If confirmed, search GitHub and show installable plugins
4. Optimizes PLAN.md with professional tool guidance
5. Creates a team to execute the defined tasks
6. Coordinates task distribution among team members
7. **(v0.9.0+)** Manages git worktrees for complex plans with on-demand isolation
8. Syncs documentation upon completion

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
python3 optr-plugin/skills/optr/scripts/discover-tools.py --verbose [path/to/PLAN.md]  # Detailed scan info
python3 optr-plugin/skills/optr/scripts/discover-tools.py --yes [path/to/PLAN.md]  # Auto-search GitHub
```
Two-phase workflow with forced output buffering for Claude CLI:
1. **Project-local**: Scans `.claude/skills/`, `skills/`, `.claude/agents/`, `agents/`, `.claude/commands/`, `commands/`
2. **Global**: Scans `~/.claude/plugins` for installed skills/agents/commands
3. **GitHub**: Uses WebSearch to find relevant plugins (after user confirms)

**Phase 1 Output:**
- Shows local matched tools (project + global installed)
- Displays count of tools found in each category
- Prompts user for GitHub search decision

**Phase 2 Output (if GitHub search confirmed):**
- Shows complete results with local and GitHub tools separated
- Lists installable GitHub tools with `claude plugin add` commands
- Provides summary of tool counts
- Shows recommended installation commands at the end

**Tool Priority:** project (score: 10) > global installed (score: 5) > GitHub (score: 3-5)

### Plan Analysis
```bash
python3 optr-plugin/skills/optr/scripts/optimize-plan.py [path/to/PLAN.md]
```
Analyzes PLAN.md for vague tasks, oversized tasks, and missing acceptance criteria. Outputs optimization suggestions without creating a team.

### Worktree Management (v0.9.0+)
```bash
python3 optr-plugin/skills/optr/scripts/worktree-manager.py analyze [path/to/PLAN.md]
python3 optr-plugin/skills/optr/scripts/worktree-manager.py create <task_id> <task_name>
python3 optr-plugin/skills/optr/scripts/worktree-manager.py list
python3 optr-plugin/skills/optr/scripts/worktree-manager.py remove <task_id>
python3 optr-plugin/skills/optr/scripts/worktree-manager.py cleanup --force
```
Strategy C: On-demand worktree creation for complex plan execution.
- **analyze**: Check if worktree support is needed (≥8 tasks, multi-module, or parallel work)
- **create**: Create isolated worktree for specific tasks (long-running or conflicting)
- **list/remove/cleanup**: Manage worktree lifecycle

**Worktree creation criteria:**
- Long-running tasks (> 1 hour estimated)
- File conflicts with other assigned tasks
- Explicit `requires_isolation: true` flag

**State tracking**: `.optr-worktrees.json` (add to `.gitignore`)

## Architecture

### Skill Structure (Progressive Disclosure)

The skill follows Claude's progressive disclosure pattern to minimize context usage:

1. **Metadata** (always loaded): SKILL.md frontmatter with `name` and `description` containing trigger phrases like "run optr", "optimize PLAN.md", "automate task execution"

2. **SKILL.md body** (~2000 words): Core workflow - 11 steps from checking PLAN.md to team shutdown. Includes tool mapping table for keyword matching.

3. **References/** (loaded as needed):
   - `tool-mapping.md` - Complete keyword → skill/agent/command mappings
   - `team-workflow.md` - Team coordination patterns (TaskCreate, TaskUpdate, SendMessage, TeamDelete)
   - `plan-optimization.md` - PLAN.md formatting best practices
   - `worktree-workflow.md` - Worktree management reference (v0.9.0+)

4. **Examples/** (working code): `plan-template.md`, `task-creation.py`, `worktree-example.sh`

5. **Scripts/** (executable utilities): `discover-tools.py`, `optimize-plan.py`, `worktree-manager.py`

### Tool Matching Algorithm

The `discover-tools.py` script implements the two-phase matching logic:

**Phase 1: Local Discovery**
1. **Scan Project-local**: Check `.claude/skills/`, `skills/`, `.claude/agents/`, `agents/`, `.claude/commands/`, `commands/`
2. **Scan Global**: Find all SKILL.md, *-agent.md, *-command.md files in `~/.claude/plugins`
3. **Display Local Matches**: Show matched local tools with source indicators (📁 project, 🏠 global)
4. **Prompt User**: Ask whether to search GitHub for additional tools

**Phase 2: GitHub Search (if confirmed)**
5. **Search GitHub**: Use WebSearch to find relevant plugins from GitHub based on PLAN.md keywords
6. **Merge and Deduplicate**: Combine all tools, removing duplicates by name
7. **Score**: Calculate relevance (project: 10, local: 5, github: 3-5)
8. **Rank**: Sort by score, priority: project > local > github
9. **Display Complete Results**: Separate local tools from installable GitHub tools
10. **Recommend Install Commands**: Show `claude plugin add <repo>` commands for GitHub tools

Example mappings:
- `"create skill"` → `skill-development` (local)
- `"build frontend"` → `frontend-design` (local)
- `"code review"` → `code-review` (github: `claude plugin add marketplaces/...`)
- Custom project tools → Found in project directories

### SKILL.md Workflow

The 14-step workflow in SKILL.md is designed for AI execution (v0.9.0+):

- **Step 0**: Check for PLAN.md, create template if missing
- **Step 1**: Read and analyze PLAN.md content
- **Step 2**: Discover relevant tools (scan plugins, match keywords)
- **Step 2.5**: Worktree Strategy Decision (conditional - analyze plan complexity)
- **Step 3**: Optimize with professional guidance (apply matched tools' best practices)
- **Step 4-7**: Team creation, task generation, spawning, assignment
- **Step 7.5**: Worktree Assignment (conditional - create worktrees for qualifying tasks)
- **Step 8**: Monitor task execution
- **Step 9**: Verify all tasks complete (BLOCKS Step 10)
- **Step 10**: PLAN.md Clear Confirmation (ask user before clearing)
- **Step 11**: Auto-sync documentation (README.md, CLAUDE.md, plugin files)
- **Step 11.5**: Worktree Cleanup (conditional - remove all worktrees)

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
  "version": "0.9.0"
}
```

**Version history:**
- v0.9.0: Added Strategy C worktree support for complex plans
- v0.8.0: Enhanced two-phase tool discovery workflow

## Local Permissions

`.claude/settings.local.json` allows necessary permissions:
- WebSearch, Bash for git operations, Python script execution, chmod

## Testing

After installing the plugin, test with:
```bash
cd /path/to/optr
claude
# In Claude CLI, type: /optr
```
