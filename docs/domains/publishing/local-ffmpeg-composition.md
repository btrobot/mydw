# local_ffmpeg V1 收口说明

> Status: Current  
> Last updated: 2026-04-20  
> Purpose: PR-4 docs + regression closeout

---

## 1. 这次收口完成了什么

`local_ffmpeg` 不再只是前后端暴露出来的配置值，而是当前仓库中的**真实可运行能力**：

- Profile 可以配置 `composition_mode = local_ffmpeg`
- 任务创建阶段会执行 V1 输入校验
- `submit_composition()` 可以真实走本地 FFmpeg
- 成功后会写回 `Task.final_video_path`
- 发布链路会继续优先消费 `final_video_path`

---

## 2. V1 明确支持范围

### 2.1 支持

- 1 个视频输入
- 0/1 个音频输入
- 0/1 个文案
- 0/1 个封面
- 多个话题

### 2.2 输入分层

| 资源 | V1 中的职责 |
| --- | --- |
| 视频 | 本地 FFmpeg 主输入 |
| 音频 | 可选背景音频 |
| 文案 | 发布层元数据 |
| 封面 | 发布层元数据 |
| 话题 | 发布层元数据 |

---

## 3. V1 明确不支持范围

当前版本**不支持**：

- multi-video montage
- multi-audio mixing strategy beyond `0/1`
- subtitle / copywriting burn-in
- cover embed into video
- 本地异步 composition scheduler
- `CompositionPoller` 驱动的 local FFmpeg 收口

---

## 4. 当前真实执行链

```text
Task(draft)
  -> submit_composition()
  -> CompositionJob(local_ffmpeg)
  -> Task(composing)
  -> local FFmpeg sync run
  -> success: Task(ready) + final_video_path
  -> failure: Task(failed) + failed_at_status=composing
```

关键点：

- `CompositionPoller` 只服务 `coze`
- `local_ffmpeg` 由 `CompositionService` 直接收口
- publish path 只关心最终视频，不关心 FFmpeg 细节

---

## 5. 回归命令集

### 5.1 backend

```powershell
cd backend
pytest tests/test_task_creation_semantics.py
pytest tests/test_task_assemble.py
pytest tests/test_task_legacy_compat.py
pytest tests/test_publish_service_semantics.py
pytest tests/test_composition_creative_writeback.py
pytest tests/test_local_ffmpeg_contract.py
pytest tests/test_local_ffmpeg_composition.py
pytest tests/test_doc_truth_fixes.py
```

### 5.2 frontend

```powershell
cd frontend
npm run typecheck
npm run build
npx playwright test -c e2e/playwright.config.ts e2e/task-diagnostics/task-diagnostics.spec.ts
```

---

## 6. closeout 结论

### 6.1 本轮已经完成

- contract 已冻结到 `local_ffmpeg V1`
- backend 执行链已打通
- frontend 已按 V1 真实能力收口
- docs 已修正为当前实现真相

### 6.2 本轮没有做

- 不扩展到复杂本地编排器
- 不补多视频合成能力
- 不补文案烧录
- 不补封面嵌入
- 不把 local FFmpeg 迁移成 poller 模式

---

## 7. 后续技术债

如需继续演进，建议按这个顺序考虑：

1. multi-video montage contract
2. richer audio mixing contract
3. subtitle / overlay rendering
4. async local composition runner
5. cancel / progress reporting

只有在上面这些 contract 被重新设计并补足测试后，才应扩大 `local_ffmpeg` 的输入面。
