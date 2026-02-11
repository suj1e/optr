#!/usr/bin/env python3
"""
Tool Discovery Script for OPTR

Scans available skills/agents/commands and matches them to PLAN.md content.

Usage:
    python scripts/discover-tools.py [path/to/PLAN.md]

This script:
1. Scans project-local directories (.claude/skills, skills/, etc.)
2. Scans ~/.claude/plugins for global tools
3. Searches GitHub for Claude Code plugins/skills/agents
4. Matches PLAN.md content to relevant tools
5. Outputs a list of matched tools with install commands
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


def print_report(project_tools, local_tools, online_tools, matched_tools):
    """Print discovery report."""
    print("\n" + "=" * 60)
    print("OPTR Tool Discovery Report")
    print("=" * 60)

    print(f"\n📊 Project-local Tools:")
    print(f"  Skills: {len(project_tools.get('skills', []))}")
    print(f"  Agents: {len(project_tools.get('agents', []))}")
    print(f"  Commands: {len(project_tools.get('commands', []))}")

    print(f"\n📦 Global Local Tools:")
    print(f"  Skills: {len(local_tools.get('skills', []))}")
    print(f"  Agents: {len(local_tools.get('agents', []))}")
    print(f"  Commands: {len(local_tools.get('commands', []))}")

    print(f"\n🌐 GitHub Tools: {len(online_tools)}")

    if matched_tools:
        print(f"\n🎯 Recommended Tools:")
        print("-" * 60)

        for i, tool in enumerate(matched_tools[:10], 1):
            source = tool.get('source', 'unknown')
            icon = {'project': '📁', 'local': '🏠', 'github': '🌐'}.get(source, '🌐')

            print(f"\n  {i}. {icon} [{source.upper()}] {tool.get('name', 'unknown')}")
            print(f"     {tool.get('description', 'N/A')[:70]}")
            print(f"     Type: {tool.get('type', 'unknown')}")

            if source == 'github':
                print(f"     Install: {tool.get('install_cmd')}")
    else:
        print("\n⚠️  No matches found.")


def main():
    if len(sys.argv) < 2:
        plan_path = Path.cwd() / 'PLAN.md'
    else:
        plan_path = Path(sys.argv[1])

    if not plan_path.exists():
        print(f"Error: PLAN.md not found at {plan_path}")
        sys.exit(1)

    plan_content = plan_path.read_text()
    plan_keywords = extract_keywords_from_plan(plan_content)

    print("📁 Scanning for project-local tools...")
    project_tools = scan_project_tools()

    print("🔍 Scanning for global local tools...")
    local_tools = scan_tools()

    print("🌐 Searching GitHub for tools...")
    online_tools = search_github_for_tools(plan_keywords)

    print("📊 Merging and scoring tools...")
    matched_tools = merge_and_score_tools(local_tools, online_tools, project_tools, plan_keywords)

    print_report(project_tools, local_tools, online_tools, matched_tools)


if __name__ == '__main__':
    main()
