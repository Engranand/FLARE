# FLARE Milestone 9: Scientific Analysis Compatibility Matrix

**Document Identifier:** `FLARE-MATRIX-M9-V1`  
**Classification:** Scientific Specification & Compatibility Audit (Read-Only)  
**Authors:** Senior Combustion Scientist, Scientific Data Engineer, Python Architect  
**Project:** FLARE (Scientific Intelligence Platform for Spacecraft Fire Safety)  
**Primary Dataset:** NASA PSI-25 / BASS-II (`PSI-25_Experimental table_BASS-II.csv`)  
**Secondary Datasets Evaluated:** BASS-I (PSI-26), Saffire-III (PSI-100), ACME Droplet Combustion (PSI-117)  
**Date:** November 2026  
**Status:** DRAFT / APPROVED FOR SPECIFICATION  

---

## 1. Compatibility Overview

This matrix defines the scientific feasibility, mathematical boundaries, input requirements, and operational constraints for prospective analytical workflows within the FLARE Milestone 9 (M9) Deterministic Scientific Analysis Engine.

Every analytical capability is evaluated against the available datasets and assigned one of three strict operational statuses:
- **`SUPPORTED`**: The dataset contains all necessary independent and dependent variables at sufficient precision, completeness, and calibration to compute the target metric without unverified assumptions.
- **`CONDITIONALLY SUPPORTED`**: The analysis is scientifically valid only when specific external calibration curves, non-dimensional scaling laws, or geometric stratification filters are strictly enforced.
- **`NOT SUPPORTED`**: The underlying dataset lacks the required spatial, temporal, or physical variables. Execution would require speculative extrapolation, uncalibrated approximations, or fabricated metrics.

---

## 2. Master Dataset Compatibility Matrix

| Analysis Capability | Target Physical Metric / Phenomenon | BASS-II (PSI-25) Tabular CSV | BASS-II (PSI-25) Video Frames | BASS-I (PSI-26) Tabular | Saffire-III (PSI-100) Vehicle Tests | ACME (PSI-117) Droplet / Gas |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Environmental Baseline Descriptive Statistics** | Non-parametric distributions of ambient initial gas ($X_{O2}, X_{CO2}, X_{CO}$) and chamber temperature. | **SUPPORTED** | **SUPPORTED** (via CSV telemetry) | **SUPPORTED** | **SUPPORTED** | **NOT SUPPORTED** (Quiescent chamber, different gas matrices) |
| **2. Oxygen Concentration & Depletion** | Stoichiometric oxygen consumption ($\Delta X_{O2}$) and molar fuel combustion. | **SUPPORTED** | **SUPPORTED** | **CONDITIONALLY SUPPORTED** (Sensor lag correction) | **CONDITIONALLY SUPPORTED** (Enclosure dilution model) | **NOT SUPPORTED** (Open boundary / non-comparable volume) |
| **3. Airflow Convection Analysis** | Boundary layer velocity gradient ($\partial u / \partial y|_{y=0}$) and forced convection effects. | **CONDITIONALLY SUPPORTED** (Requires `Fan calibration.xlsx` + restrictor stratification) | **CONDITIONALLY SUPPORTED** (Requires flow calibration) | **CONDITIONALLY SUPPORTED** (Requires duct boundary layer model) | **CONDITIONALLY SUPPORTED** (Requires large-scale channel Reynolds scaling) | **NOT SUPPORTED** (Quiescent 1D microgravity; zero forced flow) |
| **4. Fuel / Material Stratification** | Combustion response across thermal thickness regimes ($Bi < 0.1$ vs $Bi > 1.0$). | **SUPPORTED** (6 material classes, $N=129$) | **SUPPORTED** | **SUPPORTED** (PMMA focus only) | **CONDITIONALLY SUPPORTED** (SIBAL / Nomex; large-scale flame interaction) | **NOT SUPPORTED** (Liquid n-alkane droplets / gas jets) |
| **5. Flame Spread Rate ($V_f$)** | Linear flame front regression velocity ($dx_f / dt$) in $mm/s$. | **NOT SUPPORTED** (No spatial tracking or position coordinates) | **SUPPORTED** (Requires optical edge detection & scale calibration) | **SUPPORTED** (If video tracking coordinates present) | **SUPPORTED** (Multi-camera photogrammetry) | **NOT SUPPORTED** (Radially symmetric regression $\dot{r}_d$, not linear spread) |
| **6. Flame Extinction Boundaries** | Limiting Oxygen Index ($\text{LOI}_{\mu g}$) and blow-off / quench limits. | **SUPPORTED** (Gas depletion cutoff + operator notes) | **SUPPORTED** (Visual flame detachment) | **SUPPORTED** | **CONDITIONALLY SUPPORTED** (Low-pressure / hypoxia regimes) | **NOT SUPPORTED** (Radiative extinction of spherical flames) |
| **7. Cross-Investigation Synthesis** | Non-dimensional combustion scaling across microgravity platforms. | **N/A** (Baseline) | **N/A** (Baseline) | **CONDITIONALLY SUPPORTED** (Same MSG duct geometry) | **CONDITIONALLY SUPPORTED** (Damköhler matching required) | **NOT SUPPORTED** (Incompatible fluid mechanics) |

