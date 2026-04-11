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
    assert "docs/current-runtime-truth.md" in baseline


def test_docs_parity_checklist_covers_phase_1_to_6_truths() -> None:
    checklist = _read_repo_file("docs/epic-7-docs-parity-checklist.md")

    assert "schedule-config" in checklist
    assert "publish status" in checklist
    assert "task semantics" in checklist
    assert "settings" in checklist
    assert "topic relation" in checklist
