"""Document Indexing Pipeline for NASA Scientific Literature (Milestone 10.4).

Processes registered NASA PDF and DOCX files:
- Verifies local file SHA-256 byte identity.
- Extracts text while preserving 1-indexed page numbers and section headers.
- Splits into deterministic chunks.
- Persists into public.source_document and public.document_chunk.
- Guarantees deterministic, idempotent re-indexing without duplicate records.
- Preserves raw NASA source files completely read-only.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Connection, Engine, text

from app.documents.chunker import DocumentChunkData, chunk_document_pages
from app.documents.extractor import extract_document_text
from app.documents.registry import (
    REGISTERED_DOCUMENTS,
    RegisteredDocumentSpec,
    chunk_uuid,
    doc_uuid,
)


@dataclass
class IndexedDocumentResult:
    """Summary of an individual document's indexing run."""
    doc_key: str
    original_filename: str
    sha256: str
    total_pages: int
    total_chunks: int
    status: str  # 'indexed', 'already_indexed', 'skipped', 'failed'
    duration_ms: float
    error_message: str | None = None


@dataclass
class DocumentIndexReport:
    """Overall summary of the document indexing pipeline."""
    total_documents: int
    documents_indexed: int
    total_chunks_persisted: int
    results: list[IndexedDocumentResult]
    total_duration_ms: float


def compute_file_sha256(path: Path) -> tuple[str, int]:
    """Calculate SHA-256 and byte length of a local file in streaming blocks."""
    hasher = hashlib.sha256()
    size = 0
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
            size += len(chunk)
    return hasher.hexdigest(), size


