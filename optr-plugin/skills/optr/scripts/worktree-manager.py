#!/usr/bin/env python3
"""
OPTR Worktree Manager - Strategy C: On-demand Worktree Creation

This script manages git worktrees for complex plan execution:
- Creates worktrees on demand for long-running or conflicting tasks
- Tracks worktree assignments
- Cleans up worktrees when tasks complete
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


class WorktreeManager:
    """Manages git worktrees for OPTR task execution."""

    def __init__(self, repo_root: Optional[Path] = None, state_file: str = ".optr-worktrees.json"):
        self.repo_root = Path(repo_root) if repo_root else Path.cwd()
        self.state_file = self.repo_root / state_file
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load worktree state from file."""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {"worktrees": {}, "task_assignments": {}}

    def _save_state(self):
        """Save worktree state to file."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _run_git(self, *args) -> subprocess.CompletedProcess:
        """Run git command in repo root."""
        return subprocess.run(
            ["git"] + list(args),
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )

    def list_worktrees(self) -> List[Dict]:
        """List all git worktrees."""
        result = self._run_git("worktree", "list", "--porcelain")
        if result.returncode != 0:
            return []

        worktrees = []
        current = {}
        for line in result.stdout.strip().split('\n'):
            if not line:
                if current:
                    worktrees.append(current)
                    current = {}
                continue

            if line.startswith('worktree '):
                current['path'] = line[9:]
            elif line.startswith('branch '):
                current['branch'] = line[7:]
            elif line.startswith('HEAD '):
                current['head'] = line[5:]

        if current:
            worktrees.append(current)

        return worktrees

    def should_use_worktree(self, task: Dict) -> bool:
        """
        Determine if a task should use a separate worktree.

        Criteria for on-demand worktree creation:
        - Task marked as long-running (> 1 hour estimated)
        - Task has conflicts with other tasks (file paths overlap)
        - Task explicitly requests isolation
        """
        # Check explicit isolation flag
        if task.get("requires_isolation"):
            return True

        # Check for long-running flag
        if task.get("estimated_hours", 0) > 1:
            return True

        # Check for file conflicts with other assigned tasks
        task_id = task.get("id", "")
        task_files = set(task.get("files", []))

        for other_id, other_task in self.state.get("task_assignments", {}).items():
            if other_id == task_id:
                continue
            other_files = set(other_task.get("files", []))
            if task_files & other_files:  # Intersection exists
                return True

        return False

    def create_worktree(self, task_id: str, task_name: str, base_branch: str = "main") -> Optional[Dict]:
        """
        Create a new worktree for a task.

        Returns worktree info dict or None if failed.
        """
        # Generate branch name
        branch_name = f"optr/task-{task_id}"

        # Check if branch already exists
        result = self._run_git("branch", "--list", branch_name)
        if result.stdout.strip():
            # Branch exists, use it
            pass
        else:
            # Create new branch from base
            result = self._run_git("branch", branch_name, base_branch)
            if result.returncode != 0:
                print(f"Failed to create branch: {result.stderr}")
                return None

        # Create worktree directory
        worktree_name = f".optr-worktree-{task_id}"
        worktree_path = self.repo_root / worktree_name

        result = self._run_git(
            "worktree", "add",
            str(worktree_path),
            branch_name
        )

        if result.returncode != 0:
            print(f"Failed to create worktree: {result.stderr}")
            return None

        worktree_info = {
            "task_id": task_id,
            "task_name": task_name,
            "path": str(worktree_path),
            "branch": branch_name,
            "created": True
        }

        # Update state
        self.state["worktrees"][task_id] = worktree_info
        self.state["task_assignments"][task_id] = {
            "task_name": task_name,
            "worktree": worktree_name,
            "branch": branch_name
        }
        self._save_state()

        return worktree_info

    def get_worktree_for_task(self, task_id: str) -> Optional[Dict]:
        """Get worktree info for a task."""
        return self.state["worktrees"].get(task_id)

    def remove_worktree(self, task_id: str, force: bool = False) -> bool:
        """
        Remove a worktree after task completion.

        Returns True if successful, False otherwise.
        """
        worktree_info = self.state["worktrees"].get(task_id)
        if not worktree_info:
            print(f"No worktree found for task {task_id}")
            return False

        worktree_path = worktree_info.get("path")

        # Remove worktree
        args = ["worktree", "remove"]
        if force:
            args.append("--force")
        args.append(worktree_path)

        result = self._run_git(*args)

        if result.returncode != 0:
            print(f"Failed to remove worktree: {result.stderr}")
            return False

        # Update state
        del self.state["worktrees"][task_id]
        if task_id in self.state["task_assignments"]:
            del self.state["task_assignments"][task_id]
        self._save_state()

        return True

    def cleanup_all(self, force: bool = False) -> int:
        """
        Clean up all OPTR-managed worktrees.

        Returns number of worktrees removed.
        """
        removed = 0
        task_ids = list(self.state["worktrees"].keys())

        for task_id in task_ids:
            if self.remove_worktree(task_id, force=force):
                removed += 1

        return removed

    def analyze_plan_complexity(self, plan_content: str) -> Dict:
        """
        Analyze PLAN.md to determine if worktree support is needed.

        Returns dict with analysis results.
        """
        lines = plan_content.split('\n')

        # Count tasks (lines starting with - [ ])
        task_count = sum(1 for line in lines if line.strip().startswith('- ['))

        # Check for phase/module indicators
        has_modules = any(
            keyword in plan_content.lower()
            for keyword in ['module', 'component', 'service', 'frontend', 'backend']
        )

        # Check for complexity indicators
        has_parallel_work = any(
            keyword in plan_content.lower()
            for keyword in ['parallel', 'concurrent', 'simultaneous']
        )

        # Recommend worktree if:
        # - 8+ tasks
        # - OR 5+ tasks with modules
        # - OR explicit parallel work
        recommend_worktree = (
            task_count >= 8 or
            (task_count >= 5 and has_modules) or
            has_parallel_work
        )

        return {
            "task_count": task_count,
            "has_modules": has_modules,
            "has_parallel_work": has_parallel_work,
            "recommend_worktree": recommend_worktree,
            "reason": self._get_recommendation_reason(task_count, has_modules, has_parallel_work)
        }

    def _get_recommendation_reason(self, task_count: int, has_modules: bool, has_parallel: bool) -> str:
        """Get human-readable reason for recommendation."""
        if has_parallel:
            return "Plan contains parallel/concurrent work indicators"
        if task_count >= 8:
            return f"High task count ({task_count} tasks)"
        if task_count >= 5 and has_modules:
            return f"Moderate task count ({task_count}) with multiple modules"
        return "Single worktree is sufficient"


def main():
    parser = argparse.ArgumentParser(description="OPTR Worktree Manager")
    parser.add_argument("--repo", type=str, help="Repository root path")
    parser.add_argument("--state", type=str, default=".optr-worktrees.json", help="State file path")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    subparsers.add_parser("list", help="List all worktrees")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze PLAN.md for worktree needs")
    analyze_parser.add_argument("plan_file", help="Path to PLAN.md")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create worktree for task")
    create_parser.add_argument("task_id", help="Task identifier")
    create_parser.add_argument("task_name", help="Task name")
    create_parser.add_argument("--branch", default="main", help="Base branch")

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove worktree for task")
    remove_parser.add_argument("task_id", help="Task identifier")
    remove_parser.add_argument("--force", action="store_true", help="Force removal")

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up all worktrees")
    cleanup_parser.add_argument("--force", action="store_true", help="Force removal")

    # Should-use command (for task evaluation)
    should_parser = subparsers.add_parser("should-use", help="Check if task should use worktree")
    should_parser.add_argument("--json", type=str, help="Task JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    manager = WorktreeManager(repo_root=args.repo, state_file=args.state)

    if args.command == "list":
        worktrees = manager.list_worktrees()
        print(f"Found {len(worktrees)} worktrees:")
        for wt in worktrees:
            is_main = wt['path'] == str(manager.repo_root)
            marker = " (main)" if is_main else ""
            print(f"  - {wt['path']}{marker} [{wt.get('branch', 'detached')}]")

    elif args.command == "analyze":
        if not os.path.exists(args.plan_file):
            print(f"Error: Plan file not found: {args.plan_file}")
            return 1

        with open(args.plan_file, 'r') as f:
            plan_content = f.read()

        result = manager.analyze_plan_complexity(plan_content)

        print("\n" + "=" * 60)
        print("Worktree Analysis for PLAN.md")
        print("=" * 60)
        print(f"Task count: {result['task_count']}")
        print(f"Has modules: {result['has_modules']}")
        print(f"Has parallel work: {result['has_parallel_work']}")
        print()
        if result['recommend_worktree']:
            print("Recommendation: ENABLE worktree support")
            print(f"Reason: {result['reason']}")
        else:
            print("Recommendation: Single worktree is sufficient")
        print("=" * 60 + "\n")

        # Exit code: 0 if no worktree needed, 1 if worktree recommended
        return 0 if not result['recommend_worktree'] else 1

    elif args.command == "create":
        result = manager.create_worktree(args.task_id, args.task_name, args.branch)
        if result:
            print(f"Created worktree for task '{args.task_name}':")
            print(f"  Path: {result['path']}")
            print(f"  Branch: {result['branch']}")
            print(f"\nUse this path when assigning task to teammate:")
            print(f"  cd {result['path']}")
        else:
            print(f"Failed to create worktree for task '{args.task_name}'")
            return 1

    elif args.command == "remove":
        if manager.remove_worktree(args.task_id, force=args.force):
            print(f"Removed worktree for task {args.task_id}")
        else:
            print(f"Failed to remove worktree for task {args.task_id}")
            return 1

    elif args.command == "cleanup":
        count = manager.cleanup_all(force=args.force)
        print(f"Cleaned up {count} worktree(s)")

    elif args.command == "should-use":
        if args.json:
            task = json.loads(args.json)
            if manager.should_use_worktree(task):
                print("true")
            else:
                print("false")

    return 0


if __name__ == "__main__":
    sys.exit(main())
