# Sprint 3 - 任务编排层重构

**周期**: 2026-04-07 ~ 2026-04-18 (2 周)

## 目标

- Task 模型增加素材 FK 引用（双写过渡）
- 实现 TaskAssembler + TaskDistributor 领域服务
- 发布服务适配新 FK
- 前端任务页重构（组装任务 + 多账号分配）

## 任务

| ID | 任务 | 负责人 | 估计 | 依赖 | 状态 |
|----|------|--------|------|------|------|
| SP3-01 | Task 增加素材 FK + 迁移脚本 | Backend Lead | 1d | - | [ ] |
| SP3-02 | TaskTopic 多对多关联表 | Backend Lead | 0.5d | - | [ ] |
| SP3-03 | Task 数据迁移（旧字段→FK） | Backend Lead | 2d | 01,02 | [ ] |
| SP3-04 | TaskAssembler 领域服务 | Backend Lead | 1.5d | 01,02 | [ ] |
| SP3-05 | TaskDistributor 领域服务 | Backend Lead | 1d | 04 | [ ] |
| SP3-06 | 发布服务适配（FK优先+fallback） | Backend Lead | 1d | 01 | [ ] |
| SP3-07 | 任务 API 重构 (/tasks/assemble) | Backend Lead | 1.5d | 05,06 | [ ] |
| SP3-08 | API 契约对齐 | Both Leads | 0.5d | 07 | [ ] |
| SP3-09 | 任务 Hooks 更新 | Frontend Lead | 1d | 07 | [ ] |
| SP3-10 | 任务页面重构 | Frontend Lead | 2d | 09 | [ ] |
| SP3-11 | 编排集成测试 | QA Lead | 1.5d | 06,07 | [ ] |

## 容量

- 总估计: 13.5d
- 缓冲 20%: 2.7d
- 实际可用: 10 工作日
- 并行节省: 后端任务大量并行，前端/测试与后端错开

## 并行策略

```
Day 1:    SP3-01 + SP3-02 并行
Day 2-3:  SP3-03 ‖ SP3-04 ‖ SP3-06 (三路并行)
Day 4:    SP3-05 (依赖04)
Day 5-6:  SP3-07 (依赖05+06)
Day 7:    SP3-08 (契约对齐) ‖ SP3-11 前半段 (测试)
Day 8:    SP3-09 (hooks)    ‖ SP3-11 后半段
Day 9-10: SP3-10 (页面重构) + 缓冲
```

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 旧字段→FK 匹配失败 | 中 | 高 | 模糊匹配 + 手动修复兜底 |
| 双写期数据不一致 | 中 | 中 | 写入同步新旧字段，读取优先新字段 |
| 发布服务改动中断发布 | 中 | 高 | fallback 旧字段，渐进切换 |

## 交付物

- [ ] Task 模型 FK 字段 + TaskTopic 关联表
- [ ] 迁移脚本 005, 006
- [ ] TaskAssembler + TaskDistributor 服务
- [ ] POST /api/tasks/assemble 端点
- [ ] 发布服务 FK 优先读取
- [ ] 前端任务页重构（组装任务 + 多账号选择）
- [ ] 集成测试通过

## 质量检查

- [x] Sprint 周期合理（2 周）
- [x] 任务可分解到 1-3 天完成
- [x] 所有任务有明确负责人
- [x] 依赖关系已识别并记录
- [x] 缓冲容量 ≥ 20%
- [x] 风险已识别并有缓解策略
- [x] 容量计算正确

## 里程碑

| 日期 | 里程碑 |
|------|--------|
| Day 6 | 后端全部完成，API 可用 |
| Day 10 | 前端 + 测试完成，Sprint 3 交付 |
| Sprint 3 后 | Phase 3 完成，可进入 Phase 4（话题增强） |
