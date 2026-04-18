# Creative 渐进式重建 / Frontend 收口：最初规划与开发过程回顾

> 生成时间：2026-04-18  
> 生成位置：`reports/creative-rebuild-plan-and-dev-history-2026-04-18.md`  
> 目的：把这轮重构**最初怎么规划**、**后来怎么拆 PR**、**实际怎么推进**，按阶段整理成一份可回顾文档。

---

## 1. 一句话总览

这轮工作一开始的正式目标，不是“多做几个页面”，而是把系统从 **Task-first** 的执行视角，渐进式迁移到 **Creative-first** 的业务视角：

- `CreativeItem / CreativeVersion / CheckRecord / PublishPoolItem` 表达业务真相；
- `Task` 下沉为执行与诊断载体；
- `CreativeWorkbench` 成为主工作台；
- AIClip、审核、发布围绕作品版本运转；
- 最后再单独做一轮 **Frontend UI/UX Closeout（Phase E）**，把前端界面按技术栈最佳实践收口。

---

## 2. 最初的正式规划是什么

### 2.1 最初的路线图来源

本轮工作的正式规划基础主要来自以下文档：

- `.omx/plans/prd-creative-progressive-rebuild-roadmap.md`
- `.omx/plans/prd-creative-progressive-rebuild-phase-a-pr-plan.md`
- `.omx/plans/prd-creative-progressive-rebuild-phase-b-pr-plan.md`
- `.omx/plans/prd-creative-progressive-rebuild-phase-c-pr-plan.md`
- `.omx/plans/prd-creative-progressive-rebuild-phase-d-pr-plan.md`
- 后续补充：`.omx/plans/prd-frontend-ui-ux-closeout-phase-e-pr-plan.md`

### 2.2 最初为什么不是 3 个阶段，而是 4 个阶段

在 2026-04-16 的正式路线图里，结论是：**不强行压成 3 阶段，而采用 4 阶段**。

原因是中段风险实际上分成三团，不能混在一起做：

1. **业务真相建立**：先把 Creative / Version / Check 的关系做稳；
2. **运行时主链切换**：发布池、snapshot、scheduler cutover 风险很高；
3. **入口迁移与工作流接入**：AIClip workflow 和主入口迁移属于另一类产品/交互风险。

所以最初正式规划是：

- **Phase A：Creative 骨架与工作台雏形**
- **Phase B：版本管理与人工检查闭环**
- **Phase C：发布池与调度器切换**
- **Phase D：AIClip 工作流化与主入口迁移**

### 2.3 Phase A ~ D 的原始目标

#### Phase A
建立最小 Creative 域骨架，让系统第一次具备“作品对象”，并在不破坏旧 Task 入口的前提下增加：

- `CreativeWorkbench`
- `CreativeDetail`
- Task 与 Creative 的关联字段
- 最小 Creative API / 路由 / 导航入口

#### Phase B
把 Creative 从“展示对象”升级成“业务对象”，补齐：

- 版本真相
- 人工检查闭环
- composition -> creative writeback
- 版本历史 / approve / rework / reject 前端交互

#### Phase C
把“业务可发布”从 `Task.ready` 中解耦出来，建立：

- `PublishPoolItem`
- `PublishExecutionSnapshot`
- pool 驱动的 scheduler cutover
- feature flag / kill switch / shadow read / parity diagnostics

#### Phase D
让 AIClip 真正进入作品工作流，并迁移主入口：

- AIClip workflow 围绕 Creative / Version 运行
- Task 页面下沉为执行 / 诊断视图
- 默认业务入口切到 `CreativeWorkbench`

---

## 3. 为什么后来又加了 Phase E

在 A ~ D 跑通后，前端虽然已经完成 **Creative-first** 迁移，但界面仍然带有明显“过渡期 / 诊断台”痕迹，主要问题是：

- 页面职责还在靠解释型 `Alert` 来说明；
- Workbench / Detail / Dashboard / Task diagnostics 的边界不够清晰；
- 业务信息和高级诊断信息混在一起；
- Auth 页面更像技术后台，不像产品入口；
- AIClip 还带工具面板心智；
- 一些状态失败被伪装成 empty / idle；
- 整体还没有完全按 `Ant Design / ProComponents / React Router / React Query` 的最佳实践收口。

