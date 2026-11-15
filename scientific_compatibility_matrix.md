# FLARE — Scientific Compatibility Matrix

**Milestone**: M7 — Scientific Dataset Profiling & Compatibility Audit  
**Author**: FLARE Scientific Data Engineering & Combustion Research Analyst  
**Date**: 2026-11-14  
**Audit Scope**: Cross-Investigation Scientific Compatibility Assessment for FLARE Analysis Engine  

---

## 1. Compatibility Classification Framework

To ensure scientifically defensible integration into FLARE's future analysis engine, all acquired microgravity investigations are evaluated across **7 core spacecraft fire safety analysis capabilities**:

1. **Ignition Analysis**: Capability to evaluate minimum ignition energy, igniter surface heating, ignition delay, and transition to self-sustained combustion.
2. **Flame Spread Analysis**: Capability to model and predict concurrent (forward) and opposed flame spread rates ($V_f$) across fuel surfaces.
3. **Flame Extinction Analysis**: Capability to predict low-speed radiative extinction, high-speed blow-off, and low-temperature cool flame extinction boundaries.
4. **Burning Rate Analysis**: Capability to quantify solid regression rates, liquid mass loss rate constants ($K$), or equivalent gaseous fuel mass fluxes ($\dot{m}''$).
5. **Oxygen / Atmospheric Analysis**: Capability to evaluate flammability limits across variable $O_2$ concentrations ($10\% - 40\%$), sub-atmospheric to elevated pressures ($0.5 - 5.0\text{ atm}$), and diluent gases ($N_2, CO_2, He$).
6. **Smoke Detection Analysis**: Capability to evaluate particulate agglomeration, particle size distributions, smoke aging, and optical obscuration / scattering detector signatures.
7. **Spacecraft-Scale Fire Analysis**: Capability to inform realistic compartment-scale fires ($>0.5\text{ m}$ sample scale, enclosure thermodynamics, ECLS interaction).

### Evaluation Ratings:
- **DIRECTLY COMPARABLE**: Identical physical geometry, governing equations, and boundary conditions; quantitative measurements can be ingested into a single statistical or physical model without empirical scaling factors.
- **COMPLEMENTARY**: Investigates the same underlying physical mechanism or chemical regime but in a different geometric configuration, scale, or phase; requires explicit non-dimensional scaling laws (e.g., Damköhler, Reynolds, Spalding numbers) for joint modeling.
- **QUALITATIVE ONLY**: Informs physical understanding, soot mechanics, or qualitative flame behavior, but lacks compatible geometry or quantitative overlap for direct numerical fusion.
- **NOT COMPARABLE**: Fundamentally disparate combustion regime, physical state, or invalid geometry (e.g., trying to directly predict solid fabric flame spread from spherical gas burner liftoff).
- **INSUFFICIENT EVIDENCE**: Available datasets lack sufficient documentation, transducer calibration data, or operational parameters to establish scientific comparability.

---

## 2. Master Scientific Compatibility Matrix

The matrix below maps each candidate investigation group against the 7 core analysis capabilities:

