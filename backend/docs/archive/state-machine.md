# 状态机设计文档

**版本**: v1.0  
**日期**: 2026-04-06  
**状态**: 已审批

---

## 概述

系统中有三个相互关联的状态系统：

| 状态系统 | 持久化 | 作用域 |
|---------|--------|--------|
| **AccountStatus** | 数据库 | 账号生命周期，驱动前端 UI |
| **ConnectionStatus** | 内存（SSE） | 连接流程临时状态 |
| **PreviewStatus** | 内存 | 预览浏览器生命周期 |

---

## 一、AccountStatus 状态机

### 1.1 状态定义

| 枚举值 | 字符串 | 含义 |
|--------|--------|------|
| `ACTIVE` | `"active"` | Session 有效，可执行任务 |
| `INACTIVE` | `"inactive"` | 未连接或已断开 |
| `LOGGING_IN` | `"logging_in"` | 连接流程进行中 |
| `SESSION_EXPIRED` | `"session_expired"` | Session 已过期，需重新连接 |
| `ERROR` | `"error"` | 不可恢复错误（如账号被封） |
| `DISABLED` | `"disabled"` | 用户手动禁用 |

### 1.2 状态转换表

| From | To | 触发条件 | 触发端点 |
|------|----|---------|---------|
| `inactive` | `logging_in` | 用户发起连接 | `POST /connect/{id}/send-code` |
| `logging_in` | `active` | 验证码验证成功 | `POST /connect/{id}/verify` |
| `logging_in` | `inactive` | 验证码验证失败 | `POST /connect/{id}/verify` |
| `logging_in` | `error` | 浏览器异常 | `POST /connect/{id}/verify` |
| `active` | `session_expired` | 健康检查失败 | `POST /{id}/health-check` |
| `active` | `inactive` | 用户断开连接 | `POST /disconnect/{id}` |
| `session_expired` | `logging_in` | 用户重新连接 | `POST /connect/{id}/send-code` |
| `session_expired` | `active` | 重新连接成功 | `POST /connect/{id}/verify` |
| `any` | `disabled` | 用户手动禁用 | `PUT /{id}` (status=disabled) |
| `disabled` | `inactive` | 用户重新启用 | `PUT /{id}` (status=inactive) |
| `any` | `error` | 不可恢复异常 | 各端点异常路径 |

### 1.3 状态转换图

```
                    创建账号
                       │
                       ▼
                  [INACTIVE] ◄──────────────── disconnect
                    │    ▲                          ▲
         send-code  │    │ verify 失败              │
                    ▼    │                          │
               [LOGGING_IN]                         │
                    │                               │
         verify 成功│                               │
                    ▼                               │
                 [ACTIVE] ──── health check 失败 ──► [SESSION_EXPIRED]
                    │                                      │
                    │ disconnect                           │ send-code
                    └──────────────────────────────────────┘

         任意状态 ──── 手动禁用 ──► [DISABLED] ──── 重新启用 ──► [INACTIVE]
         任意状态 ──── 不可恢复异常 ──► [ERROR]
```

### 1.4 前端 UI 渲染规则

| AccountStatus | 连接按钮 | 预览按钮 | 删除按钮 | StatusBadge |
|---------------|---------|---------|---------|-------------|
| `inactive` | **连接**（可用） | 隐藏 | 可用 | 灰色 · 未登录 |
| `logging_in` | **连接中**（禁用） | 隐藏 | 禁用 | 蓝色旋转 · 登录中 |
| `active` | **重新连接**（可用） | **预览**（可用） | 可用 | 绿色 · 已登录 |
| `session_expired` | **重新连接**（可用） | **预览**（可用） | 可用 | 橙色 · 会话过期 |
| `error` | **重新连接**（可用） | 隐藏 | 可用 | 红色 · 异常 |
| `disabled` | 隐藏 | 隐藏 | 可用 | 灰色 · 已禁用 |

---

## 二、ConnectionStatus 状态机

### 2.1 状态定义

