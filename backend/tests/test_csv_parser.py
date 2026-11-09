"""Synthetic strings below are parser fixtures, not scientific observations."""
import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from app.ingestion.classification import classify
from app.ingestion.csv_parser import SourceError, parse_csv
from app.ingestion.reporting import build_outputs, write_outputs


@pytest.mark.parametrize("raw,category", [
    ("12.5", "numeric"), ("0", "numeric"), ("-1", "negative_numeric"),
    ("", "empty"), ("none", "literal_none"), (">500", "censored_numeric"),
    ("OR", "ambiguous_token"), ("over", "ambiguous_token"),
    ("0.9   1.3   2.75", "compound_text"), ("250>50", "compound_text"),
    ("unfamiliar", "other_text"), ("  -1  ", "negative_numeric"),
    ("   ", "other_text"), ("2/19/2014", "other_text"),
    ("1 cm 0.2 mm PMMA film", "other_text"), ("NaN", "other_text"),
    ("12e-3", "numeric"), ("2 <1", "other_text"),
])
def test_classifications(raw, category):
    result, flags = classify(raw)
    assert result == category
    if category == "other_text":
        assert "unclassified_text_review" in flags


def fixture_file(tmp_path: Path, rows: list[list[str]]) -> tuple[Path, str]:
    buffer = io.StringIO(newline="")
    csv.writer(buffer).writerows(rows)
    path = tmp_path / "fixture.csv"
    path.write_bytes(buffer.getvalue().encode("utf-8-sig"))
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def parse_fixture(tmp_path, rows):
    path, digest = fixture_file(tmp_path, rows)
    return path, parse_csv(path, root=tmp_path, dataset_id="technical-fixture", expected_sha256=digest)


def test_preservation_provenance_duplicates_and_output(tmp_path):
    source_rows = [["Test #", " Header  "], ["A", "  -1  "], ["A", "  -1  "],
                   ["B", 'quoted "text", comma\r\nsecond line'], ["", "none"]]
    path, table = parse_fixture(tmp_path, source_rows)
    records, report = build_outputs(table)
    assert table.headers == tuple(source_rows[0])
    assert [list(row.values) for row in table.rows] == source_rows[1:]
    assert table.rows[2].csv_record_number == 4
    assert table.rows[2].physical_line_start == 4
    assert table.rows[2].physical_line_end == 5
    assert records[0]["cells"][" Header  "]["raw_value"] == "  -1  "
    assert records[0]["record_provenance"]["source_row_id"] != records[1]["record_provenance"]["source_row_id"]
    assert report["duplicate_test_ids"] == {"A": [1, 2]}
    assert report["duplicate_complete_rows"] == [[1, 2]]
    assert report["missing_test_id_rows"] == [4]
    assert report["total_cell_count"] == 8
    for category, count in report["overall_classification_counts"].items():
        assert count == sum(c[category] for c in report["classification_counts_per_column"].values())
    output = tmp_path / "output.jsonl"
    quality = tmp_path / "quality.json"
    write_outputs(table, records, report, path, output, quality)
    assert [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()] == records
    assert json.loads(quality.read_text()) == report
    first_bytes = output.read_bytes(), quality.read_bytes()
    write_outputs(table, *build_outputs(table), path, output, quality)
    assert first_bytes == (output.read_bytes(), quality.read_bytes())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == table.sha256


@pytest.mark.parametrize("rows,match", [
    ([["Test #", "Value"], ["A"]], "Row width"),
    ([["Test #", "Value"], ["A", "1", "extra"]], "Row width"),
    ([["Test #", "Value"], []], "Row width"),
    ([["Test #", "Test #"]], "Duplicate headers"),
    ([["Test #", " "]], "blank header"),
    ([], "Missing"), ([["Other"]], "identifier column"),
])
def test_malformed_structure(tmp_path, rows, match):
    with pytest.raises(SourceError, match=match):
        parse_fixture(tmp_path, rows)


def test_hash_schema_and_record_count(tmp_path):
    path, digest = fixture_file(tmp_path, [["Test #"], ["A"]])
    with pytest.raises(SourceError, match="hash mismatch"):
        parse_csv(path, root=tmp_path, dataset_id="fixture", expected_sha256="0" * 64)
    for kwargs in [{"expected_headers": ("different",)}, {"expected_records": 2}]:
        with pytest.raises(SourceError):
            parse_csv(path, root=tmp_path, dataset_id="fixture", expected_sha256=digest, **kwargs)


@pytest.mark.parametrize("blob", [b'Test #,Value\r\nA,"unfinished', b'Test #\n\xff'])
def test_bad_csv_or_encoding(tmp_path, blob):
    path = tmp_path / "bad.csv"
    path.write_bytes(blob)
    with pytest.raises(SourceError):
        parse_csv(path, root=tmp_path, dataset_id="fixture", expected_sha256=hashlib.sha256(blob).hexdigest())


def test_no_source_overwrite_and_changed_source(tmp_path):
    path, table = parse_fixture(tmp_path, [["Test #"], ["A"]])
    records, report = build_outputs(table)
    with pytest.raises(SourceError, match="overwrite"):
        write_outputs(table, records, report, path, path, tmp_path / "q.json")
    path.write_bytes(b"changed")
    with pytest.raises(SourceError, match="changed"):
        write_outputs(table, records, report, path, tmp_path / "r.jsonl", tmp_path / "q.json")
    assert not (tmp_path / "r.jsonl").exists()


def test_full_width_empty_row_preserved(tmp_path):
    _, table = parse_fixture(tmp_path, [["Test #", "Value"], ["", ""]])
    records, report = build_outputs(table)
    assert "all_empty_record" in records[0]["quality_flags"]
    assert report["overall_classification_counts"]["empty"] == 2
