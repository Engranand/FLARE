# FLARE Milestone 10.4: Scientific Document Retrieval Completion Report

**Project**: FLARE — Scientific Intelligence Platform for Spacecraft Fire Safety  
**Milestone**: M10.4 — Scientific Document Retrieval & Evidence Grounding  
**Date**: November 15, 2026  
**Status**: **COMPLETED & VERIFIED**  

---

## 1. Executive Summary

Milestone M10.4 delivers a functional, deterministic, evidence-grounded scientific document retrieval system for FLARE. Users can ask natural-language questions regarding NASA spacecraft combustion physics, microgravity flame behavior, and fire safety flight experiments, receiving relevant, traceable source passages extracted directly from authentic NASA literature.

### Key Architectural Deliverables
1. **Document Indexing Pipeline ([extractor.py](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/documents/extractor.py), [chunker.py](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/documents/chunker.py), [registry.py](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/documents/registry.py), [indexer.py](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/documents/indexer.py))**:
   - Extracts text from NASA PDFs (using `pypdf`) and DOCX files (using pure Python XML parsing), strictly preserving 1-indexed page numbers and section headers.
   - Chunks text into bounded scientific passages with deterministic SHA-256 hashes.
   - Idempotent database persistence with zero duplicate chunks.
   - Raw NASA source files remain completely untouched and read-only.
2. **PostgreSQL Full-Text Search Schema ([0009_m10_4_document_chunks.py](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/migrations/versions/0009_m10_4_document_chunks.py))**:
   - Forward migration installing `public.document_chunk` with stored `tsvector` generated column (`tsv_content`) and GIN index.
   - Search execution via `websearch_to_tsquery('english', :query)` and `ts_rank_cd`.
   - Zero vector databases, Chroma, or pgvector dependencies introduced.
