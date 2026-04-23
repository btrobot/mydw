# PRD: Ant Design Pro UI System Adoption

日期：2026-04-23

## 1. 背景

项目已经基于 Ant Design / Ant Design Pro Components 构建，并已使用：

- `PageContainer`
- `ProTable`
- 少量 `ProDescriptions`
- 少量 `ModalForm`

但当前仍存在较多手写 UI Shell 与重复布局：

- `frontend/src/components/Layout.tsx` 自写 `Layout/Header/Sider/Menu`、折叠、断点、菜单选中、分组展开、跳转。
- `CreativeDetail` 内大量只读信息仍使用 AntD `Descriptions`。
- `CheckDrawer` 是手写 `Drawer + Form + extra submit`。
- `WorkbenchSummaryCard` / `Dashboard` 等区域存在手写指标卡片样板。
- `TaskCreate` 是否适合 `StepsForm` 仍需评估。

目标不是迁移到完整 Umi / Ant Design Pro 脚手架，而是在现有 Vite + React Router + HashRouter + Electron 架构中，充分复用已安装的 `@ant-design/pro-components`，减少 UI 样板和界面不一致。

## 2. 目标

1. 明确项目级 ADP 使用边界与回归契约。
2. 渐进引入 ADP / ProComponents 的高收益能力：
   - `ProLayout`
   - `PageContainer` 规范化
   - `ProDescriptions`
   - `DrawerForm`
   - 有条件的 `ProCard` / `StatisticCard`
   - 有条件的 `StepsForm`
3. 减少自研 UI Shell、布局、只读展示、抽屉表单、指标卡片的重复代码。
4. 获得更一致的页面框架、导航、表格、详情、表单、指标区体验。
5. 保持 Workbench / Detail 已收敛的业务状态与 URL 语义不变。

## 3. 非目标

本计划明确不做：

- 不迁移到 Umi。
- 不迁移到完整 Ant Design Pro 脚手架。
- 不新增依赖。
- 不重写 Workbench 状态模型。
- 不让 Workbench `ProTable.request` 接管 canonical query state。
- 不把复杂 authoring `Form.List` 强行迁移到 ProForm。
- 不将 diagnostics drawer 变成业务提交入口。
- 不在 `ProLayout` PR 中混入 Detail / Drawer / Dashboard / TaskCreate 迁移。

## 4. 核心原则

1. **ADP 管 UI 壳，领域代码管业务状态。**
2. **Workbench URL 是 canonical query state。**
3. **Workbench `ProTable` 保持受控展示模式。**
4. **Diagnostics URL 语义必须稳定。**
5. **先建立回归契约，再做 UI 迁移。**
6. **高收益、高风险的 `ProLayout` 必须作为 parity-gated pilot。**
7. **`StatisticCard` / `ProCard` / `StepsForm` 是评估门，不是默认迁移承诺。**

## 5. RALPLAN-DR Summary

### 5.1 Principles

1. ADP owns shell/container/display conventions, not domain state.
2. Workbench canonical URL/query ownership must remain unchanged.
3. Prefer progressive slices over broad UI rewrites.
4. Reuse installed ProComponents only; no new dependencies and no Umi migration.
5. Standardize only where ADP measurably reduces UI boilerplate.

### 5.2 Decision Drivers

1. 保护 Workbench URL 语义：
   - `keyword`
   - `status`
   - `poolState`
   - `preset`
   - `sort`
   - `page`
   - `pageSize`
   - `diagnostics`
   - `returnTo`
2. 降低自研 shell / layout / detail / drawer / metric card 样板。
3. 在 Electron + Vite + HashRouter + auth shell 环境下降低回归风险。

### 5.3 Viable Options

#### Option A: Progressive ADP shell adoption

以 `ProLayout` 为 shell 试点，同时选择性迁移 `ProDescriptions`、`DrawerForm`、`StatisticCard` / `ProCard`，Workbench 保持受控 `ProTable`。

优点：

- 最大程度减少 shell 重复代码。
- 界面一致性收益最大。
- 符合当前已安装 ProComponents 技术栈。

缺点：

- `ProLayout` 对 protected app shell 影响面较大。
- 需要严格验证 HashRouter、auth header、grace banner、菜单选中、移动端折叠。