| 枚举值 | 字符串 | 含义 | progress |
|--------|--------|------|---------|
| `IDLE` | `"idle"` | 无进行中的连接 | — |
| `WAITING_PHONE` | `"waiting_phone"` | 浏览器已打开，等待手机号 | 10 |
| `CODE_SENT` | `"code_sent"` | 短信已发送，等待用户输入 | 40 |
| `WAITING_VERIFY` | `"waiting_verify"` | 已收到验证码，等待验证 | 50 |
| `VERIFYING` | `"verifying"` | 验证码已提交，检测结果 | 80 |
| `SUCCESS` | `"success"` | 登录成功 | 100 |
| `ERROR` | `"error"` | 连接失败 | 0 |

### 2.2 状态转换图

```
POST /send-code
      │
      ▼
[WAITING_PHONE] ──► [CODE_SENT] ──► POST /verify ──► [WAITING_VERIFY]
                                                              │
                                                              ▼
                                                        [VERIFYING]
                                                        /          \
                                                       ▼            ▼
                                                  [SUCCESS]      [ERROR]
                                                  (终态)         (终态)

任意阶段异常 ──► [ERROR]（终态）
```

### 2.3 与 AccountStatus 的交互

| ConnectionStatus 变化 | AccountStatus 变化 | 触发时机 |
|----------------------|-------------------|---------|
| → `WAITING_PHONE` | `inactive` → `logging_in` | send-code 请求处理开始 |
| → `SUCCESS` | `logging_in` → `active` | verify 成功，session 保存后 |
| → `ERROR`（verify 阶段） | `logging_in` → `inactive` | verify 失败 |
| → `ERROR`（浏览器异常） | `logging_in` → `error` | 浏览器操作异常 |

### 2.4 SSE 事件协议

| 事件名 | 触发时机 | data 字段 |
|--------|---------|----------|
| `status_update` | 每次状态变化 | `{status, message, progress, timestamp}` |
| `done` | 进入终态（success/error） | `{message, final_status}` |
| `error` | SSE 内部异常 | `{message}` |
| `: heartbeat` | 每 30 秒无变化 | 注释行，无 data |

**重要**：`done` 事件的 `final_status` 值为 `"success"` 或 `"error"`（字符串），与 `ConnectionStatus` 枚举一致。

---

## 三、PreviewStatus 状态机

### 3.1 状态定义

| 状态 | 含义 |
|------|------|
| `closed` | 无预览窗口 |
| `opening` | 正在启动浏览器 |
| `open` | 预览窗口已打开 |
| `closing` | 正在关闭 |

> 当前实现用 `_current_account_id is not None` 表示 open，`None` 表示 closed。

### 3.2 状态转换图

```
[closed] ──── POST /{id}/preview ──► [opening] ──► [open]
                                                      │
                                    ┌─────────────────┤
                                    │                 │
                              用户关闭窗口        POST /preview/close
                                    │                 │
                                    ▼                 ▼
                                 [closed]          [closing] ──► [closed]
```

### 3.3 关闭检测机制

| 关闭方式 | 检测事件 | 可靠性 |
|---------|---------|--------|
| 调用 `POST /preview/close` | 主动调用 | 100% |
| 用户关闭浏览器窗口 | `page.on("close")` | 高（推荐） |
| 浏览器进程退出 | `browser.on("disconnected")` | 中（有延迟） |
| 账号被删除 | `DELETE /{id}` 端点主动清理 | 100% |

### 3.4 与 AccountStatus 的交互

| 操作 | AccountStatus 变化 |
|------|-------------------|
| 打开预览（无 session 保存） | 无变化 |
| 关闭预览（save_session=true） | 更新 `storage_state`，`last_login` |
| 删除账号时预览仍开着 | 强制关闭预览，AccountStatus 随账号删除 |

---

## 四、三者交互矩阵

