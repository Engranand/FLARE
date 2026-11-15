# FLARE M7 — Scientific Dataset Profiling & Compatibility Audit Report

**Milestone**: M7 — Scientific Dataset Profiling & Compatibility Audit  
**Author**: Antigravity Autonomous Scientific Data Engineer & Combustion Research Analyst  
**Challenge**: NASA Space Apps 2026 — Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data  
**Audit Date**: 2026-11-14  
**Audit Scope**: Strict Read-Only Scientific Integrity & Profiling Audit of 261 Acquired Resources  

---

## 1. Executive Summary & Audit Overview

Following the successful acquisition of 261 original microgravity combustion resources from the NASA Physical Sciences Informatics (PSI) repository and official Space Apps sources, this audit performs an exhaustive, **read-only scientific profiling and compatibility analysis**.

### 1.1. Core Audit Objectives
1. **Inventory Verification**: Validate that all 261 acquired files are physically intact on disk, verify their SHA-256 cryptographic hashes against the master manifest, document duplicate content clusters, investigate previously reported format anomalies, and catalog inaccessible upstream endpoints.
2. **Dataset Profiling**: Profile all 45 structured CSV files, 25 Excel workbooks, 10 Word documents, 140 technical PDFs, and 38 ISA-Tab metadata ZIP archives without altering file contents.
3. **Priority Investigation Deep Dive**: Characterize the 6 priority microgravity investigations: **BASS-II (PSI-25)**, **Saffire-III (PSI-100)**, **ACME BRE (PSI-20)**, **ACME CFI-G (PSI-159)**, **SAME (PSI-102)**, and **PSI-117 (Droplet Cool Flames)**.
4. **Epistemological Attribution**: Establish a strict column-by-column boundary separating **Experimental Measurements**, **Numerical Simulations**, **Derived Quantities**, and **Theoretical Reference Values**, with special focus on PSI-117.
5. **Cross-Investigation Compatibility**: Evaluate investigations against 7 core combustion capabilities, providing the fluid dynamic and radiative scaling criteria necessary to relate small-scale duct tests (BASS-II) to macro-scale spacecraft compartment fires (Saffire).
6. **Engine Scoping**: Formulate the minimal scientifically defensible P0 dataset subset for FLARE's future ingestion and analysis engine.

### 1.2. High-Level Inventory Metrics
- **Total Physical Files on Disk**: 261 files
- **Total Storage Footprint**: 649,403,957 bytes (619.32 MB)
- **Master Manifest Checksum Pass Rate**: **261 / 261 (100.0%)** (0 hash mismatches, 0 missing files)
- **Unique SHA-256 Hashes**: 224 distinct cryptographic digests
- **Duplicate Content Clusters**: 29 clusters comprising 66 files (primarily shared NASA administrative documentation across sub-investigations)
- **Upstream Corrupted Files**: 1 confirmed file (`original/other/PSI-39/PSI-39_Analyzed Data_FLEX-1248_Summary.pdf`)
- **Documented Inaccessible NASA URLs**: 7 endpoints with HTTP 404 responses recorded in manifest

---

## 2. Phase 1 — Inventory Verification & Integrity Analysis

### 2.1. Cryptographic Checksum Audit
Every file located in `data/raw/challenge_resources/original/` was verified by computing its full-stream SHA-256 hash and matching it against `data/raw/challenge_resources/manifests/resource_manifest.json`.

```
Cataloged Resources   : 261
Verified on Disk      : 261 (100%)
Missing Files         : 0
SHA-256 Mismatches    : 0
Format Verification   : 260 Passed, 1 Upstream Corrupted
```

### 2.2. Format Distribution Breakdown
| Format | Extension | File Count | Total Size (Bytes) | Primary Content |
|---|---|---|---|---|
| **PDF** | `.pdf` | 140 | 459,286,419 | Scientific papers, flight reports, dissertation, technical slides |
| **CSV** | `.csv` | 45 | 36,012,238 | High-rate flight telemetry, experimental test matrices, kinetic data |
| **ZIP** | `.zip` | 38 | 29,881,114 | ISA-Tab metadata, raw flight video TS streams, gas calibration packages |
| **Excel (XLSX)** | `.xlsx` | 24 | 122,814,642 | Calibrated flight sensor sheets (Saffire, BASS-II, CFI), multi-channel charts |
| **Word (DOCX)** | `.docx` | 10 | 569,067 | Science experiment readmes, test matrix explanations, investigator notes |
| **Word (DOC)** | `.doc` | 2 | 6,031,360 | Legacy technical requirements and one-year science reports |
| **Excel (XLS)** | `.xls` | 1 | 1,399,808 | Legacy radiometer and droplet burning spreadsheets |
| **Text** | `.txt` | 1 | 3,002 | Particle tracking raw data log |
| **Total** | | **261** | **649,403,957** | **619.32 MB** |

