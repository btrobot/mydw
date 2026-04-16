from __future__ import annotations

import json
from pathlib import Path

import yaml

from build_phase0_manifest import OUTPUT, build_manifest


ROOT = Path(__file__).resolve().parents[4]
ARTIFACT_ROOT = ROOT / "remote" / "remote-shared"
FIXTURE_ROOT = ARTIFACT_ROOT / "scripts" / "compat-harness" / "fixtures"


def assert_required_keys(payload: dict, required: list[str], name: str) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise AssertionError(f"{name} missing required keys: {missing}")


def validate_openapi() -> dict:
    spec_path = ARTIFACT_ROOT / "openapi" / "remote-auth-v1.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    expected_paths = {
        "/login",
        "/refresh",
        "/logout",
        "/me",
        "/self/me",
        "/self/devices",
        "/self/sessions",
        "/self/activity",
        "/self/sessions/{session_id}/revoke",
        "/admin/users",
        "/admin/users/{user_id}",
        "/admin/devices",
        "/admin/devices/{device_id}",
        "/admin/sessions",
        "/admin/sessions/{session_id}/revoke",
        "/admin/audit-logs",
    }
    missing = expected_paths.difference(spec["paths"].keys())
    if missing:
        raise AssertionError(f"OpenAPI missing expected paths: {sorted(missing)}")
    return spec


def validate_fixtures(spec: dict) -> None:
    schemas = spec["components"]["schemas"]
    fixture_map = {
        "login-success.json": schemas["AuthSuccessResponse"]["required"],
        "refresh-success.json": schemas["AuthSuccessResponse"]["required"],
        "logout-success.json": schemas["LogoutResponse"]["required"],
        "me-success.json": schemas["MeResponse"]["required"],
        "self-me-success.json": schemas["SelfMeResponse"]["required"],
        "self-devices-success.json": schemas["SelfDeviceListResponse"]["required"],
        "self-sessions-success.json": schemas["SelfSessionListResponse"]["required"],
        "self-activity-success.json": schemas["SelfActivityListResponse"]["required"],
        "self-session-revoke-success.json": schemas["SelfSessionRevokeResponse"]["required"],
    }
    for filename, required in fixture_map.items():
        payload = json.loads((FIXTURE_ROOT / filename).read_text(encoding="utf-8"))
        assert_required_keys(payload, required, filename)

    self_me = json.loads((FIXTURE_ROOT / "self-me-success.json").read_text(encoding="utf-8"))
    if "tenant_id" in self_me["user"]:
        raise AssertionError("self-me-success.json must not expose tenant_id")

    self_activity = json.loads((FIXTURE_ROOT / "self-activity-success.json").read_text(encoding="utf-8"))
    allowed_event_types = {
        "login_succeeded",
        "login_failed",
        "session_refreshed",
        "session_revoked",
        "device_bound",
        "device_unbound",
    }
    for event in self_activity["items"]:
        assert_required_keys(event, ["id", "event_type", "created_at", "summary"], "self-activity event")
        if event["event_type"] not in allowed_event_types:
            raise AssertionError(f"self-activity-success.json uses unsupported event_type {event['event_type']}")

    self_revoke = json.loads((FIXTURE_ROOT / "self-session-revoke-success.json").read_text(encoding="utf-8"))
    if self_revoke["success"] is not True:
        raise AssertionError("self-session-revoke-success.json must freeze success=true")
    if self_revoke["auth_state"] != "revoked":
        raise AssertionError("self-session-revoke-success.json must freeze auth_state=revoked")
    if self_revoke["already_revoked"] is not False:
        raise AssertionError("self-session-revoke-success.json must freeze already_revoked=false for the first revoke")

    error_codes = json.loads(
        (ARTIFACT_ROOT / "scripts" / "compat-harness" / "error-codes.json").read_text(encoding="utf-8")
    )["error_codes"]
    for path in FIXTURE_ROOT.glob("error-*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert_required_keys(payload, ["error_code", "message"], path.name)
        if payload["error_code"] not in error_codes:
            raise AssertionError(f"{path.name} uses unknown error code {payload['error_code']}")


def validate_manifest_reproducibility() -> None:
    current = build_manifest()
    checked_in = json.loads(OUTPUT.read_text(encoding="utf-8"))
    if current != checked_in:
        raise AssertionError("phase0 manifest drift detected; regenerate with build_phase0_manifest.py")


def main() -> None:
    spec = validate_openapi()
    validate_fixtures(spec)
    validate_manifest_reproducibility()
    print("phase0 compatibility gate: PASS")


if __name__ == "__main__":
    main()
