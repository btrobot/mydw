# PR-2 Runtime Acceptance：local_ffmpeg + 随机账号发布

- 日期：2026-04-20
- 关联规划：
  - `.omx/plans/prd-release-hardening-runtime-acceptance-closeout.md`
  - `.omx/plans/test-spec-release-hardening-runtime-acceptance-closeout.md`
- 结论：**通过**
- 变更范围：**仅新增本报告；未修改生产代码**

---

## 1. 本轮验收目标

验证两条已经落地、但此前缺少“真实运行留痕”的关键链路：

1. `local_ffmpeg` 是否能在真实 FFmpeg/FFprobe 环境下完成本地合成并写回任务结果。
2. 任务是否可以在**创建时不绑定账号**，并在**发布时随机选择一个 active 账号**完成发布。
3. 当没有可用 active 账号时，系统是否返回**明确业务错误**，而不是莫名其妙的 500。

---

## 2. 验收方法

为避免污染真实运行数据、又保留真实服务路径，本次采用：

- **真实代码路径**
  - `TaskDistributor`
  - `CompositionService`
  - `LocalFFmpegCompositionService`
  - `PublishService`
- **真实运行依赖**
  - 本机已安装 `ffmpeg` / `ffprobe`
  - 真实素材文件路径
- **隔离运行环境**
  - 复制 `backend/data/dewugojin.db` 到临时目录
  - 在临时目录写入匹配本机设备 ID 的 auth artifacts
- **安全边界**
  - 发布链路只在**外部副作用边界**做 stub：
    - `services.publish_service.get_dewu_client`
    - `services.publish_service.browser_manager`
  - 这样可以保留：
    - 任务发布前状态迁移
    - 随机账号选择
    - 发布语义校验
    - 上传参数构造
  - 同时避免真的向得物上传内容。

---

## 3. 运行基线

- 临时数据库：`E:\WindowsTemp\pr2-runtime-acceptance-4p9e44yb\dewugojin.db`
- 临时输出目录：`E:\WindowsTemp\pr2-runtime-acceptance-4p9e44yb\videos`
- 本机设备 ID：`device-15c7650b-f838-412b-948c-71f503f02cc9`

验收时使用到的现有基线数据：

- `PublishProfile`
  - `profile_id=2`
  - `composition_mode=local_ffmpeg`
- `Video`
  - `video_id=5`
  - `video_path=data\materials\videos\2926ef49da617814.mp4`
- 验收开始前可用 active 账号
  - `account_id=6`

---

## 4. Case A：local_ffmpeg 真实合成成功

### 执行方式

1. 通过 `TaskDistributor` 创建一个**不绑定账号**的任务。
2. 使用 `CompositionService.submit_composition(task_id)` 触发 `local_ffmpeg`。
3. 使用真实 `ffprobe` / `ffmpeg` 完成输出文件生成与回写。

### 结果

- 创建后任务：
  - `task_id=2`
  - `status=draft`
  - `account_id=null`
- 合成任务：
  - `job_id=2`
  - `job_status=completed`
- 合成完成后任务：
  - `task_status=ready`
  - `final_video_path=E:\WindowsTemp\pr2-runtime-acceptance-4p9e44yb\videos\final_2.mp4`
  - `final_video_exists=true`
  - `final_video_duration=53`
  - `final_video_size=17831747`

### 验收结论

`local_ffmpeg` 链路已经不是“只在代码里存在”：

- 能真实调用 FFmpeg；
- 能生成最终视频；
- 能把 `final_video_path / duration / size` 回写到任务与合成任务记录；
- 任务状态能从 `draft -> composing -> ready` 正常收敛。

---

## 5. Case B：无预绑账号任务在发布时随机选择 active 账号成功

### 执行方式

对 Case A 生成的 `task_id=2` 继续调用 `PublishService.publish_task(task)`，仅在外部上传/浏览器边界做 stub。

### 结果

- 发布结果：
  - `success=true`
  - `message=发布成功`
- 发布后任务：
  - `task_status=uploaded`
  - `account_id_after_publish=6`
