#!/usr/bin/env python3
"""
Tool Discovery Script for OPTR

Scans available skills/agents/commands and matches them to PLAN.md content.

Usage:
    python scripts/discover-tools.py [path/to/PLAN.md]

This script:
1. Scans project-local directories (.claude/skills, skills/, etc.)
2. Scans ~/.claude/plugins for global tools
3. Searches online for relevant tools and best practices
4. Extracts keywords and trigger phrases from tool descriptions
5. Matches PLAN.md content to relevant tools
6. Outputs a list of matched tools with relevance scores
"""

import sys
import re
import json
from pathlib import Path
from collections import defaultdict


def search_online_tools(keywords):
    """
    Search online for relevant Claude Code tools and plugins.

    Args:
        keywords: List of keywords from PLAN.md content

    Returns:
        List of online tool suggestions with metadata
    """
    online_tools = []

    if not keywords:
        return online_tools

    # Build search queries based on keywords
    search_queries = [
        "Claude Code skill plugin best practices 2025",
        "Claude Code agent command development",
        "Claude Code plugin marketplace tools",
    ]

    # Add keyword-specific queries
    for keyword in keywords[:3]:
        if len(keyword) > 3:
            search_queries.append(f"Claude Code {keyword} tool plugin")

    # Remove duplicates
    search_queries = list(dict.fromkeys(search_queries))[:5]

    # Execute searches
    for query in search_queries:
        try:
            # Use WebSearch tool - call it directly
            results = WebSearch(query=query)

            # Parse results to extract tool suggestions
            if results:
                for result in results[:3]:
                    tool_info = parse_web_search_result(result, query)
                    if tool_info:
                        online_tools.append(tool_info)
        except Exception:
            # Silently continue if web search fails
            continue

    return online_tools


def parse_web_search_result(result, source_query):
    """Parse a web search result into tool info format."""
    try:
        title = result.get('title', '')
        snippet = result.get('snippet', '')

        # Extract tool-like patterns from results
        # Look for mentions of tools, plugins, skills, commands
        if any(word in title.lower() + snippet.lower()
               for word in ['tool', 'plugin', 'skill', 'agent', 'command']):

            # Generate a tool name from title
            name = title.split(' - ')[0].split('|')[0].strip()
            name = re.sub(r'[^a-zA-Z0-9\-]', '', name)
            name = name[:30] if len(name) > 30 else name

            # Extract description from snippet
            description = snippet[:150] if snippet else "Online resource for development"

            return {
                'type': 'online_resource',
                'name': name or 'online-tool',
                'description': description,
                'source': 'online',
                'source_query': source_query,
                'keywords': extract_keywords_from_snippet(snippet),
                'relevance_score': calculate_online_relevance(title, snippet)
            }
    except Exception:
        pass

    return None


def extract_keywords_from_snippet(snippet):
    """Extract keywords from search result snippet."""
    keywords = []
    text_lower = snippet.lower()

    trigger_phrases = [
        'create', 'build', 'implement', 'design', 'develop',
        'skill', 'plugin', 'agent', 'command', 'hook',
        'frontend', 'UI', 'interface', 'component',
        'review', 'test', 'refactor', 'optimize',
        'documentation', 'docs', 'Claude'
    ]

    for phrase in trigger_phrases:
        if phrase.lower() in text_lower:
            keywords.append(phrase)

    return keywords


def calculate_online_relevance(title, snippet):
    """Calculate relevance score for online results."""
    score = 0
    text = (title + ' ' + snippet).lower()

    # Boost for specific tool mentions
    if 'claude' in text:
        score += 2
    if 'skill' in text:
        score += 2
    if 'plugin' in text:
        score += 2
    if 'agent' in text:
        score += 1
    if 'command' in text:
        score += 1

    # Boost for action verbs
    action_verbs = ['create', 'build', 'implement', 'develop', 'design']
    for verb in action_verbs:
        if verb in text:
            score += 1

    return score


