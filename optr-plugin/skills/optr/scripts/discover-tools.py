#!/usr/bin/env python3
"""
Tool Discovery Script for OPTR

Scans available skills/agents/commands and matches them to PLAN.md content.

Usage:
    python scripts/discover-tools.py [path/to/PLAN.md]
    python scripts/discover-tools.py --yes [path/to/PLAN.md]  # Skip GitHub prompt

This script:
1. Scans project-local directories (.claude/skills, skills/, etc.)
2. Scans ~/.claude/plugins for global tools
3. Shows local matches, asks whether to search GitHub
4. Searches GitHub for more tools if user confirms
5. Outputs final list with install commands
"""

import sys
import re
from pathlib import Path


def search_github_for_tools(keywords):
    """
    Search GitHub for Claude Code plugins, skills, and agents.

    Args:
        keywords: List of keywords from PLAN.md content

    Returns:
        List of tool suggestions with GitHub repo info and install commands
    """
    online_tools = []

    if not keywords:
        return online_tools

    # Build search queries
    queries = []
    queries.append("Claude Code skill plugin")
    queries.append("Claude Code agent command")

    for kw in keywords[:3]:
        if len(kw) > 3:
            queries.append(f"Claude Code {kw}")

    # Execute searches
    for query in queries[:5]:
        try:
            results = WebSearch(query=query)

            if results:
                for result in results[:5]:
                    tool_info = parse_github_result(result)
                    if tool_info:
                        online_tools.append(tool_info)
        except Exception:
            continue

    return online_tools


def parse_github_result(result):
    """Parse a GitHub search result into tool info format."""
    try:
        title = result.get('title', '')
        url = result.get('url', '')
        snippet = result.get('snippet', '')

        # Extract repo from URL
        repo_match = re.search(r'github\.com/([^/]+)/([^/]+)', url)
        if not repo_match:
            return None

        owner = repo_match.group(1)
        repo = repo_match.group(2).replace('.git', '')

        # Detect tool type
        tool_type = detect_tool_type(repo, snippet, title)
        if not tool_type:
            return None

        # Generate name from repo
        name = repo.lower()
        name = re.sub(r'[^a-z0-9-]', '', name)

        # Build description
        if snippet:
            description = snippet[:150].strip()
        else:
            description = f"{name} - {tool_type} from GitHub"

        return {
            'type': tool_type,
            'name': name,
            'description': description,
            'source': 'github',
            'url': url,
            'repo': f"{owner}/{repo}",
            'install_cmd': f"claude plugin add {owner}/{repo}",
            'relevance_score': 5
        }
    except Exception:
        pass

    return None


def detect_tool_type(repo_name, snippet, title):
    """Detect if the repo is a skill, agent, command, or plugin."""
    text = (repo_name + ' ' + snippet + ' ' + title).lower()

    if 'command' in text or 'slash' in text:
        return 'command'
    if 'agent' in text or repo_name.lower() == 'agent':
        return 'agent'
    if 'skill' in text:
        return 'skill'

    if 'command' in repo_name.lower():
        return 'command'
    if 'agent' in repo_name.lower():
        return 'agent'
    if 'skill' in repo_name.lower():
        return 'skill'

    if 'claude' in text:
        return 'skill'

    return None


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
    """Print matched local tools (project + global) and ask about GitHub search."""
    print("\n" + "=" * 60)
    print("🎯 Tool Discovery - Phase 1: Local Tools")
    print("=" * 60)

    # Show summary
    print(f"\n📁 Project-local: {len(project_tools.get('skills', []))} skills, {len(project_tools.get('agents', []))} agents, {len(project_tools.get('commands', []))} commands")
    print(f"📦 Global installed: {len(local_tools.get('skills', []))} skills, {len(local_tools.get('agents', []))} agents, {len(local_tools.get('commands', []))} commands")

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
        print("💡 Consider searching GitHub for relevant tools.")

    print("\n" + "=" * 60)
    print("\nOptions:")
    print("  [y] Search GitHub for more tools → See installable plugins")
    print("  [n] Skip GitHub search → Use local tools only")
    print("  [q] Quit without changes")

    choice = input("\n👉 Search GitHub for additional tools? [y/n/q]: ").strip().lower()

    if choice == 'y':
        return True
    elif choice == 'q':
        print("\n👋 Exiting without GitHub search.")
        sys.exit(0)
    else:
        print("\n⏭️  Skipping GitHub search. Using local tools only.")
        return False


