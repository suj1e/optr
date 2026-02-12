#!/usr/bin/env python3
"""
Tool Discovery Script for OPTR

Scans available skills/agents/commands and matches them to PLAN.md content.

Usage:
    python scripts/discover-tools.py [path/to/PLAN.md]
    python scripts/discover-tools.py --yes [path/to/PLAN.md]  # Auto-search marketplace

This script:
1. Scans project-local directories (.claude/skills, skills/, etc.)
2. Scans ~/.claude/plugins for global tools
3. Shows local matches, asks whether to search marketplace
4. Searches marketplace for plugins using AI semantic matching if user confirms
5. Outputs final list with install commands
"""

import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Any

# Force unbuffered output for better visibility in Claude CLI
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None


def search_marketplace_for_plugins(
    plan_path: Path,
    threshold: float = 0.5,
    verbose: bool = False
) -> List[Dict[str, Any]]:
    """
    Search the Claude marketplace for plugins using semantic matching.

    Args:
        plan_path: Path to the PLAN.md file
        threshold: Minimum relevance score for including a plugin
        verbose: Print debug information

    Returns:
        List of matched marketplace plugins with install commands
    """
    try:
        # Get the directory of this script
        script_dir = Path(__file__).parent
        match_plugins_path = script_dir / 'match_plugins.py'

        if not match_plugins_path.exists():
            if verbose:
                print(f"Warning: match_plugins.py not found at {match_plugins_path}")
            return []

        # Import the module
        sys.path.insert(0, str(script_dir))

        try:
            from match_plugins import (
                get_available_plugins,
                match_plugins_with_claude
            )
        except ImportError as e:
            if verbose:
                print(f"Warning: Could not import match_plugins module: {e}")
            return []

        # Read plan content
        plan_content = plan_path.read_text()

        # Get available plugins
        plugins = get_available_plugins()

        if verbose:
            print(f"   Found {len(plugins)} marketplace plugins")

        if not plugins:
            return []

        # Match plugins using Claude API
        matched = match_plugins_with_claude(
            plan_content=plan_content,
            plugins=plugins,
            threshold=threshold,
            verbose=verbose
        )

        # Convert to expected format with 'type' field
        for plugin in matched:
            if 'type' not in plugin:
                # Detect type from name/description
                name_lower = plugin.get('name', '').lower()
                desc_lower = plugin.get('description', '').lower()

                if 'command' in name_lower or 'slash' in desc_lower:
                    plugin['type'] = 'command'
                elif 'agent' in name_lower:
                    plugin['type'] = 'agent'
                else:
                    plugin['type'] = 'skill'

        return matched

    except Exception as e:
        if verbose:
            print(f"Warning: Error searching marketplace: {e}")
        return []


def scan_tools():
    """Scan Claude plugins directory for available tools."""
    tools = {'skills': [], 'agents': [], 'commands': []}
    plugins_path = Path.home() / '.claude' / 'plugins'

    for skill_file in plugins_path.rglob('SKILL.md'):
        tool_info = parse_skill_file(skill_file)
        if tool_info:
            tools['skills'].append(tool_info)

    for agent_file in plugins_path.rglob('*-agent.md'):
        tool_info = parse_agent_file(agent_file)
        if tool_info:
            tools['agents'].append(tool_info)

    for command_file in plugins_path.rglob('*-command.md'):
        tool_info = parse_command_file(command_file)
        if tool_info:
            tools['commands'].append(tool_info)

    return tools


