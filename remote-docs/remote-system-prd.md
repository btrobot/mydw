# 远端系统 PRD（Product Requirements Document）

> 版本：Draft v1  
> 范围：远端授权中心 + 远端管理后台  
> 依据文档：
> - `remote-backend-requirements-analysis.md`
> - `remote-api-contract-v1-draft.md`
> - `remote-database-schema-draft.md`
> - `remote-frontend-backend-boundary.md`
> - `remote-mvp-roadmap.md`
> - `remote-backend-module-split.md`
> - `remote-admin-ui-page-list.md`

---

## 1. 项目背景

当前本地系统已经完成 remote-auth 本地侧能力建设，包括：

- 本地 machine-session truth
- auth 状态机
- auth observability / metrics
- auth status API
- auth error UX
- 本地 auth admin

但当前远端系统仍未实现。  
因此需要建设一个新的 **远端授权中心**，作为本地 remote-auth 的上游真相源，并同时提供一个 **远端管理后台** 给管理员和支持人员使用。

这个远端系统的目标不是承载本地业务数据，而是提供：

- 身份认证
- 授权状态
- 设备绑定
- token / session 生命周期
- 撤销 / 禁用 / 版本门禁
- 审计与后台管理能力

---

## 2. 目标

### 2.1 产品目标

构建一个远端授权中心，使本地桌面系统可以：

- 安全登录远端账号
- 定期 refresh 授权
- 获得稳定的 license / entitlement / device 状态
- 在 revoke / disabled / device mismatch / expired 时收到明确远端反馈
- 在后台通过管理控制台查看并操作授权对象

### 2.2 业务目标

- 将“授权真相”从本地临时逻辑升级为可运维的远端系统
- 降低本地授权异常排查成本
- 支持未来 license / entitlement / 多设备策略演进
- 为后续多租户、SSO、MFA、审计合规打基础

---

## 3. 非目标

本 PRD 不包括：

- 本地任务/素材/调度业务系统的云端化
- Dewu 业务数据同步
- 完整 IAM/企业身份平台
- 计费、支付、商业化系统
- 多租户复杂隔离的正式交付

---

## 4. 用户角色

### 4.1 普通授权用户

使用本地客户端，通过远端系统完成：

- 登录
- refresh
- 获取授权状态
- 设备绑定

### 4.2 认证管理员（Auth Admin）

通过远端管理后台进行：

- 用户授权管理
- 会话 revoke
- 设备解绑 / 禁用
- 问题排查

### 4.3 支持人员（Support / Readonly）

通过远端管理后台进行：

- 查看用户状态
- 查看设备状态
- 查看会话
- 查看审计日志

默认不具备高风险修改权限。

---

## 5. 核心问题

当前缺少远端系统时，会带来以下问题：

1. **授权真相分散**
   - 本地无法依赖稳定上游做授权判断

2. **无法远端控制**
   - 无法统一 revoke / disable / rebind 设备

3. **问题难排查**
   - 没有远端审计、设备、session 管理能力

4. **扩展性差**
   - 无法自然演进到更强授权模型

---

## 6. 目标用户故事

### US-001 登录与授权上下文
作为一个本地客户端用户，我希望能通过远端系统登录并获得授权上下文，以便客户端知道我是否有权继续使用。

### US-002 刷新与持续授权
作为一个本地客户端用户，我希望系统能在 token 即将过期时刷新授权，以便减少频繁重新登录。

### US-003 设备绑定控制
作为一个管理员，我希望可以控制哪些设备属于某个用户，以便阻止未授权机器继续访问。

### US-004 授权撤销
作为一个管理员，我希望能立刻 revoke 某个用户或会话，以便本地客户端尽快进入锁定态。

### US-005 支持排查
作为一个支持人员，我希望查看用户、设备、会话和审计日志，以便快速定位授权问题。

---

## 7. 核心需求

## 7.1 远端认证中心（必做）

### 认证接口

必须提供：

- `POST /login`
- `POST /refresh`
- `POST /logout`
- `GET /me`

### 成功响应必须支持

- `access_token`
- `refresh_token`
- `expires_at`
- `token_type`
- `user`
- `license_status`
- `entitlements`
- `device_id`
- `device_status`
- `offline_grace_until`（可选）
- `minimum_supported_version`（可选）

### 错误语义必须支持

- `invalid_credentials`
- `token_expired`
- `revoked`
- `disabled`
- `device_mismatch`
- `minimum_version_required`
- `network_timeout`

---

## 7.2 授权与设备控制（必做）

远端后端必须支持：

- license 状态下发
- entitlement 下发
- revoke / disabled
- 设备绑定
- 设备解绑 / 重绑
- device mismatch 判定
- 最低版本门禁
- offline grace 时间下发

