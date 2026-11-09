# Scientific-variable immutability remediation

The preflight at revision 0004_m44_n1 demonstrated that an approved definition's version and unit basis could be updated under the same UUID. Protocol requirements include the scoped variable FK in the seal. The referenced definition is outside the protocol aggregate, so recomputing that seal could not detect the edit. M3 R6 relies on the referenced row being immutable. The new revision supplies that protection.

## Database changes

Alembic revision `0005_variable_immutability` follows M4.4. It contains four trigger functions and installs eight triggers. It leaves the domain schema, seal format, existing rows and historical revisions intact. It reuses the M4.3 immutable-row exception for UPDATE, DELETE and statement-level TRUNCATE. Protection begins at INSERT, including unreviewed and unreferenced definitions. ORM writes and direct SQL reach the same triggers.

Within a SERIALIZABLE transaction, insert a new UUID for the same investigation and variable_code. The database locks the investigation and requires version one for a new stream or the existing maximum plus one for a successor. The scoped unique key also excludes competing inserts at the same version. Existing gaps, if any, remain historical. A rejected or conflicting explicit version must be reconsidered from a fresh view. A successor must cite an evidence-reference ID outside all earlier definition and variable-review evidence in its stream. This proves distinct evidence identity. Scientific assessment of the content remains a reviewer responsibility.

The successor can exist pending review. Append a review targeting its exact UUID, starting its own revision chain. Approval evidence can cite the successor's supporting reference or another fresh reference. A predecessor UUID or approval cannot grant permission to use the new version. Inserting a requirement for a successor and sealing its protocol both require the highest review of that UUID to be approved and sealed. A deferred check also examines new protocol seals at transaction end. These checks cover successor identity and approval only. An existing protocol still points to the original UUID. Independent new protocol versions may explicitly select a different UUID.

Variable reviews were already append-only. The new evidence guard also rejects changes to a reference cited by a definition or any of its reviews. Registration and review lock their evidence rows. The evidence guard rejects REPEATABLE READ mutations on this table because an old snapshot may miss a concurrent registration. READ COMMITTED and SERIALIZABLE are available for edits to otherwise unpinned evidence. Artifact storage and independent scientific review remain outside this migration.

## Existing-data audit and historical limits

The effective FLARE settings had no persistent DATABASE_URL. Persistent row counts, reference counts and prior edits are therefore unknown. No persistent database was selected by guessing a host or port. The original preflight UPDATE ran on a disposable database.

The populated migration test audited a technical M4.4 variable and followed all four incoming foreign keys: semantic_annotation.variable_id, review_event.variable_id, condition_component.variable_id and protocol_requirement.variable_id. It captured its full row, evidence, approved review, requirement, protocol seal, recomputed digest and pinned N1 history before upgrading. These comparisons cover fields and identities, not timestamps as a proxy for history. The pre-upgrade technical row and the same records after successor registration and approval are compared directly.

A read-only inventory for a configured deployment can use:

```sql
SELECT v.investigation_id, v.id, v.variable_code, v.definition_version, v.evidence_id,
       (SELECT count(*) FROM semantic_annotation a WHERE (a.investigation_id,a.variable_id)=(v.investigation_id,v.id)) AS annotations,
       (SELECT count(*) FROM review_event r WHERE (r.investigation_id,r.variable_id)=(v.investigation_id,v.id)) AS reviews,
       (SELECT count(*) FROM condition_component c WHERE (c.investigation_id,c.variable_id)=(v.investigation_id,v.id)) AS components,
       (SELECT count(*) FROM protocol_requirement q WHERE (q.investigation_id,q.variable_id)=(v.investigation_id,v.id)) AS requirements
FROM scientific_variable v ORDER BY v.investigation_id,v.variable_code,v.definition_version;
```

This query describes present state. A prior in-place edit may leave the same protocol digest and no previous definition row. Historical comparison requires independent evidence such as dated backups or retained database audit logs. Installing triggers cannot reconstruct that history. Upgrade performs no data repair or reclassification.

## Migration operation

Upgrade installs enforcement transactionally and takes PostgreSQL DDL locks on the affected tables. Concurrent writers may wait. Existing definition registrations and protocol seals are preserved. The forward migration requires no domain data conversion and does not retroactively certify legacy successors. Downgrade refuses by default. The explicit Alembic option `-x confirm_destructive_downgrade=yes` or the existing programmatic confirmation enables removal of these triggers and functions in dependency order. Domain rows and the earlier sealing/N1 protections survive. Variable edits would again be possible during a downgrade interval. Re-upgrade restores prospective enforcement. Database owners that disable triggers or alter the schema can bypass ordinary DML protections.

## Change inventory

- Created `backend/migrations/versions/0005_variable_immutability.py`.
- Created `backend/tests/test_variable_immutability.py`.
- Updated `backend/tests/test_migrations.py` for the new head and revision count.
- Created `docs/implementation/m4_5_variable_immutability_remediation.md`.

The scope ends at R6 remediation. The N2 matcher remains pending independent review and explicit approval.

## Executed verification

From `backend`:

```powershell
& .venv/Scripts/python.exe -m pytest -c pyproject.toml tests -q --run-postgres '--pg-bin=C:/Program Files/PostgreSQL/17/bin' --tb=short
```

**182 passed, 0 failed, 1 warning in 79.90 seconds** on disposable PostgreSQL 17.11. The warning is the existing Starlette/httpx TestClient deprecation.

| Suite | Passed |
|---|---:|
| Existing API and parser | 40 |
| M4.1 | 34 |
| M4.2 | 16 |
| M4.3 | 27 |
| M4.4 | 52 |
| New variable remediation cases | 13 |

The eight parameterized direct SQL cases rejected edits to version, basis and description and rejected deletion before and after approval. Additional cases verified unreferenced deletion and truncation protection, ORM rollback and retrieval, fresh supporting evidence, skipped-version rejection, atomic rollback and two competing version registrations. Only one competing registration committed. The populated M4.4 upgrade test verified default downgrade refusal, confirmed downgrade, re-upgrade, original field/approval/evidence equality, exact old requirement UUID, original seal ID and stored/recomputed digest equality, and identical pinned N1 output. The new protocol's successor requirement was rejected until a fresh exact-version approval was sealed.

An independent read-only comparison checked the ordered headers, raw strings, classifications and quality flags against the preserved JSONL for all 129 records x 17 fields. All 2,193 matched. The three original SHA-256 values matched their acquisition hashes:

| File | SHA-256 |
|---|---|
| PSI-25_Experimental table_BASS-II.csv | 71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042 |
| BASS-II data FAQ.docx | 69f32647792f54ab2a561e3cdafc6c87d854564fe487aed2b09265286bd84e1d |
| BASS-II Test Matrix by PI Final.xlsx | 1a3b283dd0adec861793bbc4a454aab64d398cd32d6f37d7a1ad0f642879e686 |
