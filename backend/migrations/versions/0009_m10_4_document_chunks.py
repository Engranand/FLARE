"""Milestone 10.4: Document Chunking and Full-Text Search Schema.

Creates:
1. public.document_chunk: Stores structured text chunks extracted from NASA source documents (PDF/DOCX),
   preserving page references, section titles, chunk SHA-256, and metadata.
2. PostgreSQL tsvector generated column tsv_content for core full-text indexing.
3. GIN index ix_document_chunk_tsv for high-performance natural-language phrase and keyword retrieval.
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_m10_4_document_chunks"
down_revision = "0008_m6_security_remediation"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        op.execute("""
        CREATE TABLE IF NOT EXISTS public.document_chunk (
            id uuid NOT NULL PRIMARY KEY,
            investigation_id uuid NOT NULL,
            source_document_id uuid NOT NULL,
            chunk_index integer NOT NULL,
            page_start integer,
            page_end integer,
            section_title text,
            chunk_text text NOT NULL,
            token_count integer NOT NULL DEFAULT 0,
            chunk_sha256 text NOT NULL,
            metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
            tsv_content tsvector GENERATED ALWAYS AS (to_tsvector('english', chunk_text)) STORED,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_document_chunk_idx UNIQUE (source_document_id, chunk_index),
            CONSTRAINT fk_document_chunk_source_doc FOREIGN KEY (investigation_id, source_document_id)
                REFERENCES public.source_document (investigation_id, id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS ix_document_chunk_tsv ON public.document_chunk USING gin (tsv_content);
        CREATE INDEX IF NOT EXISTS ix_document_chunk_inv_doc ON public.document_chunk (investigation_id, source_document_id);
        """)
    else:
        # SQLite / in-memory test dialect
        op.execute("""
        CREATE TABLE IF NOT EXISTS document_chunk (
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
        );
        """)


def downgrade():
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    if dialect_name == "postgresql":
        op.execute("DROP TABLE IF EXISTS public.document_chunk CASCADE;")
    else:
        op.execute("DROP TABLE IF EXISTS document_chunk;")
