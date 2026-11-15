import { useCallback, useEffect, useState } from 'react';
export function useResource<T>(loader: (signal: AbortSignal) => Promise<T>, key: string) {
  const [data, setData] = useState<T>(); const [error, setError] = useState(''); const [loading, setLoading] = useState(true); const [version, setVersion] = useState(0);
  const retry = useCallback(() => setVersion(v => v + 1), []);
  useEffect(() => { const controller = new AbortController(); setLoading(true); setError(''); setData(undefined);
    loader(controller.signal).then(value => { if (!controller.signal.aborted) setData(value); }).catch((e: unknown) => { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Unable to load data'); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
    // The explicit key is the request identity, independent of render closure identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, version]);
  return { data, error, loading, retry };
}
