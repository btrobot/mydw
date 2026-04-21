# Release Hardening 尾项清理记录（PR-1）

> 日期：2026-04-20  
> 对应规划：`.omx/plans/archive/prd-release-hardening-runtime-acceptance-closeout.md`  
> 范围：仅处理当前工作区中的非规划尾项与提交边界，不包含功能实现。

---

## 1. 背景

在主线 A~D、Phase E 与 `local_ffmpeg` 补齐计划完成后，工作区仍残留一批未归位文件：

- `AGENTS.md`
- `ana-docs/task-state-machine-and-composition-analysis.md`
- `dev-docs/`
- `docs/collector/page.html`

这些文件本身并不等于“主线未完成”，但若长期悬空，会让后续 runtime acceptance 与 release closeout 的提交边界变得模糊。

---

## 2. 处理结论

### A. `AGENTS.md`

**结论：保留并纳入本次提交。**

保留原因：

- 其中新增的是一条长期有效的流程规则：
  - 用户已批准的 slice / PR，在实现并验证后自动按 Lore 规范提交；
- 这条规则已在最近多轮执行中被反复使用，属于正式工作约定，而不是一次性临时指令。

### B. `ana-docs/task-state-machine-and-composition-analysis.md`

**结论：删除，不纳入仓库。**

原因：

- 该分析是在用户后续澄清前提认知之前生成的；
- 用户已明确要求“撤回前面创建的文档，免得造成误解”；
- 因而不应作为正式分析文档继续留在工作区。

### C. `dev-docs/`

**结论：保留内容，但迁移到归档区。**

迁移路径：

- `docs/archive/dev-docs/login-ux-closeout/`

包含文件：

- `auth-state-machine.md`
- `auth-vs-account-connect.md`
- `login-sequence.md`
- `login-step.md`
- `login-ux-recommendations.md`

原因：

- 这些文档来自登录 UI/UX 收口阶段，属于过程性分析与设计支撑材料；
- 保留其内容有价值，但继续挂在仓库根级 `dev-docs/` 下会造成“仍在活跃编辑”的错觉；
- 放入 `docs/archive/dev-docs/` 更符合其“阶段性沉淀资料”的性质。

### D. `docs/collector/page.html`

**结论：删除，不纳入仓库。**

原因：

- 该文件是用于分析 Dewu `__NEXT_DATA__` 的原始页面样本；
- 用户要求的是 schema / 解析文档，而不是原始抓取 HTML 资产入库；
- 作为未治理的原始抓取文件，继续留在 `docs/collector/` 会模糊“正式文档”和“临时样本”的边界。

---

## 3. 本 PR 的提交边界

本 PR 只允许包含：

- `AGENTS.md` 的长期规则修订；
- 登录 UI/UX 阶段文档的归档迁移；
- 尾项清理记录文档；
- 对应的删除动作。

本 PR 明确不包含：

- backend / frontend 功能代码修改；
- runtime acceptance 实施；
- flaky E2E 修复；
- 其他计划外界面或行为调整。

---

## 4. 清理后状态目标

PR-1 完成后，工作区应满足：

1. 不再残留本轮已识别的非规划悬空尾项；
2. 后续 PR-2 可以直接聚焦真实运行验收；
3. 提交边界可清晰表达为“尾项归位与归档”，而非功能开发。

---

## 5. 后续建议

完成本 PR 后，按规划继续进入：

- `PR-2：local_ffmpeg + 随机账号发布真实运行验收`

不要在本 PR 中提前混入 runtime 修复，否则会破坏收口顺序。