---

## 3. In-Depth Analysis Capability Profiles

### 3.1 Capability 1: Environmental Baseline Descriptive Statistics
- **Protocol Code:** `M9-P1-DESC-STATS`
- **Target Phenomenon:** Statistical distribution of initial atmospheric conditions and final combustion products within the Microgravity Science Glovebox (MSG).
- **Required Inputs:**
  - `Initial O2 %` (Numeric, Range: $13.6 - 22.2\%$, Precision: $0.1\%$)
  - `Final O2 %` (Numeric, Range: $13.5 - 22.2\%$, Precision: $0.1\%$)
  - `Initial CO2 %` (Numeric, Range: $0.0 - 1.9\%$, Precision: $0.1\%$)
  - `Final CO2 %` (Numeric, Range: $0.0 - 2.0\%$, Precision: $0.1\%$)
  - `Initial CO (ppm)` (Numeric, Range: $-3 - 12\text{ ppm}$, Precision: $1\text{ ppm}$)
  - `Final CO (ppm)` (Numeric, Range: $-4 - 40\text{ ppm}$, Precision: $1\text{ ppm}$)
- **Prerequisites & Calibration Dependencies:** None for initial ambient gas percentages. Instrument baseline offset uncertainty ($\pm 3\text{ ppm}$) must be attached to CO metrics.
- **Sample Size & Statistical Power:** $N = 129$ total runs ($N=126$ complete for paired oxygen). High statistical power ($\beta < 0.05$) for median and IQR estimates across major fuel subsets.
- **Confounders & Nuances:** Clustered nominal target concentrations ($15\%, 17\%, 21\%$) produce non-normal, multimodal distributions. Standard standard deviation ($\sigma$) is scientifically misleading; robust estimators (Median, IQR, Trimmed Mean) must be used.
- **Compatibility Status:** **SUPPORTED**

---

### 3.2 Capability 2: Oxygen Concentration & Depletion Analysis
- **Protocol Code:** `M9-P2-O2-DEPLETION`
- **Target Phenomenon:** Total stoichiometric oxygen consumption ($\Delta X_{O2} = X_{O2,init} - X_{O2,final}$) and relative consumption ratio as a proxy for fuel mass loss and combustion efficiency in microgravity.
- **Required Inputs:**
  - `Initial O2 %` (Numeric)
  - `Final O2 %` (Numeric)
  - `Fuel Name` (String)
  - `Fuel Dimensions` (String)
