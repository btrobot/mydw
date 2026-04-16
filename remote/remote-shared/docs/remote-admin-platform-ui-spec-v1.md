# Remote Admin Platform UI Spec v1

## Purpose

This document defines an implementation-ready UI specification for the current `remote-admin` product while explicitly framing it as the **first business domain inside a larger enterprise back-office platform**, not a single-purpose authorization console.

The current shipped domain is **Identity & Access Operations**. The shell, navigation model, component system, and page layouts defined here must therefore satisfy two goals at the same time:

1. support the current pages and backend contracts:
   - `Dashboard`
   - `Users`
   - `Devices`
   - `Sessions`
   - `Audit Logs`
2. remain extensible for future enterprise modules such as:
   - customers / accounts
   - billing / subscriptions
   - approvals / workflows
   - operations / incidents
   - reporting / analytics
   - configuration / policy

---

## Product Positioning

### Product framing

`remote-admin` is the operator-facing frontend for the remote platform. In v1, the visible scope is concentrated in identity, device, session, and audit operations. In future phases, the same frontend should grow into a broader enterprise administration workspace.

### Current module model

The current pages should be treated as one module:

- **Module name:** `Identity & Access`
- **Module abbreviation:** `IAM`
- **Current pages:** Dashboard, Users, Devices, Sessions, Audit Logs

### UX consequence

The UI should not look like a narrow security tool. It should look like a **serious enterprise operations platform** with:

- dense but readable information
- predictable navigation
- strong operational clarity
- low-risk destructive actions
- page patterns reusable by future modules

---

## Implementation References

### Current source references

- `remote/remote-admin/src/app/App.ts`
- `remote/remote-shared/docs/admin-mvp-api-contract-v1.md`
- `remote/remote-shared/docs/error-code-matrix.md`
- `remote/remote-shared/docs/support-runbook.md`
- `remote/remote-shared/docs/remote-full-system-operating-model-v1.md`

### Current backend surface by page

| Page | Primary backend surface |
|---|---|
| Dashboard | dashboard metrics + recent failures + recent destructive actions |
| Users | `GET /admin/users`, `GET /admin/users/{id}`, `PATCH /admin/users/{id}`, `POST /admin/users/{id}/revoke`, `POST /admin/users/{id}/restore` |
| Devices | `GET /admin/devices`, `GET /admin/devices/{id}`, `POST /admin/devices/{id}/unbind`, `POST /admin/devices/{id}/disable`, `POST /admin/devices/{id}/rebind` |
| Sessions | `GET /admin/sessions`, `POST /admin/sessions/{id}/revoke` |
| Audit Logs | `GET /admin/audit-logs` |

---

## Design Direction

### Style direction

Use a hybrid of the following `ui-ux-pro-max` recommendations:

- **Data-Dense Dashboard** for core page density and operational efficiency
- **Trust & Authority** for brand tone, governance credibility, and enterprise seriousness

### Visual tone

- professional
- trustworthy
- restrained
- operational
- scalable across modules

### Anti-patterns to avoid

- looking like a marketing website
- looking like a niche one-off auth tool
- excessive gradients or playful color treatment
- overly large cards with low information density
- hiding critical actions or state changes behind hover-only affordances

---

## Global Information Architecture

## Shell model

The shell must be built as a **platform shell with module-local navigation**, even though only one module is active today.

### Header

Height: `64px`

Sections:

1. **Left cluster**
   - platform logo / wordmark
   - module switcher dropdown
   - breadcrumb trail
2. **Center cluster**
   - global search / command bar placeholder
3. **Right cluster**
   - environment badge (`Dev`, `Staging`, `Prod`)
   - API connection status
   - current role badge
   - current admin identity
   - sign out button

### Module switcher

Current state:

- selected module: `Identity & Access`
- future modules appear disabled or are omitted entirely

Implementation note:
The component must already support a multi-module menu structure, even if only one option is currently active.

### Breadcrumbs

Required because the platform is intended to grow beyond flat navigation.

Examples:

- `Platform / Identity & Access / Dashboard`
- `Platform / Identity & Access / Users`
- `Platform / Identity & Access / Audit Logs`

### Left sidebar

Width: `240px`

Sidebar is **module-local**, not platform-global.

#### Sidebar sections for current module

**Overview**
- Dashboard

**Directory**
- Users
- Devices
- Sessions

**Governance**
- Audit Logs

#### Future-ready requirement

Sidebar component must support:
- grouped sections
- active item state
- badges / counts in future
- nested items in future

---

## Global Design Tokens

### Color tokens

Use a neutral enterprise palette with blue-led trust signaling.

