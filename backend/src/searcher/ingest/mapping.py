"""Explicit Elasticsearch index mapping for `linkedin_profiles`.

The dataset mixes free-text fields meant for relevance-scored keyword search
(name, summary, skills, and job/school titles buried in the nested
`experience`/`education` structures) with categorical fields meant for exact
match filtering (`job_title`, `skills`). Dynamic mapping would guess wrong on
both counts -- e.g. it would give `job_title` a plain `text` type with no
`.keyword` sub-field, making exact-match filtering impossible without a
reindex -- so every field the search API touches is declared here up front
and imported by the ingestion script when it creates the index.

`experience` and `education` are indexed as `nested` rather than plain
`object`: each profile has a list of them, and without `nested` Elasticsearch
flattens the list's fields into parallel arrays, so a query for a single
title/company combination could match across different jobs in the same
profile.
"""

from __future__ import annotations

from typing import Any

# Keyword fields default to a length that comfortably covers this dataset's
# free-text values without wasting doc-value space on unbounded input.
_KEYWORD = {"type": "keyword", "ignore_above": 256}

_TEXT_WITH_KEYWORD = {
    "type": "text",
    "fields": {"keyword": _KEYWORD},
}

PROFILE_INDEX_MAPPING: dict[str, Any] = {
    # Every source column not declared below (e.g. `job_last_updated`,
    # `linkedin_connections`) still gets indexed via dynamic mapping, but
    # with date/numeric auto-detection off: the dataset's column-mismatch
    # rows can leave a stray value (e.g. "united states") in a field ES
    # would otherwise guess is a date from an earlier, well-formed row,
    # which then rejects every later document as a parse error.
    "date_detection": False,
    "numeric_detection": False,
    "properties": {
        # Free-text search fields (multi_match target), each with a
        # `.keyword` sub-field for exact-match filtering or sorting.
        "full_name": _TEXT_WITH_KEYWORD,
        "summary": _TEXT_WITH_KEYWORD,
        "skills": _TEXT_WITH_KEYWORD,
        # Filter fields: queried via `.keyword` in `filter` clauses, so
        # relevance scoring never applies to them.
        "job_title": _TEXT_WITH_KEYWORD,
        "industry": _KEYWORD,
        "job_title_role": _KEYWORD,
        "job_title_levels": _KEYWORD,
        "job_company_name": _TEXT_WITH_KEYWORD,
        "location_name": _KEYWORD,
        # Nested so each list entry's fields stay bound together for
        # per-entry matching instead of flattening into parallel arrays.
        "experience": {
            "type": "nested",
            "properties": {
                "title": {
                    "properties": {
                        "name": _TEXT_WITH_KEYWORD,
                        "role": _KEYWORD,
                        "sub_role": _KEYWORD,
                    }
                },
                "company": {
                    "properties": {
                        "name": _TEXT_WITH_KEYWORD,
                        "industry": _KEYWORD,
                    }
                },
                "summary": {"type": "text"},
                "start_date": _KEYWORD,
                "end_date": _KEYWORD,
            },
        },
        "education": {
            "type": "nested",
            "properties": {
                "school": {"properties": {"name": _TEXT_WITH_KEYWORD}},
                "degrees": _KEYWORD,
                "majors": _KEYWORD,
                "minors": _KEYWORD,
                "start_date": _KEYWORD,
                "end_date": _KEYWORD,
            },
        },
        # Structured records, not plain strings -- {"name": ..., "proficiency": ...}
        # and {"organization": ..., "name": ..., "start_date": ..., "end_date": ...}.
        "certifications": {
            "properties": {
                "organization": _KEYWORD,
                "name": _TEXT_WITH_KEYWORD,
                "start_date": _KEYWORD,
                "end_date": _KEYWORD,
            }
        },
        "languages": {
            "properties": {
                "name": _KEYWORD,
                "proficiency": _KEYWORD,
            }
        },
        "interests": _KEYWORD,
        # Not used by search or filtering, and shape-inconsistent across rows
        # (some rows hold structured dicts, others plain strings -- an
        # artifact of the source data's column-shift issue -- so ES's own
        # type inference would reject whichever shape it didn't see first).
        # `enabled: false` stores the raw value for retrieval without
        # attempting to parse or index it.
        "emails": {"type": "object", "enabled": False},
        "phone_numbers": {"type": "object", "enabled": False},
        "profiles": {"type": "object", "enabled": False},
    },
}

# Single-node dev setup: no replicas needed, one shard is plenty for ~336 docs.
PROFILE_INDEX_SETTINGS: dict[str, Any] = {
    "number_of_shards": 1,
    "number_of_replicas": 0,
}
