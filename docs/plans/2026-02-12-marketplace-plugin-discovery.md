# Marketplace Plugin Discovery Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace WebSearch-based GitHub tool discovery with `/plugin` command for accurate marketplace plugin matching using AI semantic analysis.

**Architecture:** Create `match-plugins.py` script that calls `claude plugin list --available --json`, uses Claude API for semantic matching against PLAN.md, and returns high-relevance plugins (score >= 0.7). Integrate into existing `discover-tools.py` Phase 2 workflow.

**Tech Stack:** Python 3, Claude API, subprocess for CLI calls, JSON parsing

---

## Task 1: Create match-plugins.py Script

**Files:**
- Create: `optr-plugin/skills/optr/scripts/match-plugins.py`

**Step 1: Write the match-plugins.py with full implementation**

```python
#!/usr/bin/env python3
"""
Marketplace Plugin Matcher for OPTR

Uses Claude API to semantically match PLAN.md content with available marketplace plugins.

Usage:
    python scripts/match-plugins.py [path/to/PLAN.md] [options]

Options:
    --threshold <0.0-1.0>    Matching threshold (default: 0.7)
    --api-key <key>           Claude API key (default: from ANTHROPIC_API_KEY env var)
    --model <model>           Claude model to use (default: claude-sonnet-4-20250514)
    --verbose                 Show detailed matching process
"""

import sys
import json
import os
import subprocess
import argparse
from pathlib import Path

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None


def get_marketplace_plugins():
    """
    Get available plugins from configured marketplaces using claude plugin command.

    Returns:
        dict: Parsed JSON with 'available' and 'installed' plugins
    """
    try:
        result = subprocess.run(
            ['claude', 'plugin', 'list', '--available', '--json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"Warning: claude plugin command failed: {result.stderr}", file=sys.stderr)
            return {"available": [], "installed": []}
    except subprocess.TimeoutExpired:
        print("Warning: claude plugin command timed out", file=sys.stderr)
        return {"available": [], "installed": []}
    except FileNotFoundError:
        print("Warning: claude command not found in PATH", file=sys.stderr)
        return {"available": [], "installed": []}
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse plugin list JSON: {e}", file=sys.stderr)
        return {"available": [], "installed": []}
    except Exception as e:
        print(f"Warning: Unexpected error getting plugins: {e}", file=sys.stderr)
        return {"available": [], "installed": []}


def match_plugins_with_claude(plan_content, plugins, api_key=None, model=None, verbose=False):
    """
    Use Claude API to semantically match plan content with available plugins.

    Args:
        plan_content: Content of PLAN.md
        plugins: List of available plugin dicts from marketplace
        api_key: Claude API key (optional, reads from env if not provided)
        model: Model name to use
        verbose: Show detailed matching info

    Returns:
        list: Matched plugins with score and reason, sorted by score descending
    """
    try:
        import anthropic
    except ImportError:
        print("Error: anthropic package not installed. Install with: pip install anthropic", file=sys.stderr)
        return []

    if not api_key:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set. Provide via --api-key or environment variable.", file=sys.stderr)
        return []

    if not model:
        model = os.environ.get('CLAUDE_MODEL', 'claude-sonnet-4-20250514')

    # Prepare plugin data for matching (limit to top 50 to manage context)
    plugin_summaries = []
    for plugin in plugins[:50]:
        plugin_summaries.append({
            "id": plugin.get("pluginId", "unknown"),
            "name": plugin.get("name", "unknown"),
            "description": plugin.get("description", ""),
            "marketplace": plugin.get("marketplaceName", "unknown")
        })

    # Build the matching prompt
    prompt = f"""You are a tool matching expert. Analyze the project plan and match it with available Claude Code plugins.

PROJECT PLAN:
{plan_content}

AVAILABLE PLUGINS:
{json.dumps(plugin_summaries, indent=2)}

TASK:
1. Analyze the project plan to understand what the user wants to build
2. Match the plan with available plugins based on SEMANTIC relevance, not just keywords
3. Return ONLY a JSON array of matched plugins that have genuine relevance to the plan

For each match, provide:
- plugin: The pluginId
- name: The plugin name
- reason: One sentence explaining why this plugin is relevant (e.g., "Plan mentions 'code review' and 'PR feedback'")
- score: Relevance score from 0.0 to 1.0 (be conservative, only score >= 0.7 if genuinely helpful)

SCORING GUIDELINES:
- 0.9-1.0: Direct, explicit match (plan explicitly mentions this functionality)
- 0.8-0.9: Strong semantic match (plan describes work this plugin is designed for)
- 0.7-0.8: Moderate match (plugin would be helpful but not essential)
- < 0.7: Do NOT include (not relevant enough)

Return ONLY the JSON array, nothing else. Format:
[{{"plugin": "plugin-id", "name": "name", "reason": "reason", "score": 0.85}}]"""

    if verbose:
        print(f"🔍 Calling Claude API with {len(plugin_summaries)} plugins...", file=sys.stderr)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        response_text = response.content[0].text.strip()

        # Extract JSON from response (handle potential markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        matches = json.loads(response_text)

        if verbose:
            print(f"✅ Got {len(matches)} matches from Claude API", file=sys.stderr)

        return matches

    except Exception as e:
        print(f"Error calling Claude API: {e}", file=sys.stderr)
        return []


def filter_by_threshold(matches, threshold=0.7):
    """Filter matches by relevance threshold and sort by score."""
    filtered = [m for m in matches if m.get('score', 0) >= threshold]
    filtered.sort(key=lambda x: x.get('score', 0), reverse=True)
    return filtered


def main():
    parser = argparse.ArgumentParser(description='Match PLAN.md with marketplace plugins')
    parser.add_argument('plan_path', nargs='?', help='Path to PLAN.md (default: ./PLAN.md)')
    parser.add_argument('--threshold', type=float, default=0.7, help='Relevance threshold (default: 0.7)')
    parser.add_argument('--api-key', help='Claude API key (default: ANTHROPIC_API_KEY env var)')
    parser.add_argument('--model', default='claude-sonnet-4-20250514', help='Claude model to use')
    parser.add_argument('--verbose', action='store_true', help='Show detailed matching process')

    args = parser.parse_args()

    # Determine plan path
    if args.plan_path:
        plan_path = Path(args.plan_path)
    else:
        plan_path = Path.cwd() / 'PLAN.md'

    if not plan_path.exists():
        print(f"Error: PLAN.md not found at {plan_path}", file=sys.stderr)
        sys.exit(1)

    # Read plan content
    plan_content = plan_path.read_text()

    if args.verbose:
        print(f"📄 Read {len(plan_content)} characters from {plan_path}", file=sys.stderr)

    # Get marketplace plugins
    marketplace_data = get_marketplace_plugins()
    available_plugins = marketplace_data.get('available', [])

    if args.verbose:
        print(f"📦 Found {len(available_plugins)} available plugins", file=sys.stderr)

    if not available_plugins:
        print("No available plugins found from marketplace", file=sys.stderr)
        sys.exit(0)

    # Match plugins using Claude
    matches = match_plugins_with_claude(
        plan_content,
        available_plugins,
        api_key=args.api_key,
        model=args.model,
        verbose=args.verbose
    )

    # Filter by threshold
    filtered_matches = filter_by_threshold(matches, threshold=args.threshold)

    # Output as JSON
    output = {
        "matched_count": len(filtered_matches),
        "threshold": args.threshold,
        "matches": filtered_matches
    }

    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
```

