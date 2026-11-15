# FLARE Milestone M10.5 — LLM Scientific Intelligence Integration Completion Report

**Document Status:** Complete & Verified  
**Milestone:** M10.5 — LLM Scientific Intelligence Integration  
**Date:** 2026-11-15  
**Verification Scope:** LLM Provider Abstraction, Scientific Claim Validation, Narrative Generation Invariants, API Integration, Frontend Evidence Explorer, Unit and PostgreSQL 17 Integration Tests  

---

## 1. Executive Summary & Architecture Overview

FLARE Milestone M10.5 establishes the **Evidence-Grounded Scientific Intelligence Layer** for the FLARE Spacecraft Fire Safety Platform. Building upon the deterministic scientific analysis engine (M9), secure orchestration state machine and server-side plan reconstruction (M10.2 / M10.3), and traceable NASA literature retrieval (M10.4), M10.5 connects these tools to a Large Language Model (LLM) while enforcing **cryptographic integrity, deterministic claim verification, and strict narrative grounding invariants**.

```
                           +-----------------------------------------------+
                           |          User Scientific Query                |
                           +-----------------------------------------------+
                                                  |
                                                  v
                           +-----------------------------------------------+
                           |  M10.2 Server-Side Plan Reconstruction & Gate |
                           |  - Intent classification & Normalization      |
                           |  - Physical scope gate & M9 Prohibitions      |
                           +-----------------------------------------------+
                                                  |
                                                  v
                           +-----------------------------------------------+
                           |  M10.3 Secure Tool Execution Boundary        |
                           |  - Read-Only Transaction (SEC-03)             |
                           |  - Cryptographic HMAC/SHA-256 Seals (SEC-02)  |
                           |  - M9 Analytical Metrics & M10.4 Passages     |
                           +-----------------------------------------------+
                                                  |
                                                  v
                           +-----------------------------------------------+
                           |  M10.5 LLM Provider Abstraction               |
                           |  - Local Ollama (qwen2.5:3b) / Configurable   |
                           |  - Structured Prompt with Physical Taxonomy   |
                           |  - Deterministic Fallback if Offline          |
                           +-----------------------------------------------+
                                                  |
                                                  v
                           +-----------------------------------------------+
                           |  M10.5 Structured Claim Validation Engine     |
                           |  - Value, unit, N, CI match against M9 seals  |
                           |  - M9 Scientific Prohibitions filter          |
                           |  - Narrative Invariant: Purge ungrounded claims|
                           +-----------------------------------------------+
                                                  |
                                                  v
                           +-----------------------------------------------+
                           |  API Response & Interactive Frontend UI       |
                           |  - Validated claims with [EM]/[DQ]/[RT]/[NS]  |
                           |  - Epistemic status & AI provider health pill |
                           |  - Traceable NASA document passages           |
                           +-----------------------------------------------+
```

### Key Architectural Invariants Enforced
1. **M9 Authority Invariant:** The LLM is strictly prohibited from inventing, calculating, or extrapolating scientific metrics. All quantitative values originate from cryptographically sealed M9 determinations or authenticated NASA literature chunks.
2. **Narrative Generation Constraint Invariant:** Any numerical or statistical claim emitted by the LLM that fails deterministic comparison against sealed analytical results (`validation_status != "VALIDATED"`) is immediately purged from the key findings and flagged in the rejection counter.
3. **Physical Taxonomy Invariant:** All evidence references are classified under explicit epistemic types:
   - `[EM]`: Experimental Measurement (flight observations)
   - `[DQ]`: Derived Quantity (deterministic scientific metrics computed by M9)
   - `[RT]`: Reference / Literature (peer-reviewed NASA technical reports)
   - `[NS]`: Numerical Simulation (model approximations)
4. **Fail-Closed Security & Provenance:** Client-supplied execution plans are discarded on arrival (`SEC-01`); aggregate seals are verified using canonical JSON and HMAC (`SEC-02`); tool dispatches execute strictly within `SET LOCAL transaction_read_only = on` (`SEC-03`).
5. **Deterministic Offline Fallback:** If the LLM provider daemon (e.g. Ollama) is unreachable, offline, or times out, the system never returns HTTP 500. Instead, it transitions gracefully into a deterministic fallback synthesis synthesized directly from retrieved tool data with `provider_status = "unavailable"`.

---

## 2. Provider Abstraction Implementation

