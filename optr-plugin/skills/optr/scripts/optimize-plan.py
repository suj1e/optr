#!/usr/bin/env python3
"""
Utility script to analyze and suggest optimizations for PLAN.md.

Usage:
    python scripts/optimize-plan.py [path/to/PLAN.md]

This script reads a PLAN.md file and provides optimization suggestions
for making tasks more actionable and well-structured.
"""

import sys
import re
from pathlib import Path


def analyze_plan(plan_path):
    """Analyze PLAN.md and provide optimization suggestions."""
    with open(plan_path, 'r') as f:
        content = f.read()

    suggestions = []
    tasks = []
    lines = content.split('\n')

    # Extract tasks
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('- ') or stripped.startswith('- [ ]'):
            task_text = stripped.replace('- [ ]', '').replace('- ', '').strip()
            if task_text:
                tasks.append({
                    'line': i + 1,
                    'text': task_text
                })

    # Check for vague task descriptions
    vague_words = ['fix', 'add', 'update', 'stuff', 'things', 'etc']
    for task in tasks:
        words = task['text'].lower().split()
        if any(word in vague_words for word in words):
            suggestions.append({
                'line': task['line'],
                'task': task['text'],
                'type': 'vague',
                'message': 'Task description is vague. Be more specific about what needs to be done.'
            })

    # Check for overly large tasks
    for task in tasks:
        word_count = len(task['text'].split())
        if word_count > 20:
            suggestions.append({
                'line': task['line'],
                'task': task['text'],
                'type': 'too-large',
                'message': 'Task might be too large. Consider breaking into smaller subtasks.'
            })

    # Check for missing acceptance criteria
    # Look for patterns like "Acceptance:" or "Criteria:" near tasks
    for i, task in enumerate(tasks):
        context_start = max(0, task['line'] - 3)
        context_end = min(len(lines), task['line'] + 3)
        context = '\n'.join(lines[context_start:context_end]).lower()

        if not any(word in context for word in ['acceptance', 'criteria', 'verify', 'test']):
            suggestions.append({
                'line': task['line'],
                'task': task['text'],
                'type': 'missing-criteria',
                'message': 'Task lacks acceptance criteria. Add what "done" looks like.'
            })

    return {
        'total_tasks': len(tasks),
        'suggestions': suggestions
    }


def print_report(analysis):
    """Print analysis report."""
    print(f"\n=== PLAN.md Analysis ===")
    print(f"Total tasks found: {analysis['total_tasks']}")
    print(f"Optimization suggestions: {len(analysis['suggestions'])}\n")

    if not analysis['suggestions']:
        print("✓ No issues found! Your plan looks well-structured.")
        return

    for suggestion in analysis['suggestions']:
        icon = {'vague': '⚠️', 'too-large': '📦', 'missing-criteria': '🎯'}.get(
            suggestion['type'], '💡'
        )
        print(f"{icon} Line {suggestion['line']}: {suggestion['message']}")
        print(f"   Task: \"{suggestion['task']}\"")
        print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python optimize-plan.py [path/to/PLAN.md]")
        print("Default: ./PLAN.md")
        plan_path = Path.cwd() / 'PLAN.md'
    else:
        plan_path = Path(sys.argv[1])

    if not plan_path.exists():
        print(f"Error: PLAN.md not found at {plan_path}")
        sys.exit(1)

    analysis = analyze_plan(plan_path)
    print_report(analysis)


if __name__ == '__main__':
    main()
