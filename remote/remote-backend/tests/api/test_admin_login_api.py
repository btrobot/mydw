from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.api import admin as admin_api
from app.core.rate_limit import InMemoryRateLimiter
from app.main import create_app
from app.schemas.admin import AdminIdentity, AdminLoginRequest, AdminLoginResponse
from app.services.admin_service import AdminServiceError


class FakeAdminService:
    def __init__(self, *, response: AdminLoginResponse | None = None, error: AdminServiceError | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, str]] = []

    def login(self, payload: AdminLoginRequest, *, client_ip: str) -> AdminLoginResponse:
        self.calls.append(
            {
                "username": payload.username,
                "password": payload.password,
                "client_ip": client_ip,
            }
        )
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch):
    app = create_app()
    monkeypatch.setattr(
        admin_api,
        "admin_login_rate_limiter",
        InMemoryRateLimiter(window_seconds=60, max_attempts=5),
    )
    yield app
    app.dependency_overrides.clear()


def _make_success_response() -> AdminLoginResponse:
    return AdminLoginResponse(
        access_token="admin_access_token",
        session_id="admin_sess_1",
        expires_at=datetime(2026, 5, 1, 0, 0, 0),
        token_type="Bearer",
        user=AdminIdentity(
            id="admin_1",
            username="admin",
            display_name="Remote Admin",
            role="super_admin",
        ),
    )


def test_admin_login_returns_success_payload_and_forwards_client_context(app) -> None:
    service = FakeAdminService(response=_make_success_response())
    app.dependency_overrides[admin_api.get_admin_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/admin/login",
            json={"username": "admin", "password": "admin-secret"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "admin_access_token",
        "session_id": "admin_sess_1",
        "expires_at": "2026-05-01T00:00:00",
        "token_type": "Bearer",
        "user": {
            "id": "admin_1",
            "username": "admin",
            "display_name": "Remote Admin",
            "role": "super_admin",
        },
    }
    assert service.calls == [
        {
            "username": "admin",
            "password": "admin-secret",
            "client_ip": "testclient",
        }
    ]


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_body"),
    [
        (
            AdminServiceError(
                "invalid_credentials",
                "Invalid username or password",
                status_code=401,
                details={"reason": "invalid_credentials"},
            ),
            401,
            {
                "error_code": "invalid_credentials",
                "message": "Invalid username or password",
                "details": {"reason": "invalid_credentials"},
            },
        ),
        (
            AdminServiceError(
                "forbidden",
                "Admin access forbidden",
                status_code=403,
                details={"reason": "forbidden"},
            ),
            403,
            {
                "error_code": "forbidden",
                "message": "Admin access forbidden",
                "details": {"reason": "forbidden"},
            },
        ),
    ],
)
def test_admin_login_surfaces_service_error_semantics(app, error: AdminServiceError, expected_status: int, expected_body: dict) -> None:
    service = FakeAdminService(error=error)
    app.dependency_overrides[admin_api.get_admin_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/admin/login",
            json={"username": "admin", "password": "wrong-password"},
        )

    assert response.status_code == expected_status
    assert response.json() == expected_body
    assert len(service.calls) == 1


def test_admin_login_returns_429_before_calling_service_when_rate_limit_bucket_is_full(app, monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeAdminService(response=_make_success_response())
    app.dependency_overrides[admin_api.get_admin_service] = lambda: service
    monkeypatch.setattr(
        admin_api,
        "admin_login_rate_limiter",
        InMemoryRateLimiter(window_seconds=60, max_attempts=1),
    )

    with TestClient(app) as client:
        first_response = client.post(
            "/admin/login",
            json={"username": "admin", "password": "admin-secret"},
        )
        second_response = client.post(
            "/admin/login",
            json={"username": "admin", "password": "admin-secret"},
        )

    assert first_response.status_code == 200
    assert second_response.status_code == 429
    assert second_response.json() == {
        "error_code": "too_many_requests",
        "message": "Too many admin login attempts, please retry later.",
        "details": {},
    }
    assert len(service.calls) == 1
