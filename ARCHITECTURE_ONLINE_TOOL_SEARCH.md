# Architecture Document: Online Tool Search for discover-tools.py

## Overview

Add capability to discover Claude Code plugins/skills/agents/commands from online sources (GitHub, npm, etc.) when local discovery doesn't yield sufficient matches.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         discover-tools.py                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐    ┌──────────────────────┐    ┌──────────────┐  │
│  │  Local Discovery │    │  Online Discovery    │    │  Deduplicator │  │
│  │  (scan_plugins)  │    │  (search_online)     │    │  (dedupe)     │  │
│  └────────┬─────────┘    └──────────┬───────────┘    └───────┬──────┘  │
│           │                         │                         │         │
│           │ Local tools             │ Online tools            │         │
│           │ (skills, agents, cmds)  │ (GitHub, npm, etc.)     │         │
│           └─────────────────────────┼─────────────────────────┘         │
│                                     │                                     │
│                                     ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    Scoring Engine                                    ││
│  │  - Local match score                                                ││
│  │  - Online relevance score                                          ││
│  │  - Combined ranking                                                ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                     │                                     │
│                                     ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    User Confirmation Workflow                        ││
│  │  - Present matched tools (local + online)                          ││
│  │  - User selection/approval                                          ││
│  │  - Output final tool list                                          ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
1. Input: PLAN.md path
   │
   ▼
2. Local Discovery: scan ~/.claude/plugins for tools
   │
   ▼
3. Match local tools to PLAN.md (existing algorithm)
   │
   ▼
4. Check match quality (is_local_sufficient)
   ├─ If YES: Return local matches
   └─ If NO: Continue to online search
   │
   ▼
5. Online Search (new feature)
   ├─ Extract search queries from PLAN.md
   ├─ Search GitHub/npm for Claude plugins
   └─ Fetch tool metadata via WebFetch
   │
   ▼
6. Deduplicate: Merge local + online, remove duplicates
   │
   ▼
7. Score and Rank: Combine relevance scores
   │
   ▼
8. Present to User: Show options, get confirmation
   │
   ▼
9. Output: JSON with matched tools + sources
```

## New API Signatures

### Python Functions

```python
# New functions to add to discover-tools.py

def search_online_for_tools(
    plan_content: str,
    min_relevance: float = 0.3,
    max_results: int = 20
) -> list[dict]:
    """
    Search online sources for relevant Claude Code tools.

    Args:
        plan_content: Raw PLAN.md content
        min_relevance: Minimum relevance score (0-1) to include
        max_results: Maximum number of online results to return

    Returns:
        List of online tool dictionaries with:
        {
            'name': str,
            'description': str,
            'url': str,
            'source': 'github' | 'npm' | 'manual',
            'relevance_score': float,
            'keywords': list[str],
            'install_command': str | None
        }
    """
    pass


def extract_search_queries(plan_content: str) -> list[str]:
    """
    Extract search queries from PLAN.md for online search.

    Returns:
        List of search query strings optimized for web search.
    """
    pass


def fetch_tool_metadata(url: str) -> dict | None:
    """
    Fetch and parse tool metadata from a URL.

    Args:
        url: Tool repository/documentation URL

    Returns:
        Parsed metadata dict or None if fetch fails
    """
    pass


def deduplicate_tools(local_tools: list, online_tools: list) -> tuple[list, list]:
    """
    Merge local and online tools, removing duplicates.

    Args:
        local_tools: Tools found locally
        online_tools: Tools found online

    Returns:
        Tuple of (merged_tools, new_online_tools) where new_online_tools
        excludes any tools already available locally.
    """
    pass


def calculate_combined_score(
    local_score: float,
    online_score: float,
    weights: dict = {'local': 0.6, 'online': 0.4}
) -> float:
    """
    Calculate combined relevance score.

    Args:
        local_score: Score from local matching algorithm
        online_score: Score from online search
        weights: Scoring weights for each source

    Returns:
        Combined score (0-1)
    """
    pass


def get_user_confirmation(
    matched_tools: list,
    include_online: bool = False
) -> tuple[list, bool]:
    """
    Present matched tools to user and get confirmation.

    Args:
        matched_tools: List of all matched tools (local + online)
        include_online: Whether online tools should be considered

    Returns:
        Tuple of (approved_tools, user_wants_online)
    """
    pass


def main_with_online_search(
    plan_path: Path,
    force_online: bool = False,
    auto_approve: bool = False
) -> dict:
    """
    Main entry point with optional online search.

    Args:
        plan_path: Path to PLAN.md
        force_online: Always include online search
        auto_approve: Skip user confirmation

    Returns:
        Final result dictionary with tools and metadata
    """
    pass
```

### CLI Arguments

```bash
# New options for discover-tools.py
--online              # Enable online search
--force-online        # Always search online, even if local matches exist
--no-online           # Disable online search (default)
--auto-approve        # Skip user confirmation dialog
--min-score float     # Minimum relevance score (default: 0.3)
--max-results int     # Max online results (default: 20)
--exclude-installed   # Don't show tools already installed
```

## Scoring Algorithm

### Local Score (existing)
```python
# Current algorithm
score = sum(1 for keyword in tool_keywords if keyword in plan_keywords)
```

### Online Score (new)
```python
def calculate_online_relevance(query: str, tool: dict) -> float:
    """
    Score online tool relevance based on:
    1. Keyword overlap with search query
    2. Description quality (length, clarity)
    3. Popularity signals (stars, downloads)
    4. Recency (recent updates preferred)
    """
    scores = {
        'keyword_match': keyword_overlap(query, tool['keywords']),
        'description_quality': description_score(tool['description']),
        'popularity': popularity_score(tool.get('stars', 0)),
        'recency': recency_score(tool.get('updated_at'))
    }
    return weighted_average(scores, [0.4, 0.2, 0.2, 0.2])
