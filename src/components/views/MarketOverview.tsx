import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import {
  Zap,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Globe2,
  ArrowRight,
  ShieldCheck,
  Star
} from 'lucide-react';
import type { MarketOverview as MarketOverviewType, IntelligenceSnapshot } from '../../types/api';
import { MOCK_COMPANIES } from '../../services/mockData';
import { WatchlistButton } from '../shared/WatchlistButton';
import type { ViewType } from '../Sidebar';

interface MarketOverviewProps {
  marketOverview: MarketOverviewType;
  onSelectSymbol: (symbol: string) => void;
  onNavigate: (view: ViewType) => void;
  watchlist: string[];
  onToggleWatchlist: (symbol: string) => void;
}

const SnapshotCard: React.FC<{
  intel: IntelligenceSnapshot;
  onSelect: (symbol: string) => void;
  variant: 'opportunity' | 'risk' | 'anomaly';
  watchlist: string[];
  onToggleWatchlist: (symbol: string) => void;
}> = ({ intel, onSelect, variant, watchlist, onToggleWatchlist }) => {
  const company = MOCK_COMPANIES[intel.symbol];
  const borderColor = variant === 'opportunity'
    ? 'border-emerald-500/30 hover:border-emerald-500/50'
    : variant === 'risk'
    ? 'border-rose-500/30 hover:border-rose-500/50'
    : 'border-amber-500/30 hover:border-amber-500/50';

  return (
    <div
      className={`glass-card p-4 rounded-xl border cursor-pointer transition-all group ${borderColor}`}
      onClick={() => onSelect(intel.symbol)}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-bold text-white font-mono">{intel.symbol}</span>
          <WatchlistButton
            symbol={intel.symbol}
            isInWatchlist={watchlist.includes(intel.symbol)}
            onToggle={onToggleWatchlist}
          />
        </div>
        <div className="flex items-center space-x-1.5">
          {intel.direction === 'BULLISH'
            ? <TrendingUp className="w-4 h-4 text-emerald-400" />
            : <TrendingDown className="w-4 h-4 text-rose-400" />
          }
          <span className={`text-[10px] font-bold ${
            intel.direction === 'BULLISH' ? 'text-emerald-400' : 'text-rose-400'
          }`}>
            {intel.direction}
          </span>
        </div>
      </div>

      <div className="text-[10px] text-slate-400 mb-2 truncate">
        {company?.name || intel.symbol} — {company?.sector || ''}
      </div>

      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="bg-slate-900/60 p-2 rounded-lg text-center">
          <span className="text-[9px] text-slate-400 font-mono block">OPPORTUNITY</span>
          <span className="text-base font-black text-cyan-400 font-mono">{intel.opportunity_score}</span>
        </div>
        <div className="bg-slate-900/60 p-2 rounded-lg text-center">
          <span className="text-[9px] text-slate-400 font-mono block">RISK</span>
          <span className="text-base font-black text-slate-200 font-mono">{intel.risk_score}</span>
        </div>
      </div>

      {intel.is_anomaly && (
        <div className="flex items-center space-x-1.5 text-amber-400 text-[10px] font-semibold">
          <AlertTriangle className="w-3 h-3" />
          <span>Anomaly Detected (Score: {intel.anomaly_score})</span>
        </div>
      )}

      <div className="mt-2 pt-2 border-t border-slate-800/50 flex items-center justify-between">
        <span className="text-[10px] text-slate-400 font-mono">Confidence: {intel.confidence}</span>
        <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400 transition-colors" />
      </div>
    </div>
  );
};

