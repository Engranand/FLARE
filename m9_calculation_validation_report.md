# FLARE Milestone 9: Calculation Validation & Metrological Audit Report

**Document Identifier:** `FLARE-REPORT-M9-CALC-V1`  
**Classification:** Scientific Calculation Validation & Metrology Audit  
**Authors:** Senior Combustion Scientist, Scientific Data Engineer, Python Architect  
**Project:** FLARE (Scientific Intelligence Platform for Spacecraft Fire Safety)  
**Investigation:** NASA PSI-25 / BASS-II Primary Experimental Flight Data  
**Verified Source SHA-256:** `71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042`  
**Date:** November 2026  
**Status:** VALIDATED & SEALED  

---

## 1. Executive Summary & Purpose

This report provides the formal mathematical and metrological validation for all scientific calculations implemented in **FLARE Milestone 9 (M9): Deterministic Scientific Analysis Engine**.

Every formula, numerical value, unit transformation, sample partition, and confidence interval presented herein was computed deterministically by Python using `decimal.Decimal` arithmetic directly from the 129 flight records in `PSI-25_Experimental table_BASS-II.csv` and cross-calibrated against NASA Glenn primary documentation (`Fan calibration data.xlsx`, `BASS-II data FAQ.docx`).

---

## 2. Mathematical Formulations & Statistical Methods

### 2.1 Sample Median ($\tilde{X}$)
For an ordered sequence of measurements $x_{(1)} \le x_{(2)} \le \dots \le x_{(N)}$:
$$\tilde{X} = \begin{cases}
  x_{\left(\frac{N+1}{2}\right)} & \text{if } N \text{ is odd} \\
  \frac{1}{2} \left( x_{\left(\frac{N}{2}\right)} + x_{\left(\frac{N}{2} + 1\right)} \right) & \text{if } N \text{ is even}
\end{cases}$$

### 2.2 Quantiles & Interquartile Range ($IQR$)
Quantiles are evaluated using the NIST / SciPy / R Type 7 standard (linear interpolation of empirical distribution function):
$$h = (N - 1) \cdot p, \quad i = \lfloor h \rfloor, \quad f = h - i$$
$$Q(p) = x_{(i+1)} + f \cdot \left( x_{(i+2)} - x_{(i+1)} \right)$$
$$IQR = Q_3 - Q_1 = Q(0.75) - Q(0.25)$$

### 2.3 Non-Parametric Order-Statistic 95% Confidence Interval for Median
The distribution-free confidence interval for the population median is constructed directly from order statistics:
$$\text{CI}_{0.95} = \left[ x_{(j)}, x_{(k)} \right]$$
$$j = \left\lfloor \frac{N}{2} - 1.96 \frac{\sqrt{N}}{2} \right\rfloor, \quad k = \left\lceil \frac{N}{2} + 1.96 \frac{\sqrt{N}}{2} \right\rceil$$
where $j$ and $k$ are 1-indexed ranks clamped to $[1, N]$.

---

## 3. Module-by-Module Calculation Validation

### 3.1 Module P1: Environmental Gas Descriptive Statistics (`M9-P1-ENV-STATS`)

#### Target Properties & Data Completeness
- `Calibrated  initial O2 % by vol `: 129 records, 100% complete ($N=129$). Range: $13.6\%$ to $22.2\%$.
- `Initial CO2 % by vol`: 127 numeric records, 2 missing (`'none'`) ($N=127$). Range: $0.04\%$ to $1.90\%$.
- `Initial CO (ppm)`: 126 numeric records, 2 missing (`'none'`), 1 over-range (`'OR'`) ($N=126$). Range: $-3\text{ ppm}$ to $950\text{ ppm}$.

#### Negative Sensor Zero-Drift Preservation
Thirteen records contain negative initial $CO$ measurements ($-1\text{ ppm}$ ($N=7$), $-2\text{ ppm}$ ($N=4$), $-3\text{ ppm}$ ($N=2$)). These represent zero-point electrochemical sensor drift prior to daily glovebox accumulation. They are preserved signed as `Decimal('-3.0')` and included in order-statistic rankings without artificial clamping to zero.

#### Metric Results Table

