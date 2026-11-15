"""Document Chunking Logic for Scientific Passage Retrieval (Milestone 10.4).

Chunks extracted document pages into coherent scientific passages while preserving
exact page numbers, section titles, and deterministic chunk SHA-256 hashes.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

from app.documents.extractor import DocumentPage


@dataclass(frozen=True)
class DocumentChunkData:
    """Represents a bounded passage of text with complete provenance."""
    chunk_index: int
    page_start: int
    page_end: int
    section_title: str | None
    chunk_text: str
    token_count: int
    chunk_sha256: str


def chunk_document_pages(
    pages: list[DocumentPage],
    target_words: int = 250,
    overlap_words: int = 40,
) -> list[DocumentChunkData]:
    """Split document pages into coherent chunks with page-range tracking.
    
    Args:
        pages: List of DocumentPage objects from document extraction.
        target_words: Target word length for each chunk.
        overlap_words: Word count overlap between consecutive chunks.
        
    Returns:
        List of DocumentChunkData objects.
    """
    if not pages:
        return []

    chunks: list[DocumentChunkData] = []
    chunk_idx = 0

    # Flatten pages into tokens with page and section annotations
    token_items: list[tuple[str, int, str | None]] = []
    for page in pages:
        raw_text = page.text.strip()
        if not raw_text:
            continue
        words = raw_text.split()
        for w in words:
            token_items.append((w, page.page_number, page.section_title))

    if not token_items:
        return []

    i = 0
    total_tokens = len(token_items)

    while i < total_tokens:
        end = min(i + target_words, total_tokens)
        slice_items = token_items[i:end]

        chunk_words = [item[0] for item in slice_items]
        chunk_text = " ".join(chunk_words)

        page_start = slice_items[0][1]
        page_end = slice_items[-1][1]

        # Use first non-empty section title found in the chunk
        section_title = next((item[2] for item in slice_items if item[2]), None)

        token_count = len(chunk_words)
        chunk_sha256 = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()

        chunks.append(
            DocumentChunkData(
                chunk_index=chunk_idx,
                page_start=page_start,
                page_end=page_end,
                section_title=section_title,
                chunk_text=chunk_text,
                token_count=token_count,
                chunk_sha256=chunk_sha256,
            )
        )
        chunk_idx += 1

        if end >= total_tokens:
            break

        # Advance by target_words - overlap_words
        step = max(1, target_words - overlap_words)
        i += step

    return chunks
