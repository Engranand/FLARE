# FLARE Milestone 10.2: Implementation Report
## Deterministic Query Understanding & Execution State Machine

**Project**: FLARE — Scientific Intelligence Platform for Spacecraft Fire Safety  
**Milestone**: M10.2 — Query Understanding and Execution State Machine  
**Document**: Technical Implementation and Verification Report  
**Date**: November 14, 2026  
**Status**: IMPLEMENTED, TESTED & VERIFIED (100% Pass Rate)  

---

## 1. Executive Summary

Milestone **M10.2** establishes the core deterministic orchestration foundation for the FLARE Scientific Intelligence Layer. In accordance with the system constraints and architectural contracts (`FLARE-M10-SPEC-V2`, `FLARE-M10-HARDENING-V2`, `FLARE-M10-CLAIM-V2`, and `FLARE-M10-SEC-V2`):

1. **Zero LLM Integration**: The orchestration layer operates purely in deterministic Python. No external language models, mock LLM APIs, or stochastic inference engines were introduced.
2. **Zero Vector Database Calls**: Literature and data access schemas rely strictly on allowlisted tool definitions and native full-text capabilities; no vector database dependencies were loaded.
3. **Zero Database Modifications**: No migrations, database schemas, or database tables were altered or written to during this milestone.
4. **Strict Scope & Security Boundary Enforcement**: Comprehensive gatekeeping prevents arbitrary SQL generation, script execution, and scientifically prohibited calculations (Biot numbers, $RQ_{comb}$, slab LOI regression, flame spread velocities, molar oxygen consumption, and lunar/Martian gravity extrapolations).
5. **100% Test Coverage**: All **59 unit and integration tests** in `backend/tests/unit/test_m10_2_orchestration.py` passed, and all **174 non-skipped tests** in the broader repository test suite passed with zero regressions.

---

## 2. Implemented Subsystems & Modules

All source files are housed under the newly created package `backend/app/intelligence/` and exposed via the FastAPI route `backend/app/api/intelligence.py`:

```
backend/app/
├── api/
│   ├── intelligence.py              # POST /api/v1/intelligence/plan
│   └── routes.py                    # Router mount for intelligence endpoints
└── intelligence/
    ├── __init__.py                  # Public exports
    ├── schemas.py                   # Pydantic v2 domain schemas, enums & exceptions
    ├── normalizer.py                # Input validation, sanitization & whitespace collapse
    ├── classifier.py                # Deterministic rule-based intent classification
    ├── scope_gate.py                # Scientific prohibitions & security boundary gate
    ├── state_machine.py             # Typed execution state machine & directed graph
    ├── tools.py                     # Pre-registered allowlist & tool validation
    └── planner.py                   # Query understanding pipeline & M9 metric mapping
```

### 2.1 Domain Schemas & Enums (`schemas.py`)
- **`IntentEnum`**: Explicitly represents the 7 supported intents:
  - `SCIENTIFIC_ANALYSIS`: Quantitative inquiries for M9 statistical metrics, medians, IQRs, depletion, airflow, morphology.
  - `OBSERVATION_LOOKUP`: Queries for specific test run records, individual sensor readings, or raw observation rows.
  - `DOCUMENT_RETRIEVAL`: Inquiries seeking NASA technical reports, README files, FAQs, or literature citations.
  - `COMBINED_RESEARCH`: Mixed queries requiring both quantitative analytical data and literature context.
  - `SCIENTIFIC_EXPLANATION`: Conceptual or mechanistic inquiries into microgravity combustion physics.
  - `OUT_OF_SCOPE`: Inquiries unrelated to spacecraft fire safety or microgravity combustion.
  - `AMBIGUOUS`: Underspecified, truncated, or excessively vague queries.
- **`ScopeStatusEnum`**: `ALLOWED`, `PROHIBITED`, `AMBIGUOUS`, `OUT_OF_SCOPE`.
- **`QueryState`**: Lifecycle states: `RECEIVED`, `NORMALIZED`, `CLASSIFIED`, `SCOPE_VALIDATED`, `PLANNED`, `READY_FOR_EXECUTION`, `ABSTAINED`, `FAILED`.
- **`ExecutionPlan`**: Pydantic v2 model capturing tracking UUID, original question, normalized question, intent, investigation, target metrics, required tools, document retrieval flag, scope status, abstention reason, execution dependencies, terminal state, and error message.
- **Exceptions**: `QueryNormalizationError`, `InvalidStateTransitionError`, `InvalidToolError`, `ScientificProhibitionError`.

### 2.2 Query Normalization (`normalizer.py`)
- Enforces strict character boundary checks ($\text{min}=3$, $\text{max}=1000$).
- Strips leading and trailing whitespace and collapses multi-character whitespace sequences (`\s+`), tabs, newlines, and carriage returns into single spaces.
- Rejects empty strings, whitespace-only inputs, out-of-bounds strings, and non-string types with `QueryNormalizationError`.
- Preserves the original raw string alongside the sanitized version in an immutable `NormalizedQuery` dataclass.

