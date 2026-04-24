# CreativeDetail P0-4 视频排序 / 角色编辑收口说明 v1

日期：2026-04-25  
对应切片：Slice P0-4

---

## 1. 本次完成内容

本次已把“当前入选区”的视频集合，继续从只读信息卡提升为可直接操作：

- 支持区内直接上移视频
- 支持区内直接下移视频
- 支持区内直接编辑每条视频的用途 / 角色
- 保存后把排序结果写回 `input_items.sequence`
- 保存后把角色文案写回 `input_items.role`

---

## 2. 关键实现策略

本次仍然没有新建第二套状态，而是继续复用现有 `form`：

- 当前入选区的视频排序与角色编辑，直接改写 `form.input_items`
- 保存继续走现有 `handleSaveInput`
- 提交继续走现有 `handleSubmitComposition`

排序实现采用了“只重排视频槽位”的策略：

- 先找出 `input_items` 中所有视频所在位置
- 只交换视频槽位里的内容
- 音频等非视频项保持原有槽位不动

这样可以保证：

- 当前入选区的视频顺序可调整
- 音频不会因为视频排序被意外挪位
- 与兼容编辑区仍共享同一份事实源

---

## 3. 本次涉及文件

- `frontend/src/features/creative/view-models/useCreativeAuthoringModel.ts`
- `frontend/src/features/creative/components/detail/CreativeDetailProjection.tsx`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- `discss/specs/creative-detail-p0-4-video-order-role-plan-v1-2026-04-25.md`

---

## 4. 新增区内交互能力

### 当前入选区 / 视频集合
- `上移`
- `下移`
- `用途 / 角色` 输入框
- 既有 `移出入选` 保持可用

### 结果
- 当前入选区已经可以承接视频集合的核心高频操作：
  - 选入
  - 移除
  - 排序
  - 角色编辑

兼容编辑区中关于视频列表的职责，进一步退化为：

- 底层结构兜底
- 低频配置
- 更细粒度参数维护

---

## 5. 验证结果

已完成验证：

- `pnpm typecheck`
- `pnpm test:e2e -- --project=chromium e2e/creative-workbench/creative-workbench.spec.ts -g "updates current selection from product and free-material zone actions before save|supports in-zone editing and clearing inside the current selection section|supports in-zone video ordering and role editing inside current selection"`
- `pnpm test:e2e -- --project=chromium e2e/creative-workbench/creative-workbench.spec.ts -g "renders projection-driven creative detail shell before legacy editor|persists candidate pool adoption separately from selected media state|updates current selection from product and free-material zone actions before save|supports in-zone editing and clearing inside the current selection section|supports in-zone video ordering and role editing inside current selection|filters full-carrier readback to video and audio operations only"`

验证覆盖了：

- projection 首屏未回退
- 当前入选区视频排序生效
- 当前入选区视频角色编辑生效
- 排序后保存 payload 正确
- 既有候选采用与兼容编辑能力未被破坏

---

## 6. 当前仍未解决的问题

P0-4 完成后，视频集合的高频操作已基本前移，但仍有这些未完成项：

- 还没有拖拽排序
- 还没有把裁切参数前移到当前入选区
- 还没有把 slot_duration 前移
- 还没有解决“同素材多次入选”的实例级精确操作
- 兼容编辑区仍然偏重，尚未进入真正的 P1 收口删减阶段

---

## 7. 推荐下一步

建议下一步进入以下两个方向之一：

### 方向 A：继续 P0 收口
- 把视频裁切 / slot_duration 继续前移
- 让当前入选区更完整地承担视频编排职责

### 方向 B：进入 P1 页面收敛
- 基于当前已前移的区内操作
- 重新压缩兼容编辑区
- 做一轮首屏密度、操作层级、信息噪音收敛

如果继续按“先把高频交互全部前移”的路线推进，推荐先做 **视频裁切参数前移**。

