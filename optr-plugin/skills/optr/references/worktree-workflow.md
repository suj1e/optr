# Worktree Workflow Reference

This guide provides detailed reference information for the OPTR worktree workflow (Strategy C: On-demand Worktree Creation).

## Quick Reference

| Command | Purpose |
|---------|---------|
| `analyze PLAN.md` | Check if worktree support is needed |
| `create <task_id> <task_name>` | Create worktree for a task |
| `list` | List all worktrees |
| `remove <task_id>` | Remove worktree after task completion |
| `cleanup --force` | Clean up all worktrees |

## Workflow Integration

The worktree workflow integrates into OPTR at these points:

```
Step 0: Check for PLAN.md
   ↓
Step 1: Read and Analyze PLAN.md
   ↓
Step 2: Discover Relevant Tools
   ↓
Step 2.5: Worktree Strategy Decision ← NEW
   ↓ (if enabled)
Step 3: Optimize PLAN.md
   ↓
Step 4: Create a Team
   ↓
Step 5: Create Tasks from PLAN.md
   ↓
Step 6: Spawn Teammates
   ↓
Step 7: Assign and Execute Tasks
   ↓
Step 7.5: Worktree Assignment ← NEW (conditional)
   ↓
Step 8: Monitor Task Execution
   ↓
Step 9: PLAN.md Completion Check
   ↓
Step 10: PLAN.md Clear Confirmation
   ↓
Step 11: Auto-Update Documentation
   ↓
Step 11.5: Worktree Cleanup ← NEW (conditional)
```

## Complexity Analysis

The worktree analyzer evaluates:

| Factor | Threshold | Weight |
|--------|-----------|--------|
| Task count | ≥ 8 tasks | High |
| Task count with modules | ≥ 5 + modules | Medium |
| Explicit parallel work | Any | High |

**Recommendation triggers:**
- `task_count >= 8` → High complexity, recommend worktree
- `task_count >= 5 AND has_modules` → Medium complexity, recommend worktree
- `has_parallel_work` → Always recommend worktree

## Task Worktree Eligibility

Individual tasks qualify for worktree if:

| Condition | Description |
|-----------|-------------|
| `requires_isolation: true` | Task explicitly requests isolation |
| `estimated_hours > 1` | Long-running task |
| File conflicts | Task files overlap with other assigned tasks |

## Worktree Naming Convention

```
Directory: .optr-worktree-<task_id>
Branch: optr/task-<task_id>
Example: .optr-worktree-task-1 → branch: optr/task-task-1
```

## State File Format

`.optr-worktrees.json` structure:

```json
{
  "worktrees": {
    "task-1": {
      "task_id": "task-1",
      "task_name": "Build frontend module",
      "path": "/absolute/path/.optr-worktree-task-1",
      "branch": "optr/task-task-1",
      "created": true
    }
  },
  "task_assignments": {
    "task-1": {
      "task_name": "Build frontend module",
      "worktree": ".optr-worktree-task-1",
      "branch": "optr/task-task-1"
    }
  }
}
```

## .gitignore Entries

Add these entries to your project's `.gitignore`:

```gitignore
# OPTR Worktree Manager
.optr-worktrees.json
.optr-worktree-*/
```

## Task Metadata with Worktree

When assigning a task to a worktree, include metadata:

```python
TaskUpdate(
  taskId="task-1",
  owner="developer-1",
  metadata={
    "worktree_path": "/path/to/.optr-worktree-task-1",
    "branch": "optr/task-task-1"
  }
)
```

## Cleanup Strategy

**After each task:**
1. Verify task completion
2. Create/merge PR if needed
3. Remove individual worktree: `remove <task_id>`

**After session:**
1. Verify all tasks complete
2. Run cleanup: `cleanup --force`
3. Remove state file: `rm .optr-worktrees.json`

## Example Session

```bash
# Step 1: Analyze plan
python3 optr-plugin/skills/optr/scripts/worktree-manager.py analyze PLAN.md
# Output: ENABLE worktree support (8 tasks)

# Step 2: Create worktree for task-1
python3 optr-plugin/skills/optr/scripts/worktree-manager.py create task-1 "Build frontend"
# Output: Created worktree at .optr-worktree-task-1

# Step 3: Assign task to teammate with worktree context
TaskUpdate(taskId="task-1", owner="dev-1", metadata={...})

# Step 4: After task completes, clean up
python3 optr-plugin/skills/optr/scripts/worktree-manager.py remove task-1

# Step 5: End of session cleanup
python3 optr-plugin/skills/optr/scripts/worktree-manager.py cleanup --force
```

## Troubleshooting

**Worktree already exists:**
```bash
git worktree list
# Manually remove if stale: git worktree remove <path>
```

**Branch already exists:**
```bash
git branch -D optr/task-<task_id>
# Then retry create
```

**State file corrupted:**
```bash
rm .optr-worktrees.json
# Worktree manager will recreate on next run
```

## Best Practices

1. **Always analyze first** - Run `analyze` before creating worktrees
2. **Clean up promptly** - Remove worktrees after tasks complete
3. **Use force carefully** - `--force` can delete uncommitted changes
4. **Track assignments** - Use state file to avoid duplicate worktrees
5. **Communicate paths** - Always provide worktree path to teammates
