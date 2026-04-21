# Media Storage Design: Content-Addressable Deduplication

> Status: Proposed | Date: 2026-04-07 | Author: Tech Lead

## 1. Problem

- `product_parse_service` downloads files as `{product_id}_{timestamp}.ext` -- re-parsing the same product creates duplicate files
- Different products may reference the same media (e.g., shared promotional video)
- Delete logic unconditionally removes physical files -- if two DB records pointed to the same file, deleting one would break the other
- `Cover` and `Audio` models lack `file_hash`, so dedup is impossible for those types
- Video upload has hash-based dedup (SP8-01) but rejects duplicates instead of sharing the physical file

## 2. Design

### 2.1 Storage Layout

```
data/materials/
  videos/   {sha256_hex16}.mp4
  covers/   {sha256_hex16}.jpg
  audios/   {sha256_hex16}.mp3
```

Files are named by the first 16 hex characters of their SHA-256 hash plus the original extension. This gives 64-bit collision resistance -- sufficient for a local tool with < 1M files.

No subdirectory sharding (e.g., `ab/cd/...`). The expected file count per type is in the hundreds, not millions.

### 2.2 Database Changes

#### Add `file_hash` to Cover and Audio

```python
# Cover model -- add column
file_hash = Column(String(64), nullable=True, index=True)

# Audio model -- add column
file_hash = Column(String(64), nullable=True, index=True)
```

#### Add index on Video.file_hash

```python
# Video model -- add index (column already exists)
file_hash = Column(String(64), nullable=True, index=True)
```

Migration: `011_media_hash_columns` -- add `file_hash` to `covers` and `audios`, add index on `videos.file_hash`.

### 2.3 Core Service: `MediaStorageService`

New file: `backend/services/media_storage.py`

```python
class MediaStorageService:
    """Content-addressable media file storage with reference counting."""

    async def store_from_url(
        self, url: str, media_type: str, extension: str,
    ) -> tuple[str, str, int]:
        """
        Download URL to content-addressed storage.
        Returns (file_path, file_hash, file_size).
        Skips download if hash already exists on disk.
        """
        # 1. Download to temp file
        # 2. Compute SHA-256
        # 3. If target path exists and size matches -> delete temp, return existing
        # 4. Else rename temp -> target
        ...

    async def store_from_path(
        self, source_path: str, media_type: str,
    ) -> tuple[str, str, int]:
        """
        Move/copy a local file into content-addressed storage.
        Returns (file_path, file_hash, file_size).
        """
        ...

    async def safe_delete(
        self, db: AsyncSession, file_hash: str, media_type: str,
    ) -> bool:
        """
        Delete physical file only if no other DB record references this hash.
        Returns True if file was deleted.
        """
        # Count references across Video, Cover, Audio tables
        # If total refs == 0 -> unlink file, return True
        # Else -> return False
        ...
```

`media_type` is one of `"videos"`, `"covers"`, `"audios"` -- maps directly to the subdirectory.

### 2.4 Download Flow (product_parse_service)

Current:
```
download URL -> save as {product_id}_{timestamp}.ext -> create DB record
```

Proposed:
```
download URL -> temp file -> compute hash -> if hash exists on disk, skip
                                           -> else rename to {hash16}.ext
-> create DB record with file_hash + file_path
```

Key change in `parse_and_create_materials`:

```python
# Before downloading, check if we already have this content
# (We can't check before download since we don't know the hash yet)
# But we CAN skip re-download if the DB record already has the hash

storage = MediaStorageService()

if pack.video_url:
    path, hash, size = await storage.store_from_url(
        pack.video_url, "videos", ".mp4"
    )
    downloaded_videos.append((path, hash, size))
```

### 2.5 Delete Flow (reference counting)

Current:
```
delete DB record -> unconditionally unlink file
```

Proposed:
```
delete DB record -> count remaining records with same file_hash
                 -> if count == 0: unlink file
                 -> else: keep file (other records still reference it)
```

Reference count query:

