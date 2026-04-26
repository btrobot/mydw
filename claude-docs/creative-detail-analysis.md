# CreativeDetail 交互设计分析

> 分析日期：2026-04-25
> 分析依据：
> - `discss/specs/creative-detail-converged-prd-v1-2026-04-24.md`
> - `discss/specs/creative-detail-three-zone-structure-note-v1-2026-04-24.md`
> - `discss/specs/creative-detail-state-machine-page-mode-spec-v1-2026-04-24.md`
> - `discss/specs/creative-detail-whole-page-lowfi-wireframe-copy-v1-2026-04-24.md`
> - `discss/specs/creative-detail-first-screen-lowfi-wireframe-copy-v1-2026-04-24.md`
> - `discss/specs/creative-detail-p0-gap-closure-ralplan-approval-note-v1-2026-04-25.md`
> - `discss/specs/creative-detail-p0-2-frontend-shell-closeout-v1-2026-04-25.md`
> - `frontend/src/features/creative/pages/CreativeDetail.tsx`（2,228 行）

---

## 一、设计意图总结

### 1.1 页面定位

CreativeDetail 的核心定位：

> **为当前作品定稿生成输入的页面。**

不是任务详情页，不是纯审核页，不是纯发布页。它要回答的核心问题是：

> **如果现在就去生成，这条作品到底会拿什么去生成？**

### 1.2 三区结构

```
入选区      ←  最终定稿（最终真值）
商品区      ←  默认来源（主题商品的候选）
自由素材区  ←  补充来源（非主题商品的候选）
```

关系：`商品区 + 自由素材区 → 入选区`

### 1.3 输入合同

| 类型 | 字段 | 规则 |
|------|------|------|
| 唯一位 | 商品名称、封面、文案、音频 | 同一时刻只有一个当前值 |
| 集合位 | 视频集合 | 可以有多个已入选视频 |

### 1.4 四种主状态

| 状态 | 页面重点 | 可编辑区 | 主 CTA |
|------|---------|---------|--------|
| 草稿（authoring） | A/B/C 三区 | 全部可编辑 | 提交生成 |
| 生成中（submitting） | 任务进度 | 全部锁定 | 查看任务 |
| 结果确认（reviewing） | D 区前移 | B/C 折叠 | 确认采用 / 重新生成 |
| 已发布（published_followup） | E 区展开 | 全部只读 | 查看发布记录 |

### 1.5 一个核心边界

> **只有"提交生成"才创建新版本。保存/确认/发布都不建版本。**

---

## 二、设计与实现的差距

### 2.1 差距总览

| 设计意图 | 实际实现 | 差距程度 |
|---------|---------|---------|
| 区内操作形成闭环 | 区内操作改 Form，需点保存才生效 | 严重 |
| legacy editor 应后移/废弃 | 800 行表单仍占据页面 40% | 严重 |
| 7 种状态应有不同布局 | 所有状态渲染同样结构，仅按钮显隐 | 中等 |
| 首屏 A/B/C 三区并重 | Hero + 多个 Alert 抢占首屏焦点 | 中等 |

### 2.2 差距 1：B/C 区操作闭环未完成

**设计意图**：

```
商品封面 → "设为当前封面" → A 区封面立即刷新
         ↓
      实时生效，不需要保存
```

**实际实现**：

- B/C 区的操作通过 `useCreativeAuthoringModel` 维护的 Form（product_links / candidate_items / input_items）来写
- 保存依赖 legacy editor 里的"保存创作定义"按钮
- 区内操作和保存之间没有闭环

**后果**：用户在 B 区点"设为当前封面"，实际上改的是 Form 数据，必须跳到 legacy editor 点保存才生效。区内操作名存实亡。

**代码位置**：`CreativeDetail.tsx` line 861-926（B/C 区的操作函数）和 line 1289-1294（保存按钮）。

### 2.3 差距 2：legacy editor 仍是主要编辑入口

**设计意图**：首屏改为 A/B/C 三区，legacy editor 后移为"兼容编辑区"。

**实际实现**：

- B/C 区的"编辑"按钮跳转的是 `#creative-detail-product-editor`（legacy editor 的锚点）
- P0-3 计划说"把兼容编辑区继续拆解"，但还未执行
- legacy editor 仍有 800 行，占据页面 line 1277-1873

**后果**：用户以为在用新 A/B/C 三区，但实际操作还是回到 legacy editor。

### 2.4 差距 3：状态模式仅通过按钮显隐表达

**设计意图**（按 PRD）：

```
authoring   → A/B/C 三区并重，D/E 折叠
reviewing   → D 区前移到 Hero 下方，A 区保留，B/C 折叠
published   → E 区展开，D 区次要
```

**实际实现**：

- 所有状态渲染同样页面结构
- 仅 `authoringSurfaceLocked` 控制 Form 是否 disabled
- Hero 的 `detailInteractionMode` 仅改变按钮显隐和文字

**后果**：用户感受不到"现在在什么模式"，7 种状态的页面视觉上没有区别。

### 2.5 差距 4：首屏视觉焦点不突出

**设计意图**（按线框图）：