The provider layer is located at `backend/app/intelligence/llm/` and provides an extensible, decoupled interface for interacting with language models.

### 2.1 Supported Adapters
- **`OllamaProvider` (`backend/app/intelligence/llm/ollama.py`):**
  - Connects to local Ollama daemon via `httpx` (`http://127.0.0.1:11434/api/generate`).
  - Configured with `qwen2.5:3b` model running locally with GPU VRAM acceleration.
  - Leverages Ollama's native JSON mode (`format="json"`) for reliable structured output generation.
  - Features configurable timeout (`settings.llm_timeout_seconds = 30.0`), explicit health check (`is_available()`), and proper error trapping converting network faults into `ProviderUnavailableError`.
- **`MockLLMProvider` (`backend/app/intelligence/llm/mock.py`):**
  - Fully deterministic mock provider for isolated unit and integration testing without external daemons.
  - Supports canned JSON responses, configurable simulated latency, call inspection, and simulated network disconnects.
- **Provider Factory (`backend/app/intelligence/llm/factory.py`):**
  - Dynamically instantiates the configured provider based on application settings (`llm_provider = "ollama"` or `"mock"`).
  - Validates endpoints and avoids any hardcoded external credentials.

### 2.2 Provider Fallback & Graceful Degradation
When `is_available()` returns `False` or the HTTP client raises an exception during prompt generation:
- The synthesis service catches `ProviderUnavailableError`.
- It constructs a deterministic synthesis payload directly from the executed tool results:
  - Summarizes the sealed M9 metrics (sample size, median, 95% CI) and retrieved literature passages.
  - Marks each claim as `VALIDATED` against the deterministic data.
  - Sets `provider_status = "unavailable"`.
  - Records a prominent uncertainty notice: `"LLM synthesis provider was unreachable; generated directly from sealed M9 deterministic results."`

---

## 3. Structured Claim Validation & Invariant Enforcement

The claim validation engine (`backend/app/intelligence/validation/claim_validator.py`) deterministically inspects every assertion in the model's output before the response is finalized.

### 3.1 Verification Rules
- **Numeric Value Matching:** Compares model-claimed numerical values against the authoritative `result_data` emitted by `m9_get_analytical_result`. Allows a tight floating-point tolerance of ±0.02.
- **Unit Verification:** Validates that reported units match the canonical metric definition (e.g. `mol/mol`, `cm/s`, `mm`, `s`).
- **Sample Size (N) Verification:** Compares sample count `N` against the sealed protocol dataset (e.g. `N=129` for BASS-II).
- **URN Syntax & Structure:** Requires stable, resolvable URN identifiers (e.g. `flare:result:M9-P1-ENV-STATS:ambient_initial_o2_median` or `flare:doc:<hash>#page=...`).
- **Scientific Prohibition Enforcement:** Scans all claimed statements and subject entities for forbidden M9 methodologies:
  - Biot number calculations (`biot_number`).
  - Limiting Oxygen Index (LOI) logistic regression on thick fuel slabs.
  - Lunar and Martian gravity extrapolations.
  - Forward flame-spread rate predictions ($V_f$).
  - Absolute molar consumption rates without calibrated flow.
  - Cubic fan flow polynomial approximations.
  - Fire risk odds ratios.
  Any claim mentioning a prohibited concept is rejected with `REJECTED` and purged from key findings.

### 3.2 Narrative Generation Invariant Implementation
In `backend/app/intelligence/synthesis/synthesizer.py`:
- `validate_claims(claims, tool_results, plan)` evaluates every candidate claim.
- All claims with `validation_status == "REJECTED"` are excluded from `synthesis.key_findings`.
- If a key finding repeats the text of a rejected claim, it is excised.
- `rejected_claims_count` is incremented and returned in the synthesis metadata so the UI and audit logs can detect attempted hallucinations.

---

## 4. API Integration

The execute endpoint at `POST /api/v1/intelligence/execute` was upgraded to incorporate LLM synthesis.

### 4.1 Request Payload
```json
{
  "question": "What was the median ambient initial oxygen concentration in BASS-II?",
  "investigation": "PSI-25",
  "synthesize": true
}
```

