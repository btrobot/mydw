# 《CreativeDetail P0-2 前端页面壳 / 首屏骨架重构计划 v1》
> 日期：2026-04-25  
> Slice：P0-2  
> 范围：`frontend/src/features/creative/pages/CreativeDetail.tsx` 及其首屏相关组件  
> 状态：执行中

---

## 1. 本 Slice 要解决什么

本 Slice 不继续堆叠旧的“大表单页”，而是把 `CreativeDetail` 重构为：

1. **新投影驱动的页面壳**
2. **首屏以当前入选区为主角**
3. **商品区 / 自由素材区成为来源区**
4. **旧编辑表单降级为后续编辑区**

目标不是一次性做完所有细交互，而是先把页面主骨架和心智顺序拉正。

---

## 2. 本 Slice 的输入依据

- `discss/specs/creative-detail-converged-prd-v1-2026-04-24.md`
- `discss/specs/creative-detail-whole-page-lowfi-wireframe-copy-v1-2026-04-24.md`
- `discss/specs/creative-detail-p0-acceptance-test-draft-v1-2026-04-24.md`
- `discss/specs/creative-detail-p0-p1-p2-implementation-slicing-plan-v1-2026-04-24.md`
- 已完成后端投影：`current_selection` / `product_zone` / `free_material_zone` / `readiness` / `page_mode`

---

## 3. 重构原则

1. **不新建路由**：仍使用 `/creative/:id`
2. **不推翻现有编辑能力**：保存、提交合成、候选池编辑等继续保留
3. **先改壳，再改深交互**：P0-2 只做页面结构重排和投影首屏
4. **兼容旧返回**：若接口投影字段缺失，前端做有限 fallback，避免现有测试夹具全部失效
5. **小步可回退**：优先新增首屏组件/投影 helper，避免一次性重写整页业务

---

## 4. 实施拆分

### 4.1 页面壳

重建 `CreativeDetail.tsx` 顶层结构为：

1. 页面头部（标题 / 状态 / readiness / CTA）
2. A 当前入选区
3. B 商品区
4. C 自由素材区
5. 兼容编辑区（旧表单）
6. 结果 / 审核 / 版本区
7. 高级诊断抽屉 / AIClip / Review Drawer

### 4.2 投影层

新增前端投影 helper，统一产出页面消费数据：

- `pageMode`
- `readiness`
- `currentSelection`
- `productZone`
- `freeMaterialZone`

若后端字段存在，优先直接使用；若缺失，则从 legacy 字段做最小推导。

### 4.3 首屏组件

首屏至少拆出以下可读组件：

- 页面头部 / readiness 摘要
- 当前入选卡组
- 商品区来源卡组
- 自由素材区来源卡组

### 4.4 兼容编辑区

旧的 `Form.List(product_links / candidate_items / input_items)` 暂不删除：

- 位置后移
- 标题改为“定义编辑区 / 兼容编辑区”
- 让它不再抢占首屏

---

## 5. 测试与验证

本 Slice 至少验证：

1. `CreativeDetail` 首屏骨架成功渲染
2. 现有保存作品定义流程不回归
3. 候选池采用逻辑不回归
4. 输入媒体编辑测试不回归
5. 前端 `typecheck` 通过

计划补充：

- 更新/增强 `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- 必要时为新首屏增加 data-testid

---

## 6. 非目标

本 Slice 不做：

- 商品选择器完整重做
- 自由素材区完整操作面板
- 结果确认页模式锁定
- 版本创建 / 发布完整交互闭环
- 视觉精修

这些留给后续 P0-3 / P1。

---

## 7. 完成标准

满足以下条件才算本 Slice 完成：

1. `CreativeDetail` 顶层结构已按新投影重排
2. 首屏主角从“大表单”切换为“当前入选区”
3. 商品区 / 自由素材区已进入页面主体
4. 现有主要编辑与提交能力仍可用
5. 类型检查与相关测试通过
6. 收尾文档已落盘

