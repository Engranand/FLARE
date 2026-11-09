import { afterEach, describe, expect, it, vi } from 'vitest';
import { API_BASE_URL, getHealth } from './api';

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
