# M3 final review gate

## A. Executive verdict

**NOT APPROVED**

The raw/semantic separation is sound and the design can represent BASS-II, but publication-set immutability and complete historical approval lineage are not sufficiently specified to authorize M4 implementation. This verdict is about architecture readiness, not the scientific validity of the NASA measurements. No Critical finding was established; four High, two Medium and one Low findings are listed below. Deferred triggers are a legitimate design technique: their absence from this design-only repository is not itself a defect. The blocking findings concern missing or ambiguous invariants beyond the already documented future gates.

Only this report was created. No SQL was executed, no database connected, no packages installed, and no other architecture, application, parser or data file changed.

## B–C. Findings and required corrections

### R1 — High — Append-only rows do not freeze published aggregate membership

**Affected:** `postgresql_schema_proposal.md`, sections `parse_run`, `source_record`, `observation`, `result_input`, `result_condition`, `result_evidence`, and “Mandatory transaction checks beyond ordinary FKs”; `data_lifecycle.md`, “Source revisions and repeated processing” and “Eligibility, withdrawal and result reproducibility”.

**Counterexample:** after a result is approved, insert another otherwise-valid result_input with a different input_role, or another result_evidence. No historical row is updated; PK/FK/UNIQUE constraints and the stated minimum-input publication rule still pass. The old result now appears to have used a different input set. Similarly a completed ParseRun can acquire additional fields/rows/cells unless the digest/count gate is explicitly rerun on every child insertion or the aggregate is sealed. The documents promise immutable completed outputs but define neither a sealing record nor a prohibition on post-publication child insertion. AnnotationEvidence also needs a defined evidence-set boundary for an approved interpretation.

**Correction:** specify atomic publication/sealing, exact member-set digest/count and an immutable publication identity. Reject all later child attachments to a sealed version; new membership creates a new version. Explicitly distinguish unsealed drafts from published records and define whether evidence additions are a new annotation revision or a separately reviewed supplement. Cover all member tables, not just UPDATE/DELETE guards. **Blocks M4: yes.**

### R2 — High — Condition provenance does not pin all historical review/identity dependencies

**Affected:** schema sections `experimental_condition`, `analytical_eligibility`, `result_condition`, “Conditions” and “Revocation propagation”; architecture “Traceability chain”; lifecycle “Eligibility, withdrawal and result reproducibility”.

Conditions pin component annotation IDs, but not each component's approving ReviewEvent or the TestSourceRecord/link review proving membership in that test. ResultInput pins such identity evidence only for its own input annotation; a condition component need not be a ResultInput. A condition can therefore be approved while a component is associated with test A, then the association can be revoked/replaced, without a preserved explicit record of which association/review was consumed by that condition approval. created_at/reviewed_at are not a transaction visibility snapshot and cannot reliably reconstruct concurrent approval dependencies. ScientificVariable reviews are also targetable in ReviewEvent but their approval/revocation effect on dependent annotations is not defined.

**Correction:** pin the complete dependency decision set at approval/publication, including component annotation approvals and identity-link approvals. Define whether variable-definition approval is mandatory and how its revocation propagates. Specify transitive stale-result evaluation over those exact dependencies, while keeping historical snapshots reproducible. **Blocks M4: yes.**

### R3 — High — Protocol requirements are an unspecified integrity language

**Affected:** schema `analysis_protocol.requirements`, `experimental_condition.extension_metadata`, and transaction gates “Eligibility” / “Result publication”; ADR-09, ADR-11, ADR-15.

A JSON object check does not define required-variable identity, definition versions, units/bases, phase rules, stable-flow evidence, applicability of test-level issues to observations, or mandatory condition coverage. In particular, the text says required result_condition decisions must match the result protocol and condition/test, but does not explicitly require each protocol-required input test/segment to have a matching condition decision. An eligible unrelated test's condition must not satisfy that gate. These are central scientific rules, not optional metadata details. The proposed requirements schema/version is not yet specified.

**Correction:** define a bounded, non-executable protocol schema, rejecting unknown/invalid keys. Represent integrity-bearing variable/definition dependencies relationally or through an explicit constrained mechanism consistent with the no-hidden-FK policy. Specify input-test/segment-to-condition coverage and issue applicability. Fail closed for unknown requirements, missing components, incompatible units and unresolved scope. No scientific defaults may be supplied by an implementation heuristic. **Blocks M4: yes.**

### R4 — High — The publication authorization boundary is not unambiguous

