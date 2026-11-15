"""FastAPI routes for scientific analysis operations."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.services.analysis import (
    get_analysis_protocols_service,
    get_analysis_results_service,
    run_analysis_service,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/run", status_code=status.HTTP_200_OK)
def run_analysis(request: Request) -> dict[str, Any]:
    """Execute Milestone 9 Deterministic Scientific Analysis Engine."""
    engine = getattr(request.app.state, "db_engine", None)
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database engine unavailable",
        )
    try:
        report = run_analysis_service(engine=engine)
        return report
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis engine execution failed: {exc}",
        ) from exc


@router.get("/protocols", status_code=status.HTTP_200_OK)
def get_protocols(request: Request) -> list[dict[str, Any]]:
    """List registered scientific analysis protocols."""
    engine = getattr(request.app.state, "db_engine", None)
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database engine unavailable",
        )
    try:
        return get_analysis_protocols_service(engine)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query protocols: {exc}",
        ) from exc


@router.get("/results", status_code=status.HTTP_200_OK)
def get_results(
    request: Request,
    protocol_code: str | None = Query(default=None, description="Filter by protocol code"),
) -> list[dict[str, Any]]:
    """Query persisted and sealed analytical results."""
    engine = getattr(request.app.state, "db_engine", None)
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database engine unavailable",
        )
    try:
        return get_analysis_results_service(engine, protocol_code=protocol_code)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query results: {exc}",
        ) from exc
