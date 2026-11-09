# M3.4 final independent architecture review

Review date: 2026-11-06. Scope: readiness of the M3.3 design for BASS-II PostgreSQL implementation.

## A. Executive verdict

**APPROVED — M3 architecture is ready for the bounded M4 implementation scope in section H.**

N1 and N2 are resolved at design level. R1–R7 remain resolved within the stated BASS-II boundary. No new Critical or High design blocker was identified. The five deliverables agree on the applicability snapshot, condition-policy matcher, publication lifecycle and 33-entity/140-FK model.

This verdict follows reconstruction of the earlier failure scenarios, adversarial examination of the revised rules and inspection of their relational representation. It is not based only on matching entity counts or on the remediation log's status labels. The new rules specify both positive paths and rejection paths without requiring an implementer to invent an applicability scope or a condition waiver.

**Approval is for architecture implementation, not for tested database enforcement, real source ingestion, production deployment or scientific validation.** Section G's database acceptance tests must pass before real source ingestion. No SQL, database connection, migration, ORM implementation or application/source modification occurred in this review. Only this report was created. Earlier NOT APPROVED reports remain unchanged historical assessments of earlier designs.

Reviewed: all five architecture deliverables; both prior reviews; both remediation logs; BASS-II source reconciliation, current dictionary, anomaly/mapping evidence, saved FAQ extraction, parser documentation and the existing CSV ingestion modules. Read-only checks independently compared the original CSV with existing JSONL and inspected workbook worksheet metadata. No separate human reviewer or executed database test is implied by this documentary reassessment.

## B. N1 and N2 independent reassessment

### N1 — RESOLVED

