# FLARE Milestone 10: Technology Decision Record (TDR)

**Project**: FLARE — Scientific Intelligence Platform for Spacecraft Fire Safety  
**Milestone**: M10 — Evidence-Grounded Scientific Intelligence Layer  
**Document**: Architectural & Framework Evaluation for Scientific Intelligence  
**Author**: Independent Senior Scientific Data Architect  
**Version**: 2.0.0 (Hardened Metrological Design)  
**Status**: APPROVED DESIGN DECISIONS  

---

## 1. Executive Summary & Evaluation Matrix

In accordance with FLARE engineering standards, technology selections must be justified on the basis of **epistemological safety**, **metrological reproducibility**, **operational reliability**, and **architectural minimalism**. No technology is introduced merely due to industry popularity.

```text
+---------------------------------------------------------------------------------------------------------------------+
|                                      M10 TECHNOLOGY DECISION SUMMARY                                                |
+--------------------------+------------------+-----------------------------------------------------------------------+
| Technology Candidate     | Verdict          | Core Justification                                                    |
+--------------------------+------------------+-----------------------------------------------------------------------+
| LangGraph / LangChain    | REJECTED         | Unnecessary abstraction layer; high cognitive & maintenance overhead; |
|                          |                  | native Python typed state machine is faster, auditable, and zero-bloat|
+--------------------------+------------------+-----------------------------------------------------------------------+
| Chroma / External Vector | REJECTED         | Unnecessary infrastructure silo; PostgreSQL 17 handles structured SQL |
| Database                 |                  | and full-text BM25 (tsvector/pg_trgm) in a single ACID engine         |
+--------------------------+------------------+-----------------------------------------------------------------------+
| pgvector Extension       | CONDITIONAL      | Verified: NOT INSTALLED in PostgreSQL 17 environment. Must NOT be     |
|                          | (FEATURE FLAG)   | assumed. Vector search is optional; native tsvector is primary        |
+--------------------------+------------------+-----------------------------------------------------------------------+
| Pure Vector RAG          | REJECTED         | Dangerous for numeric combustion data; loses tabular row context and  |
|                          |                  | precision; fails on structured statistical metrics                    |
+--------------------------+------------------+-----------------------------------------------------------------------+
| Structured SQL Retrieval | ADOPTED (CORE)   | Indispensable for 100% exact retrieval of raw flight records, M9      |
|                          |                  | sealed results, and condition parameters from PostgreSQL              |
+--------------------------+------------------+-----------------------------------------------------------------------+
| Structured Tool Calling  | ADOPTED (CORE)   | Native JSON schema function calling grounds LLM in deterministic M9   |
|                          |                  | modules, preventing mathematical hallucination                        |
+--------------------------+------------------+-----------------------------------------------------------------------+
| PostgreSQL Full-Text     | ADOPTED (CORE)   | Native tsvector (English stemming) + pg_trgm (fuzzy match) handles all|
| (tsvector + pg_trgm)     |                  | literature search without external dependencies                       |
+--------------------------+------------------+-----------------------------------------------------------------------+
| Open-Weight vs API LLM   | HYBRID /         | Frontier API (Gemini 2.5 Flash/Pro) for primary high-reasoning turn;  |
|                          | MODEL-AGNOSTIC   | Pluggable local OpenAI-compatible endpoint (Ollama/vLLM) for flight air|
|                          |                  | gap compliance via unified LLMClient protocol                         |
+--------------------------+------------------+-----------------------------------------------------------------------+
```

---

## 2. In-Depth Architectural Evaluations

---

