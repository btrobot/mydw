# 《CreativeDetail P0-6 timing 合法性校验 + 拖拽排序完成说明 v1》

日期：2026-04-25  
对应切片：Slice P0-6

---

## 1. 本次完成内容

本次切片把当前入选区的视频操作补齐到一个更可用的 P0 水位：

- 增加当前入选视频的基础 timing 合法性校验
- 在区内显式展示 timing warning
- 保存 / 提交前阻止非法 timing 写回
- 增加当前入选视频原生拖拽排序
- 补齐对应 E2E 覆盖

---

## 2. 具体落地点

### 2.1 timing 校验

新增 `getCreativeSelectedVideoTimingIssues(...)`，当前规则为：

- `slot_duration_seconds` 如填写，必须大于 0
- `trim_in` 如填写，必须大于等于 0
- `trim_out` 如填写，必须大于等于 0
- 若同时填写 `trim_in` 与 `trim_out`，则 `trim_out` 必须大于 `trim_in`

### 2.2 保存阻断

在 `useCreativeAuthoringModel` 的保存链路中增加 timing 校验：

- save / submit 前先跑 timing 校验
- 如存在非法项，直接 `messageApi.error(...)`
- 阻止 PATCH / submit-composition 发出

### 2.3 当前入选区 warning 显示

在 `CreativeDetail.tsx` 中基于当前 watched video items 计算 warning map，并在 `CreativeCurrentSelectionSection` 里逐视频渲染 warning。

这样用户在点保存前，就能先看到哪一条视频的 timing 不合法。

### 2.4 拖拽排序

在 `CreativeCurrentSelectionSection` 中为视频卡片增加：

- `draggable`
- `dragstart / dragover / drop`
- 稳定 testid
- 拖拽提示标签“可拖拽排序”

排序仍然落回 shared form 的 `input_items`，与已有上移 / 下移保持同一份状态源。

### 2.5 排序写回模型

新增 `handleReorderSelectedVideo(fromIndex, toIndex)`：

- 以“当前入选视频 index”作为排序入口
- 定位到 `input_items` 中真实的视频槽位
- 只交换视频槽位
- 非视频项（例如音频）相对位置保持不变

---

## 3. 本次改动文件

- `frontend/src/features/creative/creativeAuthoring.ts`
- `frontend/src/features/creative/view-models/useCreativeAuthoringModel.ts`
- `frontend/src/features/creative/components/detail/CreativeDetailProjection.tsx`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- `discss/specs/creative-detail-p0-6-timing-validation-drag-plan-v1-2026-04-25.md`
- `discss/specs/creative-detail-p0-6-timing-validation-drag-closeout-v1-2026-04-25.md`

---

## 4. 验证结果

已执行：

- `pnpm typecheck`
- `pnpm test:e2e -- e2e/creative-workbench/creative-workbench.spec.ts --project=chromium --grep "renders projection-driven creative detail shell before legacy editor|updates current selection from product and free-material zone actions before save|supports in-zone editing and clearing inside the current selection section|supports in-zone video ordering and role editing inside current selection|supports in-zone video trim and slot duration editing inside current selection|blocks save when current selection video timing is invalid|supports drag sorting inside current selection videos"`
- `pnpm test:e2e -- e2e/creative-workbench/creative-workbench.spec.ts --project=chromium --grep "blocks save when current selection video timing is invalid|supports drag sorting inside current selection videos"`

验证覆盖到：

- 页面壳仍正常渲染
- 商品区 / 自由素材区 -> 当前入选区联动未回退
- 区内编辑 / 清空仍正常
- 视频上移下移 / 角色编辑仍正常
- 视频 trim / slot_duration 编辑仍正常
- 非法 timing 会区内预警并阻止保存
- 拖拽排序会更新当前区展示顺序，并正确写回 payload

---

## 5. 仍保留的边界

本次仍是 P0，不解决以下问题：

- 未接入素材真实时长，因此还不能判断 `trim_out` 是否超过素材总时长
- 未提供时间轴式可视化裁切体验
- 当前视频 identity 仍按“入选 index + material_id”工作；后续若支持同素材多实例更复杂编辑，建议升级为更稳定的实例级标识

---

## 6. 对下一切片的建议

P0-6 完成后，当前入选区的视频高频操作已基本成型。下一步可以继续往两个方向推进：

1. **P0 收口**
   - 汇总当前入选区 / 商品区 / 自由素材区的交互，回写验收标准
   - 做一轮低风险 UI 整理与命名清理

2. **P1 增强**
   - timing 与真实素材时长联动
   - 更明确的视频顺序语义与镜头角色语义
   - 更强的可视化裁切与预览能力