所以后面补了一份独立规划：

- `.omx/plans/prd-frontend-ui-ux-closeout-phase-e-pr-plan.md`

Phase E 的正式目标不是“重做视觉”，而是：

- 统一信息架构、页面布局模式、状态反馈、文案语言；
- 优先复用栈内现成能力；
- 不新增技术栈已经提供的基础 UI 壳组件；
- 只抽业务域组件；
- 统一 workbench / detail / dashboard / task diagnostics 的职责边界；
- 把业务信息与高级诊断信息分层。

Phase E 最初规划为 **5 个 PR**：

- **PR-E1**：信息架构 / 导航命名 / 文案基线收口
- **PR-E2**：Workbench 工作台能力与栈内列表模式对齐
- **PR-E3**：Detail / Dashboard / Task diagnostics 职责分层收口
- **PR-E4**：统一页面四态反馈 + Auth 产品化表达
- **PR-E5**：AIClip workflow 产品化收尾 + 响应式基线整修

> 说明：正式计划文件里没有单列 `PR-E6`。后续实际开发中，“剩余 Phase E / 前端收口改动”又形成了一次追加 closeout commit，可视为 Phase E 的尾声收口，而不是最初规划里的独立 PR。

---

## 4. 实际开发过程：按阶段回顾

这一轮工作的真实推进方式，可以概括为：

1. **先用 ralplan 把阶段拆成可执行 PR 计划**；
2. **再按 PR 用 ralph 顺序推进实现**；
3. 每个 PR 尽量做到：
   - 边界清楚
   - 可验证
   - 可回滚
4. 每个阶段都伴随：
   - `typecheck`
   - `build`
   - focused tests / e2e
   - 验收补证 / 文档收口 / commit

### 4.1 Phase A：Creative 骨架与工作台雏形

**核心交付：**

- 把 Creative 域骨架接进现有系统；
- 增加 workbench / detail；
- 保持旧 Task 页面仍可用；
- 证明“Task 可以映射到 Creative”。

**开发过程特征：**

- 先做最小接入，不越界进入 review / publish pool / AIClip workflow；
- 前端有一轮明显的“补证 / 验收增强”，说明团队对阶段 A 的证明集要求比较高。

**代表性提交：**

- `a3b4207` Restore Phase A proof coverage for the creative workbench
- `9ae7ece` Confirm the Phase A creative workbench frontend is ready for handoff
- `5340f04` Close PR-3 proof gaps before Phase A sign-off
- `e1561c6` Seal Phase 1 acceptance evidence before the rebuild advances

**阶段结果：**

- 系统第一次有了作品工作台与作品详情；
- Creative 页面与旧 Task 页面并存；
- 为后续版本、审核、发布池奠定了落点。

### 4.2 Phase B：版本管理与人工检查闭环

**最初规划：**

Phase B 被拆成 3 个 PR：

- **PR-B1**：版本 invariant 与 review 后端契约
- **PR-B2**：普通 composition 写回作品域
- **PR-B3**：Review UI / VersionPanel / CheckDrawer / Phase B 收口

**实际开发过程：**

先稳住业务 invariant，再接执行写回，最后补前端 review 交互与阶段收口。

**代表性提交：**

- `3b80b9d` Enforce Creative review invariants before Phase B writeback
- `e445eb5` Preserve creative review truth when composition callbacks write back results
- `4bdb00d` Expose creative review history without collapsing task diagnostics into business truth
- `964024f` Keep Phase B exit verification hermetic across local auth artifacts

**阶段结果：**

- `CreativeVersion`、`CheckRecord`、审核状态机稳定下来；
- composition 成功/失败可以写回作品域；
- 前端出现了版本历史、审核、返工、拒绝交互；
- Task 不再承担业务判断主语义。

### 4.3 Phase C：发布池与调度器切换

**最初规划：**

Phase C 被拆成 4 个 PR，核心思想是：**先建立候选真相，再切运行时主链**。

