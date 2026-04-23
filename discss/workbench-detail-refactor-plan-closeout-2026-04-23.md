# Workbench / CreativeDetail 重构计划总收口

> 日期：2026-04-23  
> 对应 roadmap：`discss/workbench-refactor-roadmap-2026-04-23.md`  
> 总结范围：从 Workbench 高频视角/状态源修复，到 CreativeDetail 解耦，再到 diagnostics 行动面板升级。  

---

## 1. 前面几个 PR 属于哪个 plan

前面连续几个 PR 属于同一条主线：

> **Workbench / CreativeDetail 可执行重构路线图**

它不是单个 PRD，而是由 roadmap 拆出的 A/B/C/D/E 五个 slice 串起来的阶段性计划。

对应关系如下：

| Slice | 计划文件 | 测试规格 | 主要 commit / PR 语义 | 当前状态 |
| --- | --- | --- | --- | --- |
| Slice A：测试补强 | `.omx/plans/prd-workbench-slice-ab-2026-04-23.md` | `.omx/plans/test-spec-workbench-slice-ab-2026-04-23.md` | `5babe1e`：锁定 Workbench query / preset / route 行为 | 已完成 |
| Slice B：Workbench 状态源收敛 | `.omx/plans/prd-workbench-slice-ab-2026-04-23.md` | `.omx/plans/test-spec-workbench-slice-ab-2026-04-23.md` | `f02889d`：URL 成为 canonical query state，禁止未提交草稿进入 canonical state | 已完成 |
| Slice C：Workbench 页面结构拆分 | `.omx/plans/prd-workbench-slice-c-2026-04-23.md` | `.omx/plans/test-spec-workbench-slice-c-2026-04-23.md` | `65d119a`：拆出 SummaryCard / PresetBar / WorkbenchTable / DiagnosticsDrawer 等结构 | 已完成 |
| Slice D：CreativeDetail view-model 拆分 | `.omx/plans/prd-creative-detail-slice-d-2026-04-23.md` | `.omx/plans/test-spec-creative-detail-slice-d-2026-04-23.md` | `71cd132`：拆分 authoring / version-review / publish-diagnostics / navigation state | 已完成 |
| Slice E：diagnostics 行动面板 | `.omx/plans/prd-creative-diagnostics-action-panel-2026-04-23.md` | `.omx/plans/test-spec-creative-diagnostics-action-panel-2026-04-23.md` | `fe0d052`：Workbench / Detail diagnostics 增加推荐行动面板 | 已完成 |

相关但不属于 A/B/C/D/E 主计划的前置修复：

- `7f8df49`：Workbench 检索从前端窗口升级为服务端检索。
- `c919577`：修复“待审核 / 需返工”preset 参数失效并落回“全部”的问题。
- `149b83c`：删除临时迁移提示框。
- `43a118a`：修复 preset 循环后列表为空的问题。
- `cfeb843`：沉淀 Workbench 设计 review 与执行 roadmap。

这些前置修复是 roadmap 的输入事实；A/B/C/D/E 是正式收口执行链。

---

## 2. 本计划最终收口结论

本轮计划已经完成到 **可阶段性关闭**：

1. Workbench 已从“多状态源互相同步”收敛为“URL canonical query state”。
2. 高频视角 preset 的点击、往返、分页、排序、详情返回与 diagnostics route chrome 已被 E2E 锁定。
3. Workbench 页面结构已经拆成职责更清晰的组件，父页面仍保留唯一 canonical query state owner。
4. CreativeDetail 已完成第一层 view-model 拆分，核心数据/行为归属更清晰：
   - `useCreativeAuthoringModel`
   - `useCreativeVersionReviewModel`
   - `useCreativePublishDiagnosticsModel`
   - `useCreativeNavigationState`
5. Diagnostics 已从“解释型证据展示”升级为“行动建议 + 原始证据”的结构。
6. Workbench `diagnostics=runtime` 与 Detail `diagnostics=advanced` 的 URL 语义已保留。
7. Diagnostics drawer 不触发 submit composition；提交合成仍只属于主创作区。

因此，这个 plan 的主目标已经达成：  

> **不推翻作品中心模型，在保持现有用户行为的前提下，把 Workbench / Detail 从容易失控的页面实现，收敛为可维护、可验证、可继续演进的结构。**

---

## 3. 已验证的关键行为

本计划最终阶段验证过：

- `npm run typecheck`
- `npm run build`
- `npm run test:e2e -- e2e/creative-workbench/creative-workbench.spec.ts`
- `npm run test:e2e -- e2e/task-diagnostics/task-diagnostics.spec.ts`
- 合并后针对两组相关 E2E 的联合回归：50 passed
- LSP / tsc diagnostics：0 errors

核心回归覆盖：