**Affected:** schema “Result publication”, `analytical_result`, `review_event`, and “Immutability enforcement proposal”; architecture “Immutability, review and reversibility”.

The proposal mentions publication, insertion, result-review approval and current-use results but does not define a single publication event/state or the exact reader-facing predicate. It says result approval is denied until gates pass; that does not explicitly require an approved result review before consumers can use a result. It is also unclear whether revoking a result review itself removes the result from current use (the revocation gate enumerates upstream decisions). Without a fixed boundary, two otherwise conforming implementations could expose different sets of results.

**Correction:** define the publication event and mandatory approving review, the only authorized analytical read surface, and a precise current-use predicate including result-level rejection/revocation. State grants that prevent consumers from mistaking draft/base rows for approved outputs. Align this with the seal in R1. **Blocks M4: yes.**

### R5 — Medium — Seven single-valued condition roles limit extensibility

**Affected:** schema `experimental_condition`; architecture “Condition-aware comparison” / “Multi-investigation support and JSONB boundary”; ADR-09/15.

The design correctly disclaims universal BASS-II assumptions. Nevertheless, one oxygen, fan and radiometer reference per condition cannot directly represent multiple instruments/species or multiple simultaneous measurements of a role. Arbitrary segment_key strings and JSON extensions should not become a workaround that loses instrument identity or evidence. This is a documented extension boundary, not evidence that any named future NASA investigation actually has that shape.

**Correction:** define the typed extension strategy and scope/instrument identity contract before claiming general multi-investigation condition coverage. A small controlled component relation or reviewed investigation-specific typed tables are possible alternatives. **Blocks M4:** no for explicitly BASS-II-only implementation after High findings close; yes before onboarding an investigation requiring these structures.

### R6 — Medium — Immutable metadata corrections lack an explicit route

**Affected:** schema `investigation`, `source_document.source_version`, `scientific_variable`; lifecycle “Source revisions and repeated processing”; ADR-03/07.

All tables are declared append-only, but unique repository/code and investigation/hash identities prohibit simply creating a corrected replacement row for an investigation name/description or a previously unknown artifact source_version. Acquisition metadata could hold later assertions, but precedence and the authoritative read rule are not stated. Do not fix this by granting UPDATE to immutable source registration tables.

**Correction:** specify immutable registration snapshots plus evidence-backed metadata assertion revisions and effective-read rules, or explicitly designate these fields as first-registration facts whose corrections are separately discoverable. **Blocks M4:** yes for a complete persistence contract; can be closed with a documented policy without adding a large metadata subsystem.

### R7 — Low — ER intentionally omits relationships without a sufficiently explicit legend

**Affected:** `scientific_data_model.mmd`, experimental_condition attributes and material_annotation relationship; schema “Shared conventions”.

All 23 entities appear. Shown mandatory/optional parent cardinalities agree with FK nullability. However six condition-annotation relationships and self-predecessor relationships are omitted; all seven annotation FK attributes are listed while only material_annotation is drawn. XOR target constraints cannot be inferred from optional links alone. No incorrect drawn cardinality was found; this is a completeness/readability issue.

**Correction:** label collapsed/omitted relationships and XOR semantics explicitly, or add a companion detail diagram. Do not claim the 64 drawn edges enumerate all 94 FK declarations. **Blocks M4: no.**

## D. Scientific and relational integrity assessment

### What passes

The 23 schema CREATE TABLE declarations match the 23 Mermaid entities and architecture inventory. Referenced tables and referenced PK/UNIQUE column sets were checked statically. Scoped composite keys prevent accidental cross-investigation joining; same-run row/field FKs are present. Test identity uniqueness uses namespace and full test_identifier, not sample ID. No uniqueness constraint forces merging suffixes or reused samples. Actual namespace assignment still requires review across revisions.

Unscaled numeric is appropriate for these decimal measurements without imposing rounding; exact lexical precision/trailing zeroes remain in raw text. UUIDs suit surrogate identities, text preserves source identifiers, dates are distinct from audit timestamptz. Non-finite interpreted numbers are rejected. Nullable interpreted fields have value-kind checks; a CSV empty string stays non-null text while an XLSX absent cell can be SQL null. Unknown unit status is not an assumed physical unit. JSONB locators and source representation are reasonable bounded uses; R3 addresses the scientific integrity rules that cannot remain an unspecified object.

