# M4.5 prerequisite remediation — immutable role, instrument and evidence records

## Defect and decision

On the 0005 database head, component rows and condition reviews were immutable, but an ordinary UPDATE could change the role category, instrument code or evidence excerpt reached through their UUIDs. Neither the condition seal nor the review seal covers the full contents of every referenced row. The preflight demonstrated that both digests could still verify after these edits.

The five M3 design deliverables, remediation logs and M3.4 review, implementation reports through the variable fix, models, historical migrations, sealing/N1 routines and database fixtures were inspected. The installed relationships match the approved schema. ConditionComponent carries scoped FKs to ConditionRole, Instrument and EvidenceReference. Conditions and ReviewEvents also cite evidence. Roles and instruments cite evidence, and each EvidenceReference pins one SourceDocument. The condition reviewer assesses component, role and instrument evidence. The architecture defines neither a separate instrument review target nor a role/instrument version counter. [M3 integrity contract, including R1 and R6](../architecture/postgresql_schema_proposal.md)

## Enforcement

Revision `0006_evidence_immutability` follows `0005_variable_immutability`. Protection begins on insertion. PostgreSQL rejects UPDATE or DELETE of any existing row with SQLSTATE 55000. The statement trigger also rejects TRUNCATE. The rules apply to ordinary direct SQL and to writes issued through SQLAlchemy.

| Protected table | Contents preserved |
|---|---|
| condition_role | All columns, including investigation, UUID, role code, definition, variable category, evidence and creation time |
| instrument | All columns, including investigation, UUID, instrument code, description, evidence and creation time |
| evidence_reference | All columns, including the source-document FK, locator identity, JSON location, excerpt, location basis, extraction method/version and verification scope/status |
| source_document | All first-registration columns, including artifact identity, filename, SHA-256, byte count, storage key, source version and metadata |

The fourth table closes the remaining direct citation path: an immutable locator would otherwise still point to mutable source-registration contents. R6 already directs descriptive corrections to MetadataRevision. Changing external bytes at a storage key is a separate archive-integrity concern.

The migration creates **eight triggers**: `evidence_freeze` (BEFORE UPDATE OR DELETE, FOR EACH ROW) and `evidence_truncate` (BEFORE TRUNCATE, FOR EACH STATEMENT) on each table. Each calls the existing `flare_sealing.immutable()`. Added SQL functions: **zero**. No FK, unique key, domain column, digest algorithm, seal or approval record changes. Revision 0005's variable-specific trigger is retained. The unconditional evidence guard also covers unreferenced evidence and evidence shared across any number of targets.

## Corrections, attachment and concurrency

Register fresh supporting evidence at its actual distinct locator identity and explicitly insert corrected role/instrument UUIDs with available codes under the existing scoped uniqueness rules. The tables have no predecessor column or automatic latest-version lookup. A successor condition uses its existing revision/supersedes relationship, new component rows and explicit corrected FKs. Seal the successor condition, append a fresh review targeting that condition and seal its dependency membership. Old conditions, protocols and reviews retain their original references. The caller identifies the correction and supplies its evidence; the database cannot determine whether two independently registered instruments are scientifically equivalent, or whether an unattested scientific assertion is true.

An attachment does not transition a row from editable to frozen. Even an edit using a snapshot that predates the first attachment must pass the unconditional mutation trigger. Concurrent attachments use PostgreSQL's scoped FKs and normal key-share locks and can legitimately cite the same row. A DELETE may wait on an attachment's FK lock before reaching the rejection trigger. No attachment-specific lock table, reference count or application sequencing is needed. Existing SERIALIZABLE, parent-locking and review/sealing rules still apply. Tests use independent writer connections, hold the first transaction open, and use a third connection to distinguish a lock wait from immediate rejection.

## Deployment, downgrade and historical audit

