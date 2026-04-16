from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = ROOT / "remote" / "remote-shared" / "docs"
OPENAPI_PATH = ROOT / "remote" / "remote-shared" / "openapi" / "remote-auth-v1.yaml"
PHASE0_MANIFEST = ROOT / "remote" / "remote-shared" / "openapi" / "phase0-manifest.json"
PHASE1_MANIFEST = ROOT / "remote" / "remote-shared" / "openapi" / "phase1-manifest.json"


def test_b0_pr1_docs_exist_and_freeze_self_service_boundaries() -> None:
    end_user = (DOCS_ROOT / "end-user-auth-api-contract-v1.md").read_text(encoding="utf-8")
    browser = (DOCS_ROOT / "self-service-browser-contract-v1.md").read_text(encoding="utf-8")
    boundaries = (DOCS_ROOT / "auth-domain-boundaries.md").read_text(encoding="utf-8")
    errors = (DOCS_ROOT / "error-code-matrix.md").read_text(encoding="utf-8")

    assert "GET /self/me" in end_user
    assert "GET /self/activity" in end_user
    assert "canonical portal-facing current-user route" in end_user
    assert "must not freeze `tenant_id`" in end_user
    assert "own existing active session -> `200`" in end_user

    assert "Portal work must target" in browser
    assert "`GET /me` remains a legacy compatibility route" in browser
    assert "tenant_id" in browser
    assert "recent activity" in browser.lower()
    assert "must not depend on" in browser

    assert "/self/me" in boundaries
    assert "/self/activity" in boundaries
    assert "canonical self-service namespace" in boundaries
    assert "must not depend on admin-only response shapes" in boundaries

    assert "self-service-specific code" in errors
    assert "self-service routes reuse the same `v1` `error_code` matrix" in errors


def test_b0_pr1_source_openapi_freezes_self_service_contract_shapes() -> None:
    spec = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))

    for path in [
        "/self/me",
        "/self/devices",
        "/self/sessions",
        "/self/activity",
        "/self/sessions/{session_id}/revoke",
    ]:
        assert path in spec["paths"], path

    assert "/me" in spec["paths"]

    self_me_schema = spec["components"]["schemas"]["SelfMeResponse"]
    self_user_schema = spec["components"]["schemas"]["SelfUserIdentity"]
    self_activity_schema = spec["components"]["schemas"]["SelfActivityResponse"]
    revoke_schema = spec["components"]["schemas"]["SelfSessionRevokeResponse"]

    assert "tenant_id" not in self_user_schema["properties"]
    assert self_me_schema["properties"]["user"]["$ref"] == "#/components/schemas/SelfUserIdentity"

    assert sorted(self_activity_schema["required"]) == ["created_at", "event_type", "id", "summary"]
    assert "device_id" in self_activity_schema["properties"]
    assert "session_id" in self_activity_schema["properties"]

    assert revoke_schema["required"] == ["success", "session_id", "auth_state", "already_revoked"]

    activity_params = spec["paths"]["/self/activity"]["get"]["parameters"]
    assert [param["name"] for param in activity_params] == ["limit", "offset"]

    revoke_responses = spec["paths"]["/self/sessions/{session_id}/revoke"]["post"]["responses"]
    assert "200" in revoke_responses
    assert "401" in revoke_responses
    assert "403" in revoke_responses
    assert "404" in revoke_responses


def test_b0_pr1_manifests_capture_new_docs_and_fixtures() -> None:
    phase0 = json.loads(PHASE0_MANIFEST.read_text(encoding="utf-8"))
    phase1 = json.loads(PHASE1_MANIFEST.read_text(encoding="utf-8"))

    for manifest in [phase0, phase1]:
        docs = {entry["file"] for entry in manifest["docs"]}
        fixtures = {entry["file"] for entry in manifest["fixtures"]}

        assert "self-service-browser-contract-v1.md" in docs
        for fixture_name in [
            "self-me-success.json",
            "self-devices-success.json",
            "self-sessions-success.json",
            "self-activity-success.json",
            "self-session-revoke-success.json",
            "error-not-found.json",
        ]:
            assert fixture_name in fixtures
