# Claude Code 工作架构指南

> 面向：使用 Claude Code 在此项目工作的开发者  
> 更新：2026-04-25

这份文档补充 `docs/current/architecture.md`，专门解释**对 Claude Code 工作方式最关键的架构事实**——
哪些地方容易踩坑、哪些文件是权威来源、修改前必须读什么。

---

## 系统三层全景

```
Electron Shell (frontend/)
  ├── Main Process        electron/main.ts      — 窗口/托盘/backend 生命周期
  ├── Preload Bridge      electron/preload.ts   — 最小 IPC 暴露，不扩展
  └── React Renderer      src/                  — HashRouter，Ant Design 5，React Query

FastAPI Backend (backend/)          localhost:8000
  ├── api/                — 路由层（17 个文件，按域组织）
  ├── services/           — 业务逻辑层（27 个文件）
  ├── core/               — 基础设施（auth、browser、crypto、scheduler）
  ├── models/             — SQLAlchemy ORM（单文件 __init__.py）
  └── migrations/         — 自定义异步迁移（27 条）

Remote Control Plane (remote/)      独立进程
  ├── remote-backend      — Auth API（机器注册、设备信任）
  ├── remote-admin        — 管理面板
  └── remote-shared       — 契约库（TypeScript 类型）
```

---

## 前端：改代码前必须知道的

### API 客户端是生成物，不要手改

```
frontend/src/api/          ← 完全由 OpenAPI schema 生成
  ├── client/              ← HTTP 客户端配置
  ├── sdk.gen.ts           ← 所有 API 方法（1,511 行，生成）
  └── types.gen.ts         ← 所有 Pydantic 模型的 TS 类型（9,251 行，生成）
```

**规则：修改后端路由或 schema 后，必须重新生成：**
```bash
cd frontend
npm run generated:regenerate   # 导出 OpenAPI + 重新生成 SDK
npm run generated:check        # CI 验证门（会在测试中报错）
```

### 路由结构

入口文件：`frontend/src/App.tsx`

```
/ → BusinessEntryRedirect → getCreativeFlowDefaultPath()
                              ↓
/creative/workbench           ← 默认落地页（不是 /tasks，不是 /accounts）

/login                        ← 未认证入口
/status/revoked               ← 设备注销后
/status/grace                 ← 授权宽限模式（只读）
/status/device-mismatch       ← 设备不匹配
```

### 状态管理

- **服务器状态**：React Query（`@tanstack/react-query`），hooks 封装在 `src/hooks/`
- **本地 UI 状态**：Zustand（`src/stores/`），使用极少
- **原则**：不要绕过 hooks 直接调用 `sdk.gen.ts`，保持缓存失效逻辑集中

### 大文件预警

| 文件 | 行数 | 注意事项 |
|------|------|---------|
| `features/creative/pages/CreativeDetail.tsx` | 2,228 | 主动重构中；修改前先读现有模式 |
| `pages/TaskList.tsx` | 996 | 过滤/分页/批量操作混合 |
| `pages/Account.tsx` | 725 | 多账号管理 + 连接流 |

---

## 后端：改代码前必须知道的

### 路由层规范

所有路由均使用统一的依赖注入模式：

```python
# 需要 auth 的路由
router = APIRouter(dependencies=ACTIVE_ROUTE_DEPENDENCIES)

# 宽限模式（只读）路由
router = APIRouter(dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)

# 依赖来源
from core.auth_dependencies import ACTIVE_ROUTE_DEPENDENCIES, GRACE_READONLY_ROUTE_DEPENDENCIES
```

**不要绕过这个模式**——auth 状态传播依赖这里，直接写 `Depends(get_db)` 会跳过 auth 校验。

### 服务层

核心服务文件及其职责：

| 文件 | 大小 | 职责 |
|------|------|------|
| `creative_service.py` | 3,254 行 | workbench/detail/版本/投稿/review — **改之前先读** |
| `publish_planner_service.py` | — | 发布计划调度 |
| `composition_service.py` | — | FFmpeg 本地视频合成 |
| `task_assembler.py` | — | 任务组装 + material 绑定 |
| `scheduler.py` | — | APScheduler 集成 |

### 数据库迁移

**自定义模式**（非 Alembic），每个迁移是独立 Python 文件：

```python
# 标准模板
async def run_migration(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        # 1. 检查列/表是否已存在（幂等）
        result = await conn.execute(text("PRAGMA table_info(table_name)"))
        columns = [row[1] for row in result]
        if "new_column" not in columns:
            await conn.execute(text("ALTER TABLE ... ADD COLUMN ..."))
        await conn.commit()
```

新增迁移：
1. 在 `backend/migrations/` 创建 `028_xxx.py`
2. 在 `backend/core/database.py`（或迁移运行器）中注册
3. **每个迁移必须幂等**（CHECK before ALTER）

### 加密与 Secret

- Cookie/Session 加密：`core/secret_store.py`（AES-256-GCM）
- 设备身份：`core/device_identity.py`
- Remote auth 客户端：`core/remote_auth_client.py`
- **不要在代码中硬编码任何 key/token**，统一走 secret_store

---

## Remote 控制平面

**大多数功能开发不需要改 remote/**。仅在以下情况才涉及：
- 修改设备注册/信任逻辑
- 修改授权状态判断（ACTIVE / GRACE / REVOKED）
- 修改管理员后台功能

Remote 有独立的 TypeScript 契约库（`remote/remote-shared/`），修改后需同步更新。

---

## 测试：如何验证改动

### 后端测试

```bash
# 运行全部测试
pytest backend/tests

# 运行单个文件
pytest backend/tests/test_creative_api.py -v

# 运行单个用例
pytest backend/tests/test_creative_api.py::test_workbench_list -v -s

# 关键治理测试（改路由/schema 必跑）
pytest backend/tests/test_openapi_contract_parity.py
pytest backend/tests/test_generated_artifact_governance.py
```

### 前端 E2E 测试

```bash
cd frontend
npm run test:e2e                                         # 全部
npm run test:e2e -- e2e/creative-workbench/             # 单个目录
npm run test:e2e -- --headed                             # 有界面调试
```

### 修改后的检查清单

- [ ] `npm run typecheck`（前端 TS 编译）
- [ ] `pytest backend/tests/test_openapi_contract_parity.py`（API 契约一致性）
- [ ] `npm run generated:check`（生成物是否最新）
- [ ] 相关域的 E2E 测试通过

---

## 文档权威层级

| 优先级 | 文件 | 用途 |
|--------|------|------|
| 1 | `docs/current/architecture.md` | 架构权威 |
| 1 | `docs/current/runtime-truth.md` | 运行时事实（API、数据模型） |
| 2 | `docs/guides/dev-guide.md` | 环境搭建 |
| 2 | `backend/CLAUDE.md` / `frontend/CLAUDE.md` | 分层约定 |
| 3 | `discss/` | 设计讨论、PRD、工作日志（背景参考） |
| Stale | `docs/archive/` | 历史文档，不作为当前参考 |
