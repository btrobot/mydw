# RALPLAN 共识草案（Deliberate）

## 任务

围绕 Workbench / Detail 落地 creative 二级候选池模型，形成后续 `ralph` / `team` 可直接执行的总计划；本稿只做规划，不做实现。

## 证据基线

- `discss/prd-work-two-level-candidate-pool-adoption-2026-04-24.md`
- `discss/test-spec-work-two-level-candidate-pool-adoption-2026-04-24.md`
- `discss/work-two-level-candidate-pool-ia-data-roadmap-2026-04-24.md`
- `.omx/context/creative-two-level-candidate-pool-adoption-20260423T225115Z.md`
- 已确认代码触点：
  - 前端：`frontend/src/features/creative/pages/CreativeDetail.tsx`、`CreativeWorkbench.tsx`、`view-models/useCreativeAuthoringModel.ts`、`creativeAuthoring.ts`、`components/workbench/*`、`components/VersionPanel.tsx`、`components/CheckDrawer.tsx`
  - 后端：`backend/models/__init__.py`、`backend/schemas/__init__.py`、`backend/api/creative.py`、`backend/services/creative_service.py`、`backend/services/creative_version_service.py`、`backend/services/publish_service.py`
  - 现有测试/E2E：`backend/tests/test_creative_api.py`、`test_creative_schema_contract.py`、`test_creative_versioning.py`、`test_publish_execution_snapshot.py`、`frontend/e2e/creative-workbench/creative-workbench.spec.ts`、`creative-main-entry.spec.ts`、`creative-version-panel.spec.ts`

## RALPLAN-DR 摘要

### Principles

1. 作品真值优先于输入项编排语义。
2. 先稳住 Detail 真值表达，再升级 Workbench 汇总。
3. 迁移期先加结构、保兼容，不先大删旧语义。
4. 候选池与当前入选必须分层，手工覆盖规则必须显式。
5. 版本/发布只能冻结真值与当前入选，不直接依赖临时拼装态。

### Decision Drivers（Top 3）

1. **兼容性**：不能推翻现有 creative/version/package 主干。
2. **可验证性**：每个 slice 必须能被 unit/integration/e2e 独立验证。
3. **一致性**：Detail 真值、Workbench 摘要、Version/Package 冻结口径必须统一。

### Viable Options

#### 方案 A：兼容态渐进落地（推荐）
- 做法：`creative_items` 承接 current-* 真值；新增 `creative_product_links`、`creative_candidate_items`；短期继续复用 `creative_input_items` 表达 video/audio 当前入选。
- Pros：迁移风险最低；最贴合现有服务/接口；便于按 Slice 1-6 串行落地。
- Cons：短中期存在新旧语义并存；需要明确“旧字段只兼容、不新增新责任”的纪律。

#### 方案 B：目标态一次成型
- 做法：一步到位新增 `creative_selected_media_items`，同时全面重构 detail/list/version/package 聚合。
- Pros：模型最干净；长期债务最少。
- Cons：改动面过大；回归面最宽；会把数据迁移、接口改造、前端重组绑成一个高风险大包。

#### 方案 C：仅前端视图先模拟新模型
- 做法：后端不建稳定候选池，只在前端 view-model 里拼“候选/当前入选/真值”。
- Pros：初期交付快。
- Cons：无法形成稳定快照口径；Workbench 与 Version/Package 会长期不一致；后续返工最大。

### Chosen Direction

选择 **方案 A：兼容态渐进落地**。先把“作品真值模型”建起来，再逐步压缩旧输入项语义；`creative_selected_media_items` 作为二阶段可升级选项，不放入首轮必做范围。

## ADR

### Decision

采用“兼容态渐进迁移”路线：先以 `creative_items + creative_product_links + creative_candidate_items + creative_input_items(受限语义)` 建立二级候选池模型，再在稳定后评估是否抽离 `creative_selected_media_items`。

### Drivers

- 现有 `creative_service` 已直接读写 `subject_product_name_snapshot`、`main_copywriting_text`、`creative_input_items`
- `backend/api/creative.py` 与 `frontend/src/features/creative/creativeAuthoring.ts` 已形成稳定 detail/list 合同
- 现有 `creative_versioning` / `publish_execution_snapshot` 测试已假设快照从 creative 主干聚合而来

