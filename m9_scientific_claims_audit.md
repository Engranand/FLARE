# Independent Combustion Science Audit of FLARE Milestone 9 (M9) Deliverables

**Document Identifier:** `FLARE-AUDIT-M9-V1`  
**Classification:** Independent Scientific Review & Claims Audit (Read-Only)  
**Reviewer:** Independent Combustion Science & Experimental Data Reviewer  
**Project:** FLARE (Scientific Intelligence Platform for Spacecraft Fire Safety)  
**Audit Target:** M9 Architectural Specification & Pre-Implementation Deliverables (`m9_scientific_analysis_specification.md`, `m9_analysis_compatibility_matrix.md`, `m9_normalization_design.md`, `m9_result_contract.md`, `m9_validation_plan.md`, `m9_variable_registry.csv`)  
**Primary Reference Files Inspected:**
1. `data/raw/bass_ii/original/PSI-25_Experimental table_BASS-II.csv` (SHA-256: `e43997e20ec42c16aa95b7feee8018e6c79a48972f78e47bf1b6be91e93895e6`)
2. `data/raw/challenge_resources/original/bass_ii/PSI-25_Reference Data_Fan calibration data.xlsx`
3. `data/raw/bass_ii/original/BASS-II data FAQ.docx` & `PSI-25_Science Documents_BASS-II_ReadMe.docx`
4. `data/raw/bass_ii/original/BASS-II Test Matrix by PI Final.xlsx`
**Date:** November 2026  
**Review Verdict:** CONDITIONALLY AUDITED — SIGNIFICANT SCIENTIFIC DISCREPANCIES IDENTIFIED  

---

## 1. Executive Summary

This independent scientific audit evaluates the physical, mathematical, and data engineering assumptions in the Milestone 9 (M9) specification deliverables. Every assumption was tested against original primary source archives from NASA Physical Sciences Informatics (PSI) investigation PSI-25 (BASS-II).

The audit reveals that while the baseline architecture (verbatim string preservation, cryptographic aggregate sealing, and non-parametric statistics) is sound, several critical scientific claims in the M9 specification are **factually incorrect, based on fabricated physical parameters, or methodologically unsupportable given the actual structure of the BASS-II dataset**.

### Summary of Claim Classifications

| Investigation Area | Specific Claim in M9 Specification | Audit Classification | Primary Source Evidence / Conflict |
| :--- | :--- | :---: | :--- |
| **1. Limiting Oxygen Index (LOI)** | LOI of $14.5 - 15.0\%$ can be modeled for thick PMMA slabs using logistic regression on gas depletion ($\Delta X_{O2} < \epsilon$). | **`SCIENTIFICALLY UNSUPPORTED`** | Miller's thick PMMA slabs were tested **strictly at $\ge 17.9\% O_2$** ($N=20$, 0 low-oxygen extinction events). Low-oxygen tests ($13.6 - 16.0\%$) were exclusively Olson's **cylindrical rods in stagnation flow**, not flat slabs. Gas depletion reflects total burn history, not instantaneous extinction. |
| **2. Biot Number Classification** | Fuel thermal thickness can be determined via calculated Biot number: $Bi = \frac{h_c \tau}{2 k_s}$, with $k_s = 0.19\text{ W/m}\cdot\text{K}$ and $h_c = 15\text{ W/m}^2\text{K}$. | **`NOT VERIFIED`** | Parameters $k_s$ and $h_c$ are **completely absent** from NASA source files. In microgravity boundary layer combustion, $h_c$ is dynamic and coupled to flame standoff and radiation. Values were imported from terrestrial assumptions. |
| **3. CO Sensor Uncertainty** | Instrument uncertainty is $\pm 3\text{ ppm}$ based on sensor drift. `Initial CO` ranges from $-3$ to $12\text{ ppm}$; `Final CO` ranges from $-4$ to $40\text{ ppm}$. | **`NOT VERIFIED`** | The $\pm 3\text{ ppm}$ figure is an *assumed tolerance*, not traced to NASA calibration. Furthermore, the claimed ranges are grossly erroneous: actual `Initial CO` reaches **950 ppm**, and `Final CO` reaches **950 ppm, with '>500', 'over', and 'OR' (>1000 ppm)** due to unvented MSG chamber accumulation. |
| **4. Airflow Calibration** | Potentiometer readings map to velocity via a 3rd-order polynomial $U_\infty = P(S_{fan})$. `Fan display` and `Air display` are independent scalar setpoints. | **`CONDITIONALLY VERIFIED`** | There is **NO polynomial** in `Fan calibration data.xlsx`. The actual formula is $U = 1.0066 \times (\text{Air Display})\text{ cm/s}$. Over $75\%$ of rows in the CSV contain **complex strings** detailing dynamic flow adjustment sequences and operator notes, not single numeric scalars. |
| **5. Oxygen Depletion** | Pre- and post-test calibrated $O_2$ can be subtracted ($\Delta X_{O2} = X_{O2,init} - X_{O2,final}$) across 126 records. | **`CONDITIONALLY VERIFIED`** | Initial and final $O_2$ are calibrated by NASA via ISS MCA. However, 5 SIBAL tests show negative consumption ($\Delta X_{O2} = -0.1\%$) due to sensor drift, and 5 tests (`B2, P22a, P22b, T28a, T28b`) contain severe column shifts or recording anomalies (e.g. `Final O2 = 39.1%`, `40.4%`). |
| **6. Statistical Sample Sizes** | Fuel stratification supports robust comparisons for Nomex ($N=8$) and Candle ($N=8$). Repeated tests are independent. | **`SCIENTIFICALLY UNSUPPORTED`** | Actual sample counts in BASS-II are **Nomex: $N=3$** and **Candle: $N=1$**. Furthermore, at least 20 samples were re-burned multiple times, introducing thermal preheating and charring confounders that violate i.i.d. assumptions. |

