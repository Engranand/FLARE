# Architecture decisions — M3.3

Status: design proposals only; no self-approval of M3 or authorization of M4. The [historical review](m3_final_review.md) remains unchanged. These decisions replace prior alternatives rather than appending contradictory rules.

| Decision | Chosen design and reason | Rejected alternative |
| --- | --- | --- |
| R1 aggregate integrity | Explicit target-XOR seal with canonical digest/count and parent-lock insertion gate | UPDATE/DELETE denial alone leaves member sets mutable |
| R2 approval lineage | Sealed relational dependency DAG with exact review/eligibility/seal IDs | Timestamps cannot capture transaction-visible approvals |
| R3 protocol | Closed relational-v1 requirements, exact variable versions and evidence-backed unit/method rules | Executable/free-form JSON requirements hide scientific integrity assumptions |
| R4 authorization | Atomic seal + result approval + review seal + publication; one CanConsume surface | Multiple implied publication states or base-table reads bypass approval |
| R5 conditions | Typed role/component/instrument/segment relations; preserve unknown scope | Seven universal singleton settings cannot describe multiple instruments or gases |
| R6 metadata | Immutable registration plus reviewed full descriptive snapshot revisions | Unrestricted UPDATE or silent fallback to stale approved metadata |
| R7 diagram | Every declared FK drawn, explicit XOR legend and scoped keys | Omitted links without a completeness statement |
| N1 historical applicability | Extend existing sealed ApprovalDependency membership with typed observation/link/issue facts and exact nullable head/seal FKs; result ReviewEvent attests policy version and zero unresolved issues | Current-link queries or timestamps cannot reconstruct considered membership or missing heads |
| N1 current permission | Exact fresh applicability equality plus ordinary approval currency; any scope/head change requires full revalidation, with successor approval/publication for unchanged content | Silently accepting changed identity/issue universes or altering the old seal |
| N2 policy waiver | Empty ResultCondition is valid only with no condition-role requirements and all input policies not_required/not_applicable; documented input segments remain required | Requiring invented waiver components or silently waiving active evidence policies |
| N2 active policies | Same-input annotation/variable component in the same test/segment; identified_required and stable_required/transient_allowed use the explicit truth table | Borrowing another segment's evidence or treating unknown as supported |

Retained decisions: one modular relational system; investigation-scoped UUID keys; immutable external byte artifacts; text raw tokens distinct from typed semantic values; exact units and numeric precision; evidence-backed variable definitions; no assumed experiment timestamp; purpose-specific revocable eligibility; ordinary scoped indexes before speculative partitioning/JSON indexes. Runtime versions, reviewer identity mapping and storage retention provider are deployment choices for a later authorized milestone, not permission to weaken the [binding contract](postgresql_schema_proposal.md#binding-integrity-contract).

All new tables are justified by R1–R7; the original 23 entity identities remain. PostgreSQL requires custom procedures/deferred triggers/role grants for cross-row and publication checks, not only ORM FK/CHECK declarations. The SQL in the schema document is illustrative. Scientific rules cannot default to zero, numeric conversion, independent replicates or stable airflow merely because parsing succeeds.

Condition eligibility has a separate revision stream per protocol/test/segment. The complete ER inventory draws all 140 declared scoped foreign keys across 33 entities; SQL and diagram remain design artifacts. Five added FKs support typed applicability facts inside the existing dependency relation. The seal identifier advances to canonical-json-v2 for the changed row shape; no historical seal is relabeled. No additional entity or parallel snapshot structure is introduced.

The normative [N1 snapshot](postgresql_schema_proposal.md#n1--publication-time-applicability-snapshot) and [N2 truth table](postgresql_schema_proposal.md#n2--complete-condition-policy-truth-table) apply identically to publication and CanConsume. [M3.2](m3_final_review_v2.md) remains the unchanged historical review; [M3.3 remediation](m3_3_remediation_log.md) is a design response requiring fresh independent review before M4.
