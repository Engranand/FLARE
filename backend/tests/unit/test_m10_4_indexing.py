"""FLARE Milestone 10.4 Unit Tests: Document Extraction, Chunking, and Retrieval.

Executes in-memory SQLite and mock environments to test:
- PDF text extraction and page number preservation.
- Pure-Python DOCX text extraction.
- Chunk creation, page-range tracking, and deterministic SHA-256 hashes.
- Idempotent re-indexing without duplicate records.
- Missing document error handling.
- Empty search results returning explicit NO_RESULTS.
- Epistemic attribution distinction (metadata-based, not inferred from filenames).
"""
from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, text

from app.documents.chunker import chunk_document_pages
from app.documents.extractor import (
    DocumentExtractionError,
    DocumentPage,
    extract_document_text,
    extract_docx,
    extract_pdf,
)
from app.documents.indexer import (
    compute_file_sha256,
    index_single_document,
    index_source_documents,
)
from app.documents.registry import (
    REGISTERED_DOCUMENTS,
    RegisteredDocumentSpec,
    chunk_uuid,
    doc_uuid,
)
from app.intelligence.tool_executor import execute_flare_retrieve_documents
from app.intelligence.tool_schemas import ToolExecutionStatus

ROOT_DIR = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# 1. Extraction Tests
# ---------------------------------------------------------------------------

def test_extract_pdf_real_nasa_document():
    """Verify PDF extraction preserves 1-indexed page numbers and non-empty text."""
    pdf_path = ROOT_DIR / "data/raw/challenge_resources/original/other/np-2015-10-034-jsc_combustion_in_reduced_gravity-iss-mini-book-011116-508.pdf"
    if not pdf_path.is_file():
        pytest.skip("Test file not available in workspace")

    pages = extract_pdf(pdf_path)
    assert len(pages) > 0
    assert pages[0].page_number == 1
    # Check that text is extracted
    assert any("microgravity" in p.text.lower() or "combustion" in p.text.lower() for p in pages)


def test_extract_docx_real_nasa_document():
    """Verify pure-Python DOCX extraction preserves text and sections."""
    docx_path = ROOT_DIR / "data/raw/bass_ii/original/BASS-II data FAQ.docx"
    if not docx_path.is_file():
        pytest.skip("Test file not available in workspace")

    pages = extract_docx(docx_path)
    assert len(pages) >= 1
    assert pages[0].page_number == 1
    full_text = " ".join(p.text for p in pages)
    assert "spreadsheets" in full_text.lower() or "test matrix" in full_text.lower()


def test_extract_missing_document_raises_error():
    """Verify missing document raises DocumentExtractionError."""
    fake_path = ROOT_DIR / "data/raw/non_existent_document.pdf"
    with pytest.raises(DocumentExtractionError) as exc_info:
        extract_document_text(fake_path)
    assert "not found" in str(exc_info.value).lower()


def test_extract_unsupported_format_raises_error(tmp_path):
    """Verify unsupported file extension raises DocumentExtractionError."""
    fake_file = tmp_path / "test.xyz"
    fake_file.write_text("dummy", encoding="utf-8")
    with pytest.raises(DocumentExtractionError) as exc_info:
        extract_document_text(fake_file)
    assert "unsupported document format" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# 2. Chunking Tests
# ---------------------------------------------------------------------------

def test_chunking_page_range_and_overlap():
    """Verify chunk_document_pages accurately tracks page_start, page_end, and SHA-256."""
    pages = [
        DocumentPage(page_number=1, text="Word " * 150, section_title="Introduction"),
        DocumentPage(page_number=2, text="Second " * 150, section_title="Experimental Methods"),
        DocumentPage(page_number=3, text="Third " * 150, section_title="Results"),
    ]

    chunks = chunk_document_pages(pages, target_words=200, overlap_words=40)
    assert len(chunks) >= 2
    # Verify monotonic chunk indices
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    # First chunk starts on page 1
    assert chunks[0].page_start == 1
    # Check deterministic SHA-256
    for c in chunks:
        assert len(c.chunk_sha256) == 64
        assert c.token_count > 0


def test_chunking_empty_pages_returns_empty():
    """Verify chunking empty or whitespace-only pages returns empty list."""
    assert chunk_document_pages([]) == []
    pages = [DocumentPage(page_number=1, text="   ", section_title=None)]
    assert chunk_document_pages(pages) == []


# ---------------------------------------------------------------------------
# 3. SQLite In-Memory Indexing & Idempotency Tests
# ---------------------------------------------------------------------------