---

## 2. In-Depth Audit of Critical Claims

### 2.1 Investigation 1: Limiting Oxygen Index (LOI) & Extinction Modeling

#### Claims Audited
1. "The microgravity Limiting Oxygen Index ($\text{LOI}_{\mu g}$) for thick PMMA slabs ($1.27\text{ mm} - 6.35\text{ mm}$) in low-speed opposed flow is between $14.5\%$ and $15.2\%$." (`m9_validation_plan.md`, Battery 5)
2. "Extinction events can be classified via $\Delta X_{O2} < \epsilon_{threshold}$ and logistic regression in $(X_{O2}, U_\infty)$ space." (`m9_scientific_analysis_specification.md`, Section 3.6)

#### Primary Evidence from Source Data
- **NASA Source File:** `data/raw/bass_ii/original/PSI-25_Experimental table_BASS-II.csv`
- A complete query of `Calibrated  initial O2 % by vol ` by Principal Investigator reveals:
  ```
  PI: Bhattacharjee (Thin PMMA Films, N=22)  -> O2 min = 15.0%, max = 22.2%, median = 21.0%
  PI: Ferkul (Nomex/Candle, N=4)              -> O2 min = 17.4%, max = 22.2%, median = 21.35%
  PI: Miller (Thick PMMA Slabs, N=20)         -> O2 min = 17.9%, max = 22.2%, median = 20.45%
  PI: Olson (Clear PMMA Rods, N=27)           -> O2 min = 13.6%, max = 22.2%, median = 15.7%
  PI: Fernandez-Pello (Black Rods, N=27)     -> O2 min = 16.3%, max = 20.9%, median = 18.2%
  PI: T'ien (SIBAL Fabric, N=29)             -> O2 min = 16.4%, max = 20.8%, median = 17.5%
  ```
- **Physical Finding 1:** In the BASS-II experimental table, Fletcher Miller's thick PMMA slabs were **NEVER tested below 17.9% $O_2$**. There is not a single thick PMMA slab run at $14.5 - 15.0\% O_2$.
- **Physical Finding 2:** The tests conducted at $O_2 \le 16.0\%$ ($N=18$) belong almost exclusively to **Sandra Olson** (17 runs on clear/black PMMA cylindrical rods in forward stagnation flow) and Subrata Bhattacharjee (1 run, `B14`, on 200 $\mu\text{m}$ thin film).
- **Physical Finding 3 (Methodological Flaw):** In microgravity combustion, total oxygen depletion ($\Delta X_{O2}$) is the time-integral of mass burning rate over the entire burn duration:
  $$\Delta X_{O2} \propto \int_0^{t_{ext}} \dot{m}''_F(t) A_{flame}(t) \, dt$$
  In tests where the operator systematically decreased airflow until extinction occurred (e.g. Test `P1`: `'5  2   slow decr to ext'`, Test `O4`: `'5   down to ext'`), the sample burned vigorously for several minutes before extinguishing, consuming substantial oxygen ($\Delta X_{O2} = 1.2\%$). Thus, $\Delta X_{O2} \approx 0$ identifies **only ignition failures**, NOT flammability extinction boundaries.
