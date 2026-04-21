# API 测试 CLI 工具 - 任务分解

> 版本: 0.1.0
> 日期: 2026-04-02
> 状态: Ready for Development

---

## 1. 功能概述

### 1.1 目标

开发一个 CLI 工具，用于：
- 后端开发完成后自测 API
- 前端开发前测试后端连通性
- 前后端契约检查机制

### 1.2 技术选型

| 项目 | 选择 |
|------|------|
| 语言 | TypeScript |
| 运行时 | Node.js 18+ |
| 位置 | `frontend/scripts/cli/` |
| HTTP | 原生 fetch |
| 构建 | tsx 或 tsup |

### 1.3 命令设计

```bash
# 健康检查
dewu-cli health             # 后端健康检查

# 得物账号管理
dewu-cli account list       # 列出账号
dewu-cli account add        # 添加账号
dewu-cli account status     # 连接状态

# 连接管理
dewu-cli connect <id>       # 建立连接
dewu-cli disconnect <id>    # 断开连接
dewu-cli test-connection    # 测试连接（Mock）

# 通用 API
dewu-cli get <path>        # GET 请求
dewu-cli post <path> [json] # POST 请求

# 批量测试
dewu-cli test accounts      # 测试账号 API
dewu-cli test tasks        # 测试任务 API
dewu-cli test all          # 测试所有 API
```

---

## 2. 任务分解

### 2.1 基础设施

#### CLI-INF-01: 项目初始化

**描述**: 创建 CLI 项目结构、配置文件

**验收标准**:
- [ ] 创建 `frontend/scripts/cli/` 目录结构
- [ ] 创建 `package.json` 配置
- [ ] 配置 TypeScript (`tsconfig.json`)
- [ ] 配置构建脚本 (`tsx` 或 `tsup`)
- [ ] 配置 ESLint/Prettier
- [ ] 配置 `.gitignore`

**估计**: 0.5d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: -
**测试需求**: 无

---

#### CLI-INF-02: HTTP 封装

**描述**: 实现 HTTP 请求封装，支持 GET/POST/PUT/DELETE

**验收标准**:
- [ ] 实现 `http.ts` 工具
- [ ] 支持基础认证头
- [ ] 支持 JSON 请求/响应
- [ ] 支持查询参数
- [ ] 错误处理和超时
- [ ] 单元测试

**估计**: 0.5d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: CLI-INF-01
**测试需求**:
- [ ] 单元测试

---

#### CLI-INF-03: 彩色输出工具

**描述**: 实现彩色控制台输出工具（参考 ShopXO cli.mjs）

**验收标准**:
- [ ] 实现 `output.ts` 工具
- [ ] 支持绿色（成功）、红色（失败）、黄色（警告）、青色（信息）
- [ ] 实现 `ok()` / `fail()` / `info()` / `warn()` 快捷函数
- [ ] 实现 `printResult()` 格式化输出
- [ ] 支持 JSON 折叠显示

**估计**: 0.5d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: CLI-INF-01
**测试需求**: 无

---

#### CLI-INF-04: 配置管理

**描述**: 实现配置管理，支持环境变量和配置文件

**验收标准**:
- [ ] 实现 `config.ts` 工具
- [ ] 支持 `BASE_URL` 环境变量（默认 `http://localhost:8000`）
- [ ] 支持 `CLI_TOKEN_FILE` 自定义 token 文件位置
- [ ] 支持 `.dewurc.json` 配置文件（可选）

**估计**: 0.5d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: CLI-INF-01
**测试需求**: 无

---

### 2.2 核心命令

#### CLI-CMD-01: CLI 入口和帮助

**描述**: 实现 CLI 主入口、参数解析和帮助命令

**验收标准**:
- [ ] 实现 `index.ts` 主入口
- [ ] 实现命令参数解析（使用 `commander` 或原生 `process.argv`）
- [ ] 实现 `--help` 帮助命令
- [ ] 实现 `--version` 版本命令
- [ ] 实现未知命令提示

**估计**: 0.5d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: CLI-INF-01, CLI-INF-03
**测试需求**: 无

