# Remote Password Hash Upgrade ADR v1（Day 5.4 / Slice 11）

## 状态

Accepted for Day 5.5 implementation planning.

## 范围

本 ADR 只覆盖：

- **账户密码哈希升级**（end-user + admin-user）
- **平滑迁移策略**（dual-stack verify + opportunistic rehash）

本 ADR **不覆盖**：

- step-up runtime
- TOTP / 二次密码确认
- 前端登录合同改动
- refresh token 存储策略重构

---

## 一、代码事实基线

### 1. 当前密码实现只有 PBKDF2 单栈

- `remote/remote-backend/app/core/security.py:11-28`
  - `hash_password()` 当前固定产出 `pbkdf2_sha256`
  - `verify_password()` 只接受 `pbkdf2_sha256`

### 2. end-user 已有算法元数据，admin-user 没有

- `remote/remote-backend/app/models.py:35-42`
  - `user_credentials` 已有 `password_algo`
  - `user_credentials` 已有 `password_updated_at`
- `remote/remote-backend/app/models.py:148-156`
  - `admin_users` 当前只有 `password_hash`
  - **没有** `password_algo`

### 3. admin / end-user 登录都直接依赖当前单栈密码函数

- `remote/remote-backend/app/services/admin_service.py:65-89`
  - seed admin 与 admin login 都使用 `hash_password()` / `verify_password()`
- `remote/remote-backend/app/services/auth_service.py:68-104`
  - seed end-user 与 end-user login 也使用同一套 `hash_password()` / `verify_password()`

### 4. refresh token 也复用了同一套哈希函数

- `remote/remote-backend/app/services/auth_service.py:145-147`
  - refresh token 入库走 `hash_password(refresh_token)`
- `remote/remote-backend/app/services/auth_service.py:254-256`
  - refresh token rotate 仍走 `hash_password(next_refresh_token)`
- `remote/remote-backend/app/repositories/auth.py:140-156`
  - refresh token 校验走 `verify_password(refresh_token, candidate.token_hash)`

### 5. 当前配置只暴露了 PBKDF2 迭代次数

- `remote/remote-backend/app/core/config.py:43-45`
  - 只有 `PASSWORD_HASH_ITERATIONS`
  - 还没有 Argon2 参数配置

---

## 二、决策目标

Day 5 的最小目标不是“把所有 secret 都换成新算法”，而是：

1. **账户密码默认新写入改为 Argon2id**
2. **旧 PBKDF2 账户密码继续可登录**
3. **成功登录后平滑升级为 Argon2id**
4. **不改前端合同**
5. **不把 step-up runtime 一起带进来**
6. **不误伤 refresh token 流程**

---

## 三、备选方案

### 方案 A：直接把 `hash_password()` / `verify_password()` 全局切到 Argon2

**结论：拒绝**

原因：

- 当前 refresh token 也复用了这两个函数（`auth_service.py:145-147`, `254-256`; `repositories/auth.py:156`）
- 全局切换会把“密码升级”与“refresh token 存储语义变化”绑在同一刀里
- 风险面超出 Day 5.4 的最小目标

### 方案 B：账户密码改双栈，refresh token 暂不改，显式拆分 helper

**结论：采纳**

做法：

- 为“账户密码”与“refresh token”拆分显式 helper
- 账户密码走 `PBKDF2 verify + Argon2 default write`
- refresh token 暂时保持当前 PBKDF2 兼容行为

优点：

- 迁移边界清晰
- 可控地只升级真正需要升级的资产（账户密码）
- 不改 API，不改 token 合同

### 方案 C：批量离线重算所有旧密码哈希

**结论：拒绝**

原因：

- 无法从旧 hash 反推出明文密码
- 本质上会退化成“强制重置密码”，不是平滑升级
- 与“无感迁移”目标冲突

---

## 四、最终决策

### 决策 1：Day 5 只升级账户密码哈希，不升级 refresh token 存储策略

Day 5.5 落地时应先把安全 helper 拆成两类：

- 账户密码 helper
- refresh token helper

推荐 API 方向：

- `hash_account_password(password: str) -> PasswordHashRecord`
- `verify_account_password(password: str, stored_hash: str, algo: str | None) -> PasswordVerifyResult`
- `hash_refresh_token(token: str) -> str`
- `verify_refresh_token(token: str, stored_hash: str) -> bool`

这里的关键不是命名本身，而是**不要再让密码与 refresh token 共用“同一个默认哈希语义”**。

### 决策 2：默认新账户密码使用 Argon2id

推荐默认算法：

- `argon2id`

推荐原因：

- 当前目标是密码防护升级，不是通用 secret 哈希统一
- Argon2id 是密码哈希场景的更合适默认值

### 决策 3：保留 PBKDF2 验证能力，并在成功登录后 opportunistic rehash

触发规则：

- 若当前存储为 `pbkdf2_sha256`
- 且本次登录验证成功
- 则在同一业务流中尝试重写为 `argon2id`

覆盖对象：

- end-user login
- admin login

### 决策 4：为 `admin_users` 补 `password_algo` 字段；`password_updated_at` 暂不作为 Day 5 必选项