- `--bg-app: #F8FAFC`
- `--bg-surface: #FFFFFF`
- `--bg-surface-subtle: #F1F5F9`
- `--border-default: #CBD5E1`
- `--text-primary: #0F172A`
- `--text-secondary: #475569`
- `--text-muted: #64748B`
- `--brand-primary: #0369A1`
- `--brand-primary-hover: #075985`
- `--brand-secondary: #0EA5E9`
- `--success: #16A34A`
- `--warning: #D97706`
- `--danger: #DC2626`
- `--info: #2563EB`

### Semantic badge tones

- success: healthy / active / restored
- warning: degraded / pending / unbound / mismatch-like warning states
- danger: revoked / disabled / destructive
- neutral: unknown / informational

### Typography

- primary UI font: `Inter`
- mono font for technical identifiers: `Fira Code`

Use mono only for:
- `user_id`
- `device_id`
- `session_id`
- `request_id`
- `trace_id`

### Spacing

- page padding: `24px`
- card padding: `16px` desktop, `14px` dense mode
- section gap: `16px`
- control height: `40px`
- table row height: `44px` to `48px`

### Radius and elevation

- card radius: `12px`
- control radius: `10px`
- dialogs: `14px`
- rely primarily on borders, not large shadows

---

## Global Component Contract

The following reusable components must exist before page polish work proceeds:

- `AppShell`
- `PlatformHeader`
- `ModuleSidebar`
- `Breadcrumbs`
- `EnvironmentBadge`
- `ConnectionStatusBadge`
- `RoleBadge`
- `PageHeader`
- `Toolbar`
- `FilterBar`
- `FilterChipRow`
- `MetricCard`
- `DataTable`
- `DetailPanel`
- `SummaryGrid`
- `StatusBadge`
- `InlineEmptyState`
- `RetryBanner`
- `SkeletonBlock`
- `Toast`
- `ConfirmDialog`
- `JsonViewer`
- `IdPill`
- `TimestampCell`

---

## Global Behavior Rules

### Async feedback

Per `ui-ux-pro-max`, all async actions must show visible feedback.

Requirements:
- initial page load uses skeletons
- list refresh uses loading overlay or inline progress
- detail pane refresh uses local skeleton
- destructive action buttons show in-flight labels

### Accessibility

Requirements:
- visible focus ring on every interactive control
- keyboard tab order follows visual order
- skip link: `Skip to main content`
- heading hierarchy must remain sequential
- no keyboard traps in dialogs or drawers

### Sticky navigation rule

If header or filter bars are sticky, content spacing must compensate so no title, filter row, or first table row is obscured.

### Back / history rule

Navigation must preserve browser back behavior. Do not replace history for ordinary route changes.

### Role-aware behavior

For `support_readonly`:
- show all read surfaces
- disable all write actions
- show explicit reason text, not just disabled styling

### Error semantics

Front-end messaging should map to canonical backend error codes where available:

- `forbidden`
- `not_found`
- `too_many_requests`
- `network_timeout`
- `invalid_credentials`

### Destructive action rule

The following actions must always use confirmation dialogs with required reason text:

- revoke user
- restore user
- unbind device
- disable device
- rebind device
- revoke session

---

# Page Specs

---

## 1. Dashboard

### Route

`#/dashboard`

### Position in platform

This is the **module overview page** for Identity & Access today, but the layout must establish the pattern for future module dashboards.

### Page goal

Enable an operator to answer the following within 5 to 10 seconds:

- What is unhealthy right now?
- What requires follow-up?
- Where should I drill next?

### Layout

Three vertical bands:

1. KPI strip
2. operational insight strip
3. work queue and recent governance strip

### Page header

**Title:** `Identity & Access Dashboard`

**Subtitle:** `Operational overview of users, devices, sessions, failures, and governance activity.`

Header actions:
- `Refresh`
- optional future action: `Export snapshot`

### Section A: KPI strip

Grid behavior:
- desktop large: 4 columns
- desktop standard: 2 columns
- mobile: 1 column

Cards:
1. Active Sessions
2. Login Failures
3. Device Mismatches
4. Destructive Actions

Each card contains:
- label
- current value
- short hint
- delta or freshness metadata if available later
- click target for drilldown

#### KPI click mapping

- Active Sessions -> Sessions page
- Login Failures -> Audit Logs filtered to failure events
- Device Mismatches -> Audit Logs filtered to device mismatch related events
- Destructive Actions -> Audit Logs filtered to destructive admin actions

### Section B: Operational insight strip

Two-column layout on desktop.

#### Left: Trend widget

Widget title: `Failure & anomaly trend`

