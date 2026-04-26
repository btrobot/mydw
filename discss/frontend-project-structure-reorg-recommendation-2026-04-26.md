# 当前 frontend 项目专属目录重组建议（2026-04-26）

## 1. 结论先说

你的 `frontend/` 不是“结构很差”，而是处于一种**过渡态**：

- 一部分已经是 **feature-based** 结构  
  - 例如：`src/features/auth/*`
  - 例如：`src/features/creative/*`
- 另一部分仍然是 **旧式横向分层**  
  - `src/pages/*`
  - `src/hooks/*`
  - `src/components/*`
  - `src/services/*`

所以当前最合适的方向不是“推倒重来”，而是：

> **以 `features/creative` 为成熟样板，把老的 `pages/hooks/components/services` 逐步收编进 feature + app + shared 结构。**

---

## 2. 我是基于什么判断的

### 2.1 当前 `src/` 顶层结构

当前 `frontend/src` 顶层目录是：

- `api/`
- `components/`
- `features/`
- `hooks/`
- `pages/`
- `providers/`
- `services/`
- `types/`
- `utils/`

这说明现在是 **“横向公共层” + “局部 feature 化”并存**。

### 2.2 现有 feature 化最明显的两块

#### `auth`

- `frontend/src/features/auth/*`
- 包含：
  - `AuthProvider.tsx`
  - `AuthRouteGate.tsx`
  - `LoginPage.tsx`
  - `AuthStatusPage.tsx`
  - `admin/SessionAdmin.tsx`

#### `creative`

- `frontend/src/features/creative/*`
- 已经分出：
  - `components/`
  - `hooks/`
  - `pages/`
  - `types/`
  - `view-models/`

这说明项目已经自然长出了一条正确方向：  
**复杂业务应该进 feature，不应该继续堆在顶层 pages/hooks。**

### 2.3 旧结构仍然很重

例如 `App.tsx` 仍然直接 import 大量页面：

- `frontend/src/App.tsx:10-34`
- 并在一个文件里集中写大量路由：
  - `frontend/src/App.tsx:72-117`

这里的问题不是“能不能跑”，而是：

- 路由总入口太重
- 页面归属不清
- 后续新增模块会继续往 `pages/` 堆

### 2.4 壳层位置也有点混

当前：

- `ProtectedAppShell` 在 `features/auth/AuthRouteGate.tsx:43-76`
- 但实际 Layout 壳层在 `components/Layout.tsx:150-220`

也就是说：

- **鉴权 gate** 在 auth feature
- **应用壳层 shell** 在 generic components

这会导致职责不够清楚。  
`AppShell` 本质上属于 `app/`，不属于 `components/`，也不属于 `auth`。

### 2.5 API 层也有“双轨”

当前同时存在：

- 生成 API：`frontend/src/api/*`
- 手写 axios 服务：`frontend/src/services/api.ts:1-34`

这类结构短期能用，但长期容易出现：

- 一部分页面走 generated client
- 一部分页面走 axios
- query key、错误处理、鉴权注入风格不统一

---

## 3. 我对你这个项目的专属判断

你这个项目现在最适合的组织方式，不是纯 `pages/components/utils`，而是：

## 3.1 推荐总结构

```txt
frontend/
  src/
    app/
    features/
    components/
    patterns/
    lib/
    copy/
    styles/
    main.tsx

  electron/
  e2e/
  scripts/
  data/
```

### 为什么

- `app/`：放全局壳层、router、providers、theme
- `features/`：放业务模块
- `components/`：放跨业务复用组件
- `patterns/`：放 dashboard / master-detail / investigation 页面模式
- `lib/`：放纯逻辑和网络底座
- `copy/`：放统一体验文案
- `electron/`：继续独立，不建议塞进 `src/`
- `e2e/`：继续独立，但建议与 feature 命名对齐

---

## 4. 针对你当前项目的推荐目录

## 4.1 目标目录树

```txt
frontend/
  src/
    app/
      providers/
        AppProviders.tsx
        QueryProvider.tsx
        AuthBootstrapProvider.tsx
      router/
        AppRouter.tsx
        route-helpers.ts
        route-config.ts
      shell/
        AppShell.tsx
        AppHeader.tsx
        AppSidebar.tsx
      theme/
        antd-theme.ts
        tokens.ts

    features/
      auth/
        api/
        model/
        state/
        ui/
        routes/
      creative/
        components/
        hooks/
        pages/
        types/
        view-models/
      dashboard/
        hooks/
        pages/
        ui/
      account/
        hooks/
        pages/
        ui/
      task/
        hooks/
        pages/
        ui/
        model/
      material/
        hooks/
        pages/
        ui/
        model/
      settings/
        hooks/
        pages/
        ui/
      schedule/
        hooks/
        pages/
        ui/
      profile/
        hooks/
        pages/
        ui/
      ai-clip/
        hooks/
        pages/
        ui/

    components/
      feedback/
      layout/
      data-display/
      data-entry/
      safety/

    patterns/
      dashboard/
      master-detail/
      investigation/

    lib/
      api/
        generated/
        client/
      query/
      format/
      permissions/
      utils/

    copy/
      auth.ts
      common.ts
      task.ts
      material.ts
      creative.ts

    styles/
      index.css
      tokens.css

    main.tsx
```

