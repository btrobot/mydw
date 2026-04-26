# Test Spec — 作品二级候选池模型落地（Workbench / Detail）

## 1. 范围

本测试规格覆盖：

- 作品真值显式化
- 作品-商品关联表
- 作品候选池
- 当前入选媒体集合
- workbench 汇总升级
- version/package 对齐

目标不是证明视觉改版，而是证明：

1. 新模型数据正确
2. detail 页面行为正确
3. workbench 能正确汇总
4. version/package 快照正确

---

## 2. 测试原则

1. **先验证 detail，再验证 workbench**
2. **先验证真值，再验证候选联动**
3. **唯一真值与集合型入选分开测**
4. **手工覆盖行为必须单独测**
5. **version/package 冻结值必须回溯验证**

---

## 3. 测试分层

## 3.1 后端测试

重点覆盖：

- 新增/升级表结构读写
- detail/list 聚合响应正确
- 默认规则与手工覆盖规则正确
- version/package 冻结快照正确

## 3.2 前端页面测试

重点覆盖：

- detail 页面回显
- 候选 → 当前入选联动
- 手工编辑覆盖
- workbench 摘要展示与筛选

## 3.3 E2E 测试

重点覆盖：

- 新建作品
- 调整候选
- 保存
- 返回 workbench
- 再进入 detail 验证回显
- 生成版本 / 冻结发布包

---

## 4. Slice 级验证

## Slice 1：作品真值显式化

### 要验证什么

- 商品名称 / 封面 / 文案在 detail 顶部显式可见
- 来源模式能正确回显

### 后端验证

- `creative_items` 新字段可保存与读取
- `CreativeDetailResponse` 返回 current-* 字段

### 前端验证

- detail 初次加载时显示当前商品名称 / 封面 / 文案
- 修改商品名称后保存，再次进入仍正确
- 采用候选文案后，当前文案卡即时更新

### 核心用例

1. 初始值回显
2. 手工编辑商品名称
3. 手工编辑文案
4. 更换封面

---

## Slice 2：作品-商品关联表

### 要验证什么

- 一件作品可关联多个商品
- 主题商品唯一
- 顺序变更有效

### 后端验证

- `creative_product_links` CRUD
- 同一作品多个商品排序正确
- 唯一主题商品约束正确

### 前端验证

- detail 页可新增商品
- 可设为主题商品
- 可上移/下移/移除

### 核心用例

1. 添加第二个商品
2. 切换主题商品
3. 调整商品顺序
4. 移除非主题商品

---

## Slice 3：作品候选池

### 要验证什么

- 候选项能进入作品小池
- 来源信息清晰
- 候选状态正确

### 后端验证

- `creative_candidate_items` CRUD
- `source_kind` / `candidate_type` 正确
- 候选状态切换正确

### 前端验证

- 候选封面 / 文案 / 视频 / 音频分区显示
- 每项显示来源与状态
- 可采用 / 加入 / 取消

### 核心用例

1. 商品导入后自动出现候选封面/视频
2. 素材库添加一个额外音频进入候选池
3. 文案候选列表可采用当前项

---

## Slice 4：当前入选媒体集合

### 要验证什么

- 视频 / 音频当前入选可单独查看
- 候选变动可联动当前入选
- 顺序、启停、移除有效

### 后端验证

- 当前入选媒体集合正确保存
- 排序与 enabled 状态正确
- 合成读取的是当前入选集合

### 前端验证

- 候选视频加入后，当前入选视频表立即更新
- 从当前入选移除后，候选状态同步变化
- 排序后刷新仍保持

### 核心用例

1. 从候选加入两个视频
2. 调整视频顺序
3. 禁用其中一个视频
4. 加入 / 移除音频

---

## Slice 5：Workbench 汇总升级

### 要验证什么

- workbench 能展示当前定义摘要与入选摘要
- preset/filter 不被新字段破坏

### 后端验证

- 列表接口返回 summary 字段：
  - `current_product_name`
  - `selected_video_count`
  - `selected_audio_count`
  - `candidate_video_count`
  - `candidate_audio_count`
  - `definition_ready`
  - `composition_ready`

### 前端验证

- WorkbenchTable 显示新摘要
- SummaryCard 与 DiagnosticsDrawer 使用新聚合字段
- 现有筛选/排序/分页语义保持稳定

### 核心用例

1. 当前真值摘要显示
2. 当前入选摘要显示
3. 缺封面/缺文案/缺视频时 diagnostics 正确
4. 现有 preset 行为不回归

---

## Slice 6：Version / Package 对齐

### 要验证什么

- 版本记录冻结的是当时真值
- 发布包冻结的是当时真值 + 入选快照

### 后端验证

- `creative_versions` 保存 final 真值与 manifest
- `package_records` 保存 frozen 真值与 manifest

### 前端验证

- VersionPanel 能查看某版本冻结值
- 发布包区能查看某次冻结的四件套

### 核心用例

1. 保存当前定义后生成版本
2. 修改当前定义再生成第二个版本
3. 验证两个版本冻结值不同且各自正确
4. 冻结发布包并核对字段

---

## 5. 跨 Slice 关键行为测试

## 5.1 手工覆盖规则

必须单独验证：

### 商品名称

1. 默认跟随主题商品
2. 用户手工修改后切到 manual
3. 再变更主题商品时，不自动覆盖
4. 点击“恢复跟随”后重新采用主题商品名称

### 文案

1. 采用候选文案后 current value 更新
2. 手工编辑后切到 manual
3. 新候选生成后不自动覆盖

### 封面

1. 默认采用主题商品默认封面
2. 切换到其他候选封面后 current cover 更新
3. 保存/刷新后回显正确

---

## 5.2 候选与当前入选联动

必须单独验证：

1. 候选视频加入 → 当前入选出现
2. 当前入选移除 → 候选状态更新
3. 候选音频加入 → 当前音频表出现
4. 移除关联商品后，来源于该商品的候选如何处理符合定义

---

## 5.3 Workbench / Detail 往返一致性

必须验证：

1. detail 改完保存
2. 回到 workbench
3. 列表摘要正确
4. 再进入 detail
5. 当前定义与当前入选一致回显

---

## 6. 推荐自动化覆盖

## 前端

推荐补充：

- `CreativeDetail` 关键交互测试
- `WorkbenchTable` 摘要渲染测试
- 视图模型测试（若已有模式）

## E2E

推荐新增一组 detail-focused 场景：

1. 多商品关联 + 切换主题商品
2. 采用候选封面 / 文案
3. 视频候选加入与排序
4. 保存后 workbench 回显

---

## 7. 推荐验证命令

```bash
cd frontend
npm run typecheck
npm run build
npx playwright test

cd ../backend
pytest
```

如已有更细粒度 creative spec，可优先跑 creative 相关集。

---

## 8. 完成判据

当以下条件同时成立时，可视为该计划测试通过：

1. Detail 能正确表达当前定义 / 当前入选 / 候选列表
2. Workbench 能正确汇总真值与入选摘要
3. 手工覆盖规则无回归
4. 候选联动规则无回归
5. Version / Package 快照冻结正确
6. typecheck / build / relevant tests 通过

