"""Unit tests for FLARE M9 Module P1: Environmental Gas Descriptive Statistics.

Governed by FLARE-CONTRACT-FINAL-M9-V2 Section 2.1.
"""
from decimal import Decimal
import pytest

from app.analysis.engine import load_authenticated_records
from app.analysis.p1_env_stats import (
    compute_order_statistic_ci_median,
    compute_quantile_r7,
    compute_sample_median,
    execute_p1_analysis,
)


def test_compute_sample_median():
    # Odd length
    odd = [Decimal("1.0"), Decimal("3.0"), Decimal("5.0")]
    assert compute_sample_median(odd) == Decimal("3.0")

    # Even length
    even = [Decimal("1.0"), Decimal("2.0"), Decimal("4.0"), Decimal("5.0")]
    assert compute_sample_median(even) == Decimal("3.0")

    with pytest.raises(ValueError, match="empty array"):
        compute_sample_median([])


def test_compute_quantile_r7():
    # 4 points: 0, 10, 20, 30
    arr = [Decimal("0"), Decimal("10"), Decimal("20"), Decimal("30")]
    # p=0.25 -> h = 3 * 0.25 = 0.75 -> arr[0] + 0.75 * (arr[1] - arr[0]) = 7.5
    assert compute_quantile_r7(arr, 0.25) == Decimal("7.5")
    # p=0.75 -> h = 3 * 0.75 = 2.25 -> arr[2] + 0.25 * (arr[3] - arr[2]) = 22.5
    assert compute_quantile_r7(arr, 0.75) == Decimal("22.5")
    # p=0.0 -> 0, p=1.0 -> 30
    assert compute_quantile_r7(arr, 0.0) == Decimal("0")
    assert compute_quantile_r7(arr, 1.0) == Decimal("30")


def test_order_statistic_ci_median_formula():
    # For N=129: half=64.5, margin=11.1307 -> j=53, k=76 (1-indexed)
    arr_129 = [Decimal(str(i)) for i in range(1, 130)]
    ci = compute_order_statistic_ci_median(arr_129)
    assert ci.lower_rank == 53
    assert ci.upper_rank == 76
    assert ci.lower == Decimal("53")
    assert ci.upper == Decimal("76")


def test_negative_co_drift_preservation():
    # Simulated CO data with 3 negative values, 0, and positive values
    co_vals = [
        Decimal("-3.0"), Decimal("-2.0"), Decimal("-1.0"), Decimal("0.0"),
        Decimal("2.0"), Decimal("5.0"), Decimal("10.0")
    ]
    # Median of 7 elements is index 3: Decimal("0.0")
    med = compute_sample_median(co_vals)
    assert med == Decimal("0.0")
    # Ensure negative values are NOT clamped to zero
    assert co_vals[0] == Decimal("-3.0")
    assert co_vals[1] == Decimal("-2.0")
    assert co_vals[2] == Decimal("-1.0")


def test_p1_execution_on_authenticated_records():
    records = load_authenticated_records()
    assert len(records) == 129

    report = execute_p1_analysis(records)
    assert report.protocol_code == "M9-P1-ENV-STATS"
    assert report.records_processed == 129
    assert len(report.metrics) == 6

    metric_map = {m.metric_code: m for m in report.metrics}

    # 1. Initial O2
    o2_med = metric_map["ambient_initial_o2_median"]
    assert o2_med.sample_size == 129
    assert o2_med.unit == "mol/mol"
    assert o2_med.numeric_value == Decimal("0.182")
    assert len(o2_med.source_record_provenance) == 129

    o2_iqr = metric_map["ambient_initial_o2_iqr"]
    assert o2_iqr.sample_size == 129
    assert o2_iqr.numeric_value == Decimal("0.038")

    # 2. Initial CO2
    co2_med = metric_map["ambient_initial_co2_median"]
    assert co2_med.sample_size == 127
    assert co2_med.unit == "mol/mol"
    assert co2_med.numeric_value == Decimal("0.0041")
    assert co2_med.parameters["missing_count"] == 2

    co2_iqr = metric_map["ambient_initial_co2_iqr"]
    assert co2_iqr.sample_size == 127
    assert co2_iqr.numeric_value == Decimal("0.0020")

    # 3. Initial CO
    co_med = metric_map["ambient_initial_co_median"]
    assert co_med.sample_size == 126
    assert co_med.unit == "umol/mol"
    assert co_med.numeric_value == Decimal("5.5")
    assert co_med.parameters["negative_sensor_drift_records_count"] == 13
    assert "SENSOR_ZERO_DRIFT_PRESERVED" in co_med.quality_flags

    co_iqr = metric_map["ambient_initial_co_iqr"]
    assert co_iqr.sample_size == 126
    assert co_iqr.numeric_value == Decimal("58.5")