- **Mathematical Constraints:**
  $$\Delta X_{O2} = X_{O2,init} - X_{O2,final} \ge -0.1\%$$
  (Values where $\Delta X_{O2} < -0.1\%$ represent gross sensor glitch or calibration failure and must be flagged).
- **Prerequisites & Calibration Dependencies:** Zero-offset verification. Accounting for closed MSG chamber volume ($V_{MSG} \approx 255\text{ L}$).
- **Sample Size & Statistical Power:** $N = 126$ paired records. Sufficient power to detect oxygen depletion variations $\Delta(\Delta X_{O2}) \ge 0.1\%$ across material classes at $\alpha = 0.01$.
- **Confounders & Nuances:**
  - Tests with failed ignition consume zero oxygen ($\Delta X_{O2} \approx 0.0\%$).
  - Variations in burn duration ($\Delta t$) directly scale $\Delta X_{O2}$. Oxygen depletion cannot be treated as an intrinsic material property without normalizing by burn time or fuel surface area.
- **Compatibility Status:** **SUPPORTED**

---

### 3.3 Capability 3: Airflow Convection Analysis
- **Protocol Code:** `M9-P3-AIRFLOW-CONV`
- **Target Phenomenon:** Influence of forced convection velocity ($U_\infty$) on solid fuel burning behavior, boundary layer thickness ($\delta \propto \sqrt{\nu x / U_\infty}$), and convective flame stabilization.
- **Required Inputs:**
  - `Fan display` (Integer setpoint, $0 - 99$)
  - `Air display` (Integer setpoint, $0 - 55$)
  - `Flow Restrictor` (Boolean / Categorical flag: `Yes` vs `No`/`Blank`)
  - Calibration lookup table from `Fan calibration data.xlsx`
- **Mathematical Formulations:**
  $$U_\infty(S_{fan}) = \sum_{k=0}^n c_k \cdot (S_{fan})^k \quad [\text{cm/s}]$$
  where coefficients $\{c_k\}$ differ completely depending on whether `Flow Restrictor` is present.
- **Prerequisites & Calibration Dependencies:**
  - Strict mapping to empirical pitot-tube/anemometer calibration data from NASA technical documents.
  - Complete partitioning of datasets by duct constriction state.
- **Sample Size & Statistical Power:** $N = 128$ records with fan display. $N = 13$ restricted runs, $N = 115$ unrestricted runs.
- **Confounders & Nuances:**
  - Pooling restricted and unrestricted runs under raw potentiometer numbers generates spurious multi-valued velocity mappings.
  - Near-zero flow setpoints ($S_{fan} \le 5$) suffer from high anemometer calibration uncertainty ($\pm 25\%$).
- **Compatibility Status:** **CONDITIONALLY SUPPORTED**  
  *Blocking Rationale without Condition:* Raw `Fan display` cannot be treated as linear velocity. Analysis is blocked unless calibration polynomials and restrictor partitioning are active.

---

### 3.4 Capability 4: Fuel / Material Stratification Analysis
- **Protocol Code:** `M9-P4-MATERIAL-STRAT`
- **Target Phenomenon:** Comparative flammability, oxygen consumption rate, and self-extinction limits across polymer and fabric fuel classes as a function of thermal Biot number ($Bi = \frac{h L_c}{k_s}$).
- **Required Inputs:**
  - `Fuel Name` (Categorical)
  - `Fuel Dimensions` (Parsed numeric thickness $\tau$, width $w$, length $L$)
  - `Delta X_O2` (Numeric derived)
  - `Burn Duration` (Derived seconds from valid frame counts)
- **Stratified Fuel Groupings:**
  1. *Thin PMMA Films* ($\tau \in [0.05, 0.25]\text{ mm}$, $Bi < 0.1$, thermally thin)
  2. *Thick Cast PMMA Slabs* ($\tau \in [1.27, 6.35]\text{ mm}$, $Bi > 1.0$, thermally thick)
  3. *Cylindrical PMMA Rods* ($r \in [3.17, 6.35]\text{ mm}$, clear vs black pigmentation)
  4. *SIBAL Fabric* (Cotton/fiberglass blend, standard NASA flammability benchmark)
  5. *Nomex Fabric* (Aramid flame-resistant fabric)
  6. *Candle* (Paraffin cylinder with cotton wick)
