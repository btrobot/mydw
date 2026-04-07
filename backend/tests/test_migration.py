"""
Integration tests for migration 004 — Material table data split (SP1-07).

Constructs Material test data directly via SQL, runs the migration,
then verifies the target tables contain the correct records.
"""
import importlib
import sys
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

backend_root = str(Path(__file__).parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Module name starts with a digit — must use importlib
_migration_004 = importlib.import_module("migrations.004_material_split")
run_migration = _migration_004.run_migration


# ============================================================================
# Helpers
# ============================================================================

async def _insert_material(
    engine: AsyncEngine,
    *,
    mat_type: str,
    name: str | None = None,
    path: str | None = None,
    content: str | None = None,
    size: int | None = None,
    duration: int | None = None,
    product_id: int | None = None,
) -> None:
    """Insert a row directly into the materials table."""
    now = datetime.utcnow()
    async with engine.begin() as conn:
        await conn.exec_driver_sql(
            """
            INSERT INTO materials
                (type, name, path, content, size, duration, product_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (mat_type, name, path, content, size, duration, product_id, now, now),
        )


async def _count(engine: AsyncEngine, table: str) -> int:
    async with engine.begin() as conn:
        result = await conn.exec_driver_sql(f"SELECT COUNT(*) FROM {table}")
        return result.fetchone()[0]


async def _fetch_all(engine: AsyncEngine, table: str) -> list[dict]:
    async with engine.begin() as conn:
        col_info = (
            await conn.exec_driver_sql(f"PRAGMA table_info({table})")
        ).fetchall()
        col_names = [c[1] for c in col_info]
        rows = (await conn.exec_driver_sql(f"SELECT * FROM {table}")).fetchall()
    return [dict(zip(col_names, row)) for row in rows]


# ============================================================================
# Tests
# ============================================================================

class TestMaterialSplitMigration:

    @pytest.mark.asyncio
    async def test_material_split_migration_videos(self, engine: AsyncEngine) -> None:
        """video 类型 material → videos 表"""
        await _insert_material(
            engine,
            mat_type="video",
            name="clip_001.mp4",
            path="videos/clip_001.mp4",
            size=2048000,
            duration=60,
        )

        await run_migration(engine)

        rows = await _fetch_all(engine, "videos")
        paths = [r["file_path"] for r in rows]
        assert "videos/clip_001.mp4" in paths

        matched = next(r for r in rows if r["file_path"] == "videos/clip_001.mp4")
        assert matched["name"] == "clip_001.mp4"
        assert matched["file_size"] == 2048000
        assert matched["duration"] == 60
        assert matched["source_type"] == "original"

    @pytest.mark.asyncio
    async def test_material_split_migration_copywritings(self, engine: AsyncEngine) -> None:
        """text 类型 material → copywritings 表"""
        await _insert_material(
            engine,
            mat_type="text",
            content="这是迁移测试文案",
        )

        await run_migration(engine)

        rows = await _fetch_all(engine, "copywritings")
        contents = [r["content"] for r in rows]
        assert "这是迁移测试文案" in contents

        matched = next(r for r in rows if r["content"] == "这是迁移测试文案")
        assert matched["source_type"] == "manual"

    @pytest.mark.asyncio
    async def test_material_split_migration_covers(self, engine: AsyncEngine) -> None:
        """cover 类型 material → covers 表"""
        await _insert_material(
            engine,
            mat_type="cover",
            path="covers/thumb_001.jpg",
            size=51200,
        )

        await run_migration(engine)

        rows = await _fetch_all(engine, "covers")
        paths = [r["file_path"] for r in rows]
        assert "covers/thumb_001.jpg" in paths

    @pytest.mark.asyncio
    async def test_material_split_migration_audios(self, engine: AsyncEngine) -> None:
        """audio 类型 material → audios 表"""
        await _insert_material(
            engine,
            mat_type="audio",
            name="bgm_001.mp3",
            path="audios/bgm_001.mp3",
            size=3072000,
            duration=180,
        )

        await run_migration(engine)

        rows = await _fetch_all(engine, "audios")
        paths = [r["file_path"] for r in rows]
        assert "audios/bgm_001.mp3" in paths

        matched = next(r for r in rows if r["file_path"] == "audios/bgm_001.mp3")
        assert matched["name"] == "bgm_001.mp3"
        assert matched["duration"] == 180

    @pytest.mark.asyncio
    async def test_material_split_migration_topics(self, engine: AsyncEngine) -> None:
        """topic 类型 material → topics 表"""
        await _insert_material(
            engine,
            mat_type="topic",
            name="得物好物推荐",
        )

        await run_migration(engine)

        rows = await _fetch_all(engine, "topics")
        names = [r["name"] for r in rows]
        assert "得物好物推荐" in names

    @pytest.mark.asyncio
    async def test_migration_is_idempotent(self, engine: AsyncEngine) -> None:
        """迁移幂等性 — 重复执行不产生重复记录"""
        await _insert_material(
            engine,
            mat_type="video",
            name="idempotent.mp4",
            path="videos/idempotent.mp4",
        )

        await run_migration(engine)
        count_after_first = await _count(engine, "videos")

        await run_migration(engine)
        count_after_second = await _count(engine, "videos")

        assert count_after_first == count_after_second

    @pytest.mark.asyncio
    async def test_migration_empty_table(self, engine: AsyncEngine) -> None:
        """materials 表为空时迁移不报错"""
        await run_migration(engine)

        assert await _count(engine, "videos") == 0
        assert await _count(engine, "copywritings") == 0
        assert await _count(engine, "topics") == 0

    @pytest.mark.asyncio
    async def test_migration_mixed_types(self, engine: AsyncEngine) -> None:
        """多种类型混合迁移 — 各目标表各得其所"""
        await _insert_material(engine, mat_type="video", name="v.mp4", path="videos/v.mp4")
        await _insert_material(engine, mat_type="text", content="文案内容")
        await _insert_material(engine, mat_type="cover", path="covers/c.jpg")
        await _insert_material(engine, mat_type="audio", name="a.mp3", path="audios/a.mp3")
        await _insert_material(engine, mat_type="topic", name="话题名称")

        await run_migration(engine)

        assert await _count(engine, "videos") >= 1
        assert await _count(engine, "copywritings") >= 1
        assert await _count(engine, "covers") >= 1
        assert await _count(engine, "audios") >= 1
        assert await _count(engine, "topics") >= 1

    @pytest.mark.asyncio
    async def test_migration_skips_missing_path(self, engine: AsyncEngine) -> None:
        """path 为 None 的 video material 应被跳过"""
        await _insert_material(engine, mat_type="video", name="no_path.mp4", path=None)

        await run_migration(engine)

        assert await _count(engine, "videos") == 0

    @pytest.mark.asyncio
    async def test_migration_preserves_product_id(self, engine: AsyncEngine) -> None:
        """product_id 应正确传递到目标表"""
        async with engine.begin() as conn:
            await conn.exec_driver_sql(
                "INSERT INTO products (name, created_at, updated_at) VALUES (?, ?, ?)",
                ("迁移测试商品", datetime.utcnow(), datetime.utcnow()),
            )
            result = await conn.exec_driver_sql(
                "SELECT id FROM products WHERE name = ?", ("迁移测试商品",)
            )
            product_id: int = result.fetchone()[0]

        await _insert_material(
            engine,
            mat_type="video",
            name="product_linked.mp4",
            path="videos/product_linked.mp4",
            product_id=product_id,
        )

        await run_migration(engine)

        rows = await _fetch_all(engine, "videos")
        matched = next(
            (r for r in rows if r["file_path"] == "videos/product_linked.mp4"), None
        )
        assert matched is not None
        assert matched["product_id"] == product_id
