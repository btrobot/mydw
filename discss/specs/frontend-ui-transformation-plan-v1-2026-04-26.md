# 当前项目 UI 改造计划 v1（基于 remote admin 提炼）

> 日期：2026-04-26  
> 适用范围：`frontend/`  
> 依据文件：`frontend/src/App.tsx`、`frontend/src/main.tsx`、`frontend/src/components/Layout.tsx`、`frontend/src/providers/QueryProvider.tsx`、`frontend/src/pages/*`、`frontend/src/features/auth/*`、`frontend/src/features/creative/*`、`remote/remote-admin/src/app/*`、`remote/remote-admin/src/routes/router.tsx`

---

## 1. 这次改造要解决什么

当前项目的 UI 问题，不是“少几个组件”这么简单，而是：

1. **结构混杂**：`App.tsx` 同时承担 theme、provider、router、page wiring。
2. **页面标准不统一**：不同页面的标题区、卡片层级、状态反馈、操作区表达不一致。
3. **业务层 / 壳层 / 视觉层耦合**：`src/pages`、`src/components`、`src/hooks`、`src/services` 仍然有明显旧结构痕迹。
4. **产品感不稳定**：页面能用，但“像一个完成品”的稳定感不够。

一句话结论：

> **这次应该做的是“前端产品化收口工程”，而不是“零散修美化”。**

---

## 2. 核心判断

### 2.1 文件级迁移不能直接让 UI 变漂亮

目录重组能解决的是：

- 结构清晰
- 复用边界清晰
- 后续 UI 系统可落地

但真正让 UI 变漂亮的，是下面这些系统升级：

- theme token
- AppShell
- 页面模板
- 统一的 loading / empty / error / success 四态
- 统一的 page header / section card / filter bar
- 文案体系
- 信息层级

所以这次计划采用：

> **双轨推进：先做最小结构收口，再做 UI 系统升级。**

### 2.2 不建议一上来全量重写

不建议：

1. 一次性重写全部页面
2. 一边做 UI，一边顺手大改数据模型
3. 没有优先级，所有页面一起动
4. 先碰最复杂的 `CreativeDetail.tsx`

原因：

- 当前 `features/creative` 已经是较成熟的结构样板，应该复用其思路；
- `CreativeDetail.tsx`（2228 行）复杂度最高，适合作为后续能力沉淀对象，不适合作为第一批 UI 改造试点；
- 当前最该优先拿下的是“全局壳 + 高流量页面 + 通用状态组件”。

---

## 3. 目标与非目标

## 3.1 目标

本轮改造目标：

1. 建立一套像 `remote admin` 一样稳定的 **前端壳层 + theme + 页面模板**。
2. 让高频页面先获得一致、可复用、产品感稳定的 UI 表达。
3. 让后续新页面都能按同一套前端规则生长，而不是继续散着写。

## 3.2 非目标

本轮不做：

1. 不做后端接口协议重设计
2. 不做 Electron 架构重写
3. 不做所有页面一次性视觉翻新
4. 不把 `CreativeDetail` 作为第一批主战场

---

## 4. 改造总策略

采用 5 个阶段推进：

1. **Phase 0：基线与范围冻结**
2. **Phase 1：AppShell / Theme / Router 基础层收口**
3. **Phase 2：共享 UI 骨架与四态组件建立**
4. **Phase 3：高优先页面试点改造**
5. **Phase 4：领域推广与一致性收尾**

推荐优先级顺序：

1. AppShell
2. Dashboard
3. Account
4. TaskList
5. MaterialOverview / VideoList / ProductList
6. Settings / Auth Admin / Profile / Schedule
7. AIClip
8. CreativeWorkbench
9. CreativeDetail（最后单独立项）

---

## 5. 具体执行计划

## Phase 0：基线与范围冻结

### 目标

先把“什么算变漂亮”说清楚，避免边做边漂。

### 涉及文件

