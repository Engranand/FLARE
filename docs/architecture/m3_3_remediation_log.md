# M3.3 architecture remediation log

Date: 2026-11-06. Design only. This log responds to [M3.2](m3_final_review_v2.md), which remains unchanged. **Neither M3 approval nor M4 authorization is declared.** A fresh independent review is required.

## N1 — Historical issue-applicability snapshot — RESOLVED in design

**Original failure:** the conservative issue policy considered all effective identity links, but historical approval membership explicitly pinned only selected identities. Changes to a non-selected link could change issue applicability without a complete frozen explanation. Missing reviews and an empty issue set also needed explicit publication-time representation.

**Revised rule:** the [N1 contract](postgresql_schema_proposal.md#n1--publication-time-applicability-snapshot) defines exact sets O, L(o), T(o) and Q(o). O includes all input observations and known annotations in selected condition components. L(o) includes every candidate link for each source row, even non-selected/unapproved/revoked/unreviewed links, and captures the exact highest review and seal IDs or their absence. T(o) contains tests of sealed-approved link heads. Q(o) includes all observation issues and all whole-test issues for T(o), across every severity and review state. There is no segment narrowing of test-level issues.

**Affected entities:** ApprovalDependency gains four entry kinds and five nullable scoped FKs, with constrained shapes and three partial uniqueness indexes. ReviewEvent gains the result-approval-only policy version and zero-unresolved attestation. AggregateSeal freezes the expanded membership using canonical-json-v2; PublicationEvent already pins the exact result review and review seal. TestSourceRecord, ExperimentalTest, Observation, DataQualityIssue and their ReviewEvent/Seal identities are referenced directly. ResultInput/ResultCondition determine O. No new entity or parallel approval/snapshot store is introduced.

| Required evidence | Exact representation |
| --- | --- |
| Every consumed observation, including an empty issue set | One scope_observation entry per O member |
| Every considered identity link | One scope_link per owner/observation/link, including non-selected links |
| Exact link decision and test | snapshot_review_id and snapshot_review_seal_id, with explicit NULL absence; snapshot_link_id fixes the immutable test/source-record association |
| Every applicable quality issue | One scope_issue per owner/observation/issue; union over all effective linked tests and the observation itself |
| Exact issue review and resolution state | Nullable head/seal pointers; immutable ReviewEvent.decision supplies the actual state |
| No unresolved applicable issue at publication | Exact-set validation and applicability_unresolved_count=0 under identity-issue-snapshot-v1; every review/blocking issue requires a sealed resolved head |
| Snapshot revision and digest | Result ReviewEvent id/revision/supersedes_id plus PublicationEvent.review_seal_id; review seal hashes the parent attestation and every decision/scope entry |

Scope rows record facts rather than asserting that rejected/unreviewed links or open info issues are approved. All effective identity heads additionally become ordinary permission dependencies; all required issue-clearance heads become ordinary resolved dependencies. Snapshot membership therefore cannot be substituted for an approval.

**Enforcement:** typed scoped FKs and local checks, partial uniqueness, immediate post-seal insert guards, restricted procedures, exact two-way set comparison, target/head/seal validation and deferred publication checks. Every applicability-affecting write takes the investigation lock first, followed by ordered subject/parent locks. SERIALIZABLE retries cover concurrent changes; waiting does not refresh a snapshot. The attestation describes the publication transaction's valid serializable view. A later fresh read must observe committed changes. No timestamp filter is used to recover historical membership.

**Historical versus current use:** historical readers traverse only pinned scope members and immutable targets. Current CanConsume additionally requires ApplicabilityCurrent, comparing freshly derived semantic tuples and exact head/seal IDs to the snapshot. Any new link, new issue, changed head/seal or revoked link invalidates equality, including non-selected links and info issues. This intentionally conservative rule does not automatically restore permission after resolution. Unchanged contents may receive a successor result approval/snapshot and publish event after full revalidation, reusing the content seal. Changed contents require a new result identity. Old snapshots remain immutable. Explicit revoke events are optional additional audit records; current-use denial does not wait for an asynchronous revocation job.

**Evidence limit:** a seal proves integrity of stored membership, not that an external issue was unknown or known in NASA systems. The zero count is a controlled database attestation about the enumerated transaction view. Its correctness must be established by the future enforcement tests.

### N1 required PostgreSQL tests — not executed

1. One input row with selected link A and non-selected approved link B: B's test issue must enter Q(o), and B's exact approving head must enter ordinary dependencies. Reject omitted B, wrong test/row joins and a forged head or seal.
2. Add unreviewed, rejected, revoked and unsealed-head links. Preserve each head/absence as a scope fact, but only sealed-approved heads contribute tests. A selected link must be effective. Later sealing the same head must invalidate equality.
3. Enumerate observation-level and whole-test issues of every severity. Reject publication for review/blocking issues with missing, unsealed, open or otherwise non-resolved heads. An info issue with no head is retainable and does not require resolution.
4. Omit an observation marker, an applicable issue, or a link while leaving plausible counts; add an unrelated scope entry. Exact two-way set comparison must reject each case. Zero issues is an explicit marker-backed set, not a missing scope.
5. Validate zero attestation and policy version: reject absent/wrong values on approved result reviews, reject values on other subjects/decisions, and reject count=0 when any applicable review/blocking issue lacks a sealed resolved head.
6. Verify canonical-json-v2 vectors include all new nullable FKs and attestation fields. Different head absence, issue membership or link membership must change the review digest. Reject scope attachments after sealing. Do not reinterpret a v1 seal as v2.
7. Independently add a new candidate link, approve/revoke/reapprove a non-selected link, add an info or blocking issue, reopen/resolve an issue, and seal a previously unsealed head. Each relevant change must make the old ApplicabilityCurrent false; historical tuples/digest stay identical.
8. Race publication against each mutation using two connections, both lock/commit orders and barriers. Accept only a valid serial order; retry whole transactions on serialization failure. After the mutation commits, a fresh consumption must deny the mismatched old snapshot even if publication serialized first.
9. In a single transaction, create a pending publication then introduce an issue/link/review change before commit. Deferred publication validation must reject its stale snapshot/zero claim. The deferred check belongs to newly inserted publication events; it must not prevent legitimate later withdrawals merely because historical snapshots then differ.
10. Revalidate unchanged result contents: create a successor result review with a fresh snapshot/seal and publication; retain the same content seal and old review history. Failure must commit no new publication. If inputs/conditions/evidence change, require a new result identity instead.
11. Deny direct writes, forged reviewer identities, post-seal insertion and base-table analytical reads. Preserve current versus historical access separation. Test malformed/cyclic ordinary dependencies separately from historical scope facts.

## N2 — Condition-free protocol policies — RESOLVED in design

**Original failure:** empty ResultCondition was explicitly permitted without condition-role requirements, while an unconditional input-policy rule still required matching components. The waived policy pair had two plausible outcomes.

**Revised rule:** the [N2 truth table](postgresql_schema_proposal.md#n2--complete-condition-policy-truth-table) covers the actual two instrument enums and three stability enums, both with and without condition-role requirements. **Yes: no condition-role requirements plus not_required/not_applicable on every input permits an empty ResultCondition set.** This waives matching input components for those policies, not documented input segments, source identity, ordinary approval, eligibility or issue checks.

| Instrument | Stability | Input component required | Empty set with no condition-role requirements | Empty set with condition-role requirements |
| --- | --- | --- | --- | --- |
| not_required | not_applicable | No | Valid if all inputs use this pair and all other gates pass | Invalid |
| identified_required | not_applicable | Yes | Invalid | Invalid |
| not_required | transient_allowed | Yes | Invalid | Invalid |
| identified_required | transient_allowed | Yes | Invalid | Invalid |
| not_required | stable_required | Yes | Invalid | Invalid |
| identified_required | stable_required | Yes | Invalid | Invalid |

An active input policy needs a known component selected via ResultCondition for the exact input annotation and variable version, in the same test and segment. Instrument identification requires an identified status and instrument FK. Stable flow requires stable evidence; transient_allowed accepts documented stable or transient scope, not unknown scope. The same component/condition must support both active policies. Condition-role requirements independently match their required variables/roles/counts; their annotations need not be result inputs. No invented waiver component, timestamp, stable-flow assertion or instrument identity is permitted.

**Affected entities:** AnalysisProtocol remains the sealed closed grammar owner; ProtocolRequirement holds explicit policy enums; ResultCondition selects approved/eligible conditions; ConditionComponent and ConditionSegment supply exact identity/scope evidence. Publication validation and CanConsume share one matcher. No columns, enums or entities are added for N2.

**Historical versus current use:** the exact protocol seal and selected members preserve the original policy choices and evidence. Current consumption reruns that same version's matcher alongside N1 and approval currency; it does not substitute a newer protocol or fabricate missing conditions.

### N2 required PostgreSQL tests — not executed

1. Exercise all 12 combinations of the six policy pairs and presence/absence of condition-role requirements. With valid supporting evidence, verify the single expected empty-set outcome for each row.
2. For the waived/no-role positive case, accept no ResultCondition but still require documented segment/identity/observation eligibility. Reject missing waiver evidence or unknown segment scope. Mixed input requirements permit empty only if every input is waived.
3. For each active pair, reject no component, unknown component value, wrong annotation/variable version, wrong test/segment, wrong phase/unit/method, and missing evidence. Accept only supported combinations; no scientific default fills a gap.
4. For identified_required, reject unknown/not_applicable instrument or missing instrument FK. With not_required, do not demand identification solely for that policy.
5. stable_required rejects transient/unknown/not_applicable airflow. transient_allowed accepts documented stable/transient scope and rejects unknown/not_applicable. not_applicable waives airflow checking with protocol evidence but never waives documented input segment scope.
6. Require every declared condition role/count per input test/segment even when the input pair is waived. Do not require a condition-role annotation to equal an unrelated input annotation. Two segments cannot borrow one another's components or stability evidence.
7. Reject unsupported enums, literal required, NULL policies, unknown keys and unrecognized schema versions at both insertion boundaries and protocol sealing. Reject duplicates that inflate counts.
8. Compare publication and CanConsume outcomes for every positive/negative fixture. Optional selected conditions still undergo review and enter N1 applicability; choosing them cannot bypass issue checks.

## Inventory and synchronization

The design retains **33 entities**. The five new scoped applicability FKs increase the inventory from **135 to 140**, all drawn in the ER diagram. Scope entries reuse ApprovalDependency, its owner review, the existing review revision chain and AggregateSeal. The review digest version advances to canonical-json-v2 for the expanded row shape. No original review or remediation log was rewritten.

Updated deliverables: [architecture](scientific_data_architecture.md), [schema and contracts](postgresql_schema_proposal.md), [ER diagram](scientific_data_model.mmd), [lifecycle](data_lifecycle.md), and [decisions](architecture_decisions.md). The ER comments describe N1 shape discrimination and N2's waiver; solid/dotted lines now distinguish identifying versus non-identifying FKs.

## Validation and approval boundary

Static validation completed on 2026-11-06:

| Check | Result |
| --- | --- |
| Entity/column inventory | All 33 illustrative CREATE TABLE declarations match the 33 diagram entities. Every documented column/type/nullability entry matches its declaration, including the two revised tables. |
| Foreign keys | All 140 scoped FK declarations have compatible column types and declared unique referenced keys; all use RESTRICT. All 140 corresponding diagram edges match parent nullability, child maximum cardinality and identifying/non-identifying line style. |
| Applicability completeness | Documentary inspection traces every N1 requirement through O/L/T/Q membership, typed head/seal absence, ordinary permission dependencies, zero attestation, review revision/seal identity, fresh equality and successor-approval revalidation. This is contract inspection, not executed database proof. |
| Truth table | Both schema and log contain exactly the six pairs from the actual SQL policy enums, with no omissions or duplicates. The two role-presence columns define all 12 cases. Only the waived/no-role case allows an empty set; active cases require components. |
| Fail-closed behavior | The normative rule explicitly rejects missing required evidence, wrong input/test/segment matches, unknown scope and unsupported/null policies. Waiver of input policies does not waive declared condition roles or documented segments. |
| Synchronization and links | All five deliverables use 33 entities/140 FKs, the same sealed applicability model and the same waived-pair outcome. All 36 local document links and referenced heading anchors resolve. Historical counts inside prior reviews/logs remain unchanged. |
| Mermaid | The complete diagram passes a static check of its ER grammar, attribute/key syntax, relationship operators and edge references against documented Mermaid syntax. No official parser compilation or visual rendering was performed. |
| Raw preservation | Independent CSV decoding matches all 129 records, 17 exact ordered headers and all 2,193 raw JSONL cell strings. CSV SHA-256 remains 71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042. No normalization, inference or output rewrite occurred. |
| Change boundary | Baseline SHA-256 comparison shows only the five authorized architecture deliverables changed and this log was added. All 68 other checked files remain byte-identical, including both historical review reports, the M3.1 remediation log, raw/processed data, reconciliation, parser and checked application files. |

All database tests above are future obligations. No PostgreSQL connection, SQL execution, migration, ORM/parser/application change or source-data rewrite occurred. No Git commit, amend or push occurred. The unchanged M3.2 verdict remains the historical review; resolving these design rules does not self-approve M3.