- 建立 `PublishPoolItem`
- 建立 `PublishExecutionSnapshot`
- 再做 scheduler cutover 保护
- 最后补前端可见性与诊断投影

**实际开发过程：**

- 先确认 pool truth；
- 再绑定 publish execution snapshot；
- 再做 scheduler cutover、kill switch、shadow read、diagnostics；
- 最后做前端 cutover visibility 收口。

**代表性提交：**

- `1208aab` Establish Creative publish-pool truth before scheduler cutover
- `d266481` Bind publish execution to frozen pool snapshots before scheduler cutover
- `e99adae` Cut scheduler over to publish-pool selection with kill switch and diagnostics
- `dddbc48` Close Phase C with front-end publish-pool visibility and cutover diagnostics

**阶段结果：**

- 业务可发布不再直接等于 `Task.ready`；
- 调度器主候选源迁移到 Publish Pool；
- 发布前冻结输入真相，增强可追溯性；
- 整个 cutover 有保护、观测、回退能力。

### 4.4 Phase D：AIClip 工作流化与主入口迁移

**最初规划：**

Phase D 被拆成 4 个 PR：

- **D1**：AIClip workflow 后端 contract / orchestration
- **D2**：前端 workflow 接入（Creative 内发起、提交新版本）
- **D3**：Task 下沉为执行/诊断视图 + Workbench readiness hardening
- **D4**：默认主入口迁移到 `CreativeWorkbench` + Phase D 收口

**实际开发过程：**

先让 AIClip 能围绕作品工作流跑起来，再调整 Task 语义，最后才 flip 默认入口。

**代表性提交：**

- `40d0a7c` Route AI clip outputs through creative version workflow
- `92d66a1` Enable AIClip workflow submission from Creative surfaces
- `f60436a` Demote Task pages behind creative-first diagnostics flow
- `f1d236b` Move daily entry onto Creative Workbench before Phase D closeout

**阶段结果：**

- AIClip 从孤立工具页变成作品工作流的一部分；
- Task 页面正式下沉为执行 / 诊断视图；
- 默认业务入口切到 `CreativeWorkbench`；
- 用户主路径完成了 Task-first -> Creative-first 的迁移。

### 4.5 Phase E：前端 UI/UX 收口 + 技术栈最佳实践对齐

**最初规划：**

Phase E 最初规划为 5 个 PR，目标不是“视觉翻新”，而是“收口”。

#### PR-E1：IA / 导航命名 / 文案基线

**代表性提交：**

- `ef7b0d7` Make the workbench and auth entry read like the product path

**结果：**

- Workbench / Dashboard / Task / Auth 的命名与入口语义更清楚；
- 文案更偏产品语言，而不是开发调试语言。

#### PR-E2：Workbench 工作台能力与 ProTable 对齐

**结果特征：**

- Workbench 从“可浏览”变成“可筛选 / 可排序 / 可分页 / 可搜索”的主工作台；
- 重点是优先复用 `PageContainer + ProTable`，而不是自造通用壳。

> 注：从最近提交标题看，PR-E2 的语义已经被后续 E4 closeout commit 吸收了很大一部分，因此在提交历史里没有像 E1/E3/E5 那样单独留下一个非常明确的 commit 标题。

#### PR-E3：Detail / Dashboard / Task diagnostics 分层

**代表性提交：**

- `c8038cd` Clarify creative detail vs diagnostics surfaces

**结果：**

- Detail 默认先呈现业务信息；
- 高级诊断信息下沉；
- Dashboard / Task diagnostics 的职责边界更清晰。

#### PR-E4：统一页面四态 + Auth 产品化

**代表性提交：**

- `1f0aaab` Make Phase E closeout surface explicit auth and workbench failure states

**结果：**

- loading / empty / error / success 更明确；
- 请求失败不再伪装成 empty / idle；
- Auth/Login/AuthStatus 更像产品入口；
- focused e2e 与现状对齐。

#### PR-E5：AIClip workflow 产品化 + 响应式整修

**代表性提交：**

- `d115836` Make the AIClip flow readable as a product workflow on smaller screens

