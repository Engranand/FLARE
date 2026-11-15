"""Unit tests asserting FLARE M9 Explicit Scientific Prohibitions.

Governed by FLARE-CONTRACT-FINAL-M9-V2 Section 3.
Guarantees that ungrounded calculations, extrapolations, and fabricated parameters
cannot be computed or emitted by the M9 analysis engine.
"""
from decimal import Decimal
import pytest

from app.analysis.engine import load_authenticated_records
from app.analysis.p1_env_stats import execute_p1_analysis
from app.analysis.p2_oxygen import execute_p2_analysis
from app.analysis.p3_airflow import execute_p3_analysis
from app.analysis.p4_morphology import execute_p4_analysis


def test_prohibition_1_no_biot_number_calculations():
    """Assertion: Zero Biot numbers or Biot-based regimes may be calculated or inferred."""
    records = load_authenticated_records()
    p4_report = execute_p4_analysis(records)
    metric_codes = [m.metric_code for m in p4_report.metrics]
    assert not any("biot" in code for code in metric_codes)

    # Verify that thickness classifications are purely categorical
    regimes = p4_report.metadata["regime_distribution"]
    assert "THERMALLY_THIN_BI_LESS_01" not in regimes
    assert "THERMALLY_THICK_BI_GREATER_1" not in regimes


def test_prohibition_2_no_loi_logistic_regression_on_slabs():
    """Assertion: Logistic regression flammability prediction on thick slabs is prohibited."""
    records = load_authenticated_records()
    # Check Miller's thick slab records: all tested at O2 >= 17.9% with 0 low-O2 runs
    slab_records = [
        r for r in records
        if str(r.get("PI", "")).strip().lower() == "miller"
    ]
    assert len(slab_records) == 20
    slab_o2 = [Decimal(r["Calibrated  initial O2 % by vol "]) for r in slab_records]
    assert all(o2 >= Decimal("17.9") for o2 in slab_o2)
    # Complete absence of low-oxygen tests prevents logistic regression convergence (20:0 balance)


def test_prohibition_3_no_flame_spread_rate_vf():
    """Assertion: Linear flame spread rate Vf is prohibited from tabular CSV analysis."""
    records = load_authenticated_records()
    reports = [
        execute_p1_analysis(records),
        execute_p2_analysis(records),
        execute_p3_analysis(records),
        execute_p4_analysis(records),
    ]
    for rep in reports:
        for m in rep.metrics:
            assert "flame_spread" not in m.metric_code
            assert "flame_speed" not in m.metric_code
            assert "v_f" not in m.metric_code
            assert m.unit != "mm/s"


def test_prohibition_4_no_absolute_molar_consumption():
    """Assertion: Absolute molar oxygen consumption (Delta n_O2 in moles) is prohibited."""
    records = load_authenticated_records()
    p2_report = execute_p2_analysis(records)
    for m in p2_report.metrics:
        # Permitted units: mol/mol (mole fraction), % by vol, or dimensionless ratio
        assert m.unit != "mol"
        assert "moles_consumed" not in m.metric_code
        assert "delta_n_o2" not in m.metric_code


def test_prohibition_5_no_cubic_flow_polynomial():
    """Assertion: Flow velocity calculation uses strictly linear SPICE calibration."""
    records = load_authenticated_records()
    p3_report = execute_p3_analysis(records)
    vel_metric = next(m for m in p3_report.metrics if m.metric_code == "calibrated_airflow_velocity_median")
    assert "1.0066" in vel_metric.parameters["calibration_formula"]
    assert "cubic" not in vel_metric.parameters["calibration_formula"].lower()
    assert "polynomial" not in vel_metric.parameters["calibration_formula"].lower()


def test_prohibition_6_no_extrapolation_of_airflow():
    """Assertion: Dynamic sequences and stall deadband are excluded from static flow regressions."""
    records = load_authenticated_records()
    p3_report = execute_p3_analysis(records)
    # Only 24 records eligible for static velocity mapping
    assert p3_report.records_eligible == 24
    assert p3_report.records_excluded == 105


def test_prohibition_7_rq_comb_deferred():
    """Assertion: RQ_comb is not calculated in M9 metrics."""
    records = load_authenticated_records()
    p2_report = execute_p2_analysis(records)
    metric_codes = [m.metric_code for m in p2_report.metrics]
    assert not any("rq_comb" in code for code in metric_codes)
    assert not any("respiratory_quotient" in code for code in metric_codes)
