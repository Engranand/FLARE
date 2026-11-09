# PostgreSQL schema proposal — M3.3

Design only; 33 tables: 23 retained identities plus 10 justified supporting entities. No DDL executed. The historical [M3 review](m3_final_review.md) remains unchanged.

## Binding integrity contract

Design only. All mechanisms below are future database acceptance requirements, not installed protections. Immutable parent and child rows are insufficient without aggregate seals. A draft is an immutable version with no seal; an approved review is effective only when its dependency set is sealed. No mutable status flag is authoritative.

The M3.3 row-shape change advances the proposed seal format to canonical-json-v2; v1 remains the historical M3.1 design identifier. The encoding rules are retained, but v2 covers the expanded ReviewEvent/ApprovalDependency fields. A future implementation must never relabel an existing seal. No deployed v1 seals are asserted here.

### R1 — Atomic membership seals

| Seal target | Membership frozen, including parent row |
| --- | --- |
| ParseRun | SourceField, SourceRecord, Observation, including original representation and flags |
| SemanticAnnotation | AnnotationEvidence; primary evidence FK and transformation parameters are part of the parent |
| ExperimentalCondition | ConditionComponent; segment and scope/stability evidence are part of parent |
| AnalysisProtocol | ProtocolRequirement and their ProtocolUnitRule children |
| AnalyticalResult | ResultInput, ResultCondition, ResultEvidence |
| ReviewEvent | ApprovalDependency |

