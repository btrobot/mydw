# 批量登录检测 / 状态同步 设计文档

**版本**: v2.0 (Architecture Reviewed)
**日期**: 2026-04-06
**状态**: Tech Lead 审查通过
**审查者**: Tech Lead (opus)

---

## 架构审查摘要

| 检查项 | 结论 | 说明 |
|--------|------|------|
| 正确性 | Approved with Changes | 去掉 HEALTH_CHECKING 状态，改用前端本地状态 |
| 简单性 | Approved with Changes | 信号量内嵌到 BrowserManager，不新建独立类 |
| 性能 | Approved | 串行队列 + 信号量控制并发 |
| 安全性 | Approved | 得物反爬风险需要串行间隔 |
| 可维护性 | Approved | 复用现有 health_check 逻辑 |

---

## 一、问题分析

### 1.1 "重新连接"按钮语义问题

当前 `Account.tsx` 第 375-377 行：

```typescript
const connectLabel =
  record.status === 'logging_in' ? '连接中' :
  record.status === 'active' || record.status === 'session_expired' ? '重新连接' :
  record.status === 'disabled' ? null : '连接'
```

问题：`active` 和 `session_expired` 共用"重新连接"文案，但语义完全不同：

| AccountStatus | 用户意图 | 实际应该做的事 |
|---------------|---------|--------------|
| `active` | "我想确认 session 还能用" | 调用 health_check API |
| `session_expired` | "我需要重新登录" | 打开 ConnectionModal 走登录流程 |
| `error` | "出了问题，我想修复" | 打开 ConnectionModal 走登录流程 |

核心洞察：`active` 状态下的"重新连接"实际上是**状态验证**，不是重新登录。把它和 `session_expired` 的"重新登录"混为一谈，会误导用户。

### 1.2 状态不同步场景

| 场景 | 前端显示 | 实际状态 | 后果 |
|------|---------|---------|------|
| 用户隔夜未操作 | active (绿色) | session 已过期 | 发布任务失败 |
| 得物平台强制下线 | active (绿色) | session 已失效 | 自动化操作全部失败 |
| 多设备登录挤掉 | active (绿色) | session 被替换 | 操作异常 |

这些场景的共同点：**前端状态是"快照"，不是"实时"**。批量健康检查的本质是用真实浏览器会话去校准这个快照。

### 1.3 需要解决的问题（优先级排序）

1. P0: 按钮文案语义修正 + 单账号验证连接
2. P1: 批量健康检查 API + 前端批量验证按钮
3. P2: 取消批量检测 + 自动定时检测

---

## 二、架构决策

### ADR-1: 不新增 HEALTH_CHECKING 状态

**Status**: Accepted

**Context**: v1 草案提议在 AccountStatus 枚举中新增 `HEALTH_CHECKING` 状态。这意味着：
- 后端 AccountStatus 枚举从 6 个变为 7 个
- 数据库 status 字段需要支持新值
- 状态机转换表需要新增 4 条规则
- 前端 StatusBadge 需要新增配置
- 所有按 status 过滤的查询都需要考虑新状态

**Decision**: 不修改 AccountStatus 枚举。健康检查的"进行中"状态用前端本地状态管理。

**Rationale**:
- 健康检查是一个**瞬态操作**（5-15 秒），不是一个**持久状态**
- 类比：你不会因为正在刷新网页就把浏览器状态改成"refreshing"
- `logging_in` 之所以是持久状态，是因为它需要用户交互（输入验证码），可能持续数分钟
- 健康检查是全自动的，不需要用户交互，不应该污染持久化状态机
- 如果检查过程中服务崩溃，账号状态不会卡在一个无法自动恢复的中间态

**前端实现方式**:
```typescript
// 用 React 本地状态追踪哪些账号正在检查
const [checkingIds, setCheckingIds] = useState<Set<number>>(new Set())
```

### ADR-2: 信号量内嵌到 BrowserManager

**Status**: Accepted

**Context**: v1 草案提议新建独立的 `BrowserSemaphore` 类。但当前 `BrowserManager` 已经有 `_lock` 做互斥，新建独立类会形成两套并发控制，容易出现竞态。

