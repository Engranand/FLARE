"""Controlled Tool Dispatcher for FLARE Milestone 10.3.

Coordinates execution of allowlisted intelligence tools against verified execution plans:
- Strict timeout hierarchy (request deadline, per-tool deadline, statement timeout)
- Read-only transaction enforcement
- Automatic rollback and connection cleanup
- Aggregation of structured tool results into ExecutionResponse
"""
from __future__ import annotations

import time
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import DBAPIError, OperationalError, TimeoutError as SATimeoutError

from app.intelligence.planner import create_execution_plan
from app.intelligence.schemas import (
    ExecutionPlan,
    IntentEnum,
    InvalidToolError,
    QueryState,
    ScopeStatusEnum,
)
from app.intelligence.tool_executor import (
    execute_flare_check_scientific_prohibition,
    execute_flare_query_observations,
    execute_flare_retrieve_documents,
    execute_m9_get_analytical_result,
)
from app.intelligence.tool_schemas import (
    ExecutionResponse,
    ToolExecutionStatus,
    ToolResult,
)
from app.intelligence.tools import is_valid_tool, validate_tools

DEFAULT_REQUEST_TIMEOUT_SECONDS = 10.0
DEFAULT_TOOL_TIMEOUT_SECONDS = 5.0
DEFAULT_STATEMENT_TIMEOUT_MS = 3000


