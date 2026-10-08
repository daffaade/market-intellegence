import React, { useState, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LabelList,
  ReferenceLine
} from 'recharts';
import { Search, ArrowRight } from 'lucide-react';
import type { MarketOverview as MarketOverviewType, IntelligenceSnapshot, Company } from '../../types/api';
import { apiService } from '../../services/mockApi';
import { useRemote } from '../../lib/useRemote';
import { RemoteBody, SourceNote } from '../shared/RemoteState';
import { WatchlistButton } from '../shared/WatchlistButton';
import type { ViewType } from '../Sidebar';
import { formatMarketCap, formatScore } from '../../lib/format';
import { useChartColors } from '../../lib/theme';
import {
  PageHeader,
  Panel,
  Stat,
  Segmented,
  ScoreBar,
  DirectionTag,
  Tag,
  SortHeader,
  EmptyState
} from '../ui/primitives';
import { cx } from '../../lib/ui';

interface MarketOverviewProps {
  marketOverview: MarketOverviewType;
  companies: Company[];
  /** Latest snapshot for every emiten (from the backend, or simulated data in dummy mode). */
  allIntelligence: IntelligenceSnapshot[];
  onSelectSymbol: (symbol: string) => void;
  onNavigate: (view: ViewType) => void;
  watchlist: string[];
  onToggleWatchlist: (symbol: string) => void;
}

const TIMEFRAME_WEEKS = { '3M': 13, '6M': 26, '1Y': 53 } as const;

const formatPct = (v: number) => `${v >= 0 ? '+' : '−'}${Math.abs(v).toLocaleString('id-ID', { maximumFractionDigits: 1 })}%`;

type SortKey = 'symbol' | 'sector' | 'market_cap' | 'opportunity' | 'risk';

/** Compact ranked row used by the opportunity / risk / anomaly lists. */
const RankRow: React.FC<{
  rank: number;
  intel: IntelligenceSnapshot;
  name?: string;
  metric: 'opportunity' | 'risk' | 'anomaly';
  onSelect: (s: string) => void;
}> = ({ rank, intel, name, metric, onSelect }) => {
  return (
    <li>
      <button
        onClick={() => onSelect(intel.symbol)}
        className="w-full flex items-center gap-3 px-4 h-11 text-left hover:bg-surface-2 transition-colors group"
      >
        <span className="num text-xs text-ink-3 w-4 shrink-0">{rank}</span>
        <span className="num text-[13px] font-medium text-ink w-12 shrink-0">{intel.symbol}</span>
        <span className="text-[13px] text-ink-2 truncate flex-1 min-w-0">{name ?? '—'}</span>
        <span className="hidden sm:inline-flex"><DirectionTag direction={intel.direction} /></span>
        {metric === 'opportunity' && <ScoreBar value={intel.opportunity_score} width="w-16" />}
        {metric === 'risk' && <ScoreBar value={intel.risk_score} tone="risk" width="w-16" />}
        {metric === 'anomaly' && <ScoreBar value={intel.anomaly_score} tone="risk" width="w-16" />}
      </button>
    </li>
  );
};