The [normative N1 contract](postgresql_schema_proposal.md#n1--publication-time-applicability-snapshot) now defines the publication-time sets precisely:

- O includes every input observation and every non-null annotation observation in selected condition components, including extra components.
- L(o) includes every candidate link for that observation's source row, not merely the selected or currently approved link.
- Each link records its exact highest review and that head's seal, including explicit absence. The immutable link supplies its test identity. Only a sealed-approved head contributes its test to T(o).
- Q(o) includes all observation issues plus all whole-test issues for T(o), without segment narrowing, across all severities and review states.
- Observation markers represent the scope even when Q(o) is empty. Exact membership comparison, the versioned zero-unresolved attestation and the sealed review identify the captured state without timestamp reconstruction.

The five new FKs and four entry shapes implement these distinctions in the existing ApprovalDependency relation. Scope facts do not falsely assert approval of unreviewed/rejected links or open info issues. Effective identity decisions and required issue clearances also become ordinary permission dependencies. Review/blocking issues need a sealed resolved head; info issues may remain unresolved but are still captured.

The result review's id/revision/predecessor and its AggregateSeal identify the snapshot. Its digest covers the attestation and all scope/decision rows. Historical reads follow only those frozen entries and immutable targets; they do not rediscover historical membership from current links or timestamps. This supports reconstruction of historical values, memberships and authorization rationale after withdrawal. It does not establish that no unknown external scientific issue existed.

| Counterexample attempted | Why the revised design prevents it |
| --- | --- |
| Omit a component observation that was not a ResultInput | O explicitly includes annotations in every selected condition's components; exact set equality rejects the omission. |
| Select link A and ignore approved non-selected link B | L(o) contains B; B contributes its test issues and its exact approved review becomes an ordinary dependency. |
| Treat no review as a later approval | NULL head and NULL seal are immutable snapshot facts. A later head or seal changes ApplicabilityCurrent's comparison. |
| Capture an unsealed head, then seal it without changing its ID | The separately captured seal pointer changes from NULL to an ID; current permission fails equality. |
| Substitute a review/seal for another link or issue | Scoped FKs establish existence; mandatory cross-target checks require the exact subject and head. FK existence alone is explicitly insufficient. |
| Hide an unresolved issue by omitting it or preserving only a plausible count | Two-way O/L/Q membership validation rejects omissions/extras; count=0 must be derived from every distinct applicable review/blocking issue. |
| Confuse zero issues with an unperformed scan | An explicit observation marker, complete empty Q(o), policy version, zero attestation and sealed membership represent the completed scan. |
| Reject a valid snapshot merely because an unrelated candidate link is revoked | An already-revoked candidate is a scope fact, not an approving edge. Its test is excluded from T(o); unchanged captured state can remain valid. A later state change requires revalidation. |
| Add a link, revoke a non-selected link, create/reopen an issue or change its head | Exact fresh semantic membership/head/seal equality fails. New info issues also require revalidation, though info severity alone does not require resolution. |
| Resolve a reopened issue and silently revive an old publication | Its head identity differs. A successor approval/snapshot and publish event are required; old historical entries remain unchanged. |
| Reapprove changed inputs under the old content seal | Only unchanged contents may reuse that seal. Changed members require a new result identity and content seal. |

Concurrency is specified at a workable design level: investigation-first write locking, ordered subordinate locks, SERIALIZABLE transactions, full retries and deferred validation of newly inserted publications. Waiting does not refresh a snapshot. A concurrent mutation may serialize after publication; a fresh consumption after the mutation commits must observe the change and reject the old snapshot. Same-transaction writes after snapshot assembly are covered by the deferred publication check. These guarantees require implementation tests; they are not inferred from locks alone.

**N1's previous ambiguity is closed:** historical explanation uses pinned facts; current permission recomputes and compares; revalidation creates a successor approval for unchanged contents and a successor result identity for changed contents.

### N2 — RESOLVED

The [N2 contract](postgresql_schema_proposal.md#n2--complete-condition-policy-truth-table) uses the actual SQL enums. The six pairs occur exactly once in both schema and remediation tables. Independently expanding condition-role presence gives these 12 outcomes:

| Case | Condition-role requirements | Instrument policy | Stability policy | Empty ResultCondition allowed? |
| --- | --- | --- | --- | --- |
| 1 | Absent | not_required | not_applicable | Yes, if every input is waived and all other gates pass |
| 2 | Absent | identified_required | not_applicable | No |
| 3 | Absent | not_required | transient_allowed | No |
| 4 | Absent | identified_required | transient_allowed | No |
| 5 | Absent | not_required | stable_required | No |
| 6 | Absent | identified_required | stable_required | No |
| 7 | Present | not_required | not_applicable | No |
| 8 | Present | identified_required | not_applicable | No |
| 9 | Present | not_required | transient_allowed | No |
| 10 | Present | identified_required | transient_allowed | No |
| 11 | Present | not_required | stable_required | No |
| 12 | Present | identified_required | stable_required | No |

An active input policy requires a known component for the exact input annotation and variable version, selected through an approved/eligible ResultCondition for the same linked test and exact segment. It must match phase/unit/basis/method rules. One component must support both active policies; an implementer cannot combine instrument identity from one candidate with unrelated scope evidence from another.

identified_required needs an identified instrument and its FK. stable_required needs supported stable scope; transient_allowed accepts documented stable or transient scope, not unknown/not_applicable airflow. not_applicable waives the airflow check with protocol evidence. Unknown instrument is permissible only under not_required. Documented input segment scope remains mandatory even in case 1.

Mixed inputs cannot inherit the waiver from one input: every input must be waived before the empty set is permitted. Explicit condition roles remain independently mandatory per input test/segment, including case 7. Their annotations need not equal unrelated input annotations. Evidence for one segment cannot satisfy another. Missing required components/evidence, wrong identities, NULL/unsupported policies and the literal non-enum value required all fail closed.

The schema's publication and CanConsume predicates explicitly invoke the same logical N2 matcher. Architecture, lifecycle and decisions repeat the same waived-pair outcome. No invented condition, instrument, timestamp or scientific default is needed to interpret the positive path. N2's contradictory empty-set rule is removed.

## C. R1–R7 status

| Finding | Status | Independent regression assessment |
| --- | --- | --- |
| R1 | RESOLVED | Parent-lock insert guards and seals cover all six aggregate memberships, including annotation evidence, nested protocol rules and expanded review entries. Counts/digests and new-version rules remain; initial result seal/approval/publication is atomic. |
| R2 | RESOLVED | Exact annotation, variable, identity, component, eligibility and result decisions remain pinned. N1 adds complete historical applicability membership without confusing historical negative heads with permission edges. |
| R3 | RESOLVED | Closed relational-v1 requirements preserve exact variables, units/methods, phases, coverage and issue policy. N2 defines the waiver/active-policy boundary. Unknown requirements cannot be interpreted heuristically. |
| R4 | RESOLVED | Mandatory sealed result approval and explicit publication remain required. CanConsume includes approval currency, eligibility, N2 and ApplicabilityCurrent. EXECUTE-only current reads and separate historical reads prevent ordinary base-table bypass. |
| R5 | RESOLVED for BASS-II scope | Typed roles, instruments, components and segments preserve multiplicity and unknowns. No structures of unaudited NASA investigations are asserted. Raw representability does not imply current analytical eligibility. |
| R6 | RESOLVED | Reviewed full-snapshot metadata revisions preserve registration facts; pending/withdrawn newest revisions do not silently fall back to old current metadata. Exact definition versions remain pinned. |
| R7 | RESOLVED | All 140 FKs are drawn, including five scope pointers and predecessors. Cardinalities match declarations. XOR/entry-shape distinctions are explicit, and solid/dotted relationship notation now distinguishes identifying FKs. |

No M3.3 change reopens the original post-seal attachment, missing condition approval or unapproved-result read counterexamples. The original and M3.2 reports remain valid historical records, not current contradictory design instructions.

## D. New findings and non-blocking limitations

**No new Critical or High blocker was established. No additional architecture remediation is required before beginning the bounded M4 implementation.**

The older M3.2 N3 documentation caveat remains: acquisition-era reconciliation/parser text and parser warnings still describe DOCX/XLSX as pending. Current files and the later dictionary establish their availability. This is a non-blocking historical-status labeling issue, not evidence of missing current files; do not use that old warning as current acquisition authority. No parser or historical documentation was edited here.

The former N4 line-style caveat is resolved in the current diagram. Static ER syntax and edge agreement were checked, but the diagram was not rendered or compiled with the official Mermaid parser. Visual layout verification remains a documentation handoff check, not proof of database integrity.

Implementation risks remain substantial but have explicit design requirements: full canonical serialization, exhaustive mutation paths, actor authentication, transaction retries, deferred check timing and least-privilege grants. Investigation-wide write locking is conservative and may limit throughput; that is acceptable for the initial BASS-II boundary. Relaxing it later requires a separate concurrency review. None of these is evidence that the unimplemented enforcement already works.

## E. Schema consistency audit

Independent extraction from the current schema document, rather than the remediation's inventory, found:

| Check | Result |
| --- | --- |
| Entity inventory | 33 distinct CREATE TABLE declarations, matching 33 diagram entities; no additional snapshot/approval entity was introduced. |
| Column contracts | Every documented column/type/nullability entry matches its illustrative declaration. |
| Foreign keys | 140 declarations, each with matching local/target types, arity and a declared PK/UNIQUE referenced tuple. Constraint names fit PostgreSQL's identifier length. |
| Investigation/run scope | Every FK carries investigation scope; root FKs reference investigation(id). Observation record/field references additionally carry parse-run identity. |
| Revision scope | Immutable target IDs pin exact rows. Same-subject, revision+1, head selection and cross-target rules still require the specified procedures/deferred checks, not merely FKs. |
| Delete behavior | All 140 FK declarations use ON DELETE RESTRICT; no cascade delete is declared. |
| Diagram | All 140 labeled edges map to FK declarations in order; parent nullability, child maximum cardinality and identifying/non-identifying line style agree. |
| Local XOR/shapes | Review has eight exclusive targets; seal has six; issues/eligibility have observation/test XOR; ordinary dependency has three exclusive targets; scope entries have distinct checked shapes. Seal-without-head is rejected locally. |
| Snapshot uniqueness | Three partial unique indexes enforce per-owner observation, observation/link and observation/issue membership. Target/head correctness and set completeness remain cross-row gates. |
| Attestation | Approved result reviews require both version and zero count; other decisions require both NULL. Allowed values are explicitly checked. A stored zero is not accepted without recomputation. |
| JSONB | Integrity-bearing applicability and protocol references are relational. JSONB retains representation/configuration/locator/uncertainty roles with closed-schema/no-hidden-ID requirements. An object CHECK alone does not enforce those contracts. |

The 33 responsibilities remain distinct: raw extraction, source evidence, experimental identity, semantic interpretation, typed conditions, review/eligibility, protocols, results, metadata correction, sealing and publication. Extending ApprovalDependency avoids a redundant snapshot structure. Content seals and publication events are not duplicates: one freezes members, the other grants/revokes permission. Stored segment keys/counts and redundant dependency pins require the documented equality checks.

No mandatory approval cycle was found. Definition/identity reviews can originate from source evidence; annotations depend on definitions/raw seals; conditions depend on annotation/identity reviews; eligibility follows them; result approval depends on its content seal and upstream decisions; its review seal freezes members before publication. Scope facts are not traversed as approval edges. Target validation prevents a scope head from masquerading as its owning result review.

All five current deliverables agree on the same normative contract and inventory. Older 23/94 and 33/135 counts occur in historical documents and do not imply a current mismatch.

## F. Scientific integrity assessment

Read-only standard-library CSV decoding matched every existing JSONL raw_value and the exact ordered original_headers arrays: **129 distinct Test # records, 17 headers, 2,193 strings**. No classifier rerun or writer command was needed. The parser trims a working classification copy but retains original raw strings; the writer's sequential-file limitation remains documented and must not be mistaken for a successful database publication.

Original workbook XML confirms six worksheets: Bhattacharjee, Ferkul, Miller, Olson, Fernandez-Pello and T'ien. Existing source evidence contains 129 record mappings. This review did not repeat every workbook cell reconciliation or freshly render the FAQ; semantic conclusions remain attributed to the [dictionary](../bass_ii_data_dictionary.md), [anomaly investigation](../bass_ii_anomaly_investigation.md) and [mapping evidence](../bass_ii_test_matrix_mapping.md).

| Case | Current verification and required preservation |
| --- | --- |
| Empty / none | 19 empty strings and 16 literal none strings remain distinct. CSV empty text must not be mapped to XLSX absent-cell NULL. |
| Negative CO | All 13 negative Initial CO strings remain; no cause or zero correction is inferred. |
| OR / over | Three OR tokens and one over remain distinct. The FAQ-supported OR bound is not a point measurement or an established definition of over. |
| Bounds | One exact >500 and one exact <1 remain, separately from embedded qualifiers in compound strings. |
| Compound settings | Exact sequences, spacing and qualifiers match the source; no average, conversion or time series is substituted. |
| Unusual O2 | B2=1.6, P22a=0.6, P22b=39.1, T28a=0.9 and T28b=40.4 remain raw final-O2 strings. |
| Conflicting dates | T9/T18 retain 6/24/2018. The later dictionary still identifies the unresolved worksheet-header conflict. |
| Samples/suffixes | Reused sample strings and complete a/b test identities remain. P22a/b share 200m and T28a/b share 144m without collapsing the tests or asserting independent replicates. |

Recomputed original-file hashes:

| File | SHA-256 |
| --- | --- |
| PSI-25_Experimental table_BASS-II.csv | 71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042 |
| BASS-II data FAQ.docx | 69f32647792f54ab2a561e3cdafc6c87d854564fe487aed2b09265286bd84e1d |
| BASS-II Test Matrix by PI Final.xlsx | 1a3b283dd0adec861793bbc4a454aab64d398cd32d6f37d7a1ad0f642879e686 |

Source agreement establishes preservation/corroboration, not measurement validation. Unknown instrument identity, calibration uncertainty, missing scope and unresolved anomaly meanings must remain unknown. Architecture approval does not make any real BASS-II record analytically eligible automatically.

## G. Database implementation test requirements

### Technical implementability

PostgreSQL can express the intended local constraints and cross-row gates. Immediate mutation/member guards and controlled procedures must take the documented locks; deferred constraint triggers must check final publication membership/attestations, including later writes in the same transaction. Historical publications must not prevent legitimate subsequent withdrawal. [PostgreSQL trigger documentation](https://www.postgresql.org/docs/current/sql-createtrigger.html).

SERIALIZABLE transactions require full retries and a fresh transaction for each consumption. A concurrent publication can serialize before withdrawal; subsequent fresh reads after withdrawal commits must deny current access. Do not return success before commit or assume a lock wait refreshed the snapshot. [PostgreSQL isolation](https://www.postgresql.org/docs/current/transaction-iso.html).

SQLAlchemy 2.x supports composite ForeignKeyConstraint and exact numeric mapping; resolve overlapping investigation_id relationship ownership explicitly. ORM callbacks cannot substitute for database guards. [SQLAlchemy constraints](https://docs.sqlalchemy.org/en/20/core/constraints.html). Alembic can deliver reviewed custom enforcement and grants, but autogeneration is only a candidate migration and will not establish the full integrity contract. [Alembic autogeneration](https://alembic.sqlalchemy.org/en/latest/autogenerate.html).

FastAPI should control authenticated actor context, transaction lifetime and failure propagation. Pydantic closed models must forbid extra fields and preserve exact source strings/decimal values. These supplement database enforcement. [FastAPI dependency lifecycle](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/), [Pydantic configuration](https://docs.pydantic.dev/latest/api/config/).

Custom functions/procedures are required for canonical digest/count generation, complete O/L/T/Q enumeration, head selection, cross-target validation, protocol matching, atomic publication/revalidation and current/historical reads. Role grants must deny base-table analytical reads, direct writes, DDL and trigger disabling to application identities. Security-definer routines need trusted search_path, revoked public execution and authenticated authorization checks. Owner/superuser bypass remains an operational risk, not a claimed impossibility.

### Mandatory acceptance suite before real source ingestion

These tests were **not executed**. Run them against a disposable PostgreSQL instance after implementation, using clearly labeled technical fixtures rather than invented NASA measurements. The detailed tests in [M3.3](m3_3_remediation_log.md) remain mandatory, supplemented by these regression groups:

1. **Catalog and scope:** inspect all 33 tables/140 FKs, partial indexes, XOR/checks, functions, triggers and grants. Reject cross-investigation, cross-run, wrong-table/evidence-locator and wrong-subject predecessor references.
2. **Aggregate membership:** attempt late inserts into every sealed child set, including scope facts and nested unit rules; race child insertion/sealing both ways. Require unchanged old members/digests and new parent versions for changed content.
3. **Canonical vectors:** verify canonical-json-v2 with independent expected bytes for NULL/empty, Unicode/control characters, decimals, tagged JSON numbers versus strings, ordering and head/seal absence. Reject changed counts, omitted members and unsupported versions.
4. **N1 completeness:** selected A/non-selected B links; all candidate states; missing/unsealed heads; extra condition observations; every severity; zero issues; deliberately omitted/extra memberships. Counts alone must never pass incomplete sets.
5. **N1 current/history:** add links/issues, revoke/reapprove links, seal old heads and reopen/resolve issues. Every relevant scope/head change denies the old current result; historical tuples/digests remain identical. Changed outside-scope data must not invalidate unrelated results.
6. **N1 concurrency:** two connections with controlled barriers for publication versus each mutation, both serialization orders, plus mutation after snapshot construction within the same transaction. Retry whole transactions; verify the next fresh read and deferred final-state checks.
7. **N2 all 12 cases:** positive supported fixtures and negative missing-component/evidence fixtures; mixed inputs, identified instruments, stable/transient/unknown airflow, condition-role counts and two segments. Publication and consumption must return identical policy decisions.
8. **Approval lineage:** revoke each definition, annotation, selected/component/non-selected identity, condition, eligibility and result approval independently. Reject cycles, wrong-target decisions, skipped/forked revisions and concurrent duplicate first decisions. Never replace pinned history with current heads.
9. **Atomic publication/retry:** inject failure after content seal, approval parent, scope insertion, review seal and event. No partial publication may commit. Revalidation of unchanged contents reuses only the content seal and creates new approval/snapshot/event identities; changed content needs a new result.
10. **Permission boundaries:** deny draft consumption, base reads, direct inserts/mutations, forged reviewer_ref, inherited/public privilege bypass and search_path manipulation. Test separate authorized historical access and pooled-session snapshot freshness. No success response before commit.
11. **Metadata:** same-subject predecessors, concurrent first revisions, latest pending/withdrawn behavior, explicit unknown fields, source-version corrections and exact pinned variable versions without UPDATE rights.
12. **Raw representation/ingestion gate:** first test exact whitespace, empty versus NULL/none, bounds, negatives, suffixes and compound strings using technical fixtures. After enforcement tests pass, perform a rollback-only real-source staging/round-trip check comparing all 17 headers/2,193 values and hashes before permitting committed BASS-II ingestion. Do not mutate source files or derive unsupported annotations.

Passing ordinary FK tests alone is insufficient. All publication, snapshot, policy, privilege and concurrency groups must pass before the real-source gate opens. Record actual commands, environment versions and failures/results in M4; do not reuse this review's static checks as database test evidence.

## H. Explicit M4 authorization and scope

**Architecture authorization: M4 BASS-II implementation may proceed.** There is no remaining architecture-review blocker in N1, N2 or R1–R7. This review authorizes the bounded next milestone; it does not start implementation in this review-only turn.

Permitted initial M4 scope is PostgreSQL schema/migrations, SQLAlchemy mappings, reviewed custom SQL enforcement, authenticated controlled procedures, protected analytical/historical read surfaces, role configuration and the disposable-database acceptance suite. The implementation must preserve the approved rules rather than invent alternative snapshot or waiver behavior.

**Real source ingestion remains gated:** complete the synthetic-fixture enforcement suite, then the rollback-only exact source round-trip, before committed ingestion. No implicit scientific approvals may be generated merely because records load successfully. Production deployment, additional investigation onboarding, scientific analytics, AI/RAG and unrelated frontend/backend functionality are outside this authorization.

This is approval of a technically implementable architecture whose historical explanation remains reconstructable after revocation and whose current-use boundary is explicit. It is not a claim of deployed protection, scientific validity or completed M4 testing.
