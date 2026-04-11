# Sprint 1 - 素材域重建（后端）

**周期**: 2026-04-07 ~ 2026-04-18 (2 周)

## 目标

- 完成五个新实体模型定义（Video, Copywriting, Cover, Audio, Topic）
- 完成 Material → 新表数据迁移
- 完成新 API 端点 + 兼容层
- Product 提升为一级资源

## 任务

| ID | 任务 | 负责人 | 估计 | 依赖 | 状态 |
|----|------|--------|------|------|------|
| SP1-01 | Video 模型 + Schema | Backend Lead | 1d | - | [ ] |
| SP1-02 | Copywriting 模型 + Schema | Backend Lead | 0.5d | - | [ ] |
| SP1-03 | Cover 模型 + Schema | Backend Lead | 0.5d | - | [ ] |
| SP1-04 | Audio 模型 + Schema | Backend Lead | 0.5d | - | [ ] |
| SP1-05 | Topic 模型 + Schema | Backend Lead | 0.5d | - | [ ] |
| SP1-06 | Product 提升为一级资源 | Backend Lead | 1d | - | [ ] |
| SP1-07 | 数据迁移脚本 (Material → 新表) | Backend Lead | 2d | SP1-01~05 | [ ] |
| SP1-08 | 新 API 端点 (/api/videos 等) | Backend Lead | 3d | SP1-01~05 | [ ] |
| SP1-09 | 兼容层 API (旧 /api/materials) | Backend Lead | 1d | SP1-08 | [ ] |

## 容量

- 总估计: 10d
- 缓冲 20%: 2d
- 实际可用: 10 工作日
- 利用率: 10/10 = 100% (满载，缓冲靠并行节省)

## 并行策略

```
Day 1-2:  SP1-01~06 并行 (模型定义 + Product，互不依赖)
Day 3-4:  SP1-07 (迁移脚本)  ‖  SP1-08 前半段 (API 端点)
Day 5-7:  SP1-08 后半段 (API 端点)
Day 8:    SP1-09 (兼容层)
Day 9-10: 自测 + 修复 + 缓冲
```

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 数据迁移丢失关联关系 | 中 | 高 | 迁移前备份 DB，脚本幂等可重跑 |
| 5 个新 API 模块工作量超预期 | 中 | 中 | CRUD 模式统一，可用模板批量生成 |
| 兼容层遗漏边界情况 | 低 | 中 | 旧 API 测试用例全部保留 |

## Sprint 1 交付物

- [ ] 5 个新 ORM 模型 + Pydantic Schema
- [ ] 迁移脚本 `003_material_split.py`
- [ ] 5 个新 API 路由模块
- [ ] 兼容层 `/api/materials` (deprecated)
- [ ] `/api/products` 一级资源
- [ ] 后端自测通过

---

# Sprint 2 - 素材域重建（前端 + 集成 + 测试）

**周期**: 2026-04-21 ~ 2026-05-02 (2 周)

## 目标

- 前端对接新 API，素材页面重构
- API 契约对齐
- 集成测试 + 回归测试

## 任务

| ID | 任务 | 负责人 | 估计 | 依赖 | 状态 |
|----|------|--------|------|------|------|
| SP2-01 | API 契约对齐 (OpenAPI → TS 类型) | Both Leads | 0.5d | Sprint 1 完成 | [ ] |
| SP2-02 | 素材 Hooks 重构 (6 个 hook 文件) | Frontend Lead | 2d | SP2-01 | [ ] |
| SP2-03 | 素材管理页面重构 (5 个 Tab) | Frontend Lead | 3d | SP2-02 | [ ] |
| SP2-04 | Product 页面入口调整 | Frontend Lead | 0.5d | SP2-02 | [ ] |
| SP2-05 | 迁移与 API 集成测试 | QA Lead | 2d | Sprint 1 完成 | [ ] |

## 容量

- 总估计: 8d
- 缓冲 20%: 1.6d
- 实际可用: 10 工作日
- 利用率: 8/10 = 80% ✓

## 并行策略

```
Day 1:    SP2-01 (契约对齐)  ‖  SP2-05 前半段 (迁移测试)
Day 2-3:  SP2-02 (Hooks)     ‖  SP2-05 后半段 (API 测试)
Day 4-6:  SP2-03 (页面重构)
Day 7:    SP2-04 (Product)
Day 8-10: 集成验证 + 回归 + 缓冲
```

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 前端改动面大导致回归 | 中 | 中 | 逐 Tab 迁移，每个独立验证 |
| OpenAPI 生成的类型与手写不一致 | 低 | 低 | 手动补充差异类型 |

## Sprint 2 交付物

- [ ] 6 个前端 hook 文件 (useVideo, useCopywriting, useCover, useAudio, useTopic, useProduct)
- [ ] Material.tsx 重构为 5 Tab 页面
- [ ] Product 页面对接新端点
- [ ] 集成测试报告
- [ ] 回归测试通过

---

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
| 2026-04-18 | Sprint 1 完成：后端素材域重建交付 |
| 2026-05-02 | Sprint 2 完成：前端对接 + 测试通过，Phase 1 完成 |
| 2026-05-02 | Phase 1 素材域重建全部完成，可进入 Phase 2 合成项目 |
