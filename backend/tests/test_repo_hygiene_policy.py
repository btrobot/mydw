"""
Repo hygiene policy checks for cleanup execution slices.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_gitignore_covers_transient_runtime_and_test_output_paths() -> None:
    gitignore = _read(".gitignore")

    for expected in [
        ".pytest_cache/",
        ".claude/",
        "frontend/logs/",
        "frontend/test-results/",
        "production/session-logs/*.md",
        "!production/session-logs/*.md.template",
    ]:
        assert expected in gitignore, f"missing ignore rule: {expected}"


def test_session_logs_are_template_only() -> None:
    assert (REPO_ROOT / "production/session-logs/.gitkeep").exists()
    assert (REPO_ROOT / "production/session-logs/session-log.md.template").exists()
    assert not (REPO_ROOT / "production/session-logs/session-log.md").exists()


def test_frontend_last_run_artifact_is_not_kept_in_repo() -> None:
    assert not (REPO_ROOT / "frontend/test-results/.last-run.json").exists()


def test_claude_local_settings_are_not_kept_in_repo() -> None:
    assert not (REPO_ROOT / ".claude/settings.local.json").exists()


def test_claude_directory_is_removed_from_repo_surface() -> None:
    assert not (REPO_ROOT / ".claude").exists()


def test_current_docs_no_longer_rely_on_claude_paths() -> None:
    for relative_path in [
        "README.md",
        "AGENTS.md",
        "docs/README.md",
        "docs/runtime-local-artifact-policy.md",
        "docs/doc-inventory-ledger.md",
        "docs/epic-7-doc-authority-matrix.md",
        "docs/dev-guide.md",
        "docs/documentation-strategy.md",
        "docs/doc-checklist.md",
        "docs/multi-agent-guide.md",
    ]:
        assert ".claude/" not in _read(relative_path), f"active doc should not reference .claude/: {relative_path}"
