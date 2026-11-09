import { useEffect, useState } from 'react';
import { getHealth } from '../services/api';
import type { ConnectionStatus } from '../types/api';

export function useHealth() {
  const [status, setStatus] = useState<ConnectionStatus>('Checking');
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    const timeout = window.setTimeout(() => controller.abort(), 8000);
    setStatus('Checking');
    setError(null);
    getHealth(controller.signal).then(() => {
      if (active) setStatus('Connected');
    }).catch((reason: unknown) => {
      if (active) {
        setStatus('Disconnected');
        setError(controller.signal.aborted ? 'Connection timed out. Check that the API is running.' :
          reason instanceof Error ? reason.message : 'Unable to reach the API');
      }
    }).finally(() => window.clearTimeout(timeout));
    return () => { active = false; controller.abort(); window.clearTimeout(timeout); };
  }, [attempt]);
  return { status, error, retry: () => setAttempt((value) => value + 1) };
}
