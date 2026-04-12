"""
Repo hygiene policy checks for cleanup execution slices.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def _tracked_paths() -> set[str]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line for line in completed.stdout.splitlines() if line}


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_gitignore_covers_transient_runtime_and_test_output_paths() -> None:
    gitignore = _read(".gitignore")

    for expected in [
        ".pytest_cache/",
        ".omc/",
        ".omx/",
        ".claude/",
        ".codex/*",
        "!.codex/agents/",
        "!.codex/agents/**",
        "!.codex/skills/",
        "!.codex/skills/**",
        "!.codex/prompts/",
        "!.codex/prompts/**",
        "/D:/",
        "production/",
        "frontend/logs/",
        "frontend/test-results/",
    ]:
        assert expected in gitignore, f"missing ignore rule: {expected}"


def test_production_directory_is_removed_from_repo_surface() -> None:
    assert not (REPO_ROOT / "production").exists()


def test_frontend_last_run_artifact_is_not_kept_in_repo() -> None:
    assert not (REPO_ROOT / "frontend/test-results/.last-run.json").exists()


def test_claude_local_settings_are_not_kept_in_repo() -> None:
    assert not (REPO_ROOT / ".claude/settings.local.json").exists()


def test_claude_directory_is_removed_from_repo_surface() -> None:
    assert not (REPO_ROOT / ".claude").exists()


def test_omc_runtime_state_files_are_not_tracked() -> None:
    tracked = _tracked_paths()

    for relative_path in [
        ".omc/project-memory.json",
        ".omc/state/mission-state.json",
    ]:
        assert relative_path not in tracked, f"runtime state file should not be tracked: {relative_path}"


def test_backend_debug_scripts_and_screenshots_are_not_tracked() -> None:
    tracked = _tracked_paths()

    for relative_path in [
        "backend/explore_dewu_login.py",
        "backend/explore_error.png",
        "backend/explore_login_page.png",
        "backend/login_page_raw.png",
        "backend/stealth_step1.png",
        "backend/stealth_step2.png",
        "backend/step1_dom_loaded.png",
        "backend/step2_js_executed.png",
        "backend/test_browser.py",
        "backend/test_debug_page.py",
        "backend/test_export_session.py",
        "backend/test_login_flow.py",
        "backend/test_patch_login.py",
        "backend/test_patch_login_debug.py",
        "backend/test_patchright.py",
        "backend/test_scrapling.py",
        "backend/test_sms_login.py",
    ]:
        assert relative_path not in tracked, f"debug artifact should not be tracked: {relative_path}"


def test_windows_mirror_directory_is_not_tracked() -> None:
    tracked = _tracked_paths()
    assert not any(path == "D:" or path.startswith("D:/") for path in tracked)


def test_design_archive_uses_single_directory_name() -> None:
    assert (REPO_ROOT / "design/archive").exists()
    assert not (REPO_ROOT / "design/archived").exists()
