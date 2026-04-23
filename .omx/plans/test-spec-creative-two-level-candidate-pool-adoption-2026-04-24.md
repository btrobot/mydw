# Test Spec 草案（Deliberate）

## 测试目标

证明本次落地不仅改了页面表达，而且让 **作品真值、候选池、当前入选、Workbench 汇总、Version/Package 冻结** 五个层面的口径一致。

## 测试原则

1. 先 Detail，后 Workbench。
2. 先真值，再候选联动，再冻结快照。
3. 手工覆盖规则单独成组测试。
4. 所有汇总口径以后端聚合结果为准。
5. 每个 slice 都要有最小自动化闭环，不接受“最后统一测”。
6. authority source、selected-media projection、manifest contract 必须有明确合同测试，不接受“靠字符串/隐式路径工作”。
7. Phase 0 六份合同文档必须以自动化测试校验存在性与关键字段，不接受只靠人工阅读。

## 分层计划

### Unit

前端：
- `creativeAuthoring.ts` 的 parse/build 映射
- `useCreativeAuthoringModel.ts` 的 mode/联动逻辑
- Workbench 摘要字段渲染与 preset/filter 辅助函数
- current cover contract 字段映射与 mode 切换

后端：
- `creative_service.py` 的真值优先级
- 主题商品唯一性与排序规则
- 候选状态转换
- 当前入选集合排序/enabled 规则
- version/package 冻结字段组装
- `creative_input_items` 兼容退场规则
- manifest v1 结构组装

### Integration

- `backend/api/creative.py` 的 create/get/patch/list 合同
- `backend/schemas/__init__.py` 与 models 对齐
- migration 后读写兼容
- Workbench summary 聚合正确
- publish/version 服务读取真值与当前入选而非旧隐式字段
- authority matrix 对应的 read/write/freeze 路径符合约束
- `manifest v1` 结构合同可序列化、可回读、可比较
- `backend/services/creative_generation_service.py` 与 `backend/services/ai_clip_workflow_service.py` 不绕过新口径

### E2E

1. 新建作品并进入 Detail
2. 设置/修改真值
3. 添加多个商品并切换主题商品
4. 从候选池加入视频/音频并排序
5. 保存后回到 Workbench 校验摘要/诊断
6. 进入 Version/Publish 校验冻结快照

### Observability

- 关键 service 路径有结构化日志或可断言输出：
  - 真值来源模式
  - 当前入选媒体计数
  - Version/Package 冻结 manifest
- 失败时可定位到 slice/字段/模式，不是笼统 500
- 若已有 metrics/report hooks，至少保证不会因新字段缺失而静默失败

## Slice 级测试

### Slice 1：作品真值显式化

必测：
- current product name / cover / copywriting 回显
- manual/follow/adopted 模式切换
- 保存后重开 Detail 仍正确
- current cover contract 字段/API 名称稳定，无猜测空间

建议落点：
- 后端：`backend/tests/test_creative_api.py`、`test_creative_schema_contract.py`
- 前端：新增/扩展 creative authoring 相关测试

### Slice 2：作品-商品关联表

必测：
- 多商品关联
- 主题商品唯一
- 顺序调整后持久化
- 主题商品切换驱动默认真值来源
- `subject_product_id` / `primary product_link` 对应规则稳定
- snapshot 唯一写入口正确

建议落点：
- 后端：新增 creative links 相关测试到 `test_creative_api.py`
- E2E：Detail 内商品关联操作

### Slice 3：候选池

必测：
- 候选导入/增加/移除/采用
- `candidate_type`、`source_kind`、`status` 合同
- 候选与当前状态标签一致

建议落点：
- 后端：creative candidate CRUD/contract
- 前端：Detail 候选分区交互

### Slice 4：当前入选媒体集合

