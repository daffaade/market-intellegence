import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Search, X, TrendingUp, TrendingDown, ArrowLeftRight, Check, Sparkles } from 'lucide-react';
import { MOCK_COMPANIES, MOCK_INTELLIGENCE } from '../../services/mockData';

interface EmitenSwitcherModalProps {
  currentSymbol: string;
  onSelectSymbol: (symbol: string) => void;
  buttonText?: string;
  className?: string;
}

export const EmitenSwitcherModal: React.FC<EmitenSwitcherModalProps> = ({
  currentSymbol,
  onSelectSymbol,
  buttonText = "Ganti",
  className = ""
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSector, setSelectedSector] = useState<string>('ALL');
  const [highlightIndex, setHighlightIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus input when opened
  useEffect(() => {
    if (isOpen) {
      setSearchQuery('');
      setSelectedSector('ALL');
      setHighlightIndex(0);
      setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
    }
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  // Unique Sectors
  const sectors = useMemo(() => {
    const s = new Set<string>();
    Object.values(MOCK_COMPANIES).forEach(c => s.add(c.sector));
    return ['ALL', ...Array.from(s)];
  }, []);

  // Filtered Companies
  const filteredList = useMemo(() => {
    let list = Object.values(MOCK_COMPANIES);

    if (selectedSector !== 'ALL') {
      list = list.filter(c => c.sector === selectedSector);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(c =>
        c.symbol.toLowerCase().includes(q) ||
        c.name.toLowerCase().includes(q) ||
        c.sector.toLowerCase().includes(q) ||
        c.sub_sector.toLowerCase().includes(q)
      );
    }

    return list;
  }, [searchQuery, selectedSector]);

  const handleSelect = (symbol: string) => {
    onSelectSymbol(symbol);
    setIsOpen(false);
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (filteredList.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightIndex(prev => (prev < filteredList.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightIndex(prev => (prev > 0 ? prev - 1 : filteredList.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredList[highlightIndex]) {
        handleSelect(filteredList[highlightIndex].symbol);
      }
    }
  };

  return (
    <>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(true)}
        className={`px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 border border-slate-700/80 hover:border-cyan-500/40 text-xs font-medium flex items-center space-x-1.5 transition-all cursor-pointer shadow-sm group ${className}`}
        title="Ganti emiten yang sedang dianalisis"
      >
        <ArrowLeftRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-cyan-400 transition-colors" />
        <span>{buttonText}</span>
      </button>

      {/* Modal Dialog Backdrop */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
          <div
            className="w-full max-w-2xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh] animate-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">Ganti Emiten Analisis</h3>
                  <p className="text-[11px] text-slate-400">Pilih emiten yang ingin Anda telusuri sinyal dan fundamentalnya</p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Search Input Box */}
            <div className="p-4 border-b border-slate-800 bg-slate-900/60">
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  ref={inputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setHighlightIndex(0);
                  }}
                  onKeyDown={handleInputKeyDown}
                  placeholder="Ketik kode saham (e.g. TLKM, BBRI), nama perusahaan, atau sektor..."
                  className="w-full bg-slate-950 text-xs text-slate-100 pl-10 pr-10 py-3 rounded-xl border border-slate-700/80 focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/20 placeholder:text-slate-500 shadow-inner"
                />
                {searchQuery && (
                  <button
                    onClick={() => {
                      setSearchQuery('');
                      inputRef.current?.focus();
                    }}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 p-1 rounded transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              {/* Quick Sector Filter Pills */}
              <div className="flex items-center space-x-1.5 overflow-x-auto pt-3 pb-1 scrollbar-none">
                {sectors.map((sec) => (
                  <button
                    key={sec}
                    onClick={() => {
                      setSelectedSector(sec);
                      setHighlightIndex(0);
                    }}
                    className={`px-2.5 py-1 rounded-lg text-[10px] font-medium whitespace-nowrap transition-all cursor-pointer ${
                      selectedSector === sec
                        ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
                        : 'bg-slate-800/80 text-slate-400 hover:text-slate-200 border border-slate-800'
                    }`}
                  >
                    {sec === 'ALL' ? 'Semua Sektor' : sec}
                  </button>
                ))}
              </div>
            </div>

            {/* List of Emitens */}
            <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60 max-h-96 p-2">
              {filteredList.length > 0 ? (
                filteredList.map((comp, idx) => {
                  const intel = MOCK_INTELLIGENCE[comp.symbol];
                  const isCurrent = comp.symbol === currentSymbol;
                  const isHighlighted = idx === highlightIndex;

                  return (
                    <div
                      key={comp.symbol}
                      onClick={() => handleSelect(comp.symbol)}
                      onMouseEnter={() => setHighlightIndex(idx)}
                      className={`p-3 rounded-xl flex items-center justify-between cursor-pointer transition-all ${
                        isCurrent
                          ? 'bg-cyan-500/10 border border-cyan-500/30'
                          : isHighlighted
                          ? 'bg-slate-800/80 text-white'
                          : 'hover:bg-slate-800/40 text-slate-300'
                      }`}
                    >
                      <div className="flex items-center space-x-3 min-w-0">
                        <div className="w-10 h-10 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center font-mono font-bold text-sm text-cyan-400 shrink-0">
                          {comp.symbol}
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center space-x-2">
                            <span className="text-xs font-bold text-white truncate">{comp.name}</span>
                            {isCurrent && (
                              <span className="text-[9px] px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-300 font-mono font-bold flex items-center space-x-0.5">
                                <Check className="w-2.5 h-2.5 inline mr-0.5" />
                                Aktif
                              </span>
                            )}
                            {intel && (
                              <span className={`text-[9px] px-1.5 py-0.2 rounded font-bold flex items-center space-x-1 ${
                                intel.direction === 'BULLISH'
                                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                                  : intel.direction === 'BEARISH'
                                  ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                                  : 'bg-slate-800 text-slate-400 border border-slate-700'
                              }`}>
                                {intel.direction === 'BULLISH' && <TrendingUp className="w-2.5 h-2.5 mr-0.5 inline" />}
                                {intel.direction === 'BEARISH' && <TrendingDown className="w-2.5 h-2.5 mr-0.5 inline" />}
                                {intel.direction}
                              </span>
                            )}
                          </div>
                          <span className="text-[10px] text-slate-400 block truncate mt-0.5">
                            {comp.sector} • {comp.sub_sector}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-4 text-right shrink-0 ml-3">
                        {intel && (
                          <div>
                            <span className="text-[9px] text-slate-400 block font-mono">OPPORTUNITY</span>
                            <span className="text-xs font-bold font-mono text-cyan-400">
                              {intel.opportunity_score}
                            </span>
                          </div>
                        )}
                        <span className="text-xs text-slate-500 group-hover:text-cyan-400 font-mono">
                          Pilih &rarr;
                        </span>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="p-8 text-center text-xs text-slate-400">
                  Tidak ada emiten yang cocok dengan &quot;<span className="text-slate-200">{searchQuery}</span>&quot;
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-3 bg-slate-950/40 border-t border-slate-800 text-[10px] text-slate-500 flex items-center justify-between font-mono">
              <span>Navigasi: &uarr;&darr; panah, Enter untuk memilih</span>
              <span>Tekan Esc untuk menutup</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
