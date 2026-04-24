# Creative Two-Level Candidate Pool Adoption Closeout / 作品二级候选池总收口

> Version: 1.0.0  
> Updated: 2026-04-24  
> Owner: Product / Domain Design / Codex  
> Status: Completed

> 目的：把 `prd-creative-two-level-candidate-pool-adoption-2026-04-24.md` 这条 **Phase 0 + Slice 1~6** 总计划，从“已逐 slice 落地”收束成一份正式 closeout，明确整条计划已完成什么、哪些合同已经真正成为系统真值、哪些兼容层仍是受控保留，以及为什么现在可以退出该计划。

---

## 1. 一句话总结

> 截至 2026 年 4 月 24 日，creative 二级候选池计划已完成 **合同冻结 → 当前真值显式化 → 商品关联主语义收敛 → 作品候选池持久化 → selected-media projection 收口 → Workbench 汇总升级 → Version/Package/Publish freeze 对齐** 的完整闭环；该计划可以正式收口，后续工作应转入独立 follow-up，而不再继续以本计划名义扩边界。

---

## 2. 本计划范围

本次收口对应的正式总计划：

- PRD：`.omx/plans/prd-creative-two-level-candidate-pool-adoption-2026-04-24.md`
- companion test spec：`.omx/plans/test-spec-creative-two-level-candidate-pool-adoption-2026-04-24.md`
- IA / data / roadmap：`discss/work-two-level-candidate-pool-ia-data-roadmap-2026-04-24.md`

执行范围是：

- **Phase 0**
  - authority matrix
  - primary-product rules
  - current-cover contract
  - input-items compat retirement
  - workbench summary mapping
  - manifest v1 contract
- **Slice 1 ~ Slice 6**
  - Slice 1：作品真值显式化
  - Slice 2：作品-商品关联表
  - Slice 3：作品候选池
  - Slice 4：当前入选媒体集合 / selected-media projection
  - Slice 5：Workbench 汇总升级
  - Slice 6：Version / Package 对齐

本次 closeout **不把更早的 Creative Domain Model Realignment Phase 0~4 重写一遍**；它们作为前置背景仍然成立，但本文件只对本次二级候选池计划本身负责。

---

## 3. 完成矩阵（Phase 0 + Slice 1~6）

| Phase / Slice | 目标 | 实际落地 | 代表提交 / 证据 |
|---|---|---|---|
| Phase 0 | 冻结合同与 authority boundary | 已完成 | `454eac9` |
| Slice 1 | 作品真值显式化 | 已完成 | `2fb9561` |
| Slice 2 | 商品关联主语义收敛到 `creative_product_links` | 已完成 | `38b8a29` |
| Slice 3 | 作品候选池持久化 | 已完成 | `6333d13` |
| Slice 4 | selected-media projection 收口 | 已完成 | `a426abd`、`867c80d`；稳定化证据：`6e42b75`、`33dcc21`、`ace91e0` |
| Slice 5 | Workbench 只消费后端聚合摘要 | 已完成 | `b81fcad` |
| Slice 6 | Version / Package / Publish freeze 统一读口径 | 已完成 | `9a49bb9` |

结论：

- 计划内 **无未完成 slice**
- 计划内 **无遗留“批准但未实现”的主功能块**
- 剩余事项已不属于本计划内的必做 slice，而是后续独立治理项

---

## 4. 本计划最终改变了什么

### 4.1 当前真值层

作品当前定义现在稳定收敛到 `creative_items` 上的 current-* contract：

- `current_product_name`
- `product_name_mode`
- `current_cover_asset_type`
- `current_cover_asset_id`
- `cover_mode`
- `current_copywriting_id`
- `current_copywriting_text`
- `copywriting_mode`

这意味着：

- 商品名称 / 封面 / 文案不再依赖旧 snapshot/拼装叙事才能表达
- Detail 与 Workbench 读的是同一层 current truth

### 4.2 商品关联层

主题商品与商品顺序现在以 `creative_product_links` 为主语义面：

- `is_primary` 成为唯一主题商品入口
- `subject_product_id` 降为兼容镜像/历史回读

### 4.3 候选池层

作品候选范围现在由 `creative_candidate_items` 持久化表达：

- 候选与当前入选分层
- 候选不再等于“当前已采用”
- 候选池可独立支撑来源、状态、adopt/remove 语义

### 4.4 当前入选层

当前真正参与作品定义/合成的媒体集合已收口为 selected-media projection：

- 迁移期物理承载仍为 `creative_input_items`
- 但权威写入只允许 `video/audio`
- `enabled` 成为 selected membership gate
- video/audio 顺序语义按全局 `sequence` 过滤后确定

### 4.5 Workbench 汇总层

Workbench 现在只消费后端聚合摘要，不再以前端临时拼装为长期方案：