```

### Combined Score
```python
def combined_score(local: float, online: float) -> float:
    """
    Final score = 0.6 * local_score + 0.4 * online_score

    Rationale:
    - Local tools are preferred (installed = usable)
    - Online tools provide broader coverage
    """
    return 0.6 * local + 0.4 * online
```

## User Confirmation Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    Tool Discovery Results                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Local Tools (5 found, 3 matched):                         │
│    [1] skill-development (score: 8, keywords: create,skill) │
│    [2] frontend-design (score: 5, keywords: build,UI)       │
│    [3] code-review (score: 3, keywords: review)             │
│                                                              │
│  Online Tools (discovered via GitHub search):              │
│    [4] auth-handler (score: 0.85, GitHub)                   │
│    [5] api-gateway (score: 0.72, npm)                       │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  Found 2 additional relevant tools online.                 │
│                                                              │
│  Options:                                                   │
│  [A] Use local tools only                                  │
│  [B] Include all matched tools (local + online)             │
│  [C] Select specific tools from list                        │
│  [Q] Cancel                                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### User Confirmation API

```python
def confirm_tool_selection(
    tools: list,
    local_count: int,
    online_count: int,
    default: str = 'B'
) -> tuple[list, bool]:
    """
    Interactive confirmation workflow.

    Returns:
        (selected_tools, include_online)
    """
    # If --auto-approve, return default selection
    if auto_approve:
        return (tools, online_count > 0)
```

## Error Handling

### WebSearch Failures
```python
try:
    results = web_search(query)
except WebSearchError as e:
    logger.warning(f"Web search failed for '{query}': {e}")
    return []  # Fall back to local-only
```

### WebFetch Failures
```python
def fetch_tool_metadata(url):
    try:
        content = web_fetch(url)
        return parse_metadata(content)
    except (WebFetchError, TimeoutError) as e:
        logger.debug(f"Failed to fetch {url}: {e}")
        return None  # Skip this tool, continue with others
```

### Deduplication Conflicts
```python
def deduplicate(local, online):
    for online_tool in online:
        # Check if local version exists
        if is_similar(online_tool, local):
            # Prefer local version
            online_tool['install_command'] = None  # Mark as already installed
    return online
```

## Integration Points

### Existing Code Integration

```python
# In main():
def main():
    # ... existing code ...

    # NEW: Check for online flag
    if '--online' in sys.argv or '--force-online' in sys.argv:
        enable_online_search()

    # NEW: After local matching
    if not is_local_sufficient(matches) or force_online:
        print("Searching online for additional tools...")
        online_tools = search_online_for_tools(plan_content)
        matches = merge_and_rerank(matches, online_tools)

    # NEW: User confirmation if online tools included
    if has_online_tools(matches):
        if '--auto-approve' not in sys.argv:
            matches = get_user_confirmation(matches)

    # ... rest of existing code ...
```

### Configuration

```python
# Optional config file: ~/.claude/optr-config.json
_search": {
        "enabled": true{
    "online,
        "default_to_online": false,
        "auto_approve": false,
        "preferred_sources": ["github", "npm"],
        "min_score": 0.3,
        "max_results": 20,
        "timeout_seconds": 30
    },
    "sources": {
        "github": {
            "enabled": true,
            "search_query": "claude-code skill OR claude-code plugin"
        },
        "npm": {
            "enabled": true,
            "search_query": "claude-code"
        }
    }
}
```

## File Structure

```
optr-plugin/skills/optr/scripts/
├── discover-tools.py          # Main script (existing)
├── discover-tools-online.py   # NEW: Online search module
├── config/
│   └── optr-config.json       # NEW: Configuration file
├── online_sources/
│   ├── __init__.py
│   ├── github.py              # NEW: GitHub search API
│   ├── npm.py                 # NEW: npm search API
│   └── base.py                # NEW: Abstract source class
└── tests/
    ├── test_online_search.py  # NEW
    └── test_deduplication.py  # NEW
```

## Implementation Roadmap

### Phase 1: Core Infrastructure
- [ ] Create `discover-tools-online.py` module
- [ ] Implement `search_online_for_tools()` function
- [ ] Add `extract_search_queries()` for PLAN.md analysis

### Phase 2: Source Integration
- [ ] Implement GitHub search via WebSearch
- [ ] Implement npm search via WebSearch
- [ ] Add `fetch_tool_metadata()` for URL parsing

### Phase 3: Scoring & Deduplication
- [ ] Implement `calculate_online_relevance()`
- [ ] Implement `deduplicate_tools()`
- [ ] Implement `calculate_combined_score()`

### Phase 4: User Workflow
- [ ] Implement `get_user_confirmation()`
- [ ] Add CLI arguments
- [ ] Integrate with existing `main()`

### Phase 5: Testing & Polish
- [ ] Error handling for network failures
- [ ] Rate limiting for API calls
- [ ] Configuration file support
- [ ] Unit tests
