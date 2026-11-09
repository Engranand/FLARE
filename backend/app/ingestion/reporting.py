"""Build deterministic JSON records and quality summaries from a parsed table."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from app.ingestion.classification import CATEGORIES, classify
from app.ingestion.csv_parser import ParsedTable, SourceError

PARSER_VERSION = "1.0.0"


def build_outputs(table: ParsedTable, warnings: tuple[str, ...] = ()) -> tuple[list[dict], dict]:
    source = {"filename": table.filename, "sha256": table.sha256,
              "relative_path": table.relative_path}
    records: list[dict] = []
    counts = {h: Counter({c: 0 for c in CATEGORIES}) for h in table.headers}
    identifiers: dict[str, list[int]] = defaultdict(list)
    complete_rows: dict[tuple[str, ...], list[int]] = defaultdict(list)
    id_column = table.headers.index(table.test_id_header)
    for row in table.rows:
        identifiers[row.values[id_column]].append(row.data_row_index)
        complete_rows[row.values].append(row.data_row_index)
    duplicate_ids = {k: v for k, v in identifiers.items() if k.strip() and len(v) > 1}
    duplicate_rows = [v for v in complete_rows.values() if len(v) > 1]
    for row in table.rows:
        cells = {}
        flags: set[str] = set()
        for column, (header, raw) in enumerate(zip(table.headers, row.values, strict=True), start=1):
            category, cell_flags = classify(raw)
            cells[header] = {"original_header": header, "column_index": column,
                             "raw_value": raw, "classification": category, "quality_flags": cell_flags}
            counts[header][category] += 1
            flags.update(cell_flags)
        test_id = row.values[id_column]
        if not test_id.strip():
            flags.add("missing_test_identifier")
        if test_id in duplicate_ids:
            flags.add("duplicate_test_identifier")
        if len(complete_rows[row.values]) > 1:
            flags.add("duplicate_complete_row")
        if all(v == "" for v in row.values):
            flags.add("all_empty_record")
        records.append({"dataset_id": table.dataset_id, "parser_version": PARSER_VERSION,
                        "source": source, "record_provenance": {
                            "source_row_id": f"{table.dataset_id}:{table.sha256}:record:{row.csv_record_number}",
                            "data_row_index": row.data_row_index,
                            "csv_record_number": row.csv_record_number,
                            "physical_line_start": row.physical_line_start,
                            "physical_line_end": row.physical_line_end,
                            "original_test_id": test_id, "original_headers": list(table.headers)},
                        "cells": cells, "quality_flags": sorted(flags)})
    overall = {c: sum(column[c] for column in counts.values()) for c in CATEGORIES}
    report = {"dataset_id": table.dataset_id, "parser_version": PARSER_VERSION, "source": source,
              "header_count": len(table.headers), "data_record_count": len(table.rows),
              "original_headers": list(table.headers),
              "classification_counts_per_column": {h: dict(c) for h, c in counts.items()},
              "overall_classification_counts": overall,
              "total_cell_count": sum(overall.values()),
              "duplicate_test_ids": duplicate_ids, "duplicate_complete_rows": duplicate_rows,
              "missing_test_id_rows": [r.data_row_index for r in table.rows if not r.values[id_column].strip()],
              "row_width_validation": {"expected": len(table.headers), "checked": len(table.rows),
                                       "valid": True, "errors": []},
              "parsing_errors": [], "unresolved_scientific_interpretation_warnings": list(warnings)}
    return records, report


def write_outputs(table: ParsedTable, records: list[dict], report: dict,
                  source_path: Path, records_path: Path, report_path: Path) -> None:
    """Validate before writing; filenames are supplied by the dataset command."""
    targets = [records_path.resolve(), report_path.resolve()]
    if len(set(targets + [source_path.resolve()])) != 3:
        raise SourceError("Output paths must be distinct and cannot overwrite the source")
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != table.sha256:
        raise SourceError("Source changed since parsing; outputs not written")
    payloads = ["".join(json.dumps(r, ensure_ascii=False, allow_nan=False) + "\n" for r in records),
                json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"]
    for target, payload in zip(targets, payloads, strict=True):
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
