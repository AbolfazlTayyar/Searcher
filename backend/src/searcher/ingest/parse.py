"""Row parsing and validation for the LinkedIn profile dataset.

The source file (`data/300_user_linkedin.txt`) is CSV in name only: nested
list/dict fields are Python-literal reprs rather than JSON, and roughly 16%
of rows carry unescaped quotes in free-text fields (e.g. `summary`) that
shift every column for the rest of that physical row. Trusting column
position blindly would silently index garbage under the wrong field names,
so every row's field count is validated against the header before it is
used, and anything that doesn't match is skipped and logged rather than
guessed at.
"""

from __future__ import annotations

import ast
import csv
import logging
from pathlib import Path
from typing import Any

from searcher.ingest.logging_setup import LOG_PATH, configure_file_logging

logger = logging.getLogger(__name__)

# Columns whose raw value is a Python-literal repr of a list/dict, not JSON.
NESTED_FIELDS = frozenset(
    {
        "skills",
        "experience",
        "education",
        "emails",
        "phone_numbers",
        "interests",
        "certifications",
        "languages",
        "profiles",
    }
)

# Expected Python type for each nested field once parsed, checked against
# the literal `ast.literal_eval` actually produced. A handful of rows have
# unescaped quotes that shift fields without changing the row's overall
# column count (so the header-vs-row length check in `parse_profiles`
# doesn't catch them) -- e.g. an address `dict` lands in `skills`, which
# Elasticsearch's mapping expects as a list of strings. Fields not listed
# here (`emails`, `phone_numbers`, `profiles`) aren't indexed/searched, so
# their shape is never validated.
_EXPECTED_NESTED_TYPE: dict[str, type] = {
    "skills": list,
    "interests": list,
    "certifications": list,
    "languages": list,
    "experience": list,
    "education": list,
}

# A single cleaned profile record: column name -> scalar value, parsed
# nested structure, or None if the field was absent/blank in the source row.
ProfileRecord = dict[str, Any]

# Element type expected inside each `list`-typed nested field above.
# `certifications`/`languages` are lists of structured records (e.g.
# {"name": "english", "proficiency": None}), not plain strings.
_EXPECTED_LIST_ELEMENT_TYPE: dict[str, type] = {
    "skills": str,
    "interests": str,
    "certifications": dict,
    "languages": dict,
    "experience": dict,
    "education": dict,
}


def _clean_scalar(raw_value: str) -> str | None:
    """Strip whitespace and treat a blank string as an absent field, not an error."""
    value = raw_value.strip()
    return value or None


def _parse_nested(field_name: str, raw_value: str, row_index: int) -> Any:
    """Parse a Python-literal-repr field (e.g. "['a', 'b']") via `ast.literal_eval`.

    Falls back to None on a blank value, a literal that fails to parse, or a
    literal whose type doesn't match what this field should hold (a sign
    that upstream quote-shifting landed a different column's data here) --
    in every case the row itself is still usable, just without that one
    field, rather than indexing it under the wrong shape.
    """
    stripped = raw_value.strip()
    if not stripped:
        return None
    try:
        value = ast.literal_eval(stripped)
    except (ValueError, SyntaxError) as exc:
        logger.warning(
            "Row %d: could not parse nested field %r (%s); treating as absent",
            row_index,
            field_name,
            exc,
        )
        return None

    expected_type = _EXPECTED_NESTED_TYPE.get(field_name)
    if expected_type is not None and not isinstance(value, expected_type):
        logger.warning(
            "Row %d: nested field %r parsed as %s, expected %s; treating as absent",
            row_index,
            field_name,
            type(value).__name__,
            expected_type.__name__,
        )
        return None

    expected_element_type = _EXPECTED_LIST_ELEMENT_TYPE.get(field_name)
    if expected_element_type is not None and isinstance(value, list):
        if not all(isinstance(element, expected_element_type) for element in value):
            logger.warning(
                "Row %d: nested field %r has elements of the wrong type; treating as absent",
                row_index,
                field_name,
            )
            return None

    return value


def _build_record(header: list[str], row: list[str], row_index: int) -> ProfileRecord:
    record: ProfileRecord = {}
    for column_name, raw_value in zip(header, row, strict=True):
        if column_name in NESTED_FIELDS:
            record[column_name] = _parse_nested(column_name, raw_value, row_index)
        else:
            record[column_name] = _clean_scalar(raw_value)
    return record


def parse_profiles(path: str | Path) -> list[ProfileRecord]:
    """Parse the LinkedIn dataset CSV into clean, structured profile records.

    Each row's field count is checked against the header before any column
    is trusted; a mismatch means unescaped quotes upstream have shifted that
    row's columns, so the row is skipped and logged (index + reason) to
    `backend/ingest.log` rather than indexed under the wrong field names.
    """
    configure_file_logging(logger)

    csv_path = Path(path)
    records: list[ProfileRecord] = []
    skipped = 0

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        expected_field_count = len(header)

        for row_index, row in enumerate(reader, start=2):
            if len(row) != expected_field_count:
                skipped += 1
                logger.warning(
                    "Skipping row %d: expected %d fields, got %d",
                    row_index,
                    expected_field_count,
                    len(row),
                )
                continue
            records.append(_build_record(header, row, row_index))

    logger.info(
        "Parsed %d clean record(s), skipped %d malformed row(s) from %s",
        len(records),
        skipped,
        csv_path,
    )
    return records


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dataset_path = Path(__file__).resolve().parents[4] / "data" / "300_user_linkedin.txt"
    profiles = parse_profiles(dataset_path)
    print(f"Parsed {len(profiles)} clean profile record(s). See {LOG_PATH} for skipped rows.")