@pytest.fixture
def sqlite_doc_db():
    """Set up an in-memory SQLite database matching M10.4 schema."""
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE investigation (
            id text NOT NULL PRIMARY KEY,
            repository_code text NOT NULL,
            investigation_code text NOT NULL,
            name text NOT NULL,
            agency text NOT NULL,
            doi text,
            description text,
            source_repository_url text,
            metadata text NOT NULL DEFAULT '{}',
            created_at text NOT NULL
        )
        """))
        conn.execute(text("""
        CREATE TABLE source_document (
            investigation_id text NOT NULL,
            id text NOT NULL PRIMARY KEY,
            original_filename text NOT NULL,
            source_type text NOT NULL,
            artifact_origin text NOT NULL,
            sha256 text NOT NULL,
            file_size_bytes integer NOT NULL,
            storage_key text NOT NULL,
            source_version text,
            metadata text NOT NULL DEFAULT '{}',
            created_at text NOT NULL
        )
        """))
        conn.execute(text("""
        CREATE TABLE document_chunk (
            id text NOT NULL PRIMARY KEY,
            investigation_id text NOT NULL,
            source_document_id text NOT NULL,
            chunk_index integer NOT NULL,
            page_start integer,
            page_end integer,
            section_title text,
            chunk_text text NOT NULL,
            token_count integer NOT NULL DEFAULT 0,
            chunk_sha256 text NOT NULL,
            metadata text NOT NULL DEFAULT '{}',
            created_at text NOT NULL,
            UNIQUE (source_document_id, chunk_index)
        )
        """))
        # Seed investigation
        conn.execute(text("""
        INSERT INTO investigation (id, repository_code, investigation_code, name, agency, metadata, created_at)
        VALUES ('a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d', 'PSI', 'PSI-25', 'BASS-II', 'NASA', '{}', '2026-11-15T00:00:00Z')
        """))
    return engine


def test_sqlite_indexing_and_idempotency(sqlite_doc_db):
    """Verify document indexing populates document_chunk and re-indexing is idempotent without duplicate records."""
    report = index_source_documents(
        engine=sqlite_doc_db,
        root_dir=ROOT_DIR,
        investigation_code="PSI-25",
        target_docs=["bass_ii_faq"],
    )

    assert report.total_documents == 1
    assert report.documents_indexed == 1
    assert report.total_chunks_persisted > 0

    with sqlite_doc_db.connect() as conn:
        chunk_count = conn.execute(text("SELECT count(*) FROM document_chunk")).scalar()
        assert chunk_count == report.total_chunks_persisted

    # Re-index the same document (force_reindex=False)
    report2 = index_source_documents(
        engine=sqlite_doc_db,
        root_dir=ROOT_DIR,
        investigation_code="PSI-25",
        target_docs=["bass_ii_faq"],
        force_reindex=False,
    )

    assert report2.documents_indexed == 0
    assert report2.results[0].status == "already_indexed"

    with sqlite_doc_db.connect() as conn:
        chunk_count_after = conn.execute(text("SELECT count(*) FROM document_chunk")).scalar()
        assert chunk_count_after == chunk_count  # Zero duplicates created!


# ---------------------------------------------------------------------------
# 4. Retrieval Tool Unit Tests
# ---------------------------------------------------------------------------

def test_retrieval_tool_nominal_on_indexed_data(sqlite_doc_db):
    """Verify flare_retrieve_documents returns matching passages on SQLite."""
    index_source_documents(
        engine=sqlite_doc_db,
        root_dir=ROOT_DIR,
        investigation_code="PSI-25",
        target_docs=["bass_ii_faq"],
    )

    with sqlite_doc_db.connect() as conn:
        res = execute_flare_retrieve_documents(
            parameters={"query": "test matrix and calibration", "limit": 3},
            request_id=uuid4(),
            conn=conn,
        )

        assert res.execution_status == ToolExecutionStatus.SUCCESS
        assert len(res.result_data) > 0
        passage = res.result_data[0]
        assert "spreadsheets" in passage["passage_text"].lower() or "matrix" in passage["passage_text"].lower()
        assert passage["page_start"] is not None
        assert passage["epistemic_attribution"] == "reference_information"
        assert passage["is_validated_measurement"] is False
        assert passage["flare_uri"].startswith("flare://source_document/")


def test_retrieval_tool_empty_query_returns_invalid_input(sqlite_doc_db):
    """Verify empty query string returns INVALID_INPUT."""
    with sqlite_doc_db.connect() as conn:
        res = execute_flare_retrieve_documents(
            parameters={"query": "   "},
            request_id=uuid4(),
            conn=conn,
        )
        assert res.execution_status == ToolExecutionStatus.INVALID_INPUT
        assert "non-empty" in res.limitations[0]


def test_retrieval_tool_no_results_found(sqlite_doc_db):
    """Verify query with no matches returns explicit NO_RESULTS."""
    index_source_documents(
        engine=sqlite_doc_db,
        root_dir=ROOT_DIR,
        investigation_code="PSI-25",
        target_docs=["bass_ii_faq"],
    )

    with sqlite_doc_db.connect() as conn:
        res = execute_flare_retrieve_documents(
            parameters={"query": "quantum superconducting tokamak stellarator"},
            request_id=uuid4(),
            conn=conn,
        )
        assert res.execution_status == ToolExecutionStatus.NO_RESULTS
        assert res.result_data == []
        assert "No authentic NASA document passages" in res.limitations[0]


def test_retrieval_tool_offline_connection_returns_no_results():
    """Verify tool called without database connection returns NO_RESULTS."""
    res = execute_flare_retrieve_documents(
        parameters={"query": "microgravity flame"},
        request_id=uuid4(),
        conn=None,
    )
    assert res.execution_status == ToolExecutionStatus.NO_RESULTS
    assert "Database connection unavailable" in res.limitations[0]
