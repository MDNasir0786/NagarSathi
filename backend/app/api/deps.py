"""Shared router dependencies (pagination, common query parameters)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query

from app.utils.config import settings


@dataclass(frozen=True)
class Pagination:
    limit: int
    offset: int


def pagination_params(
    limit: Annotated[
        int,
        Query(ge=1, le=settings.max_page_size, description="Page size."),
    ] = settings.default_page_size,
    offset: Annotated[int, Query(ge=0, description="Rows to skip.")] = 0,
) -> Pagination:
    return Pagination(limit=limit, offset=offset)


PaginationDep = Annotated[Pagination, Depends(pagination_params)]

WindowDays = Annotated[
    int,
    Query(ge=1, le=365, description="Analysis window in days."),
]
