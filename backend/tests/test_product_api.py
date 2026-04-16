"""
Integration tests for Product API.

Covers: POST /api/products, GET /api/products, GET /api/products/{id},
        PUT /api/products/{id}, DELETE /api/products/{id},
        parser name-preservation and conflict handling.
"""
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

backend_root = str(Path(__file__).parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from api import product as product_api
from models import Product
from services.product_parse_service import MaterialPack, _replace_product_materials

VALID_SHARE_TEXT_1 = "Check this out https://www.dewu.com/product/12345"
VALID_SHARE_TEXT_2 = "Check this out https://www.dewu.com/product/23456"
VALID_DEWU_URL_1 = "https://www.dewu.com/product/12345"
UNKNOWN_TITLE = "未知商品"
VIDEO_SUFFIX = "_视频"


async def _noop_parse_materials(*args, **kwargs):
    return {
        "success": True,
        "videos_downloaded": 0,
        "covers_downloaded": 0,
        "topics": [],
        "errors": [],
    }


class TestProductAPI:

    @pytest.mark.asyncio
    async def test_create_product_success(self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(product_api, "parse_and_create_materials", AsyncMock(side_effect=_noop_parse_materials))

        response = await client.post(
            "/api/products",
            json={"name": "product-a", "share_text": VALID_SHARE_TEXT_1},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "product-a"
        assert data["dewu_url"] == VALID_DEWU_URL_1
        assert data["parse_status"] == "parsing"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_product_missing_name_returns_422(self, client: AsyncClient) -> None:
        response = await client.post("/api/products", json={"share_text": VALID_SHARE_TEXT_1})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_product_blank_name_returns_422(self, client: AsyncClient) -> None:
        response = await client.post("/api/products", json={"name": "   ", "share_text": VALID_SHARE_TEXT_1})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_product_missing_share_text_returns_422(self, client: AsyncClient) -> None:
        response = await client.post("/api/products", json={"name": "product-a"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_product_blank_share_text_returns_422(self, client: AsyncClient) -> None:
        response = await client.post("/api/products", json={"name": "product-a", "share_text": "   "})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_product_invalid_share_text_returns_422(self, client: AsyncClient) -> None:
        response = await client.post("/api/products", json={"name": "product-a", "share_text": "no dewu url here"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_product_duplicate_name_returns_409(self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(product_api, "parse_and_create_materials", AsyncMock(side_effect=_noop_parse_materials))
        first = await client.post("/api/products", json={"name": "duplicate-name", "share_text": VALID_SHARE_TEXT_1})
        assert first.status_code == 201

        second = await client.post("/api/products", json={"name": "duplicate-name", "share_text": VALID_SHARE_TEXT_2})
        assert second.status_code == 409
        assert second.json()["detail"] == "商品名称已存在"

    @pytest.mark.asyncio
    async def test_create_product_duplicate_dewu_url_returns_409(self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(product_api, "parse_and_create_materials", AsyncMock(side_effect=_noop_parse_materials))
        first = await client.post("/api/products", json={"name": "product-a", "share_text": VALID_SHARE_TEXT_1})
        assert first.status_code == 201

        second = await client.post("/api/products", json={"name": "product-b", "share_text": VALID_SHARE_TEXT_1})
        assert second.status_code == 409
        assert second.json()["detail"] == "该得物链接已存在"

    @pytest.mark.asyncio
    async def test_list_products(self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(product_api, "parse_and_create_materials", AsyncMock(side_effect=_noop_parse_materials))
        await client.post("/api/products", json={"name": "product-a", "share_text": VALID_SHARE_TEXT_1})
        await client.post("/api/products", json={"name": "product-b", "share_text": VALID_SHARE_TEXT_2})

        response = await client.get("/api/products")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_get_product(self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(product_api, "parse_and_create_materials", AsyncMock(side_effect=_noop_parse_materials))
        create_resp = await client.post("/api/products", json={"name": "single-product", "share_text": VALID_SHARE_TEXT_1})
        product_id = create_resp.json()["id"]

        response = await client.get(f"/api/products/{product_id}")
        assert response.status_code == 200
        assert response.json()["id"] == product_id
        assert response.json()["name"] == "single-product"

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/products/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_product(self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(product_api, "parse_and_create_materials", AsyncMock(side_effect=_noop_parse_materials))
        create_resp = await client.post("/api/products", json={"name": "original-name", "share_text": VALID_SHARE_TEXT_1})
        product_id = create_resp.json()["id"]

        update_resp = await client.put(f"/api/products/{product_id}", json={"name": "updated-name"})
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["name"] == "updated-name"

    @pytest.mark.asyncio
    async def test_update_product_blank_name_returns_422(self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(product_api, "parse_and_create_materials", AsyncMock(side_effect=_noop_parse_materials))
        create_resp = await client.post("/api/products", json={"name": "editable-product", "share_text": VALID_SHARE_TEXT_1})
        product_id = create_resp.json()["id"]

        response = await client.put(f"/api/products/{product_id}", json={"name": "   "})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_product_duplicate_name_returns_409(self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(product_api, "parse_and_create_materials", AsyncMock(side_effect=_noop_parse_materials))
        await client.post("/api/products", json={"name": "existing-name", "share_text": VALID_SHARE_TEXT_1})
        create_resp = await client.post("/api/products", json={"name": "updatable-name", "share_text": VALID_SHARE_TEXT_2})
        product_id = create_resp.json()["id"]

        response = await client.put(f"/api/products/{product_id}", json={"name": "existing-name"})
        assert response.status_code == 409
        assert response.json()["detail"] == "商品名称已存在"

    @pytest.mark.asyncio
    async def test_parse_materials_preserves_product_name(
        self,
        client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(product_api, "parse_and_create_materials", AsyncMock(side_effect=_noop_parse_materials))
        create_resp = await client.post("/api/products", json={"name": "user-product-name", "share_text": VALID_SHARE_TEXT_1})
        product_id = create_resp.json()["id"]

        async def _parse_with_replace(*, db: AsyncSession, product: Product):
            pack = MaterialPack(cover_urls=[], video_url=None, title="parsed-title", topics=[])
            return await _replace_product_materials(
                db=db,
                product=product,
                pack=pack,
                video_results=[],
                cover_results=[],
            )

        monkeypatch.setattr(product_api, "parse_and_create_materials", _parse_with_replace)

        parse_resp = await client.post(f"/api/products/{product_id}/parse-materials")
        assert parse_resp.status_code == 200
        data = parse_resp.json()
        assert data["name"] == "user-product-name"
        assert data["parse_status"] == "parsed"
        assert any(cw["content"] == "parsed-title" for cw in data["copywritings"])

    @pytest.mark.asyncio
    async def test_replace_product_materials_prefers_pack_title_for_material_names(self, db_session: AsyncSession) -> None:
        product = Product(name="user-product-name", dewu_url=VALID_DEWU_URL_1, parse_status="parsing")
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        await _replace_product_materials(
            db=db_session,
            product=product,
            pack=MaterialPack(cover_urls=[], video_url=None, title="parsed-title", topics=[]),
            video_results=[("videos/test.mp4", "hash1", 123)],
            cover_results=[("covers/test.webp", "hash2", 45)],
        )

        refreshed = await db_session.get(Product, product.id)
        assert refreshed is not None
        await db_session.refresh(refreshed, attribute_names=["videos", "covers"])
        assert refreshed.videos[0].name == f"parsed-title{VIDEO_SUFFIX}"
        assert refreshed.covers[0].name == "parsed-title"
        assert refreshed.name == "user-product-name"

    @pytest.mark.asyncio
    async def test_replace_product_materials_falls_back_to_product_name_when_title_unknown(self, db_session: AsyncSession) -> None:
        product = Product(name="user-product-name", dewu_url=VALID_DEWU_URL_1, parse_status="parsing")
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)

        await _replace_product_materials(
            db=db_session,
            product=product,
            pack=MaterialPack(cover_urls=[], video_url=None, title=UNKNOWN_TITLE, topics=[]),
            video_results=[("videos/test.mp4", "hash1", 123)],
            cover_results=[("covers/test.webp", "hash2", 45)],
        )

        refreshed = await db_session.get(Product, product.id)
        assert refreshed is not None
        await db_session.refresh(refreshed, attribute_names=["videos", "covers"])
        assert refreshed.videos[0].name == f"user-product-name{VIDEO_SUFFIX}"
        assert refreshed.covers[0].name == "user-product-name"

    @pytest.mark.asyncio
    async def test_create_product_integrity_error_race_returns_409(self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
        original_commit = AsyncSession.commit

        async def _race_commit(self, *args, **kwargs):
            raise IntegrityError("insert", {}, Exception("UNIQUE constraint failed: products.name"))

        monkeypatch.setattr(AsyncSession, "commit", _race_commit)
        response = await client.post("/api/products", json={"name": "race-product", "share_text": VALID_SHARE_TEXT_1})
        monkeypatch.setattr(AsyncSession, "commit", original_commit)

        assert response.status_code == 409
        assert response.json()["detail"] == "商品名称已存在"

    @pytest.mark.asyncio
    async def test_update_product_integrity_error_race_returns_409(self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(product_api, "parse_and_create_materials", AsyncMock(side_effect=_noop_parse_materials))
        create_resp = await client.post("/api/products", json={"name": "original-name", "share_text": VALID_SHARE_TEXT_1})
        product_id = create_resp.json()["id"]

        original_commit = AsyncSession.commit

        async def _race_commit(self, *args, **kwargs):
            raise IntegrityError("update", {}, Exception("UNIQUE constraint failed: products.name"))

        monkeypatch.setattr(AsyncSession, "commit", _race_commit)
        response = await client.put(f"/api/products/{product_id}", json={"name": "conflicting-name"})
        monkeypatch.setattr(AsyncSession, "commit", original_commit)

        assert response.status_code == 409
        assert response.json()["detail"] == "商品名称已存在"

    @pytest.mark.asyncio
    async def test_delete_product(self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(product_api, "parse_and_create_materials", AsyncMock(side_effect=_noop_parse_materials))
        create_resp = await client.post("/api/products", json={"name": "deletable-product", "share_text": VALID_SHARE_TEXT_1})
        product_id = create_resp.json()["id"]

        delete_resp = await client.delete(f"/api/products/{product_id}")
        assert delete_resp.status_code == 204

        get_resp = await client.get(f"/api/products/{product_id}")
        assert get_resp.status_code == 404