**Decision**: 在 `BrowserManager` 中新增 `_context_semaphore`，统一管控所有浏览器上下文的并发创建。

**Rationale**:
- 单一职责：浏览器资源管控归 BrowserManager
- 避免两套锁的死锁风险
- 现有 `create_context` 调用方无需感知信号量

### ADR-3: 批量检测使用串行队列 + 间隔

**Status**: Accepted

**Context**: 得物平台有反爬策略。短时间内多个浏览器实例同时访问 `creator.dewu.com` 可能触发风控。

**Decision**: 批量检测默认串行执行（concurrency=1），每次检测间隔 2 秒。可通过参数调整。

**Rationale**:
- 安全第一：得物平台的反爬策略不可预测，保守策略更安全
- 10 个账号串行检测约需 70-120 秒（每个 5-10 秒 + 2 秒间隔），可接受
- 用户可以通过参数提高并发数，但默认值应该是安全的
- 并发数上限设为 3，避免资源耗尽

---

## 三、API 设计

### 3.1 批量健康检查

```
POST /api/accounts/batch-health-check
```

**Request Body** (所有字段可选):

```json
{
  "account_ids": [1, 2, 3],
  "concurrency": 1,
  "interval_seconds": 2,
  "skip_inactive": true
}
```

| 字段 | 类型 | 默认值 | 约束 | 说明 |
|------|------|--------|------|------|
| `account_ids` | `List[int]` | null | - | 为空则检测所有非 inactive/disabled 账号 |
| `concurrency` | `int` | 1 | 1-3 | 并发数 |
| `interval_seconds` | `int` | 2 | 0-10 | 每次检测间隔秒数 |
| `skip_inactive` | `bool` | true | - | 跳过 inactive/disabled 状态的账号 |

**Response** (200 OK):

```json
{
  "total": 10,
  "checked": 8,
  "skipped": 2,
  "valid_count": 6,
  "expired_count": 2,
  "error_count": 0,
  "results": [
    {
      "account_id": 1,
      "account_name": "账号A",
      "previous_status": "active",
      "current_status": "active",
      "is_valid": true,
      "message": "Session 有效",
      "checked_at": "2026-04-06T12:00:00Z"
    },
    {
      "account_id": 2,
      "account_name": "账号B",
      "previous_status": "active",
      "current_status": "session_expired",
      "is_valid": false,
      "message": "Session 已过期",
      "checked_at": "2026-04-06T12:00:07Z"
    }
  ],
  "started_at": "2026-04-06T12:00:00Z",
  "completed_at": "2026-04-06T12:01:10Z"
}
```

**Error Responses**:

| 状态码 | 场景 | Body |
|--------|------|------|
| 409 Conflict | 已有批量检测在进行中 | `{"detail": "批量检测正在进行中"}` |
| 400 Bad Request | 无可检测的账号 | `{"detail": "没有可检测的账号"}` |

### 3.2 批量检测进度查询

```
GET /api/accounts/batch-health-check/status
```

**Response** (200 OK):

```json
{
  "in_progress": true,
  "progress": 5,
  "total": 10,
  "current_account_name": "账号E",
  "started_at": "2026-04-06T12:00:00Z"
}
```

前端轮询此端点显示进度。当 `in_progress` 为 false 时停止轮询。

### 3.3 取消批量检测 (P2)

```
DELETE /api/accounts/batch-health-check
```

**Response** (200 OK):

```json
{
  "cancelled": true,
  "checked_so_far": 5,
  "message": "批量检测已取消"
}
```

---

## 四、Pydantic Schema 定义