3. **Retrieval Tool Implementation ([tool_executor.py](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/backend/app/intelligence/tool_executor.py#L753-L910))**:
   - Implements `flare_retrieve_documents` within the read-only transaction boundary.
   - Returns structured passages with document identity, source SHA-256, page references, section headers, and relevance scores.
   - Explicit `NO_RESULTS` status when no matching passages are found.
4. **Evidence Traceability & Epistemic Attribution**:
   - Every passage carries a stable FLARE URI (`flare://source_document/<doc_id>#page=<page_start>&chunk=<chunk_index>`).
   - Explicitly distinguishes `experimental_observation`, `reference_information`, and `numerical_simulation`.
   - Attribution is derived directly from registered document metadata, **never inferred from filenames alone**.
   - Retrieved passages are explicitly marked as qualitative literature context (`is_validated_measurement: False`).
5. **Interactive Frontend Experience ([EvidenceExplorer.tsx](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/frontend/src/pages/EvidenceExplorer.tsx))**:
   - Mounted at `/evidence` ("Evidence Explorer").
   - Provides scientific question input, quick-prompt buttons, relevance scores, verified SHA-256 badges, page references, epistemic attribution pills, and clear `NO_RESULTS` guidance.

---

## 2. Supported Questions & Grounded Retrieval

The system deterministically routes and answers core microgravity combustion inquiries:

| Scientific Question | Classified Intent | Required Tools | Retrieved Evidence Summary | Source Document & Provenance |
| :--- | :--- | :--- | :--- | :--- |
| **Why does flame shape change in microgravity?** | `SCIENTIFIC_EXPLANATION` | `flare_retrieve_documents` | Explains elimination of buoyant convection in microgravity, transition from tear-drop shape to spherical diffusion flames, and soot shell formation. | `np-2015-10-034-jsc_combustion_in_reduced_gravity-iss-mini-book-011116-508.pdf` (pp. 6–12) |
| **How does airflow affect flame behaviour?** | `SCIENTIFIC_EXPLANATION` | `flare_retrieve_documents` | Details convective flow effects: slow forced airflow supplies oxygen, elongates flames, and controls extinction limits in flight chambers. | `PSI-25_Reports_BASS-II Summary Report.pdf` & `BASS-II data FAQ.docx` |
| **What NASA experiments investigated solid-fuel flammability?** | `SCIENTIFIC_EXPLANATION` | `flare_retrieve_documents` | Outlines BASS, BASS-II, and Saffire experiments investigating thick vs thin PMMA, cotton-fiberglass, and Nomex flammability limits aboard ISS and Cygnus. | `PSI-25_Science Documents_BASS-II_ReadMe.docx` & Saffire literature |
| **What differences were observed between experimental conditions?** | `SCIENTIFIC_EXPLANATION` | `flare_retrieve_documents` | Compares varying ambient oxygen mole fractions (16% to 22%), duct airflow speeds (0 to 5.5 cm/s), and fuel thickness regimes (thin film vs thick slab). | `PSI-25_Reports_BASS-II Summary Report.pdf` |

---

## 3. Test Results & Verification Evidence

All testing was executed cleanly across both in-memory unit suites and live PostgreSQL 17 clusters:

### 3.1 Unit Test Suite (In-Memory / Mock Environment)
* **Command**: `backend\.venv\Scripts\python -m pytest backend/tests/unit/ -v`
* **Result**: **122 passed, 0 failed, 0 skipped** (4.95s)
* **Coverage**:
  - `test_extract_pdf_real_nasa_document` (Passed)
  - `test_extract_docx_real_nasa_document` (Passed)
  - `test_extract_missing_document_raises_error` (Passed)
  - `test_extract_unsupported_format_raises_error` (Passed)
  - `test_chunking_page_range_and_overlap` (Passed)
  - `test_chunking_empty_pages_returns_empty` (Passed)
  - `test_sqlite_indexing_and_idempotency` (Passed)
  - `test_retrieval_tool_nominal_on_indexed_data` (Passed)
  - `test_retrieval_tool_empty_query_returns_invalid_input` (Passed)
  - `test_retrieval_tool_no_results_found` (Passed)
  - `test_retrieval_tool_offline_connection_returns_no_results` (Passed)
  - All existing M9 and M10.2 orchestration unit tests passed with zero regressions.

### 3.2 Live PostgreSQL 17 Integration Suite
* **Command**: `backend\.venv\Scripts\python -m pytest backend/tests/integration/test_m10_4_retrieval.py -v --run-postgres --pg-bin "C:\Program Files\PostgreSQL\17\bin"`
* **Result**: **6 passed, 0 failed, 0 skipped** (19.85s)
* **Coverage**:
  - `test_pg_document_chunks_indexed_with_tsvector` (Passed)
  - `test_pg_query_flame_shape_change_microgravity` (Passed)
  - `test_pg_query_airflow_flame_behaviour` (Passed)
  - `test_pg_query_solid_fuel_flammability_experiments` (Passed)
  - `test_pg_unmatched_query_returns_no_results` (Passed)
  - `test_pg_api_end_to_end_explanation_retrieval` (Passed)

### 3.3 Full Integration Suite (M9, M10.3, and M10.4)
* **Command**: `backend\.venv\Scripts\python -m pytest backend/tests/integration/ -v --run-postgres --pg-bin "C:\Program Files\PostgreSQL\17\bin"`
* **Result**: **18 passed, 0 failed, 0 skipped** (61.50s)

### 3.4 API Regression Suite
* **Command**: `backend\.venv\Scripts\python -m pytest backend/tests/test_api.py -v`
* **Result**: **10 passed, 0 failed, 0 skipped** (2.50s)

### 3.5 Frontend Unit & Build Suite
* **Command**: `npm --prefix frontend run test`
* **Result**: **6 passed, 0 failed, 0 skipped** (0.63s)
* **Command**: `npm --prefix frontend run build`
* **Result**: Production bundle compiled successfully (`dist/index.html`, `dist/assets/index-*.js`, `dist/assets/index-*.css`) in 5.94s with zero type errors.

---

## 4. Compliance with Milestone Constraints

| Constraint | Status | Audit Verification |
| :--- | :--- | :--- |
| **No Modification of Historical Migrations** | **COMPLIED** | Migrations 0001 through 0008 remain untouched; forward migration `0009_m10_4_document_chunks.py` installed. |
| **No Ingestion of PSI-117 Blended Datasets** | **COMPLIED** | Only verified NASA literature (BASS-II summary report, FAQs, mini-books, Saffire papers) indexed; no unclassified tabular datasets ingested. |
| **No Modification of NASA Raw Files** | **COMPLIED** | All original files in `data/raw/` accessed via read-only file streams. |
| **Preservation of M10.3 Security Controls** | **COMPLIED** | Server-side plan reconstruction, read-only transaction blocks (`SET LOCAL transaction_read_only = on`), and tool allowlists remain strictly enforced. |
| **No Vector Database / pgvector Dependency** | **COMPLIED** | Pure core PostgreSQL full-text search (`tsvector`, GIN, `websearch_to_tsquery`, `ts_rank_cd`). |
| **No External LLM API in M10.4** | **COMPLIED** | Deterministic extraction, indexing, ranking, and retrieval only. |
| **No Git History Rewrites / Commits** | **COMPLIED** | Working copy preserved without git commit, push, amend, or reset. |

---

## 5. Conclusion

Milestone M10.4 is complete, fully functional end-to-end, and verified across all test environments. The platform now seamlessly unifies deterministic quantitative combustion metrics (M9/M10.3) with authentic, traceable qualitative NASA literature passages (M10.4).
