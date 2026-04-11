"""
Phase 6 / PR5: remaining JSON field decision and migration-ledger checks.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from schemas import AccountResponse, PublishProfileCreate, PublishProfileUpdate


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_repo_file(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_account_response_parses_json_tags_into_list() -> None:
    response = AccountResponse.model_validate(
        {
            "id": 1,
            "account_id": "acct_phase6",
            "account_name": "Phase6 Account",
            "status": "active",
            "tags": '["tag-a", "tag-b"]',
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
    )

    assert response.tags == ["tag-a", "tag-b"]


def test_publish_profile_create_accepts_valid_composition_params_json() -> None:
    profile = PublishProfileCreate(
        name="phase6-profile",
        composition_params='{"workflow":"coze","steps":2}',
    )

    assert profile.composition_params == '{"workflow":"coze","steps":2}'


def test_publish_profile_update_rejects_invalid_composition_params_json() -> None:
    with pytest.raises(ValidationError, match="composition_params 必须是合法的 JSON 字符串"):
        PublishProfileUpdate(composition_params="{invalid-json")


def test_phase6_migration_ledger_documents_final_remaining_json_decisions() -> None:
    ledger = _read_repo_file("docs/phase-6-migration-ledger.md")

    assert "accounts.tags" in ledger
    assert "tasks.source_video_ids" in ledger
    assert "tasks.composition_params" in ledger
    assert "publish_profiles.composition_params" in ledger
    assert "normalize-later" in ledger
    assert "keep-json" in ledger
    assert "delete-ready-later" in ledger
    assert "compat → cutover → delete" in ledger
