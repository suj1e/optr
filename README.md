# OPTR - Optimizer & Team Runner

OPTR 是一个 Claude Code 技能插件，用于自动化项目计划优化和任务执行。

## 功能特性

- **智能计划优化**：分析 PLAN.md，识别模糊任务、过大任务和缺失的验收标准
- **自动工具匹配**：扫描可用插件，将任务与专业工具智能关联
- **团队任务执行**：自动创建团队并分配任务
- **文档自动同步**：任务完成后自动更新 PLAN.md、README.md 和 CLAUDE.md

## 安装说明

```bash
./install.sh
```

或手动安装：

```bash
cp -r optr-plugin/skills/optr ~/.claude/skills/optr
```

## 使用方法

1. 运行 `claude`
2. 输入 `/optr` 或相关触发短语
3. OPTR 将自动优化 PLAN.md 并执行任务
