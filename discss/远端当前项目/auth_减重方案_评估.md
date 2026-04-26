# `discss/new/auth_减重方案.md` 评估

日期：2026-04-25

## 总结

这份“减重方案”**方向上有启发，但不能整体照搬**。

按当前仓内实现看，我的结论是：

- **建议 1（合并 DB + secret store）**：**方向成立，但不是低风险“小减重”**；它会动到本地 admin/session 可观测性，属于一次架构重排。
- **建议 2（设备身份单一来源）**：**最值得采纳**；而且仓内已经做了一半，下一步应把前端 `localStorage` 彻底收口到 Electron/本地后端的同一来源。
- **建议 3（9 状态压成 4 状态）**：**不建议直接压平后端 canonical state**；可以压缩为 **4 个 UI bucket / route bucket**，但底层状态最好保留。
- **建议 4（去掉 401/403 后的 syncSession）**：**不建议直接删光**；当前 403 不只表示“去登录”，还可能表示 `grace / revoked / device_mismatch`，直接跳登录会丢语义。

一句话结论：

> **这份方案更适合作为“前端投影层简化 + 设备身份收口”的改造提纲，而不是“把现有 auth 内核整体砍成单文件状态机”。**

---

## 仓内现状核对

### 1) 当前确实是“DB 状态 + 文件 secret”双存储

- 本地非敏感 session 状态存在 `RemoteAuthSession` 表：`backend/models/__init__.py:834-850`
- token secrets 存在文件型 `FileSecretStore`：`backend/core/secret_store.py:46-107`
- 登录/刷新路径先写 token，再更新 DB session：`backend/services/auth_service.py:113-114`, `568-570`

这说明文档里说的“需要协调两个存储”是**真实问题**，不是空想。

### 2) 设备身份已经部分收口，但前端还没彻底统一

- 本地后端已经有独立文件型 device identity store：`backend/core/device_identity.py:13-65`
- AuthService 已把它当 canonical device id 来源：`backend/services/auth_service.py:795-796`
- 但前端仍然自己在 `localStorage` 里生成/保存 device id：`frontend/src/features/auth/device.ts:1-17`
- 登录页还会把后端返回的 `device_id` 反写回前端本地存储：`frontend/src/features/auth/LoginPage.tsx:47-54`

所以建议 2 不是“从零开始”，而是**把现有半收口方案收完整**。

### 3) 当前 9 状态不只是 UI 噪音，部分是策略语义

- 前端 auth state 明确有 9 个：`frontend/src/features/auth/types.ts:1-10`
- 后端本地策略矩阵也直接依赖这些状态：`backend/core/auth_dependencies.py:35-46`, `72-91`
- 其中 `authenticated_grace / revoked / device_mismatch` 都映射成不同 403 语义：`backend/core/auth_dependencies.py:72-91`
- 前端路由也有独立页：`frontend/src/features/auth/AuthRouteGate.tsx:47-72`

所以这 9 个状态里，**有些是实现细节，有些已经变成产品语义**。

### 4) 当前前端确实存在 401/403 后的会话回同步

- transport 层在 401/403 时会调用 `syncSession()`：`frontend/src/features/auth/transport.ts:15-59`

所以文档第 4 条评价的是现有真实实现。

---

## 对四条建议的逐项评价

## 建议 1：合并两个存储为一个

### 我给的评价

**方向可理解，但不适合被描述成“简单减重”。**

### 为什么它有道理

当前实现确实有 split-brain 风险：

- token 在文件
- auth_state / expires_at / grace / denial_reason 在 DB
- 登录与刷新路径是“先写 token，再写 session 元数据”

如果两步之间异常退出，理论上会留下不一致窗口。

### 为什么我不建议直接照抄

因为当前 DB 不只是“多余状态表”，它还承担了这些职责：

- admin 查询本地 session：`backend/api/auth.py:253-275`
- 本地 session 详情/健康检查：`backend/services/auth_service.py:309-372`
- admin 页面展示 token presence、current session、时间戳：`frontend/src/features/auth/admin/SessionAdmin.tsx`, `SessionList.tsx`

也就是说，**现在的 DB 已经是“可观测层”**，不是单纯缓存。

如果直接合成“一个加密 JSON 文件”，会带来两个后果：

1. 读写原子性更好  
2. 但 admin/debug/inspection 能力会变差，或者你得再做一层投影/索引把这些能力补回来

### 更合理的改法

我更推荐这两种之一：

- **方案 A（保守）**：保留 DB 作为可查询 metadata，改成“单个 encrypted envelope + DB projection”
  - secrets + session snapshot 放一个加密文件
  - DB 只存 admin/debug 需要的索引字段或最近快照
- **方案 B（激进）**：彻底单文件化，但前提是先确认本地 admin session 面是否还能接受能力下降

### 结论

**可做，但这是架构改造，不是纯减重。**

---

## 建议 2：设备身份单一来源

### 我给的评价

**这是四条里最对的一条。**

### 为什么

当前仓内已经暴露出“双来源”：

- 后端有 `FileDeviceIdentityStore`
- 前端有 `localStorage` device id