- `frontend/src/App.tsx`
- `frontend/src/components/Layout.tsx`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/Account.tsx`
- `frontend/src/pages/TaskList.tsx`
- `frontend/src/pages/material/MaterialOverview.tsx`
- `frontend/src/pages/material/VideoList.tsx`
- `frontend/src/pages/product/ProductList.tsx`
- `frontend/src/features/creative/pages/CreativeWorkbench.tsx`

### 动作

1. 选定第一批改造页面：`Dashboard`、`Account`、`TaskList`、`MaterialOverview`。
2. 为这些页面建立“改造前截图基线”。
3. 盘点现有壳层与页面共性问题：
   - 头部样式不统一
   - 卡片间距不统一
   - 文案语气不统一
   - loading / empty / error 表达不统一
4. 冻结第一批不动范围：
   - `frontend/electron/*`
   - `frontend/e2e/*` 仅补 smoke，不先重写
   - `features/creative/pages/CreativeDetail.tsx`

### 验收标准

1. 有一份明确的首批页面名单。
2. 有一份“当前 UI 问题基线清单”。
3. 团队对“先壳层、后页面”的顺序达成一致。

---

## Phase 1：AppShell / Theme / Router 基础层收口

### 目标

把当前分散在 `App.tsx`、`Layout.tsx` 的壳层逻辑，收成类似 remote admin 的 `app/` 基础层。

### 当前问题

- `frontend/src/App.tsx` 过厚，承担：
  - theme
  - providers
  - router
  - page imports
  - route wiring
- `frontend/src/components/Layout.tsx` 是壳层组件，但仍放在通用 `components/` 下。
- theme 只是内联常量，不是可演化系统。

### 推荐目标结构

```text
frontend/src/
  app/
    AppProviders.tsx
    router.tsx
    theme/
      index.ts
      tokens.ts
    shell/
      AppShell.tsx
      navigation.tsx
  components/
    ui/
    feedback/
  features/
  lib/
```

### 预计文件动作

1. `frontend/src/App.tsx`
   - 收薄为应用入口壳
   - 不再直接堆满业务 route
2. `frontend/src/components/Layout.tsx`
   - 迁移为 `frontend/src/app/shell/AppShell.tsx`
3. 新建 `frontend/src/app/router.tsx`
   - 承接 route 定义
4. 新建 `frontend/src/app/AppProviders.tsx`
   - 收纳 `QueryProvider`、`AuthBootstrapProvider`、`ConfigProvider`、`AntApp`
5. 新建 `frontend/src/app/theme/tokens.ts`
6. 新建 `frontend/src/app/theme/index.ts`

### 设计原则

1. AppShell 负责壳，不负责业务判断细节。
2. router 负责路由，不负责视觉结构。
3. provider 负责上下文，不把页面装配逻辑混进去。
4. theme token 先小而稳，不追求第一步就做复杂 design system。

### 验收标准

1. `App.tsx` 明显瘦身，只保留入口编排职责。
2. `AppShell` 成为显式的 `app/shell` 资产。
3. theme 不再以内联对象散落在入口文件。
4. route 定义迁移到独立文件，页面接入路径更清晰。

---

## Phase 2：共享 UI 骨架与四态组件建立

### 目标

把“页面看起来不统一”的核心问题，先用一套共享骨架压住。

### 新增共享资产建议

```text
frontend/src/components/
  ui/
    PageHeader.tsx
    PageSectionCard.tsx
    PageToolbar.tsx
    StatCard.tsx
    FilterBar.tsx
    DangerZoneCard.tsx
  feedback/
    PageLoading.tsx
    PageEmpty.tsx
    PageError.tsx
    InlineNotice.tsx
```

### 适用页面

- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/Account.tsx`
- `frontend/src/pages/TaskList.tsx`
- `frontend/src/pages/material/MaterialOverview.tsx`
- `frontend/src/pages/material/VideoList.tsx`
- `frontend/src/pages/product/ProductList.tsx`
- `frontend/src/pages/Settings.tsx`

### 动作

1. 统一页面头部模型：
   - 标题
   - 副标题
   - 主要操作
   - 次级操作
2. 统一卡片模型：
   - 默认间距
   - 默认圆角
   - 默认边框与阴影策略
3. 统一反馈状态：
   - 页面加载
   - 空态
   - 错误态
   - 局部提示
4. 统一危险操作表达：
   - 删除
   - 注销
   - 会话踢出
   - 批量操作

### 特别说明

这一阶段是“变漂亮”的真正起点。  
如果没有这一层，后面页面改造很容易重新散掉。

### 验收标准

1. 首批改造页面都使用统一 `PageHeader`。
2. loading / empty / error / notice 不再各写各的。
3. 相同类型操作（筛选、批量操作、危险操作）外观和位置一致。

---

## Phase 3：高优先页面试点改造

### 目标

先拿下最影响整体观感的页面，形成“看得见的改造结果”。

### 批次 1：Dashboard

#### 文件

- `frontend/src/pages/Dashboard.tsx`

#### 目标

- 从“信息堆叠页”变成“概览页”
- 只保留关键指标、系统状态、快捷入口

#### 改造重点

1. 顶部统一页头
2. 核心指标卡统一风格
3. 次要说明信息下沉
4. 避免首屏出现解释型大段文案

### 批次 2：Account

#### 文件

- `frontend/src/pages/Account.tsx`

#### 目标

- 从“功能杂糅页”变成“账户与权限中心”

#### 改造重点

1. 账户信息卡
2. 会话与安全卡
3. 危险操作区单独收口
4. 主要操作聚焦，不让按钮抢层级

### 批次 3：TaskList

#### 文件

- `frontend/src/pages/TaskList.tsx`
- `frontend/src/pages/task/taskPresentation.ts`
- `frontend/src/pages/task/taskSemantics.ts`

#### 目标

- 从“大型表格实现页”变成“任务运营工作台”

#### 改造重点

1. 筛选条收口成统一 `FilterBar`
2. 表格上方加清晰页面头部与摘要
3. 批量操作区样式统一
4. 空态与无结果态分开表达

### 批次 4：Material 概览页

#### 文件

- `frontend/src/pages/material/MaterialOverview.tsx`
- `frontend/src/pages/material/VideoList.tsx`
- `frontend/src/pages/product/ProductList.tsx`

#### 目标

- 让素材体系的入口、列表、详情跳转关系更稳定

#### 改造重点

1. 先做 overview 入口层级
2. 再统一列表页框架
3. 产品/视频/话题等列表共享同一壳

### 验收标准

1. 改造后的 4 类页面，在标题、副标题、操作区、卡片层级、反馈态上看起来像同一产品。
2. 页面首屏不再需要靠解释性提示告诉用户“这个页面是干嘛的”。
3. 每个页面都有明确的一号动作。

---

## Phase 4：领域推广与一致性收尾

### 目标

把前面沉淀出来的壳层与模板，推广到剩余页面。

### 推广对象

- `frontend/src/pages/Settings.tsx`
- `frontend/src/pages/ScheduleConfig.tsx`
- `frontend/src/pages/ProfileManagement.tsx`
- `frontend/src/features/auth/admin/*`
- `frontend/src/pages/AIClip.tsx`
- `frontend/src/features/creative/pages/CreativeWorkbench.tsx`

### 动作

1. 配置类页面统一成“策略页”表达，而不是“参数散表”。
2. AIClip 从工具面板感，升级为“流程页 + 高级参数折叠层”。
3. CreativeWorkbench 吸收通用页头、通用反馈态，但保留其业务特性。
4. CreativeDetail 最后单独立项，不混入本轮基础改造。

### 验收标准

1. 同一层级页面使用同一套版式语言。
2. 配置页、列表页、详情页、工作台页都有稳定模板。
3. 不再新增新的“临时风格页面”。

---

## 6. 页面优先级排序（结合当前代码复杂度）

按“全局收益 / 风险 / 当前复杂度”综合排序：

### 第一优先级

1. `frontend/src/components/Layout.tsx` → `app/shell/AppShell.tsx`
2. `frontend/src/App.tsx`
3. `frontend/src/pages/Dashboard.tsx`
4. `frontend/src/pages/Account.tsx`

### 第二优先级

1. `frontend/src/pages/TaskList.tsx`（996 行，高复杂度高收益）
2. `frontend/src/pages/material/MaterialOverview.tsx`
3. `frontend/src/pages/material/VideoList.tsx`
4. `frontend/src/pages/product/ProductList.tsx`

### 第三优先级

1. `frontend/src/pages/Settings.tsx`
2. `frontend/src/pages/ScheduleConfig.tsx`
3. `frontend/src/pages/ProfileManagement.tsx`
4. `frontend/src/features/auth/admin/*`

### 暂缓

1. `frontend/src/features/creative/pages/CreativeDetail.tsx`
2. `frontend/src/pages/task/TaskCreate.tsx`
3. `frontend/src/pages/task/TaskDetail.tsx`

暂缓原因：

- 复杂度高
- 容易拖大范围
- 更适合等 UI 基础件成熟后再进入

---

## 7. 迁移与改造要遵守的执行原则

1. **先壳层，后页面。**
2. **先统一骨架，再做局部美化。**
3. **每次只打一条主线，不混着做。**
4. **页面改造与数据模型重构解耦。**
5. **先把通用组件做对，再复制到多个页面。**
6. **优先删除散乱样式，而不是继续叠样式。**
7. **新页面不允许绕过 `app/ + shared ui` 体系直接野生生长。**

---

## 8. 每阶段的验证方式

### 结构验证

1. `App.tsx` 是否瘦身
2. `router.tsx`、`AppProviders.tsx`、`theme/`、`app/shell/` 是否建立
3. 新页面是否从新结构接入

### 视觉验证

1. 改造前后截图对比
2. 页头、卡片、筛选条、危险操作区是否一致
3. 同级页面是否仍有明显“像不同人写的”感觉

### 交互验证

1. 登录后导航是否正常
2. 菜单跳转是否正常
3. 页面 loading / empty / error 是否可见且合理

### 回归验证

1. 至少覆盖登录、壳层导航、Dashboard、Task、Material 入口 smoke
2. 关键页面无路由回归
3. 旧页面不因结构迁移失效

---

## 9. 推荐的第一轮实施切片

如果现在就进入执行，我建议第一轮只做这一刀：

## Slice 1：AppShell + Theme + PageHeader 基础层

### 范围

- `frontend/src/App.tsx`
- `frontend/src/components/Layout.tsx`
- `frontend/src/providers/QueryProvider.tsx`
- 新建 `frontend/src/app/*`
- 新建 `frontend/src/components/ui/PageHeader.tsx`
- 新建 `frontend/src/components/feedback/*`

### 不做

- 不改 `CreativeDetail`
- 不改复杂表单
- 不动 Electron
- 不顺手重构接口层

### 为什么先做这刀

因为这是后面所有“变漂亮”的基础。  
如果这一层不先立起来，后面每个页面都会重复造轮子。

### Slice 1 验收标准

1. AppShell 独立出来
2. theme token 独立出来
3. 页面可以接入统一 `PageHeader`
4. 至少 1 个页面成功换到新骨架

---

## 10. 最终建议

这次改造不要定义成“美化几个页面”，而要定义成：

> **建立一套能持续产出漂亮页面的前端产品化结构。**

最合理的推进顺序是：

1. 先做 **基础壳层收口**
2. 再做 **共享 UI 骨架**
3. 再做 **高流量页面试点**
4. 最后做 **复杂页面专项**

如果你愿意，我下一步可以直接继续给你出：

1. **Slice 1 的实施清单（精确到文件新增/迁移/改名）**
2. **Slice 1 的 AI 执行 Prompt**
3. **Slice 1 的验收清单**

