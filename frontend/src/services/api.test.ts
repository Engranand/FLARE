import { afterEach, describe, expect, it, vi } from 'vitest';
import { API_BASE_URL, executeScientificQuery, getHealth } from './api';

afterEach(() => vi.unstubAllGlobals());

describe('health client', () => {
  it('calls the configured versioned endpoint and forwards cancellation', async () => {
    const payload = { status: 'ok', application_name: 'FLARE', version: '0.1.0' };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload)));
    vi.stubGlobal('fetch', fetchMock);
    const controller = new AbortController();
    await expect(getHealth(controller.signal)).resolves.toEqual(payload);
    expect(fetchMock).toHaveBeenCalledWith(`${API_BASE_URL}/health`, {
      signal: controller.signal, headers: { Accept: 'application/json' },
    });
  });
  it('rejects HTTP errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('', { status: 503 })));
    await expect(getHealth()).rejects.toThrow('HTTP 503');
  });
  it('rejects invalid response shapes', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"status":"ok"}')));
    await expect(getHealth()).rejects.toThrow('unexpected health response');
  });
  it('propagates network failures', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    await expect(getHealth()).rejects.toThrow('Failed to fetch');
  });
});

describe('scientific intelligence client', () => {
  it('posts question to intelligence execute endpoint', async () => {
    const payload = {
      request_id: '1234',
      plan: {
        original_question: 'Why does flame shape change in microgravity?',
        intent: 'SCIENTIFIC_EXPLANATION',
        scope_status: 'ALLOWED',
        state: 'READY_FOR_EXECUTION',
        required_tools: ['flare_retrieve_documents'],
        requested_metrics: [],
      },
      tool_results: [
        {
          tool_id: 'flare_retrieve_documents',
          execution_status: 'SUCCESS',
          request_id: '1234',
          result_data: [],
          evidence_references: [],
          limitations: [],
        },
      ],
      overall_status: 'SUCCESS',
      duration_ms: 12.5,
    };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload)));
    vi.stubGlobal('fetch', fetchMock);

    const result = await executeScientificQuery('Why does flame shape change in microgravity?');
    expect(result).toEqual(payload);
    expect(fetchMock).toHaveBeenCalledWith(
      `${API_BASE_URL}/intelligence/execute`,
      expect.objectContaining({
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          question: 'Why does flame shape change in microgravity?',
          investigation: 'PSI-25',
        }),
      })
    );
  });

  it('handles execution HTTP errors with detail message', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: 'Prohibited scientific inquiry' }), { status: 422 })
      )
    );
    await expect(
      executeScientificQuery('Calculate Biot number Bi << 0.1')
    ).rejects.toThrow('Prohibited scientific inquiry');
  });
});