### Decision 1: Orchestration Framework — LangGraph vs. Native Python State Machine
- **Evaluation**: Should FLARE adopt `langgraph` / `langchain` to coordinate multi-step query orchestration?
- **Analysis**:
  - *Problem to solve*: Coordinating the sequential transitions: query parsing $\rightarrow$ planning $\rightarrow$ tool execution $\rightarrow$ evidence validation $\rightarrow$ generation $\rightarrow$ citation auditing.
  - *Does existing infrastructure solve it?*: Yes. The FLARE backend already possesses a clean service architecture in [backend/app/services/](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/services/) and robust Pydantic data schemas.
  - *Drawbacks of LangGraph*:
    - Adds approximately 40 transitive dependencies to `pyproject.toml`, increasing vulnerability surface area.
    - Opaque control flow and debugging; serialization of complex database engines or Decimal types through LangGraph channels is prone to runtime errors.
    - In safety-critical aerospace intelligence, control flow must be explicit, statically typed, and fully auditable line-by-line.
- **Verdict**: **REJECT LangGraph**.
- **Adopted Solution**: Implement a native, typed Python state machine (`QueryExecutionPipeline`) using Pydantic `2.14` models, explicit transition functions, and standard async/await.

---

### Decision 2: Document Indexing & Storage — Chroma vs. PostgreSQL 17 Native Capabilities
- **Evaluation**: Should FLARE deploy Chroma, Qdrant, or Pinecone as a dedicated vector database?
- **Analysis**:
  - *Problem to solve*: Storing and indexing text from NASA papers, ISA-Tab metadata, and FAQs.
  - *Does existing infrastructure solve it?*: Yes. FLARE already depends on PostgreSQL 17 as its single source of truth, containing 33 core tables in [backend/app/models/scientific.py](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/models/scientific.py).
  - *Drawbacks of Chroma / External Vector DB*:
    - Creates a distributed data silo where document chunks exist in Chroma while `source_document`, `evidence_reference`, and `analytical_result` exist in PostgreSQL.
    - Dual-write consistency hazards: deleting or updating a document in PostgreSQL requires two-phase commits to keep the vector database in sync.
    - Increases operational complexity: requires running, securing, and monitoring a separate container/daemon.
- **Verdict**: **REJECT Chroma / Dedicated Vector DB**.
- **Adopted Solution**: Utilize PostgreSQL 17 as the unified storage engine. Document chunks are stored directly in PostgreSQL.

---

