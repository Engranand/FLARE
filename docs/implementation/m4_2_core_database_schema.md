# M4.2 core scientific database schema

Verified 2026-11-06. M4.2 implements the approved relational declarations only. The real NASA ingestion gate remains closed. This report does not authorize M4.3 or claim scientific/workflow validation.

## Repository audit and scope

Read the M3.4 final review, all five architecture deliverables and the M4.1 implementation report before changes. `postgresql_schema_proposal.md` is the normative DDL source; the ER diagram is a corroborating inventory, not an alternative specification.

Reused M4.1 settings, lazy PostgreSQL engine, SERIALIZABLE application configuration, session factory, safe error handling, Alembic connection injection, empty baseline and isolated PostgreSQL fixture. Python is 3.12.8; installed direct database dependencies remain SQLAlchemy 2.0.57, psycopg/psycopg-binary 3.3.8 and Alembic 1.20.1. Dependency files were not changed. No backend formatter or type checker is configured.

Persistent development connectivity is not configured; backend/.env is absent. No persistent database was migrated. Tests provisioned a private PostgreSQL 17.11 cluster through the existing fixture, with random credentials, loopback port and owned temporary directory. M4.2 created three randomly named, owned databases inside that cluster: migrated implementation, original approved-DDL oracle, and ORM metadata oracle. Each was dropped; the fixture stopped its own cluster. No existing PostgreSQL service or database was changed. No SQLite was used.

## Implementation and enforcement boundary

`app/models/scientific.py` contains 33 explicit typed SQLAlchemy 2 declarative classes. `app/models/__init__.py` registers/exports them; Alembic imports that module. No model or migration reads architecture documents at runtime. Tests alone read the approved DDL as an independent oracle.

Types map exactly: UUID(as_uuid=True), Text, BigInteger, Integer, Numeric(asdecimal=True) without an imposed scale/precision, Date, DateTime(timezone=True), and PostgreSQL JSONB. Nullable columns have optional Python annotations. No speculative defaults, entities or columns were added. SQL columns called `metadata` are mapped to Python `metadata_json` because DeclarativeBase reserves `metadata`; SQL names are unchanged. JSONB nested in-place mutation is not tracked automatically: assign a replacement object to persist a change. The committed-session test verifies serialization, not an unspecified mutation-tracking feature.

All 140 FK paths have typed, scalar, read-only relationships with explicit joins and foreign columns. Shared investigation/parse-run keys have one write interface: the scalar mapped columns. Relationships use viewonly=True, lazy='raise'; callers explicitly eager-load references. A second path to the same target uses a `_scoped_ref` suffix. Self-referential predecessor mappings specify remote_side and are tested with selectinload. No overlaps warning suppression or ORM delete cascade is configured. Relationship assignment does not persist changes; callers must set FK columns. Mapper configuration is tested with SAWarning treated as an error.

The proposal defines enum domains as TEXT plus CHECK, not native PostgreSQL enums. Accordingly **zero native enum types** are created or dropped. Every original enum restriction remains in the 110 CHECK constraints. No additional native enum type is invented.

FK and explicitly declared index names are identical to the proposal. Its PK, UNIQUE and CHECK declarations are unnamed: deterministic names `pk_<table>_01`, `uq_<table>_<ordinal>` and `ck_<table>_<ordinal>` identify them in models/migration. Inline protocol CHECKs are lifted to named table CHECKs with identical expressions. These naming choices do not change keys or predicates.

Cross-row correctness is deliberately not implemented: no aggregate sealing/digests, N1 enumeration/completeness, N2 policy matcher, review approval workflow, publication/revalidation, CanConsume/current versus historical authorization, security-definer functions or final application-role grants. CHECKs enforce only their declared row-local expressions. All architectural fields supporting later enforcement remain present. In particular, syntactically valid snapshot rows or result rows are not evidence of valid applicability, approval or publication. No scientific annotations were created, including in technical fixtures.

## Migration and downgrade

Revision `0002_m42_core_schema` follows `0001_m41_baseline`. The migration contains static, reviewed SQL independent of mutable ORM imports. It creates all tables and local constraints first, then 140 FKs (including cyclic relationships), then 112 indexes. It contains no data inserts. The original baseline remains unchanged.

Upgrade to head is explicit, never on application startup. Destructive downgrade is refused unless the operator explicitly supplies `alembic -x confirm_destructive_downgrade=yes downgrade 0001_m41_baseline`, or an embedding caller sets config.attributes['allow_destructive_downgrade'] to True. The tests exercise refusal and confirmation only on an owned disposable database. After confirmation, downgrade removes FK constraints first and tables in reverse order without CASCADE. It does not claim to preserve data: review/backup and conscious operator authorization are necessary before destructive use. No native enums exist to clean up. Revision and dependency order, confirmed round-trip, repeat upgrade and Alembic check were verified.

## Verification results

Final command, from backend (PowerShell):

