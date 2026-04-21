# Creative 渐进式重建重构总结

> 范围：Creative Progressive Rebuild Phase A ~ Phase D  
> 参考计划：
> - `.omx/plans/archive/prd-creative-progressive-rebuild-roadmap.md`
> - `.omx/plans/archive/prd-creative-progressive-rebuild-phase-b-pr-plan.md`
> - `.omx/plans/archive/prd-creative-progressive-rebuild-phase-c-pr-plan.md`
> - `.omx/plans/archive/prd-creative-progressive-rebuild-phase-d-pr-plan.md`
> 更新日期：2026-04-18

## 1. 这次重构的核心目标

这轮重构的核心，不是“再加几个页面”，而是把系统的业务主语义从 **Task 驱动**，逐步迁移到 **Creative 驱动**：

- 用 `CreativeItem / CreativeVersion / CheckRecord / PublishPoolItem` 表达业务真相；
- 让 `Task` 退回执行载体与诊断对象；
- 让 `Creative Workbench` 成为用户的主工作台；
- 让 AIClip、人工检查、发布调度都围绕作品版本运转。

一句话总结：

> **系统已经从“以任务为中心的执行界面”，重构为“以作品为中心的创作、审核、发布工作流”。**

---

## 2. 这次重构做了什么

## Phase A：搭起 Creative 骨架与工作台入口

这一阶段完成了作品域的最小落地：

- 新增 Creative 相关后端骨架与最小 API；
- 在 `Task` 上补齐 `creative_item_id`、`creative_version_id`、`task_kind` 等关联语义；
- 新增前端：
  - `CreativeWorkbench`
  - `CreativeDetail`
- 在不破坏旧 Task 视图的前提下，把 Creative 页面并存接入导航与路由。

阶段结果：

- 系统第一次具备“作品对象”；
- 至少一条 Task 可以映射到 Creative；
- 用户可以从 `/creative/workbench` 进入作品工作台，而旧 Task 页面仍可用。

---

## Phase B：补齐版本管理与人工检查闭环

这一阶段把 Creative 从“展示对象”升级为“业务对象”：

- 新增 `CheckRecord` 及审核相关 API / service；
- 固化版本 invariant：
  - 检查只作用于当前版本；
  - 非当前版本不能 approve；
  - 新版本生成后旧批准结论失效；
  - `REWORK_REQUIRED` 必须带 `rework_type`；
- 把普通 composition 成功/失败写回作品域：
  - success -> 新版本 -> `WAITING_REVIEW`
  - failure -> 保留 Task 执行失败真相，但不污染审核语义；
- 前端新增：
  - `VersionPanel`
  - `CheckDrawer`
  - 版本历史、审核、返工、拒绝等交互。

阶段结果：

- 作品有了“当前版本”与“审核状态”；
- 生成、审核、返工、再审核形成闭环；
- Task 不再承担业务判断主语义。

---

## Phase C：把发布从 Task.ready 切到 Publish Pool

这一阶段完成了发布链路的真相切换：

- 新增 `PublishPoolItem`，明确“可发布候选”不再直接等于 `Task.ready`；
- 新增 `PublishExecutionSnapshot`，在发布前冻结 version / account / profile / task 等输入真相；
- 新增：
  - `publish_pool_service.py`
  - `publish_planner_service.py`
  - 对应 API / schema / migration；
- 调度器切到 pool 驱动，并补齐：
  - feature flag
  - kill switch
  - shadow read
  - parity / diagnostics
- 前端补齐发布池可见性与 cutover 诊断投影。

阶段结果：

- “业务可发布”与“执行任务状态”正式解耦；
- 调度器主候选源从 Task 切到 Publish Pool；
- 发布任务绑定具体版本且可追溯；
- 出现问题时可以回退到旧调度路径。

---

## Phase D：把 AIClip 接入作品工作流，并迁移默认主入口

这一阶段完成了用户主路径迁移：

- 新增 `ai_clip_workflow_service.py` 与 `creative_workflows` API；
- 保持 `AIClipService` 继续做工具层，不把作品业务状态机塞回工具层；
- 支持从 Creative 页面发起 AIClip workflow，并把输出提交为新版本；
- 前端新增：
  - `AIClipWorkflowPanel`
  - `useCreativeWorkflow`
- `TaskList / TaskDetail` 被重新定位为执行 / 诊断视图；
- 根路由与登录后默认落点切到 `/creative/workbench`；
- `Dashboard` 降级为运行态观察页面，不再是默认业务起点。

阶段结果：

- AIClip 不再只是孤立工具页，而是作品版本生产链的一部分；
- 用户主入口正式迁移到 Creative Workbench；
- Task 页面保留诊断价值，但不再承担主工作台角色。

---

## 3. 横向上还做了哪些收口

除四个阶段主线外，这轮重构还完成了这些横向收口：

