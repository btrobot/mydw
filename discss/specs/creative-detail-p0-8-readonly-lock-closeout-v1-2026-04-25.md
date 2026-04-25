# 《CreativeDetail P0-8 锁定态 / 只读态收口完成说明 v1》

日期：2026-04-25  
对应切片：Slice P0-8

---

## 1. 本次完成内容

本 Slice 把 CreativeDetail 从“只有首屏文案像结果页”推进到“锁定态下交互也像结果页”：

- reviewing / submitting / publishing / published_followup 下，A/B/C 不再暴露编辑动作
- 兼容编辑区降级为只读快照，不再允许保存或提交
- authoring 相关能力保持不回退
- E2E 补齐 reviewing 只读断言，并把仍需编辑的旧用例切回 authoring 状态

---

## 2. 具体收口

### 2.1 A 当前入选区

在锁定态下移除：

- 商品名区内编辑
- 文案区内编辑
- 清空封面 / 文案 / 音频
- 视频排序 / 移出 / 角色编辑 / timing 编辑 / 拖拽

同时新增只读提示：

- “当前入选区为只读结果快照”

### 2.2 B 商品区 / C 自由素材区

在锁定态下移除：

- 编辑商品区 / 管理自由素材
- 设为当前封面 / 文案
- 加入入选 / 移出入选
- 用作当前商品名 / 设为主题商品

保留：

- 候选内容
- 当前值标记
- 已入选标记
- 来源追溯信息

即：锁定态下仍可看“这版作品是怎么来的”，但不能在这里继续改定义。

### 2.3 兼容编辑区

兼容编辑区改为：

- 标题：`定义快照区（兼容只读）`
- 显示只读 tag 与 notice
- 表单整体 disabled
- 隐藏保存创作定义
- 隐藏提交合成
- 隐藏增删改排序按钮

页面仍保留快照读回，方便排查和追溯，但不再把 reviewing / publishing / published 页面伪装成编辑器。

---

## 3. 涉及文件

- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/src/features/creative/components/detail/CreativeDetailProjection.tsx`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- `discss/specs/creative-detail-p0-8-readonly-lock-plan-v1-2026-04-25.md`
- `discss/specs/creative-detail-p0-8-readonly-lock-closeout-v1-2026-04-25.md`

---

## 4. 验证结果

已执行：

- `pnpm typecheck`
- `pnpm test:e2e -- e2e/creative-workbench/creative-workbench.spec.ts --project=chromium --grep "saves creative brief and input_items without legacy list write fields|renders projection-driven creative detail shell before legacy editor|locks current selection, source zones, and compatibility editor in reviewing mode|switches hero summary and primary CTA back to authoring semantics when detail is editable|updates current selection from product and free-material zone actions before save|supports in-zone editing and clearing inside the current selection section|supports in-zone video ordering and role editing inside current selection|supports in-zone video trim and slot duration editing inside current selection|blocks save when current selection video timing is invalid|supports drag sorting inside current selection videos|filters full-carrier readback to video and audio operations only|persists candidate pool adoption separately from selected media state"`

结果：

- typecheck 通过
- 12 条定向 E2E 全部通过
- reviewing 模式下只读语义成立
- authoring 模式下 P0-3 ~ P0-7 的区内交互能力未回退

---

## 5. 本次完成后的页面语义

到 P0-8 为止，CreativeDetail 已形成更清晰的模式边界：

- **authoring / reworking / failed_recovery**：这是编辑页
- **submitting / reviewing / publishing / published_followup**：这是结果 / 发布跟进页

也就是说，页面不再只靠 Hero 提醒用户“现在不要编辑”，而是实际把编辑动作收掉。

---

## 6. 剩余风险 / 后续建议

1. 当前锁定规则仍是前端模式治理，后端尚未做更强约束
2. `REJECTED` 目前仍跟随 reviewing 语义，需要后续结合业务再决定是否独立成可返工模式
3. 新版本创建入口、发布后继续迭代入口，还需要后续切片补齐

最自然的下一步是：

- **P0-9：P0 验收回归总收口**
- 或进入 **P1：版本创建 / 发布后继续迭代入口**
