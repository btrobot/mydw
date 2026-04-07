"""
Integration tests for Product API (SP1-06).

Covers: POST /api/products, GET /api/products, GET /api/products/{id},
        PUT /api/products/{id}, DELETE /api/products/{id}
"""
import sys
from pathlib import Path

import pytest
from httpx import AsyncClient

backend_root = str(Path(__file__).parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)


class TestProductAPI:

    @pytest.mark.asyncio
    async def test_create_product(self, client: AsyncClient) -> None:
        """POST /api/products — 201 + 返回字段验证"""
        response = await client.post(
            "/api/products",
            json={
                "name": "测试商品",
                "link": "https://example.com/product/1",
                "description": "商品描述",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "测试商品"
        assert data["link"] == "https://example.com/product/1"
        assert data["description"] == "商品描述"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_product_duplicate(self, client: AsyncClient) -> None:
        """POST /api/products — 重名时返回 400"""
        payload = {"name": "重名商品"}
        first = await client.post("/api/products", json=payload)
        assert first.status_code == 201

        second = await client.post("/api/products", json=payload)
        assert second.status_code == 400

    @pytest.mark.asyncio
    async def test_list_products(self, client: AsyncClient) -> None:
        """GET /api/products — 验证列表格式"""
        await client.post("/api/products", json={"name": "商品A"})
        await client.post("/api/products", json={"name": "商品B"})

        response = await client.get("/api/products")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_get_product(self, client: AsyncClient) -> None:
        """GET /api/products/{id} — 200 + 正确数据"""
        create_resp = await client.post("/api/products", json={"name": "单查商品"})
        product_id = create_resp.json()["id"]

        response = await client.get(f"/api/products/{product_id}")
        assert response.status_code == 200
        assert response.json()["id"] == product_id
        assert response.json()["name"] == "单查商品"

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, client: AsyncClient) -> None:
        """GET /api/products/{id} — 不存在时返回 404"""
        response = await client.get("/api/products/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_product(self, client: AsyncClient) -> None:
        """PUT /api/products/{id} — 200 + 字段已更新"""
        create_resp = await client.post(
            "/api/products", json={"name": "原始商品名"}
        )
        product_id = create_resp.json()["id"]

        update_resp = await client.put(
            f"/api/products/{product_id}",
            json={"name": "更新后商品名", "description": "新描述"},
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["name"] == "更新后商品名"
        assert data["description"] == "新描述"

    @pytest.mark.asyncio
    async def test_update_product_duplicate_name(self, client: AsyncClient) -> None:
        """PUT /api/products/{id} — 改名与已有商品重名时返回 400"""
        await client.post("/api/products", json={"name": "已存在商品"})
        create_resp = await client.post("/api/products", json={"name": "待更新商品"})
        product_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/products/{product_id}",
            json={"name": "已存在商品"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_product(self, client: AsyncClient) -> None:
        """DELETE /api/products/{id} — 204 + 后续 GET 返回 404"""
        create_resp = await client.post("/api/products", json={"name": "待删除商品"})
        product_id = create_resp.json()["id"]

        delete_resp = await client.delete(f"/api/products/{product_id}")
        assert delete_resp.status_code == 204

        get_resp = await client.get(f"/api/products/{product_id}")
        assert get_resp.status_code == 404
