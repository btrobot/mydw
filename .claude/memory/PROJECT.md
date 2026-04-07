# DewuGoJin - 项目核心记忆

## 项目概述

- **名称**: DewuGoJin (得物掘金工具)
- **类型**: 得物平台自动化视频发布系统
- **架构**: Electron 桌面应用 + FastAPI 后端 (前后端分离)
- **目标用户**: 得物平台内容创作者，批量管理多账号视频发布

## 技术栈

| 层 | 技术 |
|----|------|
| 桌面框架 | Electron 28 + React 18 + TypeScript 5 + Vite 5 |
| UI 组件库 | Ant Design 5 |
| 前端状态 | React Query (TanStack Query 5) — 服务端状态缓存 |
| 后端框架 | Python FastAPI + SQLAlchemy 2 (async) + aiosqlite |
| 浏览器自动化 | Patchright (Playwright fork, 反检测) |
| 视频处理 | FFmpeg (subprocess) |
| 加密 | AES-256-GCM + PBKDF2HMAC |
| 日志 | Loguru |

## 规范位置

- 编码规范: `.claude/rules/`
- API 设计规范: `.claude/rules/api-design-rules.md`
- 安全规范: `.claude/rules/security-rules.md`
- 系统架构: `docs/system-architecture.md`
- API 参考: `docs/api-reference.md`
- 数据模型: `docs/data-model.md`
- 开发指南: `docs/dev-guide.md`

## 常用引用快捷方式

- [[arch]] → docs/system-architecture.md
- [[api]] → docs/api-reference.md
- [[data]] → docs/data-model.md
- [[dev]] → docs/dev-guide.md
- [[py-rules]] → .claude/rules/python-coding-rules.md
- [[ts-rules]] → .claude/rules/typescript-coding-rules.md
- [[security]] → .claude/rules/security-rules.md
- [[coord]] → .claude/rules/coordination-rules.md

## 绝对禁止

1. **禁止在代码或日志中明文输出 cookie / storage_state / 手机号**
   - 教训: 敏感凭证泄露风险极高
   - 正确: 使用 `utils/crypto.py` 的 AES-256-GCM 加解密，日志中使用 `mask_phone()`

2. **禁止在 Python 中使用 print() 输出日志**
   - 正确: 使用 `loguru` 的 `logger.info()` / `logger.error()` 等
   - 原因: print 不带时间戳、不分级别、不写文件

3. **禁止在 TypeScript 中使用 `any` 类型**
   - 正确: 使用具体类型或 `unknown` + 类型守卫
   - 原因: 破坏类型安全，隐藏潜在 bug

4. **禁止跨域直接修改代码**
   - 前端 agent 不能改 backend/ 下的文件，反之亦然
   - 必须通过 coordination-rules.md 的授权流程

5. **禁止在 Electron renderer 中直接访问 Node.js API**
   - 正确: 通过 preload 的 `contextBridge` 暴露最小化 API
   - 原因: contextIsolation=true 是安全边界

6. **禁止硬编码加密密钥或在代码中存储 secrets**
   - 正确: 环境变量 `COOKIE_ENCRYPT_KEY`，`.env` 文件
   - 原因: 代码会进 git，secrets 不能

## 必须执行

1. **Pydantic 验证所有 API 输入**
   - 所有请求体必须有对应的 Pydantic Schema
   - 响应模型必须排除敏感字段 (cookie, phone_encrypted, storage_state)

2. **加密存储所有敏感数据**
   - cookie → AES-256-GCM 加密后存 DB
   - storage_state → AES-256-GCM 加密后存 DB
   - phone → AES-256-GCM 加密后存 DB，展示时 mask_phone()

3. **更新会话状态文件**
   - 位置: `production/session-state/active.md`
   - 时机: 设计批准、架构决策、里程碑、测试结果、任务开始/完成/阻塞

4. **Python 公共函数必须有类型注解**
   - 参数和返回值都要标注
   - 使用 Pydantic v2 模型做数据验证

5. **前端使用 React Query 管理服务端状态**
   - 不要用 useState 缓存 API 数据
   - 使用 useQuery / useMutation + 自动失效

## 标杆参照

### 后端标杆
- **账号管理**: `backend/api/account.py` + `backend/services/` — 完整的 CRUD + 连接流程
- **加密实现**: `backend/utils/crypto.py` — AES-256-GCM 标准实现

### 前端标杆
- **页面结构**: `frontend/src/pages/Account/` — 标准页面组件模式
- **API 调用**: `frontend/src/hooks/` — React Query 封装模式

### 自动化标杆
- **浏览器管理**: `backend/core/browser.py` — BrowserManager + PreviewBrowserManager
- **得物客户端**: `backend/core/dewu_client.py` — Patchright 自动化操作

## 业务域

| 域 | 核心实体 | 关键挑战 |
|----|---------|---------|
| 账号管理 | Account, 连接状态, Session | 会话过期检测、反检测、多账号并发 |
| 任务管理 | Task, 发布队列 | 状态机 (pending→running→success/failed)、优先级调度 |
| 素材管理 | Video, Copywriting, Cover, Audio | 文件系统同步、FFmpeg 处理、大文件上传 |
| 发布引擎 | PublishConfig, PublishLog, Scheduler | 时间窗口控制、频率限制、错误重试 |
| AI 剪辑 | FFmpeg pipeline | 高光检测、智能剪辑、音频混合 |
| 商品管理 | Product | 商品-素材关联、得物链接解析 |

## 当前活跃任务

查看 `production/session-state/active.md` 获取最新状态。
