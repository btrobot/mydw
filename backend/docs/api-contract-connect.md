# API Contract: 得物账号连接功能

**版本**: v2.0
**作者**: Backend Lead
**日期**: 2026-04-06
**状态**: 待审批

---

## 概述

得物账号连接功能采用两阶段手机验证码登录流程：

1. **发送验证码阶段** (`send-code`): 后端打开浏览器，导航至登录页，输入手机号并触发平台发送短信
2. **验证登录阶段** (`verify`): 后端将用户提供的验证码输入登录表单，完成登录并持久化 session

SSE 流端点贯穿整个流程，提供实时进度推送。

### 端点总览

| 方法 | 路径 | 功能 |
|------|------|------|
| `POST` | `/api/accounts/connect/{account_id}/send-code` | 第一阶段：发送短信验证码 |
| `POST` | `/api/accounts/connect/{account_id}/verify` | 第二阶段：验证码登录 |
| `GET` | `/api/accounts/connect/{account_id}/stream` | SSE 实时状态推送（保持不变） |

---

## 一、端点定义

### 1.1 POST /api/accounts/connect/{account_id}/send-code

**功能**: 触发后端在浏览器中打开得物登录页，输入手机号并点击发送验证码按钮。后端保持浏览器实例以供 verify 步骤使用。

#### Path Parameters

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `account_id` | `integer` | 是 | 账号数据库主键 ID（非得物平台 account_id） |

#### Request Body

Content-Type: `application/json`

```json
{
  "phone": "13800138000"
}
```

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `phone` | `string` | 是 | 长度精确为 11 位，`^1\d{10}$` | 绑定得物账号的手机号 |

**Pydantic Schema** (新增):
```python
class SendCodeRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11, description="手机号")
```

#### 成功响应 — 202 Accepted

后端已接受请求，开始异步执行浏览器操作。短信发送为异步过程，实际发送状态通过 SSE 推送。

```json
{
  "success": true,
  "message": "验证码发送中，请通过 SSE 监听状态",
  "status": "code_sent"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `boolean` | 始终为 `true`（请求已接受，非验证码已到达） |
| `message` | `string` | 人类可读消息 |
| `status` | `string` | 当前 ConnectionStatus 枚举值，此处为 `"code_sent"` |

**HTTP Status Codes**:

| 状态码 | 场景 |
|--------|------|
| `202 Accepted` | 请求已接受，后端异步处理中 |
| `400 Bad Request` | 手机号格式不正确 |
| `404 Not Found` | 账号不存在 |
| `409 Conflict` | 该账号已有进行中的连接会话（防重复提交） |
| `500 Internal Server Error` | 后端内部错误 |

#### 错误响应格式

所有错误均使用 FastAPI 默认的 `HTTPException` 格式：

```json
{
  "detail": "错误描述"
}
```

**具体错误示例**:

```json
// 400 Bad Request — 手机号格式不正确
{ "detail": "手机号格式不正确，必须为11位数字" }

// 404 Not Found — 账号不存在
{ "detail": "账号不存在" }

