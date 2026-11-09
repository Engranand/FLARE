# M4.3 aggregate integrity and sealing

M4.3 installs database enforcement for the six content seals in the [approved PostgreSQL proposal](../architecture/postgresql_schema_proposal.md). An unsealed version accepts new members. Sealing records its complete contents in one transaction. Subsequent membership changes require a new parent identity, new member identities and a new seal.

## Repository inspection

The five approved architecture deliverables, M3.3 remediation log, M3.4 final review, M4.1 and M4.2 implementation reports, actual schema migration, ORM models and PostgreSQL test fixtures were inspected. The M4.2 inventory agrees with the implementation. It contains 33 domain tables, 140 foreign keys, six exclusive aggregate seal targets and one unique key per target. No schema discrepancy was found. The working tree already contained untracked project directories. Neither historical migration was edited.

## Ownership

| Parent | Seal target column | Member table and ownership column |
|---|---|---|
| parse_run | parse_run_id | source_field.parse_run_id, source_record.parse_run_id, observation.parse_run_id |
| semantic_annotation | annotation_id | annotation_evidence.annotation_id |
| experimental_condition | condition_id | condition_component.condition_id |
| analysis_protocol | protocol_id | protocol_requirement.protocol_id, protocol_unit_rule.requirement_id through protocol_requirement.protocol_id |
| analytical_result | result_id | result_input.result_id, result_condition.result_id, result_evidence.result_id |
| review_event | review_id | approval_dependency.owner_review_id |

Every lookup includes investigation_id. Evidence, tests, definitions and other referenced records retain their FK identities in the hashed row. Only the listed ownership paths collect children. A new review of a subject therefore does not change that subject's sealed membership.

## Lifecycle and database interfaces

Insert a parent and its members in a SERIALIZABLE transaction. Each member insert locks its investigation and owning parent and checks for a seal. Parent rows, member rows and seals are append-only from insertion. UPDATE, DELETE and TRUNCATE are rejected. Members may be appended to a draft across transactions subject to parse completeness. A failed parse may have no children. A complete run must have its declared number of records and a cell for each record/field pair within its table. Cross-table cells are rejected. Those checks also run when a draft transaction commits.

Call `flare_sealing.seal(target, investigation_id, parent_id, seal_id, actor, archive_bytes)` in the same transaction as any final inserts. The archive argument defaults to SQL NULL and is required for a new parse seal. The function locks the target, enumerates the database rows, calculates counts and digest, inserts one seal and returns it. Repeating a call for the same sealed identity returns the original seal. The M4.2 unique constraint also prevents competing seal identities. Success is final only after commit.

`flare_sealing.snapshot(target, investigation_id, parent_id)` returns counts, exact canonical bytes and the SHA-256 digest of the visible membership. Compare these with the immutable seal to verify content. During a draft, this read describes the current transaction view. It confers no analytical permission. Direct inserts into aggregate_seal undergo the same target, count and digest checks. Parse inserts must also present hash-matching archive bytes. Supplying bytes through a transaction-local setting transports evidence. The database recomputes its hash and compares its contents even for a direct insert.

## Canonical bytes

The fixed version is `canonical-json-v2`. The top-level UTF-8 object contains `members` followed by `parent`. The parent is its full column-keyed row. Each member is a four-element array containing its table name, lowercase investigation UUID, lowercase member UUID and full row. Members sort by bytewise table name and UUID. Object keys sort by Unicode code point in the verified UTF-8 database. Arrays preserve order. Full rows include all SQL columns, including nullable snapshot review and seal IDs. The seal row and member_counts are outside the digest input.

The serializer emits no insignificant whitespace or Unicode normalization. Quotes and backslashes are escaped, slash is literal and JSON controls use lowercase four-digit Unicode escapes. SQL NULL becomes JSON null and empty text remains an empty string. PostgreSQL rejects invalid surrogate sequences and U+0000 before they can be stored as text. SQL numbers use decimal strings without exponent, trailing fractional zeros or negative zero. UTC timestamps use six fractional digits and a Z suffix. Dates use ISO form and byte strings use hexadecimal. UUIDs, typed numbers and untouched source strings are serialized from their original SQL column types.

