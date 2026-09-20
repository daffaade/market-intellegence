import React from 'react';
import { FileSearch, Zap, BookOpen, Layers, Link2 } from 'lucide-react';
import type { StandardizedSignalOutput } from '../../types/api';

interface EvidencePanelProps {
  signal: StandardizedSignalOutput;
  symbol: string;
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ signal, symbol }) => {
  return (
    <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileSearch className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
            Evidence Panel — {symbol}
          </h3>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full bg-cyan-500/15 text-cyan-300 font-mono font-semibold border border-cyan-500/30">
          Standardized Output
        </span>
      </div>

      {/* 1. Finding */}
      <div className="space-y-2">
        <div className="flex items-center space-x-2 text-emerald-400">
          <Zap className="w-4 h-4" />
          <span className="text-xs font-bold uppercase tracking-wider font-mono">Finding</span>
        </div>
        <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-800">
          <p className="text-sm text-slate-200 leading-relaxed">{signal.finding}</p>
        </div>
      </div>

      {/* 2. Score */}
      <div className="space-y-2">
        <span className="text-xs font-bold uppercase tracking-wider font-mono text-sky-400">Score</span>
        <div className="grid grid-cols-3 gap-3">
          <div className="glass-card p-3 rounded-xl text-center">
            <span className="text-[10px] text-slate-400 font-mono block">Opportunity</span>
            <span className="text-xl font-black text-cyan-400 font-mono">{signal.score.opportunity}</span>
          </div>
          <div className="glass-card p-3 rounded-xl text-center">
            <span className="text-[10px] text-slate-400 font-mono block">Risk</span>
            <span className="text-xl font-black text-rose-400 font-mono">{signal.score.risk}</span>
          </div>
          <div className="glass-card p-3 rounded-xl text-center">
            <span className="text-[10px] text-slate-400 font-mono block">Composite</span>
            <span className="text-xl font-black text-amber-400 font-mono">{signal.score.composite}</span>
          </div>
        </div>
      </div>

      {/* 3. Explanation */}
      <div className="space-y-2">
        <div className="flex items-center space-x-2 text-indigo-400">
          <BookOpen className="w-4 h-4" />
          <span className="text-xs font-bold uppercase tracking-wider font-mono">Explanation</span>
        </div>
        <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-800">
          <p className="text-xs text-slate-300 leading-relaxed">{signal.explanation}</p>
        </div>
      </div>

      {/* 4. Evidence */}
      <div className="space-y-2">
        <div className="flex items-center space-x-2 text-cyan-400">
          <Layers className="w-4 h-4" />
          <span className="text-xs font-bold uppercase tracking-wider font-mono">Evidence ({signal.evidence.length} Metrik)</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-mono">
                <th className="pb-2 font-semibold">METRIK</th>
                <th className="pb-2 font-semibold">NILAI EMITEN</th>
                <th className="pb-2 font-semibold">MEDIAN PEER</th>
                <th className="pb-2 font-semibold text-right">POSISI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {signal.evidence.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-2.5 font-medium text-slate-200">{item.metric}</td>
                  <td className="py-2.5 font-mono font-bold text-cyan-400">{item.company_value}</td>
                  <td className="py-2.5 font-mono text-slate-400">{item.peer_median}</td>
                  <td className="py-2.5 text-right">
                    <span className={`px-2 py-0.5 rounded text-[9px] font-semibold ${
                      item.position.includes('TOP') || item.position === 'PREMIUM'
                        ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                        : item.position.includes('BOTTOM')
                        ? 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
                        : 'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}>
                      {item.position}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 5. Related Signals */}
      <div className="space-y-2">
        <div className="flex items-center space-x-2 text-amber-400">
          <Link2 className="w-4 h-4" />
          <span className="text-xs font-bold uppercase tracking-wider font-mono">Related Signals ({signal.related_signals.length})</span>
        </div>
        <div className="space-y-2">
          {signal.related_signals.map((rs, idx) => (
            <div key={idx} className="glass-card p-3 rounded-xl border border-slate-800 flex items-start justify-between">
              <div className="space-y-0.5">
                <span className="text-xs font-semibold text-slate-200">{rs.signal_type}</span>
                <p className="text-[11px] text-slate-400 leading-relaxed">{rs.description}</p>
              </div>
              <span className={`shrink-0 ml-3 px-2 py-0.5 rounded text-[9px] font-bold border ${
                rs.strength === 'STRONG'
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                  : rs.strength === 'MODERATE'
                  ? 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                  : 'bg-slate-800 text-slate-400 border-slate-700'
              }`}>
                {rs.strength}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
