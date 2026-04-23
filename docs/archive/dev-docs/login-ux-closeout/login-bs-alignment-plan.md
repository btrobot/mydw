# 登录页 B/S 化展示收口方案

日期：2026-04-20

---

## 1. 目标

把当前登录页收口成**用户看起来像普通 B/S 应用登录页**的体验：

- 账号
- 密码
- 记住我
- 登录
- 忘记密码 / 联系管理员（按实际能力选择）

同时**不重做现有 auth 架构**：

- 前端仍然只调用本地后端 `/api/auth/*`
- 本地后端仍然负责 remote auth 代理、session 编排、device 绑定、refresh、状态机判定
- 前端不直接接管 token / secret / 远端认证细节

一句话定义：

> 展示层完全按普通 B/S 登录心智收口；Electron / 本地后端 / 远端认证代理只是内部实现，不应投射到用户界面。

---

## 2. 非目标

本轮**不做**：

- 不改成前端直连远端认证
- 不删除 device_id / client_version / 本地 session 机制
- 不把 `revoked` / `device_mismatch` / `expired` / `grace` 合并回普通登录错误
- 不新增一套独立 auth SDK
- 不重做视觉品牌系统

---

## 3. 当前架构结论

当前真实链路：

```text
LoginPage
  -> frontend/src/features/auth/api.ts
  -> POST /api/auth/login
  -> backend/api/auth.py
  -> backend/services/auth_service.py
  -> backend/core/remote_auth_client.py
  -> 远端认证系统
```

所以当前系统已经天然支持：

- 前端看起来像普通登录页
- 认证细节留在本地后端

这意味着：

> “像普通 B/S 登录页”只是展示层收口，不需要推翻实现。

---

## 4. 核心产品原则

### 4.1 用户只看见“登录应用”

登录页首屏只回答三件事：

1. 这是应用登录入口
2. 我需要输入什么
3. 登录失败时下一步做什么

不在首屏强调：

- 本地授权
- 设备标识
- 客户端版本
- 状态同步
- machine-session

进一步说：

> 用户不关心实现。  
> 对用户而言，这就应该只是一个普通登录页；  
> Electron 架构下的本地代理、设备绑定、session 恢复，都是系统内部实现。

---

### 4.2 异常分层

分两类异常：

#### A. 普通登录异常

留在登录页内解决：

- 账号或密码错误
- 网络超时
- 服务暂时不可用

#### B. 授权状态异常

继续走独立状态页：

- `revoked`
- `device_mismatch`
- `expired`
- `authenticated_grace`

原则：

> 登录页负责“进入”，状态页负责“解释例外”。

---

### 4.3 诊断信息默认折叠

保留但下沉：

- 设备 ID
- 客户端版本
- 当前 auth_state
- 最近校验时间

这些信息仅出现在：

- 折叠的“诊断信息”
- 状态页
- 管理页 / 支持排障场景

---

## 5. 推荐的登录页结构

### 5.1 页面结构

```text
Card
  ├─ 标题：登录应用
  ├─ 副标题：登录后继续使用作品工作台、任务管理和素材管理
  ├─ Form
  │   ├─ 用户名
  │   ├─ 密码
  │   ├─ 记住我
  │   └─ 登录按钮
  ├─ 辅助入口
  │   └─ 忘记密码 / 联系管理员（择一）
  ├─ 表单内错误反馈
  └─ 折叠：诊断信息
```

### 5.2 文案方向

- 标题：`登录应用`
- 副标题：`登录后继续使用作品工作台、任务管理和素材管理`
- 辅助说明：`登录会绑定到当前设备，用于保护你的应用访问权限`

避免在首屏使用：

- “本地授权”
- “机器会话”
- “工作台授权状态”
- “客户端版本”

---

## 6. “记住我”的建议语义

可以展示成普通 B/S 的“记住我”，但实现语义必须与当前系统一致。

推荐定义：

> 记住我 = 允许当前设备保留并恢复本地登录状态

而不是：

> 浏览器 cookie 式弱记忆

### 6.1 实现建议

如果短期不想改后端 contract：

- 先上 UI 占位
- 默认勾选
- 文案解释为“在当前设备上保持登录状态”
- 实际上仍复用现有 session restore / refresh 逻辑

如果要做成真实可控开关，则后续可增加：

- 前端偏好持久化
- 后端对“退出即清除 / 保持恢复”做策略分支

但这属于下一步，不是本轮阻塞项。

---

## 7. 推荐的前后端职责边界

### 前端职责

- 采集用户名/密码
- 展示普通 B/S 登录体验
- 调用本地 `/api/auth/login`
- 接收本地 session 结果
- 根据 auth_state 路由到工作台或状态页

