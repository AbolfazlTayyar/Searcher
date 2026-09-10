"""Shared fixtures for endpoint tests.

Endpoint tests hit a real Elasticsearch index rather than a mocked client,
since what's under test is query correctness (does `job_title.keyword` +
`skills.keyword` filtering, `multi_match` scoring, and their combination
actually behave against a real ES) -- a mock would just assert that our code
calls the mock the way our code calls the mock. The index is created fresh
under a unique name per test session and dropped afterward, so tests never
touch the `linkedin_profiles` index used by the real app.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest_asyncio
from elasticsearch import AsyncElasticsearch
from httpx import ASGITransport, AsyncClient

from searcher.config import Settings, get_settings
from searcher.dependencies import get_es_client
from searcher.ingest.mapping import PROFILE_INDEX_MAPPING, PROFILE_INDEX_SETTINGS
from searcher.main import app

TEST_INDEX_NAME = f"linkedin_profiles_test_{uuid.uuid4().hex[:8]}"

# Fixed fixture documents, chosen so each test can assert on an exact,
# non-overlapping slice: only "Alice Nguyen" mentions "kubernetes" in her
# summary (keyword search), only "Bob Smith" is a "Data Scientist" (job_title
# filter), "skills.keyword" narrows to exact-match skill strings (not
# substrings), and the combined-filter case has exactly one document
# satisfying both.
_DOCUMENTS = [
    {
        "full_name": "Alice Nguyen",
        "job_title": "Software Engineer",
        "industry": "Technology",
        "skills": ["python", "kubernetes"],
        "summary": "Backend engineer who loves deploying services on kubernetes.",
        "location_name": "Seattle",
    },
    {
        "full_name": "Bob Smith",
        "job_title": "Data Scientist",
        "industry": "Technology",
        "skills": ["python", "machine learning"],
        "summary": "Data scientist focused on predictive modeling.",
        "location_name": "Austin",
    },
    {
        "full_name": "Carol Diaz",
        "job_title": "Data Scientist",
        "industry": "Finance",
        "skills": ["sql", "python"],
        "summary": "Quantitative analyst turned data scientist.",
        "location_name": "New York",
    },
    {
        "full_name": "Dave Park",
        "job_title": "Product Manager",
        "industry": "Technology",
        "skills": ["roadmapping", "python"],
        "summary": "Product manager for developer tools.",
        "location_name": "Denver",
    },
]


@pytest_asyncio.fixture(scope="session")
async def es_client() -> AsyncIterator[AsyncElasticsearch]:
    """Session-scoped client pointed at a real, disposable test index."""
    settings = Settings()
    client = AsyncElasticsearch(settings.ES_HOST)

    await client.indices.create(
        index=TEST_INDEX_NAME,
        mappings=PROFILE_INDEX_MAPPING,
        settings=PROFILE_INDEX_SETTINGS,
    )
    for document in _DOCUMENTS:
        await client.index(index=TEST_INDEX_NAME, document=document)
    await client.indices.refresh(index=TEST_INDEX_NAME)

    try:
        yield client
    finally:
        await client.indices.delete(index=TEST_INDEX_NAME, ignore_unavailable=True)
        await client.close()


@pytest_asyncio.fixture
async def client(es_client: AsyncElasticsearch) -> AsyncIterator[AsyncClient]:
    """`httpx.AsyncClient` wired to the FastAPI app with ES dependencies overridden.

    Overrides `get_es_client`/`get_settings` directly rather than exercising
    the app's `lifespan` startup, since the test index (and its name) must
    exist before any request is made -- the app's own lifespan would instead
    open a fresh client against the default `ES_INDEX_NAME`.
    """
    test_settings = Settings(ES_INDEX_NAME=TEST_INDEX_NAME)
    app.dependency_overrides[get_es_client] = lambda: es_client
    app.dependency_overrides[get_settings] = lambda: test_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client

    app.dependency_overrides.clear()
