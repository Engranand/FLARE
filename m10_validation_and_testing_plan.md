# FLARE Milestone 10: Validation, Testing & Evaluation Plan

**Project**: FLARE — Scientific Intelligence Platform for Spacecraft Fire Safety  
**Milestone**: M10 — Evidence-Grounded Scientific Intelligence Layer  
**Document**: Quality Assurance, LLM Evaluation Harness, and Regression Testing Plan  
**Version**: 1.0.0 (Authoritative Design)  
**Status**: DESIGN & SPECIFICATION ONLY  

---

## 1. Testing & Evaluation Philosophy

In standard conversational AI, subjective metrics such as "helpfulness" or "tone" are common. In FLARE, evaluation is governed by **Metrological Faithfulness** and **Scientific Determinism**:
1. **Zero Hallucinated Quantities**: Not a single numerical value, unit, or decimal place may be invented by the model.
2. **100% Citation Resolvability**: Every citation bracket must resolve to a valid, cryptographically verified database record.
3. **100% Prohibition Gating**: Prohibited queries (Biot numbers, $RQ_{comb}$, slab LOI logistic regression, Martian gravity extrapolation) must trigger structured scientific abstention in 100% of test runs.

---

## 2. Evaluation Framework & Metrics

```mermaid
flowchart TD
    subgraph TestInputs [Benchmark Inputs (50 Golden Questions)]
        Q1[Numerical Analysis Queries (15)]
        Q2[Observation & Material Queries (15)]
        Q3[Literature & FAQ Queries (10)]
        Q4[Prohibited & Out-of-Scope Queries (10)]
    end

    subgraph Pipeline [M10 Execution Pipeline]
        Q1 --> Engine[Query Execution Engine]
        Q2 --> Engine
        Q3 --> Engine
        Q4 --> Engine
    end

    subgraph MetricGates [Automated Validation Gates]
        Engine --> Gate1[1. Tool Dispatch Accuracy Gate]
        Engine --> Gate2[2. Numerical Grounding Gate (Regex & AST)]
        Engine --> Gate3[3. Citation Precision Gate (DB Resolution)]
        Engine --> Gate4[4. Limitation Compliance Gate]
        Engine --> Gate5[5. Abstention Verification Gate]
    end

    subgraph EvaluationOutput [Test Scorecard & Verdict]
        Gate1 --> Scorecard[Evaluation Scorecard]
        Gate2 --> Scorecard
        Gate3 --> Scorecard
        Gate4 --> Scorecard
        Gate5 --> Scorecard
    end
```

### 2.1 Formal Evaluation Metrics

| Metric Name | Target | Calculation / Formula | Failure Consequence |
| :--- | :--- | :--- | :--- |
| **Numerical Faithfulness** | **100.0%** | $\frac{\text{Verified Numeric Tokens Matching Tool Results}}{\text{Total Numeric Tokens in Narrative}} \times 100$ | Any unanchored number fails the build. |
| **Citation Precision** | **100.0%** | $\frac{\text{Citations Resolving to Valid DB / Doc Pointers}}{\text{Total Inline Citations Emitted}} \times 100$ | Any orphan citation fails the build. |
| **Prohibition Abstention Rate** | **100.0%** | $\frac{\text{Prohibited Queries Resulting in Formal Abstention}}{\text{Total Prohibited Queries Injected}} \times 100$ | Answering a prohibited question fails the build. |
| **Tool Selection Accuracy** | **$\ge 98.0\%$** | $\frac{\text{Correct Tools Selected per Intent}}{\text{Total Test Queries}} \times 100$ | Regression logged; prompt tuned. |
| **Limitation Transparency** | **100.0%** | $\frac{\text{Answers Explaining Mandatory Limitations}}{\text{Answers Where Quality Flags Present}} \times 100$ | Omission of sensor drift / hot-wire lag fails build. |

---

## 3. The 50-Query Golden Scientific Benchmark Suite

A curated benchmark of 50 ground-truth questions will be maintained in `backend/tests/fixtures/m10_benchmark_queries.json`. The suite is partitioned into four functional subsets:

### 3.1 Subset A: Numerical Analysis & M9 Metrics (15 Queries)
- *Benchmark Q1*: "What was the sample median pre-ignition oxygen mole fraction in BASS-II?"  
  *Expected Output*: Must report $0.182\text{ mol/mol}$ ($18.2\%$ by vol), $N=129$, and 95% CI $[0.175, 0.188]\text{ mol/mol}$ with `[RESULT:ambient_initial_o2_median]`.
- *Benchmark Q2*: "What was the median relative oxygen depletion across non-negative BASS-II runs?"  
  *Expected Output*: Must report $0.0040\text{ mol/mol}$ ($0.4\%$), $N=117$, 95% CI $[0.0020, 0.0050]\text{ mol/mol}$, and $\Pi_{O2}$ median $0.01935$.
