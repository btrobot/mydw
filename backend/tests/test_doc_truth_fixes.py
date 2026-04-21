"""
Code-review remediation PR-A: documentation truth-fix checks.
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_openapi_workflow_describes_tracked_generated_snapshot_correctly() -> None:
    workflow = _read("docs/guides/openapi-generation-workflow.md")

    assert "frontend/openapi.local.json" in workflow
    assert "tracked generated artifact" in workflow
    assert "docs/governance/generated-artifact-policy.md" in workflow
    assert "npm run generated:check" in workflow


def test_readme_uses_actual_packaged_output_directory() -> None:
    readme = _read("README.md")

    assert "dist-electron" in readme
    assert "frontend/release/" not in readme


def test_documentation_strategy_matches_epic7_authority_model() -> None:
    strategy = _read("docs/governance/documentation-strategy.md")

    assert "docs/current/architecture.md" in strategy
    assert "docs/current/runtime-truth.md" in strategy
    assert "system-architecture.md" in strategy
    assert "唯一来源" not in strategy or "system-architecture.md 是架构的唯一来源" not in strategy


def test_doc_checklist_recognizes_current_vs_archival_docs() -> None:
    checklist = _read("docs/governance/doc-checklist.md")

    assert "docs/current/architecture.md" in checklist
    assert "docs/current/runtime-truth.md" in checklist
    assert "stale" in checklist or "archival" in checklist or "过时" in checklist
    assert "system-architecture.md" in checklist


def test_task_domain_doc_matches_local_ffmpeg_v1_truth() -> None:
    doc = _read("docs/domains/tasks/task-management-domain-model.md")

    assert "local_ffmpeg V1" in doc
    assert "不走 `CompositionPoller`" in doc
    assert "1 个视频输入" in doc
    assert "0/1 个音频输入" in doc
    assert "multi-video montage" in doc
    assert "本地同步执行" in doc


def test_task_semantics_doc_no_longer_claims_broad_local_ffmpeg_inputs() -> None:
    doc = _read("docs/domains/tasks/task-semantics.md")

    assert "local_ffmpeg V1" in doc
    assert "broader composition inputs surface" in doc
    assert "submit_composition()" in doc
    assert "final_video_path" in doc
    assert "CompositionPoller" in doc
    assert "broader composition inputs 仍然允许" not in doc


def test_local_ffmpeg_closeout_doc_lists_support_limits_and_regression_commands() -> None:
    doc = _read("docs/domains/publishing/local-ffmpeg-composition.md")

    assert "PR-4 docs + regression closeout" in doc
    assert "1 个视频输入" in doc
    assert "0/1 个音频输入" in doc
    assert "multi-video montage" in doc
    assert "pytest tests/test_local_ffmpeg_composition.py" in doc
    assert "npm run typecheck" in doc


def test_project_introduction_uses_canonical_dev_baseline_and_electron_ts_entry() -> None:
    intro = _read("docs/specs/project-introduction.md")

    assert "frontend/electron/main.ts" in intro
    assert "frontend/electron/main.js" not in intro
    assert "Node 22+" in intro
    assert "Python 3.11+" in intro
    assert "FFmpeg 6+" in intro
    assert "docs/guides/startup-protocol.md" in intro
