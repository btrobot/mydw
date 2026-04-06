# Account Management System Design

**Version**: v1.0
**Author**: Tech Lead
**Date**: 2026-04-06
**Status**: Proposed

---

## 1. Executive Summary

The current account management implementation provides basic CRUD and a two-phase SMS login flow but lacks essential capabilities for managing multiple Dewu platform accounts at scale. This document proposes improvements across six areas: data model, session lifecycle, login UX, batch operations, account organization, and frontend UI.

Design principles:
- **Local-first**: This is a desktop tool, not a multi-tenant SaaS. Designs should be simple and direct.
- **No data loss**: All schema changes must be additive (new columns with defaults). No column removal or rename on existing data.
- **Security by default**: Phone numbers and session data encrypted at rest with the existing AES-256-GCM infrastructure.

---

## 2. Current State Analysis

### 2.1 Account Model (as-is)

```
accounts
  id              INTEGER PK
  account_id      VARCHAR(64) UNIQUE  -- platform account identifier
  account_name    VARCHAR(128)        -- display name
  cookie          TEXT                 -- encrypted, currently unused
  storage_state   TEXT                 -- encrypted Playwright state
  status          VARCHAR(32)         -- active/inactive/error
  last_login      DATETIME
  created_at      DATETIME
  updated_at      DATETIME
```

### 2.2 Gaps Identified

| Gap | Impact |
|-----|--------|
| No phone number stored | User re-types phone every login |
| No platform profile data (nickname, avatar) | Cannot identify which account is which at a glance |
| Status enum too coarse | Cannot distinguish "session expired" from "never connected" |
| No session health check | User discovers expired session only when a task fails |
| No batch login | With 10+ accounts, manual one-by-one login is painful |
| No grouping/tagging | Hard to organize accounts by purpose |
| No notes/remarks field | Cannot annotate accounts with reminders |

---

## 3. Improved Data Model

### 3.1 New & Modified Columns on `accounts`

All new columns use `nullable=True` or have `server_default` / `default` values so that existing rows survive the migration untouched.

```
accounts (changes highlighted with +)
  id                INTEGER PK
  account_id        VARCHAR(64) UNIQUE
  account_name      VARCHAR(128)
+ phone_encrypted   TEXT            -- AES-256-GCM encrypted phone number
+ dewu_nickname     VARCHAR(128)    -- platform display name, scraped after login
+ dewu_uid          VARCHAR(64)     -- platform user ID, scraped after login
+ avatar_url        VARCHAR(512)    -- avatar URL from platform
+ tags              TEXT            -- JSON array of tag strings, e.g. ["main","fashion"]
+ remark            TEXT            -- free-form user notes
  cookie            TEXT            -- encrypted (kept for future use)
  storage_state     TEXT            -- encrypted Playwright state
  status            VARCHAR(32)     -- see revised enum below
+ session_expires_at DATETIME       -- estimated session expiry time
+ last_health_check DATETIME        -- last successful health check timestamp
+ login_fail_count  INTEGER DEFAULT 0 -- consecutive login failures
  last_login        DATETIME
  created_at        DATETIME
  updated_at        DATETIME
```

### 3.2 Field Details

| Field | Type | Encrypted | Source | Notes |
|-------|------|-----------|--------|-------|
| `phone_encrypted` | TEXT | Yes (AES-256-GCM) | User input during first login | Stored encrypted via `encrypt_data()`. Decrypted only when sending to login flow, never returned to frontend in plaintext. |
| `dewu_nickname` | VARCHAR(128) | No | Scraped from platform after successful login | Displayed in UI to help identify accounts. |
| `dewu_uid` | VARCHAR(64) | No | Scraped from platform after successful login | The Dewu platform's own user ID. Useful for deduplication. |
| `avatar_url` | VARCHAR(512) | No | Scraped from platform | Direct URL to avatar image. |
| `tags` | TEXT | No | User input | JSON array, e.g. `["fashion","main"]`. Stored as TEXT for SQLite compatibility. Indexed via application-level filtering. |
| `remark` | TEXT | No | User input | Free-form notes. |
| `session_expires_at` | DATETIME | No | Computed | Set to `last_login + SESSION_TTL` on successful login. Used by health check to decide when to probe. |
| `last_health_check` | DATETIME | No | System | Updated by the background health checker. |
| `login_fail_count` | INTEGER | No | System | Incremented on login failure, reset to 0 on success. Used for backoff logic. |

