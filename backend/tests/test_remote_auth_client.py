"""
Step 1 / PR3 tests for remote auth client and protocol adapter.
"""
from __future__ import annotations

import httpx
import pytest

from core.remote_auth_client import (
    RemoteAuthClient,
    RemoteAuthProtocolError,
    RemoteAuthResponseError,
    RemoteAuthTransportError,
)


def _build_client(handler) -> RemoteAuthClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(
        base_url="https://auth.example.test",
        timeout=5,
        transport=transport,
    )
    return RemoteAuthClient(
        base_url="https://auth.example.test",
        timeout=5,
        client=http_client,
    )


@pytest.mark.asyncio
async def test_remote_auth_client_login_success() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/login"
        payload = {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_at": "2026-04-20T10:00:00Z",
            "token_type": "Bearer",
            "user": {
                "id": "u_123",
                "username": "alice",
                "display_name": "Alice",
                "tenant_id": "tenant_1",
            },
            "license_status": "active",
            "entitlements": ["dashboard:view"],
            "device_id": "device_1",
            "device_status": "bound",
            "offline_grace_until": "2026-04-21T10:00:00Z",
            "minimum_supported_version": "0.2.0",
        }
        return httpx.Response(200, json=payload)

    client = _build_client(handler)
    result = await client.login(
        username="alice",
        password="secret",
        device_id="device_1",
        client_version="0.2.0",
    )
    await client.aclose()

    assert result.user.id == "u_123"
    assert result.device_status == "bound"
    assert result.license_status == "active"


@pytest.mark.asyncio
async def test_remote_auth_client_refresh_success() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/refresh"
        payload = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_at": "2026-04-20T11:00:00Z",
            "token_type": "Bearer",
            "user": {
                "id": "u_123",
                "username": "alice",
                "display_name": "Alice",
                "tenant_id": "tenant_1",
            },
            "license_status": "active",
            "entitlements": ["dashboard:view"],
            "device_id": "device_1",
            "device_status": "bound",
            "offline_grace_until": "2026-04-21T10:00:00Z",
            "minimum_supported_version": "0.2.0",
        }
        return httpx.Response(200, json=payload)

    client = _build_client(handler)
    result = await client.refresh(
        refresh_token="refresh-token",
        device_id="device_1",
        client_version="0.2.0",
    )
    await client.aclose()

    assert result.refresh_token == "new-refresh-token"
    assert result.user.username == "alice"


@pytest.mark.asyncio
async def test_remote_auth_client_maps_revoked_response() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={
                "error_code": "revoked",
                "message": "Remote authorization revoked",
                "details": {},
            },
        )

    client = _build_client(handler)
    with pytest.raises(RemoteAuthResponseError) as exc_info:
        await client.refresh(
            refresh_token="refresh-token",
            device_id="device_1",
            client_version="0.2.0",
        )
    await client.aclose()

    assert exc_info.value.error_code == "revoked"
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_remote_auth_client_maps_device_mismatch_response() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={
                "error_code": "device_mismatch",
                "message": "Current device does not match the bound device",
                "details": {"device_id": "other_device"},
            },
        )

    client = _build_client(handler)
    with pytest.raises(RemoteAuthResponseError) as exc_info:
        await client.me(access_token="access-token")
    await client.aclose()

    assert exc_info.value.error_code == "device_mismatch"


@pytest.mark.asyncio
async def test_remote_auth_client_maps_timeout_to_transport_error() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("boom")

    client = _build_client(handler)
    with pytest.raises(RemoteAuthTransportError) as exc_info:
        await client.login(
            username="alice",
            password="secret",
            device_id="device_1",
            client_version="0.2.0",
        )
    await client.aclose()

    assert exc_info.value.error_code == "network_timeout"


@pytest.mark.asyncio
async def test_remote_auth_client_rejects_invalid_success_payload() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "access_token": "access-token",
                # refresh_token 缺失，触发 frozen contract 校验失败
                "expires_at": "2026-04-20T10:00:00Z",
                "token_type": "Bearer",
                "user": {"id": "u_123", "username": "alice"},
                "license_status": "active",
                "entitlements": ["dashboard:view"],
                "device_id": "device_1",
                "device_status": "bound",
            },
        )

    client = _build_client(handler)
    with pytest.raises(RemoteAuthProtocolError):
        await client.login(
            username="alice",
            password="secret",
            device_id="device_1",
            client_version="0.2.0",
        )
    await client.aclose()
