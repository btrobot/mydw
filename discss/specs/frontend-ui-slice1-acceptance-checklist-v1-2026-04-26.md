# Frontend UI 改造 Slice 1 验收清单 v1

> 日期：2026-04-26  
> 对应切片：`AppShell + Theme + PageHeader 基础层`

---

## 1. 结构验收

- [ ] `frontend/src/app/` 已建立
- [ ] `frontend/src/app/theme/tokens.ts` 已建立
- [ ] `frontend/src/app/theme/index.ts` 已建立
- [ ] `frontend/src/app/AppProviders.tsx` 已建立
- [ ] `frontend/src/app/router.tsx` 已建立
- [ ] `frontend/src/app/shell/AppShell.tsx` 已建立
- [ ] `frontend/src/app/shell/navigation.tsx` 已建立
- [ ] `frontend/src/components/ui/PageHeader.tsx` 已建立
- [ ] `frontend/src/components/feedback/PageLoading.tsx` 已建立
- [ ] `frontend/src/components/feedback/PageEmpty.tsx` 已建立
- [ ] `frontend/src/components/feedback/PageError.tsx` 已建立
- [ ] `frontend/src/components/feedback/InlineNotice.tsx` 已建立

---

## 2. 入口收口验收

- [ ] `frontend/src/App.tsx` 不再内联 theme 对象
- [ ] `frontend/src/App.tsx` 不再直接堆满全部 route
- [ ] `frontend/src/App.tsx` 不再直接组合全部 provider
- [ ] `frontend/src/App.tsx` 主要只负责组装 `AppProviders + AppRouter`

---

## 3. 壳层验收

- [ ] `frontend/src/components/Layout.tsx` 已不再作为主壳入口
- [ ] `frontend/src/features/auth/AuthRouteGate.tsx` 已改为引用 `@/app/shell/AppShell`
- [ ] 登录后仍能正常进入受保护壳层
- [ ] 左侧菜单仍可展开 / 收起
- [ ] 左侧菜单选中态仍正确
- [ ] 路由跳转后菜单高亮仍正确

---

## 4. 页面试点验收

- [ ] `frontend/src/pages/Dashboard.tsx` 已接入 `PageHeader`
- [ ] Dashboard 首屏主表达不再依赖解释型大 Alert
- [ ] Dashboard 保留两个关键 CTA：
  - [ ] 进入作品工作台
  - [ ] 查看任务管理
- [ ] Dashboard 的页面级 loading / empty / error 至少有一部分已接共享 feedback 组件

---

## 5. 行为不回归验收

- [ ] 首页 `/` 仍能正确跳转到业务默认入口
- [ ] `/login` 行为未回归
- [ ] auth 状态页未回归：
  - [ ] `/auth/revoked`
  - [ ] `/auth/device-mismatch`
  - [ ] `/auth/expired`
  - [ ] `/auth/grace`
- [ ] `/dashboard` 能正常打开
- [ ] `/creative/workbench` 能正常打开

---

## 6. 工程验收

- [ ] 在 `frontend/` 下执行 `npm run typecheck` 通过
- [ ] 在 `frontend/` 下执行 `npm run build` 通过

如有条件，再补：

- [ ] 相关 smoke / e2e 验证通过

---

## 7. 代码质量验收

- [ ] 新增结构命名清晰
- [ ] 没有遗留双入口壳层
- [ ] 没有遗留双份 QueryProvider 实现
- [ ] 新组件接口不过度设计
- [ ] 改造 diff 可回滚、可审查

---

## 8. 完成定义

只有当以下 4 条同时满足，Slice 1 才算真正完成：

- [ ] app 层已建立
- [ ] 壳层已迁移
- [ ] Dashboard 已接新骨架
- [ ] typecheck / build 已通过