def scan_project_tools():
    """Scan project-local directories for skills, agents, commands."""
    tools = {'skills': [], 'agents': [], 'commands': []}
    project_root = Path.cwd()

    for skill_dir in ['.claude/skills', 'skills']:
        dir_path = project_root / skill_dir
        if dir_path.exists():
            for skill_file in dir_path.rglob('SKILL.md'):
                tool_info = parse_skill_file(skill_file)
                if tool_info:
                    tool_info['source'] = 'project'
                    tools['skills'].append(tool_info)

    for agent_dir in ['.claude/agents', 'agents']:
        dir_path = project_root / agent_dir
        if dir_path.exists():
            for agent_file in dir_path.rglob('*.md'):
                if agent_file.name == 'SKILL.md':
                    continue
                tool_info = parse_agent_file(agent_file)
                if tool_info:
                    tool_info['source'] = 'project'
                    tools['agents'].append(tool_info)

    for command_dir in ['.claude/commands', 'commands']:
        dir_path = project_root / command_dir
        if dir_path.exists():
            for command_file in dir_path.rglob('*.md'):
                if command_file.name == 'SKILL.md':
                    continue
                tool_info = parse_command_file(command_file)
                if tool_info:
                    tool_info['source'] = 'project'
                    tools['commands'].append(tool_info)

    return tools


def parse_skill_file(skill_path):
    """Extract metadata from SKILL.md file."""
    try:
        content = skill_path.read_text()
        metadata = extract_frontmatter(content)

        if metadata.get('description'):
            return {
                'type': 'skill',
                'name': metadata.get('name', 'unknown'),
                'description': metadata.get('description', ''),
                'path': str(skill_path),
                'keywords': []
            }
    except Exception:
        pass
    return None


def parse_agent_file(agent_path):
    """Extract metadata from agent.md file."""
    try:
        content = agent_path.read_text()
        lines = content.split('\n')
        description = ''
        for line in lines:
            if line.strip() and not line.startswith('#'):
                description = line.strip()
                break

        if description:
            return {
                'type': 'agent',
                'name': agent_path.stem,
                'description': description,
                'path': str(agent_path),
                'keywords': []
            }
    except Exception:
        pass
    return None


def parse_command_file(command_path):
    """Extract metadata from command.md file."""
    try:
        content = command_path.read_text()
        lines = content.split('\n')
        description = ''
        for line in lines:
            if line.strip() and not line.startswith('#'):
                description = line.strip()
                break

        if description:
            return {
                'type': 'command',
                'name': command_path.stem,
                'description': description,
                'path': str(command_path),
                'keywords': []
            }
    except Exception:
        pass
    return None


def extract_frontmatter(content):
    """Extract YAML frontmatter from markdown."""
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if match:
        frontmatter = match.group(1)
        metadata = {}
        for line in frontmatter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip().strip('"').strip("'")
        return metadata
    return {}


def extract_keywords_from_plan(plan_content):
    """Extract keywords from PLAN.md content."""
    keywords = []
    terms = [
        'skill', 'plugin', 'agent', 'command', 'hook',
        'frontend', 'backend', 'UI', 'interface',
        'API', 'database', 'test', 'review',
        'CLAUDE.md', 'documentation', 'deploy'
    ]
    verbs = ['create', 'build', 'implement', 'design', 'add', 'update']

    content_lower = plan_content.lower()
    for term in terms:
        if term.lower() in content_lower:
            keywords.append(term)
    for verb in verbs:
        if verb in content_lower:
            keywords.append(verb)

    return keywords


def merge_and_score_tools(local_tools, online_tools, project_tools, plan_keywords):
    """Merge all tools and score them."""
    all_tools = []

    # Add project tools (highest priority)
    for tool in project_tools.get('skills', []) + project_tools.get('agents', []) + project_tools.get('commands', []):
        t = dict(tool)
        t['source'] = 'project'
        t['score'] = 10
        all_tools.append(t)

    # Add local tools
    for tool in local_tools.get('skills', []) + local_tools.get('agents', []) + local_tools.get('commands', []):
        t = dict(tool)
        t['source'] = 'local'
        t['score'] = 5
        all_tools.append(t)

    # Add online tools
    for tool in online_tools:
        t = dict(tool)
        t['score'] = t.get('relevance_score', 3)
        all_tools.append(t)

    # Deduplicate
    seen = set()
    unique_tools = []
    for tool in all_tools:
        key = f"{tool.get('type', '')}:{tool.get('name', '').lower()}"
        if key not in seen:
            seen.add(key)
            unique_tools.append(tool)

    # Sort by score
    unique_tools.sort(key=lambda x: x.get('score', 0), reverse=True)
    return unique_tools


