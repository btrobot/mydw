# 当前项目前端迁移清单（文件级搬迁表，2026-04-26）

## 1. 使用说明

这不是抽象建议，而是针对当前 `frontend/` 的**文件级迁移清单**。

字段说明：

- **当前文件**：你现在仓库里的路径
- **目标路径**：建议迁移后的路径
- **动作**：
  - `keep`：保留位置
  - `move`：直接迁移
  - `move+rename`：迁移并统一命名
  - `split`：建议拆分成多个文件
  - `defer`：先不动
- **阶段**：
  - `P1`：先抽 `app/`
  - `P2`：收编 `pages/`
  - `P3`：收编 `hooks/`
  - `P4`：统一 `api/lib`
  - `P5`：共享组件与文案收口

---

## 2. app 层 / 入口层

| 当前文件 | 目标路径 | 动作 | 阶段 |
|---|---|---:|---:|
| `frontend/src/main.tsx` | `frontend/src/main.tsx` | keep | P1 |
| `frontend/src/App.tsx` | `frontend/src/App.tsx` | split | P1 |
|  | `frontend/src/app/providers/AppProviders.tsx` | 新增承接 | P1 |
|  | `frontend/src/app/router/AppRouter.tsx` | 新增承接 | P1 |
|  | `frontend/src/app/theme/antd-theme.ts` | 新增承接 | P1 |
| `frontend/src/providers/QueryProvider.tsx` | `frontend/src/app/providers/QueryProvider.tsx` | move | P1 |
| `frontend/src/index.css` | `frontend/src/styles/index.css` | move | P1 |
| `frontend/src/vite-env.d.ts` | `frontend/src/vite-env.d.ts` | keep | P1 |

---

## 3. 壳层 / layout / router

| 当前文件 | 目标路径 | 动作 | 阶段 |
|---|---|---:|---:|
| `frontend/src/components/Layout.tsx` | `frontend/src/app/shell/AppShell.tsx` | move+rename | P1 |
| `frontend/src/features/auth/AuthRouteGate.tsx` | `frontend/src/features/auth/routes/ProtectedRoute.tsx` | split | P1 |
|  | `frontend/src/features/auth/routes/PublicRoute.tsx` | 新增承接 | P1 |
|  | `frontend/src/app/router/BusinessEntryRedirect.tsx` | 新增承接 | P1 |

说明：

- `Layout.tsx` 现在本质是 AppShell，不该留在 generic `components/`
- `AuthRouteGate.tsx` 里现在混着：
  - protected gate
  - public gate
  - grace banner
  - authenticated redirect

---

## 4. auth feature

| 当前文件 | 目标路径 | 动作 | 阶段 |
|---|---|---:|---:|
| `frontend/src/features/auth/index.ts` | `frontend/src/features/auth/index.ts` | keep | P1 |
| `frontend/src/features/auth/AuthProvider.tsx` | `frontend/src/features/auth/state/AuthProvider.tsx` | move | P1 |
| `frontend/src/features/auth/api.ts` | `frontend/src/features/auth/api/auth-client.ts` | move+rename | P4 |
| `frontend/src/features/auth/transport.ts` | `frontend/src/features/auth/lib/transport.ts` | move | P4 |
| `frontend/src/features/auth/device.ts` | `frontend/src/features/auth/lib/device.ts` | move | P4 |
| `frontend/src/features/auth/types.ts` | `frontend/src/features/auth/model/auth-types.ts` | move+rename | P1 |
| `frontend/src/features/auth/useAuthStatus.ts` | `frontend/src/features/auth/hooks/useAuthStatus.ts` | move | P1 |
| `frontend/src/features/auth/authErrorHandler.ts` | `frontend/src/features/auth/lib/authErrorHandler.ts` | move | P1 |
| `frontend/src/features/auth/AuthErrorBoundary.tsx` | `frontend/src/features/auth/ui/AuthErrorBoundary.tsx` | move | P1 |
| `frontend/src/features/auth/AuthErrorMessage.tsx` | `frontend/src/features/auth/ui/AuthErrorMessage.tsx` | move | P1 |
| `frontend/src/features/auth/AuthSessionHeader.tsx` | `frontend/src/features/auth/ui/AuthSessionHeader.tsx` | move | P1 |
| `frontend/src/features/auth/LoginPage.tsx` | `frontend/src/features/auth/pages/LoginPage.tsx` | move | P1 |
| `frontend/src/features/auth/AuthStatusPage.tsx` | `frontend/src/features/auth/pages/AuthStatusPage.tsx` | move | P1 |
| `frontend/src/features/auth/admin/SessionAdmin.tsx` | `frontend/src/features/auth/pages/SessionAdminPage.tsx` | move+rename | P2 |
| `frontend/src/features/auth/admin/SessionList.tsx` | `frontend/src/features/auth/ui/SessionList.tsx` | move | P2 |

