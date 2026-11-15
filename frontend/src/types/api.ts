export interface HealthResponse {
  status: 'ok';
  application_name: string;
  version: string;
}

export type ConnectionStatus = 'Checking' | 'Connected' | 'Disconnected';

export type EpistemicAttribution =
  | 'experimental_observation'
  | 'numerical_simulation'
  | 'derived_information'
  | 'reference_information'
  | 'unresolved_attribution';

export interface DocumentPassage {
  chunk_id: string;
  source_document_id: string;
  source_document_filename: string;
  source_document_sha256: string;
  document_title: string;
  page_start: number | null;
  page_end: number | null;
  page_reference: string;
  section_title: string | null;
  passage_text: string;
  token_count?: number;
  relevance_score: number;
  evidence_type: string;
  epistemic_attribution: EpistemicAttribution;
  is_validated_measurement: boolean;
  flare_uri: string;
}

export interface EvidenceReference {
  investigation_code: string;
  source_document_sha256: string;
  source_document_filename: string;
  page_reference?: string;
  flare_uri?: string;
  epistemic_attribution?: string;
}

export interface ToolResult {
  tool_id: string;
  execution_status:
    | 'SUCCESS'
    | 'NO_RESULTS'
    | 'INVALID_INPUT'
    | 'INTEGRITY_FAILURE'
    | 'PROHIBITED'
    | 'TIMEOUT'
    | 'NOT_IMPLEMENTED'
    | 'INTERNAL_ERROR';
  request_id: string;
  result_data?: DocumentPassage[] | Record<string, unknown> | null;
  evidence_references: EvidenceReference[];
  source_hash?: string | null;
  quality_flags?: string[];
  limitations: string[];
}

export type EvidenceType = 'EM' | 'NS' | 'DQ' | 'RT';

export type EpistemicStatus = 'SUPPORTED' | 'DISPUTED' | 'UNRESOLVED' | 'HYPOTHESIS';

export type ClaimType =
  | 'NUMERICAL_MEASUREMENT'
  | 'STATISTICAL_METRIC'
  | 'MATERIAL_CLASSIFICATION'
  | 'EXPERIMENTAL_REGIME'
  | 'METHODOLOGICAL_LIMITATION';

export type ClaimValidationStatus = 'PENDING' | 'VALIDATED' | 'REJECTED' | 'QUALIFIED';

export interface StableEvidenceReference {
  uri: string;
  evidence_type: EvidenceType;
  epistemic_status: EpistemicStatus;
  source_sha256?: string | null;
  location_label: string;
  summary_snippet: string;
}

export interface ScientificClaim {
  claim_id: string;
  claim_type: ClaimType;
  subject_entity: string;
  claimed_statement: string;
  claimed_numeric_value?: number | string | null;
  claimed_unit?: string | null;
  metric_identifier?: string | null;
  claimed_ci_lower?: number | string | null;
  claimed_ci_upper?: number | string | null;
  claimed_sample_size?: number | null;
  evidence_references: StableEvidenceReference[];
  validation_status: ClaimValidationStatus;
  validation_error?: string | null;
  epistemic_verdict: EpistemicStatus;
}

export interface SynthesizedResponse {
  synthesis_id: string;
  answer: string;
  key_findings: string[];
  scientific_claims: ScientificClaim[];
  evidence_references: StableEvidenceReference[];
  uncertainty_and_limitations: string[];
  tools_used: string[];
  epistemic_status: EpistemicStatus;
  provider_status: string; // 'available' | 'unavailable' | 'degraded' | 'mock' | 'abstained'
  provider_model?: string | null;
  rejected_claims_count: number;
  execution_duration_ms: number;
}

export interface ExecutionResponse {
  request_id: string;
  plan: {
    original_question: string;
    intent: string;
    scope_status: string;
    state: string;
    required_tools: string[];
    requested_metrics: string[];
  };
  tool_results: ToolResult[];
  overall_status: string;
  duration_ms: number;
  synthesis?: SynthesizedResponse | null;
}