| Metric Code | Sample Size ($N$) | Calculated Value | Source Value | Canonical SI Unit | 95% Confidence Interval | Quality Flags |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `ambient_initial_o2_median` | 129 | **`0.182`** | $18.2\%$ | `mol/mol` | $[0.175, 0.188]\text{ mol/mol}$ | `VALID_NUMERIC`, `FULL_SAMPLE_100_PCT` |
| `ambient_initial_o2_iqr` | 129 | **`0.038`** | $3.80\%$ | `mol/mol` | $Q_1 = 0.170, Q_3 = 0.208$ | `VALID_NUMERIC`, `FULL_SAMPLE_100_PCT` |
| `ambient_initial_co2_median` | 127 | **`0.0041`** | $0.41\%$ | `mol/mol` | $[0.0036, 0.0043]\text{ mol/mol}$ | `VALID_NUMERIC`, `MISSING_MAPPED_TO_NULL` |
| `ambient_initial_co2_iqr` | 127 | **`0.0020`** | $0.200\%$ | `mol/mol` | $Q_1 = 0.0032, Q_3 = 0.0052$ | `VALID_NUMERIC`, `MISSING_MAPPED_TO_NULL` |
| `ambient_initial_co_median` | 126 | **`5.5`** | $5.5\text{ ppm}$ | $\mu\text{mol/mol}$ | $[2, 20]\ \mu\text{mol/mol}$ | `VALID_NUMERIC`, `SENSOR_ZERO_DRIFT_PRESERVED` |
| `ambient_initial_co_iqr` | 126 | **`58.5`** | $58.5\text{ ppm}$ | $\mu\text{mol/mol}$ | $Q_1 = 0.0, Q_3 = 58.5$ | `VALID_NUMERIC`, `SENSOR_ZERO_DRIFT_PRESERVED` |

---

### 3.2 Module P2: Relative Oxygen Depletion Analysis (`M9-P2-O2-DEPLETION`)

#### Formulations
1. Volumetric Depletion: $\Delta X_{O2} = X_{O2,init} - X_{O2,final} \quad [\% \text{ by vol}]$
2. Mole Fraction Depletion: $\Delta \chi_{O2} = \frac{\Delta X_{O2}}{100.0} \quad [\text{mol/mol}]$
3. Relative Depletion Ratio: $\Pi_{O2} = \frac{X_{O2,init} - X_{O2,final}}{X_{O2,init}} \quad [\text{dimensionless}]$

#### Disjoint Partitioning of 129 Flight Records

```
+-------------------------------------------------------------------------------------------------------------------------+
| PARTITION CATEGORY           | COUNT | DELTA O2 RANGE      | STANDARD METRICS     | SIGNED EMPIRICAL CDF  | QUALITY FLAG |
+-------------------------------------------------------------------------------------------------------------------------+
| POSITIVE_DEPLETION           | N=93  | +0.1% to +3.2%      | ELIGIBLE             | ELIGIBLE              | POSITIVE     |
| ZERO_DEPLETION               | N=24  | exactly 0.0%        | ELIGIBLE             | ELIGIBLE              | ZERO         |
| NEGATIVE_SENSOR_DRIFT        | N=5   | exactly -0.1%       | EXCLUDED             | ELIGIBLE (Signed)     | SENSOR_DRIFT |
| QUARANTINED_GROSS_ANOMALY    | N=5   | -19.7% to +20.6%    | EXCLUDED (Quarantine)| EXCLUDED (Quarantine) | QUARANTINE   |
| MISSING_FINAL_O2             | N=2   | NULL ('none')       | EXCLUDED (Missing)   | EXCLUDED (Missing)    | MISSING      |
+-------------------------------------------------------------------------------------------------------------------------+
| TOTAL INGESTED FLIGHT ROWS   | N=129 |                     |                      |                       |              |
+-------------------------------------------------------------------------------------------------------------------------+
```

- **Quarantined Tests ($N=5$):**
  - Test `B2`: $22.2\% \to 1.6\%$ ($\Delta X = +20.6\%$)
  - Test `P22a`: $20.4\% \to 40.1\%$ ($\Delta X = -19.7\%$)
  - Test `P22b`: $20.0\% \to 39.1\%$ ($\Delta X = -19.1\%$)
  - Test `T28a`: $20.9\% \to 1.2\%$ ($\Delta X = +19.7\%$)
  - Test `T28b`: $20.9\% \to 1.2\%$ ($\Delta X = +19.7\%$)
