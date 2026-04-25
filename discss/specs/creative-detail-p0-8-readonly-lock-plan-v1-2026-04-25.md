# 《CreativeDetail P0-8 锁定态 / 只读态收口计划 v1》

日期：2026-04-25  
对应切片：Slice P0-8

---

## 1. 本 Slice 目标

把 CreativeDetail 在非编辑阶段真正收口为“结果/发布驱动页面”，而不是仅仅改 Hero 文案：

- reviewing / submitting / publishing / published_followup 下，A/B/C 不再提供定义写入口
- 兼容编辑区降级为只读快照，不再允许继续保存或提交
- authoring / reworking / failed_recovery 继续保持可编辑

---

## 2. 锁定范围

本次按前端交互层收口，不扩后端模型：

### 锁定模式

- submitting
- reviewing
- publishing
- published_followup

### 保持可编辑模式

- authoring
- reworking
- failed_recovery

---

## 3. 具体改动

### 3.1 A 当前入选区

- 隐藏商品名区内编辑
- 隐藏文案区内编辑
- 隐藏清空封面 / 文案 / 音频
- 隐藏视频排序、移除、角色编辑、timing 编辑、拖拽
- 增加“当前入选区为只读结果快照”提示

### 3.2 B 商品区 / C 自由素材区

- 隐藏“编辑商品区 / 管理自由素材”
- 隐藏所有“设为当前 / 加入入选 / 用作当前商品名 / 设为主题商品”等动作
- 保留候选内容与已采用标记，作为来源追溯视图
- 增加只读提示

### 3.3 兼容编辑区

- 标题改为“定义快照区（兼容只读）”
- 隐藏保存 / 提交按钮
- 表单整体 disabled
- 隐藏增删改排序按钮，仅保留快照读回
- 增加只读提示 tag / notice

### 3.4 测试

- 新增 reviewing 模式只读断言
- 把仍需编辑能力的旧 E2E 用例切回 authoring 状态执行

---

## 4. 验证计划

- `pnpm typecheck`
- 定向执行 creative-workbench E2E：
  - reviewing 只读断言
  - authoring 仍可编辑
  - P0-3 ~ P0-7 已有区内交互回归

---

## 5. 边界

本次不做：

- 新版本创建机制
- 审核流领域规则调整
- 发布后再编辑的后端约束
- 更深的数据模型改造

本次只把“页面在锁定态下不继续像编辑器一样工作”落实到 UI。
