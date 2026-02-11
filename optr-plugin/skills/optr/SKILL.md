---
name: optr
description: This skill should be used when the user asks to "run optr", "optimize PLAN.md", "create team for plan", "execute plan tasks", "automate task execution", or mentions project automation with teams. Automatically optimizes PLAN.md, creates a team to handle the defined tasks, and synchronizes all project documentation and scripts upon completion.
version: 0.3.0
---

# OPTR - Optimizer & Team Runner

Optimize project plans and automate task execution using Claude Code teams.

## Purpose

OPTR (Optimizer & Team Runner) automates the workflow of:
1. Reading and optimizing the project PLAN.md file
2. Creating a team to execute the defined tasks
3. Coordinating task distribution among team members

## When to Use

Trigger this skill when:
- User types `/optr` in Claude CLI
- User asks to "run optr" or "execute optr"
- User wants to "optimize PLAN.md and create team"
- User mentions "automate my plan" or "task runner"

## Workflow

### Step 0: Check for PLAN.md

First, verify if PLAN.md exists in the current working directory:
```bash
ls PLAN.md 2>/dev/null || echo "PLAN.md not found"
```

**If PLAN.md does not exist:**
1. Inform the user that PLAN.md was not found
2. Ask if they want to create a new PLAN.md template
3. If yes, create a template using the structure from `examples/plan-template.md`
4. If no, exit gracefully with instructions on how to create PLAN.md manually

**Template creation:**
```bash
# Get the current directory name for project name
PROJECT_NAME=$(basename $(pwd))

# Create PLAN.md with template
cat > PLAN.md << 'EOF'
# PLAN - ${PROJECT_NAME}

## Project Overview
[Brief description of what this project aims to accomplish]

## Phase 1: Planning
- [ ] Define project requirements and scope
- [ ] Identify key features and deliverables
- [ ] Set up development environment

## Phase 2: Implementation
- [ ] Implement core features
- [ ] Add tests and documentation
- [ ] Deploy and verify

## Notes
- Add any important context, constraints, or technical decisions here
EOF
```

### Step 1: Read and Analyze PLAN.md

Once PLAN.md exists, read and analyze its content:
```bash
pwd  # Confirm working directory
cat PLAN.md  # Read the plan content
```

### Step 2: Discover Relevant Tools

Before optimizing, discover available professional tools that match the plan content:

```bash
# Scan for all available skills
find ~/.claude/plugins -name "SKILL.md" 2>/dev/null | head -30

# Scan for available agents
find ~/.claude/plugins -name "*-agent.md" 2>/dev/null | head -20

# Scan for available commands
find ~/.claude/plugins -name "*-command.md" 2>/dev/null | head -20
```

**Match tools to PLAN.md content:**

Use the mapping table in `references/tool-mapping.md` to find relevant tools based on keywords in the plan:

| PLAN.md contains | Match to tool |
|------------------|---------------|
| "create skill", "write skill" | skill-development |
| "build frontend", "design UI" | frontend-design |
| "code review", "review PR" | code-review, pr-review-toolkit |
| "update CLAUDE.md" | claude-md-improver |
| "create agent", "write agent" | agent-development |
| "create command" | command-development |
| "create hook" | hook-development |
| "MCP server" | mcp-integration |

**For each matched tool:**
1. Read the tool's SKILL.md or agent.md to understand its capabilities
2. Extract relevant best practices and patterns
3. Note any specific acceptance criteria or workflows recommended by the tool

**Example discovery workflow:**
```bash
# PLAN.md contains: "创建一个用户认证 skill"
# Extract keywords: ["创建", "skill"]
# Match: skill-development skill

# Read the skill-development skill
cat ~/.claude/plugins/.../skill-development/SKILL.md

# Extract best practices for skill creation
# Use these to optimize the task in PLAN.md
```

### Step 3: Optimize PLAN.md with Professional Guidance

Now optimize the plan using insights from discovered tools:

**Optimization process:**
1. **Break down vague goals** into specific, actionable tasks
2. **Add context and acceptance criteria** using best practices from matched tools
3. **Identify dependencies** between tasks
4. **Suggest specialist roles** based on available agents

**For each task, apply professional guidance:**

If the task matches `skill-development`:
- Reference skill-creator patterns
- Add progressive disclosure structure
- Include third-person description with triggers

If the task matches `frontend-design`:
- Reference design thinking principles
- Add aesthetic direction requirements
- Include production-grade criteria

If the task matches `code-review`:
- Add review checklist items
- Include quality gate criteria
- Reference testing requirements

