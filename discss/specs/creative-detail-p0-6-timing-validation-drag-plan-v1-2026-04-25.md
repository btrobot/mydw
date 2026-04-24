# 《CreativeDetail P0-6 timing 合法性校验 + 拖拽排序计划 v1》

日期：2026-04-25  
对应切片：Slice P0-6

---

## 1. 目标

在当前入选区继续补齐两类关键能力：

- timing 合法性校验
- 视频拖拽排序

目标不是做完整视频工作台，而是把当前 P0 已前移的视频高频操作补得更稳、更顺手。

---

## 2. 本次范围

### 纳入
- 对当前入选区视频的 `trim_in` / `trim_out` / `slot_duration_seconds` 做基础合法性校验
- 保存 / 提交前阻止明显非法 timing 写回
- 在当前入选区显式提示对应视频的 timing 问题
- 支持当前入选区视频拖拽排序
- 增加定向 E2E 覆盖

### 不纳入
- 基于真实素材时长的强约束校验
- 裁切后结果预览
- 时间轴式编辑器
- 多实例同素材视频的精细 identity 升级

---

## 3. 校验策略

先做 P0 可落地的“明显非法”校验：

- `slot_duration_seconds` 如果填写，必须大于 0
- `trim_in` 如果填写，必须大于等于 0
- `trim_out` 如果填写，必须大于等于 0
- 如果同时填写 `trim_in` 和 `trim_out`，则 `trim_out` 必须大于 `trim_in`

保存 / 提交策略：

- 如果存在 timing 非法项，阻止保存 / 提交
- 首先在当前入选区逐条展示 warning
- 同时通过 message 给出阻断提示

---

## 4. 拖拽策略

在不新增依赖的前提下，采用原生 HTML5 drag-and-drop：

- 当前入选区每条视频可作为 draggable item
- 目标视频条目作为 drop target
- drop 后调用既有 shared-form 排序逻辑

保留已有“上移 / 下移”按钮，拖拽作为增强而不是替换。

---

## 5. 预计改动文件

- `frontend/src/features/creative/creativeAuthoring.ts`
- `frontend/src/features/creative/view-models/useCreativeAuthoringModel.ts`
- `frontend/src/features/creative/components/detail/CreativeDetailProjection.tsx`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`

---

## 6. 验证计划

- `pnpm typecheck`
- 定向 Playwright：
  - 非法 timing 会出现区内提示
  - 非法 timing 会阻止保存
  - 拖拽排序后当前入选区顺序变化
  - 拖拽排序后 payload 顺序正确

---

## 7. 风险提示

- HTML5 drag-and-drop 在 E2E 中需要用稳定的 testid，避免选择器漂移
- 当前仍然按“当前入选视频 index”建模，后续若要支持同素材多次入选的实例级精确控制，需要再升级 identity 方案

