import React, { useState, useRef, useEffect } from 'react';
import { Search, Database, Cpu, X, TrendingUp, TrendingDown, ArrowRight } from 'lucide-react';
import { MOCK_COMPANIES, MOCK_INTELLIGENCE } from '../services/mockData';

interface NavbarProps {
  activeView?: string;
  onOpenPipeline?: () => void;
  onSelectSymbol?: (symbol: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  onOpenPipeline,
  onSelectSymbol
}) => {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const searchContainerRef = useRef<HTMLDivElement>(null);

  // Filter companies based on query
  const filteredCompanies = React.useMemo(() => {
    if (!query.trim()) return [];
    const q = query.toLowerCase().trim();
    return Object.values(MOCK_COMPANIES).filter(comp =>
      comp.symbol.toLowerCase().includes(q) ||
      comp.name.toLowerCase().includes(q) ||
      comp.sector.toLowerCase().includes(q) ||
      comp.sub_sector.toLowerCase().includes(q)
    ).slice(0, 7); // Max 7 results for clean dropdown
  }, [query]);

  // Handle outside click to close dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (symbol: string) => {
    if (onSelectSymbol) {
      onSelectSymbol(symbol);
    }
    setQuery('');
    setIsOpen(false);
    setActiveIndex(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || filteredCompanies.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(prev => (prev < filteredCompanies.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => (prev > 0 ? prev - 1 : filteredCompanies.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && activeIndex < filteredCompanies.length) {
        handleSelect(filteredCompanies[activeIndex].symbol);
      } else if (filteredCompanies.length > 0) {
        handleSelect(filteredCompanies[0].symbol);
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  return (
    <header className="h-16 glass-panel border-b border-slate-800/80 px-6 flex items-center space-x-6 sticky top-0 z-40">
      {/* Brand */}
      <div className="flex items-center space-x-3 shrink-0">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Cpu className="w-5 h-5 text-white" />
        </div>
        <div>
          <span className="font-bold text-lg bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent">
            Marketidex
          </span>
          <span className="text-xs text-slate-400 block -mt-1 font-mono tracking-wider">
            Analisis Saham Lokal
          </span>
        </div>
      </div>

      <div className="h-6 w-px bg-slate-800 shrink-0 hidden md:block" />

      {/* Search Bar (Fills remaining space with Autocomplete Dropdown) */}
      <div className="flex-1 hidden md:flex items-center">
        <div ref={searchContainerRef} className="relative w-full max-w-2xl">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setIsOpen(true);
              setActiveIndex(-1);
            }}
            onFocus={() => {
              if (query.trim()) setIsOpen(true);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Cari emiten (e.g. BBCA, TLKM), nama perusahaan, atau sektor..."
            className="bg-slate-900/90 text-xs text-slate-200 pl-9 pr-9 py-2 rounded-lg border border-slate-800 focus:outline-none focus:border-cyan-500/50 w-full transition-all placeholder:text-slate-500"
          />
          {query && (
            <button
              onClick={() => {
                setQuery('');
                setIsOpen(false);
              }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 p-0.5 rounded transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}

          {/* Autocomplete Dropdown */}
          {isOpen && query.trim().length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-slate-900/95 backdrop-blur-xl border border-slate-700/70 rounded-xl shadow-2xl z-50 overflow-hidden divide-y divide-slate-800/60 animate-in fade-in slide-in-from-top-2 duration-150">
              <div className="px-3 py-2 text-[10px] font-mono text-slate-400 uppercase tracking-wider bg-slate-950/40 flex items-center justify-between">
                <span>Hasil Pencarian Saham ({filteredCompanies.length})</span>
                <span className="text-[9px] text-slate-500">Tekan Enter untuk memilih</span>
              </div>

              {filteredCompanies.length > 0 ? (
                <div className="max-h-80 overflow-y-auto">
                  {filteredCompanies.map((comp, idx) => {
                    const intel = MOCK_INTELLIGENCE[comp.symbol];
                    const isSelected = activeIndex === idx;

                    return (
                      <div
                        key={comp.symbol}
                        onClick={() => handleSelect(comp.symbol)}
                        onMouseEnter={() => setActiveIndex(idx)}
                        className={`px-4 py-2.5 flex items-center justify-between cursor-pointer transition-colors ${
                          isSelected ? 'bg-cyan-950/40 text-white' : 'hover:bg-slate-800/50 text-slate-200'
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          <div className="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center font-mono font-bold text-xs text-cyan-400 border border-slate-700/50">
                            {comp.symbol}
                          </div>
                          <div>
                            <div className="flex items-center space-x-2">
                              <span className="text-xs font-semibold text-white">{comp.name}</span>
                              {intel && (
                                <span className={`text-[9px] px-1.5 py-0.2 rounded font-bold flex items-center space-x-1 ${
                                  intel.direction === 'BULLISH'
                                    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                                    : intel.direction === 'BEARISH'
                                    ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                                    : 'bg-slate-800 text-slate-400'
                                }`}>
                                  {intel.direction === 'BULLISH' && <TrendingUp className="w-2.5 h-2.5 mr-0.5 inline" />}
                                  {intel.direction === 'BEARISH' && <TrendingDown className="w-2.5 h-2.5 mr-0.5 inline" />}
                                  {intel.direction}
                                </span>
                              )}
                            </div>
                            <span className="text-[10px] text-slate-400 block mt-0.5">
                              {comp.sector} • {comp.sub_sector}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center space-x-3 text-right">
                          {intel && (
                            <div>
                              <span className="text-[9px] text-slate-400 block font-mono">OPPORTUNITY</span>
                              <span className="text-xs font-bold font-mono text-cyan-400">
                                {intel.opportunity_score}
                              </span>
                            </div>
                          )}
                          <ArrowRight className={`w-3.5 h-3.5 transition-transform ${
                            isSelected ? 'text-cyan-400 translate-x-1' : 'text-slate-600'
                          }`} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="p-6 text-center text-xs text-slate-400">
                  Tidak ada emiten yang cocok dengan kata kunci &quot;<span className="text-slate-200">{query}</span>&quot;
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Global Indicators & Status */}
      <div className="flex items-center space-x-4 shrink-0 ml-auto">
        <button
          onClick={onOpenPipeline}
          className="flex items-center space-x-2 bg-slate-900/60 hover:bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-800 text-xs transition-colors cursor-pointer group"
        >
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-slate-300 font-medium group-hover:text-cyan-400 transition-colors">Pipeline Active</span>
          <span className="text-slate-500 font-mono text-[10px] pl-1">| INSPECT</span>
        </button>

        <div className="flex items-center space-x-2 text-xs text-slate-400 border-l border-slate-800 pl-4">
          <Database className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-mono">Sectors API</span>
        </div>
      </div>
    </header>
  );
};