### Alternatives Considered

- 一次性目标态重构：过宽，难以分 slice 验证
- 前端模拟态：无法保证后端与发布冻结一致

### Why Chosen

它最符合“先建真值、再建汇总、最后冻版本”的主线，也最利于后续 `ralph` 逐 slice 验证与 `team` 分 lane 并行。

### Consequences

- 需要明确兼容期字段优先级与回填规则
- 需要对 Workbench 摘要引入后端统一聚合口径
- 需要补充跨 slice 回归集，防止新旧语义混写

### Follow-ups

1. 首轮执行完成后，评估 `creative_input_items -> creative_selected_media_items` 的收益/代价。
2. 若 Workbench 摘要字段持续扩张，再考虑单独的 summary assembler。

## PRD 形态（建议）

PRD 应固定为以下结构：

1. **问题与目标**
   - 从“输入项编排中心”升级为“作品真值 + 候选池 + 当前入选”
   - 用户价值：一眼看懂当前作品、候选与入选不混淆、Workbench 能看完成度
2. **范围**
   - In Scope：Slice 1-6
   - Out of Scope：新服务、新状态库、复杂时间线、多轨工程、搜索/索引专项
3. **领域模型**
   - 全局大池 / 作品小池 / 当前入选
   - 唯一真值、手工覆盖、主题商品唯一、媒体集合型入选
4. **迁移策略**
   - 兼容态先行
   - 旧字段只保兼容，不承接新增语义
5. **切片计划**
   - Slice 1 真值显式化
   - Slice 2 商品关联
   - Slice 3 候选池
   - Slice 4 当前入选媒体
   - Slice 5 Workbench 汇总
   - Slice 6 Version/Package 对齐
6. **验收与发布门禁**
   - AC、诊断口径、回归命令、观察指标

## Architect Iterate 收敛补丁

为解决 Architect 指出的 authority 漂移风险，本计划补充以下硬约束：

### 1. Phase 0 必须产出“权威源矩阵”

矩阵至少覆盖以下概念：

- primary product
- current product name
- current cover
- current copywriting
- candidate items
- selected video set
- selected audio set
- version freeze source
- package freeze source
- workbench summary source

每项都必须明确：

- write source
- read source
- freeze source
- compatibility source
- retirement slice

### 2. `creative_input_items` 的兼容使用增加退场约束

首轮允许继续复用 `creative_input_items`，但语义被严格收窄为：

- 仅承接 `video/audio` 当前入选执行投影
- 不再承接名称/封面/文案真值语义
- Slice 4 结束时必须形成唯一 **selected-media projection contract**
- Slice 6 前，Workbench / Version / Publish 不得再直接读取旧 orchestration carrier 的隐式拼装态

换句话说：

- 本轮允许“物理表暂不拆”
- 但不允许“语义继续共权”

### 3. 多商品优先级规则必须在 Phase 0 冻结

需要明确：

- `subject_product_id` 与 `primary product_link` 的对应关系
- 切换主题商品时，哪些字段 follow、哪些字段 manual 不覆盖
- snapshot 回填的唯一写入口

在此规则冻结前，不进入 Slice 2 实现。

### 4. Manifest 必须形成 v1 typed contract

虽然现网仍用 `manifest_json`，但本计划要求在 Slice 6 前先定义 `manifest v1` 结构合同，至少锁定：

- identity keys
- media order
- enabled state
- selected source
- freeze timestamp / version linkage

禁止仅以“任意 JSON 字符串”作为计划完成标准。

### 5. Workbench 新摘要字段要有明确映射策略

在 Slice 5 前必须补一张字段映射表，明确：

- `definition_ready`
- `composition_ready`
- `candidate_*_count`
- `selected_*_count`

分别：

- 从哪组 source 聚合
- 是否进入 preset/filter/sort
- 若不进入，为什么只展示不筛选

避免“新增字段已展示，但语义未进入现有 query contract”的半完成态。

### 6. 当前封面真值合同在 Phase 0 明确冻结

为避免 Slice 1 落地时猜字段/API，本计划在 Phase 0 直接冻结以下合同：