#### Option B: 只做详情/抽屉/指标区，不动 shell

不改 `Layout.tsx`，只迁移 `ProDescriptions`、`DrawerForm`、候选指标卡片。

优点：

- 初始风险较低。
- 更容易局部回归。

缺点：

- 最大样板源 `Layout.tsx` 仍保留。
- ADP shell 体系收益较小。

#### Option C: 更“原生”地使用 ProTable

将更多列表状态交给 `ProTable.request`，包括 Workbench。

优点：

- 表面上更接近 ProTable-native。

缺点：

- 与 Workbench canonical URL state 直接冲突。
- 容易回退最近已修复的 preset / URL / diagnostics 行为。

### 5.4 Decision

选择 **Option A**，但带硬约束：

- `ProLayout` 是 parity-gated pilot，不是无条件落地。
- Workbench 永远保持 controlled ProTable，不做 `request` 接管。
- `StatisticCard` / `ProCard` / `StepsForm` 是 assessment gates。

## 6. ADR

### Decision

采用渐进式 ADP adoption：

1. 先建立 ADP boundary + regression contract。
2. 再做 `ProLayout` shell pilot。
3. 通过 parity gate 后，再并行或顺序推进局部展示/表单/指标迁移。

### Drivers

- 当前已依赖 `@ant-design/pro-components`，无需新增依赖。
- 当前 shell 自写逻辑较多，`ProLayout` 是高收益候选。
- Workbench URL / diagnostics 语义已经经过多轮修复，不能被组件库接管。
- Detail / Drawer / Dashboard 存在多个低风险 ProComponents 使用机会。

### Alternatives considered

- **完整迁移 Umi / Ant Design Pro 脚手架**：拒绝。会牵动 Electron、路由、认证、构建与测试链路，收益不足。
- **不碰 shell，只做局部组件**：保留为 fallback。若 `ProLayout` parity 失败，则改为 menu config extraction + 局部 ProComponents adoption。
- **Workbench 改为 ProTable request-native**：拒绝。破坏 canonical URL query state。
- **全部 Card / Form 一次性 Pro 化**：拒绝。容易形成大 diff 和复杂表单回归。

### Consequences

- `ProLayout` slice 必须独立且验证严格。
- Workbench route / query / diagnostics E2E 是不可跳过门禁。
- 局部组件迁移必须证明“减少样板或提升一致性”，否则 no-op。

### Follow-ups

- 若 `ProLayout` pilot 成功，后续新增页面应默认遵循 ADP shell / PageContainer 约定。
- 若 `ProLayout` pilot 失败，保留自研 `Layout`，但抽取菜单配置和页面规范，继续推进局部 ProComponents。

## 7. 全局不变量

以下不变量适用于所有 slices：

1. 不新增 npm dependency。
2. 不引入 Umi。
3. 不改变 Electron 构建形态。
4. 不改变 HashRouter 基础路由形态。
5. Workbench URL 仍是 canonical query state。
6. Workbench 父组件仍是唯一 query state owner。
7. Workbench `ProTable` 仍使用受控 `dataSource` / `pagination` / handlers。
8. Workbench `diagnostics=runtime` 语义不变。
9. Detail `diagnostics=advanced` 语义不变。
10. Diagnostics drawer 不暴露、不触发 submit composition。
11. Complex authoring `Form.List` 不强制迁移 ProForm。
12. `ProLayout` PR 不混入 Detail / Drawer / Dashboard / TaskCreate 迁移。

## 8. Slices

### Slice 0: ADP boundary + regression contract

#### 目标

建立正式规划与测试契约，作为后续执行门禁。

#### 产物

- `.omx/plans/prd-adp-ui-system-adoption-2026-04-23.md`
- `.omx/plans/test-spec-adp-ui-system-adoption-2026-04-23.md`

#### 文件触点

- `.omx/plans/prd-adp-ui-system-adoption-2026-04-23.md`
- `.omx/plans/test-spec-adp-ui-system-adoption-2026-04-23.md`
- 可选后续同步到 `discss/` 或 `docs/`，但本 slice 以 `.omx/plans` 为执行门禁。

#### 验收标准

- 两个规划文件存在。
- 文件明确列出全局不变量。
- 文件明确列出 ProLayout parity gate。
- 文件明确列出 assessment gates。
- 文件明确执行模式与验证路径。

