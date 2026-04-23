# Creative Domain Model Realignment PRD（作品域重整 PRD）

> Version: 2.3.0
> Updated: 2026-04-23  
> Owner: Product / Domain Design / Codex  
> Status: Master PRD / Phase 0-4 + Workbench/Detail IA stabilization closeout artifact

> 本文档最初用于冻结 **Phase 0 PR1 的正式 PRD**；现已吸收 **Phase 1-4 的实施结果与 Phase 4 收口结论**，作为 creative-domain 主线的总 PRD / 当前真相文档。  
> 它回答：**为什么要调整 Creative 域、当前推荐并已落地的领域边界是什么、迁移是如何分阶段完成的、以及本轮主线已经收口到什么状态。**

> Origin note:
> - Originated as Phase 0 PR1 docs-only artifact
> - Keeps the frozen domain boundary and migration rationale
> - Now also records the implemented end-state through Phase 4
> - Future follow-up PRs should still cite this master PRD and the master test spec
> - 2026-04-23 additionally absorbs the Workbench / CreativeDetail IA stabilization closeout from `discss/workbench-detail-refactor-plan-closeout-2026-04-23.md`

## 0. 在启动包中的角色

本 PRD 是“Creative 领域模型重整”这条主线的范围与完成定义文档，应与以下材料配套使用：

- 上下文快照：`.omx/context/creative-domain-model-realignment-2026-04-22.md`
- 讨论备忘：`discss/creative-material-version-publish-package-domain-model-2026-04-22.md`
- 风格参考：`docs/governance/next-phase-prd.md`
- 配套验证文档：`.omx/plans/test-spec-creative-domain-model-realignment.md`

使用规则：

1. 本文档负责锁定范围、边界、迁移阶段与验收口径。
2. 若后续方案改变了对象边界、迁移顺序或非目标，先更新本 PRD，再更新 test spec。
3. 本文档仍是 creative-domain 主线的规范性来源；后续 PR 不得绕过本文档重新定义领域边界。
4. Phase 0 的 planning 属性仍保留为历史来源说明；但本文档同时承担 Phase 4 之后的 master closeout/当前真相职责。

## 1. 规划主题

**把 Creative 从“素材快照容器”提升为“作品 brief + 输入编排 + 版本产出 + 发布冻结”的业务主对象体系。**

## 2. 背景与当前真相

### 2.1 已经成立的产品真相

仓库已有证据表明系统主语义已经迁移到 Creative：

- `Creative Workbench` 已成为主工作台，`Task` 已被下沉为执行/诊断视图：`docs/domains/creative/progressive-rebuild-final-summary.md:13-18`
- 默认入口切到 `/creative/workbench`，Dashboard 退回运行态观察页：`docs/domains/creative/progressive-rebuild-final-summary.md:107-117`
- 重构总结明确写明：`Task` 只负责执行、追踪、诊断：`docs/domains/creative/progressive-rebuild-final-summary.md:186-192`

### 2.2 启动时尚未完成的技术真相（历史背景）

尽管产品主语义已迁移，当前数据与 contract 仍保留明显的 Task-era 表达：

- `CreativeCreateRequest` / `CreativeUpdateRequest` 仍以 `video_ids`、`copywriting_ids`、`cover_ids`、`audio_ids`、`topic_ids` 表达作品输入：`backend/schemas/__init__.py:595-625`
- 这些字段在 schema 层被保序去重，天然丢失重复实例语义：`backend/schemas/__init__.py:605-625`
- `CreativeService` 仍围绕“输入 ID 列表 + snapshot_hash”做双写：`backend/services/creative_service.py:756-835`
- 现有 contract test 明确把“重复 ID 被去重且 hash 稳定”视为正确行为：`backend/tests/test_creative_input_snapshot_contract.py:168-245`
- Task 域文档仍把资源关联与 `final_video_duration` 放在 Task 核心职责中：`docs/domains/tasks/task-management-domain-model.md:41-60`
- 当前任务真实输入面仍定义为 ID 集合字段：`docs/domains/tasks/task-management-domain-model.md:110-118`
- `local_ffmpeg V1` 当前只支持单视频输入；测试也锁定了这一点：`docs/domains/tasks/task-management-domain-model.md:136-159`、`backend/tests/test_task_creation_semantics.py:70-84`

