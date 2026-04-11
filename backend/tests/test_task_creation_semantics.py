"""
Phase 2 / PR3 + Phase 6 / PR1: create / assemble path semantics validation tests.

Phase 6 / PR1 keeps this file focused on authoritative task input rules:
- direct-publish validation is collection-based
- topic multiplicity is allowed at validation time
- topic source resolution is handled elsewhere and must not reintroduce legacy FK semantics here
"""
import pytest

from services.task_execution_semantics import TaskSemanticsError, validate_task_resource_inputs


def test_validate_task_resource_inputs_rejects_multiple_copywritings_for_direct_publish() -> None:
    with pytest.raises(TaskSemanticsError, match="仅支持 0 或 1 个文案"):
        validate_task_resource_inputs(
            video_ids=[1],
            copywriting_ids=[10, 11],
            composition_mode="none",
        )


def test_validate_task_resource_inputs_rejects_audio_for_direct_publish() -> None:
    with pytest.raises(TaskSemanticsError, match="不支持独立音频输入"):
        validate_task_resource_inputs(
            video_ids=[1],
            audio_ids=[20],
            composition_mode="none",
        )


def test_validate_task_resource_inputs_allows_broader_inputs_for_composition_mode() -> None:
    validate_task_resource_inputs(
        video_ids=[1, 2],
        copywriting_ids=[10, 11],
        cover_ids=[30, 31],
        audio_ids=[20],
        composition_mode="coze",
    )


def test_validate_task_resource_inputs_allows_single_copywriting_and_cover_for_direct_publish() -> None:
    validate_task_resource_inputs(
        video_ids=[1],
        copywriting_ids=[10],
        cover_ids=[20],
        composition_mode="none",
    )