```python
# backend/schemas/__init__.py 新增

class BatchHealthCheckRequest(BaseModel):
    """批量健康检查请求"""
    account_ids: Optional[List[int]] = Field(
        None, description="指定账号ID列表，为空则检测所有"
    )
    concurrency: int = Field(
        default=1, ge=1, le=3,
        description="并发数（默认串行，最大3）"
    )
    interval_seconds: int = Field(
        default=2, ge=0, le=10,
        description="每次检测间隔秒数"
    )
    skip_inactive: bool = Field(
        default=True,
        description="跳过 inactive/disabled 状态的账号"
    )


class BatchHealthCheckResultItem(BaseModel):
    """单个账号检测结果"""
    account_id: int
    account_name: str
    previous_status: AccountStatus
    current_status: AccountStatus
    is_valid: bool
    message: str
    checked_at: datetime


class BatchHealthCheckResponse(BaseModel):
    """批量健康检查响应"""
    total: int
    checked: int
    skipped: int
    valid_count: int
    expired_count: int
    error_count: int
    results: List[BatchHealthCheckResultItem]
    started_at: datetime
    completed_at: datetime


class BatchHealthCheckStatusResponse(BaseModel):
    """批量检测进度"""
    in_progress: bool
    progress: int = 0
    total: int = 0
    current_account_name: Optional[str] = None
    started_at: Optional[datetime] = None
```

---

## 五、状态机变更

### 不变。

现有状态机完全不变。健康检查的状态转换已经在 `state-machine.md` 中定义：

```
active → health_check 成功 → active (更新 last_health_check, session_expires_at)
active → health_check 失败 → session_expired
```

批量检测只是对现有单账号 health_check 的批量调度，不引入新的状态转换。

---

## 六、前端 UX 设计

### 6.1 按钮文案修正

| AccountStatus | 当前文案 | 新文案 | 点击行为 |
|---------------|---------|--------|---------|
| `inactive` | 连接 | 连接 | 打开 ConnectionModal |
| `logging_in` | 连接中 | 连接中 | 禁用 |
| `active` | 重新连接 | 检查连接 | 调用 health_check API，不打开 Modal |
| `session_expired` | 重新连接 | 重新登录 | 打开 ConnectionModal |
| `error` | 重新连接 | 重新登录 | 打开 ConnectionModal |
| `disabled` | (隐藏) | (隐藏) | - |

关键变化：`active` 状态的按钮从"打开 ConnectionModal"变为"直接调用 health_check API"。这是语义上的根本修正。

### 6.2 单账号"检查连接"交互流程

```
用户点击"检查连接"
  → 按钮变为 "检查中..." (loading + disabled)
  → 调用 POST /{id}/health-check
  → 成功且 is_valid=true:
      → message.success("Session 有效")
      → 刷新账号列表
  → 成功且 is_valid=false:
      → message.warning("Session 已过期，请重新登录")
      → 账号状态自动变为 session_expired
      → 按钮文案变为"重新登录"
  → 失败:
      → message.error("检查失败，请稍后重试")
```

### 6.3 工具栏批量验证按钮 (P1)

```
┌──────────────────────────────────────────────────────────────────────┐
│ [+ 添加账号]  [搜索框...]  [标签筛选]          [批量检查连接]  │
└──────────────────────────────────────────────────────────────────────┘
```

位置：工具栏右侧，与"添加账号"同级。

**按钮状态**:

| 状态 | 样式 | 文案 |
|------|------|------|
| 默认 | 默认按钮 + SyncOutlined 图标 | 批量检查连接 |
| 检测中 | 禁用 + LoadingOutlined | 检查中 (5/10) |
| 完成 | 3 秒后恢复默认 | 批量检查连接 |

**点击行为**:
1. 直接开始检测（不弹确认框 -- 这是非破坏性操作）
2. 按钮进入 loading 状态，显示进度
3. 前端轮询 `GET /batch-health-check/status` 更新进度
4. 完成后 Toast 通知 + 刷新列表

### 6.4 批量检测结果展示

检测完成后，在表格上方显示结果 Banner（Alert 组件）：

```
[info] 批量检查完成：6 个有效，2 个已过期，0 个异常    [x 关闭]
```

- 类型：`Alert` with `type="info"` / `type="warning"`（有过期时）
- 可关闭
- 5 秒后自动消失

### 6.5 StatusBadge 无需修改

不新增 `health_checking` 状态，StatusBadge 组件保持不变。检查中的视觉反馈通过操作列按钮的 loading 状态体现。

---

## 七、并发控制

### 7.1 BrowserManager 改造

在现有 `BrowserManager` 中新增信号量：

