# 《CreativeDetail P0-2 前端页面壳 / 首屏骨架重构收尾说明 v1》
> 日期：2026-04-25  
> Slice：P0-2  
> 状态：已完成并通过本 Slice 验证

---

## 1. 本 Slice 实际完成内容

本次完成了 `CreativeDetail` 的页面壳重排，但没有推翻旧编辑能力：

1. **首屏改为投影驱动**
   - 新增基于 `current_selection / product_zone / free_material_zone / readiness / page_mode` 的首屏结构
   - 首屏顺序调整为：
     - 页面头部 / readiness
     - A 当前入选区
     - B 商品区
     - C 自由素材区

2. **旧大表单降级为兼容编辑区**
   - 原 `product_links / candidate_items / input_items` 编辑能力保留
   - 位置后移，不再抢占首屏

3. **增加前端 fallback 投影**
   - 当返回里缺少新投影字段时，前端仍能从 legacy 字段推导基础首屏数据
   - 这样可以兼容现有测试夹具与渐进式后端联调

4. **增加首屏回归测试**
   - 为 `creative-workbench.spec.ts` 补充新首屏结构断言
   - 同时保留并验证保存 / 候选池 / 当前入选媒体三类旧能力未回归

---

## 2. 本 Slice 修改文件

### 新增

- `frontend/src/features/creative/components/detail/projection.ts`
- `frontend/src/features/creative/components/detail/CreativeDetailProjection.tsx`
- `discss/specs/creative-detail-p0-2-frontend-shell-plan-v1-2026-04-25.md`
- `discss/specs/creative-detail-p0-2-frontend-shell-closeout-v1-2026-04-25.md`

### 修改

- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`

---

## 3. 关键实现决策

### 3.1 不新建页面，不新建路由

仍然保留：

- `/creative/:id`
- `CreativeDetail.tsx`

本 Slice 只重构页面壳和首屏骨架，不做路线切换。

### 3.2 新投影优先，legacy 回退

优先吃后端新投影；如果测试数据或部分环境未补齐投影字段，则由前端做最小 fallback。

这样做的好处是：

- 可以立刻把首屏结构切正
- 不会因为联调节奏卡死前端改造
- 可以渐进替换现有 mock / fixture

### 3.3 保守保留旧编辑区

P0-2 不是细交互重做 Slice，因此没有删掉老编辑表单，而是把它后移为：

> **定义编辑区（兼容编辑）**

这样既能兑现“首屏心智重排”，又能保证已有操作仍然可用。

---

## 4. 验证结果

### 4.1 类型检查

已执行：

```bash
pnpm typecheck
```

结果：通过

### 4.2 定向 E2E

已执行：

```bash
pnpm playwright test --config e2e/playwright.config.ts e2e/creative-workbench/creative-workbench.spec.ts -g "renders projection-driven creative detail shell|saves creative brief and input_items without legacy list write fields|filters full-carrier readback to video and audio operations only|persists candidate pool adoption separately from selected media state"
```

结果：通过（8 passed）

覆盖了：

- 新首屏页面壳渲染
- 保存作品定义
- full-carrier 读回只暴露 video/audio 编辑
- 候选池采用与当前入选状态分离

---

## 5. 当前收益

本 Slice 完成后，`CreativeDetail` 不再是“一进来就是大表单”：

- 用户先看到当前入选结果
- 再看商品区和自由素材区这两个来源区
- 再进入兼容编辑区继续细调

这使页面更接近此前收敛 PRD 的主心智。

---

## 6. 仍然留下的后续工作

P0-2 之后，建议继续：

1. **P0-3：把兼容编辑区继续拆解**
   - 商品区编辑
   - 自由素材区编辑
   - 当前入选区编辑

2. **把“滚动到编辑区”替换成真正区内操作**
   - 例如：替换封面、管理视频、选择主题商品

3. **把页面模式锁定做完整**
   - `definition`
   - `result_pending_confirm`
   - `published_followup`

4. **减少 legacy 表单直出密度**
   - 当前仍属保守过渡态

---

## 7. 风险与说明

### 已控制风险

- 没有删除既有保存/提交逻辑
- 没有新增依赖
- 没有新建并行页面

### 尚存风险

- 首屏虽然已经投影化，但深层操作仍通过兼容编辑区承接
- 当前前端 fallback 是过渡手段，后续仍应推动 fixture / backend 全面转向新投影

---

## 8. 对下一 Slice 的建议

下一步最合适的是：

> **Slice P0-3：继续把商品区 / 自由素材区 / 当前入选区的交互从兼容编辑区中抽出来，形成真正的区内操作闭环。**