### 4.2 Response Payload
When `synthesize: true`, the endpoint returns the standard execution payload enriched with the `synthesis` block:
```json
{
  "request_id": "9f564754-...",
  "plan": {
    "original_question": "What was the median ambient initial oxygen concentration in BASS-II?",
    "intent": "SCIENTIFIC_ANALYSIS",
    "scope_status": "ALLOWED",
    "state": "COMPLETED",
    "required_tools": ["m9_get_analytical_result"],
    "requested_metrics": ["ambient_initial_o2_median"]
  },
  "tool_results": [...],
  "overall_status": "SUCCESS",
  "duration_ms": 142.5,
  "synthesis": {
    "synthesis_id": "c71e06d9-...",
    "answer": "In the BASS-II microgravity combustion investigation, the median ambient initial oxygen concentration was determined to be 0.182 mol/mol across 129 test burns, with an order-statistic 95% confidence interval of [0.175, 0.188] mol/mol.",
    "key_findings": [
      "Median initial ambient oxygen was 0.182 mol/mol.",
      "Total test count N=129 under BASS-II flight protocol."
    ],
    "scientific_claims": [
      {
        "claim_id": "c-1",
        "claim_type": "STATISTICAL_METRIC",
        "subject_entity": "ambient_initial_o2",
        "claimed_statement": "Median initial oxygen mole fraction was 0.182 mol/mol (N=129).",
        "claimed_numeric_value": 0.182,
        "claimed_unit": "mol/mol",
        "metric_identifier": "ambient_initial_o2_median",
        "claimed_sample_size": 129,
        "evidence_references": [
          {
            "uri": "flare:result:M9-P1-ENV-STATS:ambient_initial_o2_median",
            "evidence_type": "DQ",
            "epistemic_status": "SUPPORTED",
            "location_label": "BASS-II Environmental Gas Statistics",
            "summary_snippet": "Median initial oxygen mole fraction"
          }
        ],
        "validation_status": "VALIDATED",
        "epistemic_verdict": "SUPPORTED"
      }
    ],
    "evidence_references": [...],
    "uncertainty_and_limitations": [
      "Instrumental resolution of oxygen electrochemical sensor is ±0.005 mol/mol."
    ],
    "tools_used": ["m9_get_analytical_result"],
    "epistemic_status": "SUPPORTED",
    "provider_status": "available",
    "provider_model": "qwen2.5:3b",
    "rejected_claims_count": 0,
    "execution_duration_ms": 118.2
  }
}
```

---

## 5. Frontend Evidence & Intelligence Explorer

The frontend Evidence Explorer page (`frontend/src/pages/EvidenceExplorer.tsx`) was upgraded into an interactive scientific intelligence interface:
- **Unified Query Input:** Pre-populated with representative analytical (M9 engine) and conceptual (NASA literature) prompt pills.
- **Scientific Intelligence Synthesis Card:**
  - Header displaying AI Provider status badge (`AI Active: qwen2.5:3b` / `Deterministic Fallback (LLM Offline)` / `Guardrail Abstained`), Epistemic Status (`Supported`, `Disputed`, `Unresolved`, `Hypothesis`), and execution duration.
  - Formatted synthesized narrative response.
  - Bulleted Key Findings section with checkmark indicators.
  - Validated Scientific Claims cards displaying validation badges (`VALIDATED`, `QUALIFIED`, `REJECTED`), physical taxonomy origins (`[EM]`, `[DQ]`, `[RT]`, `[NS]`), metric IDs, numerical values, units, sample size $N$, and 95% confidence intervals.
  - Grounding pills linking to resolvable `flare:result:...` and `flare:doc:...` URNs.
  - Invariant Filter Alert: Informs users when unverified assertions were purged by the validator.
  - Physical Scope, Methodology & Epistemic Limitations highlighted box.
- **Governance & Verification Trace Drawer:** Collapsible drawer exposing server-side plan reconstruction (SEC-01), cryptographic HMAC/SHA-256 seal verification (SEC-02), read-only transaction boundary (SEC-03), and claim invariant filter metrics.
- **Traceable Literature Passages:** Preserves the M10.4 document passage cards with SHA-256 hashes, page ranges, section titles, and full-text relevance scores.

---

## 6. Acceptance & Verification Evidence

### 6.1 Unit Tests (Backend)
All **140 unit tests** passed across all intelligence and analysis modules:
- Query normalization and state machine tests (`test_m10_2_orchestration.py`)
- Tool execution, security remediations, and gating tests (`test_m10_3_tool_execution.py`)
- Literature extraction, chunking, and SQLite indexing tests (`test_m10_4_indexing.py`)
- LLM provider adapters, claim validation, synthesis invariants, and API tests (`test_m10_5_synthesis.py`)
- Deterministic analysis algorithms and prohibitions (`test_m9_*.py`)

