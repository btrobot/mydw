# Ant Design Pro 最佳实践复用分析

日期：2026-04-23

## 结论摘要

当前项目不是“没有使用 Ant Design Pro / ProComponents”，而是“已经使用了 `PageContainer`、`ProTable` 等核心能力，但还没有充分复用 ADP 在应用 Shell、信息展示、标准表单容器、指标卡片和统一 UI 体系上的便利机制”。

建议方向不是迁移到完整 Umi / Ant Design Pro 脚手架，而是继续保持当前 Vite + React Router + HashRouter + Electron 的工程形态，在现有依赖 `@ant-design/pro-components` 基础上渐进吸收 ADP 能力。

最重要的边界是：不要为了“更 ProTable 原生”而破坏 Workbench 已经收敛好的状态模型。Workbench 的 canonical query state 仍应由 URL 和父组件掌控，ProTable 只负责表格展示、搜索表单壳、toolbar 和分页交互。

## 当前 ADP 使用现状

### 已经使用较好的部分

项目已经使用了以下 ProComponents：

- `PageContainer`
  - `CreativeWorkbench`
  - `CreativeDetail`
  - `AIClip`
  - 素材 / 商品详情页
- `ProTable`
  - Workbench 表格
  - 素材列表
  - 商品列表
  - 任务列表
- `ProDescriptions`
  - 部分素材 / 商品详情页
- `ModalForm`
  - 商品详情编辑弹窗

这说明项目已经在采用 ADP 的页面容器和数据表格体系。

### 复用不足的部分

以下 ADP / ProComponents 能力当前复用较少：

- `ProLayout`
  - 目前仍是自写 `Layout/Header/Sider/Menu`
  - 文件：`frontend/src/components/Layout.tsx`
- `ProCard` / `StatisticCard`
  - 当前大量区域仍是 `Card + Row + Col + Space + Statistic` 手写组合
- `DrawerForm`
  - 审核抽屉 `CheckDrawer` 目前是 `Drawer + Form + Button` 手写
- `ProDescriptions`
  - `CreativeDetail` 内大量只读信息仍使用 AntD `Descriptions`
- `StepsForm`
  - 任务创建如果属于多步骤流程，可以评估
- `ProList`
  - 暂无强需求，可作为移动端/卡片流候选

## 核心原则

### 1. ADP 管壳，领域代码管业务状态

建议采用：

> ADP / ProComponents 负责 Shell、页面容器、列表交互、只读信息展示、标准表单容器、指标卡片和 UI 规范；业务状态、URL 语义、诊断规则和 view-model 继续留在领域代码里。

这与当前 Workbench / Detail 的重构方向是一致的。

### 2. 不要回退 Workbench 的 canonical state 设计

Workbench 最近已经收敛出一个关键原则：

> URL 是 canonical query state；父组件是唯一状态源；ProTable 是受控展示组件。

因此 Workbench 不适合让 `ProTable.request` 重新接管搜索、筛选、排序和分页。当前的模式更合适：

- 父组件解析 URL
- 父组件构建 query state
- 父组件调用 `useCreatives`
- 表格接收 `dataSource`、`loading`、`pagination`
- 表格事件回传给父组件
- 父组件再写回 URL

普通素材列表可以使用 ProTable-native `request` 模式，但 Workbench 应继续 controlled ProTable 模式。

### 3. 渐进替换，不做大爆炸迁移

当前项目包含 Electron 构建、HashRouter、React Query、认证壳、后端 API 生成链路。为了追求“更正宗 ADP”而迁移完整 Umi 脚手架，短期收益不高，风险较大。

推荐是围绕现有工程渐进吸收 ProComponents：

1. Shell 先试点 `ProLayout`
2. 详情只读展示迁移 `ProDescriptions`
3. 抽屉表单迁移 `DrawerForm`
4. 指标卡片再评估 `StatisticCard`
5. 多步骤任务创建再评估 `StepsForm`

