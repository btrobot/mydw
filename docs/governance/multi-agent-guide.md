# DewuGoJin 多 Agent 协作开发指南

> Updated: 2026-04-12
> Status: Active

本文档只回答一件事：**在当前仓库里，如何以 GitHub-friendly 的方式使用 OMX / Codex 多 agent 协作。**

更高优先级的约束见：

- `AGENTS.md` — 当前工作流总入口与执行约束
- `docs/runtime-local-artifact-policy.md` — runtime / local artifact 边界
- `docs/README.md` — 当前文档阅读入口

## 当前协作面

当前仓库里应被视为**共享协作资产**的内容：

- `AGENTS.md`
- `.codex/agents/`
- `.codex/prompts/`
- `.codex/skills/`

这些内容描述角色、提示词和技能，适合随仓库共享。

以下路径属于**本地 runtime / session**，不要把它们当成主文档入口，也不要把临时状态当成需要长期跟踪的 repo 资产：

- `.omc/`
- `.omx/`
- `.codex/` 下除 `agents/`, `prompts/`, `skills/` 外的历史/状态目录
- 本地 session / runtime 输出目录（仓库不保留 `production/`）

## 什么时候直接做，什么时候多 agent

### 直接在主会话完成

适合：

- 小改动
- 单文件修复
- 明确路径的定向修改
- 简单测试/验证

### 使用多 agent

适合：

- 前后端并行改动
- 文档 + 代码 + 测试需要一起推进
- 需要独立 review / verifier 复核
- 需要大范围搜索、方案评估、结构整理

## 推荐协作模式

### 1. Explore → Plan → Execute → Verify

这是当前仓库最稳定的协作节奏：

1. **Explore**：先理解现状、确认边界
2. **Plan**：形成可执行方案
3. **Execute**：按子任务修改
4. **Verify**：独立验证，不在同一思路里自我批准

### 2. 手递手（handoff）要足够具体

委托时至少包含：

- 背景：为什么要改
- 范围：改哪些文件 / 不改哪些文件
- 约束：测试、兼容、文档边界、生成物边界
- 期望输出：要给结论、补丁，还是只做调查

### 3. 并行只发生在相互独立的切片上

可以并行：

- backend 文档整理 + frontend 文档整理
- 代码修改 + 独立 verifier 检查
- 不同目录下的结构清理

不要并行：

- 两个 agent 改同一文件
- 一个任务依赖另一个任务产出时
- 尚未确定边界的重构

## 当前仓库的推荐分工

| 工作类型 | 推荐处理方式 |
|---|---|
| 仓库结构梳理 | 先 explore，再 plan，再分目录执行 |
| 代码实现 | 主会话或 executor |
| 大范围搜索 | explore |
| 架构/边界判断 | planner / architect |
| 独立复核 | verifier / code-reviewer |
| 测试策略 | test-engineer |

## 与 GitHub-friendly 目录结构的一致性

当前整理原则是：

- 把**源码**、**文档**、**共享 workflow 定义**、**本地 runtime** 分开
- 允许 `.codex/agents/`, `.codex/prompts/`, `.codex/skills/` 保留在仓库中
- 不再让 `.omc/`、`.omx/`、session logs、调试截图、root-level 调试脚本污染 repo surface

换句话说，多 agent 工作流仍然保留，但它应该以**共享定义入库、运行时状态本地化**的方式存在。

## 常见流程示例

### 新功能

1. 读 `docs/README.md` 与相关 current docs
2. explore 现有实现
3. plan 明确改动面
4. 实现前后端变更
5. verifier / targeted tests 复核

### 仓库清理 / 结构重整

1. 先做 inventory
2. 区分 current / working / historical / runtime
3. 清理 tracked runtime artifacts
4. 更新 README / docs / hygiene tests
5. 用 targeted tests 验证边界没有回归

### 调试

1. 先确认是代码问题、生成物问题还是 runtime/state 问题
2. 临时调试产物不要长期停留在 repo root
3. 调试脚本若保留，应明确归入手工工具目录，而不是伪装成正式测试

## 参考文档

- `AGENTS.md`
- `docs/README.md`
- `docs/runtime-local-artifact-policy.md`
- `docs/generated-artifact-policy.md`
- `.codex/skills/team/SKILL.md`
