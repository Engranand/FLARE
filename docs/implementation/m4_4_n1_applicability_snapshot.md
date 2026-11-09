# M4.4 N1 applicability snapshots

## Inspection

The M3.4 approval, M3.3 remediation, five design deliverables, M4.1–M4.3 reports, 33 mappings, migrations, sealing SQL and PostgreSQL fixtures agree on the representation. M4.3 verifies row shapes and freezes all dependency columns. Its technical graph intentionally seals a scope_link belonging to a link review, a shape that M4.4 must reject on semantic grounds. Historical schema tests therefore stay at their explicit revisions. M4.3 protects review/observation aggregates but does not freeze test_source_record or data_quality_issue rows. N1 must protect those referenced identities for historical explanations.

## Database contract

The migration adds no domain tables or columns. An approved result ReviewEvent supplies the snapshot identity, revision, predecessor, policy identity-issue-snapshot-v1 and zero-unresolved attestation. ApprovalDependency holds the membership. AggregateSeal pins the canonical-json-v2 digest and member counts. The snapshot is constructed at approval in the transaction that will eventually publish. Publication itself is deferred.

| Set | Derivation and persistent representation |
|---|---|
| O | Union the observation IDs reached through all result input annotations and all non-null annotations on components of selected conditions, including extra components. Store one scope_observation marker per distinct observation, including those with zero issues. |
| L(o) | Enumerate every link for the observation's scoped source record. Store one scope_link per observation and link. Pin the greatest review revision, including a negative or unsealed head, and the seal for that exact review when present. NULL records the corresponding absence. |
| T(o) | The immutable link fixes its source record and experimental test. Include its test only when its captured head is approved and sealed. Store one applicability_identity decision dependency per distinct effective head. |
| Q(o) | Union observation-target issues with issues for every test in T(o), across all segments and severities. Store one scope_issue per observation and issue, pinning its greatest review revision and that review's exact seal, including absences. A shared whole-test issue appears once for each applicable observation. Its ordinary clearance edge occurs once per distinct sealed resolved head. |

Each selected input must use an effective link for its annotation observation, exact pinned review and segment's test. A known component must have an effective source-row link to its condition's test, pinned by the selected condition review. The result and selected conditions have content seals. An unknown component with no annotation contributes no observation. The zero-unresolved claim holds only when every review/blocking issue has a sealed resolved head. Info issues still enter membership. Scope rows can record negative decisions without adding an approval edge.

The validator uses EXCEPT ALL in both directions on kind, role, observation, link, issue, review, seal and ordinary N1 dependency IDs. It independently checks selected identities and unresolved issues. The existing unique indexes, row shapes and investigation-scoped FKs remain active. Physical member UUIDs and creation times are excluded from the semantic comparison. They remain covered by the M4.3 seal.

## Use

Within a replayable SERIALIZABLE transaction, prepare the exact result and condition content seals. Insert the approved result review and its ordinary dependencies, then call flare_n1.build(investigation, review, seal_id, actor). The function appends the derived entries and seals the existing review aggregate through flare_sealing.seal. A result approval cannot commit without a matching seal and complete N1 dependencies. For an already sealed review, repeating build returns its original seal only if applicability still matches. Revalidation creates a successor result review and seal. An unchanged result can keep its content seal.

flare_n1.historical(investigation, review, seal_id) returns only evidence anchored to that exact pair. It follows stored IDs to immutable links, issue targets and reviews. The output includes revision, predecessor, policy, attestation, digest, member identity, associated/effective test, severity, decision and pinned seal. Missing heads stay NULL. An empty membership yields an attestation row with NULL member identity. A mismatched owner/seal pair yields no rows.

flare_n1.applicability_current(investigation, review) requires an existing review seal, derives fresh O/L/T/Q, compares the exact N1 edges and rechecks required clearances and selected identities. The Python applicability_current entry point opens a fresh SERIALIZABLE transaction and returns after commit. This predicate evaluates the N1 component of future consumption permission. Currency of the overall result approval, unrelated ordinary approval chains, N2, publication selection and reader authorization belong to their respective later gates.

## Transactions and enforcement

N1-affecting inserts lock the investigation first. Review inserts then lock their link, issue or result subject, enforce highest revision plus one and require the exact predecessor. Review sealing and member inserts reuse M4.3 parent locks. The review-seal range read by writers complements the reads of links, issues and heads during certification, allowing SERIALIZABLE to detect stale overlapping snapshots. Tests observe the actual lock wait before releasing the leader.

Use the M4.3 run_aggregate_transaction wrapper to retry the complete operation, including commit, on SQLSTATE 40001. append_head calculates the revision and predecessor in that transaction. If another append wins a revision or predecessor unique index, the controlled function translates those specific conflicts into 40001. Other unique violations retain their original errors. A direct SQL client can still receive 23505 for competing inserts. An inconsistent revision, snapshot or clearance fails with 23514.

Deferred triggers validate each new approval and review seal against the final transaction view. When certification fires early through SET CONSTRAINTS, it takes a transaction-level shared advisory lock marking the newly certified seal tuple. Later mutation checks examine only those markers held by their own backend. The two integer lock keys identify the seal's block and offset (the second key uses the reserved 1444000000 offset base). The tuple is immovable under the transaction's relation locks. The marker expires at transaction end and never supplies historical identity, membership or decision evidence. This permits later transactions to reopen issues or append reviews without revalidating old snapshots. Ordinary callers should reserve that advisory-key range for N1.