建议在 Day 5.5 的 Alembic revision 中新增：

- `admin_users.password_algo`

默认 / 回填策略：

- 现有 admin 行回填为 `pbkdf2_sha256`
- 新写入 admin 默认为 `argon2id`

为什么只把 `password_algo` 作为 Day 5 必选：

- 它是 dual-stack verify / opportunistic rehash 的最小元数据
- `password_updated_at` 对将来的密码年龄策略有价值，但不是本轮最小交付必需
- 当前 Day 5.4 明确**不做 step-up runtime**

### 决策 5：rehash 失败不能阻断旧 PBKDF2 登录可用性

推荐策略：

- PBKDF2 校验成功后，登录主流程视为已满足认证
- 后续 Argon2 重算 / 回写若失败，应记录 warning / audit 线索，但**不能把本次登录改判为失败**

也就是说：

- **验证成功** 是登录放行条件
- **rehash 成功** 只是增强动作，不是放行前置条件

---

## 五、Day 5.5 建议实现顺序

### Step 1：先拆 helper，不改行为

目标：

- 把 refresh token 与账户密码的 helper 分离
- 先做到“语义收口”，再切默认算法

验收：

- refresh/login 现有回归不变
- 所有 token 路径不再依赖“账户密码默认算法”

### Step 2：补配置

新增配置建议：

- `PASSWORD_HASH_DEFAULT_ALGO=argon2id`
- `PASSWORD_HASH_ARGON2_TIME_COST`
- `PASSWORD_HASH_ARGON2_MEMORY_COST_KB`
- `PASSWORD_HASH_ARGON2_PARALLELISM`
- `PASSWORD_HASH_ARGON2_HASH_LEN`
- `PASSWORD_HASH_ARGON2_SALT_LEN`

保留：

- `PASSWORD_HASH_ITERATIONS`

用途：

- 只为旧 PBKDF2 账户密码验证 / refresh token 兼容路径服务

### Step 3：补 schema 元数据

Alembic revision：

- 新增 `admin_users.password_algo`
- 回填现有数据为 `pbkdf2_sha256`

### Step 4：落地双栈验证与 rehash

end-user：

- 读取 `user_credentials.password_algo`
- 若为空或未知，按“安全失败”处理，不做盲猜
- `pbkdf2_sha256` 成功后触发 rehash

admin-user：

- 读取 `admin_users.password_algo`
- 对历史无此字段的数据，先通过 migration 回填，再进入运行时逻辑

### Step 5：切默认新写入算法

下列新写入默认使用 `argon2id`：

- seed user
- seed admin
- bootstrap admin
- 未来任何密码重置 / 改密入口

---

## 六、测试计划

### 单元测试

- `PBKDF2 -> verify success`
- `Argon2 -> verify success`
- `wrong password -> verify fail`
- `malformed hash / malformed algo -> safe fail`
- `PBKDF2 -> needs_rehash = true`
- `Argon2 current params -> needs_rehash = false`
- `refresh token verify/hash` 继续通过，且不依赖账户密码默认算法

### 服务层测试

- end-user 旧 PBKDF2 登录成功，并升级到 Argon2
- admin-user 旧 PBKDF2 登录成功，并升级到 Argon2
- 错误密码不会触发 rehash
- rehash 抛错时，本次旧密码登录仍成功
- 新 seed / bootstrap 写入的是 Argon2

### 集成 / migration 测试

- Alembic revision 能为 `admin_users` 回填 `password_algo`
- 旧库升级后 admin 登录链路可用
- backend 全量 pytest 通过

---

## 七、Acceptance Criteria

1. 新账户密码默认写入 `argon2id`
2. 旧 `pbkdf2_sha256` 账户密码无需批量重置即可继续登录
3. 成功登录后可平滑升级为 `argon2id`
4. admin / end-user 两条链路都覆盖 dual-stack verify
5. refresh token 行为与合同不因本次改造而漂移
6. 不新增前端合同变更
7. 不实现 step-up runtime

---

## 八、后续跟进

### Day 5.5

- 实现双栈密码校验
- 实现 opportunistic rehash
- 补 `admin_users.password_algo` Alembic revision

### Day 5.6

- 只输出 step-up security 设计稿
- 不进入运行时实现

---

## ADR 摘要

### Decision

采用 **“账户密码双栈 + Argon2 默认新写入 + opportunistic rehash + refresh token 暂不改”** 的最小风险方案。

### Drivers

- 不能打断现有登录链路
- 不能把 refresh token 风险混入密码升级
- 不能把 step-up runtime 一起带进本轮

### Alternatives considered

- 全局切 Argon2：拒绝
- 双栈密码 + refresh token 暂不改：采纳
- 批量离线重算旧密码：拒绝

### Why chosen

它是**最小可交付安全升级**，且能与当前代码事实对齐。

### Consequences

- 需要拆 helper
- 需要补 `admin_users.password_algo`
- 需要补更多安全与迁移测试

### Follow-ups

- Day 5.5 实现
- Day 5.6 输出 step-up 设计，不进运行时
