# L5: 路径规则与守护机制

## 1. Rules 系统概述

CCGS 的 `.claude/rules/` 目录包含 11 个路径特定规则文件。这些规则在 agent 编辑匹配路径的文件时自动生效，充当代码质量的守护机制。

## 2. 规则文件格式

每个规则文件由 YAML frontmatter (指定路径匹配模式) + Markdown body (规则内容) 组成:

```yaml
---
paths:
  - "src/gameplay/**"
---

# Gameplay Code Rules

- ALL gameplay values MUST come from external config/data files, NEVER hardcoded
- Use delta time for ALL time-dependent calculations
- NO direct references to UI code — use events/signals
...
```

`paths` 字段使用 glob 模式匹配。当 agent 使用 Write/Edit 工具修改匹配路径的文件时，Claude Code 会自动将对应规则注入到 agent 的上下文中。

## 3. 规则清单

| 规则文件 | 路径模式 | 核心约束 |
|---------|---------|---------|
| `gameplay-code.md` | `src/gameplay/**` | 数据驱动值、delta time、无 UI 引用、接口隔离 |
| `engine-code.md` | `src/core/**` | 热路径零分配、线程安全、API 稳定性 |
| `ai-code.md` | `src/ai/**` | 性能预算、可调试性、数据驱动参数 |
| `network-code.md` | `src/networking/**` | 服务器权威、版本化消息、安全性 |
| `ui-code.md` | `src/ui/**` | 不拥有游戏状态、本地化就绪、无障碍 |
| `design-docs.md` | `design/gdd/**` | 必须包含 8 个必需节、公式格式、边界情况 |
| `narrative.md` | `design/narrative/**` | 世界观一致性、角色语音、正典级别 |
| `data-files.md` | `assets/data/**` | JSON 有效性、命名规范、schema 规则 |
| `test-standards.md` | `tests/**` | 测试命名、覆盖率要求、fixture 模式 |
| `prototype-code.md` | `prototypes/**` | 放宽标准、必须有 README、假设已文档化 |
| `shader-code.md` | `assets/shaders/**` | 命名规范、性能目标、跨平台规则 |

## 4. 规则如何影响 Agent 通信

### 4.1 自动注入机制

```
Agent 调用 Write("src/gameplay/combat/damage.gd", content)
    │
    ▼
Claude Code 检测路径匹配 src/gameplay/**
    │
    ▼
自动将 gameplay-code.md 规则注入 agent 上下文
    │
    ▼
Agent 在规则约束下生成/修改代码
    │
    ▼
如果违反规则，agent 应自行修正并解释
```

### 4.2 规则与协作协议的交互

Implementation Agent Protocol 中明确要求:

> "If rules/hooks flag issues, fix them and explain what was wrong"

这意味着规则不仅是被动约束，还是 agent 间的"隐式通信" -- 规则代表了 tech-director 和 lead-programmer 的架构决策，专家 agent 必须遵守。

### 4.3 设计文档规则的特殊作用

`design-docs.md` 规则要求所有设计文档必须包含 8 个节:

1. Overview (概述)
2. Player Fantasy (玩家幻想)
3. Detailed Rules (详细规则)
4. Formulas (公式)
5. Edge Cases (边界情况)
6. Dependencies (依赖)
7. Tuning Knobs (调优旋钮)
8. Acceptance Criteria (验收标准)

这确保了设计 agent 输出的文档格式统一，实现 agent 可以可靠地解析和引用。

## 5. Hooks 作为守护机制

除了 Rules，Hooks 也充当守护角色:

### 5.1 PreToolUse Hooks (工具调用前守护)

```
validate-ecommerce-commit.sh:
  触发: git commit 命令
  检查:
    - Schema 变更是否有对应 migration
    - DTO 变更是否更新了测试
    - 新 Controller 是否有 API 文档
    - 是否包含安全敏感文件
    - 是否有大文件
  结果: 警告信息 (不阻断)
```

### 5.2 PostToolUse Hooks (工具调用后守护)

```
validate-schema-change.sh:
  触发: Write/Edit 操作
  条件: 修改的文件是 schema.prisma
  动作: 提示执行 validate -> generate -> migrate 步骤
```

### 5.3 守护层级

```
第一层: Rules (路径规则)
  - 编辑时自动注入
  - agent 自行遵守
  - 违反时自行修正

第二层: PreToolUse Hooks (工具前检查)
  - 提交前验证
  - 可以阻断操作 (exit 2)
  - 输出警告信息

第三层: PostToolUse Hooks (工具后检查)
  - 操作后提示
  - 不能阻断 (已执行)
  - 提供后续步骤建议

第四层: agent-collaboration-check.sh (手动自检)
  - 验证框架完整性
  - 检查 agent 定义、上下文传递、文档、代码质量
  - 输出通过/失败/警告报告
```

## 6. agent-collaboration-check.sh 自检脚本

CCGS 提供了一个独立的协作有效性自检脚本，检查 8 个维度:

| 检查项 | 内容 |
|--------|------|
| 智能体定义完整性 | 12 个必需 agent 定义文件是否存在 |
| 上下文传递机制 | session-state 目录和 CLAUDE.md 配置 |
| 协作文档存在性 | PRD 文档、架构文档是否存在 |
| 代码产出质量 | Server/MP/Admin 代码是否存在、build 脚本 |
| 数据库 Schema 同步 | Prisma Schema 和 migration 是否同步 |
| API 文档同步 | API 文档数量、Swagger 注解 |
| 测试覆盖 | 测试文件是否存在 |
| 协作流程合规性 | Sprint/Milestone 规划、Co-Authored-By 提交 |

## 7. 权限控制作为守护

settings.json 的 permissions 配置也是守护机制的一部分:

```json
"deny": [
  "Bash(rm -rf *)",           // 防止误删
  "Bash(git push --force*)",  // 防止强制推送
  "Bash(git reset --hard*)",  // 防止硬重置
  "Bash(*>.env*)",            // 防止覆盖环境文件
  "Read(**/.env*)"            // 防止读取敏感配置
]
```

这确保了即使 agent 试图执行危险操作，也会被 Claude Code 框架层面阻断。

## 8. 对 DewuGoJin 的启示

1. **路径规则**: DewuGoJin 可为 `backend/api/**`、`frontend/src/pages/**` 等路径定义规则
2. **设计文档模板强制**: 通过规则确保所有设计文档格式统一
3. **多层守护**: Rules (编辑时) + PreToolUse (提交前) + PostToolUse (操作后) 三层防护
4. **自检脚本**: 定期运行协作有效性检查，确保框架健康
5. **权限最小化**: deny 列表应覆盖所有危险操作
