# Frontend UI 改造 Slice 1 实施清单 v1

> 日期：2026-04-26  
> 对应总计划：`discss/specs/frontend-ui-transformation-plan-v1-2026-04-26.md`  
> 目标：完成 **AppShell + Theme + PageHeader 基础层**  
> 范围：只做前端壳层收口与 1 个页面试点，不进入大规模页面翻新

---

## 1. Slice 1 要产出的结果

本 Slice 完成后，项目里要出现 4 个明确能力：

1. **有独立的 app 层**
   - 不再把 theme / provider / router / shell 全堆在 `App.tsx`
2. **有独立的 AppShell**
   - 由 `src/app/shell/AppShell.tsx` 承接
3. **有独立的 theme token**
   - 不再在入口里内联 theme 对象
4. **有统一页面头部与基础反馈态**
   - 至少让 `Dashboard` 接上新骨架

---

## 2. 这刀明确不做什么

本 Slice 不做：

1. 不改 `frontend/src/features/creative/pages/CreativeDetail.tsx`
2. 不重写 `TaskList.tsx`
3. 不动 `electron/*`
4. 不顺手改接口层架构
5. 不做完整 design system

---

## 3. 文件级实施清单

## 3.1 新建目录

```text
frontend/src/app/
frontend/src/app/providers/
frontend/src/app/theme/
frontend/src/app/shell/
frontend/src/components/ui/
frontend/src/components/feedback/
```

## 3.2 新建文件

### A. app 层

1. `frontend/src/app/AppProviders.tsx`
   - 负责组合：
     - `ConfigProvider`
     - `AntApp`
     - `QueryProvider`
     - `AuthBootstrapProvider`
     - `AuthErrorBoundary`

2. `frontend/src/app/router.tsx`
   - 从 `App.tsx` 迁出全部路由定义
   - 承接：
     - `HashRouter`
     - `Routes`
     - `Route`
     - `Navigate`

3. `frontend/src/app/routes/BusinessEntryRedirect.tsx`
   - 从当前 `App.tsx` 中抽出 `BusinessEntryRedirect`
   - 保留 `useSystemConfig` + `getCreativeFlowDefaultPath` 逻辑

4. `frontend/src/app/providers/QueryProvider.tsx`
   - 从 `frontend/src/providers/QueryProvider.tsx` 迁入
   - 逻辑尽量不改，只做位置迁移

### B. theme 层

5. `frontend/src/app/theme/tokens.ts`
   - 承接当前 `App.tsx` 中的 theme token
   - 只抽：
     - `colorPrimary`
     - `borderRadius`
     - `colorBgLayout`
     - `Table.headerBg`

6. `frontend/src/app/theme/index.ts`
   - 导出统一 `appTheme`

### C. shell 层

7. `frontend/src/app/shell/navigation.tsx`
   - 从当前 `components/Layout.tsx` 中抽离：
     - `shellMenuItems`
     - `subMenuKeys`
     - `rootMenuPaths`
     - `menuTestIds`
     - `getSelectedKey`
     - `getInitialOpenKeys`

8. `frontend/src/app/shell/AppShell.tsx`
   - 从 `frontend/src/components/Layout.tsx` 迁移而来
   - 保留现有行为
   - 只做结构收口，不做大视觉重写

### D. shared ui / feedback

9. `frontend/src/components/ui/PageHeader.tsx`
   - 支持：
     - `title`
     - `subtitle`
     - `extra`
     - 可选 `breadcrumbs`（先可留接口，不必强上）

10. `frontend/src/components/feedback/PageLoading.tsx`
11. `frontend/src/components/feedback/PageEmpty.tsx`
12. `frontend/src/components/feedback/PageError.tsx`
13. `frontend/src/components/feedback/InlineNotice.tsx`

这些基础件要求：

- 轻量
- 可复用
- 先覆盖大多数普通页面

## 3.3 修改文件