```python
async def count_hash_refs(db: AsyncSession, file_hash: str) -> int:
    """Count total DB records referencing this hash across all media tables."""
    total = 0
    for model in (Video, Cover, Audio):
        result = await db.execute(
            select(func.count()).select_from(model).where(model.file_hash == file_hash)
        )
        total += result.scalar() or 0
    return total
```

The delete endpoints in `video.py`, `cover.py`, `audio.py` will call `safe_delete` after removing the DB record, instead of unconditionally unlinking.

### 2.6 Upload Flow (video upload)

Current behavior (SP8-01): reject duplicate upload with HTTP 409.

Proposed: keep the reject behavior for user uploads. Users uploading the same file twice is likely a mistake. The content-addressed storage is primarily for automated downloads (parse service).

For scan import: compute hash, store in content-addressed path, skip if hash already in DB.

## 3. Edge Cases

| Case | Handling |
|------|----------|
| Hash collision (different content, same 16-char prefix) | Extremely unlikely at 64 bits. If it happens, the second file silently reuses the first. Acceptable risk for a local tool. Full 64-char hash is stored in DB for future verification if needed. |
| Download fails mid-stream | Temp file is cleaned up. No hash entry created. |
| File deleted from disk but DB record exists | `file_exists` field on VideoResponse already handles this. Store/download will recreate the file. |
| Concurrent downloads of same URL | Both write to temp files, both compute same hash. Second rename is a no-op (file already exists). No data loss. |
| Re-parse same product | Old DB records are deleted (current behavior). `safe_delete` checks refs before unlinking. New records are created pointing to same hash -- no re-download needed since file exists. |
| Migration of existing files | One-time script: compute hash for all existing files, rename to hash-based name, update `file_path` in DB. |

## 4. What Does NOT Change

- `MATERIAL_BASE_PATH` and user-managed files (scan import source) -- untouched
- Video upload dedup (SP8-01 reject behavior) -- kept as-is
- DB schema for `file_path` -- still stores the absolute path, just the path now uses hash-based naming
- API response models -- no change
- Frontend -- no change

## 5. Architecture Decision

```
ADR-003: Content-Addressable Media Storage

Status: Proposed

Context:
  Product parsing downloads duplicate files. No dedup for covers/audios.
  Delete logic can break shared files.

Decision:
  Files stored by SHA-256 hash prefix. DB stores hash for reference counting.
  Physical delete only when zero references remain.

Consequences:
  [+] Eliminates duplicate files on disk
  [+] Safe deletion with reference counting
  [+] Faster re-parse (skip existing files)
  [-] One-time migration needed for existing files
  [-] Slightly more complex delete logic
  [~] 16-char hash prefix has theoretical collision risk (acceptable)
```

## 6. Implementation Tasks

### Task 1: Migration -- add hash columns (Backend Lead)
- Add `file_hash` column (String(64), indexed) to `covers` and `audios` tables
- Add index on existing `videos.file_hash`
- Migration file: `011_media_hash_columns.py`
- Estimate: small

### Task 2: MediaStorageService (Backend Lead)
- Create `backend/services/media_storage.py`
- Implement `store_from_url`, `store_from_path`, `safe_delete`, `count_hash_refs`
- Unit tests for each method
- Estimate: medium

### Task 3: Refactor product_parse_service (Backend Lead)
- Replace direct `download_file` calls with `MediaStorageService.store_from_url`
- Pass `file_hash` when creating Video/Cover records
- Estimate: small

### Task 4: Refactor delete endpoints (Backend Lead)
- Update `video.py`, `cover.py`, `audio.py` delete handlers
- Replace unconditional `unlink()` with `MediaStorageService.safe_delete`
- Estimate: small

### Task 5: Existing file migration script (Backend Lead)
- One-time script: compute hashes, rename files, update DB paths
- Run manually, idempotent
- Estimate: small

### Task 6: Update scan import (Backend Lead)
- Use `store_from_path` for scanned files
- Hash-based dedup instead of path-based dedup
- Estimate: small

Suggested order: Task 1 -> Task 2 -> Task 3 + Task 4 (parallel) -> Task 5 -> Task 6