Upgrade installs triggers transactionally and takes PostgreSQL DDL locks on the four tables. Concurrent writes can wait during installation. The migration executes no data-modifying statements. Downgrade refuses by default. The project’s explicit `-x confirm_destructive_downgrade=yes` option or equivalent programmatic confirmation removes only these eight triggers in reverse order. Data and the previous variable, N1 and aggregate guards survive. Edits could again occur in the downgrade interval; re-upgrade cannot reconstruct them.

The effective FLARE configuration had **no persistent development DATABASE_URL**. No persistent row counts or conclusions about prior edits are available. Current rows can identify the recorded roles, instruments, locators and registered document hashes. A seal establishes its own immutable membership and pinned FK identities. It cannot establish the past contents of formerly mutable referenced rows. Investigating older content would require independent retained backups, audit records or trusted source artifacts. The populated database used for verification contained disposable technical fixtures.

## Verification method

The migration round-trip test creates content on revision 0005 and captures it before upgrading: role, instrument, component, three distinct evidence cases (condition-only, review-only and shared), source registration, protocol seal and a historical N1 result snapshot selecting the reviewed condition. It independently rebuilds canonical-json-v2 bytes in Python for the condition and review and compares their SHA-256 digests with the stored values. After upgrade and after creating a corrected successor with fresh UUIDs, evidence and a sealed condition review, it compares the complete captured rows, original seal identities, bytes and historical output. Drift is checked with Alembic at head.

Direct SQL tests exercise updates and deletes on each evidence path, including a reference shared by role, instrument and component. The deletion tests check the immutability SQLSTATE rather than relying on FK failure. Tests also attempt TRUNCATE CASCADE inside a rollback boundary. The concurrency cases exercise attachment versus excerpt change, attachment versus deletion, two targets attaching the same evidence, and a successor review versus a change to the original role.

The read-only preservation comparison verified all 129 CSV records, all 17 ordered original headers and all 2,193 source strings against the existing JSONL. Reclassifying each original string produced the same classification and quality flags. SHA-256 matched all three original acquisitions: CSV `71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042`, DOCX `69f32647792f54ab2a561e3cdafc6c87d854564fe487aed2b09265286bd84e1d`, XLSX `1a3b283dd0adec861793bbc4a454aab64d398cd32d6f37d7a1ad0f642879e686`.

## Files and limits

Created the 0006 migration, backend/tests/test_reviewed_evidence.py and this report. Updated backend/tests/test_migrations.py for the new head and revision count. No historical migration changes. Direct DML protection assumes triggers remain enabled; owner-level DDL and archive retention are operational controls. This prerequisite covers immutable identities and evidence. N2 matching and its twelve-case acceptance matrix await independent review and explicit approval.

## Executed results

From backend on the fixture-owned PostgreSQL 17.11 cluster:

```powershell
& .venv/Scripts/python.exe -m pytest -c pyproject.toml tests -q --run-postgres '--pg-bin=C:/Program Files/PostgreSQL/17/bin' --tb=short
```

**202 passed, 0 failed, 1 warning in 73.61 seconds.** The warning was the existing Starlette/httpx TestClient deprecation.

| Group | Passed |
|---|---:|
| API and CSV parser | 40 |
| M4.1 foundation | 34 |
| M4.2 schema | 16 |
| M4.3 aggregate sealing | 27 |
| M4.4 N1 snapshots | 52 |
| Scientific-variable immutability | 13 |
| Direct UPDATE and DELETE rejection | 14 |
| TRUNCATE CASCADE rejection | 1 |
| Populated upgrade, guarded downgrade, re-upgrade, independent digest/history and successor checks | 1 |
| Concurrent operations | 4 |

All fourteen direct mutation attempts returned 55000. Concurrent edits and deletion failed, both independent target attachments committed with the same evidence UUID, and the successor review committed while the original role edit failed. The populated migration cycle passed the Alembic drift check. The independent digests, original seal IDs, referenced contents, protocol seal and historical N1 output compared equal after successor approval. The N2 matrix was not executed.
