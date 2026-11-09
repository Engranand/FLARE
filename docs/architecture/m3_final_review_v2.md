# M3.2 independent architecture re-review

Review date: 2026-11-06. Scope: documentary architecture readiness for M4, not scientific validation or database enforcement testing.

## A. Executive verdict

**NOT APPROVED — M4 remains blocked.**

The revised design substantially improves aggregate immutability, explicit approval lineage and publication authorization. Independent static inspection confirms **33 entities, 135 declared foreign keys and 135 corresponding ER edges**. Read-only comparison confirms **129 CSV records, 17 exact headers and all 2,193 raw strings**, and the original workbook contains six worksheets.

However, the required historical approval snapshot does not explicitly cover the expanded identity-link universe used by the new issue-applicability policy (N1, High). The protocol contract also gives conflicting directions for condition-free protocols (N2, Medium). R2 and R3 therefore remain partially resolved. M4 cannot be authorized under the supplied criteria even though the original insertion and direct-read counterexamples now have explicit defenses.

This review reconstructs counterexamples from the actual schema and binding contract; it does not adopt the remediation log's RESOLVED labels. The seven architecture documents, current dictionary, source reconciliation, parser documentation, anomaly/mapping evidence and existing ingestion modules were inspected. The original review and all architecture/source/application files remain unchanged. Only this report was created. No PostgreSQL connection, SQL execution, migration, ORM implementation, parser run that writes outputs, package installation or Git mutation occurred.

## B. R1–R7 reassessment

