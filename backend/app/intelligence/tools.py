"""Tool registry and allowlist validation for FLARE Milestone 10.2 Intelligence Engine.

Enforces strict security and capability boundaries:
- Pure allowlist-based tool invocation
- Strict prohibition of arbitrary SQL or code execution
- Deterministic parameter contracts
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.intelligence.schemas import InvalidToolError


@dataclass(frozen=True)
class ToolDefinition:
    """Metadata specification for an allowlisted FLARE intelligence tool."""
    name: str
    description: str
    parameters_schema: dict[str, Any]
    required_role: str = "researcher"


TOOL_REGISTRY: dict[str, ToolDefinition] = {
    "m9_get_analytical_result": ToolDefinition(
        name="m9_get_analytical_result",
        description=(
            "Retrieve cryptographically sealed M9 scientific analytical results and metrics "
            "by investigation, protocol code, or metric code."
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "investigation": {"type": "string", "description": "Target investigation (e.g. PSI-25)"},
                "protocol_code": {"type": "string", "description": "M9 protocol code (e.g. M9-P1-ENV-STATS)"},
                "metric_code": {"type": "string", "description": "Specific M9 metric code"},
            },
            "required": ["investigation"],
        },
    ),
    "flare_query_observations": ToolDefinition(
        name="flare_query_observations",
        description=(
            "Query raw observational flight records and sensor measurements using safe "
            "parameterized SQL only. Arbitrary SQL generation is strictly prohibited."
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "investigation": {"type": "string", "description": "Target investigation (e.g. PSI-25)"},
                "test_number": {"type": "string", "description": "Specific test run number (e.g. test_01)"},
                "limit": {"type": "integer", "default": 50, "description": "Maximum records to return"},
            },
            "required": ["investigation"],
        },
    ),
    "flare_retrieve_documents": ToolDefinition(
        name="flare_retrieve_documents",
        description=(
            "Retrieve relevant literature chunks from authentic NASA technical reports, "
            "README files, and FAQs using PostgreSQL tsvector full-text search."
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query keywords"},
                "evidence_type": {
                    "type": "string",
                    "enum": ["EM", "NS", "DQ", "RT"],
                    "description": "Optional orthogonal evidence taxonomy filter",
                },
                "top_k": {"type": "integer", "default": 5, "description": "Number of top chunks to return"},
            },
            "required": ["query"],
        },
    ),
    "flare_check_scientific_prohibition": ToolDefinition(
        name="flare_check_scientific_prohibition",
        description=(
            "Audit a proposed scientific concept, metric, or extrapolation against explicit "
            "FLARE scientific prohibitions (Biot numbers, RQ_comb, slab LOI, lunar/Martian gravity, etc.)."
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "concept": {"type": "string", "description": "Scientific concept or calculation name to audit"},
            },
            "required": ["concept"],
        },
    ),
}

ALLOWLISTED_TOOLS: frozenset[str] = frozenset(TOOL_REGISTRY.keys())


def is_valid_tool(tool_name: str) -> bool:
    """Check if a tool name is present in the allowlisted registry."""
    return tool_name in ALLOWLISTED_TOOLS


def validate_tools(tool_names: list[str]) -> None:
    """Validate that all requested tool names exist in the allowlist.
    
    Raises:
        InvalidToolError: If any tool name is not recognized.
    """
    for tool in tool_names:
        if not is_valid_tool(tool):
            raise InvalidToolError(
                f"Tool '{tool}' is not an allowlisted tool. "
                f"Permitted tools are: {sorted(ALLOWLISTED_TOOLS)}"
            )


def get_tool_definition(tool_name: str) -> ToolDefinition:
    """Retrieve the formal specification for an allowlisted tool.
    
    Raises:
        InvalidToolError: If the tool name is not registered.
    """
    if not is_valid_tool(tool_name):
        raise InvalidToolError(
            f"Tool '{tool_name}' is not registered. "
            f"Permitted tools are: {sorted(ALLOWLISTED_TOOLS)}"
        )
    return TOOL_REGISTRY[tool_name]
