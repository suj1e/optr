# Tool Mapping Reference

自动匹配 PLAN.md 内容到相关专业工具的映射表。

## 发现可用工具

在优化 PLAN.md 之前，先扫描当前项目可用的工具：

```bash
# 扫描所有 skills
find ~/.claude/plugins -name "SKILL.md" 2>/dev/null

# 扫描所有 agents
find ~/.claude/plugins -name "agent.md" -o -name "*-agent.md" 2>/dev/null

# 扫描所有 commands
find ~/.claude/plugins -name "command.md" -o -name "*-command.md" 2>/dev/null
```

## 关键词到工具的映射

### Plugin Development

**关键词**: skill, plugin, agent, command, hook, MCP

| 关键词 | 匹配工具 | 工具路径 | 用途 |
|--------|----------|----------|------|
| `create.*skill` | skill-development | plugin-dev/skills/skill-development | 创建和优化 skills |
| `create.*plugin` | plugin-structure | plugin-dev/skills/plugin-structure | 插件结构指导 |
| `create.*agent` | agent-development | plugin-dev/skills/agent-development | 创建 agents |
| `create.*command` | command-development | plugin-dev/skills/command-development | 创建 commands |
| `create.*hook` | hook-development | plugin-dev/skills/hook-development | 创建 hooks |
| `MCP.*server` | mcp-integration | plugin-dev/skills/mcp-integration | MCP 集成 |
| `plugin.*settings` | plugin-settings | plugin-dev/skills/plugin-settings | 插件配置 |

### Frontend Development

**关键词**: frontend, UI, component, page, design, React, Vue

| 关键词 | 匹配工具 | 工具路径 | 用途 |
|--------|----------|----------|------|
| `build.*frontend` | frontend-design | frontend-design/skills/frontend-design | 前端设计 |
| `create.*component` | frontend-design | frontend-design/skills/frontend-design | 组件设计 |
| `design.*UI` | frontend-design | frontend-design/skills/frontend-design | UI 设计 |

### Code Quality

**关键词**: review, refactor, test, quality

| 关键词 | 匹配工具 | 工具路径 | 用途 |
|--------|----------|----------|------|
| `code.*review` | code-review | code-review/commands/code-review | 代码审查 |
| `review.*PR` | review-pr | pr-review-toolkit/commands/review-pr | PR 审查 |
| `refactor.*code` | code-reviewer | feature-dev/agents/code-reviewer | 代码重构建议 |

### Documentation

**关键词**: CLAUDE.md, documentation, docs

| 关键词 | 匹配工具 | 工具路径 | 用途 |
|--------|----------|----------|------|
| `CLAUDE\.md` | claude-md-improver | claude-md-management/skills/claude-md-improver | CLAUDE.md 优化 |
| `update.*CLAUDE\.md` | claude-md-improver | claude-md-management/skills/claude-md-improver | 更新 CLAUDE.md |

### Feature Development

**关键词**: feature, implement, develop

| 关键词 | 匹配工具 | 工具路径 | 用途 |
|--------|----------|----------|------|
| `develop.*feature` | feature-dev | feature-dev/commands/feature-dev | 功能开发 |
| `explore.*codebase` | code-explorer | feature-dev/agents/code-explorer | 代码探索 |
| `design.*architecture` | code-architect | feature-dev/agents/code-architect | 架构设计 |

## 匹配算法

1. **提取关键词**: 从 PLAN.md 的每个任务中提取关键词
2. **正则匹配**: 使用正则表达式匹配工具描述
3. **优先级排序**: 按匹配度排序相关工具
4. **调用工具**: 使用 Skill 工具调用匹配的 skill

## 示例匹配流程

```python
# PLAN.md 任务: "创建一个用户认证 skill"
# 提取关键词: ["create", "skill"]
# 匹配工具: skill-development
# 调用: Skill(skill="skill-development")

# PLAN.md 任务: "构建用户管理界面"
# 提取关键词: ["build", "界面", "UI"]
# 匹配工具: frontend-design
# 调用: Skill(skill="frontend-design")

# PLAN.md 任务: "更新 CLAUDE.md 项目文档"
# 提取关键词: ["CLAUDE.md", "文档"]
# 匹配工具: claude-md-improver
# 调用: Skill(skill="claude-md-improver")
```

## 动态发现

除了预定义映射，还可以动态发现工具：

```bash
# 获取所有 skill 的描述
grep -r "^description:" ~/.claude/plugins --include="SKILL.md" | head -20

# 示例输出:
# plugin-dev/skills/skill-development/SKILL.md:description: This skill should be used when the user wants to "create a skill"
# frontend-design/skills/frontend-design/SKILL.md:description: Create distinctive, production-grade frontend interfaces
```

然后用 Grep 工具在 PLAN.md 中搜索匹配的触发短语。