| Investigation ID & Group | 1. Ignition Analysis | 2. Flame Spread Analysis | 3. Flame Extinction Analysis | 4. Burning Rate Analysis | 5. Oxygen / Atmosphere | 6. Smoke Detection | 7. Spacecraft Scale Fire |
|---|---|---|---|---|---|---|---|
| **BASS-II (PSI-25)** | **DIRECTLY COMPARABLE** | **DIRECTLY COMPARABLE** | **DIRECTLY COMPARABLE** | **DIRECTLY COMPARABLE** | **DIRECTLY COMPARABLE** | **QUALITATIVE ONLY** | **COMPLEMENTARY** |
| **BASS-I (PSI-26)** | **DIRECTLY COMPARABLE** | **DIRECTLY COMPARABLE** | **DIRECTLY COMPARABLE** | **DIRECTLY COMPARABLE** | **COMPLEMENTARY** | **QUALITATIVE ONLY** | **COMPLEMENTARY** |
| **Saffire-III (PSI-100)** | **COMPLEMENTARY** | **COMPLEMENTARY** | **COMPLEMENTARY** | **COMPLEMENTARY** | **COMPLEMENTARY** | **DIRECTLY COMPARABLE** | **DIRECTLY COMPARABLE** |
| **Saffire-I (PSI-98)** | **COMPLEMENTARY** | **COMPLEMENTARY** | **COMPLEMENTARY** | **COMPLEMENTARY** | **COMPLEMENTARY** | **QUALITATIVE ONLY** | **DIRECTLY COMPARABLE** |
| **Saffire-II (PSI-99)** | **COMPLEMENTARY** | **COMPLEMENTARY** | **COMPLEMENTARY** | **COMPLEMENTARY** | **COMPLEMENTARY** | **QUALITATIVE ONLY** | **COMPLEMENTARY** |
| **ACME BRE (PSI-20)** | **COMPLEMENTARY** | **NOT COMPARABLE** | **DIRECTLY COMPARABLE** | **DIRECTLY COMPARABLE** | **DIRECTLY COMPARABLE** | **QUALITATIVE ONLY** | **COMPLEMENTARY** |
| **ACME CFI-G (PSI-159)** | **COMPLEMENTARY** | **NOT COMPARABLE** | **DIRECTLY COMPARABLE** | **COMPLEMENTARY** | **DIRECTLY COMPARABLE** | **QUALITATIVE ONLY** | **NOT COMPARABLE** |
| **SAME (PSI-102)** | **NOT COMPARABLE** | **NOT COMPARABLE** | **NOT COMPARABLE** | **COMPLEMENTARY** | **QUALITATIVE ONLY** | **DIRECTLY COMPARABLE** | **COMPLEMENTARY** |
| **SAME-R (PSI-101)** | **NOT COMPARABLE** | **NOT COMPARABLE** | **NOT COMPARABLE** | **COMPLEMENTARY** | **QUALITATIVE ONLY** | **DIRECTLY COMPARABLE** | **COMPLEMENTARY** |
| **DAFT (PSI-47)** | **NOT COMPARABLE** | **NOT COMPARABLE** | **NOT COMPARABLE** | **NOT COMPARABLE** | **NOT COMPARABLE** | **DIRECTLY COMPARABLE** | **COMPLEMENTARY** |
| **PSI-117 (Cool Flames)** | **COMPLEMENTARY** | **NOT COMPARABLE** | **DIRECTLY COMPARABLE** | **DIRECTLY COMPARABLE** | **DIRECTLY COMPARABLE** | **QUALITATIVE ONLY** | **NOT COMPARABLE** |
| **FLEX Suite (PSI-39/68/69)**| **COMPLEMENTARY** | **NOT COMPARABLE** | **DIRECTLY COMPARABLE** | **DIRECTLY COMPARABLE** | **COMPLEMENTARY** | **QUALITATIVE ONLY** | **NOT COMPARABLE** |
| **ACME Suite (10/21/22/23)**| **QUALITATIVE ONLY** | **NOT COMPARABLE** | **COMPLEMENTARY** | **QUALITATIVE ONLY** | **COMPLEMENTARY** | **COMPLEMENTARY** | **NOT COMPARABLE** |
| **SLICE & SPICE (106/107)** | **QUALITATIVE ONLY** | **NOT COMPARABLE** | **COMPLEMENTARY** | **QUALITATIVE ONLY** | **COMPLEMENTARY** | **DIRECTLY COMPARABLE**| **NOT COMPARABLE** |
| **Modeling (60/62/115/142)** | **QUALITATIVE ONLY** | **QUALITATIVE ONLY** | **QUALITATIVE ONLY** | **QUALITATIVE ONLY** | **QUALITATIVE ONLY** | **QUALITATIVE ONLY** | **QUALITATIVE ONLY** |

---

## 3. Scientific Rationale by Analysis Capability

### 3.1. Flame Spread & Extinction: BASS-II vs. Saffire-III
- **BASS-II (PSI-25)**: Evaluates flame spread over thin PMMA films (100–200 $\mu$m), thick PMMA slabs (1.2–2.5 cm), PMMA rods, and SIBAL cloth in a small flow duct ($7.6\text{ cm} \times 7.6\text{ cm}$) at low flow velocities ($1.0 - 5.5\text{ cm/s}$) and variable oxygen concentrations ($16.5\% - 22.2\%$). It provides the fundamental benchmark for microgravity flame spread and extinction limits.
- **Saffire-III (PSI-100)**: Evaluates flame spread over a large SIBAL cloth sample ($0.4\text{ m} \times 1.0\text{ m}$) inside the Cygnus pressurized cargo vehicle at an airflow of $30\text{ cm/s}$.
- **Compatibility Classification**: **COMPLEMENTARY (Not Automatically Validating)**.

