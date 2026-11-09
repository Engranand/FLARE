# Proposed data dictionary

**Planning only: this is not a validated NASA data model.** No entity is persisted, downloaded or scientifically validated in Milestone 1. Field names, relationships, types and cardinalities must be reconciled with actual source files in the ingestion milestone.

| Entity | Purpose | Proposed fields |
| --- | --- | --- |
| Investigation | Source-level investigation metadata | id, source_id, title, description, agency, source_url, doi, manifest_id |
| Experiment | A source-identifiable experimental run | id, investigation_id, source_run_id, source_file, source_locator, description, validation_status |
| Condition | A recorded experimental input or context | id, experiment_id, name, original_value, normalized_value, original_unit, normalized_unit, source_locator |
| Measurement | A measured quantity with provenance | id, experiment_id, quantity, value, unit, time_offset, time_unit, uncertainty, uncertainty_unit, missing_reason, source_locator |
| ResearchDocument | A traceable scientific source | id, investigation_id, title, authors, publication_date, doi, source_url, content_hash, access_terms |
| Evidence | A precise reference supporting a claim | id, document_id, experiment_id, source_locator, excerpt, evidence_type, provenance_manifest_id |
| Finding | A reviewed interpretation with scope limits | id, statement, evidence_ids, method, limitations, review_status, created_at |

IDs are proposed strings; references should resolve to retained source objects. Evidence may refer to a document or experimental record; exact constraints remain undecided. Numeric measurements must carry units and explicit time semantics. Preserve original values before normalization. Missing values are not zero. Uncertainty must be source-supported, not guessed. Findings must distinguish observation from interpretation and must not imply spacecraft risk predictions.
