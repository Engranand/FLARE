"""Typing and domain data structures for FLARE Milestone 9 Scientific Analysis Engine.

Governed by FLARE-CONTRACT-FINAL-M9-V2.
All numeric values are deterministic and use Decimal for exact precision.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID


@dataclass(frozen=True)
class OrderStatisticCI:
    """Non-parametric order-statistic 95% confidence interval for sample median."""
    lower: Decimal
    upper: Decimal
    lower_rank: int  # 1-indexed rank j
    upper_rank: int  # 1-indexed rank k
    confidence_level: float = 0.95

    def to_dict(self) -> dict[str, Any]:
        return {
            "lower": str(self.lower),
            "upper": str(self.upper),
            "lower_rank": self.lower_rank,
            "upper_rank": self.upper_rank,
            "confidence_level": self.confidence_level,
        }


@dataclass(frozen=True)
class MetricPayload:
    """Single scientific metric calculated by an M9 module."""
    metric_code: str
    protocol_code: str
    canonical_name: str
    result_kind: Literal["numeric", "text", "artifact"]
    numeric_value: Decimal | None
    unit: str | None
    unit_status: Literal["known", "unknown", "not_applicable"]
    text_value: str | None
    sample_size: int
    parameters: dict[str, Any]
    uncertainty: dict[str, Any]
    quality_flags: list[str]
    source_record_provenance: list[int]  # CSV row numbers (e.g. 2..130)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_code": self.metric_code,
            "protocol_code": self.protocol_code,
            "canonical_name": self.canonical_name,
            "result_kind": self.result_kind,
            "numeric_value": str(self.numeric_value) if self.numeric_value is not None else None,
            "unit": self.unit,
            "unit_status": self.unit_status,
            "text_value": self.text_value,
            "sample_size": self.sample_size,
            "parameters": self.parameters,
            "uncertainty": self.uncertainty,
            "quality_flags": self.quality_flags,
            "source_record_provenance": self.source_record_provenance,
        }


@dataclass
class ModuleExecutionReport:
    """Execution output and calculated metrics for an analysis module."""
    protocol_code: str
    protocol_version: str
    description: str
    metrics: list[MetricPayload] = field(default_factory=list)
    records_processed: int = 0
    records_eligible: int = 0
    records_excluded: int = 0
    prohibitions_enforced: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_code": self.protocol_code,
            "protocol_version": self.protocol_version,
            "description": self.description,
            "metrics": [m.to_dict() for m in self.metrics],
            "records_processed": self.records_processed,
            "records_eligible": self.records_eligible,
            "records_excluded": self.records_excluded,
            "prohibitions_enforced": self.prohibitions_enforced,
            "metadata": self.metadata,
        }


@dataclass
class EngineRunResult:
    """Overall execution summary of the M9 analysis engine."""
    investigation_code: str
    source_sha256: str
    status: Literal["completed", "failed", "partial"]
    module_reports: dict[str, ModuleExecutionReport]
    total_metrics_computed: int
    persisted_results_count: int
    sealed_results_count: int
    duration_seconds: float
    cryptographic_seals: dict[str, str] = field(default_factory=dict)  # result_id -> member_digest

    def to_dict(self) -> dict[str, Any]:
        return {
            "investigation_code": self.investigation_code,
            "source_sha256": self.source_sha256,
            "status": self.status,
            "module_reports": {k: v.to_dict() for k, v in self.module_reports.items()},
            "total_metrics_computed": self.total_metrics_computed,
            "persisted_results_count": self.persisted_results_count,
            "sealed_results_count": self.sealed_results_count,
            "duration_seconds": round(self.duration_seconds, 4),
            "cryptographic_seals": self.cryptographic_seals,
        }
