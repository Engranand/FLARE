# M3.1 remediation log

Design remediation only; 33 entities. All statuses below concern explicit design solutions, not tested database enforcement or independent approval. [M3 NOT APPROVED](m3_final_review.md) remains the historical verdict; a fresh independent gate must authorize M4.

## R1 — RESOLVED

Original problem: Mutable published child membership.

Design correction: AggregateSeal and member-insert lock guards. Affected entities/relationships: parse/annotation/condition/protocol/result/review seals. Evidence: [schema contract R1](postgresql_schema_proposal.md#binding-integrity-contract), synchronized architecture, lifecycle and decision records. Enforcement: scoped FKs/local checks plus restricted insertion/publication procedures, deferred validation, shared parent/subject locks and SERIALIZABLE retries; R7 is a documentation consistency check.

Required future tests: race child insertion against seal; reject post-seal inserts; digest golden vectors; evidence supplement new revision. These tests are specifications, not execution claims.

## R2 — RESOLVED

Original problem: Incomplete consumed approval history.

Design correction: Sealed ApprovalDependency DAG. Affected entities/relationships: review, variable, identity, condition, eligibility, seals. Evidence: [schema contract R2](postgresql_schema_proposal.md#binding-integrity-contract), synchronized architecture, lifecycle and decision records. Enforcement: scoped FKs/local checks plus restricted insertion/publication procedures, deferred validation, shared parent/subject locks and SERIALIZABLE retries; R7 is a documentation consistency check.

Required future tests: revoke every dependency class; reject missing/wrong/recursive edges; reconstruct old snapshots after revocation. These tests are specifications, not execution claims.

## R3 — RESOLVED

Original problem: Unspecified scientific policy language.

Design correction: Relational-v1 requirements and unit rules. Affected entities/relationships: protocol, exact variables, condition roles, segments. Evidence: [schema contract R3](postgresql_schema_proposal.md#binding-integrity-contract), synchronized architecture, lifecycle and decision records. Enforcement: scoped FKs/local checks plus restricted insertion/publication procedures, deferred validation, shared parent/subject locks and SERIALIZABLE retries; R7 is a documentation consistency check.

Required future tests: unknown keys; wrong version/unit/phase; unrelated condition test; missing segment; new/reopened test and component issues. These tests are specifications, not execution claims.

## R4 — RESOLVED

Original problem: Ambiguous publication boundary.

Design correction: Atomic publication event and exact CanConsume predicate. Affected entities/relationships: result seal, result review seal, publication chain. Evidence: [schema contract R4](postgresql_schema_proposal.md#binding-integrity-contract), synchronized architecture, lifecycle and decision records. Enforcement: scoped FKs/local checks plus restricted insertion/publication procedures, deferred validation, shared parent/subject locks and SERIALIZABLE retries; R7 is a documentation consistency check.

Required future tests: draft/base read denial; result-level revoke; concurrent consume/revoke; re-publication after fresh approval. These tests are specifications, not execution claims.

## R5 — RESOLVED

Original problem: Singleton BASS-II condition assumptions.

Design correction: Typed components with instruments and segments. Affected entities/relationships: condition_role/component/segment/instrument. Evidence: [schema contract R5](postgresql_schema_proposal.md#binding-integrity-contract), synchronized architecture, lifecycle and decision records. Enforcement: scoped FKs/local checks plus restricted insertion/publication procedures, deferred validation, shared parent/subject locks and SERIALIZABLE retries; R7 is a documentation consistency check.

Required future tests: multiple gases/instruments; duplicate slots cannot inflate counts; unknown instruments and scope fail required policies. These tests are specifications, not execution claims.

## R6 — RESOLVED

Original problem: No correction route for immutable metadata.

Design correction: Full snapshot metadata revisions; variable versions remain exact. Affected entities/relationships: metadata_revision, review target, source/ investigation. Evidence: [schema contract R6](postgresql_schema_proposal.md#binding-integrity-contract), synchronized architecture, lifecycle and decision records. Enforcement: scoped FKs/local checks plus restricted insertion/publication procedures, deferred validation, shared parent/subject locks and SERIALIZABLE retries; R7 is a documentation consistency check.

Required future tests: parallel first revisions; withdrawn newest snapshot; unknown source version; old variable remains pinned. These tests are specifications, not execution claims.

## R7 — RESOLVED

Original problem: Incomplete ER relationship explanation.

Design correction: Full FK edge inventory and XOR legend. Affected entities/relationships: all scoped and predecessor relationships. Evidence: [schema contract R7](postgresql_schema_proposal.md#binding-integrity-contract), synchronized architecture, lifecycle and decision records. Enforcement: scoped FKs/local checks plus restricted insertion/publication procedures, deferred validation, shared parent/subject locks and SERIALIZABLE retries; R7 is a documentation consistency check.

Required future tests: compare every FK to ER edge; validate mandatory/optional parent cardinalities and target uniqueness. These tests are specifications, not execution claims.

## Validation

Static validation completed on 2026-11-06. No database connection, SQL execution, migrations, ORM changes, runtime dependency installation or scientific analytics occurred.

| Check | Result and evidence |
| --- | --- |
| Entity consistency | 33 CREATE TABLE declarations match 33 table contracts and 33 Mermaid entities. All original 23 entity identities are retained. The architecture, lifecycle and decisions consistently use the binding schema contract. |
| Foreign keys | All 135 declared FKs have existing, type-compatible columns and declared unique referenced keys. Investigation scope is included. All 135 have corresponding diagram edges; FK nullability and unique child keys match the drawn cardinalities. |
| Mermaid syntax | Every line passes a static check of the restricted ER grammar used here: entity blocks, typed PK/FK attributes, relationship operators and labels. No Mermaid renderer was available; visual layout and validation with the official parser remain independent-review checks. |
| Links | All 27 local document links in the five Markdown deliverables resolve, including referenced heading anchors. |
| Preserved files | SHA-256 comparison against the pre-remediation baseline confirms 52 files outside the five edited architecture documents are unchanged, including raw/processed data, parser/application files, reconciliation documents and the historical review. |
| Raw representation | Read-only comparison confirms all 129 records, all 17 exact headers and all 2,193 raw cell strings match the existing JSONL, including missing and unusual tokens. No parser run or artifact rewrite was needed. |
| Historical verdict | `m3_final_review.md` remains SHA-256 `4f5c4247a6492e267f8627dd304a9e6caa410338f10537c552d7b1824ac0e2aa`; its NOT APPROVED verdict is preserved. |
| Lifecycle and dependency inspection | The binding R1–R4 contract and lifecycle agree on atomic result seal, mandatory approval, review seal and publication. Review/eligibility heads, exact dependencies, current issue checks and historical access are explicitly distinguished. This is documentary inspection, not a database test. |
| BASS-II and investigation boundaries | Raw values remain representable without approving interpretations. Unknown units, scope and instruments can be preserved but cannot satisfy incompatible analytical requirements. No structures are asserted for unaudited investigations. |

### Supporting-entity justification

| Added entity | Required responsibility |
| --- | --- |
| aggregate_seal | Freeze exact parent/child membership, counts and digest for R1. |
| approval_dependency | Preserve a closed set of exact consumed decisions for R2. |
| publication_event | Record immutable publish/revoke history and authorization identity for R4. |
| protocol_requirement | Constrain exact variables, phases, cardinalities and conditions for R3. |
| protocol_unit_rule | Constrain accepted unit/basis/method/version combinations for R3. |
| condition_segment | Give test scope an evidence-backed relational identity for R3/R5. |
| instrument | Preserve explicit instrument identities for R5. |
| condition_role | Define controlled, evidence-backed component roles for R5. |
| condition_component | Replace the seven singleton condition columns with typed members for R5. |
| metadata_revision | Correct descriptive metadata without modifying registrations for R6. |

The consistency pass also changed test eligibility's revision key to `(investigation, protocol, test, segment, revision)`. Observation eligibility retains its own observation/protocol stream. Future tests must publish a result covering two segments concurrently, withdraw one segment decision, and verify that historical reconstruction preserves both original decisions. Duplicate annotation slots must not inflate requirement cardinalities. Canonical digest vectors must distinguish a JSON number from a numeric string and preserve raw lexical differences.

R1–R7 are **RESOLVED as design findings**, with the evidence and future test obligations above. This is not M3 approval or M4 authorization. A fresh independent review must assess the revised documents; database permissions, deferred checks, concurrency behavior, digest implementation and publication enforcement remain unimplemented and untested.