- **Physical Finding 4 (Logistic Regression Breakdown):** Fitting a logistic regression model requires binary class variance across the predictor domain. For thick PMMA slabs, all 20 runs ignited and burned successfully ($20:0$ class balance). Logistic regression encounters complete separation and cannot converge.

#### Audit Classification: `SCIENTIFICALLY UNSUPPORTED`

---

### 2.2 Investigation 2: Biot Number Classification & Heat Transfer

#### Claims Audited
"Fuel thermal thickness is calculated via solid Biot number: $Bi = \frac{h_c \tau}{2 k_s}$, where $k_s \approx 0.19\text{ W/m}\cdot\text{K}$ and $h_c \approx 15\text{ W/m}^2\text{K}$." (`m9_normalization_design.md`, Section 6.3)

#### Primary Evidence from Source Data
- **NASA Source Files:** `PSI-25_Experimental table_BASS-II.csv`, `BASS-II data FAQ.docx`, `PSI-25_Science Documents_BASS-II_ReadMe.docx`.
- **Physical Finding 1:** The primary NASA files contain physical dimensions (length, width, thickness in mm/inches) but **zero measurements or tabulated values** for solid thermal conductivity ($k_s$), solid density ($\rho_s$), heat capacity ($c_p$), gas thermal conductivity ($k_g$), or heat transfer coefficient ($h_c$).
- **Physical Finding 2:** In microgravity forced convection, convective heat transfer is coupled to the boundary layer velocity gradient and flame standoff distance. The convective coefficient $h_c$ is neither uniform nor constant ($15\text{ W/m}^2\text{K}$); it varies with local coordinates and flow speed:
  $$h_c(x) \sim \frac{k_g}{\delta_T(x)} \propto \sqrt{\frac{U_\infty}{\nu x}}$$
