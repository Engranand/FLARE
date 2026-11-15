# FLARE Milestone 9: Scientific Audit Reconciliation Report

**Document Identifier:** `FLARE-RECON-SCI-M9-V1`  
**Classification:** Scientific Data Audit & Physical Reconciliation (Read-Only)  
**Auditor:** Independent Scientific Data Auditor  
**Project:** FLARE (Scientific Intelligence Platform for Spacecraft Fire Safety)  
**Target Investigation:** NASA PSI-25 / BASS-II (`PSI-25_Experimental table_BASS-II.csv`)  
**Date:** November 2026  
**Audit Status:** SCIENTIFIC FINDINGS FULLY RECONCILED  

---

## 1. Overview & Objectives

This report provides a formal, evidence-backed reconciliation of the scientific discrepancies and empirical anomalies identified in the Milestone 9 (M9) pre-implementation review. Every metric, range, and record cited herein was re-verified via direct programmatic inspection of the authentic primary data files.

---

## 2. Itemized Verification of Critical Findings

### 2.1 Carbon Monoxide (CO) Concentrations & Sensor Saturation
- **Original M9 Specification Claim:** `Initial CO` ranges from $-3$ to $12\text{ ppm}$; `Final CO` ranges from $-4$ to $40\text{ ppm}$.
- **Reconciled Empirical Ground Truth:**
  - **`Initial CO (ppm)` (129 rows):**
    - 2 missing/unreported entries (literal `'none'`).
    - 1 over-range entry (literal `'OR'`).
    - 126 numeric entries spanning **$-3.0\text{ to }950.0\text{ ppm}$**.
    - Exactly **13 records report negative readings**: `-1` (11 rows), `-2` (1 row), `-3` (1 row).
    - Exactly **22 records report initial concentrations $\ge 100\text{ ppm}$**.
  - **`Final CO (ppm)` (129 rows):**
    - 1 empty string and 4 literal `'none'` entries (5 total null/unreported).
    - 4 saturation entries: literal `'>500'` (1 row), `'over'` (1 row), and `'OR'` (2 rows).
    - 120 numeric entries spanning **$0.3\text{ to }950.0\text{ ppm}$**.
    - Exactly **0 records report negative readings** in `Final CO`.
    - Exactly **58 records report post-burn concentrations $\ge 100\text{ ppm}$**.
- **Physical Explanation:** The Microgravity Science Glovebox (MSG) is a sealed 255-liter volume that was not purged between sequential runs during daily testing sessions. Combustion byproducts accumulated continuously throughout the crew shift. Saturated readings reflect severe incomplete combustion in oxygen-depleted runs.

---

### 2.2 Paired Oxygen Observations & Gross Recording Anomalies
Across the 129 flight records, initial and final calibrated oxygen concentrations were evaluated:
- Total records with paired numeric $O_2$ readings: **127 records** (2 records contain `'none'` in Final $O_2$: Test `B14` and Test `F3`).
- **The Five Gross Recording Anomalies:**
  Five records exhibit extreme differences ($|\Delta X_{O2}| > 19\%$) caused by operational data recording errors, subtest splits, or column shifts:

| Test ID | PI | Fuel Sample Material | Initial $O_2$ (%) | Final $O_2$ (%) | Raw $\Delta X_{O2}$ | Discovered Root Cause in Source Files |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **`B2`** | Bhattacharjee | 200 $\mu\text{m}$ PMMA film | 22.2 | 1.6 | **+20.6%** | Final $O_2$ of `1.6` was recorded in place of $\Delta O_2$ or sensor voltage. |
| **`P22a`** | Fernandez-Pello | 3/8" black PMMA rod | 20.8 | 0.6 | **+20.2%** | Final $O_2$ of `0.6` was recorded in place of depletion amount $\Delta O_2$. |
| **`P22b`** | Fernandez-Pello | 3/8" black PMMA rod | 20.0 | 39.1 | **-19.1%** | Sensor millivolt telemetry or duration (`39.1`) shifted into $O_2$ column. |
| **`T28a`** | T'ien | 1 cm SIBAL fabric | 20.7 | 0.9 | **+19.8%** | Final $O_2$ of `0.9` represents depletion amount $\Delta O_2$. |
| **`T28b`** | T'ien | 1 cm SIBAL fabric | 20.7 | 40.4 | **-19.7%** | Radiometer/sensor readout (`40.4`) shifted into $O_2$ column. |

