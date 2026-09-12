"""Endpoint tests for `GET /suggest`.

Uses the same fixed fixture set as `test_search.py`: "Data Scientist" appears
on two documents (Bob Smith, Carol Diaz), so it also covers that a repeated
value is returned once, not once per document.
"""

from __future__ import annotations

from httpx import AsyncClient


async def test_job_title_prefix_match(client: AsyncClient) -> None:
    response = await client.get("/suggest", params={"field": "job_title", "prefix": "data"})

    assert response.status_code == 200
    assert response.json()["values"] == ["Data Scientist"]


async def test_prefix_match_is_case_insensitive(client: AsyncClient) -> None:
    response = await client.get("/suggest", params={"field": "job_title", "prefix": "DATA"})

    assert response.status_code == 200
    assert response.json()["values"] == ["Data Scientist"]


async def test_prefix_matches_any_word_in_a_multi_word_value(client: AsyncClient) -> None:
    response = await client.get("/suggest", params={"field": "job_title", "prefix": "sci"})

    assert response.status_code == 200
    assert response.json()["values"] == ["Data Scientist"]


async def test_skill_prefix_match(client: AsyncClient) -> None:
    response = await client.get("/suggest", params={"field": "skill", "prefix": "mach"})

    assert response.status_code == 200
    assert response.json()["values"] == ["machine learning"]


async def test_no_prefix_match_returns_empty_list(client: AsyncClient) -> None:
    response = await client.get("/suggest", params={"field": "job_title", "prefix": "zzz"})

    assert response.status_code == 200
    assert response.json()["values"] == []


async def test_limit_out_of_range_is_rejected(client: AsyncClient) -> None:
    response = await client.get("/suggest", params={"field": "skill", "prefix": "p", "limit": 0})

    assert response.status_code == 422


async def test_unknown_field_is_rejected(client: AsyncClient) -> None:
    response = await client.get("/suggest", params={"field": "industry", "prefix": "tech"})

    assert response.status_code == 422


async def test_empty_prefix_is_rejected(client: AsyncClient) -> None:
    response = await client.get("/suggest", params={"field": "job_title", "prefix": ""})

    assert response.status_code == 422