**Step 2: Make script executable**

Run: `chmod +x optr-plugin/skills/optr/scripts/match-plugins.py`
Expected: No errors, file is now executable

**Step 3: Test basic functionality (requires API key)**

Run: `ANTHROPIC_API_KEY=your_key python3 optr-plugin/skills/optr/scripts/match-plugins.py PLAN.md --threshold 0.7`
Expected: JSON output with matched plugins or error about missing API key

**Step 4: Commit**

```bash
git add optr-plugin/skills/optr/scripts/match-plugins.py
git commit -m "feat: add marketplace plugin matching script with AI semantic analysis"
```

---

## Task 2: Update discover-tools.py to Integrate Marketplace Search

**Files:**
- Modify: `optr-plugin/skills/optr/scripts/discover-tools.py:27-64, 398-522`

**Step 1: Remove GitHub search functions**

Delete the `search_github_for_tools`, `parse_github_result`, and `detect_tool_type` functions (lines 27-135). These are replaced by marketplace matching.

**Step 2: Add import for match-plugins**

Add at top of file after imports (around line 25):

```python
# Import marketplace matcher
SCRIPT_DIR = Path(__file__).parent
MATCH_PLUGINS_PATH = SCRIPT_DIR / 'match-plugins.py'
```

**Step 3: Add marketplace matching function**

