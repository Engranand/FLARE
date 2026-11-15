"""Module P4: Observed Fuel Morphology & Specimen Grouping.

Governed by FLARE-CONTRACT-FINAL-M9-V2 Section 2.5:
- Protocol Code: M9-P4-FUEL-REGIMES (v1.0.0)
- Observed Morphological Regimes (N=129 flight runs, 107 unique physical specimens):
    1. CLEAR_PMMA_RODS_STAGNATION (27 runs, 20 unique specimens)
    2. BLACK_PMMA_RODS_OPPOSED (27 runs, 21 unique specimens)
    3. SIBAL_FABRIC_OPPOSED (27 runs, 22 unique specimens)
    4. THIN_PMMA_FILMS (22 runs, 20 unique specimens)
    5. THICK_PMMA_SLABS_UNSPECIFIED_MOUNT (14 runs, 14 unique specimens)
    6. THICK_PMMA_SLABS_1SIDED (5 runs, 5 unique specimens)
    7. NOMEX_III_FABRIC (3 runs, 3 unique specimens)
    8. PMMA_SPHERE_SEGMENT (2 runs, 1 unique specimen)
    9. CANDLE_WAX_WICK (1 run, 1 unique specimen)
    10. THICK_PMMA_SLABS_2SIDED (1 run, 1 unique specimen)
- Pseudoreplication & Specimen Tracking:
    - FIRST_BURN_SUBSET: N=107 runs (initial burn per physical specimen).
    - SUBSEQUENT_REBURN_SUBSET: N=22 runs (pre-ignited specimens).
    - 20 specimens burned multiple times across 42 runs; 87 burned once.
    - Confounder: shared unvented chamber air during GMT daily testing blocks.
- Explicit prohibitions:
    - NO Biot number calculations or inferences (Bi << 0.1 or Bi >> 1.0 strictly expunged).
    - NO logistic regression LOI modeling for thick slabs (zero low-oxygen runs, 20:0 balance).
    - NO flame spread rate (Vf) calculations (optical pixel/spatial tracking absent in CSV).
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.analysis.types import MetricPayload, ModuleExecutionReport

PROTOCOL_CODE = "M9-P4-FUEL-REGIMES"
PROTOCOL_VERSION = "1.0.0"
PROTOCOL_DESCRIPTION = (
    "Observed fuel morphology regime classification and specimen repeated-burn tracking "
    "across 129 BASS-II flight runs and 107 unique physical specimens without Biot inferences."
)


@dataclass(frozen=True)
class EvaluatedSpecimenRecord:
    """Classified morphology and specimen tracking record."""
    test_id: str
    csv_record_number: int
    pi: str
    sample_number: str
    fuel_sample_material: str
    regime_code: str
    regime_description: str
    observed_category: str
    flow_geometry: str
    burn_subset: str  # FIRST_BURN_SUBSET or SUBSEQUENT_REBURN_SUBSET
    is_repeated_sample: bool
    burn_sequence_index: int  # 1, 2, or 3
    repeated_sample_id_group: str | None


def classify_morphology_record(
    record: dict[str, Any],
    sample_seen_counts: dict[str, int],
    multi_burn_samples: set[str],
) -> EvaluatedSpecimenRecord:
    """Classify a record into its audited morphological regime and burn sequence."""
    test_id = str(record.get("Test #", "")).strip()
    rec_num = int(record.get("csv_record_number", 0))
    pi = str(record.get("PI", "")).strip()
    sample_num = str(record.get("Sample #", "")).strip()
    material = str(record.get("Fuel Sample Material", "")).strip()

    # Track burn sequence
    prior_burns = sample_seen_counts.get(sample_num, 0)
    current_burn_index = prior_burns + 1
    sample_seen_counts[sample_num] = current_burn_index

    burn_subset = "FIRST_BURN_SUBSET" if current_burn_index == 1 else "SUBSEQUENT_REBURN_SUBSET"
    is_repeated = sample_num in multi_burn_samples
    group_id = sample_num if is_repeated else None

    # Exact regime classification matching audited NASA PI assignments
    pi_clean = pi.lower().replace("'", "").strip()
    mat_lower = material.lower()

    if "olson" in pi_clean:
        regime = "CLEAR_PMMA_RODS_STAGNATION"
        desc = "Clear cast PMMA cylindrical rods (1/4, 3/8, 1/2 in) in stagnation/concurrent flow"
        cat = "Cylindrical Rod"
        geom = "stagnation_flow"
    elif "fernandez" in pi_clean or "pello" in pi_clean:
        regime = "BLACK_PMMA_RODS_OPPOSED"
        desc = "Black carbon-doped PMMA cylindrical rods (1/4, 3/8, 1/2 in) in opposed flow"
        cat = "Cylindrical Rod"
        geom = "opposed_flow"
    elif "bhattacharjee" in pi_clean:
        regime = "THIN_PMMA_FILMS"
        desc = "Cast PMMA thin films (100 to 400 um nominal thickness) in opposed flow"
        cat = "Thin Film"
        geom = "opposed_flow"
    elif "tien" in pi_clean:
        if "sphere" in mat_lower or "spherical" in mat_lower or test_id.lower() in ("t3", "t7"):
            regime = "PMMA_SPHERE_SEGMENT"
            desc = "Cast PMMA 4 cm spherical section in forced flow over sphere"
            cat = "Spherical Section"
            geom = "flow_over_sphere"
        else:
            regime = "SIBAL_FABRIC_OPPOSED"
            desc = "SIBAL fabric (75% cotton / 25% fiberglass woven blend) in opposed flow"
            cat = "Woven Fabric"
            geom = "opposed_flow"
    elif "ferkul" in pi_clean:
        if "candle" in mat_lower or "wax" in mat_lower or test_id.lower() == "f4":
            regime = "CANDLE_WAX_WICK"
            desc = "Japan Wax paraffin candle with cotton wick in coflow diffusion"
            cat = "Candle Wax"
            geom = "coflow_diffusion"
        else:
            regime = "NOMEX_III_FABRIC"
            desc = "Nomex III natural aramid woven fabric in opposed flow"
            cat = "Woven Fabric"
            geom = "opposed_flow"
    elif "miller" in pi_clean:
        if "1-sided" in mat_lower or "1 sided" in mat_lower or test_id.lower() in ("m1", "m2", "m3", "m14", "m15"):
            regime = "THICK_PMMA_SLABS_1SIDED"
            desc = "Cast PMMA slabs (1 to 5 mm) with 1-sided phenolic mount in opposed flow"
            cat = "Thick Slab"
            geom = "opposed_flow"
        elif "2-sided" in mat_lower or "2 sided" in mat_lower or test_id.lower() == "m5":
            regime = "THICK_PMMA_SLABS_2SIDED"
            desc = "Cast PMMA slab (3 mm) with 2-sided unbacked free burn in opposed flow"
            cat = "Thick Slab"
            geom = "opposed_flow"
        else:
            regime = "THICK_PMMA_SLABS_UNSPECIFIED_MOUNT"
            desc = "Cast PMMA slabs (1 to 5 mm) with mounting unspecified in tabular CSV"
            cat = "Thick Slab"
            geom = "opposed_flow"
    else:
        regime = "UNRESOLVED_MORPHOLOGY"
        desc = "Unresolved specimen morphology"
        cat = "Unknown"
        geom = "unknown"

    return EvaluatedSpecimenRecord(
        test_id=test_id,
        csv_record_number=rec_num,
        pi=pi,
        sample_number=sample_num,
        fuel_sample_material=material,
        regime_code=regime,
        regime_description=desc,
        observed_category=cat,
        flow_geometry=geom,
        burn_subset=burn_subset,
        is_repeated_sample=is_repeated,
        burn_sequence_index=current_burn_index,
        repeated_sample_id_group=group_id,
    )


def execute_p4_analysis(records: list[dict[str, Any]]) -> ModuleExecutionReport:
    """Execute Module P4 on ingested BASS-II records."""
    report = ModuleExecutionReport(
        protocol_code=PROTOCOL_CODE,
        protocol_version=PROTOCOL_VERSION,
        description=PROTOCOL_DESCRIPTION,
        records_processed=len(records),
        prohibitions_enforced=[
            "EXPUNGED_BIOT_NUMBERS: All Biot number calculations and regime inferences (Bi << 0.1, Bi >> 1.0) strictly expunged",
            "PROHIBITED_LOI_LOGISTIC_REGRESSION: Flammability logistic regression on slabs prohibited due to 20:0 class balance",
            "PROHIBITED_FLAME_SPREAD: Flame spread velocity (Vf) prohibited due to absence of spatial coordinates in CSV",
            "TRANSPARENT_PSEUDOREPLICATION: Separate reporting of 129 runs vs 107 unique specimens with unvented chamber covariate note",
        ],
    )

    # First pass: identify unique samples and multi-burn samples
    sample_counts = Counter(str(r.get("Sample #", "")).strip() for r in records)
    multi_burn_samples = {s for s, c in sample_counts.items() if c > 1}
    unique_samples = set(sample_counts.keys())

    # Second pass: classify in chronological / row order
    sample_seen_counts: dict[str, int] = {}
    classified: list[EvaluatedSpecimenRecord] = []
    for r in records:
        rec = classify_morphology_record(r, sample_seen_counts, multi_burn_samples)
        classified.append(rec)

    first_burns = [r for r in classified if r.burn_subset == "FIRST_BURN_SUBSET"]
    re_burns = [r for r in classified if r.burn_subset == "SUBSEQUENT_REBURN_SUBSET"]

    regime_counter = Counter(r.regime_code for r in classified)
    category_counter = Counter(r.observed_category for r in classified)

    report.records_eligible = len(classified)
    report.records_excluded = 0

    report.metadata["specimen_counts"] = {
        "total_experimental_runs": len(classified),
        "unique_physical_specimens": len(unique_samples),
        "single_burn_specimens": len(unique_samples) - len(multi_burn_samples),
        "repeated_burn_specimens": len(multi_burn_samples),
        "first_burn_subset_runs": len(first_burns),
        "subsequent_reburn_subset_runs": len(re_burns),
    }
    report.metadata["regime_distribution"] = dict(regime_counter)
    report.metadata["observed_categories"] = dict(category_counter)

    # 1. Metric: Total Flight Runs Count
    all_rows = [r.csv_record_number for r in classified]
    report.metrics.append(
        MetricPayload(
            metric_code="total_flight_runs_count",
            protocol_code=PROTOCOL_CODE,
            canonical_name="Total Ingested BASS-II Flight Test Runs",
            result_kind="numeric",
            numeric_value=Decimal(str(len(classified))),
            unit="count",
            unit_status="known",
            text_value=None,
            sample_size=len(classified),
            parameters={
                "dataset": "NASA PSI-25 / BASS-II",
                "unique_specimens_count": len(unique_samples),
            },
            uncertainty={},
            quality_flags=["FLIGHT_RECORDS_COMPLETE", "NASA_PSI_25"],
            source_record_provenance=all_rows,
        )
    )

    # 2. Metric: Unique Physical Specimens Count
    report.metrics.append(
        MetricPayload(
            metric_code="unique_physical_specimens_count",
            protocol_code=PROTOCOL_CODE,
            canonical_name="Unique Physical Fuel Specimens Tested",
            result_kind="numeric",
            numeric_value=Decimal(str(len(unique_samples))),
            unit="count",
            unit_status="known",
            text_value=None,
            sample_size=len(unique_samples),
            parameters={
                "single_burn_specimens": len(unique_samples) - len(multi_burn_samples),
                "multi_burn_specimens": len(multi_burn_samples),
                "first_burn_subset_count": len(first_burns),
                "subsequent_reburn_subset_count": len(re_burns),
            },
            uncertainty={
                "statistical_independence_caveat": (
                    "First burn subset (N=107) does not establish statistical independence; "
                    "shared unvented glovebox chamber accumulated CO (up to 950 ppm) and CO2 (up to 1.9%)."
                ),
            },
            quality_flags=["PSEUDOREPLICATION_RESOLVED", "SPECIMEN_TRACKING"],
            source_record_provenance=all_rows,
        )
    )

    # 3. Metric: First Burn Subset Count
    first_rows = [r.csv_record_number for r in first_burns]
    report.metrics.append(
        MetricPayload(
            metric_code="first_burn_subset_runs_count",
            protocol_code=PROTOCOL_CODE,
            canonical_name="First Burn Experimental Runs Count (Virgin Specimens)",
            result_kind="numeric",
            numeric_value=Decimal(str(len(first_burns))),
            unit="count",
            unit_status="known",
            text_value=None,
            sample_size=len(first_burns),
            parameters={
                "subset_name": "FIRST_BURN_SUBSET",
                "description": "Initial experimental burn for each of the 107 unique physical fuel specimens",
            },
            uncertainty={},
            quality_flags=["FIRST_BURN_SUBSET", "INITIAL_IGNITION"],
            source_record_provenance=first_rows,
        )
    )

    # 4. Metric: Subsequent Re-Burn Subset Count
    reburn_rows = [r.csv_record_number for r in re_burns]
    report.metrics.append(
        MetricPayload(
            metric_code="subsequent_reburn_subset_runs_count",
            protocol_code=PROTOCOL_CODE,
            canonical_name="Subsequent Re-Burn Experimental Runs Count (Pre-Burned Specimens)",
            result_kind="numeric",
            numeric_value=Decimal(str(len(re_burns))),
            unit="count",
            unit_status="known",
            text_value=None,
            sample_size=len(re_burns),
            parameters={
                "subset_name": "SUBSEQUENT_REBURN_SUBSET",
                "repeated_specimens_count": len(multi_burn_samples),
                "description": "Tests on previously ignited specimens with altered sample lengths or preheating",
            },
            uncertainty={},
            quality_flags=["REBURN_SUBSET", "THERMAL_HISTORY_CONFOUNDER"],
            source_record_provenance=reburn_rows,
        )
    )

    # 5. Metric: Observed Morphological Regime Breakdown Summary
    regime_summary = {k: v for k, v in regime_counter.most_common()}
    report.metrics.append(
        MetricPayload(
            metric_code="observed_morphology_regimes_summary",
            protocol_code=PROTOCOL_CODE,
            canonical_name="Observed Fuel Morphology Regimes Distribution",
            result_kind="text",
            numeric_value=None,
            unit="distribution",
            unit_status="known",
            text_value=str(regime_summary),
            sample_size=len(classified),
            parameters={
                "regime_counts": regime_summary,
                "biot_number_status": "EXPUNGED",
                "metrology_basis": "Nominal dimensions and observed geometry as documented by NASA PIs",
            },
            uncertainty={},
            quality_flags=["CATEGORICAL_METADATA", "NO_BIOT_CALCULATION"],
            source_record_provenance=all_rows,
        )
    )

    return report