```python
class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.contexts: Dict[int, any] = {}
        self._lock = asyncio.Lock()
        self._context_semaphore = asyncio.Semaphore(3)  # 最多 3 个并发上下文

    async def create_context(self, account_id: int, storage_state: Optional[str] = None):
        """为账号创建浏览器上下文（受信号量保护）"""
        await self._context_semaphore.acquire()
        try:
            await self.init()
            async with self._lock:
                # ... 现有逻辑不变
                pass
        except Exception:
            self._context_semaphore.release()
            raise

    async def close_context(self, account_id: int):
        """关闭账号的浏览器上下文"""
        async with self._lock:
            if account_id in self.contexts:
                await self.contexts[account_id].close()
                del self.contexts[account_id]
                self._context_semaphore.release()  # 释放信号量
```

### 7.2 批量检测调度器

```python
async def run_batch_health_check(
    db: AsyncSession,
    accounts: List[Account],
    concurrency: int = 1,
    interval_seconds: int = 2,
) -> List[BatchHealthCheckResultItem]:
    """
    批量健康检查调度器

    使用 asyncio.Semaphore 控制并发，
    每次检测之间插入间隔以规避反爬。
    """
    semaphore = asyncio.Semaphore(concurrency)
    results: List[BatchHealthCheckResultItem] = []

    async def check_one(account: Account) -> BatchHealthCheckResultItem:
        async with semaphore:
            result = await _do_single_health_check(db, account)
            if interval_seconds > 0:
                await asyncio.sleep(interval_seconds)
            return result

    tasks = [check_one(acc) for acc in accounts]
    for coro in asyncio.as_completed(tasks):
        result = await coro
        results.append(result)
        # 更新进度状态（供轮询端点使用）
        batch_status_store.progress += 1

    return results
```

### 7.3 全局批量检测状态

```python
class BatchCheckState:
    """批量检测全局状态（内存中，单例）"""
    def __init__(self):
        self.in_progress: bool = False
        self.progress: int = 0
        self.total: int = 0
        self.current_account_name: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self._cancel_event: Optional[asyncio.Event] = None

    def start(self, total: int) -> None:
        self.in_progress = True
        self.progress = 0
        self.total = total
        self.started_at = datetime.utcnow()
        self._cancel_event = asyncio.Event()

    def finish(self) -> None:
        self.in_progress = False
        self._cancel_event = None

    def cancel(self) -> None:
        if self._cancel_event:
            self._cancel_event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._cancel_event is not None and self._cancel_event.is_set()

batch_check_state = BatchCheckState()
```

### 7.4 配置项

在 `core/config.py` 的 `Settings` 中新增：

```python
# 批量健康检查
BATCH_HEALTH_CHECK_MAX_CONCURRENCY: int = 3
BATCH_HEALTH_CHECK_DEFAULT_INTERVAL: int = 2  # 秒
BATCH_HEALTH_CHECK_TIMEOUT: int = 30  # 单次检测超时（秒）
BATCH_HEALTH_CHECK_MAX_ACCOUNTS: int = 100
```

---

## 八、实现计划

### P0 -- 最小可用方案 (预计 2h)

| 任务 | 文件 | 说明 |
|------|------|------|
| 按钮文案修正 | `frontend/src/pages/Account.tsx` | active="检查连接", session_expired/error="重新登录" |
| active 状态点击行为修改 | `frontend/src/pages/Account.tsx` | active 状态直接调 health_check，不打开 Modal |
| 新增 useHealthCheck hook | `frontend/src/hooks/useAccount.ts` | 封装 health_check API 调用 |
| 按钮 loading 状态 | `frontend/src/pages/Account.tsx` | 检查中显示 loading |

P0 不涉及后端改动，完全复用现有 `POST /{id}/health-check` 端点。

### P1 -- 批量检测核心 (预计 8h)

| 任务 | 文件 | 说明 |
|------|------|------|
| Schema 定义 | `backend/schemas/__init__.py` | 新增 4 个 Schema |
| 批量检测 API | `backend/api/account.py` | POST /batch-health-check |
| 进度查询 API | `backend/api/account.py` | GET /batch-health-check/status |
| BrowserManager 信号量 | `backend/core/browser.py` | 新增 _context_semaphore |
| 批量检测状态管理 | `backend/api/account.py` | BatchCheckState 单例 |
| 配置项 | `backend/core/config.py` | 新增 4 个配置 |
| 前端批量按钮 | `frontend/src/pages/Account.tsx` | 工具栏新增按钮 |
| 前端 hooks | `frontend/src/hooks/useAccount.ts` | useBatchHealthCheck, useBatchCheckStatus |
| 结果 Banner | `frontend/src/pages/Account.tsx` | Alert 组件展示结果 |

