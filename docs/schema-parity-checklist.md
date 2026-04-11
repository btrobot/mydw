# Phase 3 / PR1 — Frozen Schema Parity Checklist

> 目的：冻结本轮准备进入 OpenAPI regeneration 之前的高价值 contract 基线。  
> 本清单完成后，Phase 3 / PR2 才应执行 baseline client regeneration。

## 适用范围

本轮只覆盖高价值域：

- account
- task
- profile
- publish / schedule-config
- system
- topic / topic-group（高价值路径）

## 已对齐项

### Account
- [x] `GET /api/accounts/` OpenAPI 已显式包含：
  - `status`
  - `tag`
  - `search`
- [x] 账号响应仍以 `AccountResponse` 为 authoritative shape
- [x] 预览相关接口已有显式 response schema：
  - `POST /api/accounts/{account_id}/preview`
  - `POST /api/accounts/{account_id}/preview/close`

### Task
- [x] `TaskResponse` authoritative shape 为 collection-based：
  - `video_ids`
  - `copywriting_ids`
  - `cover_ids`
  - `audio_ids`
  - `topic_ids`
- [x] public create contract 为 `TaskCreateRequest`
- [x] legacy 单资源 FK 不再作为 authoritative public contract

### Profile
- [x] `PublishProfileResponse` 已显式表达：
  - `composition_mode`
  - `global_topic_ids`
  - `auto_retry`
  - `max_retry_count`

### Publish / Schedule
- [x] `/api/schedule-config` 已有显式 request/response schema
- [x] `/api/publish/config` 仍是兼容入口，但 contract 已有明确 schema
- [x] `/api/publish/status` 与 control path schema 已稳定

### System
- [x] `GET /api/system/config` 已有显式 response schema
- [x] `PUT /api/system/config` 已有显式 response schema
- [x] `POST /api/system/backup` 已有显式 response schema
- [x] `GET /api/system/material-stats` 已有显式 response schema

### Topic / Topic Group
- [x] `GlobalTopicRequest` / `GlobalTopicResponse` 已显式存在
- [x] `TopicGroupResponse` / `TopicGroupListResponse` 已显式存在

## 明确保留的兼容/例外

这些内容在 Phase 3 / PR1 不强行消除，但必须被视为已知例外：

- [ ] frontend 仍存在大量手写 axios 使用（迁移属于 PR3 / PR4）
- [ ] backend 某些低价值接口仍可能返回简单 dict / 未细化 schema
- [ ] system/config 语义仍偏占位，但 response shape 已显式化
- [ ] preview / system 等接口虽然 schema 已补齐，但 frontend 仍未完全切到 generated client

## 进入 PR2 的门槛

只有当下面这些条件成立时，才应执行 Phase 3 / PR2 regeneration：

- [x] 高价值域的 backend schema 已冻结
- [x] 高价值路径的 OpenAPI 响应 shape 可通过测试验证
- [x] 本清单已提交到 repo
- [ ] 未解决的例外已明确记录，不会在 PR2 中边修边生

## 说明

本清单不是“所有接口都完美建模”的声明。  
它是一个 **可执行冻结点**：保证高价值域已经足够稳定，适合做一次 baseline regeneration，而不是在 regeneration 过程中继续修改 contract。
