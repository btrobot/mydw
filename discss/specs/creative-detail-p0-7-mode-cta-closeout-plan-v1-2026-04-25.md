# 《CreativeDetail P0-7 页面模式 / 头部 CTA 收口计划 v1》

日期：2026-04-25  
对应切片：Slice P0-7

---

## 1. 目标

在当前 P0-6 基础上，继续收口 CreativeDetail 首屏最核心的“主任务表达”问题：

- 让头部状态语言更贴近当前页面模式
- 让主 CTA 跟随当前模式变化
- 弱化首屏上的并列强动作，避免再次滑回“总控页”

---

## 2. 本次范围

### 纳入

- 基于当前 `creative.status` / `projection.pageMode` 派生首屏模式文案
- Hero 主 CTA / 次 CTA 随模式变化
- 头部摘要在“结果待确认 / 发布跟进”时改用结果状态语言，而不是继续用 readiness 语言硬套
- 弱化顶部低频动作的强度，避免和主 CTA 并列抢焦点
- 增加对应 E2E

### 不纳入

- 大范围只读 / 锁定权限切换
- 新的后端字段
- 发布流程的真实新动作（如真正发起发布）
- 版本确认机制本身的领域改造

---

## 3. 为什么现在做

前面 P0-2 ~ P0-6 已把：

- 页面骨架
- A/B/C 联动
- 视频高频编排

基本搭出来了。

但如果头部仍然：

- readiness 语言和当前模式不一致
- 主 CTA 不跟随模式变化
- 高级动作与主动作并列过强

用户仍会感觉“这页主任务不清楚”。

所以 P0-7 的核心不是加新功能，而是：

> **把首屏主任务表达真正拉直。**

---

## 4. 实现策略

### 4.1 新增前端 mode summary

前端先做一层轻量 mode summary，把现有状态翻译为首屏语言：

- `authoring`
- `reviewing`
- `reworking`
- `publishing`
- `published_followup`
- `submitting`
- `failed_recovery`

### 4.2 Hero 改为“模式感知”

Hero 至少要支持：

- mode label
- 当前模式一句话说明
- 主 CTA label / action
- 次 CTA 集合
- 结果态时切换摘要标题

### 4.3 首屏动作强弱收口

保留原有能力入口，但降低其默认强调级别：

- 高级诊断
- AIClip
- 审核当前版本

避免除主 CTA 外再出现第二个“最强按钮”。

---

## 5. 预计改动文件

- `frontend/src/features/creative/components/detail/CreativeDetailProjection.tsx`
- `frontend/src/features/creative/pages/CreativeDetail.tsx`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`

---

## 6. 验证计划

- `pnpm typecheck`
- Playwright 定向验证：
  - reviewing 态主 CTA 改为审核语义
  - authoring 态主 CTA 仍保持保存/提交语义
  - 顶部额外动作不再出现额外 primary 按钮

---

## 7. 风险提示

- 这是“首屏表达收口”，不是完整锁定态切换；不要在本 Slice 里顺手扩大到整页读写权限治理
- 需要兼容既有测试和既有按钮 testid，避免无意义回归