---

## 5. creative feature

这块已经是当前项目最成熟的 feature 样板，原则上**不做大迁移**，只做轻量收口。

| 当前文件 | 目标路径 | 动作 | 阶段 |
|---|---|---:|---:|
| `frontend/src/features/creative/pages/CreativeWorkbench.tsx` | `frontend/src/features/creative/pages/CreativeWorkbenchPage.tsx` | move+rename | P2 |
| `frontend/src/features/creative/pages/CreativeDetail.tsx` | `frontend/src/features/creative/pages/CreativeDetailPage.tsx` | move+rename | P2 |
| `frontend/src/features/creative/components/AIClipWorkflowPanel.tsx` | `frontend/src/features/creative/ui/AIClipWorkflowPanel.tsx` | move | P5 |
| `frontend/src/features/creative/components/CheckDrawer.tsx` | `frontend/src/features/creative/ui/CheckDrawer.tsx` | move | P5 |
| `frontend/src/features/creative/components/CreativeEmptyState.tsx` | `frontend/src/features/creative/ui/CreativeEmptyState.tsx` | move | P5 |
| `frontend/src/features/creative/components/VersionPanel.tsx` | `frontend/src/features/creative/ui/VersionPanel.tsx` | move | P5 |
| `frontend/src/features/creative/components/detail/CreativeDetailProjection.tsx` | `frontend/src/features/creative/ui/detail/CreativeDetailProjection.tsx` | move | P5 |
| `frontend/src/features/creative/components/detail/projection.ts` | `frontend/src/features/creative/model/projection.ts` | move | P5 |
| `frontend/src/features/creative/components/diagnostics/DiagnosticsActionPanel.tsx` | `frontend/src/features/creative/ui/diagnostics/DiagnosticsActionPanel.tsx` | move | P5 |
| `frontend/src/features/creative/components/workbench/shared.ts` | `frontend/src/features/creative/model/workbench-shared.ts` | move+rename | P5 |
| `frontend/src/features/creative/components/workbench/WorkbenchDiagnosticsDrawer.tsx` | `frontend/src/features/creative/ui/workbench/WorkbenchDiagnosticsDrawer.tsx` | move | P5 |
| `frontend/src/features/creative/components/workbench/WorkbenchPresetBar.tsx` | `frontend/src/features/creative/ui/workbench/WorkbenchPresetBar.tsx` | move | P5 |
| `frontend/src/features/creative/components/workbench/WorkbenchSummaryCard.tsx` | `frontend/src/features/creative/ui/workbench/WorkbenchSummaryCard.tsx` | move | P5 |
| `frontend/src/features/creative/components/workbench/WorkbenchTable.tsx` | `frontend/src/features/creative/ui/workbench/WorkbenchTable.tsx` | move | P5 |
| `frontend/src/features/creative/creativeAuthoring.ts` | `frontend/src/features/creative/lib/creativeAuthoring.ts` | move | P5 |
| `frontend/src/features/creative/creativeFlow.ts` | `frontend/src/features/creative/lib/creativeFlow.ts` | move | P1 |
| `frontend/src/features/creative/hooks/useCreatives.ts` | `frontend/src/features/creative/hooks/useCreatives.ts` | keep | P3 |
| `frontend/src/features/creative/hooks/useCreativeWorkflow.ts` | `frontend/src/features/creative/hooks/useCreativeWorkflow.ts` | keep | P3 |
| `frontend/src/features/creative/types/creative.ts` | `frontend/src/features/creative/model/creative.ts` | move | P3 |
| `frontend/src/features/creative/view-models/useCreativeAuthoringModel.ts` | `frontend/src/features/creative/view-models/useCreativeAuthoringModel.ts` | keep | P3 |
| `frontend/src/features/creative/view-models/useCreativeNavigationState.ts` | `frontend/src/features/creative/view-models/useCreativeNavigationState.ts` | keep | P3 |
| `frontend/src/features/creative/view-models/useCreativePublishDiagnosticsModel.ts` | `frontend/src/features/creative/view-models/useCreativePublishDiagnosticsModel.ts` | keep | P3 |
| `frontend/src/features/creative/view-models/useCreativeVersionReviewModel.ts` | `frontend/src/features/creative/view-models/useCreativeVersionReviewModel.ts` | keep | P3 |

