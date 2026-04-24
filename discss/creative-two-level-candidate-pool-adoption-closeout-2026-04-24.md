# 作品二级候选池计划总收口

> 日期：2026-04-24  
> 对应计划 PRD：`.omx/plans/prd-creative-two-level-candidate-pool-adoption-2026-04-24.md`  
> 对应讨论 PRD：`discss/prd-work-two-level-candidate-pool-adoption-2026-04-24.md`  
> 对应 test spec：`.omx/plans/test-spec-creative-two-level-candidate-pool-adoption-2026-04-24.md`  
> 对应 roadmap：`discss/work-two-level-candidate-pool-ia-data-roadmap-2026-04-24.md`

---

## 1. 总结论

`creative-two-level-candidate-pool-adoption` 这条主线已经完成总收口。

它完成的不是单点修补，而是把 creative 的主语义正式收敛为：

> **作品当前真值 + 作品候选池 + 当前入选媒体 + 统一 freeze/manifest 口径。**

因此，从 2026-04-24 起，这条计划应视为：

> **已完成主线，不再继续追加 Slice。**

---

## 2. 完成矩阵

| Phase / Slice | 目标 | 状态 | 代表提交 |
| --- | --- | --- | --- |
| Phase 0 | 冻结 authority / contract baseline | completed | `454eac9` |
| Slice 1 | 作品真值显式化 | completed | `2fb9561` |
| Slice 2 | 作品-商品关联表 | completed | `38b8a29` |
| Slice 3 | 作品候选池 | completed | `6333d13` |
| Slice 4 | 当前入选媒体集合 / selected-media projection | completed | `a426abd`、`867c80d` |
| Slice 5 | Workbench 汇总升级 | completed | `b81fcad` |
| Slice 6 | Version / Package 对齐 | completed | `9a49bb9` |

Slice 4 的最终稳定化还由以下提交补强：

- `6e42b75`
- `33dcc21`
- `ace91e0`

---

## 3. 最终收口后的系统口径

### 3.1 当前真值

作品当前定义以 `creative_items.current-*` 为准，包括：

- 当前商品名称
- 当前封面
- 当前文案

### 3.2 主题商品

主题商品以 `creative_product_links.is_primary` 为唯一主入口；旧 `subject_product_id` 仅保留兼容意义。

### 3.3 候选池

作品候选范围以 `creative_candidate_items` 为准；候选与当前入选不再混用。

### 3.4 当前入选媒体

当前真正参与作品的 `video/audio` 由 selected-media projection 表达；迁移期仍物理复用 `creative_input_items`，但 authority 已收紧。

### 3.5 Workbench 汇总

Workbench 只消费后端 summary aggregator，不再由前端临时拼装 summary 作为长期方案。

### 3.6 Version / Package / Publish

冻结口径以统一 freeze/manifest contract 为准，不再允许多套 ad-hoc snapshot builder 并行演化。

---

## 4. 已并入 roadmap 与总 PRD 的内容

### roadmap

`discss/work-two-level-candidate-pool-ia-data-roadmap-2026-04-24.md` 已补入“执行收口状态”，把原先的未来路线改写为：

- 已实现迁移回放
- 当前边界说明
- 后续 follow-up 划界

### 总 PRD

`discss/prd-work-two-level-candidate-pool-adoption-2026-04-24.md` 已补入 “2026-04-24 总收口更新”，把原先的目标式表述改写为：

- 已完成矩阵
- 当前系统口径
- 本 PRD 的关闭边界

同时，计划侧主 PRD `.omx/plans/prd-creative-two-level-candidate-pool-adoption-2026-04-24.md` 也已补入 master closeout update。

---

## 5. 验证摘要

本次总收口沿用各 Slice 已完成实现与历史验证证据，并补充最终收口验证：

- backend freeze / publish / openapi / slice6 contracts：通过
- frontend generated check：通过
- frontend typecheck：通过
- frontend build：通过

此外，本轮文档已完成 UTF-8 读回验证。

---

## 6. 后续不再属于本计划主线的事项

以下事项如果继续推进，应单列 follow-up：

1. legacy compat write fields 的 hard-removal
2. `creative_input_items` 是否迁移为独立 selected-media 物理表
3. publish/runtime live verification 与 observability 增强

---

## 7. 最终退出结论

这条计划的退出条件已经满足：

- Phase 0 + Slice 1~6 已全部完成
- authority matrix 已被实现吸收
- Workbench / Detail / Version / Package / Publish 已围绕同一套 current truth + selected-media + freeze contract 运转
- 剩余事项已清晰转化为独立 follow-up，而非“本计划未完成”

因此，本计划现在可以正式关闭。
