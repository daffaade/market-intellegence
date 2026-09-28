import React from 'react';
import { Star } from 'lucide-react';
import { cx } from '../../lib/ui';

interface WatchlistButtonProps {
  symbol: string;
  isInWatchlist: boolean;
  onToggle: (symbol: string) => void;
  withLabel?: boolean;
}

export const WatchlistButton: React.FC<WatchlistButtonProps> = ({ symbol, isInWatchlist, onToggle, withLabel }) => (
  <button
    onClick={e => {
      e.stopPropagation();
      onToggle(symbol);
    }}
    aria-pressed={isInWatchlist}
    title={isInWatchlist ? `Hapus ${symbol} dari watchlist` : `Tambah ${symbol} ke watchlist`}
    className={cx(
      'inline-flex items-center gap-1.5 rounded-md transition-colors',
      withLabel ? 'h-8 px-3 text-[13px] border border-line-strong bg-surface hover:bg-surface-2' : 'p-1 hover:bg-surface-2',
      isInWatchlist ? 'text-warn' : 'text-ink-3 hover:text-ink'
    )}
  >
    <Star className={cx('w-3.5 h-3.5', isInWatchlist && 'fill-current')} />
    {withLabel && <span className="text-ink">{isInWatchlist ? 'Di watchlist' : 'Watchlist'}</span>}
  </button>
);