### 3.1 OpenAPI / 前端 SDK 对齐

围绕新增的 Creative / Review / Publish Pool / Workflow 接口，更新了：

- `frontend/src/api/core/serverSentEvents.gen.ts`
- `frontend/src/api/index.ts`
- `frontend/src/api/sdk.gen.ts`
- `frontend/src/api/types.gen.ts`

这些文件属于 **根据后端 OpenAPI contract 自动生成 / 同步的前端 API 产物**，用于让前端 hook、页面与后端 schema 保持一致。

### 3.2 测试链路补齐

后端新增或扩展了针对以下主题的自动化测试：

- Creative versioning
- Creative review flow
- composition -> creative writeback
- publish pool
- publish execution snapshot
- scheduler cutover
- AIClip workflow
- OpenAPI contract parity

前端新增或扩展了 E2E：

- `creative-workbench`
- `creative-review`
- `creative-version-panel`
- `publish-pool`
- `publish-cutover`
- `ai-clip-workflow`
- `task-diagnostics`
- `creative-main-entry`
- 以及 login / auth-routing / auth-shell 基线回归

### 3.3 导航与权限路径对齐

为了配合默认入口迁移，还同步对齐了：

- `frontend/src/App.tsx`
- `frontend/src/components/Layout.tsx`
- `frontend/src/features/auth/AuthRouteGate.tsx`

确保 active / grace 等授权态下，新的默认主入口仍然可用且路径一致。

---

## 4. 这轮重构最终改变了什么

从结果看，这轮重构把系统的核心工作流改成了下面的结构：

### 重构前

- Task 是主列表、主入口、主业务对象；
- 审核、版本、发布候选语义都容易被执行状态混在一起；
- AIClip 更像孤立工具页；
- 发布是否可执行主要依赖 `Task.ready`。

### 重构后

- Creative Workbench 是主入口；
- `CreativeItem / CreativeVersion` 是业务真相；
- `CheckRecord` 承担审核证据；
- `PublishPoolItem` 承担可发布候选；
- `PublishExecutionSnapshot` 承担发布前冻结输入；
- `Task` 只负责执行、追踪、诊断；
- AIClip 进入作品版本工作流。

---

## 5. 本轮重构涉及的主要代码面

### 后端新增 / 收口

- API
  - `backend/api/creative_review.py`
  - `backend/api/creative_publish_pool.py`
  - `backend/api/creative_workflows.py`
- Services
  - `backend/services/creative_review_service.py`
  - `backend/services/creative_generation_service.py`
  - `backend/services/publish_pool_service.py`
  - `backend/services/publish_planner_service.py`
  - `backend/services/ai_clip_workflow_service.py`
- Domain / migration / schema
  - `backend/models/__init__.py`
  - `backend/schemas/__init__.py`
  - `backend/migrations/025_*` ~ `029_*`

### 前端新增 / 收口

- Creative 页面与组件
  - `frontend/src/features/creative/pages/CreativeWorkbench.tsx`
  - `frontend/src/features/creative/pages/CreativeDetail.tsx`
  - `frontend/src/features/creative/components/VersionPanel.tsx`
  - `frontend/src/features/creative/components/CheckDrawer.tsx`
  - `frontend/src/features/creative/components/AIClipWorkflowPanel.tsx`
- Hook / type
  - `frontend/src/features/creative/hooks/useCreatives.ts`
  - `frontend/src/features/creative/hooks/useCreativeWorkflow.ts`
  - `frontend/src/features/creative/types/creative.ts`
- 导航 / 页面语义迁移
  - `frontend/src/App.tsx`
  - `frontend/src/components/Layout.tsx`
  - `frontend/src/pages/Dashboard.tsx`
  - `frontend/src/pages/TaskList.tsx`
  - `frontend/src/pages/task/TaskDetail.tsx`

---

## 6. 本次重构的边界与保留项

这轮重构也明确保留了一些边界，没有把所有东西都推翻重写：

- 没有重写 `PublishService.publish_task()` 的叶子执行逻辑；
- 没有让 `AIClipService` 直接拥有 Creative 域状态；
- 没有删除 Task 页面，只是让它下沉为执行 / 诊断视图；
- 没有把 remote/control-plane 规划混进这轮本地 Creative rebuild。

也就是说，这次重构采用的是：

> **“新建上层业务真相 + 渐进替换主入口 + 复用既有执行底座”**

而不是“大爆炸式重写”。

---

## 7. 一句话验收结论

这轮重构已经完成了从 **Phase A 到 Phase D** 的主线落地，最终交付的是：

- 一个以作品为中心的工作台；
- 一条围绕版本、审核、发布池、调度器、AIClip workflow 的主业务链；
- 以及一个明确退回执行 / 诊断角色的 Task 体系。

如果只保留一句总结，可以写成：

> **这次重构完成了“Task-first” 到 “Creative-first” 的系统迁移。**
