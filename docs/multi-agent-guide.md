# DewuGoJin 多 Agent 协作开发指南

> 版本: 1.0.0 | 创建日期: 2026-04-09
> 作者: Tech Lead

---

## 一、Agent 与 Skill 总览

### Agent 层级

```
用户（Product Owner）
  └── Tech Lead (opus, 40 turns)
        ├── Frontend Lead (sonnet, 25 turns)
        │     └── UI Designer (sonnet, 20 turns)
        ├── Backend Lead (sonnet, 25 turns)
        │     └── Automation Developer (sonnet, 20 turns)
        ├── QA Lead (sonnet, 20 turns)
        ├── Security Expert (sonnet, 20 turns)
        └── DevOps Engineer (sonnet, 20 turns)
```

### Skill 清单

| Skill | 命令 | 用途 | 主要使用者 |
|-------|------|------|-----------|
| task-breakdown | `/task-breakdown` | 功能分解为开发任务 | Tech Lead |
| sprint-plan | `/sprint-plan` | Sprint 规划和管理 | Tech Lead |
| architecture-review | `/architecture-review` | 架构决策审查 | Tech Lead |
| code-review | `/code-review` | 代码质量审查 | 各 Lead |
| security-scan | `/security-scan` | 安全漏洞扫描 | Security Expert |
| bug-report | `/bug-report` | Bug 记录和跟踪 | QA Lead |
| release-checklist | `/release-checklist` | 发布前质量验证 | QA Lead |
| ui-workflow | `/ui-workflow` | UI 设计→实现完整流程 | 主会话编排 |

---

## 二、场景指南

### 场景 1：实现新功能（端到端）

最常见的场景，从需求到交付的完整流程。

```
步骤 1: /task-breakdown <功能名>
  ↓ 输出任务清单
步骤 2: /architecture-review <设计文档>
  ↓ 架构审查通过
步骤 3: @backend-lead + @frontend-lead（并行委托开发）
  ↓ 代码实现
步骤 4: /code-review
  ↓ 代码审查通过
步骤 5: 测试验证
```

**实际示例**（本次任务管理重构）：

```bash
# 1. 需求分析和业务建模（Tech Lead 直接做）
用户: "分析任务管理需求"
→ Tech Lead 输出领域模型文档

# 2. 架构审查
/architecture-review 任务管理领域模型

# 3. 任务分解
/task-breakdown 任务管理领域模型实施
→ 输出 17 个任务，4 个 Phase

# 4. 并行委托开发
@backend-lead BE-TM-01 创建 publish_profiles 表
@backend-lead BE-TM-02 创建 composition_jobs 表  （并行）
@backend-lead BE-TM-03 创建 schedule_config 表   （并行）

# 5. 集成审查
/code-review 任务管理领域模型实施
```

---

### 场景 2：纯后端功能

只涉及 API、数据库、业务逻辑。

```
@backend-lead → /code-review → 测试
```

**示例**：添加一个新的 API 端点

```bash
# 直接委托
@backend-lead "实现 POST /api/tasks/{id}/submit-composition 端点"

# 审查
/code-review backend/api/task.py
```

---

### 场景 3：纯前端功能

只涉及页面、组件、交互。

```
方式 A（简单）: @frontend-lead → /code-review
方式 B（复杂）: /ui-workflow → 自动编排 ui-designer + frontend-lead
```

**示例 A**：修改状态标签颜色

```bash
@frontend-lead "更新 Task.tsx 的状态标签，7 状态枚举"
```

**示例 B**：设计并实现全新页面

```bash
/ui-workflow 任务详情页
# 自动流程：
#   1. ui-designer 输出页面规格
#   2. 用户确认设计
#   3. frontend-lead 实现
#   4. ui-designer 审查实现
```

---

### 场景 4：Bug 修复

```
/bug-report → @对应 Lead 修复 → /code-review
```

**示例**：

```bash
# 1. 记录 Bug
/bug-report "启动时 async_session 为 NoneType"

# 2. 修复（根据 Bug 涉及的域选择 agent）
@backend-lead "修复 main.py 中 async_session 在 init_db 之前被引用的问题"

# 3. 验证
/code-review backend/main.py
```

---

### 场景 5：安全审计

```
/security-scan → @security-expert 深入分析 → @backend-lead 修复
```

**示例**：

```bash
# 快速扫描
/security-scan quick backend/

# 完整扫描（含依赖）
/security-scan full

# 发现问题后委托修复
@backend-lead "修复 crypto.py 中的密钥派生问题"
```

---

### 场景 6：发布前检查

```
/release-checklist → /security-scan → 修复阻塞项 → 发布
```

**示例**：

```bash
/release-checklist v2.0.0
# 自动检查：
#   - 功能完整性
#   - 代码质量
#   - 测试覆盖率
#   - 安全扫描
#   - 文档更新
# 输出：通过/阻塞（含阻塞原因）
```

---

### 场景 7：Sprint 规划

```
/sprint-plan new → /task-breakdown（逐个功能）→ 分配
```

**示例**：

```bash
/sprint-plan new
# 输出 2 周 Sprint 计划：
#   - 目标
#   - 任务列表（含估时、负责人、依赖）
#   - 风险识别
```

---

### 场景 8：方案评估

需要对比多个技术方案时。

