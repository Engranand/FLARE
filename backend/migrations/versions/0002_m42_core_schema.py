"""M4.2 approved declarative schema; no data or procedural enforcement.

All tables precede cyclic FKs. Enum domains remain TEXT + CHECK, as approved.
The static DDL is independent of mutable application model imports.
"""
from alembic import context, op
from alembic.util import CommandError

revision = "0002_m42_core_schema"
down_revision = "0001_m41_baseline"
branch_labels = None
depends_on = None

TABLE_DDL = (
    """CREATE TABLE investigation (
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
    CONSTRAINT pk_investigation_01 PRIMARY KEY (id),
    CONSTRAINT uq_investigation_01 UNIQUE (repository_code, investigation_code),
    CONSTRAINT ck_investigation_01 CHECK (jsonb_typeof(metadata) = 'object')
)""",
    """CREATE TABLE source_document (
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
    CONSTRAINT pk_source_document_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_source_document_01 UNIQUE (investigation_id, sha256),
    CONSTRAINT ck_source_document_01 CHECK (source_type IN ('csv','xlsx','docx','pdf','image','video','other')),
    CONSTRAINT ck_source_document_02 CHECK (artifact_origin IN ('external_original','generated_artifact','software_artifact')),
    CONSTRAINT ck_source_document_03 CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_source_document_04 CHECK (file_size_bytes >= 0),
    CONSTRAINT ck_source_document_05 CHECK (jsonb_typeof(metadata) = 'object')
)""",
    """CREATE TABLE source_acquisition (
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
    CONSTRAINT pk_source_acquisition_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT ck_source_acquisition_01 CHECK (verification_status IN ('verified','failed','unverified')),
    CONSTRAINT ck_source_acquisition_02 CHECK (verification_status <> 'verified' OR (source_document_id IS NOT NULL AND actual_filename IS NOT NULL)),
    CONSTRAINT ck_source_acquisition_03 CHECK (jsonb_typeof(metadata) = 'object')
)""",
    """CREATE TABLE evidence_reference (
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
    CONSTRAINT pk_evidence_reference_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_evidence_reference_01 UNIQUE (investigation_id, source_document_id, locator_version, locator_key),
    CONSTRAINT ck_evidence_reference_01 CHECK (locator_kind IN ('csv','xlsx','docx','pdf','image','video','document')),
    CONSTRAINT ck_evidence_reference_02 CHECK (verification_status IN ('verified','unverified','needs_review')),
    CONSTRAINT ck_evidence_reference_03 CHECK (jsonb_typeof(locator) = 'object')
)""",
    """CREATE TABLE parse_run (
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
    CONSTRAINT pk_parse_run_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_parse_run_01 UNIQUE (investigation_id, source_document_id, parser_name, parser_version, code_sha256, configuration_sha256, output_sha256),
    CONSTRAINT ck_parse_run_01 CHECK (status IN ('complete','failed')),
    CONSTRAINT ck_parse_run_02 CHECK (record_count >= 0),
    CONSTRAINT ck_parse_run_03 CHECK (code_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_parse_run_04 CHECK (configuration_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_parse_run_05 CHECK (jsonb_typeof(configuration) = 'object'),
    CONSTRAINT ck_parse_run_06 CHECK (output_sha256 ~ '^[0-9a-f]{64}$')
)""",
    """CREATE TABLE source_field (
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
    CONSTRAINT pk_source_field_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_source_field_01 UNIQUE (investigation_id, parse_run_id, table_key, ordinal),
    CONSTRAINT uq_source_field_02 UNIQUE (investigation_id, parse_run_id, id),
    CONSTRAINT ck_source_field_01 CHECK (ordinal > 0),
    CONSTRAINT ck_source_field_02 CHECK (raw_unit_status IN ('stated','not_stated','not_applicable')),
    CONSTRAINT ck_source_field_03 CHECK ((raw_unit_status = 'stated') = (raw_unit IS NOT NULL))
)""",
    """CREATE TABLE source_record (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    parse_run_id uuid NOT NULL,
    table_key text NOT NULL,
    source_record_number bigint NOT NULL,
    source_row_id text NOT NULL,
    row_evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT pk_source_record_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_source_record_01 UNIQUE (investigation_id, parse_run_id, table_key, source_record_number),
    CONSTRAINT uq_source_record_02 UNIQUE (investigation_id, parse_run_id, id),
    CONSTRAINT uq_source_record_03 UNIQUE (investigation_id, parse_run_id, source_row_id),
    CONSTRAINT ck_source_record_01 CHECK (source_record_number > 0)
)""",
    """CREATE TABLE experimental_test (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    identity_namespace text NOT NULL,
    test_identifier text NOT NULL,
    identity_evidence_id uuid NOT NULL,
    metadata jsonb NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT pk_experimental_test_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_experimental_test_01 UNIQUE (investigation_id, identity_namespace, test_identifier),
    CONSTRAINT ck_experimental_test_01 CHECK (jsonb_typeof(metadata) = 'object')
)""",
    """CREATE TABLE test_source_record (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    experimental_test_id uuid NOT NULL,
    source_record_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    match_method text NOT NULL,
    method_version text NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT pk_test_source_record_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_test_source_record_01 UNIQUE (investigation_id, experimental_test_id, source_record_id)
)""",
    """CREATE TABLE test_relationship (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    left_test_id uuid NOT NULL,
    right_test_id uuid NOT NULL,
    relationship_type text NOT NULL,
    evidence_id uuid NOT NULL,
    description text NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT pk_test_relationship_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_test_relationship_01 UNIQUE (investigation_id, left_test_id, right_test_id, relationship_type, evidence_id),
    CONSTRAINT ck_test_relationship_01 CHECK (left_test_id <> right_test_id)
)""",
    """CREATE TABLE observation (
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
    CONSTRAINT pk_observation_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_observation_01 UNIQUE (investigation_id, parse_run_id, source_record_id, source_field_id),
    CONSTRAINT ck_observation_01 CHECK (source_value_kind IN ('text','numeric_lexeme','empty_cell','other')),
    CONSTRAINT ck_observation_02 CHECK (unit_origin IN ('field','cell','not_stated','not_applicable')),
    CONSTRAINT ck_observation_03 CHECK ((unit_origin = 'cell') = (raw_unit IS NOT NULL)),
    CONSTRAINT ck_observation_04 CHECK ((unit_origin = 'cell') = (unit_evidence_id IS NOT NULL)),
    CONSTRAINT ck_observation_05 CHECK ((source_value_kind = 'empty_cell') = (raw_value IS NULL)),
    CONSTRAINT ck_observation_06 CHECK (jsonb_typeof(parser_flags) = 'object'),
    CONSTRAINT ck_observation_07 CHECK (jsonb_typeof(original_representation) = 'object')
)""",
    """CREATE TABLE scientific_variable (
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
    CONSTRAINT pk_scientific_variable_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_scientific_variable_01 UNIQUE (investigation_id, variable_code, definition_version),
    CONSTRAINT ck_scientific_variable_01 CHECK (definition_version > 0),
    CONSTRAINT ck_scientific_variable_02 CHECK (variable_category IN ('measurement','identifier','instrument_setting','condition','context')),
    CONSTRAINT ck_scientific_variable_03 CHECK (definition_status IN ('confirmed','partially_confirmed','unresolved','identifier_only','not_applicable'))
)""",
    """CREATE TABLE semantic_annotation (
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
    CONSTRAINT pk_semantic_annotation_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_semantic_annotation_01 UNIQUE (investigation_id, observation_id, interpretation_key, revision),
    CONSTRAINT uq_semantic_annotation_02 UNIQUE (investigation_id, supersedes_id),
    CONSTRAINT ck_semantic_annotation_01 CHECK (revision > 0),
    CONSTRAINT ck_semantic_annotation_02 CHECK (supersedes_id IS NULL OR supersedes_id <> id),
    CONSTRAINT ck_semantic_annotation_03 CHECK (value_kind IN ('numeric','censored','text','date','missing','unresolved','sequence')),
    CONSTRAINT ck_semantic_annotation_04 CHECK (unit_status IN ('known','unknown','not_applicable')),
    CONSTRAINT ck_semantic_annotation_05 CHECK ((unit_status = 'known') = (interpreted_unit IS NOT NULL)),
    CONSTRAINT ck_semantic_annotation_06 CHECK ((value_kind = 'numeric') = (numeric_value IS NOT NULL)),
    CONSTRAINT ck_semantic_annotation_07 CHECK ((value_kind = 'censored') = (bound_value IS NOT NULL)),
    CONSTRAINT ck_semantic_annotation_08 CHECK ((value_kind = 'censored') = (comparator IS NOT NULL)),
    CONSTRAINT ck_semantic_annotation_09 CHECK (comparator IS NULL OR comparator IN ('<','<=','>','>=')),
    CONSTRAINT ck_semantic_annotation_10 CHECK ((value_kind = 'date') = (date_value IS NOT NULL)),
    CONSTRAINT ck_semantic_annotation_11 CHECK ((value_kind IN ('text','missing','unresolved','sequence')) = (text_value IS NOT NULL)),
    CONSTRAINT ck_semantic_annotation_12 CHECK (numeric_value IS NULL OR numeric_value::text NOT IN ('NaN','Infinity','-Infinity')),
    CONSTRAINT ck_semantic_annotation_13 CHECK (bound_value IS NULL OR bound_value::text NOT IN ('NaN','Infinity','-Infinity')),
    CONSTRAINT ck_semantic_annotation_14 CHECK (jsonb_typeof(parameters) = 'object'),
    CONSTRAINT ck_semantic_annotation_15 CHECK (jsonb_typeof(uncertainty) = 'object')
)""",
    """CREATE TABLE annotation_evidence (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    annotation_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    role text NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT pk_annotation_evidence_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_annotation_evidence_01 UNIQUE (investigation_id, annotation_id, evidence_id, role)
)""",
    """CREATE TABLE experimental_condition (
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
    CONSTRAINT pk_experimental_condition_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_experimental_condition_01 UNIQUE (investigation_id, experimental_test_id, segment_key, revision),
    CONSTRAINT uq_experimental_condition_02 UNIQUE (investigation_id, supersedes_id),
    CONSTRAINT ck_experimental_condition_01 CHECK (revision > 0),
    CONSTRAINT ck_experimental_condition_02 CHECK (supersedes_id IS NULL OR supersedes_id <> id),
    CONSTRAINT ck_experimental_condition_03 CHECK (airflow_stability IN ('stable','transient','unknown','not_applicable')),
    CONSTRAINT ck_experimental_condition_04 CHECK (extension_metadata = '{}'::jsonb)
)""",
    """CREATE TABLE data_quality_issue (
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
    CONSTRAINT pk_data_quality_issue_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT ck_data_quality_issue_01 CHECK (num_nonnulls(observation_id,experimental_test_id) = 1),
    CONSTRAINT ck_data_quality_issue_02 CHECK (severity IN ('info','review','blocking'))
)""",
    """CREATE TABLE review_event (
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
    CONSTRAINT pk_review_event_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_review_event_01 UNIQUE (investigation_id, supersedes_id),
    CONSTRAINT uq_review_event_02 UNIQUE (investigation_id, annotation_id, revision),
    CONSTRAINT uq_review_event_03 UNIQUE (investigation_id, variable_id, revision),
    CONSTRAINT uq_review_event_04 UNIQUE (investigation_id, condition_id, revision),
    CONSTRAINT uq_review_event_05 UNIQUE (investigation_id, test_link_id, revision),
    CONSTRAINT uq_review_event_06 UNIQUE (investigation_id, test_relation_id, revision),
    CONSTRAINT uq_review_event_07 UNIQUE (investigation_id, issue_id, revision),
    CONSTRAINT uq_review_event_08 UNIQUE (investigation_id, result_id, revision),
    CONSTRAINT ck_review_event_01 CHECK (num_nonnulls(metadata_revision_id,annotation_id,variable_id,condition_id,test_link_id,test_relation_id,issue_id,result_id) = 1),
    CONSTRAINT ck_review_event_02 CHECK (revision > 0),
    CONSTRAINT ck_review_event_03 CHECK (supersedes_id IS NULL OR supersedes_id <> id),
    CONSTRAINT ck_review_event_04 CHECK (decision IN ('approved','rejected','revoked','needs_review','resolved','open')),
    CONSTRAINT uq_review_event_09 UNIQUE (investigation_id, metadata_revision_id, revision),
    CONSTRAINT ck_review_event_05 CHECK ((applicability_policy_version IS NOT NULL) = (result_id IS NOT NULL AND decision = 'approved')),
    CONSTRAINT ck_review_event_06 CHECK ((applicability_unresolved_count IS NOT NULL) = (result_id IS NOT NULL AND decision = 'approved')),
    CONSTRAINT ck_review_event_07 CHECK (applicability_policy_version IS NULL OR applicability_policy_version = 'identity-issue-snapshot-v1'),
    CONSTRAINT ck_review_event_08 CHECK (applicability_unresolved_count IS NULL OR applicability_unresolved_count = 0)
)""",
    """CREATE TABLE analysis_protocol (
    issue_policy text NOT NULL,
    CONSTRAINT ck_analysis_protocol_01 CHECK (issue_policy = 'all_unresolved_review_or_blocking'),
    coverage_policy text NOT NULL,
    CONSTRAINT ck_analysis_protocol_02 CHECK (coverage_policy = 'every_input_test_segment'),
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    protocol_code text NOT NULL,
    protocol_version text NOT NULL,
    description text NOT NULL,
    requirements_schema_version text NOT NULL,
    display_metadata jsonb NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT pk_analysis_protocol_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_analysis_protocol_01 UNIQUE (investigation_id, protocol_code, protocol_version),
    CONSTRAINT ck_analysis_protocol_03 CHECK (display_metadata = '{}'::jsonb),
    CONSTRAINT ck_analysis_protocol_04 CHECK (requirements_schema_version = 'relational-v1')
)""",
    """CREATE TABLE analytical_eligibility (
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
    CONSTRAINT pk_analytical_eligibility_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_analytical_eligibility_01 UNIQUE (investigation_id, protocol_id, observation_id, revision),
    CONSTRAINT uq_analytical_eligibility_02 UNIQUE (investigation_id, protocol_id, experimental_test_id, segment_id, revision),
    CONSTRAINT uq_analytical_eligibility_03 UNIQUE (investigation_id, supersedes_id),
    CONSTRAINT ck_analytical_eligibility_01 CHECK (num_nonnulls(observation_id,experimental_test_id) = 1),
    CONSTRAINT ck_analytical_eligibility_02 CHECK (revision > 0),
    CONSTRAINT ck_analytical_eligibility_03 CHECK (supersedes_id IS NULL OR supersedes_id <> id),
    CONSTRAINT ck_analytical_eligibility_04 CHECK (eligibility_status IN ('eligible','ineligible','needs_review','withdrawn')),
    CONSTRAINT ck_analytical_eligibility_05 CHECK (eligibility_status <> 'eligible' OR observation_id IS NULL OR (annotation_id IS NOT NULL AND annotation_review_id IS NOT NULL)),
    CONSTRAINT ck_analytical_eligibility_06 CHECK (eligibility_status <> 'eligible' OR experimental_test_id IS NULL OR (condition_id IS NOT NULL AND condition_review_id IS NOT NULL)),
    CONSTRAINT ck_analytical_eligibility_07 CHECK ((annotation_id IS NULL) = (annotation_review_id IS NULL)),
    CONSTRAINT ck_analytical_eligibility_08 CHECK ((condition_id IS NULL) = (condition_review_id IS NULL)),
    CONSTRAINT ck_analytical_eligibility_09 CHECK ((experimental_test_id IS NOT NULL) = (segment_id IS NOT NULL))
)""",
    """CREATE TABLE analytical_result (
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
    CONSTRAINT pk_analytical_result_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT ck_analytical_result_01 CHECK (result_kind IN ('numeric','text','artifact')),
    CONSTRAINT ck_analytical_result_02 CHECK (unit_status IN ('known','unknown','not_applicable')),
    CONSTRAINT ck_analytical_result_03 CHECK ((unit_status = 'known') = (unit IS NOT NULL)),
    CONSTRAINT ck_analytical_result_04 CHECK ((result_kind = 'numeric') = (numeric_value IS NOT NULL)),
    CONSTRAINT ck_analytical_result_05 CHECK ((result_kind = 'text') = (text_value IS NOT NULL)),
    CONSTRAINT ck_analytical_result_06 CHECK ((result_kind = 'artifact') = (artifact_document_id IS NOT NULL)),
    CONSTRAINT ck_analytical_result_07 CHECK (numeric_value IS NULL OR numeric_value::text NOT IN ('NaN','Infinity','-Infinity')),
    CONSTRAINT ck_analytical_result_08 CHECK (jsonb_typeof(parameters) = 'object'),
    CONSTRAINT ck_analytical_result_09 CHECK (jsonb_typeof(uncertainty) = 'object')
)""",
    """CREATE TABLE result_input (
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
    CONSTRAINT pk_result_input_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_result_input_01 UNIQUE (investigation_id, result_id, annotation_id, input_role)
)""",
    """CREATE TABLE result_condition (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    result_id uuid NOT NULL,
    condition_id uuid NOT NULL,
    eligibility_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT pk_result_condition_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_result_condition_01 UNIQUE (investigation_id, result_id, condition_id)
)""",
    """CREATE TABLE result_evidence (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    result_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    role text NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT pk_result_evidence_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_result_evidence_01 UNIQUE (investigation_id, result_id, evidence_id, role)
)""",
    """CREATE TABLE condition_segment (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    experimental_test_id uuid NOT NULL,
    segment_key text NOT NULL,
    scope_status text NOT NULL,
    description text NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT pk_condition_segment_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT ck_condition_segment_01 CHECK (scope_status IN ('documented','unknown')),
    CONSTRAINT uq_condition_segment_01 UNIQUE (investigation_id, experimental_test_id, segment_key)
)""",
    """CREATE TABLE instrument (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    instrument_code text NOT NULL,
    description text NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT pk_instrument_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_instrument_01 UNIQUE (investigation_id, instrument_code)
)""",
    """CREATE TABLE condition_role (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    role_code text NOT NULL,
    definition text NOT NULL,
    variable_category text NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT pk_condition_role_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_condition_role_01 UNIQUE (investigation_id, role_code)
)""",
    """CREATE TABLE condition_component (
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
    CONSTRAINT pk_condition_component_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT ck_condition_component_01 CHECK (slot > 0),
    CONSTRAINT ck_condition_component_02 CHECK (value_status IN ('known','unknown','not_applicable')),
    CONSTRAINT ck_condition_component_03 CHECK ((value_status = 'known') = (annotation_id IS NOT NULL)),
    CONSTRAINT ck_condition_component_04 CHECK (instrument_status IN ('identified','unknown','not_applicable')),
    CONSTRAINT ck_condition_component_05 CHECK ((instrument_status = 'identified') = (instrument_id IS NOT NULL)),
    CONSTRAINT uq_condition_component_01 UNIQUE (investigation_id, condition_id, role_id, slot)
)""",
    """CREATE TABLE protocol_requirement (
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
    CONSTRAINT pk_protocol_requirement_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_protocol_requirement_01 UNIQUE (investigation_id, protocol_id, requirement_key),
    CONSTRAINT ck_protocol_requirement_01 CHECK (target_kind IN ('input','condition')),
    CONSTRAINT ck_protocol_requirement_02 CHECK ((target_kind = 'condition') = (role_id IS NOT NULL)),
    CONSTRAINT ck_protocol_requirement_03 CHECK (min_count > 0 AND max_count >= min_count),
    CONSTRAINT ck_protocol_requirement_04 CHECK (value_policy IN ('numeric_only','numeric_or_censored','categorical')),
    CONSTRAINT ck_protocol_requirement_05 CHECK (stability_policy IN ('stable_required','transient_allowed','not_applicable')),
    CONSTRAINT ck_protocol_requirement_06 CHECK (instrument_policy IN ('identified_required','not_required'))
)""",
    """CREATE TABLE protocol_unit_rule (
    investigation_id uuid NOT NULL,
    id uuid NOT NULL,
    requirement_id uuid NOT NULL,
    unit_text text NOT NULL,
    unit_basis text NOT NULL,
    method text NOT NULL,
    method_version text NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT pk_protocol_unit_rule_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT uq_protocol_unit_rule_01 UNIQUE (investigation_id, requirement_id, unit_text, unit_basis, method, method_version)
)""",
    """CREATE TABLE metadata_revision (
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
    CONSTRAINT pk_metadata_revision_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT ck_metadata_revision_01 CHECK (subject_kind IN ('investigation','source_document')),
    CONSTRAINT ck_metadata_revision_02 CHECK ((subject_kind = 'source_document') = (source_document_id IS NOT NULL)),
    CONSTRAINT ck_metadata_revision_03 CHECK (revision > 0),
    CONSTRAINT uq_metadata_revision_01 UNIQUE (investigation_id, source_document_id, revision),
    CONSTRAINT uq_metadata_revision_02 UNIQUE (investigation_id, supersedes_id)
)""",
    """CREATE TABLE aggregate_seal (
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
    CONSTRAINT pk_aggregate_seal_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT ck_aggregate_seal_01 CHECK (num_nonnulls(parse_run_id,annotation_id,condition_id,protocol_id,result_id,review_id) = 1),
    CONSTRAINT ck_aggregate_seal_02 CHECK (seal_version = 'canonical-json-v2'),
    CONSTRAINT ck_aggregate_seal_03 CHECK (jsonb_typeof(member_counts) = 'object'),
    CONSTRAINT ck_aggregate_seal_04 CHECK (member_digest ~ '^[0-9a-f]{64}$'),
    CONSTRAINT uq_aggregate_seal_01 UNIQUE (investigation_id, parse_run_id),
    CONSTRAINT uq_aggregate_seal_02 UNIQUE (investigation_id, annotation_id),
    CONSTRAINT uq_aggregate_seal_03 UNIQUE (investigation_id, condition_id),
    CONSTRAINT uq_aggregate_seal_04 UNIQUE (investigation_id, protocol_id),
    CONSTRAINT uq_aggregate_seal_05 UNIQUE (investigation_id, result_id),
    CONSTRAINT uq_aggregate_seal_06 UNIQUE (investigation_id, review_id)
)""",
    """CREATE TABLE approval_dependency (
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
    CONSTRAINT pk_approval_dependency_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT ck_approval_dependency_01 CHECK ((entry_kind = 'decision' AND num_nonnulls(dependency_review_id,dependency_eligibility_id,dependency_seal_id) = 1 AND num_nonnulls(snapshot_observation_id,snapshot_link_id,snapshot_issue_id,snapshot_review_id,snapshot_review_seal_id) = 0 AND role NOT IN ('scope_observation','scope_link','scope_issue')) OR (entry_kind = 'scope_observation' AND num_nonnulls(dependency_review_id,dependency_eligibility_id,dependency_seal_id) = 0 AND snapshot_observation_id IS NOT NULL AND num_nonnulls(snapshot_link_id,snapshot_issue_id,snapshot_review_id,snapshot_review_seal_id) = 0 AND role = 'scope_observation') OR (entry_kind = 'scope_link' AND num_nonnulls(dependency_review_id,dependency_eligibility_id,dependency_seal_id) = 0 AND snapshot_observation_id IS NOT NULL AND snapshot_link_id IS NOT NULL AND snapshot_issue_id IS NULL AND role = 'scope_link') OR (entry_kind = 'scope_issue' AND num_nonnulls(dependency_review_id,dependency_eligibility_id,dependency_seal_id) = 0 AND snapshot_observation_id IS NOT NULL AND snapshot_issue_id IS NOT NULL AND snapshot_link_id IS NULL AND role = 'scope_issue')),
    CONSTRAINT ck_approval_dependency_02 CHECK (dependency_review_id IS NULL OR dependency_review_id <> owner_review_id),
    CONSTRAINT uq_approval_dependency_01 UNIQUE (investigation_id, owner_review_id, dependency_review_id, role),
    CONSTRAINT uq_approval_dependency_02 UNIQUE (investigation_id, owner_review_id, dependency_eligibility_id, role),
    CONSTRAINT uq_approval_dependency_03 UNIQUE (investigation_id, owner_review_id, dependency_seal_id, role),
    CONSTRAINT ck_approval_dependency_03 CHECK (entry_kind IN ('decision','scope_observation','scope_link','scope_issue')),
    CONSTRAINT ck_approval_dependency_04 CHECK (snapshot_review_seal_id IS NULL OR snapshot_review_id IS NOT NULL)
)""",
    """CREATE TABLE publication_event (
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
    CONSTRAINT pk_publication_event_01 PRIMARY KEY (investigation_id, id),
    CONSTRAINT ck_publication_event_01 CHECK (revision > 0),
    CONSTRAINT ck_publication_event_02 CHECK (action IN ('publish','revoke')),
    CONSTRAINT uq_publication_event_01 UNIQUE (investigation_id, result_id, revision),
    CONSTRAINT uq_publication_event_02 UNIQUE (investigation_id, supersedes_id)
)""",
)

