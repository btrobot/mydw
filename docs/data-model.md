# Data Model

> Status: Stale / archival reference  
> 当前 authoritative 数据模型真相请优先看：
> - `backend/models/__init__.py`
> - `docs/current-architecture-baseline.md`
> - `docs/current-runtime-truth.md`
>
> 本文档保留为历史性字典参考，但不再保证字段/关系描述始终与当前代码完全同步。

> Version: 1.0.0 | Updated: 2026-04-07
> Owner: Backend Lead

Database: SQLite (aiosqlite) at `backend/data/dewugojin.db`
ORM: SQLAlchemy 2.0 async
Source of truth: `backend/models/__init__.py`

---

## Endpoints Summary

| Table | tablename | Description | Key Relationships |
|-------|-----------|-------------|-------------------|
| Account | accounts | Dewu platform accounts | 1:N Task |
| Task | tasks | Publish tasks | N:1 Account, N:1 Product, N:N Topic |
| Product | products | Product catalog | 1:N Task, 1:N Video, 1:N Copywriting |
| Video | videos | Video materials | N:1 Product, 1:N Cover |
| Copywriting | copywritings | Copywriting materials | N:1 Product |
| Cover | covers | Cover images | N:1 Video |
| Audio | audios | Audio materials | -- |
| Topic | topics | Dewu topics/hashtags | N:N Task |
| TaskTopic | task_topics | Task-Topic junction | N:1 Task, N:1 Topic |
| PublishLog | publish_logs | Publish execution logs | N:1 Task |
| PublishConfig | publish_config | Publish scheduler config | -- |
| SystemLog | system_logs | System-level logs | -- |

---

## accounts

Dewu platform user accounts with encrypted credentials.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Internal ID |
| account_id | String(64) | unique, not null, index | External account identifier |
| account_name | String(128) | not null | Display name |
| cookie | Text | nullable | Encrypted cookie (AES-256-GCM) |
| storage_state | Text | nullable | Playwright storage state JSON |
| status | String(32) | default="active", index | active/inactive/error/session_expired/disabled |
| last_login | DateTime | nullable | Last successful login time |
| phone_encrypted | Text | nullable | AES-256-GCM encrypted phone number |
| dewu_nickname | String(128) | nullable | Dewu platform nickname |
| dewu_uid | String(64) | nullable | Dewu platform UID |
| avatar_url | String(512) | nullable | Avatar URL |
| tags | Text | default='[]' | JSON array of tags |
| remark | Text | nullable | Notes |
| session_expires_at | DateTime | nullable | Session expiration time |
| last_health_check | DateTime | nullable | Last health check time |
| login_fail_count | Integer | default=0 | Consecutive login failure count |
| created_at | DateTime | default=utcnow | Creation timestamp |
| updated_at | DateTime | default=utcnow, onupdate | Last update timestamp |

**Relationships:**
- Account 1:N Task (via `tasks.account_id`)

**Notes:**
- `cookie` and `phone_encrypted` are encrypted at rest via `utils/crypto.py`

---

## tasks

Publish tasks linking accounts to materials.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Internal ID |
| account_id | Integer | FK(accounts.id), not null, index | Owning account |
| product_id | Integer | FK(products.id), nullable | Associated product |
| video_id | Integer | FK(videos.id), nullable, index | Video material |
| copywriting_id | Integer | FK(copywritings.id), nullable, index | Copywriting material |
| audio_id | Integer | FK(audios.id), nullable, index | Audio material |
| status | String(32) | default="pending", index | pending/running/success/failed/paused |
| publish_time | DateTime | nullable, index | Scheduled publish time |
| error_msg | Text | nullable | Error message on failure |
| priority | Integer | default=0 | Higher = higher priority |
| created_at | DateTime | default=utcnow | Creation timestamp |
| updated_at | DateTime | default=utcnow, onupdate | Last update timestamp |

**Relationships:**
- Task N:1 Account (via `account_id`)
- Task N:1 Product (via `product_id`)
- Task N:1 Video (via `video_id`)
- Task N:1 Copywriting (via `copywriting_id`)
- Task N:1 Audio (via `audio_id`)
- Task 1:N PublishLog (via `publish_logs.task_id`)
- Task N:N Topic (via `task_topics` junction)

---

## products

Product catalog for Dewu platform items.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Internal ID |
| name | String(256) | unique, not null, index | Product name |
| link | String(512) | nullable | Product link |
| description | Text | nullable | Product description |
| dewu_url | String(512) | nullable | Dewu product page URL |
| image_url | String(512) | nullable | Product image URL |
| created_at | DateTime | default=utcnow | Creation timestamp |
| updated_at | DateTime | default=utcnow, onupdate | Last update timestamp |

**Relationships:**
- Product 1:N Task (via `tasks.product_id`)
- Product 1:N Video (via `videos.product_id`)
- Product 1:N Copywriting (via `copywritings.product_id`)

---

## videos