```
Tech Lead 分析 → /architecture-review → 用户决策
```

**示例**（本次扣子集成方案评估）：

```bash
# Tech Lead 调研
用户: "联网查找扣子 API 集成方式"
→ Tech Lead 输出技术方案文档

# 架构审查
/architecture-review 扣子集成方案
→ 输出：Approved / Approved with Changes / Rejected
```

---

### 场景 9：跨域协作

前后端同时修改，需要协调 API 契约。

```
Tech Lead 定义 API 契约
  → @backend-lead 实现 API（并行）
  → @frontend-lead 实现调用（并行）
  → /code-review 集成审查
```

**示例**：

```bash
# Tech Lead 定义契约
"Profile CRUD API：POST/GET/PUT/DELETE /api/profiles"

# 并行开发
@backend-lead "实现 Profile CRUD API"
@frontend-lead "实现 Profile 管理页面"  # 同时启动

# 集成审查
/code-review  # Full Stack 模式
```

---

### 场景 10：重构

大范围代码重构，需要谨慎推进。

```
/architecture-review（评估方案）
  → /task-breakdown（拆分步骤）
  → 逐步委托（每步 /code-review）
```

---

## 三、Agent 选择速查表

| 我要做什么 | 用哪个 Agent/Skill |
|-----------|-------------------|
| 分析需求、做技术决策 | Tech Lead（主会话直接做） |
| 拆分任务 | `/task-breakdown` |
| 评估架构方案 | `/architecture-review` |
| 写后端代码 | `@backend-lead` |
| 写前端代码 | `@frontend-lead` |
| 设计+实现 UI | `/ui-workflow` |
| 写浏览器自动化/FFmpeg | `@automation-developer` |
| 审查代码 | `/code-review` |
| 安全扫描 | `/security-scan` |
| 记录 Bug | `/bug-report` |
| 发布检查 | `/release-checklist` |
| Sprint 规划 | `/sprint-plan` |
| 构建/部署问题 | `@devops-engineer` |

---

## 四、并行策略

### 可并行的组合

| 组合 | 条件 |
|------|------|
| 多个 @backend-lead | 修改不同文件（如不同 migration） |
| @backend-lead + @frontend-lead | 后端 API 已定义，前端可先行 |
| @frontend-lead × 3 | 修改不同页面 |
| @backend-lead + @security-expert | 开发 + 安全审计同步 |

### 不能并行的组合

| 组合 | 原因 |
|------|------|
| 两个 agent 改同一文件 | 会产生冲突 |
| 有依赖关系的任务 | 后者需要前者的输出 |

### 并行启动语法

```bash
# 单条消息中启动多个 agent，它们会并行执行
@backend-lead "BE-TM-01 创建 publish_profiles 表"
@backend-lead "BE-TM-02 创建 composition_jobs 表"
@backend-lead "BE-TM-03 创建 schedule_config 表"
# 三个 agent 同时跑，等全部完成后继续
```

---

## 五、典型工作流模板

### 模板 A：小功能（< 1 天）

```
用户描述需求
  → @对应 Lead 直接实现
  → /code-review
  → 完成
```

### 模板 B：中等功能（1-3 天）

```
用户描述需求
  → /task-breakdown
  → 按依赖顺序委托 agent（尽量并行）
  → /code-review
  → 测试验证
  → 完成
```

### 模板 C：大功能（> 3 天）

```
用户描述需求
  → Tech Lead 分析 + 输出设计文档
  → /architecture-review
  → /task-breakdown
  → /sprint-plan（排期）
  → 分 Phase 执行：
      每个 Phase:
        → 并行委托 agent
        → /code-review
        → 测试验证
  → /release-checklist
  → 完成
```

---

## 六、注意事项

### Agent 使用规则

1. **主会话是唯一编排者** — agent 不能嵌套委托其他 agent
2. **Handoff 必须完整** — 委托时提供 Context、Constraints、Expected Output
3. **重试上限 2 次** — 同一 agent 同一 prompt 最多重试 2 次，之后换 agent 或主会话吸收
4. **跨域禁止** — backend-lead 不能改 frontend 代码，反之亦然

### Skill 使用规则

1. **Skill 是流程模板** — 定义了"做什么、怎么做、输出什么"
2. **Skill 可以触发 Agent** — 如 `/ui-workflow` 内部编排 ui-designer + frontend-lead
3. **Skill 输出更新会话状态** — 结果写入 `production/session-state/active.md`

### 常见错误

| 错误 | 正确做法 |
|------|---------|
| 让 agent 自己决定做什么 | 明确告诉 agent 要修改哪些文件、实现什么 |
| 一次委托太大的任务 | 拆成小任务，每个 agent 做一件事 |
| 并行修改同一文件 | 串行执行，或拆分到不同文件 |
| 跳过 /code-review | 每次开发完都应该审查 |
| 不提供上下文 | Handoff 中包含设计文档路径、现有代码位置 |

---

## 附录

### 参考文档

- [AGENTS 总入口](AGENTS.md) — 当前 OMX/Codex 协作约束与模式选择
- [Team 工作流](.codex/skills/team/SKILL.md) — 当前多 Agent 团队执行面
- [领域模型设计](docs/task-management-domain-model.md) — 最近的大功能实施案例
- [任务分解](docs/archive/examples/task-management-impl.md) — 任务分解示例