FK_DDL = (
    'ALTER TABLE source_document ADD CONSTRAINT source_document_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE source_acquisition ADD CONSTRAINT source_acquisition_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE source_acquisition ADD CONSTRAINT source_acquisition_source_document_id_fk FOREIGN KEY (investigation_id, source_document_id) REFERENCES source_document (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE evidence_reference ADD CONSTRAINT evidence_reference_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE evidence_reference ADD CONSTRAINT evidence_reference_source_document_id_fk FOREIGN KEY (investigation_id, source_document_id) REFERENCES source_document (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE parse_run ADD CONSTRAINT parse_run_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE parse_run ADD CONSTRAINT parse_run_source_document_id_fk FOREIGN KEY (investigation_id, source_document_id) REFERENCES source_document (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE source_field ADD CONSTRAINT source_field_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE source_field ADD CONSTRAINT source_field_parse_run_id_fk FOREIGN KEY (investigation_id, parse_run_id) REFERENCES parse_run (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE source_field ADD CONSTRAINT source_field_header_evidence_id_fk FOREIGN KEY (investigation_id, header_evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE source_record ADD CONSTRAINT source_record_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE source_record ADD CONSTRAINT source_record_parse_run_id_fk FOREIGN KEY (investigation_id, parse_run_id) REFERENCES parse_run (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE source_record ADD CONSTRAINT source_record_row_evidence_id_fk FOREIGN KEY (investigation_id, row_evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE experimental_test ADD CONSTRAINT experimental_test_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE experimental_test ADD CONSTRAINT experimental_test_identity_evidence_id_fk FOREIGN KEY (investigation_id, identity_evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE test_source_record ADD CONSTRAINT test_source_record_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE test_source_record ADD CONSTRAINT test_source_record_experimental_test_id_fk FOREIGN KEY (investigation_id, experimental_test_id) REFERENCES experimental_test (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE test_source_record ADD CONSTRAINT test_source_record_source_record_id_fk FOREIGN KEY (investigation_id, source_record_id) REFERENCES source_record (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE test_source_record ADD CONSTRAINT test_source_record_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE test_relationship ADD CONSTRAINT test_relationship_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE test_relationship ADD CONSTRAINT test_relationship_left_test_id_fk FOREIGN KEY (investigation_id, left_test_id) REFERENCES experimental_test (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE test_relationship ADD CONSTRAINT test_relationship_right_test_id_fk FOREIGN KEY (investigation_id, right_test_id) REFERENCES experimental_test (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE test_relationship ADD CONSTRAINT test_relationship_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE observation ADD CONSTRAINT observation_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE observation ADD CONSTRAINT observation_parse_run_id_fk FOREIGN KEY (investigation_id, parse_run_id) REFERENCES parse_run (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE observation ADD CONSTRAINT observation_source_record_id_fk FOREIGN KEY (investigation_id, source_record_id) REFERENCES source_record (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE observation ADD CONSTRAINT observation_source_field_id_fk FOREIGN KEY (investigation_id, source_field_id) REFERENCES source_field (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE observation ADD CONSTRAINT observation_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE observation ADD CONSTRAINT observation_unit_evidence_id_fk FOREIGN KEY (investigation_id, unit_evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE scientific_variable ADD CONSTRAINT scientific_variable_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE scientific_variable ADD CONSTRAINT scientific_variable_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE semantic_annotation ADD CONSTRAINT semantic_annotation_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE semantic_annotation ADD CONSTRAINT semantic_annotation_observation_id_fk FOREIGN KEY (investigation_id, observation_id) REFERENCES observation (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE semantic_annotation ADD CONSTRAINT semantic_annotation_variable_id_fk FOREIGN KEY (investigation_id, variable_id) REFERENCES scientific_variable (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE semantic_annotation ADD CONSTRAINT semantic_annotation_supersedes_id_fk FOREIGN KEY (investigation_id, supersedes_id) REFERENCES semantic_annotation (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE semantic_annotation ADD CONSTRAINT semantic_annotation_primary_evidence_id_fk FOREIGN KEY (investigation_id, primary_evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE annotation_evidence ADD CONSTRAINT annotation_evidence_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE annotation_evidence ADD CONSTRAINT annotation_evidence_annotation_id_fk FOREIGN KEY (investigation_id, annotation_id) REFERENCES semantic_annotation (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE annotation_evidence ADD CONSTRAINT annotation_evidence_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE experimental_condition ADD CONSTRAINT experimental_condition_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE experimental_condition ADD CONSTRAINT experimental_condition_experimental_test_id_fk FOREIGN KEY (investigation_id, experimental_test_id) REFERENCES experimental_test (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE experimental_condition ADD CONSTRAINT experimental_condition_supersedes_id_fk FOREIGN KEY (investigation_id, supersedes_id) REFERENCES experimental_condition (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE experimental_condition ADD CONSTRAINT experimental_condition_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE data_quality_issue ADD CONSTRAINT data_quality_issue_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE data_quality_issue ADD CONSTRAINT data_quality_issue_observation_id_fk FOREIGN KEY (investigation_id, observation_id) REFERENCES observation (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE data_quality_issue ADD CONSTRAINT data_quality_issue_experimental_test_id_fk FOREIGN KEY (investigation_id, experimental_test_id) REFERENCES experimental_test (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE data_quality_issue ADD CONSTRAINT data_quality_issue_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE review_event ADD CONSTRAINT review_event_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE review_event ADD CONSTRAINT review_event_annotation_id_fk FOREIGN KEY (investigation_id, annotation_id) REFERENCES semantic_annotation (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE review_event ADD CONSTRAINT review_event_variable_id_fk FOREIGN KEY (investigation_id, variable_id) REFERENCES scientific_variable (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE review_event ADD CONSTRAINT review_event_condition_id_fk FOREIGN KEY (investigation_id, condition_id) REFERENCES experimental_condition (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE review_event ADD CONSTRAINT review_event_test_link_id_fk FOREIGN KEY (investigation_id, test_link_id) REFERENCES test_source_record (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE review_event ADD CONSTRAINT review_event_test_relation_id_fk FOREIGN KEY (investigation_id, test_relation_id) REFERENCES test_relationship (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE review_event ADD CONSTRAINT review_event_issue_id_fk FOREIGN KEY (investigation_id, issue_id) REFERENCES data_quality_issue (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE review_event ADD CONSTRAINT review_event_result_id_fk FOREIGN KEY (investigation_id, result_id) REFERENCES analytical_result (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE review_event ADD CONSTRAINT review_event_supersedes_id_fk FOREIGN KEY (investigation_id, supersedes_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE review_event ADD CONSTRAINT review_event_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE analysis_protocol ADD CONSTRAINT analysis_protocol_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE analysis_protocol ADD CONSTRAINT analysis_protocol_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_protocol_id_fk FOREIGN KEY (investigation_id, protocol_id) REFERENCES analysis_protocol (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_observation_id_fk FOREIGN KEY (investigation_id, observation_id) REFERENCES observation (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_experimental_test_id_fk FOREIGN KEY (investigation_id, experimental_test_id) REFERENCES experimental_test (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_supersedes_id_fk FOREIGN KEY (investigation_id, supersedes_id) REFERENCES analytical_eligibility (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_annotation_id_fk FOREIGN KEY (investigation_id, annotation_id) REFERENCES semantic_annotation (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_annotation_review_id_fk FOREIGN KEY (investigation_id, annotation_review_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_condition_id_fk FOREIGN KEY (investigation_id, condition_id) REFERENCES experimental_condition (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_condition_review_id_fk FOREIGN KEY (investigation_id, condition_review_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE analytical_result ADD CONSTRAINT analytical_result_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE analytical_result ADD CONSTRAINT analytical_result_protocol_id_fk FOREIGN KEY (investigation_id, protocol_id) REFERENCES analysis_protocol (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE analytical_result ADD CONSTRAINT analytical_result_artifact_document_id_fk FOREIGN KEY (investigation_id, artifact_document_id) REFERENCES source_document (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE result_input ADD CONSTRAINT result_input_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE result_input ADD CONSTRAINT result_input_result_id_fk FOREIGN KEY (investigation_id, result_id) REFERENCES analytical_result (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE result_input ADD CONSTRAINT result_input_annotation_id_fk FOREIGN KEY (investigation_id, annotation_id) REFERENCES semantic_annotation (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE result_input ADD CONSTRAINT result_input_eligibility_id_fk FOREIGN KEY (investigation_id, eligibility_id) REFERENCES analytical_eligibility (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE result_input ADD CONSTRAINT result_input_test_link_id_fk FOREIGN KEY (investigation_id, test_link_id) REFERENCES test_source_record (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE result_input ADD CONSTRAINT result_input_test_link_review_id_fk FOREIGN KEY (investigation_id, test_link_review_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE result_condition ADD CONSTRAINT result_condition_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE result_condition ADD CONSTRAINT result_condition_result_id_fk FOREIGN KEY (investigation_id, result_id) REFERENCES analytical_result (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE result_condition ADD CONSTRAINT result_condition_condition_id_fk FOREIGN KEY (investigation_id, condition_id) REFERENCES experimental_condition (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE result_condition ADD CONSTRAINT result_condition_eligibility_id_fk FOREIGN KEY (investigation_id, eligibility_id) REFERENCES analytical_eligibility (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE result_evidence ADD CONSTRAINT result_evidence_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE result_evidence ADD CONSTRAINT result_evidence_result_id_fk FOREIGN KEY (investigation_id, result_id) REFERENCES analytical_result (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE result_evidence ADD CONSTRAINT result_evidence_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE observation ADD CONSTRAINT observation_source_record_id_same_run_fk FOREIGN KEY (investigation_id, parse_run_id, source_record_id) REFERENCES source_record (investigation_id, parse_run_id, id) ON DELETE RESTRICT',
    'ALTER TABLE observation ADD CONSTRAINT observation_source_field_id_same_run_fk FOREIGN KEY (investigation_id, parse_run_id, source_field_id) REFERENCES source_field (investigation_id, parse_run_id, id) ON DELETE RESTRICT',
    'ALTER TABLE condition_segment ADD CONSTRAINT condition_segment_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE condition_segment ADD CONSTRAINT condition_segment_experimental_test_id_fk FOREIGN KEY (investigation_id, experimental_test_id) REFERENCES experimental_test (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE condition_segment ADD CONSTRAINT condition_segment_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE instrument ADD CONSTRAINT instrument_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE instrument ADD CONSTRAINT instrument_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE condition_role ADD CONSTRAINT condition_role_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE condition_role ADD CONSTRAINT condition_role_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE condition_component ADD CONSTRAINT condition_component_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE condition_component ADD CONSTRAINT condition_component_condition_id_fk FOREIGN KEY (investigation_id, condition_id) REFERENCES experimental_condition (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE condition_component ADD CONSTRAINT condition_component_role_id_fk FOREIGN KEY (investigation_id, role_id) REFERENCES condition_role (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE condition_component ADD CONSTRAINT condition_component_instrument_id_fk FOREIGN KEY (investigation_id, instrument_id) REFERENCES instrument (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE condition_component ADD CONSTRAINT condition_component_variable_id_fk FOREIGN KEY (investigation_id, variable_id) REFERENCES scientific_variable (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE condition_component ADD CONSTRAINT condition_component_annotation_id_fk FOREIGN KEY (investigation_id, annotation_id) REFERENCES semantic_annotation (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE condition_component ADD CONSTRAINT condition_component_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE experimental_condition ADD CONSTRAINT experimental_condition_segment_id_fk FOREIGN KEY (investigation_id, segment_id) REFERENCES condition_segment (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE result_input ADD CONSTRAINT result_input_segment_id_fk FOREIGN KEY (investigation_id, segment_id) REFERENCES condition_segment (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE protocol_requirement ADD CONSTRAINT protocol_requirement_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE protocol_requirement ADD CONSTRAINT protocol_requirement_protocol_id_fk FOREIGN KEY (investigation_id, protocol_id) REFERENCES analysis_protocol (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE protocol_requirement ADD CONSTRAINT protocol_requirement_variable_id_fk FOREIGN KEY (investigation_id, variable_id) REFERENCES scientific_variable (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE protocol_requirement ADD CONSTRAINT protocol_requirement_role_id_fk FOREIGN KEY (investigation_id, role_id) REFERENCES condition_role (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE protocol_requirement ADD CONSTRAINT protocol_requirement_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE protocol_unit_rule ADD CONSTRAINT protocol_unit_rule_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE protocol_unit_rule ADD CONSTRAINT protocol_unit_rule_requirement_id_fk FOREIGN KEY (investigation_id, requirement_id) REFERENCES protocol_requirement (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE protocol_unit_rule ADD CONSTRAINT protocol_unit_rule_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE metadata_revision ADD CONSTRAINT metadata_revision_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE metadata_revision ADD CONSTRAINT metadata_revision_source_document_id_fk FOREIGN KEY (investigation_id, source_document_id) REFERENCES source_document (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE metadata_revision ADD CONSTRAINT metadata_revision_supersedes_id_fk FOREIGN KEY (investigation_id, supersedes_id) REFERENCES metadata_revision (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE metadata_revision ADD CONSTRAINT metadata_revision_evidence_id_fk FOREIGN KEY (investigation_id, evidence_id) REFERENCES evidence_reference (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE review_event ADD CONSTRAINT review_event_metadata_revision_id_fk FOREIGN KEY (investigation_id, metadata_revision_id) REFERENCES metadata_revision (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE aggregate_seal ADD CONSTRAINT aggregate_seal_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE aggregate_seal ADD CONSTRAINT aggregate_seal_parse_run_id_fk FOREIGN KEY (investigation_id, parse_run_id) REFERENCES parse_run (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE aggregate_seal ADD CONSTRAINT aggregate_seal_annotation_id_fk FOREIGN KEY (investigation_id, annotation_id) REFERENCES semantic_annotation (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE aggregate_seal ADD CONSTRAINT aggregate_seal_condition_id_fk FOREIGN KEY (investigation_id, condition_id) REFERENCES experimental_condition (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE aggregate_seal ADD CONSTRAINT aggregate_seal_protocol_id_fk FOREIGN KEY (investigation_id, protocol_id) REFERENCES analysis_protocol (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE aggregate_seal ADD CONSTRAINT aggregate_seal_result_id_fk FOREIGN KEY (investigation_id, result_id) REFERENCES analytical_result (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE aggregate_seal ADD CONSTRAINT aggregate_seal_review_id_fk FOREIGN KEY (investigation_id, review_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE approval_dependency ADD CONSTRAINT approval_dependency_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE approval_dependency ADD CONSTRAINT approval_dependency_owner_review_id_fk FOREIGN KEY (investigation_id, owner_review_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE approval_dependency ADD CONSTRAINT approval_dependency_dependency_review_id_fk FOREIGN KEY (investigation_id, dependency_review_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE approval_dependency ADD CONSTRAINT approval_dependency_dependency_eligibility_id_fk FOREIGN KEY (investigation_id, dependency_eligibility_id) REFERENCES analytical_eligibility (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE approval_dependency ADD CONSTRAINT approval_dependency_dependency_seal_id_fk FOREIGN KEY (investigation_id, dependency_seal_id) REFERENCES aggregate_seal (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE publication_event ADD CONSTRAINT publication_event_investigation_id_fk FOREIGN KEY (investigation_id) REFERENCES investigation (id) ON DELETE RESTRICT',
    'ALTER TABLE publication_event ADD CONSTRAINT publication_event_result_id_fk FOREIGN KEY (investigation_id, result_id) REFERENCES analytical_result (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE publication_event ADD CONSTRAINT publication_event_result_seal_id_fk FOREIGN KEY (investigation_id, result_seal_id) REFERENCES aggregate_seal (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE publication_event ADD CONSTRAINT publication_event_result_review_id_fk FOREIGN KEY (investigation_id, result_review_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE publication_event ADD CONSTRAINT publication_event_review_seal_id_fk FOREIGN KEY (investigation_id, review_seal_id) REFERENCES aggregate_seal (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE publication_event ADD CONSTRAINT publication_event_supersedes_id_fk FOREIGN KEY (investigation_id, supersedes_id) REFERENCES publication_event (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE analytical_eligibility ADD CONSTRAINT analytical_eligibility_segment_id_fk FOREIGN KEY (investigation_id, segment_id) REFERENCES condition_segment (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE approval_dependency ADD CONSTRAINT ad_snapshot_observation_id_fk FOREIGN KEY (investigation_id, snapshot_observation_id) REFERENCES observation (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE approval_dependency ADD CONSTRAINT ad_snapshot_link_id_fk FOREIGN KEY (investigation_id, snapshot_link_id) REFERENCES test_source_record (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE approval_dependency ADD CONSTRAINT ad_snapshot_issue_id_fk FOREIGN KEY (investigation_id, snapshot_issue_id) REFERENCES data_quality_issue (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE approval_dependency ADD CONSTRAINT ad_snapshot_review_id_fk FOREIGN KEY (investigation_id, snapshot_review_id) REFERENCES review_event (investigation_id, id) ON DELETE RESTRICT',
    'ALTER TABLE approval_dependency ADD CONSTRAINT ad_snapshot_review_seal_id_fk FOREIGN KEY (investigation_id, snapshot_review_seal_id) REFERENCES aggregate_seal (investigation_id, id) ON DELETE RESTRICT',
)