- `creative_items.current_cover_asset_type`
- `creative_items.current_cover_asset_id`
- `creative_items.cover_mode`
- `CreativeDetailResponse.current_cover_asset_type`
- `CreativeDetailResponse.current_cover_asset_id`
- `CreativeDetailResponse.cover_mode`

读写规则：

- write source：Detail 当前定义区
- read source：Detail / Workbench 摘要 / Version freeze assembler
- freeze source：Version / Package 统一从 current cover contract 读取
- compatibility source：旧 `cover_ids` / 旧 input projection 仅做回读兼容，不再承担当前封面真值

### 7. `creative_input_items` 收窄规则在 Phase 0 冻结

迁移期明确：

- `copywriting`：真值迁移到 `current_copywriting_*`；旧 input item 只回读兼容，退场目标 Slice 4
- `cover`：真值迁移到 current cover contract；旧 input item 只回读兼容，退场目标 Slice 4
- `topic`：不再作为当前入选/执行权威面；保留为候选或生成输入参考，退场目标 Slice 3/4 间完成
- `video/audio`：迁移期仍可复用 `creative_input_items`，但只作为 selected-media projection

未冻结上述规则前，不进入 Slice 4 实现。

## Test Spec 形态（建议）

测试规格应固定为以下结构：

1. **测试原则**：先 Detail 后 Workbench；先真值后联动；手工覆盖单测；冻结快照回溯验证
2. **分层覆盖**
   - Unit：字段映射、模式切换、聚合规则
   - Integration：API/schema/service/DB 读写与聚合
   - E2E：Detail→Workbench→Version/Publish 闭环
   - Observability：诊断字段、日志、快照一致性、失败可定位性
3. **Slice 级核心用例**
4. **跨 Slice 回归**
5. **验证命令与完成判据**

## 总执行计划

### Phase 0：合同冻结与兼容策略定稿

目标：
- 定义 current-*、mode、候选状态、入选集合的统一词汇表
- 确认 `creative_input_items` 首轮仍用于 video/audio 当前入选

产出：
- PRD/Test Spec 定稿
- 字段优先级与兼容规则表
- 迁移后验收清单

### Phase 1：Slice 1 作品真值显式化

目标：
- 商品名称/封面/文案成为 `creative_items` 显式真值

主要触点：
- `backend/models/__init__.py`
- `backend/schemas/__init__.py`
- `backend/services/creative_service.py`
- `backend/api/creative.py`
- `frontend/src/features/creative/creativeAuthoring.ts`
- `frontend/src/features/creative/view-models/useCreativeAuthoringModel.ts`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/src/features/creative/types/creative.ts`

验收：
- Detail 顶部可直接显示/编辑当前真值
- 手工编辑进入 manual 模式并可回显
- 旧 `subject_product_*` / `main_copywriting_text` 不再是唯一展示来源

### Phase 2：Slice 2 作品-商品关联表

目标：
- 一件作品可关联多个商品，且主题商品唯一、顺序稳定

主要触点：
- `backend/models/__init__.py`
- `backend/schemas/__init__.py`
- `backend/services/creative_service.py`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`

验收：
- 新增/切换/排序/移除商品可持久化
- 主题商品切换能驱动默认名称/封面来源

### Phase 3：Slice 3 候选池落地

目标：
- 建立作品持久化候选池，不再依赖运行时拼凑

主要触点：
- `backend/models/__init__.py`
- `backend/schemas/__init__.py`
- `backend/services/creative_service.py`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- 可能新增 detail 子组件（执行时再定）

验收：
- 候选封面/文案/视频/音频分区展示
- 来源、状态、采用/加入/取消动作具备稳定合同

### Phase 4：Slice 4 当前入选媒体集合收敛

目标：
- 明确 video/audio 的当前入选集合、排序、启停与移除语义

