"""Evaluate N2 condition policy matching and consumption in SERIALIZABLE transactions."""
from typing import Any
from uuid import UUID

from sqlalchemy import Engine, text

from app.db.aggregate import run_aggregate_transaction


def n2_matches(engine: Engine, investigation_id: UUID, result_id: UUID) -> bool:
    """Evaluate N2 condition-policy matching in a fresh SERIALIZABLE transaction."""
    def evaluate(connection):
        return connection.execute(
            text("SELECT flare_n2.matches(:investigation, :result)"),
            {"investigation": investigation_id, "result": result_id},
        ).scalar_one()

    return run_aggregate_transaction(engine, evaluate)


def validate_n2_result(engine: Engine, investigation_id: UUID, result_id: UUID) -> list[dict[str, Any]]:
    """Return detailed diagnostic results from N2 policy matching."""
    def evaluate(connection):
        rows = connection.execute(
            text("SELECT rule, passed, detail FROM flare_n2.validate_result(:investigation, :result)"),
            {"investigation": investigation_id, "result": result_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    return run_aggregate_transaction(engine, evaluate)