**结果：**

- AIClip 的主链表达更像业务工作流；
- 高级参数退居次级区域；
- 小窗口 / 非最大化窗口下的基本可用性增强。

---

## 5. 这轮开发过程的几个关键特点

### 5.1 先规划，再按 PR 串行推进

这一轮不是“边写边猜”，而是：

- 先用 roadmap 确定大阶段；
- 再把每个阶段拆成 PR 计划；
- 然后按 PR 顺序推进；
- 每个阶段都在做“收口、补证、验收、commit”。

### 5.2 不追求一次性大翻新，而是渐进式替换

整个过程都遵守了一个原则：

- **新建目录 / 渐进替换 / 复用底层能力**

也就是说，没有直接推翻 Task / AIClip / Dashboard 的既有底层，而是在上层逐步建立新的业务真相与入口结构。

### 5.3 风险最高的地方都被单独拆开了

尤其是：

- review invariant
- composition writeback
- publish pool truth
- execution snapshot
- scheduler cutover
- AIClip workflow 接入
- 主入口 flip

这些都没有被糊成一个超大 PR，而是拆开推进，这也是这轮开发能够持续收口的关键原因。

### 5.4 前端最后单独做了一轮“最佳实践对齐”

这说明团队没有把“功能跑通”误当成“项目完成”。

A ~ D 解决的是业务真相与系统路径；
E 解决的是：

- 页面职责
- 技术栈对齐
- 信息分层
- 状态反馈
- Auth 产品化
- AIClip 界面心智收尾

这是一次明显的“把工程实现进一步拉回产品界面”的动作。

---

## 6. 当前可以怎样理解这轮工作的完成状态

截至当前仓库状态，可以把这轮工作理解为两层：

### 第一层：主重构主线已完成

- Phase A ~ D：Creative progressive rebuild 主线已完成；
- 系统已经完成 Task-first -> Creative-first 迁移；
- 业务真相、发布真相、AIClip workflow、主入口迁移都已落地。

### 第二层：前端收口已基本完成

- Phase E 的 5 个规划目标已基本落地；
- 另外还有一次“remaining frontend closeout”收口提交；
- 当前前端不再只是“能跑通”，而是已经进入“按技术栈最佳实践组织页面”的状态。

### 当前工作区剩余非本阶段内容

当前仍有两个未提交文件，不属于这份回顾中的前端/重构主线收口：

- `remote/remote-shared/openapi/phase0-manifest.json`
- `remote/remote-shared/openapi/phase1-manifest.json`

---

## 7. 最终回顾：从最初规划到实际开发，路线有没有跑偏？

**整体没有跑偏。**

反而可以说，实际开发过程基本沿着最初规划的风险顺序推进：

1. 先建立 Creative 域骨架；
2. 再建立版本与审核真相；
3. 再切发布候选与调度链；
4. 再把 AIClip 接入业务主线并迁移入口；
5. 最后单独做一轮前端 UI/UX 收口。

这说明最初的分期设计本身是有效的：

- **A ~ D** 解决“业务真相”和“系统主链”；
- **E** 解决“界面表达”和“技术栈最佳实践收口”。

如果只保留一句总结，可以写成：

> 这轮开发从最初规划到实际落地，完成了系统主语义从 **Task-first** 向 **Creative-first** 的迁移，并在主链稳定后，额外完成了一轮前端 UI/UX 与技术栈最佳实践收口。

---

## 8. 参考文档

- `.omx/plans/prd-creative-progressive-rebuild-roadmap.md`
- `.omx/plans/prd-creative-progressive-rebuild-phase-a-pr-plan.md`
- `.omx/plans/prd-creative-progressive-rebuild-phase-b-pr-plan.md`
- `.omx/plans/prd-creative-progressive-rebuild-phase-c-pr-plan.md`
- `.omx/plans/prd-creative-progressive-rebuild-phase-d-pr-plan.md`
- `.omx/plans/prd-frontend-ui-ux-closeout-phase-e-pr-plan.md`
- `docs/creative-progressive-rebuild-final-summary.md`
- `docs/frontend-ui-issues-and-improvements.md`