- **Sample Size & Statistical Power:**
  - PMMA Sheet/Slab: $N = 78$ (High power)
  - PMMA Rods: $N = 24$ (Moderate power)
  - SIBAL: $N = 11$ (Low power; exploratory)
  - Nomex: $N = 8$ (Low power; exploratory)
  - Candle: $N = 8$ (Low power; exploratory)
- **Confounders & Nuances:**
  - Pigmentation in black PMMA rods dramatically enhances internal radiative absorption compared to clear rods.
  - Fabrics (SIBAL, Nomex) experience fabric weave thermal shrinkage and curl, altering effective convective view factors.
- **Compatibility Status:** **SUPPORTED**

---

### 3.5 Capability 5: Flame Spread Rate ($V_f$) Analysis
- **Protocol Code:** `M9-P5-FLAME-SPREAD`
- **Target Phenomenon:** Quasi-steady flame front propagation velocity ($V_f = \frac{dx_f}{dt}$) in opposing or concurrent forced flow.
- **Required Inputs:**
  - Continuous flame front coordinates $x_f(t_k)$ at times $\{t_k\}$.
  - Optical calibration factor $K_{opt}$ ($mm / \text{pixel}$).
  - Reliable temporal sample rate ($f_{cam} \approx 30.0\text{ fps}$).
- **Audit Finding:**
  - `PSI-25_Experimental table_BASS-II.csv` contains only integer scalar bounds `Frame start` and `Frame stop`.
  - It contains **zero spatial tracking measurements**, no flame front coordinates, no pyrolyzing boundary positions, and no optical pixel scales.
- **Methodological Evaluation:**
  - Estimating $V_f$ as sample length divided by frame elapsed time ($V_{f,naive} = \frac{L_{sample} \cdot 30}{\text{Frame stop} - \text{Frame start}}$) is **scientifically invalid**.
  - In over $65\%$ of BASS-II tests, the flame was prematurely extinguished (nitrogen purge, fan stop, or blow-off) prior to reaching the sample end.
  - In other tests, prolonged smoldering or ignition delay occurred, causing $\Delta t$ to severely overestimate the active flame spread period.
- **Compatibility Status:** **NOT SUPPORTED**  
  *Blocking Rationale:* The required spatial tracking data does not exist in the primary tabular dataset. Execution is blocked until digitized video coordinate tables are ingested.

---

### 3.6 Capability 6: Flame Extinction Boundary Analysis
- **Protocol Code:** `M9-P6-EXTINCTION-BOUND`
- **Target Phenomenon:** Delineation of the flammability boundary and microgravity Limiting Oxygen Index ($\text{LOI}_{\mu g}$) in $(X_{O2}, U_\infty)$ space.
- **Required Inputs:**
  - `Initial O2 %` (Numeric)
  - Calibrated velocity $U_\infty$ (Numeric)
  - Binary extinction state indicator $E_i \in \{0, 1\}$ derived from `Notes` and $\Delta X_{O2} < 0.1\%$
  - `Fuel Dimensions` (Thermal thickness regime)
- **Mathematical Formulations:**
  - Logistic Flammability Boundary:
    $$P(\text{Combustion} = 1) = \frac{1}{1 + \exp\left( - (\beta_0 + \beta_1 X_{O2} + \beta_2 U_\infty + \beta_3 \tau) \right)}$$
  - Boundary contour defined at $P = 0.50$.
