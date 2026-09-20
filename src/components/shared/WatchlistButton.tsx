import React from 'react';
import { Star } from 'lucide-react';

interface WatchlistButtonProps {
  symbol: string;
  isInWatchlist: boolean;
  onToggle: (symbol: string) => void;
}

export const WatchlistButton: React.FC<WatchlistButtonProps> = ({
  symbol,
  isInWatchlist,
  onToggle
}) => {
  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        onToggle(symbol);
      }}
      title={isInWatchlist ? `Hapus ${symbol} dari Watchlist` : `Tambah ${symbol} ke Watchlist`}
      className={`p-1.5 rounded-lg transition-all ${
        isInWatchlist
          ? 'text-amber-400 bg-amber-500/10 hover:bg-amber-500/20 shadow-sm shadow-amber-500/10'
          : 'text-slate-500 hover:text-amber-400 hover:bg-slate-800'
      }`}
    >
      <Star className={`w-4 h-4 ${isInWatchlist ? 'fill-amber-400' : ''}`} />
    </button>
  );
};