def print_local_matches(project_tools, local_tools, matched_tools):
    """Print matched local tools (project + global) and ask about marketplace search."""
    # Force flush output to ensure it displays before input prompt
    sys.stdout.flush()

    print("\n" + "=" * 60)
    print("🎯 Tool Discovery - Phase 1: Local Tools")
    print("=" * 60)
    sys.stdout.flush()

    # Show summary
    print(f"\n📁 Project-local: {len(project_tools.get('skills', []))} skills, {len(project_tools.get('agents', []))} agents, {len(project_tools.get('commands', []))} commands")
    print(f"📦 Global installed: {len(local_tools.get('skills', []))} skills, {len(local_tools.get('agents', []))} agents, {len(local_tools.get('commands', []))} commands")
    sys.stdout.flush()

    if matched_tools:
        print(f"\n✅ Local tools matched to your PLAN.md:")
        print("-" * 60)

        local_matches = [t for t in matched_tools if t.get('source') in ('project', 'local')]

        for i, tool in enumerate(local_matches[:10], 1):
            source = tool.get('source', 'unknown')
            icon = '📁' if source == 'project' else '🏠'
            print(f"\n  {i}. {icon} [{source.upper()}] {tool.get('name', 'unknown')}")
            desc = tool.get('description', 'N/A')
            if len(desc) > 70:
                desc = desc[:67] + "..."
            print(f"     {desc}")
    else:
        print("\n⚠️  No local tools matched to your PLAN.md content.")
        print("💡 Consider searching the marketplace for relevant tools.")
        sys.stdout.flush()

    print("\n" + "=" * 60)
    print("\nOptions:")
    print("  [y] Search marketplace for more tools → See installable plugins")
    print("  [n] Skip marketplace search → Use local tools only")
    print("  [q] Quit without changes")
    sys.stdout.flush()

    choice = input("\n👉 Search marketplace for additional tools? [y/n/q]: ").strip().lower()

    if choice == 'y':
        return True
    elif choice == 'q':
        print("\n👋 Exiting without marketplace search.")
        sys.exit(0)
    else:
        print("\n⏭️  Skipping marketplace search. Using local tools only.")
        return False


