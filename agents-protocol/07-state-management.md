# L6: 状态管理与上下文持久化

## 1. 核心理念: 文件即内存

CCGS 的状态管理建立在一个核心理念上:

> **文件是记忆，对话是临时的。** 对话是短暂的，会被压缩或丢失。磁盘上的文件跨越压缩和会话崩溃持久存在。

这意味着 agent 间的"长期通信"不依赖对话上下文，而是通过文件系统实现。

## 2. 状态管理架构

```
production/
├── session-state/
│   └── active.md          ← 活跃会话状态 (临时，会话结束时归档删除)
├── session-logs/
│   ├── session-log.md     ← 会话日志归档 (持久)
│   ├── agent-audit.log    ← Agent 调用审计 (持久)
│   └── compaction-log.txt ← 上下文压缩记录 (持久)
├── sprints/               ← Sprint 计划文档
├── milestones/            ← 里程碑文档
└── tests/                 ← 自检日志

.claude/memory/
├── PROJECT.md             ← 项目核心记忆 (永久)
├── PATTERNS.md            ← 常用模式速查 (永久)
└── DECISIONS.md           ← 关键决策记录 (永久)
```

## 3. active.md -- 会话状态文件

### 3.1 生命周期

```
会话启动
  │
  ├── session-start.sh 检测 active.md 是否存在
  │   ├── 存在: 预览前 20 行，提示 Claude 读取恢复上下文
  │   └── 不存在: 正常启动
  │
  ▼
会话进行中
  │
  ├── Agent 在关键节点更新 active.md:
  │   - 设计节批准并写入文件后
  │   - 架构决策做出后
  │   - 实现里程碑达成后
  │   - 测试结果获得后
  │
  ▼
上下文压缩前
  │
  ├── pre-compact.sh 将 active.md 内容注入对话
  │   (确保压缩摘要包含关键状态)
  │
  ▼
会话结束
  │
  └── session-stop.sh:
      1. 将 active.md 归档到 session-log.md
      2. 删除 active.md
```

### 3.2 内容结构

active.md 应包含:
- 当前任务
- 进度检查清单
- 已做出的关键决策
- 正在处理的文件列表
- 未解决的问题

Production 阶段还包含 STATUS 块:

```markdown
<!-- STATUS -->
Epic: Combat System
Feature: Melee Combat
Task: Implement hitbox detection
<!-- /STATUS -->
```

这个 STATUS 块会被 `statusline.sh` 解析，显示在状态栏中。

### 3.3 更新时机

| 事件 | 更新内容 |
|------|---------|
| 设计节批准 | 标记该节完成，记录决策 |
| 架构决策 | 记录 ADR 编号和关键结论 |
| 实现里程碑 | 更新进度检查清单 |
| 测试结果 | 记录通过/失败数量 |
| 任务开始/完成/阻塞 | 更新任务状态 |
| Agent 调用结果 | 记录成功/失败/阻塞 |

## 4. Memory 系统 (.claude/memory/)

CCGS 使用 `.claude/memory/` 目录存储跨会话的永久记忆:

### 4.1 PROJECT.md -- 项目核心记忆

内容:
- 项目概述 (名称、类型、架构)
- 技术栈
- 规范位置索引
- 常用引用快捷方式
- 绝对禁止事项 (从错误中学到的教训)
- 必须执行事项 (质量门禁)
- 标杆参照 (参考实现)
- 关键决策快速查阅

特点:
- 这是"从错误中学习"的机制
- 例如: "禁止在生成类型上再包一层手动封装 -- 教训: api-contract 12分钟生命周期"
- 新会话的 agent 读取此文件，避免重复犯错

### 4.2 PATTERNS.md -- 常用模式速查

内容:
- 后端模式 (Service 方法模板、事务处理、跨域调用、循环依赖处理)
- 前端模式 (页面生命周期、请求封装、并行请求、Pinia Store)
- 列表页模式
- 会话恢复点格式
- 质量门禁命令

特点:
- 这是 agent 间"知识共享"的机制
- 一个 agent 总结出的最佳实践，所有 agent 都可以引用
- 避免每个 agent 重新发现相同的模式