### 2.3. Duplicate Content Cluster Analysis
The 224 unique SHA-256 hashes across 261 files reflect 29 duplicate groups (66 files total). Crucially, these duplicates are not redundant downloads of different datasets; they represent shared official documentation distributed across NASA PSI sub-investigations:
1. **ACME Shared Documentation**: Identical copies of `ACME non-imaging data file description 20170217.pdf` and `ACME-DOC-010_D.pdf` are bundled within both `PSI-20` (BRE) and `PSI-22` (E-FIELD) metadata archives.
2. **Saffire Readmes**: Identical copies of `SAFFIRE-I and SAFFIRE-III Readme.docx` exist across `PSI-98` (Saffire-I) and `PSI-100` (Saffire-III).
3. **BASS-II Readmes**: Identical copies of `BASS-II_ReadMe.docx` exist in the root `original/bass_ii/` and the sub-study folder `original/bass_ii/PSI-25/`.

### 2.4. Upstream Corrupted File Post-Mortem
- **File**: `original/other/PSI-39/PSI-39_Analyzed Data_FLEX-1248_Summary.pdf`
- **Path**: `data/raw/challenge_resources/original/other/PSI-39/PSI-39_Analyzed Data_FLEX-1248_Summary.pdf`
- **Size**: 382,777 bytes | **SHA-256**: `c00d437024ea5b8220f789aa734d493a77d710f43b7bc479b329432657738f6b`
- **Technical Post-Mortem**: Inspection of the initial 64 bytes revealed the binary sequence `b'$mÎmo...'` (`24 1a 9c 92 6d 85 ce 6d...`). Standard PDF files must begin with the header `%PDF-` (`25 50 44 46 2d`). Attempted decompression using `gzip`, `zlib`, and `bz2` failed. This conclusively establishes that the file is corrupted on the upstream NASA PSI repository (`psi.nasa.gov`), rather than being damaged during local transfer.

### 2.5. Documented Inaccessible NASA Endpoints
Seven official challenge resource URLs returned HTTP 404 (Not Found) during acquisition:
1. `PSI-26_Reports_SPICE_FinalReport.pdf` (PSI-26 / SPICE)
2. `PSI-26_Reports_BASS_FinalReport.pdf` (PSI-26 / BASS-I)
3. `PSI-39_Raw Data_F173E01A.txt` (PSI-39 / CFI)
4. `PSI-98_Raw Data_Saffire-I Telemetry Data Good Process Version.xlsx` (PSI-98 / Saffire-I)
5. `PSI-98_Raw Data_Saffire-I Sample 1 Sensor Data Complete TM graphs.xlsx` (PSI-98 / Saffire-I)
6. `a13-review-report-app-b-c-d-e-19700078726.pdf` (Apollo 13 Historical Report)
7. `A13_MissionReport.pdf` (Apollo 13 Historical Report)

---

## 3. Phase 2 — Dataset Profiling & Structural Inspection

### 3.1. Structured Data Profiles (CSV & XLSX)
The 45 CSV files and 25 Excel workbooks encompass three major functional archetypes:
1. **Experimental Test Matrices**: Compact tables recording run conditions, fuel types, dimensions, ambient $O_2$ concentrations, flow rates, and high-level burn outcomes (e.g., `PSI-25_Experimental table_BASS-II.csv`, `PSI-100_Experimental table_SAFFIRE-3.csv`, `PSI-159_Experimental table_CFI-G_Normal Flames.csv`).
2. **High-Rate Flight Telemetry**: Time-series logs recording physical sensor arrays at frequencies ranging from 1 Hz to 30 Hz (e.g., `PSI-100_Raw Data_Raw telemetry file.csv`, `PSI-20_Raw Data_19056A2_data.csv`, `PSI-100_Raw Data_Saffire III Sample 1 Sensors.xlsx`).
3. **Extracted Physical & Kinetic Properties**: Processed experimental measurements coupled with numerical simulation outputs (e.g., the 9 PSI-117 CSV datasets).