---

## 7.3 管理后台（MVP 必做）

### 页面

至少包含：

- 登录页
- Dashboard
- 用户列表页
- 用户详情 / 授权页
- 设备列表页
- Session 列表页
- 审计日志页

### 管理 API

至少包含：

- `GET /admin/users`
- `GET /admin/users/{id}`
- `PATCH /admin/users/{id}`
- `POST /admin/users/{id}/revoke`
- `POST /admin/users/{id}/restore`
- `GET /admin/devices`
- `GET /admin/devices/{id}`
- `POST /admin/devices/{id}/unbind`
- `POST /admin/devices/{id}/disable`
- `POST /admin/devices/{id}/rebind`
- `GET /admin/sessions`
- `POST /admin/sessions/{id}/revoke`
- `GET /admin/audit-logs`

---

## 7.4 审计能力（必做）

远端后端必须记录以下事件：

- login success / failure
- refresh success / failure
- revoke
- disabled
- device mismatch
- minimum version block
- admin revoke user
- admin revoke session
- admin unbind device

审计日志需支持：

- 时间范围筛选
- 用户筛选
- 设备筛选
- event_type 筛选

---

## 8. 数据模型需求

MVP 至少需要以下表：

- `users`
- `user_credentials`
- `licenses`
- `user_entitlements`
- `devices`
- `user_devices`
- `sessions`
- `refresh_tokens`
- `audit_logs`
- `admin_users`
- `admin_roles`
- `admin_user_roles`

多租户为后续增强项，可在下一阶段增加：

- `tenants`
- `tenant_users`
- `tenant_licenses`

---

## 9. 关键边界

### 9.1 前台职责

远端前台负责：

- 展示
- 查询
- 发起管理操作

### 9.2 后端职责

远端后端负责：

- 授权真相
- 规则判定
- token / session 生命周期
- 设备绑定与 mismatch 判定
- admin RBAC
- 审计日志

### 9.3 本地系统职责

本地仍负责：

- machine-session truth
- 本地路由与服务门禁
- 本地 grace / expired / revoked 执行行为

---

## 10. 非功能需求

### 安全

- HTTPS only
- 密码哈希存储
- refresh token 不存明文
- access token 短期有效
- refresh token 支持轮转 / 吊销
- admin API 强制 RBAC
- 审计日志不可随意篡改

### 稳定性

- `/login /refresh /me` 要求高稳定性
- 错误码语义稳定
- 远端故障时不返回模糊错误

### 可观测性

远端系统本身应具备：

- auth 请求日志
- metrics
- trace_id / request_id
- revoke / device mismatch 审计

---

## 11. MVP 分阶段路线

### Phase 0 — 契约与设计冻结

产出：

- API 契约
- 数据库设计
- 前后台职责拆分

### Phase 1 — 认证主链路

实现：

- login
- refresh
- logout
- me

### Phase 2 — 授权 / 设备控制

实现：

- revoke / disabled
- device binding / mismatch
- version gate
- offline grace

### Phase 3 — 管理后台 MVP

实现：

- 用户
- 设备
- 会话
- 基础管理操作

### Phase 4 — 审计与支持能力

实现：

- 审计日志
- 查询筛选
- 支持排障能力

### Phase 5 — 增强能力

后置：

- 多租户
- SSO
- MFA
- 更细粒度 RBAC
- 风控

---

## 12. 验收标准

### 核心认证

- [ ] 本地客户端可调用远端 `/login /refresh /logout /me`
- [ ] 返回字段满足 v1 契约
- [ ] 错误码满足 v1 契约

### 授权控制

- [ ] revoke 后，本地 refresh / me 返回 `revoked`
- [ ] 非绑定设备会得到 `device_mismatch`
- [ ] 低版本客户端得到 `minimum_version_required`

### 管理后台

- [ ] 管理员可查看用户、设备、session
- [ ] 管理员可 revoke 用户 / session
- [ ] 管理员可解绑 / 禁用设备

### 审计

- [ ] 关键 auth 事件有审计记录
- [ ] 审计日志支持按用户/设备/事件筛选

---

## 13. 风险

### 主要风险

1. 远端错误码语义漂移，导致本地状态机失真
2. 设备绑定规则不清，导致误判 `device_mismatch`
3. token / session / revoke 逻辑耦合，影响可维护性
4. admin 权限控制不足，导致高风险操作暴露

### 风险缓解

- 冻结 v1 契约
- 独立 device / session / token 模块
- 所有管理操作写 audit
- 管理 API 独立 RBAC

---

## 14. 最终一句话定义

远端系统 MVP 的目标是：

> 构建一个可以稳定支撑本地 remote-auth 运行，并允许管理员查看、控制和审计授权状态的远端授权中心。