### 2.3 启动结论

**当前系统已经是 Creative-first 的产品结构，但仍不是 Creative-first 的领域模型。**

### 2.4 当前收口真相（截至 2026-04-23）

经过 Phase 1-4 的连续落地，当前主线已经收口为：

- **作品定义真值**：`CreativeItem` + `input_items` + `input_profile_id` + `input_orchestration`
- **版本结果真值**：`CreativeVersion`
- **发布冻结真值**：`PackageRecord / PublishPackage`
- **任务定位**：`Task` 仅承担执行 / 诊断 / 运行结果回写，不再反向定义作品输入真值

同时，legacy request list fields（如 `video_ids` / `audio_ids` / `copywriting_ids` 等）当前只作为 **deprecated compatibility surface** 存在：

1. schema / OpenAPI 已标记 deprecated
2. 写入路径已被 validator 拒绝
3. 若后续要做 strict API hard-removal，应作为单独 follow-up，而不是回滚本轮主线

### 2.5 Workbench / Detail IA 收口真相（截至 2026-04-23）

在领域模型 Phase 0-4 收口之后，Workbench / CreativeDetail 又完成了一轮信息架构与页面结构稳定化：

- **Workbench 主入口定位已稳定**：作品工作台继续作为 Creative 主入口，Task 继续下沉为执行 / 诊断视图。
- **Workbench 查询状态已收敛**：`keyword/status/poolState/preset/sort/page/pageSize/diagnostics` 由 URL canonical state 统一驱动。
- **Workbench 检索已服务端化**：搜索、筛选、排序、分页与高频 preset 均基于服务端结果，而不是前端窗口过滤。
- **CreativeDetail 已拆第一层 view-model**：authoring、version-review、publish-diagnostics、navigation state 各自拥有清晰归属。
- **Diagnostics 已行动化**：Workbench runtime diagnostics 与 Detail advanced diagnostics 均先展示推荐行动，再保留原始证据。
- **Mutation 边界已锁定**：diagnostics drawer 只能触发 retry / navigation / preset，不触发 submit composition。

本轮收口对应 roadmap：

- `discss/workbench-refactor-roadmap-2026-04-23.md`
- `discss/workbench-detail-refactor-plan-closeout-2026-04-23.md`

## 3. 问题陈述

如果继续在旧集合快照模型上叠加字段，会持续放大四类问题：

1. **作品语义过弱**  
   `Creative` 更像“素材输入容器”，而不是“我要做成什么”的业务主对象。
2. **输入模型无法表达编排**  
   `video_ids` 无法表达顺序、重复实例、片段裁剪、用途角色。
3. **商品名称与文案归属错误**  
   商品名/文案既有来源属性，也有作品层当前采用值，还需要版本/发布冻结值；不能只停留在素材层。
4. **目标时长与实际时长混在执行层**  
   目标时长属于作品约束，实际时长属于版本结果，Task 侧时长只应保留执行产物语义。

## 4. 目标

### 4.1 核心目标

1. 明确把旧 Task 中“业务定义责任”迁移到 Creative。
2. 用可审查的领域边界区分 `Material / Creative / CreativeInputItem / CreativeVersion / PublishPackage / Task`。
3. 为后续 API、Schema、DB、前端交互与执行层迁移提供统一共识。
4. 把后续验证口径从“旧快照是否稳定”改为“新业务表达是否成立、迁移是否可控”。

### 4.2 结果目标

1. 作品层可以直接表达：
   - 商品主体/展示名
   - 主文案
   - 目标输出时长
   - 输入编排
2. 输入层可以表达：
   - 多视频
   - 同视频重复添加
   - 顺序
   - role
   - trim 区间
3. 版本层可以表达本次实际产物与审核对象。
4. 发布包可以冻结最终四件套与发布约束。

## 5. 非目标

本轮 PRD **不**直接要求：