1. `frontend/src/App.tsx`
   - 去掉内联 theme
   - 去掉大量 route 定义
   - 去掉直接 provider 组装
   - 收薄为：
     - `AppProviders`
     - `AppRouter`

2. `frontend/src/main.tsx`
   - 理论上可不改
   - 若入口引用有变，做最小修正

3. `frontend/src/features/auth/AuthRouteGate.tsx`
   - `LayoutComponent` 引用改为 `AppShell`
   - import 路径改为 `@/app/shell/AppShell`

4. `frontend/src/providers/QueryProvider.tsx`
   - 删除或转发导出
   - 建议最终删除，避免双入口

5. `frontend/src/components/Layout.tsx`
   - 删除原文件，避免旧壳继续被引用

6. `frontend/src/pages/Dashboard.tsx`
   - 接入 `PageHeader`
   - 至少把首屏 Alert 式说明收口为更稳定的页头表达
   - loading / empty / error 尽量优先接新反馈组件

---

## 4. 推荐执行顺序

### Step 1：先抽 theme

先做：

- `app/theme/tokens.ts`
- `app/theme/index.ts`

原因：

- 风险最低
- 最容易先让 `App.tsx` 变薄

### Step 2：再抽 QueryProvider + AppProviders

先建立 `AppProviders.tsx`，再把 QueryProvider 移进去。

### Step 3：再抽 router

把 `App.tsx` 里的 route wiring 移到 `app/router.tsx`。

### Step 4：再迁 AppShell

把 `components/Layout.tsx` 收到 `app/shell/AppShell.tsx`，并同步拆出 `navigation.tsx`。

### Step 5：最后补 shared ui

建立：

- `PageHeader`
- `PageLoading`
- `PageEmpty`
- `PageError`
- `InlineNotice`

### Step 6：最后只挑 1 个页面接新骨架

推荐只改：

- `frontend/src/pages/Dashboard.tsx`

原因：

- 体量适中
- 全局观感收益高
- 不容易把范围带崩

---

## 5. PageHeader 最小接口建议

```ts
interface PageHeaderProps {
  title: ReactNode
  subtitle?: ReactNode
  extra?: ReactNode
}
```

不要在 Slice 1 里把它做太重。  
只要它能替代大量页面里重复的：

- 标题
- 副标题
- 右侧按钮区

就够了。

---

## 6. Dashboard 试点改造要求

`frontend/src/pages/Dashboard.tsx` 在本 Slice 只做这些：

1. 用 `PageHeader` 替换首屏解释型 `Alert` 的主表达职责
2. 保留原有关键 CTA：
   - 进入作品工作台
   - 查看任务管理
3. 尽量把页面级 loading / empty / error 替换成共享反馈组件
4. 不重写业务 hooks
5. 不改统计语义

目标不是把 Dashboard 做完美，而是：

> **证明这套 app + shell + header + feedback 骨架能落地。**

---

## 7. 回归风险点

1. 路由迁移后首页跳转可能失效
2. AuthRouteGate 改引用后壳层可能白屏
3. 菜单选中态 / 展开态可能回归
4. Dashboard 首屏重构后 CTA 可能丢失
5. 旧 `QueryProvider` 路径残留可能造成双实现

---

## 8. 必做验证

在 `frontend/` 下至少跑：

1. `npm run typecheck`
2. `npm run build`

如果本地已有可跑环境，再补：

3. `npm run test:e2e -- --grep app-shell`
4. 或至少人工验证：
   - 登录
   - 首页跳转
   - 左侧菜单导航
   - Dashboard 两个主 CTA

---

## 9. 完成定义

满足以下条件，Slice 1 才算完成：

1. `App.tsx` 明显瘦身
2. `app/` 层建立完成
3. `components/Layout.tsx` 不再作为主壳存在
4. `Dashboard` 已接入 `PageHeader`
5. typecheck / build 通过
6. 登录后壳层导航正常

---

## 10. 一句话实施策略

> **这一刀不是为了“把页面做漂亮”，而是为了建立后面能持续做漂亮页面的骨架。**