### 3.3 Revised AccountStatus Enum

```python
class AccountStatus(str, Enum):
    ACTIVE = "active"               # Session valid, ready for tasks
    INACTIVE = "inactive"           # Never connected or manually disconnected
    SESSION_EXPIRED = "session_expired"  # Session detected as expired
    ERROR = "error"                 # Unrecoverable error
    LOGGING_IN = "logging_in"      # Login in progress
    DISABLED = "disabled"           # Manually disabled by user
```

State transitions:

```
                   create account
                        |
                        v
                   [INACTIVE] <------------ disconnect
                     |     ^                     ^
          send-code  |     | login fail          |
                     v     |                     |
                [LOGGING_IN]                     |
                     |                           |
          login ok   |                           |
                     v                           |
                  [ACTIVE] ---------> [SESSION_EXPIRED]
                     |                     |
          health     |       re-login ok   |
          check fail |          |          |
                     v          v          |
                  [SESSION_EXPIRED] -------+
                     |
          manual disable
                     v
                 [DISABLED] <--- can be re-enabled to INACTIVE
                     |
                  [ERROR] <--- unrecoverable (e.g., account banned)
```

### 3.4 Why Not a Separate Tags Table?

For a local desktop tool with < 100 accounts, a JSON array in a TEXT column is the simplest approach. It avoids additional join complexity and migration overhead. If grouping needs grow, a many-to-many `account_tags` table can be introduced later (P2).

---

## 4. Session Lifecycle Management

### 4.1 Session Expiry Estimation

Dewu platform sessions typically expire after some period of inactivity. Since we cannot read the exact cookie expiry programmatically from storage_state in a reliable way, we use a heuristic:

- On successful login, set `session_expires_at = now + SESSION_TTL`
- Default `SESSION_TTL = 24 hours` (configurable in `Settings`)
- On each successful health check, extend: `session_expires_at = now + SESSION_TTL`

New config field:

```python
# core/config.py
SESSION_TTL_HOURS: int = 24  # session time-to-live estimate
HEALTH_CHECK_INTERVAL_MINUTES: int = 30  # how often to probe active accounts
```

### 4.2 Background Health Checker

A lightweight asyncio task that runs periodically and checks active accounts whose sessions may be approaching expiry.

**Algorithm**:

```
every HEALTH_CHECK_INTERVAL_MINUTES:
  for account in accounts where status = ACTIVE:
    if now > session_expires_at - 1 hour:  # probe 1 hour before estimated expiry
      result = probe_session(account)
      if result == valid:
        account.last_health_check = now
        account.session_expires_at = now + SESSION_TTL
      else:
        account.status = SESSION_EXPIRED
        emit notification event
```

**Probe method** (`probe_session`):

1. Load storage_state into a fresh browser context
2. Navigate to `https://creator.dewu.com`
3. Check if URL redirects to `/login`
4. If no redirect: session valid. Close context.
5. If redirect: session expired.