---

## 6. account 域

| 当前文件 | 目标路径 | 动作 | 阶段 |
|---|---|---:|---:|
| `frontend/src/pages/Account.tsx` | `frontend/src/features/account/pages/AccountPage.tsx` | move+rename | P2 |
| `frontend/src/hooks/useAccount.ts` | `frontend/src/features/account/hooks/useAccount.ts` | move | P3 |
| `frontend/src/components/BatchDeleteButton.tsx` | `frontend/src/features/account/ui/BatchDeleteButton.tsx` | move | P2 |
| `frontend/src/components/ConnectionModal.tsx` | `frontend/src/features/account/ui/ConnectionModal.tsx` | move | P2 |
| `frontend/src/components/StatusBadge.tsx` | `frontend/src/components/data-display/StatusBadge.tsx` | move | P5 |

说明：

- `BatchDeleteButton` / `ConnectionModal` 当前只在 `Account.tsx` 使用，优先判定为账号域组件
- `StatusBadge` 明显是跨业务组件，适合进 shared components

---

## 7. dashboard 域

| 当前文件 | 目标路径 | 动作 | 阶段 |
|---|---|---:|---:|
| `frontend/src/pages/Dashboard.tsx` | `frontend/src/features/dashboard/pages/DashboardPage.tsx` | move+rename | P2 |
| `frontend/src/hooks/useSystem.ts` | `frontend/src/features/system/hooks/useSystem.ts` | move | P3 |
| `frontend/src/hooks/usePublish.ts` | `frontend/src/features/publish/hooks/usePublish.ts` | move | P3 |

说明：

- `Dashboard.tsx` 本身依赖 system/task/publish 多域数据，页面归 dashboard 域
- `useSystem.ts` 不建议继续挂在顶层 hooks

---

## 8. task 域

| 当前文件 | 目标路径 | 动作 | 阶段 |
|---|---|---:|---:|
| `frontend/src/pages/TaskList.tsx` | `frontend/src/features/task/pages/TaskListPage.tsx` | move+rename | P2 |
| `frontend/src/pages/task/TaskCreate.tsx` | `frontend/src/features/task/pages/TaskCreatePage.tsx` | move+rename | P2 |
| `frontend/src/pages/task/TaskDetail.tsx` | `frontend/src/features/task/pages/TaskDetailPage.tsx` | move+rename | P2 |
| `frontend/src/pages/task/taskPresentation.ts` | `frontend/src/features/task/model/taskPresentation.ts` | move | P2 |
| `frontend/src/pages/task/taskSemantics.ts` | `frontend/src/features/task/model/taskSemantics.ts` | move | P2 |
| `frontend/src/hooks/useTask.ts` | `frontend/src/features/task/hooks/useTask.ts` | move | P3 |
| `frontend/src/components/MaterialBasket.tsx` | `frontend/src/features/task/ui/MaterialBasket.tsx` | move | P2 |
| `frontend/src/components/MaterialSelectModal.tsx` | `frontend/src/features/task/ui/MaterialSelectModal.tsx` | move | P2 |
| `frontend/src/components/ProductQuickImport.tsx` | `frontend/src/features/task/ui/ProductQuickImport.tsx` | move | P2 |