## 重点领域分析

### 1. Layout：优先评估 ProLayout

当前 `frontend/src/components/Layout.tsx` 自行维护了：

- Header
- Sider
- Menu
- collapsed 状态
- breakpoint 行为
- selectedKeys
- openKeys
- 菜单点击跳转
- `AuthSessionHeader` 挂载

这些正是 `ProLayout` 擅长提供的能力。

建议目标不是迁移工程框架，而是：

> 保留 Vite + React Router + HashRouter，只将自研 Shell 逐步替换为 ProLayout。

预期收益：

- 菜单配置集中
- 页面头部、侧边栏、面包屑行为更接近 ADP
- 响应式折叠逻辑减少自写代码
- 后续权限、菜单隐藏、页面标题和 breadcrumb 更容易标准化
- `AuthSessionHeader` 可以作为 header right content 接入

主要风险：

- `/creative/:id` 仍需高亮 Workbench 菜单
- `HashRouter` 下菜单跳转需要回归
- 移动端 collapsed 行为不能退化
- 认证头部不能丢
- 当前菜单分组的点击行为需要保持

因此 `ProLayout` 应该作为独立 Slice，而不是混在 Workbench / Detail 业务重构中。

### 2. PageContainer：建立统一页面规范

项目已经广泛使用 `PageContainer`，下一步应统一使用约定：

- 列表页：
  - `title`
  - `subTitle`
  - `extra`
  - 主要操作放右上角
- 详情页：
  - `title`
  - `onBack`
  - `tags`
  - `extra`
- 诊断页 / 诊断抽屉入口：
  - 刷新、打开诊断、跳转任务等动作放在一致位置

同时应评估当前 `ListPageLayout.tsx` 的必要性。它现在只是手写 `Card + Row + Col` 包装，如果页面已经使用 `PageContainer + ProTable toolbar/search`，该 wrapper 可能会逐步变得冗余。

### 3. ProTable：区分 ProTable-native 与 controlled ProTable

#### 普通列表页：推荐 ProTable-native

适合对象：

- 素材列表
- 商品列表
- 相对独立的任务列表

可充分使用：

- `request`
- `columns`
- `valueEnum`
- `search`
- `toolBarRender`
- `actionRef`
- `rowSelection`
- `tableAlertRender`
- `columnsState`

#### Workbench：继续 controlled ProTable

适合对象：

- Workbench

原因：

- URL 是业务可恢复状态
- preset 是业务概念
- diagnostics drawer 也具有 URL 语义
- 搜索、筛选、排序、分页都需要可复现

因此 Workbench 应继续：

- 父组件保留 parse/build URL 逻辑
- 父组件保留 query state
- `ProTable` 使用 `dataSource`
- `pagination` 受控
- `onSubmit/onReset/onChange/onSortChange` 回写 URL

这不是“不符合 ADP”，而是合理使用 ProComponents 的受控模式。

### 4. CreativeDetail：优先迁移只读信息到 ProDescriptions

`CreativeDetail` 里大量只读信息仍使用 AntD `Descriptions`。这些区域适合渐进迁移到 `ProDescriptions`：

- 作品基础信息
- 当前版本结果
- 发布包冻结值
- 发布侧能力与调度诊断
- package / task 关系
- 候选项证据摘要

预期收益：

- 字段配置化
- 空值展示更统一
- label/value 样式更一致
- 与素材 / 商品详情页的实现靠拢

但不建议短期强行迁移复杂 authoring 表单。当前 authoring 区域包含 `Form.List`、动态素材项、嵌套状态和复杂业务联动，继续使用 AntD `Form` 更稳妥。

### 5. DrawerForm / ModalForm：先从 CheckDrawer 切入

`CheckDrawer` 当前是典型的：

- `Drawer`
- `Form`
- 自定义提交按钮
- mutation loading
- 成功后关闭

这类“抽屉内提交表单”很适合迁移为 `DrawerForm`。