### 本地后端职责

- 代理远端认证
- 管理 access/refresh token
- 管理 device_id 绑定
- 恢复本地 session
- 刷新 / 过期 / 撤销 / 宽限判定

### 远端认证系统职责

- 最终认证结果
- 远端账户状态
- token 签发 / 续期 / 撤销

结论：

> UI 应该尽量与普通 B/S 应用无差别；`前端 -> 本地后端 -> 远端认证` 只是 Electron 部署形态下的内部实现。

---

## 8. 可执行 PR 计划

### PR-1：登录页 IA 收口为标准 B/S 表单

**变更范围**

- `frontend/src/features/auth/LoginPage.tsx`
- 如有必要：`AuthErrorMessage.tsx`

**组件策略**

- 继续使用 Ant Design Form / Input / Input.Password / Button / Checkbox
- 不新增自定义基础表单组件
- 仅在登录域内整理结构与文案

**改动目标**

- 登录页首屏只保留标准表单结构
- 加入“记住我”复选框
- 诊断信息继续折叠
- 弱化技术实现文案

**验收标准**

- 用户首屏看起来像标准 B/S 登录页
- 不暴露 device/client/session 等实现噪音
- 表单主路径清晰，焦点顺序自然

**测试方式**

- Playwright：`e2e/login/login.spec.ts`
- 验证字段、提交、错误、折叠诊断区
- 手工验证 Tab 顺序、回车提交、加载态

---

### PR-2：登录错误反馈与状态反馈分层

**变更范围**

- `frontend/src/features/auth/LoginPage.tsx`
- `frontend/src/features/auth/authErrorHandler.ts`
- `frontend/src/features/auth/AuthErrorMessage.tsx`

**组件策略**

- 表单错误留在页面内
- toast 只保留必要成功反馈，避免重复反馈
- 不引入新的全局通知模式

**改动目标**

- 普通登录失败在登录页内展示
- “状态同步中 / 同步失败”降噪
- 避免同时出现表单错误 + message.error 双反馈

**验收标准**

- 用户能明确知道错误和当前表单有关
- 网络/服务异常可理解
- 错误反馈不重复、不抢主流程

**测试方式**

- Playwright：invalid credentials / network timeout / bootstrap error
- 检查 `.ant-message-notice` 是否不再承担失败主反馈

---

### PR-3：状态页语义与登录页职责边界收紧

**变更范围**

- `frontend/src/features/auth/AuthStatusPage.tsx`
- `frontend/src/features/auth/AuthRouteGate.tsx`

**组件策略**

- 继续使用单卡片状态页
- 文案动作导向
- 诊断信息继续折叠

**改动目标**

- 把 `revoked / device_mismatch / expired / grace` 的解释彻底留在状态页
- 登录页不再承担状态解释职责
- CTA 更符合用户下一步动作

**验收标准**

- 用户能理解“为什么不能继续”
- 每个状态页都有明确下一步
- 登录页不再混入状态机语义说明

**测试方式**

- Playwright：`auth-shell.spec.ts`、`auth-routing.spec.ts`
- 验证跳转、文案、CTA 数量、折叠诊断区

---

### PR-4：记住我语义补齐（可选，取决于是否要做真实开关）

**变更范围**

- 前端 login UI
- 如要做真实语义：`backend/api/auth.py` / `schemas.auth` / `AuthService`

**组件策略**

- 若仅 UI 收口：不改 backend contract
- 若做真实开关：扩展 login request，但不破坏既有默认行为

**改动目标**

- 明确“记住我”到底是展示性收口，还是实际控制持久化策略

**验收标准**

- 语义与真实行为一致
- 不出现 UI 承诺和系统行为不一致

**测试方式**

- 单测 / 集成测试：登录后重启恢复语义
- Playwright：勾选/不勾选的行为验证（若实现真实开关）

---

## 9. 推荐执行顺序

建议顺序：

1. PR-1
2. PR-2
3. PR-3
4. PR-4（如果这一轮要做真实“记住我”）

原因：

- 先把展示层收口
- 再降噪反馈
- 再收紧状态边界
- 最后再决定是否扩展真实行为 contract

---

## 10. 最终判断

答案是：**完全可以做成普通 B/S 登录页的观感，而且这是当前架构下的推荐方向。**

正确做法不是重写 auth，而是：

> 让用户看到标准 B/S 登录体验，把 Electron 下的特殊实现完全隐藏在系统内部。

这能同时满足：

- 用户看起来简单
- 工程实现保持稳定
- 设备绑定 / refresh / 状态机能力不丢
