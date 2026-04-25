from __future__ import annotations


def resolve_page_metadata(*, limit: int | None, offset: int, returned_count: int) -> tuple[int, int]:
    page_size = limit if limit is not None else returned_count
    if page_size <= 0:
        return 1, 0
    return (offset // page_size) + 1, page_size
