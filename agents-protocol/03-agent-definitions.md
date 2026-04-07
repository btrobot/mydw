# L2: Agent 定义结构与层级体系

## 1. Agent 定义文件格式

每个 agent 定义为一个 `.md` 文件，位于 `.claude/agents/` 目录。文件由 YAML frontmatter + Markdown body 组成。

### 1.1 Frontmatter 结构

```yaml
---
name: lead-programmer
description: "The Lead Programmer owns code-level architecture..."
tools: Read, Glob, Grep, Write, Edit, Bash
model: kimi-for-coding
maxTurns: 20
memory: user          # 可选，启用用户级记忆
skills: [code-review, architecture-decision, tech-debt]  # 可选，绑定技能
---
```

| 字段 | 作用 | 通信意义 |
|------|------|---------|
| `name` | agent 唯一标识 | 其他 agent 通过此名称引用和委派 |
| `description` | 能力描述 | 决定何时被选中调用 |
| `tools` | 可用工具列表 | 限制 agent 的操作能力边界 |
| `model` | 使用的 LLM 模型 | 影响推理能力和成本 |
| `maxTurns` | 最大交互轮次 | 防止 agent 无限循环 |
| `memory` | 记忆类型 | 跨会话状态持久化 |
| `skills` | 绑定的技能 | 决定 agent 可执行的工作流 |

### 1.2 Body 结构 (Markdown)

Body 部分是 agent 的系统提示词，包含:

1. **角色定义**: "You are the [Role] for..."
2. **协作协议**: 标准化的交互模式 (见第 4 章)
3. **核心职责**: Key Responsibilities 列表
4. **禁止事项**: What This Agent Must NOT Do
5. **委派地图**: Delegation Map -- 上报/下派/协调关系

## 2. 三层层级体系

### 2.1 Tier 1: 领导层 (3 个 agent)

| Agent | 决策领域 | 模型 | maxTurns |
|-------|---------|------|----------|
| `creative-director` | 创意愿景、创意冲突 | kimi-for-coding | 30 |
| `technical-director` | 技术架构、技术选型 | kimi-for-coding | 30 |
| `producer` | 进度管理、跨部门协调 | kimi-for-coding | 30 |

特点:
- 使用最高级模型
- maxTurns 最大 (30)
- 拥有 `memory: user` (跨会话记忆)
- 协作协议: Leadership Agent Protocol

### 2.2 Tier 2: 部门层 (8 个 agent)

| Agent | 专业领域 | 模型 | maxTurns |
|-------|---------|------|----------|
| `game-designer` | 游戏设计 | kimi-for-coding | 25 |
| `lead-programmer` | 代码架构 | kimi-for-coding | 20 |
| `art-director` | 视觉方向 | kimi-for-coding | 20 |
| `audio-director` | 音频方向 | kimi-for-coding | 20 |
| `narrative-director` | 叙事方向 | kimi-for-coding | 20 |
| `qa-lead` | 质量保障 | kimi-for-coding | 20 |
| `release-manager` | 发布管线 | kimi-for-coding | 20 |
| `localization-lead` | 国际化 | kimi-for-coding | 20 |

特点:
- 拥有各自领域的专业知识
- 可向下委派给 Tier 3 专家
- 协作协议: Design Agent Protocol 或 Implementation Agent Protocol

### 2.3 Tier 3: 专家层 (37+ 个 agent)

包括各类专业开发者、设计师、测试人员等。按领域分组:

**设计类**: systems-designer, level-designer, economy-designer, ux-designer
**编程类**: gameplay-programmer, engine-programmer, ai-programmer, network-programmer, tools-programmer, ui-programmer
**内容类**: writer, world-builder, sound-designer, technical-artist
**运维类**: devops-engineer, performance-analyst, analytics-engineer, security-engineer
**引擎专家**: unreal-specialist, unity-specialist, godot-specialist (各含子专家)

特点:
- 执行具体任务
- 不能做跨域决策
- 协作协议: Implementation Agent Protocol

## 3. 委派关系图

