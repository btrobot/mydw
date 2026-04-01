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
  └── Project Manager (PM)
        └── Tech Lead
              ├── Frontend Lead
              │     └── UI Developer
              ├── Backend Lead
              │     ├── API Developer
              │     └── Automation Developer
              ├── QA Lead
              │     └── Test Engineer
              └── DevOps Engineer
```

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
| **冲突升级** | 技术 → Tech Lead；产品/设计 → PM |
| **变更传播** | 跨域变更需 PM 协调各方确认 |
| **禁止跨域** | 除非获得授权，否则不能修改其他域的代码 |

### 冲突解决

```
冲突发生 → 水平协商 → 无法解决 → 升级到共同上级 → 文档化决策
```

---

## 可用 Agents

### 领导层

| Agent | 描述 |
|-------|------|
| `project-manager` | 任务分配、优先级、跨域协调 |
| `tech-lead` | 架构设计、API契约、代码审查 |

### 执行层

| Agent | 描述 |
|-------|------|
| `frontend-lead` | React/TypeScript/Electron 负责人 |
| `backend-lead` | FastAPI/Python 负责人 |
| `qa-lead` | 测试和质量负责人 |
| `devops-engineer` | CI/CD 和部署 |

### 专家层

| Agent | 描述 |
|-------|------|
| `ui-developer` | React 组件、UI 实现 |
| `api-developer` | FastAPI 端点、服务层 |
| `automation-developer` | Playwright/FFmpeg 自动化 |
| `test-engineer` | 测试用例、自动化测试 |
| `security-expert` | 安全审计、漏洞检测 |

---

## 可用 Skills

| Skill | 调用 | 描述 |
|-------|------|------|
| Sprint 规划 | `/sprint-plan` | 创建和管理 Sprint |
| 任务分解 | `/task-breakdown` | 分解功能为可执行任务 |
| 架构审查 | `/architecture-review` | 审查技术架构 |
| 代码审查 | `/code-review` | 审查代码质量和安全 |
| 安全扫描 | `/security-scan` | 扫描安全漏洞 |

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
│   └── session-state/           # 会话状态
└── .claude/                     # Agent 框架
    ├── agents/                  # Agent 定义
    ├── skills/                  # Skills 工作流
    ├── hooks/                   # 生命周期钩子
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

当前工作状态保存在 `production/session-state/active.md`。

每次任务开始/完成、决策做出时更新此文件。

---

## 相关文档

- [.claude/docs/coordination-rules.md](.claude/docs/coordination-rules.md) - 详细协作规则
- [.claude/rules/](.claude/rules/) - 代码规范
- [.claude/skills/](.claude/skills/) - 技能文档
