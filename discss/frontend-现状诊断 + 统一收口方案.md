# frontend-现状诊断 + 统一收口方案

## 1. 目标

本方案以以下原则为核心：

> **尽可能利用既定技术栈的组件库，而不是重复造轮子；尽可能按照技术栈最佳实践收口页面、交互、组件与代码组织。**

本文不是泛泛而谈的“前端规范”，而是基于当前 `frontend` 代码现状，对问题做客观诊断，并给出一套可以逐步落地的统一收口方案。

---

## 2. 当前技术栈事实

根据 `frontend/package.json`，当前项目已经明确使用：

- React 18
- TypeScript
- React Router
- Ant Design 5
- `@ant-design/pro-components`
- React Query
- Zustand
- Vite
- Playwright E2E

这意味着：**项目并不是没有技术栈基础，而是“已有技术栈，但尚未形成统一落地方式”。**

---

## 3. 现状诊断

## 3.1 页面骨架没有统一

当前项目至少并存三种页面骨架：

### A. `PageContainer` 路线

适用于部分创作与详情页，例如：

- `src/features/creative/pages/CreativeWorkbench.tsx`
- `src/features/creative/pages/CreativeDetail.tsx`
- `src/pages/AIClip.tsx`
- `src/pages/material/VideoDetail.tsx`
- `src/pages/product/ProductDetail.tsx`
- `src/pages/material/TopicGroupDetail.tsx`

### B. `PageHeader + Space + Card/ProTable` 路线

适用于部分管理页，例如：

- `src/pages/TaskList.tsx`
- `src/pages/product/ProductList.tsx`
- `src/pages/material/MaterialOverview.tsx`
- `src/pages/Dashboard.tsx`
- `src/pages/Account.tsx`
- `src/pages/ProfileManagement.tsx`
- `src/pages/ScheduleConfig.tsx`

### C. 手工拼装路线

典型代表：

- `src/pages/task/TaskCreate.tsx`

这类页面直接使用：

- 返回按钮
- `Title`
- 多个 `Card`
- `Tabs`
- `Form`

但没有落到统一的页面容器范式。

### 诊断结论

**页面骨架不是没有抽象，而是没有收敛到单一标准。**

这会直接导致：

- 首屏标题区结构不一致
- 操作区位置不一致
- 详情页与列表页视觉语言不一致
- AI / 新人无法判断“应该跟谁对齐”

---

## 3.2 没有充分利用 ProComponents 的既有能力

虽然项目已经依赖了 `@ant-design/pro-components`，但实际使用并不统一。

### 已经较好利用的页面

- `TaskList` 使用 `ProTable`
- `ProductList` 使用 `ProTable`
- 多个详情页使用 `ProDescriptions`
- 壳层使用 `ProLayout`

### 仍然没有充分利用的页面

- `Account.tsx` 仍使用原生 `Table`
- `TaskCreate.tsx` 使用原生 `Form + Card + Tabs` 进行复杂页面编排
- 一部分页面自己处理标题区，而不是统一容器

### 诊断结论

当前问题不是“没上组件库”，而是：

> **上了 Ant Design / ProComponents，但没有制定“哪些场景必须优先使用哪些官方能力”的项目级约束。**

于是不同页面会：

- 有的用 `ProTable`
- 有的用 `Table`
- 有的用 `PageContainer`
- 有的用自定义 `PageHeader`
- 有的自己拼卡片布局

这就是“技术栈已确定，但落地标准未冻结”。

---

## 3.3 自定义抽象存在，但复用边界不清

项目中已经存在若干抽象组件，例如：

- `PageHeader`
- `InlineNotice`
- `PageLoading`
- `PageError`
- `PageEmpty`
- `BatchDeleteButton`
- `ConnectionModal`
- `StatusBadge`
- `MaterialBasket`
- `ProductQuickImport`
- `MaterialSelectModal`

其中有两类情况：

### 第一类：已经形成稳定价值

例如：

- `PageHeader`
- `InlineNotice`
- `PageLoading / PageError / PageEmpty`

这些组件已经在多个页面复用，说明项目实际上已经在形成自己的页面语言。

### 第二类：已经抽象出来，但没有形成真正标准入口

例如：

