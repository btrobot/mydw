# 得物掘金工具 (DewuGoJin Tool)

得物平台自动化视频发布系统 — 多 Agent 协作开发框架

## 技术栈

| 领域 | 技术 |
|------|------|
| **前端** | Electron 28 + React 18 + TypeScript 5 + Vite 5 + Ant Design 5 + Zustand |
| **后端** | Python FastAPI + SQLAlchemy + aiosqlite |
| **自动化** | Playwright (浏览器自动化) |
| **媒体** | FFmpeg (视频处理) |
| **安全** | AES-256-GCM (Cookie加密), PBKDF2HMAC (密钥派生) |

---

## 平台要求

### Windows (当前开发环境)

本项目使用 **PowerShell** 作为默认 Shell。

- Hooks 使用 `.ps1` 脚本
- 脚本头部声明: `#Requires -Version 5.1`
- 颜色使用 `$host.UI.RawUI.ForegroundColor`（原生颜色）
- 路径使用反斜杠或 `Join-Path`

### 不可用命令

Windows + PowerShell 环境下，以下 Unix 命令不可用：

| ❌ 禁止 | ✅ 替代 |
|---------|--------|
| `grep` / `rg` | `Grep` 工具 |
| `cat` | `Read` 工具 |
| `sed` / `awk` | `Edit` 工具 |
| `find` | `Glob` 工具 |
| `bash -c "..."` | 直接写 PowerShell 命令 |

### 编码问题

PowerShell 控制台编码可能为 GB2312/GBK，涉及中文时输出可能乱码。

**必须遵守**：
1. 搜索含中文的代码：使用 `Grep` 工具（支持 UTF-8）
2. 读取含中文的文件：使用 `Read` 工具
3. 禁止在 PowerShell 命令中内联中文字符
4. 禁止尝试用 `chcp 65001` 修复编码

### Unix/macOS (可选)

如需在 Unix/macOS 上运行：

- 使用 `.sh` 脚本版本
- Hooks 需要执行权限: `chmod +x hooks/*.sh`

---

## 组织架构

```
用户 (Product Owner)
  └── Tech Lead (opus) ← 战略层
        ├── Frontend Lead ← 前端实现
        ├── Backend Lead ← 后端实现
        │     └── Automation Developer
        ├── QA Lead ← 测试质量
        └── Security Expert ← 安全审计
              └── DevOps Engineer
```

### 角色定位

| 角色 | 类型 | 模型 | 职责 |
|------|------|------|------|
| `tech-lead` | 战略 | **opus** | 架构设计、技术决策、API 契约 |
| `frontend-lead` | 战术 | sonnet | 组件架构、状态管理、API 集成 |
| `backend-lead` | 战术 | sonnet | API 实现、服务层、数据库 |
| `automation-developer` | 专家 | sonnet | Playwright、FFmpeg 自动化 |
| `qa-lead` | 战术 | sonnet | 测试策略、缺陷管理、发布质量 |
| `security-expert` | 专家 | sonnet | 安全审计、漏洞检测 |
| `devops-engineer` | 专家 | haiku | CI/CD、部署、配置 |

---

## 协作协议

### 核心规则

**每个任务遵循**: Question → Options → Decision → Draft → Approval

1. **Question**: 理解需求，问清楚模糊点
2. **Options**: 提出 2-3 个方案，分析利弊
3. **Decision**: 用户选择方案
4. **Draft**: Agent 编写代码草案
5. **Approval**: "我可以写入这个文件吗？" → 用户确认

### 协作规则

| 规则 | 说明 |
|------|------|
| **垂直委托** | 复杂决策不能跳过层级，必须层层传达 |
| **水平协商** | 同级 Agent 只能协商，不能做绑定决定 |
| **冲突升级** | 技术问题 → Tech Lead；安全问题 → Security Expert |
| **变更传播** | 跨域变更需相关 Lead 协调确认 |
| **禁止跨域** | 除非获得授权，否则不能修改其他域的代码 |

### 冲突解决

```
冲突发生 → 水平协商 → 无法解决 → 升级到 Tech Lead → 文档化决策
```

### 主会话职责边界

主会话（Session）与 Agent 是不同的角色，遵循**委托优先**原则：

| 职责 | 主会话 | Agent |
|------|--------|-------|
| **任务复杂度** | 简单明确的一次性操作 | 复杂探索、多步骤、需要深度研究 |
| **工具调用** | 快速 Read/Edit/Glob | Agent 工具启动子进程 |
| **执行模式** | "挽起袖子自己干" | "派遣专项负责人" |

**判断标准**：

1. **直接执行**（主会话做）
   - 单次文件读写/编辑
   - 简单搜索和定位
   - 明确知道答案的问题
   - 工具调用 ≤ 3 次能完成

2. **委托执行**（启动 Agent）
   - 需要多轮搜索、交叉验证
   - 涉及多个文件/模块
   - 需要并行处理独立任务
   - 任务边界清晰，可描述为"请帮我完成 X"

3. **Agent 出问题时**
   - 分析根因：是指令不清？Agent 能力不足？环境问题？
   - 调整策略：修正指令、换 Agent、或主会话接手
   - 解决后记录经验，完善协作流程

**核心理念**：主会话是**协调者**，不是**执行者**。除非是举手之劳，否则优先委托给合适的 Agent。