References below are to [the binding schema contract](postgresql_schema_proposal.md#binding-integrity-contract), using the reviewed file's line numbers where useful. These are design assessments; every database test remains future work.

| Finding | Independent status | Original failure, revised protection and remaining question | Future tests |
| --- | --- | --- | --- |
| R1 | RESOLVED at design level | Previously another child could attach after approval. R1 now seals parent plus all raw, annotation-evidence, condition-component, protocol/unit-rule, result-member and review-dependency children. All inserts share the parent lock with sealing, including nested ownership. Unique target seals, exact counts and deterministic typed serialization close that counterexample. Initial result seal/approval/publication is one transaction. New membership requires a new parent version. | T01–T04: every member table, both race orders, rollback and digest vectors. |
| R2 | PARTIALLY RESOLVED | Previously a condition could consume an unrecorded annotation/identity approval. Condition reviews now pin those exact decisions, including definition reviews transitively; result reviews pin eligibility and selected identities. Revocation does not rewrite historical members. **N1:** issue applicability now uses additional current approved identity links, while the mandatory snapshot enumeration names selected links. A complete historical applicability snapshot is not specified. | T05–T07, especially a second non-selected test link and its issue-clearance decision. |
| R3 | PARTIALLY RESOLVED | Free-form requirements are replaced by sealed relational-v1 requirements and unit rules, exact variable versions, explicit phases/cardinality and same-test/same-segment coverage. Unknown keys and unresolved evidence fail closed. Unrelated test conditions no longer satisfy coverage. **N2:** an empty condition set is permitted at line 45 but line 47 requires input instrument/stability evaluation through ResultCondition even without condition-role requirements, without defining waiver behavior. | T08–T10, including the waiver truth table and two segments. |
| R4 | RESOLVED at design level | Previously a result might be exposed without an explicit approval/publication event. R4 now requires a result seal, current sealed result approval and publication event, plus CanConsume and EXECUTE-only analytical access. Result-level revocation independently denies current use. Historical read access is separate. This resolves the original authorization ambiguity; N1/N2 still affect the inputs to that predicate. | T11–T13: privilege bypass, fresh read transactions, concurrent withdrawal and publication retries. |
| R5 | RESOLVED for the stated BASS-II boundary | Seven singleton roles are replaced by components with explicit role, variable, instrument, slot and test segment. Multiple gases/instruments and unknown scopes can be stored without universal dataset assumptions. Unknown scope cannot acquire analytical permission by matching another unknown. Typed storage extensibility is established; it does not promise every future analysis is supported. | T10, T14: multiple instruments/components, duplicates, unknown scope and unsupported future protocols. |
| R6 | RESOLVED at design level | Previously immutable registration metadata had no correction route. Evidence-backed full-snapshot MetadataRevision, same-subject predecessors and review heads now determine authoritative reads. Pending/withdrawn newest metadata does not silently promote an older snapshot to current. Source-version corrections and exact ScientificVariable versions have explicit routes. | T15: concurrent first revisions, withdrawals, null-as-unknown and old pinned definitions. |
| R7 | RESOLVED for completeness/cardinality | Previously only 64 of 94 relationships were drawn. All 135 revised FK declarations map to diagram edges, including predecessors and scope links. Referenced keys, nullable parents, unique child maxima and XOR explanations were checked independently. There is a minor notation caveat in N4, not a missing-FK blocker. | T16: migration/catalog/diagram correspondence; official Mermaid rendering before handoff. |

The enforcement mechanisms are technically feasible in PostgreSQL. This does not mean the illustrative DDL alone implements them: most publication, revision and dependency guarantees require controlled functions/procedures and cross-row validation. Missing implementation is expected in a design milestone; N1/N2 concern missing or inconsistent design decisions, not the absence of triggers in the repository.

## C. New findings

### N1 — High — Historical issue applicability has an unpinned identity-decision scope

**Evidence:** schema lines 29–37 enumerate mandatory approval dependencies, including every selected identity approval. Line 49 expands applicable test issues to the union across **all current approved identity links** for a consumed observation. Line 92 explicitly pins resolved issue reviews, but does not require pinning the additional identity-link decisions that made those issues applicable. R2's generic requirement to derive a complete closure does not define the historical membership of this expanded set.

**Counterexample (technical scenario, not invented NASA data):** a source row has approved links L-A and L-B to two tests. A result selects L-A. Under line 49, a test-B issue must also be checked; publication may consume its resolved review. The enumerated result dependency set can include L-A and the resolved issue review without L-B's exact approving decision. After L-B is revoked/reapproved, or another link is added, the preserved result does not identify the complete link-decision set used to determine applicability at publication. Querying current links changes the answer; timestamps cannot reconstruct transaction visibility. Conversely, an implementation that pins every such link may invalidate the result when a non-selected link changes, while one that pins only selected links may not. The present contract does not choose between those consequences.

The original condition-component omission is fixed. This is an additional gap introduced by broadening applicability beyond selected links. All immutable raw inputs can still be reconstructed; the complete historical authorization/applicability rationale cannot yet be reconstructed under one unambiguous rule.

**Required correction:** define the publication-time applicability set and its exact identity-review dependencies, including non-selected links, and freeze its membership. Specify which additions/removals affect current permission versus historical explanation. Define how the snapshot records that no applicable unresolved issue was found without reconstructing membership from wall-clock timestamps. Existing seals/dependency relations may be sufficient; this review does not require a particular new table. A blanket statement that all dependencies are complete is insufficient without the set-selection rule.

**Blocks M4: yes**, because complete consumed-decision history and transitive withdrawal are mandatory R2 criteria. Required tests: T06–T07. Do not treat this as permission to remove conservative test-level issue checking.

### N2 — Medium — Condition-free protocol behavior is contradictory

**Evidence:** schema line 45 explicitly permits no ResultCondition when no condition requirements exist. Line 47 says input instrument/stability requirements are evaluated using approved condition components selected through ResultCondition for the exact variable/annotation, and absent matching evidence fails closed even without a condition-role requirement. Every ProtocolRequirement has non-null instrument_policy and stability_policy.

**Counterexample:** a protocol declares only an input requirement, instrument_policy=not_required and stability_policy=not_applicable with the stipulated protocol evidence. It has no condition requirements. One implementation accepts an otherwise eligible input with an empty condition set under line 45. Another rejects it under line 47 because there is no selected matching component. Neither the enums nor the matching rules explicitly say when the second rule is waived. This does not demonstrate unsafe data already published; it demonstrates that implementers cannot derive one required outcome.

**Required correction:** give a complete policy truth table. State whether the not_required/not_applicable pair waives component selection, and which active policies require a selected condition even without a condition-role requirement. Keep scope evidence distinct from a requirement for the exact input annotation to also be a condition component. Synchronize the empty-set allowance and CanConsume rule accordingly.

**Blocks M4: yes**, because R3 and document agreement must be resolved before authorization. Required tests: T08–T09. No scientific default or fabricated condition may be used to make the example pass.

### N3 — Low — Historical acquisition statements are still easy to read as current

[Source reconciliation](../bass_ii_source_reconciliation.md) is explicitly an older milestone but opens with missing DOCX/XLSX and a nonexistent original directory. [Parser documentation](../bass_ii_parser.md) and `backend/app/ingestion/bass_ii.py` retain pending-acquisition warnings. The current dictionary and actual files establish later acquisition. These statements should be treated as historical parser-era context, not current acquisition authority. A future separately authorized documentation cleanup should make supersession visible without rewriting preserved artifacts or changing parser semantics in this review.

**Blocks M4: no independently.** The report's integrity checks use actual present files and current reconciliation evidence.

### N4 — Low — Diagram line style does not distinguish identifying relationships

Every edge uses solid `--`. Mermaid assigns identifying semantics to solid lines, although many displayed FKs are not part of the child's identity (for example a component's annotation reference). The contract describes these edges simply as FK inventory. Cardinalities and FK coverage are correct; clarify that line style is schematic, or use the appropriate distinction in a future authorized diagram revision. [Mermaid ER notation](https://mermaid.js.org/syntax/entityRelationshipDiagram.html).

**Blocks M4: no.** This is a presentation distinction, not an incorrect relational key or XOR constraint.

## D. Expanded-schema audit

### Entity responsibilities and duplication

All 33 entities have identifiable responsibilities:

| Entity group | Entities and responsibility |
| --- | --- |
| Registration/provenance | investigation: repository identity; source_document: immutable byte artifact; source_acquisition: acquisition attempts/aliases; evidence_reference: exact source locator. |
| Raw extraction | parse_run: code/config/output identity; source_field: ordered original columns; source_record: source rows; observation: exact cell representation. |
| Experimental identity | experimental_test: scoped full test identifier; test_source_record: evidenced row/test association; test_relationship: supported relationships without collapsing samples. |
| Semantics | scientific_variable: exact definition versions; semantic_annotation: interpretations without raw mutation; annotation_evidence: supporting membership. |
| Conditions | experimental_condition: reviewed versioned condition aggregate; condition_segment: test scope; instrument: instrument identity; condition_role: controlled role definition; condition_component: typed member. |
| Review/quality | data_quality_issue: observation/test issue; review_event: target-specific decision history; analytical_eligibility: protocol-specific observation or test/segment decision. |
| Protocol | analysis_protocol: versioned policy aggregate; protocol_requirement: exact variable/phase/count/policy; protocol_unit_rule: allowed unit/basis/method/version. |
| Results | analytical_result: result and method identity; result_input: selected interpretations/identity/eligibility; result_condition: selected condition/eligibility; result_evidence: supporting sources. |
| Integrity/history | aggregate_seal: frozen membership; approval_dependency: consumed decision graph; publication_event: publish/revoke history; metadata_revision: descriptive corrections. |

The original 23 identities remain and ten supports have distinct jobs. A seal and publication event are not redundant: membership immutability and current permission are different properties. Review and eligibility likewise have different subjects/purposes. Duplicated segment_key alongside segment_id, stored counts alongside member sets, and direct review pins alongside dependency edges are intentional denormalizations only if the documented equality/completeness checks are enforced. No additional entity is justified merely to duplicate those values.

### Keys, relationships and JSONB

- All 135 referenced column tuples have a corresponding declared PK/UNIQUE target; local/target types agree. All FK declarations use ON DELETE RESTRICT. None specifies cascade deletion.
- All FKs include investigation_id; root references target investigation(id). Observation row/field FKs also preserve parse-run scope. Revision identity is preserved by immutable row IDs, uniqueness and same-stream predecessor checks; a scoped FK alone does not prove same subject, revision+1 or current approval.
- All 33 schema entities match the diagram. All 135 edge labels map to the declarations in order; parent optionality and child maximum cardinality match FK nullability/unique keys. Minimum child membership is enforced by publication gates, not by ER arrows.
- XOR targets are explicit for review, seal, dependency, issue and eligibility; metadata_kind/document presence is explicit. The partial investigation-metadata revision index addresses nullable document IDs. Target-specific review decisions and eligibility field consistency require the additional documented cross-row/procedure gates.
- Protocol variable/role/unit-rule relationships and approval dependencies are relational, not IDs buried in JSONB. Configuration, locators, representation, uncertainty and method parameters remain JSONB; their closed schema validators and prohibition on hidden dependency IDs must be enforced. An object-type CHECK alone is insufficient.
- No mandatory approval cycle was found: a variable review can have an empty dependency set; annotation approval follows definition approval and raw/annotation seals; condition approval follows annotation/identity approvals; eligibility follows those reviews; result approval follows its result seal and those upstream decisions. The review seal then freezes dependencies before publication. A content seal is not itself an approving review, so result approval depending on its own content seal is not a circular approval. Optional dependency edges still need explicit cycle/target checks.

The five architecture deliverables consistently refer to the same 33-entity contract and 135-edge inventory. Only the schema and diagram enumerate the entire inventory; architecture/lifecycle/decisions summarize it. This is acceptable, but consistency of counts does not cure N1/N2. Mermaid was checked statically against documented ER syntax; it was not rendered or compiled with the official parser.

### Technical implementation readiness

| Layer | Suitable responsibility and limits |
| --- | --- |
| Ordinary PostgreSQL constraints | Scoped PK/FK, unique stream revisions/predecessors, partial metadata index, local XOR/value-kind checks and lookup indexes. |
| Custom database enforcement | Immutable-row and member-insert guards; parent/subject locking; nested ownership; same-stream and cross-target validation; seal canonicalization/count checks; dependency completeness; protocol matching; publication/revocation routines; protected current/historical read surfaces. Deferred constraint triggers are available for suitable end-of-transaction cross-row checks; immediate guards are still needed for insert access and locking. [PostgreSQL trigger documentation](https://www.postgresql.org/docs/current/sql-createtrigger.html). |
| Transactions | Whole-transaction SERIALIZABLE retries and consistent lock ordering. A concurrent publication may serialize before withdrawal; after withdrawal commits, a fresh current read must deny use. Establish isolation before the first query, use a fresh transaction per consumption and return no success before commit. A reused old snapshot is not a fresh permission check. [Transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html), [SET TRANSACTION](https://www.postgresql.org/docs/current/sql-set-transaction.html). |
| Permissions | Restricted owner, procedure-only writes, EXECUTE-only analytical readers, explicit investigation/protocol authorization and separate historical access. Security-definer routines need trusted search_path and revoked default public execution. Actor/reviewer identity must derive from authenticated context, not a client-supplied reviewer_ref. Owners/superusers remain an operational exception. [CREATE FUNCTION security guidance](https://www.postgresql.org/docs/current/sql-createfunction.html). |
| SQLAlchemy 2.x | Map composite ForeignKeyConstraint objects, exact Numeric/Decimal and scoped relationships; resolve overlapping investigation_id write ownership explicitly. ORM hooks cannot substitute for database guards or protect other clients. [SQLAlchemy constraints](https://docs.sqlalchemy.org/en/20/core/constraints.html). |
| Alembic | Reviewed migrations can carry constraints and custom SQL objects/grants. Autogeneration is a starting point, not verification of functions/triggers or all checks. No migration was generated here. [Alembic autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html). |
| FastAPI/Pydantic | Request authorization, transaction orchestration and closed typed request models with extra fields forbidden; preserve raw strings and exact decimals. Commit before exposing success; propagate failures and retry only complete safe transactions. Validation supplements database enforcement. [Pydantic configuration](https://docs.pydantic.dev/latest/api/config/), [FastAPI dependency lifecycle](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/). |

The stack is capable of implementing the intended design after N1/N2 are resolved. N1 is not a PostgreSQL limitation, and N2 must not be resolved by an undocumented ORM or API heuristic.

## E. Scientific data integrity assessment

An independent standard-library CSV decode was compared with every existing JSONL raw_value and ordered original_headers list. All **129 × 17 = 2,193** values agree exactly. Original Test # strings remain distinct; no sample-ID deduplication was introduced. XML inspection of the original XLSX confirms `Bhattacharjee`, `Ferkul`, `Miller`, `Olson`, `Fernandez-Pello` and `T'ien`. This review did not rerun the full prior cell-by-cell workbook reconciliation or render the FAQ; those source interpretations remain attributed to the existing evidence-backed dictionary/mapping.

| Integrity case | Observed/preserved result and architectural handling |
| --- | --- |
| Empty versus none | 19 empty CSV strings and 16 literal none strings remain different. Use non-null text for CSV empty strings; absent XLSX cells can use empty_cell/null. Do not map the parser's empty classification directly to SQL null. |
| Negative CO | All 13 negative Initial CO strings remain signed; causes remain unresolved. No zero-clamping. |
| OR versus over | Three OR tokens and one over token remain distinct. FAQ supports OR as >1000 ppm only; over has no independently established threshold. Reviewed bounds must not become point values. |
| Literal bounds | One exact >500 and one exact <1 remain; compound strings can contain other embedded bound notation. No global sensor threshold is inferred. |
| Compound settings | Full strings remain, including repeated spaces and embedded qualifiers. No averaging, invented timestamps or wholesale fan-to-flow conversion. |
| Unresolved oxygen | B2, P22a, P22b, T28a and T28b remain unchanged; corroboration in the workbook is not validation of the readings. |
| Conflicting dates | T9/T18 retain 6/24/2018 despite the worksheet header conflict. The separate supported Olson 2016 exception does not repair those years. |
| Samples/suffixes | Exact identifiers and a/b variants remain. Reused samples do not establish independent replicates. |

The dictionary and anomaly report support these scientific cautions. Parser classifications are lexical and remain separate from approved interpretations. The proposal can preserve all these values; no database round-trip or scientific comparability claim is made.

Recomputed original-file SHA-256 values:

| Original file | SHA-256 |
| --- | --- |
| PSI-25_Experimental table_BASS-II.csv | 71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042 |
| BASS-II data FAQ.docx | 69f32647792f54ab2a561e3cdafc6c87d854564fe487aed2b09265286bd84e1d |
| BASS-II Test Matrix by PI Final.xlsx | 1a3b283dd0adec861793bbc4a454aab64d398cd32d6f37d7a1ad0f642879e686 |

These establish local byte identity, not an independently authenticated NASA checksum. No missing value, scope, unit basis, calibration coefficient or experiment was fabricated.

## F. Required database enforcement tests

These are acceptance specifications for a later authorized disposable PostgreSQL environment. **None was executed in this review.**

### Ten requested adversarial publication scenarios

| Scenario | Design outcome and exact test |
| --- | --- |
| 1. Add a result input after sealing | Reject INSERT; digest/count and publication remain unchanged. Race insertion before and after seal lock acquisition. T01. |
| 2. Add evidence after sealing | Reject ResultEvidence and AnnotationEvidence attachments; allow a new parent revision with fresh seal/approval. Also cover review dependencies and nested protocol rules. T01–T02. |
| 3. Replace an approved annotation dependency | Reject UPDATE/DELETE and post-seal dependency INSERT. A new annotation/decision requires new review lineage; do not silently redirect old result FKs. T05. |
| 4. Revoke a test/source link | Fresh current read returns no analytical result; historical graph retains the exact earlier review. Separately exercise non-selected applicability links under N1. T05–T07. |
| 5. Revoke a definition approval | Deny every dependent result through annotation and condition paths, including conditions absent from ResultInput and protocol-only definition dependencies. T05. |
| 6. Withdraw eligibility during publication | Use two connections and both commit orderings. If withdrawal precedes the publication's valid serialization order, reject/retry publication. If publication serializes first, a subsequent fresh read after withdrawal must deny use. No half-publication. T11. |
| 7. Revoke result approval | Deny current use even if the last publication event is still publish and all upstream approvals remain valid. T12. |
| 8. Read a draft | consume_result denies; base SELECT and alternate function/role paths deny. Historical access requires separate authorization and cannot masquerade as current use. T12. |
| 9. Missing test/segment coverage | Reject a condition from another test, another segment or wrong protocol; two segments require independent correct decisions. Resolve condition-free policy N2 before fixing its expected test outcome. T08–T10. |
| 10. Retry after transaction failure | Inject failure after each publication stage. Verify no partial seal/review/publication commit, rerun the entire transaction and create exactly one initial publication. Revalidate changed dependencies on retry. T04/T13. |

### Detailed test inventory

1. **T01 — Sealed membership:** exercise every child table in the six seal target sets; try direct and procedure-mediated inserts, insert/seal races and wrong aggregate ownership. Assert exact counts/digests remain unchanged after rejection.
2. **T02 — Revisions/evidence:** supplement annotation evidence through a successor revision; keep the original evidence set unchanged. Reject wrong-subject, skipped, cyclic and forked predecessors, including concurrent revision-1 creation.
3. **T03 — Canonical digest:** golden vectors for child ordering, Unicode/control escaping, SQL null, CSV empty text, decimal trailing zeros, negative zero, tagged JSON numbers versus strings, dates and UTC timestamps. Reject unsupported serializer versions and invalid count keys. Two implementations must produce identical bytes before hashing.
4. **T04 — Partial raw runs:** reject incomplete/mismatched row-field-cell counts, wrong output hash and failed-run sealing. Retrying identical verified extraction must not attach members to a sealed run or produce duplicate raw identities.
5. **T05 — Dependency classes:** independently revoke/supersede annotation, variable, selected identity, condition-component identity, condition and result approvals. Reject missing/wrong-role dependencies and cycles. Validate historical exact IDs/predecessors after each change.
6. **T06 — Expanded applicability:** one consumed row linked to tests A/B, selecting A only; add a B-level issue and its resolved review. Require the chosen complete applicability snapshot, including B's deciding identity review; omission must fail. Later change B's identity decision and verify the explicitly chosen current-use policy without altering history.
7. **T07 — Dynamic issue changes:** create/reopen issues before, during and after publication; include additional links and issues with no review, unsealed review or non-resolved head. Reconstruct the publication-time scope without timestamp filtering. New unresolved applicable issues must block fresh reads.
8. **T08 — Closed protocol:** unknown keys/enums, missing unit rules, wrong variable versions/phases/unit basis/method version and unsupported transformations all reject. Exercise every instrument/stability policy combination after N2 is resolved, with and without explicit condition requirements.
9. **T09 — Positive waiver case:** an otherwise valid protocol with no condition requirements and evidence-backed not_required/not_applicable policies must have one documented expected outcome. Test it alongside stable_required and identified_required negative cases; never invent a component to satisfy the test.
10. **T10 — Coverage/counting:** two tests and two segments, mixed conditions, duplicate component slots/annotations, extra unclassified inputs and wrong eligibility subjects. Withdraw only one segment decision and preserve both historical decisions. Assert counts cannot be inflated by duplicate selection.
11. **T11 — Concurrency:** publication versus eligibility withdrawal, definition revocation, issue reopening and competing first review. Verify complete retries, consistent lock order and no success before transaction commit. Allowed serialization order is explicit; no stale authorization cache.
12. **T12 — Reader security:** deny base reads, direct writes, inherited/public privilege paths, forged actor identity and search_path attacks. Verify result-level rejection/revocation and protocol/investigation authorization. Test a fresh transaction after revocation; ensure a pooled prior snapshot cannot be presented as a fresh consumption.
13. **T13 — Publication rollback/retry:** fail after result seal, review insertion, review seal and event insertion; assert atomic rollback. Retry with current dependencies, distinguish intentional re-publication from retry, and reject a second initial event or wrong seal targets.
14. **T14 — Typed conditions:** several gas definitions/instruments in one segment, unknown instrument/scope, unsupported categories and mismatched component variables. Preserve unknown values but deny unsupported analytical use. Future investigation structures remain unaudited.
15. **T15 — Metadata:** correct name/source version without touching registration bytes; concurrent first revisions; same-subject predecessor and partial uniqueness; pending/withdrawn newest snapshot; explicit null rather than inherited value; new variable version must not retarget existing annotations/protocols.
16. **T16 — Catalog/schema:** inspect all 33 tables, 135 FKs, referenced keys, XOR/checks, grants, triggers and indexes after migrations. Reject cross-investigation and cross-run references. Verify mutation/TRUNCATE/DDL denial for application roles and document privileged-owner exceptions.
17. **T17 — Source round-trip:** preserve all 17 headers and 2,193 strings, 19 empties versus 16 none values, bounds, suffixes and source locators. Retain workbook original representation separately; no source update or silent numeric conversion. Verify file hashes again.

## G. M4 implementation authorization and scope

**M4 is not authorized by this review.** Resolve N1/R2 and N2/R3 in a separately authorized architecture revision, synchronize the five deliverables and repeat the review gate. N3/N4 do not independently block BASS-II implementation, but should be recorded as explicit follow-up work.

After approval, the appropriate initial scope is an integrity-first BASS-II implementation: schema and reviewed custom enforcement, least-privilege roles, controlled publication/current/historical surfaces, then the required disposable-database tests. Passing those tests is a prerequisite to importing source data into that implementation. Approval must not imply validated combustion measurements, general multi-investigation analytics, AI/RAG or frontend expansion.

Historical value/member reconstruction is well specified; complete historical applicability-decision reconstruction needs N1. Runtime enforcement remains unimplemented and untested. No architecture or application correction was made as part of this review.