### P2 -- 增强功能 (预计 5h)

| 任务 | 说明 |
|------|------|
| 取消批量检测 API | DELETE /batch-health-check |
| 前端取消按钮 | 检测中显示取消按钮 |
| 自动定时检测 | 后台定时任务，可配置间隔 |
| 启动时自动检测 | 应用启动后自动检测所有 active 账号 |

---

## 九、风险分析

### 9.1 得物反爬风险 (高)

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 短时间多次访问触发风控 | 中 | 账号被限制/封禁 | 默认串行 + 2 秒间隔 |
| IP 被临时封禁 | 低 | 所有账号检测失败 | 检测到连续失败时自动停止 |
| 浏览器指纹被识别 | 低 | 检测结果不准确 | 使用 Patchright 反检测 |

**关键缓解策略**：如果连续 3 个账号检测都失败（非 session 过期，而是网络/超时错误），自动停止批量检测并通知用户。

### 9.2 资源风险 (中)

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 浏览器上下文泄漏 | 中 | 内存持续增长 | try/finally 确保 close_context |
| 检测超时堆积 | 低 | 系统卡顿 | 单次 30 秒超时 + 信号量限制 |
| 与正常操作竞争资源 | 中 | 登录/预览变慢 | 信号量统一管控 |

### 9.3 用户体验风险 (低)

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 批量检测耗时长 | 高 | 用户等待焦虑 | 进度显示 + 可取消 |
| 检测期间状态闪烁 | 低 | 视觉干扰 | 检测完成后一次性刷新列表 |

---

## 十、向后兼容性

| 维度 | 影响 | 说明 |
|------|------|------|
| API | 无破坏性变更 | 新增端点，现有端点不变 |
| 数据库 | 无变更 | 不新增字段，不修改表结构 |
| 状态机 | 无变更 | 不新增状态枚举值 |
| 前端 | 仅文案变更 | 按钮文案和点击行为调整 |

---

## 十一、实现顺序建议

```
P0 (前端独立完成，不依赖后端改动)
  ├── 1. 修改按钮文案和点击行为
  ├── 2. 新增 useHealthCheck hook
  └── 3. 按钮 loading 状态

P1 (前后端协同)
  ├── 后端
  │   ├── 4. Schema 定义
  │   ├── 5. BrowserManager 信号量
  │   ├── 6. 批量检测 API + 状态管理
  │   └── 7. 配置项
  └── 前端
      ├── 8. 批量检测按钮 + hooks
      └── 9. 结果 Banner

P2 (独立迭代)
  ├── 10. 取消功能
  └── 11. 自动定时检测
```

P0 可以立即开始，不阻塞 P1 的后端开发。

---

## 十二、决策记录

| # | 决策 | 选项 | 选择 | 理由 |
|---|------|------|------|------|
| 1 | 是否新增 HEALTH_CHECKING 状态 | 新增 / 不新增 | 不新增 | 瞬态操作不应污染持久化状态机 |
| 2 | 信号量放在哪里 | 独立类 / BrowserManager 内 | BrowserManager 内 | 避免两套并发控制 |
| 3 | 默认并发数 | 1 / 3 / 5 | 1 (串行) | 得物反爬风险，安全优先 |
| 4 | 检测间隔 | 0 / 2 / 5 秒 | 2 秒 | 平衡速度和安全 |
| 5 | 批量检测模式 | 同步阻塞 / 后台任务 | 后台任务 + 轮询 | 避免 HTTP 超时 |
| 6 | 结果展示方式 | 仅刷新列表 / Banner 通知 | Banner 通知 | 用户可能没注意到状态变化 |
| 7 | 连续失败处理 | 继续 / 自动停止 | 连续 3 次非 session 错误则停止 | 防止触发风控 |
