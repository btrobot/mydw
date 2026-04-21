# Product Redesign: Material Pack Model

> Date: 2026-04-07 | Author: Tech Lead | Status: Proposed

## 1. Core Concept

**Product = Virtual Material Pack**

A Product is not a "product" in the e-commerce sense. It is a container that groups materials (videos, covers, copywritings, topics) sourced from a single Dewu page URL.

```
Product (Material Pack)
├── dewu_url          ← source identifier (unique)
├── name              ← auto-filled from page title on parse
├── videos[]          ← downloaded from Dewu page
│   └── covers[]      ← extracted from video / page
├── copywritings[]    ← page title as copywriting
└── topics[]          ← hashtags from page content
```

The lifecycle is: **create pack from URL -> parse to fill materials -> use materials in tasks**.

## 2. Current State Analysis

### What works

- Create: accepts share_text, extracts dewu_url, creates empty Product
- Parse: `POST /{id}/parse-materials` fetches page, downloads media, replaces all materials
- Detail: returns Product + all nested materials
- Delete: detaches materials (sets product_id=NULL), deletes Product

### Problems

| # | Problem | Impact |
|---|---------|--------|
| P1 | Create + Parse are two separate steps. User must create first, then click "parse" | Extra click, empty product exists with no materials |
| P2 | Product.name defaults to dewu_url on create, only gets real title after parse | Confusing list display before parse |
| P3 | Product has `link`, `description`, `image_url` fields that are never populated by parse | Dead columns, confusing schema |
| P4 | Delete sets `product_id=NULL` on videos/copywritings instead of deleting them | Orphaned materials accumulate |
| P5 | ProductList fetches video/copywriting counts via N+1 queries (separate hooks per row) | Performance issue on list page |
| P6 | No re-parse feedback -- parse replaces everything silently, user can't see what changed | UX gap |

## 3. Proposed Design

### 3.1 Operation Flow

#### Create (merge create + parse into one step)

```
User pastes share_text
  → Backend extracts dewu_url
  → Backend checks dewu_url uniqueness
  → Backend creates Product row (name = dewu_url, placeholder)
  → Backend immediately triggers parse_and_create_materials()
  → Returns ProductDetailResponse with all materials populated
```

Single endpoint: `POST /products` -- accepts `share_text`, returns full detail.

The old two-step flow (create empty, then parse) becomes one atomic operation.

#### Re-parse (refresh materials)

Keep `POST /products/{id}/parse-materials` for manual refresh.

Use case: Dewu page updated, user wants to re-fetch. This is an explicit "refresh" action, not a creation step.

#### Edit

Only allow editing `name`. Remove `link`, `description`, `image_url` from update schema -- these fields serve no purpose in the material-pack model.

`dewu_url` should be read-only after creation (changing it would mean a different product).

#### Delete

Two options to decide:

| Option | Behavior | Pros | Cons |
|--------|----------|------|------|
| A: Cascade delete | Delete product + all associated materials (videos, covers, copywritings, topic links) | Clean, no orphans | Irreversible, loses downloaded files |
| B: Detach (current) | Set product_id=NULL, keep materials | Materials reusable | Orphan accumulation |

**Recommendation**: Option A (cascade delete). Materials parsed from Dewu are cheap to re-fetch. Orphaned materials with no product association create confusion. If a user wants to keep specific materials, they should be able to detach them individually before deleting the product -- but that's a future feature.

### 3.2 Data Model Changes

#### Product table -- drop unused columns

```sql
-- Remove these columns (never populated):
ALTER TABLE products DROP COLUMN link;
ALTER TABLE products DROP COLUMN description;
ALTER TABLE products DROP COLUMN image_url;
```

#### Add material counts to Product (denormalized)

```sql
ALTER TABLE products ADD COLUMN video_count INTEGER DEFAULT 0;
ALTER TABLE products ADD COLUMN cover_count INTEGER DEFAULT 0;
ALTER TABLE products ADD COLUMN copywriting_count INTEGER DEFAULT 0;
ALTER TABLE products ADD COLUMN topic_count INTEGER DEFAULT 0;
ALTER TABLE products ADD COLUMN parse_status VARCHAR(32) DEFAULT 'pending';
-- parse_status: pending | parsing | parsed | error
```