虽然现在后端会逐步“纠正”前端传入值，但这仍然意味着：

- 首次启动谁先生成 device id 取决于调用路径
- Renderer 仍然拥有生成身份的能力
- 设备身份边界不够清晰

### 最佳落地方式

文档提的方向基本正确：

- Electron main 负责生成/读取 device id
- preload 暴露只读 IPC
- Renderer 只消费，不生成
- 本地后端也读同一路径，或由 Electron 统一注入

当前 Electron preload 只有 `getVersion`，没有 `getDeviceId`：`frontend/electron/preload.ts:8-37`

所以这条的最小落地可以是：

1. 新增 `electronAPI.getDeviceId()`
2. `frontend/src/features/auth/device.ts` 删除 `localStorage` 生成逻辑
3. 前端登录页改为异步读取 canonical device id
4. 后端继续使用 `FileDeviceIdentityStore`，并确保路径与 Electron 一致

### 结论

**建议优先采纳。**

---

## 建议 3：状态从 9 个压到 4 个

### 我给的评价

**“压 UI，不压内核”可以；“直接压后端真相层”不建议。**

### 为什么不能直接压到底

当前状态不是全都一个层级：

- `authenticated_active`
- `authenticated_grace`
- `revoked`
- `device_mismatch`
- `expired`
- `unauthenticated`
- `refresh_required`
- `authorizing`
- `error`

其中至少这几个不该被随便揉平：

- `revoked`：管理员撤销/禁用后的硬拒绝
- `device_mismatch`：安全/绑定语义，应该单独暴露
- `authenticated_grace`：可读不可写，不等于“过期”

如果把它们都压成 `expired` 或统一“重新登录”，会损失：

- 用户提示准确性
- 支持排障能力
- 本地策略判断可解释性

### 但它说的痛点也是真实的

前端 route 分支确实偏多，transport/error copy 也比较散。  
所以**UI 层应该做投影聚合**。

更好的做法是保留 canonical state，同时提供一个更粗的 view model，例如：

- `active`
- `grace`
- `reauth`（含 `unauthenticated / refresh_required / expired / error`）
- `hard_denied`（含 `revoked / device_mismatch`）

其实后端已经在做类似投影：

- `is_active`
- `is_grace`
- `requires_reauth`
- `can_read_local_data`
- `can_run_protected_actions`

见：`backend/services/auth_service.py:242-278`

这说明正确方向不是“删状态”，而是**增加 capability/bucket 投影层**。

### 结论

**建议改成“4 个 UI bucket”，不要改成“4 个底层状态”。**

---

## 建议 4：前端只保留一条 session 同步路径

### 我给的评价

**不建议直接按文档那样删除。**

### 核心问题

它假设：

> 401/403 基本都等于“session 已失效，再 sync 也没意义”

但在当前代码里，这个前提并不成立。

因为 403 可能表示：

- `authenticated_grace`（可读不可写）
- `revoked`
- `device_mismatch`

见：`backend/core/auth_dependencies.py:72-91`

这三种后续 UI 行为完全不同：

- grace：继续读、限制写、展示 banner
- revoked：跳 revoked 页
- device_mismatch：跳设备异常页

如果简单把所有 401/403 都改成“直接去登录页”，会把这些状态信息抹平。

### 这条建议哪里有价值

它指出了一个真实问题：  
**当前 transport 层的 401/403 → syncSession 是粗粒度的。**

这可能造成：

- 多一次 round-trip
- 错误处理分散在 transport 和 route 两层
- 某些请求失败时产生重复同步

### 更合理的改法

不是“删光 sync”，而是“缩窄触发条件”：

- 对明确的 auth-sensitive 失败保留 sync
- 做 singleflight / debounce，避免同一波 401/403 连续触发多次
- 对某些明确的登录失效场景可直接走本地状态切换
- 让 UI 最终依赖 `/auth/status` 或 session summary 的投影，而不是裸 HTTP code

### 结论

**建议优化，不建议删掉。**

---

## 我最终的采纳建议

如果真要按“减重”推进，我建议采用下面的优先级：

### P1：立即值得做

1. **设备身份单一来源**
2. **把前端状态消费改成 bucket/capability 驱动**
3. **收敛 401/403 后的 syncSession 触发条件**

### P2：评估后再做

4. **合并 secret + session snapshot 的持久化模型**

但第 4 条必须先确认：

- 本地 admin session 页面还要不要
- token presence / current session / history 还要不要
- 是否接受 debug 可观测性下降

---

## 最终结论

这份 `auth_减重方案.md` 的**最大价值**，不是“给出可直接照搬的新架构”，而是指出了当前 auth 的三个真问题：

1. **设备身份来源不够单一**
2. **前端状态消费层过细**
3. **401/403 后的同步策略过粗**

但它的两个激进判断需要下调：

- **“一个加密 JSON 文件就够了”**：低估了当前 DB 可观测层的价值
- **“401/403 直接跳登录就行”**：低估了 `grace / revoked / device_mismatch` 的区别

所以我的总体评价是：

> **70 分方案：适合作为减重方向，不适合作为直接实施稿。**

