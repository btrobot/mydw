# 对应 Slice 2~6 的可直接复制 OMX 指令清单

日期：2026-04-24

关联文档：

- `discss/creative-two-level-candidate-pool-execution-rhythm-rules-2026-04-24.md`
- `discss/creative-two-level-candidate-pool-slice-2-6-execution-judgment-2026-04-24.md`
- `.omx/plans/prd-creative-two-level-candidate-pool-adoption-2026-04-24.md`
- `.omx/plans/test-spec-creative-two-level-candidate-pool-adoption-2026-04-24.md`

---

## 1. 使用说明

这份清单按当前推荐节奏组织：

- **Slice 2：直做**
- **Slice 3：直做**
- **Slice 4：先局部 ralplan，再执行**
- **Slice 5：条件直做**
- **Slice 6：先局部 ralplan，再执行**

默认原则：

1. 所有执行都以现有 PRD / test spec 为上位约束
2. 不允许未说明的扩边界
3. 每个 Slice 完成后都要 fresh verification
4. 若执行中发现 authority / freeze / manifest / summary contract 漂移，立即停止并回到 `$ralplan`

---

## 2. Slice 2：作品-商品关联表

## 2.1 直接执行

```bash
$ralph "执行已批准的 Slice 2：作品-商品关联表。严格遵守已冻结 primary-product 规则与 authority matrix；落地作品-商品关联、主题商品唯一性、顺序调整、默认跟随与手工覆盖；不进入候选池、不进入 selected-media、不改 Workbench summary、不改 Version/Package freeze 语义。完成后给出 changed files、verification evidence、remaining risks。"
```

## 2.2 如果执行中发现规则不够清楚，退回补规划

```bash
$ralplan --interactive "只规划 Slice 2：作品-商品关联表。补齐 primary-product 切换规则、subject_product_id 与 primary link 对应关系、默认跟随/手工覆盖边界、文件触点、验收标准与推荐执行模式；不要扩到候选池、selected-media、Workbench summary、Version/Package。"
```

---

## 3. Slice 3：作品候选池

## 3.1 直接执行

```bash
$ralph "执行已批准的 Slice 3：作品候选池。仅落地作品级 candidate pool 的 CRUD / adopt / remove / status 合同；保持候选与当前入选分层，不提前进入 selected-media 总收口，不改 Version/Package freeze 逻辑，不改 Workbench summary contract。完成后给出 changed files、verification evidence、remaining risks。"
```

## 3.2 如果候选池状态机或边界说不清，退回补规划

```bash
$ralplan --interactive "只规划 Slice 3：作品候选池。补齐 candidate_type/source_kind/status 合同、adopt/remove 边界、与当前入选集合的职责分层、文件触点、验收标准与推荐执行模式；不要扩到 selected-media、Workbench 汇总、Version/Package 对齐。"
```

---

## 4. Slice 4：当前入选媒体集合

## 4.1 先做局部规划

```bash
$ralplan --interactive "只规划 Slice 4：当前入选媒体集合。补齐 selected-media projection contract、creative_input_items 兼容边界、video/audio 顺序与 enabled 语义、候选转入选动作边界、文件触点、验收标准与推荐执行模式；不要扩到 Workbench 汇总与 Version/Package 对齐。"
```

## 4.2 规划批准后执行

```bash
$ralph "执行已批准的 Slice 4：当前入选媒体集合。严格按 selected-media projection contract 落地；明确当前真正入选的 video/audio 集合、顺序、enabled 语义与候选转入选规则；保持 creative_input_items 只作为已批准的兼容桥接，不提前扩边界到 Workbench/Version/Package 总收口。完成后给出 changed files、verification evidence、remaining risks。"
```

---

## 5. Slice 5：Workbench 汇总升级

## 5.1 满足前置条件时直接执行

前置条件：

- Slice 2 已稳定
- Slice 3 已稳定
- Slice 4 已明确 selected-media projection contract
- Phase 0 的 Workbench summary mapping 未被推翻

满足时执行：

```bash
$ralph "执行已批准的 Slice 5：Workbench 汇总升级。以已冻结 workbench summary mapping 为唯一口径；Workbench 只消费后端聚合结果，补齐 current_product_name、selected/candidate 媒体计数、definition_ready、composition_ready 等摘要字段；不得让前端自行拼接 summary，不扩展到 Version/Package 语义。完成后给出 changed files、verification evidence、remaining risks。"
```