def print_final_report(matched_tools, searched_marketplace=False):
    """Print final report with all matched tools."""
    print("\n" + "=" * 60)
    print("🎯 Final Tool Discovery Results")
    print("=" * 60)

    if searched_marketplace:
        print("\n🌐 Including marketplace-sourced plugins")
    else:
        print("\n📦 Using local tools only")

    if not matched_tools:
        print("\n⚠️  No matching tools found.")
        return

    # Separate tools by source
    project_tools = [t for t in matched_tools if t.get('source') == 'project']
    local_tools = [t for t in matched_tools if t.get('source') == 'local']
    marketplace_tools = [t for t in matched_tools if t.get('source') == 'marketplace']

    # Section 1: Available Local Tools
    if project_tools or local_tools:
        print(f"\n" + "=" * 60)
        print("✅ Available Local Tools (Ready to Use)")
        print("=" * 60)

        for i, tool in enumerate(project_tools + local_tools, 1):
            source = tool.get('source', 'unknown')
            icon = '📁' if source == 'project' else '🏠'
            print(f"\n  {i}. {icon} [{source.upper()}] {tool.get('name', 'unknown')}")
            desc = tool.get('description', 'N/A')
            if len(desc) > 70:
                desc = desc[:67] + "..."
            print(f"     {desc}")

    # Section 2: Installable Marketplace Plugins
    if marketplace_tools:
        print(f"\n" + "=" * 60)
        print("🌐 Installable Marketplace Plugins")
        print("=" * 60)
        print("\n💡 Run these commands to install additional plugins:\n")

        for i, tool in enumerate(marketplace_tools, 1):
            print(f"  {i}. {tool.get('name', 'unknown')}")
            desc = tool.get('description', 'N/A')
            if len(desc) > 70:
                desc = desc[:67] + "..."
            print(f"     {desc}")

            # Show relevance score if available
            score = tool.get('relevance_score')
            if score is not None:
                print(f"     Relevance: {score:.2f}")

            print(f"     Install: {tool.get('install_cmd')}")

            # Show match reason if available
            reason = tool.get('match_reason')
            if reason:
                print(f"     Reason: {reason[:100]}{'...' if len(reason) > 100 else ''}")

    # Section 3: Summary
    print(f"\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"  📁 Project-local tools: {len(project_tools)}")
    print(f"  🏠 Global installed: {len(local_tools)}")
    print(f"  🌐 Marketplace available: {len(marketplace_tools)}")
    print(f"  📦 Total matched: {len(matched_tools)}")


def main():
    # Check for --yes flag (skip marketplace search prompt)
    auto_yes = '--yes' in sys.argv
    # Check for --verbose flag (show more details)
    verbose = '--verbose' in sys.argv
    sys.argv = [a for a in sys.argv if a not in ['--yes', '--verbose']]

    if len(sys.argv) < 2:
        plan_path = Path.cwd() / 'PLAN.md'
    else:
        plan_path = Path(sys.argv[1])

    if not plan_path.exists():
        print(f"Error: PLAN.md not found at {plan_path}")
        sys.exit(1)

    plan_content = plan_path.read_text()
    plan_keywords = extract_keywords_from_plan(plan_content)

    if verbose:
        print(f"📝 Extracted keywords: {plan_keywords}")

    print("📁 Scanning for project-local tools...")
    project_tools = scan_project_tools()
    if verbose:
        print(f"   Found: {len(project_tools.get('skills', []))} skills, {len(project_tools.get('agents', []))} agents, {len(project_tools.get('commands', []))} commands")

    print("🔍 Scanning for global local tools...")
    local_tools = scan_tools()
    if verbose:
        print(f"   Found: {len(local_tools.get('skills', []))} skills, {len(local_tools.get('agents', []))} agents, {len(local_tools.get('commands', []))} commands")

    # Merge local tools only for initial matching
    local_matched = merge_and_score_tools(local_tools, [], project_tools, plan_keywords)
    if verbose:
        print(f"   Matched: {len(local_matched)} tools")
        sys.stdout.flush()

    # Show local matches and ask about marketplace search
    if auto_yes:
        searched_marketplace = True
        print("\n🌐 Auto-searching marketplace (--yes flag)")
    else:
        searched_marketplace = print_local_matches(project_tools, local_tools, local_matched)

    marketplace_tools = []
    if searched_marketplace:
        print("\n🌐 Searching marketplace for plugins...")
        marketplace_tools = search_marketplace_for_plugins(plan_path, verbose=verbose)

    # Final merge of all tools
    matched_tools = merge_and_score_tools(local_tools, marketplace_tools, project_tools, plan_keywords)

    # Print phase 2 results
    print("\n" + "=" * 60)
    print("🎯 Tool Discovery - Phase 2: Complete Results")
    print("=" * 60)

    print_final_report(matched_tools, searched_marketplace)

    # Final recommendations
    marketplace_plugins = [t for t in matched_tools if t.get('source') == 'marketplace']
    if marketplace_plugins:
        print(f"\n" + "=" * 60)
        print("💡 Recommended Installation Commands")
        print("=" * 60)
        print("\nCopy and paste these commands to install additional plugins:\n")
        for tool in marketplace_plugins:
            print(f"  {tool.get('install_cmd')}")
        print()


if __name__ == '__main__':
    main()
