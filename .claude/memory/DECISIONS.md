# 关键决策记录（快速查阅）

## ADR-001: 前后端通信方式

**状态**: 已接受
**关键结论**: 前端通过 HTTP REST + SSE 与 FastAPI 后端通信，不使用 Electron IPC 传递业务数据
**理由**:
- 前后端完全解耦，后端可独立开发调试
- SSE 用于长连接场景（账号连接状态推送）
- Electron IPC 仅用于窗口控制和系统级操作

**实施**:
```
Renderer → HTTP/SSE → FastAPI (业务数据)
Renderer → IPC → Main Process (窗口控制、文件对话框)
```

---

## ADR-002: 浏览器自动化选型 Patchright

**状态**: 已接受
**关键结论**: 使用 Patchright (Playwright fork) 而非原版 Playwright
**理由**:
- 得物平台有自动化检测机制
- Patchright 内置反检测能力，API 与 Playwright 兼容
- 降低账号被封风险

**注意事项**:
- 文档和代码中统一使用 "Patchright" 术语，不混用 "Playwright"
- 浏览器管理分两个 Manager: BrowserManager (headless 自动化) + PreviewBrowserManager (headed 预览)

---

## ADR-003: 敏感数据加密方案

**状态**: 已接受
**关键结论**: AES-256-GCM 加密 + PBKDF2HMAC 密钥派生
**理由**:
- GCM 模式提供认证加密，防篡改
- PBKDF2HMAC 从环境变量密钥派生实际加密密钥
- 每次加密生成随机 nonce，相同明文产生不同密文

**加密范围**:
| 字段 | 加密 | 脱敏展示 |
|------|------|---------|
| cookie | AES-256-GCM | 不展示 |
| storage_state | AES-256-GCM | 不展示 |
| phone | AES-256-GCM | mask_phone() → 138****8000 |

**实施**: `backend/utils/crypto.py`

---

## ADR-004: 前端状态管理选型

**状态**: 已接受
**关键结论**: React Query (TanStack Query) 管理服务端状态，不使用 Zustand/Redux 做 API 缓存
**理由**:
- 本项目 90% 状态来自服务端 (账号列表、任务列表、素材列表)
- React Query 自带缓存、失效、重试、乐观更新
- 减少手动状态同步代码

**注意**: CLAUDE.md 中提到 Zustand，但实际实现已迁移到 React Query。少量纯客户端状态（如 UI 偏好）可用 useState 或 Zustand。

---

## ADR-005: 数据库选型 SQLite

**状态**: 已接受
**关键结论**: 使用 SQLite (aiosqlite) 作为本地数据库
**理由**:
- 桌面应用，单用户，无需 PostgreSQL/MySQL
- 零配置，数据文件随应用分发
- aiosqlite 支持 async，与 FastAPI 异步模型匹配

**限制**:
- 不支持真正的并发写入（WAL 模式缓解）
- 迁移脚本必须幂等 (`backend/migrations/`)

---

## 其他关键决策

### 发布调度策略

- 时间窗口控制: start_hour ~ end_hour 之间才发布
- 频率限制: interval_minutes 间隔 + max_per_account_per_day 每日上限
- 优先级调度: priority 高的任务优先执行
- 随机化: shuffle 选项打乱发布顺序，降低平台检测风险

### API 响应模型安全

- 所有 AccountResponse 必须排除: cookie, phone_encrypted, storage_state
- 使用 Pydantic `response_model` 参数自动过滤
- 禁止在任何 API 响应中返回加密原文

### 素材文件管理

- 素材文件存储在本地文件系统，DB 只存路径
- 删除素材时同时删除文件和 DB 记录
- 上传时校验文件类型和大小限制

---

## 决策模板

新增决策时:
1. 在本文件添加 ADR 条目
2. 编号递增 (ADR-00N)
3. 包含: 状态、关键结论、理由、实施代码示例
4. 更新 `production/session-state/active.md` 决策日志