```
Hero（轻量：标题 + 状态 + 主 CTA）
    ↓
A 区（最重：当前入选的四件套）
    ↓
B/C 区（中段）
    ↓
D/E 区（折叠/后置）
```

**实际实现**：

- Hero 卡片承载大量文字（readiness 摘要 + 状态语言 + 操作提示 + 多个 Alert）
- 4 个 Alert 堆在 Hero 下面：`generation_error_msg` / `diagnosticsUnavailable` / `heroModeNotice` / `authoringLockMeta`
- A/B/C 三区在首屏可折叠范围内，但 B/C 是两列平铺，视觉权重与 A 区相当

**后果**：用户进页面不知道"该看哪里"，首屏信息过载。

---

## 三、关键问题

### 问题 1：B/C 区操作是否需要实时生效？

两种节奏，对应两种实现路径：

**路径 A：实时生效**
- B/C 区操作后 A 区立即刷新
- 不需要单独的"保存"按钮
- 页面任何变更自动同步到后端（debounce 保存）

**路径 B：批量保存**
- B/C 区 + A 区 + legacy editor 都是同一个 Form 的不同视图
- 最后点一次"保存创作定义"生效

**现状**：走的是路径 B，但区内操作给了用户"实时"的错觉。

### 问题 2：7 种状态是否需要不同布局？

**PRD 设计**：是的，不同状态页面重点不同。

**现状实现**：不是，所有状态渲染同样结构，仅按钮显隐。

### 问题 3：legacy editor 的去留？

- A：保留作为"高级编辑模式"
- B：废弃，在 P0-3~P0-6 把区内操作闭环后删除
- C：暂时保留，等整体重构

### 问题 4：首屏视觉优先级

用户是否感受到"页面太满，不知道看哪里"？

---

## 四、推荐解决方案

### 方案概述

```
Phase 1（立即）：首屏减负 + 状态感知增强
Phase 2（P0-3~P0-6）：B/C 区内操作闭环 + legacy editor 移除
Phase 3（可选）：状态驱动布局切换
```

### Phase 1：首屏减负

**改动 1.1：Hero 卡片精简**

现在的 Hero 卡片（`CreativeDetailHeroCard`）包含：
- modeMeta（状态标签）
- summaryTitle / summaryLead / summarySupportingText
- primaryAction + secondaryActions（多个按钮）
- heroModeNotice（Alert）

精简为：
```
┌─────────────────────────────────────────────────┐
│ [← 返回]  作品名称          [状态标签] [主CTA]  │
│ 缺失：封面 1 项 / 音频 1 项                      │
└─────────────────────────────────────────────────┘
```

readiness 详情、模式说明、操作建议折叠到 `?` 提示里或 Drawer。

**改动 1.2：Alert 收拢**

现在有 4 个 Alert 散落在 Hero 和 A 区之间：
- `generation_error_msg`
- `diagnosticsUnavailable`
- `heroModeNotice`
- `authoringLockMeta`

收拢为一个"状态通知中心"，通过 Tag + Tooltip 或 Drawer 展示。

**改动 1.3：A/B/C 区视觉权重调整**

- A 区（入选区）：卡片式，高视觉权重
- B/C 区（来源区）：折叠面板式，默认折叠，用户展开后操作

这样首屏只需展示 A 区 + Hero，B/C 折叠不抢占焦点。

### Phase 2：B/C 区内操作闭环

**改动 2.1：区内操作直接改入选区状态**

不再通过 Form 间接操作，改为：

```
B 区封面候选 → "设为当前封面" → API PATCH creative → A 区刷新
```

每个操作立即生效，不需要"保存"按钮。

**改动 2.2：移除 legacy editor**

把 legacy editor 的能力全部分布到 A/B/C 三区：
- 商品关联 → B 区
- 候选池管理 → B/C 区
- 入选媒体编辑 → A 区视频卡片

legacy editor 移除后，页面从 2,228 行压缩到约 1,200 行。

### Phase 3：状态驱动布局（可选）

根据 `detailInteractionMode` 动态调整页面结构：

```
authoring   → 默认展示 A/B/C（编辑模式）
reviewing   → A 区缩小为快照，D 区展开
published   → 仅展示 D/E（查看模式）
```

---

## 五、改动优先级

| 优先级 | 改动 | 影响 |
|--------|------|------|
| P0 | 首屏 Alert 收拢 | 立即改善混乱感 |
| P0 | B/C 区操作闭环 | 消除"点了没用"的问题 |
| P0 | legacy editor 移除 | 彻底解决双轨问题 |
| P1 | Hero 卡片精简 | 减少首屏认知负担 |
| P2 | 状态驱动布局 | 完全对齐 PRD |

---

## 六、结论

CreativeDetail 的设计文档（PRD + 线框图）已经非常成熟，问题在于实现进度落后于设计。

最核心的障碍是 **legacy editor 没有真正退出机制**——它名义上"后移为兼容编辑区"，实际上仍是主要操作入口。

建议以 **"区内操作闭环 + legacy editor 移除"** 作为下一阶段的核心目标，这是解决当前混乱感的关键。
