"""Reusable CSV reader. Raw values are decoded CSV fields, never normalized."""
from dataclasses import dataclass
import csv
import hashlib
import io
from pathlib import Path
import re


class SourceError(ValueError):
    """Invalid source identity, encoding, schema or CSV structure."""


@dataclass(frozen=True)
class SourceRow:
    data_row_index: int
    csv_record_number: int
    physical_line_start: int
    physical_line_end: int
    values: tuple[str, ...]


@dataclass(frozen=True)
class ParsedTable:
    dataset_id: str
    filename: str
    relative_path: str
    sha256: str
    headers: tuple[str, ...]
    rows: tuple[SourceRow, ...]
    test_id_header: str


def parse_csv(path: Path, *, root: Path, dataset_id: str, expected_sha256: str,
              test_id_header: str = "Test #", expected_headers: tuple[str, ...] | None = None,
              expected_records: int | None = None, encoding: str = "utf-8-sig",
              delimiter: str = ",") -> ParsedTable:
    """Fail closed on malformed rows; no partial table or outputs are produced."""
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise SourceError("Expected SHA-256 must contain 64 hexadecimal characters")
    try:
        relative = path.resolve().relative_to(root.resolve()).as_posix()
        blob = path.read_bytes()
    except (OSError, ValueError) as exc:
        raise SourceError(f"Source must be readable and inside the source root: {exc}") from exc
    digest = hashlib.sha256(blob).hexdigest()
    if digest != expected_sha256.lower():
        raise SourceError(f"Source hash mismatch: expected {expected_sha256}, got {digest}")
    try:
        text = blob.decode(encoding, errors="strict")
    except (UnicodeError, LookupError) as exc:
        raise SourceError(f"Source decoding failed: {exc}") from exc
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter,
                        quotechar='"', doublequote=True, skipinitialspace=False, strict=True)
    rows: list[SourceRow] = []
    try:
        headers = tuple(next(reader, []))
        if not headers or any(not h.strip() for h in headers):
            raise SourceError("Missing or blank header")
        if len(set(headers)) != len(headers):
            raise SourceError("Duplicate headers would overwrite cells")
        if test_id_header not in headers:
            raise SourceError(f"Missing identifier column: {test_id_header!r}")
        if expected_headers is not None and headers != expected_headers:
            raise SourceError("Original headers do not match the expected schema")
        previous_line = reader.line_num
        for index, values in enumerate(reader, start=1):
            if len(values) != len(headers):
                raise SourceError(f"Row width mismatch at CSV record {index + 1}, "
                                  f"physical lines {previous_line + 1}-{reader.line_num}: "
                                  f"expected {len(headers)}, got {len(values)}")
            rows.append(SourceRow(index, index + 1, previous_line + 1,
                                  reader.line_num, tuple(values)))
            previous_line = reader.line_num
    except csv.Error as exc:
        raise SourceError(f"Malformed CSV near physical line {reader.line_num}: {exc}") from exc
    if expected_records is not None and len(rows) != expected_records:
        raise SourceError(f"Expected {expected_records} data records, got {len(rows)}")
    return ParsedTable(dataset_id, path.name, relative, digest, headers, tuple(rows), test_id_header)
