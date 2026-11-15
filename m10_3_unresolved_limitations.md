# FLARE Milestone 10.3: Unresolved Limitations & Boundary Report

**Project**: FLARE — Scientific Intelligence Platform for Spacecraft Fire Safety  
**Milestone**: M10.3 — Scientific Tool Execution Layer  
**Document**: Epistemic Boundaries, Deferred Capabilities, and Operational Limitations  
**Date**: November 14, 2026  
**Status**: ACTIVE GOVERNANCE DOCUMENT  

---

## 1. Scope & Purpose

This document provides a transparent, unvarnished accounting of all architectural, scientific, and infrastructural limitations remaining after the implementation and verification of Milestone M10.3.

---

## 2. Technical & Infrastructural Limitations

### 2.1 Document Retrieval Deferred (`flare_retrieve_documents`)
- **Current Status**: The tool interface is registered in the allowlist and state machine, but executing the tool returns `ToolExecutionStatus.NOT_IMPLEMENTED`.
- **Planned Resolution**: Milestone **M10.4** will implement database text extraction, chunking, and native PostgreSQL `tsvector` full-text search and `pg_trgm` fuzzy matching under forward migration `0009_m10_evidence_indexing.py`.
- **Operational Boundary**: No literature chunks, technical papers, or README text are currently searched or returned by M10.3.

### 2.2 Absence of LLM Synthesis & Narrative Generation
- **Current Status**: M10.3 is strictly a deterministic computation and data retrieval layer. It returns structured JSON data (`ExecutionResponse`, `ToolResult`).
- **Planned Resolution**: Natural language narrative generation will be integrated in subsequent phases only after the **Structured Scientific Claim Validation Gate** has been deployed to verify draft assertions against sealed M9 results.
- **Operational Boundary**: Endpoints do not return conversational markdown answers or synthetic prose.

### 2.3 PostgreSQL Extension Reality (`pgvector`)
- **Audit Finding**: In accordance with the PostgreSQL 17 filesystem audit, the `pgvector` extension (`vector.control`) is not installed in the Windows PostgreSQL 17 cluster.
- **Design Invariant**: Literature retrieval in FLARE M10 unconditionally uses native PostgreSQL `tsvector` (GIN index) and `pg_trgm` (trigram similarity). Dense vector retrieval remains an optional feature flag (`enable_vector_search = False`) and must not be assumed.

---

## 3. Scientific & Metrological Limitations

### 3.1 Inherited M9 Scientific Prohibitions
The following 8 combustion science prohibitions remain strictly enforced at the scope gate and within tool dispatchers:
1. **Biot Numbers**: Neither thin-film ($Bi \ll 0.1$) nor thick-slab ($Bi \gg 1$) Biot regimes may be calculated or inferred, as thermal conductivity ($k$), surface heat transfer coefficient ($h$), and solid thermal properties are uncalibrated in BASS-II flight telemetry.
2. **Combustion Quotient ($RQ_{comb}$)**: Deferred and prohibited due to unverified sensor alignment and non-stoichiometric unvented chamber accumulation.
3. **Thick Slab LOI Logistic Regression**: Prohibited because PMMA slab extinctions occurred under forced blowoff, not stagnant LOI equilibrium.
4. **Flame Spread Rate ($V_f$)**: Not derivable from tabular data due to absence of video tracking coordinates and camera calibration timestamps.
5. **Absolute Molar Oxygen Consumption ($\Delta n_{O2}$)**: Prohibited because microgravity chamber volume pressure logs and temperature transients are uncalibrated.
6. **Cubic Airflow Velocity Polynomials**: Prohibited in favor of quadratic nozzle calibration and piecewise linear interpolation (M9-P3).
7. **Lunar / Martian Gravity Extrapolations**: Prohibited; flight tests were conducted strictly aboard the ISS ($10^{-6}\,g$) with forced convective flow.
8. **Fire-Risk Odds Ratios**: Prohibited due to non-randomized convenience flight matrix protocol.

### 3.2 Dataset Scope Specialization (PSI-25)
- **Current Scope**: M9 and M10.3 deterministic tool execution specializes in NASA PSI-25 / BASS-II (129 flight runs, 2,193 raw observations).
- **Other Challenge Datasets**: Other acquired microgravity datasets (e.g. PSI-117 droplet cool flames, PSI-100 Saffire telemetry) are cataloged and profiled in M7, but have not yet been seeded into dedicated analysis protocols under `analysis_protocol`.

### 3.3 Flight Safety Operational Disclaimer
- **Platform Classification**: FLARE is an evidence-grounded scientific intelligence research platform for ground analysis.
- **Certification Boundary**: FLARE is **NOT** a certified flight-critical safety system, does not possess DO-178C avionics software certification, and must never be used for real-time autonomous fire suppression, life support control, or emergency spacecraft telemetry decisions.