// 409 Conflict — 连接进行中
{ "detail": "账号正在连接中，请勿重复提交" }
```

#### 后端行为

1. 验证 `account_id` 对应的账号存在于数据库
2. 检查是否已有进行中的连接会话（`ConnectionStatusManager` 中是否已有非终态状态）
3. 将账号状态更新为 `AccountStatus.LOGGING_IN`
4. 通过 `ConnectionStatusManager.set_status()` 推送 `WAITING_PHONE` 状态
5. 异步启动浏览器操作（`BackgroundTasks`）：
   a. 调用 `DewuClient.send_sms_code(phone)` — 新方法，负责打开登录页、输入手机号、点击发送按钮
   b. 操作成功后推送 `CODE_SENT` 状态（progress=40）
   c. 操作失败后推送 `ERROR` 状态，恢复账号状态为 `INACTIVE`
6. 同步返回 202 响应（不等待浏览器操作完成）

---

### 1.2 POST /api/accounts/connect/{account_id}/verify

**功能**: 将用户输入的验证码填入浏览器中已打开的登录表单，点击登录按钮，等待登录结果，成功后保存 storage state。

#### Path Parameters

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `account_id` | `integer` | 是 | 账号数据库主键 ID |

#### Request Body

Content-Type: `application/json`

```json
{
  "code": "123456"
}
```

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `code` | `string` | 是 | 长度 4-6 位，仅数字 | 用户收到的短信验证码 |

**Pydantic Schema** (新增):
```python
class VerifyCodeRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=6, description="短信验证码")
```

#### 成功响应 — 200 OK

```json
{
  "success": true,
  "message": "连接成功",
  "status": "active"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `boolean` | 登录是否成功 |
| `message` | `string` | 人类可读消息 |
| `status` | `string` | 账号最终的 `AccountStatus` 枚举值 |

注意: `storage_state` 字段**不包含**在响应中（已在后端加密存入数据库，不暴露给客户端）。

#### 失败响应 — 200 OK（业务失败）

登录验证本身失败时仍返回 200，通过 `success: false` 区分：

```json
{
  "success": false,
  "message": "验证码错误或已过期",
  "status": "inactive"
}
```

**HTTP Status Codes**:

| 状态码 | 场景 |
|--------|------|
| `200 OK` | 请求处理完成（含业务成功和失败） |
| `400 Bad Request` | 验证码格式不正确 |
| `404 Not Found` | 账号不存在 |
| `422 Unprocessable Entity` | 没有进行中的连接会话（需要先调用 send-code） |
| `500 Internal Server Error` | 后端内部错误 |

**具体错误示例**:

```json
// 400 Bad Request — 验证码格式不正确
{ "detail": "验证码格式不正确，需为4-6位数字" }

// 422 Unprocessable Entity — 没有活跃的浏览器会话
{ "detail": "没有进行中的连接会话，请先发送验证码" }
```

#### 后端行为

1. 验证 `account_id` 对应的账号存在
2. 验证 `ConnectionStatusManager` 中存在该账号的进行中状态（`CODE_SENT` 或 `WAITING_VERIFY`），否则返回 422
3. 推送 `WAITING_VERIFY` 状态（progress=50）
4. 调用 `DewuClient.verify_sms_code(code)` — 新方法，负责输入验证码、点击登录、检测登录结果
5. 成功路径：
   a. 推送 `VERIFYING` 状态（progress=80）
   b. 调用 `client.save_login_session()` 保存加密 storage state 至数据库
   c. 更新账号 `status = active`，记录 `last_login`
   d. 推送 `SUCCESS` 状态（progress=100）
   e. 写入 `SystemLog`
   f. 返回 `success: true`
6. 失败路径：
   a. 推送 `ERROR` 状态（progress=0）
   b. 恢复账号 `status = inactive`
   c. 返回 `success: false`
7. 异常路径：
   a. 捕获所有 Exception
   b. 推送 `ERROR` 状态
   c. 更新账号 `status = error`
   d. 记录 loguru error（不含验证码内容）
   e. 返回 `success: false`

---

### 1.3 GET /api/accounts/connect/{account_id}/stream（保持不变）

SSE 流端点不做修改，此处仅完整记录其协议规范供前端参考。

**功能**: 以 Server-Sent Events 实时推送连接状态变化。

#### Path Parameters

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `account_id` | `integer` | 是 | 账号数据库主键 ID |

#### Response Headers

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

#### 打开时机

前端应在进入连接弹窗时立即建立 SSE 连接，**早于**调用 `send-code` 端点，以确保不错过任何状态事件。

---

## 二、SSE 事件协议

### 2.1 事件格式

所有 SSE 事件遵循标准格式：

```
event: <event_type>\n
data: <JSON 字符串>\n
\n
```

心跳使用注释格式（无 event/data）：

```
: heartbeat\n
\n
```

### 2.2 事件类型列表

#### status_update 事件

在连接流程的每个状态变更时推送。

```
event: status_update
data: {"status": "code_sent", "message": "验证码已发送，请在5分钟内输入", "progress": 40, "timestamp": "2026-04-06T10:00:00.000000"}
```

**data 字段**:

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| `status` | `string` | 是 | `ConnectionStatus` 枚举字符串值 |
| `message` | `string` | 是 | 人类可读的状态描述 |
| `progress` | `integer` | 是 | 进度百分比，范围 0-100 |
| `timestamp` | `string` | 是 | ISO 8601 UTC 时间戳 |

#### done 事件

在流程进入终态（`success` 或 `error`）后，`status_update` 之后额外推送。接收此事件后，客户端应关闭 SSE 连接。

```
event: done
data: {"message": "连接流程结束", "final_status": "success"}
```

```
event: done
data: {"message": "连接流程结束", "final_status": "error"}
```

**data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `message` | `string` | 固定为 `"连接流程结束"` |
| `final_status` | `string` | `"success"` 或 `"error"`（与 ConnectionStatus 枚举一致） |

**重要**: `final_status` 使用 `"success"` 而非 `"connected"`，与 `ConnectionStatus.SUCCESS = "success"` 保持一致。

#### error 事件

SSE 内部发生未预期异常时推送（不同于连接流程失败的 `done` 事件）。

```
event: error
data: {"message": "服务器内部错误"}
```

#### 心跳（注释行）

每 30 秒无状态变化时发送，防止连接超时。

```
: heartbeat
```

### 2.3 SSE 初始状态推送

若客户端在流程已开始后才连接 SSE，服务端会立即推送当前最新状态（`subscribe()` 方法的初始状态逻辑），确保客户端不错过进度。

### 2.4 终止条件

SSE 流在以下条件下终止：

1. 服务端推送 `done` 事件后主动结束生成器
2. 客户端主动关闭 EventSource（如关闭弹窗）
3. 连接发生网络错误
4. `asyncio.CancelledError` 被捕获（请求取消）

---

## 三、ConnectionStatus 状态机

### 3.1 状态枚举

| 枚举值 | 字符串值 | 含义 |
|--------|----------|------|
| `ConnectionStatus.IDLE` | `"idle"` | 初始状态，无进行中的连接 |
| `ConnectionStatus.WAITING_PHONE` | `"waiting_phone"` | 浏览器已打开，等待手机号输入（内部中间态） |
| `ConnectionStatus.CODE_SENT` | `"code_sent"` | 短信已发送，等待用户输入验证码 |
| `ConnectionStatus.WAITING_VERIFY` | `"waiting_verify"` | 已收到验证码，等待后端执行验证 |
| `ConnectionStatus.VERIFYING` | `"verifying"` | 验证码已提交，正在检测登录结果 |
| `ConnectionStatus.SUCCESS` | `"success"` | 登录成功，session 已保存 |
| `ConnectionStatus.ERROR` | `"error"` | 连接失败（任意阶段） |

### 3.2 状态转移图

```
                    POST /send-code
                         │
                         ▼
         [IDLE] ──────► [WAITING_PHONE]
                              │
                              │  浏览器输入手机号完成，
                              │  短信发送成功
                              ▼
                        [CODE_SENT] ◄────── 等待用户输入验证码
                              │
                              │ POST /verify
                              ▼
                      [WAITING_VERIFY]
                              │
                              │  后端将验证码输入浏览器
                              ▼
                         [VERIFYING]
                         /         \
                        /           \
                       ▼             ▼
                  [SUCCESS]       [ERROR]
                   (终态)         (终态)

          任意阶段发生异常
                  │
                  └──────────────► [ERROR]
                                   (终态)
```

### 3.3 触发端点与状态对应

| 状态 | 触发端点 | 触发时机 | progress |
|------|----------|----------|----------|
| `waiting_phone` | `POST /send-code` | 请求处理开始时 | 10 |
| `code_sent` | `POST /send-code` | 浏览器成功发送短信后（后台任务中） | 40 |
| `waiting_verify` | `POST /verify` | 请求处理开始时 | 50 |
| `verifying` | `POST /verify` | 验证码填入后，等待登录结果 | 80 |
| `success` | `POST /verify` | 登录成功且 session 保存完成 | 100 |
| `error` | 任意端点 | 任意步骤发生错误 | 0 |

---

## 四、错误处理

### 4.1 错误场景分类

#### send-code 阶段

| 场景 | HTTP 状态码 | `detail` 消息 | 客户端行为 |
|------|-------------|---------------|------------|
| `account_id` 不存在 | 404 | `"账号不存在"` | 关闭弹窗，刷新账号列表 |
| 手机号格式错误 | 400 | `"手机号格式不正确，必须为11位数字"` | 提示用户重新输入 |
| 已有进行中的连接 | 409 | `"账号正在连接中，请勿重复提交"` | 提示用户等待或先取消 |
| 浏览器创建失败 | SSE `error` | （通过 SSE 推送） | 显示错误，提供重试按钮 |
| 找不到手机号输入框 | SSE `error` | （通过 SSE 推送） | 显示错误 |
| 找不到发送验证码按钮 | SSE `error` | （通过 SSE 推送） | 显示错误 |

#### verify 阶段

| 场景 | HTTP 状态码 / 字段 | 说明 | 客户端行为 |
|------|-------------------|------|------------|
| `account_id` 不存在 | 404 | `"账号不存在"` | 关闭弹窗 |
| 验证码格式错误 | 400 | `"验证码格式不正确，需为4-6位数字"` | 提示用户检查输入 |
| 没有进行中的会话 | 422 | `"没有进行中的连接会话，请先发送验证码"` | 返回发送验证码步骤 |
| 验证码错误/过期 | 200 + `success: false` | 业务失败 | 提示重新获取验证码 |
| 登录超时 | 200 + `success: false` | 业务失败 | 提示重新尝试 |
| 浏览器操作异常 | 200 + `success: false` | 业务失败 | 显示具体错误消息 |

### 4.2 错误响应统一格式

HTTP 错误（4xx/5xx）使用 FastAPI 的 `HTTPException`：

```json
{
  "detail": "错误描述文本"
}
```

业务失败（HTTP 200 但操作未成功）：

```json
{
  "success": false,
  "message": "具体失败原因",
  "status": "inactive"
}
```

### 4.3 客户端错误处理策略

```typescript
// send-code 错误处理
try {
  await axios.post(`/api/accounts/connect/${accountId}/send-code`, { phone })
} catch (error: unknown) {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status
    if (status === 404) {
      // 账号不存在，关闭弹窗
    } else if (status === 409) {
      // 已有连接中，提示等待
    } else {
      message.error(error.response?.data?.detail || '发送失败')
    }
  }
}

// verify 错误处理
const response = await axios.post<VerifyResponse>(
  `/api/accounts/connect/${accountId}/verify`,
  { code }
)
if (!response.data.success) {
  // 业务失败，提示重新获取验证码
  message.error(response.data.message)
}
```

---

## 五、生命周期管理

### 5.1 DewuClient 实例保持策略

两阶段流程中，浏览器实例必须在 `send-code` 和 `verify` 之间持久保持：

- `DewuClient` 实例存储在模块级字典 `_active_clients: Dict[int, DewuClient]` 中，以 `account_id` 为键
- `send-code` 端点创建并存储实例
- `verify` 端点从字典中取出实例
- 流程结束（成功或失败）后，从字典中移除实例

**建议实现方式**:

```python
# core/dewu_client.py 新增
_active_clients: Dict[int, DewuClient] = {}

async def get_or_create_client(account_id: int) -> DewuClient:
    if account_id not in _active_clients:
        _active_clients[account_id] = DewuClient(account_id)
    return _active_clients[account_id]

def release_client(account_id: int) -> None:
    _active_clients.pop(account_id, None)
```

### 5.2 超时清理策略

| 超时类型 | 时长 | 行为 |
|----------|------|------|
| 验证码有效期 | 5 分钟 | 超过后用户提交 verify 会在浏览器端失败，返回 `success: false` |
| 浏览器页面操作超时 | 60 秒（每次 Playwright wait） | 触发 `PlaywrightTimeout`，推送 `ERROR` 状态，释放实例 |
| SSE 心跳间隔 | 30 秒 | 每 30 秒发送心跳注释行 |
| DewuClient 会话最长保持 | 10 分钟 | 超过此时间若未完成 verify，后台清理任务释放浏览器实例并推送 ERROR |

10 分钟的会话清理需通过 background task 或 asyncio 定时器实现，确保异常退出不会留存僵尸浏览器实例。

### 5.3 用户取消时的清理

用户在连接弹窗中点击"取消"时，前端应：

1. 关闭 SSE EventSource
2. （可选）调用 `POST /api/accounts/disconnect/{account_id}` 清理后端状态

`disconnect` 端点已存在，其行为：

1. 调用 `browser_manager.close_context(account_id)` 关闭浏览器上下文
2. 调用 `release_client(account_id)` 释放 DewuClient 实例（需在实现时添加）
3. 调用 `connection_status_manager.clear_status(account_id)` 清除 SSE 状态
4. 将账号状态重置为 `inactive`，清除 `storage_state` 和 `cookie`

### 5.4 异常退出清理

所有操作应在 `try/finally` 块中确保：

```python
try:
    # 业务逻辑
    ...
finally:
    if failed:
        release_client(account_id)
        connection_status_manager.clear_status(account_id)
```

---

## 六、向后兼容

### 6.1 旧 POST /connect/{account_id} 端点

**处理方式**: 弃用（deprecated），保留现有实现直到前端完成迁移。

- 标记 `@router.post("/connect/{account_id}", deprecated=True)`
- 响应体中增加 `X-Deprecated: true` 响应头（可选）
- 不再作为主流程使用，但继续可用

**迁移建议**: 前端将 `handleSendCode` 中对 `POST /connect/{account_id}` 的调用迁移至新的 `POST /connect/{account_id}/send-code`，将 `handleConnect` 中的提交逻辑迁移至 `POST /connect/{account_id}/verify`。

### 6.2 旧 /login/ 端点系列

**处理方式**: 已标记为弃用，现有行为保持不变，通过 delegate 方式转发至新端点：

| 旧端点 | 新端点 | 状态 |
|--------|--------|------|
| `POST /login/{id}` | `POST /connect/{id}` | 已弃用，保留 |
| `GET /login/{id}/stream` | `GET /connect/{id}/stream` | 已弃用，保留 |
| `GET /login/{id}/status` | `GET /connect/{id}/status` | 已弃用，保留 |
| `POST /login/{id}/export` | `POST /connect/{id}/export` | 已弃用，保留 |
| `POST /login/{id}/import` | `POST /connect/{id}/import` | 已弃用，保留 |

所有弃用端点继续通过 `delegate` 方式工作（参见 `account.py` 中的现有实现），不在此次改动范围内。

---

## 七、新增 Pydantic Schemas

以下 Schemas 需添加至 `backend/schemas/__init__.py`：

```python
class SendCodeRequest(BaseModel):
    """发送验证码请求"""
    phone: str = Field(..., min_length=11, max_length=11, description="手机号（11位）")


class SendCodeResponse(BaseModel):
    """发送验证码响应"""
    success: bool
    message: str
    status: str = "code_sent"


class VerifyCodeRequest(BaseModel):
    """验证码登录请求"""
    code: str = Field(..., min_length=4, max_length=6, description="短信验证码（4-6位）")


class VerifyCodeResponse(BaseModel):
    """验证码登录响应"""
    success: bool
    message: str
    status: str = "inactive"
```

---

## 八、DewuClient 方法拆分

现有 `login_with_sms(phone, code)` 方法需拆分为两个独立方法：

### 8.1 send_sms_code(phone)

```python
async def send_sms_code(self, phone: str) -> Tuple[bool, str]:
    """
    第一阶段：打开登录页，输入手机号，点击发送验证码

    Args:
        phone: 手机号（11位）

    Returns:
        Tuple[bool, str]: (成功标志, 消息)
    """
    # 创建浏览器页面
    # 导航至 LOGIN_URL
    # 勾选协议复选框
    # 输入手机号
    # 点击发送验证码按钮
    # 等待短信发送确认
    # 返回 (True, "验证码已发送") 或 (False, 错误消息)
```

### 8.2 verify_sms_code(code)

```python
async def verify_sms_code(self, code: str) -> Tuple[bool, str]:
    """
    第二阶段：输入验证码，点击登录，检测登录结果

    前提：send_sms_code 已成功执行，self.page 持有登录页实例

    Args:
        code: 短信验证码（4-6位）

    Returns:
        Tuple[bool, str]: (成功标志, 消息)
    """
    # 验证 self.page 存在
    # 输入验证码
    # 点击登录按钮
    # 调用 _check_login_result()
    # 返回结果
```

**注意**: `verify_sms_code` 依赖 `self.page` 是 `send_sms_code` 遗留的登录页面实例，不能重新导航。

---

## 九、前端迁移指南

ConnectionModal.tsx 需要做以下调整（供 frontend-lead 参考，非本文档实现范围）：

### 9.1 handleSendCode 变更

```typescript
// 旧实现
await axios.post(`/api/accounts/connect/${accountId}`, {
  phone,
  code: '',  // 空验证码表示只发送
})

// 新实现
await axios.post(`/api/accounts/connect/${accountId}/send-code`, {
  phone,
})
```

### 9.2 handleConnect 变更

```typescript
// 旧实现
const response = await axios.post<ConnectResponse>(
  `/api/accounts/connect/${accountId}`,
  { phone: values.phone, code: values.code }
)

// 新实现
const response = await axios.post<VerifyResponse>(
  `/api/accounts/connect/${accountId}/verify`,
  { code: values.code }  // 不需要传 phone，后端已在 send-code 阶段持有
)
```

### 9.3 ConnectionStatus 类型修正

前端 SSE `DoneEvent` 的 `final_status` 类型需从 `'connected' | 'error'` 修正为 `'success' | 'error'`：

```typescript
// 旧定义
interface DoneEvent {
  final_status: 'connected' | 'error'
}

// 新定义
interface DoneEvent {
  final_status: 'success' | 'error'
}

// 旧检查
if (data.final_status === 'connected') { ... }

// 新检查
if (data.final_status === 'success') { ... }
```

同时 `ConnectionStatus` 类型中的 `'connected'` 需修正为 `'success'`：

```typescript
// 旧
type ConnectionStatus = 'idle' | 'waiting_phone' | 'code_sent' | 'waiting_verify' | 'verifying' | 'connected' | 'error'

// 新
type ConnectionStatus = 'idle' | 'waiting_phone' | 'code_sent' | 'waiting_verify' | 'verifying' | 'success' | 'error'
```

---

## 十、开放问题

以下问题需在实现前确认：

| # | 问题 | 建议方案 | 决策人 |
|---|------|----------|--------|
| 1 | `DewuClient` 实例字典应存储在哪一层？(`core/dewu_client.py` 模块级，还是 `ConnectionStatusManager` 内部) | 建议模块级，与 `ConnectionStatusManager` 解耦 | Tech Lead |
| 2 | `send-code` 是否返回 202 异步，还是同步等待短信确认返回 200？ | 建议 202 异步，通过 SSE 告知结果 | Tech Lead / Product Owner |
| 3 | 超过 10 分钟的会话清理用 `asyncio` 定时器还是 APScheduler？ | 建议 `asyncio.create_task` + `asyncio.sleep` 内联实现 | Backend Lead |

---

*文档版本 v2.0 — 待 Tech Lead 审批后进入实现阶段*