- Workbench preset 从左到右、从右到左切换后可回到全部并显示完整列表。
- `waiting_review` / `needs_rework` 不再落回全部。
- 搜索、筛选、排序、分页与 preset 均基于服务端结果。
- diagnostics 打开/关闭只作为 route chrome，不污染业务 query state。
- 未提交 draft filter 不会因为打开 diagnostics 或切换 sort 被提升为 canonical state。
- Workbench diagnostics 推荐行动点击 preset 后继续保留 `diagnostics=runtime`。
- Detail diagnostics 推荐行动只能调用 retry / navigation / task-list 等既有动作。
- Detail diagnostics drawer 内不存在 `creative-submit-composition`。

---

## 4. 合并到 roadmap 的状态标记

Roadmap 中的阶段状态应更新为：

| Roadmap 阶段 | 对应 Slice | 状态 |
| --- | --- | --- |
| Phase 0：锁行为，补测试 | Slice A | 已完成 |
| Phase 1：收敛 Workbench 查询状态 | Slice B | 已完成 |
| Phase 2：拆 Workbench 页面结构 | Slice C | 已完成 |
| Phase 3：拆 CreativeDetail view-model 与区域职责 | Slice D | 已完成 |
| Phase 4：诊断区从说明页升级为行动面板 | Slice E | 已完成 |
| Phase 5：是否升级为 Tab / 子路由 | 后续评估项 | 暂不推进 |

Phase 5 暂不推进的原因：

- 当前单页 + drawer 的信息架构已经能覆盖主流程。
- 引入 tab / subroute 会扩大 URL 语义、returnTo、drawer 行为和 E2E 面。
- 目前更值得优先做的是真实业务能力补齐，而不是继续切页面结构。

---

## 5. 合并到总 PRD 的产品结论

总 PRD 应吸收以下阶段性结论：

### 5.1 Workbench 已成为作品中心主入口

当前 Workbench 不再只是“最近 200 条前端窗口”的列表，而是服务端检索驱动的作品操作台：

- 搜索、筛选、排序、分页、preset 都应视为服务端检索语义。
- URL 是页面状态的可分享 / 可返回 / 可刷新 truth。
- 高频视角是运营队列，不是一次性前端过滤按钮。

### 5.2 Task 退为诊断与执行承载面

任务页仍然重要，但不再是创作主入口：

- Workbench / Detail 承接业务主流。
- Task list / task detail 承接执行进度、失败重试、日志与排障。
- Detail 可以通过 diagnostics 跳转到 task，但 task 不回写作品定义本身。

### 5.3 Detail 是作品定义与证据聚合页

CreativeDetail 当前承担：

- 创作定义维护
- 素材编排
- 合成提交
- 版本结果查看
- 审核结论查看
- 发布池 / 发布诊断 / cutover 对账
- AIClip 入口

但这些职责已经通过 view-model 做了第一层归属拆分，因此当前结论是：

> **继续保持单页信息架构，不立即升级为 tab/subroute。**

### 5.4 Diagnostics 的产品语义升级

Diagnostics 不再只是“解释当前状态”，而是优先回答：

1. 当前是否有阻塞？
2. 阻塞在哪里？
3. 下一步应该点哪里？
4. 原始证据是什么？

推荐行动只允许复用已有安全动作：

- retry diagnostics
- open task diagnostics
- open task list
- switch Workbench preset

不得在 diagnostics drawer 内新增 submit composition 这类业务 mutation。

---

## 6. 后续不建议继续在本 plan 内扩边界

本计划到此应关闭，不建议继续顺手做：

- CreativeDetail tab/subroute 化。
- diagnostics 内新增执行/提交/发布等强动作。
- 新增后端 diagnostics API。
- 新增全局状态库。
- 重写 Workbench table 技术栈。

这些都应该作为新 plan 单独评估。

---

## 7. 推荐下一阶段

下一阶段不应继续“为了重构而重构”，而应回到业务能力：

1. 真实发布链路 / 发布池能力继续补齐。
2. CreativeDetail 主创作区的业务体验优化。
3. AIClip 与作品版本链路的进一步闭环。
4. 只有当 Detail 单页继续膨胀且出现明确使用/维护痛点时，再启动 tab/subroute 计划。

执行档位建议：

- 小 UI / 文案 / 局部 bug：直接做。
- 中等结构调整：短计划 + targeted verification。
- 涉及 URL / 状态机 / API / 数据模型：再进入 `ralplan`。
- 需要强闭环验收：再进入 `ralph`。

---

## 8. 最终状态

**Workbench / CreativeDetail 重构 roadmap 的 A/B/C/D/E 主链已收口完成。**

后续引用时，可以把本轮称为：

> **Creative Workbench & Detail IA Stabilization Plan（2026-04-23 收口版）**

