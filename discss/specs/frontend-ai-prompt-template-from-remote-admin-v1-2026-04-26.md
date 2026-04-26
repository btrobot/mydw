# 前端 AI Prompt 模板（基于 Remote Admin 10 条原则）

## 目标

这份模板的目的不是让 AI “生成一个页面”，而是让 AI 按中后台前端方法来实现：

- 先做系统，再做页面
- 先做规则，再做细节
- 先做结构，再做美化

---

## 模板 1：通用后台页面实现模板

```md
请作为资深前端工程师，使用以下约束实现页面/模块：

【技术栈】
- React
- TypeScript
- Ant Design
- React Router
- React Query

【产品定位】
这是一个企业级中后台/运维控制台，不是营销站，也不是一次性 demo。
风格要 professional、restrained、trustworthy、operational。

【必须遵守的实现原则】
1. 先做系统一致性，再做单页细节
2. 先复用 AppShell / PageHeader / 状态组件，不要从零散写页面
3. 先使用 theme token，不要随意硬编码颜色、圆角、间距
4. 按页面模式实现，不要把每个页面当成全新结构
5. loading / empty / error 必须是明确状态，不要只实现正常态
6. 权限必须显式表达，不要只 disabled
7. 危险操作必须放入 danger zone，并带确认说明
8. 服务端状态、本地状态、会话状态要分层
9. 文案要专业克制，不能像 demo
10. 组件优先复用，页面只负责编排

【输出要求】
请先给出：
1. 页面属于哪种模式（dashboard / master-detail / investigation）
2. 组件拆分方案
3. 状态分层方案
4. 再输出实现代码
```

---

## 模板 2：实现 AppShell 的 prompt

```md
请实现一个企业后台前端的 AppShell，技术栈为 React + TypeScript + Ant Design + React Router。

要求：
- 整体结构为：Sidebar + Header + Content
- Sidebar 支持导航分组、当前项高亮、图标/缩写、可折叠
- Header 支持页面标题、当前用户、角色 badge、退出按钮
- Content 只承载子页面，不混入业务细节
- 所有登录后路由必须挂在 AppShell 下

设计风格要求：
- 深色侧边栏，浅色内容区
- 品牌色以克制蓝色为主
- 使用边框、层级和间距建立秩序，不依赖大阴影
- 看起来像 serious enterprise operations platform

实现要求：
- theme token 单独抽离
- router 使用 layout route
- AppShell 不要耦合某个具体业务页面
```

---

## 模板 3：实现 master-detail 页面的 prompt

```md
请实现一个标准企业后台 master-detail 页面，技术栈为 React + TypeScript + Ant Design + React Query。

页面结构必须固定为：
1. PageHeader
2. Permission notice（如适用）
3. FilterBar
4. 左侧列表/ListPane
5. 右侧详情/DetailPane
6. 详情中的编辑区
7. DangerZone（如有危险操作）

请严格按下面方式组织状态：
- 服务端状态：list query / detail query / mutation
- 本地状态：selectedId / modalOpen / draftFilters / formDraft
- 全局状态：currentUser / role / session

请补齐以下体验状态：
- loading
- empty
- error
- success feedback

权限要求：
- readonly 角色不能只 disabled，必须有明确提示文案
- 危险操作必须有说明、确认、进行中状态、成功/失败反馈

请先输出组件树，再输出代码。
```

---

## 模板 4：让 AI 先做目录结构再做代码

```md
请不要直接开始写页面代码。

先基于企业后台前端最佳实践，为这个项目设计目录结构。

约束：
- app/ 管全局骨架、router、providers、theme
- features/ 按业务域拆分
- components/ 放跨业务复用组件
- patterns/ 放 dashboard / master-detail / investigation 这类页面模式
- lib/ 放纯逻辑
- copy/ 放体验文案

然后说明：
1. 每个目录承担什么责任
2. 这个页面/模块应该放在哪里
3. 哪些内容应该抽成复用组件
4. 最后再给出代码实现
```

---

## 模板 5：让 AI 做“更像企业后台”的视觉而不是营销站

```md
请优化这个前端页面的 UI，但不要做成营销站，也不要做成花哨 dashboard。

目标风格：
- enterprise admin console
- trust & authority
- restrained
- data-dense but readable

要求：
- 通过 layout、spacing、border、typography hierarchy 提升专业感
- 通过 token 控制颜色、圆角、间距
- 减少无意义的渐变和大阴影
- 强化标题、副标题、说明文案、状态标签、危险操作区的层级
- 页面必须保持组件化和可维护性，不允许为了视觉硬堆大量重复 JSX

请先说明：
1. 你要调整哪些视觉层级
2. 哪些会沉淀为 token
3. 哪些会沉淀为复用组件
4. 再输出代码
```

---

## 模板 6：用于已有页面重构

```md
请重构这个现有前端页面，但目标不是只把代码拆小，而是把它改造成企业后台可维护结构。

重构目标：
- 保持现有功能不变
- 提升结构清晰度
- 提升状态管理清晰度
- 提升页面一致性
- 提升权限和危险操作表达

重构原则：
1. 页面只负责编排
2. 提取可复用状态组件：LoadingState / EmptyState / ErrorState
3. 提取页面区块组件：FilterBar / ListPane / DetailPane / DangerZone
4. 服务端状态与本地状态分离
5. 把体验文案从大段 JSX 中抽离

请输出：
1. 重构前主要问题
2. 重构后的组件拆分
3. 状态分层
4. 代码实现
```

---

## 最短可直接用版本

如果你懒得写很多，至少给 AI 这段：

```md
请按企业后台前端方式实现，不要按 demo 页面方式实现。

技术栈：React + TypeScript + Ant Design + React Router + React Query。

必须满足：
- 先复用 AppShell / PageHeader / 状态组件
- 使用 theme token，不要乱写样式
- 页面按 dashboard / master-detail / investigation 三种模式之一实现
- loading / empty / error 必须明确
- 权限必须显式表达，不能只 disabled
- 危险操作必须单独放入 danger zone
- 页面只负责编排，组件负责细节，hooks 负责状态和数据

请先输出组件拆分和状态分层，再输出代码。
```

---

## 一句话总结

> 给 AI 提前说清楚“产品定位、页面模式、状态分层、权限表达、复用边界”，比单纯说“做个好看的后台页面”有效得多。