export const MarketOverviewView: React.FC<MarketOverviewProps> = ({
  marketOverview,
  companies,
  allIntelligence,
  onSelectSymbol,
  onNavigate,
  watchlist,
  onToggleWatchlist
}) => {
  const colors = useChartColors();
  const [timeframe, setTimeframe] = useState<'3M' | '6M' | '1Y'>('1Y');
  const [focus, setFocus] = useState<string>('BBCA');
  const performance = useRemote(() => apiService.getPricePerformance(), []);

  const [search, setSearch] = useState('');
  const [sector, setSector] = useState('ALL');
  const [sortKey, setSortKey] = useState<SortKey>('opportunity');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const rows = useMemo(() => {
    const intelBySymbol = new Map(allIntelligence.map(i => [i.symbol, i]));
    return companies.map(c => ({ ...c, intel: intelBySymbol.get(c.symbol) }));
  }, [companies, allIntelligence]);

  const nameOf = useMemo(() => {
    const names = new Map(companies.map(c => [c.symbol, c.name]));
    return (symbol: string) => names.get(symbol);
  }, [companies]);

  // ── Market-wide summary numbers ──
  const summary = useMemo(() => {
    const intels = rows.map(r => r.intel).filter((i): i is IntelligenceSnapshot => !!i);
    const count = (d: IntelligenceSnapshot['direction']) => intels.filter(i => i.direction === d).length;
    const avg = intels.reduce((a, i) => a + i.opportunity_score, 0) / (intels.length || 1);
    return {
      total: rows.length,
      bullish: count('BULLISH'),
      neutral: count('NEUTRAL'),
      bearish: count('BEARISH'),
      avgOpp: avg,
      scored: intels.length
    };
  }, [rows]);

  // ── Price performance chart: weekly closes rebased to 0% at the start of the window ──
  const symbols = performance.data?.symbols ?? [];
  const timeline = useMemo(() => {
    const pts = performance.data?.points ?? [];
    const window = pts.slice(-TIMEFRAME_WEEKS[timeframe]);
    const base: Record<string, number | null> = {};
    symbols.forEach(sym => {
      const first = window.find(p => typeof p[sym] === 'number');
      base[sym] = first ? Number(first[sym]) : null;
    });
    return window.map(p => {
      const row: Record<string, number | string | null> = {
        period: new Date(p.date).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: '2-digit' })
      };
      symbols.forEach(sym => {
        const v = p[sym];
        row[sym] = typeof v === 'number' && base[sym] ? +(((v / base[sym]!) - 1) * 100).toFixed(2) : null;
      });
      return row;
    });
  }, [performance.data, symbols, timeframe]);

  const focusDelta = useMemo(() => {
    const vals = timeline.map(r => r[focus]).filter((v): v is number => typeof v === 'number');
    const ranked = symbols
      .map(sym => ({ sym, v: [...timeline].reverse().find(r => typeof r[sym] === 'number')?.[sym] as number | undefined }))
      .filter(r => r.v !== undefined)
      .sort((a, b) => b.v! - a.v!);
    return { end: vals[vals.length - 1] ?? 0, rank: ranked.findIndex(r => r.sym === focus) + 1, of: ranked.length };
  }, [timeline, focus, symbols]);

  // ── Directory ──
  const sectors = useMemo(() => Array.from(new Set(rows.map(r => r.sector))).sort(), [rows]);

  const directory = useMemo(() => {
    const q = search.toLowerCase().trim();
    let list = rows.filter(
      r =>
        (sector === 'ALL' || r.sector === sector) &&
        (!q ||
          r.symbol.toLowerCase().includes(q) ||
          r.name.toLowerCase().includes(q) ||
          r.sub_sector.toLowerCase().includes(q))
    );
    const val = (r: (typeof rows)[number]): number | string => {
      switch (sortKey) {
        case 'symbol': return r.symbol;
        case 'sector': return r.sector;
        case 'market_cap': return r.market_cap;
        case 'opportunity': return r.intel?.opportunity_score ?? -1;
        case 'risk': return r.intel?.risk_score ?? -1;
      }
    };
    list = [...list].sort((a, b) => {
      const va = val(a);
      const vb = val(b);
      const cmp = typeof va === 'string' ? va.localeCompare(vb as string) : (va as number) - (vb as number);
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return list;
  }, [rows, search, sector, sortKey, sortDir]);

  const onSort = (k: SortKey) => {
    if (k === sortKey) setSortDir(d => (d === 'asc' ? 'desc' : 'asc'));
    else {
      setSortKey(k);
      setSortDir(k === 'symbol' || k === 'sector' ? 'asc' : 'desc');
    }
  };

  const topOpps = [...marketOverview.top_opportunities].sort((a, b) => b.opportunity_score - a.opportunity_score);
  const topRisks = [...marketOverview.top_risks].sort((a, b) => b.risk_score - a.risk_score);
  const anomalies = [...marketOverview.detected_anomalies].sort((a, b) => b.anomaly_score - a.anomaly_score);

  const pct = (n: number) => `${(n / (summary.scored || 1)) * 100}%`;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Pasar · Bursa Efek Indonesia"
        title="Ringkasan pasar"
        description="Skor peluang dan risiko untuk setiap emiten yang diproses pipeline, beserta anomali yang perlu diperiksa lebih lanjut."
      />

      {/* Summary strip */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-line border border-line rounded-lg overflow-hidden [&>*]:bg-surface [&>*]:p-4">
        <Stat label="Emiten dianalisis" value={summary.total} hint={`${sectors.length} sektor`} />
        <div>
          <div className="text-xs text-ink-3">Arah sinyal</div>
          <div className="num text-[22px] leading-tight text-ink mt-1">
            <span className="text-up">{summary.bullish}</span>
            <span className="text-ink-3 mx-1.5">/</span>
            <span className="text-ink-2">{summary.neutral}</span>
            <span className="text-ink-3 mx-1.5">/</span>
            <span className="text-down">{summary.bearish}</span>
          </div>
          <div className="flex h-1.5 mt-2 rounded-full overflow-hidden gap-0.5" aria-hidden="true">
            <div className="bg-up" style={{ width: pct(summary.bullish) }} />
            <div className="bg-line-strong" style={{ width: pct(summary.neutral) }} />
            <div className="bg-down" style={{ width: pct(summary.bearish) }} />
          </div>
          <div className="text-xs text-ink-3 mt-1.5">Bullish / netral / bearish</div>
        </div>
        <Stat label="Rata-rata skor peluang" value={formatScore(Number(summary.avgOpp.toFixed(1)))} hint="Skala 0–100" />
        <Stat
          label="Anomali terdeteksi"
          value={<span className={anomalies.length ? 'text-warn' : undefined}>{anomalies.length}</span>}
          hint="Harga dan fundamental tidak searah"
        />
      </section>

      {/* Ranked lists */}
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
        <Panel
          className="xl:col-span-3"
          title="Peluang tertinggi"
          meta="Skor peluang"
          flush
          actions={
            <button onClick={() => onNavigate('market')} className="text-xs text-ink-2 hover:text-ink inline-flex items-center gap-1">
              Buka screener <ArrowRight className="w-3 h-3" />
            </button>
          }
        >
          <ol className="divide-y divide-line py-1">
            {topOpps.map((intel, i) => (
              <RankRow key={intel.symbol} rank={i + 1} intel={intel} name={nameOf(intel.symbol)} metric="opportunity" onSelect={onSelectSymbol} />
            ))}
          </ol>
        </Panel>

        <div className="xl:col-span-2 space-y-6">
          <Panel title="Risiko tertinggi" meta="Skor risiko" flush>
            {topRisks.length ? (
              <ol className="divide-y divide-line py-1">
                {topRisks.map((intel, i) => (
                  <RankRow key={intel.symbol} rank={i + 1} intel={intel} name={nameOf(intel.symbol)} metric="risk" onSelect={onSelectSymbol} />
                ))}
              </ol>
            ) : (
              <EmptyState title="Tidak ada emiten berisiko tinggi" />
            )}
          </Panel>

          <Panel title="Anomali & divergensi" meta="Skor anomali" flush>
            {anomalies.length ? (
              <ol className="divide-y divide-line py-1">
                {anomalies.map((intel, i) => (
                  <RankRow key={intel.symbol} rank={i + 1} intel={intel} name={nameOf(intel.symbol)} metric="anomaly" onSelect={onSelectSymbol} />
                ))}
              </ol>
            ) : (
              <EmptyState title="Tidak ada anomali pada siklus ini" />
            )}
          </Panel>
        </div>
      </div>

      {/* Price performance — one highlighted series against the rest in gray */}
      <Panel
        title="Kinerja harga"
        meta="Emiten yang dipantau, mingguan"
        actions={
          <Segmented
            ariaLabel="Rentang waktu"
            value={timeframe}
            onChange={setTimeframe}
            options={[
              { value: '3M', label: '3 bln' },
              { value: '6M', label: '6 bln' },
              { value: '1Y', label: '12 bln' }
            ]}
          />
        }
        flush
      >
        <RemoteBody remote={performance} skeletonClassName="h-72" errorTitle="Data harga belum bisa dimuat">
          {data => (
            <div className="p-4">
              <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4 mb-4">
                <div className="flex flex-wrap gap-1.5" role="radiogroup" aria-label="Sorot emiten">
                  {symbols.map(sym => (
                    <button
                      key={sym}
                      role="radio"
                      aria-checked={focus === sym}
                      onClick={() => setFocus(sym)}
                      className={cx(
                        'num h-7 px-2.5 rounded-md text-xs border transition-colors',
                        focus === sym
                          ? 'border-accent text-accent bg-accent-soft'
                          : 'border-line text-ink-2 hover:border-line-strong hover:text-ink'
                      )}
                    >
                      {sym}
                    </button>
                  ))}
                </div>

                <div className="flex items-end gap-6 shrink-0">
                  <div>
                    <div className="text-xs text-ink-3">Sejak {timeline[0]?.period}</div>
                    <div className={cx('num text-[15px]', focusDelta.end >= 0 ? 'text-up' : 'text-down')}>{formatPct(focusDelta.end)}</div>
                  </div>
                  <div>
                    <div className="text-xs text-ink-3">Peringkat</div>
                    <div className="num text-[15px] text-ink">{focusDelta.rank > 0 ? `${focusDelta.rank} / ${focusDelta.of}` : '—'}</div>
                  </div>
                  <button
                    onClick={() => onSelectSymbol(focus)}
                    className="text-xs text-accent hover:underline inline-flex items-center gap-1 pb-1"
                  >
                    Buka {focus} <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>

              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timeline} margin={{ top: 8, right: 44, left: -8, bottom: 0 }}>
                    <CartesianGrid stroke={colors.grid} vertical={false} />
                    <XAxis dataKey="period" stroke={colors.axis} fontSize={11} tickLine={false} axisLine={{ stroke: colors.grid }} minTickGap={24} />
                    <YAxis stroke={colors.axis} fontSize={11} tickLine={false} axisLine={false} tickFormatter={v => `${v}%`} />
                    <ReferenceLine y={0} stroke={colors.axis} strokeDasharray="3 3" />
                    <Tooltip
                      cursor={{ stroke: colors.context }}
                      content={({ active, payload, label }) => {
                        if (!active || !payload?.length) return null;
                        const sorted = [...payload].filter(p => p.value !== null).sort((a, b) => Number(b.value) - Number(a.value));
                        return (
                          <div className="bg-surface border border-line-strong rounded-md shadow-lg px-3 py-2 text-xs min-w-[150px]">
                            <div className="text-ink-3 mb-1">{label}</div>
                            {sorted.map(p => (
                              <div
                                key={String(p.dataKey)}
                                className={cx('flex justify-between gap-4 num', p.dataKey === focus ? 'text-ink font-medium' : 'text-ink-3')}
                              >
                                <span>{String(p.dataKey)}</span>
                                <span>{formatPct(Number(p.value))}</span>
                              </div>
                            ))}
                          </div>
                        );
                      }}
                    />
                    {symbols.filter(s => s !== focus).map(sym => (
                      <Line
                        key={sym}
                        type="monotone"
                        dataKey={sym}
                        stroke={colors.context}
                        strokeWidth={1.25}
                        dot={false}
                        activeDot={false}
                        connectNulls
                        isAnimationActive={false}
                      />
                    ))}
                    <Line
                      key={focus}
                      type="monotone"
                      dataKey={focus}
                      stroke={colors.series1}
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 4, stroke: colors.surface, strokeWidth: 2 }}
                      connectNulls
                      isAnimationActive={false}
                    >
                      <LabelList
                        dataKey={focus}
                        content={({ x, y, index }) =>
                          index === timeline.length - 1 ? (
                            <text x={Number(x) + 8} y={Number(y) + 4} fontSize={11} fill={colors.ink} fontFamily="IBM Plex Mono">
                              {focus}
                            </text>
                          ) : null
                        }
                      />
                    </Line>
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3">
                <SourceNote source="Yahoo Finance, harga disesuaikan dividen" date={data.as_of} />
              </div>
            </div>
          )}
        </RemoteBody>
      </Panel>

      {/* Sector summary */}
      <Panel
        title="Sektor"
        meta={`${marketOverview.sector_summary.length} sektor`}
        flush
      >
        <div className="overflow-x-auto">
          <table className="w-full text-[13px]">
            <thead className="border-b border-line">
              <tr className="text-left">
                <th className="px-4 h-9 font-medium text-xs text-ink-3">Sektor</th>
                <th className="px-4 h-9 font-medium text-xs text-ink-3">Sentimen</th>
                <th className="px-4 h-9 font-medium text-xs text-ink-3">Rata-rata peluang</th>
                <th className="px-4 h-9 font-medium text-xs text-ink-3 text-right">Anomali</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {[...marketOverview.sector_summary]
                .sort((a, b) => b.avg_opportunity - a.avg_opportunity)
                .map(sec => (
                  <tr key={sec.sector} className="hover:bg-surface-2">
                    <td className="px-4 h-10 text-ink">{sec.sector}</td>
                    <td className="px-4 h-10">
                      <Tag tone={sec.sentiment === 'Bullish' ? 'up' : sec.sentiment === 'Bearish' ? 'down' : 'neutral'}>
                        {sec.sentiment === 'Neutral' ? 'Netral' : sec.sentiment}
                      </Tag>
                    </td>
                    <td className="px-4 h-10"><ScoreBar value={sec.avg_opportunity} width="w-28" /></td>
                    <td className={cx('px-4 h-10 num text-right', sec.anomaly_count ? 'text-warn' : 'text-ink-3')}>
                      {sec.anomaly_count}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </Panel>

      {/* Directory */}
      <Panel
        title="Semua emiten"
        meta={`${directory.length} dari ${rows.length}`}
        flush
      >
        <div className="flex flex-col sm:flex-row gap-2 p-3 border-b border-line">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-3.5 h-3.5 text-ink-3 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Saring kode, nama, sub-sektor"
              className="w-full h-8 pl-8 pr-3 rounded-md bg-canvas border border-line text-[13px] text-ink placeholder:text-ink-3 outline-none focus:border-accent"
            />
          </div>
          <select
            value={sector}
            onChange={e => setSector(e.target.value)}
            className="h-8 px-2 rounded-md bg-canvas border border-line text-[13px] text-ink outline-none focus:border-accent"
            aria-label="Filter sektor"
          >
            <option value="ALL">Semua sektor</option>
            {sectors.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-[13px]">
            <thead className="border-b border-line">
              <tr className="text-left">
                <th className="w-8" />
                <SortHeader label="Kode" sortKey="symbol" current={sortKey} dir={sortDir} onSort={onSort} />
                <SortHeader label="Sektor" sortKey="sector" current={sortKey} dir={sortDir} onSort={onSort} />
                <SortHeader label="Kap. pasar" sortKey="market_cap" current={sortKey} dir={sortDir} onSort={onSort} align="right" />
                <th className="px-4 h-9 font-medium text-xs text-ink-3">Arah</th>
                <SortHeader label="Peluang" sortKey="opportunity" current={sortKey} dir={sortDir} onSort={onSort} />
                <SortHeader label="Risiko" sortKey="risk" current={sortKey} dir={sortDir} onSort={onSort} />
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {directory.map(r => (
                <tr
                  key={r.symbol}
                  onClick={() => onSelectSymbol(r.symbol)}
                  className="hover:bg-surface-2 cursor-pointer"
                >
                  <td className="pl-3 h-11">
                    <WatchlistButton
                      symbol={r.symbol}
                      isInWatchlist={watchlist.includes(r.symbol)}
                      onToggle={onToggleWatchlist}
                    />
                  </td>
                  <td className="px-4 h-11">
                    <div className="flex items-baseline gap-2.5 min-w-[200px]">
                      <span className="num font-medium text-ink">{r.symbol}</span>
                      <span className="text-ink-2 truncate">{r.name}</span>
                      {r.intel?.is_anomaly && <span className="text-warn text-xs" title="Anomali terdeteksi">●</span>}
                    </div>
                  </td>
                  <td className="px-4 h-11 text-ink-2 whitespace-nowrap">{r.sector}</td>
                  <td className="px-4 h-11 num text-ink-2 text-right whitespace-nowrap">{formatMarketCap(r.market_cap)}</td>
                  <td className="px-4 h-11">{r.intel ? <DirectionTag direction={r.intel.direction} /> : <span className="text-ink-3">—</span>}</td>
                  <td className="px-4 h-11">{r.intel ? <ScoreBar value={r.intel.opportunity_score} width="w-16" /> : '—'}</td>
                  <td className="px-4 h-11">{r.intel ? <ScoreBar value={r.intel.risk_score} tone="risk" width="w-16" /> : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {directory.length === 0 && (
            <EmptyState title="Tidak ada emiten yang cocok">Ubah kata kunci atau pilih sektor lain.</EmptyState>
          )}
        </div>
      </Panel>
    </div>
  );
};