---

## 5. 你当前目录怎么映射到目标目录

下面这部分最重要。

## 5.1 `src/App.tsx`

### 当前问题

- 同时承担：
  - theme 注入
  - provider 编排
  - router
  - route table
  - 页面入口跳转

参考：

- `frontend/src/App.tsx:38-49`
- `frontend/src/App.tsx:65-125`

### 建议落点

- `src/app/providers/AppProviders.tsx`
- `src/app/router/AppRouter.tsx`
- `src/app/theme/antd-theme.ts`

### 目标

让 `App.tsx` 只剩类似：

- `<AppProviders><AppRouter /></AppProviders>`

---

## 5.2 `src/components/Layout.tsx`

### 当前问题

这是标准的 `AppShell`，但放在 generic `components/` 里。

参考：

- 菜单配置：`frontend/src/components/Layout.tsx:70-109`
- 侧栏/头部壳层：`frontend/src/components/Layout.tsx:180-220`

### 建议落点

- `src/app/shell/AppShell.tsx`

### 可顺手再拆

- `AppHeader.tsx`
- `AppSidebar.tsx`
- `shellMenu.ts`

### 目标

把“应用骨架”从“普通组件”里提升出来。

---

## 5.3 `src/features/auth/AuthRouteGate.tsx`

### 当前问题

这个文件里既有：

- auth gate
- public route gate
- grace banner
- authenticated redirect

并且直接依赖 `LayoutComponent`。

参考：

- `frontend/src/features/auth/AuthRouteGate.tsx:43-102`

### 建议落点

- `src/features/auth/routes/ProtectedRoute.tsx`
- `src/features/auth/routes/PublicRoute.tsx`

如果保留 `ProtectedAppShell` 这个概念，也建议它只负责：

- 鉴权通过后挂 `AppShell`

不要把 Shell 细节放进 auth feature。

---

## 5.4 `src/pages/*`

这是当前最值得重组的一块。

### 当前状态

顶层 `pages/` 下既有：

- `Dashboard.tsx`
- `Account.tsx`
- `AIClip.tsx`
- `Settings.tsx`
- `ScheduleConfig.tsx`
- `ProfileManagement.tsx`
- `TaskList.tsx`

又有分目录：

- `pages/material/*`
- `pages/product/*`
- `pages/task/*`

这说明页面归属标准不统一。

### 建议落点

#### 迁移建议

- `pages/Dashboard.tsx`
  -> `features/dashboard/pages/DashboardPage.tsx`

- `pages/Account.tsx`
  -> `features/account/pages/AccountPage.tsx`

- `pages/AIClip.tsx`
  -> `features/ai-clip/pages/AIClipPage.tsx`

- `pages/Settings.tsx`
  -> `features/settings/pages/SettingsPage.tsx`

- `pages/ScheduleConfig.tsx`
  -> `features/schedule/pages/ScheduleConfigPage.tsx`

- `pages/ProfileManagement.tsx`
  -> `features/profile/pages/ProfileManagementPage.tsx`

- `pages/TaskList.tsx`
  -> `features/task/pages/TaskListPage.tsx`

- `pages/task/TaskCreate.tsx`
  -> `features/task/pages/TaskCreatePage.tsx`

- `pages/task/TaskDetail.tsx`
  -> `features/task/pages/TaskDetailPage.tsx`

- `pages/material/*`
  -> `features/material/pages/*`

---

## 5.5 `src/hooks/*`

### 当前问题

目前这些 hooks 基本是业务 hooks：

- `useAccount.ts`
- `useAIClip.ts`
- `useAudio.ts`
- `useCopywriting.ts`
- `useCover.ts`
- `useProduct.ts`
- `useProfile.ts`
- `usePublish.ts`
- `useScheduleConfig.ts`
- `useSystem.ts`
- `useTask.ts`
- `useTopic.ts`
- `useVideo.ts`

这类命名说明它们不属于“全局 hooks”，而是属于各业务模块。

### 建议落点

- `useAccount.ts`
  -> `features/account/hooks/useAccount.ts`

- `useTask.ts`
  -> `features/task/hooks/useTask.ts`

- `useVideo.ts / useAudio.ts / useCover.ts / useCopywriting.ts / useTopic.ts`
  -> `features/material/hooks/*`

- `useProduct.ts`
  -> 如果商品逻辑仍然挂在素材域里，则进 `features/material/hooks/useProduct.ts`
  -> 如果商品独立成域，则进 `features/product/hooks/useProduct.ts`

- `useSystem.ts`
  -> 更适合进 `features/system/hooks/useSystemConfig.ts`
  或 `app/hooks/useSystemConfig.ts`（如果它只服务 App 启动）

### 核心原则

顶层 `src/hooks/` 最后应该尽量只保留：

- 极少数 truly shared hooks
- 或直接清空

---

## 5.6 `src/components/*`

### 当前问题

现在这里混着三类东西：

1. 壳层类组件  
   - `Layout.tsx`

