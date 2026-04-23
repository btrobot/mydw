from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_phase0_contract_docs_exist() -> None:
    required = [
        ".omx/plans/phase0-creative-two-level-candidate-pool-authority-matrix-2026-04-24.md",
        ".omx/plans/phase0-creative-two-level-candidate-pool-primary-product-rules-2026-04-24.md",
        ".omx/plans/phase0-creative-two-level-candidate-pool-current-cover-contract-2026-04-24.md",
        ".omx/plans/phase0-creative-two-level-candidate-pool-input-items-compat-retirement-2026-04-24.md",
        ".omx/plans/phase0-creative-two-level-candidate-pool-workbench-summary-mapping-2026-04-24.md",
        ".omx/plans/phase0-creative-two-level-candidate-pool-manifest-v1-contract-2026-04-24.md",
    ]

    for rel in required:
        assert (REPO_ROOT / rel).exists(), f"missing Phase 0 contract: {rel}"


def test_authority_matrix_freezes_read_write_freeze_and_retirement() -> None:
    doc = _read(".omx/plans/phase0-creative-two-level-candidate-pool-authority-matrix-2026-04-24.md")

    assert "Write source" in doc
    assert "Read source" in doc
    assert "Freeze source" in doc
    assert "Compatibility source" in doc
    assert "Retirement slice" in doc
    assert "primary product" in doc
    assert "current product name" in doc
    assert "current cover" in doc
    assert "current copywriting" in doc
    assert "candidate items" in doc
    assert "selected video set" in doc
    assert "selected audio set" in doc
    assert "version freeze source" in doc
    assert "package freeze source" in doc
    assert "workbench summary" in doc
    assert "manifest v1" in doc


def test_primary_product_rules_freeze_single_write_entry_and_manual_follow_behavior() -> None:
    doc = _read(".omx/plans/phase0-creative-two-level-candidate-pool-primary-product-rules-2026-04-24.md")

    assert "primary product 只能有一个" in doc
    assert "`creative_product_links.is_primary = true`" in doc
    assert "`creative_items.subject_product_id` 作为兼容镜像" in doc
    assert "`product_name_mode = follow_primary_product`" in doc
    assert "`product_name_mode = manual`" in doc
    assert "`cover_mode = default_from_primary_product`" in doc
    assert "唯一写入口" in doc


def test_current_cover_contract_freezes_db_api_and_freeze_paths() -> None:
    doc = _read(".omx/plans/phase0-creative-two-level-candidate-pool-current-cover-contract-2026-04-24.md")

    assert "creative_items.current_cover_asset_type" in doc
    assert "creative_items.current_cover_asset_id" in doc
    assert "creative_items.cover_mode" in doc
    assert "CreativeDetailResponse" in doc
    assert "creative_version_service.py" in doc
    assert "creative_generation_service.py" in doc
    assert "publish_service.py" in doc
    assert "ai_clip_workflow_service.py" in doc


def test_input_items_compat_retirement_table_freezes_non_media_retirement() -> None:
    doc = _read(".omx/plans/phase0-creative-two-level-candidate-pool-input-items-compat-retirement-2026-04-24.md")

    assert "| video | selected-media projection |" in doc
    assert "| audio | selected-media projection |" in doc
    assert "| copywriting | read-only compatibility |" in doc
    assert "| cover | read-only compatibility |" in doc
    assert "| topic | candidate / prompt reference only |" in doc
    assert "Cutover Trigger" in doc
    assert "selected-media projection 稳定" in doc


def test_workbench_summary_mapping_freezes_sources_and_query_policy() -> None:
    doc = _read(".omx/plans/phase0-creative-two-level-candidate-pool-workbench-summary-mapping-2026-04-24.md")

    assert "`current_product_name`" in doc
    assert "`selected_video_count`" in doc
    assert "`candidate_cover_count`" in doc
    assert "`definition_ready`" in doc
    assert "`composition_ready`" in doc
    assert "展示优先" in doc
    assert "前端禁止自行重复推导" in doc


def test_manifest_v1_contract_freezes_typed_shape() -> None:
    doc = _read(".omx/plans/phase0-creative-two-level-candidate-pool-manifest-v1-contract-2026-04-24.md")

    assert '"version": "v1"' in doc
    assert '"current_cover"' in doc
    assert '"current_copywriting"' in doc
    assert '"selected_videos"' in doc
    assert '"selected_audios"' in doc
    assert "selected-media projection" in doc
    assert "current truth contracts" in doc


def test_phase0_prd_and_test_spec_reference_gate_artifacts() -> None:
    prd = _read(".omx/plans/prd-creative-two-level-candidate-pool-adoption-2026-04-24.md")
    spec = _read(".omx/plans/test-spec-creative-two-level-candidate-pool-adoption-2026-04-24.md")

    assert "authority matrix" in prd
    assert "current cover contract" in prd
    assert "Workbench 摘要字段映射" in prd
    assert "manifest v1" in prd
    assert "authority matrix" in spec
    assert "selected-media projection" in spec
    assert "manifest v1" in spec