```powershell
& .venv/Scripts/python.exe -m pytest -c pyproject.toml tests -q --run-postgres '--pg-bin=C:/Program Files/PostgreSQL/17/bin'
```

Final output: **90 passed, 1 warning in 32.76s**. The existing warning is Starlette's httpx TestClient deprecation; no relationship warnings occurred. The first execution exposed three fixture mistakes (duplicate Python keyword, wrong required field, self-reference loading); those were corrected before the passing runs. Final verification also materialized ORM metadata separately to compare CHECKs that Alembic autogeneration does not compare.

| Category | Passed |
|---|---:|
| Existing API tests | 9 |
| Existing CSV parser tests | 31 |
| M4.1 configuration tests | 18 |
| M4.1 infrastructure tests | 10 |
| Migration discovery/offline/error tests (updated for new head) | 3 |
| M4.1 PostgreSQL integration tests | 3 |
| New model/static-migration tests | 2 |
| New M4.2 PostgreSQL integration cases | 14 |
| Total | 90 |

Catalog verification uses SQLAlchemy's PostgreSQL inspector (PostgreSQL system catalogs) and server_version_num. It compares migrated schema, original proposal DDL executed independently, and ORM metadata materialized independently. Comparisons cover ordered columns/types/nullability/defaults, PKs, every unique-key tuple, PostgreSQL-normalized CHECK expressions, all named FK tuples/delete rules, and explicit index column order/uniqueness/predicates. Unnamed source constraints are compared by definition rather than server-generated names. The Alembic version table is explicitly excluded from the domain count. FK target PK/UNIQUE eligibility and compatible ordered local/remote types are also asserted individually.

| Catalog assertion | Verified result |
|---|---:|
| PostgreSQL server_version_num | 170011 (17.11) |
| Domain tables / ER entities | 33 / 33 |
| Columns | 384 |
| Primary keys | 33 |
| UNIQUE constraints | 54 |
| CHECK constraints | 110 |
| Foreign keys | 140 |
| RESTRICT delete FKs | 140 |
| Missing referenced columns / incompatible ordered types | 0 / 0 |
| Unintended cascade FKs / unexpected domain tables | 0 / 0 |
| Explicit indexes | 112 |
| Partial unique indexes (included in 112) | 4 |
| PK/UNIQUE backing indexes | 87 |
| Total domain indexes | 199 |
| Native enum types | 0 (approved TEXT+CHECK domains) |
| Catalog definition differences among three schemas | 0 |
| Alembic metadata drift | 0 |

Technical fixture results: successful source/evidence/parse/record/field/observation persistence; composite observation joins; JSONB nested serialization and SQL NULL versus empty string; timezone-bearing retrieval; unrounded Decimal round trip; revision predecessor join; explicit commit followed by retrieval in a new Session; valid shapes for all four dependency entry kinds without approving anything. Invalid cases correctly raise SQLSTATE 23502 (NOT NULL), 23503 (investigation and parse-run FK scope, restricted deletion), 23505 (revision/predecessor and all four partial unique indexes), or 23514 (invalid enum, object shape, exclusive targets, nonfinite numeric values, protocol policies, missing snapshot evidence and mixed dependency shapes). Test records are explicitly labelled technical fixtures, never NASA measurements. Rejection tests use savepoints and expected SQLSTATE assertions; fixtures roll back, and the explicit commit test deletes its technical row.

## Preservation and change control

A SHA-256 comparison checked 98 existing files against the pre-change snapshot. Only six existing files changed, all listed below. All approved architecture/review documents, raw NASA files, processed JSONL/quality output, parser logic/tests and frontend files in that snapshot are unchanged. A separate read-only CSV-to-JSONL comparison confirmed **129 records x 17 columns = 2,193 original values**, including exact strings/empty values. CSV SHA-256 remains `71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042`. No real NASA records were inserted into any database. No commits, amendments or pushes were performed.

Modified existing files:

- backend/app/db/base.py (metadata docstring only)
- backend/app/models/README.md
- backend/migrations/env.py (register models)
- backend/tests/test_db_infrastructure.py (remove obsolete empty-metadata assertion)
- backend/tests/test_migrations.py (new head; retain explicit baseline test)
- backend/tests/test_postgres_integration.py (explicit baseline target; full-head drift test moved to M4.2 tests)

New files:

- backend/app/models/__init__.py
- backend/app/models/scientific.py
- backend/migrations/versions/0002_m42_core_schema.py
- backend/tests/test_scientific_models.py
- backend/tests/test_core_schema_postgres.py
- docs/implementation/m4_2_core_database_schema.md

The one-time local translation helper was removed; it is not a runtime or build dependency. The repository was already untracked, so Git status alone cannot distinguish prior work; the pre-change hash snapshot supplies that distinction.

## Entity, constraint and index inventory

Counts below exclude FK constraints from the PK/UQ/CHECK columns. The index count includes declared partial unique indexes, but excludes automatically created PK/UNIQUE backing indexes.

