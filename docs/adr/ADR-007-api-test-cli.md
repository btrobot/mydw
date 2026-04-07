# ADR-007: API 测试 CLI 技术选型

**状态**: Accepted

**日期**: 2026-04-02

**更新日期**: 2026-04-02

---

## 背景

用户需要开发一个 API 测试工具，用于前后端契约检查。参考了 ShopXO 的 `cli.mjs` 设计。

---

## 决策

### 推荐方案: TypeScript + Node.js CLI

**位置**: `frontend/scripts/cli/`

| 优势 | 说明 |
|-----|------|
| 类型复用 | 可使用 hey-api 生成的类型定义 |
| 一致性 | 与前端 API 客户端保持一致 |
| 独立运行 | 使用原生 fetch，不依赖构建 |

---

## 术语澄清

⚠️ **重要**: CLI 中的命令涉及的是**得物账号**和**连接管理**，不是系统用户认证。

```bash
# ❌ 旧术语（混淆）
dewu-cli login              # 系统登录？得物账号登录？
dewu-cli test-login         # 测试登录？

# ✅ 新术语（清晰）
dewu-cli connect            # 建立得物连接
dewu-cli test-connection    # 测试连接流程
```

---

## 命令设计 (更新版)

```bash
# ========== 系统端 (暂不实现) ==========
# dewu-cli auth login      # 系统用户登录（暂不考虑）
# dewu-cli auth whoami     # 当前系统用户（暂不考虑）

# ========== 得物账号端 (核心) ==========
dewu-cli health             # 后端健康检查

# 账号管理
dewu-cli account list       # 列出已注册的得物账号
dewu-cli account add       # 添加得物账号
dewu-cli account remove    # 删除得物账号
dewu-cli account status    # 检查得物连接状态

# 连接管理
dewu-cli connect <id>      # 建立连接（触发验证码流程）
dewu-cli connect --phone 13800138000  # 带手机号测试
dewu-cli disconnect <id>   # 断开连接
dewu-cli test-connection   # 测试完整连接流程
dewu-cli test-connection --mock  # Mock 模式（不发送真实短信）

# 通用 API
dewu-cli get <path>        # GET 请求
dewu-cli post <path> [json] # POST 请求
dewu-cli put <path> [json]  # PUT 请求
dewu-cli delete <path>     # DELETE 请求

# 批量测试
dewu-cli test accounts      # 测试得物账号 API
dewu-cli test tasks        # 测试任务 API
dewu-cli test materials    # 测试素材 API
dewu-cli test all          # 测试所有 API
```

---

## 目录结构

```
frontend/scripts/cli/
├── index.ts              # CLI 入口
├── commands/
│   ├── account.ts         # 得物账号管理命令
│   ├── connection.ts      # 连接管理命令
│   ├── http.ts           # 通用 HTTP 命令
│   └── test.ts           # 批量测试命令
├── suites/
│   ├── accounts.ts        # 得物账号测试套件
│   ├── tasks.ts          # 任务测试套件
│   ├── materials.ts      # 素材测试套件
│   ├── publish.ts        # 发布测试套件
│   ├── system.ts        # 系统测试套件
│   └── ai.ts             # AI 剪辑测试套件
├── utils/
│   ├── http.ts           # HTTP 封装
│   ├── output.ts         # 彩色输出
│   └── token.ts         # Token 缓存 (预留)
└── package.json
```

---

## 测试用例设计

### 得物账号域 (accounts)

| 测试 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 账号列表 | GET | `/api/accounts/` | 获取得物账号列表 |
| 注册账号 | POST | `/api/accounts/` | 注册新的得物账号 |
| 账号详情 | GET | `/api/accounts/{id}` | 获取账号详情 |
| 账号统计 | GET | `/api/accounts/stats` | 获取统计信息 |
| 更新账号 | PUT | `/api/accounts/{id}` | 更新账号信息 |
| 删除账号 | DELETE | `/api/accounts/{id}` | 删除账号 |
| 建立连接 | POST | `/api/accounts/connect/{id}` | 触发连接流程 |
| SSE 状态 | GET | `/api/accounts/connect/{id}/stream` | SSE 连接状态 |
| 断开连接 | POST | `/api/accounts/disconnect/{id}` | 断开连接 |

### 任务域 (tasks)

| 测试 | 方法 | 路径 |
|------|------|------|
| 任务列表 | GET | `/api/tasks/` |
| 创建任务 | POST | `/api/tasks/` |
| 任务详情 | GET | `/api/tasks/{id}` |
| 任务统计 | GET | `/api/tasks/stats` |
| 更新任务 | PUT | `/api/tasks/{id}` |
| 删除任务 | DELETE | `/api/tasks/{id}` |
| 发布任务 | POST | `/api/tasks/{id}/publish` |
| 打乱任务 | POST | `/api/tasks/shuffle` |

### 素材域 (materials)

| 测试 | 方法 | 路径 |
|------|------|------|
| 素材列表 | GET | `/api/materials/` |
| 素材统计 | GET | `/api/materials/stats` |
| 素材详情 | GET | `/api/materials/{id}` |
| 扫描素材 | POST | `/api/materials/scan` |
| 删除素材 | DELETE | `/api/materials/{id}` |
| 获取路径 | GET | `/api/materials/path/{type}` |
| 导入素材 | POST | `/api/materials/import` |

---

## 特殊功能

### SSE 连接状态流

得物连接流程使用 SSE 流式输出：

```typescript
// 命令: dewu-cli connect 1 --sse
async function testConnectionWithSSE() {
  const response = await fetch(`${BASE_URL}/api/accounts/connect/1/stream`, {
    headers: { 'Accept': 'text/event-stream' }
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    console.log(decoder.decode(value));
  }
}
```

### Mock 模式

开发阶段使用 Mock 模式，避免发送真实短信：

```bash
# Mock 模式
dewu-cli test-connection --mock

# 预期输出:
# [MOCK] 连接流程模拟
# [MOCK] 验证码已发送 (123456)
# [MOCK] 连接成功
```

---

## 实现计划

| 阶段 | 内容 | 优先级 |
|------|------|--------|
| Phase 1 | 基础设施 (HTTP 封装、输出工具) | 高 |
| Phase 2 | 核心命令 (account, connect, health) | 高 |
| Phase 3 | 测试套件 (accounts, tasks, materials) | 中 |
| Phase 4 | 特殊功能 (SSE, Mock) | 中 |

---

## 参考

- [ADR-008: 得物账号 vs 系统用户概念澄清](./ADR-008-dewu-account-terminology.md)
- [得物掘金工具架构文档](../architecture.md)
- [ShopXO CLI 参考实现](../reference/cli.mjs)