主要触点：
- `backend/services/creative_service.py`
- `frontend/src/features/creative/view-models/useCreativeVersionReviewModel.ts`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`

验收：
- 合成/版本视图仅读当前入选集合
- 候选↔入选联动一致，刷新后不丢

### Phase 5：Slice 5 Workbench 汇总升级

目标：
- Workbench 汇总“定义完成度 + 当前入选摘要 + 诊断”

主要触点：
- `backend/schemas/__init__.py`
- `backend/services/creative_service.py`
- `frontend/src/features/creative/pages/CreativeWorkbench.tsx`
- `frontend/src/features/creative/components/workbench/WorkbenchTable.tsx`
- `frontend/src/features/creative/components/workbench/WorkbenchSummaryCard.tsx`
- `frontend/src/features/creative/components/workbench/WorkbenchPresetBar.tsx`
- `frontend/src/features/creative/components/workbench/WorkbenchDiagnosticsDrawer.tsx`

验收：
- 列表与摘要都能表达 current truth / selected media / candidate diagnostics
- 现有 preset/filter/sort 语义不回归

### Phase 6：Slice 6 Version / Package 对齐

目标：
- 版本与发布冻结基于真值与当前入选快照

主要触点：
- `backend/services/creative_service.py`
- `backend/services/creative_version_service.py`
- `backend/services/creative_generation_service.py`
- `backend/services/ai_clip_workflow_service.py`
- `backend/services/publish_service.py`
- `frontend/src/features/creative/components/VersionPanel.tsx`
- `frontend/src/features/creative/components/CheckDrawer.tsx`
- `frontend/src/features/creative/view-models/useCreativeVersionReviewModel.ts`
- `frontend/src/features/creative/view-models/useCreativePublishDiagnosticsModel.ts`

验收：
- 可查看某次版本/发布冻结的名称、封面、文案、入选媒体 manifest
- 新旧快照口径一致且可回溯

## 风险与缓解

1. **兼容期语义冲突**
   - 缓解：建立字段优先级表；新字段生效后旧字段仅做回读兼容。
2. **Detail 改动过大引发交互回归**
   - 缓解：按 Slice 拆分；每 slice 先补 contract test 再动页面结构。
3. **Workbench 与 Detail 口径漂移**
   - 缓解：汇总字段只从后端统一聚合输出，不在前端重复推导。
4. **Version/Publish 冻结错误继承旧拼装态**
   - 缓解：在 Slice 6 前增加冻结口径测试，不允许直接读旧隐式字段。
5. **候选池被做成资源库页**
   - 缓解：UI 与 AC 强制“当前定义/当前入选优先展示”。
6. **`creative_input_items` 长期滞留为双真值承载**
   - 缓解：Phase 0 产出 authority matrix；Slice 4 完成 selected-media projection；Slice 6 前切断 Workbench/Version/Publish 对旧隐式读取路径的依赖。
7. **多商品主语义与单商品快照路径冲突**
   - 缓解：冻结 `primary product` 优先级规则与 snapshot 写入口；未冻结前不推进 Slice 2 实现。
8. **manifest 只有字符串无合同，导致冻结不可回溯**
   - 缓解：Slice 6 前定义并验证 manifest v1 typed contract。

## 3-Senario Pre-mortem

### 场景 1：上线后 Detail 看起来对，但生成/发布用的仍是旧输入项
- 触发：服务层继续从旧字段或旧 `creative_input_items` 拼装
- 结果：用户看到的真值与实际生成不一致
- 预防：Slice 4/6 必做 service contract test；冻结逻辑禁止绕过 current-* / selected 集合

### 场景 2：Workbench 摘要与 Detail 回显长期不一致
- 触发：Workbench 前端自行推导摘要，或后端 summary 字段不完整
- 结果：列表诊断不可信，运营误判作品状态
- 预防：summary 字段后端单源生成；E2E 加“Detail 保存→Workbench 回显→再回 Detail”闭环

### 场景 3：候选池扩张后手工覆盖规则失效
- 触发：新候选导入或主题商品切换时覆盖了 manual 值
- 结果：用户已定稿文案/封面被悄悄改写
- 预防：manual/follow/adopted 模式独立建模；为名称/封面/文案分别建立回归测试

## File Touchpoints（执行优先级）

### 必碰
- `backend/models/__init__.py`
- `backend/schemas/__init__.py`
- `backend/api/creative.py`
- `backend/services/creative_service.py`
- `frontend/src/features/creative/creativeAuthoring.ts`
- `frontend/src/features/creative/types/creative.ts`
- `frontend/src/features/creative/view-models/useCreativeAuthoringModel.ts`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/src/features/creative/pages/CreativeWorkbench.tsx`