- `MaterialBasket` 组件存在，但当前未成为任务创建页的标准承载组件
- 任务创建页仍然自己维护 basket 状态、UI、删除逻辑和 tab 结构

### 诊断结论

问题不是“没有组件”，而是：

> **抽象是否成为项目标准复用入口，并没有被流程和规范强制下来。**

---

## 3.4 架构处于迁移中间态

当前目录同时存在：

- `src/features/creative/...`
- `src/features/auth/...`
- `src/pages/...`
- `src/hooks/...`
- `src/components/...`

这说明项目已经开始向 feature-first 演进，但仍保留大量旧式 page-first / global-hooks 结构。

### 具体表现

- `creative` 相关模块组织较完整
- `task / material / product / account` 仍偏页面堆叠
- hooks 同时承担通用能力与业务能力

### 诊断结论

这类“半迁移状态”在中途项目很常见，但如果没有明确收口策略，后续只会继续分裂出更多写法。

---

## 3.5 页面文件偏大，页面承担了过多职责

部分页面已经明显超出“页面容器层”的合理大小，例如：

- `CreativeDetail.tsx`
- `TaskList.tsx`
- `Account.tsx`
- `TaskCreate.tsx`

这意味着页面文件不仅在负责：

- 页面结构
- 交互状态
- 请求拼装
- 业务语义
- 列表列定义
- 反馈逻辑

还在承担局部业务编排。

### 诊断结论

这会造成两个问题：

1. AI / 新人更容易在页面里继续堆代码  
2. 组件库最佳实践难以发挥，因为页面已经变成“超级控制器”

---

## 3.6 视觉系统入口存在，但约束不足

项目已有：

- `src/app/theme/tokens.ts`
- `ConfigProvider theme={appTheme}`

但目前 token 很薄，主要定义了：

- 主色
- 圆角
- 布局背景
- 表头背景

与此同时，页面内联样式使用仍然很多。

### 诊断结论

这说明：

> **主题系统存在，但尚未成为页面视觉一致性的主约束。**

当前更多依赖页面开发者自行决定样式细节。

---

## 3.7 工程守卫偏弱

当前具备：

- TypeScript 类型检查
- Playwright E2E

但缺少：

- `lint` 脚本
- ESLint 约束
- 针对页面结构和组件使用的一致性规则

### 诊断结论

当前工程体系更擅长发现：

- 类型错误
- 功能回归

但不擅长阻止：

- 风格漂移
- 组件乱用
- 页面骨架继续分裂

---

## 4. 核心问题归纳

当前 frontend 的核心问题，不是“代码不能运行”，而是：

### 4.1 技术栈已经选定，但没有形成项目级“默认实现路线”

也就是说，大家知道项目用了：

- Ant Design
- ProComponents

但不知道：

- 列表页默认该用什么
- 详情页默认该用什么
- 创建页默认该用什么
- 页面头部默认该用什么
- 什么情况下允许不用官方能力

### 4.2 自定义组件与官方组件的边界没有制度化

导致：

- 有的页面走官方标准
- 有的页面走项目自定义
- 有的页面走临时组合

### 4.3 缺少“单一真相源”

AI / 新人进入项目后，不知道应该以谁为准：

- 以 `PageContainer` 为准？
- 以 `PageHeader` 为准？
- 以 `ProTable` 为准？
- 以 `Table` 为准？
- 以 `creative` 目录的写法为准？
- 还是以 `pages/` 的老页面为准？

这才是“跑偏”的根本原因。

---

## 5. 统一收口总原则

在本项目中，建议采用以下总原则：

### 原则 1：优先使用技术栈官方能力

优先级如下：

1. **Ant Design / ProComponents 官方组件**
2. **项目已沉淀的通用页面组件**
3. **业务复合组件**
4. **最后才允许新增自定义基础组件**

### 原则 2：先统一页面骨架，再统一交互与视觉细节

当前最该先收的是：

- 列表页骨架
- 详情页骨架
- 创建 / 编辑页骨架

### 原则 3：页面容器只做编排，不做一切

页面层要逐步收缩为：

- 布局编排
- 路由参数
- 页面级状态协调

而不是继续承载：

- 大量 UI 细节
- 大量表格列细节
- 复杂业务计算
- 多重局部组件行为

### 原则 4：允许保留项目自定义抽象，但必须明确它和官方组件的关系

