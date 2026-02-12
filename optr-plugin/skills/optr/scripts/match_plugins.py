#!/usr/bin/env python3
"""
Marketplace Plugin Matching Script for OPTR

Uses Claude API to semantically match PLAN.md content with available marketplace plugins.

Usage:
    python scripts/match-plugins.py [path/to/PLAN.md]
    python scripts/match-plugins.py --threshold 0.7 [path/to/PLAN.md]
    python scripts/match-plugins.py --api-key YOUR_KEY [path/to/PLAN.md]
    python scripts/match-plugins.py --model claude-3-7-sonnet [path/to/PLAN.md]
    python scripts/match-plugins.py --verbose [path/to/PLAN.md]

This script:
1. Calls `claude plugin list --available --json` to get marketplace plugins
2. Uses Anthropic Claude API for semantic matching with plan content
3. Returns JSON with matched plugins sorted by relevance score
4. Filters plugins by threshold (default: 0.5)
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from typing import Any, Dict, List, Optional


# Force unbuffered output for better visibility in Claude CLI
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None


def get_available_plugins() -> List[Dict[str, Any]]:
    """
    Get list of available marketplace plugins using claude CLI.

    Returns:
        List of plugin dictionaries with name, description, repository info
    """
    try:
        result = subprocess.run(
            ['claude', 'plugin', 'list', '--available', '--json'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return []

        try:
            plugins = json.loads(result.stdout)
            return plugins if isinstance(plugins, list) else []
        except json.JSONDecodeError:
            return []

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def match_plugins_with_claude(
    plan_content: str,
    plugins: List[Dict[str, Any]],
    api_key: Optional[str] = None,
    model: str = 'claude-3-7-sonnet-20250219',
    threshold: float = 0.5,
    verbose: bool = False
) -> List[Dict[str, Any]]:
    """
    Use Claude API to semantically match plugins to plan content.

    Args:
        plan_content: Content of the PLAN.md file
        plugins: List of available marketplace plugins
        api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        model: Claude model to use for matching
        threshold: Minimum relevance score (0-1) to include a plugin
        verbose: Print debug information

    Returns:
        List of matched plugins with relevance scores, sorted by score
    """
    if not plugins:
        return []

    # Get API key from parameter or environment
    if not api_key:
        api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        if verbose:
            print("match-plugins.py: No ANTHROPIC_API_KEY found, returning empty matches", file=sys.stderr)
        return []

    try:
        from anthropic import Anthropic
    except ImportError:
        if verbose:
            print("match-plugins.py: anthropic package not installed, returning empty matches", file=sys.stderr)
        return []

    try:
        client = Anthropic(api_key=api_key)

        # Build plugin list for context
        plugin_descriptions = []
        for i, plugin in enumerate(plugins):
            name = plugin.get('name', 'unknown')
            desc = plugin.get('description', plugin.get('summary', ''))
            repo = plugin.get('repository', plugin.get('repo', ''))

            plugin_desc = f"{i+1}. {name}"
            if desc:
                plugin_desc += f": {desc}"
            if repo:
                plugin_desc += f" (from {repo})"
            plugin_descriptions.append(plugin_desc)

        plugins_text = "\n".join(plugin_descriptions)

        # Build the matching prompt
        prompt = f"""You are a plugin matching assistant. Given a project plan and a list of available Claude Code plugins, identify which plugins would be most useful for the plan.

Project Plan:
{plan_content[:3000]}

Available Plugins:
{plugins_text}

Analyze each plugin and determine its relevance to the plan. Return a JSON array of objects with this structure:
[
  {{
    "name": "plugin-name",
    "score": 0.8,
    "reason": "Brief explanation of why this plugin is relevant"
  }}
]

Only include plugins with a score >= {threshold}. Score from 0 (not relevant) to 1 (highly relevant).
Return ONLY the JSON array, no other text."""

        if verbose:
            print(f"match-plugins.py: Calling Claude API with {len(plugins)} plugins", file=sys.stderr)

        response = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{'role': 'user', 'content': prompt}]
        )

        # Extract response text
        response_text = response.content[0].text

        if verbose:
            print(f"match-plugins.py: Got response from Claude API", file=sys.stderr)

        # Parse JSON response
        matches = json.loads(response_text)

        # Enhance matches with full plugin info
        matched_plugins = []
        plugin_by_name = {p.get('name', ''): p for p in plugins}

        for match in matches if isinstance(matches, list) else []:
            name = match.get('name', '')
            if name and name in plugin_by_name:
                plugin_info = plugin_by_name[name].copy()
                plugin_info['relevance_score'] = match.get('score', 0.5)
                plugin_info['match_reason'] = match.get('reason', '')
                plugin_info['source'] = 'marketplace'

                # Add install command
                repo = plugin_info.get('repository', plugin_info.get('repo', ''))
                if repo:
                    plugin_info['install_cmd'] = f"claude plugin add {repo}"

                matched_plugins.append(plugin_info)

        # Sort by relevance score descending
        matched_plugins.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        return matched_plugins

    except Exception as e:
        if verbose:
            print(f"match-plugins.py: Error calling Claude API: {e}", file=sys.stderr)
        return []


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Match marketplace plugins to PLAN.md content using Claude API'
    )
    parser.add_argument(
        'plan_path',
        nargs='?',
        default=None,
        help='Path to PLAN.md file (default: ./PLAN.md)'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.5,
        help='Minimum relevance score (0-1, default: 0.5)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='Anthropic API key (default: ANTHROPIC_API_KEY env var)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='claude-3-7-sonnet-20250219',
        help='Claude model to use (default: claude-3-7-sonnet-20250219)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print debug information to stderr'
    )

    args = parser.parse_args()

    # Validate threshold
    if not 0 <= args.threshold <= 1:
        print("Error: --threshold must be between 0 and 1", file=sys.stderr)
        sys.exit(1)

    # Get plan path
    if args.plan_path:
        plan_path = Path(args.plan_path)
    else:
        plan_path = Path.cwd() / 'PLAN.md'

    # Read plan content
    if not plan_path.exists():
        print(f"Error: PLAN.md not found at {plan_path}", file=sys.stderr)
        sys.exit(1)

    plan_content = plan_path.read_text()

    if args.verbose:
        print(f"match-plugins.py: Read plan from {plan_path} ({len(plan_content)} chars)", file=sys.stderr)

    # Get available plugins
    plugins = get_available_plugins()

    if args.verbose:
        print(f"match-plugins.py: Found {len(plugins)} available marketplace plugins", file=sys.stderr)

    # Match plugins
    matched = match_plugins_with_claude(
        plan_content=plan_content,
        plugins=plugins,
        api_key=args.api_key,
        model=args.model,
        threshold=args.threshold,
        verbose=args.verbose
    )

    # Filter by threshold
    filtered = [p for p in matched if p.get('relevance_score', 0) >= args.threshold]

    if args.verbose:
        print(f"match-plugins.py: Returning {len(filtered)} matched plugins (threshold={args.threshold})", file=sys.stderr)

    # Output JSON
    print(json.dumps(filtered, indent=2))


if __name__ == '__main__':
    main()