Chart type:
- line chart with anomaly markers

Requirements:
- hover tooltip
- anomaly point marker in danger color
- click anomaly opens Audit Logs with a prefilled time range

If no chart data exists yet:
- keep the widget container
- show a structured empty state: `Trend data is not available yet. Recent event streams remain available below.`

#### Right: Critical event stream

Widget title: `Recent critical events`

Rows show:
- event type
- actor id
- target summary
- created at
- severity badge

Click behavior:
- opens Audit Logs with focus on the matching record if possible

### Section C: Operations follow-up strip

Two cards:

#### Left card

Title: `Recent destructive actions`

Shows the latest revoke / disable / unbind / rebind style operations.

#### Right card

Title: `Follow-up queue`

Current v1 implementation can synthesize entries from recent failures and destructive actions.

Future-ready note:
This card is intentionally generic and should later support tasks from non-IAM modules.

### Section D: Workspace context card

Title: `Current workspace`

Fields:
- current admin display name
- current role
- session id
- session expires at
- metrics generated at

Use mono styling for session id.

### Components

- `PageHeader`
- `MetricCard`
- `InsightChartCard`
- `EventListCard`
- `WorkQueueCard`
- `WorkspaceContextCard`

### States

#### Loading
- 4 metric skeletons
- chart skeleton
- two list skeletons

#### Error
- each section retries independently
- do not blank the whole page if one widget fails

#### Empty
- metrics may show `0`
- list widgets show explanatory empty states

### Acceptance criteria

- operator can drill from each top KPI to the relevant page
- dashboard never appears empty without explanatory messaging
- all widgets render safely with partial backend data

---

## 2. Users

### Route

`#/users`

### Position in platform

This is the current **person / account workspace** for the IAM module. In the future platform, this page pattern should be reusable for other business entities.

### Page goal

Support fast lookup, inspection, and controlled mutation of a managed user record.

### Layout

Desktop layout:
- top filter bar
- main table area
- right detail panel

Column split:
- main table: flexible
- detail panel: `420px`

Mobile:
- detail opens in drawer
- table becomes horizontally scrollable

### Page header

**Title:** `Users`

**Subtitle:** `Search and manage user state, license state, entitlements, and related operational context.`

Actions:
- `Refresh`

### Filter bar

Fields:
- Search
- Status
- License Status

Buttons:
- Apply filters
- Clear filters

Search placeholder:
- `Search by username, display name, email, or user id`

Optional secondary row:
- active filter chips
- current result count

### Table

Columns:
- Name
- Username
- Status
- License
- Entitlements Count
- Device Count
- Last Seen

Cell rules:
- Name uses display name, fallback to username
- Username secondary text style
- Status and License use badges
- Last Seen uses timestamp formatting

Row interaction:
- click row selects it
- selected row receives border + subtle surface highlight
- keyboard selection supported

### Detail panel structure

#### Section A: Identity summary
- User ID
- Username
- Display Name
- Email
- Tenant ID

#### Section B: Access state
- User Status
- License Status
- License Expires At
- Entitlements list

#### Section C: Related operations summary
- Device Count
- Last Seen
- quick links:
  - View Devices for this user
  - View Sessions for this user
  - View Audit Logs for this user

#### Section D: Edit form
Fields:
- Display Name
- License Status
- License Expires At
- Entitlements CSV

Buttons:
- Save Changes
- Reset

#### Section E: Destructive / recovery actions
Buttons:
- Revoke User
- Restore User

### Dialogs

#### Revoke user dialog
Fields:
- user summary
- impact note
- reason textarea (required)

Impact note:
`Revoking a user may invalidate future auth continuity and requires the user to re-authenticate after restoration.`

#### Restore user dialog
Fields:
- user summary
- reason textarea (required)

### Permission behavior

#### `super_admin` / `auth_admin`
- full write access

#### `support_readonly`
- detail visible
- edit form disabled
- revoke / restore disabled
- inline note shown:
  `This role is read-only. Escalate to auth_admin or super_admin for write actions.`

### Components

- `PageHeader`
- `FilterBar`
- `FilterChipRow`
- `DataTable`
- `DetailPanel`
- `SummaryGrid`
- `FormSection`
- `ConfirmDialog`

### States

#### Loading
- table skeleton rows
- detail skeleton when switching rows

#### Error
- list errors and detail errors handled separately

#### Empty
- `No users matched the current filters.`

### Acceptance criteria

- operator can search users by all currently supported identifiers
- selected user can be edited without losing filter context
- role restrictions are visually obvious
- quick links carry the user filter into Devices, Sessions, and Audit Logs

---

