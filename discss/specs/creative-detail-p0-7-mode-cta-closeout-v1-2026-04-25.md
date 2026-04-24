# 《CreativeDetail P0-7 页面模式 / 头部 CTA 收口完成说明 v1》

日期：2026-04-25  
对应切片：Slice P0-7

---

## 1. 本次完成内容

本 Slice 继续收口 CreativeDetail 首屏的“主任务表达”：

- 头部增加更明确的页面模式表达
- Hero 主 CTA 改为随模式变化
- 结果态 / 发布态不再继续硬套 readiness 语言
- 顶部额外动作去掉并列 primary，避免和首屏主 CTA 争夺焦点
- E2E 补充 reviewing / authoring 两种语义切换验证

---

## 2. 本次收口的核心问题

P0-6 之后，A/B/C 交互已经基本可用，但首屏仍存在两个问题：

1. **头部语言不够像“当前模式”**
   - review / publish 场景下，首屏还容易沿用 authoring 的表述

2. **主 CTA 还不够唯一**
   - 页面上已有多个强动作入口，用户不容易判断“此刻最正确的一步”

所以本次目标不是再加业务能力，而是：

> **把首屏主任务表达进一步拉直。**

---

## 3. 具体实现

### 3.1 增加前端交互模式归纳

在 `CreativeDetail.tsx` 内增加轻量 mode summary，把现有状态翻译成首屏语义：

- `authoring`
- `submitting`
- `reviewing`
- `reworking`
- `publishing`
- `published_followup`
- `failed_recovery`

这一步先只用于首屏表达，不扩大到整页权限治理。

### 3.2 Hero 改为模式感知

`CreativeDetailHeroCard` 不再内置固定的：

- 保存
- 提交
- 诊断

而是改成由页面层传入：

- `modeMeta`
- `summaryTitle`
- `summaryLead`
- `summarySupportingText`
- `primaryAction`
- `secondaryActions`

这样首屏可以按模式切换：

- authoring：`readiness 摘要` + 保存 / 提交
- reviewing：`结果待确认摘要` + 审核当前版本
- submitting：`生成进度摘要` + 查看任务进度
- publishing / published：`发布跟进摘要` + 查看高级诊断

### 3.3 结果态不再用 readiness 语言强行主导

对于 reviewing / publishing / published / failed 等模式，
首屏摘要改成结果状态语言：

- `结果待确认摘要`
- `生成进度摘要`
- `发布跟进摘要`
- `失败恢复摘要`

从而更贴近 PRD 中“结果态由结果语言承接”的要求。

### 3.4 弱化顶部低频动作

保留顶部入口：

- 高级诊断
- AIClip
- 审核当前版本

但把顶部“审核当前版本”从 primary 改为普通按钮，避免首屏同时存在两个最强动作。

### 3.5 新增模式提示条

对于非纯 authoring 场景，首屏增加轻量提示条：

- reviewing：先审核当前版本
- submitting：先关注执行进度
- publishing：先关注发布状态与诊断
- published：先关注发布记录
- failed：先确认失败点

---

## 4. 涉及文件

- `frontend/src/features/creative/components/detail/CreativeDetailProjection.tsx`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- `discss/specs/creative-detail-p0-7-mode-cta-closeout-plan-v1-2026-04-25.md`
- `discss/specs/creative-detail-p0-7-mode-cta-closeout-v1-2026-04-25.md`

---

## 5. 验证结果

已执行：

- `pnpm typecheck`
- `pnpm test:e2e -- e2e/creative-workbench/creative-workbench.spec.ts --project=chromium --grep "renders projection-driven creative detail shell before legacy editor|switches hero summary and primary CTA back to authoring semantics when detail is editable|updates current selection from product and free-material zone actions before save|supports in-zone editing and clearing inside the current selection section|supports drag sorting inside current selection videos"`
- `pnpm test:e2e -- e2e/creative-workbench/creative-workbench.spec.ts --project=chromium --grep "renders projection-driven creative detail shell before legacy editor|switches hero summary and primary CTA back to authoring semantics when detail is editable|updates current selection from product and free-material zone actions before save|supports in-zone editing and clearing inside the current selection section|supports in-zone video ordering and role editing inside current selection|supports in-zone video trim and slot duration editing inside current selection|blocks save when current selection video timing is invalid|supports drag sorting inside current selection videos"`

验证结论：

- reviewing 态首屏已切到“结果确认”语义
- authoring 态首屏已切回 readiness + 提交语义
- 现有 A/B/C 联动未被回退
- 视频顺序 / timing / drag 等 P0-4 ~ P0-6 能力未被回退

---

## 6. 当前边界

本次仍然是“表达收口”，不是完整锁定态治理：

- 没有在本 Slice 把 reviewing / publishing 全量改成只读
- 没有引入新的领域动作（如真正发起发布）
- 没有改造版本确认机制本身

也就是说：

> **先把首屏主任务说清楚，再决定是否继续推进整页读写权限切换。**

---

## 7. 下一步建议

P0-7 完成后，P0 剩余更像两条路：

1. **P0-8：锁定态 / 只读态真正收口**
   - reviewing / publishing / published 下 A/B/C 是否应降级只读
   - 哪些按钮该禁用 / 折叠 / 迁移

2. **P0-9：P0 验收与回归总收口**
   - 按 PRD / AC / TC 做更完整的回归闭环
   - 补充剩余 detail-focused E2E

如果继续沿着“P0 主任务表达”推进，最自然的下一步是：

> **P0-8：锁定态 / 只读态收口。**