- **Sample Size & Statistical Power:** $N = 126$ runs. Sufficient extinction events ($N_{ext} \approx 35$) to fit two-parameter logistic boundaries for thin PMMA and thick PMMA.
- **Confounders & Nuances:**
  - Must differentiate between true flammability extinction and ignition failure (igniter hot wire burned through before fuel pyrolyzed).
  - Operator-forced fan turn-off must not be classified as natural blow-off extinction.
- **Compatibility Status:** **SUPPORTED**

---

### 3.7 Capability 7: Cross-Investigation Comparisons

#### 3.7.1 Comparison with BASS-I (PSI-26)
- **Status:** **CONDITIONALLY SUPPORTED**
- **Physical Apparatus:** Identical Microgravity Science Glovebox (MSG) flow duct ($7.6 \times 7.6\text{ cm}^2$).
- **Fuel Formulations:** Both investigations utilized flat PMMA cast sheets.
- **Condition for Execution:** Must verify that duct flow profile calibration and igniter geometry are identical. Can pool flammability boundary points directly in $(X_{O2}, U_\infty)$ space.

#### 3.7.2 Comparison with Saffire-III (PSI-100)
- **Status:** **CONDITIONALLY SUPPORTED**
- **Physical Apparatus:** Cygnus unmanned spacecraft internal flow duct ($0.6 \times 0.9\text{ m}^2$, $L \approx 1\text{ m}$).
- **Physical Regime Disparity:** Flow Reynolds number in Saffire is over an order of magnitude larger than BASS-II ($Re_{Saffire} \sim 10^4$ vs $Re_{BASS} \sim 10^2 - 10^3$). Flame radiation view factors to duct walls are drastically different.
- **Condition for Execution:** Direct pooling of raw values ($U_\infty, \Delta X_{O2}$) is **prohibited**. Comparison is permitted only through non-dimensional Damköhler number scaling ($Da = \tau_{res} / \tau_{chem}$) and normalized mass burning fluxes.

#### 3.7.3 Comparison with ACME / Droplet Combustion (PSI-117)
- **Status:** **NOT SUPPORTED**
- **Physical Regime Disparity:** ACME examines isolated spherical liquid fuel droplets or gaseous round burner jets in quiescent microgravity ($U_\infty = 0$). Spherically symmetric diffusion flame dynamics with heavy soot radiative loss have no mathematical or aerodynamic equivalence to boundary-layer solid polymer combustion.
- **Blocking Rationale:** Pooling or joint statistical modeling of BASS-II solid combustion with ACME droplet combustion violates fundamental fluid mechanics and combustion principles.

---

## 4. Summary of Prerequisites and Implementation Blockers

| Protocol Code | Capability Name | Final Verdict | Primary Scientific Blocker / Prerequisite |
| :--- | :--- | :--- | :--- |
| `M9-P1-DESC-STATS` | Baseline Descriptive Statistics | **SUPPORTED** | None. Ready for implementation. |
| `M9-P2-O2-DEPLETION` | Oxygen Depletion & Stoichiometry | **SUPPORTED** | Exclude runs with sensor anomalies ($\Delta X_{O2} < -0.1\%$). |
| `M9-P3-AIRFLOW-CONV` | Airflow Convection Analysis | **CONDITIONALLY SUPPORTED** | Blocked until calibration lookup from `Fan calibration data.xlsx` is encoded. |
| `M9-P4-MATERIAL-STRAT` | Fuel / Material Stratification | **SUPPORTED** | Thickness must be parsed into SI meters and Biot number assigned. |
| `M9-P5-FLAME-SPREAD` | Flame Spread Rate ($V_f$) | **NOT SUPPORTED** | Blocked. Tabular CSV lacks spatial flame front tracking data. |
| `M9-P6-EXTINCTION-BOUND` | Flame Extinction Boundary | **SUPPORTED** | Operator forced extinctions must be filtered from natural blow-offs. |
| `M9-P7-CROSS-INVEST` | Cross-Investigation Synthesis | **CONDITIONALLY SUPPORTED** | Blocked for ACME. Conditioned on Damköhler matching for Saffire. |