## 3. Devices

### Route

`#/devices`

### Position in platform

This is the current **asset / endpoint registry workspace** for the IAM module. The page pattern should later generalize to hardware assets, clients, or managed endpoints in other modules.

### Page goal

Allow operators to inspect binding state and safely perform device unbind, disable, or rebind actions.

### Layout

Same structural pattern as Users:
- filter bar
- main table
- right detail panel

### Page header

**Title:** `Devices`

**Subtitle:** `Inspect device binding, ownership, status, version, and operational history.`

Actions:
- `Refresh`

### Filter bar

Fields:
- Search
- Device Status
- User ID

Search placeholder:
- `Search by device id, user id, or client version`

Buttons:
- Apply filters
- Clear filters

### Table

Columns:
- Device ID
- Bound User
- Status
- Client Version
- First Bound
- Last Seen

Cell rules:
- Device ID uses mono styling
- Bound User links to Users context in future, plain text in v1 if needed
- Status uses badge

### Detail panel structure

#### Section A: Device summary
- Device ID
- Bound User ID
- Device Status
- Client Version

#### Section B: Lifecycle
- First Bound At
- Last Seen At

#### Section C: Related links
- View User
- View Sessions for this device
- View Audit Logs for this device

#### Section D: Action form
Fields for rebind:
- Target User ID
- Client Version

Buttons:
- Rebind Device
- Unbind Device
- Disable Device

### Dialogs

#### Unbind device dialog
Content:
- device summary
- current bound user
- reason textarea required
- warning note:
  `Unbinding may cause future device mismatch failures for the current owner.`

#### Disable device dialog
Content:
- device summary
- reason textarea required
- warning note:
  `Disabling blocks future valid use of this device until operational recovery.`

#### Rebind device confirmation
Content:
- current user
- target user
- client version
- reason textarea required

### Permission behavior

Same as Users.

### Components

- `DataTable`
- `DetailPanel`
- `SummaryGrid`
- `InlineWarningBlock`
- `ConfirmDialog`

### States

#### Loading
- table and detail skeletons

#### Error
- retry banner in list or detail scope

#### Empty
- `No devices matched the current filters.`

### Acceptance criteria

- operator can identify device ownership quickly
- rebind flow makes current and target ownership explicit
- destructive actions never execute without confirmation and reason
- device page can deep-link from audit or user contexts

---

## 4. Sessions

### Route

`#/sessions`

### Position in platform

This is the current **runtime activity workspace** for active and historical auth sessions. In the future platform, it should influence patterns for jobs, runs, live connections, or process-oriented records.

### Page goal

Help operators locate a session quickly, inspect its current auth state, and revoke it when immediate cut-off is required.

### Layout

Same master-detail pattern as Users and Devices.

### Page header

**Title:** `Sessions`

**Subtitle:** `Inspect session lifecycle, auth state, user/device linkage, and revoke active continuity when necessary.`

Actions:
- `Refresh`

### Filter bar

Fields:
- Search
- Auth State
- User ID
- Device ID

Search placeholder:
- `Search by session id, user id, or device id`

Buttons:
- Apply filters
- Clear filters

### Table

Columns:
- Session ID
- User
- Device
- Auth State
- Issued At
- Expires At
- Last Seen

Cell rules:
- Session ID uses mono styling
- Auth State uses semantic badge
- timestamps use compact format with hover full timestamp

### Detail panel structure

#### Section A: Session summary
- Session ID
- User ID
- Device ID
- Auth State

#### Section B: Lifecycle
- Issued At
- Expires At
- Last Seen At

#### Section C: Follow-up links
- View User
- View Device
- View Audit Logs for this session

#### Section D: Action area
Button:
- Revoke Session

### Revoke session dialog
Content:
- session summary
- reason textarea required
- warning note:
  `Revoking a session immediately invalidates further continuity for this session.`

### Permission behavior

Same as Users and Devices.

### Components

- `DataTable`
- `DetailPanel`
- `SummaryGrid`
- `ConfirmDialog`

### States

#### Loading
- table skeleton rows
- detail skeleton

#### Error
- preserve filters and selection when possible

#### Empty
- `No sessions matched the current filters.`

### Acceptance criteria

- operator can find a session by session, user, or device id
- revoke action is prominently available but safely guarded
- session state is visually scannable in both list and detail views

---

## 5. Audit Logs

### Route

`#/audit-logs`

### Position in platform

This is the current **governance and investigation workspace**. In the future platform, it should evolve into a cross-module activity and audit center.

### Page goal

Support operational investigation, root-cause tracing, and evidence gathering.

### Layout

