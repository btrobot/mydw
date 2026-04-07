# L4: Skills 工作流与团队编排

## 1. Skills 系统概述

CCGS 定义了 37+ 个 Skills (技能/工作流)，位于 `.claude/skills/` 目录。Skills 是预定义的多步骤工作流，通过 `/command` 方式触发。

Skills 分为两类:
- **单 agent 技能**: 由一个 agent 独立执行 (如 `/code-review`, `/bug-report`)
- **团队编排技能**: 协调多个 agent 按流水线执行 (如 `/team-combat`, `/team-release`)

## 2. Skill 定义文件格式

每个 Skill 定义为 `SKILL.md` 文件，位于 `.claude/skills/[skill-name]/` 目录。

### 2.1 Frontmatter 结构

```yaml
---
name: team-combat
description: "Orchestrate the combat team: coordinates game-designer, gameplay-programmer..."
argument-hint: "[combat feature description]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task, AskUserQuestion, TodoWrite
---
```

| 字段 | 作用 |
|------|------|
| `name` | 技能唯一标识，对应 `/name` 命令 |
| `description` | 功能描述 |
| `argument-hint` | 参数提示 |
| `user-invocable` | 是否可由用户直接调用 |
| `allowed-tools` | 执行此技能时可用的工具集 |

关键: 团队编排技能的 `allowed-tools` 包含 `Task` 工具，这是启动子 agent 的能力。

## 3. 团队编排技能 (Team Skills)

CCGS 定义了 7 个团队编排技能，每个都是一个多 agent 流水线:

| 技能 | 团队成员 | 流水线阶段 |
|------|---------|-----------|
| `/team-combat` | game-designer, gameplay-programmer, ai-programmer, technical-artist, sound-designer, qa-tester | 设计 -> 架构 -> 并行实现 -> 集成 -> 验证 -> 签核 |
| `/team-narrative` | narrative-director, writer, world-builder, level-designer | 叙事 -> 世界观 -> 关卡 -> 验证 |
| `/team-ui` | ux-designer, ui-programmer, art-director | 设计 -> 实现 -> 视觉审查 |
| `/team-release` | release-manager, qa-lead, devops-engineer, producer | 分支 -> 测试 -> 构建 -> 部署 -> 监控 |
| `/team-polish` | performance-analyst, technical-artist, sound-designer, qa-tester | 性能分析 -> 优化 -> 打磨 -> 回归 |
| `/team-audio` | audio-director, sound-designer, technical-artist, gameplay-programmer | 方向 -> 设计 -> 实现 -> 集成 |
| `/team-level` | level-designer, narrative-director, world-builder, art-director, systems-designer, qa-tester | 叙事 -> 布局 -> 美术 -> 系统 -> 测试 |

### 3.1 团队编排流水线详解 (以 /team-combat 为例)

```
Phase 1: 设计 (串行)
  └── game-designer: 创建/更新设计文档
       输出: design/gdd/[feature].md

Phase 2: 架构 (串行)
  └── gameplay-programmer + ai-programmer: 审查设计文档，设计代码架构
       输出: 架构草图 (类结构、接口、数据流)

Phase 3: 实现 (并行)
  ├── gameplay-programmer: 核心战斗代码
  ├── ai-programmer: NPC/敌人 AI 行为
  ├── technical-artist: VFX 和 shader 效果
  └── sound-designer: 音频事件列表

Phase 4: 集成 (串行)
  └── 连接游戏代码、AI、VFX、音频

Phase 5: 验证 (串行)
  └── qa-tester: 从验收标准编写测试用例，测试边界情况

Phase 6: 签核 (串行)
  └── 汇总所有团队成员的结果，报告状态
```

### 3.2 委派方式

团队编排技能使用 `Task` 工具启动子 agent:

```
Task 工具调用:
  subagent_type: "game-designer"
  prompt: "Design the [feature] mechanic. Read design/gdd/combat-system.md for context.
           Output a complete design document covering: overview, player fantasy,
           detailed rules, formulas, edge cases, dependencies, tuning knobs,
           acceptance criteria."
```

关键规则:
- 每个子 agent 的 prompt 必须包含完整上下文 (文件路径、约束条件)
- 独立的 agent 可以并行启动 (Phase 3)
- 每个阶段转换时使用 `AskUserQuestion` 让用户审批

### 3.3 决策点

团队编排技能在每个阶段转换时都有决策点:

```
Phase 1 完成 -> AskUserQuestion: "设计文档是否批准? [批准/修改/拒绝]"
Phase 2 完成 -> AskUserQuestion: "架构方案是否批准? [批准/修改/拒绝]"
Phase 3 完成 -> AskUserQuestion: "实现是否可以集成? [继续/修改]"
...
```

用户必须在每个阶段批准后才能进入下一阶段。

## 4. 单 Agent 技能

### 4.1 分析类技能

| 技能 | 执行者 | 输入 | 输出 |
|------|--------|------|------|
| `/code-review` | lead-programmer | 文件路径 | 审查报告 (问题列表、严重级别) |
| `/design-review` | game-designer | 设计文档路径 | 审查报告 (完整性、一致性) |
| `/balance-check` | economy-designer | 平衡数据 | 异常值分析 |
| `/perf-profile` | performance-analyst | 代码/场景 | 性能瓶颈报告 |
| `/tech-debt` | lead-programmer | 代码库 | 技术债务清单 |
| `/scope-check` | producer | 当前计划 | 范围蔓延分析 |

### 4.2 生成类技能

| 技能 | 执行者 | 输入 | 输出 |
|------|--------|------|------|
| `/sprint-plan` | producer | 里程碑目标 | Sprint 计划文档 |
| `/bug-report` | qa-tester | 问题描述 | 结构化 bug 报告 |
| `/architecture-decision` | technical-director | 决策问题 | ADR 文档 |
| `/changelog` | release-manager | git 历史 | 变更日志 |
| `/patch-notes` | community-manager | 内部数据 | 面向玩家的更新说明 |
| `/estimate` | producer | 任务描述 | 工作量估算 |

### 4.3 引导类技能

| 技能 | 执行者 | 功能 |
|------|--------|------|
| `/start` | (通用) | 首次引导，检测项目状态，路由到正确工作流 |
| `/brainstorm` | (通用) | 引导式创意探索 |
| `/prototype` | prototyper | 快速原型搭建 |
| `/setup-engine` | (通用) | 引擎配置和技术偏好设置 |
| `/map-systems` | (通用) | 系统分解和依赖映射 |
| `/design-system` | (通用) | 逐节引导式 GDD 编写 |

### 4.4 验证类技能

| 技能 | 执行者 | 功能 |
|------|--------|------|
| `/gate-check` | (通用) | 阶段就绪验证 (PASS/CONCERNS/FAIL) |
| `/release-checklist` | release-manager | 发布前检查清单 |
| `/launch-checklist` | (通用) | 完整上线就绪验证 |
| `/milestone-review` | producer | 里程碑进度审查 |

## 5. /start 技能的特殊地位

`/start` 是整个框架的入口点，体现了 CCGS 的"不假设"原则:

```
1. 静默检测项目状态
   - 引擎是否配置?
   - 游戏概念是否存在?
   - 源代码是否存在?
   - 设计文档是否存在?

2. 询问用户当前状态
   A) 完全没有想法
   B) 模糊的想法
   C) 明确的概念
   D) 已有工作成果

3. 根据回答路由到正确的工作流
   A -> /brainstorm -> /setup-engine -> /map-systems -> /prototype -> /sprint-plan
   B -> /brainstorm [hint] -> /setup-engine -> /map-systems -> /prototype
   C -> /setup-engine -> /design-review -> /map-systems -> /design-system
   D -> /project-stage-detect -> /gate-check -> /sprint-plan

4. 确认后才执行下一步 (不自动运行)
```

## 6. Skills 与 Agent 的绑定关系

Agent 定义中的 `skills` 字段决定了哪些 agent 可以执行哪些技能:

```yaml
# producer.md
skills: [sprint-plan, scope-check, estimate, milestone-review]

# lead-programmer.md
skills: [code-review, architecture-decision, tech-debt]
```

未绑定 skills 的 agent 不能直接执行技能，但可以被团队编排技能通过 Task 工具调用。

## 7. 对 DewuGoJin 的启示

1. **团队编排模式**: DewuGoJin 可定义类似的团队技能，如 `/team-publish` (编排账号管理、视频处理、自动化发布的完整流水线)
2. **阶段门控**: 每个阶段转换都需要用户批准，防止 agent 自主推进
3. **并行执行**: 独立的子任务可以并行启动，提高效率
4. **/start 入口**: 为新用户提供引导式入口，根据项目状态自动路由
5. **Skills 与 Agent 绑定**: 确保正确的 agent 执行正确的工作流