### 4.3 DECISIONS.md -- 关键决策记录

内容:
- ADR 快速查阅索引
- 每个 ADR 的状态、关键结论、理由、实施代码示例
- 其他关键决策 (循环依赖处理优先级、两遍执行策略、批量修复原则)

特点:
- 这是"决策传播"的机制
- 新 agent 不需要重新讨论已决定的事项
- 包含代码示例，agent 可以直接参考实现

## 5. 增量文件写入策略

CCGS 定义了一种"增量写入"策略来管理大型文档的创建:

```
1. 立即创建文件骨架 (所有节标题，空内容)
2. 在对话中逐节讨论和起草
3. 每节批准后立即写入文件
4. 写入后更新 active.md
5. 已写入的节可以安全地被上下文压缩丢弃 -- 决策在文件中
```

这种策略的通信意义:
- 对话上下文只需保持当前节的讨论 (~3-5k tokens)
- 而非整个文档的讨论历史 (~30-50k tokens)
- 文件成为 agent 间的"共享内存"

## 6. 上下文预算

CCGS 为不同任务类型定义了上下文预算:

| 任务类型 | 预算 |
|---------|------|
| 轻量 (读取/审查) | ~3k tokens 启动 |
| 中等 (实现功能) | ~8k tokens |
| 重量 (多系统重构) | ~15k tokens |

## 7. 压缩与恢复流程

### 7.1 主动压缩

在 60-70% 上下文使用率时主动压缩，而非等到极限。

自然压缩点:
- 写入一节到文件后
- 提交代码后
- 完成一个任务后
- 开始新话题前

聚焦压缩命令:
```
/compact Focus on [current task] — sections 1-3 are written to file, working on section 4
```

### 7.2 压缩后恢复

```
1. pre-compact.sh 已将状态注入压缩前对话
2. 压缩摘要包含:
   - active.md 的引用
   - 已修改文件列表
   - 架构决策
   - Sprint 任务状态
   - Agent 调用结果
   - 测试结果
   - 未解决的阻塞
3. 压缩后: 读取 active.md 和正在处理的文件恢复完整上下文
```

### 7.3 会话崩溃恢复

```
1. session-start.sh 自动检测 active.md
2. 输出: "检测到活跃会话状态，读取此文件以恢复上下文"
3. Agent 读取 active.md
4. 读取部分完成的文件
5. 从下一个未完成的节或任务继续
```

## 8. 子 Agent 的上下文隔离

子 agent (通过 Task 工具启动) 运行在独立的上下文窗口中:

- 不继承对话历史
- 必须在 prompt 中提供完整上下文
- 只返回结果摘要给主 agent
- 适合: 跨多文件调查、探索不熟悉的代码、消耗 >5k tokens 的研究
- 不适合: 已知只需检查 1-2 个文件的情况

## 9. 审计追踪

CCGS 维护多层审计追踪:

| 日志 | 位置 | 内容 | 写入者 |
|------|------|------|--------|
| Agent 调用日志 | `session-logs/agent-audit.log` | 时间戳 + agent 名称 | log-agent.sh |
| 会话日志 | `session-logs/session-log.md` | 提交记录 + 未提交变更 + 归档状态 | session-stop.sh |
| 压缩日志 | `session-logs/compaction-log.txt` | 压缩时间戳 | pre-compact.sh |

## 10. 对 DewuGoJin 的启示

1. **active.md 生命周期管理**: DewuGoJin 已有 `production/session-state/active.md`，可参考 CCGS 的完整生命周期 (启动检测 -> 运行时更新 -> 压缩前保存 -> 结束时归档)
2. **Memory 目录**: 建立 `.claude/memory/` 存储项目核心记忆、模式速查、决策记录
3. **增量写入策略**: 大型文档逐节写入，减少上下文压力
4. **主动压缩**: 在 60-70% 时主动压缩，不等到极限
5. **审计追踪**: SubagentStart hook 记录所有 agent 调用，便于调试和优化协作模式
6. **从错误中学习**: PROJECT.md 中的"绝对禁止"列表是宝贵的知识积累机制