Add after `extract_keywords_from_plan` function (around line 300):

```python
def search_marketplace_for_plugins(plan_path, threshold=0.7, verbose=False):
    """
    Search marketplace for plugins using AI semantic matching.

    Args:
        plan_path: Path to PLAN.md
        threshold: Relevance threshold (default: 0.7)
        verbose: Show detailed info

    Returns:
        List of matched plugin tools with install commands
    """
    if not MATCH_PLUGINS_PATH.exists():
        print("Warning: match-plugins.py not found", file=sys.stderr)
        return []

    try:
        import json
        result = subprocess.run(
            [sys.executable, str(MATCH_PLUGINS_PATH), str(plan_path),
             '--threshold', str(threshold)],
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, 'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY', '')}
        )

        if result.returncode != 0:
            if verbose:
                print(f"Warning: match-plugins.py failed: {result.stderr}", file=sys.stderr)
            return []

        data = json.loads(result.stdout)
        matches = data.get('matches', [])

        # Convert to tool format
        tools = []
        for match in matches:
            plugin_id = match.get('plugin', '')
            # Extract marketplace and plugin name from pluginId (format: name@marketplace)
            if '@' in plugin_id:
                name, marketplace = plugin_id.split('@', 1)
            else:
                name = match.get('name', 'unknown')
                marketplace = 'unknown'

            tools.append({
                'type': 'plugin',
                'name': name,
                'description': match.get('reason', ''),
                'source': 'marketplace',
                'plugin_id': plugin_id,
                'marketplace': marketplace,
                'score': int(match.get('score', 0) * 10),  # Convert to 0-10 scale
                'install_cmd': f"claude plugin install {plugin_id}"
            })

        return tools

    except subprocess.TimeoutExpired:
        print("Warning: Marketplace search timed out", file=sys.stderr)
        return []
    except Exception as e:
        if verbose:
            print(f"Warning: Marketplace search failed: {e}", file=sys.stderr)
        return []
```

**Step 4: Update print_local_matches to mention marketplace**

Replace the prompt text in `print_local_matches` function (around line 375-379):

```python
    print("\n" + "=" * 60)
    print("\nOptions:")
    print("  [y] Search marketplace for more tools → See installable plugins")
    print("  [n] Skip marketplace search → Use local tools only")
    print("  [q] Quit without changes")
    sys.stdout.flush()

    choice = input("\n👉 Search marketplace for additional tools? [y/n/q]: ").strip().lower()
```

**Step 5: Update main function to use marketplace search**

Replace the GitHub search section in main() function (around lines 498-522):

Find:
```python
    online_tools = []
    if searched_github:
        print("\n🌐 Searching GitHub for tools...")
        online_tools = search_github_for_tools(plan_keywords)
```

Replace with:
```python
    marketplace_tools = []
    if searched_github:
        print("\n🔍 Searching marketplace for relevant plugins...")
        marketplace_tools = search_marketplace_for_plugins(plan_path, threshold=0.7, verbose=verbose)
```

**Step 6: Update merge_and_score_tools call**

Find:
```python
    # Final merge of all tools
    matched_tools = merge_and_score_tools(local_tools, online_tools, project_tools, plan_keywords)
```

Replace with:
```python
    # Final merge of all tools
    matched_tools = merge_and_score_tools(local_tools, marketplace_tools, project_tools, plan_keywords)
```

**Step 7: Update print_final_report references**

Find all references to 'github_tools' and update to 'marketplace_tools':

```python
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
    marketplace_plugins = [t for t in matched_tools if t.get('source') == 'marketplace']

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
    if marketplace_plugins:
        print(f"\n" + "=" * 60)
        print("🌐 Installable Marketplace Plugins")
        print("=" * 60)
        print("\n💡 Run these commands to install additional plugins:\n")

        for i, tool in enumerate(marketplace_plugins, 1):
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
    print(f"  🌐 Marketplace plugins: {len(marketplace_plugins)}")
    print(f"  📦 Total matched: {len(matched_tools)}")
```

**Step 8: Update final recommendations section**

Find near line 513:
```python
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
```

Replace with:
```python
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
```

**Step 9: Update main function call**

Find in main():
```python
    print_final_report(matched_tools, searched_github)
```

Replace with:
```python
    print_final_report(matched_tools, searched_github)
```

**Step 10: Test the updated discover-tools.py**

