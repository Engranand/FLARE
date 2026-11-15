"""Service layer for FLARE Scientific Analysis Engine."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import Engine, text

from app.analysis.engine import ACTOR_REF, ROOT_DIR, run_m9_analysis_engine


def run_analysis_service(
    engine: Engine,
    root: Path = ROOT_DIR,
    actor: str = ACTOR_REF,
    seal_results: bool = True,
) -> dict[str, Any]:
    """Execute M9 analysis engine and return dictionary summary."""
    result = run_m9_analysis_engine(engine=engine, root=root, actor=actor, seal_results=seal_results)
    return result.to_dict()


def get_analysis_protocols_service(engine: Engine) -> list[dict[str, Any]]:
    """Query registered analysis protocols."""
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
            SELECT id, protocol_code, protocol_version, description,
                   issue_policy, coverage_policy, requirements_schema_version,
                   created_at
            FROM public.analysis_protocol
            ORDER BY protocol_code, protocol_version
            """)
        ).mappings().fetchall()
        return [dict(r) for r in rows]


def get_analysis_results_service(
    engine: Engine,
    protocol_code: str | None = None,
) -> list[dict[str, Any]]:
    """Query persisted analytical results with optional protocol filter."""
    query = """
        SELECT r.id, p.protocol_code, p.protocol_version, r.method, r.method_version,
               r.result_kind, r.numeric_value, r.unit, r.unit_status, r.text_value,
               r.parameters, r.uncertainty, r.producer_ref, r.created_at,
               s.member_digest AS seal_digest, s.created_at AS sealed_at
        FROM public.analytical_result r
        JOIN public.analysis_protocol p ON (p.investigation_id, p.id) = (r.investigation_id, r.protocol_id)
        LEFT JOIN public.aggregate_seal s ON (s.investigation_id, s.result_id) = (r.investigation_id, r.id)
    """
    params: dict[str, Any] = {}
    if protocol_code:
        query += " WHERE p.protocol_code = :pcode"
        params["pcode"] = protocol_code
    query += " ORDER BY p.protocol_code, r.id"

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).mappings().fetchall()
        return [dict(r) for r in rows]
