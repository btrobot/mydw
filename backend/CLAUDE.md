# Backend 开发规范

> Updated: 2026-04-12
> Scope: FastAPI backend + automation/runtime support

## 当前定位

`backend/` 是项目的后端源码面，主要包含：

- `api/` — FastAPI 路由层
- `core/` — 配置、浏览器集成、平台客户端等核心运行逻辑
- `services/` — 业务服务层
- `models/` / `schemas/` — 持久化模型与 API schema
- `migrations/` — 数据库迁移
- `tests/` — 当前有效的自动化测试
- `main.py` — FastAPI 入口

## 目录边界

下面这些内容不应再被当作 backend repo surface 的一部分：

- 根层 `test_*.py` 调试脚本
- 根层调试截图 / 页面抓图
- 本地虚拟环境内容（如 `venv/`）
- 本地日志、缓存、运行产物

如果需要保留手工排查脚本，请放到明确的手工工具目录，并避免继续使用 `test_*.py` 这类会与自动化测试混淆的命名。

## 运行方式

优先参考 `docs/guides/dev-guide.md` 的当前开发流程。

常见命令示例：

```bash
cd backend
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m uvicorn main:app --reload --port 8000
```

如本地已经有项目专用虚拟环境，也可以在激活后执行同样命令；但不要把某个固定 `backend/venv/` 路径当作仓库协作前提。

## 测试与验证

当前自动化测试以 `backend/tests/` 为准。

常见命令：

```bash
pytest backend/tests/test_repo_hygiene_policy.py
pytest backend/tests/test_epic7_stale_docs.py
pytest backend/tests/test_generated_artifact_governance.py
pytest backend/tests
```

## 参考文档

| Document | Path | What it answers |
|----------|------|-----------------|
| Docs Index | `docs/README.md` | 当前文档阅读入口 |
| Current Architecture | `docs/current/architecture.md` | 当前系统结构总览 |
| Current Runtime Truth | `docs/current/runtime-truth.md` | 当前运行事实 / live surfaces |
| Dev Guide | `docs/guides/dev-guide.md` | 开发环境与启动方式 |
| Runtime/Local Artifact Policy | `docs/governance/runtime-local-artifact-policy.md` | `.codex/` / `.omx/` / `.omc/` / session artifacts 的边界 |
| API Reference (stale) | `docs/archive/reference/api-reference.md` | 历史 API 参考，需晚于 current docs 阅读 |
| Data Model (stale) | `docs/archive/reference/data-model.md` | 历史数据模型参考，需晚于 current docs 阅读 |