| SQL function | Purpose |
|---|---|
| facts | Derive O, candidate links with exact heads/seals, effective tests and issues |
| expected, stored | Project derived and persisted semantic tuples into comparable shapes |
| matches | Validate both set differences, selected identity paths and clearances |
| historical, applicability_current | Read pinned evidence or evaluate fresh N1 applicability |
| append_head | Append a link, issue or result review against its exact predecessor |
| build | Insert N1 facts/decision edges and create the review seal |
| lock_write, check_owner | Serialize relevant writes, enforce review lineage and scope ownership |
| certify, recheck_new | Check new approvals and review seals, including later same-transaction mutations |

| Trigger family | Tables and event |
|---|---|
| n1_immutable, n1_truncate | Before update/delete or truncate on test_source_record, data_quality_issue, analytical_eligibility, condition_segment and experimental_test. These protect the identities traversed by N1. |
| n1_lock | Before insert on test_source_record, data_quality_issue, review_event and analytical_eligibility |
| n1_owner | Before an approval_dependency insert |
| n1_certify, n1_result_final | Deferred after aggregate_seal or review_event insert |
| n1_mutation_final | Deferred after link, issue, review or seal insert |

## Migration and limitations

Revision 0004_m44_n1 follows 0003_m43_sealing and ships with m44_n1.sql. Upgrade locks the relevant preflight tables, checks existing N1 subject review streams and installs the flare_n1 function schema and triggers. Pre-N1 result approvals or snapshot-shaped evidence cannot establish historical completeness from the earlier transaction. Upgrade therefore rejects such data for explicit provenance review. It neither adopts those rows nor rewrites history. Downgrade requires the existing explicit confirmation, preserves domain data and removes the added triggers and functions in dependency order. A later reinstall with retained approvals encounters the same provenance preflight. The disposable migration test verifies upgrade, refusal, confirmed downgrade, re-upgrade and a clean Alembic metadata check on the empty baseline.

The approved four entry shapes and six sealing aggregates are unchanged. Implementation choices include a scoped append helper and a transaction-local certification marker for early constraint evaluation. N1 currently re-enumerates scope during validation. Production throughput has not been benchmarked. A future publication operation must bind its exact result review and review seal and run its own final validation inside the publishing transaction. Application-role grants and authentication remain deferred. An owner who disables database triggers is outside these guarantees.

## Acceptance evidence

Technical fixture data only. The valid fixture has two observations, including one reached only through an extra selected condition component, seven candidate link facts, and both effective and ineffective links. Expected memberships are checked by identity. The first observation has multiple issues and the second initially has zero. A separate shared whole-test issue produces two scope facts and one clearance edge.

Forgery tests submit manually altered dependencies to the existing M4.3 sealer and attempt to commit. They cover missing/extra O, L and Q rows, ineffective test-derived issues, wrong source rows, swapped heads/seals, missing seals, invalid ordinary edges, duplicates, wrong owner/kind and revoked selected identities. Negative selected-input and component tests exercise cross-test and wrong-condition selection. Unreviewed, open or unsealed review/blocking issues reject approval.

Fresh reads after adding a link, approving a non-selected link, revoking it, advancing a head, sealing a formerly unsealed head, creating an issue, reopening it or resolving it under a successor all deny the old snapshot. Historical output, including dependency identities, absences and digest, stays identical. A successor approval can regain current applicability for unchanged result contents. Changes outside the scope preserve a valid snapshot.

Concurrency cases use separate writers and an observer of pg_blocking_pids. Both commit orders are exercised against link insertion, link approval, review sealing, issue creation, reopening and resolution. The suite also races two head advances and tests same-transaction changes with deferred and early constraint evaluation.

The read-only source comparison matched all 129 CSV records and 17 fields against their exact JSONL strings (2,193 values). Original CSV SHA-256 was 71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042.

## Files

Created the 0004_m44_n1.py migration and m44_n1.sql asset in backend/migrations/versions, backend/app/db/applicability.py, backend/tests/test_n1_snapshot.py and this report. Updated backend/tests/test_migrations.py for the new head and backend/tests/test_aggregate_sealing.py to test its historical revision and share a technical fixture with a valid N1 mode. M4.1–M4.3 revisions and their SQL assets retain their original bytes.

## Final run

From backend, using the fixture-owned PostgreSQL 17.11 cluster:

```powershell
& .venv/Scripts/python.exe -m pytest -c pyproject.toml tests -q --run-postgres '--pg-bin=C:/Program Files/PostgreSQL/17/bin' --tb=short
```

**169 passed, 0 failed, 1 warning in 57.29 seconds.** The warning is the existing Starlette/httpx TestClient deprecation.

| Group | Passed |
|---|---:|
| API | 9 |
| CSV parser | 31 |
| M4.1 infrastructure, configuration, migrations and PostgreSQL | 34 |
| M4.2 models and schema | 16 |
| M4.3 sealing | 27 |
| M4.4 N1 | 52 |

All twelve snapshot-versus-mutation race cases passed, as did the separate two-head race. An earlier run exposed a unique-index race between writers choosing the same next subject revision. The controlled append function now maps that verified append collision to 40001 and the existing retry wrapper replays from a fresh snapshot. The final test verified that the second writer names the first committed review as its predecessor. The mixed-pin regression verified that one valid selected component identity cannot mask another incompatible selected identity.

The implementation adds twelve SQL functions and twenty-one trigger instances. No domain schema change or deviation from the approved N1 sets was required. Work stopped at M4.4.