2. 真正跨域复用组件  
   - `StatusBadge.tsx`

3. 明显业务组件  
   - `MaterialBasket.tsx`
   - `MaterialSelectModal.tsx`
   - `ProductQuickImport.tsx`
   - `ProductSelect.tsx`

### 建议落点

#### 应搬到 `app/`

- `Layout.tsx`
  -> `app/shell/AppShell.tsx`

#### 应搬到 `components/`

- `StatusBadge.tsx`
  -> `components/data-display/StatusBadge.tsx`

#### 应搬到 `features/material/ui/`

- `MaterialBasket.tsx`
- `MaterialSelectModal.tsx`

#### 应搬到 `features/product/ui/` 或 `features/material/ui/`

- `ProductQuickImport.tsx`
- `ProductSelect.tsx`

#### 待判断归属

- `ConnectionModal.tsx`
- `BatchDeleteButton.tsx`

如果是跨业务通用：

- `components/safety/`
或
- `components/data-entry/`

如果强依赖某业务，就应该回到该 feature。

---

## 5.7 `src/services/api.ts` 和 `src/api/*`

### 当前问题

现在有两套 API 入口：

- generated：`src/api/*`
- axios：`src/services/api.ts`

### 建议

统一成：

```txt
src/lib/api/
  generated/
  client/
```

#### 推荐方式

- `src/api/*`
  -> `src/lib/api/generated/*`

- `src/services/api.ts`
  -> `src/lib/api/client/axiosClient.ts`

### 原则

以后 feature 里的 hooks 不要直接从到处 import API。
而是统一从：

- generated SDK
或
- client adapter

进入。

---

## 5.8 `src/providers/`

### 当前状态

只有：

- `QueryProvider.tsx`

### 建议

迁到：

- `src/app/providers/QueryProvider.tsx`

并逐步补成：

- `AppProviders.tsx`
- `QueryProvider.tsx`
- `AuthBootstrapProvider.tsx`

让 provider 组合从 `App.tsx` 中抽出来。

---

## 5.9 `src/types/` / `src/utils/`

### 当前建议

不要继续无脑往这里堆。

#### 应保留在全局的

- truly shared utility
- formatter
- generic helper

#### 应该回 feature 的

- task 专属 types
- material 专属 utils
- creative 专属 mapper

### 建议目标

```txt
src/lib/format/
src/lib/utils/
src/features/*/model/
```

---

## 6. 我对你项目的“最优先重组顺序”

不要一次性全改。

## Phase 1：先抽 app 层

目标：

- `App.tsx` 变薄
- `Layout.tsx` 改名并迁到 `app/shell/`
- router/theme/providers 拆出去

这一阶段几乎不改业务，只改结构骨架。

### 优先改

- `src/App.tsx`
- `src/components/Layout.tsx`
- `src/providers/QueryProvider.tsx`
- `src/features/auth/AuthRouteGate.tsx`

---

## Phase 2：把 `pages/` 收编进 `features/`

优先收编这几组：

1. `task`
2. `material`
3. `dashboard`
4. `account`
5. `settings / schedule / profile / ai-clip`

原因：

- 这些目前最明显还在旧结构里
- 收完后项目结构会一下子清晰很多

---

## Phase 3：把 `hooks/` 拆回 feature

这是最关键的一步。

因为只要 hooks 还散在顶层，说明数据逻辑仍然是“全局散装”的。

收编后你会得到：

- feature 自带 query/mutation
- page 只负责编排
- App 不再知道太多业务细节

---

## Phase 4：统一 API 层

收口到：

- `lib/api/generated`
- `lib/api/client`

然后逐步让各 feature 的 hooks 只从这两个入口拿数据。

---

## Phase 5：补 shared/patterns/copy

这是产品化阶段，不是第一刀。

等 app 和 features 收稳以后，再做：

- `components/feedback/`
- `components/safety/`
- `patterns/master-detail/`
- `copy/*`

---

## 7. 我不建议你现在做的事

### 7.1 不建议先全面改文件名

例如一开始就把所有：

- `Dashboard.tsx`
- `TaskList.tsx`

都改成 `XxxPage.tsx`

这件事可以做，但不该先做。  
先把目录责任划清，再统一命名。

### 7.2 不建议先大规模抽 shared components

因为现在很多组件其实还没稳定，过早抽 shared 容易抽错层。

### 7.3 不建议同时重组 `electron/`

当前 `electron/` 已经独立：

- `main.ts`
- `preload.ts`
- `backendLauncher.ts`

这块边界很清楚，先别动它。

### 7.4 不建议先改 e2e 结构

`e2e/` 现在已经相对按主题分组了。  
等前端 feature 结构稳定后，再做命名对齐即可。

---

## 8. 最终一句话建议

对你这个项目最适合的目录重组方案，不是“从 pages 架构重写成大而全的设计系统”，而是：

> **把 `features/creative` 这种成熟 feature 结构，复制到 task / material / account / settings 等旧页面域；同时把 `Layout + router + theme + providers` 提升到 `app/` 层，把 `api/services` 收口到 `lib/` 层。**

这条路径风险最低，也最符合你项目现在的真实形态。