---

## 可用 Agents

### 战略层 (opus)

| Agent | 描述 |
|-------|------|
| `tech-lead` | 架构设计、技术决策、API 契约、安全评审 |

### 战术层 (sonnet)

| Agent | 描述 |
|-------|------|
| `frontend-lead` | React/TypeScript/Electron 组件、状态管理、API 集成 |
| `backend-lead` | FastAPI API、服务层、数据库、安全实现 |
| `automation-developer` | Playwright 浏览器自动化、FFmpeg 视频处理 |
| `qa-lead` | 测试策略、测试用例、缺陷管理、发布质量 |
| `security-expert` | 安全审计、漏洞检测、加密实现 |

### 专家层 (haiku)

| Agent | 描述 |
|-------|------|
| `devops-engineer` | CI/CD 配置、部署脚本、环境配置 |

---

## 可用 Skills

| Skill | 调用 | 描述 | 主要使用者 |
|-------|------|------|-----------|
| 代码审查 | `/code-review` | 审查代码质量和规范 | tech-lead, frontend-lead, backend-lead |
| 安全扫描 | `/security-scan` | 扫描安全漏洞 | security-expert |
| 架构审查 | `/architecture-review` | 审查技术架构 | tech-lead |
| Sprint 规划 | `/sprint-plan` | 创建和管理 Sprint | - |
| 任务分解 | `/task-breakdown` | 分解功能为可执行任务 | - |
| Bug 报告 | `/bug-report` | 记录和跟踪缺陷 | qa-lead |
| 发布检查 | `/release-checklist` | 发布前的质量验证 | qa-lead |

---

## 项目结构

```
dewugojin/
├── frontend/                      # Electron + React 前端
│   └── src/
│       ├── pages/               # 页面组件
│       ├── components/          # 公共组件
│       ├── services/            # API 服务
│       └── stores/             # Zustand 状态
├── backend/                      # Python FastAPI 后端
│   ├── api/                     # API 路由
│   ├── models/                  # 数据模型
│   ├── schemas/                 # Pydantic schemas
│   ├── services/                # 业务服务
│   └── utils/                   # 工具函数
├── production/                   # 生产管理
│   ├── session-state/          # 会话状态
│   │   └── active.md.template  # 状态模板
│   └── session-logs/           # 会话归档
│       ├── session-log.md       # 会话历史
│       └── agent-audit.log      # Agent 调用审计
└── .claude/                     # Agent 框架
    ├── agents/                  # Agent 定义
    ├── skills/                  # Skills 工作流
    ├── hooks/                   # 生命周期钩子
    │   ├── session-start.ts    # 会话开始
    │   ├── session-end.ts      # 会话结束
    │   └── log-agent.ts        # Agent 审计
    └── rules/                   # 代码规范
```

---

## 开发规范

### 前端
- TypeScript 严格模式，禁止 `any`
- 组件使用函数式组件 + Hooks
- 状态管理使用 Zustand

### 后端
- 使用 Pydantic 进行数据验证
- 所有 API 端点必须定义 Response Model
- 敏感数据使用 `utils/crypto.py` 加密

---

## 状态管理

### 核心原则

**文件即内存，对话即临时。** 对话是临时的，会被压缩或丢失；文件是持久化的，跨会话和崩溃都能保留。

### 会话状态文件

`production/session-state/active.md` 是会话的"活检查点"，包含：

| 章节 | 内容 |
|------|------|
| **STATUS** | 当前 Epic/Feature/Task（会被 Hook 自动解析） |
| **Active Task** | 当前组件、阶段、状态 |
| **Progress** | 任务进度清单 |
| **Key Decisions** | 重要决策记录 |
| **Files Being Worked On** | 正在修改的文件 |
| **Open Questions** | 待解决的问题和选项 |
| **Blocker Notes** | 当前阻塞 |
| **Agent Invocations** | Agent 调用记录 |
| **Session Log** | 会话操作历史 |

### 更新时机

在以下情况后更新 `active.md`：

1. 设计文档章节批准并写入文件
2. 架构决策做出
3. 实现里程碑达到
4. 测试结果获取
5. 任务开始/完成/阻塞

### 自动机制

| Hook | 功能 |
|------|------|
| `session-start.ts` | 检测并恢复上次的会话状态 |
| `session-end.ts` | 自动归档状态到 `session-logs/session-log.md` |
| `log-agent.ts` | 审计所有 Agent 调用 |

### 主动压缩

- **~60-70% 上下文使用**：主动压缩，不要等到极限
- **自然压缩点**：章节完成后、提交后、任务完成后
- **压缩后恢复**：读取 `active.md` 恢复上下文

### 子 Agent 使用

| 场景 | 方式 |
|------|------|
| 跨多个文件调查、探索不熟悉的代码、消耗 >5k tokens 的研究 | 使用 Agent 工具 |
| 精确知道要检查哪 1-2 个文件 | 直接使用 Read/Grep 工具 |

子 Agent 不继承对话历史，需在 prompt 中提供完整上下文。

---

## 相关文档

- [.claude/docs/coordination-rules.md](.claude/docs/coordination-rules.md) - 详细协作规则
- [.claude/rules/](.claude/rules/) - 代码规范
- [.claude/skills/](.claude/skills/) - 技能文档