---

#### CLI-CMD-02: 健康检查命令

**描述**: 实现 `health` 命令

**验收标准**:
- [ ] 实现 `health` 命令
- [ ] 调用 `GET /health`
- [ ] 显示健康状态
- [ ] 连接失败时显示错误

**估计**: 0.25d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: CLI-INF-02
**测试需求**: 无

---

#### CLI-CMD-03: 得物账号管理命令

**描述**: 实现得物账号管理相关命令

**验收标准**:
- [ ] `account list` - 列出得物账号
- [ ] `account add <account_id> <name>` - 添加账号
- [ ] `account status <id>` - 查看连接状态
- [ ] `account remove <id>` - 删除账号

**估计**: 1d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: CLI-INF-02, CLI-CMD-01
**测试需求**: 无

---

#### CLI-CMD-04: 连接管理命令

**描述**: 实现得物连接管理命令

**验收标准**:
- [ ] `connect <id>` - 建立连接（触发验证码流程）
- [ ] `connect --phone <phone>` - 带手机号建立连接
- [ ] `disconnect <id>` - 断开连接
- [ ] 支持 SSE 流式输出（可选 `--sse` 参数）

**估计**: 1.5d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: CLI-INF-02, CLI-CMD-03
**测试需求**: 无

---

#### CLI-CMD-05: 通用 API 命令

**描述**: 实现通用 HTTP 命令

**验收标准**:
- [ ] `get <path>` - GET 请求
- [ ] `get <path>?key=value` - 带查询参数
- [ ] `post <path> [json]` - POST 请求
- [ ] `put <path> [json]` - PUT 请求
- [ ] `delete <path>` - DELETE 请求
- [ ] 格式化输出响应

**估计**: 0.5d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: CLI-INF-02, CLI-CMD-01
**测试需求**: 无

---

### 2.3 测试套件

#### CLI-SUIT-01: 得物账号测试套件

**描述**: 实现得物账号 API 测试套件

**验收标准**:
- [ ] 创建 `suites/accounts.ts`
- [ ] 测试用例：
  - [ ] GET `/api/accounts/` - 账号列表
  - [ ] POST `/api/accounts/` - 注册账号
  - [ ] GET `/api/accounts/{id}` - 账号详情
  - [ ] GET `/api/accounts/stats` - 统计信息
  - [ ] PUT `/api/accounts/{id}` - 更新账号
  - [ ] DELETE `/api/accounts/{id}` - 删除账号
  - [ ] GET `/api/accounts/connect/{id}/status` - 连接状态
- [ ] 测试结果统计（通过/失败）

**估计**: 1d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: CLI-CMD-05
**测试需求**: 无

---

#### CLI-SUIT-02: 任务测试套件

**描述**: 实现任务 API 测试套件

**验收标准**:
- [ ] 创建 `suites/tasks.ts`
- [ ] 测试用例：
  - [ ] GET `/api/tasks/` - 任务列表
  - [ ] POST `/api/tasks/` - 创建任务
  - [ ] GET `/api/tasks/{id}` - 任务详情
  - [ ] GET `/api/tasks/stats` - 统计信息
  - [ ] PUT `/api/tasks/{id}` - 更新任务
  - [ ] DELETE `/api/tasks/{id}` - 删除任务
  - [ ] POST `/api/tasks/shuffle` - 打乱任务

**估计**: 1d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: CLI-SUIT-01
**测试需求**: 无

---

#### CLI-SUIT-03: 素材测试套件

**描述**: 实现素材 API 测试套件

**验收标准**:
- [ ] 创建 `suites/materials.ts`
- [ ] 测试用例：
  - [ ] GET `/api/materials/` - 素材列表
  - [ ] GET `/api/materials/stats` - 统计信息
  - [ ] GET `/api/materials/{id}` - 素材详情
  - [ ] GET `/api/materials/path/{type}` - 获取路径

**估计**: 0.5d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: CLI-SUIT-02
**测试需求**: 无

---

#### CLI-SUIT-04: 系统和 AI 测试套件

**描述**: 实现系统和 AI API 测试套件

