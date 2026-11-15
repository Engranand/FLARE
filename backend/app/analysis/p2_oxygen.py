"""Module P2: Relative Oxygen Depletion Analysis.

Governed by FLARE-CONTRACT-FINAL-M9-V2 Section 2.2 and 2.3:
- Protocol Code: M9-P2-O2-DEPLETION (v1.0.0)
- Computes relative oxygen depletion metrics:
    Delta X_O2 = X_init - X_final [% by vol]
    Delta chi_O2 = Delta X_O2 / 100.0 [mol/mol]
    Pi_O2 = (X_init - X_final) / X_init [dimensionless]
- Disjoint partitioning across 129 records:
    1. POSITIVE_DEPLETION (N=93): +0.1% to +3.2%
    2. ZERO_DEPLETION (N=24): exactly 0.0%
       (Non-negative subtotal: N=117)
    3. NEGATIVE_SENSOR_DRIFT (N=5): exactly -0.1%, preserved signed as Decimal('-0.0010') mol/mol
       (Reconciled valid signed subtotal: N=122)
    4. QUARANTINED_GROSS_ANOMALY (N=5): |Delta X| > 19% (B2, P22a, P22b, T28a, T28b) - EXCLUDED
    5. MISSING_FINAL_O2 (N=2): final O2 is 'none' (B14, F3) - EXCLUDED
- Explicit scientific boundaries:
    - RQ_comb is EXPLICITLY DEFERRED (division-by-zero on 24 runs, sensor asynchrony, 100% noise).
    - Absolute molar balance (Delta n_O2) is PROHIBITED (missing P, T, displaced volume).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal

from app.analysis.p1_env_stats import (
    compute_order_statistic_ci_median,
    compute_quantile_r7,
    compute_sample_median,
)
from app.analysis.types import MetricPayload, ModuleExecutionReport, OrderStatisticCI

PROTOCOL_CODE = "M9-P2-O2-DEPLETION"
PROTOCOL_VERSION = "1.0.0"
PROTOCOL_DESCRIPTION = (
    "Deterministic relative oxygen depletion analysis across 129 BASS-II flight records. "
    "Partitions records into non-negative, signed drift, quarantined anomalies, and missing."
)

QUARANTINED_TEST_IDS = frozenset({"B2", "P22a", "P22b", "T28a", "T28b"})
NEGATIVE_DRIFT_TEST_IDS = frozenset({"T5", "T10", "T12", "T13", "T23"})


@dataclass(frozen=True)
class EvaluatedOxygenRecord:
    """Classified and evaluated oxygen record."""
    test_id: str
    csv_record_number: int
    initial_o2_vol_pct: Decimal
    final_o2_vol_pct: Decimal | None
    delta_o2_vol_pct: Decimal | None
    delta_o2_mol_fraction: Decimal | None
    relative_ratio_pi: Decimal | None
    category: Literal[
        "POSITIVE_DEPLETION",
        "ZERO_DEPLETION",
        "NEGATIVE_SENSOR_DRIFT",
        "QUARANTINED_GROSS_ANOMALY",
        "MISSING_FINAL_O2",
    ]
    is_eligible_standard: bool
    is_eligible_signed_cdf: bool
    exclusion_reason: str | None


def classify_oxygen_record(record: dict[str, Any]) -> EvaluatedOxygenRecord:
    """Classify a single BASS-II record into its audited P2 eligibility category."""
    test_id = str(record.get("Test #", "")).strip()
    rec_num = int(record.get("csv_record_number", 0))

    init_str = str(record.get("Calibrated  initial O2 % by vol ", "")).strip()
    final_str = str(record.get("Calibrated final O2 % by vol", "")).strip()

    if not init_str or init_str.lower() in ("none", "n/a", ""):
        raise ValueError(f"Record {test_id} has invalid initial O2: {init_str!r}")

    init_val = Decimal(init_str)

    # Check for missing final O2
    if not final_str or final_str.lower() in ("none", "n/a", ""):
        return EvaluatedOxygenRecord(
            test_id=test_id,
            csv_record_number=rec_num,
            initial_o2_vol_pct=init_val,
            final_o2_vol_pct=None,
            delta_o2_vol_pct=None,
            delta_o2_mol_fraction=None,
            relative_ratio_pi=None,
            category="MISSING_FINAL_O2",
            is_eligible_standard=False,
            is_eligible_signed_cdf=False,
            exclusion_reason="Final O2 measurement unrecorded ('none')",
        )

    final_val = Decimal(final_str)
    delta_vol_pct = init_val - final_val
    delta_mol_fraction = delta_vol_pct / Decimal("100")
    pi = delta_vol_pct / init_val

    # Check for quarantined gross recording anomalies
    if test_id in QUARANTINED_TEST_IDS or abs(delta_vol_pct) > Decimal("19.0"):
        return EvaluatedOxygenRecord(
            test_id=test_id,
            csv_record_number=rec_num,
            initial_o2_vol_pct=init_val,
            final_o2_vol_pct=final_val,
            delta_o2_vol_pct=delta_vol_pct,
            delta_o2_mol_fraction=delta_mol_fraction,
            relative_ratio_pi=pi,
            category="QUARANTINED_GROSS_ANOMALY",
            is_eligible_standard=False,
            is_eligible_signed_cdf=False,
            exclusion_reason=f"Gross recording anomaly (|Delta O2| = {delta_vol_pct}% > 19%)",
        )

    # Check for resolution-limited negative drift
    if delta_vol_pct < Decimal("0.0"):
        return EvaluatedOxygenRecord(
            test_id=test_id,
            csv_record_number=rec_num,
            initial_o2_vol_pct=init_val,
            final_o2_vol_pct=final_val,
            delta_o2_vol_pct=delta_vol_pct,
            delta_o2_mol_fraction=delta_mol_fraction,
            relative_ratio_pi=pi,
            category="NEGATIVE_SENSOR_DRIFT",
            is_eligible_standard=False,
            is_eligible_signed_cdf=True,
            exclusion_reason="Negative sensor zero-drift (-0.1 vol %); excluded from non-negative depletion",
        )

    # Check for zero depletion
    if delta_vol_pct == Decimal("0.0"):
        return EvaluatedOxygenRecord(
            test_id=test_id,
            csv_record_number=rec_num,
            initial_o2_vol_pct=init_val,
            final_o2_vol_pct=final_val,
            delta_o2_vol_pct=delta_vol_pct,
            delta_o2_mol_fraction=delta_mol_fraction,
            relative_ratio_pi=Decimal("0.0"),
            category="ZERO_DEPLETION",
            is_eligible_standard=True,
            is_eligible_signed_cdf=True,
            exclusion_reason=None,
        )

    # Positive depletion
    return EvaluatedOxygenRecord(
        test_id=test_id,
        csv_record_number=rec_num,
        initial_o2_vol_pct=init_val,
        final_o2_vol_pct=final_val,
        delta_o2_vol_pct=delta_vol_pct,
        delta_o2_mol_fraction=delta_mol_fraction,
        relative_ratio_pi=pi,
        category="POSITIVE_DEPLETION",
        is_eligible_standard=True,
        is_eligible_signed_cdf=True,
        exclusion_reason=None,
    )


def execute_p2_analysis(records: list[dict[str, Any]]) -> ModuleExecutionReport:
    """Execute Module P2 on ingested BASS-II records."""
    report = ModuleExecutionReport(
        protocol_code=PROTOCOL_CODE,
        protocol_version=PROTOCOL_VERSION,
        description=PROTOCOL_DESCRIPTION,
        records_processed=len(records),
        prohibitions_enforced=[
            "EXPLICIT_DEFERRAL: RQ_comb deferred due to division-by-zero on 24 runs and sensor asynchrony",
            "PROHIBITED_METRIC: Absolute molar consumption (Delta n_O2) prohibited due to missing P, T, V",
            "NO_UNSUPPORTED_CLAMPING: 5 negative sensor drift records preserved signed as -0.0010 mol/mol",
            "MANDATORY_QUARANTINE: 5 gross recording anomalies (|Delta O2| > 19%) strictly quarantined",
        ],
    )

    classified = [classify_oxygen_record(r) for r in records]

    # Partitions
    positive_recs = [r for r in classified if r.category == "POSITIVE_DEPLETION"]
    zero_recs = [r for r in classified if r.category == "ZERO_DEPLETION"]
    drift_recs = [r for r in classified if r.category == "NEGATIVE_SENSOR_DRIFT"]
    anomaly_recs = [r for r in classified if r.category == "QUARANTINED_GROSS_ANOMALY"]
    missing_recs = [r for r in classified if r.category == "MISSING_FINAL_O2"]

    non_negative_recs = positive_recs + zero_recs
    signed_valid_recs = non_negative_recs + drift_recs

    report.metadata["category_counts"] = {
        "POSITIVE_DEPLETION": len(positive_recs),
        "ZERO_DEPLETION": len(zero_recs),
        "NON_NEGATIVE_SUBTOTAL": len(non_negative_recs),
        "NEGATIVE_SENSOR_DRIFT": len(drift_recs),
        "SIGNED_VALID_SUBTOTAL": len(signed_valid_recs),
        "QUARANTINED_GROSS_ANOMALY": len(anomaly_recs),
        "MISSING_FINAL_O2": len(missing_recs),
        "TOTAL_PROCESSED": len(classified),
    }

    report.records_eligible = len(non_negative_recs)
    report.records_excluded = len(anomaly_recs) + len(missing_recs)

    # 1. Non-Negative Depletion (N = 117)
    if non_negative_recs:
        nn_sorted = sorted(non_negative_recs, key=lambda x: x.delta_o2_mol_fraction)
        nn_deltas = [x.delta_o2_mol_fraction for x in nn_sorted]
        nn_rows = [x.csv_record_number for x in nn_sorted]
        n_nn = len(nn_deltas)

        nn_med = compute_sample_median(nn_deltas)
        nn_q1 = compute_quantile_r7(nn_deltas, 0.25)
        nn_q3 = compute_quantile_r7(nn_deltas, 0.75)
        nn_iqr = nn_q3 - nn_q1
        nn_ci = compute_order_statistic_ci_median(nn_deltas)

        report.metrics.append(
            MetricPayload(
                metric_code="non_negative_o2_depletion_median",
                protocol_code=PROTOCOL_CODE,
                canonical_name="Non-Negative Oxygen Mole Fraction Depletion Median",
                result_kind="numeric",
                numeric_value=nn_med,
                unit="mol/mol",
                unit_status="known",
                text_value=None,
                sample_size=n_nn,
                parameters={
                    "subset": "NON_NEGATIVE_DEPLETION",
                    "includes_zero_depletion": True,
                    "zero_depletion_count": len(zero_recs),
                    "positive_depletion_count": len(positive_recs),
                    "min_delta_mol_fraction": str(nn_deltas[0]),
                    "max_delta_mol_fraction": str(nn_deltas[-1]),
                },
                uncertainty={
                    "confidence_interval_95": nn_ci.to_dict(),
                    "discretization_uncertainty": "0.0010 mol/mol",
                },
                quality_flags=["NON_NEGATIVE_SUBSET", "AUDITED_VALID"],
                source_record_provenance=nn_rows,
            )
        )
        report.metrics.append(
            MetricPayload(
                metric_code="non_negative_o2_depletion_iqr",
                protocol_code=PROTOCOL_CODE,
                canonical_name="Non-Negative Oxygen Mole Fraction Depletion Interquartile Range",
                result_kind="numeric",
                numeric_value=nn_iqr,
                unit="mol/mol",
                unit_status="known",
                text_value=None,
                sample_size=n_nn,
                parameters={
                    "subset": "NON_NEGATIVE_DEPLETION",
                    "q1": str(nn_q1),
                    "q3": str(nn_q3),
                    "interpolation_method": "R_TYPE_7",
                },
                uncertainty={},
                quality_flags=["NON_NEGATIVE_SUBSET", "AUDITED_VALID"],
                source_record_provenance=nn_rows,
            )
        )

        # Relative Oxygen Depletion Ratio Pi_O2 for N=117
        nn_pi_sorted = sorted([x.relative_ratio_pi for x in non_negative_recs])
        nn_pi_med = compute_sample_median(nn_pi_sorted)
        nn_pi_q1 = compute_quantile_r7(nn_pi_sorted, 0.25)
        nn_pi_q3 = compute_quantile_r7(nn_pi_sorted, 0.75)
        nn_pi_iqr = nn_pi_q3 - nn_pi_q1

        report.metrics.append(
            MetricPayload(
                metric_code="relative_o2_depletion_ratio_median",
                protocol_code=PROTOCOL_CODE,
                canonical_name="Relative Oxygen Depletion Ratio Median (Non-Negative Subset)",
                result_kind="numeric",
                numeric_value=nn_pi_med,
                unit=None,
                unit_status="not_applicable",
                text_value=None,
                sample_size=n_nn,
                parameters={
                    "formula": "Pi_O2 = (X_init - X_final) / X_init",
                    "subset": "NON_NEGATIVE_DEPLETION",
                    "q1": str(nn_pi_q1),
                    "q3": str(nn_pi_q3),
                    "iqr": str(nn_pi_iqr),
                },
                uncertainty={},
                quality_flags=["DIMENSIONLESS_RATIO", "NON_NEGATIVE_SUBSET"],
                source_record_provenance=nn_rows,
            )
        )

    # 2. Positive-Only Depletion (N = 93)
    if positive_recs:
        pos_sorted = sorted(positive_recs, key=lambda x: x.delta_o2_mol_fraction)
        pos_deltas = [x.delta_o2_mol_fraction for x in pos_sorted]
        pos_rows = [x.csv_record_number for x in pos_sorted]
        n_pos = len(pos_deltas)

        pos_med = compute_sample_median(pos_deltas)
        pos_q1 = compute_quantile_r7(pos_deltas, 0.25)
        pos_q3 = compute_quantile_r7(pos_deltas, 0.75)
        pos_iqr = pos_q3 - pos_q1
        pos_ci = compute_order_statistic_ci_median(pos_deltas)

        report.metrics.append(
            MetricPayload(
                metric_code="positive_o2_depletion_median",
                protocol_code=PROTOCOL_CODE,
                canonical_name="Positive Oxygen Mole Fraction Depletion Median",
                result_kind="numeric",
                numeric_value=pos_med,
                unit="mol/mol",
                unit_status="known",
                text_value=None,
                sample_size=n_pos,
                parameters={
                    "subset": "POSITIVE_DEPLETION",
                    "min_delta_mol_fraction": str(pos_deltas[0]),
                    "max_delta_mol_fraction": str(pos_deltas[-1]),
                },
                uncertainty={
                    "confidence_interval_95": pos_ci.to_dict(),
                    "discretization_uncertainty": "0.0010 mol/mol",
                },
                quality_flags=["POSITIVE_SUBSET", "AUDITED_VALID"],
                source_record_provenance=pos_rows,
            )
        )
        report.metrics.append(
            MetricPayload(
                metric_code="positive_o2_depletion_iqr",
                protocol_code=PROTOCOL_CODE,
                canonical_name="Positive Oxygen Mole Fraction Depletion Interquartile Range",
                result_kind="numeric",
                numeric_value=pos_iqr,
                unit="mol/mol",
                unit_status="known",
                text_value=None,
                sample_size=n_pos,
                parameters={
                    "subset": "POSITIVE_DEPLETION",
                    "q1": str(pos_q1),
                    "q3": str(pos_q3),
                    "interpolation_method": "R_TYPE_7",
                },
                uncertainty={},
                quality_flags=["POSITIVE_SUBSET", "AUDITED_VALID"],
                source_record_provenance=pos_rows,
            )
        )

    # 3. Signed Distribution (N = 122 reconciled valid records, including signed drift)
    if signed_valid_recs:
        sig_sorted = sorted(signed_valid_recs, key=lambda x: x.delta_o2_mol_fraction)
        sig_deltas = [x.delta_o2_mol_fraction for x in sig_sorted]
        sig_rows = [x.csv_record_number for x in sig_sorted]
        n_sig = len(sig_deltas)

        sig_med = compute_sample_median(sig_deltas)
        sig_q1 = compute_quantile_r7(sig_deltas, 0.25)
        sig_q3 = compute_quantile_r7(sig_deltas, 0.75)
        sig_iqr = sig_q3 - sig_q1
        sig_ci = compute_order_statistic_ci_median(sig_deltas)

        report.metrics.append(
            MetricPayload(
                metric_code="signed_distribution_o2_depletion_median",
                protocol_code=PROTOCOL_CODE,
                canonical_name="Complete Signed Empirical Oxygen Depletion Median",
                result_kind="numeric",
                numeric_value=sig_med,
                unit="mol/mol",
                unit_status="known",
                text_value=None,
                sample_size=n_sig,
                parameters={
                    "subset": "SIGNED_VALID_CDF",
                    "negative_sensor_drift_records_preserved": len(drift_recs),
                    "zero_depletion_records": len(zero_recs),
                    "positive_depletion_records": len(positive_recs),
                    "quarantined_records_excluded": len(anomaly_recs),
                    "missing_records_excluded": len(missing_recs),
                    "min_signed_delta": str(sig_deltas[0]),
                    "max_signed_delta": str(sig_deltas[-1]),
                },
                uncertainty={
                    "confidence_interval_95": sig_ci.to_dict(),
                    "sensor_drift_preserved": True,
                },
                quality_flags=["SIGNED_COMPLETE_DISTRIBUTION", "UNCLAMPED_DRIFT_INCLUDED"],
                source_record_provenance=sig_rows,
            )
        )

    return report
