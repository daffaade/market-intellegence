/**
 * Device copy of the portfolio. When signed in, lib/userData.ts also keeps it
 * in the user's Supabase row and treats that as the source of truth.
 */
export interface PortfolioHolding {
  symbol: string;
  /** Allocation in percent of the portfolio. */
  weight: number;
}

const STORAGE_KEY = 'marketidex_portfolio';

export const EXAMPLE_PORTFOLIO: PortfolioHolding[] = [
  { symbol: 'BBCA', weight: 40 },
  { symbol: 'TLKM', weight: 25 },
  { symbol: 'ASII', weight: 20 },
  { symbol: 'GOTO', weight: 15 }
];

export const loadPortfolio = (): PortfolioHolding[] => {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
    if (Array.isArray(parsed)) {
      return parsed
        .filter(h => h && typeof h.symbol === 'string' && typeof h.weight === 'number')
        .map(h => ({ symbol: h.symbol.toUpperCase(), weight: h.weight }));
    }
  } catch {
    // unavailable or corrupt storage: start empty
  }
  return [];
};

export const savePortfolio = (holdings: PortfolioHolding[]): void => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(holdings));
  } catch {
    // storage unavailable (private mode); the portfolio just won't persist
  }
};