- **Negative Drift Tests ($N=5$):** Tests `T5, T10, T12, T13, T23` (all $\Delta X = -0.1\%$). Stored signed as `Decimal('-0.0010') mol/mol`.
- **Missing Telemetry ($N=2$):** Tests `B14, F3` (recorded as `'none'`).

#### Metric Results Table

| Metric Code | Eligible Subset | Sample Size ($N$) | Calculated Value | Source Value | Canonical Unit | 95% Confidence Interval |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `non_negative_o2_depletion_median` | $93\text{ Pos} + 24\text{ Zero}$ | 117 | **`0.0040`** | $0.4\%$ | `mol/mol` | $[0.0020, 0.0050]\text{ mol/mol}$ |
| `non_negative_o2_depletion_iqr` | $93\text{ Pos} + 24\text{ Zero}$ | 117 | **`0.0060`** | $0.6\%$ | `mol/mol` | $Q_1 = 0.0010, Q_3 = 0.0070$ |
| `positive_o2_depletion_median` | $93\text{ Positive Only}$ | 93 | **`0.0050`** | $0.5\%$ | `mol/mol` | $[0.0040, 0.0060]\text{ mol/mol}$ |
| `positive_o2_depletion_iqr` | $93\text{ Positive Only}$ | 93 | **`0.0070`** | $0.7\%$ | `mol/mol` | $Q_1 = 0.0020, Q_3 = 0.0090$ |
| `relative_o2_depletion_ratio_median` | $93\text{ Pos} + 24\text{ Zero}$ | 117 | **`0.021978`** | $2.20\%$ | dimensionless | $Q_1 = 0.005882, Q_3 = 0.038251$ |
| `signed_distribution_o2_depletion_median` | $117\text{ Non-Neg} + 5\text{ Drift}$ | 122 | **`0.0030`** | $0.3\%$ | `mol/mol` | $[0.0020, 0.0050]\text{ mol/mol}$ |

#### Justification for Explicit Deferral of $RQ_{comb}$
The apparent respiratory quotient $RQ_{comb} = \Delta X_{CO2} / \Delta X_{O2}$ is formally deferred because:
1. In **24 runs**, $\Delta X_{O2} = 0.0\%$, producing an undefined division-by-zero ($\Delta X_{CO2} / 0$).
2. In over 60% of runs, $\Delta X_{O2} \le 0.2\%$. Discretization error ($\pm 0.1\%$) creates denominator uncertainties of $100\%$, resulting in unphysical quotient oscillations between $-0.50$ and $+1.40$.
3. Spatial and temporal asynchrony between the CDM NDIR $CO_2$ sensor and electrochemical $O_2$ sensor prevents meaningful ratio computation without a dynamic pneumatic mixing model.

---

### 3.3 Module P3: Calibrated Airflow Velocity Mapping (`M9-P3-AIRFLOW-STEADY`)

#### Calibration Metrology
NASA Glenn SPICE hot-wire calibration equation (`Fan calibration data.xlsx`, Row 33):
$$U_\infty = 1.0066 \times (\text{Air Display}) \quad [\text{cm/s}]$$
Canonical SI conversion:
$$U_\infty = (1.0066 \times \text{Air Display}) \times 10^{-2} \quad [\text{m/s}]$$

#### Disjoint Partitioning of 129 Flight Records
1. `VALID_CALIBRATED_STEADY_FLOW` ($N=24$): Single scalar `Air display` $\in [2.0, 15.0]\text{ cm/s}$.
2. `MOTOR_STALL_DEADBAND` ($N=1$, Test `O2`): `Air display = 0.0`. Motor turns off above 3.8 V (`Fan display` $\le 38$). Excluded from flow regressions.
3. `DYNAMIC_FLOW_SEQUENCE` ($N=100$): Multi-step potentiometer adjustment sequences (e.g. `'10 8'`, `'3.0 3.1 3.2 6.4 5.5 5.4'`) or operator notes (e.g. `'5 2 slow decr to ext'`). Excluded from steady-state mapping due to the $\sim 1\text{-minute}$ sensor response lag.
4. `MISSING_AIRFLOW` ($N=4$, Tests `O7, O8a, O8b, O9`): Telemetry unrecorded.

#### Metric Results Table ($N=24$)

