# OPTR - Optimizer & Team Runner

Automate project plan optimization and task execution using Claude Code teams with intelligent tool matching.

## What is OPTR?

OPTR is a Claude Code skill that:
1. **Reads and optimizes** your `PLAN.md` file
2. **Discovers relevant tools** (skills/agents/commands) based on plan content
3. **Applies professional guidance** from matched tools to optimize tasks
4. **Creates a team** to execute the defined tasks
5. **Coordinates** task distribution among team members
6. **Auto-syncs documentation** after task completion ✨

## Key Features

### 🧠 Intelligent Tool Matching

OPTR automatically scans your available Claude plugins and matches PLAN.md content to relevant professional tools:

- **Plugin Development**: skill-development, agent-development, command-development, hook-development
- **Frontend Design**: frontend-design for UI/components
- **Code Quality**: code-review, pr-review-toolkit
- **Documentation**: claude-md-improver
- **Feature Development**: feature-dev, code-architect

### 📋 Smart Plan Optimization

Uses matched tools' best practices to optimize your PLAN.md:
- Progressive disclosure structure
- Third-person descriptions with triggers
- Professional acceptance criteria
- Specialist role suggestions

### 👥 Team Coordination

Creates and manages teams with specialist teammates based on your project needs.

### 📚 Auto-Documentation Sync ✨

After task completion, automatically synchronizes all project documentation:
- **PLAN.md**: Mark completed tasks, add timestamps
- **README.md**: Update features and workflows
- **CLAUDE.md**: Sync with current architecture
- **plugin.json**: Bump version automatically

## Installation

Run the installation script:
```bash
./install.sh
```

Or manually copy the skill to Claude's skills directory:
```bash
cp -r optr-plugin/skills/optr ~/.claude/skills/optr
```

## Usage

Once installed, simply type in Claude CLI:

```
/optr
```

Or use any of these triggers:
- "run optr"
- "optimize PLAN.md and create team"
- "automate my plan"

## What OPTR Does

When triggered, OPTR will:

1. **Check for PLAN.md** - create template if missing
2. **Read and analyze** the plan content
3. **Discover relevant tools** by scanning available plugins
4. **Match tools to tasks** using keyword analysis
5. **Optimize with professional guidance** using matched tools
6. **Create a team** to handle the tasks
7. **Spawn teammates** including specialists if needed
8. **Assign tasks** based on the optimized plan
9. **Monitor progress** until completion
10. **Clean up** team resources when done
11. **Auto-sync documentation** ✨ - update all project docs and scripts

## Tool Matching Example

Given a PLAN.md containing:
```markdown
- 创建一个用户认证 skill
- 构建登录界面
```

OPTR will:
1. Match "创建 skill" → **skill-development** skill
2. Match "登录界面" → **frontend-design** skill
3. Apply best practices from each tool to optimize tasks

## Plugin Structure

```
optr-plugin/
├── .claude-plugin/
│   └── plugin.json           # Plugin metadata
├── skills/
│   └── optr/
│       ├── SKILL.md          # Main skill definition
│       ├── references/       # Detailed documentation
│       │   ├── tool-mapping.md       # Tool keyword mappings
│       │   ├── team-workflow.md      # Team coordination patterns
│       │   └── plan-optimization.md  # PLAN.md optimization guidelines
│       ├── examples/         # Example files
│       │   ├── plan-template.md
│       │   └── task-creation.py
│       └── scripts/          # Utility scripts
│           ├── sync-docs.py          # Documentation sync script ✨
│           ├── discover-tools.py      # Tool discovery script
│           ├── match_plugins.py      # AI semantic plugin matching
│           └── optimize-plan.py      # Plan analysis script
└── README.md
```

## PLAN.md Format

Your `PLAN.md` should contain actionable tasks:

```markdown
# Project: My Project

## Phase 1: Setup
- Initialize project structure
- Configure development environment

## Phase 2: Features
- Implement user authentication
- Build dashboard UI
- Add data export functionality
```

## Utility Scripts

### Documentation Sync ✨

```bash
python3 optr-plugin/skills/optr/scripts/sync-docs.py [project_directory]
```

Automatically synchronizes all project documentation after task completion:
- Updates PLAN.md with completion status and timestamps
- Refreshes README.md with new workflows and features
- Syncs CLAUDE.md with current architecture
- Bumps plugin version in plugin.json

### Tool Discovery

```bash
python3 optr-plugin/skills/optr/scripts/discover-tools.py [path/to/PLAN.md]
python3 optr-plugin/skills/optr/scripts/discover-tools.py --verbose [path/to/PLAN.md]  # Detailed scan info
python3 optr-plugin/skills/optr/scripts/discover-tools.py --yes [path/to/PLAN.md]  # Auto-search marketplace
```

Two-phase tool discovery with AI semantic matching from marketplace:
- **Phase 1**: Scans local tools, shows matches, asks about marketplace search
- **Phase 2**: If confirmed, uses AI to match PLAN.md with available marketplace plugins
- **Options**: `--verbose` for detailed scan info, `--yes` to skip marketplace prompt

### Marketplace Plugin Matching

```bash
python3 optr-plugin/skills/optr/scripts/match_plugins.py [path/to/PLAN.md]
```

Uses AI semantic analysis to match PLAN.md content with marketplace plugins:
- Queries `claude plugin list --available --json` for available plugins
- Uses Claude API to match based on semantic relevance (not just keywords)
- Returns plugins with relevance score >= 0.7
- Options: `--threshold <0.0-1.0>` (default: 0.7), `--api-key`, `--model`, `--verbose`

### Plan Analysis

```bash
python3 optr-plugin/skills/optr/scripts/optimize-plan.py [path/to/PLAN.md]
```

Analyzes your plan and suggests improvements without creating a team.

## Tool Mapping

OPTR uses intelligent keyword matching to find relevant tools:

| PLAN.md Content | Matched Tool |
|-----------------|--------------|
| "create skill" | skill-development |
| "build frontend" | frontend-design |
| "code review" | code-review |
| "CLAUDE.md" | claude-md-improver |
| "create agent" | agent-development |
| "create hook" | hook-development |

See `references/tool-mapping.md` for complete mapping table.

## Requirements

- Claude Code CLI
- A `PLAN.md` file in your project directory (auto-created if missing)

## License

MIT

---

Created with [skill-creator](https://code.claude.com/docs/en/skills)