JSONB is recursively tagged. JSON null becomes `["null"]`. Other scalars use a type name and value, including `["number","1.2"]` versus `["string","1.2"]`. Arrays contain ordered tagged values. Objects contain key-sorted arrays of key/tagged-value pairs. Review rows retain explicit SQL null for absent heads and seals. The implementation uses PostgreSQL's built-in SHA-256 over the exact UTF-8 bytes. Counts have exactly one integer per child table, including zero, plus parent equal to one. Unsupported versions and claims that differ from independently enumerated membership fail with SQLSTATE 23514.

## Parse output witness

The implemented archive adapter reads the repository parser's UTF-8 JSONL record layout. The caller supplies original bytes and the database verifies the complete byte stream against parse_run.output_sha256. Each archive record must identify a distinct source row in order, with the correct logical record number, source filename/hash and parser version. The adapter checks ordered headers, column positions, field and record coverage, complete archived cell objects, raw values, parser classifications and quality flags. The technical representation stores the archived cell object in original_representation and its flag array under parser_flags.quality_flags. The hash also binds archive metadata without a separate relational column. Archive storage keys are never used as filesystem read instructions.

These JSONL-to-column conventions are implementation choices for the existing parser layout. M3 specifies byte and content equality but does not specify a universal adapter for every future parser. A new parser layout needs its own explicitly verified mapping. A header-only table has no header witness in this JSONL format and cannot receive a parse seal using it. Hash verification says nothing about long-term external archive availability.

## Database objects and transaction behavior

All 14 routines are in the flare_sealing schema and run with invoker privileges.

| Functions | Responsibility |
|---|---|
| ownership | Fixed six-parent and eleven-child inventory used by enumeration and insert guards |
| quote_string, json_value, full_row | String escaping, tagged JSONB encoding and SQL column serialization |
| snapshot | Ordered full membership, counts, UTF-8 bytes and digest |
| lock_parent, lock_parents | Investigation-first locking and ordered multi-aggregate reservation |
| immutable | Reject row mutation or table truncation |
| guard_child | Immediate check before insertion and deferred member validation |
| parse_shape, check_parse | Validate draft/final parse counts and cell coverage |
| archive_matches | Compare supplied archived bytes and represented rows |
| check_seal | Validate proposed seal and recheck it at transaction end |
| seal | Create or retrieve an immutable aggregate seal |

| Trigger name | Attached to | Instances |
|---|---|---:|
| freeze_row | All six parents, eleven children and aggregate_seal, before UPDATE/DELETE | 18 |
| freeze_truncate | Same eighteen tables, before TRUNCATE | 18 |
| guard_member | Each member table, before INSERT | 11 |
| member_final | Each member table, deferred after INSERT | 11 |
| parse_final | Parse parent and its three member tables, deferred after INSERT | 4 |
| seal_guard | aggregate_seal, before INSERT | 1 |
| seal_final | aggregate_seal, deferred after INSERT | 1 |
| **Total** | | **64** |

Both concurrent operations take the same existing parent row lock. Multi-aggregate callers can predeclare targets to lock_parents as JSON objects with target, inv and pid. This routine locks all investigations by UUID first, then parents by table name and UUID. The investigation lock serializes competing writes within one investigation. Immediate guards cover direct DML. Deferred checks enumerate the final visible membership, including indirect unit rules. The tests also try a late member after sealing inside the same transaction. A conflicting lock wait under SERIALIZABLE can invalidate a snapshot. run_aggregate_transaction retries SQLSTATE 40001 using a fresh transaction and replays the whole callback, including commit. Its configurable attempt limit defaults to three. Callers keep external side effects outside that replayable callback. SQLSTATE 55000 identifies immutable or already sealed content, and 25001 identifies insufficient isolation.

## Migration

Alembic revision 0003_m43_sealing follows 0002_m42_core_schema. It adds a function schema and triggers without adding domain tables or changing the ORM. The SQL file beside the revision is a versioned migration asset and must ship with it. Initial migration validates any pre-existing parse shapes and retained seals. A populated re-upgrade must supply original archived bytes for existing parse seals through transaction-local flare.m43_archives, a JSON map from output SHA-256 to hexadecimal bytes. Re-upgrade independently checks each retained seal. A mismatch rolls back installation. Verification cannot reconstruct changes made by an owner during an interval with enforcement disabled.

