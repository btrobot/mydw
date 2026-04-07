"""
Integration tests for Topic API (SP1-05).

Covers: POST /api/topics, GET /api/topics, GET /api/topics?sort=heat, DELETE /api/topics/{id}
"""
import sys
from pathlib import Path

import pytest
from httpx import AsyncClient

backend_root = str(Path(__file__).parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)


class TestTopicAPI:

    @pytest.mark.asyncio
    async def test_create_topic(self, client: AsyncClient) -> None:
        """POST /api/topics — 201 + 返回字段验证"""
        response = await client.post(
            "/api/topics",
            json={"name": "测试话题", "heat": 100, "source": "manual"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "测试话题"
        assert data["heat"] == 100
        assert data["source"] == "manual"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_list_topics(self, client: AsyncClient) -> None:
        """GET /api/topics — 验证列表格式"""
        await client.post("/api/topics", json={"name": "话题X"})
        await client.post("/api/topics", json={"name": "话题Y"})

        response = await client.get("/api/topics")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_list_topics_sort_heat(self, client: AsyncClient) -> None:
        """GET /api/topics?sort=heat — 按热度降序排列"""
        await client.post("/api/topics", json={"name": "低热度话题", "heat": 10})
        await client.post("/api/topics", json={"name": "高热度话题", "heat": 9999})
        await client.post("/api/topics", json={"name": "中热度话题", "heat": 500})

        response = await client.get("/api/topics?sort=heat")
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) >= 3
        heats = [item["heat"] for item in items]
        assert heats == sorted(heats, reverse=True)

    @pytest.mark.asyncio
    async def test_delete_topic(self, client: AsyncClient) -> None:
        """DELETE /api/topics/{id} — 204 + 后续列表中不再包含该话题"""
        create_resp = await client.post(
            "/api/topics", json={"name": "待删除话题"}
        )
        assert create_resp.status_code == 201
        topic_id = create_resp.json()["id"]

        delete_resp = await client.delete(f"/api/topics/{topic_id}")
        assert delete_resp.status_code == 204

        list_resp = await client.get("/api/topics")
        ids = [item["id"] for item in list_resp.json()["items"]]
        assert topic_id not in ids
