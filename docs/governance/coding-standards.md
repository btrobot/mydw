# Coding Standards

> Version: 1.0.0  
> Updated: 2026-04-16  
> Scope: repo-wide engineering conventions  
> Related: `AGENTS.md`, `docs/dev-guide.md`, `refactor-docs/架构与工程约束.md`

---

## 1. 文档定位

这份文档是**长期工程规范**，应放在 `docs/`，而不是 `refactor-docs/`。

原因：

- `docs/` 适合长期有效、跨阶段复用的规范；
- `refactor-docs/` 更适合当前重构/设计阶段的专题文档；
- 编码规范属于持续生效的工程基线，不应被视为一次性重构产物。

---

## 2. 术语与命名

默认使用以下产品术语：

- **本地业务后端**：`backend/`
- **产品控制后台**：`remote/remote-backend`
- **产品管理后台**：`remote/remote-admin`
- **桌面工作台**：Electron + `frontend/`

说明：

- `remote` 可作为实现目录名保留；
- 在 PRD、设计文档、代码注释、提交说明中，优先使用产品术语，而不是把 `remote` 当产品名称。

---

## 3. 通用编码原则

1. **先复用，再新增**
   - 优先复用已有 service、hook、schema、组件和 util。
2. **单一职责**
   - route、service、model、schema、page 不混写职责。
3. **显式优于隐式**
   - 状态流转、错误码、兼容回退都要写清楚。
4. **兼容边界集中**
   - legacy 字段、兼容 API、fallback 逻辑应集中收口，不能散落。
5. **避免 silent fallback**
   - 尤其是发布、合成、授权、版本切换等关键流程，不能静默降级。
6. **面向真相源编码**
   - 新代码必须围绕 canonical source，而不是旧字段习惯。

---

## 4. 前端规范

## 4.1 技术约束

- React + TypeScript strict
- Ant Design 作为主 UI 组件库
- React Query 负责服务端状态
- 优先通过生成的 API client 调接口

## 4.2 页面层规范

页面负责：

- 视图展示
- 收集输入
- 调用 hooks
- 组织交互状态

页面不负责：

- 复杂业务编排
- 直接访问底层执行器
- 直接拼装远程/本地双重真相

## 4.3 Hook 规范

- 一个 hook 聚焦一个资源域或一个动作域
- 命名统一 `useXxx`
- mutation/query 错误处理风格保持一致
- 不在 hook 中写复杂 UI 文案判断

## 4.4 组件规范

- 通用组件放 `src/components`
- 页面私有交互优先靠近页面放置
- 避免“超大万能组件”
- Props 要类型明确，避免 `any`

## 4.5 状态与路由规范

- 业务主视图逐步围绕“作品”展开
- `Task` 页面保留执行视角，不继续扩展成业务主视图
- 新增重要页面时，路由命名应体现领域概念，而不是临时实现细节

---

## 5. 本地业务后端规范

## 5.1 Route 规范

`backend/api/*` 只做：

- 参数接收
- 基础校验
- 调用 service
- 返回 schema

禁止：

- 在 route 中堆大段业务逻辑
- 在 route 中直接写复杂数据库编排
- 在 route 中拼接临时返回结构绕过 schema

## 5.2 Service 规范

`backend/services/*` 负责：

- 业务编排
- 状态流转
- 真相源读写
- 错误与兼容边界收口

要求：

- 一个 service 文件聚焦一个领域或一个流程
- 关键状态流转要有日志
- 高风险分支要有明确异常语义

## 5.3 Schema 规范

- API contract 统一走 Pydantic schema
- ORM model 不直接暴露为 API 契约
- 新接口必须有明确 request/response schema
- 兼容字段要在 schema 描述里标清楚

## 5.4 Model 规范

- 数据持久化结构统一走 SQLAlchemy model
- 新增模型前先确认是否已有等价领域对象
- 不要把“临时 JSON 字段”当长期主结构，除非文档已明确保留策略

---

## 6. 产品控制后台规范

## 6.1 职责约束

产品控制后台只负责：

- 用户
- 授权
- License / entitlement
- 设备
- session
- 版本门禁
- 管理后台与审计

禁止：

- 承接本地重媒体业务执行
- 直接接管本地素材/作品/任务主数据真相

## 6.2 契约约束

- auth / admin / self-service 错误码语义必须稳定
- 关键字段命名不能随意漂移
- 涉及本地联动的字段变化必须先评估兼容性

---

## 7. 状态机与领域语义规范

## 7.1 Task 语义

- `Task` authoritative model 是资源集合模型
- 新代码围绕 `video_ids / copywriting_ids / cover_ids / audio_ids / topic_ids`
- 不得重新把 legacy 单资源 FK 当主语义

## 7.2 作品语义

- 作品是业务主对象
- 版本是内容快照
- 检查和发布都绑定版本
- 发布池只接纳被确认可发布的当前版本

## 7.3 Direct publish 语义

当前必须遵守保守模式：

- 1 个最终视频
- 0/1 个文案
- 0/1 个封面
- 独立音频不能 direct publish
- 不允许静默选第一个素材发布

---

## 8. 日志、错误与可观测性规范

- 后端统一用 `loguru`，不使用随意 `print`
- 用户可见错误与内部诊断错误分层处理
- 错误码要稳定、可搜索、可归因
- 授权、调度、发布、合成、版本切换等关键链路必须有日志

---

## 9. 文档与代码同步规范

以下变化必须同步更新文档：

- 核心架构分层变化
- 真相源变化
- 状态机变化
- API contract 变化
- 重要术语变化

优先更新：

- `refactor-docs/架构与工程约束.md`
- 对应 PRD / 详细设计文档
- `docs/current-runtime-truth.md`（若 runtime truth 变化）
- ADR（若属于架构决策）

---

## 10. 提交与变更要求

- 提交信息遵循 Lore Commit Protocol
- 重要设计变更先写文档再改代码，或代码与文档同 PR 提交
- 新增依赖、状态机变化、真相源变化必须在说明中写清动机与边界

---

## 11. 一句话定义

> 这份文档约束的是“代码应该怎么写、系统应该怎么持续演进”：围绕真相源、职责边界、稳定契约和长期可维护性来实现，而不是围绕临时方便和局部捷径来实现。
