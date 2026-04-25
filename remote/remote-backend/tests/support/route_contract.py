from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ErrorContractCase:
    status: int
    error_code: str
    message: str
    details: dict[str, Any]


class RecordingRouteService:
    def __init__(self, responses: Mapping[str, Any] | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.responses = dict(responses or {})
        self.errors: dict[str, Exception] = {}

    def handle(self, method: str, **kwargs: Any) -> Any:
        self.calls.append({"method": method, **kwargs})
        error = self.errors.get(method)
        if error is not None:
            raise error
        return self.responses.get(method)


def bearer_headers(token: str | None) -> dict[str, str] | None:
    if token is None:
        return None
    return {"Authorization": f"Bearer {token}"}


def expected_access_token(status: int, token: str) -> str:
    return "" if status == 401 else token


def assert_json_model_response(response, model: Any) -> None:
    assert response.status_code == 200
    assert response.json() == model.model_dump(mode="json")


def assert_error_response(response, case: ErrorContractCase) -> None:
    assert response.status_code == case.status
    assert response.json() == {
        "error_code": case.error_code,
        "message": case.message,
        "details": case.details,
    }


def assert_single_service_call(calls: list[dict[str, Any]], *, method: str, **kwargs: Any) -> None:
    assert calls == [{"method": method, **kwargs}]
