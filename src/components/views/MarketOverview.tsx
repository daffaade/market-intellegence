import React, { useState, useMemo } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import {
  Zap,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Globe2,
  ArrowRight,
  ShieldCheck,
  Star,
  Search,
  SlidersHorizontal,
  Building2,
  Activity
} from 'lucide-react';
import type { MarketOverview as MarketOverviewType, IntelligenceSnapshot } from '../../types/api';
import { MOCK_COMPANIES, MOCK_INTELLIGENCE, MOCK_TOP10_GROWTH_TIMELINE } from '../../services/mockData';
import { WatchlistButton } from '../shared/WatchlistButton';
import type { ViewType } from '../Sidebar';

interface MarketOverviewProps {
  marketOverview: MarketOverviewType;
  onSelectSymbol: (symbol: string) => void;
  onNavigate: (view: ViewType) => void;
  watchlist: string[];
  onToggleWatchlist: (symbol: string) => void;
}

const EMITEN_COLORS: Record<string, string> = {
  BBCA: '#06b6d4', // Cyan
  BBRI: '#3b82f6', // Blue
  BMRI: '#6366f1', // Indigo
  BBNI: '#8b5cf6', // Purple
  TLKM: '#ec4899', // Pink
  AMMN: '#f59e0b', // Amber
  ICBP: '#10b981', // Emerald
  ASII: '#14b8a6', // Teal
  ADRO: '#f97316', // Orange
  KLBF: '#84cc16', // Lime
};