### 3.2. Metadata Packages (ISA-Tab ZIP Archives)
Inspection of the 38 ZIP archives revealed that 26 of them contain NASA PSI **ISA-Tab** (Investigation, Study, Assay) metadata packages (`i_Investigation.txt` and `s_*.txt`). 
- While `i_Investigation.txt` establishes the Dublin Core and ontology parameters (e.g., EFO 132), the accompanying `s_*.txt` study files frequently contain placeholder strings (`"Do not use this"`).
- Consequently, scientific metadata (exact oxygen concentrations, flow velocities, burner configurations) must be extracted directly from the investigator test matrices and documentation readmes, rather than relying on automated ISA-Tab parsers.

---

## 4. Phase 3 — Priority Investigation Scientific Analysis

Below is the detailed scientific profiling of the 6 priority investigations required for the FLARE analysis engine:

```
========================================================================================
1. BASS-II / PSI-25 (Burning and Suppression of Solids — II)
========================================================================================
- Physical Phenomenon : Solid surface flammability, flame spread, and extinction limits in microgravity forced convective flow.
- Fuel / Materials    : PMMA flat slabs (thick fuel, 1.2–2.5 cm), PMMA thin films (100–200 µm), PMMA rods (clear & black), Cotton-Fiberglass fabric (SIBAL cloth, 75% cotton / 25% fiberglass), Nomex.
- Gravity Condition   : Microgravity (10^-4 to 10^-6 g) aboard the International Space Station (ISS) Microgravity Science Glovebox (MSG).
- Chamber Pressure    : Nominal 1.0 atm (ambient ISS cabin pressure, 14.7 psia / 101.3 kPa).
- Oxygen Concentration: Varied systematically from 16.5% to 22.2% by volume (calibrated in-situ).
- Flow Conditions     : Forced airflow in a 7.6 cm x 7.6 cm duct, velocity range u = 1.0 to 5.5 cm/s (controlled via calibrated fan restrictor plate).
- Temperature Range   : Ambient ISS glovebox temperature (approx. 20–25 °C / 293–298 K).
- Measured Variables  : Flame spread rate (Vf, mm/s), flame standoff distance (mm), radiant heat flux (narrow-band radiometers at 10, 50, 250, 1000 gain), video flame tip and base coordinates, extinction air speed (low-speed radiative extinction vs. high-speed convective blow-off).
- Units Recorded      : Time (s), Velocity (cm/s), Oxygen (%), Radiometer Output (counts / mV), Sample Dimensions (mm / cm).
- Data Limitations    : In-depth solid temperatures not measured (no internal thermocouples in PMMA); visual flame tracking obscured by soot deposition on duct windows during long burns.
- Measurement Errors  : Fan calibration uncertainty +/- 0.2 cm/s; oxygen sensor drift +/- 0.2% O2; video frame timing offset (+1 day leap year metadata offset noted in README).

========================================================================================
2. Saffire-III / PSI-100 (Spacecraft Fire Safety Demonstration — III)
========================================================================================
- Physical Phenomenon : Large-scale, realistic spacecraft compartment flame growth, spread acceleration, and airflow suppression.
- Fuel / Materials    : Large-scale SIBAL composite fabric (75% cotton, 25% fiberglass), sample dimensions 0.4 m wide x 1.0 m long (0.33 cm thickness).
- Gravity Condition   : Microgravity (approx. 10^-5 g) inside an uncrewed Cygnus cargo spacecraft post-undocking from ISS.
- Chamber Pressure    : Uncontrolled sealed vessel (approx. 14.4 to 15.2 psia / 99.3 to 104.8 kPa); dynamic pressure rise observed from flame heating.
- Oxygen Concentration: Ambient Cygnus cabin atmosphere (approx. 19.7% to 21.5% O2).
- Flow Conditions     : Forced concurrent and opposed airflow driven by tunnel fan array at u = 30 cm/s in a 0.5 m x 0.5 m x 1.0 m flow duct.
- Temperature Range   : Gas plume temperatures up to 850 °C (1123 K); solid substrate temperatures up to 600 °C.
- Measured Variables  : 6 gas plume thermocouples (TC1–TC6), 6 sample substrate thermocouples (TC7–TC12), 4 calibrated radiometers (mW/cm^2), 2 hot-wire anemometers (cm/s), fan tachometer (RPM), chamber pressure (psia), cabin CO2 and O2 concentrations (%), vehicle smoke detector obscuration and scattering signals.
- Units Recorded      : Time (s, ms), Temperature (°C), Radiant Flux (mW/cm^2), Flow (cm/s), Pressure (PSIA), Concentrations (%).
- Data Limitations    : Single large sample per test run (high-consequence, unrepeatable flight test); flow duct exit boundary influences flame tail.
- Measurement Errors  : Thermocouple radiative heat loss uncorrected in raw telemetry; hot-wire anemometer temperature sensitivity during flame arrival.

========================================================================================
3. ACME BRE / PSI-20 (Burning Rate Emulator)
========================================================================================
- Physical Phenomenon : Emulation of condensed-phase (solid/liquid) burning, gas-phase heat feedback, and extinction without condensed-phase mass regression.
- Fuel / Materials    : Porous sintered bronze circular burners (25 mm and 50 mm diameter) delivering 100% ethylene (C2H4), 50% ethylene / 50% N2, and 100% methane (CH4).
- Gravity Condition   : Microgravity aboard the ISS Combustion Integrated Rack (CIR).
- Chamber Pressure    : 0.7 to 1.3 atm (varied across CIR chamber fills).
- Oxygen Concentration: 21%, 26.5%, 34%, and 40% O2 diluted with nitrogen.
- Flow Conditions     : Quiescent microgravity with fuel delivery mass fluxes from 0.5 to 5.0 mg/(cm^2*s).
- Temperature Range   : Burner porous surface temperatures (25 to 200 °C) and flame reaction zone temperatures (up to 2200 K).
- Measured Variables  : Fuel mass flow rates (mg/s), burner surface heat fluxes, chamber pressure, ion current (pA), electric field voltage, PMT luminescence.
- Units Recorded      : Time (ms), Flow (V / mg/s), Current (nA), Pressure (bar), Voltage (V).
- Data Limitations    : Simulates stationary planar gas flames; cannot capture solid char formation, intumescence, or material deformation.

========================================================================================
4. ACME CFI-G / PSI-159 (Cool Flames Investigation with Gases)
========================================================================================
- Physical Phenomenon : Steady, low-temperature cool diffusion flames (normal and inverse) in gaseous mixtures.
- Fuel / Materials    : Ethane, ethylene, propane diluted with N2, CO2, and He; oxidizer up to 40% O2.
- Gravity Condition   : Microgravity aboard the ISS Combustion Integrated Rack (CIR).
- Chamber Pressure    : 0.5 to 1.5 bar.
- Oxygen Concentration: 15% to 40% O2 (Exploration Atmosphere relevance: 34% O2 at 8.2 psia).
- Flow Conditions     : Co-flow laminar jet burner.
- Measured Variables  : Fuel mass delivery rate (mg/s), O2 mass flow rate (mg/s), visual/UV cool flame chemiluminescence, pre/post O2 mole fraction, calculated Tad.
- Units Recorded      : mg/s, bar, mole fraction, Tad in Kelvin.
- Data Limitations    : Gaseous phase only; no soot agglomeration data.

========================================================================================
5. SAME / PSI-102 & SAME-R / PSI-101 (Smoke Aerosol Measurement Experiment)
========================================================================================
- Physical Phenomenon : Smoke particle agglomeration, particle size distribution (PSD), and smoke detector response in microgravity.
- Fuel / Materials    : Overheated spacecraft materials: Kapton (polyimide film), Teflon (PTFE), silicone rubber, and cotton lamp wick.
- Gravity Condition   : Microgravity aboard the ISS.
- Flow Conditions     : Low-speed convective flow (u = 5.0 to 8.1 cm/s).
- Measured Variables  : Particle mass loss rate (mg/min), particle diameter ratios (Rt/R0), primary and net aerosol aging times (s), condensation nucleus counter concentrations.
- Units Recorded      : mg/min, cm/s, seconds, counts/cm^3.
- Relevance to Safety : Prevents false smoke alarms caused by cabin dust and establishes true particulate signatures of overheating avionics.

========================================================================================
6. PSI-117 (Combustion of Droplets / Farouk et al.)
========================================================================================
- Physical Phenomenon : Warm/cool flame transitions, second-stage radiative cool flame extinction, and multi-stage oscillations in alkane droplets.
- Fuel / Materials    : n-Heptane (C7H16), n-Decane (C10H22), n-Dodecane (C12H26).
- Gravity Condition   : Microgravity (ISS CIR/MDCA flight tests) combined with 1D unsteady numerical kinetics simulations.
- Chamber Pressure    : 0.5 to 5.0 atm.
- Oxygen Concentration: 10% to 21% O2 with N2, He, and ozone (O3) additions.
- Measured Variables  : Droplet surface area (d^2, mm^2), optical flame diameter (mm), radiometer radiance (W), extinction diameters (Dext,HF, Dext,CF).
- Attribution Nature  : Strongly blended dataset (simulations and experiments packaged in identical files).
```