```
                         [Human Developer]
                               |
               +---------------+---------------+
               |               |               |
       creative-director  technical-director  producer
               |               |               |
      +--------+--------+     |        (coordinates all)
      |        |        |     |
game-designer art-dir  narr-dir  lead-programmer  qa-lead  audio-dir
      |        |        |         |                |        |
   +--+--+     |     +--+--+  +--+--+--+--+--+   |        |
   |  |  |     |     |     |  |  |  |  |  |  |   |        |
  sys lvl eco  ta   wrt  wrld gp ep  ai net tl ui qa-t    snd
```

### 3.1 委派规则表

| 委派方 | 可委派给 |
|--------|---------|
| creative-director | game-designer, art-director, audio-director, narrative-director |
| technical-director | lead-programmer, devops-engineer, performance-analyst |
| producer | 任何 agent (仅限其领域内的任务分配) |
| game-designer | systems-designer, level-designer, economy-designer |
| lead-programmer | gameplay-programmer, engine-programmer, ai-programmer, network-programmer, tools-programmer, ui-programmer |
| art-director | technical-artist, ux-designer |
| audio-director | sound-designer |
| narrative-director | writer, world-builder |
| qa-lead | qa-tester |

### 3.2 升级路径

| 冲突类型 | 升级到 |
|---------|--------|
| 两个设计师对机制有分歧 | game-designer |
| 游戏设计 vs 叙事冲突 | creative-director |
| 设计 vs 技术可行性 | producer 协调 -> creative-director + technical-director |
| 代码架构分歧 | technical-director |
| 跨系统代码冲突 | lead-programmer -> technical-director |
| 排期冲突 | producer |
| 质量门禁分歧 | qa-lead -> technical-director |

## 4. Agent 定义中的通信要素

### 4.1 Delegation Map (委派地图)

每个 agent 定义文件末尾都包含明确的委派地图:

```markdown
### Delegation Map

Delegates to:
- `gameplay-programmer` for gameplay feature implementation
- `engine-programmer` for core engine systems

Reports to: `technical-director`
Coordinates with: `game-designer` for feature specs, `qa-lead` for testability
```

三种关系:
- **Delegates to**: 可以向谁分配任务
- **Reports to**: 向谁汇报/升级
- **Coordinates with**: 需要与谁协调

### 4.2 Skills 绑定

agent 通过 `skills` 字段绑定可执行的工作流:

```yaml
skills: [code-review, architecture-decision, tech-debt]
```

这意味着该 agent 可以执行 `/code-review`、`/architecture-decision`、`/tech-debt` 等技能。

### 4.3 Tools 限制

不同 agent 拥有不同的工具集:

- 领导层: `Read, Glob, Grep, Write, Edit, Bash, WebSearch`
- 技能编排: `Read, Glob, Grep, Write, Edit, Bash, Task, AskUserQuestion, TodoWrite`
- 只读分析: `Read, Glob, Grep, AskUserQuestion`

`Task` 工具是 agent 间通信的关键 -- 它允许一个 agent 启动另一个 agent 作为子 agent。

## 5. 电商项目适配

CCGS 原本是游戏开发框架，后适配为电商项目。电商相关 agent 包括:

| Agent | 电商职责 |
|-------|---------|
| `biz-pm` | 核心业务产品 (商品/订单/支付/用户 PRD) |
| `marketing-pm` | 营销增长产品 |
| `backend-arch` | 后端架构 (服务边界、API 设计、数据模型) |
| `frontend-arch` | 前端架构 |
| `product-dev` | 商品服务开发 |
| `order-dev` | 订单服务开发 |
| `payment-dev` | 支付服务开发 |
| `marketing-dev` | 营销服务开发 |
| `miniprogram-dev` | 小程序开发 |
| `admin-dev` | 管理后台开发 |

## 6. 对 DewuGoJin 的启示

1. **Frontmatter 标准化**: CCGS 用 YAML frontmatter 定义 agent 元数据，DewuGoJin 可采用相同格式
2. **maxTurns 分级**: 领导层 30、部门层 20-25、专家层更低，防止 agent 失控
3. **Tools 最小权限**: 每个 agent 只给必要的工具，减少误操作风险
4. **Delegation Map 显式化**: 每个 agent 文件中明确写出上下级和协调关系
5. **Skills 绑定**: 将工作流与 agent 关联，确保正确的 agent 执行正确的任务