All UPDATE/DELETE/TRUNCATE remain forbidden. Every child INSERT locks its owning aggregate parent, resolves nested ownership (a unit rule belongs to its requirement's protocol), and rejects if a seal exists. Seal insertion uses the same parent lock, validates the complete member set and appends exactly one seal in that transaction. Only restricted procedures may write. Lock parents in table-name/UUID order under SERIALIZABLE and retry whole transactions after serialization failures. First-child and first-seal races use the already existing parent row as lock anchor. Recheck every invariant at transaction end, including all indirect child inserts. Missing or duplicate membership, partial runs and failed-run children reject commit. A complete ParseRun status is an extraction assertion only: no raw publication until its seal validates archived output hash, row/field/cell counts and exact output equality. Failed runs never seal for analytical use.

Digest canonical-json-v2 is SHA-256 over UTF-8 JSON of the parent and sorted child tuples `(table_name, investigation_id, id, full_row)`, excluding only aggregate_seal itself. Sort table names and UUID strings bytewise; object keys use Unicode code-point order; no Unicode normalization of values; arrays preserve order; JSON has no insignificant whitespace; strings use JSON escaping without escaping non-ASCII; SQL null is JSON null; UUIDs lowercase; numeric SQL values are canonical decimal strings (no exponent, no insignificant trailing fraction zeros, zero is '0'); timestamps are UTC with six fractional digits; dates ISO; byte strings hex. Raw strings are never numerically canonicalized. For JSONB columns use the recursively type-tagged encoding defined below, with exact decimals, not binary floats. member_counts has exactly one nonnegative count per member table plus parent=1. Schema/serialization changes require a new seal_version implementation, never silently reuse v1. Seal evidence documents reference immutable source hashes; rows cannot be replaced. Future golden-vector tests must cover null/empty, Unicode, decimals and ordering.

Changed members require a new parent version with new ID and new seal, including copied unchanged members under new IDs. Annotation evidence supplements require a successor annotation revision and fresh approval; they cannot attach to the sealed old annotation. Result changes require a new result ID/publication; no content rewrite. New review events are history for their subjects, not new members of the old subject seal. New parsing output requires a new ParseRun identity; a byte-identical retry reuses the existing sealed run.

### R2 — Complete decision snapshots

ApprovalDependency uses scoped FKs and a closed entry_kind discriminator, not ID arrays. Ordinary decision entries have exactly one review/eligibility/seal target; applicability entries have the explicit shapes in N1 below. Before sealing a review, its procedure derives the required dependency closure and applicability sets and rejects omission, wrong role/target or extra members. Every ordinary dependency review is already sealed. Applicability entries record historical heads, including missing or unsealed heads, and are not ordinary approval edges. Review predecessors are exact immutable IDs with same-target revision+1; uniqueness and subject locks prevent forks. Timestamps are audit data, never a snapshot algorithm.

| Approved subject | Mandatory pinned dependencies |
| --- | --- |
| Variable definition / metadata revision / identity link / test relationship | Exact source evidence through subject FK; any consumed prior reviews explicitly pinned; dependency set may otherwise be empty |
| Annotation | Own annotation seal, sealed parse-run input, exact approving review of its exact ScientificVariable version |
| Condition | Own condition seal; for each known component, exact annotation approval and exact identity-link approval connecting its source row to the condition's test; each component's variable approval transitively pinned; segment evidence validated |
| Result | Own result seal and protocol seal; every input annotation approval, every selected identity approval, every condition approval and every observation/test eligibility decision consumed, even if already reachable transitively; complete N1 applicability entries, plus ordinary approval dependencies for all effective identity links, selected or not, and all required issue clearances |

Only approved sealed variable-definition reviews permit annotation approval. Condition approvals pin component identities even when that component is not a ResultInput. Eligibility streams are keyed by (protocol, observation) or (protocol, test, segment); segment_id is mandatory only for test decisions. Thus approving a second segment does not supersede the first segment. Its segment must belong to its target test and selected condition. Eligibility rows already pin annotation/condition review IDs; only sealed effective reviews may be used. Sealed result approval pins each consumed eligibility row and its predecessor/revision through immutable FKs. No later approval transfers to an old dependency automatically. Revocation or a superseding decision makes the pinned decision non-current and invalidates current use transitively, including variable-definition and identity reviews. Historical reads return the pinned graph unchanged. New unresolved applicable issues invalidate current use even if created after the snapshot; historical validity and present validity are distinct.

### R3 — Closed protocol grammar and coverage

AnalysisProtocol requirements_schema_version must be `relational-v1`; its display_metadata must be `{}`. Protocol records and all children have closed field sets: reject unknown request keys, unknown enum values and absent required values in both the validated insertion procedure and API boundary. There is no user SQL, expression evaluator, executable policy or free-form requirements JSON. Each ProtocolRequirement references the exact ScientificVariable row/version. Input requirements have no condition role; condition requirements reference a controlled ConditionRole. phase is an exact source label, or explicit `not_applicable`; no wildcard or inferred phase. min_count/max_count are explicit positive bounds. Value policy is numeric_only, numeric_or_censored, or categorical; missing/unresolved values never satisfy a requirement. Negative values are not silently removed: open scientific issues determine eligibility.

Every requirement needs at least one ProtocolUnitRule. Unit text matches SemanticAnnotation.interpreted_unit and basis matches its exact ScientificVariable.unit_basis. Both must match exactly, with unit_status=not_applicable and null interpreted_unit matching only the explicit rule token `not_applicable` for categorical values; unknown units never match. Rule method/version must equal the annotation's transformation method/version. Identity interpretation is explicitly named, not defaulted. Conversion is permitted only when that exact documented method/version and evidence-backed parameters have already produced a separate reviewed annotation; protocol matching performs no conversion. A conversion rule does not authorize execution of an arbitrary method. All rules need evidence and are sealed with the protocol.

For each result input, require an approved exact row-to-test link and a documented ConditionSegment belonging to that test. Enforce every input requirement's cardinality per `(test, segment)`. Every input must match exactly one input requirement, with input_role equal to its requirement_key (no unclassified extra inputs or double-counting). At least one input requirement and one input are mandatory. Categorical means value_kind=text; date/sequence/missing/unresolved are preserved but not analytical inputs in relational-v1. For each required condition role, require ResultCondition for that same test and exact segment, not an unrelated eligible test. Match component variable version, role, phase, unit, count and instrument policy; no pooling across segments or requirements to meet counts; each counted instrument must satisfy the stated instrument policy. Every selected condition must correspond to an input test/segment. Each ResultCondition must pin a current eligible test/segment decision selecting that exact condition; all selected decisions use the result's protocol. Empty ResultCondition is valid exactly when no condition-role requirements exist and every input requirement uses instrument_policy=not_required and stability_policy=not_applicable, with the required protocol evidence. The N2 truth table is normative for both publication and consumption.

stable_required demands documented stable scope and known segment boundaries; transient_allowed requires documented stable or transient scope without asserting steadiness; not_applicable needs explicit protocol evidence and waives the airflow-stability check. Unknown segment scope fails analytical publication, including condition-free protocols. Unknown/not_applicable components do not satisfy required known values. identified_required rejects unknown instrument identity. Active input policies require the exact matching component defined in N2, even without a condition-role requirement; the not_required/not_applicable pair waives that component requirement. Multiple slots cannot count the same annotation/instrument/role twice.

Issue policy v1 remains `all_unresolved_review_or_blocking`. N1 defines its complete publication-time set and current comparison. Observation issues and whole-test issues across every effective approved identity link are checked, including non-selected links. Only a sealed resolved head clears a review/blocking issue; missing, unsealed or any other head fails closed. Info issues do not require resolution, but their membership/head changes still require snapshot revalidation. No source-row relinking hides an observation issue. More permissive policies require a new reviewed design, not new JSON keys.

### N1 — Publication-time applicability snapshot

Use the existing ReviewEvent → ApprovalDependency → AggregateSeal structure. No new entity, parallel snapshot or JSON ID list is introduced. The owner is the exact approved result review. Its identity/revision/predecessor and publication_event.result_review_id identify the snapshot revision; publication_event.review_seal_id pins its complete membership digest. New approval-dependency entry kinds distinguish ordinary permission edges from historical applicability facts.

Define the following sets in the publication transaction's SERIALIZABLE view, including its own validated writes:

1. **O:** distinct observations of all ResultInput annotations and all non-null annotations in every selected ResultCondition component, including extra components. Unknown components without an annotation introduce no fabricated observation. Their definition reviews remain required.
2. **L(o):** every TestSourceRecord row for o.source_record_id, regardless of whether selected, approved, rejected, revoked or unreviewed. Record the highest review revision for each link, or explicit absence. Record the exact seal of that head, or explicit absence. A link is effective only if that captured head is sealed and approved. Its immutable link FK fixes both source record and test identity; no separate test-ID copy is needed.
3. **T(o):** tests of effective links in L(o). The selected input/component identity link must be one of them. Non-selected effective links contribute equally to issue applicability.
4. **Q(o):** all DataQualityIssue rows targeting o, plus all test-target issues for every test in T(o), with no segment narrowing. Include every severity and every review state. Record each issue's highest review revision or absence and that head's exact seal or absence. Duplicate issue occurrences across different observations are intentional; within one observation each issue occurs once.

For every o, insert one scope_observation entry, including when its Q(o) is empty. For every link in L(o), insert one scope_link entry with its head/seal pair. For every issue in Q(o), insert one scope_issue entry with its head/seal pair. snapshot_review_id=NULL means **no review existed in this view**, not an unknown fallback to query later. A non-null head with null snapshot_review_seal_id means the head was unsealed. Both absences remain immutable even if that head is later sealed. Non-null heads must target the exact snapshot link/issue; non-null seals must target that exact head. Only result-approval owners may have scope entries.

The existing table gains entry_kind plus five nullable scoped FKs: snapshot_observation_id, snapshot_link_id, snapshot_issue_id, snapshot_review_id and snapshot_review_seal_id. Local checks enforce these shapes:

| entry_kind | Ordinary dependency targets | Snapshot fields | role |
| --- | --- | --- | --- |
| decision | Exactly one of dependency_review_id / dependency_eligibility_id / dependency_seal_id | All five NULL | Existing validated decision role; reserved scope roles forbidden |
| scope_observation | All NULL | observation required; link/issue/head/seal NULL | scope_observation |
| scope_link | All NULL | observation and link required; issue NULL; head optional; seal optional only with head | scope_link |
| scope_issue | All NULL | observation and issue required; link NULL; head optional; seal optional only with head | scope_issue |

Partial unique indexes enforce one observation marker per owner/observation, one link entry per owner/observation/link, and one issue entry per owner/observation/issue. The procedure enforces exact set equality in both directions, not only matching counts. It validates all immutable join paths. Every effective link also contributes an ordinary dependency on its exact approved review with role applicability_identity. Every distinct review/blocking issue contributes an ordinary dependency on its exact sealed resolved review with role applicability_clearance. Info heads and ineffective link heads are historical facts, not approvals that must be approved. Ordinary dependency DAG rules do not traverse scope facts; their target/owner rules prohibit self-reference to the result review.

**Evidence of absence:** the approved result ReviewEvent has applicability_policy_version=`identity-issue-snapshot-v1` and applicability_unresolved_count=0. Both are NULL for other decisions. The restricted procedure derives this count over the distinct applicable review/blocking issues, verifies all marker/link/issue memberships against the transaction view, and rejects approval if nonzero. An empty scope is represented explicitly, never inferred from omitted rows. The review seal hashes the parent attestation and every decision/scope row with the existing canonical-json-v2 rules; member_counts still counts the complete ApprovalDependency table membership. Per-kind counts are derived from the frozen rows. This is an auditable database attestation about that transaction's visible set, not a cryptographic proof about external unknown issues or a timestamp-based reconstruction.

**Historical explanation:** use only the publication's exact review and seal, its scope entries, immutable targets and recorded head/seal pointers. Never enumerate current links/issues or infer historical absence from current state. The snapshot stores the entire considered link universe, its effective subset and all resulting issues, including explicit absence of reviews. Later sealing, new heads and revocation cannot alter this explanation.

**Current analytical permission:** in a fresh transaction recompute O/L/T/Q and their exact head/seal pointers under the same policy, and compare semantic membership tuples to the pinned snapshot. Ignore scope-row UUIDs, created_at and ordinary dependency row ordering in this comparison; compare observation ID, link/issue ID, head ID and seal ID, including NULLs. Require equality, ordinary approval/eligibility currency, all protocol gates and zero unresolved applicable review/blocking issues. This is ApplicabilityCurrent(result_review), an additional mandatory CanConsume conjunct. A new link (even unreviewed), any changed link head/seal, new issue (even info), changed issue head/seal, reopened issue or revoked non-selected link makes equality false. No automatic return to permission occurs merely because an issue later resolves: its head changed. Events outside O and its considered link/test issue scope have no effect.

**Revalidation:** mismatch withdraws current-use eligibility immediately through CanConsume; the old publication event and snapshot remain historical. Explicit revoke events may additionally record withdrawal. If result contents/members are unchanged, full revalidation creates a successor result ReviewEvent with a fresh complete snapshot, seals it and appends a new publish event atomically, reusing the existing result content seal. Failed revalidation publishes nothing. If content/membership changes, create a new AnalyticalResult identity and content seal. Revoked selected links or other invalid mandatory inputs cannot be repaired by applicability-only reapproval. New/reopened unresolved issues must be resolved through their own review process first.

**PostgreSQL enforcement:** procedure-only writes; immediate parent-seal guards; local shape checks/partial uniqueness/FKs; deferred cross-target/set-completeness/count verification; and restricted publication/current/historical surfaces. All procedures that insert links, issues, their reviews or review seals, eligibility changes or publications acquire the investigation row lock first, then the existing ordered parent/subject locks. This deliberately conservative BASS-II write serialization avoids an unbounded per-row lock-discovery protocol; future scaling requires a reviewed replacement. All transactions use SERIALIZABLE and full retries, including serialization errors after waiting. Locks do not refresh an already acquired snapshot. The attestation means the publication transaction's valid serializable view, not a wall-clock commit-time reconstruction. An overlapping change may serialize after publication; the next fresh consumption after that change commits must fail equality. Establish a fresh read transaction per consumption and return success only after its checks/commit. Deferred validation must also catch later writes in the same publication transaction before commit. These are design requirements, not executed controls. [PostgreSQL isolation](https://www.postgresql.org/docs/current/transaction-iso.html), [constraint triggers](https://www.postgresql.org/docs/current/sql-createtrigger.html).

### N2 — Complete condition-policy truth table

Actual enums remain instrument_policy ∈ {not_required, identified_required} and stability_policy ∈ {not_applicable, transient_allowed, stable_required}. The word “required” is descriptive shorthand only: literal required and all unknown/null policies are rejected. No schema default chooses a policy. Condition-role requirements mean ProtocolRequirement.target_kind=condition; they are independent of input-policy activation.

For each input requirement, evaluate all six combinations below. C=0 means the protocol contains no condition-role requirements; C=1 means at least one exists. “Yes” permits an empty set only if **every** input requirement has that same waived pair. All other publication gates, including documented input segments and waiver evidence, still apply.

| instrument_policy | stability_policy | Matching input component needed? | Instrument test | Condition stability test | Empty ResultCondition valid, C=0? | Empty valid, C=1? |
| --- | --- | --- | --- | --- | --- | --- |
| not_required | not_applicable | No | Waived | Waived, protocol evidence required | Yes | No |
| identified_required | not_applicable | Yes | identified with instrument FK | Waived, protocol evidence required | No | No |
| not_required | transient_allowed | Yes | Waived | stable or transient, documented scope | No | No |
| identified_required | transient_allowed | Yes | identified with instrument FK | stable or transient, documented scope | No | No |
| not_required | stable_required | Yes | Waived | stable with supporting evidence | No | No |
| identified_required | stable_required | Yes | identified with instrument FK | stable with supporting evidence | No | No |

**Explicit answer: yes.** With no condition-role requirements, not_required plus not_applicable for every input permits an empty ResultCondition set. This does not invent a condition, infer steady flow or waive the existing documented ConditionSegment/identity/eligibility requirements. A nonempty optional condition set must still satisfy all ordinary condition approval/provenance checks and enters O for issue applicability.

For an active input policy, select through ResultCondition a condition whose test equals the input's approved link test and whose segment_id equals ResultInput.segment_id. The supporting known component must have annotation_id exactly equal to ResultInput.annotation_id and variable_id exactly equal to the requirement/annotation version; match phase, accepted unit/basis and method/version using the existing rules. The role must be an audited role compatible with that variable category; it need not be an explicitly required condition role. A single component must satisfy both active instrument and stability policies; do not combine a sensor from one component with another component's scope. If multiple candidates qualify, all satisfy the gates and the snapshot includes all selected components; no hidden “first match” choice grants permission. The selected condition's evidence must substantiate the asserted stable/transient scope for this input and segment, not merely a generic instrument description.

When policies are waived, no matching input component is required solely for those policies. If C=1, its declared role requirements still require matching components and counts in every input test/segment. Apply the same instrument/stability tests to each component counted for a condition-role requirement; it need not equal an input annotation, since it represents that required condition variable. No role/phase/instrument can substitute for a different variable or test/segment. One segment's evidence never covers another implicitly. Unknown instrument is acceptable only when instrument_policy=not_required; unknown stability is acceptable only when stability_policy=not_applicable and the segment itself is documented. Missing required components, unknown scope, wrong IDs, absent required evidence or unsupported policies reject publication and current consumption. Condition-free does not mean scope-free.

AnalysisProtocol sealing validates the closed policy enums, required evidence and unit rules. ProtocolRequirement carries the explicit policy choices. ResultCondition stores selected reviewed/eligible conditions, not fabricated waiver rows. Publication and CanConsume call the same logical N2 matcher over each input and required condition component; no alternate API waiver or database shortcut is allowed.

### R4 — One publication lifecycle and read predicate

Draft creation → validate complete parent/children → seal result → append mandatory result-level approved ReviewEvent with complete dependencies, N1 scope membership and zero-unresolved attestation → seal that review → append publication_event(action=publish). Result seal, result approval and approval seal, and initial publication are committed atomically in the publication procedure; upstream dependencies must already be sealed/current. Draft objects assembled earlier are invisible to analytical readers. Any failure rolls back publication; a seal alone is not publication. Publication events form a same-result revision+1 chain with unique predecessor, exact result seal and exact result review/seal. A revoke event is append-only; it may reference the formerly published approval while recording revocation reason/actor. A new publish requires a fresh current approved review, freshly captured N1 snapshot and complete N2 revalidation; changed result content needs a new result version.

`CanConsume(result, protocol, reader)` is true iff: reader is authorized for investigation and protocol; the latest publication chain head for result is publish; its result seal targets this result and its approval seal targets the exact approved result review; that review targets this result and is the current sealed review head; result.protocol_id equals requested protocol; all seal digests/members are structurally valid; every ordinary decision review in the dependency DAG is the current sealed approved head for its subject (issue-clearance reviews use resolved); each pinned eligibility is the current eligible same-subject/protocol decision and pins the exact selected annotation/condition; every protocol requirement and test/segment coverage constraint passes under the N2 truth table; ApplicabilityCurrent(result_review) from N1 is true; and no applicable unresolved review/blocking issue exists now. All conjuncts are mandatory. Unknown, revoked, rejected, unsealed or superseded mandatory permission decisions mean false. Scope facts may legitimately record negative or absent heads; their exact unchanged state, not approval, is required. Result-level revocation/rejection alone is sufficient to deny use, even without a publication revoke event.

Analytical readers receive EXECUTE only on a restricted security-definer `consume_result` surface that evaluates this predicate and reads members in one consistent SERIALIZABLE transaction/snapshot. No base-table SELECT, arbitrary SQL function access, owner membership or raw-export privileges. Fix search_path, validate caller authorization, revoke PUBLIC execution, and never interpolate caller SQL. Review/ingestion roles also write via narrowly granted procedures only. Historical auditors use a distinct read-only, authorized surface returning sealed versions plus pinned decision graphs, clearly marked historical/not-current; they cannot confer present eligibility. No cached boolean grants access. A concurrent revocation linearizes before or after a consumption transaction; already returned data cannot be retroactively recalled. Fresh consumption observes committed withdrawal. No promise of revoking downloaded data is made.

### R5 — Typed condition extension boundary

Replace seven singleton annotation columns by ConditionComponent, referencing a controlled role, exact variable definition, optional explicitly identified Instrument, slot, annotation or explicit unknown/not_applicable state, and evidence. ConditionSegment identifies documented test scope without inventing timestamps; experimental_condition.segment_key must equal its segment's key and test ID. result_input.segment_id must belong to its approved linked test. Initial BASS-II roles remain material, geometry, restrictor, air_speed, oxygen, fan and radiometer, but no role is globally required. Its missing instrument IDs and scope may remain unknown; this preserves data while withholding unsupported analytics.

Multiple gases or instruments use separate typed components/variable definitions/instrument IDs, not dynamic JSON fields. Multiple scopes use distinct documented segments and condition versions. Instrument and role registration rows are immutable; corrected descriptions require new identities and new version-qualified codes, with evidence explicitly locating the correction. Existing references remain unchanged; no automatic successor selection is allowed. New investigation-specific role definitions must be audited and approved through their associated variable-definition review before use. This is a constrained component relation, not arbitrary string EAV: scalar/bound/date types and units live in reviewed annotations; slots/roles/variables/identities use FKs. No claim is made about actual Saffire/FLEX/ACME/SAME schemas. Future capabilities outside relational-v1 require a new reviewed design before import, not relaxed validators.

### R6 — Immutable metadata correction policy

Investigation and SourceDocument descriptive fields are first-registration snapshots only. MetadataRevision supplies a full replacement descriptive snapshot with reason/evidence, target and revision chain. Nullable fields mean explicitly unknown, not inherit-prior. Identity fields (repository/code/hash/size/storage identity) cannot be changed here; mistaken identities require new registrations and reviewed associations. Investigation metadata streams have one first/head revision per investigation; source-document streams have one per document. An explicit partial unique index enforces investigation revision uniqueness. All predecessor relations must have identical subject and revision+1 under subject locks.

Metadata approval is a sealed ReviewEvent targeting that exact revision. The authoritative metadata surface returns the highest proposed revision only if its current sealed review is approved; otherwise it returns `pending_or_withdrawn` and the last approved snapshot as clearly historical, never silently falling back as current. If no revision exists, first-registration metadata is explicitly labeled unreviewed registration, not verified current metadata. Later source-version information uses source-document MetadataRevision, not an update or inferred portal version. Parsed provenance remains pinned to artifact bytes. No scientific value belongs in descriptive metadata.

ScientificVariable definitions are corrected using a new immutable definition_version for the same variable_code and fresh evidence/approval. Existing annotations keep old versions. Selecting an effective definition requires an explicit protocol FK to an approved exact version; there is no implicit latest-version substitution. Withdrawal of a pinned definition approval invalidates current downstream use; approving a new definition does not retroactively normalize any old observation.

### R7 — Complete relationship inventory

The [ER diagram](scientific_data_model.mmd) draws all 140 declared foreign keys over all 33 entities, including scope and self-predecessor links. Labels fk_0 through fk_139 correspond in order to the ALTER TABLE declarations below. Composite FK columns form one edge, not separate edges per column. Parent optionality follows FK nullability; child maximum is one when its FK columns contain a declared unique key, otherwise many. Minimum child count is zero; publication completeness is a separate gate. Each entity block shows identity/FK attributes; the table contracts list every other field.

XOR is not implied by optional edges: ReviewEvent has exactly one of eight targets; AggregateSeal exactly one of six; ApprovalDependency decision entries exactly one of review/eligibility/seal, with separate N1 scope shapes; eligibility and issues exactly one observation/test. MetadataRevision subject_kind selects investigation (document null) or source_document (document required). These checks and cross-target consistency are mandatory alongside the drawn relationships.

### Common enforcement and preserved contracts

All composite FKs include investigation_id; RESTRICT deletes and immutable row guards remain. Deferred triggers/procedures must enforce document/run/table/locator consistency, exact original field order, XOR targets, same-subject monotone revision chains, no cycles, scoped identity uniqueness and all gates above. Locking alone does not make a check correct: every insertion path including nested members must share the lock protocol. Do not expose direct table writes. Owner/superuser can bypass SQL guards; independent content-addressed storage retention, backups and hash audits are required. No such controls have been implemented here.

Evidence locator v1 remains a closed discriminated schema: CSV logical_record/physical_line_start/end/table_key plus column_ordinal/original_header for cells; XLSX exact sheet/cell range; DOCX paragraph bounds and saved-page basis; PDF page bounds; image pixel/frame basis; video nonnegative timestamp bounds and explicit timebase; document scope label. Reject unknown keys, wrong format, negative/reversed ranges, missing cell specificity and mismatched artifacts. locator_key is canonical typed serialization, not a free-form citation. Method parameters, uncertainty and parser representation metadata must follow named closed schemas; no hidden FK arrays. Unknown uncertainty stays unknown.

Raw strings, exact headers, '' versus none, negatives, OR, over, >500, <1 and all sequences are unchanged. Observations need not be numerically interpretable. Numeric and bound fields remain distinct; no unit conversion, O2 correction, date repair, sample deduplication or inference of independent replicates occurs. FAQ p. 2 paragraph 25 supports OR >1000 ppm, not over; p. 1 paragraphs 19–20 distinguishes voltage/pot/air display; p. 2 paragraph 21 states radiometer gain is uncalibrated. See [dictionary](../bass_ii_data_dictionary.md), [mapping](../bass_ii_test_matrix_mapping.md), [anomalies](../bass_ii_anomaly_investigation.md) and [suitability](../bass_ii_analytical_suitability.md).


Cross-row checks must also enforce: annotation variable category/type/unit compatibility; each known component variable equals its annotation variable; each component role category matches its variable category; annotation review targets exactly the selected annotation; condition review targets exactly the selected condition; result input eligibility targets its annotation's observation and result protocol; identity review targets the selected link, whose source record contains that observation; source record and field share the observation's parse run; source evidence refers to the registered artifact and actual locator. A test eligibility's selected condition must share its test and segment. An observation eligibility cannot carry condition fields; a test eligibility cannot carry annotation fields. Revoked/ineligible decisions may retain their historical subject references but never grant permission.

Review heads are the highest revision for the exact XOR subject, including unsealed proposals: an unsealed new head fails closed rather than keeping an old approval implicitly current. Only issues accept open/resolved; ordinary scientific subjects accept approved/rejected/revoked/needs_review. Eligibility heads likewise use their exact observation or test/segment stream. Revision 1 has no predecessor; later revisions require the immediately preceding same-stream ID. Review predecessor edges are audit history, not dependencies requiring old revoked decisions to be current. Pinned review IDs preserve that predecessor chain without promoting predecessor decisions into the approval dependency DAG.

Condition approval requires approved exact variable definitions for every component, including unknown/not_applicable components. Known components additionally require annotation and test-link approval. The component, role and instrument evidence are immutable and evaluated by the condition reviewer; no separate invented instrument-approval target exists. Result approval pins approvals for every protocol-required definition, even if its version is not otherwise encountered through an annotation. Current-use checks re-evaluate these decisions transitively. Clearing an issue for publication pins its exact resolved review in the result's dependency set; newly created/reopened applicable issues remain dynamic read-time blockers.

Canonical seal serialization further fixes JSON escaping: quote/backslash use their two-character escapes; control code points use lowercase four-digit unicode escapes; slash is not escaped; lone surrogates are rejected. JSONB values are recursively tagged: null is ["null"], boolean is ["boolean",true/false], number is ["number",canonical_decimal_string], string is ["string",original_string], array is ["array",ordered_tagged_values], and object is ["object",key_sorted_array_of_[key,tagged_value]_pairs]. This distinguishes numbers from numeric strings and prevents user objects from impersonating type tags. Each full_row is a column-name-keyed object; member tuples are an array under `members`, with parent under `parent`. Digest input is precisely this two-key object, not the seal row or member_counts. Identical values with different raw lexemes remain different raw strings. This is a local versioned encoding, not a claim of conformance to an external canonical-JSON standard.

## Complete table contracts

PK is (investigation_id,id) except investigation(id). All scoped FKs include investigation_id. Nullable is stated for every column. All UUIDs are application-assigned; timestamps are audit instants, never inferred experiment times. PostgreSQL numeric has no imposed scale; raw text retains original lexical precision. All proposed indexes are scoped B-tree indexes; no generic JSONB GIN indexing or premature partitioning.

### investigation

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| id | uuid | no | PK; — |
| repository_code | text | no | — |
| investigation_code | text | no | — |
| name | text | no | — |
| agency | text | no | — |
| doi | text | yes | — |
| description | text | yes | — |
| source_repository_url | text | no | — |
| metadata | jsonb | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (id); UNIQUE (repository_code, investigation_code); CHECK (jsonb_typeof(metadata) = 'object').

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### source_document

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation |
| id | uuid | no | PK; — |
| original_filename | text | no | — |
| source_type | text | no | — |
| artifact_origin | text | no | — |
| file_size_bytes | bigint | no | — |
| storage_key | text | no | — |
| source_version | text | yes | — |
| metadata | jsonb | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, sha256); CHECK (source_type IN ('csv','xlsx','docx','pdf','image','video','other')); CHECK (artifact_origin IN ('external_original','generated_artifact','software_artifact')); CHECK (sha256 ~ '^[0-9a-f]{64}$'); CHECK (file_size_bytes >= 0); CHECK (jsonb_typeof(metadata) = 'object').

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### source_acquisition

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, source_document |
| id | uuid | no | PK; — |
| source_document_id | uuid | yes | source_document |
| actual_filename | text | yes | — |
| portal_filename_alias | text | yes | — |
| source_page_url | text | yes | — |
| original_download_url | text | yes | — |
| local_relative_path | text | yes | — |
| retrieved_at | timestamptz | yes | — |
| verified_at | timestamptz | no | — |
| verification_status | text | no | — |
| verification_scope | text | no | — |
| method | text | no | — |
| actor_ref | text | no | — |
| metadata | jsonb | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); CHECK (verification_status IN ('verified','failed','unverified')); CHECK (verification_status <> 'verified' OR (source_document_id IS NOT NULL AND actual_filename IS NOT NULL)); CHECK (jsonb_typeof(metadata) = 'object').

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### evidence_reference

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, source_document |
| id | uuid | no | PK; — |
| source_document_id | uuid | no | source_document |
| locator_kind | text | no | — |
| locator_key | text | no | — |
| locator_version | text | no | — |
| locator | jsonb | no | — |
| excerpt | text | yes | — |
| location_basis | text | no | — |
| extraction_method | text | no | — |
| extractor_version | text | no | — |
| verification_status | text | no | — |
| verification_scope | text | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, source_document_id, locator_version, locator_key); CHECK (locator_kind IN ('csv','xlsx','docx','pdf','image','video','document')); CHECK (verification_status IN ('verified','unverified','needs_review')); CHECK (jsonb_typeof(locator) = 'object').

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### parse_run

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, source_document |
| id | uuid | no | PK; — |
| source_document_id | uuid | no | source_document |
| parser_name | text | no | — |
| parser_version | text | no | — |
| code_storage_key | text | no | — |
| configuration | jsonb | no | — |
| output_storage_key | text | no | — |
| record_count | bigint | no | — |
| status | text | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, source_document_id, parser_name, parser_version, code_sha256, configuration_sha256, output_sha256); CHECK (status IN ('complete','failed')); CHECK (record_count >= 0); CHECK (code_sha256 ~ '^[0-9a-f]{64}$'); CHECK (configuration_sha256 ~ '^[0-9a-f]{64}$'); CHECK (jsonb_typeof(configuration) = 'object'); CHECK (output_sha256 ~ '^[0-9a-f]{64}$').

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### source_field

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, parse_run, evidence_reference |
| id | uuid | no | PK; — |
| parse_run_id | uuid | no | parse_run |
| table_key | text | no | — |
| ordinal | integer | no | — |
| original_header | text | no | — |
| raw_unit | text | yes | — |
| raw_unit_status | text | no | — |
| header_evidence_id | uuid | no | evidence_reference |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, parse_run_id, table_key, ordinal); UNIQUE (investigation_id, parse_run_id, id); CHECK (ordinal > 0); CHECK (raw_unit_status IN ('stated','not_stated','not_applicable')); CHECK ((raw_unit_status = 'stated') = (raw_unit IS NOT NULL)).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### source_record

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, parse_run, evidence_reference |
| id | uuid | no | PK; — |
| parse_run_id | uuid | no | parse_run |
| table_key | text | no | — |
| source_record_number | bigint | no | — |
| source_row_id | text | no | — |
| row_evidence_id | uuid | no | evidence_reference |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, parse_run_id, table_key, source_record_number); UNIQUE (investigation_id, parse_run_id, id); UNIQUE (investigation_id, parse_run_id, source_row_id); CHECK (source_record_number > 0).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### experimental_test

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, evidence_reference |
| id | uuid | no | PK; — |
| identity_namespace | text | no | — |
| test_identifier | text | no | — |
| identity_evidence_id | uuid | no | evidence_reference |
| metadata | jsonb | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, identity_namespace, test_identifier); CHECK (jsonb_typeof(metadata) = 'object').

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### test_source_record

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, experimental_test, source_record, evidence_reference |
| id | uuid | no | PK; — |
| experimental_test_id | uuid | no | experimental_test |
| source_record_id | uuid | no | source_record |
| evidence_id | uuid | no | evidence_reference |
| match_method | text | no | — |
| method_version | text | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, experimental_test_id, source_record_id).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### test_relationship

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, experimental_test, experimental_test, evidence_reference |
| id | uuid | no | PK; — |
| left_test_id | uuid | no | experimental_test |
| right_test_id | uuid | no | experimental_test |
| relationship_type | text | no | — |
| evidence_id | uuid | no | evidence_reference |
| description | text | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, left_test_id, right_test_id, relationship_type, evidence_id); CHECK (left_test_id <> right_test_id).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### observation

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, parse_run, source_record, source_field, evidence_reference, evidence_reference, source_record, source_field |
| id | uuid | no | PK; — |
| parse_run_id | uuid | no | parse_run, source_record, source_field |
| source_record_id | uuid | no | source_record, source_record |
| source_field_id | uuid | no | source_field, source_field |
| evidence_id | uuid | no | evidence_reference |
| raw_value | text | yes | — |
| source_value_kind | text | no | — |
| unit_origin | text | no | — |
| raw_unit | text | yes | — |
| unit_evidence_id | uuid | yes | evidence_reference |
| parser_classification | text | no | — |
| parser_flags | jsonb | no | — |
| original_representation | jsonb | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, parse_run_id, source_record_id, source_field_id); CHECK (source_value_kind IN ('text','numeric_lexeme','empty_cell','other')); CHECK (unit_origin IN ('field','cell','not_stated','not_applicable')); CHECK ((unit_origin = 'cell') = (raw_unit IS NOT NULL)); CHECK ((unit_origin = 'cell') = (unit_evidence_id IS NOT NULL)); CHECK ((source_value_kind = 'empty_cell') = (raw_value IS NULL)); CHECK (jsonb_typeof(parser_flags) = 'object'); CHECK (jsonb_typeof(original_representation) = 'object').

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### scientific_variable

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, evidence_reference |
| id | uuid | no | PK; — |
| variable_code | text | no | — |
| definition_version | integer | no | — |
| canonical_name | text | no | — |
| description | text | no | — |
| physical_quantity | text | yes | — |
| canonical_unit | text | yes | — |
| unit_basis | text | no | — |
| variable_category | text | no | — |
| measurement_type | text | no | — |
| definition_status | text | no | — |
| evidence_id | uuid | no | evidence_reference |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, variable_code, definition_version); CHECK (definition_version > 0); CHECK (variable_category IN ('measurement','identifier','instrument_setting','condition','context')); CHECK (definition_status IN ('confirmed','partially_confirmed','unresolved','identifier_only','not_applicable')).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### semantic_annotation

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, observation, scientific_variable, semantic_annotation, evidence_reference |
| id | uuid | no | PK; — |
| observation_id | uuid | no | observation |
| variable_id | uuid | no | scientific_variable |
| interpretation_key | text | no | — |
| revision | integer | no | — |
| supersedes_id | uuid | yes | semantic_annotation |
| value_kind | text | no | — |
| numeric_value | numeric | yes | — |
| bound_value | numeric | yes | — |
| comparator | text | yes | — |
| text_value | text | yes | — |
| date_value | date | yes | — |
| interpreted_unit | text | yes | — |
| unit_status | text | no | — |
| observed_phase | text | yes | — |
| transformation_method | text | no | — |
| transformation_version | text | no | — |
| parameters | jsonb | no | — |
| uncertainty | jsonb | no | — |
| primary_evidence_id | uuid | no | evidence_reference |
| author_ref | text | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, observation_id, interpretation_key, revision); UNIQUE (investigation_id, supersedes_id); CHECK (revision > 0); CHECK (supersedes_id IS NULL OR supersedes_id <> id); CHECK (value_kind IN ('numeric','censored','text','date','missing','unresolved','sequence')); CHECK (unit_status IN ('known','unknown','not_applicable')); CHECK ((unit_status = 'known') = (interpreted_unit IS NOT NULL)); CHECK ((value_kind = 'numeric') = (numeric_value IS NOT NULL)); CHECK ((value_kind = 'censored') = (bound_value IS NOT NULL)); CHECK ((value_kind = 'censored') = (comparator IS NOT NULL)); CHECK (comparator IS NULL OR comparator IN ('<','<=','>','>=')); CHECK ((value_kind = 'date') = (date_value IS NOT NULL)); CHECK ((value_kind IN ('text','missing','unresolved','sequence')) = (text_value IS NOT NULL)); CHECK (numeric_value IS NULL OR numeric_value::text NOT IN ('NaN','Infinity','-Infinity')); CHECK (bound_value IS NULL OR bound_value::text NOT IN ('NaN','Infinity','-Infinity')); CHECK (jsonb_typeof(parameters) = 'object'); CHECK (jsonb_typeof(uncertainty) = 'object').

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### annotation_evidence

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, semantic_annotation, evidence_reference |
| id | uuid | no | PK; — |
| annotation_id | uuid | no | semantic_annotation |
| evidence_id | uuid | no | evidence_reference |
| role | text | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, annotation_id, evidence_id, role).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### experimental_condition

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| segment_id | uuid | no | condition_segment |
| investigation_id | uuid | no | PK; investigation, experimental_test, experimental_condition, evidence_reference, condition_segment |
| id | uuid | no | PK; — |
| experimental_test_id | uuid | no | experimental_test |
| segment_key | text | no | — |
| revision | integer | no | — |
| supersedes_id | uuid | yes | experimental_condition |
| scope_description | text | no | — |
| airflow_stability | text | no | — |
| evidence_id | uuid | no | evidence_reference |
| extension_metadata | jsonb | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, experimental_test_id, segment_key, revision); UNIQUE (investigation_id, supersedes_id); CHECK (revision > 0); CHECK (supersedes_id IS NULL OR supersedes_id <> id); CHECK (airflow_stability IN ('stable','transient','unknown','not_applicable')); CHECK (extension_metadata = '{}'::jsonb).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### data_quality_issue

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, observation, experimental_test, evidence_reference |
| id | uuid | no | PK; — |
| observation_id | uuid | yes | observation |
| experimental_test_id | uuid | yes | experimental_test |
| issue_type | text | no | — |
| description | text | no | — |
| severity | text | no | — |
| detector_method | text | no | — |
| detector_version | text | no | — |
| evidence_id | uuid | no | evidence_reference |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); CHECK (num_nonnulls(observation_id,experimental_test_id) = 1); CHECK (severity IN ('info','review','blocking')).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### review_event

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| applicability_policy_version | text | yes | — |
| applicability_unresolved_count | integer | yes | — |
| metadata_revision_id | uuid | yes | metadata_revision |
| investigation_id | uuid | no | PK; investigation, semantic_annotation, scientific_variable, experimental_condition, test_source_record, test_relationship, data_quality_issue, analytical_result, review_event, evidence_reference, metadata_revision |
| id | uuid | no | PK; — |
| annotation_id | uuid | yes | semantic_annotation |
| variable_id | uuid | yes | scientific_variable |
| condition_id | uuid | yes | experimental_condition |
| test_link_id | uuid | yes | test_source_record |
| test_relation_id | uuid | yes | test_relationship |
| issue_id | uuid | yes | data_quality_issue |
| result_id | uuid | yes | analytical_result |
| revision | integer | no | — |
| supersedes_id | uuid | yes | review_event |
| decision | text | no | — |
| rationale | text | no | — |
| evidence_id | uuid | no | evidence_reference |
| reviewer_ref | text | no | — |
| reviewed_at | timestamptz | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, supersedes_id); UNIQUE (investigation_id, annotation_id, revision); UNIQUE (investigation_id, variable_id, revision); UNIQUE (investigation_id, condition_id, revision); UNIQUE (investigation_id, test_link_id, revision); UNIQUE (investigation_id, test_relation_id, revision); UNIQUE (investigation_id, issue_id, revision); UNIQUE (investigation_id, result_id, revision); CHECK (num_nonnulls(metadata_revision_id,annotation_id,variable_id,condition_id,test_link_id,test_relation_id,issue_id,result_id) = 1); CHECK (revision > 0); CHECK (supersedes_id IS NULL OR supersedes_id <> id); CHECK (decision IN ('approved','rejected','revoked','needs_review','resolved','open')); UNIQUE (investigation_id, metadata_revision_id, revision); CHECK ((applicability_policy_version IS NOT NULL) = (result_id IS NOT NULL AND decision = 'approved')); CHECK ((applicability_unresolved_count IS NOT NULL) = (result_id IS NOT NULL AND decision = 'approved')); CHECK (applicability_policy_version IS NULL OR applicability_policy_version = 'identity-issue-snapshot-v1'); CHECK (applicability_unresolved_count IS NULL OR applicability_unresolved_count = 0).

