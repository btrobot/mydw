"""
Integration tests for Copywriting API (SP1-02).

Covers: POST /api/copywritings, GET /api/copywritings, DELETE /api/copywritings/{id}
"""
import sys
from pathlib import Path

import pytest
from httpx import AsyncClient

backend_root = str(Path(__file__).parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from models import Account, Product, Video


class TestCopywritingAPI:

    @pytest.mark.asyncio
    async def test_create_copywriting(self, client: AsyncClient) -> None:
        """POST /api/copywritings — 201 + source_type 默认 'manual'"""
        response = await client.post(
            "/api/copywritings",
            json={"content": "这是一段测试文案内容"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "这是一段测试文案内容"
        assert data["source_type"] == "manual"
        assert data["product_id"] is None
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_list_copywritings(self, client: AsyncClient) -> None:
        """GET /api/copywritings — 验证列表格式"""
        await client.post("/api/copywritings", json={"content": "文案A"})
        await client.post("/api/copywritings", json={"content": "文案B"})

        response = await client.get("/api/copywritings")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_list_filter_by_product(self, client: AsyncClient, db_session) -> None:
        """GET /api/copywritings?product_id=X — 只返回该商品的文案"""
        product = Product(name="copywriting_filter_product")
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        product_id = product.id

        await client.post(
            "/api/copywritings",
            json={"content": "关联文案", "product_id": product_id},
        )
        await client.post(
            "/api/copywritings",
            json={"content": "无关联文案"},
        )

        response = await client.get(f"/api/copywritings?product_id={product_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["product_id"] == product_id
        assert data["items"][0]["content"] == "关联文案"

    @pytest.mark.asyncio
    async def test_delete_copywriting(self, client: AsyncClient) -> None:
        """DELETE /api/copywritings/{id} — 204 + 后续 GET 返回 404"""
        create_resp = await client.post(
            "/api/copywritings", json={"content": "待删除文案"}
        )
        assert create_resp.status_code == 201
        cw_id = create_resp.json()["id"]

        delete_resp = await client.delete(f"/api/copywritings/{cw_id}")
        assert delete_resp.status_code == 204

        get_resp = await client.get(f"/api/copywritings/{cw_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_copywriting_blocks_when_task_resource_relation_references_copywriting(
        self,
        client: AsyncClient,
        db_session,
    ) -> None:
        create_resp = await client.post(
            "/api/copywritings", json={"content": "被任务引用的文案"}
        )
        assert create_resp.status_code == 201
        copywriting_id = create_resp.json()["id"]

        account = Account(
            account_id="copywriting_ref_guard_account",
            account_name="Copywriting Ref Guard",
            status="active",
        )
        video = Video(name="copywriting_guard_video.mp4", file_path="videos/copywriting_guard_video.mp4")
        db_session.add_all([account, video])
        await db_session.commit()
        await db_session.refresh(account)
        await db_session.refresh(video)

        task_resp = await client.post(
            "/api/tasks/",
            json={
                "video_ids": [video.id],
                "copywriting_ids": [copywriting_id],
                "account_ids": [account.id],
            },
        )
        assert task_resp.status_code == 201

        delete_resp = await client.delete(f"/api/copywritings/{copywriting_id}")
        assert delete_resp.status_code == 409
        assert "无法删除" in delete_resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_batch_delete_copywritings_skips_relation_referenced_copywriting(
        self,
        client: AsyncClient,
        db_session,
    ) -> None:
        referenced_resp = await client.post(
            "/api/copywritings", json={"content": "批量保护文案"}
        )
        free_resp = await client.post(
            "/api/copywritings", json={"content": "可删除文案"}
        )
        assert referenced_resp.status_code == 201
        assert free_resp.status_code == 201
        referenced_id = referenced_resp.json()["id"]
        free_id = free_resp.json()["id"]

        account = Account(
            account_id="copywriting_batch_guard_account",
            account_name="Copywriting Batch Guard",
            status="active",
        )
        video = Video(name="copywriting_batch_video.mp4", file_path="videos/copywriting_batch_video.mp4")
        db_session.add_all([account, video])
        await db_session.commit()
        await db_session.refresh(account)
        await db_session.refresh(video)

        task_resp = await client.post(
            "/api/tasks/",
            json={
                "video_ids": [video.id],
                "copywriting_ids": [referenced_id],
                "account_ids": [account.id],
            },
        )
        assert task_resp.status_code == 201

        batch_resp = await client.post(
            "/api/copywritings/batch-delete",
            json={"ids": [referenced_id, free_id]},
        )
        assert batch_resp.status_code == 200
        payload = batch_resp.json()
        assert payload["deleted"] == 1
        assert payload["skipped"] == 1
        assert payload["skipped_ids"] == [referenced_id]