- **Physical Finding 3:** The values $k_s = 0.19\text{ W/m}\cdot\text{K}$ and $h = 15\text{ W/m}^2\text{K}$ represent assumed handbook parameters imported by the author of M9, violating the strict restriction against fabricated physical parameters.
- **Defensible Solution:** The NASA science team established categorical regimes directly based on fuel morphology:
  1. *Thin Films* (Bhattacharjee, $\tau \le 0.5\text{ mm}$, thermally thin limit).
  2. *Thick Slabs* (Miller, $\tau \ge 1.0\text{ mm}$, thermally thick limit; divided into 1-sided mount vs 2-sided unbacked burns).
  3. *Cylindrical Rods* (Olson/Fernandez-Pello, diameters 1/4", 3/8", 1/2").
  4. *Fabrics* (T'ien SIBAL, Ferkul Nomex).

#### Audit Classification: `NOT VERIFIED` (Categorical regimes verified; numeric Biot formula unsupported)

---

### 2.3 Investigation 3: Carbon Monoxide (CO) Sensor Uncertainty & Ranges

#### Claims Audited
1. "Baseline uncertainty is $\pm 3\text{ ppm}$ based on electrochemical sensor zero drift." (`m9_normalization_design.md`, Section 3)
2. "Initial CO (ppm) Range: $-3$ to $12\text{ ppm}$." (`m9_scientific_analysis_specification.md`, Section 2.2)
3. "Final CO (ppm) Range: $-4$ to $40\text{ ppm}$." (`m9_scientific_analysis_specification.md`, Section 2.2)

#### Primary Evidence from Source Data
- **NASA Source Files:** `PSI-25_Experimental table_BASS-II.csv`, `BASS-II data FAQ.docx`.
- Inspection of `BASS-II data FAQ.docx` states:
  > *"CO readings: CSA-CP sensor readings. OR = over range (> 1000 ppm)"*
- A full scan of all 129 records in `PSI-25_Experimental table_BASS-II.csv` reveals:
  ```
  Initial CO (ppm):
    Negative readings: -1 (11 rows), -2 (1 row), -3 (1 row) -> Total negative: 13 rows.
    High readings: 103, 105, 113, 117, 118, 119, 140, 152, 185, 232, 290, 389, 398, 436, 496, 523, 525, 536, 660, 950 ppm, and 'OR' (1 row).
  
  Final CO (ppm):
    Negative readings: EXACTLY 0 ROWS. (There is not a single negative reading in Final CO).
    High readings: Values span 0 to 950 ppm, with 56 entries > 100 ppm, and saturated entries '>500', 'over', 'OR' (2 rows).
  ```
- **Discrepancy Analysis:** The M9 specification reported `Final CO` range as "$-4$ to $40\text{ ppm}$". This is factually false by more than an order of magnitude. The author inspected only the first four runs (B1–B4) and missed the fact that because tests were conducted sequentially in a sealed 255-liter glovebox, CO accumulated up to **950 ppm**, frequently saturating the CSA-CP sensor.
- **Uncertainty Traceability:** The $\pm 3\text{ ppm}$ uncertainty was not derived from NASA CSA-CP calibration logs. It was an ad-hoc heuristic selected because $-3\text{ ppm}$ was the minimum value observed in `Initial CO`.

#### Audit Classification: `NOT VERIFIED` (Negative drift verified; claimed ranges and $\pm 3\text{ ppm}$ standard unverified)

---

### 2.4 Investigation 4: Airflow Duct Calibration & Input Formats

#### Claims Audited
1. "Potentiometer reading $S_{fan} \in [0, 99]$ maps to velocity via calibration polynomial: $U_\infty = a_0 + a_1 S_{fan} + a_2 S_{fan}^2 + a_3 S_{fan}^3$." (`m9_scientific_analysis_specification.md`, Section 3.3)
2. "`Fan display` and `Air display` represent scalar control setpoints." (`m9_result_contract.md`)

#### Primary Evidence from Source Data
- **NASA Source File:** `data/raw/challenge_resources/original/bass_ii/PSI-25_Reference Data_Fan calibration data.xlsx`.
- Inspection of the 109-column calibration workbook reveals:
  - Row 33 explicitly defines the calibration:
    $$\mathbf{U = 1.0066 \times (\text{AIR})}$$
  - Row 34 states:
    > *"Based on SPICE fan calibration data at 56 mm downstream, 36 mm from bottom (centerline)"*
  - Row 7 to 31: Column E formula is uniformly `=1.0066*C7`, where column C is `Air Display`.
  - Column D formula is `=B7/10`, where column B is `Fan Display` (verifying that Fan Display is Volts $\times 10$).
  - **There is no cubic polynomial anywhere in the workbook.**
- **Actual Data Format in `PSI-25_Experimental table_BASS-II.csv`:**
  - `Fan display` contains **97 complex string entries** out of 129 rows (75.2%), such as:
    - `'116 (pot 9.3)    89   80   84'` (Test M2)
    - `'3.0  3.1  3.2  6.4  5.5  5.4'` (Test M3)
    - `'Fan pot 3.7   1.7   1.5   1.3   0.8   0.6   0.5   0.3ext'` (Test O1)
  - `Air display` contains **100 complex string entries** out of 129 rows (77.5%), such as:
    - `'5  2   slow decr to ext'` (Test P1)
    - `'10  17  14  10  8'` (Test M5)
    - `'5   very low (0.85   0.32   0.31   0.305   0.30   0.295)'` (Test P3b)
  - **Critical Anomaly:** In over 75% of tests, the flow was actively altered by the astronaut during combustion. Treating `Fan display` or `Air display` as a single static scalar setpoint is completely invalid.
- **Instrument Lag:** `BASS-II data FAQ.docx` notes:
  > *"Air display: flow speed measured in the duct in cm/s on the video display. Response time is very slow (~ 1 min), so reading is only steady for long times at the same flow setting."*
  Because the sensor required ~1 minute to stabilize, dynamic fan adjustments rendered the instantaneous `Air display` reading non-representative of actual fluid velocity.

#### Audit Classification: `CONDITIONALLY VERIFIED` (Linear conversion $U = 1.0066 \times \text{Air}$ verified; static scalar assumption and polynomial claim rejected)

---

### 2.5 Investigation 5: Oxygen Depletion Integrity & Comparability

#### Claims Audited
"Stoichiometric oxygen depletion $\Delta X_{O2} = X_{O2,init} - X_{O2,final}$ can be calculated across 126 paired records." (`m9_scientific_analysis_specification.md`, Section 3.2)

#### Primary Evidence from Source Data
- **NASA Source File:** `PSI-25_Experimental table_BASS-II.csv`.
- An audit of paired numeric $O_2$ values across all 129 rows reveals:
  1. **Nominal Depletion:** 117 records exhibit expected combustion depletion ($0.0\% \le \Delta X_{O2} \le 3.5\%$).
  2. **Negative Consumption (Drift):** Five SIBAL tests (`T5, T10, T12, T13, T23`) report $\Delta X_{O2} = -0.1\%$ ($X_{O2,final} > X_{O2,init}$), caused by sensor thermal stabilization and baseline drift.
  3. **Gross Data Anomalies & Column Swaps:**
     - Test `B2`: $X_{O2,init} = 22.2\%$, $X_{O2,final} = 1.6\%$ ($\Delta = +20.6\%$).
     - Test `P22a`: $X_{O2,init} = 20.8\%$, $X_{O2,final} = 0.6\%$ ($\Delta = +20.2\%$).
     - Test `P22b`: $X_{O2,init} = 20.0\%$, $X_{O2,final} = 39.1\%$ ($\Delta = -19.1\%$).
     - Test `T28a`: $X_{O2,init} = 20.7\%$, $X_{O2,final} = 0.9\%$ ($\Delta = +19.8\%$).
     - Test `T28b`: $X_{O2,init} = 20.7\%$, $X_{O2,final} = 40.4\%$ ($\Delta = -19.7\%$).
- **Explanation:** In subtests `a` and `b`, the operators recorded depletion in place of final concentration, or values from other sensor columns were shifted into `Calibrated final O2`. These five records must be strictly quarantined.
- **Safe Subsample:** Exactly **122 records** can safely enter quantitative gas consumption calculations after filtering out gross anomalies ($\Delta X_{O2} > 5\%$ or $\Delta X_{O2} < -0.2\%$).

#### Audit Classification: `CONDITIONALLY VERIFIED` (Valid only after applying anomaly exclusion filters)

---

### 2.6 Investigation 6: Sample Sizes, Confounders & Statistical Validity

#### Claims Audited
1. "Sample sizes for fuel stratification: Nomex Fabric $N = 8$, Candle / Cotton Wick $N = 8$." (`m9_scientific_analysis_specification.md`, Section 3.4)
2. "Fuel comparisons can be conducted across stratified fuel groups using i.i.d. non-parametric estimators."

#### Primary Evidence from Source Data
- **NASA Source File:** `PSI-25_Experimental table_BASS-II.csv`.
- Querying all rows under PI Paul Ferkul reveals:
  ```
  Row 22 (Test F1): Sample 227  -> Nomex natural (nomex III)
  Row 23 (Test F2): Sample 228m -> Nomex natural (nomex III)
  Row 24 (Test F3): Sample 229m -> Nomex natural (nomex III)
  Row 25 (Test F4): Sample 39M  -> Japan Wax candle
  ```
  **Actual sample counts in BASS-II are $N=3$ for Nomex and $N=1$ for Candle.** The M9 specification's claim of $N=8$ is completely unsubstantiated by the primary BASS-II table.
- **Severe Confounder — Sample Reuse (Pseudoreplication):**
  Inspection of `Sample #` reveals that at least **20 distinct fuel specimens were burned multiple times** (e.g. `144m` burned 3 times, `220m` burned 3 times, `200m` burned twice).
  `BASS-II data FAQ.docx` explicitly cites:
  > *"Paul Ferkul et al., 'Thickness and Fuel Preheating Effects on Material Flammability in Microgravity from the BASS Experiment'"*
  Prior burns introduce surface charring, fuel thickness regression, and elevated initial solid temperatures, directly altering flammability limits and burning rates. Treating these tests as independent observations invalidates standard statistical hypothesis tests.
- **Severe Confounder — Background Chamber Accumulation:**
  Because the MSG was closed, background $CO_2$ rose from $0.0\%$ to $1.9\%$ and $CO$ accumulated to $950\text{ ppm}$ over sequential runs. Carbon dioxide acts as a radiative absorber and thermal diluent, systematically depressing flame temperatures across later runs in the same test sequence.

#### Audit Classification: `SCIENTIFICALLY UNSUPPORTED` (Sample sizes misstated; i.i.d. assumption violated by sample reuse)

---

## 3. Discrepancy Matrix: M9 Specification vs. Ground Truth

| Parameter / Feature | Claimed in M9 Specification Deliverables | Actual Physical Ground Truth in NASA BASS-II Files | Reviewer Finding & Impact |
| :--- | :--- | :--- | :--- |
| **Thick PMMA Low-O2 Runs** | Tested down to $14.5 - 15.0\% O_2$. | Miller's thick slabs were **strictly tested at $\ge 17.9\% O_2$** ($N=20$). | **Fatal Claim Discrepancy:** No LOI boundary exists in the data for thick slabs. |
| **Flow Calibration Formula** | Cubic polynomial: $U_\infty = \sum c_k S_{fan}^k$. | Linear formula: $U = 1.0066 \times (\text{Air Display})\text{ cm/s}$. | **Formula Discrepancy:** Cubic polynomial was fabricated. |
| **Fan & Air Display Format** | Single static numeric setpoints ($0 - 99$). | **75% complex strings** with dynamic multi-step sequences. | **Data Type Discrepancy:** Scalar assumptions will crash or misrepresent flows. |
| **CO Measurement Ranges** | Initial: $-3$ to $12\text{ ppm}$; Final: $-4$ to $40\text{ ppm}$. | Initial: $-3$ to **950 ppm**; Final: $0$ to **950 ppm + Saturation**. | **Range Error:** Misreported by a factor of $>23\times$; negative final CO does not exist. |
| **Biot Number Calculation** | Calculated using $k_s = 0.19\text{ W/m}\cdot\text{K}$ and $h_c = 15\text{ W/m}^2\text{K}$. | Parameters are **absent** from NASA archives. | **Fabrication:** Unmeasured constants imported from terrestrial textbooks. |
| **Nomex / Candle Sample Sizes** | Nomex $N = 8$; Candle $N = 8$. | Nomex **$N = 3$**; Candle **$N = 1$**. | **Sample Count Error:** Hallucinated sample sizes; cannot support statistical inference. |
| **Extinction Identification** | Identified by $\Delta X_{O2} < \epsilon$. | Identified by operator notes; prolonged burns have large $\Delta X_{O2}$. | **Physical Flaw:** Integrates total burn history, not extinction state. |
| **CSV "Notes" Column** | Claimed as Column 15 in CSV. | **There is no Notes column in the CSV.** Notes are inside Air/Fan cells. | **Schema Flaw:** Schema mapping was misaligned with raw CSV. |

---

## 4. Final Reviewer Verdict & Recommendations

### Overall Assessment
The M9 architectural specification contains significant scientific assumptions that fail verification against original NASA BASS-II files. If implemented as currently specified, the engine would produce invalid logistic regression boundaries, execute erroneous flow polynomials, fail on complex string values in flow fields, and report fabricated Biot numbers.

### Mandatory Pre-Implementation Adjustments
1. **Quarantine the Proposed LOI Logistic Regression Protocol (`M9-P6`):** BASS-II does not have sufficient low-oxygen extinction data for thick PMMA slabs ($N=0$ at $\le 16\% O_2$) or clean binary outcome tags.
2. **Replace Numerical Biot Numbers with Categorical Regimes:** Group materials strictly by PI and nominal geometry (Thin Films, Thick Slabs, Cylindrical Rods, Fabrics) without calculating pseudo-$Bi$ numbers.
3. **Correct Flow Calibration Logic:** Apply $U = 1.0066 \times (\text{Air Display})$ only to tests with steady scalar values; classify dynamic multi-step flow strings as `DYNAMIC_FLOW_SEQUENCE` rather than attempting scalar conversion.
4. **Enforce Anomaly Filters on Oxygen Depletion:** Exclude tests with gross recording errors (`B2, P22a, P22b, T28a, T28b`) and flag negative drift tests (`T5, T10, T12, T13, T23`).
5. **Acknowledge Pseudoreplication:** Group repeated burns on the same `Sample #` to avoid violating statistical independence.