INDEX_DDL = (
    "CREATE UNIQUE INDEX metadata_investigation_revision ON metadata_revision (investigation_id, revision) WHERE subject_kind = 'investigation'",
    'CREATE INDEX lookup_2 ON source_acquisition (investigation_id, source_document_id)',
    'CREATE INDEX lookup_4 ON evidence_reference (investigation_id, source_document_id)',
    'CREATE INDEX lookup_6 ON parse_run (investigation_id, source_document_id)',
    'CREATE INDEX lookup_8 ON source_field (investigation_id, parse_run_id)',
    'CREATE INDEX lookup_9 ON source_field (investigation_id, header_evidence_id)',
    'CREATE INDEX lookup_11 ON source_record (investigation_id, parse_run_id)',
    'CREATE INDEX lookup_12 ON source_record (investigation_id, row_evidence_id)',
    'CREATE INDEX lookup_14 ON experimental_test (investigation_id, identity_evidence_id)',
    'CREATE INDEX lookup_16 ON test_source_record (investigation_id, experimental_test_id)',
    'CREATE INDEX lookup_17 ON test_source_record (investigation_id, source_record_id)',
    'CREATE INDEX lookup_18 ON test_source_record (investigation_id, evidence_id)',
    'CREATE INDEX lookup_20 ON test_relationship (investigation_id, left_test_id)',
    'CREATE INDEX lookup_21 ON test_relationship (investigation_id, right_test_id)',
    'CREATE INDEX lookup_22 ON test_relationship (investigation_id, evidence_id)',
    'CREATE INDEX lookup_24 ON observation (investigation_id, parse_run_id)',
    'CREATE INDEX lookup_25 ON observation (investigation_id, source_record_id)',
    'CREATE INDEX lookup_26 ON observation (investigation_id, source_field_id)',
    'CREATE INDEX lookup_27 ON observation (investigation_id, evidence_id)',
    'CREATE INDEX lookup_28 ON observation (investigation_id, unit_evidence_id)',
    'CREATE INDEX lookup_30 ON scientific_variable (investigation_id, evidence_id)',
    'CREATE INDEX lookup_32 ON semantic_annotation (investigation_id, observation_id)',
    'CREATE INDEX lookup_33 ON semantic_annotation (investigation_id, variable_id)',
    'CREATE INDEX lookup_34 ON semantic_annotation (investigation_id, supersedes_id)',
    'CREATE INDEX lookup_35 ON semantic_annotation (investigation_id, primary_evidence_id)',
    'CREATE INDEX lookup_37 ON annotation_evidence (investigation_id, annotation_id)',
    'CREATE INDEX lookup_38 ON annotation_evidence (investigation_id, evidence_id)',
    'CREATE INDEX lookup_40 ON experimental_condition (investigation_id, experimental_test_id)',
    'CREATE INDEX lookup_41 ON experimental_condition (investigation_id, supersedes_id)',
    'CREATE INDEX lookup_42 ON experimental_condition (investigation_id, evidence_id)',
    'CREATE INDEX lookup_44 ON data_quality_issue (investigation_id, observation_id)',
    'CREATE INDEX lookup_45 ON data_quality_issue (investigation_id, experimental_test_id)',
    'CREATE INDEX lookup_46 ON data_quality_issue (investigation_id, evidence_id)',
    'CREATE INDEX lookup_48 ON review_event (investigation_id, annotation_id)',
    'CREATE INDEX lookup_49 ON review_event (investigation_id, variable_id)',
    'CREATE INDEX lookup_50 ON review_event (investigation_id, condition_id)',
    'CREATE INDEX lookup_51 ON review_event (investigation_id, test_link_id)',
    'CREATE INDEX lookup_52 ON review_event (investigation_id, test_relation_id)',
    'CREATE INDEX lookup_53 ON review_event (investigation_id, issue_id)',
    'CREATE INDEX lookup_54 ON review_event (investigation_id, result_id)',
    'CREATE INDEX lookup_55 ON review_event (investigation_id, supersedes_id)',
    'CREATE INDEX lookup_56 ON review_event (investigation_id, evidence_id)',
    'CREATE INDEX lookup_58 ON analysis_protocol (investigation_id, evidence_id)',
    'CREATE INDEX lookup_60 ON analytical_eligibility (investigation_id, protocol_id)',
    'CREATE INDEX lookup_61 ON analytical_eligibility (investigation_id, observation_id)',
    'CREATE INDEX lookup_62 ON analytical_eligibility (investigation_id, experimental_test_id)',
    'CREATE INDEX lookup_63 ON analytical_eligibility (investigation_id, supersedes_id)',
    'CREATE INDEX lookup_64 ON analytical_eligibility (investigation_id, annotation_id)',
    'CREATE INDEX lookup_65 ON analytical_eligibility (investigation_id, annotation_review_id)',
    'CREATE INDEX lookup_66 ON analytical_eligibility (investigation_id, condition_id)',
    'CREATE INDEX lookup_67 ON analytical_eligibility (investigation_id, condition_review_id)',
    'CREATE INDEX lookup_68 ON analytical_eligibility (investigation_id, evidence_id)',
    'CREATE INDEX lookup_70 ON analytical_result (investigation_id, protocol_id)',
    'CREATE INDEX lookup_71 ON analytical_result (investigation_id, artifact_document_id)',
    'CREATE INDEX lookup_73 ON result_input (investigation_id, result_id)',
    'CREATE INDEX lookup_74 ON result_input (investigation_id, annotation_id)',
    'CREATE INDEX lookup_75 ON result_input (investigation_id, eligibility_id)',
    'CREATE INDEX lookup_76 ON result_input (investigation_id, test_link_id)',
    'CREATE INDEX lookup_77 ON result_input (investigation_id, test_link_review_id)',
    'CREATE INDEX lookup_79 ON result_condition (investigation_id, result_id)',
    'CREATE INDEX lookup_80 ON result_condition (investigation_id, condition_id)',
    'CREATE INDEX lookup_81 ON result_condition (investigation_id, eligibility_id)',
    'CREATE INDEX lookup_83 ON result_evidence (investigation_id, result_id)',
    'CREATE INDEX lookup_84 ON result_evidence (investigation_id, evidence_id)',
    'CREATE INDEX lookup_85 ON observation (investigation_id, parse_run_id, source_record_id)',
    'CREATE INDEX lookup_86 ON observation (investigation_id, parse_run_id, source_field_id)',
    'CREATE INDEX lookup_88 ON condition_segment (investigation_id, experimental_test_id)',
    'CREATE INDEX lookup_89 ON condition_segment (investigation_id, evidence_id)',
    'CREATE INDEX lookup_91 ON instrument (investigation_id, evidence_id)',
    'CREATE INDEX lookup_93 ON condition_role (investigation_id, evidence_id)',
    'CREATE INDEX lookup_95 ON condition_component (investigation_id, condition_id)',
    'CREATE INDEX lookup_96 ON condition_component (investigation_id, role_id)',
    'CREATE INDEX lookup_97 ON condition_component (investigation_id, instrument_id)',
    'CREATE INDEX lookup_98 ON condition_component (investigation_id, variable_id)',
    'CREATE INDEX lookup_99 ON condition_component (investigation_id, annotation_id)',
    'CREATE INDEX lookup_100 ON condition_component (investigation_id, evidence_id)',
    'CREATE INDEX lookup_101 ON experimental_condition (investigation_id, segment_id)',
    'CREATE INDEX lookup_102 ON result_input (investigation_id, segment_id)',
    'CREATE INDEX lookup_104 ON protocol_requirement (investigation_id, protocol_id)',
    'CREATE INDEX lookup_105 ON protocol_requirement (investigation_id, variable_id)',
    'CREATE INDEX lookup_106 ON protocol_requirement (investigation_id, role_id)',
    'CREATE INDEX lookup_107 ON protocol_requirement (investigation_id, evidence_id)',
    'CREATE INDEX lookup_109 ON protocol_unit_rule (investigation_id, requirement_id)',
    'CREATE INDEX lookup_110 ON protocol_unit_rule (investigation_id, evidence_id)',
    'CREATE INDEX lookup_112 ON metadata_revision (investigation_id, source_document_id)',
    'CREATE INDEX lookup_113 ON metadata_revision (investigation_id, supersedes_id)',
    'CREATE INDEX lookup_114 ON metadata_revision (investigation_id, evidence_id)',
    'CREATE INDEX lookup_115 ON review_event (investigation_id, metadata_revision_id)',
    'CREATE INDEX lookup_117 ON aggregate_seal (investigation_id, parse_run_id)',
    'CREATE INDEX lookup_118 ON aggregate_seal (investigation_id, annotation_id)',
    'CREATE INDEX lookup_119 ON aggregate_seal (investigation_id, condition_id)',
    'CREATE INDEX lookup_120 ON aggregate_seal (investigation_id, protocol_id)',
    'CREATE INDEX lookup_121 ON aggregate_seal (investigation_id, result_id)',
    'CREATE INDEX lookup_122 ON aggregate_seal (investigation_id, review_id)',
    'CREATE INDEX lookup_124 ON approval_dependency (investigation_id, owner_review_id)',
    'CREATE INDEX lookup_125 ON approval_dependency (investigation_id, dependency_review_id)',
    'CREATE INDEX lookup_126 ON approval_dependency (investigation_id, dependency_eligibility_id)',
    'CREATE INDEX lookup_127 ON approval_dependency (investigation_id, dependency_seal_id)',
    'CREATE INDEX lookup_129 ON publication_event (investigation_id, result_id)',
    'CREATE INDEX lookup_130 ON publication_event (investigation_id, result_seal_id)',
    'CREATE INDEX lookup_131 ON publication_event (investigation_id, result_review_id)',
    'CREATE INDEX lookup_132 ON publication_event (investigation_id, review_seal_id)',
    'CREATE INDEX lookup_133 ON publication_event (investigation_id, supersedes_id)',
    'CREATE INDEX lookup_134 ON analytical_eligibility (investigation_id, segment_id)',
    "CREATE UNIQUE INDEX ad_scope_observation_once ON approval_dependency (investigation_id, owner_review_id, snapshot_observation_id) WHERE entry_kind = 'scope_observation'",
    "CREATE UNIQUE INDEX ad_scope_link_once ON approval_dependency (investigation_id, owner_review_id, snapshot_observation_id, snapshot_link_id) WHERE entry_kind = 'scope_link'",
    "CREATE UNIQUE INDEX ad_scope_issue_once ON approval_dependency (investigation_id, owner_review_id, snapshot_observation_id, snapshot_issue_id) WHERE entry_kind = 'scope_issue'",
    'CREATE INDEX lookup_135 ON approval_dependency (investigation_id, snapshot_observation_id)',
    'CREATE INDEX lookup_136 ON approval_dependency (investigation_id, snapshot_link_id)',
    'CREATE INDEX lookup_137 ON approval_dependency (investigation_id, snapshot_issue_id)',
    'CREATE INDEX lookup_138 ON approval_dependency (investigation_id, snapshot_review_id)',
    'CREATE INDEX lookup_139 ON approval_dependency (investigation_id, snapshot_review_seal_id)',
)