Purpose and rules: N1 snapshot attestation and sealed decision/applicability membership. Local checks do not replace exact-set and target validation. Scoped lookup indexes and the three partial membership indexes are listed in the illustrative DDL.

### analysis_protocol

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| issue_policy | text | no | — |
| coverage_policy | text | no | — |
| investigation_id | uuid | no | PK; investigation, evidence_reference |
| id | uuid | no | PK; — |
| protocol_code | text | no | — |
| protocol_version | text | no | — |
| description | text | no | — |
| requirements_schema_version | text | no | — |
| display_metadata | jsonb | no | — |
| evidence_id | uuid | no | evidence_reference |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, protocol_code, protocol_version); CHECK (display_metadata = '{}'::jsonb); CHECK (requirements_schema_version = 'relational-v1').

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### analytical_eligibility

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| segment_id | uuid | yes | condition_segment |
| investigation_id | uuid | no | PK; investigation, analysis_protocol, observation, experimental_test, analytical_eligibility, semantic_annotation, review_event, experimental_condition, review_event, evidence_reference, condition_segment |
| id | uuid | no | PK; — |
| protocol_id | uuid | no | analysis_protocol |
| observation_id | uuid | yes | observation |
| experimental_test_id | uuid | yes | experimental_test |
| revision | integer | no | — |
| supersedes_id | uuid | yes | analytical_eligibility |
| eligibility_status | text | no | — |
| annotation_id | uuid | yes | semantic_annotation |
| annotation_review_id | uuid | yes | review_event |
| condition_id | uuid | yes | experimental_condition |
| condition_review_id | uuid | yes | review_event |
| reason | text | no | — |
| evidence_id | uuid | no | evidence_reference |
| reviewer_ref | text | no | — |
| reviewed_at | timestamptz | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, protocol_id, observation_id, revision); UNIQUE (investigation_id, protocol_id, experimental_test_id, segment_id, revision); UNIQUE (investigation_id, supersedes_id); CHECK (num_nonnulls(observation_id,experimental_test_id) = 1); CHECK (revision > 0); CHECK (supersedes_id IS NULL OR supersedes_id <> id); CHECK (eligibility_status IN ('eligible','ineligible','needs_review','withdrawn')); CHECK (eligibility_status <> 'eligible' OR observation_id IS NULL OR (annotation_id IS NOT NULL AND annotation_review_id IS NOT NULL)); CHECK (eligibility_status <> 'eligible' OR experimental_test_id IS NULL OR (condition_id IS NOT NULL AND condition_review_id IS NOT NULL)); CHECK ((annotation_id IS NULL) = (annotation_review_id IS NULL)); CHECK ((condition_id IS NULL) = (condition_review_id IS NULL)); CHECK ((experimental_test_id IS NOT NULL) = (segment_id IS NOT NULL)).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### analytical_result

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, analysis_protocol, source_document |
| id | uuid | no | PK; — |
| protocol_id | uuid | no | analysis_protocol |
| method | text | no | — |
| method_version | text | no | — |
| parameters | jsonb | no | — |
| result_kind | text | no | — |
| numeric_value | numeric | yes | — |
| unit | text | yes | — |
| unit_status | text | no | — |
| text_value | text | yes | — |
| artifact_document_id | uuid | yes | source_document |
| producer_ref | text | no | — |
| uncertainty | jsonb | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); CHECK (result_kind IN ('numeric','text','artifact')); CHECK (unit_status IN ('known','unknown','not_applicable')); CHECK ((unit_status = 'known') = (unit IS NOT NULL)); CHECK ((result_kind = 'numeric') = (numeric_value IS NOT NULL)); CHECK ((result_kind = 'text') = (text_value IS NOT NULL)); CHECK ((result_kind = 'artifact') = (artifact_document_id IS NOT NULL)); CHECK (numeric_value IS NULL OR numeric_value::text NOT IN ('NaN','Infinity','-Infinity')); CHECK (jsonb_typeof(parameters) = 'object'); CHECK (jsonb_typeof(uncertainty) = 'object').

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### result_input

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| segment_id | uuid | no | condition_segment |
| investigation_id | uuid | no | PK; investigation, analytical_result, semantic_annotation, analytical_eligibility, test_source_record, review_event, condition_segment |
| id | uuid | no | PK; — |
| result_id | uuid | no | analytical_result |
| annotation_id | uuid | no | semantic_annotation |
| eligibility_id | uuid | no | analytical_eligibility |
| test_link_id | uuid | no | test_source_record |
| test_link_review_id | uuid | no | review_event |
| input_role | text | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, result_id, annotation_id, input_role).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### result_condition

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, analytical_result, experimental_condition, analytical_eligibility |
| id | uuid | no | PK; — |
| result_id | uuid | no | analytical_result |
| condition_id | uuid | no | experimental_condition |
| eligibility_id | uuid | no | analytical_eligibility |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, result_id, condition_id).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### result_evidence

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, analytical_result, evidence_reference |
| id | uuid | no | PK; — |
| result_id | uuid | no | analytical_result |
| evidence_id | uuid | no | evidence_reference |
| role | text | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, result_id, evidence_id, role).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### condition_segment

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, experimental_test, evidence_reference |
| id | uuid | no | PK; — |
| experimental_test_id | uuid | no | experimental_test |
| segment_key | text | no | — |
| scope_status | text | no | — |
| description | text | no | — |
| evidence_id | uuid | no | evidence_reference |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); CHECK (scope_status IN ('documented','unknown')); UNIQUE (investigation_id, experimental_test_id, segment_key).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### instrument

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, evidence_reference |
| id | uuid | no | PK; — |
| instrument_code | text | no | — |
| description | text | no | — |
| evidence_id | uuid | no | evidence_reference |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, instrument_code).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### condition_role

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, evidence_reference |
| id | uuid | no | PK; — |
| role_code | text | no | — |
| definition | text | no | — |
| variable_category | text | no | — |
| evidence_id | uuid | no | evidence_reference |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, role_code).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### condition_component

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, experimental_condition, condition_role, instrument, scientific_variable, semantic_annotation, evidence_reference |
| id | uuid | no | PK; — |
| condition_id | uuid | no | experimental_condition |
| role_id | uuid | no | condition_role |
| slot | integer | no | — |
| instrument_id | uuid | yes | instrument |
| instrument_status | text | no | — |
| variable_id | uuid | no | scientific_variable |
| annotation_id | uuid | yes | semantic_annotation |
| value_status | text | no | — |
| evidence_id | uuid | no | evidence_reference |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); CHECK (slot > 0); CHECK (value_status IN ('known','unknown','not_applicable')); CHECK ((value_status = 'known') = (annotation_id IS NOT NULL)); CHECK (instrument_status IN ('identified','unknown','not_applicable')); CHECK ((instrument_status = 'identified') = (instrument_id IS NOT NULL)); UNIQUE (investigation_id, condition_id, role_id, slot).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### protocol_requirement

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, analysis_protocol, scientific_variable, condition_role, evidence_reference |
| id | uuid | no | PK; — |
| protocol_id | uuid | no | analysis_protocol |
| requirement_key | text | no | — |
| target_kind | text | no | — |
| variable_id | uuid | no | scientific_variable |
| role_id | uuid | yes | condition_role |
| phase | text | no | — |
| min_count | integer | no | — |
| max_count | integer | no | — |
| value_policy | text | no | — |
| stability_policy | text | no | — |
| instrument_policy | text | no | — |
| evidence_id | uuid | no | evidence_reference |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, protocol_id, requirement_key); CHECK (target_kind IN ('input','condition')); CHECK ((target_kind = 'condition') = (role_id IS NOT NULL)); CHECK (min_count > 0 AND max_count >= min_count); CHECK (value_policy IN ('numeric_only','numeric_or_censored','categorical')); CHECK (stability_policy IN ('stable_required','transient_allowed','not_applicable')); CHECK (instrument_policy IN ('identified_required','not_required')).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### protocol_unit_rule

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, protocol_requirement, evidence_reference |
| id | uuid | no | PK; — |
| requirement_id | uuid | no | protocol_requirement |
| unit_text | text | no | — |
| unit_basis | text | no | — |
| method | text | no | — |
| method_version | text | no | — |
| evidence_id | uuid | no | evidence_reference |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); UNIQUE (investigation_id, requirement_id, unit_text, unit_basis, method, method_version).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### metadata_revision

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, source_document, metadata_revision, evidence_reference |
| id | uuid | no | PK; — |
| subject_kind | text | no | — |
| source_document_id | uuid | yes | source_document |
| revision | integer | no | — |
| supersedes_id | uuid | yes | metadata_revision |
| name | text | yes | — |
| description | text | yes | — |
| agency | text | yes | — |
| doi | text | yes | — |
| repository_url | text | yes | — |
| source_version | text | yes | — |
| evidence_id | uuid | no | evidence_reference |
| reason | text | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); CHECK (subject_kind IN ('investigation','source_document')); CHECK ((subject_kind = 'source_document') = (source_document_id IS NOT NULL)); CHECK (revision > 0); UNIQUE (investigation_id, source_document_id, revision); UNIQUE (investigation_id, supersedes_id).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### aggregate_seal

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, parse_run, semantic_annotation, experimental_condition, analysis_protocol, analytical_result, review_event |
| id | uuid | no | PK; — |
| parse_run_id | uuid | yes | parse_run |
| annotation_id | uuid | yes | semantic_annotation |
| condition_id | uuid | yes | experimental_condition |
| protocol_id | uuid | yes | analysis_protocol |
| result_id | uuid | yes | analytical_result |
| review_id | uuid | yes | review_event |
| seal_version | text | no | — |
| member_counts | jsonb | no | — |
| member_digest | text | no | — |
| sealed_by | text | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); CHECK (num_nonnulls(parse_run_id,annotation_id,condition_id,protocol_id,result_id,review_id) = 1); CHECK (seal_version = 'canonical-json-v2'); CHECK (jsonb_typeof(member_counts) = 'object'); CHECK (member_digest ~ '^[0-9a-f]{64}$'); UNIQUE (investigation_id, parse_run_id); UNIQUE (investigation_id, annotation_id); UNIQUE (investigation_id, condition_id); UNIQUE (investigation_id, protocol_id); UNIQUE (investigation_id, result_id); UNIQUE (investigation_id, review_id).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

