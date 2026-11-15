"""FastAPI route handlers for FLARE Scientific Intelligence operations (Milestone 10.2 & 10.3)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.intelligence.dispatcher import ToolDispatcher
from app.intelligence.normalizer import QueryNormalizationError
from app.intelligence.planner import create_execution_plan
from app.intelligence.schemas import PlanRequest, PlanResponse
from app.intelligence.synthesis import ScientificSynthesisService
from app.intelligence.tool_schemas import ExecutionRequest, ExecutionResponse

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.post("/plan", response_model=PlanResponse, status_code=status.HTTP_200_OK)
def plan_query(payload: PlanRequest) -> PlanResponse:
    """Generate a deterministic query execution plan without LLM invocation.
    
    Validates input, checks scientific scope, classifies intent, maps target metrics,
    and returns a structured execution plan. Does not execute any tools.
    """
    try:
        plan = create_execution_plan(
            question=payload.question,
            investigation=payload.investigation,
            request_id=payload.request_id,
        )
        return PlanResponse(plan=plan)
    except QueryNormalizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution plan generation failed: {exc}",
        ) from exc


@router.post("/execute", response_model=ExecutionResponse, status_code=status.HTTP_200_OK)
def execute_query(request: Request, payload: ExecutionRequest) -> ExecutionResponse:
    """Execute allowlisted scientific tools against a validated execution plan.
    
    Accepts question parameters or a plan request, reconstructs and validates the
    ExecutionPlan server-side to prevent scope-gate bypass (SEC-01), coordinates
    tool execution within a read-only database transaction, and returns structured,
    immutable tool responses.
    """
    engine = getattr(request.app.state, "db_engine", None)

    try:
        # SEC-01 Remediation: Never trust client-submitted ExecutionPlan directly.
        # Always extract the original question and reconstruct the plan server-side
        # through normalizer, scope-gate, and intent classifier.
        question_text: str | None = None
        investigation: str = payload.investigation or "PSI-25"
        request_id = payload.request_id

        if payload.question is not None and str(payload.question).strip():
            question_text = str(payload.question).strip()
        elif payload.plan is not None:
            if payload.plan.original_question and str(payload.plan.original_question).strip():
                question_text = str(payload.plan.original_question).strip()
            if payload.plan.investigation:
                investigation = payload.plan.investigation
            if payload.plan.request_id:
                request_id = payload.plan.request_id

        if not question_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Either 'plan' or 'question' must be provided in ExecutionRequest",
            )

        # Server-side authoritative plan reconstruction
        server_plan = create_execution_plan(
            question=question_text,
            investigation=investigation,
            request_id=request_id,
        )

        dispatcher = ToolDispatcher(engine=engine)
        exec_response = dispatcher.dispatch_plan(plan=server_plan)

        if payload.synthesize:
            synth_service = getattr(request.app.state, "synthesis_service", None)
            if synth_service is None:
                synth_service = ScientificSynthesisService()
            exec_response.synthesis = synth_service.synthesize(
                plan=server_plan,
                tool_results=exec_response.tool_results,
            )

        return exec_response

    except QueryNormalizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool execution failed: {exc}",
        ) from exc
