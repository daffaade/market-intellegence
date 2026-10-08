import { useCallback, useEffect, useRef, useState } from 'react';
import type { ResponseWrapper } from '../types/api';

export interface Remote<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: () => void;
}

/**
 * Loads one backend resource for a panel. Stale responses (from a previous
 * symbol) are dropped, and an error is kept separate from "no data" so the
 * panel can offer a retry instead of silently showing nothing.
 */
export function useRemote<T>(fetcher: () => Promise<ResponseWrapper<T>>, deps: unknown[]): Remote<T> {
  const [state, setState] = useState<{ data: T | null; error: string | null; loading: boolean }>({
    data: null,
    error: null,
    loading: true
  });
  const [nonce, setNonce] = useState(0);
  const seq = useRef(0);

  useEffect(() => {
    const id = ++seq.current;
    setState(s => ({ data: s.data, error: null, loading: true }));
    fetcher().then(res => {
      if (id !== seq.current) return;
      if (res.status === 'success' && res.data !== undefined) {
        setState({ data: res.data, error: null, loading: false });
      } else {
        setState({ data: null, error: res.message || 'Gagal memuat data', loading: false });
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);

  const reload = useCallback(() => setNonce(n => n + 1), []);
  return { ...state, reload };
}