- 立即把 `local_ffmpeg V1` 升级成 multi-video 引擎
- 一次性删除所有 legacy snapshot/list 字段
- 直接开始全量前后端重构
- 把 remote/control-plane 规划并入本轮领域建模
- 把执行拆分细化到每个实现 PR

## 6. 领域边界与推荐模型

### 6.1 Material（素材层）

回答：**“我有什么可用输入？”**

职责：

- 保存可复用原始资源
- 允许被多个作品反复引用
- 不承担某次创作的最终采用值

典型对象：

- `VideoMaterial`
- `AudioMaterial`
- `CoverMaterial`
- `CopywritingMaterial`
- `ProductProfile` / `ProductMaterial`
- `TopicMaterial`

### 6.2 Creative（作品层）

回答：**“这条内容要做成什么？”**

职责：

- 作品身份：`id / title / status / creative_type?`
- 作品业务定义：`subject_product_id`、`subject_product_name_snapshot`、`main_copywriting_text`、`target_duration_seconds`
- 作品编排入口：`creative_input_items[]`
- 作品约束：渠道、风格、策略约束

### 6.3 CreativeInputItem（输入编排层）

回答：**“作品输入轨道里按什么顺序、以什么角色、放了哪些素材实例？”**

建议最小字段：

- `id`
- `creative_id`
- `material_type`
- `material_id`
- `role`
- `sequence`
- `instance_no` 或 `repeat_group`
- `trim_in`
- `trim_out`
- `slot_duration_seconds?`
- `enabled`

关键要求：

- 同一素材必须允许重复出现
- 顺序必须是稳定且显式的
- 每个实例必须可携带独立 role/trim
- 不得再被集合式去重语义吞掉

### 6.4 CreativeVersion（版本层）

回答：**“这一次实际产出了什么？”**

职责：

- 保存本次产出视频/封面
- 保存最终商品名/最终文案快照
- 记录 `actual_duration_seconds`
- 作为审核对象存在

### 6.5 PublishPackage（发布冻结层）

回答：**“最终准备发布出去的冻结内容是什么？”**

职责：

- 冻结最终视频、封面、商品名、文案、话题
- 冻结发布 profile 与平台约束
- 形成不可歧义、可追溯的发布输入真相

### 6.6 Task（执行层）

回答：**“何时、在哪个账号、通过哪条执行路径去发布？”**

职责：

- 调度
- 执行状态流转
- 错误诊断
- 上传/发布结果
- 技术产物回写（如 `final_video_duration`）

原则：

> `Task` 继续存在，但不再承担“定义作品是什么”的责任。

## 7. 关键业务不变量

1. 作品输入必须保留顺序。
2. 同一素材可在同一作品中重复出现。
3. 重复素材实例必须可区分，不得自动去重。
4. `Creative.target_duration_seconds` 表达目标时长。
5. `CreativeVersion.actual_duration_seconds` 表达实际时长。
6. `Task.final_video_duration` 仅表达执行结果，不再充当作品目标时长。
7. 商品名称/文案必须允许“来源值”“作品当前采用值”“版本最终值”“发布冻结值”并存。
8. PublishPackage 必须成为发布前冻结真相层。

## 8. RALPLAN-DR（compact）

### Principles

1. 业务定义优先于执行参数。
2. 输入应建模为编排，不应建模为去重集合。
3. 来源层、作品层、版本层、发布层必须分责。
4. 迁移可以并行兼容，但新模型必须尽早成为 authoritative source。

### Top 3 Decision Drivers

1. **表达能力**：当前 `video_ids` 合同无法表达重复实例、顺序、trim、role。
2. **语义一致性**：Creative-first 产品主语义必须与领域模型对齐。
3. **迁移风险可控**：需要允许 legacy contract 过渡，同时避免继续固化旧语义。

### Options

#### Option A — 继续沿用集合快照模型，仅在 Creative 上追加字段

优点：

- 表面改动较小
- 短期兼容成本最低

缺点：

- 不能原生表达重复素材与编排
- 会继续固化 schema 去重与 hash 稳定合同
- 会让 Creative 继续停留在“素材篮”语义

#### Option B — 保持 Task 为主，Creative 只做展示壳

优点：

