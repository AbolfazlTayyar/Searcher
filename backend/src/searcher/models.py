"""Pydantic request/response models for the search API.

Kept separate from `search_service.py` so the API's public shape (what the
frontend can rely on) stays decoupled from how it's produced from ES's
response documents -- no raw ES `_source` dicts cross the API boundary.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProfileResult(BaseModel):
    """A single profile as displayed in the results list.

    Deliberately narrower than the full indexed document (nested
    `experience`/`education`/`certifications`/etc. aren't surfaced here) --
    only the fields `ResultsList.tsx` actually renders. Every field is
    optional because the source dataset leaves many of them legitimately
    empty (e.g. `job_title` ~28%, `industry` ~40%) rather than that being an
    error condition.
    """

    name: str | None = Field(default=None, description="Full name")
    job_title: str | None = Field(default=None, description="Current job title")
    industry: str | None = Field(default=None, description="Industry")
    skills: list[str] = Field(default_factory=list, description="Skill keywords")
    summary: str | None = Field(default=None, description="Free-text profile summary")
    location: str | None = Field(default=None, description="Location name")


class SearchResponse(BaseModel):
    """Paginated envelope returned by `GET /search`."""

    results: list[ProfileResult]
    total: int = Field(ge=0, description="Total number of matching profiles")
    page: int = Field(ge=1, description="Current page number, 1-indexed")
    page_size: int = Field(ge=1, description="Number of results per page")


class SuggestResponse(BaseModel):
    """Envelope returned by `GET /suggest` -- exact values a filter would accept."""

    values: list[str] = Field(description="Matching field values, most frequent first")