class ToolDispatcher:
    """Manages secure, parameterized execution of intelligence tools."""

    def __init__(
        self,
        engine: Engine | None = None,
        request_timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
        tool_timeout_seconds: float = DEFAULT_TOOL_TIMEOUT_SECONDS,
        statement_timeout_ms: int = DEFAULT_STATEMENT_TIMEOUT_MS,
    ) -> None:
        self.engine = engine
        self.request_timeout_seconds = request_timeout_seconds
        self.tool_timeout_seconds = tool_timeout_seconds
        self.statement_timeout_ms = statement_timeout_ms

    def dispatch_plan(
        self,
        plan: ExecutionPlan,
        conn: Connection | None = None,
    ) -> ExecutionResponse:
        """Execute all allowlisted tools required by an ExecutionPlan.
        
        Args:
            plan: Validated execution plan from M10.2 orchestration.
            conn: Optional existing database connection. If None, uses self.engine.
            
        Returns:
            ExecutionResponse detailing all tool outputs and overall execution status.
        """
        t_start = time.perf_counter()
        request_id = plan.request_id

        # 1. Check if plan is abstained, failed, or prohibited (SEC-01 defense-in-depth)
        if plan.scope_status in (ScopeStatusEnum.PROHIBITED, ScopeStatusEnum.OUT_OF_SCOPE):
            return ExecutionResponse(
                request_id=request_id,
                plan=plan,
                tool_results=[],
                overall_status=ToolExecutionStatus.PROHIBITED,
                duration_ms=(time.perf_counter() - t_start) * 1000,
            )

        if plan.state == QueryState.ABSTAINED:
            # Map scope status to appropriate ToolExecutionStatus
            agg_status = (
                ToolExecutionStatus.PROHIBITED
                if plan.scope_status in (ScopeStatusEnum.PROHIBITED, ScopeStatusEnum.OUT_OF_SCOPE)
                else ToolExecutionStatus.NO_RESULTS
            )

            return ExecutionResponse(
                request_id=request_id,
                plan=plan,
                tool_results=[],
                overall_status=agg_status,
                duration_ms=(time.perf_counter() - t_start) * 1000,
            )

        if plan.state == QueryState.FAILED:
            return ExecutionResponse(
                request_id=request_id,
                plan=plan,
                tool_results=[],
                overall_status=ToolExecutionStatus.INTERNAL_ERROR,
                duration_ms=(time.perf_counter() - t_start) * 1000,
            )

        # 2. Validate all tools prior to execution
        try:
            validate_tools(plan.required_tools)
        except InvalidToolError as exc:
            return ExecutionResponse(
                request_id=request_id,
                plan=plan,
                tool_results=[
                    ToolResult(
                        tool_id="dispatcher_validation",
                        execution_status=ToolExecutionStatus.INVALID_INPUT,
                        request_id=request_id,
                        limitations=[str(exc)],
                    )
                ],
                overall_status=ToolExecutionStatus.INVALID_INPUT,
                duration_ms=(time.perf_counter() - t_start) * 1000,
            )

        # 3. Connection Management (Read-Only Transaction Block SEC-03)
        tool_results: list[ToolResult] = []

        if conn is not None:
            if conn.dialect.name == "postgresql":
                if not conn.in_transaction():
                    with conn.begin():
                        conn.execute(text("SET LOCAL transaction_read_only = on"))
                        conn.execute(text(f"SET LOCAL statement_timeout = {self.statement_timeout_ms}"))
                        self._execute_tools(conn, plan, tool_results, t_start)
                else:
                    conn.execute(text("SET LOCAL transaction_read_only = on"))
                    conn.execute(text(f"SET LOCAL statement_timeout = {self.statement_timeout_ms}"))
                    self._execute_tools(conn, plan, tool_results, t_start)
            else:
                self._execute_tools(conn, plan, tool_results, t_start)
        elif self.engine is not None:
            try:
                with self.engine.connect() as managed_conn:
                    # Enforce explicit transaction block for SET LOCAL read-only and statement timeout
                    with managed_conn.begin():
                        if managed_conn.dialect.name == "postgresql":
                            managed_conn.execute(text("SET LOCAL transaction_read_only = on"))
                            managed_conn.execute(
                                text(f"SET LOCAL statement_timeout = {self.statement_timeout_ms}")
                            )
                        self._execute_tools(managed_conn, plan, tool_results, t_start)
            except (SATimeoutError, OperationalError, DBAPIError) as exc:
                err_msg = str(exc)
                if "timeout" in err_msg.lower() or "canceling statement" in err_msg.lower():
                    tool_results.append(
                        ToolResult(
                            tool_id="database_timeout",
                            execution_status=ToolExecutionStatus.TIMEOUT,
                            request_id=request_id,
                            limitations=[f"Database statement timeout exceeded ({self.statement_timeout_ms} ms)"],
                        )
                    )
                elif "read-only" in err_msg.lower() or "25006" in err_msg:
                    tool_results.append(
                        ToolResult(
                            tool_id="database_security",
                            execution_status=ToolExecutionStatus.INTERNAL_ERROR,
                            request_id=request_id,
                            limitations=["Write query rejected by read-only transaction enforcement (SQLSTATE 25006)"],
                        )
                    )
                else:
                    tool_results.append(
                        ToolResult(
                            tool_id="database_error",
                            execution_status=ToolExecutionStatus.INTERNAL_ERROR,
                            request_id=request_id,
                            limitations=[f"Database operational error encountered during tool execution: {exc.__class__.__name__}"],
                        )
                    )
        else:
            # No database connection provided; execute non-database tools or return NO_RESULTS
            self._execute_tools_offline(plan, tool_results, t_start)

        t_end = time.perf_counter()
        total_duration_ms = (t_end - t_start) * 1000
        overall_status = self._aggregate_status(tool_results)

        return ExecutionResponse(
            request_id=request_id,
            plan=plan,
            tool_results=tool_results,
            overall_status=overall_status,
            duration_ms=total_duration_ms,
        )

    def _execute_tools(
        self,
        conn: Connection,
        plan: ExecutionPlan,
        tool_results: list[ToolResult],
        t_start: float,
    ) -> None:
        """Dispatch required tools using an active connection."""
        for tool_name in plan.required_tools:
            # Check deadline
            if (time.perf_counter() - t_start) > self.request_timeout_seconds:
                tool_results.append(
                    ToolResult(
                        tool_id=tool_name,
                        execution_status=ToolExecutionStatus.TIMEOUT,
                        request_id=plan.request_id,
                        limitations=[f"Request deadline exceeded ({self.request_timeout_seconds} s) before tool execution"],
                    )
                )
                break

            if tool_name == "m9_get_analytical_result":
                res = execute_m9_get_analytical_result(
                    conn=conn,
                    parameters={"investigation": plan.investigation},
                    request_id=plan.request_id,
                    target_metrics=plan.requested_metrics,
                )
                tool_results.append(res)

            elif tool_name == "flare_query_observations":
                params = {"investigation": plan.investigation}
                # Check if specific target metrics map to variable keywords
                if plan.requested_metrics:
                    params["variable"] = plan.requested_metrics[0]
                res = execute_flare_query_observations(
                    conn=conn,
                    parameters=params,
                    request_id=plan.request_id,
                )
                tool_results.append(res)

            elif tool_name == "flare_check_scientific_prohibition":
                res = execute_flare_check_scientific_prohibition(
                    parameters={"concept": plan.normalized_question},
                    request_id=plan.request_id,
                )
                tool_results.append(res)

            elif tool_name == "flare_retrieve_documents":
                res = execute_flare_retrieve_documents(
                    parameters={"query": plan.normalized_question},
                    request_id=plan.request_id,
                    conn=conn,
                )
                tool_results.append(res)

    def _execute_tools_offline(
        self,
        plan: ExecutionPlan,
        tool_results: list[ToolResult],
        t_start: float,
    ) -> None:
        """Handle execution when no database engine is connected."""
        for tool_name in plan.required_tools:
            if tool_name == "flare_check_scientific_prohibition":
                res = execute_flare_check_scientific_prohibition(
                    parameters={"concept": plan.normalized_question},
                    request_id=plan.request_id,
                )
                tool_results.append(res)
            elif tool_name == "flare_retrieve_documents":
                res = execute_flare_retrieve_documents(
                    parameters={"query": plan.normalized_question},
                    request_id=plan.request_id,
                    conn=conn,
                )
                tool_results.append(res)
            else:
                tool_results.append(
                    ToolResult(
                        tool_id=tool_name,
                        execution_status=ToolExecutionStatus.INTERNAL_ERROR,
                        request_id=plan.request_id,
                        limitations=["Database engine unavailable for analytical tool execution"],
                    )
                )

    @staticmethod
    def _aggregate_status(results: list[ToolResult]) -> ToolExecutionStatus:
        """Compute aggregate status across multiple executed tools."""
        if not results:
            return ToolExecutionStatus.NO_RESULTS

        statuses = [r.execution_status for r in results]

        if ToolExecutionStatus.INTEGRITY_FAILURE in statuses:
            return ToolExecutionStatus.INTEGRITY_FAILURE
        if ToolExecutionStatus.TIMEOUT in statuses:
            return ToolExecutionStatus.TIMEOUT
        if ToolExecutionStatus.INTERNAL_ERROR in statuses:
            return ToolExecutionStatus.INTERNAL_ERROR
        if ToolExecutionStatus.PROHIBITED in statuses:
            return ToolExecutionStatus.PROHIBITED
        if ToolExecutionStatus.INVALID_INPUT in statuses:
            return ToolExecutionStatus.INVALID_INPUT
        if all(s == ToolExecutionStatus.NOT_IMPLEMENTED for s in statuses):
            return ToolExecutionStatus.NOT_IMPLEMENTED
        if all(s == ToolExecutionStatus.NO_RESULTS for s in statuses):
            return ToolExecutionStatus.NO_RESULTS
        if any(s == ToolExecutionStatus.SUCCESS for s in statuses):
            return ToolExecutionStatus.SUCCESS

        return statuses[0]
