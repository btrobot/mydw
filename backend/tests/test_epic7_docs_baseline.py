"""
Epic 7 / PR1: docs baseline and authority-matrix checks.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_repo_file(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_current_architecture_baseline_exists_and_links_runtime_truth() -> None:
    baseline = _read_repo_file("docs/current-architecture-baseline.md")

    assert "当前架构基线" in baseline
    assert "docs/current-runtime-truth.md" in baseline
    assert "docs/runtime-truth.md" in baseline
    assert "docs/epic-7-doc-authority-matrix.md" in baseline
    assert "Phase 1-6" in baseline


def test_doc_authority_matrix_defines_baseline_runtime_and_legacy_roles() -> None:
    authority_matrix = _read_repo_file("docs/epic-7-doc-authority-matrix.md")

    assert "docs/README.md" in authority_matrix
    assert "current-architecture-baseline.md" in authority_matrix
    assert "current-runtime-truth.md" in authority_matrix
    assert "runtime-truth.md" in authority_matrix
    assert "system-architecture.md" in authority_matrix
    assert "authoritative" in authority_matrix
    assert "entrypoint" in authority_matrix
    assert "legacy" in authority_matrix or "archival" in authority_matrix


def test_runtime_truth_alias_is_lightweight_entrypoint_not_competing_source() -> None:
    runtime_truth_alias = _read_repo_file("docs/runtime-truth.md")

    assert "入口" in runtime_truth_alias
    assert "docs/current-runtime-truth.md" in runtime_truth_alias
    assert "docs/current-architecture-baseline.md" in runtime_truth_alias
    assert "不应与 canonical 内容竞争" in runtime_truth_alias


def test_current_architecture_baseline_contains_recommended_reading_path() -> None:
    baseline = _read_repo_file("docs/current-architecture-baseline.md")

    assert "推荐阅读路径" in baseline
    assert "README.md" in baseline
    assert "docs/README.md" in baseline
    assert "docs/current-runtime-truth.md" in baseline


def test_docs_parity_checklist_covers_phase_1_to_6_truths() -> None:
    checklist = _read_repo_file("docs/epic-7-docs-parity-checklist.md")

    assert "schedule-config" in checklist
    assert "publish status" in checklist
    assert "task semantics" in checklist
    assert "settings" in checklist
    assert "topic relation" in checklist


def test_docs_readme_exists_and_separates_current_docs_from_runtime_artifacts() -> None:
    docs_index = _read_repo_file("docs/README.md")

    assert "文档导航" in docs_index or "Documentation" in docs_index
    assert "docs/current-architecture-baseline.md" in docs_index
    assert "docs/current-runtime-truth.md" in docs_index
    assert "docs/epic-7-doc-authority-matrix.md" in docs_index
    assert "docs/doc-inventory-ledger.md" in docs_index
    assert "docs/runtime-local-artifact-policy.md" in docs_index
    assert "docs/archive/exports/" in docs_index
    assert ".codex/" in docs_index
    assert ".omx/" in docs_index
    assert ".claude/" not in docs_index
    assert "runtime" in docs_index or "本地" in docs_index or "运行时" in docs_index


def test_doc_inventory_ledger_classifies_major_document_and_runtime_clusters() -> None:
    ledger = _read_repo_file("docs/doc-inventory-ledger.md")

    assert "Inventory Ledger" in ledger or "台账" in ledger
    assert "docs/" in ledger
    assert "design/" in ledger
    assert "dev-docs/" in ledger
    assert "private-docs/" in ledger
    assert "backend/docs/" in ledger
    assert "docs/archive/exports/" in ledger
    assert "production/" in ledger
    assert ".codex/" in ledger
    assert ".omx/" in ledger
    assert ".claude/" not in ledger
    assert "current" in ledger
    assert "working" in ledger
    assert "historical" in ledger or "archival" in ledger
    assert "runtime" in ledger
    assert "keep" in ledger
    assert "archive" in ledger or "move" in ledger


def test_first_archive_batch_moves_old_planning_docs_out_of_docs_root() -> None:
    archived = [
        "docs/archive/planning/task-breakdown-phase1.md",
        "docs/archive/planning/task-breakdown-phase3.md",
        "docs/archive/planning/task-breakdown-phase4.md",
        "docs/archive/planning/sprint-plan-phase1.md",
        "docs/archive/planning/sprint-plan-phase3.md",
        "docs/archive/planning/sprint-plan-phase4.md",
        "docs/archive/planning/sprint-plan-sprint5.md",
        "docs/archive/planning/sprint-6-plan.md",
        "docs/archive/planning/sprint-7-plan.md",
        "docs/archive/planning/sprint-8-plan.md",
    ]

    for archived_path in archived:
        assert (REPO_ROOT / archived_path).exists(), f"missing archived file: {archived_path}"

    for root_path in [
        "docs/task-breakdown-phase1.md",
        "docs/task-breakdown-phase3.md",
        "docs/task-breakdown-phase4.md",
        "docs/sprint-plan-phase1.md",
        "docs/sprint-plan-phase3.md",
        "docs/sprint-plan-phase4.md",
        "docs/sprint-plan-sprint5.md",
        "docs/sprint-6-plan.md",
        "docs/sprint-7-plan.md",
        "docs/sprint-8-plan.md",
    ]:
        assert not (REPO_ROOT / root_path).exists(), f"file should no longer be in docs root: {root_path}"


def test_second_archive_batch_moves_unreferenced_analysis_docs_out_of_docs_root() -> None:
    archived = [
        "docs/archive/analysis/refactor-list.md",
        "docs/archive/analysis/task-management-analysis.md",
        "docs/archive/analysis/task-management-er-design.md",
        "docs/archive/analysis/task-management-operations.md",
    ]

    for archived_path in archived:
        assert (REPO_ROOT / archived_path).exists(), f"missing archived file: {archived_path}"

    for root_path in [
        "docs/refactor-list.md",
        "docs/task-management-analysis.md",
        "docs/task-management-er-design.md",
        "docs/task-management-operations.md",
    ]:
        assert not (REPO_ROOT / root_path).exists(), f"file should no longer be in docs root: {root_path}"


def test_design_and_devdocs_archive_batch_moves_exploratory_docs_out_of_primary_paths() -> None:
    archived = [
        "design/archive/Claude Code Hooks.md",
        "design/archive/sprint-intro.md",
        "design/archive/task-breakdown-intro.md",
        "dev-docs/archive/dewu-login-automation.md",
        "dev-docs/archive/login-dewu.md",
        "dev-docs/archive/thinking-x.md",
        "dev-docs/archive/req-04-02.md",
    ]

    for archived_path in archived:
        assert (REPO_ROOT / archived_path).exists(), f"missing archived file: {archived_path}"

    for root_path in [
        "design/Claude Code Hooks.md",
        "design/sprint-intro.md",
        "design/task-breakdown-intro.md",
        "dev-docs/dewu-login-automation.md",
        "dev-docs/login-dewu.md",
        "dev-docs/thinking-x.md",
        "dev-docs/req/04-02.md",
    ]:
        assert not (REPO_ROOT / root_path).exists(), f"file should no longer remain in primary path: {root_path}"


def test_backend_docs_archive_batch_moves_legacy_backend_design_docs_out_of_primary_path() -> None:
    archived = [
        "backend/docs/archive/account-management-design.md",
        "backend/docs/archive/api-contract-connect.md",
        "backend/docs/archive/batch-health-check-design.md",
        "backend/docs/archive/state-machine.md",
    ]

    for archived_path in archived:
        assert (REPO_ROOT / archived_path).exists(), f"missing archived file: {archived_path}"

    for root_path in [
        "backend/docs/account-management-design.md",
        "backend/docs/api-contract-connect.md",
        "backend/docs/batch-health-check-design.md",
        "backend/docs/state-machine.md",
    ]:
        assert not (REPO_ROOT / root_path).exists(), f"file should no longer remain in backend/docs root: {root_path}"


def test_design_core_archive_batch_moves_stale_stack_and_login_docs_out_of_primary_path() -> None:
    archived = [
        "design/archive/backend-stack.md",
        "design/archive/frontend-stack.md",
        "design/archive/login-arch.md",
    ]

    for archived_path in archived:
        assert (REPO_ROOT / archived_path).exists(), f"missing archived file: {archived_path}"

    for root_path in [
        "design/backend-stack.md",
        "design/frontend-stack.md",
        "design/login-arch.md",
    ]:
        assert not (REPO_ROOT / root_path).exists(), f"file should no longer remain in design root: {root_path}"


def test_runtime_local_artifact_policy_documents_boundary_and_current_git_state() -> None:
    policy = _read_repo_file("docs/runtime-local-artifact-policy.md")

    assert ".codex/" in policy
    assert ".omx/" in policy
    assert ".claude/" not in policy
    assert "docs/archive/exports/" in policy
    assert "production/session-logs" in policy or "production/session-state" in policy
    assert ".gitignore" in policy
    assert "runtime" in policy or "本地" in policy or "运行时" in policy
    assert "committed" in policy or "已提交" in policy
    assert "future policy" in policy or "后续策略" in policy


def test_root_plans_and_task_breakdown_examples_move_out_of_root_runtime_paths() -> None:
    archived = [
        "docs/archive/planning/cosmic-baking-micali.md",
        "docs/archive/examples/task-management-impl.md",
        "docs/archive/examples/task-orchestration.md",
    ]

    for archived_path in archived:
        assert (REPO_ROOT / archived_path).exists(), f"missing archived file: {archived_path}"

    for old_path in [
        "plans/cosmic-baking-micali.md",
        "production/task-breakdown/task-management-impl.md",
        "production/task-breakdown/task-orchestration.md",
    ]:
        assert not (REPO_ROOT / old_path).exists(), f"file should no longer remain in old path: {old_path}"


def test_private_docs_move_into_archive_and_d_mirror_dirs_are_reclassified_as_local_paths() -> None:
    archived = [
        "docs/archive/private/arch.md",
        "docs/archive/private/multi-agents-review.md",
    ]

    for archived_path in archived:
        assert (REPO_ROOT / archived_path).exists(), f"missing archived file: {archived_path}"

    for old_path in [
        "private-docs/arch.md",
        "private-docs/multi-agents-review.md",
    ]:
        assert not (REPO_ROOT / old_path).exists(), f"file should no longer remain in old path: {old_path}"

    runtime_policy = _read_repo_file("docs/runtime-local-artifact-policy.md")
    assert "D:" in runtime_policy or "mirror" in runtime_policy


def test_export_snapshots_move_under_docs_archive_exports() -> None:
    archived = [
        "docs/archive/exports/dewu-architecture-and-dataflow.md",
        "docs/archive/exports/dewu-architecture-risks-and-refactor-recommendations.md",
        "docs/archive/exports/dewu-database-models-and-field-responsibilities.md",
        "docs/archive/exports/dewu-frontend-backend-interface-mapping.md",
        "docs/archive/exports/dewu-frontend-backend-page-api-mapping.md",
        "docs/archive/exports/dewu-page-api-mapping.md",
        "docs/archive/exports/dewu-project-overview.md",
        "docs/archive/exports/dewu-task-end-to-end-sequence.md",
        "docs/archive/exports/dewu-task-lifecycle-sequence.md",
    ]

    for archived_path in archived:
        assert (REPO_ROOT / archived_path).exists(), f"missing archived export: {archived_path}"

    assert not (REPO_ROOT / ".codex-export").exists(), ".codex-export should no longer remain at repo root"