- 对现有执行层扰动最小
- 旧 Task 文档与部分实现无需重画

缺点：

- 与现有 Creative-first 事实相冲突
- 继续混淆“业务定义”和“执行对象”
- 会拖累 Workbench / Review / PublishPool 的后续设计

#### Option C — 采用分层模型，先锁 Creative 主语义，再分阶段迁移 API/执行层

优点：

- 与仓库现有产品真相一致
- 能承接重复视频、顺序、trim、role、目标时长等新增需求
- 允许执行层按阶段跟进，而不是一次性重写

缺点：

- 会出现短期“模型领先于执行层”的阶段差异
- 需要同步重写 test spec 与 migration contract

### Recommendation

**推荐 Option C。**

原因：它是唯一同时满足“语义正确、表达完整、迁移可控”的方案；其主要成本是规划与迁移纪律，而不是方向风险。

## 9. 迁移阶段与完成状态

### Phase 0 — 共识锁定（已完成）

产出：

- 正式 PRD
- companion test spec
- 决策记录与验收口径

退出条件：

- 团队认可新对象边界与新不变量
- 后续实现工作以新 test spec 为准

当前状态：

- 已完成，并沉淀为 master PRD / master test spec / execution breakdown 三件套
- Phase 0 closeout 已完成：`.omx/plans/closeout-creative-domain-model-realignment-phase0.md`

### Phase 1 — 模型并行引入（已完成）

目标：

- 引入 `CreativeInputItem`
- 为 Creative 增加作品层业务字段
- 保留 legacy snapshot/list 字段用于兼容回读
- **仅在本阶段允许双写**：新编排模型与旧列表 carrier 可以并行写入，但必须明确记录映射关系

退出条件：

- 新模型可被创建/读取
- legacy 字段仍可回读
- contract 明确谁是 authoritative source
- 双写范围与回退策略有书面约束，避免“隐式长期双轨”

当前状态：

- 已完成 `CreativeInputItem` / 作品层业务字段 / 受控双写与兼容回读的引入
- authoritative source 已开始从旧集合 carrier 向新编排模型迁移
- Phase 1 结果已被后续 Phase 2-4 持续消费与收口

### Phase 2 — API / Schema / 前端主语义切换（已完成）

目标：

- 创建/编辑作品的主入口转向“输入编排”
- Workbench / Detail 改为显示作品业务定义与版本/发布冻结语义
- **从本阶段开始**：authoring/UI/API 的 canonical semantic source = `CreativeInputItem`
- legacy list/snapshot 字段降级为 **compatibility carrier / read-only projection**，不得继续作为主语义写入口

退出条件：

- 前端主流程不再依赖旧集合字段拼装新语义
- 默认页面语义与新领域模型一致
- Phase 2+ 的新入口、新接口、新文档不再把 `video_ids` 等旧字段描述为 canonical authoring semantics

当前状态：

- 已完成 backend/API 语义源切换
- Workbench / Detail 主创作流已切到 canonical authoring semantics
- legacy list/snapshot 字段已降级为 compatibility carrier / deprecated projection

### Phase 3 — 版本与发布冻结落地（已完成）

目标：

- 版本层保存最终产出快照
- 发布包冻结四件套与平台约束
- Task 改为读取冻结结果执行

退出条件：

- 发布链路可追溯最终采用值
- Task 侧不再承担作品定义责任

当前状态：

- 已完成版本层结果归位与发布冻结语义落地
- `CreativeVersion` / `PackageRecord` 已承接最终采用值与冻结值
- Task 已收敛为执行与诊断载体

### Phase 4 — 退役旧合同（已完成）

目标：

- 弱化/删除去重快照合同
- deprecate `video_ids` 等集合式 public contract
- 将 hash 升级为编排快照 hash
- 正式移除 legacy carrier 的写语义，保留期结束后不再作为业务写入来源

退出条件：

- 旧集合 contract 不再是主要验收口径
- 新编排 contract 成为唯一主线
- legacy carrier retired；旧字段若仍存在，仅用于历史数据读取或迁移观察，不再承担新写入职责

当前状态：

