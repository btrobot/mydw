# A~D + Phase E 最终验收缺口清单

> 生成时间：2026-04-18  
> 目的：对照主线规划（Creative Progressive Rebuild Phase A~D）与前端收口规划（Phase E），梳理当前**仍未彻底收口**的事项。  
> 结论：**未发现主线功能性漏项，当前缺口主要集中在验收归档、仓库清洁、手工联调与少量工程技术债。**

---

## 1. 范围

本清单覆盖两套规划：

### 主线规划
- `.omx/plans/prd-creative-progressive-rebuild-roadmap.md`
- 对应阶段：**Phase A ~ Phase D**

### 前端收口规划
- `.omx/plans/prd-frontend-ui-ux-closeout-phase-e-pr-plan.md`
- 对应阶段：**Phase E**

---

## 2. 当前总体判断

### 2.1 已完成判断

#### 主线 A~D
当前判断：**功能目标已完成**

已具备的能力包括：
- Creative 骨架、Workbench、Detail、Task ↔ Creative 映射
- 版本管理与人工检查闭环
- composition -> creative writeback
- Publish Pool / PublishExecutionSnapshot / scheduler cutover
- AIClip workflow 接入 Creative 主链
- 默认主入口迁移到 Creative Workbench
- Task 下沉为执行 / 诊断视图

#### 前端收口 Phase E
当前判断：**规划目标已基本完成**

已具备的能力包括：
- IA / 命名 / CTA / 文案整体收口
- Workbench 工作台化（搜索 / 筛选 / 排序 / 分页）
- Detail / Dashboard / Task diagnostics 边界清晰化
- Workbench / Detail / Dashboard / Auth 四态清晰化
- AIClip workflow 产品化表达与响应式基线整修
- 栈内能力优先，未见明显新增通用基础 UI 壳组件

### 2.2 当前缺口判断

> 当前没有发现“规划里承诺了但没有落地”的大块功能缺口。  
> 当前缺口主要属于：

1. **验收归档不足**
2. **仓库状态未完全清洁**
3. **手工联调验收仍有空白**
4. **存在少量非阻塞工程技术债**

---

## 3. 已有验证证据

### 3.1 主线 A~D 核心后端验证
已验证通过：

```powershell
python -m pytest backend/tests/test_creative_task_mapping.py backend/tests/test_creative_versioning.py backend/tests/test_creative_review_flow.py backend/tests/test_composition_creative_writeback.py backend/tests/test_publish_pool_service.py backend/tests/test_publish_execution_snapshot.py backend/tests/test_publish_scheduler_cutover.py backend/tests/test_ai_clip_workflow.py backend/tests/test_creative_workflow_contract.py
```

结果：
- **35 passed**

### 3.2 前端 Phase E 核心验证
已验证通过：

```powershell
cd frontend
npm run typecheck
npm run build
```

结果：
- typecheck ✅
- build ✅

### 3.3 前端 Phase E 回归切片
已验证通过：

```powershell
cd frontend
E2E_BASE_URL=http://127.0.0.1:4173 node node_modules/playwright/cli.js test -c e2e/playwright.config.ts \
  e2e/creative-main-entry/creative-main-entry.spec.ts \
  e2e/creative-workbench/creative-workbench.spec.ts \
  e2e/creative-review/creative-review.spec.ts \
  e2e/creative-version-panel/creative-version-panel.spec.ts \
  e2e/publish-pool/publish-pool.spec.ts \
  e2e/publish-cutover/publish-cutover.spec.ts \
  e2e/task-diagnostics/task-diagnostics.spec.ts \
  e2e/ai-clip-workflow/ai-clip-workflow.spec.ts \
  e2e/login/login.spec.ts \
  e2e/auth-routing/auth-routing.spec.ts \
  e2e/auth-shell/auth-shell.spec.ts \
  e2e/auth-error-ux/auth-error-ux.spec.ts
```

结果：
- **82 passed**

---

## 4. 最终验收缺口清单

## 4.1 P0：必须收口的缺口

### Gap-01：缺少一份正式的 A~D 最终验收归档
**状态：未完全收口**

当前已有：
- `docs/creative-progressive-rebuild-final-summary.md`

问题：
- 这份更偏“总结”，还不是严格意义上的 completion audit / acceptance checklist。
- 如果后续要做交接、回顾、追责、发布判断，缺少一份更结构化的“主线最终验收单”。

建议动作：
- 补一份例如：
  - `docs/creative-progressive-rebuild-completion-audit.md`
  - 或 `docs/creative-progressive-rebuild-acceptance-checklist.md`

建议内容：
- A/B/C/D 分阶段目标达成情况
- 对应测试/证据链接
- 未解决风险
- 非目标范围说明

---

### Gap-02：缺少一份正式的 Phase E 最终验收归档
**状态：未完全收口**

当前已有：
- `.omx/plans/prd-frontend-ui-ux-closeout-phase-e-pr-plan.md`
- 相关回顾文档与 commit 记录

问题：
- 缺少一份正式的“Phase E final summary / acceptance checklist”。
- 目前更多是执行过程、commit 结果、临时回顾，并非正式归档件。

建议动作：
- 补一份例如：
  - `docs/frontend-ui-ux-closeout-final-summary.md`
  - 或 `docs/frontend-ui-ux-closeout-acceptance-checklist.md`

建议内容：
- E1~E5 对应结果
- 是否满足 Exit Criteria / Full Exit Gate
- focused e2e 覆盖情况
- 剩余风险与后续建议

---

### Gap-03：仓库未完全 clean
**状态：未收口**