def merge_tools(local_tools, online_tools, project_tools=None):
    """
    Merge project, local, and online tools, removing duplicates.

    Priority order:
    1. Project-local tools (highest priority)
    2. Global local tools (~/.claude/plugins)
    3. Online tools
    """
    if project_tools is None:
        project_tools = {'skills': [], 'agents': [], 'commands': []}

    merged = []
    seen_names = set()

    # Priority levels for sorting
    source_priority = {
        'project': 3,
        'local': 2,
        'online': 1
    }

    # Collect all tools with their sources
    all_tools = []

    # Add project tools
    for tool in project_tools['skills'] + project_tools['agents'] + project_tools['commands']:
        tool_copy = dict(tool)
        tool_copy['source'] = 'project'
        tool_copy['relevance_score'] = 10  # Highest base score
        all_tools.append(tool_copy)

    # Add global local tools
    for tool in local_tools['skills'] + local_tools['agents'] + local_tools['commands']:
        tool_copy = dict(tool)
        tool_copy['source'] = 'local'
        tool_copy['relevance_score'] = 5  # Base score
        all_tools.append(tool_copy)

    # Add online tools
    for tool in online_tools:
        tool_copy = dict(tool)
        tool_copy['source'] = 'online'
        all_tools.append(tool_copy)

    # Deduplicate and merge
    for tool in all_tools:
        name_key = f"{tool.get('type', 'unknown')}:{tool['name'].lower()}"
        if name_key not in seen_names:
            seen_names.add(name_key)
            merged.append(tool)

    # Sort by priority (project > local > online), then by relevance score
    merged.sort(key=lambda x: (source_priority.get(x.get('source'), 0), x.get('relevance_score', 0)), reverse=True)

    return merged


def score_tools(merged_tools, plan_keywords):
    """Score merged tools against PLAN.md keywords."""
    scored = []

    for tool in merged_tools:
        score = 0
        matched_keywords = []

        # Base score from relevance_score
        score += tool.get('relevance_score', 0)

        # Keyword matching
        for keyword in tool.get('keywords', []):
            keyword_lower = str(keyword).lower()
            for plan_keyword in plan_keywords:
                if keyword_lower in plan_keyword.lower() or plan_keyword.lower() in keyword_lower:
                    score += 1
                    if keyword not in matched_keywords:
                        matched_keywords.append(keyword)

        # Bonus for source reliability
        source = tool.get('source', 'unknown')
        if source == 'project':
            score += 5  # Project tools get highest bonus
        elif source == 'local':
            score += 3  # Global local tools get bonus

        scored.append({
            'tool': tool,
            'score': score,
            'matched_keywords': matched_keywords,
            'reason': generate_recommendation_reason(tool, score, matched_keywords)
        })

    # Sort by score descending
    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored


def scan_tools():
    """Scan Claude plugins directory and project-local tools for available tools."""
    tools = {
        'skills': [],
        'agents': [],
        'commands': []
    }

    plugins_path = Path.home() / '.claude' / 'plugins'

    # Scan for skills
    for skill_file in plugins_path.rglob('SKILL.md'):
        tool_info = parse_skill_file(skill_file)
        if tool_info:
            tools['skills'].append(tool_info)

    # Scan for agents
    for agent_file in plugins_path.rglob('*-agent.md'):
        tool_info = parse_agent_file(agent_file)
        if tool_info:
            tools['agents'].append(tool_info)

    # Scan for commands
    for command_file in plugins_path.rglob('*-command.md'):
        tool_info = parse_command_file(command_file)
        if tool_info:
            tools['commands'].append(tool_info)

    return tools


def scan_project_tools():
    """
    Scan project-local directories for skills, agents, and commands.

    Scans:
    - .claude/skills/, skills/
    - .claude/agents/, agents/
    - .claude/commands/, commands/

    Returns:
        Dict with 'skills', 'agents', 'commands' lists
    """
    tools = {
        'skills': [],
        'agents': [],
        'commands': []
    }

    project_root = Path.cwd()

    # Directories to scan for each type
    skill_dirs = ['.claude/skills', 'skills']
    agent_dirs = ['.claude/agents', 'agents']
    command_dirs = ['.claude/commands', 'commands']

    # Scan project skills
    for skill_dir in skill_dirs:
        dir_path = project_root / skill_dir
        if dir_path.exists():
            for skill_file in dir_path.rglob('SKILL.md'):
                tool_info = parse_skill_file(skill_file)
                if tool_info:
                    tool_info['source'] = 'project'
                    tools['skills'].append(tool_info)

    # Scan project agents
    for agent_dir in agent_dirs:
        dir_path = project_root / agent_dir
        if dir_path.exists():
            for agent_file in dir_path.rglob('*.md'):
                # Exclude SKILL.md files
                if agent_file.name == 'SKILL.md':
                    continue
                tool_info = parse_agent_file(agent_file)
                if tool_info:
                    tool_info['source'] = 'project'
                    tools['agents'].append(tool_info)

    # Scan project commands
    for command_dir in command_dirs:
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
                'keywords': extract_keywords(metadata.get('description', ''))
            }
    except Exception as e:
        pass
    return None


def parse_agent_file(agent_path):
    """Extract metadata from agent.md file."""
    try:
        content = agent_path.read_text()
        # Agents might not have frontmatter, extract from first paragraph
        lines = content.split('\n')
        description = ''
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('#'):
                description = line.strip()
                break

        if description:
            return {
                'type': 'agent',
                'name': agent_path.stem,
                'description': description,
                'path': str(agent_path),
                'keywords': extract_keywords(description)
            }
    except Exception as e:
        pass
    return None