Read-only comparison confirmed 129 parsed CSV records, 17 exact headers and all 2,193 raw strings against the source CSV. Existing workbook evidence records six sheets and 129 mappings. The model can retain their distinct representations without replacing CSV strings. FAQ saved page/paragraph basis is explicitly represented; it must not be called freshly rendered pagination.

| Source case | Assessment |
| --- | --- |
| Empty versus none versus zero | Distinct source tokens; missing observation rows must never be dropped |
| 13 negative Initial CO values | Preserved; numeric interpretation is not evidence of zero offsets or validity |
| OR | Raw ambiguous_token remains; optional >1000 ppm semantic bound needs FAQ p. 2 paragraph 25 evidence; never point 1000/1001 |
| over | Independent meaning remains unresolved; must not inherit OR threshold |
| >500 and <1 | Separate comparator/bound annotations permitted; no forced numeric point |
| Compound Fan/Air settings | Full strings retained; no automatic average, timestamp series or voltage-to-speed inference |
| Radiometer gain | Instrument configuration, not calibrated flame intensity; FAQ p. 2 paragraph 21 |
| Unusual final O2 | B2, P22a/b, T28a/b retained with unresolved issues; no assumed second calibration |
| Conflicting dates/GMT | 2018 strings retained; no timestamp or year repair from a video-day offset |
| Samples and a/b suffixes | Complete IDs retained; same-sample relations do not imply independent replicates |

Scientific authority: [field reconciliation](../bass_ii_field_reconciliation.md), [anomaly investigation](../bass_ii_anomaly_investigation.md), [all-record mapping](../bass_ii_test_matrix_mapping.md), [suitability assessment](../bass_ii_analytical_suitability.md). These findings establish representability, not measurement validation or blanket eligibility.

### Provenance trace

Conceptual existing example: CSV O4 row 52 Final CO → hash-pinned SourceDocument → ParseRun (code/config/output identity) → SourceRecord row evidence → Observation with exact header/cell evidence and raw OR → SemanticAnnotation with method/version, bound >1000 ppm and FAQ saved p. 2 paragraph 25 → ResultInput with exact annotation/eligibility/link review → future AnalyticalResult under the same AnalysisProtocol.

Every basic link has an FK/evidence representation. A new source hash cannot overwrite that chain. R1–R4 identify missing aggregate and decision-snapshot guarantees around it; a structurally linked chain is not yet a frozen publication. ReviewEvent revision order, rather than timestamps, is correctly proposed, but dependent approvals need explicit pins rather than historical inference from clocks.

### Conceptual workflow stress tests

| Question | Review result / required mechanism |
| --- | --- |
| Can normal application users rewrite/delete raw rows? | Intended no: separate owner, revoked UPDATE/DELETE/TRUNCATE/DDL, mutation triggers and procedure-only writes. Not deployed. Ensure inherited/public privileges and trigger-disabling rights cannot bypass it. |
| Can corrections retain originals? | Yes for new source hashes, parse runs, annotations and decisions; metadata policy needs R6. |
| Can annotation/eligibility be withdrawn? | Yes via same-subject successor review/eligibility events; exact-target and current-head checks require procedures/deferred triggers. |
| Can an old result be reconstructed? | Values are pinned, but member sets and full condition approval snapshots need R1/R2. |
| Can reviewers conflict? | Local revision/predecessor uniqueness helps; same-stream checks, first-event locks, serializable transactions and complete transaction retries remain necessary. Different candidate test links require shared source-record locking. |
| Can owners/superusers bypass guards? | Yes; explicitly acknowledged. External storage retention, independent backups/hash audits and restricted operational identities are required. |
| Are cross-row checks implementable? | Yes in principle with deferred triggers/procedures, provided all affected writes and publication transitions are covered. Ordinary CHECK constraints alone cannot implement them. R1–R4 must first define their precise predicates. |

No generic EAV interpretation forces unrelated investigations into common physical units. Investigation-local variable definitions, phases, source types and namespaces support audited expansion. R5 limits the current condition projection. No source schema for Saffire/FLEX/ACME/SAME was presumed or verified in this review.

## E. M4 implementation readiness and mandatory tests

