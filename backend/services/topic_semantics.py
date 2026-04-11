"""
Topic semantics helpers.

Phase 6 / PR3:
- make current canonical topic semantics explicit before structural migration
"""
from __future__ import annotations


def merge_task_topic_ids(
    *,
    explicit_topic_ids: list[int] | None = None,
    profile_default_topic_ids: list[int] | None = None,
) -> list[int]:
    """
    Merge task topic inputs using the current PR3 baseline semantics.

    Current precedence:
    1. explicit task `topic_ids`
    2. profile-level default topics (`PublishProfile.global_topic_ids`)
    3. stable deduplication in first-seen order

    Not included here:
    - `/api/topics/global` singleton topics
    - `TopicGroup.topic_ids`
    """
    merged: list[int] = []
    seen: set[int] = set()

    for topic_id in (explicit_topic_ids or []) + (profile_default_topic_ids or []):
        if topic_id not in seen:
            merged.append(topic_id)
            seen.add(topic_id)

    return merged