### Slice 1: ProLayout parity-gated pilot

#### 目标

评估并尝试用 `ProLayout` 替代/封装当前自研 `Layout.tsx`，减少 shell 样板，同时保持现有导航、认证、响应式行为。

#### 文件触点

- `frontend/src/components/Layout.tsx`
- `frontend/src/features/auth/AuthRouteGate.tsx`
- `frontend/src/App.tsx`，仅当路由壳接入确实需要时
- `frontend/e2e/**` 中 shell / auth / workbench 相关测试

#### 必须保持

- `AuthSessionHeader` 仍渲染。
- Grace banner / auth shell 行为不变。
- HashRouter 导航正常。
- `/creative/:id` 仍高亮 Workbench。
- 分组菜单 label / click 行为不变。
- 移动端 breakpoint/collapse 仍可用。
- 页面内容区 padding / background 不明显退化。

#### 前置测试

在替换 `Layout.tsx` 前，先补齐或确认 shell parity 测试。

#### Pass criteria

- typecheck 通过。
- build 通过。
- shell parity E2E 通过。
- creative workbench E2E 通过。
- auth routing/bootstrap 相关 E2E 通过。
- diff 主要集中在 shell 文件与测试，不混入其他业务迁移。

#### Fail / fallback criteria

满足任一条件即暂停 ProLayout 落地：

- HashRouter 跳转或菜单选中无法稳定保持。
- auth header / grace banner 行为回归。
- 移动端折叠行为明显退化。
- 需要大范围改 `App.tsx` 或业务页面才能接入。
- PR diff 明显扩散到 Detail / Drawer / Dashboard / TaskCreate。

Fallback：

- 保留 custom Layout。
- 只抽取菜单配置和 route-key 映射。
- 继续推进 Slice 3 / Slice 4 等局部 ProComponents。

### Slice 2: PageContainer normalization / ListPageLayout assessment

#### 目标

统一 PageContainer 使用约定，并评估 `ListPageLayout` 是否仍有价值。

#### 文件触点

- `frontend/src/components/ListPageLayout.tsx`
- 使用 `ListPageLayout` 的页面
- 已使用 `PageContainer` 的列表/详情页

#### 规则

- 列表页主操作优先进入 `PageContainer.extra` 或 `ProTable.toolBarRender`。
- 详情页使用 `PageContainer.title/onBack/tags/extra`。
- 如果 ProTable search/toolbar 已覆盖布局需求，不再额外包重复 Card。

#### 验收标准

- 有清单说明哪些页面保留 `ListPageLayout`，哪些页面可删除/简化。
- 若迁移，页面视觉和交互不变。
- 不与 ProLayout PR 混合。

### Slice 3: CreativeDetail read-only ProDescriptions

#### 目标

将 CreativeDetail 中适合配置化的只读展示迁移到 `ProDescriptions`，提升详情展示一致性。

#### 文件触点

- `frontend/src/features/creative/pages/CreativeDetail.tsx`

#### 可迁移区域

- 作品基础信息。
- 当前版本结果。
- 发布包冻结值。
- 发布侧能力与调度诊断。
- package / task 关系。
- 候选项证据摘要。

#### 禁止范围

- 不改 authoring `Form.List`。
- 不改 drawer URL 语义。
- 不改 review/publish diagnostics 行为。
- 不拆 tab/subroute。

#### 验收标准

- 展示字段一致。
- 空值展示一致。
- 操作按钮位置不变。
- Detail diagnostics E2E / task diagnostics E2E 通过。
- typecheck/build 通过。

### Slice 4: CheckDrawer to DrawerForm

#### 目标

将审核抽屉从手写 `Drawer + Form + extra submit` 迁移为 `DrawerForm`，减少表单容器样板。

#### 文件触点

- `frontend/src/features/creative/components/CheckDrawer.tsx`

#### 必须保持

- approve / rework / reject 三条 mutation 路径不变。
- rework 条件字段不变。
- note trim 行为不变。
- loading 行为不变。
- close/reset 行为不变。
- 成功 message 不变。

#### 验收标准

- 审核通过、需返工、驳回三类交互可用。
- 表单校验不退化。
- E2E 或组件相关回归通过。
- typecheck/build 通过。

### Slice 5: StatisticCard / ProCard assessment gate