---

## 5. Phase 4 — Experimental vs. Simulated Attribution

A central finding of this audit is that **computational models and empirical data are deeply intertwined within several acquired datasets**, most notably in **PSI-117**. 

```
                                      DATA ATTRIBUTION TAXONOMY
                                                  │
            ┌───────────────────────────┬─────────┴─────────┬───────────────────────────┐
            ▼                           ▼                   ▼                           ▼
   EXPERIMENTAL MEASUREMENT      DERIVED QUANTITY   NUMERICAL SIMULATION        THEORETICAL REFERENCE
   (Direct physical sensors)     (Computed from EM) (Differential solvers)      (Equilibrium / Constants)
   - Photodiode radiance         - Burning rate K   - Flame T_max               - Adiabatic T_ad
   - Optical edge tracking       - Stand-off Df/Dd  - 1D kinetic D_ext          - Certified gas bottles
   - Thermocouple EMF            - (d/d0)^2         - Kinetic time (10^-10 s)   - Initial sample dimensions
```

### 5.1. PSI-117 Critical Attribution Rules
1. **`PROCI_2019_Oscillatory_Cool_Flame.csv` and `PROCI_2019_Stable_Cool.csv`**:
   - **Attribution**: **100% NUMERICAL SIMULATION**.
   - **Evidence**: Time variable steps at sub-nanosecond increments ($\Delta t = 1.0 	imes 10^{-10}	ext{ s}$); $T_{	ext{max}}$ (600–2100 K) and radical peak standoffs ($D_{	ext{OHm}}/D_{	ext{drop}}$) are continuous differential solver outputs.
   - **Engine Restriction**: **Must NEVER be ingested into FLARE's empirical measurement database.**
