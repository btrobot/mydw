"""
Epic 7 / PR2: stale-doc cleanup and reading-path checks.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_repo_file(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_readme_points_to_current_authoritative_docs() -> None:
    readme = _read_repo_file("README.md")

    assert "当前推荐阅读入口" in readme
    assert "docs/README.md" in readme
    assert "docs/current/architecture.md" in readme
    assert "docs/current/runtime-truth.md" in readme
    assert "ARCHITECTURE.md" not in readme


def test_system_architecture_is_marked_stale_and_redirects() -> None:
    system_arch = _read_repo_file("docs/archive/reference/system-architecture.md")

    assert "Status: Stale" in system_arch or "状态: Stale" in system_arch or "已过时" in system_arch
    assert "docs/current/architecture.md" in system_arch
    assert "docs/current/runtime-truth.md" in system_arch


def test_api_reference_is_marked_stale_and_points_to_live_surfaces() -> None:
    api_ref = _read_repo_file("docs/archive/reference/api-reference.md")

    assert "Status: Stale" in api_ref or "状态: Stale" in api_ref or "已过时" in api_ref
    assert "/docs" in api_ref
    assert "/openapi.json" in api_ref
    assert "docs/current/architecture.md" in api_ref


def test_data_model_doc_is_marked_stale_and_points_to_current_truth() -> None:
    data_model = _read_repo_file("docs/archive/reference/data-model.md")

    assert "Status: Stale" in data_model or "状态: Stale" in data_model or "已过时" in data_model
    assert "backend/models/__init__.py" in data_model
    assert "docs/current/architecture.md" in data_model
    assert "docs/current/runtime-truth.md" in data_model


def test_stale_doc_inventory_lists_high_visibility_docs() -> None:
    inventory = _read_repo_file("docs/governance/inventory/epic-7-stale-doc-inventory.md")

    assert "README.md" in inventory
    assert "docs/archive/reference/system-architecture.md" in inventory
    assert "docs/archive/reference/api-reference.md" in inventory
    assert "docs/archive/reference/data-model.md" in inventory
    assert "docs/current/architecture.md" in inventory
    assert "recommended reading path" in inventory or "推荐阅读路径" in inventory


def test_refactor_planning_docs_are_marked_historical_and_redirect_to_current_truth() -> None:
    for relative_path in [
        "docs/archive/history/refactor-roadmap.md",
        "docs/archive/history/refactor-issue-breakdown.md",
        "docs/archive/history/refactor-gap-list.md",
    ]:
        content = _read_repo_file(relative_path)

        assert "Historical Planning Reference" in content or "历史规划参考" in content
        assert "docs/README.md" in content
        assert "docs/current/architecture.md" in content
        assert "docs/current/runtime-truth.md" in content
        assert ".omx" in content or "历史 planning context" in content or "历史上下文" in content