不是说一律不要自定义组件，而是要明确：

- `PageHeader` 是不是要继续存在
- 如果存在，它是 `PageContainer` 的补充，还是替代？
- 哪些页面必须走 `PageContainer`
- 哪些页面允许走 `PageHeader`

---

## 6. 推荐的收口标准

## 6.1 页面骨架标准

建议统一成以下标准：

### A. 管理型列表页

默认结构：

- `PageContainer`
- 头部说明 / 副标题
- `InlineNotice`（可选）
- `ProTable`

适用页面：

- `TaskList`
- `ProductList`
- `VideoList`
- `TopicList`
- `TopicGroupList`
- `CopywritingList`
- `CoverList`
- `AudioList`
- `Account`（建议迁移）

### B. 详情页

默认结构：

- `PageContainer`
- `ProDescriptions`
- `Tabs` / `ProTable` / `Card` 作为详情分区

适用页面：

- `ProductDetail`
- `VideoDetail`
- `TopicGroupDetail`
- `CreativeDetail`

### C. 创建 / 编辑 / 工作流页

默认结构：

- `PageContainer`
- 页面说明区
- `Card` 分区
- 表单区优先统一使用 Pro 系表单能力，或明确约定原生 `Form` 的使用边界

适用页面：

- `TaskCreate`
- `AIClip`
- `CreativeWorkbench`

### 结论

建议项目把：

> **`PageContainer` 定义为页面级第一容器标准**

而把 `PageHeader` 降级为：

> **仅在特殊页面或局部场景下使用的辅助头部组件**

否则两者并存会长期制造分裂。

---

## 6.2 列表组件标准

建议统一：

- 后台管理型列表页：**优先 `ProTable`**
- 原生 `Table` 只允许在以下场景使用：
  - 纯局部嵌入表格
  - 复杂布局下的子表格
  - `ProTable` 明确不适配的特例

### 直接建议

`Account.tsx` 应作为重点治理对象之一：

- 从原生 `Table` 迁移到统一的 `ProTable` 范式
- 将搜索、筛选、批量操作、状态提示全部纳入统一结构

---

## 6.3 头部与页面说明标准

建议：

- 页面第一层标题统一由 `PageContainer` 承担
- `InlineNotice` 继续保留，作为统一的信息说明组件
- 若确有特殊头部布局需求，可在 `PageContainer` 内再嵌套项目级头部辅助组件

也就是说：

- **页面容器标准统一**
- **说明组件可以自定义**

不要反过来让自定义头部成为全项目一级页面容器替代品。

---

## 6.4 组件复用标准

组件分层建议统一为：

### 基础层

直接来自：

- `antd`
- `@ant-design/pro-components`

### 页面通用层

例如：

- `InlineNotice`
- `PageLoading`
- `PageError`
- `PageEmpty`

### 业务复合层

例如：

- `ConnectionModal`
- `ProductQuickImport`
- `MaterialSelectModal`
- `StatusBadge`

### 结论

像 `MaterialBasket` 这种组件，必须明确：

- 是保留并真正成为标准入口
- 还是删除，避免“有组件但页面不用”

**项目里最糟糕的状态不是没有抽象，而是存在失效抽象。**

---

## 6.5 架构组织标准

建议未来逐步向 feature-first 收口，但不要一次性大搬家。

### 目标形态

建议逐步形成：

- `features/auth`
- `features/creative`
- `features/task`
- `features/material`
- `features/product`
- `features/account`

其中每个 feature 内再分：

- `pages`
- `components`
- `hooks`
- `api`
- `types`
- `view-models`（如确有需要）

### 原则

不是为了“目录好看”，而是为了让：

- 页面
- 组件
- hooks
- 类型
- 业务语义

按业务域归位，减少全局漂移。

---

## 7. 分阶段治理方案

## 第一阶段：先冻结标准，不急着全量改

先补齐文档与入口，而不是直接大面积重构。

应先补的文档：

1. `前端页面骨架规范.md`
2. `列表页实现规范.md`
3. `详情页实现规范.md`
4. `创建/编辑页实现规范.md`
5. `组件复用边界规范.md`

这些属于跨项目前端规范，建议放在：

- `discss/specs/`

---

## 第二阶段：选出标准样板页

