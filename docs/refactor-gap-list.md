# Refactor Gap List

> 目的：列出当前代码与目标架构之间的明确差距，供后续 Phase / PR 跟踪使用。

## Phase 1 — 统一配置真相

### Gap 1.1: `PublishConfig` vs `ScheduleConfig`
- **现状**：
  - backend canonical 与 legacy config 接口都已桥接到 `ScheduleConfig`
  - `PublishConfig` 仍保留为遗留模型，但不再是主写路径
- **目标**：
  - backend 只有一个调度配置真相：`ScheduleConfig`
- **状态**：
   - PR2 backend 已完成，待 frontend 和文档消费层进一步收口

### Gap 1.2: 前端仍消费旧 config contract
- **现状**：
  - `frontend/src/pages/ScheduleConfig.tsx` 已切换到 canonical hook / contract
  - `frontend/src/hooks/useScheduleConfig.ts` 已绑定 `/api/schedule-config`
  - `frontend/src/hooks/usePublish.ts` 已只保留发布控制/状态相关 hooks
- **目标**：
  - 前端配置页面改为 canonical schedule-config contract
 - **状态**：
   - PR3 已完成

### Gap 1.3: runtime status split-brain
- **现状**：
  - `/api/publish/status` 已依赖 scheduler runtime truth
  - start / pause / stop 已不再依赖 API 内部平行 dict
- **目标**：
  - API status 完全派生自 scheduler runtime truth
 - **状态**：
   - PR4 已完成

## 后续 Phase 提醒

### Phase 2
- 任务资源集合模型与发布执行语义仍不一致

### Phase 3
- OpenAPI/generated client 与手写 axios 仍有漂移

### Phase 4
- Electron 主进程与 backend 启动路径耦合过深

### Phase 5
- system/settings 存在伪配置能力