def upgrade():
    for statement in (*TABLE_DDL, *FK_DDL, *INDEX_DDL):
        op.execute(statement)


def downgrade():
    confirmed = context.config.attributes.get("allow_destructive_downgrade") is True
    confirmed = confirmed or context.get_x_argument(as_dictionary=True).get("confirm_destructive_downgrade") == "yes"
    if not confirmed:
        raise CommandError("Destructive M4.2 downgrade requires explicit confirm_destructive_downgrade=yes")
    op.execute("ALTER TABLE approval_dependency DROP CONSTRAINT ad_snapshot_review_seal_id_fk")
    op.execute("ALTER TABLE approval_dependency DROP CONSTRAINT ad_snapshot_review_id_fk")
    op.execute("ALTER TABLE approval_dependency DROP CONSTRAINT ad_snapshot_issue_id_fk")
    op.execute("ALTER TABLE approval_dependency DROP CONSTRAINT ad_snapshot_link_id_fk")
    op.execute("ALTER TABLE approval_dependency DROP CONSTRAINT ad_snapshot_observation_id_fk")
    op.execute("ALTER TABLE analytical_eligibility DROP CONSTRAINT analytical_eligibility_segment_id_fk")
    op.execute("ALTER TABLE publication_event DROP CONSTRAINT publication_event_supersedes_id_fk")
    op.execute("ALTER TABLE publication_event DROP CONSTRAINT publication_event_review_seal_id_fk")
    op.execute("ALTER TABLE publication_event DROP CONSTRAINT publication_event_result_review_id_fk")
    op.execute("ALTER TABLE publication_event DROP CONSTRAINT publication_event_result_seal_id_fk")
    op.execute("ALTER TABLE publication_event DROP CONSTRAINT publication_event_result_id_fk")
    op.execute("ALTER TABLE publication_event DROP CONSTRAINT publication_event_investigation_id_fk")
    op.execute("ALTER TABLE approval_dependency DROP CONSTRAINT approval_dependency_dependency_seal_id_fk")
    op.execute("ALTER TABLE approval_dependency DROP CONSTRAINT approval_dependency_dependency_eligibility_id_fk")
    op.execute("ALTER TABLE approval_dependency DROP CONSTRAINT approval_dependency_dependency_review_id_fk")
    op.execute("ALTER TABLE approval_dependency DROP CONSTRAINT approval_dependency_owner_review_id_fk")
    op.execute("ALTER TABLE approval_dependency DROP CONSTRAINT approval_dependency_investigation_id_fk")
    op.execute("ALTER TABLE aggregate_seal DROP CONSTRAINT aggregate_seal_review_id_fk")
    op.execute("ALTER TABLE aggregate_seal DROP CONSTRAINT aggregate_seal_result_id_fk")
    op.execute("ALTER TABLE aggregate_seal DROP CONSTRAINT aggregate_seal_protocol_id_fk")
    op.execute("ALTER TABLE aggregate_seal DROP CONSTRAINT aggregate_seal_condition_id_fk")
    op.execute("ALTER TABLE aggregate_seal DROP CONSTRAINT aggregate_seal_annotation_id_fk")
    op.execute("ALTER TABLE aggregate_seal DROP CONSTRAINT aggregate_seal_parse_run_id_fk")
    op.execute("ALTER TABLE aggregate_seal DROP CONSTRAINT aggregate_seal_investigation_id_fk")
    op.execute("ALTER TABLE review_event DROP CONSTRAINT review_event_metadata_revision_id_fk")
    op.execute("ALTER TABLE metadata_revision DROP CONSTRAINT metadata_revision_evidence_id_fk")
    op.execute("ALTER TABLE metadata_revision DROP CONSTRAINT metadata_revision_supersedes_id_fk")
    op.execute("ALTER TABLE metadata_revision DROP CONSTRAINT metadata_revision_source_document_id_fk")
    op.execute("ALTER TABLE metadata_revision DROP CONSTRAINT metadata_revision_investigation_id_fk")
    op.execute("ALTER TABLE protocol_unit_rule DROP CONSTRAINT protocol_unit_rule_evidence_id_fk")
    op.execute("ALTER TABLE protocol_unit_rule DROP CONSTRAINT protocol_unit_rule_requirement_id_fk")
    op.execute("ALTER TABLE protocol_unit_rule DROP CONSTRAINT protocol_unit_rule_investigation_id_fk")
    op.execute("ALTER TABLE protocol_requirement DROP CONSTRAINT protocol_requirement_evidence_id_fk")
    op.execute("ALTER TABLE protocol_requirement DROP CONSTRAINT protocol_requirement_role_id_fk")
    op.execute("ALTER TABLE protocol_requirement DROP CONSTRAINT protocol_requirement_variable_id_fk")
    op.execute("ALTER TABLE protocol_requirement DROP CONSTRAINT protocol_requirement_protocol_id_fk")
    op.execute("ALTER TABLE protocol_requirement DROP CONSTRAINT protocol_requirement_investigation_id_fk")
    op.execute("ALTER TABLE result_input DROP CONSTRAINT result_input_segment_id_fk")
    op.execute("ALTER TABLE experimental_condition DROP CONSTRAINT experimental_condition_segment_id_fk")
    op.execute("ALTER TABLE condition_component DROP CONSTRAINT condition_component_evidence_id_fk")
    op.execute("ALTER TABLE condition_component DROP CONSTRAINT condition_component_annotation_id_fk")
    op.execute("ALTER TABLE condition_component DROP CONSTRAINT condition_component_variable_id_fk")
    op.execute("ALTER TABLE condition_component DROP CONSTRAINT condition_component_instrument_id_fk")
    op.execute("ALTER TABLE condition_component DROP CONSTRAINT condition_component_role_id_fk")
    op.execute("ALTER TABLE condition_component DROP CONSTRAINT condition_component_condition_id_fk")
    op.execute("ALTER TABLE condition_component DROP CONSTRAINT condition_component_investigation_id_fk")
    op.execute("ALTER TABLE condition_role DROP CONSTRAINT condition_role_evidence_id_fk")
    op.execute("ALTER TABLE condition_role DROP CONSTRAINT condition_role_investigation_id_fk")
    op.execute("ALTER TABLE instrument DROP CONSTRAINT instrument_evidence_id_fk")
    op.execute("ALTER TABLE instrument DROP CONSTRAINT instrument_investigation_id_fk")
    op.execute("ALTER TABLE condition_segment DROP CONSTRAINT condition_segment_evidence_id_fk")
    op.execute("ALTER TABLE condition_segment DROP CONSTRAINT condition_segment_experimental_test_id_fk")
    op.execute("ALTER TABLE condition_segment DROP CONSTRAINT condition_segment_investigation_id_fk")
    op.execute("ALTER TABLE observation DROP CONSTRAINT observation_source_field_id_same_run_fk")
    op.execute("ALTER TABLE observation DROP CONSTRAINT observation_source_record_id_same_run_fk")
    op.execute("ALTER TABLE result_evidence DROP CONSTRAINT result_evidence_evidence_id_fk")
    op.execute("ALTER TABLE result_evidence DROP CONSTRAINT result_evidence_result_id_fk")
    op.execute("ALTER TABLE result_evidence DROP CONSTRAINT result_evidence_investigation_id_fk")
    op.execute("ALTER TABLE result_condition DROP CONSTRAINT result_condition_eligibility_id_fk")
    op.execute("ALTER TABLE result_condition DROP CONSTRAINT result_condition_condition_id_fk")
    op.execute("ALTER TABLE result_condition DROP CONSTRAINT result_condition_result_id_fk")
    op.execute("ALTER TABLE result_condition DROP CONSTRAINT result_condition_investigation_id_fk")
    op.execute("ALTER TABLE result_input DROP CONSTRAINT result_input_test_link_review_id_fk")
    op.execute("ALTER TABLE result_input DROP CONSTRAINT result_input_test_link_id_fk")
    op.execute("ALTER TABLE result_input DROP CONSTRAINT result_input_eligibility_id_fk")
    op.execute("ALTER TABLE result_input DROP CONSTRAINT result_input_annotation_id_fk")
    op.execute("ALTER TABLE result_input DROP CONSTRAINT result_input_result_id_fk")
    op.execute("ALTER TABLE result_input DROP CONSTRAINT result_input_investigation_id_fk")
    op.execute("ALTER TABLE analytical_result DROP CONSTRAINT analytical_result_artifact_document_id_fk")
    op.execute("ALTER TABLE analytical_result DROP CONSTRAINT analytical_result_protocol_id_fk")
    op.execute("ALTER TABLE analytical_result DROP CONSTRAINT analytical_result_investigation_id_fk")
    op.execute("ALTER TABLE analytical_eligibility DROP CONSTRAINT analytical_eligibility_evidence_id_fk")
    op.execute("ALTER TABLE analytical_eligibility DROP CONSTRAINT analytical_eligibility_condition_review_id_fk")
    op.execute("ALTER TABLE analytical_eligibility DROP CONSTRAINT analytical_eligibility_condition_id_fk")
    op.execute("ALTER TABLE analytical_eligibility DROP CONSTRAINT analytical_eligibility_annotation_review_id_fk")
    op.execute("ALTER TABLE analytical_eligibility DROP CONSTRAINT analytical_eligibility_annotation_id_fk")
    op.execute("ALTER TABLE analytical_eligibility DROP CONSTRAINT analytical_eligibility_supersedes_id_fk")
    op.execute("ALTER TABLE analytical_eligibility DROP CONSTRAINT analytical_eligibility_experimental_test_id_fk")
    op.execute("ALTER TABLE analytical_eligibility DROP CONSTRAINT analytical_eligibility_observation_id_fk")
    op.execute("ALTER TABLE analytical_eligibility DROP CONSTRAINT analytical_eligibility_protocol_id_fk")
    op.execute("ALTER TABLE analytical_eligibility DROP CONSTRAINT analytical_eligibility_investigation_id_fk")
    op.execute("ALTER TABLE analysis_protocol DROP CONSTRAINT analysis_protocol_evidence_id_fk")
    op.execute("ALTER TABLE analysis_protocol DROP CONSTRAINT analysis_protocol_investigation_id_fk")
    op.execute("ALTER TABLE review_event DROP CONSTRAINT review_event_evidence_id_fk")
    op.execute("ALTER TABLE review_event DROP CONSTRAINT review_event_supersedes_id_fk")
    op.execute("ALTER TABLE review_event DROP CONSTRAINT review_event_result_id_fk")
    op.execute("ALTER TABLE review_event DROP CONSTRAINT review_event_issue_id_fk")
    op.execute("ALTER TABLE review_event DROP CONSTRAINT review_event_test_relation_id_fk")
    op.execute("ALTER TABLE review_event DROP CONSTRAINT review_event_test_link_id_fk")
    op.execute("ALTER TABLE review_event DROP CONSTRAINT review_event_condition_id_fk")
    op.execute("ALTER TABLE review_event DROP CONSTRAINT review_event_variable_id_fk")
    op.execute("ALTER TABLE review_event DROP CONSTRAINT review_event_annotation_id_fk")
    op.execute("ALTER TABLE review_event DROP CONSTRAINT review_event_investigation_id_fk")
    op.execute("ALTER TABLE data_quality_issue DROP CONSTRAINT data_quality_issue_evidence_id_fk")
    op.execute("ALTER TABLE data_quality_issue DROP CONSTRAINT data_quality_issue_experimental_test_id_fk")
    op.execute("ALTER TABLE data_quality_issue DROP CONSTRAINT data_quality_issue_observation_id_fk")
    op.execute("ALTER TABLE data_quality_issue DROP CONSTRAINT data_quality_issue_investigation_id_fk")
    op.execute("ALTER TABLE experimental_condition DROP CONSTRAINT experimental_condition_evidence_id_fk")
    op.execute("ALTER TABLE experimental_condition DROP CONSTRAINT experimental_condition_supersedes_id_fk")
    op.execute("ALTER TABLE experimental_condition DROP CONSTRAINT experimental_condition_experimental_test_id_fk")
    op.execute("ALTER TABLE experimental_condition DROP CONSTRAINT experimental_condition_investigation_id_fk")
    op.execute("ALTER TABLE annotation_evidence DROP CONSTRAINT annotation_evidence_evidence_id_fk")
    op.execute("ALTER TABLE annotation_evidence DROP CONSTRAINT annotation_evidence_annotation_id_fk")
    op.execute("ALTER TABLE annotation_evidence DROP CONSTRAINT annotation_evidence_investigation_id_fk")
    op.execute("ALTER TABLE semantic_annotation DROP CONSTRAINT semantic_annotation_primary_evidence_id_fk")
    op.execute("ALTER TABLE semantic_annotation DROP CONSTRAINT semantic_annotation_supersedes_id_fk")
    op.execute("ALTER TABLE semantic_annotation DROP CONSTRAINT semantic_annotation_variable_id_fk")
    op.execute("ALTER TABLE semantic_annotation DROP CONSTRAINT semantic_annotation_observation_id_fk")
    op.execute("ALTER TABLE semantic_annotation DROP CONSTRAINT semantic_annotation_investigation_id_fk")
    op.execute("ALTER TABLE scientific_variable DROP CONSTRAINT scientific_variable_evidence_id_fk")
    op.execute("ALTER TABLE scientific_variable DROP CONSTRAINT scientific_variable_investigation_id_fk")
    op.execute("ALTER TABLE observation DROP CONSTRAINT observation_unit_evidence_id_fk")
    op.execute("ALTER TABLE observation DROP CONSTRAINT observation_evidence_id_fk")
    op.execute("ALTER TABLE observation DROP CONSTRAINT observation_source_field_id_fk")
    op.execute("ALTER TABLE observation DROP CONSTRAINT observation_source_record_id_fk")
    op.execute("ALTER TABLE observation DROP CONSTRAINT observation_parse_run_id_fk")
    op.execute("ALTER TABLE observation DROP CONSTRAINT observation_investigation_id_fk")
    op.execute("ALTER TABLE test_relationship DROP CONSTRAINT test_relationship_evidence_id_fk")
    op.execute("ALTER TABLE test_relationship DROP CONSTRAINT test_relationship_right_test_id_fk")
    op.execute("ALTER TABLE test_relationship DROP CONSTRAINT test_relationship_left_test_id_fk")
    op.execute("ALTER TABLE test_relationship DROP CONSTRAINT test_relationship_investigation_id_fk")
    op.execute("ALTER TABLE test_source_record DROP CONSTRAINT test_source_record_evidence_id_fk")
    op.execute("ALTER TABLE test_source_record DROP CONSTRAINT test_source_record_source_record_id_fk")
    op.execute("ALTER TABLE test_source_record DROP CONSTRAINT test_source_record_experimental_test_id_fk")
    op.execute("ALTER TABLE test_source_record DROP CONSTRAINT test_source_record_investigation_id_fk")
    op.execute("ALTER TABLE experimental_test DROP CONSTRAINT experimental_test_identity_evidence_id_fk")
    op.execute("ALTER TABLE experimental_test DROP CONSTRAINT experimental_test_investigation_id_fk")
    op.execute("ALTER TABLE source_record DROP CONSTRAINT source_record_row_evidence_id_fk")
    op.execute("ALTER TABLE source_record DROP CONSTRAINT source_record_parse_run_id_fk")
    op.execute("ALTER TABLE source_record DROP CONSTRAINT source_record_investigation_id_fk")
    op.execute("ALTER TABLE source_field DROP CONSTRAINT source_field_header_evidence_id_fk")
    op.execute("ALTER TABLE source_field DROP CONSTRAINT source_field_parse_run_id_fk")
    op.execute("ALTER TABLE source_field DROP CONSTRAINT source_field_investigation_id_fk")
    op.execute("ALTER TABLE parse_run DROP CONSTRAINT parse_run_source_document_id_fk")
    op.execute("ALTER TABLE parse_run DROP CONSTRAINT parse_run_investigation_id_fk")
    op.execute("ALTER TABLE evidence_reference DROP CONSTRAINT evidence_reference_source_document_id_fk")
    op.execute("ALTER TABLE evidence_reference DROP CONSTRAINT evidence_reference_investigation_id_fk")
    op.execute("ALTER TABLE source_acquisition DROP CONSTRAINT source_acquisition_source_document_id_fk")
    op.execute("ALTER TABLE source_acquisition DROP CONSTRAINT source_acquisition_investigation_id_fk")
    op.execute("ALTER TABLE source_document DROP CONSTRAINT source_document_investigation_id_fk")
    op.execute("DROP TABLE publication_event")
    op.execute("DROP TABLE approval_dependency")
    op.execute("DROP TABLE aggregate_seal")
    op.execute("DROP TABLE metadata_revision")
    op.execute("DROP TABLE protocol_unit_rule")
    op.execute("DROP TABLE protocol_requirement")
    op.execute("DROP TABLE condition_component")
    op.execute("DROP TABLE condition_role")
    op.execute("DROP TABLE instrument")
    op.execute("DROP TABLE condition_segment")
    op.execute("DROP TABLE result_evidence")
    op.execute("DROP TABLE result_condition")
    op.execute("DROP TABLE result_input")
    op.execute("DROP TABLE analytical_result")
    op.execute("DROP TABLE analytical_eligibility")
    op.execute("DROP TABLE analysis_protocol")
    op.execute("DROP TABLE review_event")
    op.execute("DROP TABLE data_quality_issue")
    op.execute("DROP TABLE experimental_condition")
    op.execute("DROP TABLE annotation_evidence")
    op.execute("DROP TABLE semantic_annotation")
    op.execute("DROP TABLE scientific_variable")
    op.execute("DROP TABLE observation")
    op.execute("DROP TABLE test_relationship")
    op.execute("DROP TABLE test_source_record")
    op.execute("DROP TABLE experimental_test")
    op.execute("DROP TABLE source_record")
    op.execute("DROP TABLE source_field")
    op.execute("DROP TABLE parse_run")
    op.execute("DROP TABLE evidence_reference")
    op.execute("DROP TABLE source_acquisition")
    op.execute("DROP TABLE source_document")
    op.execute("DROP TABLE investigation")
