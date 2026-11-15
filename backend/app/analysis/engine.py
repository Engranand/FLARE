"""Deterministic Scientific Analysis Engine Coordinator for FLARE Milestone 9.

Governed by FLARE-CONTRACT-FINAL-M9-V2.
Coordinates pure-Python execution of modules P1, P2, P3, P4, persists outputs to
PostgreSQL under migrations 0003/0008, and commits cryptographic SHA-256 seals.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import Connection, Engine, text

from app.analysis.p1_env_stats import execute_p1_analysis
from app.analysis.p2_oxygen import execute_p2_analysis
from app.analysis.p3_airflow import execute_p3_analysis
from app.analysis.p4_morphology import execute_p4_analysis
from app.analysis.protocols import NAMESPACE_M9, seed_m9_protocols
from app.analysis.types import EngineRunResult, MetricPayload, ModuleExecutionReport
from app.db.aggregate import run_aggregate_transaction

AUTHENTIC_SHA256 = "71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042"
INVESTIGATION_CODE = "PSI-25"
ACTOR_REF = "FLARE M9 Deterministic Analysis Engine"
ROOT_DIR = Path(__file__).resolve().parents[3]


def metric_uuid(protocol_id: UUID, metric_code: str) -> UUID:
    """Deterministic UUID for an analytical result."""
    return uuid5(NAMESPACE_M9, f"analytical_result:{protocol_id}:{metric_code}")


def load_authenticated_records(root: Path = ROOT_DIR) -> list[dict[str, Any]]:
    """Load the 129 BASS-II records from the verified CSV file."""
    csv_path = root / "data/raw/bass_ii/original/PSI-25_Experimental table_BASS-II.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Authentic BASS-II CSV not found at {csv_path}")

    content_bytes = csv_path.read_bytes()
    observed_hash = hashlib.sha256(content_bytes).hexdigest()
    if observed_hash != AUTHENTIC_SHA256:
        raise ValueError(
            f"BASS-II CSV hash mismatch! Expected {AUTHENTIC_SHA256}, got {observed_hash}"
        )

    records: list[dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for data_idx, row in enumerate(reader, start=1):
            row_dict = dict(row)
            # csv_record_number: line 1 is header, data rows are lines 2 through 130
            row_dict["data_row_index"] = data_idx
            row_dict["csv_record_number"] = data_idx + 1
            records.append(row_dict)

    if len(records) != 129:
        raise ValueError(f"Expected exactly 129 records, found {len(records)}")

    return records


def run_m9_analysis_engine(
    engine: Engine,
    root: Path = ROOT_DIR,
    actor: str = ACTOR_REF,
    seal_results: bool = True,
) -> EngineRunResult:
    """Execute complete Milestone 9 Scientific Analysis Engine.
    
    1. Preflight: Verify BASS-II dataset identity & DB investigation.
    2. Seed & Seal Protocols: Seed M9 protocols in analysis_protocol.
    3. Calculate: Run deterministic pure-Python analysis for P1, P2, P3, P4.
    4. Persist: Write analytical_result and result_evidence rows in SERIALIZABLE txn.
    5. Seal: Cryptographically seal analytical_result trees via flare_sealing.seal.
    """
    t_start = time.perf_counter()

    # 1. Load authenticated records
    records = load_authenticated_records(root)

    # 2. Preflight database query
    with engine.connect() as conn:
        inv_row = conn.execute(
            text("SELECT id FROM public.investigation WHERE investigation_code = :code"),
            {"code": INVESTIGATION_CODE},
        ).mappings().first()

        if inv_row is None:
            raise RuntimeError(
                f"Investigation {INVESTIGATION_CODE} not found in database. Run M8 ingestion first."
            )
        inv_id = inv_row["id"]

        # Find CSV source document and primary evidence reference
        doc_row = conn.execute(
            text("""
            SELECT id FROM public.source_document
            WHERE investigation_id = :inv AND sha256 = :sha
            """),
            {"inv": inv_id, "sha": AUTHENTIC_SHA256},
        ).mappings().first()

        if doc_row is None:
            raise RuntimeError(
                f"Source document with hash {AUTHENTIC_SHA256} not found in database."
            )
        doc_id = doc_row["id"]

        ev_row = conn.execute(
            text("""
            SELECT id FROM public.evidence_reference
            WHERE investigation_id = :inv AND source_document_id = :doc
            LIMIT 1
            """),
            {"inv": inv_id, "doc": doc_id},
        ).mappings().first()

        if ev_row is None:
            raise RuntimeError(
                "Primary evidence reference for BASS-II source document not found."
            )
        ev_id = ev_row["id"]

    # 3. Seed Protocols in SERIALIZABLE transaction
    def _seed_protocols(conn: Connection) -> dict[str, UUID]:
        return seed_m9_protocols(
            conn,
            investigation_id=inv_id,
            evidence_id=ev_id,
            actor=actor,
            seal_protocols=seal_results,
        )

    protocol_ids = run_aggregate_transaction(engine, _seed_protocols, attempts=3)

    # 4. Pure Python calculations
    p1_report = execute_p1_analysis(records)
    p2_report = execute_p2_analysis(records)
    p3_report = execute_p3_analysis(records)
    p4_report = execute_p4_analysis(records)

    module_reports = {
        "P1_ENV_STATS": p1_report,
        "P2_O2_DEPLETION": p2_report,
        "P3_AIRFLOW_STEADY": p3_report,
        "P4_FUEL_REGIMES": p4_report,
    }

    all_metrics: list[tuple[UUID, MetricPayload]] = []
    for report in module_reports.values():
        prot_id = protocol_ids[report.protocol_code]
        for m in report.metrics:
            all_metrics.append((prot_id, m))

    # 5. Persistence Phase (SERIALIZABLE transaction)
    persisted_result_ids: list[UUID] = []

    def _persist_results(conn: Connection) -> list[UUID]:
        now = datetime.now(timezone.utc)
        ids: list[UUID] = []

        for prot_id, metric in all_metrics:
            res_id = metric_uuid(prot_id, metric.metric_code)
            ids.append(res_id)

            # Check if this analytical result is already sealed (idempotency guard)
            existing_seal = conn.execute(
                text("""
                SELECT id FROM public.aggregate_seal
                WHERE investigation_id = :inv AND result_id = :pid
                """),
                {"inv": inv_id, "pid": res_id},
            ).first()

            if existing_seal is not None:
                continue

            # Insert analytical_result
            conn.execute(
                text("""
                INSERT INTO public.analytical_result (
                    investigation_id, id, protocol_id, method, method_version,
                    parameters, result_kind, numeric_value, unit, unit_status,
                    text_value, artifact_document_id, producer_ref,
                    uncertainty, created_at
                ) VALUES (
                    :inv, :id, :prot, 'deterministic_python_engine', '1.0.0',
                    :params, :kind, :num_val, :unit, :unit_stat,
                    :text_val, NULL, :actor,
                    :uncertainty, :now
                ) ON CONFLICT (investigation_id, id) DO NOTHING
                """),
                {
                    "inv": inv_id,
                    "id": res_id,
                    "prot": prot_id,
                    "params": json.dumps(metric.parameters),
                    "kind": metric.result_kind,
                    "num_val": metric.numeric_value,
                    "unit": metric.unit,
                    "unit_stat": metric.unit_status,
                    "text_val": metric.text_value,
                    "actor": actor,
                    "uncertainty": json.dumps(metric.uncertainty),
                    "now": now,
                },
            )

            # Insert result_evidence
            res_ev_id = uuid5(NAMESPACE_M9, f"result_evidence:{res_id}:{ev_id}")
            conn.execute(
                text("""
                INSERT INTO public.result_evidence (
                    investigation_id, id, result_id, evidence_id, role, created_at
                ) VALUES (
                    :inv, :id, :res, :ev, 'primary_source_data', :now
                ) ON CONFLICT (investigation_id, result_id, evidence_id, role) DO NOTHING
                """),
                {
                    "inv": inv_id,
                    "id": res_ev_id,
                    "res": res_id,
                    "ev": ev_id,
                    "now": now,
                },
            )

        return ids

    persisted_result_ids = run_aggregate_transaction(engine, _persist_results, attempts=3)

    # 6. Cryptographic Sealing Phase
    seals: dict[str, str] = {}
    if seal_results:
        def _seal_all_results(conn: Connection) -> dict[str, str]:
            local_seals: dict[str, str] = {}
            for res_id in persisted_result_ids:
                # Check if already sealed
                existing = conn.execute(
                    text("""
                    SELECT id, member_digest FROM public.aggregate_seal
                    WHERE investigation_id = :inv AND result_id = :pid
                    """),
                    {"inv": inv_id, "pid": res_id},
                ).mappings().first()

                if existing is not None:
                    local_seals[str(res_id)] = existing["member_digest"]
                    continue

                seal_id = uuid5(NAMESPACE_M9, f"aggregate_seal:result:{res_id}")
                seal_row = conn.execute(
                    text("""
                    SELECT id, member_digest
                    FROM flare_sealing.seal('analytical_result', :inv, :pid, :sid, :actor)
                    """),
                    {
                        "inv": inv_id,
                        "pid": res_id,
                        "sid": seal_id,
                        "actor": actor,
                    },
                ).mappings().one()
                local_seals[str(res_id)] = seal_row["member_digest"]

            return local_seals

        seals = run_aggregate_transaction(engine, _seal_all_results, attempts=3)

    t_end = time.perf_counter()

    return EngineRunResult(
        investigation_code=INVESTIGATION_CODE,
        source_sha256=AUTHENTIC_SHA256,
        status="completed",
        module_reports=module_reports,
        total_metrics_computed=len(all_metrics),
        persisted_results_count=len(persisted_result_ids),
        sealed_results_count=len(seals),
        duration_seconds=t_end - t_start,
        cryptographic_seals=seals,
    )
