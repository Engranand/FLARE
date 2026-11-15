import type { ExecutionResponse, HealthResponse } from '../types/api';

// The base includes the version prefix; change it alongside API_V1_PREFIX.
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/+$/, '');

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`, {
    signal,
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) throw new Error(`API returned HTTP ${response.status}`);
  const data: unknown = await response.json();
  if (
    typeof data !== 'object' ||
    data === null ||
    !('status' in data) ||
    data.status !== 'ok' ||
    !('application_name' in data) ||
    typeof data.application_name !== 'string' ||
    !('version' in data) ||
    typeof data.version !== 'string'
  ) {
    throw new Error('API returned an unexpected health response');
  }
  return { status: data.status, application_name: data.application_name, version: data.version };
}

export async function executeScientificQuery(
  question: string,
  investigation: string = 'PSI-25',
  signal?: AbortSignal,
): Promise<ExecutionResponse> {
  const response = await fetch(`${API_BASE_URL}/intelligence/execute`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({ question, investigation }),
    signal,
  });
  if (!response.ok) {
    let errDetail = `HTTP ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson && typeof errJson.detail === 'string') {
        errDetail = errJson.detail;
      }
    } catch {
      // ignore
    }
    throw new Error(`Query failed: ${errDetail}`);
  }
  return response.json() as Promise<ExecutionResponse>;
}