当前工作区仍有：
- `remote/remote-shared/openapi/phase0-manifest.json`
- `remote/remote-shared/openapi/phase1-manifest.json`
- `reports/`（本轮分析文档）
- `frontend/e2e/reports/`（测试产物，运行验证后会再次生成）

问题：
- 即便规划目标已完成，仓库状态不 clean 会影响真正意义上的“收口完成”。
- `frontend/e2e/reports/` 明显属于运行产物，不应混入最终功能提交边界。
- `remote manifest` 变更当前看不属于 A~D / Phase E 主线收口本身。

建议动作：
- 删除或忽略 `frontend/e2e/reports/`
- 决定 `reports/` 是否纳入版本管理
- 单独判断并处理 `remote/remote-shared/openapi/phase0-manifest.json` / `phase1-manifest.json`

---

## 4.2 P1：建议补完的验收缺口

### Gap-04：缺少真实 backend + Electron/本地运行态的手工联调验收
**状态：仍有空白**

当前自动化已较完整，但仍缺少一类证据：
- 在真实 backend 会话下
- 以真实 auth / workbench / detail / AIClip / dashboard / task diagnostics 路径
- 做一遍手工联调验收

为什么它重要：
- 自动化多数使用 mock / controlled preview 环境
- 真实运行态仍可能暴露：
  - auth session 行为细节
  - Electron 非最大化窗口布局问题
  - /api 代理环境问题
  - 真数据下的页面密度或状态回退问题

建议动作：
- 做一次最小人工走查，并记录结果：
  1. 登录
  2. 进入 workbench
  3. 打开 detail
  4. 发起 AIClip workflow
  5. 查看 dashboard
  6. 进入 task diagnostics 再返回 creative 主路径

---

### Gap-05：Phase E 口径存在“PR-E6”编号漂移
**状态：管理尾巴未完全收口**

问题：
- 正式计划文件只定义了 `PR-E1 ~ PR-E5`
- 后续执行中又出现“PR-E6”的口头说法
- 这会影响回顾、验收、后续追踪的清晰度

当前建议口径：
- **正式计划：E1 ~ E5**
- 后续补充的 `1f0aaab`：作为 **Phase E closeout commit** 处理
- 不再把它当成“原计划中的正式 E6 条目”

建议动作：
- 在最终 Phase E summary 里写清楚这个约定

---

## 4.3 P2：非阻塞工程技术债

### Gap-06：FastAPI 生命周期 API 仍有 deprecated 用法
**状态：非阻塞**

当前验证中可见：
- `on_event("startup")`
- `on_event("shutdown")`

问题：
- 属于未来升级兼容性风险
- 不阻塞当前规划验收，但属于技术债

建议动作：
- 后续改为 lifespan handlers

---

### Gap-07：多处 `datetime.utcnow()` deprecation
**状态：非阻塞**

问题：
- 当前测试通过，但存在未来 Python/依赖升级的兼容性风险

建议动作：
- 后续替换为 timezone-aware UTC 时间

---

### Gap-08：运行配置仍有默认安全告警
**状态：非阻塞**

当前警告：
- `COOKIE_ENCRYPT_KEY` 使用默认值

问题：
- 本地开发可接受
- 作为真正交付/运行基线，不应长期保留默认安全值

建议动作：
- 在 `.env` / runtime docs 中明确收口

---

### Gap-09：前端构建仍有大 chunk 警告
**状态：非阻塞**

问题：
- 不影响当前规划完成功能
- 但说明后续还可做 code-splitting / chunk 拆分优化

建议动作：
- 后续做性能优化时再处理

---

## 5. 不算缺口、但需要注意的事项

以下内容**不应误判为主线/Phase E 未完成**：

1. `frontend/e2e/reports/`
   - 这是测试运行产物，不是规划漏项

2. `reports/`
   - 这是本轮人工分析/回顾文档输出目录，不是功能漏项

3. `remote/remote-shared/openapi/phase0-manifest.json` / `phase1-manifest.json`
   - 当前看属于另一条 remote/openapi 文档清单更新，不应直接算作 A~D 或 Phase E 功能遗漏

---

## 6. 最终判断

### 功能完成度判断

| 规划 | 结论 |
|---|---|
| Creative Progressive Rebuild（Phase A~D） | 已完成 |
| Frontend UI/UX Closeout（Phase E） | 已基本完成 |

### 当前主要缺口类型

| 类型 | 是否阻塞“规划完成” | 说明 |
|---|---|---|
| 功能漏项 | 否 | 当前未发现明确漏项 |
| 验收归档不足 | 是，影响正式收口质量 | 建议补正式 completion audit / final summary |
| 仓库不 clean | 是，影响真正收尾 | 需处理 reports、e2e/reports、remote manifests |
| 手工联调空白 | 中等 | 自动化较完整，但真实运行态证据仍值得补 |
| 工程技术债 | 否 | 属于后续优化项 |

---

## 7. 建议下一步顺序

### 推荐顺序
1. **补正式验收归档文档**
   - A~D completion audit
   - Phase E final summary / acceptance checklist

2. **整理仓库状态**
   - 清理 `frontend/e2e/reports/`
   - 决定 `reports/` 是否纳入版本管理
   - 单独处理 remote manifests

3. **补一轮最小手工联调验收**
   - 登录 -> workbench -> detail -> AIClip -> dashboard -> task diagnostics

4. **把技术债列成后续 backlog**
   - FastAPI lifespan
   - timezone-aware datetime
   - security config baseline
   - frontend chunk optimization

---

## 8. 一句话结论

> 现在的问题已经不是“主线和前端收口有没有做完”，而是“怎么把已经做完的东西，正式验收、正式归档、正式收尾”。
