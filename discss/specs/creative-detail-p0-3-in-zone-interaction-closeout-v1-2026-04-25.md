# CreativeDetail P0-3 区内交互收口说明 v1

日期：2026-04-25  
对应切片：Slice P0-3  
范围：商品区 / 自由素材区 / 当前入选区

---

## 1. 本次完成内容

本次已把以下操作，从“兼容编辑区”继续前移到真正的区内交互：

### A. 当前入选区
- 商品名称支持区内快速编辑
- 商品名称支持“恢复跟随主题商品”
- 文案支持区内快速编辑
- 文案支持直接清空
- 当前封面支持直接清空
- 当前音频支持直接清空
- 当前入选视频支持逐条移出

### B. 商品区
- 已关联商品支持直接设为主题商品
- 商品默认名称支持直接带入当前商品名
- 商品封面候选支持直接设为当前封面
- 商品视频候选支持直接加入 / 移出当前入选
- 商品文案候选支持直接设为当前文案

### C. 自由素材区
- 自由封面候选支持直接设为当前封面
- 自由视频候选支持直接加入 / 移出当前入选
- 自由音频候选支持直接设为当前音频
- 自由文案候选支持直接设为当前文案

---

## 2. 仍然保留的兼容编辑区职责

P0-3 之后，兼容编辑区仍然保留，但职责收窄为：

- 补充维护关联商品结构
- 补充维护候选池结构
- 补充维护输入素材底层表单
- 承担尚未前移到首屏区内的低频配置

也就是说：

- 高频定义动作：优先在 A / B / C 区完成
- 底层结构维护：仍可回退到兼容编辑区完成

---

## 3. 关键实现策略

本次没有新建第二套状态，而是继续以现有 form 作为单一事实源：

- 区内交互直接改写 `form`
- 保存仍走现有 `handleSaveInput`
- 提交生成仍走现有 `handleSubmitComposition`
- Projection 首屏继续通过 watched form state 即时回显

这样可以保证：

- 区内交互和兼容编辑区不会各写一套状态
- 改动小、可回退
- 后续 P1 可以继续删减兼容编辑区，而不是推倒重来

---

## 4. 本次涉及文件

- `frontend/src/features/creative/view-models/useCreativeAuthoringModel.ts`
- `frontend/src/features/creative/components/detail/CreativeDetailProjection.tsx`
- `frontend/src/features/creative/components/detail/projection.ts`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`

---

## 5. 验证结果

已完成验证：

- `pnpm typecheck`
- `pnpm test:e2e -- --project=chromium e2e/creative-workbench/creative-workbench.spec.ts -g "renders projection-driven creative detail shell before legacy editor|filters full-carrier readback to video and audio operations only|persists candidate pool adoption separately from selected media state|updates current selection from product and free-material zone actions before save|supports in-zone editing and clearing inside the current selection section"`

验证重点覆盖：

- 首屏 projection 壳仍可正常渲染
- 候选池采用逻辑未回退
- 商品区 / 自由素材区可直接推动当前入选结果变化
- 当前入选区可直接编辑 / 清空 / 移除
- 保存 payload 与区内交互结果一致

---

## 6. 当前仍未解决的问题

P0-3 只是把“能操作”前移，还没有做完这些更高阶问题：

- 商品区仍然缺少更强的商品选择器（当前仍主要依赖兼容编辑区维护关联商品）
- 当前入选区还是“可操作版信息卡”，还不是完整的作品定义工作台
- 视频顺序编排、拖拽排序、角色编辑仍主要依赖兼容编辑区
- 自由素材区还没有做更强的筛选、检索、批量勾选
- 商品素材与自由素材的“来源解释”还可以再强化

---

## 7. 推荐下一步

建议直接进入 P0-4 / P1 收口：

1. 把视频排序与角色编辑继续前移到当前入选区
2. 把商品关联补强成“可视化商品选择器”
3. 继续压缩兼容编辑区，只保留低频结构维护
4. 基于当前已前移的交互，再做一轮 UI 收敛与首屏信息密度调整