**验收标准**:
- [ ] 创建 `suites/system.ts`
  - [ ] GET `/api/system/stats` - 系统统计
  - [ ] GET `/api/system/config` - 系统配置
- [ ] 创建 `suites/ai.ts`
  - [ ] GET `/api/ai/video-info` - 视频信息（需要测试视频）
  - [ ] GET `/api/ai/detect-highlights` - 高光检测（需要测试视频）

**估计**: 0.5d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: CLI-SUIT-03
**测试需求**: 无

---

#### CLI-CMD-06: 批量测试命令

**描述**: 实现批量测试命令

**验收标准**:
- [ ] `test accounts` - 测试账号 API
- [ ] `test tasks` - 测试任务 API
- [ ] `test materials` - 测试素材 API
- [ ] `test system` - 测试系统 API
- [ ] `test ai` - 测试 AI API
- [ ] `test all` - 测试所有 API
- [ ] 测试结果汇总（总计通过/失败）
- [ ] 彩色输出通过/失败

**估计**: 0.5d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: CLI-SUIT-01, CLI-SUIT-02, CLI-SUIT-03, CLI-SUIT-04
**测试需求**: 无

---

### 2.4 特殊功能

#### CLI-SPEC-01: Mock 模式

**描述**: 实现连接测试的 Mock 模式

**验收标准**:
- [ ] `test-connection --mock` 命令
- [ ] 模拟完整连接流程（不发送真实短信）
- [ ] 返回 Mock 验证码 `123456`
- [ ] 显示 `[MOCK]` 前缀区分
- [ ] 记录 Mock 测试到日志

**估计**: 0.5d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: CLI-CMD-04
**测试需求**: 无

---

#### CLI-SPEC-02: SSE 流式输出

**描述**: 实现 SSE 连接状态的流式输出

**验收标准**:
- [ ] `connect --sse` 命令
- [ ] 支持 SSE 流式接收
- [ ] 实时显示状态更新
- [ ] 状态格式化输出
- [ ] 支持中断（Ctrl+C）

**估计**: 0.5d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: CLI-CMD-04
**测试需求**: 无

---

#### CLI-SPEC-03: Shell 自动补全

**描述**: 实现 Shell 自动补全支持

**验收标准**:
- [ ] 支持 bash 自动补全
- [ ] 支持 zsh 自动补全
- [ ] 支持 PowerShell 自动补全
- [ ] `dewu-cli completion bash > /etc/bash_completion.d/dewu-cli`

**估计**: 0.5d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: CLI-CMD-06
**测试需求**: 无

---

### 2.5 文档和发布

#### CLI-DOC-01: 使用文档

**描述**: 编写使用文档

**验收标准**:
- [ ] `README.md` - 快速开始
- [ ] `docs/usage.md` - 详细使用指南
- [ ] 命令帮助信息
- [ ] 示例输出

**估计**: 0.5d
**负责人**: Frontend Lead
**类型**: frontend
**依赖**: CLI-SPEC-03
**测试需求**: 无

---

## 3. 任务汇总

### 任务列表