- 已完成 legacy snapshot storage / public snapshot read contract / frontend snapshot narration 的正式退役
- Phase 4 PR ledger：
  - PR1 `5fb287b` — canonical orchestration contract / deprecation gate
  - PR2 `cd56b59` — runtime dual-write / fallback retirement
  - PR3 `81a2cf6` — frontend / SDK snapshot retirement
  - PR4 `bf34ec6` — physical cleanup + closeout evidence
- active runtime / frontend surface 已不再依赖 snapshot carriers
- destructive cleanup 已由 migration / regression / search audit 证明安全

### Phase 4 之后的主线结论

截至本轮收口，creative-domain 主线已经实现从“集合快照叙事”到“作品 / 输入编排 / 版本 / 发布冻结”模型的完整切换。

随后完成的 Workbench / CreativeDetail IA stabilization 不改变领域模型边界，而是把该模型在主要页面中的使用方式收口为：

- Workbench 是作品队列与运营处理入口。
- CreativeDetail 是作品定义、版本证据、审核结论、发布诊断的聚合页。
- Task 是执行与诊断承载面，不再反向定义作品。
- Diagnostics 是行动建议 + 原始证据，不是新的业务 mutation 面。

剩余 follow-up 不再属于本次主线收口阻塞项，主要包括：

1. deprecated request list fields 的 API hard-removal（可单开后续 slice）
2. task-diagnostics 首屏跳转偶发 E2E flake 的持续观察

## 10. 验收标准（testable）

视为本轮规划收敛完成，至少需要满足以下条件：

1. PRD 与 companion test spec 同步落盘，并明确新对象边界、迁移阶段、验证口径。
2. 文档明确引用仓库证据，至少覆盖：
   - `backend/schemas/__init__.py:595-625`
   - `backend/services/creative_service.py:756-835`
   - `backend/tests/test_creative_input_snapshot_contract.py:168-245`
   - `docs/domains/tasks/task-management-domain-model.md:41-60,110-118,136-159`
3. 新模型的不变量被明确写成可验证条目，而非抽象口号。
4. migration phases 明确说明：
   - 哪一阶段允许 legacy 双轨
   - 哪一阶段切主语义
   - 哪一阶段退役旧合同
5. 后续实现 handoff 可以直接按本文档拆解，而不需要重新做领域边界讨论。

截至 2026-04-23，上述规划验收已经被 Phase 1-4 的实现与 closeout 证据满足；后续验证与主线完成情况可回链：

- `.omx/plans/execution-breakdown-creative-domain-model-realignment.md`
- `.omx/plans/closeout-creative-domain-model-realignment-phase2.md`
- `.omx/plans/closeout-creative-domain-model-realignment-phase3.md`
- `.omx/plans/closeout-creative-domain-model-realignment-phase4.md`

## 11. 风险与缓解

| 风险 | 表现 | 缓解 |
| --- | --- | --- |
| 模型先行导致执行层暂时落后 | 文档先进，能力未跟上 | 明确 phased migration，不把执行层限制误写成业务边界 |
| 兼容期双轨过长 | 新旧语义长期并存 | 在 Phase 2/4 设退出门禁，禁止无限期保留旧 contract |
| 前端表面换名、底层仍拼装旧字段 | 语义迁移失败 | 在 test spec 中把“authoritative source 切换”设为必检项 |
| 版本层与发布层混淆 | 四件套最终值仍无冻结真相 | 分别锁定 Version 与 PublishPackage 的责任和验证点 |

## 12. 具体验证建议（供 companion test spec 使用）

后续 test spec 至少应覆盖五组验证：

1. **编排 contract**
   - 可重复添加同一素材
   - 顺序稳定
   - role/trim 独立
2. **作品 brief contract**
   - 商品名/主文案/目标时长属于作品层
3. **版本产出 contract**
   - 实际时长与最终采用值存在于版本层
4. **发布冻结 contract**
   - 四件套在发布前被明确冻结
5. **迁移兼容 contract**
   - legacy 字段可回读
   - 新模型是 authoritative source
   - 旧“去重 + hash 稳定”合同进入退役路径

## 13. 后续 staffing guidance（供 future $ralph / $team handoff）

