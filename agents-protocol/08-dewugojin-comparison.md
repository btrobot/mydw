# 与 DewuGoJin 的对比及借鉴建议

## 1. 框架对比总览

| 维度 | CCGS (参考) | DewuGoJin (当前) | 差距评估 |
|------|------------|-----------------|---------|
| Agent 数量 | 48+ (三层层级) | 7 (两层层级) | DewuGoJin 规模合理，无需扩展 |
| Agent 定义格式 | YAML frontmatter + Markdown | YAML frontmatter + Markdown | 基本一致 |
| Hooks 数量 | 7 个 (6 类事件) | 6 个 (TypeScript) | DewuGoJin 已覆盖核心事件 |
| Skills 数量 | 37+ | 7 | 可按需扩展 |
| Rules 数量 | 11 (路径规则) | 9 | 基本一致 |
| 协作协议 | 三种模板 (Leadership/Design/Implementation) | 统一协议 | 可细化 |
| Memory 系统 | `.claude/memory/` (PROJECT/PATTERNS/DECISIONS) | 无独立 memory 目录 | 建议引入 |
| 状态管理 | active.md 完整生命周期 | active.md 已有 | 可完善生命周期 |
| 审计追踪 | agent-audit.log + session-log + compaction-log | session-log + agent-audit | 基本一致 |
| 自检机制 | agent-collaboration-check.sh | 无 | 建议引入 |

## 2. DewuGoJin 已有的优势

DewuGoJin 在某些方面已经超越了 CCGS:

### 2.1 Handoff 协议更完善

DewuGoJin 的 `coordination-rules.md` 定义了详细的 Handoff 格式:

```markdown
## Handoff
**From**: [caller agent name]
**To**: [target agent name]
**Task**: [one-line summary]
### Context / Constraints / Input Artifacts / Expected Output
```

CCGS 没有这种显式的 handoff 格式，agent 间的任务传递更依赖隐式约定。

### 2.2 失败检测与恢复更系统化

DewuGoJin 定义了 5 种失败类型 (Timeout/Wrong output/Scope violation/Quality failure/Blocked) 和恢复流程 (Refine -> Reroute -> Absorb)，以及 2 次重试限制。CCGS 没有这种级别的失败处理机制。

### 2.3 并行 Handoff 同步门控

DewuGoJin 定义了并行 agent 的同步门控机制:
1. 启动并行 agent
2. 各自完成并返回
3. 集成检查 (输出兼容性、冲突检测)
4. 同步门控通过后才进入下一阶段

### 2.4 跨域变更授权流程

DewuGoJin 有明确的跨域变更授权流程 (请求 -> 解释 -> 确认 -> 文档化)，比 CCGS 的"禁止单方面跨域修改"更具操作性。

### 2.5 Hooks 使用 TypeScript

DewuGoJin 的 hooks 使用 TypeScript (通过 bun 执行)，比 CCGS 的 bash 脚本更类型安全、更易维护。

## 3. 建议从 CCGS 借鉴的机制

### 3.1 Memory 系统 (高优先级)

建议在 `.claude/memory/` 下创建三个文件:

```
.claude/memory/
├── PROJECT.md     -- 项目核心记忆 (技术栈、规范位置、绝对禁止事项)
├── PATTERNS.md    -- 常用模式速查 (API 模式、Patchright 模式、FFmpeg 模式)
└── DECISIONS.md   -- 关键决策记录 (ADR 索引、实施代码示例)
```

价值: 新会话的 agent 读取这些文件，避免重复犯错，共享最佳实践。

CCGS 的 PROJECT.md 中"绝对禁止"列表特别有价值:
```markdown
## 绝对禁止
1. 禁止在生成类型上再包一层手动封装
   - 教训: api-contract 12分钟生命周期
```

DewuGoJin 可以记录类似的教训，如:
```markdown
## 绝对禁止
1. 禁止在 Patchright 脚本中使用 page.wait_for_timeout() 替代显式等待
   - 教训: [具体教训]
2. 禁止在 cookie 加密中使用固定 IV
   - 教训: [具体教训]
```

### 3.2 三种协作协议模板 (中优先级)

当前 DewuGoJin 所有 agent 使用统一的协作协议。建议参考 CCGS 细化为:

| 协议 | 适用 Agent | 核心特征 |
|------|-----------|---------|
| Leadership Protocol | Tech Lead | 战略决策工作流: 理解 -> 框定 -> 选项 -> 推荐 -> 支持 |
| Design Protocol | Frontend Lead, Backend Lead | 提问优先: 澄清 -> 选项 -> 迭代起草 -> 批准写入 |
| Implementation Protocol | Automation Developer, DevOps | 实现工作流: 读设计 -> 提问 -> 提出架构 -> 透明实现 -> 批准写入 |

### 3.3 active.md 完整生命周期 (中优先级)

当前 DewuGoJin 有 active.md 但生命周期管理不如 CCGS 完善。建议补充:

```
SessionStart hook:
  - 检测 active.md 是否存在
  - 存在则预览并提示恢复

PreCompact hook:
  - 将 active.md 内容注入压缩前对话
  - 列出未提交变更和 WIP 标记

Stop hook:
  - 归档 active.md 到 session-log.md
  - 删除 active.md
```

### 3.4 SubagentStart 审计增强 (低优先级)

DewuGoJin 已有 `log-agent.ts`，可参考 CCGS 增加更多上下文:

```
20260407_143022 | Agent invoked: backend-lead | Task: implement account API
```

### 3.5 StatusLine 增强 (低优先级)

CCGS 的 statusline 显示:
```
ctx: 45% | Model | Stage | Epic > Feature > Task
```

DewuGoJin 可参考添加项目阶段和当前任务面包屑。

### 3.6 协作自检脚本 (低优先级)

参考 CCGS 的 `agent-collaboration-check.sh`，创建一个自检脚本验证:
- 所有 agent 定义文件是否存在
- session-state 目录是否正常
- 文档是否同步
- 测试覆盖情况

## 4. 不建议借鉴的部分

| CCGS 特性 | 不借鉴原因 |
|-----------|-----------|
| 48+ agent | DewuGoJin 项目规模不需要这么多 agent，7 个已足够 |
| 游戏设计理论 (MDA/SDT/Bartle) | 与电商/视频发布无关 |
| 引擎专家 agent | 不适用 |
| 设计文档 8 节模板 | 游戏设计特有，DewuGoJin 有自己的文档规范 |
| AskUserQuestion 工具 | Claude Code CLI 环境下可能不可用 |

## 5. 实施优先级建议

| 优先级 | 建议 | 工作量 | 预期收益 |
|--------|------|--------|---------|
| P0 | 创建 `.claude/memory/` 三文件 | 小 | 高 -- 避免重复犯错 |
| P1 | 完善 active.md 生命周期 (hooks 增强) | 中 | 高 -- 跨会话恢复能力 |
| P1 | 细化三种协作协议模板 | 中 | 中 -- 提升 agent 交互质量 |
| P2 | 增强 SubagentStart 审计 | 小 | 低 -- 调试便利 |
| P2 | StatusLine 增强 | 小 | 低 -- 用户体验 |
| P3 | 协作自检脚本 | 中 | 低 -- 框架健康检查 |

## 6. 架构差异总结

```
CCGS 模式:                          DewuGoJin 模式:
┌─────────────────┐                 ┌─────────────────┐
│ 48+ agents      │                 │ 7 agents        │
│ 3 层层级        │                 │ 2 层层级        │
│ 游戏工作室隐喻   │                 │ 小团队隐喻      │
│ 通用框架        │                 │ 专用框架        │
│ bash hooks      │                 │ TypeScript hooks │
│ memory 系统     │                 │ (待引入)        │
│ 37+ skills      │                 │ 7 skills        │
└─────────────────┘                 └─────────────────┘

共同点:
- YAML frontmatter agent 定义
- settings.json hook 配置
- active.md 状态管理
- 垂直委派 + 水平协商
- Question -> Options -> Decision 流程
- 文件即内存理念
- 路径规则自动注入
```

DewuGoJin 的框架已经具备了 CCGS 的核心通信机制，且在 Handoff 协议、失败处理、同步门控等方面更加成熟。主要差距在 Memory 系统和 active.md 生命周期管理上，这两项投入产出比最高。
