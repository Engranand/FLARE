# M4.5 N2 condition-policy matcher — preflight report

## Current preflight at 0005_variable_immutability

**M4.5 remains blocked at the mandatory inspection gate.** The variable remediation is installed and its regression tests pass. A separate direct-SQL diagnostic reproduced changes to the role, instrument identity and source evidence reached through a sealed condition. The approved proposal explicitly requires immutable component, role and instrument evidence. [N2 and common enforcement contract](../architecture/postgresql_schema_proposal.md)

The inspection covered the five approved architecture deliverables, remediation logs and final review, implementation reports through variable remediation, the actual ORM, migration chain, SQL routines, triggers and test fixtures. The M4.3 seal includes the condition parent and full component rows, hence their reference IDs. M4.4 guards the condition segment and experimental test. Revision 0005 protects scientific variables and evidence references used by a scientific variable or variable review. An evidence reference used solely for condition, role or instrument evidence falls outside that guard. The existing protocol enum requires identification through the supporting component's instrument FK; the approved ProtocolRequirement has no independent instrument-ID column.

**Committed reproduction on disposable PostgreSQL 17.11.** The test verified the installed Alembic revision, created dedicated technical evidence, an identified instrument and a compatible role, then sealed the condition and its technical approval review. It recorded both seal IDs and both stored and independently recomputed membership digests. Three ordinary UPDATEs ran with triggers enabled and committed. A fresh transaction read the following values through the original component:

| Referenced field | Before commit | After commit |
|---|---|---|
| condition_role.variable_category | context | measurement |
| instrument.instrument_code | technical sensor A | technical sensor B |
| evidence_reference.excerpt | Original fixture excerpt | different technical scope |

The condition and review retained their original seal IDs. Both recomputed digests still equaled their original stored digests. The new category no longer matched the component variable category, and the instrument identity and excerpt seen by a later reader differed from those presented for review. The probe establishes a capability on the installed schema. It does not establish that any persistent scientific record was edited.

**Verification:** the complete existing suite and the temporary reproduction ran together using the backend Python interpreter with `-m pytest -c pyproject.toml tests -q --run-postgres "--pg-bin=C:/Program Files/PostgreSQL/17/bin" --tb=short`. **183 passed, 0 failed, 1 existing warning in 71.19 seconds**: 182 regressions and one successful defect reproduction. Existing protocol/aggregate digest, historical N1 and variable immutability checks passed. Independent reads verified all 129 original CSV records, 17 ordered headers, 2,193 raw strings with their classifications and flags, and all three acquisition SHA-256 values.

This report is the only retained change. The temporary diagnostic was removed after the run. Under the requested stop condition, N2 implementation stopped before a new revision. The approved 12-case table below remains the specification. N2 matrix, negative, concurrency and migration-cycle tests executed: zero. The outstanding prerequisite is database enforcement preserving the reviewed role, instrument and evidence contents across later transactions. Verification should repeat these committed mutation attempts and cover concurrent attachment and editing of evidence, including evidence shared across distinct targets.

## Earlier preflight at 0004_m44_n1 (resolved by revision 0005)

