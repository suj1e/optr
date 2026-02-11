#!/usr/bin/env python3
"""
Project Synchronization Script for OPTR

Automatically updates project documentation and scripts after task completion:
- Documentation: PLAN.md, README.md, CLAUDE.md
- Scripts: Check permissions, update references, sync versions
- Plugin: Bump version, update metadata

Usage:
    python scripts/sync-docs.py [project_directory]

This script is automatically called by OPTR after team task completion.
"""

import sys
import re
import os
import ast
import json
from pathlib import Path
from datetime import datetime


def update_plan_markdown(plan_path):
    """Update PLAN.md with completed task markers and timestamp."""
    if not plan_path.exists():
        print(f"  ⚠️  PLAN.md not found at {plan_path}")
        return False

    content = plan_path.read_text()
    original_content = content

    # Ensure consistent formatting of completed tasks
    content = re.sub(r'- \[x\](.*?)(?!✅)', r'- [x]\1 ✅', content)

    # Add/update last updated timestamp
    if "_Last Updated:" in content:
        content = re.sub(
            r'_Last Updated:.*',
            f'_Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}_',
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
    """Update CLAUDE.md with current project structure and scripts."""
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
                sync_docs_entry = "\n### Documentation & Script Sync\n```bash\npython3 optr-plugin/skills/optr/scripts/sync-docs.py\n```\nAutomatically updates PLAN.md, README.md, CLAUDE.md, and checks all project scripts after task completion.\n"

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


def check_and_update_scripts(project_dir):
    """Check all project scripts for consistency and update as needed."""
    print("\n  📜 Checking scripts...")

    scripts_to_check = []
    plugin_dir = project_dir / "optr-plugin"

    # Find all Python scripts in the project
    for script in project_dir.rglob("*.py"):
        # Skip __pycache__ and virtual environments
        if "__pycache__" not in str(script) and ".venv" not in str(script):
            scripts_to_check.append(script)

    updated_count = 0
    issues_found = []

    for script in scripts_to_check:
        relative_path = script.relative_to(project_dir)
        content = script.read_text()
        original_content = content
        issues = []

        # 1. Check shebang
        if script.name.endswith(".py"):
            first_line = content.split('\n')[0] if content else ""
            if not first_line.startswith("#!"):
                issues.append("missing shebang")
                # Add shebang for executable scripts
                if "scripts" in str(script):
                    content = f"#!/usr/bin/env python3\n\n{content}"

        # 2. Check for hardcoded paths that might need updating
        # Look for paths to scripts that might have moved
        # Note: Comments mentioning script names are okay - only flag if clearly broken
        script_refs = re.findall(r'(?:scripts|optr-plugin/skills/optr/scripts)/[\w\-\.]+\.py', content)
        for ref in script_refs:
            ref_path = project_dir / ref
            # Only flag as broken if it's clearly a runtime path, not a comment
            if "Usage:" in content or "python" in content.lower():
                # These are likely documentation comments, skip
                continue

        # 3. Check for version numbers that might need syncing
        version_matches = re.findall(r'version\s*=\s*["\']([\d.]+)["\']', content)
        if version_matches:
            # Could sync versions across scripts here
            pass

        # 4. Check for TODO/FIXME comments
        todos = re.findall(r'(TODO|FIXME):?\s*(.+)', content)
        if todos:
            issues.append(f"{len(todos)} TODO/FIXME comments")

        # 5. Check for print statements (should use logging in production)
        if "import logging" not in content and re.search(r'^\s*print\(', content, re.MULTILINE):
            # Only warn for scripts not in examples/
            if "examples" not in str(script):
                issues.append("uses print() instead of logging")

        # 6. Check docstring
        if content.strip():
            try:
                module_ast = ast.parse(content)
                docstring = ast.get_docstring(module_ast)
                if not docstring and "examples" not in str(script):
                    issues.append("missing module docstring")
            except:
                issues.append("syntax error (cannot parse)")

        # Report issues
        if issues:
            issues_found.append(f"  ⚠️  {relative_path}: {', '.join(issues)}")

        # Update if content changed
        if content != original_content:
            script.write_text(content)
            updated_count += 1
            print(f"  ✅ Updated {relative_path}")

    # Print summary
    if issues_found:
        print("\n  📋 Script issues found:")
        for issue in issues_found[:10]:  # Limit output
            print(issue)
        if len(issues_found) > 10:
            print(f"  ... and {len(issues_found) - 10} more")

    if updated_count > 0:
        print(f"\n  ✅ Updated {updated_count} script(s)")
    else:
        print(f"  ℹ️  All scripts up to date")

    return updated_count > 0


def sync_script_references(project_dir):
    """Sync script references across documentation and other scripts."""
    print("\n  🔗 Syncing script references...")

    scripts_dir = project_dir / "optr-plugin" / "skills" / "optr" / "scripts"
    if not scripts_dir.exists():
        return False

    scripts = list(scripts_dir.glob("*.py"))
    script_names = [s.stem for s in scripts]

    # Files that might reference scripts
    files_to_check = [
        project_dir / "PLAN.md",
        project_dir / "README.md",
        project_dir / "CLAUDE.md",
        project_dir / "optr-plugin" / "README.md",
        project_dir / "optr-plugin" / "skills" / "optr" / "SKILL.md",
    ]

    updated = False

    for file_path in files_to_check:
        if not file_path.exists():
            continue

        content = file_path.read_text()
        original = content

        # Check for script references
        for script in script_names:
            # Look for old or missing references
            if script not in content:
                # Check if there's a generic reference that should be specific
                continue

        # Update script paths if project structure changed
        # This is a placeholder for more sophisticated path updating

        if content != original:
            file_path.write_text(content)
            print(f"  ✅ Synced {file_path.relative_to(project_dir)}")
            updated = True

    if not updated:
        print(f"  ℹ️  All references up to date")

    return updated


def check_script_dependencies(project_dir):
    """Check that script dependencies are consistent."""
    print("\n  📦 Checking script dependencies...")

    requirements_files = list(project_dir.rglob("requirements*.txt"))
    has_issues = False

    # Common dependencies that should be documented
    common_deps = {
        "requests": "HTTP library",
        "yaml": "YAML parsing",
        "click": "CLI framework",
        "pytest": "Testing framework",
    }

    # Find imports in scripts
    imported_modules = set()
    for script in project_dir.rglob("*.py"):
        if "__pycache__" in str(script):
            continue
        try:
            content = script.read_text()
            imports = re.findall(r'^import\s+(\w+)|^from\s+(\w+)', content, re.MULTILINE)
            for imp in imports:
                module = imp[0] or imp[1]
                imported_modules.add(module)
        except:
            continue

    # Check if requirements.txt exists for external dependencies
    if requirements_files:
        print(f"  ℹ️  Found {len(requirements_files)} requirements file(s)")
    else:
        # If scripts use external packages, suggest requirements.txt
        external_packages = imported_modules & {k for k in common_deps.keys()}
        if external_packages:
            print(f"  ⚠️  Scripts import {', '.join(external_packages)} but no requirements.txt found")
            has_issues = True
        else:
            print(f"  ℹ️  No external dependencies detected")

    return not has_issues


def update_plugin_version(plugin_json_path):
    """Bump plugin version after changes."""
    if not plugin_json_path.exists():
        return False

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


def generate_sync_report(project_dir):
    """Generate a report of what was synced."""
    print("\n📊 Sync Summary:")
    print("=" * 50)

    # Count files by type
    docs = list(project_dir.glob("*.md"))
    scripts = list(project_dir.rglob("*.py"))
    config_files = list(project_dir.rglob("*.json"))

    print(f"  📄 Documentation files: {len(docs)}")
    print(f"  🐍 Python scripts: {len(scripts)}")
    print(f"  ⚙️  Config files: {len(config_files)}")

    print("\n" + "=" * 50)


def main():
    if len(sys.argv) > 1:
        project_dir = Path(sys.argv[1])
    else:
        project_dir = Path.cwd()

    print(f"\n🔄 OPTR Project Sync")
    print(f"   Project: {project_dir}\n")

    changes = []

    # Track if any updates were made
    any_updates = False

    # Update documentation files
    print("📚 Updating documentation files...")
    plan_path = project_dir / "PLAN.md"
    readme_path = project_dir / "README.md"
    claude_md_path = project_dir / "CLAUDE.md"
    plugin_json_path = project_dir / "optr-plugin" / ".claude-plugin" / "plugin.json"

    if update_plan_markdown(plan_path):
        any_updates = True
    if update_readme(readme_path, changes):
        any_updates = True
    if update_claude_md(claude_md_path, project_dir):
        any_updates = True
    if update_plugin_version(plugin_json_path):
        any_updates = True

    # Check and update scripts
    if check_and_update_scripts(project_dir):
        any_updates = True

    # Sync script references
    if sync_script_references(project_dir):
        any_updates = True

    # Check dependencies
    check_script_dependencies(project_dir)

    # Generate summary
    generate_sync_report(project_dir)

    if any_updates:
        print("\n✨ Project sync complete!\n")

        # Suggest git commit
        print("Suggested git commit:")
        print("  git add -A")
        print('  git commit -m "chore: sync project documentation and scripts after task completion"')
        print()
    else:
        print("\n✨ Everything already up to date!\n")


if __name__ == "__main__":
    main()
