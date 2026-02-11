# Team Workflow Reference

Detailed patterns for coordinating Claude Code teams.

## Team Lifecycle

### 1. Team Creation

```bash
TeamCreate(
  team_name: "project-name",
  description: "Brief description of team purpose",
  agent_type: "general-purpose"  # or other specialist types
)
```

### 2. Spawning Teammates

```bash
Task(
  subagent_type: "general-purpose",
  team_name: "project-name",  # Must match created team
  name: "member-name",  # Human-readable name for messaging
  prompt: "Your role and instructions..."
)
```

### 3. Task Assignment

```bash
TaskUpdate(
  taskId: "1",
  owner: "member-name"  # Assign to specific teammate
)
```

### 4. Dependency Management

```bash
TaskUpdate(
  taskId: "2",
  addBlockedBy: ["1"]  # Task 2 waits for task 1
)

TaskUpdate(
  taskId: "1",
  addBlocks: ["2"]  # Task 1 blocks task 2
)
```

### 5. Shutdown Sequence

1. Send shutdown requests to each teammate:
```bash
SendMessage(
  type: "shutdown_request",
  recipient: "member-name",
  content: "All tasks complete, shutting down"
)
```

2. Delete team after all teammates terminate:
```bash
TeamDelete()
```

## Teammate Coordination

### Checking Team Status

```bash
TaskList()  # See all tasks and their status
```

### Discovering Team Members

Read team config to find member names:
```bash
Read(~/.claude/teams/{team-name}/config.json)
```

### Inter-Team Communication

```bash
SendMessage(
  type: "message",
  recipient: "member-name",
  content: "Update or question...",
  summary: "Brief summary"
)
```

## Common Patterns

### Parallel Execution

Spawn multiple teammates and assign independent tasks simultaneously:
- Tasks with empty `blockedBy` can run in parallel
- Use `TeamCreate` with multiple `Task` calls in one message

### Sequential Pipeline

Use `addBlockedBy` to create chains:
```
Task1 -> Task2 -> Task3
```

### Fan-Out/Fan-In

One task spawns multiple parallel tasks, then汇总:
```
Task1 (setup)
  ├── Task2 (parallel work A)
  ├── Task3 (parallel work B)
  └── Task4 (parallel work C)
      ↓
Task5 (integration, blockedBy: [2,3,4])
```

## Idle State Handling

Teammates automatically go idle after each turn. This is normal:
- Idle teammates can receive messages
- Use `SendMessage` to wake them with new work
- Idle notifications are informational, not errors