#### Critical Scientific Analysis: Why Saffire Does NOT Automatically Validate BASS-II at Spacecraft Scale
It is scientifically invalid to claim that a small-scale BASS-II flame spread model is automatically validated by Saffire flight observations without rigorous multi-scale boundary layer and radiation scaling. The governing physics change dramatically across these two experimental regimes:

1. **Boundary Layer Growth & Hydrodynamic Confinement**:
   - In BASS-II, the sample length is small ($L \sim 5 - 10\text{ cm}$), and the flow tunnel cross-section is restricted ($7.6\text{ cm} \times 7.6\text{ cm}$). The boundary layer $\delta(x) \sim \sqrt{\nu x / u_\infty}$ remains thin ($\sim 2 - 5\text{ mm}$), and duct sidewalls impose significant boundary shear and 2D velocity profile distortion.
   - In Saffire, the sample is 1.0 meter long, and the flow channel cross-section is $0.5\text{ m} \times 0.5\text{ m}$. Over a 1-meter span at $u_\infty = 20 - 30\text{ cm/s}$, the boundary layer grows to over $30\text{ mm}$, transitioning from laminar to perturbed shear flow. The flame base experiences a locally sheared velocity gradient that is far lower than the free-stream velocity $u_\infty$.

2. **Thermal Radiation Feedback & Optical Thickness**:
   - In BASS-II, the flame is small and optically thin (emissivity $\epsilon_{flame} \ll 1$). Radiant emission escapes directly to the surrounding ambient walls with negligible self-absorption, causing severe radiative cooling that drives low-speed radiative extinction ($u_\infty < 1\text{ cm/s}$).
   - In Saffire, the continuous burning zone extends for tens of centimeters. The large flame volume produces high concentrations of soot and hot $CO_2/H_2O$, becoming optically thick. Significant radiative energy is re-absorbed internally and emitted directly forward onto the unburned downstream fabric, driving acceleratory flame spread ($V_f > 2\text{ mm/s}$) that does not occur in small-scale BASS-II tests.

3. **Oxygen Depletion & Enclosure Feedback**:
   - BASS-II runs in the ISS Microgravity Science Glovebox where total consumed oxygen is negligible compared to the chamber volume, maintaining near-constant ambient $X_{O2}$.
   - Saffire burns inside a sealed, isolated Cygnus vehicle ($20\text{ m}^3$). Combustion consumes significant vehicle oxygen and releases thousands of liters of hot expansion gases, altering cabin pressure and gas density dynamically during the burn.

#### Necessary Validation Requirements to Bridge BASS-II and Saffire:
To scientifically defend using BASS-II models for Saffire-scale predictions, the FLARE engine must satisfy four mandatory scaling criteria:
1. **Local Boundary Layer Scaling**: Transform free-stream velocity $u_\infty$ to the local velocity gradient at the flame base $g_w = \left. \frac{\partial u}{\partial y} \right|_{y=0}$ using non-similar boundary layer formulations.
2. **Radiation View Factor Integration**: Incorporate a multi-dimensional radiation transfer model (DOM or P1 approximation) that accounts for geometric view factors and radiative preheating of the downstream virgin fabric.
3. **Damköhler Number Matching**: Ensure the gas-phase Damköhler number $Da = \tau_{flow} / \tau_{chem} = \frac{\alpha / u^2}{A \exp(-E_a/RT)}$ properly accounts for the order-of-magnitude increase in residence time over large fuel lengths.
4. **Enclosure Mass & Energy Balance**: Couple the local solid pyrolysis model to the Cygnus global pressure rise and $O_2$ consumption rate equations.

---

### 3.2. Condensed-Phase Burning Rate: BASS-II vs. ACME BRE (PSI-20)
- **ACME BRE (PSI-20)**: Uses a porous metal gas burner (25 mm and 50 mm diameter) burning gaseous ethylene/nitrogen mixtures to emulate solid or liquid fuels without the complications of solid surface regression or in-depth heat conduction.
- **Compatibility Classification**: **DIRECTLY COMPARABLE for Gas-Phase Extinction & Heat Flux; COMPLEMENTARY for Mass Loss**.
- **Scientific Rationale**: BRE directly measures the required fuel mass flux $\dot{m}''_{fuel}$ and surface radiative heat flux $q''_{rad}$ necessary to sustain a flame against varying convective airflow and oxygen levels. This enables FLARE to validate gas-phase extinction sub-models independent of solid-state pyrolysis uncertainties.