### 高概率补充
- `backend/services/creative_version_service.py`
- `backend/services/creative_generation_service.py`
- `backend/services/ai_clip_workflow_service.py`
- `backend/services/publish_service.py`
- `frontend/src/features/creative/view-models/useCreativeVersionReviewModel.ts`
- `frontend/src/features/creative/view-models/useCreativePublishDiagnosticsModel.ts`
- `frontend/src/features/creative/components/workbench/WorkbenchTable.tsx`
- `frontend/src/features/creative/components/workbench/WorkbenchSummaryCard.tsx`
- `frontend/src/features/creative/components/workbench/WorkbenchPresetBar.tsx`
- `frontend/src/features/creative/components/workbench/WorkbenchDiagnosticsDrawer.tsx`
- `frontend/src/features/creative/components/VersionPanel.tsx`
- `frontend/src/features/creative/components/CheckDrawer.tsx`

### 高概率新增
- 新 migration（名称待执行时确定）
- Detail 子组件（如 CurrentDefinition / ProductLink / CandidateList / SelectedMedia 面板）
- Creative 相关后端/前端测试文件

## Acceptance Criteria（总验收）

1. Detail 能显式展示并编辑当前真值：商品名称、封面、文案、目标时长。
2. 候选池与当前入选清晰分离，视频/音频的加入、排序、启停、移除可稳定回显。
3. 多商品关联支持唯一主题商品、可排序、可驱动默认真值来源。
4. Workbench 能展示定义完成度、当前入选摘要、候选规模与缺失诊断。
5. Version/Package 能冻结并回看真值与当前入选快照。
6. manual/follow/adopted 三类模式行为稳定，候选变化不会误覆盖手工值。
7. 相关 typecheck/build/pytest/playwright 集合通过。
8. Phase 0 已交付 authority matrix、primary-product 规则表、manifest v1 contract、Workbench 摘要字段映射表。
9. 当前封面真值合同已冻结，Slice 1 无需再猜字段/API 名称。
10. `creative_input_items` 对 copywriting/cover/topic 的兼容退场规则已冻结，Slice 4 无需再猜过渡边界。

## 推荐执行顺序

1. Phase 0：合同冻结与兼容策略
2. Slice 1：真值显式化
3. Slice 2：商品关联
4. Slice 3：候选池
5. Slice 4：当前入选媒体
6. Slice 5：Workbench 汇总
7. Slice 6：Version/Package 对齐
8. 收口：删除/降权旧隐式读取路径；若确有延后，必须以显式技术债记录而非默认保留

## Staffing Guidance（后续执行）

### 可用 agent types
- `planner`
- `architect`
- `critic`
- `executor`
- `debugger`
- `test-engineer`
- `verifier`
- `code-reviewer`
- `security-reviewer`
- `explore`

### `ralph` 单主线建议

- Leader：`executor`/高推理
- 每个 slice 一个小闭环：建模 → 接口 → 前端 → 测试 → 验证
- 每次只推进 1 个 slice，避免跨 slice 半完成态
- 每 slice 完成后必须跑该 slice 的后端 + 前端 + E2E 最小回归

### `team` 并行建议

- Lane A（backend, `executor`, high）：模型/schema/API/service/migration
- Lane B（frontend-detail, `executor`, high）：Detail + authoring model
- Lane C（frontend-workbench, `executor`, medium）：Workbench 汇总与 diagnostics
- Lane D（tests, `test-engineer`, medium）：后端合同、前端交互、E2E、观测性断言
- Lane E（verify, `verifier`, high）：汇总证据、检查口径漂移

约束：
- A 与 B 在 Slice 1-4 强耦合，先串行对齐合同，再并行落代码
- C 必须在 Slice 5 才主启动
- D 从 Slice 1 起常驻跟进
- E 只在每个 slice 收尾时介入

### Team Launch Hints

- `ralph`：按 slice 逐轮执行，适合低并发高一致性
- `$team` / `omx team`：从 Slice 1 开始可双 lane（backend + detail），到 Slice 5 再开 workbench lane

