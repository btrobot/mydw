# Frontend Development

> Version: 1.1.0
> Updated: 2026-04-12
> Status: Active

Frontend entry point for the DewuGoJin Electron + React application.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Desktop | Electron 28 |
| UI Framework | React 18 |
| Language | TypeScript 5 |
| Build | Vite 5 |
| Components | Ant Design 5 |
| State | Zustand |
| Data Fetching | @tanstack/react-query |
| API Client | @hey-api/client-fetch + generated SDK |
| E2E Testing | Playwright |

## Current repo surface

`frontend/` 里的高信号目录：

- `src/` — 页面、组件、hooks、状态和前端逻辑
- `electron/` — Electron 主进程 / preload / launcher 层
- `scripts/` — OpenAPI 导出、生成物检查、版本同步等脚本
- `e2e/` — Playwright E2E 测试

本地运行产物不应被当作 repo surface：

- `node_modules/`
- `dist/`, `dist-electron/`
- `logs/`
- `test-results/`

## Common commands

```bash
cd frontend
npm install
npm run dev
npm run dev:electron
npm run typecheck
npm run api:generate
npm run generated:check
npm run test:e2e
```

## Generated artifacts

当前前端存在一部分**应受治理的生成物**，请遵循现有策略：

- `frontend/openapi.local.json`
- `frontend/src/api/`
- `frontend/electron/*.js` 及其 map 文件

修改相关来源后，优先使用：

```bash
npm run generated:regenerate
npm run generated:check
```

## References

| Document | Path | What it answers |
|----------|------|-----------------|
| Docs Index | `docs/README.md` | 当前文档阅读入口 |
| Current Architecture | `docs/current/architecture.md` | 当前前后端架构基线 |
| Current Runtime Truth | `docs/current/runtime-truth.md` | 当前运行/API 真相 |
| Dev Guide | `docs/guides/dev-guide.md` | 环境搭建与启动流程 |
| Generated Artifact Policy | `docs/governance/generated-artifact-policy.md` | 生成物边界与治理规则 |
| OpenAPI Workflow | `docs/guides/openapi-generation-workflow.md` | OpenAPI 导出与 SDK 生成流程 |
| Runtime/Local Artifact Policy | `docs/governance/runtime-local-artifact-policy.md` | runtime / local artifact 边界 |
| API Reference (stale) | `docs/archive/reference/api-reference.md` | 历史 API 参考，需晚于 current docs 阅读 |
| Data Model (stale) | `docs/archive/reference/data-model.md` | 历史数据模型参考，需晚于 current docs 阅读 |
