# API Reference

> Status: Stale / archival reference  
> 当前 authoritative API truth 请优先看：
> - backend live docs: `/docs`
> - OpenAPI export: `/openapi.json`
> - `docs/current/architecture.md`
> - `docs/current/runtime-truth.md`
>
> 本文档保留为历史性参考，不再保证逐端点细节始终与当前代码同步。

> Version: 1.0.0 | Updated: 2026-04-07
> Owner: Backend Lead

Base URL: `http://localhost:8000`
Live docs: `/docs` (Swagger) | `/redoc` | `/openapi.json`

---

## Endpoints Summary

| Module | Prefix | Count | Key Operations |
|--------|--------|-------|----------------|
| Accounts | /api/accounts | 21+7dep | CRUD, connect, health-check, preview, SSE |
| Tasks | /api/tasks | 11 | CRUD, batch, assemble, shuffle, publish |
| Publish | /api/publish | 7 | config, control, status, logs |
| Products | /api/products | 5 | CRUD, name search |
| Videos | /api/videos | 5 | CRUD, product filter |
| Copywritings | /api/copywritings | 5 | CRUD, product/source filter |
| Covers | /api/covers | 3 | upload, list, delete |
| Audios | /api/audios | 3 | upload, list, delete |
| Topics | /api/topics | 6 | CRUD, search, global topics |
| AI Clip | /api/ai | 7 | video-info, highlights, clip, pipeline |
| System | /api/system | 6 | stats, logs, config, backup |

---

## Accounts -- /api/accounts

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | / | Create account | 201 |
| GET | / | List accounts (?status, ?skip, ?limit) | 200 |
| GET | /stats | Account statistics | 200 |
| GET | /{id} | Get single account | 200/404 |
| PUT | /{id} | Update account | 200/404 |
| DELETE | /{id} | Delete account | 204/404 |
| POST | /{id}/health-check | Single account health check | 200 |
| POST | /batch-health-check | Batch health check | 200 |
| GET | /batch-health-check/status | Batch check progress | 200 |
| GET | /preview/status | Preview window status | 200 |
| POST | /{id}/preview | Open preview browser | 200 |
| POST | /{id}/preview/close | Close preview browser | 200 |
| POST | /connect/{id}/send-code | Send SMS verification code | 202 |
| POST | /connect/{id}/verify | Verify SMS code, complete login | 200 |
| GET | /connect/{id}/stream | SSE connection status stream | 200 |
| GET | /connect/{id}/status | Get connection status | 200 |
| POST | /connect/{id}/export | Export session/cookies | 200 |
| POST | /connect/{id}/import | Import session/cookies | 200 |
| GET | /connect/{id}/screenshot | Browser screenshot | 200 |
| POST | /test/{id} | Test account connectivity | 200 |
| POST | /disconnect/{id} | Disconnect session | 200 |

Deprecated aliases (use `/connect/` and `/disconnect/` instead):
`/login/{id}`, `/login/{id}/stream`, `/login/{id}/status`, `/login/{id}/export`, `/login/{id}/import`, `/login/{id}/screenshot`, `/logout/{id}`

### Key Schemas

**AccountCreate**: account_id (str, required), account_name (str, required)

**AccountResponse**: id, account_id, account_name, status, dewu_nickname, dewu_uid, avatar_url, tags, remark, last_login, last_health_check, created_at, updated_at (excludes cookie, phone_encrypted, storage_state)

---

## Tasks -- /api/tasks

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | / | Create task | 201/404 |
| GET | / | List tasks (?status, ?account_id, ?limit, ?offset) | 200 |
| GET | /stats | Task statistics | 200 |
| GET | /{id} | Get task details | 200/404 |
| PUT | /{id} | Update task | 200/404 |
| DELETE | /{id} | Delete task | 204/404 |
| DELETE | / | Delete all tasks (?status filter) | 204 |
| POST | /{id}/publish | Queue task for publish | 200/400/404 |
| POST | /batch | Batch create tasks | 201 |
| POST | /shuffle | Randomize task order | 200 |
| POST | /assemble | Auto-distribute videos to accounts | 201 |

### Key Schemas

**TaskCreate**: account_id (int, required), product_id, video_id, copywriting_id, audio_id, publish_time, priority

**TaskResponse**: id, account_id, product_id, video_id, copywriting_id, audio_id, status, publish_time, error_msg, priority, created_at, updated_at + nested video, copywriting, topics, product

**AssembleTasksRequest**: video_ids (list[int]), account_ids (list[int]), strategy, copywriting_mode

---

