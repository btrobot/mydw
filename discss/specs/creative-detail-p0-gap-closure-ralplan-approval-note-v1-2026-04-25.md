# CreativeDetail P0 缺口补齐计划：RALPLAN 审批结果说明 v1

## 结果

- 最终计划文件：
  - `.omx/plans/ralplan-creative-detail-p0-gap-closure-final-candidate-2026-04-25.md`
- architect 复核结果：
  - `APPROVE`
- critic 复核结果：
  - `APPROVE`

## 本轮补齐的关键 blocker

1. 补入 AC-22 的真实保存草稿链路
   - `creative-detail-save-authoring`
   - `PATCH /api/creatives/{creative_id}`
   - `CreativeDetailResponse`
   - 明确“不创建新版本”的字段级信号
2. 补入 `creative.status -> backend page_mode -> frontend detailInteractionMode -> hero/test ids` 对账表
3. 补入 AIClip 真正的新版本 authority 文件
   - `backend/services/ai_clip_workflow_service.py:47-136`
4. 放宽 R4 对 observation-heavy / route-state-heavy 条目的证据矩阵规则
5. 明确 AC-24 当前只可按“review 子集成立 / 独立 confirm CTA 未被假定已存在”的口径收口

## 非阻塞提醒

- R3 的 UI 验收语句，后续执行时优先按：
  - `creative.status -> page_mode -> detailInteractionMode`
  的映射表验收
- 不建议再回退成“只看 page_mode 下按钮是否可见”的旧口径

## 下一步建议

- 这份计划现在可以作为后续执行模式的批准输入：
  - 若强调单 owner 严格串行收口：走 `ralph`
  - 若要并行分 lane 补齐：走 `team`
