from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.api import admin as admin_api
from app.core.rate_limit import InMemoryRateLimiter
from app.main import create_app
from app.schemas.admin import AdminStepUpVerifyRequest, AdminStepUpVerifyResponse
from app.services.admin_service import AdminServiceError


class FakeAdminStepUpService:
    def __init__(
        self,
        *,
        response: AdminStepUpVerifyResponse | None = None,
        error: AdminServiceError | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, str]] = []

    def verify_step_up_password(
        self,
        access_token: str,
        payload: AdminStepUpVerifyRequest,
        *,
        client_ip: str,
    ) -> AdminStepUpVerifyResponse:
        self.calls.append(
            {
                "access_token": access_token,
                "password": payload.password,
                "scope": payload.scope,
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
        "admin_step_up_rate_limiter",
        InMemoryRateLimiter(window_seconds=60, max_attempts=5),
    )
    yield app
    app.dependency_overrides.clear()


def _make_success_response() -> AdminStepUpVerifyResponse:
    return AdminStepUpVerifyResponse(
        step_up_token="admin_step_up_token",
        scope="users.write",
        expires_at=datetime(2026, 5, 1, 0, 5, 0),
        method="password",
    )


def test_admin_step_up_verify_returns_success_payload_and_forwards_context(app) -> None:
    service = FakeAdminStepUpService(response=_make_success_response())
    app.dependency_overrides[admin_api.get_admin_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/admin/step-up/password/verify",
            headers={"Authorization": "Bearer admin_access_token"},
            json={"password": "admin-secret", "scope": "users.write"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "step_up_token": "admin_step_up_token",
        "scope": "users.write",
        "expires_at": "2026-05-01T00:05:00",
        "method": "password",
    }
    assert service.calls == [
        {
            "access_token": "admin_access_token",
            "password": "admin-secret",
            "scope": "users.write",
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
                details={"reason": "invalid_credentials", "scope": "users.write"},
            ),
            401,
            {
                "error_code": "invalid_credentials",
                "message": "Invalid username or password",
                "details": {"reason": "invalid_credentials", "scope": "users.write"},
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
def test_admin_step_up_verify_surfaces_service_error_semantics(
    app,
    error: AdminServiceError,
    expected_status: int,
    expected_body: dict,
) -> None:
    service = FakeAdminStepUpService(error=error)
    app.dependency_overrides[admin_api.get_admin_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/admin/step-up/password/verify",
            headers={"Authorization": "Bearer admin_access_token"},
            json={"password": "wrong-password", "scope": "users.write"},
        )

    assert response.status_code == expected_status
    assert response.json() == expected_body
    assert len(service.calls) == 1


def test_admin_step_up_verify_returns_429_before_calling_service_when_rate_limit_bucket_is_full(
    app,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = FakeAdminStepUpService(response=_make_success_response())
    app.dependency_overrides[admin_api.get_admin_service] = lambda: service
    monkeypatch.setattr(
        admin_api,
        "admin_step_up_rate_limiter",
        InMemoryRateLimiter(window_seconds=60, max_attempts=1),
    )

    with TestClient(app) as client:
        first_response = client.post(
            "/admin/step-up/password/verify",
            headers={"Authorization": "Bearer admin_access_token"},
            json={"password": "admin-secret", "scope": "users.write"},
        )
        second_response = client.post(
            "/admin/step-up/password/verify",
            headers={"Authorization": "Bearer admin_access_token"},
            json={"password": "admin-secret", "scope": "users.write"},
        )

    assert first_response.status_code == 200
    assert second_response.status_code == 429
    assert second_response.json() == {
        "error_code": "too_many_requests",
        "message": "Too many admin step-up attempts, please retry later.",
        "details": {},
    }
    assert len(service.calls) == 1
