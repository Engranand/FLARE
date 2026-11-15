"""Unit tests for FLARE M9 Module P3: Calibrated Airflow Mapping.

Governed by FLARE-CONTRACT-FINAL-M9-V2 Section 2.4.
"""
from decimal import Decimal
import pytest

from app.analysis.engine import load_authenticated_records
from app.analysis.p3_airflow import (
    CALIBRATION_COEFFICIENT,
    classify_airflow_record,
    execute_p3_analysis,
)


def test_calibration_formula():
    air_display = Decimal("5.0")
    expected_cm_s = Decimal("1.0066") * air_display  # 5.033 cm/s
    expected_m_s = expected_cm_s * Decimal("0.01")  # 0.05033 m/s

    record = {
        "Test #": "TEST_CALIB",
        "csv_record_number": 999,
        "Air display": "5.0",
        "Fan display": "65",
        "Flow restrictor": "0",
    }
    evaluated = classify_airflow_record(record)
    assert evaluated.classification == "VALID_CALIBRATED_STEADY_FLOW"
    assert evaluated.calibrated_velocity_cm_s == expected_cm_s
    assert evaluated.calibrated_velocity_m_s == expected_m_s


def test_p3_classification_counts():
    records = load_authenticated_records()
    assert len(records) == 129

    classified = [classify_airflow_record(r) for r in records]

    counts = {}
    for r in classified:
        counts[r.classification] = counts.get(r.classification, 0) + 1

    assert counts["VALID_CALIBRATED_STEADY_FLOW"] == 24
    assert counts["MOTOR_STALL_DEADBAND"] == 1
    assert counts["DYNAMIC_FLOW_SEQUENCE"] == 100
    assert counts["MISSING_AIRFLOW"] == 4
    assert sum(counts.values()) == 129


def test_motor_stall_deadband_record():
    records = load_authenticated_records()
    stall_recs = [
        classify_airflow_record(r)
        for r in records
        if r.get("Test #", "").strip() == "O2"
    ]
    assert len(stall_recs) == 1
    stall = stall_recs[0]
    assert stall.classification == "MOTOR_STALL_DEADBAND"
    assert stall.air_display_raw in ("0", "0.0")
    assert stall.raw_scalar_display == Decimal("0.0")
    assert stall.calibrated_velocity_m_s == Decimal("0.0")
    assert stall.is_eligible_static is False


def test_missing_airflow_records():
    records = load_authenticated_records()
    missing_test_ids = {"O7", "O8a", "O8b", "O9"}
    missing = [
        classify_airflow_record(r)
        for r in records
        if r.get("Test #", "").strip() in missing_test_ids
    ]
    assert len(missing) == 4
    for m in missing:
        assert m.classification == "MISSING_AIRFLOW"
        assert m.is_eligible_static is False


def test_p3_execution_on_authenticated_records():
    records = load_authenticated_records()
    report = execute_p3_analysis(records)

    assert report.protocol_code == "M9-P3-AIRFLOW-STEADY"
    assert report.records_processed == 129
    assert report.records_eligible == 24
    assert report.records_excluded == 105  # 100 sequences + 1 stall + 4 missing

    metric_map = {m.metric_code: m for m in report.metrics}

    # Velocity median for steady scalar runs
    vel_med = metric_map["calibrated_airflow_velocity_median"]
    assert vel_med.sample_size == 24
    assert vel_med.unit == "m/s"
    assert vel_med.numeric_value == Decimal("0.05033")
    assert Decimal(vel_med.parameters["min_velocity_m_s"]) == Decimal("0.020132")
    assert Decimal(vel_med.parameters["max_velocity_m_s"]) == Decimal("0.15099")

    # Velocity IQR
    vel_iqr = metric_map["calibrated_airflow_velocity_iqr"]
    assert vel_iqr.sample_size == 24
    assert vel_iqr.numeric_value == Decimal("0.05033")

    # Range
    vel_range = metric_map["calibrated_airflow_velocity_range"]
    assert vel_range.result_kind == "text"
    assert vel_range.text_value == "[0.020132, 0.150990]"
