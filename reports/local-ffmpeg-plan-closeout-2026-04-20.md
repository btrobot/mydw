# local_ffmpeg 补齐规划收口说明

> 日期：2026-04-20  
> 对应规划：`.omx/plans/archive/prd-local-ffmpeg-composition-pr-plan.md`  
> 结论：**规划主线已完成并收口**

---

## 1. 规划范围回顾

本轮规划目标是把 `local_ffmpeg` 从“前后端已暴露但未真正可用”的半成品状态，收口成一个：

- 有明确 V1 契约
- 有可执行后端链路
- 有前端真实能力对齐
- 有文档与回归证据

的可运行能力。

规划拆分为 4 个 PR：

1. **PR-1**：冻结 `local_ffmpeg` V1 契约
2. **PR-2**：打通本地 FFmpeg 合成执行链
3. **PR-3**：前端按真实能力收口
4. **PR-4**：文档 + 回归收口

---

## 2. 执行结果

### PR-1 已完成

- 提交：`bd6edb3`
- 结果：
  - 冻结 `local_ffmpeg V1` 输入边界
  - 把非法输入前移为明确校验
  - 避免 `local_ffmpeg` 继续停留在“假能力入口”

### PR-2 已完成

- 提交：`3fa583d`
- 结果：
  - `CompositionService` 已能真正处理 `local_ffmpeg`
  - 可写回 `Task.final_video_path`
  - 打通 `draft -> composing -> ready/failed`

### PR-3 已完成

- 提交：`8f1804e`
- 结果：
  - Profile / TaskCreate / TaskDetail 已按 V1 真实能力对齐
  - 前端不再暗示不存在的复杂本地合成能力
  - 用户在提交前即可看到 V1 限制

### PR-4 已完成

- 提交：`cfd658d`
- 结果：
  - 文档改写为当前真实实现
  - 增加 doc-truth regression checks
  - 留下 `local_ffmpeg` 的收口说明与回归命令集

---

## 3. 规划验收结论

对照规划，当前可以确认：

- `local_ffmpeg` 已不再只是 schema / UI 中的声明值
- 后端已具备真实执行路径
- 前端已与 V1 能力边界一致
- 文档、代码、测试三者已基本对齐

因此：

> **`local_ffmpeg 补齐 PR 计划` 的 4 个规划切片已经全部完成。**

---

## 4. 规划外但相关的后续提交

在主线完成后，又补了一笔与任务创建/发布语义相关的后续切片：

- 提交：`9582801`
- 内容：
  - 任务创建不再强制预绑定账号
  - 发布时允许随机选择可用账号
  - 同步收口任务管理/素材选择相关前端体验

这笔提交**不属于原始 `local_ffmpeg` 4 PR 规划本身**，但它与任务主链语义有关，属于规划完成后的后续增强。

---

## 5. 本轮已验证证据

### 主线验证

- Backend：
  - `pytest tests/test_task_creation_semantics.py`
  - `pytest tests/test_task_assemble.py`
  - `pytest tests/test_task_legacy_compat.py`
  - `pytest tests/test_publish_service_semantics.py`
  - `pytest tests/test_composition_creative_writeback.py`
  - `pytest tests/test_local_ffmpeg_contract.py`
  - `pytest tests/test_local_ffmpeg_composition.py`
  - `pytest tests/test_doc_truth_fixes.py`
- Frontend：
  - `npm run typecheck`
  - `npm run build`
  - `playwright e2e/task-diagnostics/task-diagnostics.spec.ts`

### 后续增强验证（账号可选发布）

- `pytest tests/test_task_assemble.py tests/test_publish_service_semantics.py`
- `npm run typecheck`
- `npm run build`
- `playwright e2e/task-diagnostics/task-diagnostics.spec.ts`
- `playwright e2e/creative-workbench/creative-workbench.spec.ts`

---

## 6. 当前冻结的 V1 能力边界

当前 `local_ffmpeg V1` 支持：

- 1 个视频输入
- 0/1 个音频输入
- 0/1 个文案
- 0/1 个封面
- 多个话题

当前明确不支持：

- 多视频 montage
- 多音频复杂混音策略
- 文案烧录
- 封面嵌入视频
- 本地异步 composition scheduler
- `CompositionPoller` 驱动的 local FFmpeg 收口

---

## 7. 仍需注意的非主线问题

这些不构成“规划未完成”，但仍值得注意：

1. **工作区还有非本规划尾项**
   - `AGENTS.md`
   - `ana-docs/task-state-machine-and-composition-analysis.md`
   - `dev-docs/`
   - `docs/collector/`

2. **E2E 稳定性仍需持续观察**
   - 最近一次 `task-diagnostics` 回归出现过一次 flaky retry 后通过
   - 当前不构成主线阻塞，但说明前端回归环境仍有波动

3. **V1 只是收口，不是终态**
   - 当前目标是“真实可运行”
   - 不是“复杂本地视频编排器”

---

## 8. 收口结论

本轮可以正式收口为：

> `local_ffmpeg` 从“伪配置入口”补齐为“有契约、有执行链、有前端对齐、有文档与回归证据”的 V1 能力。

如果后续继续演进，建议新开独立规划，避免把：

- 多视频编排
- 本地异步调度
- 更复杂的媒体处理能力

混回本轮已完成的 V1 收口范围。