迁移时必须保持：

- 审核提交语义不变
- approve / rework / reject 三种 mutation 不变
- loading 行为不变
- close/reset 行为不变
- rework 条件字段不变
- 现有测试不退化

不建议一上来全量迁移所有表单。先选 `CheckDrawer` 这种容器型表单，收益更明确。

### 6. ProCard / StatisticCard：只替换真正的指标和布局样板

适合候选：

- Workbench summary
- Dashboard 指标区
- 运行态统计卡片
- 发布诊断中的摘要指标

收益：

- 指标卡片风格统一
- 减少 `Card + Statistic + Space` 样板
- 多指标组合更容易保持一致布局

不建议替换：

- 高度定制的行动建议面板
- 内容很简单的单个 Card
- 替换后代码反而更长的区域

`ProCard` / `StatisticCard` 应该是减少布局样板的工具，而不是全项目统一换皮。

### 7. StepsForm：仅在 TaskCreate 是明确多步骤流程时使用

如果任务创建天然是：

1. 选择任务类型
2. 配置素材 / 参数
3. 确认执行
4. 提交

则可以评估 `StepsForm`。

如果当前任务创建只是一个普通表单，不建议为了 ADP 化强行拆步骤。

### 8. ProList：暂不优先

`ProList` 适合：

- 移动端卡片流
- 版本记录
- 候选项记录
- AIClip 结果流
- 非强表格结构的数据列表

但当前 Workbench 仍是管理型表格场景，`ProTable` 更合适。`ProList` 可以作为后续移动端或卡片视图候选，不应作为近期主线。

## UI 系统与交互规范

当前 `App.tsx` 已使用 `ConfigProvider` 和 AntD `App`，这是好的基础。后续可以进一步收敛：

- 页面背景
- Card 圆角 / padding
- Table density
- Form label 宽度
- Button 主操作位置
- Empty / Result / Alert 使用规范
- Drawer 宽度规则
- 页面间距规则
- message / modal / notification 使用规范

目标是减少页面内到处散落的：

```tsx
style={{ marginBottom: 16 }}
style={{ width: '100%' }}
styles={{ body: { padding: ... } }}
```

但这也应该渐进完成，避免一次性扫全项目造成大 diff。

## 不建议做的事

### 不建议迁移完整 Umi / Ant Design Pro 脚手架

当前项目是：

- Vite
- React Router
- HashRouter
- Electron 构建
- React Query
- Zustand
- OpenAPI 生成链路

完整迁移 Umi 会牵动构建、路由、认证、Electron、测试链路，短期风险明显大于收益。

### 不建议让 ProTable 接管 Workbench URL 状态

这会破坏 Workbench 最近刚收敛好的设计。

Workbench 的 URL 状态、preset 语义、diagnostics drawer 语义都应继续由父组件掌控。

### 不建议全量把 Form 换成 ProForm

复杂动态表单不一定更适合 ProForm。应优先迁移 `DrawerForm` / `ModalForm` 这类容器型表单。

### 不建议所有 Card 都换成 ProCard

只有在能减少样板、统一布局、提升一致性时才换。

## 推荐重构路线

### Slice 1：ADP 使用规范文档

目标：

- 建立项目级 ADP 使用约定
- 明确哪些页面用 ProTable-native
- 明确哪些页面用 controlled ProTable
- 明确 PageContainer、DrawerForm、ProDescriptions、ProCard 的使用边界

验收：

- 文档落盘
- 后续 PR 可引用该规范
- 不改业务行为

### Slice 2：ProLayout 试点

目标：

- 将自研 Shell 逐步迁移为 ProLayout
- 保留 Vite / React Router / HashRouter
- 保留认证头部

验收：

- 菜单选中正确
- `/creative/:id` 仍高亮 Workbench
- HashRouter 跳转正常
- `AuthSessionHeader` 正常
- 移动端折叠行为正常

### Slice 3：CreativeDetail 只读信息 ProDescriptions 化