必测：
- 候选加入入选集合
- 排序/启停/移除
- 刷新后保持
- 合成/版本读取当前入选集合
- selected-media projection 成为唯一读取口径
- Workbench / Version / Publish 不再直接依赖旧 orchestration 隐式拼装
- copywriting/cover/topic 的兼容退场规则符合 Phase 0 附录

建议落点：
- 后端：`backend/tests/test_composition_creative_writeback.py`
- 前端/E2E：Detail 媒体入选操作

### Slice 5：Workbench 汇总升级

必测：
- `current_product_name`
- `selected_video_count`
- `selected_audio_count`
- `candidate_video_count`
- `candidate_audio_count`
- `definition_ready`
- `composition_ready`
- preset/filter/sort 不回归

建议落点：
- 后端：creative list summary contract
- 前端：`frontend/e2e/creative-workbench/creative-workbench.spec.ts`

### Slice 6：Version / Package 对齐

必测：
- 两次不同版本能冻结不同真值
- 发布包冻结值与当前 detail 状态一致
- manifest 可回溯
- `manifest v1` key 集、顺序语义、enabled 语义稳定
- 冻结读取路径不绕过 authority matrix
- `creative_generation_service.py` / `ai_clip_workflow_service.py` / `publish_service.py` 消费口径一致

建议落点：
- 后端：`backend/tests/test_creative_versioning.py`、`test_publish_execution_snapshot.py`
- 前端/E2E：`frontend/e2e/creative-version-panel/creative-version-panel.spec.ts`

## 跨 Slice 扩展回归

### Authority / Cutover 回归

- 新字段生效后，旧字段仅回读兼容，不再承担新增语义
- Workbench summary 只读后端统一聚合结果
- Version / Publish 只读当前真值与 selected-media projection

### 手工覆盖规则

- 商品名：manual 后切主题商品不覆盖；恢复跟随后恢复自动同步
- 文案：采用候选后可手改；新候选生成不应覆盖 manual
- 封面：切换候选、保存、刷新、回显一致

### Detail / Workbench 往返一致性

- Detail 修改 → Workbench 摘要变化 → 再进 Detail 一致

### 冻结一致性

- 生成版本 / 冻结发布后，与当时 Detail 展示一致

## 3 个预警性失败场景的测试映射

1. **生成仍读旧输入项**
   - 测试：版本/发布服务 contract test + E2E 冻结比对
2. **Workbench 摘要与 Detail 漂移**
   - 测试：list API summary contract + 往返 E2E
3. **manual 被新候选覆盖**
   - 测试：mode transition unit + Detail 回归 E2E

## 推荐执行时的测试顺序

1. 后端 schema/service 合同
2. 前端 authoring/workbench unit
3. 单 slice integration
4. 单 slice E2E
5. 跨 slice 回归
6. 收口时跑 creative 相关全集

## 推荐验证命令

```bash
cd frontend
npm run typecheck
npm run build
npx playwright test frontend/e2e/creative-workbench/creative-workbench.spec.ts frontend/e2e/creative-main-entry/creative-main-entry.spec.ts frontend/e2e/creative-version-panel/creative-version-panel.spec.ts

cd ../backend
pytest backend/tests/test_creative_api.py backend/tests/test_creative_schema_contract.py backend/tests/test_creative_versioning.py backend/tests/test_publish_execution_snapshot.py backend/tests/test_composition_creative_writeback.py backend/tests/test_ai_clip_workflow.py backend/tests/test_creative_workflow_contract.py backend/tests/test_publish_scheduler_cutover.py backend/tests/test_publish_service_semantics.py backend/tests/test_openapi_contract_parity.py backend/tests/test_creative_task_mapping.py
```

## 完成判据

1. Detail 真值、候选池、当前入选都可稳定回显。
2. Workbench 摘要与 Detail 一致。
3. manual/follow/adopted 规则无回归。
4. 版本/发布冻结值与当时作品状态一致。
5. authority matrix、selected-media projection、manifest v1 contract 对应测试全部通过。
6. 关键测试集全部通过，且无未解释失败。