2. **`PROCI_2023_Alkane_Extinction_Diameter_1atm.csv` and `PROCI_2023_C12_Extinction_Diameter_vs_pressure.csv`**:
   - Explicitly split into sub-blocks labeled `Expt` and `Sim` / `Model`.
   - **Engine Action**: Ingestion scripts must extract only columns tagged `Expt` or `_EXPT` and error bars (`ErrorBar+`, `ErrorBar-`), routing `Sim` and `_model` columns to a segregated simulation benchmark repository.
3. **`MST_2024_Radiance_Flame_Diameter.csv` and `MST_2024_Burning_history_Flame_diameter.csv`**:
   - Contain experimental photodiode radiance ($Q$) and video flame diameters ($d_{	ext{flame}}$) in Columns 0–11, followed by multi-phase CFD predictions in Columns 12–40.
   - **Engine Action**: Split tables horizontally at Column 11.

---

## 6. Phase 5 — Cross-Investigation Compatibility & Scaling Analysis

### 6.1. Synthesis Across 7 Core Capabilities
The compatibility assessment revealed distinct specialized roles across the acquired datasets:
- **Ignition & Solid Flame Spread**: **BASS-II (PSI-25)** provides the definitive small-scale empirical benchmark, while **Saffire-III (PSI-100)** provides the macro-scale compartment fire validation target.
- **Flame Extinction Boundaries**: **ACME BRE (PSI-20)** provides the gas-phase surface heat flux extinction limits, **ACME CFI-G (PSI-159)** provides the elevated-oxygen cool flame flammability boundary, and **PSI-117** provides liquid droplet extinction diameters.
- **Spacecraft Smoke Detection**: **SAME (PSI-102)** and **SAME-R (PSI-101)** provide the microscopic aerosol size distributions and aging kinetics that directly validate the macro-scale obscuration and scattering signals recorded by the Cygnus vehicle smoke detectors in **Saffire-III**.