#### 目标

评估并仅在确实减少样板时迁移指标卡片。

#### 文件触点

- `frontend/src/features/creative/components/workbench/WorkbenchSummaryCard.tsx`
- `frontend/src/pages/Dashboard.tsx`

#### 每个候选必须记录

1. 当前实现摘要。
2. 预期简化点。
3. 迁移或 no-op 决策。
4. 若迁移，明确验收测试。

#### No-op 条件

- 替换后代码更长。
- 视觉收益不明显。
- 需要过多样式覆盖。
- 会影响行动建议面板或业务状态。

#### 验收标准

- 若迁移，指标展示不变。
- 若 no-op，有明确理由。
- 不混入 shell / drawer / detail 行为改动。

### Slice 6: TaskCreate StepsForm assessment gate

#### 目标

评估 `TaskCreate` 是否适合 `StepsForm`。当前倾向是 assessment-only。

#### 文件触点

- `frontend/src/pages/task/TaskCreate.tsx`

#### 评估维度

- 当前流程是否天然线性多步骤。
- 用户是否需要先选类型、再配置、再确认。
- 当前 tabs / material basket / modal selection / validation alert 是否会因 StepsForm 更清晰。
- 迁移是否减少复杂度而不是增加跨步骤状态管理。

#### No-op 条件

- 当前页面更像高级单页配置台，而非线性 wizard。
- 迁移需要重做校验/提交流程。
- 迁移会增加状态同步复杂度。

#### 验收标准

- 至少输出 migrate/no-op 决策。
- 若迁移，创建任务流程、校验、提交不变。
- 若 no-op，文档说明原因。

## 9. 风险

| 风险 | 影响 | 缓解 |
|---|---|---|
| ProLayout 与 HashRouter/menu state 不兼容 | 全站导航回归 | Slice 1 先补 parity tests；失败则 fallback |
| Auth shell / grace banner 回归 | 登录和授权体验受损 | auth routing/bootstrap E2E 必跑 |
| Workbench URL 状态被 ProTable 接管 | preset/search/filter/page 回归 | 全局不变量 + Workbench E2E |
| diagnostics URL 语义回归 | drawer route chrome 不稳定 | Workbench/Detail diagnostics tests |
| 过度 Pro 化复杂表单 | 代码更复杂、行为回归 | Complex Form.List 禁止迁移 |
| 指标卡片迁移收益不足 | 大 diff 低收益 | StatisticCard/ProCard assessment gate |

## 10. 推荐执行模式

### 默认推荐

先用 `$ralph` 执行 Slice 0，因为它是文档/契约落盘，无需并行。

### Slice 1

推荐 `$ralph`，原因：

- `ProLayout` 是高风险 shell pilot。
- 需要一个 owner 严格控制 diff。
- 不应与其他 UI 迁移并行。

### Slice 3 / Slice 4

在 Slice 1 完成或明确 fallback 后，可以使用 `$team` 并行：

- Lane A：`CreativeDetail` read-only `ProDescriptions`
- Lane B：`CheckDrawer` `DrawerForm`
- Lane C：Verifier 跑 Detail / Workbench / task diagnostics 回归

### Slice 5 / Slice 6

推荐轻量 `$ralph` 或普通 solo 执行，先 assessment，再决定是否代码迁移。

## 11. Available agent roster

- `planner`：更新执行拆解、slice sequencing。
- `architect`：审查 ProLayout shell 边界与 fallback。
- `critic`：检查计划是否可测、是否过度迁移。
- `executor`：执行具体迁移。
- `test-engineer`：补 shell parity / regression tests。
- `verifier`：执行 typecheck/build/e2e/lsp diagnostics。
- `code-reviewer`：最终 PR 审查。

## 12. Suggested reasoning by lane

- ProLayout shell pilot：high。
- Workbench URL / diagnostics verification：high。
- CreativeDetail ProDescriptions：medium。
- CheckDrawer DrawerForm：medium。
- StatisticCard / ProCard assessment：medium。
- TaskCreate StepsForm assessment：medium。

## 13. Launch hints

### Sequential / conservative

```text
$ralph "执行已批准的 ADP UI System Adoption Slice 0：建立 ADP boundary + regression contract。要求只落盘规划与测试契约，不改业务代码。"
```

