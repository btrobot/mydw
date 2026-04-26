# 技术债 Roadmap

> 更新：2026-04-25  
> 来源：代码库静态分析 + git 历史 + discss/ 文档审读

---

## 债务总图

```
优先级 高 ────────────────────────────────────────── 低
影响大 │  [1] creative_service.py 拆分              │
       │  [2] CreativeDetail.tsx 重构（进行中）      │
影响中 │  [3] 迁移模式文档化                         │
       │  [4] account.py 路由/服务分离               │
影响小 │  [5] runtime-truth.md 补完                  │
       │  [6] .codex/ 插件缓存清理（1.1 GB）          │
       └──────────────────────────────────────────── ┘
```

---

## P1 — 应尽快处理

### [1] creative_service.py 拆分

| 属性 | 值 |
|------|----|
| 文件 | `backend/services/creative_service.py` |
| 现状 | 3,254 行，包含 workbench 列表、详情、创建/更新、投稿、版本管理、review 流 |
| 风险 | 调试定位慢；测试边界模糊；并发修改冲突概率高 |
| 是否阻塞功能 | 否，但会拖慢迭代速度 |

**建议拆分方式：**

```
creative_service.py  →  workbench_service.py      # 列表、过滤、candidate pool 状态
                         creative_authoring_service.py  # CRUD、投稿、payload 校验
                         creative_review_service.py     # review 流程、状态机
                         creative_version_service.py    # 版本管理、快照
```

保持统一入口（`__init__.py` 导出），避免改调用方。

**前置条件：**
- 先确保 `test_creative_api.py` 覆盖现有所有行为
- 拆分前写 characterization tests 锁住接口

---

### [2] CreativeDetail.tsx 重构（进行中）

| 属性 | 值 |
|------|----|
| 文件 | `frontend/src/features/creative/pages/CreativeDetail.tsx` |
| 现状 | 2,228 行；P0 gap closure ralplan 已在 2026-04-25 生成 |
| 风险 | 模式耦合；难以独立测试；多人修改冲突 |
| 状态 | **主动重构中** — 参见 `discss/specs/creative-detail-p0-gap-closure-*.md` |

**当前 P0 目标（按 ralplan）：**
1. 确保第一屏显示正确的 next action
2. 锁定模式防止 pending/published 版本被意外变更
3. 提交流程验证正确（mode-correct）
4. OMX-native closure loop 对齐

**后续重构方向（P0 完成后）：**
```
CreativeDetail.tsx  →  CreativeDetailShell.tsx       # 路由 + 加载状态
                        CreativeAuthoringPanel.tsx   # 编辑区域
                        CreativeReviewPanel.tsx      # 审核区域
                        CreativePublishPanel.tsx     # 发布区域
                        hooks/useCreativeDetail.ts   # 状态逻辑提取
```

---

## P2 — 近期排上日程

### [3] 数据库迁移模式文档化

| 属性 | 值 |
|------|----|
| 位置 | `backend/migrations/`（无 README） |
| 问题 | 自定义 `async def run_migration(engine)` 模式，无模板、无 rollback 说明 |
| 影响 | 新开发者写迁移容易出错（漏幂等检查、漏注册） |

**需要创建 `backend/migrations/README.md`，包含：**
- 模式说明（为何不用 Alembic）
- 完整模板（含幂等检查）
- 如何注册新迁移
- rollback 手动流程（SQLite 不支持 DDL 回滚，需备份策略）
- 命名约定：`NNN_<intent>.py`

---

### [4] account.py 路由/服务分离

| 属性 | 值 |
|------|----|
| 文件 | `backend/api/account.py`（1,767 行） |
| 问题 | 混合了 UI 传输逻辑（HTTP 处理）和域操作（browser automation、material sync） |
| 建议 | 将连接流、材料同步提取到 `account_connection_service.py` |
| 优先级 | 低于 creative_service；账号域不是当前开发热点 |

---

## P3 — 维护级

### [5] runtime-truth.md 补完

| 属性 | 值 |
|------|----|
| 文件 | `docs/current/runtime-truth.md`（112 行，内容偏稀疏） |
| 缺失 | 完整 schema 事实矩阵、API endpoint 稳定性标记、序列化规则 |
| 影响 | 新人上手需要读更多代码才能理解数据流 |

---

### [6] .codex/ 插件缓存清理

```bash
# 安全清理，不影响代码库
rm -rf .codex/.tmp/plugins/   # ~1.1 GB，可重新缓存
```

`.codex/` 整体可清理（会话历史 ~1.8 GB），清理后 Claude Code 重新初始化即可。

---

## 不是技术债的项目

以下是**刻意选择**，不需要"修复"：

| 项目 | 理由 |
|------|------|
| SQLite 而非 PostgreSQL | 单机桌面工具，SQLite 是正确选择 |
| 自定义迁移模式而非 Alembic | SQLite + async 环境；自定义模式足够简单且已证明有效 |
| 前端无单元测试（只有 E2E） | UI 重组件 + Electron 环境，E2E 是更高价值的验证手段 |
| creative_service.py 大但未拆 | 域复杂度确实高；强行拆分可能引入协调复杂度 |
| discss/ 文件多 | 这是工作日志，不是代码；文件多说明工作量有记录 |

---

## 债务跟踪建议

从 OMX 切换到 Claude Code 后，原来在 `.omx/plans/` 和 AGENTS.md roadmap
里追踪的债务，建议迁移到：

1. **GitHub Issues**（推荐）：每个债务项一个 issue，标 `tech-debt` label
2. **discss/ 积压文档**：`discss/tech-debt-backlog.md`，按优先级排序
3. **根 CLAUDE.md 的 "Known Issues" 节**：只放影响日常工作的最高优先级项

不建议在代码里用 TODO/FIXME 追踪——当前项目已经证明这个纪律有效，保持即可。