说明：

- 这 3 个组件都主要服务 `TaskCreate.tsx`，虽然会依赖 material/product hooks，但 UI 归 task 域更稳

---

## 9. material 域

| 当前文件 | 目标路径 | 动作 | 阶段 |
|---|---|---:|---:|
| `frontend/src/pages/material/MaterialOverview.tsx` | `frontend/src/features/material/pages/MaterialOverviewPage.tsx` | move+rename | P2 |
| `frontend/src/pages/material/VideoList.tsx` | `frontend/src/features/material/pages/VideoListPage.tsx` | move+rename | P2 |
| `frontend/src/pages/material/VideoDetail.tsx` | `frontend/src/features/material/pages/VideoDetailPage.tsx` | move+rename | P2 |
| `frontend/src/pages/material/CopywritingList.tsx` | `frontend/src/features/material/pages/CopywritingListPage.tsx` | move+rename | P2 |
| `frontend/src/pages/material/CoverList.tsx` | `frontend/src/features/material/pages/CoverListPage.tsx` | move+rename | P2 |
| `frontend/src/pages/material/AudioList.tsx` | `frontend/src/features/material/pages/AudioListPage.tsx` | move+rename | P2 |
| `frontend/src/pages/material/TopicList.tsx` | `frontend/src/features/material/pages/TopicListPage.tsx` | move+rename | P2 |
| `frontend/src/pages/material/TopicGroupList.tsx` | `frontend/src/features/material/pages/TopicGroupListPage.tsx` | move+rename | P2 |
| `frontend/src/pages/material/TopicGroupDetail.tsx` | `frontend/src/features/material/pages/TopicGroupDetailPage.tsx` | move+rename | P2 |
| `frontend/src/pages/product/ProductList.tsx` | `frontend/src/features/material/pages/ProductListPage.tsx` | move+rename | P2 |
| `frontend/src/pages/product/ProductDetail.tsx` | `frontend/src/features/material/pages/ProductDetailPage.tsx` | move+rename | P2 |
| `frontend/src/hooks/useVideo.ts` | `frontend/src/features/material/hooks/useVideo.ts` | move | P3 |
| `frontend/src/hooks/useCopywriting.ts` | `frontend/src/features/material/hooks/useCopywriting.ts` | move | P3 |
| `frontend/src/hooks/useCover.ts` | `frontend/src/features/material/hooks/useCover.ts` | move | P3 |
| `frontend/src/hooks/useAudio.ts` | `frontend/src/features/material/hooks/useAudio.ts` | move | P3 |
| `frontend/src/hooks/useTopic.ts` | `frontend/src/features/material/hooks/useTopic.ts` | move | P3 |
| `frontend/src/hooks/useProduct.ts` | `frontend/src/features/material/hooks/useProduct.ts` | move | P3 |
| `frontend/src/components/ProductSelect.tsx` | `frontend/src/features/material/ui/ProductSelect.tsx` | move | P2 |
| `frontend/src/types/material.ts` | `frontend/src/features/material/model/material.ts` | move | P3 |

说明：

- 当前路由仍然是 `material/product/*`，所以短期最稳的做法是把 product 先收编到 material 域，不额外分新 feature

---

## 10. settings / schedule / profile / ai-clip 域

| 当前文件 | 目标路径 | 动作 | 阶段 |
|---|---|---:|---:|
| `frontend/src/pages/Settings.tsx` | `frontend/src/features/settings/pages/SettingsPage.tsx` | move+rename | P2 |
| `frontend/src/pages/ScheduleConfig.tsx` | `frontend/src/features/schedule/pages/ScheduleConfigPage.tsx` | move+rename | P2 |
| `frontend/src/pages/ProfileManagement.tsx` | `frontend/src/features/profile/pages/ProfileManagementPage.tsx` | move+rename | P2 |
| `frontend/src/pages/AIClip.tsx` | `frontend/src/features/ai-clip/pages/AIClipPage.tsx` | move+rename | P2 |
| `frontend/src/hooks/useScheduleConfig.ts` | `frontend/src/features/schedule/hooks/useScheduleConfig.ts` | move | P3 |
| `frontend/src/hooks/useProfile.ts` | `frontend/src/features/profile/hooks/useProfile.ts` | move | P3 |
| `frontend/src/hooks/useAIClip.ts` | `frontend/src/features/ai-clip/hooks/useAIClip.ts` | move | P3 |