def print_final_report(matched_tools, searched_github=False):
    """Print final report with all matched tools."""
    print("\n" + "=" * 60)
    print("🎯 Final Tool Discovery Results")
    print("=" * 60)

    if searched_github:
        print("\n🌐 Including GitHub-sourced tools")
    else:
        print("\n📦 Using local tools only")

    if not matched_tools:
        print("\n⚠️  No matching tools found.")
        return

    # Separate tools by source
    project_tools = [t for t in matched_tools if t.get('source') == 'project']
    local_tools = [t for t in matched_tools if t.get('source') == 'local']
    github_tools = [t for t in matched_tools if t.get('source') == 'github']

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

    # Section 2: Installable GitHub Tools
    if github_tools:
        print(f"\n" + "=" * 60)
        print("🌐 Installable GitHub Tools")
        print("=" * 60)
        print("\n💡 Run these commands to install additional tools:\n")

        for i, tool in enumerate(github_tools, 1):
            print(f"  {i}. {tool.get('name', 'unknown')}")
            desc = tool.get('description', 'N/A')
            if len(desc) > 70:
                desc = desc[:67] + "..."
            print(f"     {desc}")
            print(f"     Install: {tool.get('install_cmd')}")

    # Section 3: Summary
    print(f"\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"  📁 Project-local tools: {len(project_tools)}")
    print(f"  🏠 Global installed: {len(local_tools)}")
    print(f"  🌐 GitHub available: {len(github_tools)}")
    print(f"  📦 Total matched: {len(matched_tools)}")


def main():
    if len(sys.argv) < 2:
        plan_path = Path.cwd() / 'PLAN.md'
    else:
        plan_path = Path(sys.argv[1])

    # Check for --yes flag (skip GitHub search prompt)
    auto_yes = '--yes' in sys.argv
    if auto_yes:
        sys.argv = [a for a in sys.argv if a != '--yes']

    if not plan_path.exists():
        print(f"Error: PLAN.md not found at {plan_path}")
        sys.exit(1)

    plan_content = plan_path.read_text()
    plan_keywords = extract_keywords_from_plan(plan_content)

    print("📁 Scanning for project-local tools...")
    project_tools = scan_project_tools()

    print("🔍 Scanning for global local tools...")
    local_tools = scan_tools()

    # Merge local tools only for initial matching
    local_matched = merge_and_score_tools(local_tools, [], project_tools, plan_keywords)

    # Show local matches and ask about GitHub search
    if auto_yes:
        searched_github = True
        print("\n🌐 Auto-searching GitHub (--yes flag)")
    else:
        searched_github = print_local_matches(project_tools, local_tools, local_matched)

    online_tools = []
    if searched_github:
        print("\n🌐 Searching GitHub for tools...")
        online_tools = search_github_for_tools(plan_keywords)

    # Final merge of all tools
    matched_tools = merge_and_score_tools(local_tools, online_tools, project_tools, plan_keywords)

    # Print phase 2 results
    print("\n" + "=" * 60)
    print("🎯 Tool Discovery - Phase 2: Complete Results")
    print("=" * 60)

    print_final_report(matched_tools, searched_github)

    # Final recommendations
    github_tools = [t for t in matched_tools if t.get('source') == 'github']
    if github_tools:
        print(f"\n" + "=" * 60)
        print("💡 Recommended Installation Commands")
        print("=" * 60)
        print("\nCopy and paste these commands to install additional tools:\n")
        for tool in github_tools:
            print(f"  {tool.get('install_cmd')}")
        print()


if __name__ == '__main__':
    main()
