import React, { useState } from 'react';
import {
  Globe2,
  SlidersHorizontal,
  Calendar,
  Activity
} from 'lucide-react';
import type { MarketOverview, ScreenerFilter, IntelligenceSnapshot } from '../../types/api';
import { MOCK_MACRO, MOCK_EVENTS, MOCK_SIGNAL_MATRIX } from '../../services/mockData';
import { apiService } from '../../services/mockApi';
import { SignalMatrix } from '../shared/SignalMatrix';

interface MarketIntelligenceProps {
  marketOverview: MarketOverview;
  onSelectSymbol: (symbol: string) => void;
}

export const MarketIntelligence: React.FC<MarketIntelligenceProps> = ({
  marketOverview,
  onSelectSymbol
}) => {
  // Screener state
  const [selectedSector, setSelectedSector] = useState<string>('');
  const [minOpportunity, setMinOpportunity] = useState<number>(50);
  const [maxRisk, setMaxRisk] = useState<number>(80);
  const [mustHaveDivergence, setMustHaveDivergence] = useState<boolean>(false);
  const [screenerResults, setScreenerResults] = useState<IntelligenceSnapshot[]>(
    marketOverview.top_opportunities
  );
  const [isSearching, setIsSearching] = useState<boolean>(false);

  const handleApplyFilter = async () => {
    setIsSearching(true);
    const filter: ScreenerFilter = {
      sector: selectedSector || undefined,
      min_opportunity: minOpportunity,
      max_risk: maxRisk,
      must_have_divergence: mustHaveDivergence
    };
    const res = await apiService.runScreener(filter);
    if (res.status === 'success' && res.data) {
      setScreenerResults(res.data);
    }
    setIsSearching(false);
  };

  return (
    <div className="space-y-6">
      {/* Sector Intelligence Heatmap Section */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Globe2 className="w-5 h-5 text-cyan-400" />
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Sector Intelligence & Health Map
            </h3>
          </div>
          <span className="text-xs text-slate-400">Agregasi Sinyal Real-time</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {marketOverview.sector_summary.map((sec, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-xl border flex flex-col justify-between transition-all ${
                sec.sentiment === 'Bullish'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : sec.sentiment === 'Bearish'
                  ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                  : 'bg-slate-900/60 border-slate-800 text-slate-300'
              }`}
            >
              <div>
                <span className="text-xs font-bold block truncate">{sec.sector}</span>
                <span className="text-[10px] uppercase font-mono opacity-80 mt-0.5 block">
                  Sentiment: {sec.sentiment}
                </span>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800/50 flex items-center justify-between">
                <span className="text-xs font-mono font-bold">{sec.avg_opportunity} Opp Score</span>
                {sec.anomaly_count > 0 && (
                  <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                    {sec.anomaly_count} Anomali
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Signal Matrix 2D Quadrant */}
      <div className="pt-2">
        <SignalMatrix data={MOCK_SIGNAL_MATRIX} onSelectSymbol={onSelectSymbol} />
      </div>

      {/* Intelligent Screener Section */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800">
        <div className="flex items-center space-x-2 mb-4">
          <SlidersHorizontal className="w-5 h-5 text-sky-400" />
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
            Intelligent Screener (Kombinasi Logika Kustom)
          </h3>
        </div>

        {/* Filter Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-4 bg-slate-900/60 rounded-xl border border-slate-800 mb-6">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Filter Sektor</label>
            <select
              value={selectedSector}
              onChange={(e) => setSelectedSector(e.target.value)}
              className="w-full bg-slate-950 text-xs text-slate-200 p-2 rounded-lg border border-slate-800 focus:outline-none focus:border-cyan-500"
            >
              <option value="">Semua Sektor</option>
              <option value="Financials">Financials</option>
              <option value="Telecommunication">Telecommunication</option>
              <option value="Technology">Technology</option>
              <option value="Consumer Staples">Consumer Staples</option>
            </select>
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Min Opportunity Score ({minOpportunity})</label>
            <input
              type="range"
              min="0"
              max="100"
              value={minOpportunity}
              onChange={(e) => setMinOpportunity(Number(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer"
            />
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Max Risk Score ({maxRisk})</label>
            <input
              type="range"
              min="0"
              max="100"
              value={maxRisk}
              onChange={(e) => setMaxRisk(Number(e.target.value))}
              className="w-full accent-rose-400 cursor-pointer"
            />
          </div>

          <div className="flex items-center space-x-3 pt-4">
            <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={mustHaveDivergence}
                onChange={(e) => setMustHaveDivergence(e.target.checked)}
                className="rounded border-slate-800 text-cyan-500 focus:ring-0"
              />
              <span>Hanya yang ada Anomali / Divergensi</span>
            </label>
            <button
              onClick={handleApplyFilter}
              disabled={isSearching}
              className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs rounded-lg transition-all shadow-md shadow-cyan-500/20"
            >
              {isSearching ? 'Filtering...' : 'Jalankan Filter'}
            </button>
          </div>
        </div>

        {/* Screener Results Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-mono">
                <th className="pb-3 font-semibold">EMITEN</th>
                <th className="pb-3 font-semibold">OPPORTUNITY</th>
                <th className="pb-3 font-semibold">RISK LEVEL</th>
                <th className="pb-3 font-semibold">DIRECTION</th>
                <th className="pb-3 font-semibold">ANOMALY / DIVERGENCE</th>
                <th className="pb-3 font-semibold text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {screenerResults.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 font-bold text-white font-mono">{item.symbol}</td>
                  <td className="py-3 font-mono font-bold text-cyan-400">{item.opportunity_score} / 100</td>
                  <td className="py-3 font-mono text-slate-300">{item.risk_level} ({item.risk_score})</td>
                  <td className="py-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                      item.direction === 'BULLISH'
                        ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                        : 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
                    }`}>
                      {item.direction}
                    </span>
                  </td>
                  <td className="py-3">
                    {item.is_anomaly ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/20">
                        DETECTED
                      </span>
                    ) : (
                      <span className="text-slate-500 text-[10px]">Normal</span>
                    )}
                  </td>
                  <td className="py-3 text-right">
                    <button
                      onClick={() => onSelectSymbol(item.symbol)}
                      className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded text-[11px] font-semibold transition-all"
                    >
                      Analisa Emiten
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Event Study & Macro Impact Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Event Study */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center space-x-2 mb-4">
            <Calendar className="w-5 h-5 text-indigo-400" />
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Event Study Analysis (Evaluasi Dampak Peristiwa)
            </h3>
          </div>

          <div className="space-y-3">
            {MOCK_EVENTS.map((evt, idx) => (
              <div key={idx} className="glass-card p-3 rounded-xl border border-slate-800 flex justify-between items-center">
                <div>
                  <div className="text-xs font-semibold text-slate-200">{evt.event_name}</div>
                  <div className="text-[10px] text-slate-400 font-mono">{evt.date} | {evt.category}</div>
                </div>
                <div className="text-right">
                  <span className={`text-xs font-mono font-bold ${
                    evt.price_reaction_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}>
                    {evt.price_reaction_pct >= 0 ? '+' : ''}{evt.price_reaction_pct}% Reaction
                  </span>
                  <div className="text-[10px] text-slate-400">{evt.market_sentiment}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Macro Impact Analysis */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center space-x-2 mb-4">
            <Activity className="w-5 h-5 text-emerald-400" />
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Macro Impact & Correlation Analysis
            </h3>
          </div>

          <div className="space-y-3">
            {MOCK_MACRO.map((macro, idx) => (
              <div key={idx} className="glass-card p-3 rounded-xl border border-slate-800 flex justify-between items-center">
                <div>
                  <div className="text-xs font-semibold text-slate-200">{macro.name}</div>
                  <div className="text-[10px] text-slate-400">{macro.correlation_with_market}</div>
                </div>
                <div className="text-right">
                  <span className="text-xs font-mono font-bold text-cyan-400">{macro.value}</span>
                  <div className="text-[10px] text-emerald-400 font-semibold">{macro.impact_assessment}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
