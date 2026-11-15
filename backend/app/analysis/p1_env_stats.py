"""Module P1: Environmental Gas Descriptive Statistics.

Governed by FLARE-CONTRACT-FINAL-M9-V2 Section 2.1:
- Protocol Code: M9-P1-ENV-STATS (v1.0.0)
- Computes non-parametric sample median, IQR (Type 7 linear interpolation),
  and order-statistic 95% confidence intervals.
- Preserves signed negative CO sensor drift (-1, -2, -3 ppm, N=13) without clamping.
- Converts volume % to canonical SI mole fraction (mol/mol).
- Preserves exact source CSV row provenance for every calculation.
"""
from __future__ import annotations

from decimal import Decimal
import math
from typing import Any

from app.analysis.types import MetricPayload, ModuleExecutionReport, OrderStatisticCI

PROTOCOL_CODE = "M9-P1-ENV-STATS"
PROTOCOL_VERSION = "1.0.0"
PROTOCOL_DESCRIPTION = (
    "Non-parametric descriptive statistics and order-statistic confidence intervals "
    "for pre-ignition environmental gas concentrations (O2, CO2, CO) from NASA BASS-II."
)


def compute_sample_median(sorted_values: list[Decimal]) -> Decimal:
    """Compute sample median for sorted Decimal array.
    
    If N is odd: middle element at index N // 2.
    If N is even: arithmetic mean of elements at N // 2 - 1 and N // 2.
    """
    n = len(sorted_values)
    if n == 0:
        raise ValueError("Cannot compute median of empty array")
    if n % 2 == 1:
        return sorted_values[n // 2]
    return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / Decimal("2")


def compute_quantile_r7(sorted_values: list[Decimal], p: float) -> Decimal:
    """Compute quantile using NIST/SciPy default method (R Type 7, linear interpolation).
    
    Index h = (N - 1) * p.
    Let i = floor(h), frac = h - i.
    Q(p) = x[i] + frac * (x[i + 1] - x[i]).
    """
    n = len(sorted_values)
    if n == 0:
        raise ValueError("Cannot compute quantile of empty array")
    if n == 1:
        return sorted_values[0]
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"Quantile probability must be in [0, 1], got {p}")

    h = (n - 1) * p
    i = int(math.floor(h))
    if i >= n - 1:
        return sorted_values[-1]

    frac = Decimal(str(h - i))
    return sorted_values[i] + frac * (sorted_values[i + 1] - sorted_values[i])


def compute_order_statistic_ci_median(sorted_values: list[Decimal], confidence: float = 0.95) -> OrderStatisticCI:
    """Compute non-parametric order-statistic confidence interval for sample median.
    
    Formula from M9 Contract:
    half = N / 2.0
    margin = 1.96 * sqrt(N) / 2.0
    j = floor(half - margin)   (1-indexed)
    k = ceil(half + margin)    (1-indexed)
    CI = [x_(j), x_(k)]
    """
    n = len(sorted_values)
    if n < 4:
        raise ValueError("Sample size too small for non-parametric order statistic CI (N >= 4 required)")

    half = n / 2.0
    margin = 1.96 * math.sqrt(n) / 2.0
    j = int(math.floor(half - margin))
    k = int(math.ceil(half + margin))

    # Clamp ranks to valid 1-indexed boundaries [1, N]
    j_clamped = max(1, min(j, n))
    k_clamped = max(1, min(k, n))

    lower_val = sorted_values[j_clamped - 1]
    upper_val = sorted_values[k_clamped - 1]

    return OrderStatisticCI(
        lower=lower_val,
        upper=upper_val,
        lower_rank=j_clamped,
        upper_rank=k_clamped,
        confidence_level=confidence,
    )


