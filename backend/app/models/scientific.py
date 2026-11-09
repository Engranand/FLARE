"""Approved M4.2 declarative schema. FK scalar columns own writes; references are read-only."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (BigInteger, CheckConstraint, Date, DateTime, ForeignKeyConstraint, Index, Integer, Numeric, PrimaryKeyConstraint, Text, UniqueConstraint, and_, text)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import conv
from app.db.base import Base


class Investigation(Base):
    __tablename__ = 'investigation'

    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    repository_code: Mapped[str] = mapped_column('repository_code', Text(), nullable=False)
    investigation_code: Mapped[str] = mapped_column('investigation_code', Text(), nullable=False)
    name: Mapped[str] = mapped_column('name', Text(), nullable=False)
    agency: Mapped[str] = mapped_column('agency', Text(), nullable=False)
    doi: Mapped[str | None] = mapped_column('doi', Text(), nullable=True)
    description: Mapped[str | None] = mapped_column('description', Text(), nullable=True)
    source_repository_url: Mapped[str] = mapped_column('source_repository_url', Text(), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column('metadata', JSONB(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('id', name=conv('pk_investigation_01')),
        UniqueConstraint('repository_code', 'investigation_code', name=conv('uq_investigation_01')),
        CheckConstraint("jsonb_typeof(metadata) = 'object'", name=conv('ck_investigation_01')),
    )


class SourceDocument(Base):
    __tablename__ = 'source_document'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    original_filename: Mapped[str] = mapped_column('original_filename', Text(), nullable=False)
    source_type: Mapped[str] = mapped_column('source_type', Text(), nullable=False)
    artifact_origin: Mapped[str] = mapped_column('artifact_origin', Text(), nullable=False)
    sha256: Mapped[str] = mapped_column('sha256', Text(), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column('file_size_bytes', BigInteger(), nullable=False)
    storage_key: Mapped[str] = mapped_column('storage_key', Text(), nullable=False)
    source_version: Mapped[str | None] = mapped_column('source_version', Text(), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column('metadata', JSONB(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_source_document_01')),
        UniqueConstraint('investigation_id', 'sha256', name=conv('uq_source_document_01')),
        CheckConstraint("source_type IN ('csv','xlsx','docx','pdf','image','video','other')", name=conv('ck_source_document_01')),
        CheckConstraint("artifact_origin IN ('external_original','generated_artifact','software_artifact')", name=conv('ck_source_document_02')),
        CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'", name=conv('ck_source_document_03')),
        CheckConstraint('file_size_bytes >= 0', name=conv('ck_source_document_04')),
        CheckConstraint("jsonb_typeof(metadata) = 'object'", name=conv('ck_source_document_05')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='source_document_investigation_id_fk', ondelete="RESTRICT"),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(SourceDocument.investigation_id == Investigation.id),
        foreign_keys=lambda: [SourceDocument.investigation_id],
        viewonly=True, lazy="raise",
    )

class SourceAcquisition(Base):
    __tablename__ = 'source_acquisition'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    source_document_id: Mapped[UUID | None] = mapped_column('source_document_id', PGUUID(as_uuid=True), nullable=True)
    actual_filename: Mapped[str | None] = mapped_column('actual_filename', Text(), nullable=True)
    portal_filename_alias: Mapped[str | None] = mapped_column('portal_filename_alias', Text(), nullable=True)
    source_page_url: Mapped[str | None] = mapped_column('source_page_url', Text(), nullable=True)
    original_download_url: Mapped[str | None] = mapped_column('original_download_url', Text(), nullable=True)
    local_relative_path: Mapped[str | None] = mapped_column('local_relative_path', Text(), nullable=True)
    retrieved_at: Mapped[datetime | None] = mapped_column('retrieved_at', DateTime(timezone=True), nullable=True)
    verified_at: Mapped[datetime] = mapped_column('verified_at', DateTime(timezone=True), nullable=False)
    verification_status: Mapped[str] = mapped_column('verification_status', Text(), nullable=False)
    verification_scope: Mapped[str] = mapped_column('verification_scope', Text(), nullable=False)
    method: Mapped[str] = mapped_column('method', Text(), nullable=False)
    actor_ref: Mapped[str] = mapped_column('actor_ref', Text(), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column('metadata', JSONB(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_source_acquisition_01')),
        CheckConstraint("verification_status IN ('verified','failed','unverified')", name=conv('ck_source_acquisition_01')),
        CheckConstraint("verification_status <> 'verified' OR (source_document_id IS NOT NULL AND actual_filename IS NOT NULL)", name=conv('ck_source_acquisition_02')),
        CheckConstraint("jsonb_typeof(metadata) = 'object'", name=conv('ck_source_acquisition_03')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='source_acquisition_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'source_document_id'], ['source_document.investigation_id', 'source_document.id'], name='source_acquisition_source_document_id_fk', ondelete="RESTRICT"),
        Index('lookup_2', 'investigation_id', 'source_document_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(SourceAcquisition.investigation_id == Investigation.id),
        foreign_keys=lambda: [SourceAcquisition.investigation_id],
        viewonly=True, lazy="raise",
    )
    source_document_ref: Mapped[SourceDocument | None] = relationship(
        'SourceDocument', primaryjoin=lambda: and_(SourceAcquisition.investigation_id == SourceDocument.investigation_id, SourceAcquisition.source_document_id == SourceDocument.id),
        foreign_keys=lambda: [SourceAcquisition.investigation_id, SourceAcquisition.source_document_id],
        viewonly=True, lazy="raise",
    )

class EvidenceReference(Base):
    __tablename__ = 'evidence_reference'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    source_document_id: Mapped[UUID] = mapped_column('source_document_id', PGUUID(as_uuid=True), nullable=False)
    locator_kind: Mapped[str] = mapped_column('locator_kind', Text(), nullable=False)
    locator_key: Mapped[str] = mapped_column('locator_key', Text(), nullable=False)
    locator_version: Mapped[str] = mapped_column('locator_version', Text(), nullable=False)
    locator: Mapped[dict[str, Any]] = mapped_column('locator', JSONB(), nullable=False)
    excerpt: Mapped[str | None] = mapped_column('excerpt', Text(), nullable=True)
    location_basis: Mapped[str] = mapped_column('location_basis', Text(), nullable=False)
    extraction_method: Mapped[str] = mapped_column('extraction_method', Text(), nullable=False)
    extractor_version: Mapped[str] = mapped_column('extractor_version', Text(), nullable=False)
    verification_status: Mapped[str] = mapped_column('verification_status', Text(), nullable=False)
    verification_scope: Mapped[str] = mapped_column('verification_scope', Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_evidence_reference_01')),
        UniqueConstraint('investigation_id', 'source_document_id', 'locator_version', 'locator_key', name=conv('uq_evidence_reference_01')),
        CheckConstraint("locator_kind IN ('csv','xlsx','docx','pdf','image','video','document')", name=conv('ck_evidence_reference_01')),
        CheckConstraint("verification_status IN ('verified','unverified','needs_review')", name=conv('ck_evidence_reference_02')),
        CheckConstraint("jsonb_typeof(locator) = 'object'", name=conv('ck_evidence_reference_03')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='evidence_reference_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'source_document_id'], ['source_document.investigation_id', 'source_document.id'], name='evidence_reference_source_document_id_fk', ondelete="RESTRICT"),
        Index('lookup_4', 'investigation_id', 'source_document_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(EvidenceReference.investigation_id == Investigation.id),
        foreign_keys=lambda: [EvidenceReference.investigation_id],
        viewonly=True, lazy="raise",
    )
    source_document_ref: Mapped[SourceDocument] = relationship(
        'SourceDocument', primaryjoin=lambda: and_(EvidenceReference.investigation_id == SourceDocument.investigation_id, EvidenceReference.source_document_id == SourceDocument.id),
        foreign_keys=lambda: [EvidenceReference.investigation_id, EvidenceReference.source_document_id],
        viewonly=True, lazy="raise",
    )

class ParseRun(Base):
    __tablename__ = 'parse_run'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    source_document_id: Mapped[UUID] = mapped_column('source_document_id', PGUUID(as_uuid=True), nullable=False)
    parser_name: Mapped[str] = mapped_column('parser_name', Text(), nullable=False)
    parser_version: Mapped[str] = mapped_column('parser_version', Text(), nullable=False)
    code_sha256: Mapped[str] = mapped_column('code_sha256', Text(), nullable=False)
    code_storage_key: Mapped[str] = mapped_column('code_storage_key', Text(), nullable=False)
    configuration_sha256: Mapped[str] = mapped_column('configuration_sha256', Text(), nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column('configuration', JSONB(), nullable=False)
    output_sha256: Mapped[str] = mapped_column('output_sha256', Text(), nullable=False)
    output_storage_key: Mapped[str] = mapped_column('output_storage_key', Text(), nullable=False)
    record_count: Mapped[int] = mapped_column('record_count', BigInteger(), nullable=False)
    status: Mapped[str] = mapped_column('status', Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_parse_run_01')),
        UniqueConstraint('investigation_id', 'source_document_id', 'parser_name', 'parser_version', 'code_sha256', 'configuration_sha256', 'output_sha256', name=conv('uq_parse_run_01')),
        CheckConstraint("status IN ('complete','failed')", name=conv('ck_parse_run_01')),
        CheckConstraint('record_count >= 0', name=conv('ck_parse_run_02')),
        CheckConstraint("code_sha256 ~ '^[0-9a-f]{64}$'", name=conv('ck_parse_run_03')),
        CheckConstraint("configuration_sha256 ~ '^[0-9a-f]{64}$'", name=conv('ck_parse_run_04')),
        CheckConstraint("jsonb_typeof(configuration) = 'object'", name=conv('ck_parse_run_05')),
        CheckConstraint("output_sha256 ~ '^[0-9a-f]{64}$'", name=conv('ck_parse_run_06')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='parse_run_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'source_document_id'], ['source_document.investigation_id', 'source_document.id'], name='parse_run_source_document_id_fk', ondelete="RESTRICT"),
        Index('lookup_6', 'investigation_id', 'source_document_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(ParseRun.investigation_id == Investigation.id),
        foreign_keys=lambda: [ParseRun.investigation_id],
        viewonly=True, lazy="raise",
    )
    source_document_ref: Mapped[SourceDocument] = relationship(
        'SourceDocument', primaryjoin=lambda: and_(ParseRun.investigation_id == SourceDocument.investigation_id, ParseRun.source_document_id == SourceDocument.id),
        foreign_keys=lambda: [ParseRun.investigation_id, ParseRun.source_document_id],
        viewonly=True, lazy="raise",
    )

class SourceField(Base):
    __tablename__ = 'source_field'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    parse_run_id: Mapped[UUID] = mapped_column('parse_run_id', PGUUID(as_uuid=True), nullable=False)
    table_key: Mapped[str] = mapped_column('table_key', Text(), nullable=False)
    ordinal: Mapped[int] = mapped_column('ordinal', Integer(), nullable=False)
    original_header: Mapped[str] = mapped_column('original_header', Text(), nullable=False)
    raw_unit: Mapped[str | None] = mapped_column('raw_unit', Text(), nullable=True)
    raw_unit_status: Mapped[str] = mapped_column('raw_unit_status', Text(), nullable=False)
    header_evidence_id: Mapped[UUID] = mapped_column('header_evidence_id', PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_source_field_01')),
        UniqueConstraint('investigation_id', 'parse_run_id', 'table_key', 'ordinal', name=conv('uq_source_field_01')),
        UniqueConstraint('investigation_id', 'parse_run_id', 'id', name=conv('uq_source_field_02')),
        CheckConstraint('ordinal > 0', name=conv('ck_source_field_01')),
        CheckConstraint("raw_unit_status IN ('stated','not_stated','not_applicable')", name=conv('ck_source_field_02')),
        CheckConstraint("(raw_unit_status = 'stated') = (raw_unit IS NOT NULL)", name=conv('ck_source_field_03')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='source_field_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'parse_run_id'], ['parse_run.investigation_id', 'parse_run.id'], name='source_field_parse_run_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'header_evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='source_field_header_evidence_id_fk', ondelete="RESTRICT"),
        Index('lookup_8', 'investigation_id', 'parse_run_id', unique=False),
        Index('lookup_9', 'investigation_id', 'header_evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(SourceField.investigation_id == Investigation.id),
        foreign_keys=lambda: [SourceField.investigation_id],
        viewonly=True, lazy="raise",
    )
    parse_run_ref: Mapped[ParseRun] = relationship(
        'ParseRun', primaryjoin=lambda: and_(SourceField.investigation_id == ParseRun.investigation_id, SourceField.parse_run_id == ParseRun.id),
        foreign_keys=lambda: [SourceField.investigation_id, SourceField.parse_run_id],
        viewonly=True, lazy="raise",
    )
    header_evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(SourceField.investigation_id == EvidenceReference.investigation_id, SourceField.header_evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [SourceField.investigation_id, SourceField.header_evidence_id],
        viewonly=True, lazy="raise",
    )

class SourceRecord(Base):
    __tablename__ = 'source_record'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    parse_run_id: Mapped[UUID] = mapped_column('parse_run_id', PGUUID(as_uuid=True), nullable=False)
    table_key: Mapped[str] = mapped_column('table_key', Text(), nullable=False)
    source_record_number: Mapped[int] = mapped_column('source_record_number', BigInteger(), nullable=False)
    source_row_id: Mapped[str] = mapped_column('source_row_id', Text(), nullable=False)
    row_evidence_id: Mapped[UUID] = mapped_column('row_evidence_id', PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_source_record_01')),
        UniqueConstraint('investigation_id', 'parse_run_id', 'table_key', 'source_record_number', name=conv('uq_source_record_01')),
        UniqueConstraint('investigation_id', 'parse_run_id', 'id', name=conv('uq_source_record_02')),
        UniqueConstraint('investigation_id', 'parse_run_id', 'source_row_id', name=conv('uq_source_record_03')),
        CheckConstraint('source_record_number > 0', name=conv('ck_source_record_01')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='source_record_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'parse_run_id'], ['parse_run.investigation_id', 'parse_run.id'], name='source_record_parse_run_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'row_evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='source_record_row_evidence_id_fk', ondelete="RESTRICT"),
        Index('lookup_11', 'investigation_id', 'parse_run_id', unique=False),
        Index('lookup_12', 'investigation_id', 'row_evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(SourceRecord.investigation_id == Investigation.id),
        foreign_keys=lambda: [SourceRecord.investigation_id],
        viewonly=True, lazy="raise",
    )
    parse_run_ref: Mapped[ParseRun] = relationship(
        'ParseRun', primaryjoin=lambda: and_(SourceRecord.investigation_id == ParseRun.investigation_id, SourceRecord.parse_run_id == ParseRun.id),
        foreign_keys=lambda: [SourceRecord.investigation_id, SourceRecord.parse_run_id],
        viewonly=True, lazy="raise",
    )
    row_evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(SourceRecord.investigation_id == EvidenceReference.investigation_id, SourceRecord.row_evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [SourceRecord.investigation_id, SourceRecord.row_evidence_id],
        viewonly=True, lazy="raise",
    )

class ExperimentalTest(Base):
    __tablename__ = 'experimental_test'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    identity_namespace: Mapped[str] = mapped_column('identity_namespace', Text(), nullable=False)
    test_identifier: Mapped[str] = mapped_column('test_identifier', Text(), nullable=False)
    identity_evidence_id: Mapped[UUID] = mapped_column('identity_evidence_id', PGUUID(as_uuid=True), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column('metadata', JSONB(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_experimental_test_01')),
        UniqueConstraint('investigation_id', 'identity_namespace', 'test_identifier', name=conv('uq_experimental_test_01')),
        CheckConstraint("jsonb_typeof(metadata) = 'object'", name=conv('ck_experimental_test_01')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='experimental_test_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'identity_evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='experimental_test_identity_evidence_id_fk', ondelete="RESTRICT"),
        Index('lookup_14', 'investigation_id', 'identity_evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(ExperimentalTest.investigation_id == Investigation.id),
        foreign_keys=lambda: [ExperimentalTest.investigation_id],
        viewonly=True, lazy="raise",
    )
    identity_evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(ExperimentalTest.investigation_id == EvidenceReference.investigation_id, ExperimentalTest.identity_evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [ExperimentalTest.investigation_id, ExperimentalTest.identity_evidence_id],
        viewonly=True, lazy="raise",
    )

class TestSourceRecord(Base):
    __tablename__ = 'test_source_record'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    experimental_test_id: Mapped[UUID] = mapped_column('experimental_test_id', PGUUID(as_uuid=True), nullable=False)
    source_record_id: Mapped[UUID] = mapped_column('source_record_id', PGUUID(as_uuid=True), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    match_method: Mapped[str] = mapped_column('match_method', Text(), nullable=False)
    method_version: Mapped[str] = mapped_column('method_version', Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_test_source_record_01')),
        UniqueConstraint('investigation_id', 'experimental_test_id', 'source_record_id', name=conv('uq_test_source_record_01')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='test_source_record_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'experimental_test_id'], ['experimental_test.investigation_id', 'experimental_test.id'], name='test_source_record_experimental_test_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'source_record_id'], ['source_record.investigation_id', 'source_record.id'], name='test_source_record_source_record_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='test_source_record_evidence_id_fk', ondelete="RESTRICT"),
        Index('lookup_16', 'investigation_id', 'experimental_test_id', unique=False),
        Index('lookup_17', 'investigation_id', 'source_record_id', unique=False),
        Index('lookup_18', 'investigation_id', 'evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(TestSourceRecord.investigation_id == Investigation.id),
        foreign_keys=lambda: [TestSourceRecord.investigation_id],
        viewonly=True, lazy="raise",
    )
    experimental_test_ref: Mapped[ExperimentalTest] = relationship(
        'ExperimentalTest', primaryjoin=lambda: and_(TestSourceRecord.investigation_id == ExperimentalTest.investigation_id, TestSourceRecord.experimental_test_id == ExperimentalTest.id),
        foreign_keys=lambda: [TestSourceRecord.investigation_id, TestSourceRecord.experimental_test_id],
        viewonly=True, lazy="raise",
    )
    source_record_ref: Mapped[SourceRecord] = relationship(
        'SourceRecord', primaryjoin=lambda: and_(TestSourceRecord.investigation_id == SourceRecord.investigation_id, TestSourceRecord.source_record_id == SourceRecord.id),
        foreign_keys=lambda: [TestSourceRecord.investigation_id, TestSourceRecord.source_record_id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(TestSourceRecord.investigation_id == EvidenceReference.investigation_id, TestSourceRecord.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [TestSourceRecord.investigation_id, TestSourceRecord.evidence_id],
        viewonly=True, lazy="raise",
    )

class TestRelationship(Base):
    __tablename__ = 'test_relationship'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    left_test_id: Mapped[UUID] = mapped_column('left_test_id', PGUUID(as_uuid=True), nullable=False)
    right_test_id: Mapped[UUID] = mapped_column('right_test_id', PGUUID(as_uuid=True), nullable=False)
    relationship_type: Mapped[str] = mapped_column('relationship_type', Text(), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    description: Mapped[str] = mapped_column('description', Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_test_relationship_01')),
        UniqueConstraint('investigation_id', 'left_test_id', 'right_test_id', 'relationship_type', 'evidence_id', name=conv('uq_test_relationship_01')),
        CheckConstraint('left_test_id <> right_test_id', name=conv('ck_test_relationship_01')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='test_relationship_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'left_test_id'], ['experimental_test.investigation_id', 'experimental_test.id'], name='test_relationship_left_test_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'right_test_id'], ['experimental_test.investigation_id', 'experimental_test.id'], name='test_relationship_right_test_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='test_relationship_evidence_id_fk', ondelete="RESTRICT"),
        Index('lookup_20', 'investigation_id', 'left_test_id', unique=False),
        Index('lookup_21', 'investigation_id', 'right_test_id', unique=False),
        Index('lookup_22', 'investigation_id', 'evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(TestRelationship.investigation_id == Investigation.id),
        foreign_keys=lambda: [TestRelationship.investigation_id],
        viewonly=True, lazy="raise",
    )
    left_test_ref: Mapped[ExperimentalTest] = relationship(
        'ExperimentalTest', primaryjoin=lambda: and_(TestRelationship.investigation_id == ExperimentalTest.investigation_id, TestRelationship.left_test_id == ExperimentalTest.id),
        foreign_keys=lambda: [TestRelationship.investigation_id, TestRelationship.left_test_id],
        viewonly=True, lazy="raise",
    )
    right_test_ref: Mapped[ExperimentalTest] = relationship(
        'ExperimentalTest', primaryjoin=lambda: and_(TestRelationship.investigation_id == ExperimentalTest.investigation_id, TestRelationship.right_test_id == ExperimentalTest.id),
        foreign_keys=lambda: [TestRelationship.investigation_id, TestRelationship.right_test_id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(TestRelationship.investigation_id == EvidenceReference.investigation_id, TestRelationship.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [TestRelationship.investigation_id, TestRelationship.evidence_id],
        viewonly=True, lazy="raise",
    )

class Observation(Base):
    __tablename__ = 'observation'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    parse_run_id: Mapped[UUID] = mapped_column('parse_run_id', PGUUID(as_uuid=True), nullable=False)
    source_record_id: Mapped[UUID] = mapped_column('source_record_id', PGUUID(as_uuid=True), nullable=False)
    source_field_id: Mapped[UUID] = mapped_column('source_field_id', PGUUID(as_uuid=True), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    raw_value: Mapped[str | None] = mapped_column('raw_value', Text(), nullable=True)
    source_value_kind: Mapped[str] = mapped_column('source_value_kind', Text(), nullable=False)
    unit_origin: Mapped[str] = mapped_column('unit_origin', Text(), nullable=False)
    raw_unit: Mapped[str | None] = mapped_column('raw_unit', Text(), nullable=True)
    unit_evidence_id: Mapped[UUID | None] = mapped_column('unit_evidence_id', PGUUID(as_uuid=True), nullable=True)
    parser_classification: Mapped[str] = mapped_column('parser_classification', Text(), nullable=False)
    parser_flags: Mapped[dict[str, Any]] = mapped_column('parser_flags', JSONB(), nullable=False)
    original_representation: Mapped[dict[str, Any]] = mapped_column('original_representation', JSONB(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_observation_01')),
        UniqueConstraint('investigation_id', 'parse_run_id', 'source_record_id', 'source_field_id', name=conv('uq_observation_01')),
        CheckConstraint("source_value_kind IN ('text','numeric_lexeme','empty_cell','other')", name=conv('ck_observation_01')),
        CheckConstraint("unit_origin IN ('field','cell','not_stated','not_applicable')", name=conv('ck_observation_02')),
        CheckConstraint("(unit_origin = 'cell') = (raw_unit IS NOT NULL)", name=conv('ck_observation_03')),
        CheckConstraint("(unit_origin = 'cell') = (unit_evidence_id IS NOT NULL)", name=conv('ck_observation_04')),
        CheckConstraint("(source_value_kind = 'empty_cell') = (raw_value IS NULL)", name=conv('ck_observation_05')),
        CheckConstraint("jsonb_typeof(parser_flags) = 'object'", name=conv('ck_observation_06')),
        CheckConstraint("jsonb_typeof(original_representation) = 'object'", name=conv('ck_observation_07')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='observation_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'parse_run_id'], ['parse_run.investigation_id', 'parse_run.id'], name='observation_parse_run_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'source_record_id'], ['source_record.investigation_id', 'source_record.id'], name='observation_source_record_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'source_field_id'], ['source_field.investigation_id', 'source_field.id'], name='observation_source_field_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='observation_evidence_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'unit_evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='observation_unit_evidence_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'parse_run_id', 'source_record_id'], ['source_record.investigation_id', 'source_record.parse_run_id', 'source_record.id'], name='observation_source_record_id_same_run_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'parse_run_id', 'source_field_id'], ['source_field.investigation_id', 'source_field.parse_run_id', 'source_field.id'], name='observation_source_field_id_same_run_fk', ondelete="RESTRICT"),
        Index('lookup_24', 'investigation_id', 'parse_run_id', unique=False),
        Index('lookup_25', 'investigation_id', 'source_record_id', unique=False),
        Index('lookup_26', 'investigation_id', 'source_field_id', unique=False),
        Index('lookup_27', 'investigation_id', 'evidence_id', unique=False),
        Index('lookup_28', 'investigation_id', 'unit_evidence_id', unique=False),
        Index('lookup_85', 'investigation_id', 'parse_run_id', 'source_record_id', unique=False),
        Index('lookup_86', 'investigation_id', 'parse_run_id', 'source_field_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(Observation.investigation_id == Investigation.id),
        foreign_keys=lambda: [Observation.investigation_id],
        viewonly=True, lazy="raise",
    )
    parse_run_ref: Mapped[ParseRun] = relationship(
        'ParseRun', primaryjoin=lambda: and_(Observation.investigation_id == ParseRun.investigation_id, Observation.parse_run_id == ParseRun.id),
        foreign_keys=lambda: [Observation.investigation_id, Observation.parse_run_id],
        viewonly=True, lazy="raise",
    )
    source_record_ref: Mapped[SourceRecord] = relationship(
        'SourceRecord', primaryjoin=lambda: and_(Observation.investigation_id == SourceRecord.investigation_id, Observation.source_record_id == SourceRecord.id),
        foreign_keys=lambda: [Observation.investigation_id, Observation.source_record_id],
        viewonly=True, lazy="raise",
    )
    source_field_ref: Mapped[SourceField] = relationship(
        'SourceField', primaryjoin=lambda: and_(Observation.investigation_id == SourceField.investigation_id, Observation.source_field_id == SourceField.id),
        foreign_keys=lambda: [Observation.investigation_id, Observation.source_field_id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(Observation.investigation_id == EvidenceReference.investigation_id, Observation.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [Observation.investigation_id, Observation.evidence_id],
        viewonly=True, lazy="raise",
    )
    unit_evidence_ref: Mapped[EvidenceReference | None] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(Observation.investigation_id == EvidenceReference.investigation_id, Observation.unit_evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [Observation.investigation_id, Observation.unit_evidence_id],
        viewonly=True, lazy="raise",
    )
    source_record_scoped_ref: Mapped[SourceRecord] = relationship(
        'SourceRecord', primaryjoin=lambda: and_(Observation.investigation_id == SourceRecord.investigation_id, Observation.parse_run_id == SourceRecord.parse_run_id, Observation.source_record_id == SourceRecord.id),
        foreign_keys=lambda: [Observation.investigation_id, Observation.parse_run_id, Observation.source_record_id],
        viewonly=True, lazy="raise",
    )
    source_field_scoped_ref: Mapped[SourceField] = relationship(
        'SourceField', primaryjoin=lambda: and_(Observation.investigation_id == SourceField.investigation_id, Observation.parse_run_id == SourceField.parse_run_id, Observation.source_field_id == SourceField.id),
        foreign_keys=lambda: [Observation.investigation_id, Observation.parse_run_id, Observation.source_field_id],
        viewonly=True, lazy="raise",
    )

class ScientificVariable(Base):
    __tablename__ = 'scientific_variable'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    variable_code: Mapped[str] = mapped_column('variable_code', Text(), nullable=False)
    definition_version: Mapped[int] = mapped_column('definition_version', Integer(), nullable=False)
    canonical_name: Mapped[str] = mapped_column('canonical_name', Text(), nullable=False)
    description: Mapped[str] = mapped_column('description', Text(), nullable=False)
    physical_quantity: Mapped[str | None] = mapped_column('physical_quantity', Text(), nullable=True)
    canonical_unit: Mapped[str | None] = mapped_column('canonical_unit', Text(), nullable=True)
    unit_basis: Mapped[str] = mapped_column('unit_basis', Text(), nullable=False)
    variable_category: Mapped[str] = mapped_column('variable_category', Text(), nullable=False)
    measurement_type: Mapped[str] = mapped_column('measurement_type', Text(), nullable=False)
    definition_status: Mapped[str] = mapped_column('definition_status', Text(), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_scientific_variable_01')),
        UniqueConstraint('investigation_id', 'variable_code', 'definition_version', name=conv('uq_scientific_variable_01')),
        CheckConstraint('definition_version > 0', name=conv('ck_scientific_variable_01')),
        CheckConstraint("variable_category IN ('measurement','identifier','instrument_setting','condition','context')", name=conv('ck_scientific_variable_02')),
        CheckConstraint("definition_status IN ('confirmed','partially_confirmed','unresolved','identifier_only','not_applicable')", name=conv('ck_scientific_variable_03')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='scientific_variable_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='scientific_variable_evidence_id_fk', ondelete="RESTRICT"),
        Index('lookup_30', 'investigation_id', 'evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(ScientificVariable.investigation_id == Investigation.id),
        foreign_keys=lambda: [ScientificVariable.investigation_id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(ScientificVariable.investigation_id == EvidenceReference.investigation_id, ScientificVariable.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [ScientificVariable.investigation_id, ScientificVariable.evidence_id],
        viewonly=True, lazy="raise",
    )

class SemanticAnnotation(Base):
    __tablename__ = 'semantic_annotation'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    observation_id: Mapped[UUID] = mapped_column('observation_id', PGUUID(as_uuid=True), nullable=False)
    variable_id: Mapped[UUID] = mapped_column('variable_id', PGUUID(as_uuid=True), nullable=False)
    interpretation_key: Mapped[str] = mapped_column('interpretation_key', Text(), nullable=False)
    revision: Mapped[int] = mapped_column('revision', Integer(), nullable=False)
    supersedes_id: Mapped[UUID | None] = mapped_column('supersedes_id', PGUUID(as_uuid=True), nullable=True)
    value_kind: Mapped[str] = mapped_column('value_kind', Text(), nullable=False)
    numeric_value: Mapped[Decimal | None] = mapped_column('numeric_value', Numeric(asdecimal=True), nullable=True)
    bound_value: Mapped[Decimal | None] = mapped_column('bound_value', Numeric(asdecimal=True), nullable=True)
    comparator: Mapped[str | None] = mapped_column('comparator', Text(), nullable=True)
    text_value: Mapped[str | None] = mapped_column('text_value', Text(), nullable=True)
    date_value: Mapped[date | None] = mapped_column('date_value', Date(), nullable=True)
    interpreted_unit: Mapped[str | None] = mapped_column('interpreted_unit', Text(), nullable=True)
    unit_status: Mapped[str] = mapped_column('unit_status', Text(), nullable=False)
    observed_phase: Mapped[str | None] = mapped_column('observed_phase', Text(), nullable=True)
    transformation_method: Mapped[str] = mapped_column('transformation_method', Text(), nullable=False)
    transformation_version: Mapped[str] = mapped_column('transformation_version', Text(), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column('parameters', JSONB(), nullable=False)
    uncertainty: Mapped[dict[str, Any]] = mapped_column('uncertainty', JSONB(), nullable=False)
    primary_evidence_id: Mapped[UUID] = mapped_column('primary_evidence_id', PGUUID(as_uuid=True), nullable=False)
    author_ref: Mapped[str] = mapped_column('author_ref', Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_semantic_annotation_01')),
        UniqueConstraint('investigation_id', 'observation_id', 'interpretation_key', 'revision', name=conv('uq_semantic_annotation_01')),
        UniqueConstraint('investigation_id', 'supersedes_id', name=conv('uq_semantic_annotation_02')),
        CheckConstraint('revision > 0', name=conv('ck_semantic_annotation_01')),
        CheckConstraint('supersedes_id IS NULL OR supersedes_id <> id', name=conv('ck_semantic_annotation_02')),
        CheckConstraint("value_kind IN ('numeric','censored','text','date','missing','unresolved','sequence')", name=conv('ck_semantic_annotation_03')),
        CheckConstraint("unit_status IN ('known','unknown','not_applicable')", name=conv('ck_semantic_annotation_04')),
        CheckConstraint("(unit_status = 'known') = (interpreted_unit IS NOT NULL)", name=conv('ck_semantic_annotation_05')),
        CheckConstraint("(value_kind = 'numeric') = (numeric_value IS NOT NULL)", name=conv('ck_semantic_annotation_06')),
        CheckConstraint("(value_kind = 'censored') = (bound_value IS NOT NULL)", name=conv('ck_semantic_annotation_07')),
        CheckConstraint("(value_kind = 'censored') = (comparator IS NOT NULL)", name=conv('ck_semantic_annotation_08')),
        CheckConstraint("comparator IS NULL OR comparator IN ('<','<=','>','>=')", name=conv('ck_semantic_annotation_09')),
        CheckConstraint("(value_kind = 'date') = (date_value IS NOT NULL)", name=conv('ck_semantic_annotation_10')),
        CheckConstraint("(value_kind IN ('text','missing','unresolved','sequence')) = (text_value IS NOT NULL)", name=conv('ck_semantic_annotation_11')),
        CheckConstraint("numeric_value IS NULL OR numeric_value::text NOT IN ('NaN','Infinity','-Infinity')", name=conv('ck_semantic_annotation_12')),
        CheckConstraint("bound_value IS NULL OR bound_value::text NOT IN ('NaN','Infinity','-Infinity')", name=conv('ck_semantic_annotation_13')),
        CheckConstraint("jsonb_typeof(parameters) = 'object'", name=conv('ck_semantic_annotation_14')),
        CheckConstraint("jsonb_typeof(uncertainty) = 'object'", name=conv('ck_semantic_annotation_15')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='semantic_annotation_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'observation_id'], ['observation.investigation_id', 'observation.id'], name='semantic_annotation_observation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'variable_id'], ['scientific_variable.investigation_id', 'scientific_variable.id'], name='semantic_annotation_variable_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'supersedes_id'], ['semantic_annotation.investigation_id', 'semantic_annotation.id'], name='semantic_annotation_supersedes_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'primary_evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='semantic_annotation_primary_evidence_id_fk', ondelete="RESTRICT"),
        Index('lookup_32', 'investigation_id', 'observation_id', unique=False),
        Index('lookup_33', 'investigation_id', 'variable_id', unique=False),
        Index('lookup_34', 'investigation_id', 'supersedes_id', unique=False),
        Index('lookup_35', 'investigation_id', 'primary_evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(SemanticAnnotation.investigation_id == Investigation.id),
        foreign_keys=lambda: [SemanticAnnotation.investigation_id],
        viewonly=True, lazy="raise",
    )
    observation_ref: Mapped[Observation] = relationship(
        'Observation', primaryjoin=lambda: and_(SemanticAnnotation.investigation_id == Observation.investigation_id, SemanticAnnotation.observation_id == Observation.id),
        foreign_keys=lambda: [SemanticAnnotation.investigation_id, SemanticAnnotation.observation_id],
        viewonly=True, lazy="raise",
    )
    variable_ref: Mapped[ScientificVariable] = relationship(
        'ScientificVariable', primaryjoin=lambda: and_(SemanticAnnotation.investigation_id == ScientificVariable.investigation_id, SemanticAnnotation.variable_id == ScientificVariable.id),
        foreign_keys=lambda: [SemanticAnnotation.investigation_id, SemanticAnnotation.variable_id],
        viewonly=True, lazy="raise",
    )
    supersedes_ref: Mapped[SemanticAnnotation | None] = relationship(
        'SemanticAnnotation', primaryjoin=lambda: and_(SemanticAnnotation.investigation_id == SemanticAnnotation.investigation_id, SemanticAnnotation.supersedes_id == SemanticAnnotation.id),
        foreign_keys=lambda: [SemanticAnnotation.investigation_id, SemanticAnnotation.supersedes_id],
        remote_side=lambda: [SemanticAnnotation.investigation_id, SemanticAnnotation.id],
        viewonly=True, lazy="raise",
    )
    primary_evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(SemanticAnnotation.investigation_id == EvidenceReference.investigation_id, SemanticAnnotation.primary_evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [SemanticAnnotation.investigation_id, SemanticAnnotation.primary_evidence_id],
        viewonly=True, lazy="raise",
    )

class AnnotationEvidence(Base):
    __tablename__ = 'annotation_evidence'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    annotation_id: Mapped[UUID] = mapped_column('annotation_id', PGUUID(as_uuid=True), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column('role', Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_annotation_evidence_01')),
        UniqueConstraint('investigation_id', 'annotation_id', 'evidence_id', 'role', name=conv('uq_annotation_evidence_01')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='annotation_evidence_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'annotation_id'], ['semantic_annotation.investigation_id', 'semantic_annotation.id'], name='annotation_evidence_annotation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='annotation_evidence_evidence_id_fk', ondelete="RESTRICT"),
        Index('lookup_37', 'investigation_id', 'annotation_id', unique=False),
        Index('lookup_38', 'investigation_id', 'evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(AnnotationEvidence.investigation_id == Investigation.id),
        foreign_keys=lambda: [AnnotationEvidence.investigation_id],
        viewonly=True, lazy="raise",
    )
    annotation_ref: Mapped[SemanticAnnotation] = relationship(
        'SemanticAnnotation', primaryjoin=lambda: and_(AnnotationEvidence.investigation_id == SemanticAnnotation.investigation_id, AnnotationEvidence.annotation_id == SemanticAnnotation.id),
        foreign_keys=lambda: [AnnotationEvidence.investigation_id, AnnotationEvidence.annotation_id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(AnnotationEvidence.investigation_id == EvidenceReference.investigation_id, AnnotationEvidence.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [AnnotationEvidence.investigation_id, AnnotationEvidence.evidence_id],
        viewonly=True, lazy="raise",
    )

class ExperimentalCondition(Base):
    __tablename__ = 'experimental_condition'

    segment_id: Mapped[UUID] = mapped_column('segment_id', PGUUID(as_uuid=True), nullable=False)
    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    experimental_test_id: Mapped[UUID] = mapped_column('experimental_test_id', PGUUID(as_uuid=True), nullable=False)
    segment_key: Mapped[str] = mapped_column('segment_key', Text(), nullable=False)
    revision: Mapped[int] = mapped_column('revision', Integer(), nullable=False)
    supersedes_id: Mapped[UUID | None] = mapped_column('supersedes_id', PGUUID(as_uuid=True), nullable=True)
    scope_description: Mapped[str] = mapped_column('scope_description', Text(), nullable=False)
    airflow_stability: Mapped[str] = mapped_column('airflow_stability', Text(), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    extension_metadata: Mapped[dict[str, Any]] = mapped_column('extension_metadata', JSONB(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_experimental_condition_01')),
        UniqueConstraint('investigation_id', 'experimental_test_id', 'segment_key', 'revision', name=conv('uq_experimental_condition_01')),
        UniqueConstraint('investigation_id', 'supersedes_id', name=conv('uq_experimental_condition_02')),
        CheckConstraint('revision > 0', name=conv('ck_experimental_condition_01')),
        CheckConstraint('supersedes_id IS NULL OR supersedes_id <> id', name=conv('ck_experimental_condition_02')),
        CheckConstraint("airflow_stability IN ('stable','transient','unknown','not_applicable')", name=conv('ck_experimental_condition_03')),
        CheckConstraint("extension_metadata = '{}'::jsonb", name=conv('ck_experimental_condition_04')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='experimental_condition_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'experimental_test_id'], ['experimental_test.investigation_id', 'experimental_test.id'], name='experimental_condition_experimental_test_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'supersedes_id'], ['experimental_condition.investigation_id', 'experimental_condition.id'], name='experimental_condition_supersedes_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='experimental_condition_evidence_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'segment_id'], ['condition_segment.investigation_id', 'condition_segment.id'], name='experimental_condition_segment_id_fk', ondelete="RESTRICT"),
        Index('lookup_40', 'investigation_id', 'experimental_test_id', unique=False),
        Index('lookup_41', 'investigation_id', 'supersedes_id', unique=False),
        Index('lookup_42', 'investigation_id', 'evidence_id', unique=False),
        Index('lookup_101', 'investigation_id', 'segment_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(ExperimentalCondition.investigation_id == Investigation.id),
        foreign_keys=lambda: [ExperimentalCondition.investigation_id],
        viewonly=True, lazy="raise",
    )
    experimental_test_ref: Mapped[ExperimentalTest] = relationship(
        'ExperimentalTest', primaryjoin=lambda: and_(ExperimentalCondition.investigation_id == ExperimentalTest.investigation_id, ExperimentalCondition.experimental_test_id == ExperimentalTest.id),
        foreign_keys=lambda: [ExperimentalCondition.investigation_id, ExperimentalCondition.experimental_test_id],
        viewonly=True, lazy="raise",
    )
    supersedes_ref: Mapped[ExperimentalCondition | None] = relationship(
        'ExperimentalCondition', primaryjoin=lambda: and_(ExperimentalCondition.investigation_id == ExperimentalCondition.investigation_id, ExperimentalCondition.supersedes_id == ExperimentalCondition.id),
        foreign_keys=lambda: [ExperimentalCondition.investigation_id, ExperimentalCondition.supersedes_id],
        remote_side=lambda: [ExperimentalCondition.investigation_id, ExperimentalCondition.id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(ExperimentalCondition.investigation_id == EvidenceReference.investigation_id, ExperimentalCondition.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [ExperimentalCondition.investigation_id, ExperimentalCondition.evidence_id],
        viewonly=True, lazy="raise",
    )
    segment_ref: Mapped[ConditionSegment] = relationship(
        'ConditionSegment', primaryjoin=lambda: and_(ExperimentalCondition.investigation_id == ConditionSegment.investigation_id, ExperimentalCondition.segment_id == ConditionSegment.id),
        foreign_keys=lambda: [ExperimentalCondition.investigation_id, ExperimentalCondition.segment_id],
        viewonly=True, lazy="raise",
    )

class DataQualityIssue(Base):
    __tablename__ = 'data_quality_issue'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    observation_id: Mapped[UUID | None] = mapped_column('observation_id', PGUUID(as_uuid=True), nullable=True)
    experimental_test_id: Mapped[UUID | None] = mapped_column('experimental_test_id', PGUUID(as_uuid=True), nullable=True)
    issue_type: Mapped[str] = mapped_column('issue_type', Text(), nullable=False)
    description: Mapped[str] = mapped_column('description', Text(), nullable=False)
    severity: Mapped[str] = mapped_column('severity', Text(), nullable=False)
    detector_method: Mapped[str] = mapped_column('detector_method', Text(), nullable=False)
    detector_version: Mapped[str] = mapped_column('detector_version', Text(), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_data_quality_issue_01')),
        CheckConstraint('num_nonnulls(observation_id,experimental_test_id) = 1', name=conv('ck_data_quality_issue_01')),
        CheckConstraint("severity IN ('info','review','blocking')", name=conv('ck_data_quality_issue_02')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='data_quality_issue_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'observation_id'], ['observation.investigation_id', 'observation.id'], name='data_quality_issue_observation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'experimental_test_id'], ['experimental_test.investigation_id', 'experimental_test.id'], name='data_quality_issue_experimental_test_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='data_quality_issue_evidence_id_fk', ondelete="RESTRICT"),
        Index('lookup_44', 'investigation_id', 'observation_id', unique=False),
        Index('lookup_45', 'investigation_id', 'experimental_test_id', unique=False),
        Index('lookup_46', 'investigation_id', 'evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(DataQualityIssue.investigation_id == Investigation.id),
        foreign_keys=lambda: [DataQualityIssue.investigation_id],
        viewonly=True, lazy="raise",
    )
    observation_ref: Mapped[Observation | None] = relationship(
        'Observation', primaryjoin=lambda: and_(DataQualityIssue.investigation_id == Observation.investigation_id, DataQualityIssue.observation_id == Observation.id),
        foreign_keys=lambda: [DataQualityIssue.investigation_id, DataQualityIssue.observation_id],
        viewonly=True, lazy="raise",
    )
    experimental_test_ref: Mapped[ExperimentalTest | None] = relationship(
        'ExperimentalTest', primaryjoin=lambda: and_(DataQualityIssue.investigation_id == ExperimentalTest.investigation_id, DataQualityIssue.experimental_test_id == ExperimentalTest.id),
        foreign_keys=lambda: [DataQualityIssue.investigation_id, DataQualityIssue.experimental_test_id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(DataQualityIssue.investigation_id == EvidenceReference.investigation_id, DataQualityIssue.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [DataQualityIssue.investigation_id, DataQualityIssue.evidence_id],
        viewonly=True, lazy="raise",
    )

class ReviewEvent(Base):
    __tablename__ = 'review_event'

    applicability_policy_version: Mapped[str | None] = mapped_column('applicability_policy_version', Text(), nullable=True)
    applicability_unresolved_count: Mapped[int | None] = mapped_column('applicability_unresolved_count', Integer(), nullable=True)
    metadata_revision_id: Mapped[UUID | None] = mapped_column('metadata_revision_id', PGUUID(as_uuid=True), nullable=True)
    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    annotation_id: Mapped[UUID | None] = mapped_column('annotation_id', PGUUID(as_uuid=True), nullable=True)
    variable_id: Mapped[UUID | None] = mapped_column('variable_id', PGUUID(as_uuid=True), nullable=True)
    condition_id: Mapped[UUID | None] = mapped_column('condition_id', PGUUID(as_uuid=True), nullable=True)
    test_link_id: Mapped[UUID | None] = mapped_column('test_link_id', PGUUID(as_uuid=True), nullable=True)
    test_relation_id: Mapped[UUID | None] = mapped_column('test_relation_id', PGUUID(as_uuid=True), nullable=True)
    issue_id: Mapped[UUID | None] = mapped_column('issue_id', PGUUID(as_uuid=True), nullable=True)
    result_id: Mapped[UUID | None] = mapped_column('result_id', PGUUID(as_uuid=True), nullable=True)
    revision: Mapped[int] = mapped_column('revision', Integer(), nullable=False)
    supersedes_id: Mapped[UUID | None] = mapped_column('supersedes_id', PGUUID(as_uuid=True), nullable=True)
    decision: Mapped[str] = mapped_column('decision', Text(), nullable=False)
    rationale: Mapped[str] = mapped_column('rationale', Text(), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    reviewer_ref: Mapped[str] = mapped_column('reviewer_ref', Text(), nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column('reviewed_at', DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_review_event_01')),
        UniqueConstraint('investigation_id', 'supersedes_id', name=conv('uq_review_event_01')),
        UniqueConstraint('investigation_id', 'annotation_id', 'revision', name=conv('uq_review_event_02')),
        UniqueConstraint('investigation_id', 'variable_id', 'revision', name=conv('uq_review_event_03')),
        UniqueConstraint('investigation_id', 'condition_id', 'revision', name=conv('uq_review_event_04')),
        UniqueConstraint('investigation_id', 'test_link_id', 'revision', name=conv('uq_review_event_05')),
        UniqueConstraint('investigation_id', 'test_relation_id', 'revision', name=conv('uq_review_event_06')),
        UniqueConstraint('investigation_id', 'issue_id', 'revision', name=conv('uq_review_event_07')),
        UniqueConstraint('investigation_id', 'result_id', 'revision', name=conv('uq_review_event_08')),
        CheckConstraint('num_nonnulls(metadata_revision_id,annotation_id,variable_id,condition_id,test_link_id,test_relation_id,issue_id,result_id) = 1', name=conv('ck_review_event_01')),
        CheckConstraint('revision > 0', name=conv('ck_review_event_02')),
        CheckConstraint('supersedes_id IS NULL OR supersedes_id <> id', name=conv('ck_review_event_03')),
        CheckConstraint("decision IN ('approved','rejected','revoked','needs_review','resolved','open')", name=conv('ck_review_event_04')),
        UniqueConstraint('investigation_id', 'metadata_revision_id', 'revision', name=conv('uq_review_event_09')),
        CheckConstraint("(applicability_policy_version IS NOT NULL) = (result_id IS NOT NULL AND decision = 'approved')", name=conv('ck_review_event_05')),
        CheckConstraint("(applicability_unresolved_count IS NOT NULL) = (result_id IS NOT NULL AND decision = 'approved')", name=conv('ck_review_event_06')),
        CheckConstraint("applicability_policy_version IS NULL OR applicability_policy_version = 'identity-issue-snapshot-v1'", name=conv('ck_review_event_07')),
        CheckConstraint('applicability_unresolved_count IS NULL OR applicability_unresolved_count = 0', name=conv('ck_review_event_08')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='review_event_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'annotation_id'], ['semantic_annotation.investigation_id', 'semantic_annotation.id'], name='review_event_annotation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'variable_id'], ['scientific_variable.investigation_id', 'scientific_variable.id'], name='review_event_variable_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'condition_id'], ['experimental_condition.investigation_id', 'experimental_condition.id'], name='review_event_condition_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'test_link_id'], ['test_source_record.investigation_id', 'test_source_record.id'], name='review_event_test_link_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'test_relation_id'], ['test_relationship.investigation_id', 'test_relationship.id'], name='review_event_test_relation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'issue_id'], ['data_quality_issue.investigation_id', 'data_quality_issue.id'], name='review_event_issue_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'result_id'], ['analytical_result.investigation_id', 'analytical_result.id'], name='review_event_result_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'supersedes_id'], ['review_event.investigation_id', 'review_event.id'], name='review_event_supersedes_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='review_event_evidence_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'metadata_revision_id'], ['metadata_revision.investigation_id', 'metadata_revision.id'], name='review_event_metadata_revision_id_fk', ondelete="RESTRICT"),
        Index('lookup_48', 'investigation_id', 'annotation_id', unique=False),
        Index('lookup_49', 'investigation_id', 'variable_id', unique=False),
        Index('lookup_50', 'investigation_id', 'condition_id', unique=False),
        Index('lookup_51', 'investigation_id', 'test_link_id', unique=False),
        Index('lookup_52', 'investigation_id', 'test_relation_id', unique=False),
        Index('lookup_53', 'investigation_id', 'issue_id', unique=False),
        Index('lookup_54', 'investigation_id', 'result_id', unique=False),
        Index('lookup_55', 'investigation_id', 'supersedes_id', unique=False),
        Index('lookup_56', 'investigation_id', 'evidence_id', unique=False),
        Index('lookup_115', 'investigation_id', 'metadata_revision_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(ReviewEvent.investigation_id == Investigation.id),
        foreign_keys=lambda: [ReviewEvent.investigation_id],
        viewonly=True, lazy="raise",
    )
    annotation_ref: Mapped[SemanticAnnotation | None] = relationship(
        'SemanticAnnotation', primaryjoin=lambda: and_(ReviewEvent.investigation_id == SemanticAnnotation.investigation_id, ReviewEvent.annotation_id == SemanticAnnotation.id),
        foreign_keys=lambda: [ReviewEvent.investigation_id, ReviewEvent.annotation_id],
        viewonly=True, lazy="raise",
    )
    variable_ref: Mapped[ScientificVariable | None] = relationship(
        'ScientificVariable', primaryjoin=lambda: and_(ReviewEvent.investigation_id == ScientificVariable.investigation_id, ReviewEvent.variable_id == ScientificVariable.id),
        foreign_keys=lambda: [ReviewEvent.investigation_id, ReviewEvent.variable_id],
        viewonly=True, lazy="raise",
    )
    condition_ref: Mapped[ExperimentalCondition | None] = relationship(
        'ExperimentalCondition', primaryjoin=lambda: and_(ReviewEvent.investigation_id == ExperimentalCondition.investigation_id, ReviewEvent.condition_id == ExperimentalCondition.id),
        foreign_keys=lambda: [ReviewEvent.investigation_id, ReviewEvent.condition_id],
        viewonly=True, lazy="raise",
    )
    test_link_ref: Mapped[TestSourceRecord | None] = relationship(
        'TestSourceRecord', primaryjoin=lambda: and_(ReviewEvent.investigation_id == TestSourceRecord.investigation_id, ReviewEvent.test_link_id == TestSourceRecord.id),
        foreign_keys=lambda: [ReviewEvent.investigation_id, ReviewEvent.test_link_id],
        viewonly=True, lazy="raise",
    )
    test_relation_ref: Mapped[TestRelationship | None] = relationship(
        'TestRelationship', primaryjoin=lambda: and_(ReviewEvent.investigation_id == TestRelationship.investigation_id, ReviewEvent.test_relation_id == TestRelationship.id),
        foreign_keys=lambda: [ReviewEvent.investigation_id, ReviewEvent.test_relation_id],
        viewonly=True, lazy="raise",
    )
    issue_ref: Mapped[DataQualityIssue | None] = relationship(
        'DataQualityIssue', primaryjoin=lambda: and_(ReviewEvent.investigation_id == DataQualityIssue.investigation_id, ReviewEvent.issue_id == DataQualityIssue.id),
        foreign_keys=lambda: [ReviewEvent.investigation_id, ReviewEvent.issue_id],
        viewonly=True, lazy="raise",
    )
    result_ref: Mapped[AnalyticalResult | None] = relationship(
        'AnalyticalResult', primaryjoin=lambda: and_(ReviewEvent.investigation_id == AnalyticalResult.investigation_id, ReviewEvent.result_id == AnalyticalResult.id),
        foreign_keys=lambda: [ReviewEvent.investigation_id, ReviewEvent.result_id],
        viewonly=True, lazy="raise",
    )
    supersedes_ref: Mapped[ReviewEvent | None] = relationship(
        'ReviewEvent', primaryjoin=lambda: and_(ReviewEvent.investigation_id == ReviewEvent.investigation_id, ReviewEvent.supersedes_id == ReviewEvent.id),
        foreign_keys=lambda: [ReviewEvent.investigation_id, ReviewEvent.supersedes_id],
        remote_side=lambda: [ReviewEvent.investigation_id, ReviewEvent.id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(ReviewEvent.investigation_id == EvidenceReference.investigation_id, ReviewEvent.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [ReviewEvent.investigation_id, ReviewEvent.evidence_id],
        viewonly=True, lazy="raise",
    )
    metadata_revision_ref: Mapped[MetadataRevision | None] = relationship(
        'MetadataRevision', primaryjoin=lambda: and_(ReviewEvent.investigation_id == MetadataRevision.investigation_id, ReviewEvent.metadata_revision_id == MetadataRevision.id),
        foreign_keys=lambda: [ReviewEvent.investigation_id, ReviewEvent.metadata_revision_id],
        viewonly=True, lazy="raise",
    )

class AnalysisProtocol(Base):
    __tablename__ = 'analysis_protocol'

    issue_policy: Mapped[str] = mapped_column('issue_policy', Text(), nullable=False)
    coverage_policy: Mapped[str] = mapped_column('coverage_policy', Text(), nullable=False)
    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    protocol_code: Mapped[str] = mapped_column('protocol_code', Text(), nullable=False)
    protocol_version: Mapped[str] = mapped_column('protocol_version', Text(), nullable=False)
    description: Mapped[str] = mapped_column('description', Text(), nullable=False)
    requirements_schema_version: Mapped[str] = mapped_column('requirements_schema_version', Text(), nullable=False)
    display_metadata: Mapped[dict[str, Any]] = mapped_column('display_metadata', JSONB(), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint("issue_policy = 'all_unresolved_review_or_blocking'", name=conv('ck_analysis_protocol_01')),
        CheckConstraint("coverage_policy = 'every_input_test_segment'", name=conv('ck_analysis_protocol_02')),
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_analysis_protocol_01')),
        UniqueConstraint('investigation_id', 'protocol_code', 'protocol_version', name=conv('uq_analysis_protocol_01')),
        CheckConstraint("display_metadata = '{}'::jsonb", name=conv('ck_analysis_protocol_03')),
        CheckConstraint("requirements_schema_version = 'relational-v1'", name=conv('ck_analysis_protocol_04')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='analysis_protocol_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='analysis_protocol_evidence_id_fk', ondelete="RESTRICT"),
        Index('lookup_58', 'investigation_id', 'evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(AnalysisProtocol.investigation_id == Investigation.id),
        foreign_keys=lambda: [AnalysisProtocol.investigation_id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(AnalysisProtocol.investigation_id == EvidenceReference.investigation_id, AnalysisProtocol.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [AnalysisProtocol.investigation_id, AnalysisProtocol.evidence_id],
        viewonly=True, lazy="raise",
    )

class AnalyticalEligibility(Base):
    __tablename__ = 'analytical_eligibility'

    segment_id: Mapped[UUID | None] = mapped_column('segment_id', PGUUID(as_uuid=True), nullable=True)
    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    protocol_id: Mapped[UUID] = mapped_column('protocol_id', PGUUID(as_uuid=True), nullable=False)
    observation_id: Mapped[UUID | None] = mapped_column('observation_id', PGUUID(as_uuid=True), nullable=True)
    experimental_test_id: Mapped[UUID | None] = mapped_column('experimental_test_id', PGUUID(as_uuid=True), nullable=True)
    revision: Mapped[int] = mapped_column('revision', Integer(), nullable=False)
    supersedes_id: Mapped[UUID | None] = mapped_column('supersedes_id', PGUUID(as_uuid=True), nullable=True)
    eligibility_status: Mapped[str] = mapped_column('eligibility_status', Text(), nullable=False)
    annotation_id: Mapped[UUID | None] = mapped_column('annotation_id', PGUUID(as_uuid=True), nullable=True)
    annotation_review_id: Mapped[UUID | None] = mapped_column('annotation_review_id', PGUUID(as_uuid=True), nullable=True)
    condition_id: Mapped[UUID | None] = mapped_column('condition_id', PGUUID(as_uuid=True), nullable=True)
    condition_review_id: Mapped[UUID | None] = mapped_column('condition_review_id', PGUUID(as_uuid=True), nullable=True)
    reason: Mapped[str] = mapped_column('reason', Text(), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    reviewer_ref: Mapped[str] = mapped_column('reviewer_ref', Text(), nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column('reviewed_at', DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_analytical_eligibility_01')),
        UniqueConstraint('investigation_id', 'protocol_id', 'observation_id', 'revision', name=conv('uq_analytical_eligibility_01')),
        UniqueConstraint('investigation_id', 'protocol_id', 'experimental_test_id', 'segment_id', 'revision', name=conv('uq_analytical_eligibility_02')),
        UniqueConstraint('investigation_id', 'supersedes_id', name=conv('uq_analytical_eligibility_03')),
        CheckConstraint('num_nonnulls(observation_id,experimental_test_id) = 1', name=conv('ck_analytical_eligibility_01')),
        CheckConstraint('revision > 0', name=conv('ck_analytical_eligibility_02')),
        CheckConstraint('supersedes_id IS NULL OR supersedes_id <> id', name=conv('ck_analytical_eligibility_03')),
        CheckConstraint("eligibility_status IN ('eligible','ineligible','needs_review','withdrawn')", name=conv('ck_analytical_eligibility_04')),
        CheckConstraint("eligibility_status <> 'eligible' OR observation_id IS NULL OR (annotation_id IS NOT NULL AND annotation_review_id IS NOT NULL)", name=conv('ck_analytical_eligibility_05')),
        CheckConstraint("eligibility_status <> 'eligible' OR experimental_test_id IS NULL OR (condition_id IS NOT NULL AND condition_review_id IS NOT NULL)", name=conv('ck_analytical_eligibility_06')),
        CheckConstraint('(annotation_id IS NULL) = (annotation_review_id IS NULL)', name=conv('ck_analytical_eligibility_07')),
        CheckConstraint('(condition_id IS NULL) = (condition_review_id IS NULL)', name=conv('ck_analytical_eligibility_08')),
        CheckConstraint('(experimental_test_id IS NOT NULL) = (segment_id IS NOT NULL)', name=conv('ck_analytical_eligibility_09')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='analytical_eligibility_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'protocol_id'], ['analysis_protocol.investigation_id', 'analysis_protocol.id'], name='analytical_eligibility_protocol_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'observation_id'], ['observation.investigation_id', 'observation.id'], name='analytical_eligibility_observation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'experimental_test_id'], ['experimental_test.investigation_id', 'experimental_test.id'], name='analytical_eligibility_experimental_test_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'supersedes_id'], ['analytical_eligibility.investigation_id', 'analytical_eligibility.id'], name='analytical_eligibility_supersedes_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'annotation_id'], ['semantic_annotation.investigation_id', 'semantic_annotation.id'], name='analytical_eligibility_annotation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'annotation_review_id'], ['review_event.investigation_id', 'review_event.id'], name='analytical_eligibility_annotation_review_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'condition_id'], ['experimental_condition.investigation_id', 'experimental_condition.id'], name='analytical_eligibility_condition_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'condition_review_id'], ['review_event.investigation_id', 'review_event.id'], name='analytical_eligibility_condition_review_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='analytical_eligibility_evidence_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'segment_id'], ['condition_segment.investigation_id', 'condition_segment.id'], name='analytical_eligibility_segment_id_fk', ondelete="RESTRICT"),
        Index('lookup_60', 'investigation_id', 'protocol_id', unique=False),
        Index('lookup_61', 'investigation_id', 'observation_id', unique=False),
        Index('lookup_62', 'investigation_id', 'experimental_test_id', unique=False),
        Index('lookup_63', 'investigation_id', 'supersedes_id', unique=False),
        Index('lookup_64', 'investigation_id', 'annotation_id', unique=False),
        Index('lookup_65', 'investigation_id', 'annotation_review_id', unique=False),
        Index('lookup_66', 'investigation_id', 'condition_id', unique=False),
        Index('lookup_67', 'investigation_id', 'condition_review_id', unique=False),
        Index('lookup_68', 'investigation_id', 'evidence_id', unique=False),
        Index('lookup_134', 'investigation_id', 'segment_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(AnalyticalEligibility.investigation_id == Investigation.id),
        foreign_keys=lambda: [AnalyticalEligibility.investigation_id],
        viewonly=True, lazy="raise",
    )
    protocol_ref: Mapped[AnalysisProtocol] = relationship(
        'AnalysisProtocol', primaryjoin=lambda: and_(AnalyticalEligibility.investigation_id == AnalysisProtocol.investigation_id, AnalyticalEligibility.protocol_id == AnalysisProtocol.id),
        foreign_keys=lambda: [AnalyticalEligibility.investigation_id, AnalyticalEligibility.protocol_id],
        viewonly=True, lazy="raise",
    )
    observation_ref: Mapped[Observation | None] = relationship(
        'Observation', primaryjoin=lambda: and_(AnalyticalEligibility.investigation_id == Observation.investigation_id, AnalyticalEligibility.observation_id == Observation.id),
        foreign_keys=lambda: [AnalyticalEligibility.investigation_id, AnalyticalEligibility.observation_id],
        viewonly=True, lazy="raise",
    )
    experimental_test_ref: Mapped[ExperimentalTest | None] = relationship(
        'ExperimentalTest', primaryjoin=lambda: and_(AnalyticalEligibility.investigation_id == ExperimentalTest.investigation_id, AnalyticalEligibility.experimental_test_id == ExperimentalTest.id),
        foreign_keys=lambda: [AnalyticalEligibility.investigation_id, AnalyticalEligibility.experimental_test_id],
        viewonly=True, lazy="raise",
    )
    supersedes_ref: Mapped[AnalyticalEligibility | None] = relationship(
        'AnalyticalEligibility', primaryjoin=lambda: and_(AnalyticalEligibility.investigation_id == AnalyticalEligibility.investigation_id, AnalyticalEligibility.supersedes_id == AnalyticalEligibility.id),
        foreign_keys=lambda: [AnalyticalEligibility.investigation_id, AnalyticalEligibility.supersedes_id],
        remote_side=lambda: [AnalyticalEligibility.investigation_id, AnalyticalEligibility.id],
        viewonly=True, lazy="raise",
    )
    annotation_ref: Mapped[SemanticAnnotation | None] = relationship(
        'SemanticAnnotation', primaryjoin=lambda: and_(AnalyticalEligibility.investigation_id == SemanticAnnotation.investigation_id, AnalyticalEligibility.annotation_id == SemanticAnnotation.id),
        foreign_keys=lambda: [AnalyticalEligibility.investigation_id, AnalyticalEligibility.annotation_id],
        viewonly=True, lazy="raise",
    )
    annotation_review_ref: Mapped[ReviewEvent | None] = relationship(
        'ReviewEvent', primaryjoin=lambda: and_(AnalyticalEligibility.investigation_id == ReviewEvent.investigation_id, AnalyticalEligibility.annotation_review_id == ReviewEvent.id),
        foreign_keys=lambda: [AnalyticalEligibility.investigation_id, AnalyticalEligibility.annotation_review_id],
        viewonly=True, lazy="raise",
    )
    condition_ref: Mapped[ExperimentalCondition | None] = relationship(
        'ExperimentalCondition', primaryjoin=lambda: and_(AnalyticalEligibility.investigation_id == ExperimentalCondition.investigation_id, AnalyticalEligibility.condition_id == ExperimentalCondition.id),
        foreign_keys=lambda: [AnalyticalEligibility.investigation_id, AnalyticalEligibility.condition_id],
        viewonly=True, lazy="raise",
    )
    condition_review_ref: Mapped[ReviewEvent | None] = relationship(
        'ReviewEvent', primaryjoin=lambda: and_(AnalyticalEligibility.investigation_id == ReviewEvent.investigation_id, AnalyticalEligibility.condition_review_id == ReviewEvent.id),
        foreign_keys=lambda: [AnalyticalEligibility.investigation_id, AnalyticalEligibility.condition_review_id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(AnalyticalEligibility.investigation_id == EvidenceReference.investigation_id, AnalyticalEligibility.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [AnalyticalEligibility.investigation_id, AnalyticalEligibility.evidence_id],
        viewonly=True, lazy="raise",
    )
    segment_ref: Mapped[ConditionSegment | None] = relationship(
        'ConditionSegment', primaryjoin=lambda: and_(AnalyticalEligibility.investigation_id == ConditionSegment.investigation_id, AnalyticalEligibility.segment_id == ConditionSegment.id),
        foreign_keys=lambda: [AnalyticalEligibility.investigation_id, AnalyticalEligibility.segment_id],
        viewonly=True, lazy="raise",
    )

class AnalyticalResult(Base):
    __tablename__ = 'analytical_result'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    protocol_id: Mapped[UUID] = mapped_column('protocol_id', PGUUID(as_uuid=True), nullable=False)
    method: Mapped[str] = mapped_column('method', Text(), nullable=False)
    method_version: Mapped[str] = mapped_column('method_version', Text(), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column('parameters', JSONB(), nullable=False)
    result_kind: Mapped[str] = mapped_column('result_kind', Text(), nullable=False)
    numeric_value: Mapped[Decimal | None] = mapped_column('numeric_value', Numeric(asdecimal=True), nullable=True)
    unit: Mapped[str | None] = mapped_column('unit', Text(), nullable=True)
    unit_status: Mapped[str] = mapped_column('unit_status', Text(), nullable=False)
    text_value: Mapped[str | None] = mapped_column('text_value', Text(), nullable=True)
    artifact_document_id: Mapped[UUID | None] = mapped_column('artifact_document_id', PGUUID(as_uuid=True), nullable=True)
    producer_ref: Mapped[str] = mapped_column('producer_ref', Text(), nullable=False)
    uncertainty: Mapped[dict[str, Any]] = mapped_column('uncertainty', JSONB(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_analytical_result_01')),
        CheckConstraint("result_kind IN ('numeric','text','artifact')", name=conv('ck_analytical_result_01')),
        CheckConstraint("unit_status IN ('known','unknown','not_applicable')", name=conv('ck_analytical_result_02')),
        CheckConstraint("(unit_status = 'known') = (unit IS NOT NULL)", name=conv('ck_analytical_result_03')),
        CheckConstraint("(result_kind = 'numeric') = (numeric_value IS NOT NULL)", name=conv('ck_analytical_result_04')),
        CheckConstraint("(result_kind = 'text') = (text_value IS NOT NULL)", name=conv('ck_analytical_result_05')),
        CheckConstraint("(result_kind = 'artifact') = (artifact_document_id IS NOT NULL)", name=conv('ck_analytical_result_06')),
        CheckConstraint("numeric_value IS NULL OR numeric_value::text NOT IN ('NaN','Infinity','-Infinity')", name=conv('ck_analytical_result_07')),
        CheckConstraint("jsonb_typeof(parameters) = 'object'", name=conv('ck_analytical_result_08')),
        CheckConstraint("jsonb_typeof(uncertainty) = 'object'", name=conv('ck_analytical_result_09')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='analytical_result_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'protocol_id'], ['analysis_protocol.investigation_id', 'analysis_protocol.id'], name='analytical_result_protocol_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'artifact_document_id'], ['source_document.investigation_id', 'source_document.id'], name='analytical_result_artifact_document_id_fk', ondelete="RESTRICT"),
        Index('lookup_70', 'investigation_id', 'protocol_id', unique=False),
        Index('lookup_71', 'investigation_id', 'artifact_document_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(AnalyticalResult.investigation_id == Investigation.id),
        foreign_keys=lambda: [AnalyticalResult.investigation_id],
        viewonly=True, lazy="raise",
    )
    protocol_ref: Mapped[AnalysisProtocol] = relationship(
        'AnalysisProtocol', primaryjoin=lambda: and_(AnalyticalResult.investigation_id == AnalysisProtocol.investigation_id, AnalyticalResult.protocol_id == AnalysisProtocol.id),
        foreign_keys=lambda: [AnalyticalResult.investigation_id, AnalyticalResult.protocol_id],
        viewonly=True, lazy="raise",
    )
    artifact_document_ref: Mapped[SourceDocument | None] = relationship(
        'SourceDocument', primaryjoin=lambda: and_(AnalyticalResult.investigation_id == SourceDocument.investigation_id, AnalyticalResult.artifact_document_id == SourceDocument.id),
        foreign_keys=lambda: [AnalyticalResult.investigation_id, AnalyticalResult.artifact_document_id],
        viewonly=True, lazy="raise",
    )

class ResultInput(Base):
    __tablename__ = 'result_input'

    segment_id: Mapped[UUID] = mapped_column('segment_id', PGUUID(as_uuid=True), nullable=False)
    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    result_id: Mapped[UUID] = mapped_column('result_id', PGUUID(as_uuid=True), nullable=False)
    annotation_id: Mapped[UUID] = mapped_column('annotation_id', PGUUID(as_uuid=True), nullable=False)
    eligibility_id: Mapped[UUID] = mapped_column('eligibility_id', PGUUID(as_uuid=True), nullable=False)
    test_link_id: Mapped[UUID] = mapped_column('test_link_id', PGUUID(as_uuid=True), nullable=False)
    test_link_review_id: Mapped[UUID] = mapped_column('test_link_review_id', PGUUID(as_uuid=True), nullable=False)
    input_role: Mapped[str] = mapped_column('input_role', Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_result_input_01')),
        UniqueConstraint('investigation_id', 'result_id', 'annotation_id', 'input_role', name=conv('uq_result_input_01')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='result_input_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'result_id'], ['analytical_result.investigation_id', 'analytical_result.id'], name='result_input_result_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'annotation_id'], ['semantic_annotation.investigation_id', 'semantic_annotation.id'], name='result_input_annotation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'eligibility_id'], ['analytical_eligibility.investigation_id', 'analytical_eligibility.id'], name='result_input_eligibility_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'test_link_id'], ['test_source_record.investigation_id', 'test_source_record.id'], name='result_input_test_link_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'test_link_review_id'], ['review_event.investigation_id', 'review_event.id'], name='result_input_test_link_review_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'segment_id'], ['condition_segment.investigation_id', 'condition_segment.id'], name='result_input_segment_id_fk', ondelete="RESTRICT"),
        Index('lookup_73', 'investigation_id', 'result_id', unique=False),
        Index('lookup_74', 'investigation_id', 'annotation_id', unique=False),
        Index('lookup_75', 'investigation_id', 'eligibility_id', unique=False),
        Index('lookup_76', 'investigation_id', 'test_link_id', unique=False),
        Index('lookup_77', 'investigation_id', 'test_link_review_id', unique=False),
        Index('lookup_102', 'investigation_id', 'segment_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(ResultInput.investigation_id == Investigation.id),
        foreign_keys=lambda: [ResultInput.investigation_id],
        viewonly=True, lazy="raise",
    )
    result_ref: Mapped[AnalyticalResult] = relationship(
        'AnalyticalResult', primaryjoin=lambda: and_(ResultInput.investigation_id == AnalyticalResult.investigation_id, ResultInput.result_id == AnalyticalResult.id),
        foreign_keys=lambda: [ResultInput.investigation_id, ResultInput.result_id],
        viewonly=True, lazy="raise",
    )
    annotation_ref: Mapped[SemanticAnnotation] = relationship(
        'SemanticAnnotation', primaryjoin=lambda: and_(ResultInput.investigation_id == SemanticAnnotation.investigation_id, ResultInput.annotation_id == SemanticAnnotation.id),
        foreign_keys=lambda: [ResultInput.investigation_id, ResultInput.annotation_id],
        viewonly=True, lazy="raise",
    )
    eligibility_ref: Mapped[AnalyticalEligibility] = relationship(
        'AnalyticalEligibility', primaryjoin=lambda: and_(ResultInput.investigation_id == AnalyticalEligibility.investigation_id, ResultInput.eligibility_id == AnalyticalEligibility.id),
        foreign_keys=lambda: [ResultInput.investigation_id, ResultInput.eligibility_id],
        viewonly=True, lazy="raise",
    )
    test_link_ref: Mapped[TestSourceRecord] = relationship(
        'TestSourceRecord', primaryjoin=lambda: and_(ResultInput.investigation_id == TestSourceRecord.investigation_id, ResultInput.test_link_id == TestSourceRecord.id),
        foreign_keys=lambda: [ResultInput.investigation_id, ResultInput.test_link_id],
        viewonly=True, lazy="raise",
    )
    test_link_review_ref: Mapped[ReviewEvent] = relationship(
        'ReviewEvent', primaryjoin=lambda: and_(ResultInput.investigation_id == ReviewEvent.investigation_id, ResultInput.test_link_review_id == ReviewEvent.id),
        foreign_keys=lambda: [ResultInput.investigation_id, ResultInput.test_link_review_id],
        viewonly=True, lazy="raise",
    )
    segment_ref: Mapped[ConditionSegment] = relationship(
        'ConditionSegment', primaryjoin=lambda: and_(ResultInput.investigation_id == ConditionSegment.investigation_id, ResultInput.segment_id == ConditionSegment.id),
        foreign_keys=lambda: [ResultInput.investigation_id, ResultInput.segment_id],
        viewonly=True, lazy="raise",
    )

class ResultCondition(Base):
    __tablename__ = 'result_condition'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    result_id: Mapped[UUID] = mapped_column('result_id', PGUUID(as_uuid=True), nullable=False)
    condition_id: Mapped[UUID] = mapped_column('condition_id', PGUUID(as_uuid=True), nullable=False)
    eligibility_id: Mapped[UUID] = mapped_column('eligibility_id', PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_result_condition_01')),
        UniqueConstraint('investigation_id', 'result_id', 'condition_id', name=conv('uq_result_condition_01')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='result_condition_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'result_id'], ['analytical_result.investigation_id', 'analytical_result.id'], name='result_condition_result_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'condition_id'], ['experimental_condition.investigation_id', 'experimental_condition.id'], name='result_condition_condition_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'eligibility_id'], ['analytical_eligibility.investigation_id', 'analytical_eligibility.id'], name='result_condition_eligibility_id_fk', ondelete="RESTRICT"),
        Index('lookup_79', 'investigation_id', 'result_id', unique=False),
        Index('lookup_80', 'investigation_id', 'condition_id', unique=False),
        Index('lookup_81', 'investigation_id', 'eligibility_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(ResultCondition.investigation_id == Investigation.id),
        foreign_keys=lambda: [ResultCondition.investigation_id],
        viewonly=True, lazy="raise",
    )
    result_ref: Mapped[AnalyticalResult] = relationship(
        'AnalyticalResult', primaryjoin=lambda: and_(ResultCondition.investigation_id == AnalyticalResult.investigation_id, ResultCondition.result_id == AnalyticalResult.id),
        foreign_keys=lambda: [ResultCondition.investigation_id, ResultCondition.result_id],
        viewonly=True, lazy="raise",
    )
    condition_ref: Mapped[ExperimentalCondition] = relationship(
        'ExperimentalCondition', primaryjoin=lambda: and_(ResultCondition.investigation_id == ExperimentalCondition.investigation_id, ResultCondition.condition_id == ExperimentalCondition.id),
        foreign_keys=lambda: [ResultCondition.investigation_id, ResultCondition.condition_id],
        viewonly=True, lazy="raise",
    )
    eligibility_ref: Mapped[AnalyticalEligibility] = relationship(
        'AnalyticalEligibility', primaryjoin=lambda: and_(ResultCondition.investigation_id == AnalyticalEligibility.investigation_id, ResultCondition.eligibility_id == AnalyticalEligibility.id),
        foreign_keys=lambda: [ResultCondition.investigation_id, ResultCondition.eligibility_id],
        viewonly=True, lazy="raise",
    )

class ResultEvidence(Base):
    __tablename__ = 'result_evidence'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    result_id: Mapped[UUID] = mapped_column('result_id', PGUUID(as_uuid=True), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column('role', Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_result_evidence_01')),
        UniqueConstraint('investigation_id', 'result_id', 'evidence_id', 'role', name=conv('uq_result_evidence_01')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='result_evidence_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'result_id'], ['analytical_result.investigation_id', 'analytical_result.id'], name='result_evidence_result_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='result_evidence_evidence_id_fk', ondelete="RESTRICT"),
        Index('lookup_83', 'investigation_id', 'result_id', unique=False),
        Index('lookup_84', 'investigation_id', 'evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(ResultEvidence.investigation_id == Investigation.id),
        foreign_keys=lambda: [ResultEvidence.investigation_id],
        viewonly=True, lazy="raise",
    )
    result_ref: Mapped[AnalyticalResult] = relationship(
        'AnalyticalResult', primaryjoin=lambda: and_(ResultEvidence.investigation_id == AnalyticalResult.investigation_id, ResultEvidence.result_id == AnalyticalResult.id),
        foreign_keys=lambda: [ResultEvidence.investigation_id, ResultEvidence.result_id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(ResultEvidence.investigation_id == EvidenceReference.investigation_id, ResultEvidence.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [ResultEvidence.investigation_id, ResultEvidence.evidence_id],
        viewonly=True, lazy="raise",
    )

class ConditionSegment(Base):
    __tablename__ = 'condition_segment'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    experimental_test_id: Mapped[UUID] = mapped_column('experimental_test_id', PGUUID(as_uuid=True), nullable=False)
    segment_key: Mapped[str] = mapped_column('segment_key', Text(), nullable=False)
    scope_status: Mapped[str] = mapped_column('scope_status', Text(), nullable=False)
    description: Mapped[str] = mapped_column('description', Text(), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_condition_segment_01')),
        CheckConstraint("scope_status IN ('documented','unknown')", name=conv('ck_condition_segment_01')),
        UniqueConstraint('investigation_id', 'experimental_test_id', 'segment_key', name=conv('uq_condition_segment_01')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='condition_segment_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'experimental_test_id'], ['experimental_test.investigation_id', 'experimental_test.id'], name='condition_segment_experimental_test_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='condition_segment_evidence_id_fk', ondelete="RESTRICT"),
        Index('lookup_88', 'investigation_id', 'experimental_test_id', unique=False),
        Index('lookup_89', 'investigation_id', 'evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(ConditionSegment.investigation_id == Investigation.id),
        foreign_keys=lambda: [ConditionSegment.investigation_id],
        viewonly=True, lazy="raise",
    )
    experimental_test_ref: Mapped[ExperimentalTest] = relationship(
        'ExperimentalTest', primaryjoin=lambda: and_(ConditionSegment.investigation_id == ExperimentalTest.investigation_id, ConditionSegment.experimental_test_id == ExperimentalTest.id),
        foreign_keys=lambda: [ConditionSegment.investigation_id, ConditionSegment.experimental_test_id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(ConditionSegment.investigation_id == EvidenceReference.investigation_id, ConditionSegment.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [ConditionSegment.investigation_id, ConditionSegment.evidence_id],
        viewonly=True, lazy="raise",
    )

class Instrument(Base):
    __tablename__ = 'instrument'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    instrument_code: Mapped[str] = mapped_column('instrument_code', Text(), nullable=False)
    description: Mapped[str] = mapped_column('description', Text(), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_instrument_01')),
        UniqueConstraint('investigation_id', 'instrument_code', name=conv('uq_instrument_01')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='instrument_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='instrument_evidence_id_fk', ondelete="RESTRICT"),
        Index('lookup_91', 'investigation_id', 'evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(Instrument.investigation_id == Investigation.id),
        foreign_keys=lambda: [Instrument.investigation_id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(Instrument.investigation_id == EvidenceReference.investigation_id, Instrument.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [Instrument.investigation_id, Instrument.evidence_id],
        viewonly=True, lazy="raise",
    )

class ConditionRole(Base):
    __tablename__ = 'condition_role'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    role_code: Mapped[str] = mapped_column('role_code', Text(), nullable=False)
    definition: Mapped[str] = mapped_column('definition', Text(), nullable=False)
    variable_category: Mapped[str] = mapped_column('variable_category', Text(), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_condition_role_01')),
        UniqueConstraint('investigation_id', 'role_code', name=conv('uq_condition_role_01')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='condition_role_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='condition_role_evidence_id_fk', ondelete="RESTRICT"),
        Index('lookup_93', 'investigation_id', 'evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(ConditionRole.investigation_id == Investigation.id),
        foreign_keys=lambda: [ConditionRole.investigation_id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(ConditionRole.investigation_id == EvidenceReference.investigation_id, ConditionRole.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [ConditionRole.investigation_id, ConditionRole.evidence_id],
        viewonly=True, lazy="raise",
    )

class ConditionComponent(Base):
    __tablename__ = 'condition_component'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    condition_id: Mapped[UUID] = mapped_column('condition_id', PGUUID(as_uuid=True), nullable=False)
    role_id: Mapped[UUID] = mapped_column('role_id', PGUUID(as_uuid=True), nullable=False)
    slot: Mapped[int] = mapped_column('slot', Integer(), nullable=False)
    instrument_id: Mapped[UUID | None] = mapped_column('instrument_id', PGUUID(as_uuid=True), nullable=True)
    instrument_status: Mapped[str] = mapped_column('instrument_status', Text(), nullable=False)
    variable_id: Mapped[UUID] = mapped_column('variable_id', PGUUID(as_uuid=True), nullable=False)
    annotation_id: Mapped[UUID | None] = mapped_column('annotation_id', PGUUID(as_uuid=True), nullable=True)
    value_status: Mapped[str] = mapped_column('value_status', Text(), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_condition_component_01')),
        CheckConstraint('slot > 0', name=conv('ck_condition_component_01')),
        CheckConstraint("value_status IN ('known','unknown','not_applicable')", name=conv('ck_condition_component_02')),
        CheckConstraint("(value_status = 'known') = (annotation_id IS NOT NULL)", name=conv('ck_condition_component_03')),
        CheckConstraint("instrument_status IN ('identified','unknown','not_applicable')", name=conv('ck_condition_component_04')),
        CheckConstraint("(instrument_status = 'identified') = (instrument_id IS NOT NULL)", name=conv('ck_condition_component_05')),
        UniqueConstraint('investigation_id', 'condition_id', 'role_id', 'slot', name=conv('uq_condition_component_01')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='condition_component_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'condition_id'], ['experimental_condition.investigation_id', 'experimental_condition.id'], name='condition_component_condition_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'role_id'], ['condition_role.investigation_id', 'condition_role.id'], name='condition_component_role_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'instrument_id'], ['instrument.investigation_id', 'instrument.id'], name='condition_component_instrument_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'variable_id'], ['scientific_variable.investigation_id', 'scientific_variable.id'], name='condition_component_variable_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'annotation_id'], ['semantic_annotation.investigation_id', 'semantic_annotation.id'], name='condition_component_annotation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='condition_component_evidence_id_fk', ondelete="RESTRICT"),
        Index('lookup_95', 'investigation_id', 'condition_id', unique=False),
        Index('lookup_96', 'investigation_id', 'role_id', unique=False),
        Index('lookup_97', 'investigation_id', 'instrument_id', unique=False),
        Index('lookup_98', 'investigation_id', 'variable_id', unique=False),
        Index('lookup_99', 'investigation_id', 'annotation_id', unique=False),
        Index('lookup_100', 'investigation_id', 'evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(ConditionComponent.investigation_id == Investigation.id),
        foreign_keys=lambda: [ConditionComponent.investigation_id],
        viewonly=True, lazy="raise",
    )
    condition_ref: Mapped[ExperimentalCondition] = relationship(
        'ExperimentalCondition', primaryjoin=lambda: and_(ConditionComponent.investigation_id == ExperimentalCondition.investigation_id, ConditionComponent.condition_id == ExperimentalCondition.id),
        foreign_keys=lambda: [ConditionComponent.investigation_id, ConditionComponent.condition_id],
        viewonly=True, lazy="raise",
    )
    role_ref: Mapped[ConditionRole] = relationship(
        'ConditionRole', primaryjoin=lambda: and_(ConditionComponent.investigation_id == ConditionRole.investigation_id, ConditionComponent.role_id == ConditionRole.id),
        foreign_keys=lambda: [ConditionComponent.investigation_id, ConditionComponent.role_id],
        viewonly=True, lazy="raise",
    )
    instrument_ref: Mapped[Instrument | None] = relationship(
        'Instrument', primaryjoin=lambda: and_(ConditionComponent.investigation_id == Instrument.investigation_id, ConditionComponent.instrument_id == Instrument.id),
        foreign_keys=lambda: [ConditionComponent.investigation_id, ConditionComponent.instrument_id],
        viewonly=True, lazy="raise",
    )
    variable_ref: Mapped[ScientificVariable] = relationship(
        'ScientificVariable', primaryjoin=lambda: and_(ConditionComponent.investigation_id == ScientificVariable.investigation_id, ConditionComponent.variable_id == ScientificVariable.id),
        foreign_keys=lambda: [ConditionComponent.investigation_id, ConditionComponent.variable_id],
        viewonly=True, lazy="raise",
    )
    annotation_ref: Mapped[SemanticAnnotation | None] = relationship(
        'SemanticAnnotation', primaryjoin=lambda: and_(ConditionComponent.investigation_id == SemanticAnnotation.investigation_id, ConditionComponent.annotation_id == SemanticAnnotation.id),
        foreign_keys=lambda: [ConditionComponent.investigation_id, ConditionComponent.annotation_id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(ConditionComponent.investigation_id == EvidenceReference.investigation_id, ConditionComponent.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [ConditionComponent.investigation_id, ConditionComponent.evidence_id],
        viewonly=True, lazy="raise",
    )

class ProtocolRequirement(Base):
    __tablename__ = 'protocol_requirement'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    protocol_id: Mapped[UUID] = mapped_column('protocol_id', PGUUID(as_uuid=True), nullable=False)
    requirement_key: Mapped[str] = mapped_column('requirement_key', Text(), nullable=False)
    target_kind: Mapped[str] = mapped_column('target_kind', Text(), nullable=False)
    variable_id: Mapped[UUID] = mapped_column('variable_id', PGUUID(as_uuid=True), nullable=False)
    role_id: Mapped[UUID | None] = mapped_column('role_id', PGUUID(as_uuid=True), nullable=True)
    phase: Mapped[str] = mapped_column('phase', Text(), nullable=False)
    min_count: Mapped[int] = mapped_column('min_count', Integer(), nullable=False)
    max_count: Mapped[int] = mapped_column('max_count', Integer(), nullable=False)
    value_policy: Mapped[str] = mapped_column('value_policy', Text(), nullable=False)
    stability_policy: Mapped[str] = mapped_column('stability_policy', Text(), nullable=False)
    instrument_policy: Mapped[str] = mapped_column('instrument_policy', Text(), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_protocol_requirement_01')),
        UniqueConstraint('investigation_id', 'protocol_id', 'requirement_key', name=conv('uq_protocol_requirement_01')),
        CheckConstraint("target_kind IN ('input','condition')", name=conv('ck_protocol_requirement_01')),
        CheckConstraint("(target_kind = 'condition') = (role_id IS NOT NULL)", name=conv('ck_protocol_requirement_02')),
        CheckConstraint('min_count > 0 AND max_count >= min_count', name=conv('ck_protocol_requirement_03')),
        CheckConstraint("value_policy IN ('numeric_only','numeric_or_censored','categorical')", name=conv('ck_protocol_requirement_04')),
        CheckConstraint("stability_policy IN ('stable_required','transient_allowed','not_applicable')", name=conv('ck_protocol_requirement_05')),
        CheckConstraint("instrument_policy IN ('identified_required','not_required')", name=conv('ck_protocol_requirement_06')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='protocol_requirement_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'protocol_id'], ['analysis_protocol.investigation_id', 'analysis_protocol.id'], name='protocol_requirement_protocol_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'variable_id'], ['scientific_variable.investigation_id', 'scientific_variable.id'], name='protocol_requirement_variable_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'role_id'], ['condition_role.investigation_id', 'condition_role.id'], name='protocol_requirement_role_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='protocol_requirement_evidence_id_fk', ondelete="RESTRICT"),
        Index('lookup_104', 'investigation_id', 'protocol_id', unique=False),
        Index('lookup_105', 'investigation_id', 'variable_id', unique=False),
        Index('lookup_106', 'investigation_id', 'role_id', unique=False),
        Index('lookup_107', 'investigation_id', 'evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(ProtocolRequirement.investigation_id == Investigation.id),
        foreign_keys=lambda: [ProtocolRequirement.investigation_id],
        viewonly=True, lazy="raise",
    )
    protocol_ref: Mapped[AnalysisProtocol] = relationship(
        'AnalysisProtocol', primaryjoin=lambda: and_(ProtocolRequirement.investigation_id == AnalysisProtocol.investigation_id, ProtocolRequirement.protocol_id == AnalysisProtocol.id),
        foreign_keys=lambda: [ProtocolRequirement.investigation_id, ProtocolRequirement.protocol_id],
        viewonly=True, lazy="raise",
    )
    variable_ref: Mapped[ScientificVariable] = relationship(
        'ScientificVariable', primaryjoin=lambda: and_(ProtocolRequirement.investigation_id == ScientificVariable.investigation_id, ProtocolRequirement.variable_id == ScientificVariable.id),
        foreign_keys=lambda: [ProtocolRequirement.investigation_id, ProtocolRequirement.variable_id],
        viewonly=True, lazy="raise",
    )
    role_ref: Mapped[ConditionRole | None] = relationship(
        'ConditionRole', primaryjoin=lambda: and_(ProtocolRequirement.investigation_id == ConditionRole.investigation_id, ProtocolRequirement.role_id == ConditionRole.id),
        foreign_keys=lambda: [ProtocolRequirement.investigation_id, ProtocolRequirement.role_id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(ProtocolRequirement.investigation_id == EvidenceReference.investigation_id, ProtocolRequirement.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [ProtocolRequirement.investigation_id, ProtocolRequirement.evidence_id],
        viewonly=True, lazy="raise",
    )

class ProtocolUnitRule(Base):
    __tablename__ = 'protocol_unit_rule'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    requirement_id: Mapped[UUID] = mapped_column('requirement_id', PGUUID(as_uuid=True), nullable=False)
    unit_text: Mapped[str] = mapped_column('unit_text', Text(), nullable=False)
    unit_basis: Mapped[str] = mapped_column('unit_basis', Text(), nullable=False)
    method: Mapped[str] = mapped_column('method', Text(), nullable=False)
    method_version: Mapped[str] = mapped_column('method_version', Text(), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_protocol_unit_rule_01')),
        UniqueConstraint('investigation_id', 'requirement_id', 'unit_text', 'unit_basis', 'method', 'method_version', name=conv('uq_protocol_unit_rule_01')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='protocol_unit_rule_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'requirement_id'], ['protocol_requirement.investigation_id', 'protocol_requirement.id'], name='protocol_unit_rule_requirement_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='protocol_unit_rule_evidence_id_fk', ondelete="RESTRICT"),
        Index('lookup_109', 'investigation_id', 'requirement_id', unique=False),
        Index('lookup_110', 'investigation_id', 'evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(ProtocolUnitRule.investigation_id == Investigation.id),
        foreign_keys=lambda: [ProtocolUnitRule.investigation_id],
        viewonly=True, lazy="raise",
    )
    requirement_ref: Mapped[ProtocolRequirement] = relationship(
        'ProtocolRequirement', primaryjoin=lambda: and_(ProtocolUnitRule.investigation_id == ProtocolRequirement.investigation_id, ProtocolUnitRule.requirement_id == ProtocolRequirement.id),
        foreign_keys=lambda: [ProtocolUnitRule.investigation_id, ProtocolUnitRule.requirement_id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(ProtocolUnitRule.investigation_id == EvidenceReference.investigation_id, ProtocolUnitRule.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [ProtocolUnitRule.investigation_id, ProtocolUnitRule.evidence_id],
        viewonly=True, lazy="raise",
    )

class MetadataRevision(Base):
    __tablename__ = 'metadata_revision'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    subject_kind: Mapped[str] = mapped_column('subject_kind', Text(), nullable=False)
    source_document_id: Mapped[UUID | None] = mapped_column('source_document_id', PGUUID(as_uuid=True), nullable=True)
    revision: Mapped[int] = mapped_column('revision', Integer(), nullable=False)
    supersedes_id: Mapped[UUID | None] = mapped_column('supersedes_id', PGUUID(as_uuid=True), nullable=True)
    name: Mapped[str | None] = mapped_column('name', Text(), nullable=True)
    description: Mapped[str | None] = mapped_column('description', Text(), nullable=True)
    agency: Mapped[str | None] = mapped_column('agency', Text(), nullable=True)
    doi: Mapped[str | None] = mapped_column('doi', Text(), nullable=True)
    repository_url: Mapped[str | None] = mapped_column('repository_url', Text(), nullable=True)
    source_version: Mapped[str | None] = mapped_column('source_version', Text(), nullable=True)
    evidence_id: Mapped[UUID] = mapped_column('evidence_id', PGUUID(as_uuid=True), nullable=False)
    reason: Mapped[str] = mapped_column('reason', Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_metadata_revision_01')),
        CheckConstraint("subject_kind IN ('investigation','source_document')", name=conv('ck_metadata_revision_01')),
        CheckConstraint("(subject_kind = 'source_document') = (source_document_id IS NOT NULL)", name=conv('ck_metadata_revision_02')),
        CheckConstraint('revision > 0', name=conv('ck_metadata_revision_03')),
        UniqueConstraint('investigation_id', 'source_document_id', 'revision', name=conv('uq_metadata_revision_01')),
        UniqueConstraint('investigation_id', 'supersedes_id', name=conv('uq_metadata_revision_02')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='metadata_revision_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'source_document_id'], ['source_document.investigation_id', 'source_document.id'], name='metadata_revision_source_document_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'supersedes_id'], ['metadata_revision.investigation_id', 'metadata_revision.id'], name='metadata_revision_supersedes_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'evidence_id'], ['evidence_reference.investigation_id', 'evidence_reference.id'], name='metadata_revision_evidence_id_fk', ondelete="RESTRICT"),
        Index('metadata_investigation_revision', 'investigation_id', 'revision', unique=True, postgresql_where=text("subject_kind = 'investigation'")),
        Index('lookup_112', 'investigation_id', 'source_document_id', unique=False),
        Index('lookup_113', 'investigation_id', 'supersedes_id', unique=False),
        Index('lookup_114', 'investigation_id', 'evidence_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(MetadataRevision.investigation_id == Investigation.id),
        foreign_keys=lambda: [MetadataRevision.investigation_id],
        viewonly=True, lazy="raise",
    )
    source_document_ref: Mapped[SourceDocument | None] = relationship(
        'SourceDocument', primaryjoin=lambda: and_(MetadataRevision.investigation_id == SourceDocument.investigation_id, MetadataRevision.source_document_id == SourceDocument.id),
        foreign_keys=lambda: [MetadataRevision.investigation_id, MetadataRevision.source_document_id],
        viewonly=True, lazy="raise",
    )
    supersedes_ref: Mapped[MetadataRevision | None] = relationship(
        'MetadataRevision', primaryjoin=lambda: and_(MetadataRevision.investigation_id == MetadataRevision.investigation_id, MetadataRevision.supersedes_id == MetadataRevision.id),
        foreign_keys=lambda: [MetadataRevision.investigation_id, MetadataRevision.supersedes_id],
        remote_side=lambda: [MetadataRevision.investigation_id, MetadataRevision.id],
        viewonly=True, lazy="raise",
    )
    evidence_ref: Mapped[EvidenceReference] = relationship(
        'EvidenceReference', primaryjoin=lambda: and_(MetadataRevision.investigation_id == EvidenceReference.investigation_id, MetadataRevision.evidence_id == EvidenceReference.id),
        foreign_keys=lambda: [MetadataRevision.investigation_id, MetadataRevision.evidence_id],
        viewonly=True, lazy="raise",
    )

class AggregateSeal(Base):
    __tablename__ = 'aggregate_seal'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    parse_run_id: Mapped[UUID | None] = mapped_column('parse_run_id', PGUUID(as_uuid=True), nullable=True)
    annotation_id: Mapped[UUID | None] = mapped_column('annotation_id', PGUUID(as_uuid=True), nullable=True)
    condition_id: Mapped[UUID | None] = mapped_column('condition_id', PGUUID(as_uuid=True), nullable=True)
    protocol_id: Mapped[UUID | None] = mapped_column('protocol_id', PGUUID(as_uuid=True), nullable=True)
    result_id: Mapped[UUID | None] = mapped_column('result_id', PGUUID(as_uuid=True), nullable=True)
    review_id: Mapped[UUID | None] = mapped_column('review_id', PGUUID(as_uuid=True), nullable=True)
    seal_version: Mapped[str] = mapped_column('seal_version', Text(), nullable=False)
    member_counts: Mapped[dict[str, Any]] = mapped_column('member_counts', JSONB(), nullable=False)
    member_digest: Mapped[str] = mapped_column('member_digest', Text(), nullable=False)
    sealed_by: Mapped[str] = mapped_column('sealed_by', Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_aggregate_seal_01')),
        CheckConstraint('num_nonnulls(parse_run_id,annotation_id,condition_id,protocol_id,result_id,review_id) = 1', name=conv('ck_aggregate_seal_01')),
        CheckConstraint("seal_version = 'canonical-json-v2'", name=conv('ck_aggregate_seal_02')),
        CheckConstraint("jsonb_typeof(member_counts) = 'object'", name=conv('ck_aggregate_seal_03')),
        CheckConstraint("member_digest ~ '^[0-9a-f]{64}$'", name=conv('ck_aggregate_seal_04')),
        UniqueConstraint('investigation_id', 'parse_run_id', name=conv('uq_aggregate_seal_01')),
        UniqueConstraint('investigation_id', 'annotation_id', name=conv('uq_aggregate_seal_02')),
        UniqueConstraint('investigation_id', 'condition_id', name=conv('uq_aggregate_seal_03')),
        UniqueConstraint('investigation_id', 'protocol_id', name=conv('uq_aggregate_seal_04')),
        UniqueConstraint('investigation_id', 'result_id', name=conv('uq_aggregate_seal_05')),
        UniqueConstraint('investigation_id', 'review_id', name=conv('uq_aggregate_seal_06')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='aggregate_seal_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'parse_run_id'], ['parse_run.investigation_id', 'parse_run.id'], name='aggregate_seal_parse_run_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'annotation_id'], ['semantic_annotation.investigation_id', 'semantic_annotation.id'], name='aggregate_seal_annotation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'condition_id'], ['experimental_condition.investigation_id', 'experimental_condition.id'], name='aggregate_seal_condition_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'protocol_id'], ['analysis_protocol.investigation_id', 'analysis_protocol.id'], name='aggregate_seal_protocol_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'result_id'], ['analytical_result.investigation_id', 'analytical_result.id'], name='aggregate_seal_result_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'review_id'], ['review_event.investigation_id', 'review_event.id'], name='aggregate_seal_review_id_fk', ondelete="RESTRICT"),
        Index('lookup_117', 'investigation_id', 'parse_run_id', unique=False),
        Index('lookup_118', 'investigation_id', 'annotation_id', unique=False),
        Index('lookup_119', 'investigation_id', 'condition_id', unique=False),
        Index('lookup_120', 'investigation_id', 'protocol_id', unique=False),
        Index('lookup_121', 'investigation_id', 'result_id', unique=False),
        Index('lookup_122', 'investigation_id', 'review_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(AggregateSeal.investigation_id == Investigation.id),
        foreign_keys=lambda: [AggregateSeal.investigation_id],
        viewonly=True, lazy="raise",
    )
    parse_run_ref: Mapped[ParseRun | None] = relationship(
        'ParseRun', primaryjoin=lambda: and_(AggregateSeal.investigation_id == ParseRun.investigation_id, AggregateSeal.parse_run_id == ParseRun.id),
        foreign_keys=lambda: [AggregateSeal.investigation_id, AggregateSeal.parse_run_id],
        viewonly=True, lazy="raise",
    )
    annotation_ref: Mapped[SemanticAnnotation | None] = relationship(
        'SemanticAnnotation', primaryjoin=lambda: and_(AggregateSeal.investigation_id == SemanticAnnotation.investigation_id, AggregateSeal.annotation_id == SemanticAnnotation.id),
        foreign_keys=lambda: [AggregateSeal.investigation_id, AggregateSeal.annotation_id],
        viewonly=True, lazy="raise",
    )
    condition_ref: Mapped[ExperimentalCondition | None] = relationship(
        'ExperimentalCondition', primaryjoin=lambda: and_(AggregateSeal.investigation_id == ExperimentalCondition.investigation_id, AggregateSeal.condition_id == ExperimentalCondition.id),
        foreign_keys=lambda: [AggregateSeal.investigation_id, AggregateSeal.condition_id],
        viewonly=True, lazy="raise",
    )
    protocol_ref: Mapped[AnalysisProtocol | None] = relationship(
        'AnalysisProtocol', primaryjoin=lambda: and_(AggregateSeal.investigation_id == AnalysisProtocol.investigation_id, AggregateSeal.protocol_id == AnalysisProtocol.id),
        foreign_keys=lambda: [AggregateSeal.investigation_id, AggregateSeal.protocol_id],
        viewonly=True, lazy="raise",
    )
    result_ref: Mapped[AnalyticalResult | None] = relationship(
        'AnalyticalResult', primaryjoin=lambda: and_(AggregateSeal.investigation_id == AnalyticalResult.investigation_id, AggregateSeal.result_id == AnalyticalResult.id),
        foreign_keys=lambda: [AggregateSeal.investigation_id, AggregateSeal.result_id],
        viewonly=True, lazy="raise",
    )
    review_ref: Mapped[ReviewEvent | None] = relationship(
        'ReviewEvent', primaryjoin=lambda: and_(AggregateSeal.investigation_id == ReviewEvent.investigation_id, AggregateSeal.review_id == ReviewEvent.id),
        foreign_keys=lambda: [AggregateSeal.investigation_id, AggregateSeal.review_id],
        viewonly=True, lazy="raise",
    )

class ApprovalDependency(Base):
    __tablename__ = 'approval_dependency'

    entry_kind: Mapped[str] = mapped_column('entry_kind', Text(), nullable=False)
    snapshot_observation_id: Mapped[UUID | None] = mapped_column('snapshot_observation_id', PGUUID(as_uuid=True), nullable=True)
    snapshot_link_id: Mapped[UUID | None] = mapped_column('snapshot_link_id', PGUUID(as_uuid=True), nullable=True)
    snapshot_issue_id: Mapped[UUID | None] = mapped_column('snapshot_issue_id', PGUUID(as_uuid=True), nullable=True)
    snapshot_review_id: Mapped[UUID | None] = mapped_column('snapshot_review_id', PGUUID(as_uuid=True), nullable=True)
    snapshot_review_seal_id: Mapped[UUID | None] = mapped_column('snapshot_review_seal_id', PGUUID(as_uuid=True), nullable=True)
    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    owner_review_id: Mapped[UUID] = mapped_column('owner_review_id', PGUUID(as_uuid=True), nullable=False)
    dependency_review_id: Mapped[UUID | None] = mapped_column('dependency_review_id', PGUUID(as_uuid=True), nullable=True)
    dependency_eligibility_id: Mapped[UUID | None] = mapped_column('dependency_eligibility_id', PGUUID(as_uuid=True), nullable=True)
    dependency_seal_id: Mapped[UUID | None] = mapped_column('dependency_seal_id', PGUUID(as_uuid=True), nullable=True)
    role: Mapped[str] = mapped_column('role', Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_approval_dependency_01')),
        CheckConstraint("(entry_kind = 'decision' AND num_nonnulls(dependency_review_id,dependency_eligibility_id,dependency_seal_id) = 1 AND num_nonnulls(snapshot_observation_id,snapshot_link_id,snapshot_issue_id,snapshot_review_id,snapshot_review_seal_id) = 0 AND role NOT IN ('scope_observation','scope_link','scope_issue')) OR (entry_kind = 'scope_observation' AND num_nonnulls(dependency_review_id,dependency_eligibility_id,dependency_seal_id) = 0 AND snapshot_observation_id IS NOT NULL AND num_nonnulls(snapshot_link_id,snapshot_issue_id,snapshot_review_id,snapshot_review_seal_id) = 0 AND role = 'scope_observation') OR (entry_kind = 'scope_link' AND num_nonnulls(dependency_review_id,dependency_eligibility_id,dependency_seal_id) = 0 AND snapshot_observation_id IS NOT NULL AND snapshot_link_id IS NOT NULL AND snapshot_issue_id IS NULL AND role = 'scope_link') OR (entry_kind = 'scope_issue' AND num_nonnulls(dependency_review_id,dependency_eligibility_id,dependency_seal_id) = 0 AND snapshot_observation_id IS NOT NULL AND snapshot_issue_id IS NOT NULL AND snapshot_link_id IS NULL AND role = 'scope_issue')", name=conv('ck_approval_dependency_01')),
        CheckConstraint('dependency_review_id IS NULL OR dependency_review_id <> owner_review_id', name=conv('ck_approval_dependency_02')),
        UniqueConstraint('investigation_id', 'owner_review_id', 'dependency_review_id', 'role', name=conv('uq_approval_dependency_01')),
        UniqueConstraint('investigation_id', 'owner_review_id', 'dependency_eligibility_id', 'role', name=conv('uq_approval_dependency_02')),
        UniqueConstraint('investigation_id', 'owner_review_id', 'dependency_seal_id', 'role', name=conv('uq_approval_dependency_03')),
        CheckConstraint("entry_kind IN ('decision','scope_observation','scope_link','scope_issue')", name=conv('ck_approval_dependency_03')),
        CheckConstraint('snapshot_review_seal_id IS NULL OR snapshot_review_id IS NOT NULL', name=conv('ck_approval_dependency_04')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='approval_dependency_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'owner_review_id'], ['review_event.investigation_id', 'review_event.id'], name='approval_dependency_owner_review_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'dependency_review_id'], ['review_event.investigation_id', 'review_event.id'], name='approval_dependency_dependency_review_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'dependency_eligibility_id'], ['analytical_eligibility.investigation_id', 'analytical_eligibility.id'], name='approval_dependency_dependency_eligibility_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'dependency_seal_id'], ['aggregate_seal.investigation_id', 'aggregate_seal.id'], name='approval_dependency_dependency_seal_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'snapshot_observation_id'], ['observation.investigation_id', 'observation.id'], name='ad_snapshot_observation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'snapshot_link_id'], ['test_source_record.investigation_id', 'test_source_record.id'], name='ad_snapshot_link_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'snapshot_issue_id'], ['data_quality_issue.investigation_id', 'data_quality_issue.id'], name='ad_snapshot_issue_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'snapshot_review_id'], ['review_event.investigation_id', 'review_event.id'], name='ad_snapshot_review_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'snapshot_review_seal_id'], ['aggregate_seal.investigation_id', 'aggregate_seal.id'], name='ad_snapshot_review_seal_id_fk', ondelete="RESTRICT"),
        Index('lookup_124', 'investigation_id', 'owner_review_id', unique=False),
        Index('lookup_125', 'investigation_id', 'dependency_review_id', unique=False),
        Index('lookup_126', 'investigation_id', 'dependency_eligibility_id', unique=False),
        Index('lookup_127', 'investigation_id', 'dependency_seal_id', unique=False),
        Index('ad_scope_observation_once', 'investigation_id', 'owner_review_id', 'snapshot_observation_id', unique=True, postgresql_where=text("entry_kind = 'scope_observation'")),
        Index('ad_scope_link_once', 'investigation_id', 'owner_review_id', 'snapshot_observation_id', 'snapshot_link_id', unique=True, postgresql_where=text("entry_kind = 'scope_link'")),
        Index('ad_scope_issue_once', 'investigation_id', 'owner_review_id', 'snapshot_observation_id', 'snapshot_issue_id', unique=True, postgresql_where=text("entry_kind = 'scope_issue'")),
        Index('lookup_135', 'investigation_id', 'snapshot_observation_id', unique=False),
        Index('lookup_136', 'investigation_id', 'snapshot_link_id', unique=False),
        Index('lookup_137', 'investigation_id', 'snapshot_issue_id', unique=False),
        Index('lookup_138', 'investigation_id', 'snapshot_review_id', unique=False),
        Index('lookup_139', 'investigation_id', 'snapshot_review_seal_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(ApprovalDependency.investigation_id == Investigation.id),
        foreign_keys=lambda: [ApprovalDependency.investigation_id],
        viewonly=True, lazy="raise",
    )
    owner_review_ref: Mapped[ReviewEvent] = relationship(
        'ReviewEvent', primaryjoin=lambda: and_(ApprovalDependency.investigation_id == ReviewEvent.investigation_id, ApprovalDependency.owner_review_id == ReviewEvent.id),
        foreign_keys=lambda: [ApprovalDependency.investigation_id, ApprovalDependency.owner_review_id],
        viewonly=True, lazy="raise",
    )
    dependency_review_ref: Mapped[ReviewEvent | None] = relationship(
        'ReviewEvent', primaryjoin=lambda: and_(ApprovalDependency.investigation_id == ReviewEvent.investigation_id, ApprovalDependency.dependency_review_id == ReviewEvent.id),
        foreign_keys=lambda: [ApprovalDependency.investigation_id, ApprovalDependency.dependency_review_id],
        viewonly=True, lazy="raise",
    )
    dependency_eligibility_ref: Mapped[AnalyticalEligibility | None] = relationship(
        'AnalyticalEligibility', primaryjoin=lambda: and_(ApprovalDependency.investigation_id == AnalyticalEligibility.investigation_id, ApprovalDependency.dependency_eligibility_id == AnalyticalEligibility.id),
        foreign_keys=lambda: [ApprovalDependency.investigation_id, ApprovalDependency.dependency_eligibility_id],
        viewonly=True, lazy="raise",
    )
    dependency_seal_ref: Mapped[AggregateSeal | None] = relationship(
        'AggregateSeal', primaryjoin=lambda: and_(ApprovalDependency.investigation_id == AggregateSeal.investigation_id, ApprovalDependency.dependency_seal_id == AggregateSeal.id),
        foreign_keys=lambda: [ApprovalDependency.investigation_id, ApprovalDependency.dependency_seal_id],
        viewonly=True, lazy="raise",
    )
    snapshot_observation_ref: Mapped[Observation | None] = relationship(
        'Observation', primaryjoin=lambda: and_(ApprovalDependency.investigation_id == Observation.investigation_id, ApprovalDependency.snapshot_observation_id == Observation.id),
        foreign_keys=lambda: [ApprovalDependency.investigation_id, ApprovalDependency.snapshot_observation_id],
        viewonly=True, lazy="raise",
    )
    snapshot_link_ref: Mapped[TestSourceRecord | None] = relationship(
        'TestSourceRecord', primaryjoin=lambda: and_(ApprovalDependency.investigation_id == TestSourceRecord.investigation_id, ApprovalDependency.snapshot_link_id == TestSourceRecord.id),
        foreign_keys=lambda: [ApprovalDependency.investigation_id, ApprovalDependency.snapshot_link_id],
        viewonly=True, lazy="raise",
    )
    snapshot_issue_ref: Mapped[DataQualityIssue | None] = relationship(
        'DataQualityIssue', primaryjoin=lambda: and_(ApprovalDependency.investigation_id == DataQualityIssue.investigation_id, ApprovalDependency.snapshot_issue_id == DataQualityIssue.id),
        foreign_keys=lambda: [ApprovalDependency.investigation_id, ApprovalDependency.snapshot_issue_id],
        viewonly=True, lazy="raise",
    )
    snapshot_review_ref: Mapped[ReviewEvent | None] = relationship(
        'ReviewEvent', primaryjoin=lambda: and_(ApprovalDependency.investigation_id == ReviewEvent.investigation_id, ApprovalDependency.snapshot_review_id == ReviewEvent.id),
        foreign_keys=lambda: [ApprovalDependency.investigation_id, ApprovalDependency.snapshot_review_id],
        viewonly=True, lazy="raise",
    )
    snapshot_review_seal_ref: Mapped[AggregateSeal | None] = relationship(
        'AggregateSeal', primaryjoin=lambda: and_(ApprovalDependency.investigation_id == AggregateSeal.investigation_id, ApprovalDependency.snapshot_review_seal_id == AggregateSeal.id),
        foreign_keys=lambda: [ApprovalDependency.investigation_id, ApprovalDependency.snapshot_review_seal_id],
        viewonly=True, lazy="raise",
    )

class PublicationEvent(Base):
    __tablename__ = 'publication_event'

    investigation_id: Mapped[UUID] = mapped_column('investigation_id', PGUUID(as_uuid=True), nullable=False)
    id: Mapped[UUID] = mapped_column('id', PGUUID(as_uuid=True), nullable=False)
    result_id: Mapped[UUID] = mapped_column('result_id', PGUUID(as_uuid=True), nullable=False)
    result_seal_id: Mapped[UUID] = mapped_column('result_seal_id', PGUUID(as_uuid=True), nullable=False)
    result_review_id: Mapped[UUID] = mapped_column('result_review_id', PGUUID(as_uuid=True), nullable=False)
    review_seal_id: Mapped[UUID] = mapped_column('review_seal_id', PGUUID(as_uuid=True), nullable=False)
    revision: Mapped[int] = mapped_column('revision', Integer(), nullable=False)
    supersedes_id: Mapped[UUID | None] = mapped_column('supersedes_id', PGUUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column('action', Text(), nullable=False)
    actor_ref: Mapped[str] = mapped_column('actor_ref', Text(), nullable=False)
    reason: Mapped[str] = mapped_column('reason', Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('investigation_id', 'id', name=conv('pk_publication_event_01')),
        CheckConstraint('revision > 0', name=conv('ck_publication_event_01')),
        CheckConstraint("action IN ('publish','revoke')", name=conv('ck_publication_event_02')),
        UniqueConstraint('investigation_id', 'result_id', 'revision', name=conv('uq_publication_event_01')),
        UniqueConstraint('investigation_id', 'supersedes_id', name=conv('uq_publication_event_02')),
        ForeignKeyConstraint(['investigation_id'], ['investigation.id'], name='publication_event_investigation_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'result_id'], ['analytical_result.investigation_id', 'analytical_result.id'], name='publication_event_result_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'result_seal_id'], ['aggregate_seal.investigation_id', 'aggregate_seal.id'], name='publication_event_result_seal_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'result_review_id'], ['review_event.investigation_id', 'review_event.id'], name='publication_event_result_review_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'review_seal_id'], ['aggregate_seal.investigation_id', 'aggregate_seal.id'], name='publication_event_review_seal_id_fk', ondelete="RESTRICT"),
        ForeignKeyConstraint(['investigation_id', 'supersedes_id'], ['publication_event.investigation_id', 'publication_event.id'], name='publication_event_supersedes_id_fk', ondelete="RESTRICT"),
        Index('lookup_129', 'investigation_id', 'result_id', unique=False),
        Index('lookup_130', 'investigation_id', 'result_seal_id', unique=False),
        Index('lookup_131', 'investigation_id', 'result_review_id', unique=False),
        Index('lookup_132', 'investigation_id', 'review_seal_id', unique=False),
        Index('lookup_133', 'investigation_id', 'supersedes_id', unique=False),
    )

    investigation_ref: Mapped[Investigation] = relationship(
        'Investigation', primaryjoin=lambda: and_(PublicationEvent.investigation_id == Investigation.id),
        foreign_keys=lambda: [PublicationEvent.investigation_id],
        viewonly=True, lazy="raise",
    )
    result_ref: Mapped[AnalyticalResult] = relationship(
        'AnalyticalResult', primaryjoin=lambda: and_(PublicationEvent.investigation_id == AnalyticalResult.investigation_id, PublicationEvent.result_id == AnalyticalResult.id),
        foreign_keys=lambda: [PublicationEvent.investigation_id, PublicationEvent.result_id],
        viewonly=True, lazy="raise",
    )
    result_seal_ref: Mapped[AggregateSeal] = relationship(
        'AggregateSeal', primaryjoin=lambda: and_(PublicationEvent.investigation_id == AggregateSeal.investigation_id, PublicationEvent.result_seal_id == AggregateSeal.id),
        foreign_keys=lambda: [PublicationEvent.investigation_id, PublicationEvent.result_seal_id],
        viewonly=True, lazy="raise",
    )
    result_review_ref: Mapped[ReviewEvent] = relationship(
        'ReviewEvent', primaryjoin=lambda: and_(PublicationEvent.investigation_id == ReviewEvent.investigation_id, PublicationEvent.result_review_id == ReviewEvent.id),
        foreign_keys=lambda: [PublicationEvent.investigation_id, PublicationEvent.result_review_id],
        viewonly=True, lazy="raise",
    )
    review_seal_ref: Mapped[AggregateSeal] = relationship(
        'AggregateSeal', primaryjoin=lambda: and_(PublicationEvent.investigation_id == AggregateSeal.investigation_id, PublicationEvent.review_seal_id == AggregateSeal.id),
        foreign_keys=lambda: [PublicationEvent.investigation_id, PublicationEvent.review_seal_id],
        viewonly=True, lazy="raise",
    )
    supersedes_ref: Mapped[PublicationEvent | None] = relationship(
        'PublicationEvent', primaryjoin=lambda: and_(PublicationEvent.investigation_id == PublicationEvent.investigation_id, PublicationEvent.supersedes_id == PublicationEvent.id),
        foreign_keys=lambda: [PublicationEvent.investigation_id, PublicationEvent.supersedes_id],
        remote_side=lambda: [PublicationEvent.investigation_id, PublicationEvent.id],
        viewonly=True, lazy="raise",
    )
