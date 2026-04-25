from __future__ import annotations

from pydantic import BaseModel


class PageMetadata(BaseModel):
    total: int
    page: int
    page_size: int