const TOP_10_SYMBOLS = ['BBCA', 'BBRI', 'BMRI', 'BBNI', 'TLKM', 'AMMN', 'ICBP', 'ASII', 'ADRO', 'KLBF'];

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
  // Chart Controls State
  const [timeframe, setTimeframe] = useState<'3M' | '6M' | '1Y'>('1Y');
  const [selectedEmiten, setSelectedEmiten] = useState<string>('ALL');

  // Directory Filters State
  const [directorySearch, setDirectorySearch] = useState('');
  const [selectedSector, setSelectedSector] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'opportunity' | 'market_cap' | 'risk' | 'name'>('opportunity');

  // Filtered timeline data for charts
  const filteredTimelineData = useMemo(() => {
    if (timeframe === '3M') {
      return MOCK_TOP10_GROWTH_TIMELINE.slice(-3);
    }
    if (timeframe === '6M') {
      return MOCK_TOP10_GROWTH_TIMELINE.slice(-6);
    }
    return MOCK_TOP10_GROWTH_TIMELINE;
  }, [timeframe]);

  // Delta calculation for single focus mode
  const singleFocusMetrics = useMemo(() => {
    if (selectedEmiten === 'ALL' || filteredTimelineData.length === 0) return null;
    const startVal = Number(filteredTimelineData[0][selectedEmiten] || 0);
    const endVal = Number(filteredTimelineData[filteredTimelineData.length - 1][selectedEmiten] || 0);
    const delta = endVal - startVal;
    const deltaPct = startVal > 0 ? (delta / startVal) * 100 : 0;
    return {
      start: startVal.toFixed(1),
      end: endVal.toFixed(1),
      delta: (delta >= 0 ? '+' : '') + delta.toFixed(1),
      deltaPct: (deltaPct >= 0 ? '+' : '') + deltaPct.toFixed(1) + '%'
    };
  }, [selectedEmiten, filteredTimelineData]);

  // All Available Markets List
  const allCompaniesList = useMemo(() => {
    return Object.values(MOCK_COMPANIES).map(comp => {
      const intel = MOCK_INTELLIGENCE[comp.symbol] || {
        opportunity_score: 50,
        risk_score: 50,
        direction: 'NEUTRAL' as const,
        confidence: 'MEDIUM' as const,
        risk_level: 'MODERATE' as const,
        is_anomaly: false,
        anomaly_score: 0,
        positive_factors: ['Data operasional stabil'],
      };
      return {
        ...comp,
        intel
      };
    });
  }, []);

  // Unique Sectors for Directory Filter
  const availableSectors = useMemo(() => {
    const set = new Set<string>();
    allCompaniesList.forEach(c => set.add(c.sector));
    return Array.from(set);
  }, [allCompaniesList]);

  // Filtered and Sorted Directory List
  const filteredDirectoryMarkets = useMemo(() => {
    let list = allCompaniesList;

    // Search filter
    if (directorySearch.trim()) {
      const q = directorySearch.toLowerCase().trim();
      list = list.filter(item =>
        item.symbol.toLowerCase().includes(q) ||
        item.name.toLowerCase().includes(q) ||
        item.sector.toLowerCase().includes(q) ||
        item.sub_sector.toLowerCase().includes(q)
      );
    }

    // Sector filter
    if (selectedSector !== 'ALL') {
      list = list.filter(item => item.sector === selectedSector);
    }

    // Sorting
    return [...list].sort((a, b) => {
      if (sortBy === 'opportunity') {
        return b.intel.opportunity_score - a.intel.opportunity_score;
      }
      if (sortBy === 'risk') {
        return a.intel.risk_score - b.intel.risk_score;
      }
      if (sortBy === 'market_cap') {
        return b.market_cap - a.market_cap;
      }
      return a.symbol.localeCompare(b.symbol);
    });
  }, [allCompaniesList, directorySearch, selectedSector, sortBy]);

  // Helper formatting for Market Cap
  const formatMarketCap = (cap: number) => {
    if (cap >= 1000000000000000) {
      return `Rp ${(cap / 1000000000000000).toFixed(2)} Ribu Triliun`;
    }
    if (cap >= 1000000000000) {
      return `Rp ${(cap / 1000000000000).toFixed(1)} Triliun`;
    }
    return `Rp ${(cap / 1000000000).toFixed(0)} Miliar`;
  };

  return (
    <div className="space-y-8">
      {/* Hero Header */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 relative overflow-hidden">
        <div className="absolute -right-24 -top-24 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -left-24 -bottom-24 w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative">
          <div className="flex items-center space-x-2 mb-1">
            <Activity className="w-5 h-5 text-cyan-400" />
            <h1 className="text-xl font-bold text-white">Market Intelligence Overview</h1>
          </div>
          <p className="text-xs text-slate-400 max-w-3xl">
            Ringkasan kondisi pasar modal berbasis pemrosesan data Sectors API & Pipeline MCP.
            Menyajikan analisis tren deret waktu (*time-series*), komparasi pertumbuhan kuantitatif antar-emiten,
            deteksi anomali data, dan direktori lengkap pasar saham Indonesia.
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
          <span className="text-[10px] text-slate-400 block mt-1">Emiten dengan skor peluang tertinggi</span>
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
          <span className="text-[10px] text-slate-400 block mt-1">Ketidaksesuaian pola terdeteksi</span>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-800">
          <div className="flex items-center space-x-2 mb-2">
            <Star className="w-4 h-4 text-amber-400" />
            <span className="text-[10px] text-slate-400 font-mono uppercase">Watchlist</span>
          </div>
          <span className="text-2xl font-black text-white font-mono">{watchlist.length}</span>
          <span className="text-[10px] text-slate-400 block mt-1">Emiten dalam radar pantauan Anda</span>
        </div>
      </div>

      {/* Top 10 Opportunities Growth Chart (Time-Series) */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-5 h-5 text-cyan-400" />
              <h2 className="text-base font-bold text-white tracking-wide">
                Top 10 Market Opportunities: Tren Pertumbuhan Waktu ke Waktu
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Historis dinamika Opportunity Score bulanan untuk 10 emiten berprospek tertinggi di pasar modal Indonesia.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Timeframe Selector */}
            <div className="flex items-center bg-slate-900/80 p-1 rounded-lg border border-slate-800 text-xs">
              {(['3M', '6M', '1Y'] as const).map(tf => (
                <button
                  key={tf}
                  onClick={() => setTimeframe(tf)}
                  className={`px-3 py-1 rounded-md font-mono text-xs transition-all ${
                    timeframe === tf
                      ? 'bg-cyan-500 text-white font-bold shadow-lg shadow-cyan-500/20'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {tf === '1Y' ? '12 Bulan' : tf}
                </button>
              ))}
            </div>

            {/* Mode Focus Selector */}
            <button
              onClick={() => setSelectedEmiten('ALL')}
              className={`px-3 py-1.5 rounded-lg border text-xs font-mono transition-all ${
                selectedEmiten === 'ALL'
                  ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300 font-bold'
                  : 'bg-slate-900/80 border-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              Multi-Line (Semua Top 10)
            </button>
          </div>
        </div>

        {/* Emiten Filter Chips */}
        <div className="flex flex-wrap gap-2 mb-6 pt-2 border-t border-slate-800/60">
          <span className="text-[11px] font-mono text-slate-500 self-center mr-1">Fokus Emiten:</span>
          {TOP_10_SYMBOLS.map(sym => {
            const isFocus = selectedEmiten === sym;
            const color = EMITEN_COLORS[sym] || '#06b6d4';
            return (
              <button
                key={sym}
                onClick={() => setSelectedEmiten(sym === selectedEmiten ? 'ALL' : sym)}
                className={`px-2.5 py-1 rounded-md text-xs font-mono transition-all flex items-center space-x-1.5 border ${
                  isFocus
                    ? 'border-cyan-400/80 bg-slate-800 text-white font-bold shadow-md'
                    : selectedEmiten === 'ALL'
                    ? 'border-slate-800 bg-slate-900/60 text-slate-300 hover:border-slate-700'
                    : 'border-slate-800/40 bg-slate-950/40 text-slate-500 opacity-60 hover:opacity-100'
                }`}
              >
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                <span>{sym}</span>
              </button>
            );
          })}
        </div>

        {/* Single Focus Metrics Card */}
        {selectedEmiten !== 'ALL' && singleFocusMetrics && (
          <div className="mb-6 p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center font-mono font-bold text-white text-sm"
                style={{ backgroundColor: `${EMITEN_COLORS[selectedEmiten]}33`, border: `1px solid ${EMITEN_COLORS[selectedEmiten]}` }}
              >
                {selectedEmiten}
              </div>
              <div>
                <span className="text-sm font-bold text-white block">
                  {MOCK_COMPANIES[selectedEmiten]?.name || selectedEmiten}
                </span>
                <span className="text-xs text-slate-400">
                  {MOCK_COMPANIES[selectedEmiten]?.sector} • Sub-sektor: {MOCK_COMPANIES[selectedEmiten]?.sub_sector}
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-6 font-mono text-xs">
              <div>
                <span className="text-slate-500 block text-[10px]">SKOR AWAL ({filteredTimelineData[0]?.period})</span>
                <span className="text-slate-200 font-bold text-sm">{singleFocusMetrics.start}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">SKOR TERKINI ({filteredTimelineData[filteredTimelineData.length - 1]?.period})</span>
                <span className="text-cyan-400 font-bold text-sm">{singleFocusMetrics.end}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">DELTA PERTUMBUHAN</span>
                <span className="text-emerald-400 font-bold text-sm">
                  {singleFocusMetrics.delta} ({singleFocusMetrics.deltaPct})
                </span>
              </div>
              <button
                onClick={() => onSelectSymbol(selectedEmiten)}
                className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-sans font-bold px-3 py-1.5 rounded-lg text-xs flex items-center space-x-1 transition-colors ml-auto"
              >
                <span>Analisis Penuh</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* Chart Canvas */}
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            {selectedEmiten !== 'ALL' ? (
              <AreaChart data={filteredTimelineData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id={`gradient-${selectedEmiten}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={EMITEN_COLORS[selectedEmiten]} stopOpacity={0.4} />
                    <stop offset="95%" stopColor={EMITEN_COLORS[selectedEmiten]} stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="period" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} domain={[50, 100]} />
                <RechartsTooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)' }}
                  formatter={(value: any) => [`${value} Poin`, 'Opportunity Score']}
                  labelStyle={{ color: '#94a3b8', fontWeight: 'bold' }}
                />
                <Area
                  type="monotone"
                  dataKey={selectedEmiten}
                  stroke={EMITEN_COLORS[selectedEmiten]}
                  strokeWidth={3}
                  fillOpacity={1}
                  fill={`url(#gradient-${selectedEmiten})`}
                  dot={{ fill: EMITEN_COLORS[selectedEmiten], r: 4 }}
                  activeDot={{ r: 6, stroke: '#fff', strokeWidth: 2 }}
                />
              </AreaChart>
            ) : (
              <LineChart data={filteredTimelineData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="period" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} domain={[50, 100]} />
                <RechartsTooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '11px', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)' }}
                  labelStyle={{ color: '#94a3b8', fontWeight: 'bold', marginBottom: '4px' }}
                />
                <Legend
                  wrapperStyle={{ paddingTop: '16px', fontSize: '11px' }}
                  iconType="circle"
                />
                {TOP_10_SYMBOLS.map(sym => (
                  <Line
                    key={sym}
                    type="monotone"
                    dataKey={sym}
                    stroke={EMITEN_COLORS[sym]}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 5 }}
                  />
                ))}
              </LineChart>
            )}
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Opportunities Grid Cards */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Zap className="w-5 h-5 text-emerald-400" />
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono">
              Top 10 High Opportunity Signals
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

      {/* Top Anomalies Grid Cards */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono">
              Detected Anomalies & Divergence
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

      {/* Sector Intelligence Summary */}
      <div>
        <div className="flex items-center justify-between mb-4">
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
            <span>Lihat Screener Sektoral</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
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
                <span className="text-xs font-mono font-bold">{sec.avg_opportunity} Poin</span>
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

      {/* ─────────────────────────────────────────────────────────────
          SECTION PALING BAWAH: DIREKTORI SELURUH MARKET & EMITEN
          ───────────────────────────────────────────────────────────── */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <Building2 className="w-5 h-5 text-cyan-400" />
              <h2 className="text-base font-bold text-white tracking-wide">
                Direktori Pasar & Seluruh Emiten Terdaftar
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Katalog seluruh emiten yang telah terindeks dan diproses oleh pipeline intelijen.
              Pilih emiten untuk melihat detail fundamental, matriks sinyal, dan proyeksi risiko.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-400 font-mono">
              Total Emiten: <strong className="text-cyan-400">{filteredDirectoryMarkets.length}</strong> / {allCompaniesList.length}
            </span>
          </div>
        </div>

        {/* Directory Controls: Search, Sector Tabs & Sort */}
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4 pt-2 border-t border-slate-800/60">
          {/* Search Box */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={directorySearch}
              onChange={(e) => setDirectorySearch(e.target.value)}
              placeholder="Cari pasar (e.g. BBCA, perbankan, batubara)..."
              className="bg-slate-900/90 text-xs text-slate-200 pl-9 pr-4 py-2 rounded-lg border border-slate-800 focus:outline-none focus:border-cyan-500/50 w-full"
            />
          </div>

          {/* Sort Selector */}
          <div className="flex items-center space-x-2 shrink-0">
            <SlidersHorizontal className="w-4 h-4 text-slate-400" />
            <span className="text-xs text-slate-400">Urutkan:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="bg-slate-900 border border-slate-800 text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyan-500"
            >
              <option value="opportunity">Opportunity Tertinggi</option>
              <option value="market_cap">Kapitalisasi Pasar Terbesar</option>
              <option value="risk">Risk Terendah</option>
              <option value="name">Kode Saham (A-Z)</option>
            </select>
          </div>
        </div>

        {/* Sector Filter Chips */}
        <div className="flex items-center space-x-2 overflow-x-auto pb-2 scrollbar-thin">
          <button
            onClick={() => setSelectedSector('ALL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
              selectedSector === 'ALL'
                ? 'bg-cyan-500 text-slate-950 font-bold'
                : 'bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            Semua Sektor ({allCompaniesList.length})
          </button>
          {availableSectors.map(sec => {
            const count = allCompaniesList.filter(c => c.sector === sec).length;
            return (
              <button
                key={sec}
                onClick={() => setSelectedSector(sec)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                  selectedSector === sec
                    ? 'bg-cyan-500 text-slate-950 font-bold'
                    : 'bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                {sec} ({count})
              </button>
            );
          })}
        </div>

        {/* Directory Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDirectoryMarkets.map(item => {
            const isBullish = item.intel.direction === 'BULLISH';
            const isBearish = item.intel.direction === 'BEARISH';

            return (
              <div
                key={item.symbol}
                className="glass-card p-4 rounded-xl border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-base font-bold font-mono text-white group-hover:text-cyan-400 transition-colors">
                        {item.symbol}
                      </span>
                      <WatchlistButton
                        symbol={item.symbol}
                        isInWatchlist={watchlist.includes(item.symbol)}
                        onToggle={onToggleWatchlist}
                      />
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md flex items-center space-x-1 ${
                      isBullish
                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                        : isBearish
                        ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                        : 'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}>
                      {isBullish && <TrendingUp className="w-3 h-3 mr-0.5 inline" />}
                      {isBearish && <TrendingDown className="w-3 h-3 mr-0.5 inline" />}
                      {item.intel.direction}
                    </span>
                  </div>

                  <h3 className="text-xs font-semibold text-slate-200 line-clamp-1">
                    {item.name}
                  </h3>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    {item.sector} • {item.sub_sector}
                  </p>

                  {/* Market Cap & Key Signal */}
                  <div className="mt-3 grid grid-cols-2 gap-2 bg-slate-900/60 p-2.5 rounded-lg">
                    <div>
                      <span className="text-[9px] text-slate-400 font-mono block">OPPORTUNITY</span>
                      <span className="text-sm font-black font-mono text-cyan-400">
                        {item.intel.opportunity_score}
                      </span>
                    </div>
                    <div>
                      <span className="text-[9px] text-slate-400 font-mono block">RISK LEVEL</span>
                      <span className={`text-sm font-black font-mono ${
                        item.intel.risk_level === 'LOW' ? 'text-emerald-400' :
                        item.intel.risk_level === 'MODERATE' ? 'text-amber-400' : 'text-rose-400'
                      }`}>
                        {item.intel.risk_level}
                      </span>
                    </div>
                  </div>

                  <div className="mt-2 text-[10px] text-slate-400 flex items-center justify-between">
                    <span>Kapitalisasi Pasar:</span>
                    <span className="font-mono text-slate-200 font-semibold">{formatMarketCap(item.market_cap)}</span>
                  </div>

                  {item.intel.is_anomaly && (
                    <div className="mt-2 text-[10px] text-amber-400 font-medium flex items-center space-x-1">
                      <AlertTriangle className="w-3 h-3 shrink-0" />
                      <span>Anomali Terdeteksi (Skor {item.intel.anomaly_score})</span>
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between">
                  <span className="text-[10px] text-slate-500 font-mono">
                    Confidence: {item.intel.confidence}
                  </span>
                  <button
                    onClick={() => onSelectSymbol(item.symbol)}
                    className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center space-x-1 transition-colors group-hover:translate-x-0.5"
                  >
                    <span>Buka Analisis</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {filteredDirectoryMarkets.length === 0 && (
          <div className="p-12 text-center text-slate-400 text-xs">
            Tidak ada emiten yang sesuai dengan kriteria pencarian Anda.
          </div>
        )}
      </div>
    </div>
  );
};

