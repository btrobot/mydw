# Topic Group (话题组) Design

> Version: 1.0.0 | Updated: 2026-04-07
> Owner: Tech Lead
> Status: Proposed

## Problem

Current "global topics" is a single flat list of topic IDs stored in `PublishConfig.global_topic_ids`. Users cannot predefine multiple named topic combinations. Every task gets the same set of topics, and switching requires manually re-selecting individual topics each time.

## Goal

Replace the flat global topic list with named, reusable **Topic Groups** (话题组). Users predefine groups like "运动鞋: [#nike, #空军一号, #运动鞋推荐]", then select a group when creating tasks.

---

## Data Model

### New Table: `topic_groups`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto | Internal ID |
| name | String(128) | unique, not null, index | Group name (e.g. "运动鞋") |
| topic_ids | Text | not null, default='[]' | JSON array of topic IDs |
| created_at | DateTime | default=utcnow | Creation timestamp |
| updated_at | DateTime | default=utcnow, onupdate | Last update timestamp |

Design notes:
- `topic_ids` is a JSON array (same pattern as the existing `global_topic_ids`). This avoids a junction table for a simple ordered list that rarely exceeds 10 items.
- `name` has a unique constraint -- no duplicate group names.

### SQLAlchemy Model

```python
class TopicGroup(Base):
    """话题组 (话题模板)"""
    __tablename__ = "topic_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False, index=True)
    topic_ids = Column(Text, nullable=False, default='[]')  # JSON array of topic IDs

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Task Table Change

Add optional FK to `topic_groups`:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| topic_group_id | Integer | FK(topic_groups.id), nullable, index | Selected topic group |

When a task is created with `topic_group_id`, the system resolves `TopicGroup.topic_ids` and creates `TaskTopic` rows -- same as today, but the source is a group instead of a global flat list.

### Migration: `015_topic_groups`

1. Create `topic_groups` table.
2. Add `tasks.topic_group_id` column (nullable FK).
3. Migrate existing data: if `PublishConfig.global_topic_ids` is non-empty, create a TopicGroup named "默认话题组" with those IDs.

### PublishConfig Change

`global_topic_ids` column is **deprecated**. Replace with:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| default_topic_group_id | Integer | FK(topic_groups.id), nullable | Default group for new tasks |

This replaces the JSON blob with a proper FK. The migration copies the old data into a TopicGroup row and sets this FK.

---

## API Design

### New Endpoints: `/api/topic-groups`

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | / | List all topic groups | 200 |
| GET | /{id} | Get single group (with resolved topics) | 200/404 |
| POST | / | Create topic group | 201/400 |
| PUT | /{id} | Update topic group | 200/400/404 |
| DELETE | /{id} | Delete topic group | 204/404 |

### Schemas

```python
class TopicGroupCreate(BaseModel):
    """创建话题组"""
    name: str = Field(..., min_length=1, max_length=128)
    topic_ids: List[int] = Field(default_factory=list, description="话题ID列表")

class TopicGroupUpdate(BaseModel):
    """更新话题组"""
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    topic_ids: Optional[List[int]] = Field(None, description="话题ID列表")

class TopicGroupResponse(BaseModel):
    """话题组响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    topic_ids: List[int]          # raw ID list
    topics: List[TopicResponse]   # resolved topic objects
    created_at: datetime
    updated_at: datetime

class TopicGroupListResponse(BaseModel):
    """话题组列表响应"""
    total: int
    items: List[TopicGroupResponse]
```

### Modified Endpoints

**POST /api/tasks** and **POST /api/tasks/assemble** -- add optional `topic_group_id` parameter:

```python
class TaskCreate(BaseModel):
    # ... existing fields ...
    topic_group_id: Optional[int] = Field(None, description="话题组ID")

class AssembleTasksRequest(BaseModel):
    # ... existing fields ...
    topic_group_id: Optional[int] = Field(None, description="话题组ID (replaces global topics)")
```

When `topic_group_id` is provided, the system:
1. Loads `TopicGroup` by ID
2. Parses `topic_ids` JSON
3. Creates `TaskTopic` rows for each topic

When `topic_group_id` is omitted, falls back to `PublishConfig.default_topic_group_id` (if set).

### Deprecated Endpoints

| Endpoint | Status | Replacement |
|----------|--------|-------------|
| PUT /api/topics/global | Deprecated | POST/PUT /api/topic-groups |
| GET /api/topics/global | Deprecated | GET /api/topic-groups |

Keep them functional during transition (read/write the "默认话题组" TopicGroup), remove in next major version.

---

## TaskAssembler Changes

Current flow:
```
PublishConfig.global_topic_ids → JSON parse → attach to all tasks
```

New flow:
```
request.topic_group_id
  ?? PublishConfig.default_topic_group_id
  → load TopicGroup → parse topic_ids → attach to tasks
```

```python
# In TaskAssembler.assemble()
topic_group_id = topic_group_id or config.default_topic_group_id
if topic_group_id:
    group = await db.get(TopicGroup, topic_group_id)
    if group:
        topic_ids = json.loads(group.topic_ids)
        # ... create TaskTopic rows (same as today)
```

---

## Frontend Changes (Summary)

1. **New page/section**: Topic Group management (CRUD) -- likely a tab or section within the existing TopicList page.
2. **Task creation form**: Replace individual topic picker with a TopicGroup dropdown.
3. **Settings page**: "Default topic group" selector replaces the current "global topics" selector.
4. **TopicList.tsx**: The "全局话题" card at the top becomes "默认话题组" with a link to manage groups.

---

## Backward Compatibility

| Concern | Mitigation |
|---------|-----------|
| Existing tasks with TaskTopic rows | Unchanged -- TaskTopic rows are the source of truth for existing tasks |
| Existing global_topic_ids data | Migration creates a "默认话题组" TopicGroup from the data |
| Old API consumers | Deprecated endpoints remain functional, backed by the default TopicGroup |
| Tasks without topic_group_id | Fall back to default_topic_group_id, then no topics |

---

## ER Diagram (Updated)

```
topic_groups 1──N tasks (via tasks.topic_group_id)
     │
     └── topic_ids JSON ──references──> topics

tasks N──N topics (via task_topics, unchanged)
```

`topic_group_id` on Task records which group was selected. `task_topics` remains the actual topic-task binding (resolved at creation time). If a group is later edited, existing tasks are unaffected -- topics were already materialized into `task_topics`.

---

## Decision: Why JSON Array Instead of Junction Table

For `TopicGroup.topic_ids`, a junction table (`topic_group_topics`) was considered. JSON array was chosen because:

1. Groups are small (typically 3-10 topics) -- no query/index benefit from a junction table.
2. Topic order matters to users -- JSON preserves insertion order naturally.
3. Simpler CRUD -- update is a single row write, not delete+re-insert.
4. Consistent with the existing pattern (`PublishConfig.global_topic_ids`).

Trade-off: no FK enforcement on individual topic IDs within the JSON. Mitigation: validate topic IDs exist on create/update (same as current `set_global_topics` does).
