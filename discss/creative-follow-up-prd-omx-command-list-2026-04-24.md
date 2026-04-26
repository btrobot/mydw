# Creative Follow-up PRD OMX 指令清单

> 日期：2026-04-24  
> 对应 backlog：`discss/creative-follow-up-prd-backlog-2026-04-24.md`

---

## 1. 使用方式

这份文档不是新的 PRD，而是把 backlog 里的 follow-up 项，整理成 **可直接复制执行的 OMX 指令**。

适用原则：

1. 先跑 `$ralplan`
2. 等 PRD / test spec / slice 计划出来
3. 再按 slice 用 `$ralph` 执行

当前推荐启动顺序：

> **P0 → P1 → P2 → P3 → P4**

---

## 2. 第一优先：P0 — Creative API Compat Hard-Removal

## 2.1 规划命令

```bash
$ralplan --interactive --deliberate "为 Creative API Compat Hard-Removal 建立执行计划。目标：只清理 legacy compat write/read authority，明确 deprecated/remove 边界，补齐 OpenAPI/contract tests；不得混入 selected-media 物理迁移、publish runtime observability、Workbench/Detail IA 改版。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐切片。"
```

## 2.2 规划产物出来后，建议继续追问

```bash
$ralplan --interactive "把 Creative API Compat Hard-Removal 拆成可执行 PR 计划，输出 ralph-ready 格式。要求按低风险优先拆 slice，先 contract gate，再 schema/serializer/service cleanup，最后 compat read-only 收口与文档更新。"
```

## 2.3 进入执行时的推荐节奏

```bash
$ralph "执行已批准的 Creative API Compat Hard-Removal Slice 1：contract gate / request boundary 收紧。禁止混入 selected-media 迁移、publish runtime observability、Workbench/Detail IA 改版。完成后给出 changed files、verification evidence、remaining risks。"
```

---

## 3. 第二优先：P1 — Publish Runtime Live Verification & Observability

## 3.1 规划命令

```bash
$ralplan --interactive "为 Publish Runtime Live Verification & Observability 建立执行计划。目标：增强 publish/package/runtime 链路验证与观测，证明运行内容与 freeze truth 一致；不要混入 schema authority 改造与 selected-media 物理迁移。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐切片。"
```

## 3.2 规划产物出来后，建议继续追问

```bash
$ralplan --interactive "把 Publish Runtime Live Verification & Observability 拆成可执行 PR 计划，输出 ralph-ready 格式。优先拆为观测字段/日志、链路校验、失败诊断与运行验证脚本三个层次。"
```

## 3.3 进入执行时的推荐节奏

```bash
$ralph "执行已批准的 Publish Runtime Live Verification & Observability Slice 1：补齐 publish/package/runtime 最小观测证据与诊断字段，不改 domain authority，不改 selected-media 物理承载。完成后给出 changed files、verification evidence、remaining risks。"
```

---

## 4. 第三优先：P2 — Selected Media Physical Model Extraction

## 4.1 规划命令

```bash
$ralplan --interactive --deliberate "为 Selected Media Physical Model Extraction 建立执行计划。目标：评估并在收益明确时将 selected-media 从 creative_input_items 的迁移期 carrier 中抽离，形成独立物理模型；要求输出迁移策略、dual-read/cutover、回滚方案、test spec、风险、文件触点、验收标准。不要混入新的 authoring/workbench 语义扩边界。"
```

## 4.2 规划产物出来后，建议继续追问

```bash
$ralplan --interactive --deliberate "把 Selected Media Physical Model Extraction 拆成可执行 PR 计划，输出 ralph-ready 格式。要求先做 schema/contract plan 与 dual-read 保护，再做 backfill/cutover，最后做 compat 清理；每个 slice 都必须可回滚。"
```

## 4.3 进入执行时的推荐节奏

```bash
$ralph "执行已批准的 Selected Media Physical Model Extraction Slice 1：建立独立 schema/contract 与 dual-read 保护，不做最终 cutover，不做 compat hard-delete。完成后给出 changed files、verification evidence、remaining risks。"
```

---

## 5. 第四优先：P3 — Creative Compat Field Physical Cleanup

## 5.1 规划命令

```bash
$ralplan --interactive "为 Creative Compat Field Physical Cleanup 建立执行计划。目标：在 contract hard-removal 稳定后，物理删除已失效 compat 字段与桥接代码；不要混入新模型设计、selected-media 物理迁移、publish runtime observability。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐切片。"
```

## 5.2 规划产物出来后，建议继续追问

```bash
$ralplan --interactive "把 Creative Compat Field Physical Cleanup 拆成可执行 PR 计划，输出 ralph-ready 格式。要求先删 dead mapper/helper，再删字段依赖，最后做文档与测试收口。"
```

## 5.3 进入执行时的推荐节奏

```bash
$ralph "执行已批准的 Creative Compat Field Physical Cleanup Slice 1：删除已确认失效的 compat helper / mapper / dead path，不动高风险迁移，不动 publish runtime observability。完成后给出 changed files、verification evidence、remaining risks。"
```

---

## 6. 第五优先：P4 — Creative Authoring / IA Upgrade on Stable Domain Truth

## 6.1 规划命令

```bash
$ralplan --interactive "为 Creative Authoring / IA Upgrade on Stable Domain Truth 建立执行计划。目标：在不改变 authority matrix 的前提下，优化 Workbench / Detail 的信息架构与状态呈现，提升 current truth / candidate / selected-media / freeze 的可理解性；不要混入 schema 迁移与 compat hard-removal。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐切片。"
```

## 6.2 规划产物出来后，建议继续追问

```bash
$ralplan --interactive "把 Creative Authoring / IA Upgrade on Stable Domain Truth 拆成可执行 PR 计划，输出 ralph-ready 格式。要求优先低风险信息架构与 diagnostics 改善，再评估更大交互调整。"
```

## 6.3 进入执行时的推荐节奏

```bash
$ralph "执行已批准的 Creative Authoring / IA Upgrade on Stable Domain Truth Slice 1：只做低风险信息架构整理与状态可见性提升，不改 authority，不改 URL 语义，不改 schema。完成后给出 changed files、verification evidence、remaining risks。"
```

---

## 7. 最推荐的直接起跑命令

如果你现在就要开始下一条主线，我建议直接复制这一条：

```bash
$ralplan --interactive --deliberate "为 Creative API Compat Hard-Removal 建立执行计划。目标：只清理 legacy compat write/read authority，明确 deprecated/remove 边界，补齐 OpenAPI/contract tests；不得混入 selected-media 物理迁移、publish runtime observability、Workbench/Detail IA 改版。要求输出 PRD、test spec、风险、文件触点、验收标准、推荐切片。"
```

---

## 8. 一句话策略

这批 follow-up 的执行策略应保持为：

> **先 contract 收紧，再生产验证，再物理迁移，再物理清尾，最后做 IA/UX 深化。**
