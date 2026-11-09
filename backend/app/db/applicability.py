"""Evaluate only N1 applicability in a fresh committed transaction."""
from uuid import UUID

from sqlalchemy import Engine, text

from app.db.aggregate import run_aggregate_transaction


def applicability_current(engine: Engine, investigation_id: UUID, result_review_id: UUID) -> bool:
    """Re-evaluate a pinned approval as of a fresh SERIALIZABLE snapshot."""
    def evaluate(connection):
        return connection.execute(
            text("SELECT flare_n1.applicability_current(:investigation, :review)"),
            {"investigation": investigation_id, "review": result_review_id},
        ).scalar_one()

    return run_aggregate_transaction(engine, evaluate)