def parse_command_file(command_path):
    """Extract metadata from command.md file."""
    try:
        content = command_path.read_text()
        # Similar to agents, extract from content
        lines = content.split('\n')
        description = ''
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('#'):
                description = line.strip()
                break

        if description:
            return {
                'type': 'command',
                'name': command_path.stem,
                'description': description,
                'path': str(command_path),
                'keywords': extract_keywords(description)
            }
    except Exception as e:
        pass
    return None


def extract_frontmatter(content):
    """Extract YAML frontmatter from markdown."""
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if match:
        frontmatter = match.group(1)
        # Simple YAML parsing (for basic key-value pairs)
        metadata = {}
        for line in frontmatter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip().strip('"').strip("'")
        return metadata
    return {}


def extract_keywords(text):
    """Extract keywords from description text."""
    # Common trigger phrases to look for
    trigger_phrases = [
        'create', 'build', 'implement', 'design', 'develop',
        'skill', 'plugin', 'agent', 'command', 'hook',
        'frontend', 'UI', 'interface', 'component',
        'review', 'test', 'refactor', 'optimize',
        'CLAUDE.md', 'documentation', 'docs'
    ]

    keywords = set()
    text_lower = text.lower()

    for phrase in trigger_phrases:
        if phrase.lower() in text_lower:
            keywords.add(phrase)

    # Also extract quoted phrases (specific triggers)
    quoted = re.findall(r'"([^"]+)"', text)
    keywords.update(quoted)

    return list(keywords)


def match_tools_to_plan(plan_content, tools):
    """Match available tools to PLAN.md content."""
    matches = []

    # Combine all tools
    all_tools = tools['skills'] + tools['agents'] + tools['commands']

    # Extract keywords from plan
    plan_keywords = extract_keywords_from_plan(plan_content)

    # Score each tool based on keyword overlap
    for tool in all_tools:
        score = 0
        matched_keywords = []

        for keyword in tool['keywords']:
            keyword_lower = str(keyword).lower()
            for plan_keyword in plan_keywords:
                if keyword_lower in plan_keyword.lower() or plan_keyword.lower() in keyword_lower:
                    score += 1
                    matched_keywords.append(keyword)

        if score > 0:
            matches.append({
                'tool': tool,
                'score': score,
                'matched_keywords': matched_keywords
            })

    # Sort by score descending
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches


def extract_keywords_from_plan(plan_content):
    """Extract potential keywords from PLAN.md content."""
    keywords = []

    # Look for common development terms
    terms = [
        'skill', 'plugin', 'agent', 'command', 'hook',
        'frontend', 'backend', 'UI', 'interface',
        'API', 'database', 'test', 'review',
        'CLAUDE.md', 'documentation', 'deploy'
    ]

    content_lower = plan_content.lower()
    for term in terms:
        if term.lower() in content_lower:
            keywords.append(term)

    # Extract task verbs
    task_verbs = ['create', 'build', 'implement', 'design', 'add', 'update']
    for verb in task_verbs:
        if verb in content_lower:
            keywords.append(verb)

    return keywords


def generate_recommendation_reason(tool, score, matched_keywords):
    """Generate a human-readable recommendation reason."""
    source = tool.get('source', 'unknown')

    if source == 'project':
        if matched_keywords:
            return f"Project tool matching: {', '.join(matched_keywords[:3])}"
        return "Project-local tool - ready to use"

    if source == 'local':
        if matched_keywords:
            return f"Local tool matching: {', '.join(matched_keywords[:3])}"
        return "Local tool - installed and ready to use"

    if source == 'online':
        if matched_keywords:
            return f"Online resource for: {', '.join(matched_keywords[:3])}"
        return "Online resource found via web search"

    return "General optimization tool"