- *Benchmark Q3*: "How many tests exhibited negative oxygen sensor drift, and what were the values?"  
  *Expected Output*: Must report exactly 5 tests (`T5, T10, T12, T13, T23`), each showing $-0.1\%$ volume depletion ($-0.0010\text{ mol/mol}$), preserved signed.
- *Benchmark Q4*: "What is the calibrated duct airflow velocity range for steady scalar runs?"  
  *Expected Output*: Must report range $[0.020132, 0.150990]\text{ m/s}$ ($[2.0132, 15.0990]\text{ cm/s}$), $N=24$, median $0.050330\text{ m/s}$.

### 3.2 Subset B: Experimental Observations & Materials (15 Queries)
- *Benchmark Q16*: "Which experimental runs tested Nomex III fabric?"  
  *Expected Output*: Must identify tests `F1, F2, F3` conducted by Ferkul, woven aramid fabric in opposed flow.
- *Benchmark Q17*: "How many unique physical specimens were burned, and how many were re-burned?"  
  *Expected Output*: Must state 107 unique specimens, 87 burned once, 20 burned multiple times across 42 runs ($107 + 22 = 129$ total runs).
- *Benchmark Q18*: "Which test had a fan display of 0.0 and what was its physical meaning?"  
  *Expected Output*: Must identify Test `O2` (Olson), motor stall deadband where fan controller shuts off above 3.8 V, zero convective velocity.

### 3.3 Subset C: NASA Literature & FAQ Explanations (10 Queries)
- *Benchmark Q31*: "Why does the hot-wire anemometer in BASS-II have a ~60-second response lag?"  
  *Expected Output*: Must cite the BASS-II ReadMe / FAQ explaining thermal time constant of the anemometer sensor coil.
- *Benchmark Q32*: "Why are tests B2, P22a, P22b, T28a, and T28b quarantined?"  
  *Expected Output*: Must cite gross recording anomalies ($|\Delta X_{O2}| > 19\%$) due to telemetry dropouts or incorrect sensor calibration states.

### 3.4 Subset D: Prohibitions & Out-of-Scope Guardrails (10 Queries)
- *Benchmark Q41*: "Calculate the Biot number for test B1."  
  *Expected Output*: **Mandatory Abstention**. Must state Biot numbers are physically ungrounded because heat transfer coefficients ($h_c$) and solid conductivities ($k_s$) were not measured in flight.
- *Benchmark Q42*: "What is the combustion respiratory quotient (RQ_comb) for BASS-II?"  
  *Expected Output*: **Mandatory Abstention**. Must state $RQ_{comb}$ is explicitly deferred due to division-by-zero on 24 zero-depletion runs and sensor asynchrony.
- *Benchmark Q43*: "Calculate the flame spread rate (Vf) for thin PMMA films."  
  *Expected Output*: **Mandatory Abstention**. Must state tabular CSV lacks spatial/pixel coordinate tracking necessary for $V_f$.
- *Benchmark Q44*: "Predict flammability limits for PMMA on Mars."  
  *Expected Output*: **Mandatory Abstention**. Must state BASS-II was conducted in microgravity ($\sim 10^{-6}\text{ g}$ on ISS) and cannot be extrapolated to Martian partial gravity ($0.38\text{ g}$).

---

## 4. Test Suite Implementation Structure

```text
backend/tests/
├── unit/
│   ├── test_m10_query_parser.py           # Unit tests for query sanitization & entity extraction
│   ├── test_m10_prohibitions_gate.py      # Unit tests for fast-path abstention
│   ├── test_m10_citation_verifier.py      # Regex & AST numerical verification tests
│   └── test_m10_tool_bridge.py            # Unit tests for Pydantic tool argument validation
├── integration/
│   ├── test_m10_pipeline_ephemeral.py     # End-to-end pipeline on ephemeral PostgreSQL 17
│   ├── test_m10_api_endpoints.py          # FastAPI testclient endpoints (/query, /evidence)
│   └── test_m10_read_only_safety.py       # Confirms zero DB mutations under malicious inputs
└── evaluation/
    ├── test_m10_benchmark_runner.py       # Automated runner for the 50 golden queries
    └── test_m10_faithfulness_audit.py     # Numerical zero-hallucination auditor
```

---

## 5. Continuous Integration (CI) Quality Gates

In GitHub Actions / CI pipeline, M10 must pass the following automated stages:
1. `pytest backend/tests/unit`: 100% pass (<2s).
2. `pytest backend/tests/integration --run-postgres`: 100% pass on ephemeral PostgreSQL (<40s).
3. `pytest backend/tests/evaluation`: 50 of 50 benchmark queries pass with 100% Numerical Faithfulness and 100% Prohibition Gating.
4. `npm run test` & `npm run typecheck` in `frontend/`: 100% pass without TypeScript errors.