### approval_dependency

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| entry_kind | text | no | — |
| snapshot_observation_id | uuid | yes | observation |
| snapshot_link_id | uuid | yes | test_source_record |
| snapshot_issue_id | uuid | yes | data_quality_issue |
| snapshot_review_id | uuid | yes | review_event |
| snapshot_review_seal_id | uuid | yes | aggregate_seal |
| investigation_id | uuid | no | PK; investigation, review_event, review_event, analytical_eligibility, aggregate_seal, observation, test_source_record, data_quality_issue, review_event, aggregate_seal |
| id | uuid | no | PK; — |
| owner_review_id | uuid | no | review_event |
| dependency_review_id | uuid | yes | review_event |
| dependency_eligibility_id | uuid | yes | analytical_eligibility |
| dependency_seal_id | uuid | yes | aggregate_seal |
| role | text | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); CHECK ((entry_kind = 'decision' AND num_nonnulls(dependency_review_id,dependency_eligibility_id,dependency_seal_id) = 1 AND num_nonnulls(snapshot_observation_id,snapshot_link_id,snapshot_issue_id,snapshot_review_id,snapshot_review_seal_id) = 0 AND role NOT IN ('scope_observation','scope_link','scope_issue')) OR (entry_kind = 'scope_observation' AND num_nonnulls(dependency_review_id,dependency_eligibility_id,dependency_seal_id) = 0 AND snapshot_observation_id IS NOT NULL AND num_nonnulls(snapshot_link_id,snapshot_issue_id,snapshot_review_id,snapshot_review_seal_id) = 0 AND role = 'scope_observation') OR (entry_kind = 'scope_link' AND num_nonnulls(dependency_review_id,dependency_eligibility_id,dependency_seal_id) = 0 AND snapshot_observation_id IS NOT NULL AND snapshot_link_id IS NOT NULL AND snapshot_issue_id IS NULL AND role = 'scope_link') OR (entry_kind = 'scope_issue' AND num_nonnulls(dependency_review_id,dependency_eligibility_id,dependency_seal_id) = 0 AND snapshot_observation_id IS NOT NULL AND snapshot_issue_id IS NOT NULL AND snapshot_link_id IS NULL AND role = 'scope_issue')); CHECK (dependency_review_id IS NULL OR dependency_review_id <> owner_review_id); UNIQUE (investigation_id, owner_review_id, dependency_review_id, role); UNIQUE (investigation_id, owner_review_id, dependency_eligibility_id, role); UNIQUE (investigation_id, owner_review_id, dependency_seal_id, role); CHECK (entry_kind IN ('decision','scope_observation','scope_link','scope_issue')); CHECK (snapshot_review_seal_id IS NULL OR snapshot_review_id IS NOT NULL).