**Finding at the previous head.** On the M4.4 migration head, a committed UPDATE changed the definition version and unit basis of an approved scientific variable used by a sealed protocol. The protocol still referenced the same variable UUID and its seal still verified. M3 requires corrections to create a new immutable version with fresh evidence and approval. The M4.5 request explicitly requires stopping when the installed implementation differs from the approved design. [Approved definition-version rule, R6](../architecture/postgresql_schema_proposal.md#r6--immutable-metadata-correction-policy)

## Inspection and reproduction

Inspected the five approved architecture deliverables, M3 remediation and M3.3 remediation logs, M3.4 final review, M4.1–M4.4 reports, the 33 ORM mappings, four Alembic revisions, M4.3 and M4.4 SQL assets, and the PostgreSQL fixtures. The existing head is 0004_m44_n1. ProtocolRequirement.variable_id and SemanticAnnotation.variable_id identify a ScientificVariable row within an investigation. ScientificVariable has a unique version key (investigation_id, variable_code, definition_version). An in-place revision to an unused version number satisfies that uniqueness constraint.

The technical probe used the repository's private PostgreSQL fixture, verified server_version_num = 170011 and the Alembic head, created a sealed approving variable review, sealed the protocol and built a sealed N1 result review. With triggers enabled, it ran the following ordinary SQL and committed, then checked the result in a new transaction:

```sql
UPDATE public.scientific_variable
SET definition_version = 2, unit_basis = 'revised fixture'
WHERE investigation_id = :investigation AND id = :variable;
```

| Observation | Before commit | Fresh read after commit |
|---|---|---|
| Variable reached through the sealed protocol requirement | Original UUID, version 1 | Same UUID, version 2 |
| Unit basis | fixture | revised fixture |
| Stored protocol seal ID and SHA-256 | Recorded | Identical |
| Recomputed canonical protocol digest | Equal to stored digest | Still equal to the original digest |
| Historical N1 result snapshot | Recorded pinned membership | Identical membership and digest |

The M4.3 serializer freezes the protocol, requirements and unit rules. The requirement carries a variable FK. The referenced definition's contents are outside that aggregate, as designed. M4.3 and M4.4 install immutability triggers on their respective target tables. Neither trigger inventory includes scientific_variable. Consequently an exact-ID join can return a different definition and unit basis under the same historical evidence. This is an existing version-integrity discrepancy independent of the missing N2 matcher. [M4.3 trigger inventory](../../backend/migrations/versions/0003_m43_sealing.py) · [M4.4 trigger inventory](../../backend/migrations/versions/0004_m44_n1.py) · [Canonical aggregate enumeration](../../backend/migrations/versions/m43_sealing.sql)

## Approved matcher contract for resumption

AnalysisProtocol owns the sealed ProtocolRequirement and ProtocolUnitRule rows. Each input selects an annotation, identity link and review, segment and eligibility. Each ResultCondition selects a condition version and eligibility. ConditionComponent supplies the exact variable, annotation, role and instrument. ExperimentalCondition and ConditionSegment provide the reviewed stability assertion, documented test/segment scope and evidence. Existing FKs and CHECK constraints establish local identity and enum shape. M4.3 supplies content seals. M4.4 constructs and validates N1 observation/link/issue membership at result approval and preserves it for historical reads.

The following table records the twelve approved outcomes. Each row assumes the other required documentation, approval, identity, eligibility and issue checks succeed. An active input requires a known component for the exact input annotation and variable in the same test and segment. A single component/condition must satisfy both active policies. Condition-role requirements apply independently to their own role, variable, counts and evidence in every input test/segment.

| Condition-role requirements | Instrument policy | Stability policy | Matching input component | Empty ResultCondition permitted |
|---|---|---|---|---|
| Absent | not_required | not_applicable | Waived | Yes, only if every input requirement has this pair |
| Absent | identified_required | not_applicable | Identified instrument | No |
| Absent | not_required | transient_allowed | Documented stable or transient scope | No |
| Absent | identified_required | transient_allowed | Identified instrument and documented stable or transient scope | No |
| Absent | not_required | stable_required | Documented stable scope | No |
| Absent | identified_required | stable_required | Identified instrument and documented stable scope | No |
| Present | not_required | not_applicable | Waived for input policy; declared roles still required | No |
| Present | identified_required | not_applicable | Identified instrument | No |
| Present | not_required | transient_allowed | Documented stable or transient scope | No |
| Present | identified_required | transient_allowed | Identified instrument and documented stable or transient scope | No |
| Present | not_required | stable_required | Documented stable scope | No |
| Present | identified_required | stable_required | Identified instrument and documented stable scope | No |

A waived stability policy still requires protocol evidence. The empty-set exception preserves documented segment and identity requirements. Required role components need their specified variable and role and may represent annotations distinct from the result inputs. Protocol matching uses exact phase, value policy, unit, unit basis, transformation method/version and per-segment cardinality. The intended integration adds a separate database predicate and final approval validation alongside N1. Optional conditions continue to enter N1 scope. [Approved N2 truth table and matching rules](../architecture/postgresql_schema_proposal.md#n2--complete-condition-policy-truth-table)

## Verification, files and next decision

- Disposable database reproduction: **1 passed, 0 failed in 19.65 seconds**. A passing diagnostic means the prohibited in-place change was reproduced. The temporary pytest probe used the existing test fixtures; its source was removed with its temporary directory.
- Read-only preservation check: all **2,193** raw values and their ordered headers matched the processed JSONL. CSV SHA-256: 71e792bf6b5fb5ea620c5dd70fbbac05515992e12aefcf5dff47312caa48c042.
- Only this preflight report was created. No N2 function, trigger, migration or application change was made. The twelve cases above are design outcomes. N2 acceptance, migration round-trip and full regression results are pending.
- A forward migration can enforce the existing immutable-definition rule without adding a domain column or changing historical migrations. Its acceptance probe should verify rejection of an in-place edit, successful registration and approval of a successor definition, and continued resolution of the original protocol to the original version and unit basis. Existing seals alone cannot establish whether earlier in-place edits occurred. Authorization to remediate the discrepancy is needed before resuming M4.5.
