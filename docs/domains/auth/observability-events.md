# Auth Observability Events（Step 0 PR3）

> 状态：Frozen  
> 作用：冻结 auth 相关结构化事件名，供后续实现日志、调试与测试断言使用。

---

## 1. Purpose

后续 auth 实现必须能区分：

- 登录失败
- refresh 失败
- 授权撤销
- 设备不匹配
- grace 被使用
- 后台执行因 auth 停止

因此 Step 0 在这里冻结事件 taxonomy。

---

## 2. Frozen event names

## 2.1 Frontend / session lifecycle

- `auth_login_succeeded`
- `auth_login_failed`
- `auth_session_restored`
- `auth_session_restore_failed`
- `auth_logout_completed`

## 2.2 Refresh / validation

- `auth_refresh_started`
- `auth_refresh_succeeded`
- `auth_refresh_failed`
- `auth_me_validation_failed`

## 2.3 Authorization status changes

- `auth_revoked`
- `auth_expired`
- `auth_offline_grace_used`
- `auth_device_mismatch`

## 2.4 Background enforcement

- `scheduler_denied_by_auth`
- `background_stopped_due_to_auth`
- `publish_task_failed_due_to_auth`
- `composition_poller_stopped_due_to_auth`

---

## 3. Event usage rules

### 3.1 Distinguish network failure from remote deny

`auth_refresh_failed` 不能吞掉所有原因。  
后续实现必须能区分：

- 网络失败
- 远程 revoke
- 远程 disabled
- 远程 device mismatch

### 3.2 Background stop reasons must be visible

当 publish scheduler / composition poller 因 auth 停止时：

- 必须有单独事件
- 不得只写泛化错误日志

### 3.3 Event names are frozen

Step 1+ 实现若要改事件名，必须先补 Step 0 文档。

---

## 4. Recommended minimum fields

后续实现这些事件时，建议最少包含：

- `event_name`
- `timestamp`
- `remote_user_id`（若可用）
- `device_id`（若可用）
- `auth_state`
- `reason_code`

---

## 5. Review checklist

- [ ] 事件分类覆盖登录 / refresh / revoke / grace / background stop
- [ ] 事件名可直接用于 test assertions
- [ ] 无占位词

