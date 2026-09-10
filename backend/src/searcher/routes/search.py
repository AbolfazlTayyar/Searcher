"""`GET /search` route.

Stays thin per CLAUDE.md's backend conventions: parse/validate query params
(via Pydantic's `Query` constraints, not manual `if` checks), delegate query
building and execution to `search_service.py`, return its response model
as-is. No ES query-building logic lives here.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from searcher.config import Settings, get_settings
from searcher.dependencies import ESClientDep
from searcher.models import SearchResponse
from searcher.search_service import search_profiles

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search(
    client: ESClientDep,
    settings: Annotated[Settings, Depends(get_settings)],
    q: str | None = Query(default=None, description="Free-text keyword search"),
    job_title: str | None = Query(default=None, description="Exact job title filter"),
    skill: str | None = Query(default=None, description="Exact skill filter"),
    page: int = Query(default=1, ge=1, description="1-indexed page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Results per page"),
) -> SearchResponse:
    """Keyword search over `q`, narrowed by `job_title`/`skill`, paginated."""
    return await search_profiles(
        client,
        settings.ES_INDEX_NAME,
        q=q,
        job_title=job_title,
        skill=skill,
        page=page,
        page_size=page_size,
    )
