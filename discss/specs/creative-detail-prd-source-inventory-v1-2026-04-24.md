# 《CreativeDetail PRD 来源总表 v1》

> 日期：2026-04-24  
> 适用范围：CreativeDetail / PRD 收敛阶段  
> 目的：列出当前 CreativeDetail PRD 收敛所依赖的主要来源文档，作为后续覆盖矩阵与主 PRD 编写的输入清单  
> 状态：Draft

---

## 1. 使用说明

这份文档不是主 PRD，  
而是主 PRD 的**来源索引**。

用途：

1. 防止遗漏前面已经讨论过的关键结论
2. 给《CreativeDetail PRD 覆盖矩阵 v1》提供输入
3. 让后续主 PRD 收敛有可追踪来源

原则：

> **主 PRD 里的关键规则，原则上都应能在这里找到来源。**

---

## 2. 来源文档分组

当前来源文档分成 7 组：

1. 页面定位与业务流
2. 状态机与单用户简化
3. 版本 / 草稿 / 发布机制
4. 页面结构与三分区
5. 商品区与商品选择
6. 当前入选区与输入合同
7. 推进方法与收敛方法

---

## 3. 来源总表

| 编号 | 文档 | 主题 | 主结论摘要 | 是否主来源 |
|---|---|---|---|---|
| S01 | `creative-detail-business-flow-v1-2026-04-24.md` | 页面业务流 | CreativeDetail 是定义作品并推进到可生成状态的主页面 | 是 |
| S02 | `creative-detail-ab-current-definition-selected-spec-v1-2026-04-24.md` | A/B 结构 | A 当前定义 + B 当前入选曾是页面主骨架 | 否（已部分被三分区替代） |
| S03 | `creative-detail-state-machine-page-mode-spec-v1-2026-04-24.md` | 状态机 | 路由可统一，但页面模式必须随状态切换 | 是 |
| S04 | `creative-detail-single-user-review-simplification-analysis-v1-2026-04-24.md` | 单用户审核简化 | 审核应弱化为结果确认层，并允许撤回修改 | 是 |
| S05 | `creative-detail-single-user-simplified-state-machine-proposal-v1-2026-04-24.md` | 单用户简化状态机 | 建议用结果确认流替代审批流心智 | 是 |
| S06 | `creative-detail-version-concept-and-implementation-mechanism-v1-2026-04-24.md` | 版本概念 | CreativeVersion 是结果快照，不是草稿也不是发布包 | 是 |
| S07 | `creative-detail-new-version-timing-after-review-removal-v1-2026-04-24.md` | 新版本创建时机 | 只有提交生成 / 重新生成才创建新版本 | 是 |
| S08 | `creative-detail-single-user-version-publish-draft-boundary-spec-v1-2026-04-24.md` | 草稿/版本/发布边界 | 编辑改草稿，生成产版本，发布用版本 | 是 |
| S09 | `creative-detail-three-zone-structure-note-v1-2026-04-24.md` | 三分区收敛 | 页面可收敛成入选区、商品区、自由素材区 | 是 |
| S10 | `creative-detail-three-zone-page-spec-v1-2026-04-24.md` | 三分区页面规范 | 两个来源区，一个定稿区 | 是 |
| S11 | `creative-detail-product-selection-strategy-v1-2026-04-24.md` | 商品选择策略 | 商品选择不是普通下拉，而是选择流程 | 是 |
| S12 | `creative-detail-product-selection-lowfi-interaction-spec-v1-2026-04-24.md` | 商品选择低保真 | 入口化选择 + 摘要卡 + 展开查看 | 是 |
| S13 | `creative-detail-product-name-and-material-selection-refinement-v1-2026-04-24.md` | 商品名称/素材勾选 | 主题商品提供默认，作品定义保存最终真值 | 是 |
| S14 | `creative-detail-product-area-and-current-selection-linkage-spec-v1-2026-04-24.md` | 商品区与入选区联动 | A 区给默认与候选，B 区给最终采用 | 是 |
| S15 | `creative-detail-input-set-structure-analysis-v1-2026-04-24.md` | 输入合同结构 | 唯一位 + 集合位的输入合同模型成立 | 是 |
| S16 | `creative-detail-current-selection-field-spec-v1-2026-04-24.md` | 当前入选区字段 | B 区应承接 4 个唯一位 + 1 个视频集合 | 是 |
| S17 | `creative-detail-prd-coverage-traceability-method-v1-2026-04-24.md` | PRD 收敛方法 | 来源清单 + 覆盖矩阵 + 回查是主 PRD 的收敛方法 | 是 |
| S18 | `creative-detail-next-step-convergence-plan-v1-2026-04-24.md` | 推进建议 | 先收敛主 PRD，再做整页蓝图，再切实施片 | 是 |
| S19 | `creative-detail-interaction-skeleton-v1-2026-04-24.md` | 早期交互骨架 | 提供早期首屏骨架参考 | 否（参考） |
| S20 | `creative-detail-first-screen-lowfi-wireframe-copy-v1-2026-04-24.md` | 早期首屏线框 | 提供早期线框文案参考 | 否（参考） |
| S21 | `creative-detail-page-spec-v1-2026-04-24.md` | 页面规范模板样板 | 作为较早期规范样板参考 | 否（参考） |

