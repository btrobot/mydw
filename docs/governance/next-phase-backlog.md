# 下一阶段 Backlog（Next-Phase Backlog）

> Version: 1.0.0 | Updated: 2026-04-21  
> Owner: Tech Lead / Codex  
> Status: Active working backlog

> 目的：把当前散落在 closeout summary、audit、旧计划和专题问题文档里的未决事项压缩成一个真正可消费的 backlog。

## 1. 当前基线：已经收口了什么

在进入下一阶段前，下面这些基线已经完成：

- 文档入口收口：`README.md`、`docs/README.md`、`docs/current/architecture.md`
- 当前真相收口：`docs/current/runtime-truth.md`
- 启动协议收口：`docs/guides/dev-guide.md`、`docs/guides/startup-protocol.md`
- 验证基线收口：`docs/governance/verification-baseline.md`
- Creative A~D 主线完成：`docs/domains/creative/progressive-rebuild-completion-audit.md`
- auth Step 5 完成：`docs/domains/auth/step5-completion-audit.md`

因此，下一阶段不再需要继续讨论“主路径是不是 Creative-first”“remote auth 是否已经接上”这类已完成问题，而是集中处理**还没彻底收口的体验、技术债与文档债**。

## 2. 压缩后的未决问题清单

## 2.1 产品 / UI 层

来源：

- `docs/frontend-ui-issues-and-improvements.md`
- `docs/frontend-ui-ux-closeout-final-summary.md`

压缩结果：

1. **Workbench 还缺真正可管理能力**
   - 缺搜索、筛选、排序、分页
   - 作品量一大就会从“能浏览”退化成“难以管理”
2. **业务层与诊断层仍有混放**
   - workbench / detail 还暴露较多 scheduler / pool / shadow / kill-switch 诊断信息
3. **文案、状态反馈与页面层级还不够一致**
   - 中英混搭
   - 存在坏文案
   - loading / empty / error / success 四态不统一
4. **AIClip 仍偏工程工具面板**
   - 路径输入、低层参数、产品主 CTA 仍不够清晰

## 2.2 架构 / 平台层

来源：

- `docs/domains/creative/progressive-rebuild-completion-audit.md`
- `docs/domains/auth/step5-completion-audit.md`

压缩结果：

1. **框架 deprecation 仍未清理**
   - FastAPI `on_event(...)`
   - `datetime.utcnow()`
2. **运行时安全 / 环境警告仍未完全收口**
   - 默认 `COOKIE_ENCRYPT_KEY` 等 warning 仍是非阻塞项
3. **generated client / 手写请求边界仍有例外**
   - SSE、connect flow、媒体流 URL 仍有手写路径

## 2.3 文档 / 信息架构层

来源：

- `docs/governance/inventory/root-doc-triage.md`
- `docs/governance/inventory/inventory-ledger.md`

压缩结果：

1. `docs/` 根目录仍有一批**位置错误但内容未完全失效**的文档
2. requirements source、治理清单、domain note、historical closeout 还混在同一层
3. 下一阶段开发虽然已有启动/验证基线，但**未决问题入口**此前仍然不够集中

## 3. Open Questions

这些问题会影响下一阶段实施顺序，应该在 kickoff 时先明确：

1. **下一阶段主线是 UI/UX 收口，还是 AIClip 产品化？**
   - 当前证据更支持先做 UI/UX 收口，再做更深的 workflow 产品化
2. **Coze 方向是否仍然有 owner？**
   - 若没有，应把 `docs/coze-integration.md` 视为 archive，而不是继续保留为隐性 roadmap
3. **Task 页面是否继续保留为诊断/执行层，还是再向下沉？**
   - 当前共识是“Task 不是业务真相”，但是否继续保留现有入口需要下一阶段明确
4. **requirements source 是否需要做一次编码/清洗？**
   - `init-req.md`、`chat-req.md` 仍被引用，但当前可读性较差

## 4. 下一阶段 backlog（按优先级）

## P0 — 下一阶段第一主线

### P0.1 Creative Workbench 可用性收口

目标：

- 增加搜索 / 状态筛选 / 排序 / 分页
- 建立更稳定的日常工作台视图

为什么优先：

- 这是当前最直接影响“继续开发是否顺手”的问题
- 已有功能主路径基本成型，但管理体验还没收口

完成标志：

- workbench 在 50+ creative 场景下仍可管理
- 常见待处理状态可一眼定位

### P0.2 业务层 vs 诊断层彻底分层

目标：

- 默认业务层只保留主信息和主操作
- 将 scheduler / shadow / pool diagnostics 下沉到高级诊断层

为什么优先：

- 当前很多页面还带“验收台/诊断台”气质
- 不先分层，后续 UI/UX 与产品化改造会持续互相干扰

完成标志：

- `CreativeWorkbench` / `CreativeDetail` 默认视图不再承担过量工程诊断信息

### P0.3 文案与四态统一

目标：

- 统一中文主文案策略
- 修坏文案
- 核心页统一 loading / success / empty / error 四态

为什么优先：

- 这是最低成本、最高感知的稳定化动作

完成标志：

- auth / workbench / detail / dashboard 主页面四态一致
- 不再依赖 Alert 解释页面职责

## P1 — 紧随其后的主线

### P1.1 AIClip workflow 产品化

目标：

- 用素材选择器替代路径输入
- 引入模板 / 预设 / 结果预览
- 明确“提交为新版本”为主 CTA

前置依赖：

- 最好在 P0 完成后推进，否则会把产品化工作继续堆在过渡期 UI 上

### P1.2 generated client / manual exception 收口

目标：

- 逐项复核 `docs/manual-axios-exceptions.md` 中的例外
- 明确哪些场景永久保留、哪些需要迁回 generated client wrapper

### P1.3 requirements / root docs 下沉执行

目标：

- 按 `docs/governance/inventory/root-doc-triage.md` 执行实际 move/archive/delete
- 减少根层噪音

## P2 — 技术债 / 治理债

### P2.1 FastAPI / datetime deprecation cleanup

### P2.2 runtime security / env warnings cleanup

### P2.3 remote 发布治理自动化继续补强

说明：

- 这些问题重要，但当前不比 P0 的日常开发摩擦更紧急

## 5. 建议的执行顺序

推荐下一阶段按下面顺序推进：

1. **UI/UX 收口主线**
   - Workbench 可管理性
   - 业务/诊断分层
   - 文案与四态统一
2. **再进入 AIClip 产品化**
3. **并行做文档根层下沉**
4. **最后清理平台级 deprecation / warning**

## 6. 一句话结论

下一阶段最应该做的，不是继续扩新页面或再开一条大主线，而是：

> **把已经跑通的 Creative-first 系统，从“可验证的过渡态”收口成“可持续开发、可持续使用的稳定基线”。**
