"""FLARE Milestone 9 Deterministic Scientific Analysis Engine.

Governed by FLARE-CONTRACT-FINAL-M9-V2.
"""
from app.analysis.engine import (
    AUTHENTIC_SHA256,
    INVESTIGATION_CODE,
    load_authenticated_records,
    run_m9_analysis_engine,
)
from app.analysis.p1_env_stats import execute_p1_analysis
from app.analysis.p2_oxygen import execute_p2_analysis
from app.analysis.p3_airflow import execute_p3_analysis
from app.analysis.p4_morphology import execute_p4_analysis
from app.analysis.protocols import seed_m9_protocols
from app.analysis.types import (
    EngineRunResult,
    MetricPayload,
    ModuleExecutionReport,
    OrderStatisticCI,
)

__all__ = [
    "AUTHENTIC_SHA256",
    "INVESTIGATION_CODE",
    "EngineRunResult",
    "MetricPayload",
    "ModuleExecutionReport",
    "OrderStatisticCI",
    "execute_p1_analysis",
    "execute_p2_analysis",
    "execute_p3_analysis",
    "execute_p4_analysis",
    "load_authenticated_records",
    "run_m9_analysis_engine",
    "seed_m9_protocols",
]
