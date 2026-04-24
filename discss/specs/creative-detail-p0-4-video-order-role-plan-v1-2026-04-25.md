# 《CreativeDetail P0-4 视频排序 / 角色编辑前移计划 v1》

日期：2026-04-25  
对应切片：Slice P0-4

---

## 1. 目标

把“当前入选区”里的视频集合，从只读 + 移除，继续提升为可直接操作：

- 在当前入选区直接调整视频顺序
- 在当前入选区直接编辑每条视频的用途 / 角色

本次仍然不移除兼容编辑区，而是把高频动作前移。

---

## 2. 本次范围

### 纳入
- 视频上移
- 视频下移
- 视频角色文案直接编辑
- 保存后 payload 中的 `input_items` 顺序与 `role` 正确写回
- 增加定向 E2E 验证

### 不纳入
- 拖拽排序
- 视频裁切参数前移
- slot_duration 前移
- 批量编辑
- 多实例同素材视频的精细建模修复

---

## 3. 实现策略

继续沿用 P0 约束：

- 不新建第二套状态
- 继续以现有 `form` 为单一事实源
- 区内交互直接修改 `form.input_items`
- 保存 / 提交继续走现有 `handleSaveInput` / `handleSubmitComposition`

排序策略：

- 只重排视频子集
- 音频等非视频项保持原有槽位不动
- 通过“替换视频槽位内容”的方式，避免把非视频项顺序打乱

角色编辑策略：

- 直接修改对应视频项的 `role`
- Projection 当前入选区继续把 `role` 映射为视频说明文案

---

## 4. 预计改动文件

- `frontend/src/features/creative/view-models/useCreativeAuthoringModel.ts`
- `frontend/src/features/creative/components/detail/CreativeDetailProjection.tsx`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`

---

## 5. 验证计划

- `pnpm typecheck`
- 定向 Playwright：
  - 当前入选区可上移 / 下移视频
  - 当前入选区可编辑视频角色
  - 保存后 `input_items.sequence` 顺序符合预期
  - 保存后 `input_items.role` 符合预期

---

## 6. 风险提示

- 当前模型对“同一个视频素材多次入选”的实例级操作还不够精细，本次先按 P0 范围处理
- 若后续进入 P1，可再把“视频实例 identity”从 assetId 提升到 instance 维度