This eliminates the N+1 query problem on the list page. Counts are updated atomically during parse.

#### Cover: add direct product_id FK

Currently covers link to products only through videos (cover -> video -> product). This is fragile -- if a page has covers but no video, they can't be associated.

```sql
ALTER TABLE covers ADD COLUMN product_id INTEGER REFERENCES products(id);
```

### 3.3 API Changes

#### `POST /products` -- create + parse (atomic)

Request (unchanged):
```json
{ "share_text": "..." }
```

Response changes to `ProductDetailResponse` (status 201). Backend now:
1. Extracts dewu_url
2. Checks uniqueness
3. Creates Product
4. Calls `parse_and_create_materials()`
5. Returns full detail

If parse fails, the product is still created (with `parse_status = "error"`), so the user can retry via re-parse.

#### `PUT /products/{id}` -- simplified

Request:
```json
{ "name": "..." }
```

Remove `link`, `description`, `dewu_url`, `image_url` from `ProductUpdate`.

#### `DELETE /products/{id}` -- cascade

Deletes product + all associated videos, covers, copywritings, and product_topic links. Returns 204.

#### `GET /products` -- include counts

Response item adds:
```json
{
  "id": 1,
  "name": "...",
  "dewu_url": "...",
  "video_count": 2,
  "cover_count": 5,
  "copywriting_count": 1,
  "topic_count": 3,
  "parse_status": "parsed",
  "created_at": "...",
  "updated_at": "..."
}
```

No more N+1 queries from frontend.

#### `POST /products/{id}/parse-materials` -- keep as-is

For manual re-parse. After completion, update denormalized counts.

### 3.4 Frontend Changes

#### ProductList.tsx

- Remove `ProductCountCell` component (no more per-row queries)
- Read `video_count`, `copywriting_count` directly from list response
- Show `parse_status` as a tag (parsed / parsing / error)
- "Add Product" modal: after submit, show loading state while parse runs, then navigate to detail on success
- Remove "parse" button from list row actions (parse happens on create; re-parse is on detail page)

#### ProductDetail.tsx

- Remove edit fields for `link`, `description`, `image_url`
- Keep "Re-parse" button for refresh
- Show `parse_status` indicator
- Edit modal: only `name` field

#### Schemas (frontend types)

```typescript
interface ProductResponse {
  id: number
  name: string
  dewu_url: string | null
  video_count: number
  cover_count: number
  copywriting_count: number
  topic_count: number
  parse_status: 'pending' | 'parsing' | 'parsed' | 'error'
  created_at: string
  updated_at: string
}
```

Remove `link`, `description`, `image_url` from `ProductResponse`.

## 4. Migration Plan

| Step | Scope | Description |
|------|-------|-------------|
| M1 | Backend | Migration: drop `link`, `description`, `image_url` from products; add count columns + `parse_status` |
| M2 | Backend | Migration: add `product_id` to covers table |
| M3 | Backend | Backfill: compute counts for existing products |
| M4 | Backend | Update `ProductCreate` flow: create + parse atomic |
| M5 | Backend | Update `ProductUpdate` schema: name only |
| M6 | Backend | Update delete: cascade delete materials |
| M7 | Backend | Update `ProductResponse` / `ProductListResponse` schemas |
| M8 | Backend | Update parse service: maintain denormalized counts |
| M9 | Frontend | Update types, hooks, ProductList, ProductDetail |

## 5. Decision Required

Before implementation, need your call on:

1. **Delete behavior**: Cascade delete (recommended) vs. detach (current)?
2. **Create atomicity**: If parse fails mid-way, should we keep the product with `parse_status=error` (recommended) or rollback the entire creation?
3. **Scope of column removal**: OK to drop `link`, `description`, `image_url` from products table? Any downstream usage I'm not seeing?