- 账号选择证据：
  - `requested_account_ids=[6]`
- 上传调用证据：
  - `upload_call_count=1`
  - `upload_kwargs.video_path=E:\WindowsTemp\pr2-runtime-acceptance-4p9e44yb\videos\final_2.mp4`
  - `upload_kwargs.title=视频标题`
  - `upload_kwargs.content=""`
  - `upload_kwargs.topic=null`
  - `upload_kwargs.cover_path=null`

### 验收结论

“创建任务时不选账号、发布时自动挑选 active 账号”这条语义成立：

- 任务创建阶段可以 `account_id=null`；
- 发布阶段会补选 active 账号；
- 上传参数使用的是合成后的 `final_video_path`；
- 发布完成后任务状态正确进入 `uploaded`。

---

## 6. Case C：没有可用 active 账号时明确失败，而不是 500

### 执行方式

1. 再次通过 `TaskDistributor` 创建一个不绑定账号的任务。
2. 将临时数据库中的所有账号切换为 `inactive`。
3. 调用 `PublishService.publish_task(task)`。

### 结果

- 失败任务：
  - `task_id=3`
- 发布结果：
  - `success=false`
  - `message=没有可用发布账号`
- 失败后任务：
  - `task_status=failed`
  - `error_msg=没有可用发布账号`
  - `account_id_after_publish=null`
- 外部上传：
  - `upload_attempted=false`

### 验收结论

失败路径已经收敛为**明确、可诊断的业务错误**：

- 不再是 500；
- 没有账号时不会继续走外部上传；
- 任务会落到 `failed`，并带清晰错误文案。

---

## 7. 自动化基线回归

### Backend

命令：

```powershell
cd backend
pytest tests/test_task_assemble.py tests/test_publish_service_semantics.py tests/test_local_ffmpeg_composition.py
```

结果：

- `24 passed`

### Frontend

命令：

```powershell
cd frontend
npm run typecheck
npm run build
```

结果：

- `typecheck` 通过
- `build` 通过

---

## 8. 本轮实际遇到的阻塞与处理

### 阻塞 1：临时 auth session 的 device_id 与本机设备 ID 不一致

现象：

- `require_active_service_session()` 经过 `AuthService.restore_session()` 后返回 `device_mismatch`
- 错误为：
  - `This device is no longer authorized for the current session.`

原因：

- 当前认证策略会把数据库中的 session truth 与本机文件中的 device identity 一起校验。
- 临时验收 session 如果使用了假设备 ID，就会被判定为设备不匹配。

处理：

- 读取 `backend/data/remote_auth_device.json`
- 使用真实本机设备 ID：
  - `device-15c7650b-f838-412b-948c-71f503f02cc9`

结论：

- 这是**验收 harness 的对齐问题**，不是生产代码 bug。

### 阻塞 2：临时 session 注入时需使用当前仓库约定的 naive UTC 时间

现象：

- 初版验收脚本把 aware datetime 写入 `RemoteAuthSession`
- `restore_session()` 比较时间时触发 naive/aware 比较异常

处理：

- 验收脚本改为使用与当前仓库存储方式一致的 naive UTC 时间

结论：

- 这同样是**验收数据注入方式**需要贴合当前模型约定，并未暴露新的生产阻塞。

---

## 9. PR-2 收口结论

本次 PR-2 的目标已经满足：

- [x] `local_ffmpeg` 至少完成 1 次真实成功链路
- [x] 产物文件真实生成，`final_video_path` 已回写
- [x] 无预绑账号任务在发布时成功随机选择 active 账号
- [x] 无可用账号时返回明确业务错误，而不是 500
- [x] 自动化基线回归通过
- [x] 产出正式验收留痕文档

最终结论：

> **PR-2 可标记为完成。**

---

## 10. 本 PR 建议提交边界

本 PR 建议保持为：

- `reports/runtime-acceptance-local-ffmpeg-and-random-account-2026-04-20.md`

不混入：

- 新功能开发
- UI 调整
- flaky E2E 修复
- 额外重构

这样可以把 PR-2 明确收敛为：**真实 runtime acceptance 证据落档**。
