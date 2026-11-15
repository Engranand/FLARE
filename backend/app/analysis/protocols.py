"""Protocol registration and database seeding for FLARE M9 Analysis Protocols.

Governed by FLARE-CONTRACT-FINAL-M9-V2 Section 4:
- M9-P1-ENV-STATS (v1.0.0)
- M9-P2-O2-DEPLETION (v1.0.0)
- M9-P3-AIRFLOW-STEADY (v1.0.0)
- M9-P4-FUEL-REGIMES (v1.0.0)

All protocols conform to:
- requirements_schema_version = 'relational-v1'
- issue_policy = 'all_unresolved_review_or_blocking'
- coverage_policy = 'every_input_test_segment'
- display_metadata = '{}'::jsonb
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import Connection, text

from app.analysis.p1_env_stats import PROTOCOL_CODE as P1_CODE, PROTOCOL_DESCRIPTION as P1_DESC
from app.analysis.p2_oxygen import PROTOCOL_CODE as P2_CODE, PROTOCOL_DESCRIPTION as P2_DESC
from app.analysis.p3_airflow import PROTOCOL_CODE as P3_CODE, PROTOCOL_DESCRIPTION as P3_DESC
from app.analysis.p4_morphology import PROTOCOL_CODE as P4_CODE, PROTOCOL_DESCRIPTION as P4_DESC

# Analysis namespace for deterministic UUIDs
NAMESPACE_M9 = UUID("b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e")

PROTOCOL_SPECS = [
    {
        "code": P1_CODE,
        "version": "1.0.0",
        "name": "Environmental Gas Descriptive Statistics",
        "description": P1_DESC,
        "target_variable": "calibrated_initial_o2",
        "unit": "mol/mol",
    },
    {
        "code": P2_CODE,
        "version": "1.0.0",
        "name": "Relative Oxygen Depletion Analysis",
        "description": P2_DESC,
        "target_variable": "calibrated_final_o2",
        "unit": "mol/mol",
    },
    {
        "code": P3_CODE,
        "version": "1.0.0",
        "name": "Steady-State Calibrated Airflow Mapping",
        "description": P3_DESC,
        "target_variable": "air_display",
        "unit": "m/s",
    },
    {
        "code": P4_CODE,
        "version": "1.0.0",
        "name": "Observed Fuel Morphology & Specimen Grouping",
        "description": P4_DESC,
        "target_variable": "fuel_sample_material",
        "unit": "count",
    },
]


def protocol_uuid(code: str, version: str = "1.0.0") -> UUID:
    """Generate deterministic UUID for analysis protocol."""
    return uuid5(NAMESPACE_M9, f"analysis_protocol:{code}:{version}")


def requirement_uuid(protocol_id: UUID, req_key: str) -> UUID:
    """Generate deterministic UUID for protocol requirement."""
    return uuid5(NAMESPACE_M9, f"protocol_requirement:{protocol_id}:{req_key}")


def unit_rule_uuid(requirement_id: UUID, unit_text: str) -> UUID:
    """Generate deterministic UUID for protocol unit rule."""
    return uuid5(NAMESPACE_M9, f"protocol_unit_rule:{requirement_id}:{unit_text}")


def seed_m9_protocols(
    conn: Connection,
    investigation_id: UUID,
    evidence_id: UUID,
    actor: str = "FLARE M9 Analysis Engine",
    seal_protocols: bool = True,
) -> dict[str, UUID]:
    """Seed M9 protocols, requirements, and unit rules into PostgreSQL, and cryptographically seal them.
    
    Returns a dict mapping protocol_code -> protocol_id.
    """
    now = datetime.now(timezone.utc)
    protocol_ids: dict[str, UUID] = {}

    for spec in PROTOCOL_SPECS:
        code = spec["code"]
        ver = spec["version"]
        prot_id = protocol_uuid(code, ver)
        protocol_ids[code] = prot_id

        # Check if already sealed (idempotency guard)
        existing_seal = conn.execute(
            text("""
            SELECT id FROM public.aggregate_seal
            WHERE investigation_id = :inv AND protocol_id = :pid
            """),
            {"inv": investigation_id, "pid": prot_id},
        ).first()

        if existing_seal is not None:
            continue

        # 1. Insert analysis_protocol
        conn.execute(
            text("""
            INSERT INTO public.analysis_protocol (
                investigation_id, id, protocol_code, protocol_version,
                description, issue_policy, coverage_policy,
                requirements_schema_version, display_metadata,
                evidence_id, created_at
            ) VALUES (
                :inv, :id, :code, :ver,
                :desc, 'all_unresolved_review_or_blocking', 'every_input_test_segment',
                'relational-v1', '{}'::jsonb,
                :ev, :now
            ) ON CONFLICT (investigation_id, protocol_code, protocol_version) DO NOTHING
            """),
            {
                "inv": investigation_id,
                "id": prot_id,
                "code": code,
                "ver": ver,
                "desc": spec["description"],
                "ev": evidence_id,
                "now": now,
            },
        )

        # 2. Look up target scientific_variable for input requirement
        var_row = conn.execute(
            text("""
            SELECT id FROM public.scientific_variable
            WHERE investigation_id = :inv AND variable_code = :vcode
            ORDER BY definition_version DESC LIMIT 1
            """),
            {"inv": investigation_id, "vcode": spec["target_variable"]},
        ).mappings().first()

        if var_row is not None:
            var_id = var_row["id"]
            req_key = f"input_{spec['target_variable']}"
            req_id = requirement_uuid(prot_id, req_key)

            conn.execute(
                text("""
                INSERT INTO public.protocol_requirement (
                    investigation_id, id, protocol_id, requirement_key,
                    target_kind, variable_id, role_id, phase,
                    min_count, max_count, value_policy,
                    stability_policy, instrument_policy, evidence_id,
                    created_at
                ) VALUES (
                    :inv, :id, :prot, :rkey,
                    'input', :vid, NULL, 'not_applicable',
                    1, 1000, 'numeric_only',
                    'not_applicable', 'not_required', :ev,
                    :now
                ) ON CONFLICT (investigation_id, protocol_id, requirement_key) DO NOTHING
                """),
                {
                    "inv": investigation_id,
                    "id": req_id,
                    "prot": prot_id,
                    "rkey": req_key,
                    "vid": var_id,
                    "ev": evidence_id,
                    "now": now,
                },
            )

            urule_id = unit_rule_uuid(req_id, spec["unit"])
            conn.execute(
                text("""
                INSERT INTO public.protocol_unit_rule (
                    investigation_id, id, requirement_id, unit_text,
                    unit_basis, method, method_version, evidence_id,
                    created_at
                ) VALUES (
                    :inv, :id, :req, :utext,
                    'canonical_si', 'linear_scaling', '1.0.0', :ev,
                    :now
                ) ON CONFLICT (investigation_id, requirement_id, unit_text, unit_basis, method, method_version) DO NOTHING
                """),
                {
                    "inv": investigation_id,
                    "id": urule_id,
                    "req": req_id,
                    "utext": spec["unit"],
                    "ev": evidence_id,
                    "now": now,
                },
            )

        # 3. Seal protocol aggregate if requested
        if seal_protocols:
            # Check if already sealed
            existing_seal = conn.execute(
                text("""
                SELECT id FROM public.aggregate_seal
                WHERE investigation_id = :inv AND protocol_id = :pid
                """),
                {"inv": investigation_id, "pid": prot_id},
            ).first()

            if existing_seal is None:
                p_seal_id = uuid5(NAMESPACE_M9, f"aggregate_seal:protocol:{prot_id}")
                conn.execute(
                    text("""
                    SELECT flare_sealing.seal('analysis_protocol', :inv, :pid, :sid, :actor)
                    """),
                    {
                        "inv": investigation_id,
                        "pid": prot_id,
                        "sid": p_seal_id,
                        "actor": actor,
                    },
                )

    return protocol_ids