Video material files.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Internal ID |
| product_id | Integer | FK(products.id), nullable, index | Associated product |
| name | String(256) | not null | Display name |
| file_path | String(512) | not null | File system path |
| file_size | Integer | nullable | File size in bytes |
| duration | Integer | nullable | Duration in seconds |
| width | Integer | nullable | Video width px |
| height | Integer | nullable | Video height px |
| file_hash | String(64) | nullable | File content hash |
| source_type | String(32) | default="original" | Source type |
| created_at | DateTime | default=utcnow | Creation timestamp |
| updated_at | DateTime | default=utcnow, onupdate | Last update timestamp |

**Relationships:**
- Video N:1 Product (via `product_id`)
- Video 1:N Cover (via `covers.video_id`)

---

## copywritings

Copywriting/text materials.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Internal ID |
| product_id | Integer | FK(products.id), nullable, index | Associated product |
| content | Text | not null | Copywriting text content |
| source_type | String(32) | default="manual" | manual/ai/import |
| source_ref | String(256) | nullable | Source reference |
| created_at | DateTime | default=utcnow | Creation timestamp |
| updated_at | DateTime | default=utcnow, onupdate | Last update timestamp |

**Relationships:**
- Copywriting N:1 Product (via `product_id`)

---

## covers

Cover image files.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Internal ID |
| video_id | Integer | FK(videos.id), nullable, index | Associated video |
| file_path | String(512) | not null | File system path |
| file_size | Integer | nullable | File size in bytes |
| width | Integer | nullable | Image width px |
| height | Integer | nullable | Image height px |
| created_at | DateTime | default=utcnow | Creation timestamp |

**Relationships:**
- Cover N:1 Video (via `video_id`)

---

## audios

Audio material files.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Internal ID |
| name | String(256) | not null | Display name |
| file_path | String(512) | not null | File system path |
| file_size | Integer | nullable | File size in bytes |
| duration | Integer | nullable | Duration in seconds |
| created_at | DateTime | default=utcnow | Creation timestamp |

---

## topics

Dewu platform topics/hashtags.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Internal ID |
| name | String(256) | unique, not null, index | Topic name |
| heat | Integer | default=0 | Popularity score |
| source | String(32) | default="manual" | manual/search |
| last_synced | DateTime | nullable | Last sync from Dewu |
| created_at | DateTime | default=utcnow | Creation timestamp |

---

## task_topics

Junction table for Task-Topic many-to-many relationship.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Internal ID |
| task_id | Integer | FK(tasks.id, ondelete=CASCADE), not null, index | Task reference |
| topic_id | Integer | FK(topics.id), not null, index | Topic reference |

**Constraints:** UNIQUE(task_id, topic_id)

---

## publish_logs

Execution logs for publish operations.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Internal ID |
| task_id | Integer | FK(tasks.id), not null, index | Associated task |
| account_id | Integer | FK(accounts.id), not null, index | Associated account |
| status | String(32) | not null | started/success/failed |
| message | Text | nullable | Log message |
| created_at | DateTime | default=utcnow, index | Timestamp |

**Relationships:**
- PublishLog N:1 Task (via `task_id`)

---

## publish_config

Scheduler configuration (singleton-like, uses first row).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Internal ID |
| name | String(64) | default="default" | Config profile name |
| interval_minutes | Integer | default=30 | Minutes between publishes |
| start_hour | Integer | default=9 | Daily start hour |
| end_hour | Integer | default=22 | Daily end hour |
| max_per_account_per_day | Integer | default=5 | Daily limit per account |
| shuffle | Boolean | default=False | Randomize task order |
| auto_start | Boolean | default=False | Auto-start on app launch |
| global_topic_ids | Text | default='[]' | JSON array of global topic IDs |
| created_at | DateTime | default=utcnow | Creation timestamp |
| updated_at | DateTime | default=utcnow, onupdate | Last update timestamp |

---

## system_logs

Application-level log entries.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Internal ID |
| level | String(16) | not null | INFO/WARNING/ERROR |
| module | String(64) | nullable | Source module |
| message | Text | not null | Log message |
| details | Text | nullable | Additional details |
| created_at | DateTime | default=utcnow, index | Timestamp |

---

## Entity Relationship Diagram

```
accounts 1──N tasks N──1 products
                │              │
                │         1──N videos 1──N covers
                │              │
                │         1──N copywritings
                │
                ├──N publish_logs
                │
                └──N task_topics N──1 topics

audios (standalone)
publish_config (singleton)
system_logs (standalone)
```

## Migrations

Migrations are in `backend/migrations/` and run at startup (idempotent):

| Migration | Description |
|-----------|-------------|
| 001_account_management | Add extended account fields |
| 002_material_product_link | Link materials to products |
| 003_product_enhance | Add dewu_url, image_url to products |
| 004_material_split | Split materials into separate tables |
| 005_task_add_fk | Add video/copywriting/audio FK to tasks |
| 006_global_topics | Add global_topic_ids to publish_config |
| 007_task_topic_unique | Add unique constraint to task_topics |