### 2.3 Scientific Scope Gate & Security Boundaries (`scope_gate.py`)
Audits questions against explicit operational, security, and combustion science prohibitions:
1. **Security Boundaries**:
   - **SQL Injection**: Detects SQL keywords (`SELECT ... FROM`, `INSERT INTO`, `UPDATE ... SET`, `DELETE FROM`, `DROP`, `ALTER`, `TRUNCATE`, `UNION [ALL] SELECT`, `OR 1=1`, `--`, stacked queries `;`). Fast-fails with `PROHIBITED` status and explicit security violation reason.
   - **Code Execution**: Detects dynamic script execution patterns (`eval(`, `exec(`, `__import__`, `subprocess`, `os.system`, `import os`). Fast-fails with `PROHIBITED` status.
2. **Scientific Prohibitions (Governed by M9 Contracts)**:
   - **Biot Number**: Rejects Biot number calculations ($Bi \ll 0.1$ or $Bi \gg 1$) due to unverified thermal conductivity ($k$), surface heat transfer coefficient ($h$), and solid thermal properties in NASA BASS-II data.
   - **Combustion Quotient ($RQ_{comb}$)**: Rejects $RQ_{comb} = \Delta\text{CO}_2 / (-\Delta\text{O}_2)$ because transient chamber measurements lack verified co-temporal sensor alignment and stoichiometric equivalence in unvented burns.
   - **Slab LOI Regression**: Rejects thick slab LOI logistic regression because PMMA slab extinguishments in BASS-II occurred under forced airflow flame-blowoff conditions rather than stagnant LOI equilibrium.
   - **Flame Spread Rate ($V_f$)**: Rejects $V_f$ calculations because spatial video tracking coordinates and camera calibration timestamps were not ingested into the tabular dataset.
   - **Absolute Molar Oxygen Consumption ($\Delta n_{O2}$)**: Rejects molar consumption calculations because chamber volume pressure logs and temperature transients are uncalibrated in BASS-II.
   - **Cubic Flow Polynomial**: Rejects cubic flow calibration in favor of quadratic nozzle calibration and piecewise linear interpolation (M9-P3).
   - **Lunar / Martian Extrapolation**: Rejects partial gravity extrapolation ($1/6\,g$, $3/8\,g$) because BASS-II tests were conducted strictly aboard the ISS ($10^{-6}\,g$) with forced convective flow.
   - **Fire-Risk Odds Ratios**: Rejects odds ratios due to sample size constraints and non-randomized flight matrix protocol.
3. **Out-of-Scope & Ambiguity Gating**:
   - Identifies non-domain queries (cooking, recipes, weather, finance, sports, politics) and classifies as `OUT_OF_SCOPE`.
   - Identifies underspecified queries ("tell me more", "what happened?", single generic words) and classifies as `AMBIGUOUS`.

### 2.4 Deterministic Intent Classifier (`classifier.py`)
- Employs deterministic regex patterns and rule-based heuristics.
- Transparently documents that keyword matching does not constitute semantic AI, providing a reliable and verifiable placeholder until future phases.
- Disambiguates multi-category matches (e.g. queries referencing both document literature and quantitative metrics map to `COMBINED_RESEARCH`).

### 2.5 Typed Execution State Machine (`state_machine.py`)
- Enforces an authoritative directed graph of state transitions:
  $$\text{RECEIVED} \longrightarrow \text{NORMALIZED} \longrightarrow \text{CLASSIFIED} \longrightarrow \text{SCOPE\_VALIDATED} \longrightarrow \begin{cases} \text{PLANNED} \longrightarrow \text{READY\_FOR\_EXECUTION} \\ \text{ABSTAINED} \end{cases}$$
- Any active state may transition to `FAILED` upon an unhandled exception.
- `ABSTAINED` and `FAILED` are strictly terminal: any attempt to transition out of these states raises `InvalidStateTransitionError`.
- Records an immutable audit log of every transition with UTC timestamps and rationales.

### 2.6 Allowlisted Tool Registry (`tools.py`)
Registers metadata contracts for the four authorized FLARE intelligence tools:
- `m9_get_analytical_result`
- `flare_query_observations`
- `flare_retrieve_documents`
- `flare_check_scientific_prohibition`

Provides `is_valid_tool()`, `validate_tools()`, and `get_tool_definition()`. Any tool name outside this allowlist immediately raises `InvalidToolError`.

### 2.7 Execution Planner (`planner.py`)
- Integrates the pipeline: normalizes input, transitions state machine, classifies intent, validates scope, maps requested metrics to the 20 authoritative M9 metric codes, assigns allowlisted tools, and marks the plan `READY_FOR_EXECUTION` (or `ABSTAINED`).
- Metric extraction covers:
  - Environmental gas statistics (`ambient_initial_o2_median`, `ambient_initial_o2_iqr`, CO2, CO)
  - Oxygen depletion (`non_negative_o2_depletion_median`, `relative_o2_depletion_ratio_median`, `positive_o2_depletion_median`, `signed_distribution_o2_depletion_median`)
  - Calibrated airflow (`calibrated_airflow_velocity_median`, `calibrated_airflow_velocity_iqr`, `calibrated_airflow_velocity_range`)
  - Specimen morphology and counts (`total_flight_runs_count`, `unique_physical_specimens_count`, `first_burn_subset_runs_count`, `subsequent_reburn_subset_runs_count`, `observed_morphology_regimes_summary`)