**Create optimized PLAN.md with:**
- Clear task descriptions with imperative language
- Dependencies (blocks/blockedBy)
- Acceptance criteria from professional tools
- Suggested task owners or specialist roles
- References to relevant skills/agents

Update PLAN.md using the Edit tool with the optimized content.

### Step 4: Create a Team

Create a team using the TeamCreate tool:
- **Team name**: Use a descriptive name based on the project (e.g., "project-execution", "plan-runner")
- **Description**: Brief summary of what the team will accomplish
- **Agent type**: "general-purpose" for flexible task handling

Example:
```
TeamCreate with:
- team_name: "plan-execution"
- description: "Execute tasks from optimized PLAN.md"
```

### Step 5: Create Tasks from PLAN.md

Parse the optimized PLAN.md and create tasks using TaskCreate:
- Extract each task item from the plan
- Convert to TaskCreate format with:
  - **subject**: Brief imperative title (e.g., "Implement feature X")
  - **description**: Detailed requirements with context
  - **activeForm**: Present continuous form (e.g., "Implementing feature X")

**Include matched tool references in task descriptions:**
```
TaskCreate(
  subject="Create user authentication skill",
  description="Create a skill for user authentication using skill-development best practices...",
  activeForm="Creating user authentication skill",
  metadata={
    "matched_tool": "skill-development",
    "best_practices": ["progressive disclosure", "third-person description"]
  }
)
```

### Step 6: Spawn Teammates

Spawn teammates using the Task tool with the team_name parameter:
- Spawn 2-3 general-purpose agents as teammates
- Assign descriptive names (e.g., "developer-1", "developer-2", "tester")
- Each teammate joins the created team

**Optional: Spawn specialist teammates based on matched tools:**
```
# If PLAN.md contains frontend tasks
Task(
  subagent_type: "general-purpose",
  team_name: "plan-execution",
  name: "frontend-specialist",
  prompt: "You specialize in frontend design. Reference frontend-design skill..."
)
```

### Step 7: Assign and Execute Tasks

1. Assign tasks to teammates using TaskUpdate with the `owner` parameter
2. Set up dependencies using `addBlocks` and `addBlockedBy`
3. Monitor task progress through TaskList
4. Coordinate completion and cleanup

**Match tasks to teammates based on expertise:**
- Frontend tasks → Assign to teammate with frontend-design knowledge
- Skill creation → Assign to teammate with skill-development knowledge
- Code review → Assign to teammate with code-review expertise

### Step 8: Shutdown Team

After all tasks complete:
1. Use SendMessage to request shutdown from each teammate
2. Use TeamDelete to clean up team resources

### Step 9: Auto-Update Project Documentation & Scripts

After team shutdown and task completion, automatically synchronize all project documentation and scripts:

**Documents to update:**

1. **PLAN.md** - Update task completion status:
   - Mark completed tasks with `[x]`
   - Update phase progress indicators
   - Add notes about any changes or learnings

2. **README.md** - Reflect current project state:
   - Update installation instructions if changed
   - Add new commands or workflows
   - Update feature list based on completed work
   - Refresh examples with current patterns

3. **CLAUDE.md** - Sync with project architecture:
   - Update command references (build, test, lint)
   - Document new architectural patterns
   - Add new utility scripts
   - Update structure overview if codebase changed

4. **Plugin files** (if this is a plugin project):
   - Update `optr-plugin/skills/optr/SKILL.md` with new workflows
   - Refresh `optr-plugin/README.md` with new capabilities
   - Update version in `optr-plugin/.claude-plugin/plugin.json`

**Scripts to check and update:**

1. **Shebang check** - Ensure executable scripts have `#!/usr/bin/env python3`
2. **Reference validation** - Check for broken paths or missing imports
3. **Version sync** - Ensure version numbers are consistent across scripts
4. **TODO/FIXME tracking** - Report any pending items
5. **Code quality** - Check for print statements vs logging
6. **Docstring verification** - Ensure scripts have module docstrings

**Use sync-docs.py script:**

```bash
# Run automatic sync
python3 optr-plugin/skills/optr/scripts/sync-docs.py

# This will:
# - Update PLAN.md, README.md, CLAUDE.md
# - Check all project scripts for issues
# - Validate script references
# - Check dependencies
# - Bump plugin version
# - Generate sync report
```

**Update principles:**
- Preserve existing content structure
- Update only sections affected by completed tasks
- Maintain consistent formatting and style
- Add changelog entries for significant changes

**Example updates:**

