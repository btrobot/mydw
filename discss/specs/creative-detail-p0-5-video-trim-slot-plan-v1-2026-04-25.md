# 《CreativeDetail P0-5 视频裁切 / 槽位时长前移计划 v1》

日期：2026-04-25  
对应切片：Slice P0-5

---

## 1. 目标

把视频条目的 `trim_in` / `trim_out` / `slot_duration_seconds`，从兼容编辑区继续前移到“当前入选区”。

本次目标不是重做视频编辑器，而是把高频 timing 参数放回用户正在查看“当前真值”的地方。

---

## 2. 本次范围

### 纳入
- 当前入选区直接编辑 `slot_duration_seconds`
- 当前入选区直接编辑 `trim_in`
- 当前入选区直接编辑 `trim_out`
- 保存后 payload 正确写回 timing 字段
- 增加定向 E2E 覆盖

### 不纳入
- timing 合法性自动校验
- 裁切后时长推导提示
- 拖拽排序
- 实例级多次引用同素材的精细建模

---

## 3. 实现策略

继续沿用当前 P0 路线：

- 不新建第二套状态
- 继续以现有 `form.input_items` 为单一事实源
- 当前入选区控件直接修改对应视频条目的 timing 字段
- 保存 / 提交继续走既有管线

定位策略：

- 以“当前入选区已启用视频列表”的 index 定位对应视频
- 只更新该视频条目的 timing 字段
- 不改变其它媒体项

---

## 4. 预计改动文件

- `frontend/src/features/creative/view-models/useCreativeAuthoringModel.ts`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`

---

## 5. 验证计划

- `pnpm typecheck`
- 定向 Playwright：
  - 当前入选区 timing 输入可编辑
  - 保存后 `trim_in` / `trim_out` / `slot_duration_seconds` 正确写回
  - 与 P0-4 的排序 / 角色编辑能力不冲突

---

## 6. 风险提示

- 目前仍未做 trim 区间合法性保护
- 当前 index 定位方式对“同素材多次入选”的长远可维护性一般，但在 P0 可接受