目标：

- 只迁移只读展示
- 不碰 authoring 行为
- 不改 URL / drawer / diagnostics 语义

验收：

- 作品基础信息、版本结果、发布诊断等只读区展示一致
- 空值展示一致
- 现有测试通过

### Slice 4：CheckDrawer 迁移 DrawerForm

目标：

- 用 `DrawerForm` 替代手写 `Drawer + Form + extra submit`
- 保持审核行为不变

验收：

- approve / rework / reject 正常
- rework 条件字段正常
- loading / close / reset 行为正常
- 测试通过

### Slice 5：Workbench / Dashboard 指标卡片评估 StatisticCard

目标：

- 只替换真正的指标卡片
- 保留行动建议面板的定制结构

验收：

- 指标展示一致
- 布局更统一
- 代码没有明显变复杂

### Slice 6：TaskCreate 评估 StepsForm

目标：

- 判断任务创建是否天然多步骤
- 如果是，再迁移为 `StepsForm`
- 如果不是，保留普通表单

验收：

- 用户创建任务路径不变
- 表单校验不退化
- 提交流程不变

## 客观评判

当前项目的 ADP 使用处于“中度采用”状态：

- 列表和页面容器已经用上了 ProComponents
- 应用 Shell 还没有用 ProLayout
- 详情页只读展示没有充分用 ProDescriptions
- 表单容器没有充分使用 DrawerForm / ModalForm
- 指标卡片和布局系统仍较多手写组合

最值得优先补齐的是 `ProLayout`，因为它能减少最多自研 Shell 样板，并统一菜单、头部、响应式和页面框架。其次是 `ProDescriptions` 和 `DrawerForm`，它们能以较小风险提升详情页和表单交互的一致性。

但 Workbench 的状态模型不应倒退。对这个项目来说，ADP 最佳实践不是“所有东西都交给 ProTable request”，而是“让 ADP 提供稳定 UI 和交互壳，让领域状态继续保持清晰、可测试、可恢复”。

## 执行收口状态（2026-04-24）

基于本分析形成的 ADP UI System Adoption PRD 已阶段性完成。总收口文档见：

- `discss/adp-ui-system-adoption-closeout-2026-04-24.md`
- `.omx/plans/prd-adp-ui-system-adoption-2026-04-23.md`

### 已落地

- `ProLayout` 已作为 parity-gated pilot 接入应用 shell。
- `PageContainer / ProTable` 的使用边界已明确，未对列表页做无收益包裹。
- `CreativeDetail` 的只读信息区已迁移到 `ProDescriptions`。
- `CheckDrawer` 已从手写 `Drawer + Form` 迁移为 `DrawerForm`。

### 明确 no-op

- `WorkbenchSummaryCard / Dashboard` 暂不迁移 `StatisticCard / ProCard`：替换会增加 wrapper、`colSpan`、`ghost` 等决策，净收益不足。
- `TaskCreate` 暂不迁移 `StepsForm`：当前是高级单页配置台，不是天然线性 wizard；迁移会增加跨步骤状态同步和校验时机复杂度。

### 更新后的客观结论

项目已从“中度采用”推进到“有边界的系统性采用”：Shell、页面容器、只读展示、标准抽屉表单已经纳入 ADP / ProComponents 体系；复杂业务状态仍由领域代码负责。这个结果比“全面 Pro 化”更适合当前 Vite + React Router + HashRouter + Electron 架构。

## 参考资料

- Ant Design Pro Layout: https://pro.ant.design/docs/layout/
- ProComponents Layout: https://procomponents.ant.design/en-US/components/layout
- ProComponents Table: https://procomponents.ant.design/en-US/components/table
- ProComponents Form: https://procomponents.ant.design/en-US/components/form
- ProComponents Descriptions: https://procomponents.ant.design/en-US/components/descriptions
- Ant Design Theme: https://ant.design/docs/react/customize-theme