export const MarketOverviewView: React.FC<MarketOverviewProps> = ({
  marketOverview,
  onSelectSymbol,
  onNavigate,
  watchlist,
  onToggleWatchlist
}) => {
  const top10ChartData = marketOverview.top_opportunities.slice(0, 10).map(intel => ({
    symbol: intel.symbol,
    opportunity: intel.opportunity_score,
  }));

  return (
    <div className="space-y-6">
      {/* Hero Header */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 relative overflow-hidden">
        <div className="absolute -right-24 -top-24 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -left-24 -bottom-24 w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative">
          <h1 className="text-xl font-bold text-white mb-1">Market Intelligence Overview</h1>
          <p className="text-xs text-slate-400 max-w-2xl">
            Ringkasan kondisi pasar terkini berbasis sinyal kuantitatif, deteksi anomali, dan agregasi intelijen sektor.
            Data diproses melalui Sectors API/MCP Pipeline untuk menghasilkan <em>derived insight</em> — bukan data mentah.
          </p>
        </div>
      </div>

      {/* Quick Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card p-4 rounded-xl border border-slate-800 glow-cyan">
          <div className="flex items-center space-x-2 mb-2">
            <Zap className="w-4 h-4 text-cyan-400" />
            <span className="text-[10px] text-slate-400 font-mono uppercase">Top Opportunities</span>
          </div>
          <span className="text-2xl font-black text-white font-mono">{marketOverview.top_opportunities.length}</span>
          <span className="text-[10px] text-slate-400 block mt-1">Emiten dengan sinyal peluang tinggi</span>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-800 glow-rose">
          <div className="flex items-center space-x-2 mb-2">
            <ShieldCheck className="w-4 h-4 text-rose-400" />
            <span className="text-[10px] text-slate-400 font-mono uppercase">Top Risks</span>
          </div>
          <span className="text-2xl font-black text-white font-mono">{marketOverview.top_risks.length}</span>
          <span className="text-[10px] text-slate-400 block mt-1">Emiten dengan sinyal risiko tinggi</span>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-800 glow-amber">
          <div className="flex items-center space-x-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span className="text-[10px] text-slate-400 font-mono uppercase">Anomalies</span>
          </div>
          <span className="text-2xl font-black text-white font-mono">{marketOverview.detected_anomalies.length}</span>
          <span className="text-[10px] text-slate-400 block mt-1">Ketidaksesuaian data terdeteksi</span>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-800">
          <div className="flex items-center space-x-2 mb-2">
            <Star className="w-4 h-4 text-amber-400" />
            <span className="text-[10px] text-slate-400 font-mono uppercase">Watchlist</span>
          </div>
          <span className="text-2xl font-black text-white font-mono">{watchlist.length}</span>
          <span className="text-[10px] text-slate-400 block mt-1">Emiten dalam pantauan Anda</span>
        </div>
      </div>

      {/* Top 10 Opportunities Chart */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-cyan-400" />
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono">
              Top 10 Market Opportunities
            </h2>
          </div>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={top10ChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="symbol" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
              <YAxis stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} domain={[0, 100]} />
              <RechartsTooltip 
                cursor={{ fill: '#334155', opacity: 0.4 }}
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                itemStyle={{ color: '#22d3ee' }}
              />
              <Bar dataKey="opportunity" name="Opportunity Score" fill="#22d3ee" radius={[4, 4, 0, 0]} barSize={32} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Opportunities */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Zap className="w-5 h-5 text-emerald-400" />
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono">
              Top Opportunities
            </h2>
          </div>
          <button
            onClick={() => onNavigate('signals')}
            className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center space-x-1 transition-colors"
          >
            <span>Lihat Core Signal Engine</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {marketOverview.top_opportunities.map((intel) => (
            <SnapshotCard
              key={intel.symbol}
              intel={intel}
              onSelect={onSelectSymbol}
              variant="opportunity"
              watchlist={watchlist}
              onToggleWatchlist={onToggleWatchlist}
            />
          ))}
        </div>
      </div>

      {/* Top Anomalies */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono">
              Detected Anomalies
            </h2>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {marketOverview.detected_anomalies.map((intel) => (
            <SnapshotCard
              key={`anomaly-${intel.symbol}`}
              intel={intel}
              onSelect={onSelectSymbol}
              variant="anomaly"
              watchlist={watchlist}
              onToggleWatchlist={onToggleWatchlist}
            />
          ))}
        </div>
      </div>

      {/* Sector Summary */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Globe2 className="w-5 h-5 text-sky-400" />
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono">
              Sector Intelligence Summary
            </h2>
          </div>
          <button
            onClick={() => onNavigate('market')}
            className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center space-x-1 transition-colors"
          >
            <span>Lihat Detail Sektor & Screener</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
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
                  {sec.sentiment}
                </span>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800/50 flex items-center justify-between">
                <span className="text-xs font-mono font-bold">{sec.avg_opportunity}</span>
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
    </div>
  );
};