当前**不启动 handoff**，但建议提前锁定执行编制：

### Available-Agent-Types Roster

- `architect`：领域边界、ADR、一致性与退出门禁
- `executor`：schema / service / API / frontend 渐进落地
- `test-engineer`：验证矩阵、targeted suites、manual checklist
- `verifier`：收集完成证据、校验 claim 与 test spec 对齐

### Ralph follow-up staffing guidance

- `$ralph` 单 owner follow-up：
  - `architect`（high）：守住领域边界、迁移阶段、ADR 一致性
  - `executor`（high）：负责 schema/service/API/FE 渐进落地
  - `verifier`（high）：负责 contract/E2E/manual 证据闭环

### Team follow-up staffing guidance

- `$team` 并行 follow-up：
  - 交付 lane：`executor` ×2（high）  
    - lane A：backend schema/service/migration contract  
    - lane B：frontend workbench/detail/version/publish semantics
  - 验证 lane：`test-engineer` ×1（medium）  
    - 新旧 contract、targeted E2E、manual checklist
  - 收口 lane：`architect` ×1（high）  
    - 审核边界未漂移、阶段退出门禁是否成立

### Team verification path

`$team` 路径在 shutdown 前至少证明：

1. backend contract / migration suites 对新 authoritative source 与旧 compatibility carrier 的边界有明确证据；
2. frontend targeted E2E 证明 workbench/detail/version/publish 主语义已切到新模型；
3. manual checklist 证明执行层限制被呈现为 capability limit，而不是业务模型限制；
4. architect lane 明确签字：Phase N 的退出条件已满足、Phase N+1 的旧合同未被误加固。

Ralph / final verifier 在 handoff 后还需复核：

1. 所有 evidence 是否对齐 companion test spec；
2. 是否仍存在 Phase 2+ 把旧列表字段当 canonical authoring semantics 的残留；
3. ADR 中的决策、后果、follow-ups 是否被实现过程破坏。

建议 launch hint（后续需要时再执行，而不是现在执行）：

- Ralph：`$ralph --prd creative domain model realignment implementation`
- Team：`$team 4 "implement creative domain model realignment with contract-first migration"`

## 14. ADR（execution handoff contract）

### Decision

采用 Option C：以 `Material / Creative / CreativeInputItem / CreativeVersion / PublishPackage / Task` 的分层模型作为主线，并按阶段推进语义切换与旧合同退役。

### Drivers

1. Creative-first 的产品主语义已经成立，需要与领域模型对齐。
2. 旧列表快照模型无法表达重复实例、顺序、trim、role。
3. 必须在迁移风险可控的前提下，防止兼容双轨演变成长期语义漂移。

### Alternatives considered

- **Option A**：继续沿用集合快照模型，仅在 Creative 上追加字段  
  - 放弃原因：无法承接编排语义，会继续加固去重/hash 稳定旧合同。
- **Option B**：保持 Task 为主，Creative 只做展示壳  
  - 放弃原因：与现有 Creative-first 主入口和业务流事实冲突。
- **Option C**：采用分层模型，先锁 Creative 主语义，再分阶段迁移 API/执行层  
  - 选用原因：语义正确、表达完整、迁移可控。

### Why chosen

它是唯一同时满足“Creative-first 产品真相”“重复素材编排能力”“可控兼容迁移”的方案。

### Consequences

- 短期会出现“模型领先于执行层”的阶段差异；
- 必须显式执行 anti-drift gate，不能让 legacy carrier 在 Phase 2+ 继续充当语义写入源；
- 验证工作必须覆盖版本/发布冻结与执行层限制呈现。

### Follow-ups

1. 依据 companion test spec 产出 execution breakdown；
2. 把 anti-drift 规则写入后续 API / UI / migration plan；
3. 评估 `local_ffmpeg V1 -> V2` 的多视频支持路径；
4. 规划旧 snapshot hash 到 orchestration hash 的退役步骤。

## 15. 一句话结论

> 下一步最合理的演进，不是继续给 `Creative` 叠加素材列表字段，而是把它正式升级为“作品 brief + 输入编排 + 版本产出 + 发布冻结”的业务主对象体系。
