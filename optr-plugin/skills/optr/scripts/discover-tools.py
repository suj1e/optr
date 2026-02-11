#!/usr/bin/env python3
"""
Tool Discovery Script for OPTR

Scans available skills/agents/commands and matches them to PLAN.md content.

Usage:
    python scripts/discover-tools.py [path/to/PLAN.md]

This script:
1. Scans ~/.claude/plugins for available tools
2. Extracts keywords and trigger phrases from tool descriptions
3. Matches PLAN.md content to relevant tools
4. Outputs a list of matched tools with relevance scores
"""

import sys
import re
import json
from pathlib import Path
from collections import defaultdict


def scan_tools():
    """Scan Claude plugins directory for available tools."""
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


def print_report(tools, matches):
    """Print discovery and matching report."""
    print("\n" + "="*60)
    print("OPTR Tool Discovery Report")
    print("="*60)

    print(f"\n📊 Available Tools:")
    print(f"  Skills: {len(tools['skills'])}")
    print(f"  Agents: {len(tools['agents'])}")
    print(f"  Commands: {len(tools['commands'])}")

    if matches:
        print(f"\n🎯 Matched Tools (relevance score):")
        for i, match in enumerate(matches[:10], 1):  # Top 10
            tool = match['tool']
            print(f"\n  {i}. [{tool['type'].upper()}] {tool['name']}")
            print(f"     Score: {match['score']} | Matched: {', '.join(match['matched_keywords'][:3])}")
            print(f"     Desc: {tool['description'][:80]}...")
    else:
        print("\n⚠️  No direct tool matches found. Using general optimization.")


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

    # Scan for tools
    print("🔍 Scanning for available tools...")
    tools = scan_tools()

    # Match tools to plan
    print("🔎 Matching tools to PLAN.md content...")
    matches = match_tools_to_plan(plan_content, tools)

    # Print report
    print_report(tools, matches)

    # Optionally output JSON for programmatic use
    if '--json' in sys.argv:
        output = {
            'available_tools': tools,
            'matched_tools': [
                {
                    'tool': m['tool'],
                    'score': m['score'],
                    'matched_keywords': m['matched_keywords']
                }
                for m in matches
            ]
        }
        print('\n' + json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