**Audit Action:** These five records are **strictly quarantined** and must be excluded from all quantitative gas depletion calculations.

---

### 2.3 Negative Oxygen Depletion Records (Sensor Thermal Drift)
Five SIBAL fabric tests exhibit apparent negative consumption ($\Delta X_{O2} = -0.1\%$):

| Test ID | PI | Fuel Sample Material | Initial $O_2$ (%) | Final $O_2$ (%) | Apparent $\Delta X_{O2}$ | Physical Explanation |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **`T5`** | T'ien | 2 cm SIBAL | 18.8 | 18.9 | **-0.1%** | Electrochemical sensor zero-point drift & temperature change |
| **`T10`** | T'ien | 2 cm SIBAL | 16.4 | 16.5 | **-0.1%** | Instrument resolution limit ($\pm 0.1\%$) |
| **`T12`** | T'ien | 2 cm SIBAL | 16.8 | 16.9 | **-0.1%** | Instrument resolution limit ($\pm 0.1\%$) |
| **`T13`** | T'ien | 2 cm SIBAL | 17.5 | 17.6 | **-0.1%** | Instrument resolution limit ($\pm 0.1\%$) |
| **`T23`** | T'ien | 2 cm SIBAL | 17.2 | 17.3 | **-0.1%** | Instrument resolution limit ($\pm 0.1\%$) |

- **Physical Explanation:** The electrochemical oxygen sensor has a nominal accuracy limit of $\pm 0.1\%$. In brief, low-energy burns with minimal fuel consumption, gas cooling or barometric fluctuations within the glovebox produced baseline sensor shifts larger than the actual oxygen consumed.
- **Audit Action:** These five records must NOT be clamped or imputed to positive numbers. They must be tagged `SENSOR_RESOLUTION_LIMIT_NEGATIVE_DRIFT`.

---

### 2.4 The Reconciled 122 Valid Paired Records
Filtering the dataset yields a definitive partition:
- **Total Records:** 129
- **Unreported / Non-Numeric Final $O_2$:** 2 (`B14`, `F3`)
- **Gross Anomalies Quarantined:** 5 (`B2`, `P22a`, `P22b`, `T28a`, `T28b`)
- **Negative Resolution-Limited Drift:** 5 (`T5`, `T10`, `T12`, `T13`, `T23`)
- **Nominal Positive Depletion ($0.0 \le \Delta X_{O2} \le 3.5\%$):** 117 records.
- **Total Valid Analysis Subset:** Exactly **122 paired records** ($117 + 5$).

---

### 2.5 Reconciled Fuel Sample Counts by Principal Investigator

| Principal Investigator | Investigated Fuel Morphology | True Sample Count | Stated in Initial M9 Draft | Reconciliation Status |
| :--- | :--- | :---: | :---: | :--- |
| **Subrata Bhattacharjee** | Thin PMMA Films ($100 - 400\ \mu\text{m}$) | **$N = 22$** | $N = 78$ (Pooled) | **RECONCILED:** Distinct thin film regime ($Bi \ll 0.1$). |
| **Fletcher Miller** | Thick PMMA Slabs ($1 - 5\text{ mm}$, 1/2-sided) | **$N = 20$** | $N = 78$ (Pooled) | **RECONCILED:** Distinct thick slab regime ($Bi \gg 1.0$). |
| **Sandra Olson** | Clear PMMA Rods (Forward Stagnation Flow) | **$N = 27$** | $N = 24$ (Pooled) | **RECONCILED:** Cylinders in stagnation flow. |
| **Carlos Fernandez-Pello** | Black PMMA Rods (Opposed Flow Spread) | **$N = 27$** | $N = 24$ (Pooled) | **RECONCILED:** Cylinders in opposed flow. |
| **James T'ien** | SIBAL Fabric ($N=27$) + Sphere ($N=2$) | **$N = 29$** | $N = 11$ | **RECONCILED:** Cotton/fiberglass composite fabric. |
| **Paul Ferkul** | Nomex III Fabric ($N=3$) + Candle ($N=1$) | **$N = 4$** | $N = 8$ + $N = 8$ | **CORRECTED:** Nomex has $N=3$; Candle has $N=1$. Claims of $N=8$ were false. |
| **Total Experimental Runs** | **All Investigations** | **$N = 129$** | **$N = 129$** | **100% RECONCILED** |