---

### 3.3. Low-Temperature Kinetics & Exploration Atmospheres: PSI-117 vs. ACME CFI-G (PSI-159)
- **PSI-117 (Farouk et al.)**: Droplet cool flame transitions in alkanes ($n$-heptane, $n$-dodecane) across pressures ($0.5 - 5.0\text{ atm}$).
- **ACME CFI-G (PSI-159)**: Gaseous cool flames burning ethane and ethylene in normal and inverse diffusion geometries in elevated oxygen environments ($XO_2$ up to $40\%$).
- **Compatibility Classification**: **COMPLEMENTARY**.
- **Scientific Rationale**: Both investigations probe the negative temperature coefficient (NTC) regime ($600 - 800\text{ K}$) and low-temperature peroxide chain branching. CFI-G provides gaseous flame extinction limits under NASA Exploration Atmospheres ($34\%\text{ O}_2$ at $8.2\text{ psia}$), while PSI-117 provides liquid-fuel droplet cool flame extinction diameters ($D_{ext,CF}$). Together, they form an empirical foundation for fire extinction under exploration conditions.

---

### 3.4. Spacecraft Smoke Detection: SAME (PSI-102), SAME-R (PSI-101), DAFT (PSI-47) vs. Saffire-III
- **SAME / SAME-R / DAFT**: Measures smoke particle agglomeration, aerodynamic particle diameters, and mass loss rates from pyrolyzed spacecraft materials (Kapton, Teflon, silicone, cotton).
- **Saffire-III (PSI-100)**: Contains flight operational telemetry from the Cygnus vehicle smoke detectors (`P@CDH_F1PCM_SMK_DET_OBS_SENS_P` and `SMK_DET_SCAT_SENS_P`).
- **Compatibility Classification**: **DIRECTLY COMPARABLE for Detector Response; COMPLEMENTARY for Aerosol Evolution**.
- **Scientific Rationale**: SAME provides the particle size distribution ($d_p \sim 0.1 - 10\text{ }\mu\text{m}$) and aging coagulation kinetics in microgravity, which directly govern the light scattering and optical obscuration signals recorded by the operational smoke detectors during the Saffire-III burn.

---

## 4. Minimum Defensible Dataset Subset for Milestone 8 (Analysis Engine Core)

To build a scientifically robust, defensible analysis engine without unmanageable complexity, FLARE should restrict its first core ingestion engine to the following **Primary Quantitative Core (P0 Subset)**:

1. **Benchmark Solid Flammability**: `original/bass_ii/PSI-25_Experimental table_BASS-II.csv` (BASS-II empirical flight matrix).
2. **Spacecraft-Scale Multi-Sensor Telemetry**: `original/saffire/PSI-100_Raw Data_Raw telemetry file.csv` & `Saffire III Sample 1 Sensors.xlsx` (Thermocouple array, radiometers, flow anemometry, vehicle smoke detectors).
3. **Condensed Phase Burning Rate Emulator**: `original/acme/PSI-20_Experimental table_ACME BRE.csv` (Calibrated fuel mass fluxes and surface heat fluxes).
4. **Elevated Oxygen Cool Flame Extinction**: `original/acme/PSI-159_Experimental table_CFI-G_Normal Flames.csv` & `Inverse Flames.csv` (Flammability boundaries in Exploration Atmospheres).
5. **Microgravity Smoke Agglomeration**: `original/other/PSI-102/PSI-102_Experimental table_SAME.csv` & `original/other/PSI-101/PSI-101_Experimental table_SAME-R.csv` (Pyrolyzed particulate size distributions and mass loss rates).
6. **Droplet Cool Flame Empirical Extinction**: `original/psi_117/` (Empirical columns only: `Dext_CF_EXPT` from `PROCI_2023_C12_Extinction_Diameter_vs_pressure.csv` and `MST_2024_Kavg.csv`).

This 6-investigation subset spans the complete physical domain of spacecraft fire safety—from solid ignition and flame spread, to burning rate emulation, elevated-oxygen extinction, smoke particle detection, and macro-scale compartment growth.