def print_report(local_tools, online_tools, scored_matches, project_tools=None):
    """Print discovery and matching report."""
    if project_tools is None:
        project_tools = {'skills': [], 'agents': [], 'commands': []}

    print("\n" + "="*60)
    print("OPTR Tool Discovery Report")
    print("="*60)

    # Summary
    print(f"\n📊 Project-local Tools:")
    print(f"  Skills: {len(project_tools['skills'])}")
    print(f"  Agents: {len(project_tools['agents'])}")
    print(f"  Commands: {len(project_tools['commands'])}")

    print(f"\n📦 Global Local Tools:")
    print(f"  Skills: {len(local_tools['skills'])}")
    print(f"  Agents: {len(local_tools['agents'])}")
    print(f"  Commands: {len(local_tools['commands'])}")

    print(f"\n🌐 Online Resources: {len(online_tools)}")

    if scored_matches:
        print(f"\n🎯 Recommended Tools (priority: project > local > online):")
        print("-" * 60)

        for i, match in enumerate(scored_matches[:10], 1):  # Top 10
            tool = match['tool']
            source = tool.get('source', 'unknown')

            if source == 'project':
                source_icon = "📁"
            elif source == 'local':
                source_icon = "🏠"
            else:
                source_icon = "🌐"

            source_label = source.upper()

            print(f"\n  {i}. {source_icon} [{source_label}] {tool['name']}")
            print(f"     Description: {tool.get('description', 'N/A')[:70]}...")
            print(f"     Type: {tool['type']} | Matched: {', '.join(match['matched_keywords'][:3]) or 'none'}")
            print(f"     Reason: {match['reason']}")
    else:
        print("\n⚠️  No direct tool matches found. Using general optimization.")


def get_user_selection(scored_matches):
    """
    Prompt user to select which tools to install.

    Args:
        scored_matches: List of scored tool matches

    Returns:
        List of selected tool indices
    """
    if not scored_matches:
        return []

    online_tools = [i for i, m in enumerate(scored_matches)
                    if m['tool'].get('source') == 'online']

    if not online_tools:
        print("\n✅ All matching tools are already installed locally.")
        return []

    print("\n" + "=" * 60)
    print("🛠️  Tool Installation Selection")
    print("=" * 60)
    print("\nOnline tools found that may help with your PLAN.md:\n")

    # Show online tools with installation info
    for idx in online_tools:
        match = scored_matches[idx]
        tool = match['tool']
        print(f"  [{idx + 1}] {tool['name']}")
        print(f"      {tool.get('description', 'N/A')[:60]}...")
        print(f"      Install: claude plugin add {tool['name']}\n")

    print("-" * 60)
    print("\nSelect tools to install (comma-separated, e.g., 1,3,5)")
    print("Or press Enter to skip installation")

    user_input = input("\n👉 Your selection: ").strip()

    if not user_input:
        print("\n⏭️  Skipping tool installation.")
        return []

    try:
        selected = []
        for part in user_input.split(','):
            part = part.strip()
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(scored_matches):
                    selected.append(idx)
        return selected
    except Exception:
        return []


def print_installation_guide(selected_indices, scored_matches):
    """Print installation commands for selected tools."""
    if not selected_indices:
        return

    print("\n" + "=" * 60)
    print("📦 Installation Commands")
    print("=" * 60)

    for idx in selected_indices:
        tool = scored_matches[idx]['tool']
        print(f"\n🔹 {tool['name']}")
        print(f"   claude plugin add {tool['name']}")
        print(f"   Source: {tool.get('source_query', 'online search')}")

    print("\n" + "=" * 60)
    print("✅ Run the above commands to install selected tools")
    print("=" * 60)


def main():
    if len(sys.argv) < 2:
        plan_path = Path.cwd() / 'PLAN.md'
    else:
        plan_path = Path(sys.argv[1])

    if not plan_path.exists():
        print(f"Error: PLAN.md not found at {plan_path}")
        sys.exit(1)

    # Read plan content
    plan_content = plan_path.read_text()

    # Extract keywords from plan for searching
    plan_keywords = extract_keywords_from_plan(plan_content)

    # Scan for project-local tools
    print("📁 Scanning for project-local tools...")
    project_tools = scan_project_tools()

    # Scan for global local tools
    print("🔍 Scanning for global local tools...")
    local_tools = scan_tools()

    # Search for online tools
    print("🌐 Searching for online tools...")
    online_tools = search_online_tools(plan_keywords)

    # Merge and score all tools
    print("📊 Merging and scoring tools...")
    merged_tools = merge_tools(local_tools, online_tools, project_tools)
    scored_matches = score_tools(merged_tools, plan_keywords)

    # Print report
    print_report(local_tools, online_tools, scored_matches, project_tools)

    # User selection (skip in JSON mode or non-interactive)
    if '--json' not in sys.argv:
        selected = get_user_selection(scored_matches)
        if selected:
            print_installation_guide(selected, scored_matches)

    # Optionally output JSON for programmatic use
    if '--json' in sys.argv:
        output = {
            'project_tools': project_tools,
            'local_tools': local_tools,
            'online_tools': online_tools,
            'matched_tools': [
                {
                    'tool': m['tool'],
                    'score': m['score'],
                    'matched_keywords': m['matched_keywords'],
                    'reason': m['reason']
                }
                for m in scored_matches
            ]
        }
        print('\n' + json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