---

### 2.6 Air Display: Scalar Setpoints vs. Complex Sequences
- **Single Numeric Scalars:** Exactly **25 records** (e.g. `'5'`, `'10'`, `'2'`).
- **Complex Sequences / Text Entries:** Exactly **100 records** (77.5%).
  - Adjustment sequences: `'10 8'`, `'20 15 13 14'`, `'3.0 3.1 3.2 6.4 5.5 5.4'`.
  - Operator notes: `'5 2 slow decr to ext'`, `'10 blowoff'`, `'no ign at any flow'`.
- **Missing / Unreported:** Exactly **4 records** (NaN / empty string).
- **Audit Mandate:** Single-velocity static analyses must be strictly restricted to the 25 scalar runs. Any multi-value string must be ingested as `DYNAMIC_FLOW_SEQUENCE` and excluded from static regressions.

---

### 2.7 Flow Calibration Equation and Validity Domain
- **Formula Location:** `Fan calibration data.xlsx`, Row 33.
- **Authentic Formula:**
  $$\mathbf{U = 1.0066 \times (\text{Air Display}) \quad [\text{cm/s}]}$$
- **Reference Standard:** SPICE hot-wire anemometer calibrated at 56 mm downstream, 36 mm from duct bottom (centerline).
- **Valid Range:** $0\text{ to }\sim 30\text{ cm/s}$ ($0.0\text{ to }0.30\text{ m/s}$).
- **Hardware Limitations:**
  - Anemometer response lag is $\sim 1\text{ minute}$; only steady for long hold times.
  - Fan motor shuts off at voltages above 3.8 V (`Fan display` $\le 38$). Extrapolating down to zero flow is invalid.

---

### 2.8 Evaluation of the 255-Litre Chamber Volume & Molar Mass Balance
- **Source of Value:** The standard usable volume of the Microgravity Science Glovebox (MSG) is documented in NASA and ESA facility specifications as **255 liters** ($0.255\text{ m}^3$).
- **Missing Environmental Telemetry:**
  - Glovebox static pressure ($P$) is **not recorded** in the CSV.
  - Glovebox air temperature ($T$) is **not recorded** in the CSV.
  - Net displaced volume of the BASS-II hardware insert (flow duct, cameras, cassettes) is **not calibrated**.
  - Measurement timing post-extinguishment is **undocumented**.
- **Audit Mandate:** Because temperature and pressure vary dynamically across tests, calculating absolute molar oxygen consumption introduces unquantifiable systematic uncertainty. **Quantitative M9 oxygen analysis must be restricted strictly to relative concentration differences ($\Delta X_{O2}$ in vol % and $\text{mol/mol}$, and relative ratio $\Pi_{O2}$).** Molar conversions are relegated to secondary exploratory approximations.

---

## 3. Evaluation of Normalization Safety & Anti-Imputation

The proposed sensor-drift bounding operation in earlier drafts—which attempted to bound negative oxygen depletion ($-0.1\%$) to an artificial positive interval $[0.0, 0.001]\text{ mol/mol}$—was subjected to critical metrological review:

1. **Rejection of Ad-Hoc Clamping:** Replacing negative readings with artificial positive numbers or zero constitutes silent data imputation without physical justification.
2. **Mandatory Epistemic Preservation:**
   - Raw string preserved verbatim: `"-0.1"` or `"-3"`.
   - Raw unit preserved: `% by vol` or `ppm`.
   - Quality flag attached: `SENSOR_RESOLUTION_LIMIT_NEGATIVE_DRIFT` or `SENSOR_ZERO_DRIFT_PRESERVED`.
   - Exclusion reason logged: `NEGATIVE_DEPLETION_EXCLUDED_FROM_MASS_BALANCE`.
   - The normalized difference remains signed: `Decimal('-0.001') mol/mol`.
3. **Execution Gating:** When computing stoichiometric aggregations, downstream filters simply query `WHERE quality_flags NOT CONTAINS 'NEGATIVE_DRIFT'`, preserving total data lineage and preventing mathematical corruption.