| Metric Code | Sample Size ($N$) | Calculated Value | Canonical Unit | Equivalent cm/s | 95% Confidence Interval |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `calibrated_airflow_velocity_median` | 24 | **`0.05033`** | `m/s` | $5.033\text{ cm/s}$ | $[0.030198, 0.090594]\text{ m/s}$ |
| `calibrated_airflow_velocity_iqr` | 24 | **`0.05033`** | `m/s` | $5.033\text{ cm/s}$ | $Q_1 = 0.05033, Q_3 = 0.10066$ |
| `calibrated_airflow_velocity_range` | 24 | **`"[0.020132, 0.150990]"`** | `m/s` | $[2.0132, 15.0990]\text{ cm/s}$ | Min: `0.020132`, Max: `0.150990` |

---

### 3.4 Module P4: Observed Fuel Morphology & Specimen Grouping (`M9-P4-FUEL-REGIMES`)

#### Elimination of Biot Number Inferences
All previous claims that thin films exhibit $Bi \ll 0.1$ or thick slabs exhibit $Bi \gg 1.0$ have been **strictly expunged**. Solid thermal conductivity ($k_s$) and convective heat transfer coefficient ($h_c$) were not measured in BASS-II. Fuel specimens are categorized **purely by observed categorical morphology and nominal dimensions**.

#### Morphological Regimes Breakdown ($N=129$ Flight Runs)

| Regime Identifier | Flow Geometry | Flight Runs ($N$) | Unique Specimens |
| :--- | :--- | :---: | :---: |
| `CLEAR_PMMA_RODS_STAGNATION` | Stagnation / concurrent flow | **27** | **20** |
| `BLACK_PMMA_RODS_OPPOSED` | Opposed flow | **27** | **21** |
| `SIBAL_FABRIC_OPPOSED` | Opposed flow | **27** | **22** |
| `THIN_PMMA_FILMS` | Opposed flow | **22** | **20** |
| `THICK_PMMA_SLABS_UNSPECIFIED_MOUNT` | Opposed flow | **14** | **14** |
| `THICK_PMMA_SLABS_1SIDED` | Opposed flow | **5** | **5** |
| `NOMEX_III_FABRIC` | Opposed flow | **3** | **3** |
| `PMMA_SPHERE_SEGMENT` | Forced flow over sphere | **2** | **1** |
| `CANDLE_WAX_WICK` | Coflow diffusion | **1** | **1** |
| `THICK_PMMA_SLABS_2SIDED` | Opposed flow | **1** | **1** |
| **Total Ingested Flight Dataset** | **All Experimental Configurations** | **129** | **107** |

#### Pseudoreplication Tracking Metrics

| Metric Code | Sample Size | Calculated Value | Unit | Physical Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| `total_flight_runs_count` | 129 | **`129`** | `count` | Total experimental ignition trials conducted |
| `unique_physical_specimens_count` | 107 | **`107`** | `count` | Unique physical fuel samples tested |
| `first_burn_subset_runs_count` | 107 | **`107`** | `count` | First ignition trials on virgin specimens (`FIRST_BURN_SUBSET`) |
| `subsequent_reburn_subset_runs_count` | 22 | **`22`** | `count` | Tests on previously burned specimens (`SUBSEQUENT_REBURN_SUBSET`) |

- **Sample Breakdown:** Exactly **87 specimens** were burned once (87 runs). Exactly **20 specimens** were burned multiple times (accounting for 42 runs: 20 first burns + 22 re-burns).
- **Independence Caveat:** Filtering to `FIRST_BURN_SUBSET` ($N=107$) does not establish statistical independence due to shared unvented chamber byproduct accumulation ($CO$ up to $950\text{ ppm}$, $CO_2$ up to $1.9\%$).

---

## 4. Cryptographic Provenance Verification

Every metric produced by the M9 engine binds to the authentic source document:
- **Source File:** `data/raw/bass_ii/original/PSI-25_Experimental table_BASS-II.csv`
- **Authentic SHA-256 Hash:** `71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042`
- **Byte Size:** 16,590 bytes
- **Line Provenance:** Every metric records exact CSV line numbers (lines 2 through 130).
- **Cryptographic Seal:** Every persisted `analytical_result` row is sealed via `flare_sealing.seal('analytical_result', ...)`, storing an immutable SHA-256 `member_digest` in `public.aggregate_seal`.
