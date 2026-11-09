"""Run from backend: python -m app.ingestion.bass_ii"""
import argparse
import json
from pathlib import Path
import sys

from app.ingestion.csv_parser import SourceError, parse_csv
from app.ingestion.reporting import build_outputs, write_outputs

ROOT = Path(__file__).resolve().parents[3]
SHA256 = "71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042"
FILENAME = "PSI-25_Experimental table_BASS-II.csv"
HEADERS = (
    "PI", "Test #", "Date", "GMT", "Sample #", "Fuel Sample Material", "Flow restrictor",
    "Fan display", "Air display", "Radiometer gain   (1000   250   50   10)",
    "Total Frames Shot", "Calibrated  initial O2 % by vol ", "Calibrated final O2 % by vol",
    "Initial CO2 % by vol", "Final CO2 % by vol", "Initial CO (ppm)", "Final CO (ppm)",
)
WARNINGS = (
    "Classification is lexical, not scientific validation; numeric identifiers are not measurements.",
    "ReadMe DOCX and Test Matrices XLSX are pending acquisition and verification.",
    "Fan display, Air display, GMT, calibration, sample suffixes and instrument settings remain uninterpreted.",
    "OR/over, negative readings, unusual oxygen readings and dates are preserved without correction.",
    "No units, timestamps, flow velocities or scientific conclusions are inferred.",
    "Source hash establishes local byte identity, not independent NASA authentication or source version.",
)


def run(root: Path = ROOT) -> dict:
    source = root / "data/raw/bass_ii/original" / FILENAME
    table = parse_csv(source, root=root, dataset_id="BASS-II", expected_sha256=SHA256,
                      expected_headers=HEADERS, expected_records=129)
    records, report = build_outputs(table, WARNINGS)
    output = root / "data/processed/bass_ii"
    write_outputs(table, records, report, source, output / "bass_ii_records.jsonl",
                  output / "bass_ii_quality_report.json")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root containing canonical CSV")
    args = parser.parse_args()
    try:
        report = run(args.root)
    except (SourceError, OSError) as exc:
        print(json.dumps({"status": "failed", "parsing_errors": [str(exc)]}), file=sys.stderr)
        return 1
    print(json.dumps({"status": "parsed", "records": report["data_record_count"],
                      "classifications": report["overall_classification_counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