Downgrade preserves domain rows and seals and removes enforcement. It requires the existing explicit destructive-downgrade setting or CLI option `-x confirm_destructive_downgrade=yes`. It drops triggers first, functions in dependency order, then the empty function schema. No CASCADE is used. Tests perform refusal, confirmed downgrade, rejection of a tampered retained seal and re-upgrade with retained content. Only fixture-owned PostgreSQL databases are used.

## Verification

The suite provisions a private PostgreSQL 17.11 cluster. M4.1 and M4.2 tests continue to exercise their explicit historical revisions. Current-head drift verification runs after the M4.3 migration round trip.

```powershell
# From backend
& .venv/Scripts/python.exe -m pytest -c pyproject.toml tests -q --run-postgres '--pg-bin=C:/Program Files/PostgreSQL/17/bin' --tb=short
```

Final run on 2026-11-09: **117 passed, 0 failed, 1 warning in 44.23 seconds**. The warning is the existing Starlette/httpx TestClient deprecation.

| Suite | Passed |
|---|---:|
| API | 9 |
| Source-preserving CSV parser | 31 |
| M4.1 configuration, infrastructure, migration and PostgreSQL integration | 34 |
| M4.2 models, schema migration and PostgreSQL integration | 16 |
| M4.3 aggregate sealing, canonical bytes, archive checks, migration and races | 27 |
| **Total** | **117** |

An initial migration test found that PostgreSQL 17 parsed an unqualified json_value call as its built-in SQL/JSON expression. Schema-qualifying the recursive encoder fixed the migration. The first full regression run also found that Alembic's head check could not run on the deliberately historical M4.2 database. That test now compares its historical metadata directly, and the migration-cycle test runs the head check on M4.3.

All six aggregate fixtures contain actual technical member rows, including a nested unit rule. Separate SQLAlchemy reads and a Python expected-byte encoder verify full-row membership against PostgreSQL bytes and SHA-256. Literal vectors exercise escaping, exact decimals, tagged values, absence and ordering. All eleven late-insert paths and all eighteen protected tables are exercised. Tests reject incorrect digest/count claims, omitted and extra members, unsupported versions, incomplete or failed parses, and archives with a correct stored hash whose cells differ from the submitted rows. Rollback after seal insertion leaves no durable seal. A successor protocol changes membership while its predecessor's counts and digest remain verifiable.

The two race tests use separate writer connections and an observer. They wait until pg_blocking_pids reports the second writer blocked by the first before releasing the transaction. With the child first, the sealing operation retries and includes two requirements. With the seal first, the child retries and receives 55000. A fresh read after both writers finish verifies the committed digest against recomputed membership.

A separate read-only comparison verified all 129 rows and 17 fields against the preserved JSONL. All 2,193 original strings match. The CSV SHA-256 is 71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042.

## Change inventory

Created:

- backend/migrations/versions/0003_m43_sealing.py
- backend/migrations/versions/m43_sealing.sql
- backend/app/db/aggregate.py
- backend/tests/test_aggregate_sealing.py
- docs/implementation/m4_3_aggregate_integrity_sealing.md

Modified:

- backend/tests/test_migrations.py for revision discovery
- backend/tests/test_scientific_models.py for the static M4.2 DDL comparison
- backend/tests/test_core_schema_postgres.py for the explicit M4.2 catalog fixture and historical-revision metadata drift check

## Scope and limits

The M3 ownership sets, domain schema and canonical version were retained. Technical choices include the JSONL witness mapping, a dedicated SQL function schema, and a bounded retry wrapper. Application grants, authenticated actor identity, workflow approval, N1 applicability matching, N2 matching, publication and consumption authorization are deferred. Seal existence proves content identity only. Owner/superuser bypass, independent archive retention and backups remain operational concerns. Deferred rechecks can repeat work for large batches. Production throughput was not measured. No NASA data was inserted. M4.4 requires separate approval.
