from pathlib import Path

from searcher.ingest.parse import parse_profiles

_HEADER = "name,job_title,skills\n"


def _write_csv(tmp_path: Path, body: str) -> Path:
    csv_path = tmp_path / "profiles.csv"
    csv_path.write_text(_HEADER + body, encoding="utf-8")
    return csv_path


def _write_csv_with_header(tmp_path: Path, header: str, body: str) -> Path:
    csv_path = tmp_path / "profiles.csv"
    csv_path.write_text(header + body, encoding="utf-8")
    return csv_path


def test_parses_clean_row_including_nested_field(tmp_path: Path) -> None:
    csv_path = _write_csv(tmp_path, "alice,engineer,\"['python', 'go']\"\n")

    records = parse_profiles(csv_path)

    assert records == [{"name": "alice", "job_title": "engineer", "skills": ["python", "go"]}]


def test_empty_field_is_treated_as_absent_not_error(tmp_path: Path) -> None:
    csv_path = _write_csv(tmp_path, "bob,,[]\n")

    records = parse_profiles(csv_path)

    assert records == [{"name": "bob", "job_title": None, "skills": []}]


def test_row_with_wrong_field_count_is_skipped(tmp_path: Path) -> None:
    body = "alice,engineer,\"['python']\"\ncarol,manager,x,y\ndave,analyst,[]\n"
    csv_path = _write_csv(tmp_path, body)

    records = parse_profiles(csv_path)

    names = [record["name"] for record in records]
    assert names == ["alice", "dave"]


def test_unparseable_nested_field_is_absent_but_row_is_kept(tmp_path: Path) -> None:
    csv_path = _write_csv(tmp_path, "dave,analyst,not-a-literal\n")

    records = parse_profiles(csv_path)

    assert records == [{"name": "dave", "job_title": "analyst", "skills": None}]


def test_row_with_shifted_scalar_field_is_skipped_despite_matching_field_count(
    tmp_path: Path,
) -> None:
    """A quote-shift that nets out to the same column count still corrupts data --
    e.g. `job_title_levels` content ("['manager']") landing under `job_title`."""
    body = "alice,engineer,\"['python']\"\ncarol,['manager'],[]\ndave,analyst,[]\n"
    csv_path = _write_csv(tmp_path, body)

    records = parse_profiles(csv_path)

    names = [record["name"] for record in records]
    assert names == ["alice", "dave"]


def test_row_with_phone_like_scalar_field_is_skipped(tmp_path: Path) -> None:
    """A phone number landing in a plain-text column (e.g. `industry`) is a
    tell-tale sign of a shifted row, even when the field count still matches."""
    body = "alice,engineer,\"['python']\"\ncarol,+19104675531,[]\n"
    csv_path = _write_csv(tmp_path, body)

    records = parse_profiles(csv_path)

    names = [record["name"] for record in records]
    assert names == ["alice"]


def test_exact_duplicate_row_is_skipped(tmp_path: Path) -> None:
    body = "alice,engineer,\"['python']\"\nalice,engineer,\"['python']\"\n"
    csv_path = _write_csv(tmp_path, body)

    records = parse_profiles(csv_path)

    assert len(records) == 1


def test_row_with_bare_number_in_summary_is_skipped(tmp_path: Path) -> None:
    """A same-length shift can land a numeric field (e.g. connections count or
    years of experience) in `summary`; a genuine summary is never a bare number."""
    header = "name,job_title,skills,summary\n"
    body = "alice,engineer,\"['python']\",Loves building things\ncarol,manager,[],1646.0\n"
    csv_path = _write_csv_with_header(tmp_path, header, body)

    records = parse_profiles(csv_path)

    names = [record["name"] for record in records]
    assert names == ["alice"]


def test_row_with_phone_numbers_shifted_into_skills_is_skipped(tmp_path: Path) -> None:
    """`phone_numbers` shifted into `skills` still parses as a valid
    list-of-strings, so only a phone-shape check on the elements catches it."""
    body = (
        "alice,engineer,\"['python', 'go']\"\ncarol,manager,\"['+19104675531', '+12125551212']\"\n"
    )
    csv_path = _write_csv(tmp_path, body)

    records = parse_profiles(csv_path)

    names = [record["name"] for record in records]
    assert names == ["alice"]