Purpose and rules: N1 snapshot attestation and sealed decision/applicability membership. Local checks do not replace exact-set and target validation. Scoped lookup indexes and the three partial membership indexes are listed in the illustrative DDL.

### publication_event

| Column | Type | Nullable | Key/reference |
| --- | --- | --- | --- |
| investigation_id | uuid | no | PK; investigation, analytical_result, aggregate_seal, review_event, aggregate_seal, publication_event |
| id | uuid | no | PK; — |
| result_id | uuid | no | analytical_result |
| result_seal_id | uuid | no | aggregate_seal |
| result_review_id | uuid | no | review_event |
| review_seal_id | uuid | no | aggregate_seal |
| revision | integer | no | — |
| supersedes_id | uuid | yes | publication_event |
| action | text | no | — |
| actor_ref | text | no | — |
| reason | text | no | — |
| created_at | timestamptz | no | — |

Constraints: PRIMARY KEY (investigation_id, id); CHECK (revision > 0); CHECK (action IN ('publish','revoke')); UNIQUE (investigation_id, result_id, revision); UNIQUE (investigation_id, supersedes_id).

Purpose and rules: binding contract above; original core responsibilities remain raw provenance, identity, semantic interpretation, review or result lineage as indicated by table name. Indexes: PK/UNIQUE automatically cover identity/revision keys; each non-scope FK has an additional `(investigation_id, referenced_id)` lookup index in the DDL below.

## Example DDL — document only