PostgreSQL, SQLAlchemy 2.x, Alembic, FastAPI and Pydantic can support this design after corrections. Composite scoped relationships must use table-level ForeignKeyConstraint, not two unrelated scalar ForeignKeys. Shared investigation_id across multiple relationships requires explicit ORM join/write ownership; do not silence conflicting relationship warnings without solving them. UUID, Numeric(asdecimal=True), Date, timezone-aware timestamps, JSONB, named CHECK/UNIQUE constraints and indexes are ordinary model metadata. See [SQLAlchemy constraints](https://docs.sqlalchemy.org/en/20/core/constraints.html) and [overlapping foreign keys](https://docs.sqlalchemy.org/en/20/orm/join_conditions.html).

Use reviewed custom migration SQL for trigger functions, deferred constraint triggers, publication procedures, role grants/revokes and security-sensitive read surfaces. Alembic autogeneration produces candidate migrations, not proof of complete integrity enforcement; review all custom objects and CHECK changes explicitly. [Alembic autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html). FastAPI/Pydantic validation supplements, not replaces, database enforcement; preserve raw strings and Decimal precision in request/response serialization. No components were installed or implemented here.

Before ingestion, require the following database tests in a newly authorized disposable PostgreSQL environment (not run in this review):

1. Apply/review migrations on empty database; inspect all scoped PK/FK/UNIQUE/CHECK definitions, indexes, functions, triggers and grants. Verify FK names/columns and no unintended cascade.
2. Reject cross-investigation references, cross-run row/field pairs, mismatched table_key and evidence document/coordinates. Accept identical test names in separate investigations/namespaces.
3. Round-trip exact 17 headers and 2,193 source strings; preserve spaces, quotes, empty, none, zero, negatives, OR/over/bounds and full sequences. Compare hashes and source-row IDs; no real ingestion before gate approval.
4. Reject invalid point/bound/date/text combinations, non-finite interpreted numbers, unjustified unit origins and invalid locator shapes. Preserve decimal precision; reject unsupported raw input without silently stripping characters.
5. Verify failed/partial parse publication rollback, idempotent same-hash retry and distinct new parser/source revisions. Validate complete row/field/cell counts and digest; reject post-seal additions (R1).
6. Try UPDATE, DELETE, TRUNCATE, FK-parent deletion, direct INSERT around procedures, trigger disabling and schema DDL as every application role. Confirm denial. Verify owner/superuser exception separately and audit it rather than claiming invulnerability.
7. Reject skipped revisions, wrong-subject predecessors, cycles, forked successors and duplicate first events. Two concurrent reviewers must yield one accepted head plus a rejected/retried conflicting transaction, never silent overwrite.
8. Race approval of two test links for the same row; enforce one current association. Test symmetric relationships, suffix preservation and repeated samples without deduplication.
9. Reject known conditions backed by missing/unresolved or wrong-category annotations, wrong-test components, unsupported stable airflow and unmatched input-test/segment condition coverage. Unknown must not equal unknown for comparison.
10. Reject eligibility with wrong protocol/version, annotation/condition/approval target, stale approval, unresolved blocking issues or invalid requirements. Absent decisions fail closed. No automatic child eligibility from test approval.
11. Publish only complete sealed results with all required exact input/condition/evidence/decision dependencies. Reject foreign protocol inputs, unrelated condition decisions, drafts and unapproved/revoked result reviews (R1–R4).
12. Race withdrawal, issue reopening or link revocation against publication under SERIALIZABLE; retry the whole failed transaction. Validate current-use and historical as-of results after each transitive dependency change. [PostgreSQL consistency guidance](https://www.postgresql.org/docs/18/applevel-consistency.html).
13. Add/revoke variable-definition and component approvals; verify the pinned dependency policy from R2. New approval must not silently reinterpret an old published result.
14. Restore database plus archived source/code/config/output artifacts; reproduce a historical result's exact sealed dependency set and verify all hashes. Check corrupted/missing artifacts fail verification.
15. Validate protocol/locator schema versions, authorization identity and denial of forged reviewer_ref. Ensure current-use readers cannot bypass review projections via base-table grants.

## F. Gate conditions and validation limits

M4 is not authorized by this review. Close R1–R4 and R6 in a separately authorized architecture revision, reconcile the five design files, and repeat this gate. Define R5's scope boundary and address R7's legend before implementation planning. Then authorize an integrity-first M4 with the tests above as prerequisites to source ingestion; merely creating ORM tables is insufficient.

This review performed static DDL/ER inventory and referenced-key checks, source-to-JSONL equality checks and conceptual adversarial workflow review. It did not run PostgreSQL, execute any SQL, render/reparse Mermaid with an installed library, or rerun backend tests. Earlier Mermaid/40-test successes are historical only. Therefore no database-enforcement or concurrency test is claimed. Existing files were hash-checked for preservation during report creation.
