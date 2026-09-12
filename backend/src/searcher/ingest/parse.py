"""Row parsing and validation for the LinkedIn profile dataset.

The source file (`data/300_user_linkedin.txt`) is CSV in name only: nested
list/dict fields are Python-literal reprs rather than JSON, and unescaped
quotes in free-text fields (e.g. `summary`) shift columns for the rest of
that physical row. A field-count mismatch against the header catches most
of that, but not all of it -- some rows lose and gain fields in equal
measure partway through (one field's quoting absorbs a comma that should
have started a new column, another field further along splits in two),
landing on the *same* total column count while every field from the point
of the shift onward holds the wrong data. That kind of row sails through a
length check looking clean while `facebook_url` holds an industry name and
`job_title` holds a birth date.

So beyond the length check, every row is checked against a handful of
"anchor" fields whose shape is well known regardless of position --
platform URLs contain their own domain, `gender` is one of a small enum,
`job_title`/`industry`/`summary` are never a Python-literal repr or a bare
phone number, `summary` is never a bare int/float either, and `skills`
(a valid list-of-strings literal either way) is never a list of phone
numbers -- and a row that fails any of them is treated as shifted and
skipped in full, the same as a length mismatch, rather than trusting the
rest of its fields.
"""

from __future__ import annotations

import ast
import csv
import logging
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from searcher.ingest.logging_setup import LOG_PATH, configure_file_logging

logger = logging.getLogger(__name__)

# Matches a bare phone number (e.g. "+19104675531"): a shifted-column
# symptom seen where `phone_numbers` content lands in a scalar field like
# `industry`. Free-text industry/job-title values never look like this.
_PHONE_LIKE_RE = re.compile(r"^\+?[0-9][0-9\-\s().]{5,}$")

# Matches a bare int/float (e.g. "1646.0"): a shifted-column symptom seen
# where a numeric field (`linkedin_connections`, `inferred_years_experience`)
# lands in `summary`. A genuine free-text summary is never just a number.
_BARE_NUMBER_RE = re.compile(r"^-?\d+(\.\d+)?$")


def _looks_like_python_literal(value: str) -> bool:
    """True for a stray `"['a', 'b']"` / `"{...}"` repr landing in a scalar field."""
    return value.startswith("[") or value.startswith("{")


def _is_plausible_free_text(value: str) -> bool:
    """False if `value` looks like it belongs to a different (structured) column."""
    return not (_looks_like_python_literal(value) or _PHONE_LIKE_RE.match(value))


def _is_plausible_summary(value: str) -> bool:
    """False if `summary` looks like a shifted-in number or structured-field repr."""
    return not (_looks_like_python_literal(value) or _BARE_NUMBER_RE.match(value))


def _is_plausible_skills(value: str) -> bool:
    """False if the `skills` literal is really a shifted-in `phone_numbers` list.

    A row can shift by a fixed number of columns without changing its total
    field count (see module docstring), landing `phone_numbers` squarely in
    `skills` -- a valid list-of-strings literal, so `_parse_nested`'s type
    check accepts it. Real skills are never phone-number strings, so this
    catches what the type check alone misses.
    """
    try:
        parsed = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return True
    if not isinstance(parsed, list):
        return True
    return not any(
        isinstance(element, str) and _PHONE_LIKE_RE.match(element.strip()) for element in parsed
    )


# Column -> predicate(value) -> True if the value's shape is plausible for
# that column, checked against the *raw* (stripped) field regardless of
# whether it's blank (an absent value is always plausible). These are
# "anchor" fields: cheap to validate and, because column shifts are
# contiguous, a violation here is strong evidence the rest of the row --
# including fields the app actually displays and filters on -- is shifted
# too, so a failure here skips the whole row rather than just this field.
_ANCHOR_CHECKS: dict[str, Callable[[str], bool]] = {
    "linkedin_url": lambda v: not v or "linkedin.com" in v,
    "facebook_url": lambda v: not v or "facebook.com" in v,
    "twitter_url": lambda v: not v or "twitter.com" in v,
    "github_url": lambda v: not v or "github.com" in v,
    "gender": lambda v: not v or v in {"male", "female"},
    "job_title": lambda v: not v or _is_plausible_free_text(v),
    "industry": lambda v: not v or _is_plausible_free_text(v),
    "summary": lambda v: not v or _is_plausible_summary(v),
    "skills": lambda v: not v or _is_plausible_skills(v),
}


def _find_anchor_violation(header_index: dict[str, int], row: list[str]) -> tuple[str, str] | None:
    """Return `(field, value)` for the first anchor field whose value looks implausible."""
    for field, check in _ANCHOR_CHECKS.items():
        column_index = header_index.get(field)
        if column_index is None:
            continue
        value = row[column_index].strip()
        if not check(value):
            return field, value
    return None


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

    Three checks gate whether a row is trusted, in order: its field count
    must match the header (catches quote-shifts that add/remove columns),
    it must not be a byte-for-byte repeat of an earlier row (the source
    data contains a number of exact duplicate rows -- same `linkedin_id`,
    same everything -- which would otherwise double-index that profile),
    and none of its `_ANCHOR_CHECKS` fields may look implausible (catches
    quote-shifts that net out to the *same* column count, see module
    docstring). Anything that fails is skipped and logged (index + reason)
    to `backend/ingest.log` rather than indexed under the wrong field
    names.
    """
    configure_file_logging(logger)

    csv_path = Path(path)
    records: list[ProfileRecord] = []
    seen_rows: set[tuple[str, ...]] = set()
    skipped = 0

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        expected_field_count = len(header)
        header_index = {name: i for i, name in enumerate(header)}

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

            row_key = tuple(row)
            if row_key in seen_rows:
                skipped += 1
                logger.warning("Skipping row %d: exact duplicate of an earlier row", row_index)
                continue
            seen_rows.add(row_key)

            violation = _find_anchor_violation(header_index, row)
            if violation is not None:
                field, value = violation
                skipped += 1
                logger.warning(
                    "Skipping row %d: field %r looks shifted (value %r); "
                    "treating whole row as misaligned",
                    row_index,
                    field,
                    value,
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
