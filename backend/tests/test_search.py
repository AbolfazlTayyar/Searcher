"""Endpoint tests for `GET /search`.

Each test asserts on exact names from the fixed fixture set in `conftest.py`
rather than just a result count, so a test would fail if the query matched
the wrong documents for the right reason (e.g. an `OR` where a `filter`
should be an `AND`), not just the right number of documents.
"""

from __future__ import annotations

from httpx import AsyncClient


async def test_keyword_only_search(client: AsyncClient) -> None:
    response = await client.get("/search", params={"q": "kubernetes"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [result["name"] for result in body["results"]] == ["Alice Nguyen"]


async def test_job_title_filter_alone(client: AsyncClient) -> None:
    response = await client.get("/search", params={"job_title": "Data Scientist"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert {result["name"] for result in body["results"]} == {"Bob Smith", "Carol Diaz"}


async def test_skill_filter_alone(client: AsyncClient) -> None:
    response = await client.get("/search", params={"skill": "machine learning"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [result["name"] for result in body["results"]] == ["Bob Smith"]


async def test_job_title_and_skill_filters_combined(client: AsyncClient) -> None:
    response = await client.get("/search", params={"job_title": "Data Scientist", "skill": "sql"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [result["name"] for result in body["results"]] == ["Carol Diaz"]


async def test_keyword_search_is_case_insensitive(client: AsyncClient) -> None:
    response = await client.get("/search", params={"q": "KUBERNETES"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [result["name"] for result in body["results"]] == ["Alice Nguyen"]


async def test_job_title_filter_is_case_insensitive(client: AsyncClient) -> None:
    response = await client.get("/search", params={"job_title": "data scientist"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert {result["name"] for result in body["results"]} == {"Bob Smith", "Carol Diaz"}


async def test_skill_filter_is_case_insensitive(client: AsyncClient) -> None:
    response = await client.get("/search", params={"skill": "MACHINE LEARNING"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [result["name"] for result in body["results"]] == ["Bob Smith"]


async def test_query_with_no_matches_returns_empty_results(client: AsyncClient) -> None:
    response = await client.get("/search", params={"q": "nonexistent-keyword-xyz"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["results"] == []


async def test_page_past_es_result_window_returns_empty_results_not_an_error(
    client: AsyncClient,
) -> None:
    """A page number whose `from + size` exceeds ES's 10,000 result-window limit
    is still a valid (if pointless) request -- it should degrade to an empty
    page with the real `total`, not a raw ES error."""
    response = await client.get("/search", params={"page": 501, "page_size": 20})

    assert response.status_code == 200
    body = response.json()
    assert body["results"] == []
    assert body["total"] == 4
    assert body["page"] == 501
    assert body["page_size"] == 20
