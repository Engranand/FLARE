"""NASA BASS-II (PSI-25) Scientific Data Ingestion Pipeline.

Ingests the 129 experimental records from NASA BASS-II into PostgreSQL with:
- Full provenance preservation (exact raw strings, lexical classifications, headers, line locators).
- Cross-source reconciliation against BASS-II Test Matrix XLSX and BASS-II FAQ DOCX.
- Verification of 170/170 B1–B10 fields and 0 duplicate test identifiers.
- Cryptographic aggregate sealing of parse_run with raw archive bytes and experimental conditions.
- Idempotent execution (duplicate runs detect completed seals and do not duplicate or delete records).
- Replayable SERIALIZABLE transactions with automatic rollback on error.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import Connection, Engine, text

from app.db.aggregate import run_aggregate_transaction
from app.ingestion.classification import classify
from app.ingestion.csv_parser import ParsedTable, parse_csv
from app.ingestion.reconciliation import (
    CSV_HEADERS,
    SOURCE_FILES,
    load_workbook_evidence,
    reconcile_bass_ii,
    verify_source_integrity,
)
from app.ingestion.reporting import build_outputs

ROOT_DIR = Path(__file__).resolve().parents[3]
ACTOR_REF = "FLARE M6 Ingestion Pipeline"
INVESTIGATION_CODE = "PSI-25"
DATASET_ID = "BASS-II"

# Stable namespace for deterministic UUIDs
NAMESPACE_BASS_II = UUID("a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d")

STATED_UNITS: dict[str, str] = {
    "Calibrated  initial O2 % by vol ": "% by vol",
    "Calibrated final O2 % by vol": "% by vol",
    "Initial CO2 % by vol": "% by vol",
    "Final CO2 % by vol": "% by vol",
    "Initial CO (ppm)": "ppm",
    "Final CO (ppm)": "ppm",
}

WARNINGS = (
    "Classification is lexical, not scientific validation; numeric identifiers are not measurements.",
    "ReadMe DOCX and Test Matrices XLSX cross-reconciliation verified for 129 tests and 6 PI worksheets.",
    "Fan display, Air display, GMT, calibration, sample suffixes and instrument settings remain uninterpreted.",
    "OR/over, negative readings, unusual oxygen readings and dates are preserved without correction.",
    "No units, timestamps, flow velocities or scientific conclusions are inferred.",
    "Source hash establishes local byte identity, not independent NASA authentication or source version.",
)


def _uuid(entity: str, key: str) -> UUID:
    return uuid5(NAMESPACE_BASS_II, f"flare:{entity}:{key}")


def ingest_bass_ii(
    engine: Engine,
    root: Path = ROOT_DIR,
    actor: str = ACTOR_REF,
    seal_conditions: bool = True,
) -> dict[str, Any]:
    """Execute the complete NASA BASS-II ingestion pipeline.
    
    Preflight:
    1. Verifies hashes and zip structure of CSV, XLSX, and DOCX files.
    2. Parses the CSV and cross-reconciles against workbook evidence.
    
    Database (SERIALIZABLE transactions):
    Phase 1: Checks idempotency. If already sealed, returns immediately.
             Otherwise, persists investigation, documents, acquisitions, evidence references,
             parse_run, fields, records, observations, tests, condition segments, conditions, components.
    Phase 2: Cryptographically seals parse_run using raw archive bytes.
    Phase 3: Cryptographically seals experimental conditions.
    """
    # 1. Mandatory Preflight: verify all 3 source files
    t_start = time.perf_counter()
    source_results = verify_source_integrity(root)

    # 2. Parse CSV strictly
    csv_spec = SOURCE_FILES["csv"]
    csv_path = root / csv_spec["relative_path"]
    table = parse_csv(
        csv_path,
        root=root,
        dataset_id=DATASET_ID,
        expected_sha256=csv_spec["sha256"],
        expected_headers=CSV_HEADERS,
        expected_records=129,
    )

    # 3. Cross-source reconciliation
    reconciliation_report = reconcile_bass_ii(table, root=root)
    workbook_evidence = load_workbook_evidence(root)

    # 4. Build deterministic JSONL archive records
    records, parser_quality_report = build_outputs(table, WARNINGS)
    archive_payload = "".join(
        json.dumps(r, ensure_ascii=False, allow_nan=False) + "\n" for r in records
    )
    archive_bytes = archive_payload.encode("utf-8")
    archive_sha256 = hashlib.sha256(archive_bytes).hexdigest()

    # Parser code sha256
    csv_parser_py = root / "backend/app/ingestion/csv_parser.py"
    code_sha256 = hashlib.sha256(csv_parser_py.read_bytes()).hexdigest()

    # Parse configuration
    parse_configuration = {
        "dataset_id": DATASET_ID,
        "delimiter": ",",
        "encoding": "utf-8-sig",
        "expected_headers": list(CSV_HEADERS),
        "expected_records": 129,
        "test_id_header": "Test #",
    }
    config_json = json.dumps(parse_configuration, sort_keys=True)
    config_sha256 = hashlib.sha256(config_json.encode("utf-8")).hexdigest()

    inv_id = _uuid("investigation", INVESTIGATION_CODE)
    run_id = _uuid("parse_run", csv_spec["sha256"])

    # --- Phase 1: Insert Domain Records ---
    def _phase1_insert(conn: Connection) -> dict[str, Any]:
        now = datetime.now(timezone.utc)

        # Idempotency check: see if PSI-25 parse_run with this hash is already sealed
        existing = conn.execute(
            text("""
            SELECT pr.id, pr.record_count, pr.output_sha256, s.id AS seal_id, s.member_digest
            FROM public.parse_run pr
            JOIN public.investigation i ON i.id = pr.investigation_id
            JOIN public.aggregate_seal s ON (s.investigation_id = pr.investigation_id AND s.parse_run_id = pr.id)
            WHERE i.investigation_code = :code AND pr.status = 'complete' AND pr.output_sha256 = :out_sha
            """),
            {"code": INVESTIGATION_CODE, "out_sha": archive_sha256},
        ).mappings().first()

        if existing is not None:
            counts = conn.execute(
                text("""
                SELECT
                    (SELECT count(*) FROM public.source_document WHERE investigation_id = :inv) AS doc_count,
                    (SELECT count(*) FROM public.source_record WHERE investigation_id = :inv) AS record_count,
                    (SELECT count(*) FROM public.observation WHERE investigation_id = :inv) AS obs_count,
                    (SELECT count(*) FROM public.experimental_test WHERE investigation_id = :inv) AS test_count,
                    (SELECT count(*) FROM public.experimental_condition WHERE investigation_id = :inv) AS cond_count,
                    (SELECT count(*) FROM public.aggregate_seal WHERE investigation_id = :inv) AS seal_count
                """),
                {"inv": inv_id},
            ).mappings().one()

            return {
                "already_sealed": True,
                "status": "already_ingested",
                "investigation_id": str(inv_id),
                "investigation_code": INVESTIGATION_CODE,
                "parse_run_id": str(existing["id"]),
                "parse_run_seal_id": str(existing["seal_id"]),
                "parse_run_digest": existing["member_digest"],
                "records_persisted": counts["record_count"],
                "observations_persisted": counts["obs_count"],
                "tests_persisted": counts["test_count"],
                "conditions_persisted": counts["cond_count"],
                "seals_persisted": counts["seal_count"],
                "reconciliation": reconciliation_report,
                "source_verification": source_results,
            }

        # --- A. Insert Investigation ---
        conn.execute(
            text("""
            INSERT INTO public.investigation (
                id, repository_code, investigation_code, name, agency, doi,
                description, source_repository_url, metadata, created_at
            ) VALUES (
                :id, 'PSI', :code, :name, 'NASA', '10.60555/4qc4-de67',
                :description, 'https://psi.nasa.gov/physci/repo/data/investigations/PSI-25',
                :metadata, :now
            ) ON CONFLICT (repository_code, investigation_code) DO NOTHING
            """),
            {
                "id": inv_id,
                "code": INVESTIGATION_CODE,
                "name": "Burning and Suppression of Solids-II (BASS-II)",
                "description": "NASA Physical Sciences Informatics Investigation PSI-25: Burning and Suppression of Solids-II (BASS-II)",
                "metadata": json.dumps({
                    "doi": "10.60555/4qc4-de67",
                    "dataset_id": DATASET_ID,
                    "milestone": "M6",
                }),
                "now": now,
            },
        )

        # --- B. Insert SourceDocuments and SourceAcquisitions ---
        doc_ids: dict[str, UUID] = {}
        for key, spec in SOURCE_FILES.items():
            did = _uuid("source_document", spec["sha256"])
            doc_ids[key] = did
            conn.execute(
                text("""
                INSERT INTO public.source_document (
                    investigation_id, id, original_filename, source_type,
                    artifact_origin, sha256, file_size_bytes, storage_key,
                    source_version, metadata, created_at
                ) VALUES (
                    :inv, :id, :filename, :stype,
                    'external_original', :sha256, :size, :storage_key,
                    :ver, :metadata, :now
                ) ON CONFLICT (investigation_id, sha256) DO NOTHING
                """),
                {
                    "inv": inv_id,
                    "id": did,
                    "filename": spec["filename"],
                    "stype": spec["format"],
                    "sha256": spec["sha256"],
                    "size": spec["size_bytes"],
                    "storage_key": spec["relative_path"],
                    "ver": "4" if key == "csv" else None,
                    "metadata": json.dumps({"source_role": key, "verified": True}),
                    "now": now,
                },
            )

            acq_id = _uuid("source_acquisition", spec["sha256"])
            conn.execute(
                text("""
                INSERT INTO public.source_acquisition (
                    investigation_id, id, source_document_id, actual_filename,
                    portal_filename_alias, source_page_url, original_download_url,
                    local_relative_path, retrieved_at, verified_at,
                    verification_status, verification_scope, method,
                    actor_ref, metadata, created_at
                ) VALUES (
                    :inv, :id, :doc_id, :filename,
                    NULL, 'https://psi.nasa.gov/physci/repo/data/investigations/PSI-25', NULL,
                    :relpath, NULL, :now,
                    'verified', 'local_file_hash', 'sha256_verification',
                    :actor, :metadata, :now
                ) ON CONFLICT (investigation_id, id) DO NOTHING
                """),
                {
                    "inv": inv_id,
                    "id": acq_id,
                    "doc_id": did,
                    "filename": spec["filename"],
                    "relpath": spec["relative_path"],
                    "now": now,
                    "actor": actor,
                    "metadata": json.dumps({"sha256": spec["sha256"], "size_bytes": spec["size_bytes"]}),
                },
            )

        # --- C. Insert Evidence References ---
        csv_doc_id = doc_ids["csv"]
        xlsx_doc_id = doc_ids["xlsx"]
        docx_doc_id = doc_ids["docx"]

        # CSV Header Evidence References (1 per header)
        header_evidence_ids: dict[str, UUID] = {}
        for ordinal, header in enumerate(table.headers, start=1):
            hev_id = _uuid("evidence_reference", f"csv_header:{ordinal}")
            header_evidence_ids[header] = hev_id
            conn.execute(
                text("""
                INSERT INTO public.evidence_reference (
                    investigation_id, id, source_document_id, locator_kind,
                    locator_key, locator_version, locator, excerpt,
                    location_basis, extraction_method, extractor_version,
                    verification_status, verification_scope, created_at
                ) VALUES (
                    :inv, :id, :doc_id, 'csv',
                    :lkey, '1', :locator, :excerpt,
                    'csv_header_row', 'standard_csv_reader', '1.0.0',
                    'verified', 'field_definition', :now
                ) ON CONFLICT (investigation_id, source_document_id, locator_version, locator_key) DO NOTHING
                """),
                {
                    "inv": inv_id,
                    "id": hev_id,
                    "doc_id": csv_doc_id,
                    "lkey": f"header:{ordinal}",
                    "locator": json.dumps({"header": header, "column_index": ordinal, "line": 1}),
                    "excerpt": header,
                    "now": now,
                },
            )

        # CSV Row Evidence References (1 per row)
        row_evidence_ids: dict[int, UUID] = {}
        id_col_idx = table.headers.index(table.test_id_header)
        for row in table.rows:
            rev_id = _uuid("evidence_reference", f"csv_row:{row.csv_record_number}")
            row_evidence_ids[row.csv_record_number] = rev_id
            test_id = row.values[id_col_idx]
            conn.execute(
                text("""
                INSERT INTO public.evidence_reference (
                    investigation_id, id, source_document_id, locator_kind,
                    locator_key, locator_version, locator, excerpt,
                    location_basis, extraction_method, extractor_version,
                    verification_status, verification_scope, created_at
                ) VALUES (
                    :inv, :id, :doc_id, 'csv',
                    :lkey, '1', :locator, :excerpt,
                    'csv_data_row', 'standard_csv_reader', '1.0.0',
                    'verified', 'source_record', :now
                ) ON CONFLICT (investigation_id, source_document_id, locator_version, locator_key) DO NOTHING
                """),
                {
                    "inv": inv_id,
                    "id": rev_id,
                    "doc_id": csv_doc_id,
                    "lkey": f"row:{row.csv_record_number}",
                    "locator": json.dumps({
                        "data_row_index": row.data_row_index,
                        "csv_record_number": row.csv_record_number,
                        "test_id": test_id,
                    }),
                    "excerpt": f"Test {test_id} (line {row.csv_record_number})",
                    "now": now,
                },
            )

        # Workbook Evidence References for each test
        for mapping in workbook_evidence["record_mappings"]:
            wkev_id = _uuid("evidence_reference", f"xlsx_test:{mapping['test_id']}")
            conn.execute(
                text("""
                INSERT INTO public.evidence_reference (
                    investigation_id, id, source_document_id, locator_kind,
                    locator_key, locator_version, locator, excerpt,
                    location_basis, extraction_method, extractor_version,
                    verification_status, verification_scope, created_at
                ) VALUES (
                    :inv, :id, :doc_id, 'xlsx',
                    :lkey, '1', :locator, :excerpt,
                    'workbook_row_range', 'openxml_reader', '1.0.0',
                    'verified', 'cross_reconciliation', :now
                ) ON CONFLICT (investigation_id, source_document_id, locator_version, locator_key) DO NOTHING
                """),
                {
                    "inv": inv_id,
                    "id": wkev_id,
                    "doc_id": xlsx_doc_id,
                    "lkey": f"test:{mapping['test_id']}",
                    "locator": json.dumps({
                        "sheet": mapping["sheet"],
                        "xlsx_range": mapping["xlsx_range"],
                        "test_cell": mapping["test_cell"],
                        "sample_cell": mapping["sample_cell"],
                    }),
                    "excerpt": f"Worksheet {mapping['sheet']} {mapping['xlsx_range']}",
                    "now": now,
                },
            )

        # DOCX FAQ reference for test matrix description
        faq_ev_id = _uuid("evidence_reference", "docx_faq:test_matrix_explanation")
        conn.execute(
            text("""
            INSERT INTO public.evidence_reference (
                investigation_id, id, source_document_id, locator_kind,
                locator_key, locator_version, locator, excerpt,
                location_basis, extraction_method, extractor_version,
                verification_status, verification_scope, created_at
            ) VALUES (
                :inv, :id, :doc_id, 'docx',
                'section:test_matrix_explanation', '1', :locator, :excerpt,
                'docx_paragraph', 'openxml_reader', '1.0.0',
                'verified', 'metadata_documentation', :now
            ) ON CONFLICT (investigation_id, source_document_id, locator_version, locator_key) DO NOTHING
            """),
            {
                "inv": inv_id,
                "id": faq_ev_id,
                "doc_id": docx_doc_id,
                "locator": json.dumps({"paragraph_range": [3, 10], "topic": "Test Matrix explanation"}),
                "excerpt": "Tabs in spreadsheet for each PI.",
                "now": now,
            },
        )

        # --- D. Insert ParseRun ---
        conn.execute(
            text("""
            INSERT INTO public.parse_run (
                investigation_id, id, source_document_id, parser_name,
                parser_version, code_sha256, code_storage_key,
                configuration_sha256, configuration, output_sha256,
                output_storage_key, record_count, status, created_at
            ) VALUES (
                :inv, :id, :doc_id, 'app.ingestion.bass_ii',
                '1.0.0', :code_sha, 'backend/app/ingestion/csv_parser.py',
                :cfg_sha, :cfg, :out_sha,
                'data/processed/bass_ii/bass_ii_records.jsonl',
                :record_count, 'complete', :now
            ) ON CONFLICT (investigation_id, id) DO NOTHING
            """),
            {
                "inv": inv_id,
                "id": run_id,
                "doc_id": csv_doc_id,
                "code_sha": code_sha256,
                "cfg_sha": config_sha256,
                "cfg": config_json,
                "out_sha": archive_sha256,
                "record_count": len(table.rows),
                "now": now,
            },
        )

        # --- E. Insert SourceField (17 fields) ---
        field_ids: dict[str, UUID] = {}
        for ordinal, header in enumerate(table.headers, start=1):
            fid = _uuid("source_field", f"{run_id}:{ordinal}")
            field_ids[header] = fid
            raw_unit = STATED_UNITS.get(header)
            raw_unit_status = "stated" if raw_unit is not None else "not_stated"

            conn.execute(
                text("""
                INSERT INTO public.source_field (
                    investigation_id, id, parse_run_id, table_key,
                    ordinal, original_header, raw_unit, raw_unit_status,
                    header_evidence_id, created_at
                ) VALUES (
                    :inv, :id, :run, :table_key,
                    :ordinal, :header, :unit, :unit_status,
                    :hev, :now
                ) ON CONFLICT (investigation_id, parse_run_id, table_key, ordinal) DO NOTHING
                """),
                {
                    "inv": inv_id,
                    "id": fid,
                    "run": run_id,
                    "table_key": DATASET_ID,
                    "ordinal": ordinal,
                    "header": header,
                    "unit": raw_unit,
                    "unit_status": raw_unit_status,
                    "hev": header_evidence_ids[header],
                    "now": now,
                },
            )

        # --- F. Insert SourceRecord (129 rows) ---
        record_ids: dict[int, UUID] = {}
        for row in table.rows:
            rid = _uuid("source_record", f"{run_id}:{row.csv_record_number}")
            record_ids[row.csv_record_number] = rid
            source_row_id = f"{DATASET_ID}:{csv_spec['sha256']}:record:{row.csv_record_number}"

            conn.execute(
                text("""
                INSERT INTO public.source_record (
                    investigation_id, id, parse_run_id, table_key,
                    source_record_number, source_row_id, row_evidence_id,
                    created_at
                ) VALUES (
                    :inv, :id, :run, :table_key,
                    :rec_num, :row_id, :rev, :now
                ) ON CONFLICT (investigation_id, parse_run_id, table_key, source_record_number) DO NOTHING
                """),
                {
                    "inv": inv_id,
                    "id": rid,
                    "run": run_id,
                    "table_key": DATASET_ID,
                    "rec_num": row.csv_record_number,
                    "row_id": source_row_id,
                    "rev": row_evidence_ids[row.csv_record_number],
                    "now": now,
                },
            )

        # --- G. Insert Observation (2,193 observations: 129 rows x 17 fields) ---
        for row_idx, row in enumerate(table.rows):
            item = records[row_idx]
            for col_idx, (header, raw) in enumerate(zip(table.headers, row.values, strict=True), start=1):
                obs_id = _uuid("observation", f"{run_id}:{row.csv_record_number}:{col_idx}")
                cell = item["cells"][header]
                category = cell["classification"]
                cell_flags = cell["quality_flags"]

                source_value_kind = (
                    "numeric_lexeme" if category in ("numeric", "negative_numeric") else "text"
                )
                unit_origin = "field" if header in STATED_UNITS else "not_stated"

                conn.execute(
                    text("""
                    INSERT INTO public.observation (
                        investigation_id, id, parse_run_id, source_record_id,
                        source_field_id, evidence_id, raw_value, source_value_kind,
                        unit_origin, raw_unit, unit_evidence_id,
                        parser_classification, parser_flags, original_representation,
                        created_at
                    ) VALUES (
                        :inv, :id, :run, :rec,
                        :fld, :ev, :raw, :kind,
                        :uorig, NULL, NULL,
                        :cls, :flags, :repr, :now
                    ) ON CONFLICT (investigation_id, parse_run_id, source_record_id, source_field_id) DO NOTHING
                    """),
                    {
                        "inv": inv_id,
                        "id": obs_id,
                        "run": run_id,
                        "rec": record_ids[row.csv_record_number],
                        "fld": field_ids[header],
                        "ev": row_evidence_ids[row.csv_record_number],
                        "raw": raw,
                        "kind": source_value_kind,
                        "uorig": unit_origin,
                        "cls": category,
                        "flags": json.dumps({"quality_flags": cell_flags}),
                        "repr": json.dumps(cell),
                        "now": now,
                    },
                )

        # --- H. Insert ExperimentalTest and TestSourceRecord (129 tests) ---
        test_ids: dict[str, UUID] = {}
        for row in table.rows:
            t_id = row.values[id_col_idx]
            pi = row.values[table.headers.index("PI")]
            date_val = row.values[table.headers.index("Date")]
            sample_val = row.values[table.headers.index("Sample #")]

            exp_test_id = _uuid("experimental_test", f"NASA:PSI-25:{t_id}")
            test_ids[t_id] = exp_test_id

            conn.execute(
                text("""
                INSERT INTO public.experimental_test (
                    investigation_id, id, identity_namespace, test_identifier,
                    identity_evidence_id, metadata, created_at
                ) VALUES (
                    :inv, :id, 'NASA:PSI-25', :tid,
                    :ev, :meta, :now
                ) ON CONFLICT (investigation_id, identity_namespace, test_identifier) DO NOTHING
                """),
                {
                    "inv": inv_id,
                    "id": exp_test_id,
                    "tid": t_id,
                    "ev": row_evidence_ids[row.csv_record_number],
                    "meta": json.dumps({
                        "pi": pi,
                        "date": date_val,
                        "sample_number": sample_val,
                    }),
                    "now": now,
                },
            )

            tsr_id = _uuid("test_source_record", f"{exp_test_id}:{record_ids[row.csv_record_number]}")
            conn.execute(
                text("""
                INSERT INTO public.test_source_record (
                    investigation_id, id, experimental_test_id, source_record_id,
                    evidence_id, match_method, method_version, created_at
                ) VALUES (
                    :inv, :id, :tid, :rid,
                    :ev, 'exact_source_test_identifier', '1.0.0', :now
                ) ON CONFLICT (investigation_id, experimental_test_id, source_record_id) DO NOTHING
                """),
                {
                    "inv": inv_id,
                    "id": tsr_id,
                    "tid": exp_test_id,
                    "rid": record_ids[row.csv_record_number],
                    "ev": row_evidence_ids[row.csv_record_number],
                    "now": now,
                },
            )

        # --- I. Scientific Variables & Condition Roles ---
        variables_def = [
            ("fuel_sample_material", "Fuel Sample Material", "Solid fuel sample material description and dimensions", "context", "not_stated", None, "nominal"),
            ("flow_restrictor", "Flow Restrictor Setting", "Duct flow restrictor identifier or index", "instrument_setting", "not_stated", None, "nominal"),
            ("fan_display", "Fan Display Setting", "Fan motor controller display setting", "instrument_setting", "not_stated", None, "nominal"),
            ("air_display", "Air Display Setting", "Air flow controller display setting", "instrument_setting", "not_stated", None, "nominal"),
            ("calibrated_initial_o2", "Calibrated Initial Oxygen", "Initial calibrated oxygen volume percentage", "measurement", "stated", "% by vol", "electrochemical"),
            ("calibrated_final_o2", "Calibrated Final Oxygen", "Final calibrated oxygen volume percentage", "measurement", "stated", "% by vol", "electrochemical"),
        ]

        var_ids: dict[str, UUID] = {}
        for var_code, canon_name, desc, cat, ubasis, cunit, mtype in variables_def:
            vid = _uuid("scientific_variable", var_code)
            var_ids[var_code] = vid
            conn.execute(
                text("""
                INSERT INTO public.scientific_variable (
                    investigation_id, id, variable_code, definition_version,
                    canonical_name, description, physical_quantity,
                    canonical_unit, unit_basis, variable_category,
                    measurement_type, definition_status, evidence_id,
                    created_at
                ) VALUES (
                    :inv, :id, :vcode, 1,
                    :name, :desc, NULL,
                    :cunit, :ubasis, :cat,
                    :mtype, 'unresolved', :ev,
                    :now
                ) ON CONFLICT (investigation_id, variable_code, definition_version) DO NOTHING
                """),
                {
                    "inv": inv_id,
                    "id": vid,
                    "vcode": var_code,
                    "name": canon_name,
                    "desc": desc,
                    "cunit": cunit,
                    "ubasis": ubasis,
                    "cat": cat,
                    "mtype": mtype,
                    "ev": faq_ev_id,
                    "now": now,
                },
            )

        roles_def = [
            ("fuel_sample", "Solid fuel sample material and geometry", "condition"),
            ("duct_flow_setting", "Duct flow restrictor and airflow display settings", "condition"),
        ]
        role_ids: dict[str, UUID] = {}
        for rcode, rdef, rcat in roles_def:
            rid = _uuid("condition_role", rcode)
            role_ids[rcode] = rid
            conn.execute(
                text("""
                INSERT INTO public.condition_role (
                    investigation_id, id, role_code, definition,
                    variable_category, evidence_id, created_at
                ) VALUES (
                    :inv, :id, :rcode, :rdef,
                    :rcat, :ev, :now
                ) ON CONFLICT (investigation_id, role_code) DO NOTHING
                """),
                {
                    "inv": inv_id,
                    "id": rid,
                    "rcode": rcode,
                    "rdef": rdef,
                    "rcat": rcat,
                    "ev": faq_ev_id,
                    "now": now,
                },
            )

        # --- J. Condition Segments, Experimental Conditions, and Condition Components ---
        condition_ids: list[UUID] = []
        for row in table.rows:
            t_id = row.values[id_col_idx]
            exp_test_id = test_ids[t_id]
            rev_id = row_evidence_ids[row.csv_record_number]

            seg_id = _uuid("condition_segment", f"{exp_test_id}:nominal_run")
            conn.execute(
                text("""
                INSERT INTO public.condition_segment (
                    investigation_id, id, experimental_test_id, segment_key,
                    scope_status, description, evidence_id, created_at
                ) VALUES (
                    :inv, :id, :tid, 'nominal_run',
                    'documented', 'Reported nominal conditions from NASA BASS-II test matrix',
                    :ev, :now
                ) ON CONFLICT (investigation_id, experimental_test_id, segment_key) DO NOTHING
                """),
                {
                    "inv": inv_id,
                    "id": seg_id,
                    "tid": exp_test_id,
                    "ev": rev_id,
                    "now": now,
                },
            )

            cond_id = _uuid("experimental_condition", f"{exp_test_id}:nominal_run:1")
            condition_ids.append(cond_id)
            conn.execute(
                text("""
                INSERT INTO public.experimental_condition (
                    investigation_id, id, segment_id, experimental_test_id,
                    segment_key, revision, supersedes_id, scope_description,
                    airflow_stability, evidence_id, extension_metadata,
                    created_at
                ) VALUES (
                    :inv, :id, :seg, :tid,
                    'nominal_run', 1, NULL, 'Nominal test condition from table',
                    'unknown', :ev, '{}'::jsonb, :now
                ) ON CONFLICT (investigation_id, experimental_test_id, segment_key, revision) DO NOTHING
                """),
                {
                    "inv": inv_id,
                    "id": cond_id,
                    "seg": seg_id,
                    "tid": exp_test_id,
                    "ev": rev_id,
                    "now": now,
                },
            )

            # Component 1: Fuel Sample Material
            comp1_id = _uuid("condition_component", f"{cond_id}:1")
            conn.execute(
                text("""
                INSERT INTO public.condition_component (
                    investigation_id, id, condition_id, role_id,
                    slot, instrument_id, instrument_status,
                    variable_id, annotation_id, value_status,
                    evidence_id, created_at
                ) VALUES (
                    :inv, :id, :cid, :role_id,
                    1, NULL, 'not_applicable',
                    :var_id, NULL, 'unknown',
                    :ev, :now
                ) ON CONFLICT (investigation_id, condition_id, role_id, slot) DO NOTHING
                """),
                {
                    "inv": inv_id,
                    "id": comp1_id,
                    "cid": cond_id,
                    "role_id": role_ids["fuel_sample"],
                    "var_id": var_ids["fuel_sample_material"],
                    "ev": rev_id,
                    "now": now,
                },
            )

            # Component 2: Flow Restrictor Setting
            comp2_id = _uuid("condition_component", f"{cond_id}:2")
            conn.execute(
                text("""
                INSERT INTO public.condition_component (
                    investigation_id, id, condition_id, role_id,
                    slot, instrument_id, instrument_status,
                    variable_id, annotation_id, value_status,
                    evidence_id, created_at
                ) VALUES (
                    :inv, :id, :cid, :role_id,
                    2, NULL, 'not_applicable',
                    :var_id, NULL, 'unknown',
                    :ev, :now
                ) ON CONFLICT (investigation_id, condition_id, role_id, slot) DO NOTHING
                """),
                {
                    "inv": inv_id,
                    "id": comp2_id,
                    "cid": cond_id,
                    "role_id": role_ids["duct_flow_setting"],
                    "var_id": var_ids["flow_restrictor"],
                    "ev": rev_id,
                    "now": now,
                },
            )

        return {
            "already_sealed": False,
            "condition_ids": condition_ids,
        }

    # Execute Phase 1
    t_persistence_start = time.perf_counter()
    phase1_result = run_aggregate_transaction(engine, _phase1_insert, attempts=3)
    t_persistence_end = time.perf_counter()
    if phase1_result.get("already_sealed"):
        return phase1_result

    condition_ids = phase1_result["condition_ids"]

    # --- Phase 2: Seal ParseRun ---
    t_sealing_start = time.perf_counter()
    def _phase2_seal_parse_run(conn: Connection) -> dict[str, Any]:
        parse_seal_id = _uuid("aggregate_seal", f"parse_run:{run_id}")
        seal_row = conn.execute(
            text("""
            SELECT id, member_digest, member_counts
            FROM flare_sealing.seal('parse_run', :inv, :pid, :sid, :actor, :archive)
            """),
            {
                "inv": inv_id,
                "pid": run_id,
                "sid": parse_seal_id,
                "actor": actor,
                "archive": archive_bytes,
            },
        ).mappings().one()

        return {
            "parse_run_seal_id": str(seal_row["id"]),
            "parse_run_digest": seal_row["member_digest"],
            "parse_run_member_counts": seal_row["member_counts"],
        }

    phase2_result = run_aggregate_transaction(engine, _phase2_seal_parse_run, attempts=3)

    # --- Phase 3: Seal Conditions ---
    sealed_conditions_count = 0
    if seal_conditions:
        def _phase3_seal_conditions(conn: Connection) -> int:
            count = 0
            for cond_id in condition_ids:
                c_seal_id = _uuid("aggregate_seal", f"condition:{cond_id}")
                conn.execute(
                    text("""
                    SELECT flare_sealing.seal('experimental_condition', :inv, :pid, :sid, :actor)
                    """),
                    {
                        "inv": inv_id,
                        "pid": cond_id,
                        "sid": c_seal_id,
                        "actor": actor,
                    },
                )
                count += 1
            return count

        sealed_conditions_count = run_aggregate_transaction(engine, _phase3_seal_conditions, attempts=3)
    t_sealing_end = time.perf_counter()
    t_total_end = time.perf_counter()

    parsing_duration = t_persistence_start - t_start
    persistence_duration = t_persistence_end - t_persistence_start
    sealing_duration = t_sealing_end - t_sealing_start
    total_duration = t_total_end - t_start

    return {
        "status": "ingested",
        "investigation_id": str(inv_id),
        "investigation_code": INVESTIGATION_CODE,
        "parse_run_id": str(run_id),
        "parse_run_seal_id": phase2_result["parse_run_seal_id"],
        "parse_run_digest": phase2_result["parse_run_digest"],
        "parse_run_member_counts": phase2_result["parse_run_member_counts"],
        "records_persisted": len(table.rows),
        "observations_persisted": len(table.rows) * len(table.headers),
        "tests_persisted": len(table.rows),
        "conditions_persisted": len(condition_ids),
        "sealed_conditions_count": sealed_conditions_count,
        "reconciliation": reconciliation_report,
        "source_verification": source_results,
        "timing": {
            "parsing_seconds": round(parsing_duration, 4),
            "persistence_seconds": round(persistence_duration, 4),
            "sealing_seconds": round(sealing_duration, 4),
            "total_seconds": round(total_duration, 4),
        },
    }