### Team Verification Path

1. 后端合同测试先绿
2. 前端 detail/workbench 交互测试再绿
3. E2E 闭环验证“Detail 保存 → Workbench 摘要 → Version/Publish 冻结”
4. verifier 汇总截图/日志/测试结果，确认零已知错误再切下个 slice

## Phase 0 附录（执行前必须定稿）

具体产物路径：

- `.omx/plans/phase0-creative-two-level-candidate-pool-authority-matrix-2026-04-24.md`
- `.omx/plans/phase0-creative-two-level-candidate-pool-primary-product-rules-2026-04-24.md`
- `.omx/plans/phase0-creative-two-level-candidate-pool-current-cover-contract-2026-04-24.md`
- `.omx/plans/phase0-creative-two-level-candidate-pool-input-items-compat-retirement-2026-04-24.md`
- `.omx/plans/phase0-creative-two-level-candidate-pool-workbench-summary-mapping-2026-04-24.md`
- `.omx/plans/phase0-creative-two-level-candidate-pool-manifest-v1-contract-2026-04-24.md`

### A. current cover contract

- DB：
  - `current_cover_asset_type: Literal['cover']`
  - `current_cover_asset_id: int | null`
  - `cover_mode: default_from_primary_product | adopted_candidate | manual`
- API：
  - detail read/write surface 同名字段
- Freeze：
  - version/package 统一从 current cover contract 读取

### B. `creative_input_items` 兼容退场表

| material_type | 迁移期角色 | 新权威面 | retirement slice |
|---|---|---|---|
| video | selected-media projection | selected video set | 视二阶段评估 |
| audio | selected-media projection | selected audio set | 视二阶段评估 |
| copywriting | read-only compatibility | current copywriting contract | Slice 4 |
| cover | read-only compatibility | current cover contract | Slice 4 |
| topic | candidate/reference only | candidate/prompt source | Slice 3/4 |

### C. Workbench 摘要字段映射

| field | source | list row / global summary | filter/sort/preset |
|---|---|---|---|
| current_product_name | backend aggregated truth | row | display only |
| selected_video_count | selected-media projection | row + summary | filter candidate: no / preset: optional |
| selected_audio_count | selected-media projection | row + summary | display only |
| candidate_video_count | candidate pool | row + summary | display only |
| candidate_audio_count | candidate pool | row + summary | display only |
| definition_ready | backend aggregated readiness | row + summary | preset/filter optional after Slice 5 |
| composition_ready | backend aggregated readiness | row + summary | preset/filter optional after Slice 5 |

---

## 2026-04-24 总收口更新（Master Closeout Update）

### 结论

`creative two-level candidate pool adoption` 这条总计划已执行完成，正式 closeout 见：

- `.omx/plans/closeout-creative-two-level-candidate-pool-adoption-2026-04-24.md`

### 计划完成矩阵

| Phase / Slice | Status | 代表提交 |
|---|---|---|
| Phase 0 | completed | `454eac9` |
| Slice 1 | completed | `2fb9561` |
| Slice 2 | completed | `38b8a29` |
| Slice 3 | completed | `6333d13` |
| Slice 4 | completed | `a426abd`、`867c80d` |
| Slice 5 | completed | `b81fcad` |
| Slice 6 | completed | `9a49bb9` |

### 现状改写

本 PRD 中原本以 future tense 描述的核心设计点，现已成为已落地约束：

1. `creative_items.current-*` 已成为当前真值面
2. `creative_product_links.is_primary` 已成为 primary product 的唯一主入口
3. `creative_candidate_items` 已成为作品候选池持久化表达
4. selected-media projection 已成为 video/audio 当前入选的权威读口径
5. Workbench 已切到后端 summary aggregator
6. Version / Package / Publish 已切到统一 freeze/manifest 口径

### 计划退出规则

从 2026-04-24 起，本 PRD 不再作为“待执行 roadmap”，而是作为：

- 已实现计划的设计归档
- 后续 follow-up 的边界基线

若后续继续推进：

- compat hard-removal
- selected-media 物理迁移
- publish/runtime live verification

都应单独立项，不再继续作为本 PRD 的“追加 Slice”。
