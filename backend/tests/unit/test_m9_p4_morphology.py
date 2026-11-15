"""Unit tests for FLARE M9 Module P4: Observed Fuel Morphology & Specimen Grouping.

Governed by FLARE-CONTRACT-FINAL-M9-V2 Section 2.5.
"""
from collections import Counter
from decimal import Decimal
import pytest

from app.analysis.engine import load_authenticated_records
from app.analysis.p4_morphology import execute_p4_analysis


def test_p4_execution_on_authenticated_records():
    records = load_authenticated_records()
    assert len(records) == 129

    report = execute_p4_analysis(records)
    assert report.protocol_code == "M9-P4-FUEL-REGIMES"
    assert report.records_processed == 129
    assert report.records_eligible == 129
    assert report.records_excluded == 0

    metric_map = {m.metric_code: m for m in report.metrics}

    # 1. Total flight runs count
    runs_count = metric_map["total_flight_runs_count"]
    assert runs_count.numeric_value == Decimal("129")
    assert len(runs_count.source_record_provenance) == 129

    # 2. Unique specimens count
    spec_count = metric_map["unique_physical_specimens_count"]
    assert spec_count.numeric_value == Decimal("107")
    assert spec_count.parameters["single_burn_specimens"] == 87
    assert spec_count.parameters["multi_burn_specimens"] == 20

    # 3. First burn subset count
    first_burns = metric_map["first_burn_subset_runs_count"]
    assert first_burns.numeric_value == Decimal("107")
    assert len(first_burns.source_record_provenance) == 107

    # 4. Subsequent re-burn subset count
    reburns = metric_map["subsequent_reburn_subset_runs_count"]
    assert reburns.numeric_value == Decimal("22")
    assert len(reburns.source_record_provenance) == 22

    # Check sum of first burns and reburns
    assert first_burns.numeric_value + reburns.numeric_value == runs_count.numeric_value

    # 5. Regime breakdown counts
    regimes = report.metadata["regime_distribution"]
    assert regimes["CLEAR_PMMA_RODS_STAGNATION"] == 27
    assert regimes["BLACK_PMMA_RODS_OPPOSED"] == 27
    assert regimes["SIBAL_FABRIC_OPPOSED"] == 27
    assert regimes["THIN_PMMA_FILMS"] == 22
    assert regimes["THICK_PMMA_SLABS_UNSPECIFIED_MOUNT"] == 14
    assert regimes["THICK_PMMA_SLABS_1SIDED"] == 5
    assert regimes["NOMEX_III_FABRIC"] == 3
    assert regimes["PMMA_SPHERE_SEGMENT"] == 2
    assert regimes["CANDLE_WAX_WICK"] == 1
    assert regimes["THICK_PMMA_SLABS_2SIDED"] == 1
    assert sum(regimes.values()) == 129


def test_biot_number_expunged():
    records = load_authenticated_records()
    report = execute_p4_analysis(records)

    # Assert Biot numbers are completely absent from all metrics and parameters
    for m in report.metrics:
        assert "biot" not in m.canonical_name.lower()
        assert "biot" not in m.metric_code.lower()
        if m.parameters:
            for k in m.parameters:
                assert "biot_number" not in k.lower() or m.parameters[k] == "EXPUNGED"