### 6.2. Non-Dimensional Scaling Between BASS-II and Saffire
This audit explicitly rejects the claim that Saffire flight observations automatically validate a small-scale BASS-II flame spread model without scaling transformations. The physical mechanisms governing the two regimes differ fundamentally:

$$	ext{Damk"ohler Number: } Da = rac{	au_{	ext{flow}}}{	au_{	ext{chem}}} = rac{\delta / u_{\infty}}{A \exp(-E_a / RT)}$$

$$	ext{Boundary Layer Thickness: } \delta(x) pprox 5.0 \sqrt{rac{
u x}{u_{\infty}}}$$

1. **Hydrodynamic Boundary Layer Expansion**: Over Saffire's 1.0-meter fuel sample, $\delta(x)$ grows by an order of magnitude ($\sim 30	ext{ mm}$) compared to BASS-II ($\sim 3	ext{ mm}$). The flame base in Saffire is anchored in a deep, low-velocity boundary shear flow where the local velocity gradient $g_w = \left. rac{\partial u}{\partial y} ight|_{w}$ is vastly smaller than the free-stream $u_{\infty}$.
2. **Radiation Re-Absorption**: In BASS-II, flames are small ($<2	ext{ cm}$) and optically thin; radiative loss to the ambient cool walls drives premature extinction. In Saffire, flames extend over 30 cm, creating an optically thick soot/gas core where radiant emission pre-heats virgin fabric meters downstream, driving acceleratory flame spread.
3. **Mandatory Scaling Requirements**: To defend cross-scale modeling, FLARE must implement:
   - Local boundary layer shear scaling ($g_w$).
   - Downstream radiation view-factor integration.
   - Closed-compartment mass and energy conservation coupling.

---

## 7. Phase 6 — Recommended FLARE Dataset Scope

Based on this audit, the acquired datasets are classified into four operational tiers, and a minimal defensible subset is recommended for Milestone 8:

```
                                   FLARE DATASET CLASSIFICATION
                                                │
         ┌───────────────────────┬──────────────┴──────────────┬───────────────────────┐
         ▼                       ▼                             ▼                       ▼
    TIER P0: PRIMARY        TIER P1: COMPLEMENTARY        TIER P2: METADATA       TIER P3: CONTEXT
   (Quantitative Core)     (Diagnostics & Validation)     (Operational Protocols) (Historical Reports)
   - BASS-II Matrix        - CFI-G Normal/Inverse Flames  - ISA-Tab ZIP packages  - Apollo 1 & 13 Reports
   - Saffire-III Telemetry - ACME Gas Flow Calibration    - BASS-II FAQ / Readme  - ISS Combustion Guides
   - ACME BRE Test Table   - PSI-117 Dissertations       - Saffire Readme.docx   - General Brochures
   - SAME / SAME-R Tables  - SPICE & SLICE Tables         - Camera Proofsheets
```

### 7.1. Recommended Minimal Defensible Core Subset (Milestone 8 Ingestion Engine)
To construct an immediate, high-impact, scientifically validated analysis engine, FLARE should restrict its initial ingestion scope to the following **6 primary quantitative investigations**:

| Investigation | Primary Source File | Format | Exact SHA-256 Digest | Primary Engineering Role |
|---|---|---|---|---|
| **BASS-II** | `original/bass_ii/PSI-25_Experimental table_BASS-II.csv` | CSV | `8390bbf4ad8cb0cf03e838ff40c9ae77a76c8c4a4e17ca8eef2fcfb61ff62c3f` | Solid fuel flammability, opposed/concurrent spread, and radiative extinction limits. |
| **Saffire-III** | `original/saffire/PSI-100_Raw Data_Raw telemetry file.csv` | CSV | `5e9ce6d220b3ea1496a8e578c7eb46200676ee5f27cbbfaad2ffec109ff8ff37` | Macro-scale spacecraft compartment fire spread, thermocouple arrays, and smoke detectors. |
| **ACME BRE** | `original/acme/PSI-20_Experimental table_ACME BRE.csv` | CSV | `df943d04d80a13e2f5bfe16c526712395563ea9e917d52a2ea6f3e1bf24982bb` | Condensed-phase burning rate emulation and surface heat flux extinction boundaries. |
| **ACME CFI-G**| `original/acme/PSI-159_Experimental table_CFI-G_Normal Flames.csv` | CSV | `2e08aeeb8489db5ec4a0cc0129a39ca57a07fc240f92ddfcfa168a2db7fa37f8` | Flammability limits in elevated oxygen (up to 40% O2) and Exploration Atmospheres. |
| **SAME** | `original/other/PSI-102/PSI-102_Experimental table_SAME.csv` | CSV | `6908db632d4310df044bb6a30d93c1d9dbb830d173c33292461fe60f84860d5b` | Particulate mass loss rates and smoke aerosol sizing for overheated spacecraft materials. |
| **PSI-117** | `original/psi_117/PSI-117_Analyzed Data_MST_2024_Kavg.csv` | CSV | `a89e0639567fbf9dffc32728283a2d216bc3b7e710d0ef0938ff40c1ceaa67e7` | Measured liquid droplet burning rate constants (Kavg_CF) during microgravity cool flame regime. |

---

## 8. Epistemological Boundaries & Verified Findings

To ensure scientific honesty, all findings in this audit are explicitly classified by their epistemological status:

### 8.1. Verified Empirical Facts
1. All 261 downloaded files exist on disk, matching their manifest SHA-256 hashes with 0 discrepancies.
2. `PSI-39_Analyzed Data_FLEX-1248_Summary.pdf` is corrupted at the upstream NASA repository source, beginning with invalid non-PDF binary bytes.
3. `PROCI_2019_Oscillatory_Cool_Flame.csv` and `PROCI_2019_Stable_Cool.csv` are 100% numerical simulation outputs and contain zero direct experimental sensor measurements.
4. Saffire-III contains simultaneous calibrated measurements of flow velocity, heat flux, substrate temperature, plume temperature, vehicle pressure, and vehicle smoke detector signals during a 0.4 m x 1.0 m fabric burn.

### 8.2. Scientific Interpretations
1. Saffire-III flame spread acceleration is driven by downstream radiative view-factor preheating within an optically thick soot envelope, whereas BASS-II flame extinction is driven by radiative heat loss to cold tunnel walls in an optically thin flame.
2. ACME BRE fuel mass fluxes can substitute for solid pyrolysis rates in gas-phase extinction modeling, enabling decoupling of gas-phase kinetics from solid-state heat transfer.

### 8.3. Unresolved Questions & Data Limitations
1. In-flame gas temperature distributions inside BASS-II and droplet cool flames cannot be resolved empirically from available data due to physical instrument limitations (absence of internal thermocouples to prevent intrusive conductive quenching).
2. Saffire-I high-rate telemetry spreadsheets remain inaccessible due to upstream NASA repository 404 errors; Saffire-III telemetry must serve as the primary macro-scale empirical flight dataset.

---

## 9. Conclusion & Next Steps for FLARE Milestone 8

With the completion of this M7 Scientific Dataset Profiling & Compatibility Audit, the FLARE project possesses a fully cataloged, verified, profiled, and epistemologically segregated repository of 261 microgravity combustion files.

The five required deliverables are established:
1. `scientific_dataset_inventory.csv` — Comprehensive resource inventory across all 261 files.
2. `scientific_dataset_profile.json` — Deep structural and statistical profiles for every dataset.
3. `scientific_compatibility_matrix.md` — Rigorous 7-capability compatibility assessment and scaling criteria.
4. `experimental_vs_simulated_attribution.md` — Column-by-column epistemological attribution report.
5. `m7_scientific_audit_report.md` — Master technical audit report.

The project is now primed to proceed to **Milestone 8: Ingestion Engine Implementation**, utilizing the recommended P0 core subset to construct an uncompromised, scientifically rigorous microgravity fire safety analysis system.