| ORM entity | Table | Columns | PK | UQ | CHECK | FK | Explicit indexes |
|---|---|---:|---:|---:|---:|---:|---:|
| AggregateSeal | aggregate_seal | 13 | 1 | 6 | 4 | 7 | 6 |
| AnalysisProtocol | analysis_protocol | 11 | 1 | 1 | 4 | 2 | 1 |
| AnalyticalEligibility | analytical_eligibility | 18 | 1 | 3 | 9 | 11 | 10 |
| AnalyticalResult | analytical_result | 15 | 1 | 0 | 9 | 3 | 2 |
| AnnotationEvidence | annotation_evidence | 6 | 1 | 1 | 0 | 3 | 2 |
| ApprovalDependency | approval_dependency | 14 | 1 | 3 | 4 | 10 | 12 |
| ConditionComponent | condition_component | 12 | 1 | 1 | 5 | 7 | 6 |
| ConditionRole | condition_role | 7 | 1 | 1 | 0 | 2 | 1 |
| ConditionSegment | condition_segment | 8 | 1 | 1 | 1 | 3 | 2 |
| DataQualityIssue | data_quality_issue | 11 | 1 | 0 | 2 | 4 | 3 |
| EvidenceReference | evidence_reference | 14 | 1 | 1 | 3 | 2 | 1 |
| ExperimentalCondition | experimental_condition | 12 | 1 | 2 | 4 | 5 | 4 |
| ExperimentalTest | experimental_test | 7 | 1 | 1 | 1 | 2 | 1 |
| Instrument | instrument | 6 | 1 | 1 | 0 | 2 | 1 |
| Investigation | investigation | 10 | 1 | 1 | 1 | 0 | 0 |
| MetadataRevision | metadata_revision | 15 | 1 | 2 | 3 | 4 | 4 |
| Observation | observation | 15 | 1 | 1 | 7 | 8 | 7 |
| ParseRun | parse_run | 14 | 1 | 1 | 6 | 2 | 1 |
| ProtocolRequirement | protocol_requirement | 15 | 1 | 1 | 6 | 5 | 4 |
| ProtocolUnitRule | protocol_unit_rule | 9 | 1 | 1 | 0 | 3 | 2 |
| PublicationEvent | publication_event | 12 | 1 | 2 | 2 | 6 | 5 |
| ResultCondition | result_condition | 6 | 1 | 1 | 0 | 4 | 3 |
| ResultEvidence | result_evidence | 6 | 1 | 1 | 0 | 3 | 2 |
| ResultInput | result_input | 10 | 1 | 1 | 0 | 7 | 6 |
| ReviewEvent | review_event | 20 | 1 | 9 | 8 | 11 | 10 |
| ScientificVariable | scientific_variable | 14 | 1 | 1 | 3 | 2 | 1 |
| SemanticAnnotation | semantic_annotation | 23 | 1 | 2 | 15 | 5 | 4 |
| SourceAcquisition | source_acquisition | 16 | 1 | 0 | 3 | 2 | 1 |
| SourceDocument | source_document | 11 | 1 | 1 | 5 | 1 | 0 |
| SourceField | source_field | 10 | 1 | 2 | 3 | 3 | 2 |
| SourceRecord | source_record | 8 | 1 | 3 | 1 | 3 | 2 |
| TestRelationship | test_relationship | 8 | 1 | 1 | 1 | 4 | 3 |
| TestSourceRecord | test_source_record | 8 | 1 | 1 | 0 | 4 | 3 |

## Full foreign-key inventory

Every row below was verified against both PostgreSQL catalogs and the approved proposal. Every action is ON DELETE RESTRICT. Column ordering is significant.