Run: `python3 optr-plugin/skills/optr/scripts/discover-tools.py PLAN.md --yes 2>&1 | head -50`
Expected: Phase 1 shows local tools, Phase 2 shows marketplace plugins (or error if no API key)

**Step 11: Commit**

```bash
git add optr-plugin/skills/optr/scripts/discover-tools.py
git commit -m "feat: integrate marketplace plugin search replacing GitHub WebSearch"
```

---

## Task 3: Update SKILL.md Documentation

**Files:**
- Modify: `optr-plugin/skills/optr/SKILL.md:76-172`

**Step 1: Update Step 2 workflow description**

Find section "### Step 2: Discover Relevant Tools (Two-Phase Workflow)" and update the Phase 2 output example:

Replace the GitHub search output example with marketplace output:

```markdown
#### Phase 2: Marketplace Search + Install Suggestions (if user confirms)

```
🔍 Searching marketplace for relevant plugins...

============================================================
🎯 Tool Discovery - Phase 2: Complete Results
============================================================

============================================================
✅ Available Local Tools (Ready to Use)
============================================================

  1. 🏠 [LOCAL] skill-development
     This skill should be used when the user wants to "create a skill"

  2. 🏠 [LOCAL] frontend-design
     Create distinctive, production-grade frontend interfaces

============================================================
🌐 Installable Marketplace Plugins
============================================================

💡 Run these commands to install additional plugins:

  1. code-review
     Plan mentions 'PR review' and 'code quality checks'
     Install: claude plugin install code-review@marketplace

  2. test-runner
     Plan describes 'testing' and 'test execution' tasks
     Install: claude plugin install test-runner@marketplace

============================================================
📊 Summary
============================================================
  📁 Project-local tools: 0
  🏠 Global installed: 2
  🌐 Marketplace plugins: 2
  📦 Total matched: 4

============================================================
💡 Recommended Installation Commands
============================================================

Copy and paste these commands to install additional plugins:

  claude plugin install code-review@marketplace
  claude plugin install test-runner@marketplace
```

**Tool Sources Priority:**
1. **Project-local** (score: 10) - Your project's own tools
2. **Global local** (score: 5) - Installed in ~/.claude/plugins
3. **Marketplace** (score: based on AI relevance) - Plugins from configured marketplaces
```

**Step 2: Update tool sources description**

Find "Tool Sources Priority:" section and update:

```markdown
**Tool Sources Priority:**
1. **Project-local** (score: 10) - Your project's own tools
2. **Global local** (score: 5) - Installed in ~/.claude/plugins
3. **Marketplace** (score: based on AI matching 0.7-1.0) - Plugins from `claude plugin list --available`
```

**Step 3: Update script descriptions in Additional Resources**

Find the utility scripts section and update:

```markdown
### Utility Scripts

- **`scripts/sync-docs.py`** - Auto-sync PLAN.md, README.md, CLAUDE.md after task completion
- **`scripts/discover-tools.py`** - Two-phase tool discovery with marketplace plugin search:
  - Phase 1: Show local matches, ask about marketplace
  - Phase 2: AI semantic matching from marketplace plugins
  - Options: `--verbose` (detailed scan info), `--yes` (auto-search marketplace)
- **`scripts/match-plugins.py`** - AI semantic plugin matching:
  - Queries `claude plugin list --available --json` for marketplace plugins
  - Uses Claude API to match PLAN.md content with plugin descriptions
  - Returns plugins with relevance score >= 0.7
  - Options: `--threshold`, `--api-key`, `--model`, `--verbose`
- **`scripts/optimize-plan.py`** - Analyze PLAN.md for optimization opportunities
- **`scripts/worktree-manager.py`** - Strategy C: On-demand worktree management
```

**Step 4: Commit**

```bash
git add optr-plugin/skills/optr/SKILL.md
git commit -m "docs: update SKILL.md for marketplace plugin discovery"
```

---

## Task 4: Update README.md Documentation

**Files:**
- Modify: `README.md`

**Step 1: Find the tool discovery section**

Run: `grep -n "discover-tools\|GitHub" optr-plugin/README.md | head -20`
Expected: Line numbers for relevant sections

**Step 2: Update tool discovery description**

Based on grep results, find the section describing tool discovery and update references from "GitHub search" to "marketplace search".

**Step 3: Commit**

```bash
git add optr-plugin/README.md
git commit -m "docs: update README for marketplace plugin discovery"
```

---

## Task 5: Add anthropic to dependencies (if needed)

