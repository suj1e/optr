---
name: optr
description: This skill should be used when the user asks to "run optr", "optimize PLAN.md", "create team for plan", "execute plan tasks", "automate task execution", or mentions project automation with teams. Automatically optimizes PLAN.md, creates a team to handle the defined tasks, and synchronizes all project documentation and scripts upon completion.
version: 0.6.2
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

**CRITICAL: Execute tool discovery script first!**

```bash
python3 optr-plugin/skills/optr/scripts/discover-tools.py PLAN.md
```

**This script will:**
1. Scan project-local tools (.claude/skills/, skills/ 等)
2. Scan global tools (~/.claude/plugins)
3. Show local matches, ask about GitHub search
4. Display matched tools with install commands

**YOU MUST run this command before proceeding.** The script output tells you which tools are available for optimizing PLAN.md.

**Output example:**
```
============================================================
🎯 Local Tools Matched to PLAN.md
============================================================
📁 Project-local: 0 skills, 0 agents, 0 commands
📦 Global installed: 16 skills, 3 agents, 2 commands

✅ Matching tools found:
------------------------------------------------------------
  1. 🏠 [LOCAL] skill-development
     Description: This skill should be used when...

============================================================
Options:
  [y] Search GitHub for more tools
  [n] Skip GitHub search, use local tools only
  [q] Quit without changes

👉 Search GitHub for additional tools? [y/n/q]:
```

**Tool Sources Priority:**
1. **Project-local** (score: 10) - Your project's own tools
2. **Global local** (score: 5) - Installed in ~/.claude/plugins
3. **GitHub** (score: 3-5) - Discoverable plugins with `claude plugin add <repo>`

**After execution:**
1. Review the matched tools list
2. If GitHub search was run, note install commands
3. Proceed to Step 3 with tool knowledge

### Step 3: Optimize PLAN.md with Professional Guidance

**CRITICAL: Run optimize-plan.py first!**

```bash
python3 optr-plugin/skills/optr/scripts/optimize-plan.py PLAN.md
```

**Then apply insights from matched tools:**
1. **Break down vague goals** into specific, actionable tasks
2. **Add context and acceptance criteria** using best practices from matched tools
3. **Identify dependencies** between tasks
4. **Suggest specialist roles** based on available agents

**Apply tool-specific best practices:**

| Task type | Apply this guidance |
|-----------|-------------------|
| skill creation | skill-development patterns |
| frontend UI | frontend-design principles |
| code review | code-review checklist |

**Finally, update PLAN.md using Edit tool.**

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

### Step 8: Monitor Task Execution

1. **Check progress:**
```bash
TaskList
```

2. **If incomplete:** Wait or assist teammates
3. **If blocked:** Help resolve dependencies

### Step 9: PLAN.md Completion Check

**Verify ALL tasks complete:**

```bash
TaskList
```

**Rule:** If ANY task is incomplete → STOP, inform user, do NOT clear PLAN.md.

### Step 10: PLAN.md Clear Confirmation

**Only execute after Step 9 confirms ALL tasks complete:**

**Ask user:**
```
✅ All tasks completed!

Options:
  [y] Clear PLAN.md (reset to template)
  [n] Keep PLAN.md as-is
  [q] Quit without changes

👉 Clear PLAN.md? [y/n/q]:
```

**Process choice:**
- `y`: Edit PLAN.md to reset template
- `n`: Keep current PLAN.md
- `q`: Exit

### Step 11: Auto-Update Documentation (Optional)

**Run sync-docs.py:**
```bash
python3 optr-plugin/skills/optr/scripts/sync-docs.py
```

**Then commit changes:**
```bash
git add PLAN.md README.md CLAUDE.md optr-plugin/
git commit -m "docs: update documentation"
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
- **Verify all tasks complete** - only clear PLAN.md when ALL tasks done (Step 9)
- **Ask before clearing** - let user decide whether to reset PLAN.md (Step 10)
- **Sync documentation** - auto-update docs after task completion (Step 11)

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

1. Read `PLAN.md`
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
- **`scripts/discover-tools.py`** - Scan local tools, search online for best practices, and match to PLAN.md content. Outputs recommended tools with installation commands for user selection
- **`scripts/optimize-plan.py`** - Analyze PLAN.md for optimization opportunities