- `current_product_name`
- `current_cover_thumb`
- `current_copy_excerpt`
- `selected_video_count`
- `selected_audio_count`
- `candidate_video_count`
- `candidate_audio_count`
- `candidate_cover_count`
- `definition_ready`
- `composition_ready`
- `missing_required_fields`

### 4.6 Freeze / Publish 层

Version / Package / Publish 的 freeze 口径已统一：

- `creative_version_service.py` 成为 `manifest v1` 的统一组装 owner
- `PackageRecord.manifest_json` 不再接受 per-service 各自定义语义
- publish snapshot 读到的是同一份 package freeze truth
- compat projection 只保留回读兼容，不再承担 freeze authority

---

## 5. 哪些合同已经成为当前系统真值

以下合同已从“规划文档”升级为“代码与测试共同约束的当前系统真值”：

1. `.omx/plans/phase0-creative-two-level-candidate-pool-authority-matrix-2026-04-24.md`
2. `.omx/plans/phase0-creative-two-level-candidate-pool-primary-product-rules-2026-04-24.md`
3. `.omx/plans/phase0-creative-two-level-candidate-pool-current-cover-contract-2026-04-24.md`
4. `.omx/plans/phase0-creative-two-level-candidate-pool-input-items-compat-retirement-2026-04-24.md`
5. `.omx/plans/phase0-creative-two-level-candidate-pool-workbench-summary-mapping-2026-04-24.md`
6. `.omx/plans/phase0-creative-two-level-candidate-pool-manifest-v1-contract-2026-04-24.md`

其中最关键的收口结论是：

- **primary product**：以 `creative_product_links.is_primary` 为准
- **current truth**：以 `creative_items.current-*` 为准
- **selected media**：以 selected-media projection 为准
- **workbench summary**：以后端 aggregator 为准
- **version/package freeze**：以 `creative_version_service.py` 统一 freeze/manifest builder 为准

---

## 6. 兼容层现状（仍保留，但已降权）

本计划完成后，仍有一些兼容面被有意保留，但它们已经不再是主语义：

### 6.1 仍保留的 compat

- `creative_items.subject_product_id`
- `subject_product_name_snapshot`
- `main_copywriting_text`
- `creative_input_items` 作为 selected-media 的物理 carrier
- `manifest_json` 作为 typed-v1 的持久化字符串承载列

### 6.2 已明确降权的含义

- 它们允许回读兼容
- 它们不应再承接新增业务语义
- 它们不应再被任何新实现拿来作为 authority source

### 6.3 未纳入本计划的后续治理项

以下事项如果要做，必须开新 follow-up，而不是继续算在本计划里：

1. legacy request write fields 的 strict API hard-removal
2. `creative_input_items -> dedicated selected media table` 的物理迁移评估
3. 更彻底的 compat field 物理删除
4. live publish/runtime 的生产链路验证与观测增强

---

## 7. 最终验证证据

### 7.1 本轮最终收口验证（2026-04-24）

已执行并通过：

```powershell
pytest backend/tests/test_creative_versioning.py backend/tests/test_publish_execution_snapshot.py backend/tests/test_publish_service_semantics.py backend/tests/test_ai_clip_workflow.py backend/tests/test_openapi_contract_parity.py backend/tests/test_creative_slice6_freeze_contracts.py -q
```

结果：

- `36 passed`

已执行并通过：

```powershell
cd frontend
npm run generated:check
npm run typecheck
npm run build
```

结果：

- generated artifacts stability：PASS
- frontend typecheck：PASS
- frontend build：PASS

### 7.2 计划级证据说明

整条计划不是在一个 PR 内完成的，而是逐 slice 落地；因此总 closeout 的证据来源由两部分组成：

1. **此前各 slice 的已提交实现与收口证据**
2. **本轮最终收口时对 freeze / contract / frontend build 的再验证**

当前没有证据显示：

- Workbench summary 回退到前端拼装
- selected-media authority 回退到旧 generic input 语义
- Version / Package / Publish 回退到分散的 ad-hoc manifest builder

---

## 8. Exit decision / 总退出结论

> **creative 二级候选池计划可以正式收口。**

原因不是“仓库里再也没有 compat 字段”，而是：

- 计划内的 Phase 0 + Slice 1~6 已全部完成
- authority matrix 已被实际实现吸收
- Workbench / Detail / Version / Package / Publish 已围绕同一套 current truth + selected-media + freeze contract 运转
- 剩余事项已经清晰地从“本计划未完成”转变为“后续独立治理项”

因此，从 2026 年 4 月 24 日开始，应把这条计划视为：

> **已完成的主线，不再继续滚动扩边界。**

---

## 9. 推荐后续项（独立 follow-up，而非本计划续集）

1. API compat hard-removal planning
2. selected-media physical-table 评估（仅当收益明确）
3. publish/runtime live verification 与 observability 增强
4. 若后续再做 IA/UI 深化，应以当前 domain truth 为固定前提，不再重开模型讨论
