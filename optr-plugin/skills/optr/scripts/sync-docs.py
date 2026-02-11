#!/usr/bin/env python3
"""
Documentation Synchronization Script for OPTR

Automatically updates project documentation after task completion:
- PLAN.md: Update task completion status
- README.md: Reflect current project state
- CLAUDE.md: Sync with project architecture

Usage:
    python scripts/sync-docs.py [project_directory]

This script is automatically called by OPTR after team task completion.
"""

import sys
import re
from pathlib import Path
from datetime import datetime


def update_plan_markdown(plan_path):
    """Update PLAN.md with completed task markers."""
    if not plan_path.exists():
        print(f"  ⚠️  PLAN.md not found at {plan_path}")
        return False

    content = plan_path.read_text()
    original_content = content

    # Auto-mark tasks as complete if they contain "✅" or similar indicators
    # This is a heuristic - actual completion tracking would come from TaskList

    # Ensure consistent formatting of completed tasks
    content = re.sub(r'- \[x\](.*)', r'- [x]\1 ✅', content)

    # Add/update last updated timestamp
    if "Last Updated:" in content:
        content = re.sub(
            r'Last Updated:.*',
            f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
            content
        )
    else:
        # Add timestamp after the title
        content = re.sub(
            r'(^(# .+)$)',
            r'\1\n\n_Last Updated: ' + datetime.now().strftime("%Y-%m-%d %H:%M") + '_',
            content,
            count=1
        )

    if content != original_content:
        plan_path.write_text(content)
        print(f"  ✅ Updated PLAN.md")
        return True
    else:
        print(f"  ℹ️  PLAN.md already up to date")
        return False


def update_readme(readme_path, changes_summary):
    """Update README.md based on project changes."""
    if not readme_path.exists():
        print(f"  ⚠️  README.md not found at {readme_path}")
        return False

    content = readme_path.read_text()
    original_content = content

    # Add changelog section if not exists
    if "## Changelog" not in content and changes_summary:
        changelog_entry = f"\n## Changelog\n\n### {datetime.now().strftime('%Y-%m-%d')}\n\n"
        for change in changes_summary:
            changelog_entry += f"- {change}\n"
        content += changelog_entry
    elif "## Changelog" in content and changes_summary:
        # Add new entry to existing changelog
        new_entry = f"\n### {datetime.now().strftime('%Y-%m-%d')}\n\n"
        for change in changes_summary:
            new_entry += f"- {change}\n"
        # Insert after the Changelog heading
        content = re.sub(
            r'(## Changelog\n)',
            r'\1' + new_entry,
            content,
            count=1
        )

    if content != original_content:
        readme_path.write_text(content)
        print(f"  ✅ Updated README.md")
        return True
    else:
        print(f"  ℹ️  README.md already up to date")
        return False


def update_claude_md(claude_md_path, project_dir):
    """Update CLAUDE.md with current project structure."""
    if not claude_md_path.exists():
        print(f"  ⚠️  CLAUDE.md not found at {claude_md_path}")
        return False

    content = claude_md_path.read_text()
    original_content = content

    # Update utility scripts section if new scripts exist
    scripts_dir = project_dir / "optr-plugin" / "skills" / "optr" / "scripts"
    if scripts_dir.exists():
        scripts = list(scripts_dir.glob("*.py"))
        script_names = [s.name for s in scripts]

        # Check if sync-docs.py should be documented
        if "sync-docs.py" in script_names and "sync-docs.py" not in content:
            # Find the utility scripts section and add the new script
            if "## Utility Scripts" in content or "### Utility Scripts" in content:
                sync_docs_entry = "\n### Documentation Sync\n```bash\npython3 optr-plugin/skills/optr/scripts/sync-docs.py\n```\nAutomatically updates PLAN.md, README.md, and CLAUDE.md after task completion.\n"

                # Insert after the utility scripts section header
                content = re.sub(
                    r'(## Utility Scripts\n)',
                    r'\1' + sync_docs_entry,
                    content
                )

    if content != original_content:
        claude_md_path.write_text(content)
        print(f"  ✅ Updated CLAUDE.md")
        return True
    else:
        print(f"  ℹ️  CLAUDE.md already up to date")
        return False


def update_plugin_version(plugin_json_path):
    """Bump plugin version after changes."""
    if not plugin_json_path.exists():
        return False

    import json

    content = plugin_json_path.read_text()
    try:
        plugin_data = json.loads(content)
        version = plugin_data.get("version", "0.1.0")

        # Bump patch version
        parts = version.split(".")
        if len(parts) == 3:
            patch = int(parts[2]) + 1
            new_version = f"{parts[0]}.{parts[1]}.{patch}"
            plugin_data["version"] = new_version

            plugin_json_path.write_text(json.dumps(plugin_data, indent=2))
            print(f"  ✅ Bumped plugin version: {version} → {new_version}")
            return True
    except Exception as e:
        print(f"  ⚠️  Failed to update plugin version: {e}")

    return False


def main():
    if len(sys.argv) > 1:
        project_dir = Path(sys.argv[1])
    else:
        project_dir = Path.cwd()

    print(f"\n📚 OPTR Documentation Sync")
    print(f"   Project: {project_dir}\n")

    changes = []

    # Check for changes to document
    # In a real implementation, this would analyze git diff or task results

    # Update documentation files
    plan_path = project_dir / "PLAN.md"
    readme_path = project_dir / "README.md"
    claude_md_path = project_dir / "CLAUDE.md"
    plugin_json_path = project_dir / "optr-plugin" / ".claude-plugin" / "plugin.json"

    print("Updating documentation files...")
    update_plan_markdown(plan_path)
    update_readme(readme_path, changes)
    update_claude_md(claude_md_path, project_dir)
    update_plugin_version(plugin_json_path)

    print(f"\n✨ Documentation sync complete!\n")

    # Suggest git commit
    print("Suggested git commit:")
    print("  git add PLAN.md README.md CLAUDE.md optr-plugin/")
    print('  git commit -m "docs: update project documentation after task completion"')
    print()


if __name__ == "__main__":
    main()
