#!/bin/bash
# Example: Using OPTR with Worktree Support
# This script demonstrates the complete workflow when worktree support is enabled

set -e

PROJECT_ROOT="$(pwd)"
OPTR_SCRIPTS="$PROJECT_ROOT/optr-plugin/skills/optr/scripts"

echo "============================================"
echo "OPTR Worktree Workflow Example"
echo "============================================"
echo ""

# Step 1: Check PLAN.md exists
if [ ! -f "PLAN.md" ]; then
  echo "Error: PLAN.md not found. Please create one first."
  exit 1
fi

# Step 2: Analyze plan complexity
echo "Step 1: Analyzing PLAN.md for worktree needs..."
# Allow non-zero exit for analyze command
set +e
python3 "$OPTR_SCRIPTS/worktree-manager.py" analyze PLAN.md
ANALYSIS_EXIT=$?
set -e

echo ""

if [ $ANALYSIS_EXIT -eq 0 ]; then
  echo "Result: Single worktree is sufficient."
  echo "Proceeding with standard workflow..."
  # Standard workflow without worktrees
  exit 0
fi

echo "Result: Worktree support recommended."
echo ""

# Step 3: Discover tools (standard step)
echo "Step 2: Discovering relevant tools..."
# Note: In production, Claude would handle the interactive prompts
# For demo, use --yes to auto-confirm GitHub search
set +e
python3 "$OPTR_SCRIPTS/discover-tools.py" --yes PLAN.md || true
set -e
echo ""

# Step 4: Optimize plan (standard step)
echo "Step 3: Optimizing PLAN.md..."
# Allow non-zero exit for optimize-plan command
set +e
python3 "$OPTR_SCRIPTS/optimize-plan.py" PLAN.md
set -e
echo ""

# At this point, Claude would:
# - Create team (TeamCreate)
# - Parse tasks from PLAN.md
# - Create tasks (TaskCreate)
# - Spawn teammates (Task with team_name)
echo "Step 4-6: Team creation and task spawning (handled by Claude)..."
echo ""

# Step 5: Example worktree creation for specific tasks
echo "Step 7.5: Example worktree assignments..."
echo ""

# Example: Task 1 needs worktree (long-running)
echo "Creating worktree for task-1 (Build frontend - 2 hours estimated)..."
python3 "$OPTR_SCRIPTS/worktree-manager.py" create \
  "task-1" \
  "Build frontend module" \
  --branch main

echo ""

# Example: Task 2 doesn't need worktree (quick task)
echo "Task-2 (Write tests - 30 minutes) uses main worktree"
echo ""

# Example: Task 3 needs worktree (file conflicts)
echo "Creating worktree for task-3 (Refactor API - conflicts with task-2)..."
python3 "$OPTR_SCRIPTS/worktree-manager.py" create \
  "task-3" \
  "Refactor API endpoints" \
  --branch main

echo ""
echo "Active worktrees:"
python3 "$OPTR_SCRIPTS/worktree-manager.py" list
echo ""

# At task completion time...
echo "============================================"
echo "After Task Completion"
echo "============================================"
echo ""

echo "Step 11.5: Cleaning up worktrees..."
echo ""

# Remove individual worktrees
echo "Removing worktree for completed task-1..."
python3 "$OPTR_SCRIPTS/worktree-manager.py" remove "task-1"

echo ""
echo "Removing worktree for completed task-3..."
python3 "$OPTR_SCRIPTS/worktree-manager.py" remove "task-3"

echo ""
echo "Final state:"
python3 "$OPTR_SCRIPTS/worktree-manager.py" list

echo ""
echo "Cleanup complete!"
echo ""
echo "============================================"
echo "Summary"
echo "============================================"
echo "Worktree workflow executed successfully."
echo "Tasks used isolated environments when needed."
echo "All worktrees cleaned up after completion."
echo ""
