"""Unit tests for FLARE M9 Module P2: Relative Oxygen Depletion Analysis.

Governed by FLARE-CONTRACT-FINAL-M9-V2 Sections 2.2 and 2.3.
"""
from decimal import Decimal
import pytest

from app.analysis.engine import load_authenticated_records
from app.analysis.p2_oxygen import (
    NEGATIVE_DRIFT_TEST_IDS,
    QUARANTINED_TEST_IDS,
    classify_oxygen_record,
    execute_p2_analysis,
)


def test_p2_disjoint_partition_counts():
    records = load_authenticated_records()
    assert len(records) == 129

    classified = [classify_oxygen_record(r) for r in records]

    counts = {}
    for r in classified:
        counts[r.category] = counts.get(r.category, 0) + 1

    # Exact audited partition counts
    assert counts["POSITIVE_DEPLETION"] == 93
    assert counts["ZERO_DEPLETION"] == 24
    assert counts["NEGATIVE_SENSOR_DRIFT"] == 5
    assert counts["QUARANTINED_GROSS_ANOMALY"] == 5
    assert counts["MISSING_FINAL_O2"] == 2
    assert sum(counts.values()) == 129


def test_quarantined_test_ids_and_reasons():
    records = load_authenticated_records()
    quarantined = [
        classify_oxygen_record(r)
        for r in records
        if r.get("Test #", "").strip() in QUARANTINED_TEST_IDS
    ]
    assert len(quarantined) == 5
    for q in quarantined:
        assert q.category == "QUARANTINED_GROSS_ANOMALY"
        assert q.is_eligible_standard is False
        assert q.is_eligible_signed_cdf is False
        assert "Gross recording anomaly" in str(q.exclusion_reason)
        assert abs(q.delta_o2_vol_pct) > Decimal("19.0")


def test_negative_sensor_drift_records_signed_unclamped():
    records = load_authenticated_records()
    drift = [
        classify_oxygen_record(r)
        for r in records
        if r.get("Test #", "").strip() in NEGATIVE_DRIFT_TEST_IDS
    ]
    assert len(drift) == 5
    for d in drift:
        assert d.category == "NEGATIVE_SENSOR_DRIFT"
        assert d.delta_o2_vol_pct == Decimal("-0.1")
        assert d.delta_o2_mol_fraction == Decimal("-0.0010")
        # Never clamped to zero
        assert d.delta_o2_mol_fraction < Decimal("0.0")
        assert d.is_eligible_standard is False
        assert d.is_eligible_signed_cdf is True


def test_missing_final_o2_records():
    records = load_authenticated_records()
    missing = [
        classify_oxygen_record(r)
        for r in records
        if r.get("Test #", "").strip() in ("B14", "F3")
    ]
    assert len(missing) == 2
    for m in missing:
        assert m.category == "MISSING_FINAL_O2"
        assert m.final_o2_vol_pct is None
        assert m.delta_o2_vol_pct is None
        assert m.delta_o2_mol_fraction is None


def test_p2_execution_on_authenticated_records():
    records = load_authenticated_records()
    report = execute_p2_analysis(records)

    assert report.protocol_code == "M9-P2-O2-DEPLETION"
    assert report.records_processed == 129
    assert report.records_eligible == 117  # 93 positive + 24 zero
    assert report.records_excluded == 7    # 5 quarantined + 2 missing

    metric_map = {m.metric_code: m for m in report.metrics}

    # 1. Non-negative depletion median & IQR (N=117)
    nn_med = metric_map["non_negative_o2_depletion_median"]
    assert nn_med.sample_size == 117
    assert nn_med.numeric_value == Decimal("0.0040")
    assert nn_med.unit == "mol/mol"

    nn_iqr = metric_map["non_negative_o2_depletion_iqr"]
    assert nn_iqr.sample_size == 117
    assert nn_iqr.numeric_value == Decimal("0.0060")

    # 2. Relative depletion ratio Pi_O2 (N=117)
    pi_med = metric_map["relative_o2_depletion_ratio_median"]
    assert pi_med.sample_size == 117
    assert pi_med.unit is None
    assert pi_med.unit_status == "not_applicable"

    # 3. Positive-only depletion (N=93)
    pos_med = metric_map["positive_o2_depletion_median"]
    assert pos_med.sample_size == 93
    assert pos_med.numeric_value == Decimal("0.0050")

    pos_iqr = metric_map["positive_o2_depletion_iqr"]
    assert pos_iqr.sample_size == 93
    assert pos_iqr.numeric_value == Decimal("0.0070")

    # 4. Signed distribution (N=122)
    sig_med = metric_map["signed_distribution_o2_depletion_median"]
    assert sig_med.sample_size == 122
    assert sig_med.numeric_value == Decimal("0.0030")
    assert sig_med.parameters["negative_sensor_drift_records_preserved"] == 5
