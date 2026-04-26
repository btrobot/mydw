# OMX 执行指令清单 — 作品二级候选池模型落地

## 1. 使用原则

这组指令按 **plan-first / slice-by-slice** 的方式组织。

建议执行规则：

1. 先做总规划
2. 每个 Slice 单独过一次 `ralplan`
3. 确认该 Slice 的 PRD / test spec 后，再执行 `ralph`
4. 每个 Slice 独立提交与验证

如果你想走最稳路线，就严格按顺序执行：

- Slice 1
- Slice 2
- Slice 3
- Slice 4
- Slice 5
- Slice 6

---

## 2. 总规划入口

```bash
$ralplan --interactive --deliberate "基于 discss/prd-work-two-level-candidate-pool-adoption-2026-04-24.md 与 discss/test-spec-work-two-level-candidate-pool-adoption-2026-04-24.md，为 creative 二级候选池模型落地建立总执行计划。目标覆盖 Slice 1-6：作品真值显式化、作品-商品关联表、作品候选池、当前入选媒体集合、Workbench 汇总升级、Version/Package 对齐。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐执行顺序。"
```

---

## 3. Slice 1：作品真值显式化

### 3.1 规划

```bash
$ralplan --interactive "执行 Slice 1 规划：作品真值显式化。目标：将商品名称 / 封面 / 文案提升为 CreativeDetail 中的显式作品真值；为 creative_items 增加 current-* 与 mode 字段；保持现有 URL、version、package 主流程不变。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐执行模式。"
```

### 3.2 执行

```bash
$ralph "执行已批准的 Slice 1：作品真值显式化。要求：先完成 backend creative_items / schemas 的 current-* 与 mode 字段接线，再更新 CreativeDetail 顶部当前定义区；保持现有生成、审核、发布主流程不变；禁止引入新依赖；先补/确认回归测试，再做 UI 与接口改造。"
```

---

## 4. Slice 2：作品-商品关联表

### 4.1 规划

```bash
$ralplan --interactive "执行 Slice 2 规划：作品-商品关联表。目标：支持一个作品关联多个商品、可调整顺序、仅一个主题商品；允许后续候选池从关联商品派生；不扩到素材候选池与 version/package。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐执行模式。"
```

### 4.2 执行

```bash
$ralph "执行已批准的 Slice 2：作品-商品关联表。要求：新增 creative_product_links 或等价模型，支持多商品关联、主题商品唯一、顺序调整；CreativeDetail 增加当前入选商品表；默认规则清晰但不得顺手扩到候选池全量实现；不引入 tab/subroute，不新增依赖。"
```

---

## 5. Slice 3：作品候选池

### 5.1 规划

```bash
$ralplan --interactive --deliberate "执行 Slice 3 规划：作品候选池。目标：正式引入作品小池，支持封面 / 文案 / 视频 / 音频候选；候选来源包括商品派生与素材库补充；保持 detail 页面信息架构稳定，不做版本/发布对齐。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐执行模式。"
```

### 5.2 执行

```bash
$ralph "执行已批准的 Slice 3：作品候选池。要求：新增 creative candidate surface（表或等价结构），在 CreativeDetail 增加候选列表区，清晰展示来源与状态；候选操作可驱动当前真值/当前入选，但必须保留手工覆盖边界；禁止把候选区做成资源管理页，不新增依赖。"
```

---

## 6. Slice 4：当前入选媒体集合

### 6.1 规划

```bash
$ralplan --interactive "执行 Slice 4 规划：当前入选媒体集合。目标：将视频 / 音频从泛化 input 编排语义中收敛成清晰的当前入选集合，形成候选表与当前入选表联动；保持现有 composition 主流程可兼容。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐执行模式。"
```

### 6.2 执行

```bash
$ralph "执行已批准的 Slice 4：当前入选媒体集合。要求：优先兼容复用 creative_input_items 或等价结构表达 video/audio 当前入选；在 CreativeDetail 中形成候选 ↔ 当前入选双区联动；支持排序、启停、移除；合成只读取当前入选集合；不做复杂时间线编辑器，不新增依赖。"
```

---

## 7. Slice 5：Workbench 汇总升级

### 7.1 规划

```bash
$ralplan --interactive "执行 Slice 5 规划：Workbench 汇总升级。目标：让 CreativeWorkbench 显示当前真值摘要、当前入选摘要、定义完成度与 composition readiness；保持现有搜索、筛选、排序、preset、diagnostics URL 语义稳定。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐执行模式。"
```

### 7.2 执行

```bash
$ralph "执行已批准的 Slice 5：Workbench 汇总升级。要求：扩展 creative list summary 字段，在 WorkbenchTable / SummaryCard / DiagnosticsDrawer 中展示 current truth 与 selected media 摘要；不得破坏现有服务端检索、preset、sort、page、diagnostics 语义；先跑现有 workbench 回归，再补最小必要测试。"
```

---

## 8. Slice 6：Version / Package 对齐

### 8.1 规划

```bash
$ralplan --interactive "执行 Slice 6 规划：Version / Package 对齐。目标：让 creative_versions 与 package_records 冻结当前真值与当前入选快照；保证生成版本与发布包可回溯；不扩到新发布渠道或后端流程重写。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐执行模式。"
```

### 8.2 执行

```bash
$ralph "执行已批准的 Slice 6：Version / Package 对齐。要求：creative_versions 冻结 final 四件套与当前入选 manifest，package_records 冻结发布时四件套与输入快照；更新 VersionPanel / 发布包预览接线；保持现有审核/发布动作边界不变，不新增依赖。"
```

---

## 9. 推荐收口命令

当 Slice 1-6 全部完成后，建议执行一次总收口：

```bash
$ralplan --interactive "检查作品二级候选池模型落地计划执行情况。如果 Slice 1-6 已完成并验证通过，请输出最终收口总结：包含完成项、剩余风险、与 discss/work-two-level-candidate-pool-ia-data-roadmap-2026-04-24.md 的对齐情况，并给出是否需要并入 roadmap / 总 PRD 的建议。"
```

如需实际做收口文档与并盘：

```bash
$ralph "执行已批准的作品二级候选池模型最终收口：汇总 Slice 1-6 完成情况、验证证据、剩余风险，并将结论并入 roadmap / 总 PRD；不得混入新的实现工作。"
```

---

## 10. 最务实的执行顺序

如果你想直接开干，推荐就是下面这 7 步：

1. 总规划入口
2. Slice 1 规划 + 执行
3. Slice 2 规划 + 执行
4. Slice 3 规划 + 执行
5. Slice 4 规划 + 执行
6. Slice 5 规划 + 执行
7. Slice 6 规划 + 执行

一句话总结：

> **先把 Detail 做对，再让 Workbench 看懂，最后让 Version/Package 冻结。**