## Publish -- /api/publish

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | /config | Get scheduler config | 200 |
| PUT | /config | Update scheduler config | 200 |
| GET | /status | Get publish engine status | 200 |
| POST | /control | Control engine (start/pause/stop) | 200/400 |
| POST | /refresh | Refresh account data from Dewu | 200 |
| POST | /shuffle | Shuffle pending tasks | 200 |
| GET | /logs | Get publish logs (?limit) | 200 |

### Key Schemas

**PublishConfigRequest**: interval_minutes, start_hour, end_hour, max_per_account_per_day, shuffle, auto_start

**PublishStatusResponse**: status, current_task_id, total_pending, total_success, total_failed

---

## Products -- /api/products

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | / | List products (?name, ?skip, ?limit) | 200 |
| GET | /{id} | Get product | 200/404 |
| POST | / | Create product | 201/400 |
| PUT | /{id} | Update product | 200/400/404 |
| DELETE | /{id} | Delete product | 204/404 |

**ProductCreate**: name (str, required, unique), link, description, dewu_url, image_url

---

## Videos -- /api/videos

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | / | List videos (?product_id, ?skip, ?limit) | 200 |
| GET | /{id} | Get video | 200/404 |
| POST | / | Create video record | 201 |
| PUT | /{id} | Update video | 200/404 |
| DELETE | /{id} | Delete video | 204/404 |

**VideoCreate**: name (str, required), file_path (str, required), product_id, file_size, duration

---

## Copywritings -- /api/copywritings

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | / | List (?product_id, ?source_type, ?skip, ?limit) | 200 |
| GET | /{id} | Get copywriting | 200/404 |
| POST | / | Create copywriting | 201 |
| PUT | /{id} | Update copywriting | 200/404 |
| DELETE | /{id} | Delete copywriting | 204/404 |

**CopywritingCreate**: content (str, required), product_id, source_type, source_ref

---

## Covers -- /api/covers

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | /upload | Upload cover (JPEG/PNG/WebP, max 20MB) | 201/400 |
| GET | / | List covers (?video_id, ?skip, ?limit) | 200 |
| DELETE | /{id} | Delete cover (file + record) | 204/404 |

---

## Audios -- /api/audios

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | /upload | Upload audio (MP3/WAV/AAC/OGG, max 100MB) | 201/400 |
| GET | / | List audios (?skip, ?limit) | 200 |
| DELETE | /{id} | Delete audio (file + record) | 204/404 |

---

## Topics -- /api/topics

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | / | List topics (?sort=created_at/heat, ?skip, ?limit) | 200 |
| POST | / | Create topic | 201/400 |
| DELETE | /{id} | Delete topic | 204/404 |
| GET | /search | Search Dewu topics (?keyword, auto-imports) | 200 |
| PUT | /global | Set global topics (overwrites) | 200 |
| GET | /global | Get current global topics | 200 |

**TopicCreate**: name (str, required, unique), heat (int), source (str)

**GlobalTopicRequest**: topic_ids (list[int])

---

## AI Clip -- /api/ai

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | /video-info | Get video metadata (?video_path) | 200/400 |
| GET | /detect-highlights | Detect highlight segments (?video_path) | 200 |
| POST | /smart-clip | Clip video with segments | 200 |
| POST | /add-audio | Add background audio | 200 |
| POST | /add-cover | Add cover image | 200 |
| POST | /trim | Trim video to time range | 200 |
| POST | /full-pipeline | Full pipeline: detect+clip+audio+cover | 200 |

### Key Schemas

**SmartClipRequest**: video_path, segments (list of {start, end, reason}), output_path, target_duration

**FullPipelineRequest**: video_path, audio_path?, cover_path?, target_duration, output_dir?

**ClipResultResponse**: success (bool), output_path?, duration, error?

---

## System -- /api/system

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | /stats | System-wide statistics | 200 |
| GET | /logs | System logs (?level, ?limit) | 200 |
| POST | /logs | Add log entry | 200 |
| GET | /config | Get system config | 200 |
| PUT | /config | Update system config | 200 |
| POST | /backup | Create data backup | 200 |

**SystemStats**: total_accounts, active_accounts, total_tasks, pending_tasks, success_tasks, failed_tasks, total_products

---

## Common Patterns

**Pagination**: Most list endpoints accept `skip` (offset) and `limit` query params.

**List Response**: `{ total: int, items: [...] }` for paginated endpoints.

**Error Response**: `{ detail: "error message" }` with appropriate HTTP status code.

**File Upload**: multipart/form-data with content-type and size validation.
