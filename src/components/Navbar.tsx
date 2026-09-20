import React from 'react';
import { Search, Database, Cpu } from 'lucide-react';

interface NavbarProps {
  activeView?: string;
  onOpenPipeline?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  onOpenPipeline
}) => {
  return (
    <header className="h-16 glass-panel border-b border-slate-800/80 px-6 flex items-center space-x-6 sticky top-0 z-40">
      {/* Brand */}
      <div className="flex items-center space-x-3 shrink-0">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Cpu className="w-5 h-5 text-white" />
        </div>
        <div>
          <span className="font-bold text-lg bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent">
            Sahamphy
          </span>
          <span className="text-xs text-slate-400 block -mt-1 font-mono tracking-wider">
            Analisis Saham Lokal
          </span>
        </div>
      </div>

      <div className="h-6 w-px bg-slate-800 shrink-0 hidden md:block" />

      {/* Search Bar (Fills remaining space) */}
      <div className="flex-1 hidden md:flex items-center">
        <div className="relative w-full max-w-2xl">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Cari emiten, sinyal, atau kata kunci..."
            className="bg-slate-900/90 text-xs text-slate-200 pl-9 pr-4 py-2 rounded-lg border border-slate-800 focus:outline-none focus:border-cyan-500/50 w-full transition-all"
          />
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
