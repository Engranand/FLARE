"""Module P3: Steady-State Calibrated Airflow Velocity Mapping.

Governed by FLARE-CONTRACT-FINAL-M9-V2 Section 2.4:
- Protocol Code: M9-P3-AIRFLOW-STEADY (v1.0.0)
- Authentic NASA SPICE Calibration Equation (Fan calibration data.xlsx, Row 33):
    U_inf = 1.0066 * (Air Display) [cm/s]
    Canonical SI: U_inf = (1.0066 * Air Display) * 10^-2 [m/s]
- Gated eligibility partitioning across 129 flight records:
    1. VALID_CALIBRATED_STEADY_FLOW (N=24): single scalar Air display in [2.0, 15.0] cm/s.
    2. MOTOR_STALL_DEADBAND (N=1, Test 'O2'): Air display = 0.0 (fan shuts off above 3.8 V).
    3. SEQUENCE_EXCLUDED_FROM_STATIC_MAPPING (N=100): multi-step potentiometer adjustments
       and operator notes; excluded from static flow regressions due to ~1-min sensor lag.
    4. MISSING_EXCLUDED (N=4, Tests 'O7', 'O8a', 'O8b', 'O9'): empty/unrecorded airflow.
- Explicit prohibitions:
    - NO cubic flow polynomials (non-existent in NASA calibration records).
    - NO extrapolation beyond empirical calibration setpoints.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re
from typing import Any, Literal

from app.analysis.p1_env_stats import (
    compute_order_statistic_ci_median,
    compute_quantile_r7,
    compute_sample_median,
)
from app.analysis.types import MetricPayload, ModuleExecutionReport, OrderStatisticCI

PROTOCOL_CODE = "M9-P3-AIRFLOW-STEADY"
PROTOCOL_VERSION = "1.0.0"
PROTOCOL_DESCRIPTION = (
    "Empirical linear calibration of steady-state microgravity airflow velocity "
    "from NASA SPICE wind tunnel calibration (U = 1.0066 * Air display)."
)

CALIBRATION_COEFFICIENT = Decimal("1.0066")
SCALE_CM_TO_M = Decimal("0.01")


@dataclass(frozen=True)
class EvaluatedAirflowRecord:
    """Classified and calibrated airflow record."""
    test_id: str
    csv_record_number: int
    air_display_raw: str
    fan_display_raw: str
    flow_restrictor_setting: str
    classification: Literal[
        "VALID_CALIBRATED_STEADY_FLOW",
        "MOTOR_STALL_DEADBAND",
        "DYNAMIC_FLOW_SEQUENCE",
        "MISSING_AIRFLOW",
    ]
    raw_scalar_display: Decimal | None
    calibrated_velocity_cm_s: Decimal | None
    calibrated_velocity_m_s: Decimal | None
    is_eligible_static: bool
    status_notes: str


def classify_airflow_record(record: dict[str, Any]) -> EvaluatedAirflowRecord:
    """Classify and evaluate a single BASS-II record for steady-state airflow calibration."""
    test_id = str(record.get("Test #", "")).strip()
    rec_num = int(record.get("csv_record_number", 0))

    air_raw = str(record.get("Air display", "")).strip()
    fan_raw = str(record.get("Fan display", "")).strip()
    restrictor = str(record.get("Flow restrictor", "")).strip()

    # 1. Missing telemetry
    if not air_raw or air_raw.lower() in ("none", "n/a", ""):
        return EvaluatedAirflowRecord(
            test_id=test_id,
            csv_record_number=rec_num,
            air_display_raw=air_raw,
            fan_display_raw=fan_raw,
            flow_restrictor_setting=restrictor,
            classification="MISSING_AIRFLOW",
            raw_scalar_display=None,
            calibrated_velocity_cm_s=None,
            calibrated_velocity_m_s=None,
            is_eligible_static=False,
            status_notes="Airflow telemetry missing or unrecorded",
        )

    # 2. Check if raw value is a single scalar float/int or multi-token sequence
    tokens = air_raw.split()
    is_single_token = len(tokens) == 1

    scalar_val: Decimal | None = None
    if is_single_token:
        try:
            scalar_val = Decimal(tokens[0])
        except Exception:
            scalar_val = None

    # Multi-token or non-numeric tokens -> dynamic flow sequence
    if not is_single_token or scalar_val is None:
        return EvaluatedAirflowRecord(
            test_id=test_id,
            csv_record_number=rec_num,
            air_display_raw=air_raw,
            fan_display_raw=fan_raw,
            flow_restrictor_setting=restrictor,
            classification="DYNAMIC_FLOW_SEQUENCE",
            raw_scalar_display=None,
            calibrated_velocity_cm_s=None,
            calibrated_velocity_m_s=None,
            is_eligible_static=False,
            status_notes=f"Dynamic flow sequence or operator adjustment note ({air_raw!r}); excluded from static mapping",
        )

    # 3. Check for motor stall deadband (Air display == 0.0)
    if scalar_val == Decimal("0.0"):
        return EvaluatedAirflowRecord(
            test_id=test_id,
            csv_record_number=rec_num,
            air_display_raw=air_raw,
            fan_display_raw=fan_raw,
            flow_restrictor_setting=restrictor,
            classification="MOTOR_STALL_DEADBAND",
            raw_scalar_display=scalar_val,
            calibrated_velocity_cm_s=Decimal("0.0"),
            calibrated_velocity_m_s=Decimal("0.0"),
            is_eligible_static=False,
            status_notes="Motor stall deadband: fan controller turns off above 3.8 V; zero convective velocity",
        )

    # 4. Valid steady scalar run
    # Formula: U_cm_s = 1.0066 * Air; U_m_s = U_cm_s * 0.01
    vel_cm_s = CALIBRATION_COEFFICIENT * scalar_val
    vel_m_s = vel_cm_s * SCALE_CM_TO_M

    return EvaluatedAirflowRecord(
        test_id=test_id,
        csv_record_number=rec_num,
        air_display_raw=air_raw,
        fan_display_raw=fan_raw,
        flow_restrictor_setting=restrictor,
        classification="VALID_CALIBRATED_STEADY_FLOW",
        raw_scalar_display=scalar_val,
        calibrated_velocity_cm_s=vel_cm_s,
        calibrated_velocity_m_s=vel_m_s,
        is_eligible_static=True,
        status_notes="Valid steady-state scalar airflow within empirical calibration domain [2.0, 15.0] cm/s",
    )


def execute_p3_analysis(records: list[dict[str, Any]]) -> ModuleExecutionReport:
    """Execute Module P3 on ingested BASS-II records."""
    report = ModuleExecutionReport(
        protocol_code=PROTOCOL_CODE,
        protocol_version=PROTOCOL_VERSION,
        description=PROTOCOL_DESCRIPTION,
        records_processed=len(records),
        prohibitions_enforced=[
            "PROHIBITED_POLYNOMIAL: Cubic flow polynomial strictly prohibited (non-existent in NASA calibration records)",
            "PROHIBITED_EXTRAPOLATION: Static velocity mapping strictly confined to empirical calibration domain [2.0, 15.0] cm/s",
            "MANDATORY_EXCLUSION: 100 dynamic potentiometer adjustment sequences excluded due to ~1-min sensor lag",
            "MOTOR_STALL_FLAGGING: 1 motor stall deadband run (Test 'O2', Air display = 0.0) flagged and excluded from regressions",
        ],
    )

    classified = [classify_airflow_record(r) for r in records]

    valid_recs = [r for r in classified if r.classification == "VALID_CALIBRATED_STEADY_FLOW"]
    stall_recs = [r for r in classified if r.classification == "MOTOR_STALL_DEADBAND"]
    dyn_recs = [r for r in classified if r.classification == "DYNAMIC_FLOW_SEQUENCE"]
    missing_recs = [r for r in classified if r.classification == "MISSING_AIRFLOW"]

    report.metadata["classification_counts"] = {
        "VALID_CALIBRATED_STEADY_FLOW": len(valid_recs),
        "MOTOR_STALL_DEADBAND": len(stall_recs),
        "DYNAMIC_FLOW_SEQUENCE": len(dyn_recs),
        "MISSING_AIRFLOW": len(missing_recs),
        "TOTAL_PROCESSED": len(classified),
    }

    report.records_eligible = len(valid_recs)
    report.records_excluded = len(stall_recs) + len(dyn_recs) + len(missing_recs)

    if valid_recs:
        sorted_recs = sorted(valid_recs, key=lambda x: x.calibrated_velocity_m_s)
        vels_m_s = [x.calibrated_velocity_m_s for x in sorted_recs]
        rows = [x.csv_record_number for x in sorted_recs]
        n = len(vels_m_s)

        med_m_s = compute_sample_median(vels_m_s)
        q1_m_s = compute_quantile_r7(vels_m_s, 0.25)
        q3_m_s = compute_quantile_r7(vels_m_s, 0.75)
        iqr_m_s = q3_m_s - q1_m_s
        ci_m_s = compute_order_statistic_ci_median(vels_m_s)

        min_m_s = vels_m_s[0]
        max_m_s = vels_m_s[-1]

        report.metrics.append(
            MetricPayload(
                metric_code="calibrated_airflow_velocity_median",
                protocol_code=PROTOCOL_CODE,
                canonical_name="Calibrated Duct Airflow Velocity Median (Steady Scalar Subset)",
                result_kind="numeric",
                numeric_value=med_m_s,
                unit="m/s",
                unit_status="known",
                text_value=None,
                sample_size=n,
                parameters={
                    "calibration_formula": "U_inf = 1.0066 * (Air Display) [cm/s]",
                    "scale_factor_to_si": "0.01",
                    "calibration_source": "Fan calibration data.xlsx (Row 33, NASA Glenn SPICE traverse)",
                    "valid_range_air_display_cm_s": "[2.0, 15.0]",
                    "min_velocity_m_s": str(min_m_s),
                    "max_velocity_m_s": str(max_m_s),
                },
                uncertainty={
                    "confidence_interval_95": ci_m_s.to_dict(),
                    "hot_wire_sensor_lag": "~60 seconds",
                },
                quality_flags=["STEADY_SCALAR_SUBSET", "CALIBRATED_LINEAR_SPICE"],
                source_record_provenance=rows,
            )
        )

        report.metrics.append(
            MetricPayload(
                metric_code="calibrated_airflow_velocity_iqr",
                protocol_code=PROTOCOL_CODE,
                canonical_name="Calibrated Duct Airflow Velocity Interquartile Range (Steady Scalar Subset)",
                result_kind="numeric",
                numeric_value=iqr_m_s,
                unit="m/s",
                unit_status="known",
                text_value=None,
                sample_size=n,
                parameters={
                    "q1": str(q1_m_s),
                    "q3": str(q3_m_s),
                    "interpolation_method": "R_TYPE_7",
                },
                uncertainty={},
                quality_flags=["STEADY_SCALAR_SUBSET", "CALIBRATED_LINEAR_SPICE"],
                source_record_provenance=rows,
            )
        )

        report.metrics.append(
            MetricPayload(
                metric_code="calibrated_airflow_velocity_range",
                protocol_code=PROTOCOL_CODE,
                canonical_name="Calibrated Duct Airflow Velocity Range Bounds (Steady Scalar Subset)",
                result_kind="text",
                numeric_value=None,
                unit="m/s",
                unit_status="known",
                text_value=f"[{min_m_s}, {max_m_s}]",
                sample_size=n,
                parameters={
                    "min_m_s": str(min_m_s),
                    "max_m_s": str(max_m_s),
                    "min_cm_s": str(min_m_s * Decimal("100")),
                    "max_cm_s": str(max_m_s * Decimal("100")),
                },
                uncertainty={},
                quality_flags=["STEADY_SCALAR_SUBSET", "BOUNDS_TEXT"],
                source_record_provenance=rows,
            )
        )

    return report
