# Phase 4 话题增强 — 任务分解

> 日期: 2026-04-07
> 来源: `docs/requirements-spec.md` 4.1, `docs/domain-model-analysis.md` Phase 4
> 范围: 话题搜索(Playwright自动化) + 热度排序 + 全局话题 + 前端话题管理UI

---

## 功能概述

当前 Topic 模型已有 name/heat/source/last_synced 字段，但只支持手动添加。需要实现：
1. 从得物平台搜索话题（通过 Playwright 自动化）
2. 获取话题热度并排序
3. "全局话题"概念：选定的话题自动应用到后续所有任务
4. 前端话题搜索和批量设置 UI

## 参与者

| 角色 | 职责 |
|------|------|
| Automation Developer | Playwright 话题搜索爬取 |
| Backend Lead | 搜索 API + 全局话题配置 |
| Frontend Lead | 话题搜索 UI + 全局话题设置 |
| QA Lead | 集成测试 |

## 依赖关系图

```
BE-P4-01 (Playwright搜索) → BE-P4-02 (搜索API) → FE-P4-01 (搜索UI)
BE-P4-03 (全局话题配置)  → BE-P4-04 (Assembler集成) → FE-P4-02 (全局设置UI)
                                                              │
                                                       TEST-P4-01
```

---

## 后端任务

### BE-P4-01: Playwright 话题搜索服务

**描述**: 在 dewu_client.py 或新建 topic_service.py 中实现从得物创作者平台搜索话题

**验收标准**:
- [ ] `search_topics(keyword: str) -> List[dict]` 返回 [{name, heat}]
- [ ] 通过 Playwright 访问得物话题搜索页面
- [ ] 解析搜索结果：话题名称 + 热度值
- [ ] 超时处理（10秒）
- [ ] 无需登录即可搜索（公开接口）

**估计**: 2d
**负责人**: Automation Developer
**依赖**: -
**类型**: backend

---

### BE-P4-02: 话题搜索 API

**描述**: 新增 GET /api/topics/search?keyword=xxx 端点

**验收标准**:
- [ ] GET /api/topics/search?keyword=得物 → 返回话题列表（含热度）
- [ ] 搜索结果自动入库（source="search"，更新 heat 和 last_synced）
- [ ] 已存在的话题更新热度，不重复创建
- [ ] Schema: TopicSearchResponse(items: List[TopicResponse])

**估计**: 1d
**负责人**: Backend Lead
**依赖**: BE-P4-01
**类型**: backend

---

### BE-P4-03: 全局话题配置

**描述**: 新增"全局话题"概念，选定的话题自动应用到后续所有任务

**验收标准**:
- [ ] 新增 GlobalTopicConfig 模型或在 PublishConfig 中增加 global_topic_ids(JSON) 字段
- [ ] PUT /api/topics/global — 设置全局话题 ID 列表
- [ ] GET /api/topics/global — 获取当前全局话题
- [ ] Schema: GlobalTopicRequest(topic_ids: List[int]), GlobalTopicResponse

**估计**: 1d
**负责人**: Backend Lead
**依赖**: -
**类型**: backend

---

### BE-P4-04: TaskAssembler 集成全局话题

**描述**: TaskAssembler 组装任务时自动关联全局话题

**验收标准**:
- [ ] assemble() 读取全局话题配置
- [ ] 创建 TaskTopic 记录关联全局话题
- [ ] 双写旧字段 task.topic = 全局话题名称拼接

**估计**: 0.5d
**负责人**: Backend Lead
**依赖**: BE-P4-03
**类型**: backend

---

## 前端任务

### FE-P4-01: 话题搜索 UI

**描述**: 在素材管理的话题 Tab 中增加搜索功能

**验收标准**:
- [ ] 搜索输入框 + 搜索按钮
- [ ] 搜索结果列表：话题名称 + 热度标签 + "添加"按钮
- [ ] 搜索结果可一键添加到话题库
- [ ] 话题列表支持按热度排序

**估计**: 1.5d
**负责人**: Frontend Lead
**依赖**: BE-P4-02
**类型**: frontend

---

### FE-P4-02: 全局话题设置 UI

**描述**: 在设置页或话题 Tab 中增加全局话题管理

**验收标准**:
- [ ] 显示当前全局话题列表（Tag 形式）
- [ ] 从话题库中选择/取消全局话题（多选）
- [ ] 保存后调用 PUT /api/topics/global
- [ ] 提示"后续所有任务将自动带上这些话题"

**估计**: 1d
**负责人**: Frontend Lead
**依赖**: BE-P4-03, FE-P4-01
**类型**: frontend

---

## 测试任务

### TEST-P4-01: 话题增强集成测试

**描述**: 验证话题搜索、全局话题、任务关联全流程

**验收标准**:
- [ ] test_search_topics — 搜索 API 返回结果并入库
- [ ] test_global_topics_crud — 设置/获取全局话题
- [ ] test_assemble_with_global_topics — 组装任务自动关联全局话题

**估计**: 1d
**负责人**: QA Lead
**依赖**: BE-P4-04
**类型**: both

---

## 任务汇总

| ID | 任务 | 负责人 | 估计 | 依赖 | 类型 |
|----|------|--------|------|------|------|
| BE-P4-01 | Playwright 话题搜索 | Automation Dev | 2d | - | BE |
| BE-P4-02 | 话题搜索 API | Backend Lead | 1d | 01 | BE |
| BE-P4-03 | 全局话题配置 | Backend Lead | 1d | - | BE |
| BE-P4-04 | Assembler 集成全局话题 | Backend Lead | 0.5d | 03 | BE |
| FE-P4-01 | 话题搜索 UI | Frontend Lead | 1.5d | BE-02 | FE |
| FE-P4-02 | 全局话题设置 UI | Frontend Lead | 1d | BE-03, FE-01 | FE |
| TEST-P4-01 | 集成测试 | QA Lead | 1d | BE-04 | both |

## 统计

| 维度 | 值 |
|------|-----|
| 后端任务 | 4 个, 4.5d |
| 前端任务 | 2 个, 2.5d |
| 测试任务 | 1 个, 1d |
| **总计** | **7 个, 8d** |
| 缓冲 20% | 1.6d |
| **含缓冲** | **~10d** |

## 关键路径

```
BE-P4-01 (2d) → BE-P4-02 (1d) → FE-P4-01 (1.5d) → FE-P4-02 (1d) → TEST-P4-01 (1d)

关键路径: 2 + 1 + 1.5 + 1 + 1 = 6.5d
```

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 得物话题搜索页面结构变化 | 中 | 高 | 选择器用多个 fallback，定期验证 |
| 搜索需要登录态 | 低 | 中 | 先验证公开接口，需要时用已登录账号 |
| 热度值解析格式不一致 | 低 | 低 | 统一转为整数，异常值默认0 |