```sql
CREATE TABLE investigation (
    id uuid NOT NULL,
    repository_code text NOT NULL,
    investigation_code text NOT NULL,
    name text NOT NULL,
    agency text NOT NULL,
    doi text,
    description text,
    source_repository_url text NOT NULL,
    metadata jsonb NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (repository_code, investigation_code),
    CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE TABLE source_document (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    original_filename text NOT NULL,
    source_type text NOT NULL,
    artifact_origin text NOT NULL,
    sha256 text NOT NULL,
    file_size_bytes bigint NOT NULL,
    storage_key text NOT NULL,
    source_version text,
    metadata jsonb NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, sha256),
    CHECK (source_type IN ('csv','xlsx','docx','pdf','image','video','other')),
    CHECK (artifact_origin IN ('external_original','generated_artifact','software_artifact')),
    CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    CHECK (file_size_bytes >= 0),
    CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE TABLE source_acquisition (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    source_document_id uuid,
    actual_filename text,
    portal_filename_alias text,
    source_page_url text,
    original_download_url text,
    local_relative_path text,
    retrieved_at timestamptz,
    verified_at timestamptz NOT NULL,
    verification_status text NOT NULL,
    verification_scope text NOT NULL,
    method text NOT NULL,
    actor_ref text NOT NULL,
    metadata jsonb NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    CHECK (verification_status IN ('verified','failed','unverified')),
    CHECK (verification_status <> 'verified' OR (source_document_id IS NOT NULL AND actual_filename IS NOT NULL)),
    CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE TABLE evidence_reference (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    source_document_id uuid NOT NULL,
    locator_kind text NOT NULL,
    locator_key text NOT NULL,
    locator_version text NOT NULL,
    locator jsonb NOT NULL,
    excerpt text,
    location_basis text NOT NULL,
    extraction_method text NOT NULL,
    extractor_version text NOT NULL,
    verification_status text NOT NULL,
    verification_scope text NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, source_document_id, locator_version, locator_key),
    CHECK (locator_kind IN ('csv','xlsx','docx','pdf','image','video','document')),
    CHECK (verification_status IN ('verified','unverified','needs_review')),
    CHECK (jsonb_typeof(locator) = 'object')
);

CREATE TABLE parse_run (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    source_document_id uuid NOT NULL,
    parser_name text NOT NULL,
    parser_version text NOT NULL,
    code_sha256 text NOT NULL,
    code_storage_key text NOT NULL,
    configuration_sha256 text NOT NULL,
    configuration jsonb NOT NULL,
    output_sha256 text NOT NULL,
    output_storage_key text NOT NULL,
    record_count bigint NOT NULL,
    status text NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, source_document_id, parser_name, parser_version, code_sha256, configuration_sha256, output_sha256),
    CHECK (status IN ('complete','failed')),
    CHECK (record_count >= 0),
    CHECK (code_sha256 ~ '^[0-9a-f]{64}$'),
    CHECK (configuration_sha256 ~ '^[0-9a-f]{64}$'),
    CHECK (jsonb_typeof(configuration) = 'object'),
    CHECK (output_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE TABLE source_field (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    parse_run_id uuid NOT NULL,
    table_key text NOT NULL,
    ordinal integer NOT NULL,
    original_header text NOT NULL,
    raw_unit text,
    raw_unit_status text NOT NULL,
    header_evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, parse_run_id, table_key, ordinal),
    UNIQUE (investigation_id, parse_run_id, id),
    CHECK (ordinal > 0),
    CHECK (raw_unit_status IN ('stated','not_stated','not_applicable')),
    CHECK ((raw_unit_status = 'stated') = (raw_unit IS NOT NULL))
);

CREATE TABLE source_record (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    parse_run_id uuid NOT NULL,
    table_key text NOT NULL,
    source_record_number bigint NOT NULL,
    source_row_id text NOT NULL,
    row_evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, parse_run_id, table_key, source_record_number),
    UNIQUE (investigation_id, parse_run_id, id),
    UNIQUE (investigation_id, parse_run_id, source_row_id),
    CHECK (source_record_number > 0)
);

CREATE TABLE experimental_test (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    identity_namespace text NOT NULL,
    test_identifier text NOT NULL,
    identity_evidence_id uuid NOT NULL,
    metadata jsonb NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, identity_namespace, test_identifier),
    CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE TABLE test_source_record (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    experimental_test_id uuid NOT NULL,
    source_record_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    match_method text NOT NULL,
    method_version text NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, experimental_test_id, source_record_id)
);

CREATE TABLE test_relationship (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    left_test_id uuid NOT NULL,
    right_test_id uuid NOT NULL,
    relationship_type text NOT NULL,
    evidence_id uuid NOT NULL,
    description text NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, left_test_id, right_test_id, relationship_type, evidence_id),
    CHECK (left_test_id <> right_test_id)
);

CREATE TABLE observation (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    parse_run_id uuid NOT NULL,
    source_record_id uuid NOT NULL,
    source_field_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    raw_value text,
    source_value_kind text NOT NULL,
    unit_origin text NOT NULL,
    raw_unit text,
    unit_evidence_id uuid,
    parser_classification text NOT NULL,
    parser_flags jsonb NOT NULL,
    original_representation jsonb NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, parse_run_id, source_record_id, source_field_id),
    CHECK (source_value_kind IN ('text','numeric_lexeme','empty_cell','other')),
    CHECK (unit_origin IN ('field','cell','not_stated','not_applicable')),
    CHECK ((unit_origin = 'cell') = (raw_unit IS NOT NULL)),
    CHECK ((unit_origin = 'cell') = (unit_evidence_id IS NOT NULL)),
    CHECK ((source_value_kind = 'empty_cell') = (raw_value IS NULL)),
    CHECK (jsonb_typeof(parser_flags) = 'object'),
    CHECK (jsonb_typeof(original_representation) = 'object')
);

CREATE TABLE scientific_variable (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    variable_code text NOT NULL,
    definition_version integer NOT NULL,
    canonical_name text NOT NULL,
    description text NOT NULL,
    physical_quantity text,
    canonical_unit text,
    unit_basis text NOT NULL,
    variable_category text NOT NULL,
    measurement_type text NOT NULL,
    definition_status text NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, variable_code, definition_version),
    CHECK (definition_version > 0),
    CHECK (variable_category IN ('measurement','identifier','instrument_setting','condition','context')),
    CHECK (definition_status IN ('confirmed','partially_confirmed','unresolved','identifier_only','not_applicable'))
);

CREATE TABLE semantic_annotation (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    observation_id uuid NOT NULL,
    variable_id uuid NOT NULL,
    interpretation_key text NOT NULL,
    revision integer NOT NULL,
    supersedes_id uuid,
    value_kind text NOT NULL,
    numeric_value numeric,
    bound_value numeric,
    comparator text,
    text_value text,
    date_value date,
    interpreted_unit text,
    unit_status text NOT NULL,
    observed_phase text,
    transformation_method text NOT NULL,
    transformation_version text NOT NULL,
    parameters jsonb NOT NULL,
    uncertainty jsonb NOT NULL,
    primary_evidence_id uuid NOT NULL,
    author_ref text NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, observation_id, interpretation_key, revision),
    UNIQUE (investigation_id, supersedes_id),
    CHECK (revision > 0),
    CHECK (supersedes_id IS NULL OR supersedes_id <> id),
    CHECK (value_kind IN ('numeric','censored','text','date','missing','unresolved','sequence')),
    CHECK (unit_status IN ('known','unknown','not_applicable')),
    CHECK ((unit_status = 'known') = (interpreted_unit IS NOT NULL)),
    CHECK ((value_kind = 'numeric') = (numeric_value IS NOT NULL)),
    CHECK ((value_kind = 'censored') = (bound_value IS NOT NULL)),
    CHECK ((value_kind = 'censored') = (comparator IS NOT NULL)),
    CHECK (comparator IS NULL OR comparator IN ('<','<=','>','>=')),
    CHECK ((value_kind = 'date') = (date_value IS NOT NULL)),
    CHECK ((value_kind IN ('text','missing','unresolved','sequence')) = (text_value IS NOT NULL)),
    CHECK (numeric_value IS NULL OR numeric_value::text NOT IN ('NaN','Infinity','-Infinity')),
    CHECK (bound_value IS NULL OR bound_value::text NOT IN ('NaN','Infinity','-Infinity')),
    CHECK (jsonb_typeof(parameters) = 'object'),
    CHECK (jsonb_typeof(uncertainty) = 'object')
);

CREATE TABLE annotation_evidence (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    annotation_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    role text NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, annotation_id, evidence_id, role)
);

CREATE TABLE experimental_condition (
    segment_id uuid NOT NULL,
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    experimental_test_id uuid NOT NULL,
    segment_key text NOT NULL,
    revision integer NOT NULL,
    supersedes_id uuid,
    scope_description text NOT NULL,
    airflow_stability text NOT NULL,
    evidence_id uuid NOT NULL,
    extension_metadata jsonb NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, experimental_test_id, segment_key, revision),
    UNIQUE (investigation_id, supersedes_id),
    CHECK (revision > 0),
    CHECK (supersedes_id IS NULL OR supersedes_id <> id),
    CHECK (airflow_stability IN ('stable','transient','unknown','not_applicable')),
    CHECK (extension_metadata = '{}'::jsonb)
);

CREATE TABLE data_quality_issue (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    observation_id uuid,
    experimental_test_id uuid,
    issue_type text NOT NULL,
    description text NOT NULL,
    severity text NOT NULL,
    detector_method text NOT NULL,
    detector_version text NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    CHECK (num_nonnulls(observation_id,experimental_test_id) = 1),
    CHECK (severity IN ('info','review','blocking'))
);

CREATE TABLE review_event (
    applicability_policy_version text,
    applicability_unresolved_count integer,
    metadata_revision_id uuid,
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    annotation_id uuid,
    variable_id uuid,
    condition_id uuid,
    test_link_id uuid,
    test_relation_id uuid,
    issue_id uuid,
    result_id uuid,
    revision integer NOT NULL,
    supersedes_id uuid,
    decision text NOT NULL,
    rationale text NOT NULL,
    evidence_id uuid NOT NULL,
    reviewer_ref text NOT NULL,
    reviewed_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, supersedes_id),
    UNIQUE (investigation_id, annotation_id, revision),
    UNIQUE (investigation_id, variable_id, revision),
    UNIQUE (investigation_id, condition_id, revision),
    UNIQUE (investigation_id, test_link_id, revision),
    UNIQUE (investigation_id, test_relation_id, revision),
    UNIQUE (investigation_id, issue_id, revision),
    UNIQUE (investigation_id, result_id, revision),
    CHECK (num_nonnulls(metadata_revision_id,annotation_id,variable_id,condition_id,test_link_id,test_relation_id,issue_id,result_id) = 1),
    CHECK (revision > 0),
    CHECK (supersedes_id IS NULL OR supersedes_id <> id),
    CHECK (decision IN ('approved','rejected','revoked','needs_review','resolved','open')),
    UNIQUE (investigation_id, metadata_revision_id, revision),
    CHECK ((applicability_policy_version IS NOT NULL) = (result_id IS NOT NULL AND decision = 'approved')),
    CHECK ((applicability_unresolved_count IS NOT NULL) = (result_id IS NOT NULL AND decision = 'approved')),
    CHECK (applicability_policy_version IS NULL OR applicability_policy_version = 'identity-issue-snapshot-v1'),
    CHECK (applicability_unresolved_count IS NULL OR applicability_unresolved_count = 0)
);

CREATE TABLE analysis_protocol (
    issue_policy text NOT NULL CHECK (issue_policy = 'all_unresolved_review_or_blocking'),
    coverage_policy text NOT NULL CHECK (coverage_policy = 'every_input_test_segment'),
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    protocol_code text NOT NULL,
    protocol_version text NOT NULL,
    description text NOT NULL,
    requirements_schema_version text NOT NULL,
    display_metadata jsonb NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, protocol_code, protocol_version),
    CHECK (display_metadata = '{}'::jsonb),
    CHECK (requirements_schema_version = 'relational-v1')
);

CREATE TABLE analytical_eligibility (
    segment_id uuid,
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    protocol_id uuid NOT NULL,
    observation_id uuid,
    experimental_test_id uuid,
    revision integer NOT NULL,
    supersedes_id uuid,
    eligibility_status text NOT NULL,
    annotation_id uuid,
    annotation_review_id uuid,
    condition_id uuid,
    condition_review_id uuid,
    reason text NOT NULL,
    evidence_id uuid NOT NULL,
    reviewer_ref text NOT NULL,
    reviewed_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, protocol_id, observation_id, revision),
    UNIQUE (investigation_id, protocol_id, experimental_test_id, segment_id, revision),
    UNIQUE (investigation_id, supersedes_id),
    CHECK (num_nonnulls(observation_id,experimental_test_id) = 1),
    CHECK (revision > 0),
    CHECK (supersedes_id IS NULL OR supersedes_id <> id),
    CHECK (eligibility_status IN ('eligible','ineligible','needs_review','withdrawn')),
    CHECK (eligibility_status <> 'eligible' OR observation_id IS NULL OR (annotation_id IS NOT NULL AND annotation_review_id IS NOT NULL)),
    CHECK (eligibility_status <> 'eligible' OR experimental_test_id IS NULL OR (condition_id IS NOT NULL AND condition_review_id IS NOT NULL)),
    CHECK ((annotation_id IS NULL) = (annotation_review_id IS NULL)),
    CHECK ((condition_id IS NULL) = (condition_review_id IS NULL)),
    CHECK ((experimental_test_id IS NOT NULL) = (segment_id IS NOT NULL))
);

CREATE TABLE analytical_result (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    protocol_id uuid NOT NULL,
    method text NOT NULL,
    method_version text NOT NULL,
    parameters jsonb NOT NULL,
    result_kind text NOT NULL,
    numeric_value numeric,
    unit text,
    unit_status text NOT NULL,
    text_value text,
    artifact_document_id uuid,
    producer_ref text NOT NULL,
    uncertainty jsonb NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    CHECK (result_kind IN ('numeric','text','artifact')),
    CHECK (unit_status IN ('known','unknown','not_applicable')),
    CHECK ((unit_status = 'known') = (unit IS NOT NULL)),
    CHECK ((result_kind = 'numeric') = (numeric_value IS NOT NULL)),
    CHECK ((result_kind = 'text') = (text_value IS NOT NULL)),
    CHECK ((result_kind = 'artifact') = (artifact_document_id IS NOT NULL)),
    CHECK (numeric_value IS NULL OR numeric_value::text NOT IN ('NaN','Infinity','-Infinity')),
    CHECK (jsonb_typeof(parameters) = 'object'),
    CHECK (jsonb_typeof(uncertainty) = 'object')
);

CREATE TABLE result_input (
    segment_id uuid NOT NULL,
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    result_id uuid NOT NULL,
    annotation_id uuid NOT NULL,
    eligibility_id uuid NOT NULL,
    test_link_id uuid NOT NULL,
    test_link_review_id uuid NOT NULL,
    input_role text NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, result_id, annotation_id, input_role)
);

CREATE TABLE result_condition (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    result_id uuid NOT NULL,
    condition_id uuid NOT NULL,
    eligibility_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, result_id, condition_id)
);

CREATE TABLE result_evidence (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    result_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    role text NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, result_id, evidence_id, role)
);

CREATE TABLE condition_segment (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    experimental_test_id uuid NOT NULL,
    segment_key text NOT NULL,
    scope_status text NOT NULL,
    description text NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    CHECK (scope_status IN ('documented','unknown')),
    UNIQUE (investigation_id, experimental_test_id, segment_key)
);

CREATE TABLE instrument (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    instrument_code text NOT NULL,
    description text NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, instrument_code)
);

CREATE TABLE condition_role (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    role_code text NOT NULL,
    definition text NOT NULL,
    variable_category text NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, role_code)
);

CREATE TABLE condition_component (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    condition_id uuid NOT NULL,
    role_id uuid NOT NULL,
    slot integer NOT NULL,
    instrument_id uuid,
    instrument_status text NOT NULL,
    variable_id uuid NOT NULL,
    annotation_id uuid,
    value_status text NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    CHECK (slot > 0),
    CHECK (value_status IN ('known','unknown','not_applicable')),
    CHECK ((value_status = 'known') = (annotation_id IS NOT NULL)),
    CHECK (instrument_status IN ('identified','unknown','not_applicable')),
    CHECK ((instrument_status = 'identified') = (instrument_id IS NOT NULL)),
    UNIQUE (investigation_id, condition_id, role_id, slot)
);

CREATE TABLE protocol_requirement (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    protocol_id uuid NOT NULL,
    requirement_key text NOT NULL,
    target_kind text NOT NULL,
    variable_id uuid NOT NULL,
    role_id uuid,
    phase text NOT NULL,
    min_count integer NOT NULL,
    max_count integer NOT NULL,
    value_policy text NOT NULL,
    stability_policy text NOT NULL,
    instrument_policy text NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, protocol_id, requirement_key),
    CHECK (target_kind IN ('input','condition')),
    CHECK ((target_kind = 'condition') = (role_id IS NOT NULL)),
    CHECK (min_count > 0 AND max_count >= min_count),
    CHECK (value_policy IN ('numeric_only','numeric_or_censored','categorical')),
    CHECK (stability_policy IN ('stable_required','transient_allowed','not_applicable')),
    CHECK (instrument_policy IN ('identified_required','not_required'))
);

CREATE TABLE protocol_unit_rule (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    requirement_id uuid NOT NULL,
    unit_text text NOT NULL,
    unit_basis text NOT NULL,
    method text NOT NULL,
    method_version text NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    UNIQUE (investigation_id, requirement_id, unit_text, unit_basis, method, method_version)
);

CREATE TABLE metadata_revision (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    subject_kind text NOT NULL,
    source_document_id uuid,
    revision integer NOT NULL,
    supersedes_id uuid,
    name text,
    description text,
    agency text,
    doi text,
    repository_url text,
    source_version text,
    evidence_id uuid NOT NULL,
    reason text NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    CHECK (subject_kind IN ('investigation','source_document')),
    CHECK ((subject_kind = 'source_document') = (source_document_id IS NOT NULL)),
    CHECK (revision > 0),
    UNIQUE (investigation_id, source_document_id, revision),
    UNIQUE (investigation_id, supersedes_id)
);

CREATE TABLE aggregate_seal (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    parse_run_id uuid,
    annotation_id uuid,
    condition_id uuid,
    protocol_id uuid,
    result_id uuid,
    review_id uuid,
    seal_version text NOT NULL,
    member_counts jsonb NOT NULL,
    member_digest text NOT NULL,
    sealed_by text NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    CHECK (num_nonnulls(parse_run_id,annotation_id,condition_id,protocol_id,result_id,review_id) = 1),
    CHECK (seal_version = 'canonical-json-v2'),
    CHECK (jsonb_typeof(member_counts) = 'object'),
    CHECK (member_digest ~ '^[0-9a-f]{64}$'),
    UNIQUE (investigation_id, parse_run_id),
    UNIQUE (investigation_id, annotation_id),
    UNIQUE (investigation_id, condition_id),
    UNIQUE (investigation_id, protocol_id),
    UNIQUE (investigation_id, result_id),
    UNIQUE (investigation_id, review_id)
);

CREATE TABLE approval_dependency (
    entry_kind text NOT NULL,
    snapshot_observation_id uuid,
    snapshot_link_id uuid,
    snapshot_issue_id uuid,
    snapshot_review_id uuid,
    snapshot_review_seal_id uuid,
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    owner_review_id uuid NOT NULL,
    dependency_review_id uuid,
    dependency_eligibility_id uuid,
    dependency_seal_id uuid,
    role text NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    CHECK ((entry_kind = 'decision' AND num_nonnulls(dependency_review_id,dependency_eligibility_id,dependency_seal_id) = 1 AND num_nonnulls(snapshot_observation_id,snapshot_link_id,snapshot_issue_id,snapshot_review_id,snapshot_review_seal_id) = 0 AND role NOT IN ('scope_observation','scope_link','scope_issue')) OR (entry_kind = 'scope_observation' AND num_nonnulls(dependency_review_id,dependency_eligibility_id,dependency_seal_id) = 0 AND snapshot_observation_id IS NOT NULL AND num_nonnulls(snapshot_link_id,snapshot_issue_id,snapshot_review_id,snapshot_review_seal_id) = 0 AND role = 'scope_observation') OR (entry_kind = 'scope_link' AND num_nonnulls(dependency_review_id,dependency_eligibility_id,dependency_seal_id) = 0 AND snapshot_observation_id IS NOT NULL AND snapshot_link_id IS NOT NULL AND snapshot_issue_id IS NULL AND role = 'scope_link') OR (entry_kind = 'scope_issue' AND num_nonnulls(dependency_review_id,dependency_eligibility_id,dependency_seal_id) = 0 AND snapshot_observation_id IS NOT NULL AND snapshot_issue_id IS NOT NULL AND snapshot_link_id IS NULL AND role = 'scope_issue')),
    CHECK (dependency_review_id IS NULL OR dependency_review_id <> owner_review_id),
    UNIQUE (investigation_id, owner_review_id, dependency_review_id, role),
    UNIQUE (investigation_id, owner_review_id, dependency_eligibility_id, role),
    UNIQUE (investigation_id, owner_review_id, dependency_seal_id, role),
    CHECK (entry_kind IN ('decision','scope_observation','scope_link','scope_issue')),
    CHECK (snapshot_review_seal_id IS NULL OR snapshot_review_id IS NOT NULL)
);

CREATE TABLE publication_event (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    result_id uuid NOT NULL,
    result_seal_id uuid NOT NULL,
    result_review_id uuid NOT NULL,
    review_seal_id uuid NOT NULL,
    revision integer NOT NULL,
    supersedes_id uuid,
    action text NOT NULL,
    actor_ref text NOT NULL,
    reason text NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (investigation_id, id),
    CHECK (revision > 0),
    CHECK (action IN ('publish','revoke')),
    UNIQUE (investigation_id, result_id, revision),
    UNIQUE (investigation_id, supersedes_id)
);
ALTER TABLE source_document ADD CONSTRAINT source_document_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE source_acquisition ADD CONSTRAINT source_acquisition_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE source_acquisition ADD CONSTRAINT source_acquisition_source_document_id_fk FOREIGN KEY (investigation_id, source_document_id) REFERENCES source_document (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE evidence_reference ADD CONSTRAINT evidence_reference_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE evidence_reference ADD CONSTRAINT evidence_reference_source_document_id_fk FOREIGN KEY (investigation_id, source_document_id) REFERENCES source_document (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE parse_run ADD CONSTRAINT parse_run_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE parse_run ADD CONSTRAINT parse_run_source_document_id_fk FOREIGN KEY (investigation_id, source_document_id) REFERENCES source_document (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE source_field ADD CONSTRAINT source_field_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE source_field ADD CONSTRAINT source_field_parse_run_id_fk FOREIGN KEY (investigation_id, parse_run_id) REFERENCES parse_run (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE source_field ADD CONSTRAINT source_field_header_evidence_id_fk FOREIGN KEY (investigation_id, header_evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE source_record ADD CONSTRAINT source_record_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE source_record ADD CONSTRAINT source_record_parse_run_id_fk FOREIGN KEY (investigation_id, parse_run_id) REFERENCES parse_run (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE source_record ADD CONSTRAINT source_record_row_evidence_id_fk FOREIGN KEY (investigation_id, row_evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE experimental_test ADD CONSTRAINT experimental_test_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE experimental_test ADD CONSTRAINT experimental_test_identity_evidence_id_fk FOREIGN KEY (investigation_id, identity_evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE test_source_record ADD CONSTRAINT test_source_record_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE test_source_record ADD CONSTRAINT test_source_record_experimental_test_id_fk FOREIGN KEY (investigation_id, experimental_test_id) REFERENCES experimental_test (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE test_source_record ADD CONSTRAINT test_source_record_source_record_id_fk FOREIGN KEY (investigation_id, source_record_id) REFERENCES source_record (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE test_source_record ADD CONSTRAINT test_source_record_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE test_relationship ADD CONSTRAINT test_relationship_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE test_relationship ADD CONSTRAINT test_relationship_left_test_id_fk FOREIGN KEY (investigation_id, left_test_id) REFERENCES experimental_test (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE test_relationship ADD CONSTRAINT test_relationship_right_test_id_fk FOREIGN KEY (investigation_id, right_test_id) REFERENCES experimental_test (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE test_relationship ADD CONSTRAINT test_relationship_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE observation ADD CONSTRAINT observation_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE observation ADD CONSTRAINT observation_parse_run_id_fk FOREIGN KEY (investigation_id, parse_run_id) REFERENCES parse_run (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE observation ADD CONSTRAINT observation_source_record_id_fk FOREIGN KEY (investigation_id, source_record_id) REFERENCES source_record (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE observation ADD CONSTRAINT observation_source_field_id_fk FOREIGN KEY (investigation_id, source_field_id) REFERENCES source_field (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE observation ADD CONSTRAINT observation_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE observation ADD CONSTRAINT observation_unit_evidence_id_fk FOREIGN KEY (investigation_id, unit_evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE scientific_variable ADD CONSTRAINT scientific_variable_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE scientific_variable ADD CONSTRAINT scientific_variable_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE semantic_annotation ADD CONSTRAINT semantic_annotation_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE semantic_annotation ADD CONSTRAINT semantic_annotation_observation_id_fk FOREIGN KEY (investigation_id, observation_id) REFERENCES observation (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE semantic_annotation ADD CONSTRAINT semantic_annotation_variable_id_fk FOREIGN KEY (investigation_id, variable_id) REFERENCES scientific_variable (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE semantic_annotation ADD CONSTRAINT semantic_annotation_supersedes_id_fk FOREIGN KEY (investigation_id, supersedes_id) REFERENCES semantic_annotation (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE semantic_annotation ADD CONSTRAINT semantic_annotation_primary_evidence_id_fk FOREIGN KEY (investigation_id, primary_evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE annotation_evidence ADD CONSTRAINT annotation_evidence_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE annotation_evidence ADD CONSTRAINT annotation_evidence_annotation_id_fk FOREIGN KEY (investigation_id, annotation_id) REFERENCES semantic_annotation (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE annotation_evidence ADD CONSTRAINT annotation_evidence_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE experimental_condition ADD CONSTRAINT experimental_condition_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE experimental_condition ADD CONSTRAINT experimental_condition_experimental_test_id_fk FOREIGN KEY (investigation_id, experimental_test_id) REFERENCES experimental_test (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE experimental_condition ADD CONSTRAINT experimental_condition_supersedes_id_fk FOREIGN KEY (investigation_id, supersedes_id) REFERENCES experimental_condition (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE experimental_condition ADD CONSTRAINT experimental_condition_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE data_quality_issue ADD CONSTRAINT data_quality_issue_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE data_quality_issue ADD CONSTRAINT data_quality_issue_observation_id_fk FOREIGN KEY (investigation_id, observation_id) REFERENCES observation (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE data_quality_issue ADD CONSTRAINT data_quality_issue_experimental_test_id_fk FOREIGN KEY (investigation_id, experimental_test_id) REFERENCES experimental_test (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE data_quality_issue ADD CONSTRAINT data_quality_issue_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE review_event ADD CONSTRAINT review_event_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE review_event ADD CONSTRAINT review_event_annotation_id_fk FOREIGN KEY (investigation_id, annotation_id) REFERENCES semantic_annotation (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE review_event ADD CONSTRAINT review_event_variable_id_fk FOREIGN KEY (investigation_id, variable_id) REFERENCES scientific_variable (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE review_event ADD CONSTRAINT review_event_condition_id_fk FOREIGN KEY (investigation_id, condition_id) REFERENCES experimental_condition (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE review_event ADD CONSTRAINT review_event_test_link_id_fk FOREIGN KEY (investigation_id, test_link_id) REFERENCES test_source_record (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE review_event ADD CONSTRAINT review_event_test_relation_id_fk FOREIGN KEY (investigation_id, test_relation_id) REFERENCES test_relationship (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE review_event ADD CONSTRAINT review_event_issue_id_fk FOREIGN KEY (investigation_id, issue_id) REFERENCES data_quality_issue (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE review_event ADD CONSTRAINT review_event_result_id_fk FOREIGN KEY (investigation_id, result_id) REFERENCES analytical_result (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE review_event ADD CONSTRAINT review_event_supersedes_id_fk FOREIGN KEY (investigation_id, supersedes_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE review_event ADD CONSTRAINT review_event_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE analysis_protocol ADD CONSTRAINT analysis_protocol_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE analysis_protocol ADD CONSTRAINT analysis_protocol_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_protocol_id_fk FOREIGN KEY (investigation_id, protocol_id) REFERENCES analysis_protocol (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_observation_id_fk FOREIGN KEY (investigation_id, observation_id) REFERENCES observation (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_experimental_test_id_fk FOREIGN KEY (investigation_id, experimental_test_id) REFERENCES experimental_test (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_supersedes_id_fk FOREIGN KEY (investigation_id, supersedes_id) REFERENCES analytical_eligibility (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_annotation_id_fk FOREIGN KEY (investigation_id, annotation_id) REFERENCES semantic_annotation (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_annotation_review_id_fk FOREIGN KEY (investigation_id, annotation_review_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_condition_id_fk FOREIGN KEY (investigation_id, condition_id) REFERENCES experimental_condition (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_condition_review_id_fk FOREIGN KEY (investigation_id, condition_review_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE analytical_result ADD CONSTRAINT analytical_result_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE analytical_result ADD CONSTRAINT analytical_result_protocol_id_fk FOREIGN KEY (investigation_id, protocol_id) REFERENCES analysis_protocol (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE analytical_result ADD CONSTRAINT analytical_result_artifact_document_id_fk FOREIGN KEY (investigation_id, artifact_document_id) REFERENCES source_document (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE result_input ADD CONSTRAINT result_input_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE result_input ADD CONSTRAINT result_input_result_id_fk FOREIGN KEY (investigation_id, result_id) REFERENCES analytical_result (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE result_input ADD CONSTRAINT result_input_annotation_id_fk FOREIGN KEY (investigation_id, annotation_id) REFERENCES semantic_annotation (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE result_input ADD CONSTRAINT result_input_eligibility_id_fk FOREIGN KEY (investigation_id, eligibility_id) REFERENCES analytical_eligibility (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE result_input ADD CONSTRAINT result_input_test_link_id_fk FOREIGN KEY (investigation_id, test_link_id) REFERENCES test_source_record (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE result_input ADD CONSTRAINT result_input_test_link_review_id_fk FOREIGN KEY (investigation_id, test_link_review_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE result_condition ADD CONSTRAINT result_condition_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE result_condition ADD CONSTRAINT result_condition_result_id_fk FOREIGN KEY (investigation_id, result_id) REFERENCES analytical_result (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE result_condition ADD CONSTRAINT result_condition_condition_id_fk FOREIGN KEY (investigation_id, condition_id) REFERENCES experimental_condition (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE result_condition ADD CONSTRAINT result_condition_eligibility_id_fk FOREIGN KEY (investigation_id, eligibility_id) REFERENCES analytical_eligibility (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE result_evidence ADD CONSTRAINT result_evidence_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE result_evidence ADD CONSTRAINT result_evidence_result_id_fk FOREIGN KEY (investigation_id, result_id) REFERENCES analytical_result (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE result_evidence ADD CONSTRAINT result_evidence_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE observation ADD CONSTRAINT observation_source_record_id_same_run_fk FOREIGN KEY (investigation_id, parse_run_id, source_record_id) REFERENCES source_record (investigation_id, parse_run_id, id) ON DELETE RESTRICT;
ALTER TABLE observation ADD CONSTRAINT observation_source_field_id_same_run_fk FOREIGN KEY (investigation_id, parse_run_id, source_field_id) REFERENCES source_field (investigation_id, parse_run_id, id) ON DELETE RESTRICT;
ALTER TABLE condition_segment ADD CONSTRAINT condition_segment_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE condition_segment ADD CONSTRAINT condition_segment_experimental_test_id_fk FOREIGN KEY (investigation_id, experimental_test_id) REFERENCES experimental_test (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE condition_segment ADD CONSTRAINT condition_segment_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE instrument ADD CONSTRAINT instrument_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE instrument ADD CONSTRAINT instrument_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE condition_role ADD CONSTRAINT condition_role_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE condition_role ADD CONSTRAINT condition_role_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE condition_component ADD CONSTRAINT condition_component_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE condition_component ADD CONSTRAINT condition_component_condition_id_fk FOREIGN KEY (investigation_id, condition_id) REFERENCES experimental_condition (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE condition_component ADD CONSTRAINT condition_component_role_id_fk FOREIGN KEY (investigation_id, role_id) REFERENCES condition_role (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE condition_component ADD CONSTRAINT condition_component_instrument_id_fk FOREIGN KEY (investigation_id, instrument_id) REFERENCES instrument (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE condition_component ADD CONSTRAINT condition_component_variable_id_fk FOREIGN KEY (investigation_id, variable_id) REFERENCES scientific_variable (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE condition_component ADD CONSTRAINT condition_component_annotation_id_fk FOREIGN KEY (investigation_id, annotation_id) REFERENCES semantic_annotation (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE condition_component ADD CONSTRAINT condition_component_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE experimental_condition ADD CONSTRAINT experimental_condition_segment_id_fk FOREIGN KEY (investigation_id, segment_id) REFERENCES condition_segment (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE result_input ADD CONSTRAINT result_input_segment_id_fk FOREIGN KEY (investigation_id, segment_id) REFERENCES condition_segment (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE protocol_requirement ADD CONSTRAINT protocol_requirement_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE protocol_requirement ADD CONSTRAINT protocol_requirement_protocol_id_fk FOREIGN KEY (investigation_id, protocol_id) REFERENCES analysis_protocol (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE protocol_requirement ADD CONSTRAINT protocol_requirement_variable_id_fk FOREIGN KEY (investigation_id, variable_id) REFERENCES scientific_variable (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE protocol_requirement ADD CONSTRAINT protocol_requirement_role_id_fk FOREIGN KEY (investigation_id, role_id) REFERENCES condition_role (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE protocol_requirement ADD CONSTRAINT protocol_requirement_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE protocol_unit_rule ADD CONSTRAINT protocol_unit_rule_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE protocol_unit_rule ADD CONSTRAINT protocol_unit_rule_requirement_id_fk FOREIGN KEY (investigation_id, requirement_id) REFERENCES protocol_requirement (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE protocol_unit_rule ADD CONSTRAINT protocol_unit_rule_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE metadata_revision ADD CONSTRAINT metadata_revision_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE metadata_revision ADD CONSTRAINT metadata_revision_source_document_id_fk FOREIGN KEY (investigation_id, source_document_id) REFERENCES source_document (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE metadata_revision ADD CONSTRAINT metadata_revision_supersedes_id_fk FOREIGN KEY (investigation_id, supersedes_id) REFERENCES metadata_revision (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE metadata_revision ADD CONSTRAINT metadata_revision_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE review_event ADD CONSTRAINT review_event_metadata_revision_id_fk FOREIGN KEY (investigation_id, metadata_revision_id) REFERENCES metadata_revision (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE aggregate_seal ADD CONSTRAINT aggregate_seal_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE aggregate_seal ADD CONSTRAINT aggregate_seal_parse_run_id_fk FOREIGN KEY (investigation_id, parse_run_id) REFERENCES parse_run (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE aggregate_seal ADD CONSTRAINT aggregate_seal_annotation_id_fk FOREIGN KEY (investigation_id, annotation_id) REFERENCES semantic_annotation (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE aggregate_seal ADD CONSTRAINT aggregate_seal_condition_id_fk FOREIGN KEY (investigation_id, condition_id) REFERENCES experimental_condition (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE aggregate_seal ADD CONSTRAINT aggregate_seal_protocol_id_fk FOREIGN KEY (investigation_id, protocol_id) REFERENCES analysis_protocol (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE aggregate_seal ADD CONSTRAINT aggregate_seal_result_id_fk FOREIGN KEY (investigation_id, result_id) REFERENCES analytical_result (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE aggregate_seal ADD CONSTRAINT aggregate_seal_review_id_fk FOREIGN KEY (investigation_id, review_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE approval_dependency ADD CONSTRAINT approval_dependency_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE approval_dependency ADD CONSTRAINT approval_dependency_owner_review_id_fk FOREIGN KEY (investigation_id, owner_review_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE approval_dependency ADD CONSTRAINT approval_dependency_dependency_review_id_fk FOREIGN KEY (investigation_id, dependency_review_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE approval_dependency ADD CONSTRAINT approval_dependency_dependency_eligibility_id_fk FOREIGN KEY (investigation_id, dependency_eligibility_id) REFERENCES analytical_eligibility (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE approval_dependency ADD CONSTRAINT approval_dependency_dependency_seal_id_fk FOREIGN KEY (investigation_id, dependency_seal_id) REFERENCES aggregate_seal (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE publication_event ADD CONSTRAINT publication_event_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT;
ALTER TABLE publication_event ADD CONSTRAINT publication_event_result_id_fk FOREIGN KEY (investigation_id, result_id) REFERENCES analytical_result (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE publication_event ADD CONSTRAINT publication_event_result_seal_id_fk FOREIGN KEY (investigation_id, result_seal_id) REFERENCES aggregate_seal (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE publication_event ADD CONSTRAINT publication_event_result_review_id_fk FOREIGN KEY (investigation_id, result_review_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE publication_event ADD CONSTRAINT publication_event_review_seal_id_fk FOREIGN KEY (investigation_id, review_seal_id) REFERENCES aggregate_seal (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE publication_event ADD CONSTRAINT publication_event_supersedes_id_fk FOREIGN KEY (investigation_id, supersedes_id) REFERENCES publication_event (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_segment_id_fk FOREIGN KEY (investigation_id, segment_id) REFERENCES condition_segment (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE approval_dependency ADD CONSTRAINT ad_snapshot_observation_id_fk FOREIGN KEY (investigation_id, snapshot_observation_id) REFERENCES observation (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE approval_dependency ADD CONSTRAINT ad_snapshot_link_id_fk FOREIGN KEY (investigation_id, snapshot_link_id) REFERENCES test_source_record (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE approval_dependency ADD CONSTRAINT ad_snapshot_issue_id_fk FOREIGN KEY (investigation_id, snapshot_issue_id) REFERENCES data_quality_issue (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE approval_dependency ADD CONSTRAINT ad_snapshot_review_id_fk FOREIGN KEY (investigation_id, snapshot_review_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT;
ALTER TABLE approval_dependency ADD CONSTRAINT ad_snapshot_review_seal_id_fk FOREIGN KEY (investigation_id, snapshot_review_seal_id) REFERENCES aggregate_seal (investigation_id, id) ON DELETE RESTRICT;
CREATE UNIQUE INDEX metadata_investigation_revision ON metadata_revision (investigation_id, revision) WHERE subject_kind = 'investigation';
CREATE INDEX lookup_2 ON source_acquisition (investigation_id, source_document_id);
CREATE INDEX lookup_4 ON evidence_reference (investigation_id, source_document_id);
CREATE INDEX lookup_6 ON parse_run (investigation_id, source_document_id);
CREATE INDEX lookup_8 ON source_field (investigation_id, parse_run_id);
CREATE INDEX lookup_9 ON source_field (investigation_id, header_evidence_id);
CREATE INDEX lookup_11 ON source_record (investigation_id, parse_run_id);
CREATE INDEX lookup_12 ON source_record (investigation_id, row_evidence_id);
CREATE INDEX lookup_14 ON experimental_test (investigation_id, identity_evidence_id);
CREATE INDEX lookup_16 ON test_source_record (investigation_id, experimental_test_id);
CREATE INDEX lookup_17 ON test_source_record (investigation_id, source_record_id);
CREATE INDEX lookup_18 ON test_source_record (investigation_id, evidence_id);
CREATE INDEX lookup_20 ON test_relationship (investigation_id, left_test_id);
CREATE INDEX lookup_21 ON test_relationship (investigation_id, right_test_id);
CREATE INDEX lookup_22 ON test_relationship (investigation_id, evidence_id);
CREATE INDEX lookup_24 ON observation (investigation_id, parse_run_id);
CREATE INDEX lookup_25 ON observation (investigation_id, source_record_id);
CREATE INDEX lookup_26 ON observation (investigation_id, source_field_id);
CREATE INDEX lookup_27 ON observation (investigation_id, evidence_id);
CREATE INDEX lookup_28 ON observation (investigation_id, unit_evidence_id);
CREATE INDEX lookup_30 ON scientific_variable (investigation_id, evidence_id);
CREATE INDEX lookup_32 ON semantic_annotation (investigation_id, observation_id);
CREATE INDEX lookup_33 ON semantic_annotation (investigation_id, variable_id);
CREATE INDEX lookup_34 ON semantic_annotation (investigation_id, supersedes_id);
CREATE INDEX lookup_35 ON semantic_annotation (investigation_id, primary_evidence_id);
CREATE INDEX lookup_37 ON annotation_evidence (investigation_id, annotation_id);
CREATE INDEX lookup_38 ON annotation_evidence (investigation_id, evidence_id);
CREATE INDEX lookup_40 ON experimental_condition (investigation_id, experimental_test_id);
CREATE INDEX lookup_41 ON experimental_condition (investigation_id, supersedes_id);
CREATE INDEX lookup_42 ON experimental_condition (investigation_id, evidence_id);
CREATE INDEX lookup_44 ON data_quality_issue (investigation_id, observation_id);
CREATE INDEX lookup_45 ON data_quality_issue (investigation_id, experimental_test_id);
CREATE INDEX lookup_46 ON data_quality_issue (investigation_id, evidence_id);
CREATE INDEX lookup_48 ON review_event (investigation_id, annotation_id);
CREATE INDEX lookup_49 ON review_event (investigation_id, variable_id);
CREATE INDEX lookup_50 ON review_event (investigation_id, condition_id);
CREATE INDEX lookup_51 ON review_event (investigation_id, test_link_id);
CREATE INDEX lookup_52 ON review_event (investigation_id, test_relation_id);
CREATE INDEX lookup_53 ON review_event (investigation_id, issue_id);
CREATE INDEX lookup_54 ON review_event (investigation_id, result_id);
CREATE INDEX lookup_55 ON review_event (investigation_id, supersedes_id);
CREATE INDEX lookup_56 ON review_event (investigation_id, evidence_id);
CREATE INDEX lookup_58 ON analysis_protocol (investigation_id, evidence_id);
CREATE INDEX lookup_60 ON analytical_eligibility (investigation_id, protocol_id);
CREATE INDEX lookup_61 ON analytical_eligibility (investigation_id, observation_id);
CREATE INDEX lookup_62 ON analytical_eligibility (investigation_id, experimental_test_id);
CREATE INDEX lookup_63 ON analytical_eligibility (investigation_id, supersedes_id);
CREATE INDEX lookup_64 ON analytical_eligibility (investigation_id, annotation_id);
CREATE INDEX lookup_65 ON analytical_eligibility (investigation_id, annotation_review_id);
CREATE INDEX lookup_66 ON analytical_eligibility (investigation_id, condition_id);
CREATE INDEX lookup_67 ON analytical_eligibility (investigation_id, condition_review_id);
CREATE INDEX lookup_68 ON analytical_eligibility (investigation_id, evidence_id);
CREATE INDEX lookup_70 ON analytical_result (investigation_id, protocol_id);
CREATE INDEX lookup_71 ON analytical_result (investigation_id, artifact_document_id);
CREATE INDEX lookup_73 ON result_input (investigation_id, result_id);
CREATE INDEX lookup_74 ON result_input (investigation_id, annotation_id);
CREATE INDEX lookup_75 ON result_input (investigation_id, eligibility_id);
CREATE INDEX lookup_76 ON result_input (investigation_id, test_link_id);
CREATE INDEX lookup_77 ON result_input (investigation_id, test_link_review_id);
CREATE INDEX lookup_79 ON result_condition (investigation_id, result_id);
CREATE INDEX lookup_80 ON result_condition (investigation_id, condition_id);
CREATE INDEX lookup_81 ON result_condition (investigation_id, eligibility_id);
CREATE INDEX lookup_83 ON result_evidence (investigation_id, result_id);
CREATE INDEX lookup_84 ON result_evidence (investigation_id, evidence_id);
CREATE INDEX lookup_85 ON observation (investigation_id, parse_run_id, source_record_id);
CREATE INDEX lookup_86 ON observation (investigation_id, parse_run_id, source_field_id);
CREATE INDEX lookup_88 ON condition_segment (investigation_id, experimental_test_id);
CREATE INDEX lookup_89 ON condition_segment (investigation_id, evidence_id);
CREATE INDEX lookup_91 ON instrument (investigation_id, evidence_id);
CREATE INDEX lookup_93 ON condition_role (investigation_id, evidence_id);
CREATE INDEX lookup_95 ON condition_component (investigation_id, condition_id);
CREATE INDEX lookup_96 ON condition_component (investigation_id, role_id);
CREATE INDEX lookup_97 ON condition_component (investigation_id, instrument_id);
CREATE INDEX lookup_98 ON condition_component (investigation_id, variable_id);
CREATE INDEX lookup_99 ON condition_component (investigation_id, annotation_id);
CREATE INDEX lookup_100 ON condition_component (investigation_id, evidence_id);
CREATE INDEX lookup_101 ON experimental_condition (investigation_id, segment_id);
CREATE INDEX lookup_102 ON result_input (investigation_id, segment_id);
CREATE INDEX lookup_104 ON protocol_requirement (investigation_id, protocol_id);
CREATE INDEX lookup_105 ON protocol_requirement (investigation_id, variable_id);
CREATE INDEX lookup_106 ON protocol_requirement (investigation_id, role_id);
CREATE INDEX lookup_107 ON protocol_requirement (investigation_id, evidence_id);
CREATE INDEX lookup_109 ON protocol_unit_rule (investigation_id, requirement_id);
CREATE INDEX lookup_110 ON protocol_unit_rule (investigation_id, evidence_id);
CREATE INDEX lookup_112 ON metadata_revision (investigation_id, source_document_id);
CREATE INDEX lookup_113 ON metadata_revision (investigation_id, supersedes_id);
CREATE INDEX lookup_114 ON metadata_revision (investigation_id, evidence_id);
CREATE INDEX lookup_115 ON review_event (investigation_id, metadata_revision_id);
CREATE INDEX lookup_117 ON aggregate_seal (investigation_id, parse_run_id);
CREATE INDEX lookup_118 ON aggregate_seal (investigation_id, annotation_id);
CREATE INDEX lookup_119 ON aggregate_seal (investigation_id, condition_id);
CREATE INDEX lookup_120 ON aggregate_seal (investigation_id, protocol_id);
CREATE INDEX lookup_121 ON aggregate_seal (investigation_id, result_id);
CREATE INDEX lookup_122 ON aggregate_seal (investigation_id, review_id);
CREATE INDEX lookup_124 ON approval_dependency (investigation_id, owner_review_id);
CREATE INDEX lookup_125 ON approval_dependency (investigation_id, dependency_review_id);
CREATE INDEX lookup_126 ON approval_dependency (investigation_id, dependency_eligibility_id);
CREATE INDEX lookup_127 ON approval_dependency (investigation_id, dependency_seal_id);
CREATE INDEX lookup_129 ON publication_event (investigation_id, result_id);
CREATE INDEX lookup_130 ON publication_event (investigation_id, result_seal_id);
CREATE INDEX lookup_131 ON publication_event (investigation_id, result_review_id);
CREATE INDEX lookup_132 ON publication_event (investigation_id, review_seal_id);
CREATE INDEX lookup_133 ON publication_event (investigation_id, supersedes_id);
CREATE INDEX lookup_134 ON analytical_eligibility (investigation_id, segment_id);
CREATE UNIQUE INDEX ad_scope_observation_once ON approval_dependency (investigation_id, owner_review_id, snapshot_observation_id) WHERE entry_kind = 'scope_observation';
CREATE UNIQUE INDEX ad_scope_link_once ON approval_dependency (investigation_id, owner_review_id, snapshot_observation_id, snapshot_link_id) WHERE entry_kind = 'scope_link';
CREATE UNIQUE INDEX ad_scope_issue_once ON approval_dependency (investigation_id, owner_review_id, snapshot_observation_id, snapshot_issue_id) WHERE entry_kind = 'scope_issue';
CREATE INDEX lookup_135 ON approval_dependency (investigation_id, snapshot_observation_id);
CREATE INDEX lookup_136 ON approval_dependency (investigation_id, snapshot_link_id);
CREATE INDEX lookup_137 ON approval_dependency (investigation_id, snapshot_issue_id);
CREATE INDEX lookup_138 ON approval_dependency (investigation_id, snapshot_review_id);
CREATE INDEX lookup_139 ON approval_dependency (investigation_id, snapshot_review_seal_id);
```

All SQL is illustrative, not a migration. Future custom SQL must implement mutation denial, member-insert/seal guards, closed-schema validation, approval completeness, publication transactions and read authorization. Ordinary FKs/CHECKs alone do not enforce the binding contract.