For PLAN.md:
```markdown
## Phase 1: Skill Creation ✅
- [x] Study skill-creator documentation and best practices
- [x] Create optr-plugin with .claude-plugin/plugin.json
- [x] Implement main SKILL.md with proper triggers
```

For CLAUDE.md:
```markdown
## Commands

### Documentation Sync
```bash
python3 optr-plugin/skills/optr/scripts/sync-docs.py
```
Automatically updates PLAN.md, README.md, and CLAUDE.md after task completion.
```

**Commit updated documentation:**
```bash
git add PLAN.md README.md CLAUDE.md optr-plugin/
git commit -m "docs: update project documentation after task completion"
```

## Best Practices

- **Discover tools first** - scan for relevant skills/agents/commands before optimizing
- **Check for PLAN.md first** - create template if missing, don't fail silently
- **Always read PLAN.md first** - before making optimizations
- **Use professional guidance** - leverage matched tools for specialized tasks
- **Preserve user intent** - optimize clarity, don't change goals
- **Keep tasks focused** - break down large tasks into smaller ones
- **Clear dependencies** - use blocks/blockedBy to prevent blocking
- **Monitor progress** - check TaskList regularly
- **Clean shutdown** - always terminate teammates and delete team
- **Sync documentation** - auto-update all docs after task completion (Step 9)

## Handling Missing PLAN.md

When PLAN.md is not found:

1. **Inform the user**: Explain that PLAN.md was not found in the current directory
2. **Offer to create**: Ask if they want to create a template PLAN.md
3. **Use intelligent defaults**:
   - Use current directory name as project name
   - Include common phases (Planning, Implementation, Testing)
   - Add placeholder tasks for quick start
4. **Wait for user input**: Don't proceed with team creation until user confirms the plan

**Example interaction:**
```
User: /optr

OPTR: PLAN.md not found in /path/to/project.
Would you like me to create a template PLAN.md for you?

User: Yes

OPTR: Created PLAN.md with the following structure:
- Project Overview
- Phase 1: Planning (3 placeholder tasks)
- Phase 2: Implementation (3 placeholder tasks)

Please edit PLAN.md to add your specific tasks, then run /optr again.
```

## Example Usage

### When PLAN.md exists (with tool discovery):

User types `/optr`:

1. Read `/Users/sujie/workspace/dev/apps/optr/PLAN.md`
2. **Discover relevant tools:**
   - Scan for available skills/agents/commands
   - Match "创建 skill" → skill-development
   - Match "前端界面" → frontend-design
3. **Optimize with professional guidance:**
   - Apply skill-creator patterns to skill creation tasks
   - Apply frontend-design principles to UI tasks
4. Update PLAN.md with improved task structure and tool references
5. Create team "optr-execution"
6. Spawn teammates (including specialists if needed)
7. Create and assign tasks from the plan
8. Monitor execution until complete
9. **Auto-update documentation:** ✨
   - Mark completed tasks in PLAN.md
   - Update README.md with new workflows
   - Sync CLAUDE.md with current architecture
   - Commit documentation changes

### Example PLAN.md optimization:

**Before:**
```markdown
- 创建一个用户认证 skill
- 构建登录界面
```

**After (with tool matching):**
```markdown
- Create user authentication skill (skill-development)
  - Use progressive disclosure structure
  - Third-person description with triggers
  - Acceptance: Skill loads on "user auth" phrases
- Build login interface (frontend-design)
  - Apply design thinking principles
  - Production-grade aesthetic
  - Acceptance: Functional, accessible, responsive
```

### When PLAN.md does not exist:

User types `/optr`:

1. Check for PLAN.md in current directory - not found
2. Inform user and offer to create template
3. If user agrees, create PLAN.md with intelligent defaults
4. Instruct user to edit the plan before proceeding
5. Wait for user to run `/optr` again with updated plan

## Additional Resources

### Reference Files

- **`references/tool-mapping.md`** - Keyword to skill/agent/command mapping table
- **`references/team-workflow.md`** - Detailed team coordination patterns
- **`references/plan-optimization.md`** - PLAN.md optimization guidelines

### Example Files

- **`examples/plan-template.md`** - Template for well-structured plans
- **`examples/task-creation.sh`** - Example task parsing script

### Utility Scripts

- **`scripts/sync-docs.py`** - Auto-sync PLAN.md, README.md, CLAUDE.md after task completion
- **`scripts/discover-tools.py`** - Scan and match tools to PLAN.md content
- **`scripts/optimize-plan.py`** - Analyze PLAN.md for optimization opportunities
