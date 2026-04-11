# Sprint 4 - 话题增强

**周期**: 2026-04-07 ~ 2026-04-18 (2 周)

## 目标

- 实现得物平台话题搜索（Playwright 自动化）
- 全局话题配置 + TaskAssembler 集成
- 前端话题搜索 UI + 全局话题设置

## 任务

| ID | 任务 | 负责人 | 估计 | 依赖 | 状态 |
|----|------|--------|------|------|------|
| SP4-01 | Playwright 话题搜索服务 | Automation Dev | 2d | - | [ ] |
| SP4-02 | 话题搜索 API | Backend Lead | 1d | 01 | [ ] |
| SP4-03 | 全局话题配置 | Backend Lead | 1d | - | [ ] |
| SP4-04 | Assembler 集成全局话题 | Backend Lead | 0.5d | 03 | [ ] |
| SP4-05 | 话题搜索 UI | Frontend Lead | 1.5d | 02 | [ ] |
| SP4-06 | 全局话题设置 UI | Frontend Lead | 1d | 03,05 | [ ] |
| SP4-07 | 集成测试 | QA Lead | 1d | 04 | [ ] |

## 容量

- 总估计: 8d
- 缓冲 20%: 1.6d
- 实际可用: 10 工作日
- 利用率: 80% ✓

## 并行策略

```
Day 1-2:  SP4-01 (Playwright搜索) ‖ SP4-03 (全局话题配置)
Day 3:    SP4-02 (搜索API)        ‖ SP4-04 (Assembler集成)
Day 4-5:  SP4-05 (搜索UI)         ‖ SP4-07 (测试)
Day 6:    SP4-06 (全局设置UI)
Day 7-10: 集成验证 + 缓冲
```

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 得物话题页面结构变化 | 中 | 高 | 多 fallback 选择器 |
| 搜索需要登录态 | 低 | 中 | 先验证公开接口 |

## 交付物

- [ ] Playwright 话题搜索服务
- [ ] GET /api/topics/search 端点
- [ ] 全局话题 CRUD API
- [ ] TaskAssembler 自动关联全局话题
- [ ] 前端话题搜索 + 全局设置 UI
- [ ] 集成测试通过

## 里程碑

| 日期 | 里程碑 |
|------|--------|
| Day 3 | 后端 API 全部可用 |
| Day 6 | 前端 UI 完成 |
| Day 10 | Phase 4 完成，全部 4 个 Phase 交付（Phase 2 除外） |