**Files:**
- Create or Modify: `requirements.txt` or `pyproject.toml`

**Step 1: Check if requirements file exists**

Run: `ls -la optr-plugin/*.txt optr-plugin/pyproject.toml 2>/dev/null || echo "No Python deps file found"`

**Step 2: Add anthropic dependency**

If `requirements.txt` exists, add:
```
anthropic>=0.18.0
```

If `pyproject.toml` exists, add to dependencies:
```toml
dependencies = [
    "anthropic>=0.18.0",
]
```

**Step 3: Commit**

```bash
git add requirements.txt pyproject.toml
git commit -m "deps: add anthropic package for AI plugin matching"
```

---

## Task 6: Create Test Fixture

**Files:**
- Create: `test/fixtures/sample-plan.md`
- Create: `test/fixtures/market-mock.json`

**Step 1: Create sample PLAN.md for testing**

```bash
mkdir -p test/fixtures
cat > test/fixtures/sample-plan.md << 'EOF'
# Sample Project Plan

## Project Overview
Build a web application with user authentication, frontend UI, and API integration.

## Phase 1: Backend
- [ ] Create REST API endpoints
- [ ] Implement user authentication
- [ ] Add database models

## Phase 2: Frontend
- [ ] Design login interface
- [ ] Build dashboard UI
- [ ] Add responsive styling

## Phase 3: Testing
- [ ] Write unit tests for API
- [ ] Add integration tests
- [ ] Set up CI/CD pipeline

## Phase 4: Review
- [ ] Code review for PRs
- [ ] Documentation updates
EOF
```

**Step 2: Create mock marketplace data**

```bash
cat > test/fixtures/market-mock.json << 'EOF'
{
  "installed": [],
  "available": [
    {
      "pluginId": "code-review@claude-plugins-official",
      "name": "code-review",
      "description": "Automated code review for pull requests with quality checks",
      "marketplaceName": "claude-plugins-official",
      "version": "1.0.0",
      "installCount": 15000
    },
    {
      "pluginId": "frontend-design@claude-plugins-official",
      "name": "frontend-design",
      "description": "Production-grade frontend design with modern UI/UX principles",
      "marketplaceName": "claude-plugins-official",
      "version": "1.0.0",
      "installCount": 25000
    },
    {
      "pluginId": "test-runner@claude-plugins-official",
      "name": "test-runner",
      "description": "Automated test execution and reporting for CI/CD",
      "marketplaceName": "claude-plugins-official",
      "version": "1.0.0",
      "installCount": 18000
    }
  ]
}
EOF
```

**Step 3: Commit**

```bash
git add test/fixtures/sample-plan.md test/fixtures/market-mock.json
git commit -m "test: add fixtures for plugin matching tests"
```

---

## Task 7: Manual Integration Test

**Step 1: Test with sample PLAN.md**

Run: `python3 optr-plugin/skills/optr/scripts/discover-tools.py test/fixtures/sample-plan.md`
Expected: Phase 1 shows local tools, then prompts for marketplace search

**Step 2: Test with --yes flag**

Run: `python3 optr-plugin/skills/optr/scripts/discover-tools.py test/fixtures/sample-plan.md --yes`
Expected: Full workflow including marketplace search

**Step 3: Verify output format**

Check that marketplace plugins show with:
- Plugin name
- Match reason (one sentence)
- Install command

**Step 4: Test error handling (no API key)**

Run: `unset ANTHROPIC_API_KEY && python3 optr-plugin/skills/optr/scripts/discover-tools.py test/fixtures/sample-plan.md --yes`
Expected: Graceful fallback, warning about missing API key, continues with local tools only

**Step 5: Commit final changes**

```bash
git add .
git commit -m "test: verify marketplace integration end-to-end"
```

---

## Completion Checklist

- [ ] `match-plugins.py` created and executable
- [ ] `discover-tools.py` updated to use marketplace search
- [ ] SKILL.md documentation updated
- [ ] README.md documentation updated
- [ ] Test fixtures created
- [ ] Manual tests pass
- [ ] anthropic dependency added (if needed)

---

## Post-Implementation Notes

After implementation:
1. Test with actual ANTHROPIC_API_KEY to verify Claude API matching works
2. Adjust matching threshold if results are too broad/narrow
3. Consider adding caching for marketplace plugin list to avoid repeated CLI calls
4. Update CLAUDE.md if any workflow changes affect project instructions