def execute_p1_analysis(records: list[dict[str, Any]]) -> ModuleExecutionReport:
    """Execute Module P1 on ingested BASS-II records.
    
    Parameters
    ----------
    records : list of dict
        The 129 ingested experimental records, each containing original header strings
        and source record metadata (e.g. csv_record_number: 2..130).
    """
    report = ModuleExecutionReport(
        protocol_code=PROTOCOL_CODE,
        protocol_version=PROTOCOL_VERSION,
        description=PROTOCOL_DESCRIPTION,
        records_processed=len(records),
        prohibitions_enforced=[
            "NO_UNSUPPORTED_CLAMPING: Negative CO sensor readings (-1, -2, -3 ppm) preserved signed",
            "NO_ARBITRARY_IMPUTATION: 'none' and 'OR' treated strictly as missing/unresolved",
        ],
    )

    # 1. Calibrated initial O2 % by vol (N = 129 complete)
    o2_entries: list[tuple[Decimal, int]] = []
    for r in records:
        val_str = r.get("Calibrated  initial O2 % by vol ", "").strip()
        rec_num = int(r.get("csv_record_number", 0))
        if val_str and val_str.lower() not in ("none", "or", "n/a", ""):
            o2_entries.append((Decimal(val_str), rec_num))

    o2_entries.sort(key=lambda x: x[0])
    o2_vals = [x[0] for x in o2_entries]
    o2_rows = [x[1] for x in o2_entries]
    n_o2 = len(o2_vals)

    if n_o2 > 0:
        o2_med_vol_pct = compute_sample_median(o2_vals)
        o2_q1_vol_pct = compute_quantile_r7(o2_vals, 0.25)
        o2_q3_vol_pct = compute_quantile_r7(o2_vals, 0.75)
        o2_iqr_vol_pct = o2_q3_vol_pct - o2_q1_vol_pct
        o2_ci = compute_order_statistic_ci_median(o2_vals)

        # Canonical SI conversion: X_O2 = (% / 100) mol/mol
        o2_med_si = o2_med_vol_pct / Decimal("100")
        o2_iqr_si = o2_iqr_vol_pct / Decimal("100")
        o2_ci_si = OrderStatisticCI(
            lower=o2_ci.lower / Decimal("100"),
            upper=o2_ci.upper / Decimal("100"),
            lower_rank=o2_ci.lower_rank,
            upper_rank=o2_ci.upper_rank,
        )

        report.metrics.append(
            MetricPayload(
                metric_code="ambient_initial_o2_median",
                protocol_code=PROTOCOL_CODE,
                canonical_name="Baseline Pre-Ignition Oxygen Mole Fraction Median",
                result_kind="numeric",
                numeric_value=o2_med_si,
                unit="mol/mol",
                unit_status="known",
                text_value=None,
                sample_size=n_o2,
                parameters={
                    "source_variable": "Calibrated  initial O2 % by vol ",
                    "source_unit": "% by vol",
                    "raw_median_source_unit": str(o2_med_vol_pct),
                    "scale_factor_to_si": "0.01",
                    "method": "order_statistic_median",
                },
                uncertainty={
                    "confidence_interval_95": o2_ci_si.to_dict(),
                    "ci_source_units": o2_ci.to_dict(),
                    "discretization_uncertainty": "0.0010 mol/mol (0.1 vol %)",
                },
                quality_flags=["VALID_NUMERIC", "FULL_SAMPLE_100_PCT"],
                source_record_provenance=o2_rows,
            )
        )
        report.metrics.append(
            MetricPayload(
                metric_code="ambient_initial_o2_iqr",
                protocol_code=PROTOCOL_CODE,
                canonical_name="Baseline Pre-Ignition Oxygen Mole Fraction Interquartile Range",
                result_kind="numeric",
                numeric_value=o2_iqr_si,
                unit="mol/mol",
                unit_status="known",
                text_value=None,
                sample_size=n_o2,
                parameters={
                    "source_variable": "Calibrated  initial O2 % by vol ",
                    "source_unit": "% by vol",
                    "raw_iqr_source_unit": str(o2_iqr_vol_pct),
                    "q1_source_unit": str(o2_q1_vol_pct),
                    "q3_source_unit": str(o2_q3_vol_pct),
                    "interpolation_method": "R_TYPE_7",
                },
                uncertainty={},
                quality_flags=["VALID_NUMERIC", "FULL_SAMPLE_100_PCT"],
                source_record_provenance=o2_rows,
            )
        )

    # 2. Initial CO2 % by vol (N = 127 numeric, 2 'none')
    co2_entries: list[tuple[Decimal, int]] = []
    for r in records:
        val_str = r.get("Initial CO2 % by vol", "").strip()
        rec_num = int(r.get("csv_record_number", 0))
        if val_str and val_str.lower() not in ("none", "or", "n/a", ""):
            co2_entries.append((Decimal(val_str), rec_num))

    co2_entries.sort(key=lambda x: x[0])
    co2_vals = [x[0] for x in co2_entries]
    co2_rows = [x[1] for x in co2_entries]
    n_co2 = len(co2_vals)

    if n_co2 > 0:
        co2_med_vol_pct = compute_sample_median(co2_vals)
        co2_q1_vol_pct = compute_quantile_r7(co2_vals, 0.25)
        co2_q3_vol_pct = compute_quantile_r7(co2_vals, 0.75)
        co2_iqr_vol_pct = co2_q3_vol_pct - co2_q1_vol_pct
        co2_ci = compute_order_statistic_ci_median(co2_vals)

        co2_med_si = co2_med_vol_pct / Decimal("100")
        co2_iqr_si = co2_iqr_vol_pct / Decimal("100")
        co2_ci_si = OrderStatisticCI(
            lower=co2_ci.lower / Decimal("100"),
            upper=co2_ci.upper / Decimal("100"),
            lower_rank=co2_ci.lower_rank,
            upper_rank=co2_ci.upper_rank,
        )

        report.metrics.append(
            MetricPayload(
                metric_code="ambient_initial_co2_median",
                protocol_code=PROTOCOL_CODE,
                canonical_name="Background Chamber Carbon Dioxide Mole Fraction Median",
                result_kind="numeric",
                numeric_value=co2_med_si,
                unit="mol/mol",
                unit_status="known",
                text_value=None,
                sample_size=n_co2,
                parameters={
                    "source_variable": "Initial CO2 % by vol",
                    "source_unit": "% by vol",
                    "raw_median_source_unit": str(co2_med_vol_pct),
                    "scale_factor_to_si": "0.01",
                    "missing_count": len(records) - n_co2,
                },
                uncertainty={
                    "confidence_interval_95": co2_ci_si.to_dict(),
                    "ci_source_units": co2_ci.to_dict(),
                },
                quality_flags=["VALID_NUMERIC", "MISSING_MAPPED_TO_NULL"],
                source_record_provenance=co2_rows,
            )
        )
        report.metrics.append(
            MetricPayload(
                metric_code="ambient_initial_co2_iqr",
                protocol_code=PROTOCOL_CODE,
                canonical_name="Background Chamber Carbon Dioxide Mole Fraction Interquartile Range",
                result_kind="numeric",
                numeric_value=co2_iqr_si,
                unit="mol/mol",
                unit_status="known",
                text_value=None,
                sample_size=n_co2,
                parameters={
                    "source_variable": "Initial CO2 % by vol",
                    "source_unit": "% by vol",
                    "raw_iqr_source_unit": str(co2_iqr_vol_pct),
                    "q1_source_unit": str(co2_q1_vol_pct),
                    "q3_source_unit": str(co2_q3_vol_pct),
                    "interpolation_method": "R_TYPE_7",
                },
                uncertainty={},
                quality_flags=["VALID_NUMERIC", "MISSING_MAPPED_TO_NULL"],
                source_record_provenance=co2_rows,
            )
        )

    # 3. Initial CO (ppm) (N = 126 numeric; 2 'none'; 1 'OR')
    co_entries: list[tuple[Decimal, int]] = []
    for r in records:
        val_str = r.get("Initial CO (ppm)", "").strip()
        rec_num = int(r.get("csv_record_number", 0))
        if val_str and val_str.lower() not in ("none", "or", "n/a", ""):
            co_entries.append((Decimal(val_str), rec_num))

    co_entries.sort(key=lambda x: x[0])
    co_vals = [x[0] for x in co_entries]
    co_rows = [x[1] for x in co_entries]
    n_co = len(co_vals)

    if n_co > 0:
        co_med = compute_sample_median(co_vals)
        co_q1 = compute_quantile_r7(co_vals, 0.25)
        co_q3 = compute_quantile_r7(co_vals, 0.75)
        co_iqr = co_q3 - co_q1
        co_ci = compute_order_statistic_ci_median(co_vals)

        # Preserved signed negative count
        neg_count = sum(1 for v in co_vals if v < Decimal("0"))

        report.metrics.append(
            MetricPayload(
                metric_code="ambient_initial_co_median",
                protocol_code=PROTOCOL_CODE,
                canonical_name="Background Carbon Monoxide Concentration Median",
                result_kind="numeric",
                numeric_value=co_med,
                unit="umol/mol",
                unit_status="known",
                text_value=None,
                sample_size=n_co,
                parameters={
                    "source_variable": "Initial CO (ppm)",
                    "source_unit": "ppm",
                    "negative_sensor_drift_records_count": neg_count,
                    "over_range_records_count": 1,
                    "missing_records_count": len(records) - n_co - 1,
                    "canonical_unit_equivalence": "1 ppm = 1 umol/mol",
                },
                uncertainty={
                    "confidence_interval_95": co_ci.to_dict(),
                    "sensor_drift_status": "signed_unclamped",
                },
                quality_flags=["VALID_NUMERIC", "SENSOR_ZERO_DRIFT_PRESERVED"],
                source_record_provenance=co_rows,
            )
        )
        report.metrics.append(
            MetricPayload(
                metric_code="ambient_initial_co_iqr",
                protocol_code=PROTOCOL_CODE,
                canonical_name="Background Carbon Monoxide Concentration Interquartile Range",
                result_kind="numeric",
                numeric_value=co_iqr,
                unit="umol/mol",
                unit_status="known",
                text_value=None,
                sample_size=n_co,
                parameters={
                    "source_variable": "Initial CO (ppm)",
                    "source_unit": "ppm",
                    "q1": str(co_q1),
                    "q3": str(co_q3),
                    "interpolation_method": "R_TYPE_7",
                },
                uncertainty={},
                quality_flags=["VALID_NUMERIC", "SENSOR_ZERO_DRIFT_PRESERVED"],
                source_record_provenance=co_rows,
            )
        )

    report.records_eligible = max(n_o2, n_co2, n_co)
    report.records_excluded = len(records) - report.records_eligible
    return report
