# FLARE Milestone 9: Independent Scientific Code & Metrological Audit

**Investigation**: NASA PSI-25 / BASS-II Microgravity Combustion  
**Author**: Independent Scientific Data & Database Auditor  
**Date**: November 14, 2026  
**Audit Scope**: Milestone M9 Deterministic Scientific Analysis Engine  
**Audit Classification**: READ-ONLY Audit & Independent Metrological Verification  

---

## 1. Executive Summary

An exhaustive, independent, read-only code and metrological audit was conducted on the Milestone 9 (M9) Deterministic Scientific Analysis Engine implemented for the FLARE spacecraft fire safety intelligence platform.

The audit verified:
1. **Source Dataset Authenticity**: The underlying dataset [PSI-25_Experimental table_BASS-II.csv](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/data/raw/bass_ii/original/PSI-25_Experimental%20table_BASS-II.csv) (16,590 bytes) matches SHA-256 `71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042` byte-for-byte.
2. **First-Principles Recomputation**: All 20 scientific metrics across environmental gas statistics (P1), relative oxygen depletion (P2), calibrated airflow mapping (P3), and fuel morphology (P4) were independently recalculated from raw CSV observations using independent implementations of R Type 7 quantiles, exact sample medians, and non-parametric order-statistic 95% confidence intervals. **100% of recalculated metrics matched the implementation outputs with 0.0 numerical delta** ([m9_independent_calculation_verification.csv](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/m9_independent_calculation_verification.csv)).
3. **Specimen & Regime Mapping Integrity**: All 129 flight tests were evaluated against the approved [m9_p4_test_regime_mapping.csv](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/m9_p4_test_regime_mapping.csv), confirming zero misclassifications across all 10 morphological regimes, 107 unique physical specimens, 107 first burns, and 22 subsequent re-burns.
4. **Database & Sealing Integrity**: Analytical results and protocols are persisted within `SERIALIZABLE` transactions as aggregate roots and child evidence, cryptographically sealed via `flare_sealing.seal('analytical_result', ...)` using `canonical-json-v2` SHA-256 digests, and rendered permanently immutable by database triggers. Duplicate engine executions are verified to be strictly idempotent. Zero persistent or production databases were touched during execution.
5. **Scientific Prohibitions Enforcement**: Verified complete absence of Biot number calculations/inferences, slab LOI logistic regression models, linear flame spread rates ($V_f$), absolute molar consumption ($\Delta n_{O2}$), cubic flow polynomials, uncalibrated flow extrapolations, and combustion respiratory quotients ($RQ_{comb}$).

---

## 2. Source Data Integrity & Ingestion Grounding

### 2.1 File Identity & Integrity Verification
The audit independently verified the integrity of the primary NASA flight record file:
- **Filesystem Path**: `data/raw/bass_ii/original/PSI-25_Experimental table_BASS-II.csv`
- **File Size**: 16,590 bytes
- **Line Count**: 130 lines (1 header line + 129 experimental records)
- **Observed SHA-256 Digest**:
  ```text
  71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042
  ```