**Test Command:**
```powershell
backend\.venv\Scripts\python.exe -m pytest backend/tests/unit/ -v
```
**Result:** `140 passed in 28.48s`

### 6.2 PostgreSQL 17 Integration Tests
Executed against live, ephemeral PostgreSQL 17 test databases (migrated to head with full BASS-II ingestion, sealed M9 analytics, and indexed NASA literature):
- `test_pg_end_to_end_scientific_synthesis`: Verified nominal question answering pipeline from question to sealed M9 metric extraction, LLM synthesis, and validated claim output.
- `test_pg_narrative_invariant_filters_hallucinated_claim`: Verified that hallucinated or altered numerical values are rejected by the validator and purged from findings.
- `test_pg_provider_offline_graceful_degradation`: Verified that when the LLM provider is offline, the API remains functional and produces a deterministic fallback synthesis.
- `test_pg_prohibited_query_synthesizer_refusal`: Verified that out-of-scope or prohibited inquiries (e.g. Biot number calculation) return an abstained synthesis with prohibition warnings.

**Test Command:**
```powershell
backend\.venv\Scripts\python.exe -m pytest backend/tests/integration/ -v --run-postgres --pg-bin "C:\Program Files\PostgreSQL\17\bin"
```
**Result:** `22 passed in 197.87s (100% pass rate)`

### 6.3 General API Tests
**Test Command:**
```powershell
backend\.venv\Scripts\python.exe -m pytest backend/tests/test_api.py -v
```
**Result:** `10 passed in 2.96s`

### 6.4 Frontend Typecheck & Build
- Vitest unit tests: `6 passed (6)`
- TypeScript strict compilation & Vite bundle:
  ```
  vite v7.3.7 building client environment for production...
  ✓ 1599 modules transformed.
  rendering chunks...
  computing gzip size...
  dist/index.html                   0.52 kB │ gzip:  0.33 kB
  dist/assets/index-y6qcbeUT.css   11.34 kB │ gzip:  3.50 kB
  dist/assets/index-DsFX-t8j.js   298.92 kB │ gzip: 93.78 kB
  ✓ built in 9.11s
  ```

---

## 7. Deliverables & File Registry

| Component | File Path | Status |
|:---|:---|:---|
| LLM Provider Abstraction | `backend/app/intelligence/llm/base.py` | Complete |
| Local Ollama Adapter | `backend/app/intelligence/llm/ollama.py` | Complete |
| Mock Testing Provider | `backend/app/intelligence/llm/mock.py` | Complete |
| Provider Factory | `backend/app/intelligence/llm/factory.py` | Complete |
| Scientific Claim Schemas | `backend/app/intelligence/validation/schemas.py` | Complete |
| Structured Claim Validator | `backend/app/intelligence/validation/claim_validator.py` | Complete |
| Synthesis Prompt Builder | `backend/app/intelligence/synthesis/prompt_builder.py` | Complete |
| Synthesis Service & Invariants | `backend/app/intelligence/synthesis/synthesizer.py` | Complete |
| Intelligence API Route | `backend/app/api/intelligence.py` | Complete |
| Application Configuration | `backend/app/core/config.py` | Complete |
| Frontend API Types | `frontend/src/types/api.ts` | Complete |
| Evidence & Intelligence Explorer | `frontend/src/pages/EvidenceExplorer.tsx` | Complete |
| Unit Acceptance Tests | `backend/tests/unit/test_m10_5_synthesis.py` | Complete (18/18 Passed) |
| PostgreSQL 17 Integration Tests | `backend/tests/integration/test_m10_5_integration.py` | Complete (4/4 Passed) |

---

## 8. Conclusion

Milestone M10.5 successfully integrates a Large Language Model into FLARE while upholding strict scientific rigor, cryptographic verification, and epistemic honesty. The system seamlessly handles both analytical inquiries (via M9 deterministic computations) and conceptual literature questions (via M10.4 full-text search), deterministically guarantees that hallucinated numbers are purged, and gracefully degrades when the local model is offline. All 140 unit tests, 22 PostgreSQL 17 integration tests, and frontend production builds pass with zero defects.
