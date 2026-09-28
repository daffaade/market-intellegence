import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Search, Star, CornerDownLeft } from 'lucide-react';
import type { Company } from '../../types/api';
import { MOCK_COMPANIES, MOCK_INTELLIGENCE } from '../../services/mockData';
import { DirectionTag, Kbd } from '../ui/primitives';
import { cx } from '../../lib/ui';

interface EmitenSwitcherModalProps {
  isOpen: boolean;
  onClose: () => void;
  companies: Company[];
  currentSymbol: string;
  watchlist: string[];
  onSelectSymbol: (symbol: string) => void;
}

/**
 * Mounted only while open, so search state starts fresh each time.
 *
 * Global command palette for finding and switching emiten. Opened from the top
 * bar, "Ganti emiten" buttons, or the "/" and Ctrl+K shortcuts.
 */
export const EmitenSwitcherModal: React.FC<EmitenSwitcherModalProps> = ({
  isOpen,
  onClose,
  companies,
  currentSymbol,
  watchlist,
  onSelectSymbol
}) => {
  const [query, setQuery] = useState('');
  const [highlight, setHighlight] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const source = companies.length > 0 ? companies : Object.values(MOCK_COMPANIES);

  const results = useMemo(() => {
    const q = query.toLowerCase().trim();
    if (!q) {
      // Empty query: watchlist first, then the rest alphabetically.
      const watched = watchlist.map(s => source.find(c => c.symbol === s)).filter((c): c is Company => !!c);
      const rest = source.filter(c => !watchlist.includes(c.symbol)).sort((a, b) => a.symbol.localeCompare(b.symbol));
      return [...watched, ...rest];
    }
    return source
      .filter(
        c =>
          c.symbol.toLowerCase().includes(q) ||
          c.name.toLowerCase().includes(q) ||
          c.sector.toLowerCase().includes(q) ||
          c.sub_sector.toLowerCase().includes(q)
      )
      .sort((a, b) => {
        // Symbol prefix matches rank first.
        const ap = a.symbol.toLowerCase().startsWith(q) ? 0 : 1;
        const bp = b.symbol.toLowerCase().startsWith(q) ? 0 : 1;
        return ap - bp || a.symbol.localeCompare(b.symbol);
      });
  }, [query, source, watchlist]);

  useEffect(() => {
    listRef.current?.querySelector(`[data-index="${highlight}"]`)?.scrollIntoView({ block: 'nearest' });
  }, [highlight]);

  if (!isOpen) return null;

  const select = (symbol: string) => {
    onSelectSymbol(symbol);
    onClose();
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlight(h => Math.min(h + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlight(h => Math.max(h - 1, 0));
    } else if (e.key === 'Enter' && results[highlight]) {
      e.preventDefault();
      select(results[highlight].symbol);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center px-4 pt-[12vh] bg-black/40"
      onMouseDown={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Cari emiten"
    >
      <div
        className="w-full max-w-xl bg-surface border border-line-strong rounded-lg shadow-2xl overflow-hidden flex flex-col max-h-[70vh]"
        onMouseDown={e => e.stopPropagation()}
        onKeyDown={onKeyDown}
      >
        <div className="flex items-center gap-2.5 px-4 h-12 border-b border-line">
          <Search className="w-4 h-4 text-ink-3 shrink-0" />
          <input
            ref={inputRef}
            autoFocus
            value={query}
            onChange={e => {
              setQuery(e.target.value);
              setHighlight(0);
            }}
            placeholder="Kode, nama perusahaan, atau sektor"
            className="flex-1 bg-transparent text-[14px] text-ink placeholder:text-ink-3 outline-none"
            role="combobox"
            aria-expanded="true"
            aria-controls="emiten-results"
          />
          <Kbd>Esc</Kbd>
        </div>

        <ul id="emiten-results" ref={listRef} role="listbox" className="flex-1 overflow-y-auto py-1.5">
          {!query && watchlist.length > 0 && (
            <li className="px-4 pt-1 pb-1 text-[11px] text-ink-3">Watchlist & semua emiten</li>
          )}
          {results.map((c, idx) => {
            const intel = MOCK_INTELLIGENCE[c.symbol];
            const isCurrent = c.symbol === currentSymbol;
            return (
              <li
                key={c.symbol}
                data-index={idx}
                role="option"
                aria-selected={idx === highlight}
                onMouseMove={() => setHighlight(idx)}
                onClick={() => select(c.symbol)}
                className={cx(
                  'mx-1.5 px-2.5 h-11 rounded-md flex items-center gap-3 cursor-pointer',
                  idx === highlight && 'bg-surface-2'
                )}
              >
                <span className="num text-[13px] font-medium text-ink w-12 shrink-0">{c.symbol}</span>
                <span className="min-w-0 flex-1">
                  <span className="block text-[13px] text-ink truncate">
                    {c.name}
                    {watchlist.includes(c.symbol) && (
                      <Star className="inline w-3 h-3 ml-1.5 -mt-0.5 text-warn fill-current" aria-label="Di watchlist" />
                    )}
                  </span>
                  <span className="block text-xs text-ink-3 truncate">{c.sector} · {c.sub_sector}</span>
                </span>
                {isCurrent && <span className="text-[11px] text-ink-3">Sedang dibuka</span>}
                {intel && <DirectionTag direction={intel.direction} />}
                {intel && <span className="num text-[13px] text-ink-2 w-8 text-right">{intel.opportunity_score}</span>}
              </li>
            );
          })}
          {results.length === 0 && (
            <li className="px-4 py-10 text-center text-[13px] text-ink-3">
              Tidak ada emiten yang cocok dengan “{query}”.
            </li>
          )}
        </ul>

        <div className="px-4 h-9 border-t border-line flex items-center gap-4 text-[11px] text-ink-3">
          <span className="flex items-center gap-1"><Kbd>↑</Kbd><Kbd>↓</Kbd> pilih</span>
          <span className="flex items-center gap-1"><Kbd><CornerDownLeft className="w-2.5 h-2.5" /></Kbd> buka</span>
          <span className="ml-auto">Angka = skor peluang</span>
        </div>
      </div>
    </div>
  );
};