---

## 11. 顶层 hooks barrel

| 当前文件 | 目标路径 | 动作 | 阶段 |
|---|---|---:|---:|
| `frontend/src/hooks/index.ts` | `frontend/src/hooks/index.ts` | defer | P3 |

建议：

- 先保留一个兼容 barrel
- 等各 feature import 全部改完，再决定：
  - 删除
  - 或改成只导出 truly shared hooks

---

## 12. API / services / lib 层

| 当前文件 | 目标路径 | 动作 | 阶段 |
|---|---|---:|---:|
| `frontend/src/services/api.ts` | `frontend/src/lib/api/client/axiosClient.ts` | move+rename | P4 |
| `frontend/src/api/index.ts` | `frontend/src/lib/api/generated/index.ts` | move | P4 |
| `frontend/src/api/client.gen.ts` | `frontend/src/lib/api/generated/client.gen.ts` | move | P4 |
| `frontend/src/api/sdk.gen.ts` | `frontend/src/lib/api/generated/sdk.gen.ts` | move | P4 |
| `frontend/src/api/types.gen.ts` | `frontend/src/lib/api/generated/types.gen.ts` | move | P4 |
| `frontend/src/api/client/client.gen.ts` | `frontend/src/lib/api/generated/client/client.gen.ts` | move | P4 |
| `frontend/src/api/client/index.ts` | `frontend/src/lib/api/generated/client/index.ts` | move | P4 |
| `frontend/src/api/client/types.gen.ts` | `frontend/src/lib/api/generated/client/types.gen.ts` | move | P4 |
| `frontend/src/api/client/utils.gen.ts` | `frontend/src/lib/api/generated/client/utils.gen.ts` | move | P4 |
| `frontend/src/api/core/auth.gen.ts` | `frontend/src/lib/api/generated/core/auth.gen.ts` | move | P4 |
| `frontend/src/api/core/bodySerializer.gen.ts` | `frontend/src/lib/api/generated/core/bodySerializer.gen.ts` | move | P4 |
| `frontend/src/api/core/params.gen.ts` | `frontend/src/lib/api/generated/core/params.gen.ts` | move | P4 |
| `frontend/src/api/core/pathSerializer.gen.ts` | `frontend/src/lib/api/generated/core/pathSerializer.gen.ts` | move | P4 |
| `frontend/src/api/core/queryKeySerializer.gen.ts` | `frontend/src/lib/api/generated/core/queryKeySerializer.gen.ts` | move | P4 |
| `frontend/src/api/core/serverSentEvents.gen.ts` | `frontend/src/lib/api/generated/core/serverSentEvents.gen.ts` | move | P4 |
| `frontend/src/api/core/types.gen.ts` | `frontend/src/lib/api/generated/core/types.gen.ts` | move | P4 |
| `frontend/src/api/core/utils.gen.ts` | `frontend/src/lib/api/generated/core/utils.gen.ts` | move | P4 |

---

## 13. shared components / shared lib

| 当前文件 | 目标路径 | 动作 | 阶段 |
|---|---|---:|---:|
| `frontend/src/utils/error.ts` | `frontend/src/lib/utils/error.ts` | move | P5 |
| `frontend/src/utils/format.ts` | `frontend/src/lib/format/format.ts` | move | P5 |
| `frontend/src/types/electron.d.ts` | `frontend/src/lib/types/electron.d.ts` | move | P5 |

---

## 14. electron 层

这块当前边界清楚，**原则上不重组**，只建议未来统一命名。