```text
$ralph "执行已批准的 ADP UI System Adoption Slice 1：ProLayout parity-gated pilot。先补/确认 shell parity tests，再尝试 ProLayout；若 HashRouter/auth/menu/mobile parity 失败，fallback 为保留 custom Layout 并抽取菜单配置。不得混入 Detail/Drawer/Dashboard/TaskCreate 迁移。"
```

### Parallel after shell gate

```text
$team "执行 ADP UI System Adoption 后续局部迁移：Lane A 迁移 CreativeDetail 只读 ProDescriptions；Lane B 迁移 CheckDrawer 到 DrawerForm；Lane C 负责 Workbench/Detail/Auth 回归验证。不得改 ProLayout，不得改 Workbench canonical URL state。"
```

## 14. Completion definition

本计划完成的定义：

- Slice 0 文档存在并被后续执行引用。
- Slice 1 完成 ProLayout pilot 或明确 fallback。
- Workbench URL / diagnostics 语义无回归。
- 至少一个局部 ProComponents 迁移完成，或有明确 no-op 决策。
- typecheck/build/e2e 按 test spec 通过。

## 15. 执行收口状态（2026-04-24）

本 PRD 已完成阶段性收口。总收口文档已落盘：

- `discss/adp-ui-system-adoption-closeout-2026-04-24.md`
- `discss/ant-design-pro-best-practices-analysis-2026-04-23.md`
- `discss/workbench-refactor-roadmap-2026-04-23.md`

### 15.1 Slice 完成映射

| Slice | 结果 | 证据 |
| --- | --- | --- |
| Slice 0：ADP boundary + regression contract | 已完成 | 本 PRD 与 test spec 存在，并被 Slice 1-6 引用 |
| Slice 1：ProLayout parity-gated pilot | 已完成 | `953965b`：`Adopt ProLayout behind shell parity gates` |
| Slice 2：PageContainer / ListPageLayout assessment | 已完成 | `a7c6e5a`：`Remove unused list layout wrapper after ADP assessment`；`discss/adp-slice-2-page-container-assessment-2026-04-23.md` |
| Slice 3：CreativeDetail ProDescriptions | 已完成 | `c429f35`：`Adopt ProDescriptions for creative detail read-only sections` |
| Slice 4：CheckDrawer DrawerForm | 已完成 | `57656c6`：`Adopt DrawerForm for creative review drawer` |
| Slice 5：StatisticCard / ProCard assessment | 已完成，no-op | `9f6bbff`：`Record the ADP metric-card assessment boundary`；`discss/adp-ui-system-adoption-slice-5-assessment-2026-04-23.md` |
| Slice 6：TaskCreate StepsForm assessment | 已完成，no-op | `e3fcec3`：`Record the TaskCreate StepsForm assessment boundary`；`discss/adp-ui-system-adoption-slice-6-assessment-2026-04-24.md` |

### 15.2 最终结论

本轮采用的最终边界是：

> ADP / ProComponents 负责 shell、页面容器、只读展示、标准表单容器和低风险 UI 规范；Workbench canonical URL state、Detail diagnostics、TaskCreate material basket / submit payload 等领域状态继续由领域代码负责。

该结论满足本 PRD 的 completion definition：

- `ProLayout` pilot 已完成，没有回退到 custom shell fallback。
- `ProDescriptions` 与 `DrawerForm` 已完成至少两个局部 ProComponents 迁移。
- `StatisticCard / ProCard` 与 `StepsForm` 已完成 assessment，并在收益不足时明确 no-op。
- Workbench URL / diagnostics 语义没有被 ADP adoption 改写。
- 各 Slice 均以 typecheck / build / targeted E2E / lsp diagnostics / diff-check 作为门禁。

### 15.3 关闭边界

本 PRD 到此关闭，不继续扩展以下范围：

- 不迁移 Umi / 完整 Ant Design Pro 脚手架。
- 不让 ProTable 接管 Workbench canonical query state。
- 不强制将复杂 authoring `Form.List` 迁移到 ProForm。
- 不在 diagnostics drawer 增加 submit composition。
- 不因视觉统一而强行迁移 StatisticCard / ProCard。
- 不强拆 TaskCreate 为 StepsForm，除非未来产品流程变成真正线性 wizard。
