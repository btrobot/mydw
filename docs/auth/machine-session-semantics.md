# Machine-Session 语义（Step 0 PR2）

> 状态：Frozen

---

## 1. v1 machine model

v1 明确定义为：

> **单机单活跃远程用户会话**

含义：

- 一台机器上的一个本地桌面应用实例
- 在任一时刻只对应一个远程授权上下文
- 本地授权门禁围绕这一活跃 machine-session 运行

---

## 2. Why v1 does not support local multi-user sharing

当前仓库的本地业务数据不是多租户隔离模型：

- SQLite 为单机业务库
- 任务、素材、Dewu 账号、日志共享同一业务域

因此 v1 不承诺：

- 多远程用户共享同一业务库的安全隔离
- 多远程用户快速切换后仍保持本地资产严格隔离

如需支持，必须在后续规划本地命名空间或租户分区。

---

## 3. Logout semantics

## 3.1 Logout clears

登出时本地必须清除或失效：

- machine-session
- refresh token
- access token（若有持久化）
- 当前授权状态缓存
- 当前可执行授权态

## 3.2 Logout does not delete by default

默认不删除：

- Dewu 本地账号资产
- 本地素材文件
- 本地任务
- 业务日志
- 系统配置

原因：

- Step 0 仅冻结授权语义
- 删除本地业务资产会改变业务数据生命周期，超出本轮 auth domain model 范围

---

## 4. User switching semantics

v1 不承诺安全支持多远程用户共用同一本地业务库。  
因此：

- 用户切换应被视为重新建立一个新的 machine-session
- 但本地旧资产默认仍保留
- 是否允许新远程用户直接消费旧本地资产，不在 v1 承诺范围内

后续若要支持，需要单独冻结：

- 本地数据 ownership model
- 授权用户与本地业务库绑定策略

---

## 5. Machine-session truth rule

后续实现必须遵守：

> 本地 FastAPI machine-session 是 v1 认证真相，前端只消费其状态，不单独持有长期授权真相。