## 5.2 如果 summary mapping 发生漂移，先补局部规划

```bash
$ralplan --interactive "只规划 Slice 5：Workbench 汇总升级。重新确认 workbench summary mapping、后端聚合口径、前端只读消费边界、preset/filter/sort 回归保护、文件触点、验收标准与推荐执行模式；不要扩到 Version/Package 最终收口。"
```

---

## 6. Slice 6：Version / Package 对齐

## 6.1 先做局部规划

```bash
$ralplan --interactive --deliberate "只规划 Slice 6：Version / Package 对齐。基于 Slice 2~5 的实际落地结果，重新确认 version freeze source、package freeze source、manifest v1 typed contract、publish/version/package 统一读取口径、compat projection 退场边界、文件触点、验收标准与推荐执行模式；不要混入新的 authoring/workbench 扩边界。"
```

## 6.2 规划批准后执行

```bash
$ralph "执行已批准的 Slice 6：Version / Package 对齐。严格按最新 freeze/manifest 合同收口，统一 Version/Package/Publish 的读取口径，完成 compat projection 的受控退场；不混入新的 authoring/workbench 语义改造。完成后给出 changed files、verification evidence、remaining risks。"
```

---

## 7. 推荐顺序版清单

如果你想按推荐顺序一个个执行，直接复制下面这组：

```bash
$ralph "执行已批准的 Slice 2：作品-商品关联表。严格遵守已冻结 primary-product 规则与 authority matrix；落地作品-商品关联、主题商品唯一性、顺序调整、默认跟随与手工覆盖；不进入候选池、不进入 selected-media、不改 Workbench summary、不改 Version/Package freeze 语义。完成后给出 changed files、verification evidence、remaining risks。"
```

```bash
$ralph "执行已批准的 Slice 3：作品候选池。仅落地作品级 candidate pool 的 CRUD / adopt / remove / status 合同；保持候选与当前入选分层，不提前进入 selected-media 总收口，不改 Version/Package freeze 逻辑，不改 Workbench summary contract。完成后给出 changed files、verification evidence、remaining risks。"
```

```bash
$ralplan --interactive "只规划 Slice 4：当前入选媒体集合。补齐 selected-media projection contract、creative_input_items 兼容边界、video/audio 顺序与 enabled 语义、候选转入选动作边界、文件触点、验收标准与推荐执行模式；不要扩到 Workbench 汇总与 Version/Package 对齐。"
```

```bash
$ralph "执行已批准的 Slice 4：当前入选媒体集合。严格按 selected-media projection contract 落地；明确当前真正入选的 video/audio 集合、顺序、enabled 语义与候选转入选规则；保持 creative_input_items 只作为已批准的兼容桥接，不提前扩边界到 Workbench/Version/Package 总收口。完成后给出 changed files、verification evidence、remaining risks。"
```

```bash
$ralph "执行已批准的 Slice 5：Workbench 汇总升级。以已冻结 workbench summary mapping 为唯一口径；Workbench 只消费后端聚合结果，补齐 current_product_name、selected/candidate 媒体计数、definition_ready、composition_ready 等摘要字段；不得让前端自行拼接 summary，不扩展到 Version/Package 语义。完成后给出 changed files、verification evidence、remaining risks。"
```

```bash
$ralplan --interactive --deliberate "只规划 Slice 6：Version / Package 对齐。基于 Slice 2~5 的实际落地结果，重新确认 version freeze source、package freeze source、manifest v1 typed contract、publish/version/package 统一读取口径、compat projection 退场边界、文件触点、验收标准与推荐执行模式；不要混入新的 authoring/workbench 扩边界。"
```

```bash
$ralph "执行已批准的 Slice 6：Version / Package 对齐。严格按最新 freeze/manifest 合同收口，统一 Version/Package/Publish 的读取口径，完成 compat projection 的受控退场；不混入新的 authoring/workbench 语义改造。完成后给出 changed files、verification evidence、remaining risks。"
```

---

## 8. 最终建议

如果你要把这套清单作为当前阶段的默认执行法，可以直接记成一句话：

> **2、3 直接做；4 先局部 ralplan 再做；5 在 4 稳定后直接做；6 必须再过一次 deliberate ralplan 后再做。**

这样既保留速度，也保留关键收口点的安全性。