| 触发事件 | AccountStatus | ConnectionStatus | PreviewStatus |
|---------|--------------|-----------------|--------------|
| 创建账号 | → `inactive` | 无变化 | 无变化 |
| send-code 成功 | → `logging_in` | → `code_sent` | 无变化 |
| verify 成功 | → `active` | → `success` → 清除 | 无变化 |
| verify 失败 | → `inactive` | → `error` → 清除 | 无变化 |
| 打开预览 | 无变化 | 无变化 | → `open` |
| 关闭预览（不保存） | 无变化 | 无变化 | → `closed` |
| 关闭预览（保存 session） | 更新 storage_state | 无变化 | → `closed` |
| 健康检查失败 | → `session_expired` | 无变化 | 无变化 |
| 断开连接 | → `inactive` | 无变化 | 无变化 |
| 删除账号 | 账号删除 | 清除（如有） | 强制关闭（如有） |

---

## 五、关键场景走查

### 场景 1：新建账号 → 连接 → 登录成功

```
1. 创建账号: AccountStatus = inactive
2. 点击"连接": ConnectionModal 打开，SSE 建立
3. 输入手机号，点击"发送验证码":
   - POST /send-code → AccountStatus: inactive → logging_in
   - SSE: WAITING_PHONE(10%) → CODE_SENT(40%)
4. 输入验证码，点击"连接":
   - POST /verify → AccountStatus: logging_in → active
   - SSE: WAITING_VERIFY(50%) → VERIFYING(80%) → SUCCESS(100%)
   - SSE done 事件: final_status="success"
5. 前端: invalidateQueries(['accounts']) → 刷新列表
6. 前端: 连接按钮变为"重新连接"，预览按钮出现
```

### 场景 2：登录成功 → 打开预览 → 关闭预览

```
1. AccountStatus = active
2. 点击"预览": POST /{id}/preview
   - PreviewStatus: closed → open
   - 独立 headed 浏览器启动，加载 storage_state
3. 用户在浏览器中操作
4. 点击"关闭预览":
   - 弹出确认: "保存并关闭" / "直接关闭"
   - POST /{id}/preview/close { save_session: true/false }
   - PreviewStatus: open → closed
   - 如 save_session=true: AccountStatus.storage_state 更新
5. 前端刷新账号列表
```

### 场景 3：删除已预览的账号

```
1. AccountStatus = active, PreviewStatus = open (account_id=5)
2. 用户点击删除账号 5:
   - DELETE /accounts/5
   - 后端检查: preview_manager.current_account_id == 5
   - 强制关闭预览: preview_manager.close(save_session=False)
   - PreviewStatus: open → closed
   - 删除账号记录
3. 前端: 账号列表刷新，预览状态轮询返回 is_open=false
```

### 场景 4：session 过期 → 重新连接

```
1. AccountStatus = active
2. 健康检查: POST /{id}/health-check
   - 浏览器导航到 creator.dewu.com
   - URL 包含 /login → session 过期
   - AccountStatus: active → session_expired
3. 前端: StatusBadge 变为橙色"会话过期"，"重新连接"按钮可用
4. 用户点击"重新连接": 走场景 1 的连接流程
```

### 场景 5：用户关闭预览窗口（非通过 UI）

```
1. PreviewStatus = open (account_id=5)
2. 用户直接关闭 Chromium 窗口
3. Playwright page.on("close") 事件触发
   - _on_page_closed() 调度异步清理
   - PreviewStatus: open → closed
4. 前端轮询 /preview/status: is_open=false
5. 预览按钮恢复可用
```

---

## 六、已知问题与修复计划

| 问题 | 根因 | 修复方案 | 优先级 |
|------|------|---------|--------|
| 登录后"连接"按钮不变 | 按钮无条件渲染，不检查 status | Account.tsx 按 status 条件渲染按钮 | P0 |
| 关闭预览后按钮仍灰色 | delete_account 不清理 preview_manager | delete_account 主动清理 preview_manager | P0 |
| 手动关闭窗口检测不可靠 | `browser.disconnected` 事件有延迟 | 改用 `page.on("close")` 监听 | P1 |
| Playwright 进程泄漏 | `_on_browser_closed` 是同步回调，无法 await stop() | 改为调度异步清理任务 | P1 |
| preview_status 返回过期状态 | 不验证浏览器是否真的活着 | 端点增加 `browser.is_connected()` 检查 | P1 |
