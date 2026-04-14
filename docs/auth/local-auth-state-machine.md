# 本地 Auth 状态机（Step 0 PR2）

> 状态：Frozen  
> 图文件：`docs/auth/diagrams/local-auth-state-machine.mmd`

---

## 1. State set

v1 本地最小状态集合冻结为：

- `unauthenticated`
- `authorizing`
- `authenticated_active`
- `authenticated_grace`
- `refresh_required`
- `revoked`
- `device_mismatch`
- `expired`
- `error`

后续如果新增状态，必须先更新 Step 0 文档，而不是在实现 PR 中直接新增。

---

## 2. State definitions

### `unauthenticated`
- 本机没有有效 machine-session
- 仅允许登录与最小公开接口

### `authorizing`
- 正在执行远程登录或恢复会话校验
- UI 处于加载 / 检查中态

### `authenticated_active`
- 远程认证成功
- machine-session 有效
- 可按授权范围使用本地功能

### `authenticated_grace`
- 当前远程不可达，但本机仍在允许的离线宽限期内
- 行为边界由 PR3 冻结

### `refresh_required`
- 当前 session 需要刷新才能继续维持有效
- 是否可过渡到 grace / expired，由 PR3 冻结

### `revoked`
- 远程明确返回授权撤销 / license 禁用等结果
- 本地必须进入锁定态

### `device_mismatch`
- 远程明确返回设备不匹配
- 本地必须进入设备锁定态

### `expired`
- 本机授权已过期，且无可用 grace

### `error`
- 临时错误态
- 表示一次远程认证或检查失败，但不自动等价于已授权

---

## 3. Canonical transitions

| From | Event | To |
|---|---|---|
| `unauthenticated` | start login | `authorizing` |
| `authorizing` | login success | `authenticated_active` |
| `authorizing` | invalid credentials | `unauthenticated` |
| `authorizing` | remote revoke | `revoked` |
| `authorizing` | device mismatch | `device_mismatch` |
| `authenticated_active` | access nearing expiry / refresh needed | `refresh_required` |
| `refresh_required` | refresh success | `authenticated_active` |
| `refresh_required` | network unavailable and grace valid | `authenticated_grace` |
| `refresh_required` | network unavailable and no grace | `expired` |
| `authenticated_active` | remote revoke | `revoked` |
| `authenticated_active` | remote device mismatch | `device_mismatch` |
| `authenticated_active` | expiry beyond grace | `expired` |
| `authenticated_grace` | remote connectivity restored + validation success | `authenticated_active` |
| `authenticated_grace` | grace exceeded | `expired` |
| any authenticated state | logout | `unauthenticated` |
| any state | unexpected internal failure | `error` |

---

## 4. Transition rules

### 4.1 Revocation precedence

`revoked` 与 `device_mismatch` 的优先级高于：

- `authenticated_active`
- `authenticated_grace`
- `refresh_required`

即：一旦远程明确返回这类结果，本地不得继续保留“有效授权”解释。

### 4.2 Error is not success

`error` 不是可执行态。  
它只表示本地需要重试、恢复或切换 UI，不代表本地可继续使用本地功能。

### 4.3 Grace is conditional

`authenticated_grace` 不是默认成功态。  
它是“远程不可达但在宽限内”的受限授权态。

---

## 5. UX mapping

| State | Renderer expectation |
|---|---|
| `unauthenticated` | 显示登录页 |
| `authorizing` | 显示启动检查 / 登录中 |
| `authenticated_active` | 进入正常 dashboard |
| `authenticated_grace` | 进入受限模式 dashboard |
| `refresh_required` | 短暂 loading / retry / 过渡态 |
| `revoked` | 显示锁定页 |
| `device_mismatch` | 显示设备不匹配锁定页 |
| `expired` | 显示登录页或锁定页（由 PR3 冻结具体行为） |
| `error` | 显示错误提示与重试入口 |

---

## 6. Diagram reference

Mermaid 原图位于：

- `docs/auth/diagrams/local-auth-state-machine.mmd`