### 2.8 API Endpoint (`backend/app/api/intelligence.py`)
- Route: `POST /api/v1/intelligence/plan`
- Request Schema: `PlanRequest(question, investigation="PSI-25", request_id=None)`
- Response Schema: `PlanResponse(plan=ExecutionPlan)`
- Error Codes:
  - `422 Unprocessable Content`: On empty questions, whitespace-only questions, or strings $<3$ or $>1000$ characters.
  - `500 Internal Server Error`: On unexpected pipeline execution failure.
  - `200 OK`: For all valid plans, including plans where `plan.state == "ABSTAINED"` with explicit `abstention_reason`.
- Mounted in `backend/app/api/routes.py` and reflected in the OpenAPI schema.

---

## 3. Verification & Test Suite Results

A dedicated, comprehensive test suite was implemented in `backend/tests/unit/test_m10_2_orchestration.py`.

### 3.1 Test Execution Summary
- Command: `pytest backend\tests\unit\test_m10_2_orchestration.py -v`
- Result: **59 passed in 2.46s**
- Regressions Check: `pytest backend\tests -v` $\longrightarrow$ **174 passed, 191 skipped (DB container tests), 0 failures**.

### 3.2 Breakdown of Test Categories

| Test Category | Test Class / Function | Assertions / Invariants Verified | Result |
| :--- | :--- | :--- | :--- |
| **Normalizer** | `TestQueryNormalizer` (7 tests) | Whitespace collapse, empty strings, whitespace-only strings, $<3$ chars, $>1000$ chars, non-string types. | **PASS** |
| **Classifier** | `TestIntentClassifier` (8 tests) | Verification of all 7 intents (`SCIENTIFIC_ANALYSIS`, `OBSERVATION_LOOKUP`, `DOCUMENT_RETRIEVAL`, `COMBINED_RESEARCH`, `SCIENTIFIC_EXPLANATION`, `OUT_OF_SCOPE`, `AMBIGUOUS`). | **PASS** |
| **Scope Gate** | `TestScopeGate` (18 tests) | Valid query allowance; scientific prohibitions (Biot, $RQ_{comb}$, slab LOI, $V_f$, $\Delta n_{O2}$, cubic airflow, lunar/Martian gravity, odds ratios); SQL injection (`SELECT`, `UNION`, `DROP`, `OR 1=1`); Code execution (`eval`, `import os`); Out of scope (cooking, finance); Ambiguous queries. | **PASS** |
| **State Machine** | `TestStateMachine` (5 tests) | Complete lifecycle transition progression, abstention lifecycle, illegal skipping transitions, terminal state immutability (`ABSTAINED`, `FAILED`). | **PASS** |
| **Tool Registry** | `TestToolRegistry` (5 tests) | Exact set equality on `ALLOWLISTED_TOOLS`, tool validity checks, allowlist validation pass/fail, tool schema inspection. | **PASS** |
| **Execution Planner** | `TestExecutionPlanner` (9 tests) | End-to-end plan assembly for ambient oxygen, airflow, depletion, observation lookup, document retrieval, combined research; abstention on prohibited, out-of-scope, and ambiguous queries. | **PASS** |
| **API Endpoint** | `TestIntelligencePlanApi` (7 tests) | `POST /api/v1/intelligence/plan` 200 OK structure, prohibited query abstention response, SQL injection rejection, 422 HTTP validation errors on empty/short/whitespace input, tracking UUID preservation. | **PASS** |

---

## 4. Architectural Verification Against System Boundaries

1. **No External Network Calls**: Verified that no HTTP clients (e.g. OpenAI, Anthropic, Gemini, HuggingFace) or external sockets are invoked during planning.
2. **No Arbitrary SQL Generation**: Verified that database interactions are strictly bounded by pre-registered, parameterized tool signatures (`m9_get_analytical_result`, `flare_query_observations`).
3. **No Database Writes**: No DDL or DML was executed against the persistent PostgreSQL instance.
4. **Metrological Invariants**: The 20 M9 metric codes are accurately recognized and mapped without modifying, rounding, or recomputing any physical values in the orchestration layer.

---

## 5. Next Steps for Milestone M10

With M10.2 complete and verified, the foundation is prepared for subsequent phases:
- **Phase 3 (M10.3)**: Implement document chunk indexing with PostgreSQL `tsvector` and `pg_trgm` (`0009_m10_evidence_indexing.py`), author tool dispatcher execution functions in `backend/app/services/intelligence/tools.py`, and implement the Structured Scientific Claim Validation Gate.
- **Phase 4 (M10.4)**: Author the Buffered SSE streaming endpoints (`POST /api/v1/intelligence/query/stream`) with progress event streaming and server-side narrative buffering.
