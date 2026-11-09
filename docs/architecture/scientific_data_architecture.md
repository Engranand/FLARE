# FLARE scientific data architecture — M3.3

Design only. **33 entities** retain the original 23 core identities and add 10 relational integrity supports. No schema implementation, database access, runtime dependency installation or scientific analysis is authorized. The previous [NOT APPROVED review](m3_final_review.md) is historical and unchanged. A fresh independent review is required before M4.

The single normative lifecycle and integrity specification is the [binding schema contract](postgresql_schema_proposal.md#binding-integrity-contract). The [remediation log](m3_remediation_log.md) maps every finding to its correction and future tests. There are no conflicting alternative publication rules in this revision.

## Structure and ownership

Use one modular FastAPI backend with future PostgreSQL persistence and immutable external artifact storage. The existing offline parser and all raw/processed artifacts remain unchanged. No ORM/driver/migration package is installed. Preserve source bytes and source records separately from semantic annotations, condition snapshots, review decisions and purpose-specific eligibility.

The new supporting entities are aggregate_seal, approval_dependency, publication_event, protocol_requirement, protocol_unit_rule, condition_segment, instrument, condition_role, condition_component and metadata_revision. Each closes a specific review gap; no microservice or universal similarity score is introduced.

## Provenance and snapshots

SourceDocument → ParseRun → SourceRecord/SourceField → Observation → SemanticAnnotation → ResultInput → AnalyticalResult remains the raw-to-result chain. Every scientific interpretation has source evidence, exact definition version and method/version. Seals freeze complete membership; sealed review dependencies pin the decisions consumed. Publication requires exact result and approval seals plus current permissions. Condition components pin typed variables/instruments/segments rather than untraceable JSON values.

## Scientific boundaries

All 129 tests, 17 headers and 2,193 CSV strings are representable. Workbook records remain separate source evidence across six sheets and 129 mappings. A source revision cannot alter a sealed historical result. Unknown instrument or temporal scope may be preserved while failing an analytical protocol. BASS-II's 7 confirmed, 7 partial and 3 identifier-only definitions are not approvals. OR is a documented bound; over, negative CO causes, unusual oxygen and two conflicting years remain unresolved. See [reconciliation](../bass_ii_source_reconciliation.md), [field definitions](../bass_ii_field_reconciliation.md), [dictionary](../bass_ii_data_dictionary.md), [mapping](../bass_ii_test_matrix_mapping.md), [anomalies](../bass_ii_anomaly_investigation.md) and [parser](../bass_ii_parser.md).

Investigation-scoped keys and exact local variable versions support later audited investigations. Initial implementation scope is BASS-II relational records, not high-frequency media analytics. Multiple instruments/gases/scopes have typed component representations; no assumptions about Saffire/FLEX/ACME/SAME source schemas are asserted. New capabilities outside the bounded protocol require reviewed schema evolution. No JSONB field stores scientific dependency IDs.

## Approval boundary

Only consume_result may supply analytical outputs, using the exact CanConsume predicate in the schema contract. Base-table access cannot bypass it. Historical readers receive preserved snapshots explicitly marked historical, not current permission. Owner/superuser and storage-administrator bypass remain operational risks requiring independent retention and audits. All protections are proposed and untested against PostgreSQL.

Condition eligibility has a separate revision stream per protocol/test/segment. The complete ER inventory draws all 140 declared scoped foreign keys across 33 entities; SQL and diagram remain design artifacts. See the schema contract for the exact decision-head, XOR and publication rules.

## M3.3 applicability and condition policies

The [N1 contract](postgresql_schema_proposal.md#n1--publication-time-applicability-snapshot) extends ApprovalDependency with typed observation/link/issue scope entries and five scoped FKs; it does not add an entity or another approval system. Each result approval freezes every consumed observation, every considered identity link (selected or not), exact link/issue review heads and their seal IDs or explicit absence, and every applicable observation/whole-test issue. ReviewEvent records the policy version and zero-unresolved attestation. Its existing revision chain and review AggregateSeal identify and hash the snapshot using canonical-json-v2. Non-approved historical heads are facts, not mandatory approving edges.

Historical explanations traverse only these pinned members. Current permission additionally requires ApplicabilityCurrent: exact equality to a fresh applicability scan. New links/issues, changed heads/seals or revocation invalidate current use even when the selected inputs did not change. Full revalidation may create a successor result approval/snapshot and publication using the same content seal; changed result content requires a new result identity. Old publications and snapshots remain immutable. Conservative whole-test issue checking includes every effective non-selected link.

The [N2 truth table](postgresql_schema_proposal.md#n2--complete-condition-policy-truth-table) gives one outcome for all six enum combinations, with and without explicit condition-role requirements. **No condition-role requirements plus not_required/not_applicable for every input permits an empty ResultCondition set.** Documented input segments and all other approvals remain required. An active instrument or stability policy requires a known component for the exact input annotation/variable in the same test and segment, selected through an approved/eligible ResultCondition. Explicit condition-role requirements remain mandatory even when input policies are waived. Missing required evidence and unknown policies fail closed; publication and CanConsume use the same matcher.

These are design resolutions recorded in the [M3.3 log](m3_3_remediation_log.md). The [M3.2 review](m3_final_review_v2.md) is unchanged; a fresh independent review is still required. No M3 approval or M4 authorization is asserted.