建议从现有页面中选出“最接近目标形态”的样板页。

### 可优先作为样板的候选

- 列表页样板：`TaskList` / `ProductList`
- 详情页样板：`ProductDetail`
- PageContainer 路线样板：`AIClip` / `CreativeWorkbench`

### 需要重点治理的页面

- `Account`
- `TaskCreate`
- `MaterialOverview`

原因：

- 风格独立性较强
- 容易成为新人模仿对象
- 一旦不收口，后续会持续复制问题

---

## 第三阶段：按页面类型迁移，不按目录迁移

正确的收口顺序不是“先改整个模块”，而是：

### Step 1：统一列表页

优先完成：

- `ProTable` 范式统一
- 搜索区统一
- 批量操作统一
- 页面标题与说明区统一

### Step 2：统一详情页

优先完成：

- `PageContainer + ProDescriptions`
- 分区方式统一
- 返回动作统一

### Step 3：统一创建 / 编辑页

优先完成：

- 首屏结构
- 卡片分区
- 表单组织
- 操作按钮位置

---

## 第四阶段：删除失效抽象

治理中要定期做两类动作：

### 保留并升级

对真正有复用价值的组件：

- 补文档
- 补示例
- 补适用边界

### 删除

对没有被采用、或与新标准冲突的抽象：

- 删除
- 避免继续误导 AI / 新人

---

## 8. AGENTS.md 入口建议

AGENTS.md 不应该堆满所有前端规范细节，而应该作为统一入口。

建议在 AGENTS.md 中明确增加一段“前端实现入口规则”：

### 建议入口内容

- 开始前端页面开发前，必须先读取：
  - `discss/specs/前端页面骨架规范.md`
  - `discss/specs/列表页实现规范.md`
  - `discss/specs/详情页实现规范.md`
  - `discss/specs/组件复用边界规范.md`
- 默认优先使用：
  - `PageContainer`
  - `ProTable`
  - `ProDescriptions`
  - Ant Design / ProComponents 官方能力
- 不得新增自定义基础组件替代官方组件能力，除非已有 ADR 或明确例外说明
- 遇到现有页面风格冲突时，以最新规范文档为准，而不是机械模仿邻近文件

### 核心作用

让 AI / 新人知道：

> **AGENTS.md 是入口，规范文档是标准本体。**

---

## 9. 对当前项目的具体判断

如果只说一句话：

> **这个 frontend 当前最大的问题不是缺技术栈，而是缺“以技术栈最佳实践为中心的单一实现标准”。**

因此后续最重要的，不是继续“自由演化”，而是：

1. 先明确官方组件优先级
2. 再明确页面骨架标准
3. 再明确自定义组件边界
4. 最后把这些挂进 AGENTS.md 入口和文档系统

---

## 10. 最终建议

对这个项目，建议采用以下收口立场：

### 10.1 不再鼓励“就地自由写页面”

后续新增页面必须明确归类：

- 列表页
- 详情页
- 创建/编辑页
- 工作流页

每一类都要有默认骨架。

### 10.2 不再把自定义抽象放在官方组件之前

正确顺序必须是：

**官方组件优先 → 项目通用组件补充 → 业务组件组合**

### 10.3 不再允许“同类页面多套实现”

例如列表页：

- 不应再同时出现多个标准
- 应形成明确的默认方案

### 10.4 收口目标不是“全部重写”

而是：

- 先立标准
- 再选样板
- 再分类迁移
- 再删失效抽象

这是中途项目最可持续的治理方式。

---

## 11. 建议的后续文档

建议紧接着补以下文档：

1. `discss/specs/前端页面骨架规范.md`
2. `discss/specs/列表页实现规范.md`
3. `discss/specs/详情页实现规范.md`
4. `discss/specs/创建编辑页实现规范.md`
5. `discss/specs/组件复用边界规范.md`
6. `discss/specs/AGENTS-前端入口扩展规范.md`

---

## 12. 一句话总结

当前项目真正需要的，不是更多“前端自由发挥”，而是：

> **以 Ant Design / ProComponents 最佳实践为主轴，建立单一页面骨架标准、单一组件优先级规则、单一文档入口。**

这样 AI / 新人进入项目后，才不会再因为“看谁都像标准”而继续跑偏。