### Decision 3: Vector Search & pgvector Environmental Availability
- **Evaluation**: Can FLARE mandate `pgvector` for document similarity search?
- **Environmental Audit**:
  - An inspection of `C:\Program Files\PostgreSQL\17\share\extension\` revealed that **`pgvector` (or `vector.control`) is NOT installed** in the local PostgreSQL 17 environment.
  - Available extensions include: `amcheck, btree_gin, btree_gist, citext, cube, dblink, dict_int, dict_xsyn, earthdistance, file_fdw, fuzzystrmatch, hstore, intarray, isn, ltree, pageinspect, pgcrypto, pg_stat_statements, pg_trgm, unaccent, uuid-ossp, xml2`.
  - Crucially, **`pg_trgm` IS INSTALLED and available**.
- **Architectural Resolution**:
  1. **Strictly Separate Full-Text Search from Vector Search**:
     - Full-text literature search is the **standard, unconditional baseline**. It uses PostgreSQL's native `tsvector` with English stemming and GIN indexing (`to_tsvector('english', chunk_content)`).
     - Acronym expansion, fuzzy keyword matching, and typo tolerance are handled natively by `pg_trgm`.
  2. **Vector Retrieval is Conditional / Optional**:
     - Dense embedding search is encapsulated behind a feature flag: `enable_vector_search: bool = False`.
     - The application dynamically checks `SELECT 1 FROM pg_available_extensions WHERE name = 'vector'`.
     - If absent, the engine seamlessly operates in **Full-Text BM25 + Structured Relational Mode** without failing or requiring binary installation.
- **Verdict**: **MAKE pgvector CONDITIONAL. ADOPT tsvector + pg_trgm as PRIMARY**.

---

### Decision 4: Retrieval Strategy — Pure Vector RAG vs. Structured SQL vs. Hybrid Retrieval
- **Evaluation**: How should scientific data and documents be retrieved for query answering?
- **Analysis**:
  - *Pure Vector RAG*: Chunks CSV files or tables into text blocks, embeds them, and performs vector cosine similarity search.
    - *Why it fails in combustion science*: Vector search cannot compute medians, cannot distinguish $-0.0010\text{ mol/mol}$ from $+0.0010\text{ mol/mol}$, drops row-level alignment, and frequently retrieves irrelevant test rows due to semantic similarity in header text.
  - *Structured SQL Retrieval*: Queries relational tables (`experimental_test`, `observation`, `analytical_result`) using exact foreign keys, numeric ranges, and categorical filters.
    - *Why it is essential*: Guarantees 100% exact numerical retrieval, preserves exact Decimal values, and respects cryptographic aggregate seals.
  - *Hybrid Retrieval*:
    - Use **Structured SQL** for all experimental observations and M9 analytical results.
    - Use **Full-Text Search (`tsvector`)** for unstructured NASA research papers, ReadMes, and FAQ documents.
- **Verdict**: **ADOPT Structured SQL for Data + tsvector for Literature**.

---

### Decision 5: Read-Only Parameterized SQL Access & Execution Limits
- **Evaluation**: How should SQL queries be executed against PostgreSQL?
- **Rules**:
  1. **Strict Parameterization**: All SQL queries use prepared statements with typed parameters via SQLAlchemy `text("...").bindparams(...)`. Zero string formatting or dynamic SQL construction.
  2. **Read-Only Transaction Isolation**: All database sessions executed by intelligence services enforce `SET TRANSACTION READ ONLY`.
  3. **Resource Safeguards**:
     - `SET statement_timeout = 5000` (5,000 ms hard timeout).
     - `MAX_ROWS = 50` for tabular observation queries.
     - `MAX_CHUNKS = 5` for literature text chunks.
- **Verdict**: **MANDATORY ENFORCEMENT of Parameterized Read-Only SQL**.

---

### Decision 6: Deterministic Tool Calling Architecture
- **Evaluation**: Should the LLM generate raw SQL queries or invoke pre-defined structured tools?
- **Analysis**:
  - *Text-to-SQL*: Allowing the LLM to write arbitrary SQL queries against the 33-table schema.
    - *Why it is dangerous*: The LLM might write ad-hoc `AVG()` queries that bypass M9's audited R Type 7 interpolation, ignore order-statistic rank clamping, clamp negative sensor drift to zero, or execute invalid joins across unsealed tables.
  - *Structured Tool Calling*: The LLM selects from pre-registered tools (`m9_get_analytical_result`, `flare_query_observations`, `flare_retrieve_documents`) with strict Pydantic schemas.
    - *Why it is necessary*: Keeps all scientific calculation logic strictly inside the audited M9 Python engine and pre-written, tested SQL service functions. The LLM only supplies parameters (e.g. `metric_code="ambient_initial_o2_median"`).
- **Verdict**: **ADOPT Structured Tool Calling**. Text-to-SQL is strictly prohibited.

---

### Decision 7: LLM Selection — Frontier API vs. Local Air-Gapped Model
- **Evaluation**: What model family should power query understanding and answer synthesis?
- **Analysis**:
  - *Terrestrial Ground Research*: Frontier API (Gemini 2.5 Flash / Pro) provides superior tool-calling compliance ($\ge 99\%$) and large 1M+ token context windows without local GPU burden.
  - *Air-Gapped Flight Operations*: Self-hosted local models (e.g. Llama 3.3 70B via vLLM) ensure complete data privacy with zero external network egress, but require substantial local VRAM (minimum 48GB).
- **Verdict**: **ADOPT Model-Agnostic LLMClient Protocol**. Default to Gemini API; support pluggable local OpenAI-compatible endpoints for air-gapped deployments.
