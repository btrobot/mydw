# 本地 Auth 持久化模型（Step 0 PR2）

> 状态：Frozen

---

## 1. Persistence classes

v1 本地 auth 持久化冻结为两类：

1. **Non-secret state**
2. **Secret storage**

二者不能混为一谈。

---

## 2. Non-secret state

以下字段归类为 non-secret state，可落在 SQLite 或非敏感配置存储：

- `remote_user_id`
- `display_name`
- `license_status`
- `entitlements_snapshot`
- `expires_at`
- `last_verified_at`
- `offline_grace_until`
- `denial_reason`
- `device_id`

说明：

- 它们用于本地状态展示、路由门禁、日志与恢复判断
- 但不构成足以直接复用远程授权的秘密材料

---

## 3. Secret storage

以下归类为 secrets：

- `refresh_token`
- `access_token`（若决定持久化）
- 本地 secret seed / attestation material

### Hard rule

> `refresh_token` **不得明文写入 SQLite**

---

## 4. Logout impact on persistence

### Must clear

- secret storage 中的所有远程授权 secrets
- 当前 machine-session 授权真相缓存

### May retain

- non-secret state 的业务辅助信息，可由实现决定是删除还是保留最近状态快照  
  但无论保留与否，都不得让系统继续把它解释为“已授权”

v1 推荐：

- 删除或标记失效会话型 non-secret state
- 允许保留非敏感的最近用户展示信息，仅用于 UX 提示，不用于授权判定

---

## 5. SecretStore abstraction requirement

Step 0 冻结一个明确实现约束：

> 后续实现必须通过 `SecretStore` 抽象访问 secrets，而不是直接把 token 写进业务表或任意 JSON 文件。

### v1 allowed implementation direction

首版允许的过渡实现方向：

- 加密文件
- 加密字段

### v2 direction

后续可升级到：

- Windows Credential Manager
- macOS Keychain
- Linux Secret Service

---

## 6. Current crypto limitation note

当前仓库已有通用加密工具：

- `backend/utils/crypto.py`

它可作为过渡起点，但本 Step 0 明确冻结以下判断：

1. 它不是成熟的 auth vault
2. 不应在实现文档中被描述成最终 secrets 方案
3. `SecretStore` 抽象必须保留，以便后续替换底层存储

