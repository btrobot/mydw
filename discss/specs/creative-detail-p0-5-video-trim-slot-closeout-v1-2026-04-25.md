# CreativeDetail P0-5 视频裁切 / 槽位时长前移收口说明 v1

日期：2026-04-25  
对应切片：Slice P0-5

---

## 1. 本次完成内容

本次已把“当前入选区”的视频集合继续前移：

- 支持区内直接维护 `slot_duration_seconds`
- 支持区内直接维护 `trim_in`
- 支持区内直接维护 `trim_out`

至此，当前入选区的视频集合已经可以直接完成：

- 选入
- 移除
- 排序
- 角色编辑
- 裁切参数维护
- 槽位时长维护

---

## 2. 实现策略

本次仍然复用现有 `form`，没有新建第二套状态：

- 当前入选区输入控件直接改写 `form.input_items`
- 保存继续走现有 `handleSaveInput`
- 提交继续走现有 `handleSubmitComposition`

字段更新策略：

- 仍然按“当前入选视频列表 index”定位目标视频
- 直接更新该视频对应 input item 的：
  - `slot_duration_seconds`
  - `trim_in`
  - `trim_out`

这样可以保证：

- 当前入选区与兼容编辑区共用一份事实源
- 前移的是高频操作，不是复制一套编辑器
- 后续压缩兼容编辑区时不会出现双写状态问题

---

## 3. 本次涉及文件

- `frontend/src/features/creative/view-models/useCreativeAuthoringModel.ts`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- `discss/specs/creative-detail-p0-5-video-trim-slot-plan-v1-2026-04-25.md`（本次计划文档）
- `discss/specs/creative-detail-p0-5-video-trim-slot-closeout-v1-2026-04-25.md`

---

## 4. 验证结果

已完成验证：

- `pnpm typecheck`
- `pnpm test:e2e -- --project=chromium e2e/creative-workbench/creative-workbench.spec.ts -g "supports in-zone video ordering and role editing inside current selection|supports in-zone video trim and slot duration editing inside current selection"`
- `pnpm test:e2e -- --project=chromium e2e/creative-workbench/creative-workbench.spec.ts -g "renders projection-driven creative detail shell before legacy editor|persists candidate pool adoption separately from selected media state|updates current selection from product and free-material zone actions before save|supports in-zone editing and clearing inside the current selection section|supports in-zone video ordering and role editing inside current selection|supports in-zone video trim and slot duration editing inside current selection|filters full-carrier readback to video and audio operations only"`

验证覆盖：

- 当前入选区视频角色编辑未回退
- 当前入选区视频排序未回退
- 当前入选区视频裁切 / 槽位时长可直接编辑
- 保存后 payload 中 timing 字段正确写回
- 既有 projection 壳与兼容编辑区回退能力未被破坏

---

## 5. 当前仍未解决的问题

P0-5 之后，视频高频编排已进一步前移，但仍有这些问题未解决：

- 还没有拖拽排序
- `trim_in` / `trim_out` 还没有做合法性联动校验
- 还没有做“裁切后时长提示 / 超出素材时长提示”
- 对“同素材多次入选”的实例级控制仍不够细
- 兼容编辑区尚未进入真正的 P1 删减

---

## 6. 推荐下一步

建议下一步二选一：

### 方向 A：继续把视频编排做完整
- 做拖拽排序
- 做 timing 合法性校验
- 做裁切结果提示

### 方向 B：进入 P1 页面收敛
- 基于当前已经前移的高频交互
- 开始压缩兼容编辑区
- 收敛首屏结构、说明文案、按钮层级

如果继续按“先把高频视频编排补齐”的路线推进，推荐下一步是：

**P0-6：补 timing 合法性校验 + 拖拽排序。**

