# CCGS 多 Agent 通信机制 -- 总览

> 分析对象: Claude-Code-Game-Studios (CCGS) 项目
> 分析日期: 2026-04-07
> 目的: 为 DewuGoJin 项目提供 agent 通信架构参考

## 1. 项目背景

CCGS 是一个基于 Claude Code 多 agent 框架的电商平台项目 (ShopXO Next)，采用 Monorepo 架构。该项目定义了 48+ 个专业化 agent，组织为三层层级结构，通过文件系统、hooks、skills、rules 等机制实现 agent 间的通信与协调。

## 2. 通信架构全景

```
                    ┌─────────────────────────────────────┐
                    │         Human Developer (用户)        │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │        CLAUDE.md (主配置入口)         │
                    │  - 层级定义、协作协议、上下文管理       │
                    └──────────────┬──────────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
  ┌───────▼───────┐    ┌──────────▼──────────┐   ┌────────▼────────┐
  │  settings.json │    │  .claude/agents/     │   │  .claude/docs/  │
  │  (hooks 配置)   │    │  (agent 定义文件)     │   │  (共享知识库)    │
  └───────┬───────┘    └──────────┬──────────┘   └────────┬────────┘
          │                        │                        │
  ┌───────▼───────┐    ┌──────────▼──────────┐   ┌────────▼────────┐
  │  .claude/hooks │    │  .claude/skills/     │   │  .claude/rules/ │
  │  (生命周期钩子) │    │  (技能/工作流定义)    │   │  (路径规则)      │
  └───────┬───────┘    └──────────┬──────────┘   └────────┬────────┘
          │                        │                        │
          └────────────────────────┼────────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │     production/session-state/        │
                    │     (运行时状态 -- 文件即内存)         │
                    └─────────────────────────────────────┘
```

## 3. 通信层次划分

CCGS 的 agent 通信机制可分为 6 个层次:

| 层次 | 机制 | 文档 |
|------|------|------|
| L1: 配置层 | `settings.json` -- hooks 注册、权限控制 | `02-settings-hooks.md` |
| L2: 定义层 | Agent 定义文件 -- 角色、职责、委派关系 | `03-agent-definitions.md` |
| L3: 协议层 | 协作协议 -- 垂直委派、冲突升级、handoff | `04-coordination-protocol.md` |
| L4: 工作流层 | Skills -- 多 agent 编排、团队流水线 | `05-skills-workflow.md` |
| L5: 守护层 | Rules + Hooks -- 路径规则、生命周期守护 | `06-rules-guards.md` |
| L6: 状态层 | Session State + Memory -- 持久化状态管理 | `07-state-management.md` |

## 4. 核心设计原则

### 4.1 文件即内存 (File-Backed State)

CCGS 最核心的通信理念: **文件是记忆，对话是临时的**。所有关键决策、状态、上下文都持久化到文件系统，不依赖对话上下文。这解决了 LLM 上下文窗口有限的根本问题。

### 4.2 垂直委派 + 水平协商

- 垂直: 领导层 -> 部门层 -> 专家层，逐级委派，不跳级
- 水平: 同级 agent 可协商，但不能做跨域绑定决策

### 4.3 用户是最终决策者

所有 agent 都是"协作顾问"，不是"自主执行者"。工作流固定为:

```
Question -> Options -> Decision -> Draft -> Approval
```

### 4.4 Hook 驱动的生命周期管理

通过 Claude Code 的 hook 系统，在会话启动、工具调用前后、上下文压缩前、会话结束等关键节点注入自动化逻辑。

## 5. 文档索引

| 文件 | 内容 |
|------|------|
| `01-overview.md` | 本文件 -- 总览 |
| `02-settings-hooks.md` | settings.json 配置与 hooks 生命周期 |
| `03-agent-definitions.md` | Agent 定义结构与层级体系 |
| `04-coordination-protocol.md` | 协作协议、委派规则、冲突解决 |
| `05-skills-workflow.md` | Skills 工作流与团队编排 |
| `06-rules-guards.md` | 路径规则与守护机制 |
| `07-state-management.md` | 状态管理与上下文持久化 |
| `08-dewugojin-comparison.md` | 与 DewuGoJin 的对比及借鉴建议 |