| 当前文件 | 目标路径 | 动作 | 阶段 |
|---|---|---:|---:|
| `frontend/electron/main.ts` | `frontend/electron/main.ts` | keep | defer |
| `frontend/electron/preload.ts` | `frontend/electron/preload.ts` | keep | defer |
| `frontend/electron/backendLauncher.ts` | `frontend/electron/backendLauncher.ts` | keep | defer |
| `frontend/electron/backendLauncher.test.mjs` | `frontend/electron/backendLauncher.test.mjs` | keep | defer |
| `frontend/electron/launchers/start-backend-dev.bat` | `frontend/electron/launchers/start-backend-dev.bat` | keep | defer |
| `frontend/electron/launchers/start-backend-dev.sh` | `frontend/electron/launchers/start-backend-dev.sh` | keep | defer |
| `frontend/electron/launchers/start-backend-prod.bat` | `frontend/electron/launchers/start-backend-prod.bat` | keep | defer |
| `frontend/electron/launchers/start-backend-prod.sh` | `frontend/electron/launchers/start-backend-prod.sh` | keep | defer |
| `frontend/electron/tsconfig.json` | `frontend/electron/tsconfig.json` | keep | defer |
| `frontend/electron/main.js` | `frontend/electron/main.js` | defer（产物） | defer |
| `frontend/electron/main.js.map` | `frontend/electron/main.js.map` | defer（产物） | defer |
| `frontend/electron/preload.js` | `frontend/electron/preload.js` | defer（产物） | defer |
| `frontend/electron/preload.js.map` | `frontend/electron/preload.js.map` | defer（产物） | defer |
| `frontend/electron/backendLauncher.js` | `frontend/electron/backendLauncher.js` | defer（产物） | defer |
| `frontend/electron/backendLauncher.js.map` | `frontend/electron/backendLauncher.js.map` | defer（产物） | defer |

---

## 15. e2e 层

这块不建议现在跟着主工程一起大迁。  
当前建议是：**先保留，等 feature 收编稳定后再按 feature 命名对齐。**

| 当前文件 | 目标路径 | 动作 | 阶段 |
|---|---|---:|---:|
| `frontend/e2e/playwright.config.ts` | `frontend/e2e/playwright.config.ts` | keep | defer |
| `frontend/e2e/setup.ts` | `frontend/e2e/setup.ts` | keep | defer |
| `frontend/e2e/teardown.ts` | `frontend/e2e/teardown.ts` | keep | defer |
| `frontend/e2e/README.md` | `frontend/e2e/README.md` | keep | defer |
| `frontend/e2e/auth-*/*` | `frontend/e2e/auth-*/*` | keep | defer |
| `frontend/e2e/creative-*/*` | `frontend/e2e/creative-*/*` | keep | defer |
| `frontend/e2e/task-*/*` | `frontend/e2e/task-*/*` | keep | defer |
| `frontend/e2e/dashboard/*` | `frontend/e2e/dashboard/*` | keep | defer |
| `frontend/e2e/login/*` | `frontend/e2e/login/*` | keep | defer |
| `frontend/e2e/ai-clip-workflow/*` | `frontend/e2e/ai-clip-workflow/*` | keep | defer |
| `frontend/e2e/utils/*` | `frontend/e2e/utils/*` | keep | defer |

---

## 16. 推荐执行顺序（最小风险）

### P1

- `App.tsx`
- `providers/QueryProvider.tsx`
- `components/Layout.tsx`
- `features/auth/AuthRouteGate.tsx`
- `features/auth/*` 内部职责重排

### P2

- `pages/*`
- `components/*` 中明显业务组件

### P3

- `hooks/*`
- `types/material.ts`

### P4

- `api/*`
- `services/api.ts`

### P5

- `utils/*`
- creative 内部 ui/model 轻量收口
- shared components / copy

---

## 17. 一句话总结

> 这份文件级迁移表的核心策略是：先把 `AppShell/router/providers/theme` 抽到 `app/`，再把旧 `pages/hooks/components` 按业务域收编进 `features/`，最后统一 `lib/api` 与 shared 组件层。

