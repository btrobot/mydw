from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.core.rate_limit import InMemoryRateLimiter
from app.main import create_app
from app.schemas.auth import AuthSuccessResponse, LoginRequest, UserIdentity


class FakeAuthService:
    def __init__(self, *, response: AuthSuccessResponse) -> None:
        self.response = response
        self.calls: list[dict[str, str]] = []

    def login(self, payload: LoginRequest, *, client_ip: str) -> AuthSuccessResponse:
        self.calls.append(
            {
                "username": payload.username,
                "password": payload.password,
                "device_id": payload.device_id,
                "client_version": payload.client_version,
                "client_ip": client_ip,
            }
        )
        return self.response


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch):
    app = create_app()
    monkeypatch.setattr(
        auth_api,
        "login_rate_limiter",
        InMemoryRateLimiter(window_seconds=60, max_attempts=5),
    )
    yield app
    app.dependency_overrides.clear()


def _make_success_response() -> AuthSuccessResponse:
    return AuthSuccessResponse(
        access_token="access_token",
        refresh_token="refresh_token",
        expires_at=datetime(2026, 5, 1, 0, 0, 0),
        token_type="Bearer",
        user=UserIdentity(
            id="u_1",
            username="alice",
            display_name="Alice",
            tenant_id="tenant_1",
        ),
        license_status="active",
        entitlements=["dashboard:view"],
        device_id="device_1",
        device_status="bound",
        offline_grace_until=None,
        minimum_supported_version="0.2.0",
    )


def test_login_returns_429_before_calling_service_when_rate_limit_bucket_is_full(app, monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeAuthService(response=_make_success_response())
    app.dependency_overrides[auth_api.get_auth_service] = lambda: service
    monkeypatch.setattr(
        auth_api,
        "login_rate_limiter",
        InMemoryRateLimiter(window_seconds=60, max_attempts=1),
    )

    with TestClient(app) as client:
        first_response = client.post(
            "/login",
            json={
                "username": "alice",
                "password": "secret",
                "device_id": "device_1",
                "client_version": "0.2.0",
            },
        )
        second_response = client.post(
            "/login",
            json={
                "username": "alice",
                "password": "secret",
                "device_id": "device_1",
                "client_version": "0.2.0",
            },
        )

    assert first_response.status_code == 200
    assert second_response.status_code == 429
    assert second_response.json() == {
        "error_code": "too_many_requests",
        "message": "Too many login attempts, please retry later.",
        "details": {},
    }
    assert len(service.calls) == 1