- **Preflight Enforcement in Code**: Verified in [engine.py](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/analysis/engine.py#L39-L51), `load_authenticated_records()` computes the SHA-256 digest on load and raises `ValueError` if any bit deviates from `AUTHENTIC_SHA256`.

### 2.2 Record Provenance Tracking
In [engine.py](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/analysis/engine.py#L55-L60), each record is tagged with its 1-indexed CSV line number:
```python
row_dict["data_row_index"] = data_idx
row_dict["csv_record_number"] = data_idx + 1
```
Every metric emitted by P1, P2, P3, and P4 retains its exact `source_record_provenance` list of row numbers (ranging from row 2 through row 130).

---

## 3. Detailed Algorithmic & Metrological Code Review

### 3.1 Module P1: Environmental Gas Statistics
- **Source File**: [backend/app/analysis/p1_env_stats.py](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/analysis/p1_env_stats.py)
- **Protocol Code**: `M9-P1-ENV-STATS` (v1.0.0)
- **Mathematical Formulations**:
  1. **Sample Median** ([p1_env_stats.py#L27-L39](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/analysis/p1_env_stats.py#L27-L39)):
     $$\tilde{x} = \begin{cases} x_{(N+1)/2} & \text{if } N \text{ is odd} \\ \frac{1}{2}\left(x_{(N/2)} + x_{(N/2 + 1)}\right) & \text{if } N \text{ is even} \end{cases}$$
  2. **Quantile Method (R Type 7 / SciPy Default)** ([p1_env_stats.py#L41-L63](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/analysis/p1_env_stats.py#L41-L63)):
     $$h = (N - 1)p, \quad i = \lfloor h \rfloor, \quad \text{frac} = h - i$$
     $$Q(p) = x_{(i)} + \text{frac} \cdot (x_{(i+1)} - x_{(i)})$$
     All calculations utilize `Decimal` precision to avoid binary floating-point representation errors.
  3. **Order-Statistic 95% Confidence Interval** ([p1_env_stats.py#L65-L98](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/analysis/p1_env_stats.py#L65-L98)):
     $$j = \max\left(1, \left\lfloor \frac{N}{2} - 1.96 \frac{\sqrt{N}}{2} \right\rfloor\right), \quad k = \min\left(N, \left\lceil \frac{N}{2} + 1.96 \frac{\sqrt{N}}{2} \right\rceil\right)$$
     $$\text{CI}_{0.95} = [x_{(j)}, x_{(k)}]$$
  4. **Signed Sensor Drift Preservation** ([p1_env_stats.py#L282-L330](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/analysis/p1_env_stats.py#L282-L330)):
     The initial CO sensor readings include 13 negative values ($-1, -2, -3\text{ ppm}$) resulting from zero-calibration sensor drift in microgravity. These values are preserved signed and unclamped, correctly reflecting the true physical sensor dispersion.
  5. **Canonical SI Conversion**:
     - Pre-ignition $\text{O}_2$: $\% \text{ by vol} \times 10^{-2} \rightarrow \text{mol/mol}$
     - Pre-ignition $\text{CO}_2$: $\% \text{ by vol} \times 10^{-2} \rightarrow \text{mol/mol}$
     - Pre-ignition $\text{CO}$: $\text{ppm} \rightarrow \mu\text{mol/mol}$ ($1:1$ canonical equivalence)

### 3.2 Module P2: Relative Oxygen Depletion Analysis
- **Source File**: [backend/app/analysis/p2_oxygen.py](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/analysis/p2_oxygen.py)
- **Protocol Code**: `M9-P2-O2-DEPLETION` (v1.0.0)
- **Disjoint Partitioning Audit**:
  The engine classifies all 129 records into mutually exclusive partitions ([p2_oxygen.py#L67-L163](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/analysis/p2_oxygen.py#L67-L163)):
  - **`POSITIVE_DEPLETION` ($N=93$)**: $+0.1\%$ to $+3.2\%$ volume depletion.
  - **`ZERO_DEPLETION` ($N=24$)**: Exactly $0.0\%$ volume depletion (igniter flash/extinction without measurable O2 depletion).
  - **`NON_NEGATIVE_SUBTOTAL` ($N=117$)**: Union of positive and zero depletion. Median $= 0.0040\text{ mol/mol}$ ($0.4\%$), $\text{IQR} = 0.0060\text{ mol/mol}$ ($0.6\%$), $\text{CI}_{95} = [0.0020, 0.0050]\text{ mol/mol}$.
  - **`NEGATIVE_SENSOR_DRIFT` ($N=5$, Tests `T5, T10, T12, T13, T23`)**: Exactly $-0.1\%$ volume depletion ($-0.0010\text{ mol/mol}$). Preserved signed in the complete signed distribution ($N=122$), median $= 0.0030\text{ mol/mol}$.
  - **`QUARANTINED_GROSS_ANOMALY` ($N=5$, Tests `B2, P22a, P22b, T28a, T28b`)**: $|\Delta X| > 19\%$ volume depletion due to telemetry dropouts / incorrect sensor calibration states. Strictly quarantined and excluded from all statistical distributions.
  - **`MISSING_FINAL_O2` ($N=2$, Tests `B14, F3`)**: Final oxygen unrecorded (`'none'`). Strictly excluded.
- **Relative Depletion Ratio $\Pi_{O2}$**:
  $$\Pi_{O2} = \frac{X_{\text{init}} - X_{\text{final}}}{X_{\text{init}}}$$
  Evaluated across the 117 non-negative records: Median $= 0.0193548387...$, $\text{IQR} = 0.033149...$
- **Deferral & Prohibitions**:
  $RQ_{comb}$ is explicitly deferred due to division-by-zero on 24 zero-depletion runs and sensor asynchrony. Absolute molar consumption $\Delta n_{O2}$ is strictly prohibited due to unrecorded pressure ($P$), temperature ($T$), and displaced volume ($V$).

### 3.3 Module P3: Steady-State Airflow Mapping
- **Source File**: [backend/app/analysis/p3_airflow.py](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/analysis/p3_airflow.py)
- **Protocol Code**: `M9-P3-AIRFLOW-STEADY` (v1.0.0)
- **Calibration Equation**:
  The implementation applies the authentic NASA Glenn SPICE traverse calibration equation ([Fan calibration data.xlsx, Row 33]):
  $$U_{\infty} = 1.0066 \times (\text{Air Display}) \quad [\text{cm/s}]$$
  $$U_{\infty} = (1.0066 \times \text{Air Display}) \times 10^{-2} \quad [\text{m/s}]$$
- **Filtering & Gated Eligibility**:
  - **`VALID_CALIBRATED_STEADY_FLOW` ($N=24$)**: Single scalar Air display setpoint in $[2.0, 15.0]\text{ cm/s}$. Velocity median $= 0.050330\text{ m/s}$, $\text{IQR} = 0.050330\text{ m/s}$, Range $= [0.020132, 0.150990]\text{ m/s}$.
  - **`MOTOR_STALL_DEADBAND` ($N=1$, Test `O2`)**: Air display $= 0.0$. Fan controller shuts off above $3.8\text{ V}$; flagged and excluded from regressions.
  - **`DYNAMIC_FLOW_SEQUENCE` ($N=100$)**: Multi-step potentiometer sequences and operator adjustment notes; excluded from static velocity mapping due to the ~60-second hot-wire anemometer response lag.
  - **`MISSING_AIRFLOW` ($N=4$, Tests `O7, O8a, O8b, O9`)**: Unrecorded telemetry.
- **Prohibitions**: Cubic flow polynomials and flow extrapolation outside $[2.0, 15.0]\text{ cm/s}$ are strictly prohibited and non-existent in the codebase.

### 3.4 Module P4: Observed Fuel Morphology & Specimen Grouping
- **Source File**: [backend/app/analysis/p4_morphology.py](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/analysis/p4_morphology.py)
- **Protocol Code**: `M9-P4-FUEL-REGIMES` (v1.0.0)
- **Regime Audit (129 Runs / 10 Regimes)**:
  1. `CLEAR_PMMA_RODS_STAGNATION`: 27 runs (Olson: clear cast PMMA rods, stagnation/concurrent flow)
  2. `BLACK_PMMA_RODS_OPPOSED`: 27 runs (Fernandez-Pello: black carbon-doped PMMA rods, opposed flow)
  3. `SIBAL_FABRIC_OPPOSED`: 27 runs (Tien: 75% cotton / 25% fiberglass woven fabric, opposed flow)
  4. `THIN_PMMA_FILMS`: 22 runs (Bhattacharjee: cast PMMA thin films 100–400 $\mu\text{m}$, opposed flow)
  5. `THICK_PMMA_SLABS_UNSPECIFIED_MOUNT`: 14 runs (Miller: cast PMMA slabs 1–5 mm, unspecified mount)
  6. `THICK_PMMA_SLABS_1SIDED`: 5 runs (Miller: cast PMMA slabs, 1-sided phenolic mount: `M1, M2, M3, M14, M15`)
  7. `NOMEX_III_FABRIC`: 3 runs (Ferkul: Nomex III natural aramid woven fabric: `F1, F2, F3`)
  8. `PMMA_SPHERE_SEGMENT`: 2 runs (Tien: 4 cm spherical section: `T3, T7`)
  9. `CANDLE_WAX_WICK`: 1 run (Ferkul: paraffin candle with cotton wick: `F4`)
  10. `THICK_PMMA_SLABS_2SIDED`: 1 run (Miller: 3 mm cast PMMA slab, 2-sided unbacked free burn: `M5`)
- **Specimen Tracking & Pseudoreplication**:
  - Unique physical fuel specimens tested: **107**.
  - Single-burn specimens: **87**.
  - Repeated-burn specimens: **20** (tested across 42 runs; maximum 3 burns per specimen).
  - `FIRST_BURN_SUBSET`: **107 runs** (virgin ignitions).
  - `SUBSEQUENT_REBURN_SUBSET`: **22 runs** (pre-burned specimens).
  - **Independence Caveat**: The audit confirmed that the code explicitly documents the unvented chamber background accumulation confounder ($CO \le 950\text{ ppm}$, $CO_2 \le 1.9\%$) in metric metadata, preventing false assumptions of independent and identically distributed (i.i.d.) observations.
- **Expungement of Biot Numbers**: All Biot number calculations and regime inferences ($Bi \ll 0.1$, $Bi \gg 1.0$) were confirmed to be completely expunged.

---

## 4. Database Persistence, Transactional Integrity & Sealing

### 4.1 Relational Architecture & Tables
The database persistence layer is implemented in [protocols.py](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/analysis/protocols.py) and [engine.py](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/analysis/engine.py):
- **Protocols Schema**:
  - `analysis_protocol`: Aggregate root defining protocol metadata (`requirements_schema_version = 'relational-v1'`).
  - `protocol_requirement`: Input variable linkages (`scientific_variable` foreign key).
  - `protocol_unit_rule`: Canonical SI conversion rule (`linear_scaling`, `1.0.0`).
- **Results Schema**:
  - `analytical_result`: Aggregate root storing `numeric_value`, `parameters` (jsonb), `uncertainty` (jsonb), `unit`, `unit_status`, and `producer_ref`.
  - `result_evidence`: Child association linking each result to primary evidence (`source_document` via `evidence_reference`).

### 4.2 Cryptographic Aggregate Sealing
Sealing is performed via the stored procedure:
```sql
SELECT flare_sealing.seal('analytical_result', :inv, :pid, :sid, :actor)
```
- **Seal Version**: `canonical-json-v2`
- **Digest Algorithm**: SHA-256 over canonical JSON member representation.
- **Triggers Enforced**:
  - `guard_child`: Prevents inserting child evidence rows once the parent aggregate is sealed.
  - `freeze_row`: Prevents updating or deleting `analytical_result` rows once sealed.
- **Verification**: In integration test `test_m9_analytical_results_sealed_and_immutable()`, direct SQL `UPDATE` queries against sealed results were rejected by the database engine with an immutability violation error.

### 4.3 Transaction Boundaries & Idempotency
- All database modifications occur within `run_aggregate_transaction()` with PostgreSQL `SERIALIZABLE` isolation and retry handling.
- **Idempotency Guard**: Both [protocols.py#L104-L113](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/analysis/protocols.py#L104-L113) and [engine.py#L173-L182](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/analysis/engine.py#L173-L182) query `aggregate_seal` before inserting records. If an aggregate is already sealed, the insert is bypassed, guaranteeing that subsequent runs return the existing sealed digests without failing trigger checks or duplicating records.

---

## 5. API Design & Security Posture

### 5.1 Route Analysis
The FastAPI routes in [backend/app/api/analysis.py](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/api/analysis.py) expose three endpoints:
- `POST /api/v1/analysis/run`: Executes the deterministic analysis pipeline.
- `GET /api/v1/analysis/protocols`: Lists registered and sealed protocols.
- `GET /api/v1/analysis/results`: Queries persisted analytical results with optional `?protocol_code=` filtering.

### 5.2 Security & Tamper Resistance
1. **Zero External Parameter Injection**: The `POST /api/v1/analysis/run` endpoint accepts no user payload. The pipeline loads data exclusively from the SHA-256 authenticated file on disk. Clients cannot inject custom equations, alter thresholds, or bypass scientific eligibility filters.
2. **Readiness Guard**: In the absence of a configured database connection, endpoints fail safely with HTTP 503 (`Database engine unavailable`).
3. **Audit Finding — Authentication Posture**: Currently, the analysis endpoints do not enforce JWT authentication dependencies (`get_current_user` or role-based access control), matching the current development/staging posture of the FLARE API.
   > [!NOTE]
   > For production readiness (M10+), role-based authorization (e.g., `role: scientist` or `role: admin`) should be attached to `POST /api/v1/analysis/run` to restrict write and database-sealing privileges.

---

## 6. Audit Conclusion

The M9 Deterministic Scientific Analysis Engine implementation strictly adheres to the approved scientific specification [m9_final_analysis_contract.md](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/m9_final_analysis_contract.md). All mathematical formulas, Decimal precisions, unit conversions, eligibility rules, and explicit scientific prohibitions have been verified independently. No discrepancies, regressions, or database safety violations were detected.