def index_single_document(
    conn: Connection,
    spec: RegisteredDocumentSpec,
    root_dir: Path,
    inv_id: UUID,
    force_reindex: bool = False,
) -> IndexedDocumentResult:
    """Index a single registered document into the database within an active transaction.
    
    Args:
        conn: Active database Connection.
        spec: Registered document specification.
        root_dir: Workspace root directory.
        inv_id: Target investigation UUID.
        force_reindex: Whether to re-extract and upsert chunks if already present.
        
    Returns:
        IndexedDocumentResult detailing pages, chunks, and timing.
    """
    t_start = time.perf_counter()
    full_path = root_dir / spec.relative_path

    if not full_path.is_file():
        return IndexedDocumentResult(
            doc_key=spec.doc_key,
            original_filename=spec.original_filename,
            sha256="",
            total_pages=0,
            total_chunks=0,
            status="failed",
            duration_ms=(time.perf_counter() - t_start) * 1000,
            error_message=f"File not found on disk: {spec.relative_path}",
        )

    # 1. Compute authentic byte SHA-256 and file size
    file_sha256, file_size = compute_file_sha256(full_path)
    document_id = doc_uuid(file_sha256)
    now = datetime.now(timezone.utc)

    # 2. Ensure source_document row exists
    doc_metadata = {
        "doc_key": spec.doc_key,
        "title": spec.title,
        "description": spec.description,
        "authors": spec.authors,
        "publication_year": spec.publication_year,
        "doi": spec.doi,
        "document_type": spec.document_type,
        "epistemic_attribution": spec.epistemic_attribution,
        "is_validated_measurement": False,
        "milestone": "M10.4",
    }

    if conn.dialect.name == "postgresql":
        conn.execute(
            text("""
            INSERT INTO public.source_document (
                investigation_id, id, original_filename, source_type,
                artifact_origin, sha256, file_size_bytes, storage_key,
                source_version, metadata, created_at
            ) VALUES (
                :inv, :id, :filename, :stype,
                'external_original', :sha256, :size, :storage_key,
                :ver, :metadata, :now
            ) ON CONFLICT (investigation_id, sha256) DO NOTHING
            """),
            {
                "inv": inv_id,
                "id": document_id,
                "filename": spec.original_filename,
                "stype": spec.source_type,
                "sha256": file_sha256,
                "size": file_size,
                "storage_key": spec.relative_path,
                "ver": "1.0",
                "metadata": json.dumps(doc_metadata),
                "now": now,
            },
        )
        # Fetch the actual document_id in case the row already existed with a different UUID
        existing_doc_row = conn.execute(
            text("SELECT id FROM public.source_document WHERE investigation_id = :inv AND sha256 = :sha256"),
            {"inv": inv_id, "sha256": file_sha256},
        ).fetchone()
        if existing_doc_row is not None:
            raw_id = existing_doc_row[0]
            document_id = UUID(str(raw_id)) if not isinstance(raw_id, UUID) else raw_id
    else:
        conn.execute(
            text("""
            INSERT OR IGNORE INTO source_document (
                investigation_id, id, original_filename, source_type,
                artifact_origin, sha256, file_size_bytes, storage_key,
                source_version, metadata, created_at
            ) VALUES (
                :inv, :id, :filename, :stype,
                'external_original', :sha256, :size, :storage_key,
                :ver, :metadata, :now
            )
            """),
            {
                "inv": str(inv_id),
                "id": str(document_id),
                "filename": spec.original_filename,
                "stype": spec.source_type,
                "sha256": file_sha256,
                "size": file_size,
                "storage_key": spec.relative_path,
                "ver": "1.0",
                "metadata": json.dumps(doc_metadata),
                "now": now.isoformat(),
            },
        )
        existing_doc_row = conn.execute(
            text("SELECT id FROM source_document WHERE investigation_id = :inv AND sha256 = :sha256"),
            {"inv": str(inv_id), "sha256": file_sha256},
        ).fetchone()
        if existing_doc_row is not None:
            raw_id = existing_doc_row[0]
            document_id = UUID(str(raw_id)) if not isinstance(raw_id, UUID) else raw_id

    # 3. Check if chunks are already indexed (Idempotency)
    chunk_table = "public.document_chunk" if conn.dialect.name == "postgresql" else "document_chunk"
    existing_chunks_count = conn.execute(
        text(f"SELECT count(*) FROM {chunk_table} WHERE source_document_id = :did"),
        {"did": document_id if conn.dialect.name == "postgresql" else str(document_id)},
    ).scalar() or 0

    if existing_chunks_count > 0 and not force_reindex:
        return IndexedDocumentResult(
            doc_key=spec.doc_key,
            original_filename=spec.original_filename,
            sha256=file_sha256,
            total_pages=0,
            total_chunks=existing_chunks_count,
            status="already_indexed",
            duration_ms=(time.perf_counter() - t_start) * 1000,
        )

    # 4. Extract pages
    try:
        pages = extract_document_text(full_path)
    except Exception as exc:
        return IndexedDocumentResult(
            doc_key=spec.doc_key,
            original_filename=spec.original_filename,
            sha256=file_sha256,
            total_pages=0,
            total_chunks=0,
            status="failed",
            duration_ms=(time.perf_counter() - t_start) * 1000,
            error_message=f"Text extraction failed: {exc}",
        )

    # 5. Chunk pages
    chunks = chunk_document_pages(pages, target_words=250, overlap_words=40)

    # 6. Upsert chunks
    for ch in chunks:
        cid = chunk_uuid(document_id, ch.chunk_index)
        meta_dict = {
            "source_document_sha256": file_sha256,
            "source_document_filename": spec.original_filename,
            "document_title": spec.title,
            "epistemic_attribution": spec.epistemic_attribution,
            "document_type": spec.document_type,
            "authors": spec.authors,
            "publication_year": spec.publication_year,
            "is_validated_measurement": False,
            "flare_uri": f"flare://source_document/{document_id}#page={ch.page_start}&chunk={ch.chunk_index}",
        }

        if conn.dialect.name == "postgresql":
            conn.execute(
                text("""
                INSERT INTO public.document_chunk (
                    id, investigation_id, source_document_id, chunk_index,
                    page_start, page_end, section_title, chunk_text,
                    token_count, chunk_sha256, metadata, created_at
                ) VALUES (
                    :id, :inv, :did, :idx,
                    :p_start, :p_end, :sec, :text,
                    :tokens, :sha256, :meta, :now
                )
                ON CONFLICT (source_document_id, chunk_index) DO UPDATE
                SET chunk_text = EXCLUDED.chunk_text,
                    page_start = EXCLUDED.page_start,
                    page_end = EXCLUDED.page_end,
                    section_title = EXCLUDED.section_title,
                    token_count = EXCLUDED.token_count,
                    chunk_sha256 = EXCLUDED.chunk_sha256,
                    metadata = EXCLUDED.metadata
                """),
                {
                    "id": cid,
                    "inv": inv_id,
                    "did": document_id,
                    "idx": ch.chunk_index,
                    "p_start": ch.page_start,
                    "p_end": ch.page_end,
                    "sec": ch.section_title,
                    "text": ch.chunk_text,
                    "tokens": ch.token_count,
                    "sha256": ch.chunk_sha256,
                    "meta": json.dumps(meta_dict),
                    "now": now,
                },
            )
        else:
            conn.execute(
                text("""
                INSERT INTO document_chunk (
                    id, investigation_id, source_document_id, chunk_index,
                    page_start, page_end, section_title, chunk_text,
                    token_count, chunk_sha256, metadata, created_at
                ) VALUES (
                    :id, :inv, :did, :idx,
                    :p_start, :p_end, :sec, :text,
                    :tokens, :sha256, :meta, :now
                )
                ON CONFLICT (source_document_id, chunk_index) DO UPDATE
                SET chunk_text = excluded.chunk_text,
                    page_start = excluded.page_start,
                    page_end = excluded.page_end,
                    section_title = excluded.section_title,
                    token_count = excluded.token_count,
                    chunk_sha256 = excluded.chunk_sha256,
                    metadata = excluded.metadata
                """),
                {
                    "id": str(cid),
                    "inv": str(inv_id),
                    "did": str(document_id),
                    "idx": ch.chunk_index,
                    "p_start": ch.page_start,
                    "p_end": ch.page_end,
                    "sec": ch.section_title,
                    "text": ch.chunk_text,
                    "tokens": ch.token_count,
                    "sha256": ch.chunk_sha256,
                    "meta": json.dumps(meta_dict),
                    "now": now.isoformat(),
                },
            )

    duration = (time.perf_counter() - t_start) * 1000
    return IndexedDocumentResult(
        doc_key=spec.doc_key,
        original_filename=spec.original_filename,
        sha256=file_sha256,
        total_pages=len(pages),
        total_chunks=len(chunks),
        status="indexed",
        duration_ms=duration,
    )


