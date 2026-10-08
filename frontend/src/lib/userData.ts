import { useEffect, useRef, useState } from 'react';
import type { User } from '@supabase/supabase-js';
import { supabase } from './supabase';
import { loadPortfolio, savePortfolio, type PortfolioHolding } from './portfolioStore';

const WATCHLIST_STORAGE_KEY = 'marketidex_watchlist';
const DEFAULT_WATCHLIST = ['BBCA', 'TLKM'];

const readWatchlist = (): string[] => {
  try {
    const parsed = JSON.parse(localStorage.getItem(WATCHLIST_STORAGE_KEY) || 'null');
    if (Array.isArray(parsed)) return parsed.filter((s): s is string => typeof s === 'string');
  } catch {
    // ignore corrupt storage
  }
  return DEFAULT_WATCHLIST;
};

const writeWatchlist = (symbols: string[]) => {
  try {
    localStorage.setItem(WATCHLIST_STORAGE_KEY, JSON.stringify(symbols));
  } catch {
    // ignore
  }
};

export type SyncStatus = 'local' | 'loading' | 'synced' | 'saving' | 'error';

/**
 * Portfolio and watchlist, kept on this device and — when signed in — in the
 * user's Supabase rows. On the first sign-in, whatever the user built locally
 * is uploaded so nothing is lost; afterwards the account copy wins.
 */
export function useUserData(user: User | null) {
  const [portfolio, setPortfolio] = useState<PortfolioHolding[]>(loadPortfolio);
  const [watchlist, setWatchlist] = useState<string[]>(readWatchlist);
  const [status, setStatus] = useState<SyncStatus>('local');
  // Skip the save that would echo back data we just loaded from the account.
  const hydratedFor = useRef<string | null>(null);
  const userId = user?.id ?? null;

  useEffect(() => savePortfolio(portfolio), [portfolio]);
  useEffect(() => writeWatchlist(watchlist), [watchlist]);

  // Load (or seed) the account copy when a user signs in.
  useEffect(() => {
    hydratedFor.current = null;
    if (!supabase || !userId) {
      setStatus('local');
      return;
    }
    let cancelled = false;
    setStatus('loading');
    (async () => {
      const [p, w] = await Promise.all([
        supabase.from('user_portfolios').select('holdings').eq('user_id', userId).maybeSingle(),
        supabase.from('user_watchlists').select('symbols').eq('user_id', userId).maybeSingle()
      ]);
      if (cancelled) return;
      if (p.error || w.error) {
        setStatus('error');
        return;
      }
      const seeds: PromiseLike<unknown>[] = [];
      if (p.data) setPortfolio(p.data.holdings as PortfolioHolding[]);
      else seeds.push(supabase.from('user_portfolios').insert({ user_id: userId, holdings: loadPortfolio() }));
      if (w.data) setWatchlist(w.data.symbols as string[]);
      else seeds.push(supabase.from('user_watchlists').insert({ user_id: userId, symbols: readWatchlist() }));
      await Promise.all(seeds);
      if (cancelled) return;
      hydratedFor.current = userId;
      setStatus('synced');
    })();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  // Push edits to the account, debounced so typing a weight is one write.
  const first = useRef(true);
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    const sb = supabase;
    if (!sb || !userId || hydratedFor.current !== userId) return;
    setStatus('saving');
    const t = setTimeout(async () => {
      const now = new Date().toISOString();
      const [p, w] = await Promise.all([
        sb.from('user_portfolios').upsert({ user_id: userId, holdings: portfolio, updated_at: now }),
        sb.from('user_watchlists').upsert({ user_id: userId, symbols: watchlist, updated_at: now })
      ]);
      setStatus(p.error || w.error ? 'error' : 'synced');
    }, 800);
    return () => clearTimeout(t);
  }, [portfolio, watchlist, userId]);

  return { portfolio, setPortfolio, watchlist, setWatchlist, status };
}