| Constraint | Local table (ordered columns) | Referenced table (ordered columns) |
|---|---|---|
| source_document_investigation_id_fk | source_document (investigation_id) | investigation (id) |
| source_acquisition_investigation_id_fk | source_acquisition (investigation_id) | investigation (id) |
| source_acquisition_source_document_id_fk | source_acquisition (investigation_id, source_document_id) | source_document (investigation_id, id) |
| evidence_reference_investigation_id_fk | evidence_reference (investigation_id) | investigation (id) |
| evidence_reference_source_document_id_fk | evidence_reference (investigation_id, source_document_id) | source_document (investigation_id, id) |
| parse_run_investigation_id_fk | parse_run (investigation_id) | investigation (id) |
| parse_run_source_document_id_fk | parse_run (investigation_id, source_document_id) | source_document (investigation_id, id) |
| source_field_header_evidence_id_fk | source_field (investigation_id, header_evidence_id) | evidence_reference (investigation_id, id) |
| source_field_investigation_id_fk | source_field (investigation_id) | investigation (id) |
| source_field_parse_run_id_fk | source_field (investigation_id, parse_run_id) | parse_run (investigation_id, id) |
| source_record_investigation_id_fk | source_record (investigation_id) | investigation (id) |
| source_record_parse_run_id_fk | source_record (investigation_id, parse_run_id) | parse_run (investigation_id, id) |
| source_record_row_evidence_id_fk | source_record (investigation_id, row_evidence_id) | evidence_reference (investigation_id, id) |
| experimental_test_identity_evidence_id_fk | experimental_test (investigation_id, identity_evidence_id) | evidence_reference (investigation_id, id) |
| experimental_test_investigation_id_fk | experimental_test (investigation_id) | investigation (id) |
| test_source_record_evidence_id_fk | test_source_record (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| test_source_record_experimental_test_id_fk | test_source_record (investigation_id, experimental_test_id) | experimental_test (investigation_id, id) |
| test_source_record_investigation_id_fk | test_source_record (investigation_id) | investigation (id) |
| test_source_record_source_record_id_fk | test_source_record (investigation_id, source_record_id) | source_record (investigation_id, id) |
| test_relationship_evidence_id_fk | test_relationship (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| test_relationship_investigation_id_fk | test_relationship (investigation_id) | investigation (id) |
| test_relationship_left_test_id_fk | test_relationship (investigation_id, left_test_id) | experimental_test (investigation_id, id) |
| test_relationship_right_test_id_fk | test_relationship (investigation_id, right_test_id) | experimental_test (investigation_id, id) |
| observation_evidence_id_fk | observation (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| observation_investigation_id_fk | observation (investigation_id) | investigation (id) |
| observation_parse_run_id_fk | observation (investigation_id, parse_run_id) | parse_run (investigation_id, id) |
| observation_source_field_id_fk | observation (investigation_id, source_field_id) | source_field (investigation_id, id) |
| observation_source_field_id_same_run_fk | observation (investigation_id, parse_run_id, source_field_id) | source_field (investigation_id, parse_run_id, id) |
| observation_source_record_id_fk | observation (investigation_id, source_record_id) | source_record (investigation_id, id) |
| observation_source_record_id_same_run_fk | observation (investigation_id, parse_run_id, source_record_id) | source_record (investigation_id, parse_run_id, id) |
| observation_unit_evidence_id_fk | observation (investigation_id, unit_evidence_id) | evidence_reference (investigation_id, id) |
| scientific_variable_evidence_id_fk | scientific_variable (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| scientific_variable_investigation_id_fk | scientific_variable (investigation_id) | investigation (id) |
| semantic_annotation_investigation_id_fk | semantic_annotation (investigation_id) | investigation (id) |
| semantic_annotation_observation_id_fk | semantic_annotation (investigation_id, observation_id) | observation (investigation_id, id) |
| semantic_annotation_primary_evidence_id_fk | semantic_annotation (investigation_id, primary_evidence_id) | evidence_reference (investigation_id, id) |
| semantic_annotation_supersedes_id_fk | semantic_annotation (investigation_id, supersedes_id) | semantic_annotation (investigation_id, id) |
| semantic_annotation_variable_id_fk | semantic_annotation (investigation_id, variable_id) | scientific_variable (investigation_id, id) |
| annotation_evidence_annotation_id_fk | annotation_evidence (investigation_id, annotation_id) | semantic_annotation (investigation_id, id) |
| annotation_evidence_evidence_id_fk | annotation_evidence (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| annotation_evidence_investigation_id_fk | annotation_evidence (investigation_id) | investigation (id) |
| experimental_condition_evidence_id_fk | experimental_condition (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| experimental_condition_experimental_test_id_fk | experimental_condition (investigation_id, experimental_test_id) | experimental_test (investigation_id, id) |
| experimental_condition_investigation_id_fk | experimental_condition (investigation_id) | investigation (id) |
| experimental_condition_segment_id_fk | experimental_condition (investigation_id, segment_id) | condition_segment (investigation_id, id) |
| experimental_condition_supersedes_id_fk | experimental_condition (investigation_id, supersedes_id) | experimental_condition (investigation_id, id) |
| data_quality_issue_evidence_id_fk | data_quality_issue (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| data_quality_issue_experimental_test_id_fk | data_quality_issue (investigation_id, experimental_test_id) | experimental_test (investigation_id, id) |
| data_quality_issue_investigation_id_fk | data_quality_issue (investigation_id) | investigation (id) |
| data_quality_issue_observation_id_fk | data_quality_issue (investigation_id, observation_id) | observation (investigation_id, id) |
| review_event_annotation_id_fk | review_event (investigation_id, annotation_id) | semantic_annotation (investigation_id, id) |
| review_event_condition_id_fk | review_event (investigation_id, condition_id) | experimental_condition (investigation_id, id) |
| review_event_evidence_id_fk | review_event (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| review_event_investigation_id_fk | review_event (investigation_id) | investigation (id) |
| review_event_issue_id_fk | review_event (investigation_id, issue_id) | data_quality_issue (investigation_id, id) |
| review_event_metadata_revision_id_fk | review_event (investigation_id, metadata_revision_id) | metadata_revision (investigation_id, id) |
| review_event_result_id_fk | review_event (investigation_id, result_id) | analytical_result (investigation_id, id) |
| review_event_supersedes_id_fk | review_event (investigation_id, supersedes_id) | review_event (investigation_id, id) |
| review_event_test_link_id_fk | review_event (investigation_id, test_link_id) | test_source_record (investigation_id, id) |
| review_event_test_relation_id_fk | review_event (investigation_id, test_relation_id) | test_relationship (investigation_id, id) |
| review_event_variable_id_fk | review_event (investigation_id, variable_id) | scientific_variable (investigation_id, id) |
| analysis_protocol_evidence_id_fk | analysis_protocol (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| analysis_protocol_investigation_id_fk | analysis_protocol (investigation_id) | investigation (id) |
| analytical_eligibility_annotation_id_fk | analytical_eligibility (investigation_id, annotation_id) | semantic_annotation (investigation_id, id) |
| analytical_eligibility_annotation_review_id_fk | analytical_eligibility (investigation_id, annotation_review_id) | review_event (investigation_id, id) |
| analytical_eligibility_condition_id_fk | analytical_eligibility (investigation_id, condition_id) | experimental_condition (investigation_id, id) |
| analytical_eligibility_condition_review_id_fk | analytical_eligibility (investigation_id, condition_review_id) | review_event (investigation_id, id) |
| analytical_eligibility_evidence_id_fk | analytical_eligibility (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| analytical_eligibility_experimental_test_id_fk | analytical_eligibility (investigation_id, experimental_test_id) | experimental_test (investigation_id, id) |
| analytical_eligibility_investigation_id_fk | analytical_eligibility (investigation_id) | investigation (id) |
| analytical_eligibility_observation_id_fk | analytical_eligibility (investigation_id, observation_id) | observation (investigation_id, id) |
| analytical_eligibility_protocol_id_fk | analytical_eligibility (investigation_id, protocol_id) | analysis_protocol (investigation_id, id) |
| analytical_eligibility_segment_id_fk | analytical_eligibility (investigation_id, segment_id) | condition_segment (investigation_id, id) |
| analytical_eligibility_supersedes_id_fk | analytical_eligibility (investigation_id, supersedes_id) | analytical_eligibility (investigation_id, id) |
| analytical_result_artifact_document_id_fk | analytical_result (investigation_id, artifact_document_id) | source_document (investigation_id, id) |
| analytical_result_investigation_id_fk | analytical_result (investigation_id) | investigation (id) |
| analytical_result_protocol_id_fk | analytical_result (investigation_id, protocol_id) | analysis_protocol (investigation_id, id) |
| result_input_annotation_id_fk | result_input (investigation_id, annotation_id) | semantic_annotation (investigation_id, id) |
| result_input_eligibility_id_fk | result_input (investigation_id, eligibility_id) | analytical_eligibility (investigation_id, id) |
| result_input_investigation_id_fk | result_input (investigation_id) | investigation (id) |
| result_input_result_id_fk | result_input (investigation_id, result_id) | analytical_result (investigation_id, id) |
| result_input_segment_id_fk | result_input (investigation_id, segment_id) | condition_segment (investigation_id, id) |
| result_input_test_link_id_fk | result_input (investigation_id, test_link_id) | test_source_record (investigation_id, id) |
| result_input_test_link_review_id_fk | result_input (investigation_id, test_link_review_id) | review_event (investigation_id, id) |
| result_condition_condition_id_fk | result_condition (investigation_id, condition_id) | experimental_condition (investigation_id, id) |
| result_condition_eligibility_id_fk | result_condition (investigation_id, eligibility_id) | analytical_eligibility (investigation_id, id) |
| result_condition_investigation_id_fk | result_condition (investigation_id) | investigation (id) |
| result_condition_result_id_fk | result_condition (investigation_id, result_id) | analytical_result (investigation_id, id) |
| result_evidence_evidence_id_fk | result_evidence (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| result_evidence_investigation_id_fk | result_evidence (investigation_id) | investigation (id) |
| result_evidence_result_id_fk | result_evidence (investigation_id, result_id) | analytical_result (investigation_id, id) |
| condition_segment_evidence_id_fk | condition_segment (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| condition_segment_experimental_test_id_fk | condition_segment (investigation_id, experimental_test_id) | experimental_test (investigation_id, id) |
| condition_segment_investigation_id_fk | condition_segment (investigation_id) | investigation (id) |
| instrument_evidence_id_fk | instrument (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| instrument_investigation_id_fk | instrument (investigation_id) | investigation (id) |
| condition_role_evidence_id_fk | condition_role (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| condition_role_investigation_id_fk | condition_role (investigation_id) | investigation (id) |
| condition_component_annotation_id_fk | condition_component (investigation_id, annotation_id) | semantic_annotation (investigation_id, id) |
| condition_component_condition_id_fk | condition_component (investigation_id, condition_id) | experimental_condition (investigation_id, id) |
| condition_component_evidence_id_fk | condition_component (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| condition_component_instrument_id_fk | condition_component (investigation_id, instrument_id) | instrument (investigation_id, id) |
| condition_component_investigation_id_fk | condition_component (investigation_id) | investigation (id) |
| condition_component_role_id_fk | condition_component (investigation_id, role_id) | condition_role (investigation_id, id) |
| condition_component_variable_id_fk | condition_component (investigation_id, variable_id) | scientific_variable (investigation_id, id) |
| protocol_requirement_evidence_id_fk | protocol_requirement (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| protocol_requirement_investigation_id_fk | protocol_requirement (investigation_id) | investigation (id) |
| protocol_requirement_protocol_id_fk | protocol_requirement (investigation_id, protocol_id) | analysis_protocol (investigation_id, id) |
| protocol_requirement_role_id_fk | protocol_requirement (investigation_id, role_id) | condition_role (investigation_id, id) |
| protocol_requirement_variable_id_fk | protocol_requirement (investigation_id, variable_id) | scientific_variable (investigation_id, id) |
| protocol_unit_rule_evidence_id_fk | protocol_unit_rule (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| protocol_unit_rule_investigation_id_fk | protocol_unit_rule (investigation_id) | investigation (id) |
| protocol_unit_rule_requirement_id_fk | protocol_unit_rule (investigation_id, requirement_id) | protocol_requirement (investigation_id, id) |
| metadata_revision_evidence_id_fk | metadata_revision (investigation_id, evidence_id) | evidence_reference (investigation_id, id) |
| metadata_revision_investigation_id_fk | metadata_revision (investigation_id) | investigation (id) |
| metadata_revision_source_document_id_fk | metadata_revision (investigation_id, source_document_id) | source_document (investigation_id, id) |
| metadata_revision_supersedes_id_fk | metadata_revision (investigation_id, supersedes_id) | metadata_revision (investigation_id, id) |
| aggregate_seal_annotation_id_fk | aggregate_seal (investigation_id, annotation_id) | semantic_annotation (investigation_id, id) |
| aggregate_seal_condition_id_fk | aggregate_seal (investigation_id, condition_id) | experimental_condition (investigation_id, id) |
| aggregate_seal_investigation_id_fk | aggregate_seal (investigation_id) | investigation (id) |
| aggregate_seal_parse_run_id_fk | aggregate_seal (investigation_id, parse_run_id) | parse_run (investigation_id, id) |
| aggregate_seal_protocol_id_fk | aggregate_seal (investigation_id, protocol_id) | analysis_protocol (investigation_id, id) |
| aggregate_seal_result_id_fk | aggregate_seal (investigation_id, result_id) | analytical_result (investigation_id, id) |
| aggregate_seal_review_id_fk | aggregate_seal (investigation_id, review_id) | review_event (investigation_id, id) |
| ad_snapshot_issue_id_fk | approval_dependency (investigation_id, snapshot_issue_id) | data_quality_issue (investigation_id, id) |
| ad_snapshot_link_id_fk | approval_dependency (investigation_id, snapshot_link_id) | test_source_record (investigation_id, id) |
| ad_snapshot_observation_id_fk | approval_dependency (investigation_id, snapshot_observation_id) | observation (investigation_id, id) |
| ad_snapshot_review_id_fk | approval_dependency (investigation_id, snapshot_review_id) | review_event (investigation_id, id) |
| ad_snapshot_review_seal_id_fk | approval_dependency (investigation_id, snapshot_review_seal_id) | aggregate_seal (investigation_id, id) |
| approval_dependency_dependency_eligibility_id_fk | approval_dependency (investigation_id, dependency_eligibility_id) | analytical_eligibility (investigation_id, id) |
| approval_dependency_dependency_review_id_fk | approval_dependency (investigation_id, dependency_review_id) | review_event (investigation_id, id) |
| approval_dependency_dependency_seal_id_fk | approval_dependency (investigation_id, dependency_seal_id) | aggregate_seal (investigation_id, id) |
| approval_dependency_investigation_id_fk | approval_dependency (investigation_id) | investigation (id) |
| approval_dependency_owner_review_id_fk | approval_dependency (investigation_id, owner_review_id) | review_event (investigation_id, id) |
| publication_event_investigation_id_fk | publication_event (investigation_id) | investigation (id) |
| publication_event_result_id_fk | publication_event (investigation_id, result_id) | analytical_result (investigation_id, id) |
| publication_event_result_review_id_fk | publication_event (investigation_id, result_review_id) | review_event (investigation_id, id) |
| publication_event_result_seal_id_fk | publication_event (investigation_id, result_seal_id) | aggregate_seal (investigation_id, id) |
| publication_event_review_seal_id_fk | publication_event (investigation_id, review_seal_id) | aggregate_seal (investigation_id, id) |
| publication_event_supersedes_id_fk | publication_event (investigation_id, supersedes_id) | publication_event (investigation_id, id) |

## Explicit index inventory

All predicates below were checked against PostgreSQL-normalized predicates from the independent proposal database.

| Index | Table | Ordered columns | Unique | Predicate |
|---|---|---|---|---|
| lookup_2 | source_acquisition | investigation_id, source_document_id | False | — |
| lookup_4 | evidence_reference | investigation_id, source_document_id | False | — |
| lookup_6 | parse_run | investigation_id, source_document_id | False | — |
| lookup_8 | source_field | investigation_id, parse_run_id | False | — |
| lookup_9 | source_field | investigation_id, header_evidence_id | False | — |
| lookup_11 | source_record | investigation_id, parse_run_id | False | — |
| lookup_12 | source_record | investigation_id, row_evidence_id | False | — |
| lookup_14 | experimental_test | investigation_id, identity_evidence_id | False | — |
| lookup_16 | test_source_record | investigation_id, experimental_test_id | False | — |
| lookup_17 | test_source_record | investigation_id, source_record_id | False | — |
| lookup_18 | test_source_record | investigation_id, evidence_id | False | — |
| lookup_20 | test_relationship | investigation_id, left_test_id | False | — |
| lookup_21 | test_relationship | investigation_id, right_test_id | False | — |
| lookup_22 | test_relationship | investigation_id, evidence_id | False | — |
| lookup_24 | observation | investigation_id, parse_run_id | False | — |
| lookup_25 | observation | investigation_id, source_record_id | False | — |
| lookup_26 | observation | investigation_id, source_field_id | False | — |
| lookup_27 | observation | investigation_id, evidence_id | False | — |
| lookup_28 | observation | investigation_id, unit_evidence_id | False | — |
| lookup_85 | observation | investigation_id, parse_run_id, source_record_id | False | — |
| lookup_86 | observation | investigation_id, parse_run_id, source_field_id | False | — |
| lookup_30 | scientific_variable | investigation_id, evidence_id | False | — |
| lookup_32 | semantic_annotation | investigation_id, observation_id | False | — |
| lookup_33 | semantic_annotation | investigation_id, variable_id | False | — |
| lookup_34 | semantic_annotation | investigation_id, supersedes_id | False | — |
| lookup_35 | semantic_annotation | investigation_id, primary_evidence_id | False | — |
| lookup_37 | annotation_evidence | investigation_id, annotation_id | False | — |
| lookup_38 | annotation_evidence | investigation_id, evidence_id | False | — |
| lookup_101 | experimental_condition | investigation_id, segment_id | False | — |
| lookup_40 | experimental_condition | investigation_id, experimental_test_id | False | — |
| lookup_41 | experimental_condition | investigation_id, supersedes_id | False | — |
| lookup_42 | experimental_condition | investigation_id, evidence_id | False | — |
| lookup_44 | data_quality_issue | investigation_id, observation_id | False | — |
| lookup_45 | data_quality_issue | investigation_id, experimental_test_id | False | — |
| lookup_46 | data_quality_issue | investigation_id, evidence_id | False | — |
| lookup_115 | review_event | investigation_id, metadata_revision_id | False | — |
| lookup_48 | review_event | investigation_id, annotation_id | False | — |
| lookup_49 | review_event | investigation_id, variable_id | False | — |
| lookup_50 | review_event | investigation_id, condition_id | False | — |
| lookup_51 | review_event | investigation_id, test_link_id | False | — |
| lookup_52 | review_event | investigation_id, test_relation_id | False | — |
| lookup_53 | review_event | investigation_id, issue_id | False | — |
| lookup_54 | review_event | investigation_id, result_id | False | — |
| lookup_55 | review_event | investigation_id, supersedes_id | False | — |
| lookup_56 | review_event | investigation_id, evidence_id | False | — |
| lookup_58 | analysis_protocol | investigation_id, evidence_id | False | — |
| lookup_134 | analytical_eligibility | investigation_id, segment_id | False | — |
| lookup_60 | analytical_eligibility | investigation_id, protocol_id | False | — |
| lookup_61 | analytical_eligibility | investigation_id, observation_id | False | — |
| lookup_62 | analytical_eligibility | investigation_id, experimental_test_id | False | — |
| lookup_63 | analytical_eligibility | investigation_id, supersedes_id | False | — |
| lookup_64 | analytical_eligibility | investigation_id, annotation_id | False | — |
| lookup_65 | analytical_eligibility | investigation_id, annotation_review_id | False | — |
| lookup_66 | analytical_eligibility | investigation_id, condition_id | False | — |
| lookup_67 | analytical_eligibility | investigation_id, condition_review_id | False | — |
| lookup_68 | analytical_eligibility | investigation_id, evidence_id | False | — |
| lookup_70 | analytical_result | investigation_id, protocol_id | False | — |
| lookup_71 | analytical_result | investigation_id, artifact_document_id | False | — |
| lookup_102 | result_input | investigation_id, segment_id | False | — |
| lookup_73 | result_input | investigation_id, result_id | False | — |
| lookup_74 | result_input | investigation_id, annotation_id | False | — |
| lookup_75 | result_input | investigation_id, eligibility_id | False | — |
| lookup_76 | result_input | investigation_id, test_link_id | False | — |
| lookup_77 | result_input | investigation_id, test_link_review_id | False | — |
| lookup_79 | result_condition | investigation_id, result_id | False | — |
| lookup_80 | result_condition | investigation_id, condition_id | False | — |
| lookup_81 | result_condition | investigation_id, eligibility_id | False | — |
| lookup_83 | result_evidence | investigation_id, result_id | False | — |
| lookup_84 | result_evidence | investigation_id, evidence_id | False | — |
| lookup_88 | condition_segment | investigation_id, experimental_test_id | False | — |
| lookup_89 | condition_segment | investigation_id, evidence_id | False | — |
| lookup_91 | instrument | investigation_id, evidence_id | False | — |
| lookup_93 | condition_role | investigation_id, evidence_id | False | — |
| lookup_100 | condition_component | investigation_id, evidence_id | False | — |
| lookup_95 | condition_component | investigation_id, condition_id | False | — |
| lookup_96 | condition_component | investigation_id, role_id | False | — |
| lookup_97 | condition_component | investigation_id, instrument_id | False | — |
| lookup_98 | condition_component | investigation_id, variable_id | False | — |
| lookup_99 | condition_component | investigation_id, annotation_id | False | — |
| lookup_104 | protocol_requirement | investigation_id, protocol_id | False | — |
| lookup_105 | protocol_requirement | investigation_id, variable_id | False | — |
| lookup_106 | protocol_requirement | investigation_id, role_id | False | — |
| lookup_107 | protocol_requirement | investigation_id, evidence_id | False | — |
| lookup_109 | protocol_unit_rule | investigation_id, requirement_id | False | — |
| lookup_110 | protocol_unit_rule | investigation_id, evidence_id | False | — |
| lookup_112 | metadata_revision | investigation_id, source_document_id | False | — |
| lookup_113 | metadata_revision | investigation_id, supersedes_id | False | — |
| lookup_114 | metadata_revision | investigation_id, evidence_id | False | — |
| metadata_investigation_revision | metadata_revision | investigation_id, revision | True | subject_kind = 'investigation' |
| lookup_117 | aggregate_seal | investigation_id, parse_run_id | False | — |
| lookup_118 | aggregate_seal | investigation_id, annotation_id | False | — |
| lookup_119 | aggregate_seal | investigation_id, condition_id | False | — |
| lookup_120 | aggregate_seal | investigation_id, protocol_id | False | — |
| lookup_121 | aggregate_seal | investigation_id, result_id | False | — |
| lookup_122 | aggregate_seal | investigation_id, review_id | False | — |
| ad_scope_issue_once | approval_dependency | investigation_id, owner_review_id, snapshot_observation_id, snapshot_issue_id | True | entry_kind = 'scope_issue' |
| ad_scope_link_once | approval_dependency | investigation_id, owner_review_id, snapshot_observation_id, snapshot_link_id | True | entry_kind = 'scope_link' |
| ad_scope_observation_once | approval_dependency | investigation_id, owner_review_id, snapshot_observation_id | True | entry_kind = 'scope_observation' |
| lookup_124 | approval_dependency | investigation_id, owner_review_id | False | — |
| lookup_125 | approval_dependency | investigation_id, dependency_review_id | False | — |
| lookup_126 | approval_dependency | investigation_id, dependency_eligibility_id | False | — |
| lookup_127 | approval_dependency | investigation_id, dependency_seal_id | False | — |
| lookup_135 | approval_dependency | investigation_id, snapshot_observation_id | False | — |
| lookup_136 | approval_dependency | investigation_id, snapshot_link_id | False | — |
| lookup_137 | approval_dependency | investigation_id, snapshot_issue_id | False | — |
| lookup_138 | approval_dependency | investigation_id, snapshot_review_id | False | — |
| lookup_139 | approval_dependency | investigation_id, snapshot_review_seal_id | False | — |
| lookup_129 | publication_event | investigation_id, result_id | False | — |
| lookup_130 | publication_event | investigation_id, result_seal_id | False | — |
| lookup_131 | publication_event | investigation_id, result_review_id | False | — |
| lookup_132 | publication_event | investigation_id, review_seal_id | False | — |
| lookup_133 | publication_event | investigation_id, supersedes_id | False | — |

## Remaining limits

The catalog and representative fixture tests establish declarative equivalence, not exhaustive workflow validation or scientific suitability. No production grants, concurrency/enforcement acceptance suite, operational deployment, performance benchmark, scientific approval or ingestion has been performed. Declarative FK targets cannot by themselves enforce matching review subjects, historical completeness, same-segment requirements or current-use eligibility. Those remain subsequent authorized milestones. Stop at M4.2.