Desktop:
- advanced filter bar at top
- results table below
- right detail panel for selected event

Mobile:
- filters collapse into expandable section
- detail becomes drawer

### Page header

**Title:** `Audit Logs`

**Subtitle:** `Trace operator and system-visible events by actor, target, time, and request context.`

Actions:
- `Refresh`
- future: `Export results`

### Filter bar

Fields:
- Event Type
- Actor ID
- Target User ID
- Target Device ID
- Target Session ID
- Created From
- Created To
- Limit
- Offset

Buttons:
- Refresh Audit Logs
- Clear Filters
- Previous Page
- Next Page

Secondary row:
- active filter chips
- current result summary
- rendered query preview

Quick filter presets:
- Login Failures
- Device Mismatches
- Destructive Actions
- Permission Denials

### Table

Columns:
- Event Type
- Severity
- Actor
- Target Summary
- Request ID
- Trace ID
- Created At

#### Severity mapping

- destructive admin actions -> danger
- failure / denied / mismatch -> warning or danger
- ordinary read / lookup / refresh style events -> neutral

#### Target summary format

Show whichever exist:
- user
- device
- session

Example:
- `user:u_1 / device:device_3`

### Detail panel structure

#### Section A: Event summary
- Event Type
- Severity
- Created At

#### Section B: Correlation identifiers
- Actor ID
- Request ID
- Trace ID

#### Section C: Target identifiers
- Target User ID
- Target Device ID
- Target Session ID

#### Section D: Highlighted details
If present, emphasize these keys first:
- reason
- required_permission
- user_id
- device_id
- session_id

#### Section E: Raw structured details
- pretty JSON viewer
- collapsible by default on narrow screens

### Detail panel interactions

Clickable items:
- Actor ID -> future actor page or prefilled audit filter
- Target User ID -> Users page with user preselected
- Target Device ID -> Devices page with device preselected
- Target Session ID -> Sessions page with session preselected
- Request ID -> copy
- Trace ID -> copy

### Pagination behavior

- show `Showing X of Y`
- preserve filters while paging
- next / previous buttons disabled appropriately

### Components

- `AdvancedFilterBar`
- `FilterChipRow`
- `DataTable`
- `JsonViewer`
- `CopyableMonoField`

### States

#### Loading
- keep previous results visible if possible
- show table overlay progress

#### Error
- preserve filter state
- allow retry

#### Empty
- `No audit events matched the current filters.`

### Acceptance criteria

- operator can reconstruct an incident trail using actor, target, and request identifiers
- page supports deep links from dashboard and detail pages
- event details remain readable even when payload shape varies

---

## Shared Responsive Rules

### >= 1280px
- full shell
- sidebar always visible
- detail panel docked right

### 1024px to 1279px
- sidebar visible
- detail panel may reduce to `380px`

### 768px to 1023px
- sidebar collapsible
- detail panel becomes narrower or toggleable
- tables remain horizontally scrollable

### < 768px
- use drawer for detail view
- tables inside `overflow-x-auto`
- filter sections can collapse
- maintain access to destructive actions inside detail drawer only

---

## Cross-Page Interaction Rules

### Deep linking

Pages must support query-backed entry from other pages.

Examples:
- Dashboard -> Audit Logs with preset filters
- Users -> Devices filtered by user id
- Users -> Sessions filtered by user id
- Devices -> Audit Logs filtered by device id
- Sessions -> Audit Logs filtered by session id

### Selection persistence

When a filter refresh still contains the selected entity, preserve selection.

### Copy behavior

The following identifiers must be individually copyable:
- user id
- device id
- session id
- request id
- trace id

### Toast behavior

Success toast examples:
- `User updated successfully.`
- `User restored successfully.`
- `Device rebound successfully.`
- `Session revoked successfully.`

Error toast examples should map backend semantics rather than invent new categories.

---

## Frontend Delivery Order

### Phase A: shell and primitives
- App shell
- header
- sidebar
- filter bar
- table
- detail panel
- status badge
- dialog
- toast

### Phase B: current IAM pages
- Dashboard
- Users
- Devices
- Sessions
- Audit Logs

### Phase C: future platform readiness
- module switcher activation
- breadcrumb depth expansion
- global search / command bar
- reusable entity workspace patterns for non-IAM modules

---

## Done Criteria

This UI spec is satisfied when:

1. all five pages share one coherent platform shell
2. all list-heavy pages use the same master-detail pattern
3. read-only roles are clearly constrained in UI
4. destructive actions are confirmed and reasoned
5. navigation and component patterns are reusable for future business modules
6. the product looks like an enterprise platform, not a narrow one-off security tool