---

## 4. 建议纳入主 PRD 的“必读来源”

如果只选最关键的一组进入主 PRD 收敛，建议至少纳入以下 12 份：

- S01 页面业务流
- S03 状态机与页面模式
- S04 单用户审核简化
- S05 单用户简化状态机
- S06 版本概念与实现机制
- S07 新版本创建时机
- S08 草稿 / 版本 / 发布边界
- S10 三分区页面规范
- S12 商品选择低保真交互
- S13 商品名称与素材勾选机制
- S15 输入合同结构
- S16 当前入选区字段规范

这 12 份已经足够构成主 PRD 的硬骨架。

---

## 5. 主 PRD 需要承接的核心结论清单

基于当前来源，总结出主 PRD 至少要承接以下关键结论：

### 5.1 页面定位

- CreativeDetail 是作品定义页，不是任务详情页
- 单用户模式优先

### 5.2 页面结构

- 页面收敛成三分区：
  - 入选区
  - 商品区
  - 自由素材区

### 5.3 输入合同

- 当前商品名称：唯一
- 当前封面：唯一
- 当前文案：唯一
- 当前音频：唯一
- 当前视频集合：多选集合

### 5.4 默认值与控制权

- 主题商品提供默认值
- 用户拥有最终决定权
- 用户手改后自动脱钩

### 5.5 版本机制

- 版本是结果快照
- 保存不建版本
- 提交生成 / 重新生成才建版本

### 5.6 单用户结果确认流

- 审核语义弱化为结果确认
- 允许回到编辑
- 结果确认不等于创建新版本

---

## 6. 不应直接升为主 PRD 规则的参考文档

以下文档建议作为参考，不直接当成主规则源：

- `creative-detail-ab-current-definition-selected-spec-v1-2026-04-24.md`
- `creative-detail-interaction-skeleton-v1-2026-04-24.md`
- `creative-detail-first-screen-lowfi-wireframe-copy-v1-2026-04-24.md`
- `creative-detail-page-spec-v1-2026-04-24.md`

原因：

- 它们是早期讨论或阶段性骨架
- 其中部分结论已被更后续的三分区和输入合同模型替代

---

## 7. 使用建议

后续编写主 PRD 时，建议流程是：

1. 先以本表确立来源范围
2. 再做《CreativeDetail PRD 覆盖矩阵 v1》
3. 然后再写主 PRD
4. 最后用覆盖矩阵反查是否遗漏

---

## 8. 最终结论

这份《来源总表》的意义不是增加文档数量，  
而是把当前已经分散的 CreativeDetail 讨论收口成：

> **一份可追踪的 PRD 输入源列表**

只有先有这份来源总表，后续主 PRD 才能真正做到：

> **不是“感觉都写进去了”，而是“可以证明都写进去了”。**

