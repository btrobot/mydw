"""
Step 3 / PR3 tests for remaining business router auth gates.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_dependencies import (
    LocalAuthorizationError,
    POLICY_ACTIVE_REQUIRED,
    POLICY_GRACE_READONLY_ALLOWED,
    enforce_machine_session_policy,
    get_machine_session_summary,
    set_current_auth_summary,
    require_active_machine_session,
    require_grace_readonly_machine_session,
)
from main import app
from models import (
    Audio,
    Copywriting,
    Cover,
    Product,
    PublishProfile,
    RemoteAuthSession,
    Topic,
    TopicGroup,
    Video,
)
from schemas.auth import LocalAuthSessionSummary


def _summary(
    auth_state: str,
    *,
    denial_reason: str | None = None,
) -> LocalAuthSessionSummary:
    return LocalAuthSessionSummary(
        auth_state=auth_state,
        remote_user_id="u_123" if auth_state != "unauthenticated" else None,
        display_name="Alice" if auth_state != "unauthenticated" else None,
        license_status="active" if auth_state != "unauthenticated" else None,
        entitlements=["dashboard:view"],
        denial_reason=denial_reason,
        device_id="device-1",
    )


def _assert_denial(
    response,
    *,
    expected_status: int,
    expected_error_code: str,
    expected_auth_state: str,
    expected_policy: str,
    expected_reason_code: str | None = None,
) -> None:
    assert response.status_code == expected_status
    detail = response.json()["detail"]
    assert detail["error_code"] == expected_error_code
    assert detail["auth_state"] == expected_auth_state
    assert detail["policy"] == expected_policy
    assert detail["reason_code"] == expected_reason_code


@pytest.fixture()
def set_auth_state(db_session: AsyncSession):
    async def _install(auth_state: str, *, denial_reason: str | None = None) -> None:
        summary = _summary(auth_state, denial_reason=denial_reason)
        existing = await db_session.execute(select(RemoteAuthSession))
        for row in existing.scalars().all():
            await db_session.delete(row)
        db_session.add(
            RemoteAuthSession(
                auth_state=auth_state,
                remote_user_id=summary.remote_user_id,
                display_name=summary.display_name,
                license_status=summary.license_status,
                denial_reason=summary.denial_reason,
                device_id=summary.device_id,
            )
        )
        await db_session.commit()

        def _active_override() -> LocalAuthSessionSummary:
            try:
                allowed = enforce_machine_session_policy(summary, policy=POLICY_ACTIVE_REQUIRED)
                set_current_auth_summary(allowed)
                return allowed
            except LocalAuthorizationError as exc:
                raise exc.to_http_exception() from exc

        def _grace_override() -> LocalAuthSessionSummary:
            try:
                allowed = enforce_machine_session_policy(summary, policy=POLICY_GRACE_READONLY_ALLOWED)
                set_current_auth_summary(allowed)
                return allowed
            except LocalAuthorizationError as exc:
                raise exc.to_http_exception() from exc

        app.dependency_overrides[require_active_machine_session] = _active_override
        app.dependency_overrides[require_grace_readonly_machine_session] = _grace_override
        app.dependency_overrides[get_machine_session_summary] = lambda: (set_current_auth_summary(summary), summary)[1]

    yield _install


async def _create_product(db_session: AsyncSession, *, name: str = "Product A") -> Product:
    product = Product(name=name, parse_status="parsed")
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product


class TestAIRouterAuthGates:
    @pytest.mark.asyncio
    async def test_ai_video_info_denies_grace_before_service_call(
        self,
        client: AsyncClient,
        set_auth_state,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        get_video_info = AsyncMock()
        monkeypatch.setattr("api.ai.ai_clip_service.get_video_info", get_video_info)
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.get("/api/ai/video-info", params={"video_path": "E:/video.mp4"})

        _assert_denial(
            response,
            expected_status=403,
            expected_error_code="auth_grace_restricted",
            expected_auth_state="authenticated_grace",
            expected_policy="active_required",
            expected_reason_code="network_timeout",
        )
        get_video_info.assert_not_called()

    @pytest.mark.asyncio
    async def test_ai_smart_clip_allows_active(
        self,
        client: AsyncClient,
        set_auth_state,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        smart_clip = AsyncMock(return_value=type("ClipResult", (), {"success": True, "output_path": "out.mp4", "duration": 1.0, "error": None})())
        monkeypatch.setattr("api.ai.ai_clip_service.smart_clip", smart_clip)
        await set_auth_state("authenticated_active")

        response = await client.post(
            "/api/ai/smart-clip",
            json={
                "video_path": "E:/video.mp4",
                "segments": [{"start": 0, "end": 1, "reason": "test"}],
                "output_path": "E:/out.mp4",
                "target_duration": 60,
            },
        )

        assert response.status_code == 200
        assert response.json()["success"] is True
        smart_clip.assert_awaited_once()


class TestProductRouterAuthGates:
    @pytest.mark.asyncio
    async def test_product_materials_allow_grace_readonly(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        product = await _create_product(db_session)
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.get(f"/api/products/{product.id}/materials")

        assert response.status_code == 200
        assert response.json()["product"]["id"] == product.id

    @pytest.mark.asyncio
    async def test_product_parse_materials_denies_grace_before_parser(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        product = await _create_product(db_session)
        product.dewu_url = "https://www.example.com/item"
        await db_session.commit()
        parse_materials = AsyncMock()
        monkeypatch.setattr("api.product.parse_and_create_materials", parse_materials)
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.post(f"/api/products/{product.id}/parse-materials")

        assert response.status_code == 403
        assert response.json()["detail"]["error_code"] == "auth_grace_restricted"
        parse_materials.assert_not_called()


class TestVideoRouterAuthGates:
    @pytest.mark.asyncio
    async def test_video_stream_allows_grace_readonly(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        tmp_path: Path,
        set_auth_state,
    ) -> None:
        product = await _create_product(db_session)
        video_path = tmp_path / "sample.mp4"
        video_path.write_bytes(b"fake-video")
        video = Video(name="sample.mp4", file_path=str(video_path), product_id=product.id)
        db_session.add(video)
        await db_session.commit()
        await db_session.refresh(video)
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.get(f"/api/videos/{video.id}/stream")

        assert response.status_code == 200
        assert response.content == b"fake-video"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("auth_state", "denial_reason", "expected_status", "expected_error_code"),
        [
            ("unauthenticated", None, 401, "unauthenticated"),
            ("expired", "remote_auth_expired", 401, "expired"),
            ("device_mismatch", "remote_auth_device_mismatch", 403, "device_mismatch"),
            ("revoked", "remote_auth_revoked", 403, "revoked"),
        ],
    )
    async def test_video_stream_denial_matrix(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        tmp_path: Path,
        set_auth_state,
        auth_state: str,
        denial_reason: str | None,
        expected_status: int,
        expected_error_code: str,
    ) -> None:
        product = await _create_product(db_session, name="Product B")
        video_path = tmp_path / "private.mp4"
        video_path.write_bytes(b"private-video")
        video = Video(name="private.mp4", file_path=str(video_path), product_id=product.id)
        db_session.add(video)
        await db_session.commit()
        await db_session.refresh(video)
        await set_auth_state(auth_state, denial_reason=denial_reason)

        response = await client.get(f"/api/videos/{video.id}/stream")

        _assert_denial(
            response,
            expected_status=expected_status,
            expected_error_code=expected_error_code,
            expected_auth_state=auth_state,
            expected_policy="grace_readonly_allowed",
            expected_reason_code=denial_reason,
        )

    @pytest.mark.asyncio
    async def test_video_upload_denies_grace_without_persisting_record(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.post(
            "/api/videos/upload",
            files={"file": ("clip.mp4", b"video-bytes", "video/mp4")},
        )

        _assert_denial(
            response,
            expected_status=403,
            expected_error_code="auth_grace_restricted",
            expected_auth_state="authenticated_grace",
            expected_policy="active_required",
            expected_reason_code="network_timeout",
        )
        videos = (await db_session.execute(Video.__table__.select())).all()
        assert videos == []


class TestCopywritingRouterAuthGates:
    @pytest.mark.asyncio
    async def test_copywriting_list_allows_grace_readonly(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        db_session.add(Copywriting(name="copy", content="hello", source_type="manual"))
        await db_session.commit()
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.get("/api/copywritings")

        assert response.status_code == 200
        assert response.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_copywriting_import_denies_grace_without_db_mutation(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.post(
            "/api/copywritings/import",
            files={"file": ("copy.txt", b"line-1\nline-2", "text/plain")},
        )

        _assert_denial(
            response,
            expected_status=403,
            expected_error_code="auth_grace_restricted",
            expected_auth_state="authenticated_grace",
            expected_policy="active_required",
            expected_reason_code="network_timeout",
        )
        rows = (await db_session.execute(Copywriting.__table__.select())).all()
        assert rows == []


class TestCoverRouterAuthGates:
    @pytest.mark.asyncio
    async def test_cover_image_allows_grace_readonly(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        tmp_path: Path,
        set_auth_state,
    ) -> None:
        image_path = tmp_path / "cover.png"
        image_path.write_bytes(b"cover-bytes")
        cover = Cover(name="cover", file_path=str(image_path))
        db_session.add(cover)
        await db_session.commit()
        await db_session.refresh(cover)
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.get(f"/api/covers/{cover.id}/image")

        assert response.status_code == 200
        assert response.content == b"cover-bytes"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("auth_state", "denial_reason", "expected_status", "expected_error_code"),
        [
            ("unauthenticated", None, 401, "unauthenticated"),
            ("expired", "remote_auth_expired", 401, "expired"),
            ("device_mismatch", "remote_auth_device_mismatch", 403, "device_mismatch"),
        ],
    )
    async def test_cover_image_denial_matrix(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        tmp_path: Path,
        set_auth_state,
        auth_state: str,
        denial_reason: str | None,
        expected_status: int,
        expected_error_code: str,
    ) -> None:
        image_path = tmp_path / "private-cover.png"
        image_path.write_bytes(b"private-cover")
        cover = Cover(name="private-cover", file_path=str(image_path))
        db_session.add(cover)
        await db_session.commit()
        await db_session.refresh(cover)
        await set_auth_state(auth_state, denial_reason=denial_reason)

        response = await client.get(f"/api/covers/{cover.id}/image")

        _assert_denial(
            response,
            expected_status=expected_status,
            expected_error_code=expected_error_code,
            expected_auth_state=auth_state,
            expected_policy="grace_readonly_allowed",
            expected_reason_code=denial_reason,
        )

    @pytest.mark.asyncio
    async def test_cover_extract_denies_grace_before_side_effect(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        create_subprocess_exec = AsyncMock()
        monkeypatch.setattr("api.cover.asyncio.create_subprocess_exec", create_subprocess_exec)
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.post("/api/covers/extract", json={"video_id": 1, "timestamp": 0})

        _assert_denial(
            response,
            expected_status=403,
            expected_error_code="auth_grace_restricted",
            expected_auth_state="authenticated_grace",
            expected_policy="active_required",
            expected_reason_code="network_timeout",
        )
        create_subprocess_exec.assert_not_called()
        covers = (await db_session.execute(Cover.__table__.select())).all()
        assert covers == []


class TestAudioRouterAuthGates:
    @pytest.mark.asyncio
    async def test_audio_list_allows_grace_readonly(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        db_session.add(Audio(name="sound.mp3", file_path="E:/sound.mp3"))
        await db_session.commit()
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.get("/api/audios")

        assert response.status_code == 200
        assert len(response.json()) == 1

    @pytest.mark.asyncio
    async def test_audio_upload_denies_grace_without_db_mutation(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.post(
            "/api/audios/upload",
            files={"file": ("sound.mp3", b"audio-bytes", "audio/mpeg")},
        )

        _assert_denial(
            response,
            expected_status=403,
            expected_error_code="auth_grace_restricted",
            expected_auth_state="authenticated_grace",
            expected_policy="active_required",
            expected_reason_code="network_timeout",
        )
        rows = (await db_session.execute(Audio.__table__.select())).all()
        assert rows == []


class TestTopicRouterAuthGates:
    @pytest.mark.asyncio
    async def test_topic_global_allows_grace_readonly(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        topic = Topic(name="topic-a", heat=1, source="manual")
        db_session.add(topic)
        await db_session.commit()
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.get("/api/topics/global")

        assert response.status_code == 200
        assert response.json()["topic_ids"] == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("auth_state", "denial_reason", "expected_status", "expected_error_code"),
        [
            ("authenticated_grace", "network_timeout", 403, "auth_grace_restricted"),
            ("unauthenticated", None, 401, "unauthenticated"),
            ("expired", "remote_auth_expired", 401, "expired"),
            ("device_mismatch", "remote_auth_device_mismatch", 403, "device_mismatch"),
        ],
    )
    async def test_topic_search_denial_matrix(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
        monkeypatch: pytest.MonkeyPatch,
        auth_state: str,
        denial_reason: str | None,
        expected_status: int,
        expected_error_code: str,
    ) -> None:
        search = AsyncMock(return_value=[{"name": "new-topic", "heat": 10}])
        monkeypatch.setattr("services.topic_service.TopicSearchService.search", search)
        await set_auth_state(auth_state, denial_reason=denial_reason)

        response = await client.get("/api/topics/search", params={"keyword": "new"})

        _assert_denial(
            response,
            expected_status=expected_status,
            expected_error_code=expected_error_code,
            expected_auth_state=auth_state,
            expected_policy="active_required",
            expected_reason_code=denial_reason,
        )
        search.assert_not_called()
        rows = (await db_session.execute(Topic.__table__.select())).all()
        assert rows == []

    @pytest.mark.asyncio
    async def test_topic_group_list_allows_grace_readonly(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        group = TopicGroup(name="group-a", topic_ids="[]")
        db_session.add(group)
        await db_session.commit()
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.get("/api/topic-groups")

        assert response.status_code == 200
        assert response.json()["total"] == 1


class TestProfileRouterAuthGates:
    @pytest.mark.asyncio
    async def test_profile_list_allows_grace_readonly(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        profile = PublishProfile(
            name="profile-a",
            is_default=False,
            composition_mode="none",
            global_topic_ids="[]",
            auto_retry=True,
            max_retry_count=3,
        )
        db_session.add(profile)
        await db_session.commit()
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.get("/api/profiles")

        assert response.status_code == 200
        assert response.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_profile_set_default_denies_grace_without_mutation(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        profile = PublishProfile(
            name="profile-b",
            is_default=False,
            composition_mode="none",
            global_topic_ids="[]",
            auto_retry=True,
            max_retry_count=3,
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)
        await set_auth_state("authenticated_grace", denial_reason="network_timeout")

        response = await client.put(f"/api/profiles/{profile.id}/set-default")

        _assert_denial(
            response,
            expected_status=403,
            expected_error_code="auth_grace_restricted",
            expected_auth_state="authenticated_grace",
            expected_policy="active_required",
            expected_reason_code="network_timeout",
        )
        await db_session.refresh(profile)
        assert profile.is_default is False

    @pytest.mark.asyncio
    async def test_profile_set_default_allows_active(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        set_auth_state,
    ) -> None:
        profile = PublishProfile(
            name="profile-c",
            is_default=False,
            composition_mode="none",
            global_topic_ids="[]",
            auto_retry=True,
            max_retry_count=3,
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)
        await set_auth_state("authenticated_active")

        response = await client.put(f"/api/profiles/{profile.id}/set-default")

        assert response.status_code == 200
        assert response.json()["is_default"] is True
