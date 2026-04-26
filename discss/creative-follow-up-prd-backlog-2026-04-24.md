# Creative Follow-up PRD Backlog（基于 2026-04-24 总收口反推）

> 日期：2026-04-24  
> 前置总收口：`discss/creative-two-level-candidate-pool-adoption-closeout-2026-04-24.md`  
> 对应计划收口：`.omx/plans/closeout-creative-two-level-candidate-pool-adoption-2026-04-24.md`

---

## 1. 文档目的

本文件用于把 `creative-two-level-candidate-pool-adoption` 总收口之后的后续工作，整理成一份可执行的 **follow-up PRD backlog**。

目标不是重新打开已关闭主线，而是：

1. 明确哪些事项值得单独立项
2. 明确优先级与依赖关系
3. 明确哪些事项必须先走 `$ralplan`
4. 给出推荐执行顺序

---

## 2. 当前基线（已完成，不再重复立项）

以下主线已完成并关闭：

- `creative_items.current-*` 已成为当前真值面
- `creative_product_links.is_primary` 已成为 primary product 唯一入口
- `creative_candidate_items` 已成为作品候选池持久化表达
- selected-media projection 已成为 video/audio 当前入选的权威读口径
- Workbench 已切到后端 summary aggregator
- Version / Package / Publish 已切到统一 freeze / manifest 口径

因此，后续 PRD 必须遵守：

> **不再重开 current truth / candidate pool / selected-media / freeze authority 的主语义讨论。**

---

## 3. Follow-up PRD 清单总览

| Priority | PRD 名称 | 类型 | 价值 | 风险 | 推荐入口 |
| --- | --- | --- | --- | --- | --- |
| P0 | Creative API Compat Hard-Removal | contract / cleanup | 高 | 中 | `$ralplan --interactive --deliberate` |
| P1 | Publish Runtime Live Verification & Observability | production verification | 高 | 中 | `$ralplan --interactive` |
| P2 | Selected Media Physical Model Extraction | schema / migration | 中高 | 高 | `$ralplan --interactive --deliberate` |
| P3 | Creative Compat Field Physical Cleanup | physical cleanup | 中 | 中 | `$ralplan --interactive` |
| P4 | Creative Authoring / IA Upgrade on Stable Domain Truth | IA / UX | 中 | 中 | `$ralplan --interactive` |

---

## 4. 各 PRD 说明

## 4.1 P0 — Creative API Compat Hard-Removal

### 为什么它排第一

总收口已经明确 compat 字段只允许作为兼容回读存在，不应继续承接 authority。  
如果不先清理 API contract，后续任何开发都有可能继续把旧字段写回系统，导致新旧语义重新混杂。

### 目标

- 禁止 legacy authority write path
- 明确 request/response 中哪些字段已废弃
- 让 schema / serializer / service 只保留必要 compat read
- 补齐 OpenAPI / contract 测试

### 建议范围

- backend API schema / serializer / request parsing
- OpenAPI contract
- legacy write field deprecation / reject 规则
- compat read-only 边界

### 不应混入

- selected-media 物理迁移
- publish runtime 观测增强
- Workbench / Detail IA 改版

### 验收标准

- 新接口不再允许 legacy authority 写入
- compat 字段即使保留，也不参与主写路径
- OpenAPI / parity / regression tests 全通过

### 依赖

- 无；这是后续多项工作的前置清边界动作

### 推荐执行模式

- 必须先 `$ralplan --interactive --deliberate`
- 再拆成 2~3 个小 PR 执行

---

## 4.2 P1 — Publish Runtime Live Verification & Observability

### 为什么它排第二

当前 freeze / manifest 合同已统一，下一步最有价值的不是继续改模型，而是验证：

> **真正发出去、真正运行的内容，是否与当前真值一致。**

### 目标

- 建立 publish → package → runtime 的可验证链路
- 增强 manifest / package / execution snapshot 的诊断能力
- 增强故障定位与审计能力

### 建议范围

- publish/runtime 关键链路校验点
- execution / publish logs
- manifest / package / snapshot 对照诊断
- production-like verification checklist

### 不应混入

- schema 主语义调整
- selected-media 物理重构
- detail/workbench IA 改版

### 验收标准

- 可以回答“运行中的内容是否来自当前 freeze truth”
- 可以定位失败发生在 freeze/package/publish/runtime 哪一层
- 有稳定的验证入口与最小观测证据

### 依赖

- 最好在 P0 之后做，避免边观测边继续放大 compat 歧义

### 推荐执行模式

- 先 `$ralplan --interactive`
- 再按“观测增强 / live verification”分 slice

---

## 4.3 P2 — Selected Media Physical Model Extraction

### 为什么它不是第二而是第三

它很重要，但它属于 **高风险物理迁移**。  
在主语义已经稳定的情况下，应该优先先做 contract 收紧与生产验证，再动物理承载。

### 目标

- 评估 selected-media 是否应从 `creative_input_items` 迁出
- 如收益明确，建立独立物理模型
- 设计可回滚的迁移与 cutover

### 建议范围

- selected-media 独立表 / repo contract
- backfill / dual-read / cutover
- version/package/publish 读取一致性回归
- detail/workbench selected projection 回归

### 不应混入

- candidate pool 新语义
- workbench 新 summary contract
- authoring IA 改版

### 验收标准

- selected-media 具备独立清晰物理边界
- 外部读口径不变
- 数据迁移可验证、可回滚

### 依赖

- 推荐在 P0、P1 之后

### 推荐执行模式

- 必须先 `$ralplan --interactive --deliberate`

---

## 4.4 P3 — Creative Compat Field Physical Cleanup

