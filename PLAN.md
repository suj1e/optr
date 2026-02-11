# PLAN

_Start: 2026-02-11_

## Phase 1: 需求分析与设计 ✅
- [x] 分析当前 discover-tools.py 的工具匹配逻辑
  - 当前局限：仅扫描本地 ~/.claude/plugins 目录
  - 需要扩展：支持在线搜索最佳实践工具
- [x] 设计新功能架构
  - 输入：解析 PLAN.md 任务描述，提取关键词
  - 处理：结合本地工具 + 在线搜索
  - 输出：工具推荐列表，供用户确认
- [x] 确定技术方案
  - 使用 WebSearch/WebFetch 搜索相关工具
  - 解析 Claude 官方文档和社区最佳实践
  - 集成到现有 discover-tools.py

## Phase 2: 核心功能实现 ✅
- [x] 修改 discover-tools.py 添加在线搜索功能
  - 新增 `search_online_tools(keywords)` 函数
  - 解析搜索结果，提取工具名称和用途
  - 去重并评分，与本地工具合并
- [x] 实现用户确认交互
  - 输出工具列表，包含：名称、用途、来源、推荐理由
  - 支持用户选择安装哪些工具
  - 显示安装命令（如 `claude plugin add`）
- [x] 更新 optimize-plan.py 集成新工具匹配

## Phase 3: 测试与文档 ✅
- [x] 测试在线搜索功能
  - 验证不同关键词的搜索结果质量
  - 确认工具推荐的准确性
- [x] 更新 SKILL.md 文档
  - 说明新功能工作流程
  - 添加使用示例
- [x] 更新 CLAUDE.md 脚本说明

## 验收标准 ✅
- [x] discover-tools.py 能搜索并推荐 PLAN.md 相关工具
- [x] 输出格式清晰，包含工具用途和安装方式
- [x] 用户可选择确认后安装
- [x] 不限制工具数量，但推荐的都是高效好用的

---

_Completed: 2026-02-11_
