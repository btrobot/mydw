# Frontend UI 改造 Slice 1 - AI 执行 Prompt 模板

> 日期：2026-04-26  
> 用途：可直接喂给 AI，让它按当前项目真实结构执行第一刀改造

---

## 版本 A：直接执行版

你现在是一个高级前端重构工程师，请在 **不改变现有业务行为** 的前提下，对当前项目执行一轮 **前端 UI 基础层收口改造**。

### 改造目标

把当前项目的前端入口结构，从“App.tsx 中堆满 theme / providers / router / shell / pages”改成更稳定的 app 分层结构，参考 `remote/remote-admin` 的组织方式，但不要机械照抄，要适配当前项目。

### 当前项目事实

- 入口文件：`frontend/src/App.tsx`
- 主入口：`frontend/src/main.tsx`
- 当前壳层：`frontend/src/components/Layout.tsx`
- 当前 QueryProvider：`frontend/src/providers/QueryProvider.tsx`
- 当前路由保护：`frontend/src/features/auth/AuthRouteGate.tsx`
- 当前试点页面：`frontend/src/pages/Dashboard.tsx`

### 本次必须完成

1. 建立 `frontend/src/app/` 目录层
2. 把 theme 从 `App.tsx` 中抽离到：
   - `frontend/src/app/theme/tokens.ts`
   - `frontend/src/app/theme/index.ts`
3. 把 provider 组合抽离到：
   - `frontend/src/app/AppProviders.tsx`
4. 把路由抽离到：
   - `frontend/src/app/router.tsx`
5. 把当前 `frontend/src/components/Layout.tsx` 迁移为：
   - `frontend/src/app/shell/AppShell.tsx`
6. 从壳层中抽离导航定义到：
   - `frontend/src/app/shell/navigation.tsx`
7. 建立共享页面头部组件：
   - `frontend/src/components/ui/PageHeader.tsx`
8. 建立共享反馈组件：
   - `frontend/src/components/feedback/PageLoading.tsx`
   - `frontend/src/components/feedback/PageEmpty.tsx`
   - `frontend/src/components/feedback/PageError.tsx`
   - `frontend/src/components/feedback/InlineNotice.tsx`
9. 让 `frontend/src/pages/Dashboard.tsx` 至少接入 `PageHeader`

### 本次明确不要做

1. 不改 `frontend/src/features/creative/pages/CreativeDetail.tsx`
2. 不重写 `TaskList.tsx`
3. 不动 `frontend/electron/*`
4. 不改后端接口契约
5. 不做全站视觉翻新

### 强约束

1. 保持现有业务行为不变
2. 保持现有路由语义不变
3. 保持现有鉴权逻辑不变
4. 优先“迁移与抽离”，不要顺手大改逻辑
5. 差异要小、可回滚、可验证

### 设计要求

1. `App.tsx` 最终应尽量薄，只负责把 `AppProviders` 和 `AppRouter` 组起来
2. `AppShell` 负责壳层布局，不负责业务判断细节
3. `router.tsx` 负责路由，不直接内联视觉结构
4. `PageHeader` 要轻量，只需要：
   - title
   - subtitle
   - extra
5. Dashboard 只做试点，不要借机大改业务 hooks

### 验证要求

完成后必须运行并汇报：

1. `npm run typecheck`
2. `npm run build`

并在汇报中给出：

1. 修改文件列表
2. 新增文件列表
3. 结构上做了哪些收口
4. 哪些行为保持不变
5. 剩余风险

---

## 版本 B：更强约束版

请对当前项目做一轮 **最小可落地的前端结构收口**，目标是为后续 UI 美化打地基，而不是立即重做 UI。

### 你必须遵守

- 不新增依赖
- 不改变接口契约
- 不重构复杂业务逻辑
- 不扩大到 Slice 1 之外的范围

### 你应该优先做的事

1. 抽 theme
2. 抽 AppProviders
3. 抽 router
4. 迁移 AppShell
5. 建立 PageHeader 与基础 feedback 组件
6. 只在 Dashboard 上验证新骨架

### 你不应该做的事

1. 不要顺手整理所有 pages
2. 不要同时处理 Task / Material / CreativeDetail
3. 不要把 feedback 组件做成过度抽象的大系统

### 完成标准

- `App.tsx` 显著变薄
- `app/` 层成立
- `Dashboard` 接上 `PageHeader`
- typecheck / build 通过
- 路由与鉴权行为未回归