### 为什么它排第四

这是典型的“物理清尾巴”工作，价值明确，但不应早于 contract hard-removal。

### 目标

- 物理删除已不再需要的 compat 字段/桥接代码
- 收敛 model / schema / serializer 中的历史残留

### 建议范围

- backend model cleanup
- serializer / mapper cleanup
- dead compat helper removal
- regression coverage

### 不应混入

- 新模型设计
- selected-media 独立迁移
- publish runtime 观测增强

### 验收标准

- 已确认无主路径依赖旧 compat 字段
- 删除后 contract / regression tests 仍通过

### 依赖

- 必须在 P0 之后
- 若 P2 要做，通常应在 P2 之后再做最终清理

### 推荐执行模式

- `$ralplan --interactive`

---

## 4.5 P4 — Creative Authoring / IA Upgrade on Stable Domain Truth

### 为什么它排最后

这项工作更偏体验提升，不应与 authority / migration / production verification 混做。

### 目标

- 在稳定 domain truth 前提下提升 Workbench / Detail 可理解性与可维护性
- 提高作者对“当前真值 / 候选 / 当前入选 / freeze”关系的可见性

### 建议范围

- Detail 信息架构优化
- Workbench 摘要与操作入口优化
- diagnostics / guidance / status surface 优化

### 不应混入

- schema authority 变更
- selected-media 物理迁移
- API compat hard-removal

### 验收标准

- 用户更容易理解作品当前定义状态
- UI 提升不改变既有 authority 口径
- 行为回归可被现有测试覆盖

### 依赖

- 无硬依赖
- 但最好在 P0 / P1 之后推进

### 推荐执行模式

- `$ralplan --interactive`

---

## 5. 推荐依赖图

```text
P0 API Compat Hard-Removal
├─> P1 Publish Runtime Live Verification & Observability
├─> P2 Selected Media Physical Model Extraction
│   └─> P3 Creative Compat Field Physical Cleanup
└─> P4 Creative Authoring / IA Upgrade on Stable Domain Truth
```

补充说明：

- `P3` 最适合放在 `P0` 之后、并在 `P2` 结束后做最终清尾
- `P4` 不依赖 `P2`，但应默认依赖 `P0` 的 contract 收紧结果

---

## 6. 推荐执行顺序

## 方案 A：我推荐的稳妥顺序

1. **P0 — API Compat Hard-Removal**
2. **P1 — Publish Runtime Live Verification & Observability**
3. **P2 — Selected Media Physical Model Extraction**
4. **P3 — Creative Compat Field Physical Cleanup**
5. **P4 — Creative Authoring / IA Upgrade on Stable Domain Truth**

适用场景：

- 希望先把 contract 收紧
- 再先证明生产链路可信
- 最后再做物理清理与体验提升

## 方案 B：偏技术债优先的顺序

1. **P0 — API Compat Hard-Removal**
2. **P2 — Selected Media Physical Model Extraction**
3. **P3 — Creative Compat Field Physical Cleanup**
4. **P1 — Publish Runtime Live Verification & Observability**
5. **P4 — Creative Authoring / IA Upgrade on Stable Domain Truth**

说明：

- 这条路线更激进
- 对迁移能力要求更高
- 不如方案 A 稳妥

---

## 7. 对应 OMX 启动建议

## 7.1 先开哪一个

如果只开下一份 follow-up PRD，我建议先开：

> **P0 — Creative API Compat Hard-Removal**

原因：

- 它直接巩固刚完成的总收口成果
- 它能阻止旧语义重新渗回主路径
- 它是后续多项工作的边界前置条件

## 7.2 推荐 OMX 指令顺序

### P0

```bash
$ralplan --interactive --deliberate "为 Creative API Compat Hard-Removal 建立执行计划。目标：只清理 legacy compat write/read authority，明确 deprecated/remove 边界，补齐 OpenAPI/contract tests；不要混入 selected-media 物理迁移、publish runtime observability、Workbench/Detail IA 改版。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐切片。"
```

### P1

```bash
$ralplan --interactive "为 Publish Runtime Live Verification & Observability 建立执行计划。目标：增强 publish/package/runtime 链路验证与观测，证明运行内容与 freeze truth 一致；不要混入 schema authority 改造。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐切片。"
```

### P2

```bash
$ralplan --interactive --deliberate "为 Selected Media Physical Model Extraction 建立执行计划。目标：评估并在收益明确时将 selected-media 从 creative_input_items 的迁移期 carrier 中抽离，形成独立物理模型；要求输出迁移策略、dual-read/cutover、回滚方案、test spec、风险、文件触点、验收标准。"
```

### P3

```bash
$ralplan --interactive "为 Creative Compat Field Physical Cleanup 建立执行计划。目标：在 contract hard-removal 稳定后，物理删除已失效 compat 字段与桥接代码；不要混入新模型设计。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐切片。"
```

### P4

```bash
$ralplan --interactive "为 Creative Authoring / IA Upgrade on Stable Domain Truth 建立执行计划。目标：在不改变 authority matrix 的前提下，优化 Workbench / Detail 的信息架构与状态呈现；不要混入 schema 迁移与 compat hard-removal。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐切片。"
```

---

## 8. 最终建议

这次总收口之后，最重要的不是立刻继续大改，而是遵守下面这条节奏：

> **先守住已收口的 authority 与 contract，再做生产验证，再做物理清理，最后做体验深化。**

因此，推荐你接下来的 follow-up PRD backlog 主线就是：

> **P0 → P1 → P2 → P3 → P4**

其中第一份最值得立即启动的，是：

> **Creative API Compat Hard-Removal**
