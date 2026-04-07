"""
Integration tests for Video API (SP1-01).

Covers: POST /api/videos, GET /api/videos, GET /api/videos/{id}, DELETE /api/videos/{id}
"""
import sys
from pathlib import Path
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient

backend_root = str(Path(__file__).parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture()
def video_payload() -> dict:
    return {
        "name": "test_video.mp4",
        "file_path": "videos/test_video.mp4",
        "file_size": 1024000,
        "duration": 30,
    }


# ============================================================================
# Tests
# ============================================================================

class TestVideoAPI:

    @pytest.mark.asyncio
    async def test_create_video(self, client: AsyncClient, video_payload: dict) -> None:
        """POST /api/videos — 201 + 返回字段验证"""
        response = await client.post("/api/videos", json=video_payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == video_payload["name"]
        assert data["file_path"] == video_payload["file_path"]
        assert data["file_size"] == video_payload["file_size"]
        assert data["duration"] == video_payload["duration"]
        assert data["source_type"] == "original"
        assert data["product_id"] is None
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_list_videos(self, client: AsyncClient, video_payload: dict) -> None:
        """GET /api/videos — 验证列表格式"""
        await client.post("/api/videos", json=video_payload)
        response = await client.get("/api/videos")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_videos_filter_by_product(
        self, client: AsyncClient, db_session
    ) -> None:
        """GET /api/videos?product_id=X — 只返回该商品的视频.

        Inserts records via db_session directly to avoid the lazy-load
        greenlet issue that occurs when VideoResponse serializes product_name
        immediately after db.refresh() inside the create endpoint.
        """
        from models import Product, Video as VideoModel

        product = Product(name="video_filter_product")
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        product_id = product.id

        linked = VideoModel(name="linked.mp4", file_path="videos/linked.mp4", product_id=product_id)
        unlinked = VideoModel(name="unlinked.mp4", file_path="videos/unlinked.mp4")
        db_session.add(linked)
        db_session.add(unlinked)
        await db_session.commit()

        response = await client.get(f"/api/videos?product_id={product_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["product_id"] == product_id

    @pytest.mark.asyncio
    async def test_get_video(self, client: AsyncClient, video_payload: dict) -> None:
        """GET /api/videos/{id} — 200 + 正确数据"""
        create_resp = await client.post("/api/videos", json=video_payload)
        video_id = create_resp.json()["id"]

        response = await client.get(f"/api/videos/{video_id}")
        assert response.status_code == 200
        assert response.json()["id"] == video_id
        assert response.json()["name"] == video_payload["name"]

    @pytest.mark.asyncio
    async def test_get_video_not_found(self, client: AsyncClient) -> None:
        """GET /api/videos/{id} — 不存在时返回 404"""
        response = await client.get("/api/videos/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_video(self, client: AsyncClient, video_payload: dict) -> None:
        """DELETE /api/videos/{id} — 204 + 后续 GET 返回 404"""
        create_resp = await client.post("/api/videos", json=video_payload)
        video_id = create_resp.json()["id"]

        delete_resp = await client.delete(f"/api/videos/{video_id}")
        assert delete_resp.status_code == 204

        get_resp = await client.get(f"/api/videos/{video_id}")
        assert get_resp.status_code == 404