The probe uses a **temporary** browser context (not the account's main context) to avoid interfering with any active tasks.

**Resource management**: Only one probe runs at a time (serial, not parallel) to avoid overwhelming system resources. A configurable `MAX_CONCURRENT_PROBES = 1` controls this.

### 4.3 Session Expiry Notification

When a health check detects expiry, the system should:

1. Update `account.status = SESSION_EXPIRED`
2. Push a system notification via a new SSE endpoint or WebSocket (P1)
3. Log to `system_logs`

For P0, the frontend can poll the account list and show a visual indicator for `session_expired` accounts. Real-time push is P1.

### 4.4 API Endpoints for Health Check

| Method | Path | Description | Priority |
|--------|------|-------------|----------|
| `POST` | `/api/accounts/{id}/health-check` | Manually trigger health check for one account | P0 |
| `GET` | `/api/accounts/health-summary` | Get health status summary for all accounts | P1 |

#### POST /api/accounts/{id}/health-check

```json
// Response 200
{
  "success": true,
  "is_valid": true,
  "message": "Session is valid",
  "expires_at": "2026-04-07T10:00:00Z"
}
```

```json
// Response 200 (session expired)
{
  "success": true,
  "is_valid": false,
  "message": "Session expired, please reconnect",
  "expires_at": null
}
```

---

## 5. Login Flow Improvements

### 5.1 Phone Number Persistence

**Flow change**: When user enters phone number in the connection modal:

1. Frontend sends `phone` in `POST /send-code` (unchanged)
2. On successful login (`POST /verify` returns success), backend saves `encrypt_data(phone)` to `account.phone_encrypted`
3. Next time user opens the connection modal, frontend fetches account detail which includes `phone_masked` (e.g., `138****8000`)
4. Frontend pre-fills the phone input with the masked value, and if user does not change it, sends the original phone (backend decrypts from DB)

**New API behavior**:

- `GET /api/accounts/{id}` response adds `phone_masked: "138****8000"` (or `null` if no phone stored)
- `POST /api/accounts/connect/{id}/send-code` optionally accepts `{"phone": ""}` (empty string) to mean "use stored phone"
  - If phone is empty and no stored phone exists: return 400
  - If phone is empty and stored phone exists: decrypt and use it
  - If phone is provided: use it, and on success update stored phone

**Masking logic**:

```python
def mask_phone(phone: str) -> str:
    """Mask phone for display: 138****8000"""
    if len(phone) == 11:
        return phone[:3] + "****" + phone[7:]
    return "***"
```

### 5.2 Profile Scraping After Login

After successful login (in the `verify` endpoint, after saving storage_state), the system should attempt to scrape basic profile information from the Dewu creator platform.

**Implementation** (new method on `DewuClient`):

```python
async def scrape_profile(self) -> Optional[Dict[str, str]]:
    """
    Scrape user profile after successful login.
    Returns dict with keys: nickname, uid, avatar_url
    """
    # Navigate to profile page or extract from page header
    # Return None on failure (non-critical)
```

This is **best-effort**: if scraping fails, the account still functions. Profile data is updated on each successful login.

### 5.3 Login Failure Tracking

- `login_fail_count` increments on each failed login attempt
- After 3 consecutive failures, the UI should display a warning suggesting the user verify their phone number
- Reset to 0 on any successful login
- No automatic lockout (this is the user's own tool)

### 5.4 Revised AccountResponse Schema

```python
class AccountResponse(AccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: AccountStatus
    phone_masked: Optional[str] = None       # "138****8000"
    dewu_nickname: Optional[str] = None
    dewu_uid: Optional[str] = None
    avatar_url: Optional[str] = None
    tags: List[str] = []                     # parsed from JSON
    remark: Optional[str] = None
    session_expires_at: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    login_fail_count: int = 0
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
```

Note: `phone_masked` is a computed property, not a DB column. The serialization should decrypt `phone_encrypted` and mask it.

### 5.5 Revised AccountCreate & AccountUpdate Schemas

```python
class AccountCreate(BaseModel):
    account_id: str = Field(..., description="Platform account identifier")
    account_name: str = Field(..., description="Display name")
    phone: Optional[str] = Field(None, min_length=11, max_length=11,
                                  description="Phone number (will be encrypted)")
    tags: Optional[List[str]] = None
    remark: Optional[str] = None


class AccountUpdate(BaseModel):
    account_name: Optional[str] = None
    status: Optional[AccountStatus] = None
    phone: Optional[str] = Field(None, min_length=11, max_length=11)
    tags: Optional[List[str]] = None
    remark: Optional[str] = None
```

The `cookie` field is removed from `AccountUpdate` since cookies are managed internally, not by user input.

---

## 6. Batch Login

### 6.1 Design Overview

Batch login allows the user to select multiple accounts and initiate the two-phase SMS login flow for each one. Because SMS verification requires human interaction (reading the code from the phone), the batch flow is **semi-automatic**: it automates the browser setup and code sending, but pauses each account at the "enter code" step.

### 6.2 Batch Login Flow

```
User selects N accounts
        |
        v
POST /api/accounts/batch-login/start
  body: { account_ids: [1, 2, 3], concurrency: 2 }
        |
        v
Backend creates batch session, starts up to `concurrency` accounts simultaneously
        |
        v
For each account (up to concurrency limit):
  1. Decrypt stored phone (or skip if no phone stored)
  2. Call send_sms_code(phone)
  3. Push SSE status: code_sent
  4. Wait for user to POST /verify for this account
  5. On completion (success/fail), start next queued account
        |
        v
All accounts processed -> batch complete
```

### 6.3 Concurrency Control

- Default concurrency: `2` (configurable, max `5`)
- Rationale: Each login opens a browser context + page. Too many concurrent browsers will exhaust memory on a typical desktop.
- A semaphore controls how many logins run simultaneously
- Accounts beyond the concurrency limit are queued

### 6.4 Batch Login API

| Method | Path | Description | Priority |
|--------|------|-------------|----------|
| `POST` | `/api/accounts/batch-login/start` | Start batch login | P1 |
| `GET` | `/api/accounts/batch-login/status` | Get batch progress | P1 |
| `POST` | `/api/accounts/batch-login/cancel` | Cancel remaining batch | P1 |

#### POST /api/accounts/batch-login/start

```json
// Request
{
  "account_ids": [1, 2, 3, 5, 8],
  "concurrency": 2
}
```

```json
// Response 202
{
  "success": true,
  "batch_id": "batch_20260406_001",
  "message": "Batch login started for 5 accounts",
  "queued": 5,
  "concurrency": 2
}
```

**Preconditions**:
- All account_ids must exist
- All accounts must have `phone_encrypted` (cannot batch-login accounts without stored phone)
- No existing batch session in progress

#### GET /api/accounts/batch-login/status

```json
// Response 200
{
  "batch_id": "batch_20260406_001",
  "total": 5,
  "completed": 2,
  "in_progress": 2,
  "queued": 1,
  "accounts": [
    { "id": 1, "status": "success", "message": "Connected" },
    { "id": 2, "status": "success", "message": "Connected" },
    { "id": 3, "status": "waiting_code", "message": "Enter verification code" },
    { "id": 5, "status": "waiting_code", "message": "Enter verification code" },
    { "id": 8, "status": "queued", "message": "Waiting for slot" }
  ]
}
```

### 6.5 Failure Handling

- If `send_sms_code` fails for an account: mark it as `failed` in the batch, move to next
- If user does not enter code within 5 minutes: mark as `timeout`, move to next
- User can cancel the entire batch at any time

### 6.6 Important Constraint

Batch login requires that all accounts already have a stored phone number. Accounts without `phone_encrypted` are excluded from the batch and the user is warned. This incentivizes saving phone numbers during the first manual login.

---

## 7. Account Management Enhancements

### 7.1 Tags / Grouping

Tags are stored as a JSON array in the `tags` column. The frontend provides a tag input component.

**Predefined tag suggestions** (configurable): `["main", "backup", "fashion", "sports", "testing"]`

**Filtering API**:

```
GET /api/accounts?tag=fashion
GET /api/accounts?tags=fashion,sports  (accounts matching ANY of the tags)
```

Backend implementation: load all accounts, filter in Python. For < 100 accounts this is perfectly adequate. No need for SQL-level JSON querying on SQLite.

### 7.2 Search

```
GET /api/accounts?search=john
```

Searches across: `account_name`, `dewu_nickname`, `account_id`, `remark`. Case-insensitive, substring match.

### 7.3 Batch Operations

| Method | Path | Description | Priority |
|--------|------|-------------|----------|
| `POST` | `/api/accounts/batch` | Batch operations on multiple accounts | P1 |

```json
// Request
{
  "action": "disable",     // "disable" | "enable" | "delete" | "add_tag" | "remove_tag"
  "account_ids": [1, 2, 3],
  "payload": {             // action-specific data
    "tag": "archive"       // for add_tag/remove_tag
  }
}
```

```json
// Response 200
{
  "success": true,
  "affected": 3,
  "message": "3 accounts disabled"
}
```

### 7.4 Export / Import (Account Metadata)

Allows backing up account configuration (not sessions, which are device-specific).

| Method | Path | Description | Priority |
|--------|------|-------------|----------|
| `GET` | `/api/accounts/export` | Export all accounts as JSON | P2 |
| `POST` | `/api/accounts/import` | Import accounts from JSON | P2 |

Export format:

```json
{
  "version": 1,
  "exported_at": "2026-04-06T12:00:00Z",
  "accounts": [
    {
      "account_id": "dewu_001",
      "account_name": "My Account",
      "tags": ["main"],
      "remark": "Primary account"
      // phone NOT included for security
      // storage_state NOT included (device-specific)
    }
  ]
}
```

---

## 8. Frontend UI Improvements

### 8.1 Account List Redesign

**Current**: Simple table with columns: ID, Name, Status, Last Login, Created, Actions.

**Proposed**: Card/list hybrid view with richer information.

Each account row/card shows:
- Avatar (from `avatar_url`, or a default icon)
- Account name + Dewu nickname
- Status badge with color coding:
  - `active`: green
  - `inactive`: gray
  - `session_expired`: orange with "session expired" tooltip
  - `logging_in`: blue with spinner
  - `error`: red
  - `disabled`: gray with strikethrough
- Tags as small colored chips
- Session health indicator:
  - Green dot: session valid, expires in > 4 hours
  - Yellow dot: session valid, expires in < 4 hours
  - Red dot: session expired or error
- Last login time (relative, e.g., "2 hours ago")
- Quick action buttons: Connect / Reconnect / Disconnect / More

### 8.2 Connection Modal Improvements

- Pre-fill phone number from `phone_masked` with a "change" link
- Show login failure count as a warning if > 0
- After successful login, briefly show scraped profile info (nickname, avatar) as confirmation

### 8.3 Batch Login UI

- Checkbox column on account table for multi-select
- "Batch Login" button in toolbar (enabled when 2+ accounts selected, all have stored phone)
- Batch login panel/drawer showing:
  - List of accounts with individual status
  - For each "waiting_code" account: an inline code input field
  - Progress bar for overall batch completion
  - Cancel button

### 8.4 Account Detail View

A slide-out drawer or dedicated page for each account showing:
- Full profile information
- Session status and expiry countdown
- Login history (from `system_logs` filtered by account)
- Tags editor
- Remark editor
- Danger zone: disconnect, disable, delete

### 8.5 Toolbar Enhancements

- Search bar (filters by name/nickname/remark)
- Tag filter dropdown (multi-select)
- Status filter dropdown
- Batch action buttons (visible when rows selected)

---

## 9. Priority Matrix

### P0 - Must Have (next sprint)

| Item | Area | Effort |
|------|------|--------|
| Add `phone_encrypted` column | Model | S |
| Phone persistence in login flow | Backend + Frontend | M |
| Pre-fill phone in ConnectionModal | Frontend | S |
| Add `dewu_nickname`, `dewu_uid`, `avatar_url` columns | Model | S |
| Profile scraping after login | Backend | M |
| Revised `AccountStatus` enum (add `session_expired`, `disabled`) | Model + Schema | S |
| Enhanced AccountResponse with new fields | Schema | S |
| `POST /health-check` endpoint (manual trigger) | Backend | M |
| Status badge color coding for new statuses | Frontend | S |
| Tags column + filtering | Model + Backend + Frontend | M |
| Remark column + UI | Model + Backend + Frontend | S |
| Search endpoint | Backend | S |
| Database migration script | Backend | M |

### P1 - Should Have (following sprint)

| Item | Area | Effort |
|------|------|--------|
| Background health checker (periodic) | Backend | L |
| Session expiry estimation + countdown | Backend + Frontend | M |
| Batch login flow | Backend + Frontend | L |
| Batch operations API | Backend | M |
| Account detail drawer | Frontend | M |
| `login_fail_count` tracking | Backend | S |
| Health summary endpoint | Backend | S |
| SSE notifications for session expiry | Backend | M |

### P2 - Nice to Have (later)

| Item | Area | Effort |
|------|------|--------|
| Account export/import | Backend + Frontend | M |
| Predefined tag management | Frontend | S |
| Account card view (alternative to table) | Frontend | M |
| Login history timeline | Frontend | M |
| Many-to-many tags table (if JSON approach proves limiting) | Backend | M |

Size key: S = < 2 hours, M = 2-6 hours, L = 6+ hours

---

## 10. Database Migration Strategy

### 10.1 No Alembic Yet

The project currently uses `Base.metadata.create_all()` on startup, with no migration tooling. For the initial phase, we use a pragmatic approach.

### 10.2 Additive Migration Script

Since all changes are new columns with defaults/nullable, SQLite `ALTER TABLE ADD COLUMN` works directly. Create a migration script:

**File**: `backend/migrations/001_account_management.py`

```python
"""
Migration 001: Account Management Enhancement

Adds new columns to the accounts table for phone storage,
profile data, session management, and organization.

Safe to run multiple times (idempotent).
"""

MIGRATION_STATEMENTS = [
    "ALTER TABLE accounts ADD COLUMN phone_encrypted TEXT",
    "ALTER TABLE accounts ADD COLUMN dewu_nickname VARCHAR(128)",
    "ALTER TABLE accounts ADD COLUMN dewu_uid VARCHAR(64)",
    "ALTER TABLE accounts ADD COLUMN avatar_url VARCHAR(512)",
    "ALTER TABLE accounts ADD COLUMN tags TEXT DEFAULT '[]'",
    "ALTER TABLE accounts ADD COLUMN remark TEXT",
    "ALTER TABLE accounts ADD COLUMN session_expires_at DATETIME",
    "ALTER TABLE accounts ADD COLUMN last_health_check DATETIME",
    "ALTER TABLE accounts ADD COLUMN login_fail_count INTEGER DEFAULT 0",
]
```

**Execution approach**:

1. On startup, after `create_all()`, run each statement in a try/except block (SQLite raises error if column already exists -- catch and skip)
2. This is idempotent and safe for development
3. Before v1.0 release, consider adopting Alembic for proper version tracking

### 10.3 Status Value Migration

Existing rows with `status = "active"` or `status = "inactive"` remain valid since those values exist in the new enum. No data transformation needed.

### 10.4 Rollback

Since all changes are additive column additions, rollback is simply "ignore the new columns." SQLAlchemy will not query columns not defined in the model, so reverting the model code is sufficient.

---

## 11. Security Considerations

### 11.1 Phone Number Encryption

- Stored in `phone_encrypted` using existing `encrypt_data()` (AES-256-GCM)
- Never returned in plaintext to the frontend
- Masked format `138****8000` computed server-side via `mask_phone()`
- Decrypted only at the moment of calling `send_sms_code()`

### 11.2 API Response Filtering

- `storage_state` is never included in `AccountResponse` (already the case)
- `cookie` is never included in `AccountResponse` (already the case)
- `phone_encrypted` is never included directly; only `phone_masked` is returned

### 11.3 Health Check Security

- Health checks use temporary browser contexts that are immediately closed
- No new credentials are needed for health checks (uses stored storage_state)

### 11.4 Batch Operations

- Batch delete requires explicit confirmation parameter: `{"confirm": true}`
- Batch operations are logged in `system_logs`

---

## 12. Open Questions for User Decision

| # | Question | Options | Recommendation |
|---|----------|---------|----------------|
| 1 | Should we adopt Alembic for migrations now, or keep the simple additive script approach? | A) Adopt Alembic now B) Simple script now, Alembic later | B -- keep it simple for now, adopt Alembic when we approach a stable release |
| 2 | Health check frequency: how often should we probe active sessions? | A) Every 15 min B) Every 30 min C) Every 60 min | B -- 30 minutes balances freshness vs resource usage |
| 3 | Batch login concurrency: max simultaneous browser instances? | A) 1 B) 2 C) 3 | B -- 2 is safe for most desktops |
| 4 | Should the first sprint (P0) include the background health checker, or is manual health check sufficient? | A) Include background checker B) Manual only for P0 | B -- manual trigger is sufficient for P0; background checker is P1 |
| 5 | Should we prioritize batch login (P1) or the account organization features (tags, search) first? | A) Batch login first B) Organization first | B -- tags and search are simpler, used more often, and improve daily UX immediately |

---

## 13. ADR: Account Management Enhancement

```
## ADR-001: Account Management System Enhancement

### Status
Proposed

### Context
The current account model stores minimal data (name, platform ID, encrypted session).
Users must re-enter phone numbers on every login, cannot organize accounts, and have
no visibility into session health. With growing account counts, these gaps become
increasingly painful.

### Decision
Extend the Account model with encrypted phone storage, platform profile data, session
lifecycle tracking, and tag-based organization. Implement changes incrementally across
P0 (essential fields + login UX), P1 (health checks + batch operations), and P2 (export/import).

### Consequences
Positive:
- Users save time on repeat logins (phone persistence)
- Better account identification (profile data)
- Proactive session management (health checks)
- Scalable organization (tags, search)

Negative:
- Additional DB columns increase schema complexity
- Background health checker adds resource overhead
- Batch login requires careful concurrency management

Neutral:
- Existing data is fully preserved (additive migration)
- All new features are backward-compatible
```

---

*Document version v1.0 -- pending User (Product Owner) review and approval.*
