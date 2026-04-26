# 前端项目目录结构模板（基于 Remote Admin 方法）

## 目标

这个模板不是为了“目录好看”，而是为了把以下 10 条原则落到工程里：

1. 先做壳层，再做页面
2. 按页面模式开发
3. 先定 token，再写样式
4. 列表页统一数据流
5. loading / empty / error 组件化
6. 权限显式表达
7. 危险操作单独成区
8. 状态分层
9. 文案也是设计的一部分
10. 先系统一致，再逐页精修

---

## 推荐目录

```txt
src/
  app/
    providers/
      AppProviders.tsx
      QueryProvider.tsx
      ThemeProvider.tsx
      AuthProvider.tsx
    router/
      router.tsx
      route-helpers.ts
      ProtectedRoute.tsx
    shell/
      AppShell.tsx
      AppHeader.tsx
      AppSidebar.tsx
      AppBreadcrumbs.tsx
    theme/
      tokens.ts
      antd-theme.ts
      semantic-colors.ts
      density.ts
    main.tsx

  features/
    auth/
      api/
        auth-client.ts
      model/
        auth-types.ts
      state/
        auth-context.tsx
        auth-store.ts
      ui/
        RoleBadge.tsx
        SessionNotice.tsx
        StepUpModal.tsx

    users/
      api/
        users-client.ts
      model/
        users-types.ts
        users-filters.ts
      hooks/
        useUsersList.ts
        useUserDetail.ts
        useUserActions.ts
      ui/
        UsersPage.tsx
        UsersFilterBar.tsx
        UsersListPane.tsx
        UserDetailPane.tsx
        UserEditSection.tsx
        CreateUserModal.tsx

    devices/
      api/
      model/
      hooks/
      ui/

    sessions/
      api/
      model/
      hooks/
      ui/

    audit/
      api/
      model/
      hooks/
      ui/

  components/
    feedback/
      LoadingState.tsx
      EmptyState.tsx
      ErrorState.tsx
      RetryBanner.tsx
      SuccessNotice.tsx
    layout/
      PageHeader.tsx
      SectionCard.tsx
      DetailPanel.tsx
      SplitPane.tsx
    data-display/
      StatusBadge.tsx
      IdPill.tsx
      TimestampText.tsx
      KeyValueGrid.tsx
      JsonViewer.tsx
    data-entry/
      FilterBar.tsx
      SearchField.tsx
      OffsetPaginationControls.tsx
      FormSection.tsx
    safety/
      DangerZone.tsx
      ConfirmActionDialog.tsx
      ReadonlyNotice.tsx

  patterns/
    dashboard/
      DashboardHero.tsx
      MetricGrid.tsx
      EventListCard.tsx
    master-detail/
      MasterDetailPage.tsx
      ListPane.tsx
      SelectionState.ts
    investigation/
      InvestigationPage.tsx
      QuerySummaryBar.tsx

  lib/
    http/
      client.ts
      errors.ts
    query/
      queryKeys.ts
      pagination.ts
    format/
      date.ts
      number.ts
      text.ts
    guards/
      permissions.ts
      role-access.ts

  copy/
    common.ts
    auth.ts
    users.ts
    devices.ts
    audit.ts

  styles/
    globals.css
    reset.css
```

---

## 每一层为什么这样分

## 1. `app/`

放“全局骨架”，不放业务细节。

适合放：

- providers
- router
- shell
- theme

### 原则对应

- 先做壳层，再做页面
- 先定 token，再写样式

---

## 2. `features/`

按业务域拆，不按技术类型散落。

例如：

- `users`
- `devices`
- `sessions`
- `audit`

每个 feature 再分：

- `api/`
- `model/`
- `hooks/`
- `ui/`

### 原则对应

- 按页面模式开发，但业务归属仍然清楚
- 状态分层
- 列表页统一数据流

---

## 3. `components/`

放跨业务复用组件，不放某个具体页面专属逻辑。

建议按“用途”拆：

- `feedback/`
- `layout/`
- `data-display/`
- `data-entry/`
- `safety/`

### 原则对应

- loading / empty / error 组件化
- 权限显式表达
- 危险操作单独成区

---

## 4. `patterns/`

这是最值得加的一层。

它不是业务组件，也不是基础组件，而是“页面模式组件”。

例如：

- `dashboard/`
- `master-detail/`
- `investigation/`

### 为什么重要

因为很多后台页面不是简单组件复用，而是“页面结构复用”。

### 原则对应

- 不要按页面开发，要按页面模式开发
- 先系统一致，再逐页精修

---

## 5. `lib/`

放纯逻辑工具，不带页面语义。

例如：

- http client
- query keys
- pagination helpers
- formatter
- permission guards

### 原则对应

- 状态分层
- 列表页统一数据流

---

## 6. `copy/`

专门放文案，不要把所有说明文案散落在页面 JSX 里。

例如：

- 错误文案
- 空态文案
- danger zone 文案
- role-aware 提示文案

### 原则对应

- 文案也是设计的一部分

---

## 页面文件内部建议结构

以 `UsersPage.tsx` 为例，建议内部只保留页面编排，不堆满所有细节：

```txt
UsersPage
  PageHeader
  PermissionNotice
  UsersFilterBar
  MasterDetailPage
    UsersListPane
    UserDetailPane
      UserEditSection
      DangerZone
  CreateUserModal
```

这样做的目标是：

- 页面负责编排
- 逻辑由 hooks 管
- 视觉由组件管
- 文案由 copy 管

---

## 列表页统一数据流模板

建议每个列表类 feature 都有这几层：

### `model/`

- filters type
- entity type
- pagination type

### `hooks/`

- `useXxxList`
- `useXxxDetail`
- `useXxxActions`

### `ui/`

- `XxxFilterBar`
- `XxxListPane`
- `XxxDetailPane`

这样之后：

- Users
- Devices
- Sessions
- Orders

都能复用同一套路。

---

## 最小落地版本

如果你不想一开始分太细，至少保留这 8 个目录：

```txt
src/
  app/
  features/
  components/
  patterns/
  lib/
  copy/
  styles/
  main.tsx
```

这已经足够比“pages/components/utils 混搭”稳定很多。

---

## 一句话总结

> 这个目录模板的核心思想是：`app` 管全局骨架，`features` 管业务域，`components` 管跨域复用，`patterns` 管页面模式，`lib` 管纯逻辑，`copy` 管体验文案。