def index_source_documents(
    engine: Engine,
    root_dir: Path,
    investigation_code: str = "PSI-25",
    target_docs: list[str] | None = None,
    force_reindex: bool = False,
) -> DocumentIndexReport:
    """Execute the full document indexing pipeline for registered NASA documents.
    
    Args:
        engine: SQLAlchemy Engine.
        root_dir: Workspace root directory.
        investigation_code: Target investigation code (e.g. "PSI-25").
        target_docs: Optional filter of doc_keys to index.
        force_reindex: Re-extract and update chunks if already indexed.
        
    Returns:
        DocumentIndexReport summarizing indexing results.
    """
    t_start = time.perf_counter()
    specs_to_index = [
        spec for key, spec in REGISTERED_DOCUMENTS.items()
        if (target_docs is None or key in target_docs)
    ]

    results: list[IndexedDocumentResult] = []
    total_chunks = 0
    docs_indexed_count = 0

    with engine.begin() as conn:
        # Resolve investigation UUID
        inv_row = conn.execute(
            text("SELECT id FROM public.investigation WHERE investigation_code = :code" if conn.dialect.name == "postgresql" else "SELECT id FROM investigation WHERE investigation_code = :code"),
            {"code": investigation_code},
        ).mappings().first()

        if inv_row is None:
            # If investigation record doesn't exist yet, insert a placeholder or raise
            inv_id = UUID("a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d")
        else:
            inv_id = inv_row["id"] if isinstance(inv_row["id"], UUID) else UUID(inv_row["id"])

        for spec in specs_to_index:
            res = index_single_document(
                conn=conn,
                spec=spec,
                root_dir=root_dir,
                inv_id=inv_id,
                force_reindex=force_reindex,
            )
            results.append(res)
            if res.status in ("indexed", "already_indexed"):
                total_chunks += res.total_chunks
                if res.status == "indexed":
                    docs_indexed_count += 1

    total_duration = (time.perf_counter() - t_start) * 1000
    return DocumentIndexReport(
        total_documents=len(specs_to_index),
        documents_indexed=docs_indexed_count,
        total_chunks_persisted=total_chunks,
        results=results,
        total_duration_ms=total_duration,
    )
