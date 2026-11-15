import { API_BASE_URL } from './api';
import type { ToolResult, ExecutionResponse } from '../types/api';
export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
export interface Metric { result_id: string; metric_code: string; canonical_name: string; protocol_code: string; numeric_value: string | null; text_value: string | null; unit: string | null; sample_size: number | null; parameters: Record<string, Json>; uncertainty: Record<string, Json>; seal: { sealed_at: string; member_digest: string } }
export interface Investigation { investigation_code: string; name: string; description: string | null; source_repository_url: string; records: number; documents: number }
export interface SourceDocument { id: string; investigation_code: string; original_filename: string; title: string | null; sha256: string; source_type: string; attribution: string | null; document_type: string | null; passages: number; created_at: string }
export interface Summary { counts: Record<string, number | null>; investigations: Investigation[]; documents: SourceDocument[]; metrics: Metric[]; limitations: string[]; metric_status: string }
export interface Bin { label: string; low: number; high: number; count: number; rows: number[] }
export interface Distribution { key: string; title: string; unit: string; sample_size: number; excluded: number; median: string | null; q1: string | null; q3: string | null; bins: Bin[]; notes: string[]; source: string; sha256: string }
export interface Science { charts: Distribution[]; oxygen_quality: Record<string, number>; airflow_quality: Record<string, number>; morphology: Record<string, number>; unique_specimens: number; repeated_specimens: number; specimens: { specimen: string; tests: number }[]; pairs: { x: number; y: number; row: number; test: string }[]; conditions: { test: string; row: number; regime: string; fuel: string; specimen: string; burn: string; oxygen: string; airflow: string }[]; source: string; sha256: string; notes: string[] }
export interface Observation { id: string; investigation_code: string; test_identifier: string; source_record_number: number; variable: string; value: string | null; unit: string | null; quality: string; parser_flags: Json; dataset: string; sha256: string; source_locator: Json; verification_status: string; attribution: string }
export interface Page { items: Observation[]; total: number; page: number; page_size: number }
export interface PassageDetail { id: string; chunk_text: string; page_start: number | null; page_end: number | null; section_title: string | null; chunk_index: number; source_document_id: string; original_filename: string; sha256: string; metadata: Record<string, Json>; previous: string | null; next: string | null }
export interface Condition { investigation: string; oxygen_min: number; oxygen_max: number; airflow_min: number | null; airflow_max: number | null; fuel: string }
export interface Comparison { a: Distribution; b: Distribution; overlap: number }
export async function request<T>(path: string, signal?: AbortSignal, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { signal, method: body === undefined ? 'GET' : 'POST', headers: { Accept: 'application/json', ...(body === undefined ? {} : { 'Content-Type': 'application/json' }) }, ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
  if (!response.ok) { const data: unknown = await response.json().catch(() => null); throw new Error(data && typeof data === 'object' && 'detail' in data && typeof data.detail === 'string' ? data.detail : `Request failed (${response.status}). Check filters and connection.`); }
  return response.json() as Promise<T>;
}
export async function payload<T>(path: string, signal?: AbortSignal, body?: unknown) { return (await request<{ data: T }>(`/workstation${path}`, signal, body)).data; }
export const queryScience = (question: string, signal?: AbortSignal) => request<ExecutionResponse>('/intelligence/execute', signal, { question, investigation: 'PSI-25', synthesize: true });
export const findEvidence = (q: string, signal?: AbortSignal) => request<ToolResult>(`/workstation/evidence?q=${encodeURIComponent(q)}`, signal);