| ID | 任务 | 负责人 | 估计 | 依赖 | 类型 |
|----|------|--------|------|------|------|
| CLI-INF-01 | 项目初始化 | Frontend Lead | 0.5d | - | FE |
| CLI-INF-02 | HTTP 封装 | Frontend Lead | 0.5d | CLI-INF-01 | FE |
| CLI-INF-03 | 彩色输出工具 | Frontend Lead | 0.5d | CLI-INF-01 | FE |
| CLI-INF-04 | 配置管理 | Frontend Lead | 0.5d | CLI-INF-01 | FE |
| CLI-CMD-01 | CLI 入口和帮助 | Frontend Lead | 0.5d | CLI-INF-01, CLI-INF-03 | FE |
| CLI-CMD-02 | 健康检查命令 | Frontend Lead | 0.25d | CLI-INF-02 | FE |
| CLI-CMD-03 | 账号管理命令 | Frontend Lead | 1d | CLI-INF-02, CLI-CMD-01 | FE |
| CLI-CMD-04 | 连接管理命令 | Frontend Lead | 1.5d | CLI-INF-02, CLI-CMD-03 | FE |
| CLI-CMD-05 | 通用 API 命令 | Frontend Lead | 0.5d | CLI-INF-02, CLI-CMD-01 | FE |
| CLI-SUIT-01 | 账号测试套件 | Frontend Lead | 1d | CLI-CMD-05 | FE |
| CLI-SUIT-02 | 任务测试套件 | Frontend Lead | 1d | CLI-SUIT-01 | FE |
| CLI-SUIT-03 | 素材测试套件 | Frontend Lead | 0.5d | CLI-SUIT-02 | FE |
| CLI-SUIT-04 | 系统和 AI 测试套件 | Frontend Lead | 0.5d | CLI-SUIT-03 | FE |
| CLI-CMD-06 | 批量测试命令 | Frontend Lead | 0.5d | CLI-SUIT-04 | FE |
| CLI-SPEC-01 | Mock 模式 | Frontend Lead | 0.5d | CLI-CMD-04 | FE |
| CLI-SPEC-02 | SSE 流式输出 | Frontend Lead | 0.5d | CLI-CMD-04 | FE |
| CLI-SPEC-03 | Shell 自动补全 | Frontend Lead | 0.5d | CLI-CMD-06 | FE |
| CLI-DOC-01 | 使用文档 | Frontend Lead | 0.5d | CLI-SPEC-03 | FE |

### 时间估算

| 阶段 | 任务 | 估计 |
|------|------|------|
| 基础设施 | CLI-INF-01 ~ CLI-INF-04 | 2d |
| 核心命令 | CLI-CMD-01 ~ CLI-CMD-05 | 3.75d |
| 测试套件 | CLI-SUIT-01 ~ CLI-SUIT-04 | 3d |
| 批量测试 | CLI-CMD-06 | 0.5d |
| 特殊功能 | CLI-SPEC-01 ~ CLI-SPEC-03 | 1.5d |
| 文档 | CLI-DOC-01 | 0.5d |
| **总计** | | **10.75d** |
| **缓冲 (+20%)** | | **~13d** |

---

## 4. 目录结构

```
frontend/scripts/cli/
├── src/
│   ├── index.ts              # CLI 入口
│   ├── commands/
│   │   ├── health.ts         # 健康检查命令
│   │   ├── account.ts        # 账号管理命令
│   │   ├── connection.ts     # 连接管理命令
│   │   ├── http.ts          # 通用 HTTP 命令
│   │   └── test.ts          # 批量测试命令
│   ├── suites/
│   │   ├── index.ts         # 测试套件入口
│   │   ├── accounts.ts      # 账号测试套件
│   │   ├── tasks.ts         # 任务测试套件
│   │   ├── materials.ts     # 素材测试套件
│   │   ├── system.ts        # 系统测试套件
│   │   └── ai.ts            # AI 测试套件
│   ├── utils/
│   │   ├── http.ts          # HTTP 封装
│   │   ├── output.ts        # 彩色输出
│   │   ├── config.ts        # 配置管理
│   │   └── types.ts         # 类型定义
│   └── specials/
│       ├── mock.ts          # Mock 模式
│       └── sse.ts           # SSE 流式输出
├── package.json
├── tsconfig.json
├── README.md
└── docs/
    └── usage.md
```

---

## 5. 快速开始

```bash
# 安装依赖
cd frontend/scripts/cli
npm install

# 链接到全局
npm link

# 测试安装
dewu-cli --version

# 健康检查
dewu-cli health

# 列出得物账号
dewu-cli account list

# 测试账号 API
dewu-cli test accounts
```

---

## 6. 参考

- [ADR-007: API 测试 CLI 技术选型](../../adr/ADR-007-api-test-cli.md)
- [ADR-008: 得物账号 vs 系统用户概念澄清](../../adr/ADR-008-dewu-account-terminology.md)
- [得物掘金工具架构文档](../../architecture.md)
- [ShopXO CLI 参考实现](../reference/cli.mjs)
